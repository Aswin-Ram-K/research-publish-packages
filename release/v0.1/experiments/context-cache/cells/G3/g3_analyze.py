#!/usr/bin/env python3
"""Offline analysis for G3 rows. Re-runnable; no live calls."""
from __future__ import annotations
import json, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS_PATH = HERE / "rows.jsonl"
ANALYSIS_PATH = HERE / "analysis.json"

ARMS = ["R", "A", "C", "H"]
DEPTHS = ["32k", "64k"]


def load_rows(path=ROWS_PATH):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def analyze(rows):
    # dedupe by (arm, depth, turn) keeping last
    seen = {}
    for r in rows:
        seen[(r["arm"], r.get("depth"), r["turn"])] = r
    rows = list(seen.values())

    by = {}
    for r in rows:
        by.setdefault((r.get("depth"), r["arm"]), []).append(r)

    depths_out = {}
    for depth in DEPTHS:
        arms_out = {}
        for arm in ARMS:
            rs = sorted(by.get((depth, arm), []), key=lambda x: x["turn"])
            if not rs:
                arms_out[arm] = {"missing": True, "n": 0}
                continue
            budget = rs[-1]["budget_tokens"]
            last = rs[-1]
            total_prompt = sum(r["prompt_tokens"] for r in rs)
            total_cached = sum(r["cached_tokens"] for r in rs)
            total_uncached = sum(r["uncached"] for r in rs)
            errors = [r for r in rs if r.get("status", 200) != 200]
            final_prompt = last["prompt_tokens"]
            limit_hit = bool(final_prompt > budget)
            over_max = bool(final_prompt > 131072)
            arms_out[arm] = {
                "n": len(rs),
                "budget_tokens": budget,
                "final_prompt_tokens": final_prompt,
                "total_prompt_tokens": total_prompt,
                "total_cached_tokens": total_cached,
                "total_uncached_tokens": total_uncached,
                "mean_uncached_per_turn": round(total_uncached / len(rs), 1),
                "limit_hit": limit_hit,
                "exceeds_max_model_len": over_max,
                "errors": len(errors),
                "available": (not limit_hit) and (len(errors) == 0) and (not over_max),
                "last_status": last.get("status"),
            }
        depths_out[depth] = arms_out

    # A availability summary
    avail = {}
    for depth in DEPTHS:
        a = depths_out[depth].get("A", {})
        avail[depth] = {
            "A_available": a.get("available", False),
            "A_final_prompt": a.get("final_prompt_tokens"),
            "A_limit_hit": a.get("limit_hit"),
            "A_errors": a.get("errors"),
        }

    return {
        "unit": "G3",
        "arms": ARMS,
        "depths": depths_out,
        "A_availability": avail,
        "n_rows": len(rows),
    }


def main():
    rows = load_rows()
    payload = analyze(rows)
    # merge digest if analysis.json exists
    if ANALYSIS_PATH.exists():
        try:
            old = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
            if "digest" in old:
                payload["digest"] = old["digest"]
        except Exception:
            pass
    ANALYSIS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
