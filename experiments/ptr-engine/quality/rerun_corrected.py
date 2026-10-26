#!/usr/bin/env python3
"""BILL-REPAIR: re-run the four QUALITY-ARM arms with the CORRECTED runner.

Writes to ``rows-corrected.jsonl``, never to ``rows.jsonl``: the shipped rows are
ledger history (they are what ``hasil``-published bills were computed from) and they
stay on disk unmodified.  One row per request, flush()+fsync() per row.
"""
import json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import runner

OUT = HERE / "rows-corrected.jsonl"

def main():
    if OUT.exists():
        OUT.unlink()
    runner.ROWS = OUT
    results = []
    for arm in "ABCD":
        for rep in range(3):
            s = runner.run_rep(arm, rep)
            results.append(s)
            print(f"{arm} rep{rep}: success={s['task_success']} "
                  f"server_uncached={s['server_uncached_tokens']} "
                  f"server_cached={s['server_cached_tokens']} "
                  f"null_turns={s['server_null_turns']} law={s['billed_tokens']} "
                  f"resolved={s['resolved_total']} refused={s['refused_total']} "
                  f"codes={s['codes']}", flush=True)
            if s["errors"]:
                for e in s["errors"]:
                    print("  ERR", e[:300], flush=True)
    agg = {}
    for s in results:
        a = agg.setdefault(s["arm"], {"n": 0, "success": 0, "unc": [], "cached": [], "law": [],
                                      "nulls": [], "resolved": 0, "refused": 0, "codes": set()})
        a["n"] += 1; a["success"] += bool(s["task_success"])
        a["unc"].append(s["server_uncached_tokens"]); a["cached"].append(s["server_cached_tokens"])
        a["law"].append(s["billed_tokens"]); a["nulls"] += s["server_null_turns"]
        a["resolved"] += s["resolved_total"]; a["refused"] += s["refused_total"]
        a["codes"] |= set(s["codes"])
    out = {}
    for arm, a in agg.items():
        out[arm] = {"n": a["n"], "success": f"{a['success']}/{a['n']}",
                    "server_uncached": a["unc"], "server_cached": a["cached"],
                    "law_column": a["law"], "null_turns": a["nulls"],
                    "resolved_total": a["resolved"], "refused_total": a["refused"],
                    "codes": sorted(a["codes"])}
        print(f"ARM {arm}: {json.dumps(out[arm])}", flush=True)
    (HERE / "results-corrected.json").write_text(json.dumps(out, indent=1))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
