#!/usr/bin/env python3
"""UNIT MISS-LAW grid 2 -- dense sweep over the PRIMED length P1 rather than over
the payload, because P1 mod B is what the first diagnostic showed to matter.

Finding that motivated this shape: with the payload sweep, cells at
P1 mod 64 in {0,1} reported cached_tokens = None (a complete miss, even for an
identical repeat) while P1 mod 64 in {5,13,21,37,53} reported
cached = floor(P1/64)*64 and uncached = (P1 mod 64) + L_app.

P1 = F + 53 exactly for this request shape (nonce 10 + filler F + question +
template), verified at seven filler lengths, so a P1 target sets F = P1 - 53 with
no calibration request needed.

Cells:
  residue  : P1 over 64 consecutive values (all residues mod 64), n = 1, 3 reps
  nvar     : a few residues x payload grid, 2 reps
  block    : (vllm only) P1 spread across one 1056-token block, 3 reps
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time
import json

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("r", os.path.join(HERE, "run.py"))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

ROWS = os.path.join(HERE, "rows.jsonl")
P1_OVERHEAD = 53


def cell(server, p1_target, n, rep, B, fd, done, used, notes=""):
    key = (server, f"res-{p1_target}-n{n}", rep)
    if (server, f"res-{p1_target}-n{n}", rep, "prime") in done and \
       (server, f"res-{p1_target}-n{n}", rep, "measure") in done:
        return None
    cfg = r.SERVERS[server]
    ctx = {"name": server, "cfg": cfg}
    nonce = r.make_nonce(f"res-{p1_target}-n{n}", rep, used)
    F = p1_target - P1_OVERHEAD
    hist = nonce + "\n\n" + r.build_filler(F, cfg) + "\n\n" + r.QUESTION
    prime = [{"role": "system", "content": hist},
             {"role": "user", "content": "Reply with the single word OK."}]
    a = r.send(ctx, prime)
    P1 = a["prompt_tokens"]
    r.append_row(fd, {
        "server": server, "model": cfg["model"], "phase": "residue",
        "cell": f"res-{p1_target}-n{n}", "rep": rep, "role": "prime",
        "nonce": nonce, "filler_tokens": F, "n_payload": n,
        "prompt_tokens": P1, "cached_tokens": a["cached_tokens"],
        "cached_reported": a["cached_reported"],
        "uncached_tokens": (None if P1 is None else P1 - (a["cached_tokens"] or 0)),
        "B_measured": B, "H_res": (None if (P1 is None or not B) else P1 % B),
        "elapsed_s": a["elapsed_s"], "error": a["error"], "shape": "prime",
        "notes": notes, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    meas = prime + [{"role": "assistant", "content": "OK."},
                    {"role": "user", "content": " the" * n}]
    b = r.send(ctx, meas)
    P2 = b["prompt_tokens"]
    L = None if (P1 is None or P2 is None) else P2 - P1
    r.append_row(fd, {
        "server": server, "model": cfg["model"], "phase": "residue",
        "cell": f"res-{p1_target}-n{n}", "rep": rep, "role": "measure",
        "nonce": nonce, "filler_tokens": F, "n_payload": n,
        "prev_prompt_tokens": P1, "prompt_tokens": P2,
        "cached_tokens": b["cached_tokens"], "cached_reported": b["cached_reported"],
        "uncached_tokens": (None if P2 is None else P2 - (b["cached_tokens"] or 0)),
        "L_app": L, "B_measured": B,
        "H_res": (None if (P1 is None or not B) else P1 % B),
        "L_res": (None if (L is None or not B) else L % B),
        "elapsed_s": b["elapsed_s"], "error": b["error"],
        "hits_delta": b.get("hits_delta"), "shape": "measure", "notes": notes,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    return P1, P2, b["cached_tokens"]


def main() -> int:
    server = sys.argv[1] if len(sys.argv) > 1 else "sglang"
    max_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
    B = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    t0 = time.time()
    done, used, _n, _p = r.load_state(ROWS)
    fd = os.open(ROWS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        if server == "sglang":
            base = 8000
            reps = 3
            plan = [(base + k, 1, reps) for k in range(64)]
            for p1 in (8005, 8037, 8063, 8064, 8065):
                for n in (16, 32, 64, 128):
                    plan.append((p1, n, 2))
        else:
            base = 7000
            reps = 3
            offs = list(range(0, 1056, 66)) + [1054, 1055]
            plan = [(base + o, 1, reps) for o in offs]
            for p1 in (7000, 7050, 8055, 8056):
                for n in (64, 512, 1056):
                    plan.append((p1, n, 2))
        for p1, n, reps in plan:
            for rep in range(reps):
                if time.time() - t0 > max_seconds:
                    print(f"[budget] stop at P1={p1} n={n} rep={rep}", flush=True)
                    return 0
                out = cell(server, p1, n, rep, B, fd, done, used)
                if out:
                    P1, P2, c2 = out
                    print(f"  P1={P1} (res {P1 % B if P1 else None:4d}) n={n:4d} rep={rep} "
                          f"P2={P2} cached={c2} uncached={None if P2 is None else P2 - (c2 or 0)}",
                          flush=True)
    finally:
        os.close(fd)
    print(f"done in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
