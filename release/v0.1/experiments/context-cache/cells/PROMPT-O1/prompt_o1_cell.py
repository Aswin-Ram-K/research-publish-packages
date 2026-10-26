#!/usr/bin/env python3
"""PROMPT-O1 — five prompt arms x 71 turns, production occamy-1.0 on SGLang.

Reuses the Round-1 renderers VERBATIM from
``experiments/context-cache/cells/VLLM-CELL/vllm_cell.py`` (``SCAFFOLD``,
``delta_block``, ``summarise``, ``folded_summary``, ``pointer_index``,
``render``, ``estimate_tokens``, ``fit_budget``, ``assert_arms_distinct``) so
the arms stay byte-comparable with Round 1.  Nothing in that file is edited; it
is imported by path.

Arms (4 from Round 1 + 1 baseline):
  R   resend every turn, full body, no structure        (round-1 render("R"))
  A   stable scaffold + pointer index + newest delta    (round-1 render("A"))
  C   A with TAG[t=...] terminating the delta           (round-1 render("C"))
  H   hybrid/compaction, folds every 8 turns            (round-1 render("H"))
  C0  plain chat transcript: system + verbatim history  (new: no pointer index)

Config: ``state/config/best-config.json`` -> ``setups.O1`` (read, never
re-derived).  Endpoint ``RESEXTRACT_OCCAMY_BASE_URL`` (default
http://serving-host/v1).

Guards:
  * warm-up: two identical small calls must return
    ``usage.prompt_tokens_details.cached_tokens`` present and > 0 on the
    second, else the cell is written failed with the raw response body.
  * ARMS_IDENTICAL: each arm's turn-1 prompt is hashed; any two equal -> the
    cell reports ``status="invalid_arms_identical"`` instead of a winner.
  * cold start: every arm gets a fresh salt preamble so turn 1 cannot be
    served from another arm's prefix.
  * non-200 / missing or null cached_tokens -> the run aborts for that cell and
    the row is NOT written as a 200.

Writes only under this cell directory plus the two orchestration paths.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
assert (REPO / "src" / "resextract").is_dir(), f"repo root not found from {HERE}"

CELL = "PROMPT-O1"
ROWS_PATH = HERE / "rows.jsonl"
ANALYSIS_PATH = HERE / "analysis.json"
EVENTS_PATH = HERE / "events.jsonl"
WARMUP_PATH = HERE / "warmup.json"
LOCK_PATH = REPO / "experiments" / "context-cache" / ".occamy.lock"
BEST_CONFIG = REPO / "state" / "config" / "best-config.json"
RENDERER_PATH = REPO / "experiments" / "context-cache" / "cells" / "VLLM-CELL" / "vllm_cell.py"
HANDOFF_PATH = REPO / "orchestration" / "handoffs" / f"{CELL}.json"
UNIT_PATH = REPO / "orchestration" / "units" / f"{CELL}.md"

BASE_URL = os.environ.get("RESEXTRACT_OCCAMY_BASE_URL", "http://serving-host/v1")
TURNS = 71
BUDGET_TOKENS = 32768
MAX_TOKENS = 8
ALPHA = 0.05

ROUND1_ARMS = ("R", "A", "C", "H")
ARMS = ("R", "A", "C", "H", "C0")


# --------------------------------------------------------------------------- #
# Imports
# --------------------------------------------------------------------------- #
def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_client():
    path = REPO / "experiments" / "context-cache" / "client.py"
    mod = load_module("ctx_client_prompt_o1", path)
    return mod.ChatClient


# --------------------------------------------------------------------------- #
# Config (read, never re-derived)
# --------------------------------------------------------------------------- #
def load_setup() -> dict:
    cfg = json.loads(BEST_CONFIG.read_text(encoding="utf-8"))
    setup = cfg["setups"]["O1"]
    if setup.get("config_id") != "O1":
        raise RuntimeError(f"setups.O1 carries config_id={setup.get('config_id')!r}")
    return {
        "model": setup["model"],
        "engine": setup["engine"],
        "config_id": setup["config_id"],
        "config_sha256": setup["config_sha256"],
        "context_length": None,
        "argv": list(setup["argv"]),
    }


# --------------------------------------------------------------------------- #
# Arms
# --------------------------------------------------------------------------- #
SALT_TAG = "occamy-prompt-o1 salt:%s"


def salt_preamble(arm: str) -> str:
    """Fresh per-arm salt so no arm's turn 1 can hit another arm's prefix."""

    digest = hashlib.sha256(f"PROMPT-O1|{arm}|2026-10-24".encode("utf-8")).hexdigest()
    return SALT_TAG % digest[:16]


def arm_text(renderer, arm: str, turn: int) -> str:
    if arm in ROUND1_ARMS:
        return renderer.render(arm, turn)[0]["content"]
    if arm == "C0":
        # plain chat transcript: system prompt + verbatim history, no index
        return (renderer.SCAFFOLD + "TRANSCRIPT:\n"
                + renderer.body_upto(turn) + "\n" + renderer.CANARY)
    raise ValueError(f"unknown arm {arm!r}")


def arm_messages(renderer, arm: str, turn: int) -> list[dict]:
    """Round-1 rendering verbatim, plus the per-arm salted head message."""

    content = salt_preamble(arm) + "\n" + arm_text(renderer, arm, turn)
    first = [{"role": "user", "content": content}]
    if arm == "C0":  # plain chat transcript => role-separated history
        first = [{"role": "system", "content": salt_preamble(arm) + "\n" + renderer.SCAFFOLD}]
        for t in range(1, turn + 1):
            first.append({"role": "assistant" if t % 2 == 0 else "user",
                          "content": renderer.delta_block(t)})
        first.append({"role": "user", "content": renderer.CANARY})
        return first
    return first


def prompt_sha(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def prefix_sha(messages: list[dict]) -> str:
    """Stable-prefix digest: the first message IN FULL + the number of later ones."""

    return hashlib.sha256(json.dumps([messages[0], len(messages)], sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    import math

    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * _betai(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_ppf(p: float, df: float) -> float:
    if not 0.5 < p < 1.0:
        raise ValueError("p must be in (0.5, 1)")
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def mean_ci(values: list[float]) -> dict:
    n = len(values)
    mean = statistics.fmean(values)
    if n < 2:
        return {"n": n, "mean": mean, "sd": None, "se": None,
                "ci95": None, "ci95_excludes_zero": None}
    sd = statistics.stdev(values)
    se = sd / n ** 0.5
    half = t_ppf(1.0 - ALPHA / 2.0, n - 1) * se
    lo, hi = mean - half, mean + half
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "t_crit": t_ppf(1.0 - ALPHA / 2.0, n - 1), "ci95": [lo, hi],
            "ci95_excludes_zero": bool(lo > 0 or hi < 0)}


def paired_delta(a_vals: list[float], b_vals: list[float]) -> dict:
    if len(a_vals) != len(b_vals):
        raise RuntimeError(f"paired delta needs equal n: {len(a_vals)} vs {len(b_vals)}")
    diffs = [a - b for a, b in zip(a_vals, b_vals)]
    out = mean_ci(diffs)
    out["sum_diff"] = sum(diffs)
    out["a_minus_b"] = out["mean"]
    return out


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def call(client, messages, max_tokens=MAX_TOKENS, timeout=180.0) -> dict:
    """One chat call; returns raw usage + status. Never invents a 0."""

    used = client.payload(messages, max_tokens=max_tokens, thinking=False, stream=False)
    started = time.perf_counter()
    with client._http(timeout) as http:  # noqa: SLF001 - the class is the contract
        resp = http.post("/chat/completions", json=used)
    wall_ms = (time.perf_counter() - started) * 1000.0
    body = resp.text
    payload = None
    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001
        payload = None
    usage = (payload or {}).get("usage") if isinstance(payload, dict) else None
    details = (usage or {}).get("prompt_tokens_details") if isinstance(usage, dict) else None
    cached = details.get("cached_tokens") if isinstance(details, dict) else None
    prompt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    return {
        "http_status": int(resp.status_code),
        "usage": usage,
        "prompt_tokens": None if prompt is None else int(prompt),
        "cached_tokens": None if cached is None else int(cached),
        "details_present": isinstance(details, dict),
        "wall_ms": round(wall_ms, 3),
        "body": body,
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_row(row: dict) -> None:
    with ROWS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def write_json(path: Path, payload) -> None:
    tmp = HERE / (path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def acquire_lock(timeout_s: float = 600.0):
    handle = LOCK_PATH.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise TimeoutError(f"occamy lock {LOCK_PATH} busy for {timeout_s:.0f}s")
            time.sleep(0.5)
    handle.seek(0)
    handle.truncate()
    json.dump({"unit": CELL, "pid": os.getpid(), "acquired_utc": utc_now(),
               "scope": f"{CELL} five-arm prompt cell; held for the whole run"}, handle)
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def release_lock(handle) -> None:
    try:
        handle.seek(0)
        handle.truncate()
        json.dump({"unit": CELL, "pid": os.getpid(), "released_utc": utc_now()}, handle)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        handle.close()


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def analyse(rows: list[dict], guard: dict) -> dict:
    by_arm: dict[str, list[dict]] = {a: [] for a in ARMS}
    for r in rows:
        by_arm.setdefault(str(r["arm"]), []).append(r)

    per_arm: dict[str, dict] = {}
    series: dict[str, list[float]] = {}
    for arm in ARMS:
        rs = sorted(by_arm.get(arm, []), key=lambda r: int(r["turn"]))
        unc = [float(r["uncached_tokens"]) for r in rs if r.get("uncached_tokens") is not None]
        series[arm] = unc
        if not unc:
            per_arm[arm] = {"n_rows": len(rs), "mean_uncached_per_turn": None,
                            "sd": None, "ci95": None, "ci95_excludes_zero": None,
                            "total_prompt_tokens": 0, "total_cached_tokens": 0,
                            "total_uncached_tokens": 0, "hit_fraction_weighted": None,
                            "hit_fraction_mean_per_turn": None, "series_uncached": []}
            continue
        prompt = sum(int(r["prompt_tokens"]) for r in rs if r.get("prompt_tokens") is not None)
        cached = sum(int(r["cached_tokens"]) for r in rs if r.get("cached_tokens") is not None)
        ci = mean_ci(unc)
        per_arm[arm] = {
            "n_rows": len(rs),
            "turns": [int(r["turn"]) for r in rs],
            "mean_uncached_per_turn": ci["mean"],
            "sd": ci["sd"],
            "ci95": ci["ci95"],
            "ci95_excludes_zero": ci["ci95_excludes_zero"],
            "t_crit": ci.get("t_crit"),
            "total_prompt_tokens": prompt,
            "total_cached_tokens": cached,
            "total_uncached_tokens": int(sum(unc)),
            "hit_fraction_weighted": (cached / prompt) if prompt else None,
            "hit_fraction_mean_per_turn": (
                statistics.fmean([int(r["cached_tokens"]) / int(r["prompt_tokens"])
                                  for r in rs if r.get("cached_tokens") is not None
                                  and int(r["prompt_tokens"]) > 0]) if rs else None),
            "min_uncached": min(unc) if unc else None,
            "max_uncached": max(unc) if unc else None,
            "series_uncached": unc,
        }

    deltas: dict[str, dict] = {}
    for arm in ("A", "C", "H", "C0"):
        if not series.get(arm) or not series.get("R"):
            deltas[f"{arm}-R"] = {"mean_uncached_per_turn_delta": None, "ci95": None,
                                  "sum_diff_tokens": None, "excludes_zero": None,
                                  "n_pairs": 0}
            continue
        d = paired_delta(series.get(arm, []), series.get("R", []))
        deltas[f"{arm}-R"] = {
            "mean_uncached_per_turn_delta": d["mean"],
            "ci95": d["ci95"],
            "sum_diff_tokens": d["sum_diff"],
            "excludes_zero": d["ci95_excludes_zero"],
            "n_pairs": d["n"],
        }

    invalid = bool(guard.get("arms_identical"))
    return {
        "unit": CELL,
        "cell": CELL,
        "status": "invalid_arms_identical" if invalid else (
            "done" if len(rows) == TURNS * len(ARMS) else "partial"),
        "arms_identical_guard": guard,
        "method": {
            "metric": "uncached_tokens = prompt_tokens - prompt_tokens_details.cached_tokens",
            "interval": f"two-sided {1-ALPHA:.0%} t-interval, ddof=1, df=n-1, "
                        "paired over turns for deltas",
            "turns": TURNS,
            "budget_tokens": BUDGET_TOKENS,
            "n_rows": len(rows),
        },
        "per_arm": per_arm,
        "deltas_vs_R": deltas,
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    setup = load_setup()
    renderer = load_module("vllm_cell_round1", RENDERER_PATH)
    ChatClient = load_client()
    client = ChatClient(base_url=BASE_URL, model=setup["model"], timeout=180.0)

    # --- ARMS_IDENTICAL guard over turn-1 prompts ------------------------- #
    hashes = {a: hashlib.sha256(
        json.dumps(arm_messages(renderer, a, 1), sort_keys=True).encode()).hexdigest()
        for a in ARMS}
    collisions = []
    for i, a in enumerate(ARMS):
        for b in ARMS[i + 1:]:
            if hashes[a] == hashes[b]:
                collisions.append(f"{a}=={b}")
    guard = {"arm_first_prompt_sha256": hashes, "collisions": collisions,
             "arms_identical": bool(collisions)}
    print(f"ARMS_IDENTICAL guard: collisions={collisions or 'none'}", flush=True)

    handle = acquire_lock()
    try:
        # --- warm-up: two identical small calls ---------------------------- #
        warm_msgs = [{"role": "user", "content": (
            "PROMPT-O1 warm-up. Reply with the single word: ready.\n"
            "padding: " + ("cache probe block 0123456789 " * 400))}]
        warm1 = call(client, warm_msgs, max_tokens=8)
        warm2 = call(client, warm_msgs, max_tokens=8)
        warm = {
            "url": BASE_URL + "/chat/completions",
            "model": setup["model"],
            "call1": {k: warm1[k] for k in ("http_status", "prompt_tokens",
                                            "cached_tokens", "details_present", "usage")},
            "call2": {k: warm2[k] for k in ("http_status", "prompt_tokens",
                                            "cached_tokens", "details_present", "usage")},
            "call2_body": warm2["body"][:2000],
        }
        write_json(WARMUP_PATH, warm)
        blind = (warm2["http_status"] != 200 or not warm2["details_present"]
                 or warm2["cached_tokens"] is None or warm2["cached_tokens"] <= 0)
        print(f"warm-up: call1 cached={warm1['cached_tokens']} "
              f"call2 cached={warm2['cached_tokens']} details={warm2['details_present']} "
              f"status={warm2['http_status']}", flush=True)
        if blind:
            payload = {
                "unit": CELL, "cell": CELL, "status": "failed_blind_instrument",
                "reason": "second warm-up call did not report a positive "
                          "usage.prompt_tokens_details.cached_tokens",
                "arms_identical_guard": guard, "warmup": warm,
                "n_rows": 0,
            }
            write_json(ANALYSIS_PATH, payload)
            print("STOP: blind instrument. response body: " + warm2["body"][:1500], flush=True)
            return 2

        # --- measurement ---------------------------------------------------- #
        done = set()
        if ROWS_PATH.exists():
            for line in ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        r = json.loads(line)
                        done.add((r["arm"], int(r["turn"])))
                    except Exception:  # noqa: BLE001
                        continue
        requests = 2
        aborted = None
        for arm in ARMS:
            for turn in range(1, TURNS + 1):
                if (arm, turn) in done:
                    continue
                messages = arm_messages(renderer, arm, turn)
                fitted, truncated = renderer.fit_budget(messages, BUDGET_TOKENS)
                blob = json.dumps(fitted)
                pad_tokens = renderer.estimate_tokens(blob)
                res = call(client, fitted)
                requests += 1
                # Measured instrument shape on SGLang 0.0.0.dev1: usage reports
                # prompt_tokens_details == null WHEN NOTHING WAS REUSED (a pure
                # miss) and a positive grid-floored count on a hit.  A miss is
                # therefore cached=0, recorded as null_details_miss, never a
                # missing measurement.  http!=200 still aborts and writes no row.
                if res["http_status"] == 200 and res["cached_tokens"] is None \
                        and res["prompt_tokens"] is not None:
                    res["cached_tokens"] = 0
                    res["cold_null_details"] = True
                if res["http_status"] != 200 or res["cached_tokens"] is None \
                        or res["prompt_tokens"] is None:
                    aborted = {"arm": arm, "turn": turn, "http_status": res["http_status"],
                               "cached_tokens": res["cached_tokens"],
                               "body": res["body"][:3000]}
                    write_json(EVENTS_PATH, {"aborted": aborted, "requests": requests})
                    print(f"ABORT {arm} turn {turn}: http={res['http_status']} "
                          f"cached={res['cached_tokens']} body={res['body'][:600]}", flush=True)
                    break
                row = {
                    "stack": "sglang",
                    "config_id": setup["config_id"],
                    "config_sha256": setup["config_sha256"],
                    "model": setup["model"],
                    "engine": setup["engine"],
                    "engine_version": None,  # not reported by /v1/models
                    "arm": arm,
                    "turn": turn,
                    "prompt_tokens": res["prompt_tokens"],
                    "cached_tokens": res["cached_tokens"],
                    "uncached_tokens": res["prompt_tokens"] - res["cached_tokens"],
                    "http_status": res["http_status"],
                    "prefix_sha256": prefix_sha(fitted),
                    "pad_tokens": pad_tokens,
                    "prompt_sha256": prompt_sha(fitted),
                    "prompt_bytes": len(blob),
                    "messages": len(fitted),
                    "truncated": bool(truncated),
                    "budget_tokens": BUDGET_TOKENS,
                    "wall_ms": res["wall_ms"],
                    "cold_null_details": bool(res.get("cold_null_details")),
                    "ts_utc": utc_now(),
                }
                append_row(row)
                if turn % 10 == 0 or turn == 1:
                    print(f"  {arm} t{turn:2d} prompt={row['prompt_tokens']} "
                          f"cached={row['cached_tokens']} unc={row['uncached_tokens']}", flush=True)
            if aborted:
                break

        rows = [json.loads(l) for l in ROWS_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip()] if ROWS_PATH.exists() else []
        payload = analyse(rows, guard)
        payload["warmup_cached_tokens"] = warm2["cached_tokens"]
        payload["requests"] = {"total": requests, "cap": 400}
        payload["config"] = {k: setup[k] for k in ("model", "engine", "config_id", "config_sha256")}
        payload["renderer_source"] = {
            "path": str(RENDERER_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(RENDERER_PATH.read_bytes()).hexdigest(),
            "note": "round-1 renderer imported verbatim; C0 added here "
                    "(SCAFFOLD + verbatim body_upto, no pointer index)",
        }
        if aborted:
            payload["aborted"] = aborted
            payload["status"] = "failed_http"
        write_json(ANALYSIS_PATH, payload)
        rows_sha = hashlib.sha256(ROWS_PATH.read_bytes()).hexdigest() if ROWS_PATH.exists() else ""
        write_handoff(payload, rows, rows_sha, requests, warm2)
        print(json.dumps({"status": payload["status"], "rows": len(rows),
                          "rows_sha256": rows_sha}, indent=1), flush=True)
        return 0 if payload["status"] == "done" else 3
    finally:
        release_lock(handle)


def write_handoff(payload: dict, rows: list[dict], rows_sha: str, requests: int,
                  warm2: dict) -> None:
    pa = payload.get("per_arm") or {}
    dl = payload.get("deltas_vs_R") or {}
    cmd_rows = "wc -l experiments/context-cache/cells/PROMPT-O1/rows.jsonl"
    cmd_guard = (
        "python3 -c \"import json;rows=[json.loads(l) for l in "
        "open('experiments/context-cache/cells/PROMPT-O1/rows.jsonl')];"
        "print(sorted({r['arm'] for r in rows}), sum(1 for r in rows if "
        "r['cached_tokens'] is None), sum(1 for r in rows if r['http_status']!=200))\"")
    evidence = {
        cmd_rows: str(len(rows)),
        cmd_guard: f"{sorted({r['arm'] for r in rows})} "
                   f"{sum(1 for r in rows if r['cached_tokens'] is None)} "
                   f"{sum(1 for r in rows if r['http_status'] != 200)}",
        "warmup_call2_cached_tokens": str(warm2["cached_tokens"]),
        "per_arm_mean_uncached_per_turn": {
            a: (None if v["mean_uncached_per_turn"] is None
            else round(v["mean_uncached_per_turn"], 1)) for a, v in pa.items()},
        "deltas_vs_R": {k: [None if v["mean_uncached_per_turn_delta"] is None
                            else round(v["mean_uncached_per_turn_delta"], 1),
                            v["excludes_zero"]] for k, v in dl.items()},
        "arms_identical": payload["arms_identical_guard"]["collisions"] or "none",
        "commands": [
            ".venv/bin/python experiments/context-cache/cells/PROMPT-O1/prompt_o1_cell.py",
            cmd_rows, cmd_guard,
        ],
    }
    handoff = {
        "unit": CELL,
        "status": {"done": "done"}.get(payload["status"], "failed"),
        "artifacts": [
            str(ROWS_PATH.relative_to(REPO)),
            str(ANALYSIS_PATH.relative_to(REPO)),
            str(WARMUP_PATH.relative_to(REPO)),
        ],
        "evidence": evidence,
        "blocker": payload.get("reason") or (payload.get("aborted") and
                                             json.dumps(payload["aborted"])[:400]) or "",
        "next_unit_hint": "verifier re-runs the two acceptance commands and rebuilds "
                          "the per-arm t-intervals from rows.jsonl",
        "write_paths": [f"experiments/context-cache/cells/{CELL}/**",
                        f"orchestration/handoffs/{CELL}.json",
                        f"orchestration/units/{CELL}.md"],
        "detail": {"rows_sha256": rows_sha, "requests": requests,
                   "status": payload["status"]},
    }
    HANDOFF_PATH.write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
