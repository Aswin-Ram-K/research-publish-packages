#!/usr/bin/env python3
"""UNIT MISS-LAW analysis: measure B, fit the append-cost law, check the models.

Candidate models for the re-billed tail on an append (P1 = primed prompt length,
L_app = appended tokens, P2 = P1 + L_app, B = cache block size):

  M0  tail-preserved   cached = floor(P1/B)*B      uncached = (P1 mod B) + L_app
  M1  one-block-haircut cached = (floor(P1/B)-1)*B  uncached = (P1 mod B) + B + L_app
  M2  tail-reusable     cached = floor(P2/B)*B      uncached = P2 mod B
  M3  append-free       cached = P1                 uncached = L_app

M3 is impossible for a genuinely new append (cached can never exceed the shared
prefix P1); it is included so the fit can refute it rather than assume it.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROWS = os.path.join(ROOT, "rows.jsonl")


def load():
    rows = []
    with open(ROWS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def floor_b(p, b):
    return (p // b) * b


def measure_rows(rows, server=None):
    out = []
    for r in rows:
        if r.get("role") != "measure" or r.get("error"):
            continue
        if server and r.get("server") != server:
            continue
        if r.get("prompt_tokens") is None or r.get("cached_tokens") is None:
            continue
        if not r.get("cached_reported"):
            continue
        out.append(r)
    return out


def detect_B(meas):
    """B must divide every reported cached value, and floor(P1/B)*B must equal it."""
    best = []
    for b in range(8, 1400):
        ok = sum(1 for r in meas
                 if r["cached_tokens"] % b == 0
                 and floor_b(r.get("prev_prompt_tokens") or 0, b) == r["cached_tokens"])
        div = all(r["cached_tokens"] % b == 0 for r in meas)
        if div and ok:
            best.append((ok, b))
    best.sort(key=lambda t: (-t[0], t[1]))
    return best[:6]


def models(r, b):
    P1 = r.get("prev_prompt_tokens")
    P2 = r["prompt_tokens"]
    L = r.get("L_app")
    if not P1 or L is None:
        return None
    return {
        "M0": (P1 % b) + L,
        "M1": (P1 % b) + b + L,
        "M2": P2 % b,
        "M3": L,
    }


def main() -> int:
    rows = load()
    print(f"rows on disk: {len(rows)}")
    out = {"rows_total": len(rows), "servers": {}}

    for server in ("sglang", "vllm"):
        meas = measure_rows(rows, server)
        if not meas:
            print(f"\n### {server}: no instrumented measure rows")
            continue
        cands = detect_B(meas)
        print(f"\n{'='*70}\n### {server}: {len(meas)} measure rows")
        print("  B candidates (exact-fit count, B):", cands[:6])
        if not cands:
            continue
        B = cands[0][1]
        print(f"  B taken = {B}")

        # model scores
        scores = {}
        for name in ("M0", "M1", "M2", "M3"):
            res = []
            for r in meas:
                m = models(r, B)
                if m is None:
                    continue
                res.append(r["uncached_tokens"] - m[name])
            scores[name] = {
                "exact": sum(1 for x in res if x == 0), "n": len(res),
                "mean": round(statistics.mean(res), 2) if res else None,
                "max_abs": max((abs(x) for x in res), default=None),
            }
        print("  model fit (residual = measured_uncached - predicted):")
        for k, v in scores.items():
            print(f"    {k}: exact {v['exact']}/{v['n']}  mean {v['mean']}  max|res| {v['max_abs']}")

        # controls
        ctl = {}
        for r in rows:
            if r.get("server") != server or r.get("phase") != "control":
                continue
            ctl.setdefault(r["cell"], []).append(r)
        print("  controls:")
        for cell, rs in ctl.items():
            for r in sorted(rs, key=lambda x: x["role"]):
                if r.get("prompt_tokens") is None:
                    continue
                print(f"    {cell:9s} {r['role']:6s} prompt={r['prompt_tokens']:6d} "
                      f"cached={r['cached_tokens']} reported={r['cached_reported']} "
                      f"uncached={r['uncached_tokens']}")

        # grid, grouped by history
        grid = [r for r in meas if r.get("phase") == "grid"]
        by_h = {}
        for r in grid:
            by_h.setdefault(r["cell"].split("-")[1], []).append(r)
        print("  grid by history (one row per (n, rep) measure):")
        for h in sorted(by_h):
            rs = sorted(by_h[h], key=lambda r: (r["n_payload"], r["rep"]))
            hres = sorted({r["prompt_tokens"] and (r.get("prev_prompt_tokens") or 0) % B
                           for r in rs})
            print(f"\n   [{h}] H mod B values seen: {hres}")
            print(f"   {'n':>5} {'rep':>3} {'P1':>7} {'L_app':>6} {'P2':>7} "
                  f"{'cached':>7} {'uncached':>8} {'M0pred':>7} {'resid':>6}")
            for r in rs[:80]:
                m = models(r, B)
                print(f"   {r['n_payload']:5d} {r['rep']:3d} {r.get('prev_prompt_tokens'):7d} "
                      f"{r['L_app']:6d} {r['prompt_tokens']:7d} {r['cached_tokens']:7d} "
                      f"{r['uncached_tokens']:8d} {m['M0']:7d} {r['uncached_tokens']-m['M0']:6d}")
        out["servers"][server] = {
            "B": B, "candidates": cands[:6], "scores": scores,
            "n_measure": len(meas),
            "h_res_seen": {h: sorted({(r.get('prev_prompt_tokens') or 0) % B
                                      for r in rs}) for h, rs in by_h.items()},
        }
    with open(os.path.join(ROOT, "law_fit.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("\nwrote law_fit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
