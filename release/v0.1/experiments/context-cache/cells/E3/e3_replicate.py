#!/usr/bin/env python3
"""E3 replication -- U4-shaped append chains (single send per turn, ~810-token bodies).

Why: the balanced chains in e3_probe.py used tails of 4 and 24 sentences; U4's
372 warm appends append ~868 tokens per turn and show residual 832-7936
(median 1792).  This runs the U4 shape exactly -- base ~950 tokens, then five
appends of 27 sentences (~810 tokens), ONE send per turn (no repeat) -- to test
whether the G7 residual scale reproduces and whether the deficit equals one
appended body.

12 live requests (2 chains x 6 turns); total unit spend 104 + 12 = 116 <= 120.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("e3_probe_mod", HERE / "e3_probe.py")
P = importlib.util.module_from_spec(_spec)
sys.modules["e3_probe_mod"] = P
_spec.loader.exec_module(P)

GRID = 64
ROWS = HERE / "e3_replicate_rows.jsonl"
OUT = HERE / "e3_replicate.json"
BODY_SENT = 27
BASE_SENT = 30
TURNS = 6


def main() -> int:
    if ROWS.exists():
        ROWS.unlink()
    t0 = time.time()
    fd = open(P.LOCK_PATH, "a+")
    deadline = time.time() + 2400.0
    acquired = False
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
            break
        except OSError:
            if time.time() - deadline > 0:
                break
            time.sleep(0.5)
    if not acquired:
        OUT.write_text(json.dumps({"status": "partial", "blocker": "lock timeout"}))
        return 3
    rows = []
    req = 0
    m0 = P.metrics_snapshot("replicate:before", 1)
    try:
        for ci in range(2):
            salt = P.make_salt(940000 + ci)
            n = BASE_SENT
            prev = None
            cold = True
            for turn in range(1, TURNS + 1):
                if turn > 1:
                    n += BODY_SENT
                text = P.build_prompt(salt, n)
                P.RAW.clear()
                try:
                    pt, ct, comp, ttft, wall, status, _ = P.client.ChatClient().chat(
                        [{"role": "user", "content": text}], max_tokens=8)
                    err = ""
                except Exception as exc:  # noqa: BLE001
                    pt = ct = status = 0
                    ttft = wall = 0.0
                    err = repr(exc)
                req += 1
                L, m = int(pt), int(ct)
                if prev is None:
                    tail = deficit = None
                else:
                    expected = GRID * (prev // GRID)
                    tail = L - expected - (L % GRID)
                    deficit = expected - m
                row = {"chain": f"rep{ci}", "turn": turn, "salt": salt, "cold": cold,
                       "prompt_tokens": L, "cached_tokens": m, "uncached": L - m,
                       "prev_prompt_tokens": prev,
                       "residual": (L - m) - (L % GRID) if L else None,
                       "tail_term": tail, "deficit": deficit,
                       "ttft_ms": round(float(ttft), 1), "status": status, "error": err}
                rows.append(row)
                with ROWS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row) + "\n")
                print(json.dumps({k: row[k] for k in
                                  ("chain", "turn", "prompt_tokens", "cached_tokens",
                                   "residual", "tail_term", "deficit")}), flush=True)
                prev = L
                cold = False
        m1 = P.metrics_snapshot("replicate:after", 2)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            fd.close()

    app = [r for r in rows if r["deficit"] is not None]
    resid = [r["residual"] for r in app]
    tails = [r["tail_term"] for r in app]
    defs = [r["deficit"] for r in app]
    summary = {
        "status": "done",
        "requests_made": req,
        "rows_sha256": hashlib.sha256(ROWS.read_bytes()).hexdigest(),
        "elapsed_s": round(time.time() - t0, 2),
        "body_sentences": BODY_SENT,
        "residual": {"n": len(resid), "min": min(resid), "median": sorted(resid)[len(resid) // 2],
                     "max": max(resid)},
        "tail_term": {"median": sorted(tails)[len(tails) // 2], "min": min(tails), "max": max(tails)},
        "deficit": {"n": len(defs), "zero": sum(1 for d in defs if d == 0),
                    "positive": sum(1 for d in defs if d > 0),
                    "median": sorted(defs)[len(defs) // 2], "max": max(defs)},
        "per_turn": [{"chain": r["chain"], "turn": r["turn"], "L": r["prompt_tokens"],
                      "prev_L": r["prev_prompt_tokens"], "cached": r["cached_tokens"],
                      "residual": r["residual"], "tail_term": r["tail_term"],
                      "deficit": r["deficit"]} for r in rows],
        "metrics_before": m0["selected"], "metrics_after": m1["selected"],
    }
    OUT.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("requests_made", "residual", "tail_term", "deficit")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
