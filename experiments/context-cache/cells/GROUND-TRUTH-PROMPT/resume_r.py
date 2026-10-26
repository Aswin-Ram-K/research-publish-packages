#!/usr/bin/env python3
"""Resume GROUND-TRUTH-PROMPT's R arm: append turns not yet present, then report."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/zer0null/reserach extarctor")
HERE = Path(__file__).resolve().parent
CELL = "GROUND-TRUTH-PROMPT"
ROWS_PATH = HERE / "rows.jsonl"
SUMMARY_PATH = HERE / "summary.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"

BASE_URL = "http://192.168.2.168:8012/v1"
TURNS = 71
BUDGET_TOKENS = 32768
MAX_TOKENS = 8
ARM = "R"

SALT_SEED = "GROUND-TRUTH-PROMPT|R|2026-10-25T08:05Z|fresh-salt-1"
SALT_DIGEST = hashlib.sha256(SALT_SEED.encode("utf-8")).hexdigest()
SALT_PREAMBLE = "occamy-prompt-o1 salt:%s" % SALT_DIGEST[:16]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def load_module(name, path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def call(client, messages, timeout=180.0):
    used = client.payload(messages, max_tokens=MAX_TOKENS, thinking=False, stream=False)
    used.pop("stream_options", None)
    started = time.perf_counter()
    with client._http(timeout) as http:  # noqa: SLF001
        resp = http.post("/chat/completions", json=used)
    wall_ms = (time.perf_counter() - started) * 1000.0
    body = resp.text
    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001
        payload = None
    usage = (payload or {}).get("usage") if isinstance(payload, dict) else None
    details = (usage or {}).get("prompt_tokens_details") if isinstance(usage, dict) else None
    cached = details.get("cached_tokens") if isinstance(details, dict) else None
    prompt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    return {"http_status": int(resp.status_code), "usage": usage,
            "prompt_tokens": None if prompt is None else int(prompt),
            "cached_tokens": None if cached is None else int(cached),
            "details_present": isinstance(details, dict),
            "cold_null": bool("cold_null_details" in body),
            "wall_ms": round(wall_ms, 3), "body": body}


def prompt_sha(m):
    return hashlib.sha256(json.dumps(m, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def prefix_sha(m):
    return hashlib.sha256(json.dumps([m[0], len(m)], sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def read_rows():
    if not ROWS_PATH.exists():
        return []
    kept = []
    for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            kept.append(json.loads(line))
        except Exception:  # noqa: BLE001
            print(f"dropping torn line ({len(line)} bytes)", flush=True)
    if len(kept) != len(ROWS_PATH.read_text(encoding="utf-8").splitlines()):
        ROWS_PATH.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in kept),
                             encoding="utf-8")
    return kept


def acquire_lock(timeout_s=900.0):
    import fcntl

    handle = LOCK_PATH.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError("occamy lock busy")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": CELL, "pid": os.getpid(), "acquired_utc": utc_now(),
               "scope": f"{CELL} R-arm only on PRODUCTION sglang :8012 (no restart)"}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle):
    import fcntl

    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": CELL, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


def main():
    for p in (REPO / "src", REPO / "experiments" / "context-cache"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from client import ChatClient  # type: ignore

    setup = json.loads((REPO / "state" / "config" / "best-config.json").read_text())["setups"]["O1"]
    renderer = load_module("sglang_cell_round1", RENDERER_PATH)
    client = ChatClient(base_url=BASE_URL, model=setup["model"], timeout=180.0)

    rows = read_rows()
    have = {int(r["turn"]) for r in rows}
    print(f"resume: {len(rows)} rows present, turns {min(have) if have else 0}-"
          f"{max(have) if have else 0}", flush=True)

    requests = 0
    handle = acquire_lock()
    try:
        for turn in range(1, TURNS + 1):
            if turn in have:
                continue
            content = SALT_PREAMBLE + "\n" + renderer.render(ARM, turn)[0]["content"]
            messages = [{"role": "user", "content": content}]
            fitted, truncated = renderer.fit_budget(messages, BUDGET_TOKENS)
            pad_tokens = renderer.estimate_tokens(json.dumps(fitted))
            res = call(client, fitted)
            retries = 0
            while (res["http_status"] == 200 and res["cached_tokens"] is None
                   and res["details_present"] is False and res["cold_null"]
                   and turn != 1 and retries < 3):
                retries += 1
                time.sleep(0.15)
                res = call(client, fitted)
            requests += 1 + retries
            if res["http_status"] != 200 or res["prompt_tokens"] is None:
                print(f"ABORT turn {turn}: http={res['http_status']} {res['body'][:300]}",
                      flush=True)
                return 3
            if res["cached_tokens"] is None:
                cold = bool(res.get("cold_null")) or res["details_present"]
                cached = 0 if cold else None
                source = "cold_null" if res.get("cold_null") else (
                    "zero_cached" if res["details_present"] else "unavailable")
            else:
                cached, source = res["cached_tokens"], "reported"
            unc = (res["prompt_tokens"] - cached) if cached is not None else None
            row = {"cell": CELL, "setup": "O1", "stack": "sglang", "model": setup["model"],
                   "engine": "sglang", "engine_version": setup.get("engine_version", "unavailable"),
                   "config_id": setup["config_id"], "config_sha256": setup["config_sha256"],
                   "arm": ARM, "turn": turn, "prompt_tokens": res["prompt_tokens"],
                   "cached_tokens": cached if cached is not None else "unavailable",
                   "uncached_tokens": unc if unc is not None else "unavailable",
                   "pad_tokens": pad_tokens, "http_status": res["http_status"],
                   "prefix_sha256": prefix_sha(fitted), "prompt_sha256": prompt_sha(fitted),
                   "cache_source": source, "cold_null_details": bool(res.get("cold_null")),
                   "null_retries": retries, "budget_tokens": BUDGET_TOKENS,
                   "messages": len(fitted), "prompt_bytes": len(json.dumps(fitted)),
                   "truncated": bool(truncated), "wall_ms": res["wall_ms"],
                   "salt": SALT_DIGEST[:16], "ts_utc": utc_now()}
            with ROWS_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            print(f"  R t{turn:2d} prompt={row['prompt_tokens']} "
                  f"cached={row['cached_tokens']} unc={unc}", flush=True)
        rows = read_rows()
        cached_series = [r["cached_tokens"] for r in rows]
        prompt_series = [r["prompt_tokens"] for r in rows]
        unc_series = [r["uncached_tokens"] for r in rows]
        measured = [u for u in unc_series if isinstance(u, (int, float))]
        mean_measured = sum(measured) / len(measured)
        summary = {"cell": CELL, "salt": {"seed": SALT_SEED, "digest": SALT_DIGEST,
                                          "preamble": SALT_PREAMBLE},
                   "arm": ARM, "turns": len(rows), "budget_tokens": BUDGET_TOKENS,
                   "resume_requests": requests,
                   "non_200": sum(1 for r in rows if r["http_status"] != 200),
                   "n_measured": len(measured),
                   "mean_uncached_per_turn_measured": round(mean_measured, 6),
                   "prompt_tokens_total": sum(prompt_series),
                   "cached_tokens_total": sum(c for c in cached_series
                                              if isinstance(c, int)),
                   "cached_gt_0": sum(1 for c in cached_series
                                      if isinstance(c, int) and c > 0),
                   "cached_series": cached_series, "prompt_series": prompt_series,
                   "uncached_series": unc_series,
                   "rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
                   "finished_utc": utc_now()}
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in summary.items()
                          if k not in ("cached_series", "prompt_series",
                                       "uncached_series")}, indent=1), flush=True)
        return 0
    finally:
        release_lock(handle)


if __name__ == "__main__":
    sys.exit(main())
