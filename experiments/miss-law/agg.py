#!/usr/bin/env python3
"""UNIT MISS-LAW aggregation: turn rows.jsonl into the law, the tables and the
crossover validation. Nothing here talks to a server."""
from __future__ import annotations

import json
import os
import statistics

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


def meas(rows, server, phase=None):
    out = []
    for r in rows:
        if r.get("role") != "measure" or r.get("error"):
            continue
        if r.get("server") != server:
            continue
        if phase and r.get("phase") != phase:
            continue
        if r.get("prompt_tokens") is None:
            continue
        out.append(r)
    return out


def floor_b(p, b):
    return (p // b) * b


def detect_B(rows, server):
    """Score every B on three necessary conditions taken together."""
    rs = [r for r in meas(rows, server) if r.get("cached_tokens")]
    scored = []
    for b in range(8, 1600):
        d1 = sum(1 for r in rs if r["cached_tokens"] % b == 0)
        d2 = sum(1 for r in rs
                 if (r.get("prev_prompt_tokens") or 0) // b * b == r["cached_tokens"])
        d3 = sum(1 for r in rs
                 if (r.get("prev_prompt_tokens") or 0) % b == r["uncached_tokens"] - (r.get("L_app") or 0))
        scored.append((d1 + d2 + d3, b, d1, d2, d3))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[:5]


def main():
    rows = load()
    report = {"n_rows": len(rows), "servers": {}}
    print(f"rows: {len(rows)}")

    for server, Bguess in (("sglang", 64), ("vllm", 1056)):
        rs_all = meas(rows, server)          # includes rows where the report is null
        rs = [r for r in rs_all if r.get("cached_reported")]
        rs_res = [r for r in rs_all if r.get("phase") == "residue"]
        print(f"\n{'='*78}\n### {server}: {len(rs)} instrumented measure rows "
              f"({len(rs_res)} in the residue sweep)")
        cand = detect_B(rows, server)
        print("  B candidates (score,B,divides,floorP1,resid-match):", cand)
        B = Bguess
        print(f"  B used for the tables: {B}")

        # ---------- residue sweep
        if rs_res:
            report["servers"].setdefault(server, {})
            by_res = {}
            for r in rs_res:
                if r.get("n_payload") != 1:
                    continue
                P1 = r["prev_prompt_tokens"]
                by_res.setdefault(P1 % B, []).append(r)
            miss, ok = [], []
            print(f"\n  residue sweep, n_payload=1 (L_app constant):")
            print(f"   {'res':>4} {'reps':>4} {'P1':>7} {'L_app':>6} {'cached':>8} "
                  f"{'uncached':>9} {'unc-(res+L)':>11}")
            for res in sorted(by_res):
                grp = by_res[res]
                cacheds = {r["cached_tokens"] for r in grp}
                uncs = {r["uncached_tokens"] for r in grp}
                Ls = {r["L_app"] for r in grp}
                L = sorted(Ls)[0] if Ls else None
                resid = {r["uncached_tokens"] - ((r["prev_prompt_tokens"] % B) + (r["L_app"] or 0))
                         for r in grp}
                tag = "MISS" if cacheds == {None} else ""
                print(f"   {res:4d} {len(grp):4d} {grp[0]['prev_prompt_tokens']:7d} "
                      f"{str(L):>6} {str(sorted(cacheds, key=lambda x: (x is None, x))):>8} "
                      f"{str(sorted(uncs)):>9} {str(sorted(resid)):>11} {tag}")
                (miss if cacheds == {None} else ok).append(res)
            print(f"\n  -> residues with a COMPLETE miss (cached=None): {miss}")
            print(f"  -> residues that hit: {ok}")
            report["servers"][server] = {
                "B": B, "residue_miss": miss, "residue_ok": ok,
                "B_candidates": cand, "n_residue_rows": len(rs_res)}

        # ---------- payload variants
        varr = [r for r in rs_res if r.get("n_payload") != 1]
        if varr:
            print("\n  payload variants (predicted uncached = res + L_app):")
            print(f"   {'P1':>7} {'res':>4} {'n':>5} {'L_app':>6} {'cached':>8} {'uncached':>9} {'pred':>7} {'ok':>3}")
            for r in sorted(varr, key=lambda r: (r["prev_prompt_tokens"], r["n_payload"])):
                pred = (r["prev_prompt_tokens"] % B) + (r["L_app"] or 0)
                print(f"   {r['prev_prompt_tokens']:7d} {r['prev_prompt_tokens'] % B:4d} "
                      f"{r['n_payload']:5d} {r['L_app']:6d} {str(r['cached_tokens']):>8} "
                      f"{r['uncached_tokens']:9d} {pred:7d} "
                      f"{'OK' if pred == r['uncached_tokens'] else 'no':>3}")

        # ---------- older grid (payload sweep at fixed P1) kept for the record
        old = [r for r in meas(rows, server) if r.get("phase") == "grid" and r.get("cached_reported")]
        if old:
            print(f"\n  early payload-sweep rows with a reported hit: {len(old)}")

        # ---------- controls
        ctl = {}
        for r in rows:
            if r.get("server") == server and r.get("phase") == "control" and \
                    r.get("prompt_tokens") is not None:
                ctl.setdefault(r["cell"], []).append(r)
        if ctl:
            print("\n  controls:")
            for cell in sorted(ctl):
                off = sum(1 for r in ctl[cell] if r["role"].startswith("cold"))
                for r in sorted(ctl[cell], key=lambda x: x["role"]):
                    share = (r["cached_tokens"] or 0) / r["prompt_tokens"]
                    print(f"   {cell:9s} {r['role']:6s} prompt={r['prompt_tokens']:6d} "
                          f"cached={str(r['cached_tokens']):>6} uncached={r['uncached_tokens']:6d} "
                          f"share={share:5.1%}")

    with open(os.path.join(ROOT, "law_fit.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print("\nwrote law_fit.json")


if __name__ == "__main__":
    main()
