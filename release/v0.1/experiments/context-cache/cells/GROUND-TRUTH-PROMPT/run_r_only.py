#!/usr/bin/env python3
"""GROUND-TRUTH-PROMPT -- the R arm ONLY, 71 turns, budget 32768, NEW SALT.

Replicates cells/R2-P1-O1's R arm byte-for-byte in everything but the salt
preamble: same renderer (cells/VLLM-CELL/vllm_cell.py), same arm body
(render('R', turn)[0]["content"]), same fit_budget, same non-streaming call
carrying usage.prompt_tokens_details.cached_tokens.

Production http://serving-host/v1 (occamy-1.0). HTTP only, no restart.
Holds experiments/context-cache/.occamy.lock. Writes only into this cell.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("<workspace>")
HERE = Path(__file__).resolve().parent
CELL = "GROUND-TRUTH-PROMPT"

ROWS_PATH = HERE / "rows.jsonl"
WARMUP_PATH = HERE / "warmup.json"
LAUNCH_PATH = HERE / "launch.json"
SUMMARY_PATH = HERE / "summary.json"
LOG_PATH = HERE / "run.log"

LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"

BASE_URL = "http://serving-host/v1"
TURNS = 71
BUDGET_TOKENS = 32768
MAX_TOKENS = 8
ARM = "R"

# NEW SALT -- deliberately NOT "PROMPT-O2|R|2026-10-24" used by R2-P1-O1 / PROMPT-O1.
SALT_SEED = "GROUND-TRUTH-PROMPT|R|2026-10-25T08:05Z|fresh-salt-1"
SALT_DIGEST = hashlib.sha256(SALT_SEED.encode("utf-8")).hexdigest()
SALT_TAG = "occamy-prompt-o1 salt:%s"
SALT_PREAMBLE = SALT_TAG % SALT_DIGEST[:16]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_module(name, path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_client():
    for p in (REPO / "src", REPO / "experiments" / "context-cache"):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
    from client import ChatClient  # type: ignore

    return ChatClient


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


def prompt_sha(messages):
    return hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def prefix_sha(messages):
    return hashlib.sha256(json.dumps([messages[0], len(messages)], sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    ROWS_PATH.write_text("", encoding="utf-8")
    setup = json.loads((REPO / "state" / "config" / "best-config.json").read_text())["setups"]["O1"]
    renderer = load_module("sglang_cell_round1", RENDERER_PATH)
    client = load_client()(base_url=BASE_URL, model=setup["model"], timeout=180.0)

    salt_info = {"seed": SALT_SEED, "digest_sha256": SALT_DIGEST,
                 "preamble": SALT_PREAMBLE,
                 "baseline_seed_of_R2-P1-O1": "PROMPT-O2|R|2026-10-24",
                 "baseline_preamble": SALT_TAG % hashlib.sha256(
                     b"PROMPT-O2|R|2026-10-24").hexdigest()[:16]}
    handle = acquire_lock()
    try:
        warm_msgs = [{"role": "user", "content": (
            "GROUND-TRUTH-PROMPT warm-up on production. Reply with the single word: ready.\n"
            "padding: " + ("cache probe block 0123456789 " * 400))}]
        w1 = call(client, warm_msgs)
        w2 = call(client, warm_msgs)
        WARMUP_PATH.write_text(json.dumps({
            "salt": salt_info, "endpoint": BASE_URL, "model": setup["model"],
            "call1": {k: w1[k] for k in ("http_status", "prompt_tokens", "cached_tokens",
                                         "details_present", "usage")},
            "call2": {k: w2[k] for k in ("http_status", "prompt_tokens", "cached_tokens",
                                         "details_present", "usage")}}, indent=2) + "\n")
        gate_ok = (w2["http_status"] == 200 and w2["details_present"]
                   and w2["cached_tokens"] is not None and w2["cached_tokens"] > 0)
        print(f"G0 warmup: call1 cached={w1['cached_tokens']} call2 cached={w2['cached_tokens']} "
              f"status={w2['http_status']} gate={'PASS' if gate_ok else 'FAIL'}", flush=True)
        if not gate_ok:
            print("STOP: instrument blind. " + w2["body"][:600], flush=True)
            return 2

        LAUNCH_PATH.write_text(json.dumps({
            "cell": CELL, "arm": ARM, "turns": TURNS, "budget_tokens": BUDGET_TOKENS,
            "max_tokens": MAX_TOKENS, "endpoint": BASE_URL, "model": setup["model"],
            "config_id": "O1", "config_sha256": setup["config_sha256"],
            "renderer": str(RENDERER_PATH.relative_to(REPO)),
            "renderer_sha256": hashlib.sha256(RENDERER_PATH.read_bytes()).hexdigest(),
            "salt": salt_info, "started_utc": utc_now()}, indent=2) + "\n")

        requests = 2
        for turn in range(1, TURNS + 1):
            content = SALT_PREAMBLE + "\n" + renderer.render(ARM, turn)[0]["content"]
            messages = [{"role": "user", "content": content}]
            fitted, truncated = renderer.fit_budget(messages, BUDGET_TOKENS)
            blob = json.dumps(fitted)
            pad_tokens = renderer.estimate_tokens(blob)
            is_first = (turn == 1)
            res = call(client, fitted)
            retries = 0
            while (res["http_status"] == 200 and res["cached_tokens"] is None
                   and res["details_present"] is False and res["cold_null"]
                   and not is_first and retries < 3):
                retries += 1
                time.sleep(0.15)
                res = call(client, fitted)
            requests += 1 + retries
            if res["http_status"] != 200 or res["prompt_tokens"] is None:
                print(f"ABORT turn {turn}: http={res['http_status']} body={res['body'][:400]}",
                      flush=True)
                return 3
            if res["cached_tokens"] is None:
                cold_null = bool(res.get("cold_null")) or res["details_present"]
                cached = 0 if cold_null else None
                source = "cold_null" if res.get("cold_null") else (
                    "zero_cached" if res["details_present"] else "unavailable")
            else:
                cold_null, cached, source = False, res["cached_tokens"], "reported"
            unc = (res["prompt_tokens"] - cached) if cached is not None else None
            row = {"cell": CELL, "setup": "O1", "stack": "sglang", "model": setup["model"],
                   "engine": "sglang", "engine_version": setup.get("engine_version", "unavailable"),
                   "config_id": setup["config_id"],
                   "config_sha256": setup["config_sha256"], "arm": ARM, "turn": turn,
                   "prompt_tokens": res["prompt_tokens"],
                   "cached_tokens": cached if cached is not None else "unavailable",
                   "uncached_tokens": unc if unc is not None else "unavailable",
                   "pad_tokens": pad_tokens, "http_status": res["http_status"],
                   "prefix_sha256": prefix_sha(fitted), "prompt_sha256": prompt_sha(fitted),
                   "cache_source": source, "cold_null_details": cold_null,
                   "null_retries": retries, "budget_tokens": BUDGET_TOKENS,
                   "messages": len(fitted), "prompt_bytes": len(blob),
                   "truncated": bool(truncated), "wall_ms": res["wall_ms"],
                   "salt": SALT_DIGEST[:16], "ts_utc": utc_now()}
            with ROWS_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            if turn % 10 == 0 or turn == 1:
                print(f"  R t{turn:2d} prompt={row['prompt_tokens']} "
                      f"cached={row['cached_tokens']} unc={unc}", flush=True)

        rows = [json.loads(l) for l in ROWS_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        cached_series = [r["cached_tokens"] for r in rows]
        prompt_series = [r["prompt_tokens"] for r in rows]
        unc_series = [r["uncached_tokens"] for r in rows]
        mean_unc = sum(unc_series) / len(unc_series)
        summary = {"cell": CELL, "salt": salt_info, "arm": ARM, "turns": len(rows),
                   "budget_tokens": BUDGET_TOKENS, "requests": requests,
                   "non_200": sum(1 for r in rows if r["http_status"] != 200),
                   "mean_uncached_per_turn": round(mean_unc, 6),
                   "prompt_tokens_total": sum(prompt_series),
                   "cached_tokens_total": sum(cached_series),
                   "cached_gt_0": sum(1 for c in cached_series if c > 0),
                   "cached_series": cached_series, "prompt_series": prompt_series,
                   "uncached_series": unc_series,
                   "rows_sha256": hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest(),
                   "finished_utc": utc_now()}
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"rows": len(rows), "mean_uncached_per_turn": round(mean_unc, 6),
                          "non_200": summary["non_200"], "requests": requests,
                          "cached_gt_0": summary["cached_gt_0"],
                          "salt": SALT_DIGEST[:16]}, indent=1), flush=True)
        return 0
    finally:
        release_lock(handle)


if __name__ == "__main__":
    sys.exit(main())
