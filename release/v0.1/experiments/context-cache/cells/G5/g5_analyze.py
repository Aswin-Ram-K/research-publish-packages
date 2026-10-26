#!/usr/bin/env python3
"""G5 analysis — pure, offline, over ``rows.jsonl``.

Fan-out ratio: per-fanout total uncached tokens of layout B (and C) divided by
layout A, averaged over fan-outs, with a t-based 95% CI (df = n_fanouts - 1).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable, Sequence

HERE = Path(__file__).resolve().parent
DEFAULT_ROWS = HERE / "rows.jsonl"
DEFAULT_OUT = HERE / "analysis.json"
LAYOUTS = ("A", "B", "C")
K = 8


def load_rows(path: str | Path = DEFAULT_ROWS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _dedupe(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[tuple[str, int, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("layout")), int(row.get("fanout_index", 0)), int(row.get("branch_index", 0)))
        latest[key] = row
    return list(latest.values())


def _t_crit_95(df: int) -> float:
    # Student t two-sided 95% critical values for small df (df>=1). Fallback to z.
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
             6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    if df in table:
        return table[df]
    # approximate for larger df
    return 1.96 + 2.0 / max(df, 1)


def _ci_t(values: Sequence[float]) -> tuple[float | None, float | None, float | None]:
    n = len(values)
    if n < 2:
        m = values[0] if values else None
        return m, None, None
    m = statistics.fmean(values)
    s = statistics.stdev(values)
    tc = _t_crit_95(n - 1)
    half = tc * s / math.sqrt(n)
    return m, m - half, m + half


def _fanout_totals(rows: Sequence[dict[str, Any]], layout: str) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for r in rows:
        if str(r.get("layout")) != layout:
            continue
        fi = int(r.get("fanout_index", 0))
        bucket = out.setdefault(fi, {"fanout_index": fi, "branches": [], "total_prompt": 0,
                                    "total_cached": 0, "total_uncached": 0, "n_hit": 0,
                                    "n_warm": 0, "n_warm_hit": 0})
        bucket["branches"].append(r)
        bucket["total_prompt"] += int(r.get("prompt_tokens", 0))
        bucket["total_cached"] += int(r.get("cached_tokens", 0))
        bucket["total_uncached"] += int(r.get("uncached", r.get("uncached_tokens", 0)))
        if int(r.get("cached_tokens", 0)) > 0:
            bucket["n_hit"] += 1
        if int(r.get("branch_index", 0)) >= 2:
            bucket["n_warm"] += 1
            if int(r.get("cached_tokens", 0)) > 0:
                bucket["n_warm_hit"] += 1
    for fi, b in out.items():
        nb = len(b["branches"])
        b["n_branches"] = nb
        b["hit_fraction"] = (b["n_hit"] / nb) if nb else 0.0
    return out


def analyse(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = _dedupe(rows)
    per_layout: dict[str, Any] = {}
    for L in LAYOUTS:
        ft = _fanout_totals(rows, L)
        fanouts_list = sorted(ft.values(), key=lambda b: b["fanout_index"])
        total_prompt = sum(b["total_prompt"] for b in fanouts_list)
        total_cached = sum(b["total_cached"] for b in fanouts_list)
        total_uncached = sum(b["total_uncached"] for b in fanouts_list)
        n_branches = sum(b["n_branches"] for b in fanouts_list)
        n_hit = sum(b["n_hit"] for b in fanouts_list)
        n_warm = sum(b["n_warm"] for b in fanouts_list)
        n_warm_hit = sum(b["n_warm_hit"] for b in fanouts_list)
        per_layout[L] = {
            "n_fanouts": len(fanouts_list),
            "n_branches": n_branches,
            "total_prompt_tokens": total_prompt,
            "total_cached_tokens": total_cached,
            "total_uncached_tokens": total_uncached,
            "warm_branches": (n_warm if L in ("A", "C") else 0),
            "warm_branches_hit": (n_warm_hit if L in ("A", "C") else 0),
            "warm_hit_fraction": (n_warm_hit / n_warm if (L in ("A", "C") and n_warm) else None),
            "branch_hit_fraction": (n_hit / n_branches if n_branches else 0.0),
            "per_fanout": [
                {
                    "fanout_index": b["fanout_index"],
                    "total_prompt_tokens": b["total_prompt"],
                    "total_cached_tokens": b["total_cached"],
                    "total_uncached_tokens": b["total_uncached"],
                    "n_branches": b["n_branches"],
                    "n_hit": b["n_hit"],
                    "hit_fraction": b["hit_fraction"],
                }
                for b in fanouts_list
            ],
        }

    # Per-fanout ratios (paired by fanout_index).
    a_totals = {b["fanout_index"]: b["total_uncached_tokens"] for b in per_layout["A"]["per_fanout"]}
    b_totals = {b["fanout_index"]: b["total_uncached_tokens"] for b in per_layout["B"]["per_fanout"]}
    c_totals = {b["fanout_index"]: b["total_uncached_tokens"] for b in per_layout["C"]["per_fanout"]}

    common_ab = sorted(set(a_totals) & set(b_totals))
    ratios_ba = [b_totals[i] / a_totals[i] for i in common_ab if a_totals[i] > 0]
    m_ba, lo_ba, hi_ba = _ci_t(ratios_ba)

    common_ac = sorted(set(a_totals) & set(c_totals))
    ratios_ca = [c_totals[i] / a_totals[i] for i in common_ac if a_totals[i] > 0]
    m_ca, lo_ca, hi_ca = _ci_t(ratios_ca)

    # missed after serialisation: warm branches (branch_index >= 2) with cached==0
    missed = []
    for r in rows:
        if str(r.get("layout")) in ("A", "C") and int(r.get("branch_index", 0)) >= 2 and int(r.get("cached_tokens", 0)) == 0:
            missed.append({
                "layout": r.get("layout"),
                "fanout_index": r.get("fanout_index"),
                "branch_index": r.get("branch_index"),
            })

    any_missed = len(missed) > 0

    # warm branches = branch_index >= 2 for A/C (branch 1 is the cold insert / seed)
    branch1_warm = {}
    for L in ("A", "C"):
        cnt = 0
        for fi in sorted({int(r.get("fanout_index", 0)) for r in rows if str(r.get("layout")) == L}):
            b1 = [r for r in rows if str(r.get("layout")) == L and int(r.get("fanout_index", 0)) == fi and int(r.get("branch_index", 0)) == 1]
            if b1 and int(b1[0].get("cached_tokens", 0)) > 0:
                cnt += 1
        branch1_warm[L] = cnt

    # warm probe summary from rows (last value per fanout)
    warm_probe_summary = {}
    for L in ("A", "C"):
        seen = {}
        for r in rows:
            if str(r.get("layout")) != L:
                continue
            fi = int(r.get("fanout_index", 0))
            seen[fi] = {
                "shared_prefix_resident": bool(r.get("shared_prefix_resident", False)),
                "warm_probe_cached_tokens": int(r.get("warm_probe_cached_tokens", 0)),
                "warm_probe_prompt_tokens": int(r.get("warm_probe_prompt_tokens", 0)),
            }
        warm_probe_summary[L] = seen

    n_rows = len(rows)
    result = {
        "unit": "G5",
        "n_rows": n_rows,
        "n_fanouts_per_layout": {L: per_layout[L]["n_fanouts"] for L in LAYOUTS},
        "layouts": per_layout,
        "ratios": {
            "B_over_A": {
                "fanout_indices": common_ab,
                "per_fanout": ratios_ba,
                "mean": m_ba,
                "ci95_low": lo_ba,
                "ci95_high": hi_ba,
                "method": f"t-based 95% CI, n={len(ratios_ba)}, df={len(ratios_ba)-1}",
                "ratio_of_means": (sum(b_totals[i] for i in common_ab) / sum(a_totals[i] for i in common_ab)) if common_ab and sum(a_totals[i] for i in common_ab) > 0 else None,
            },
            "C_over_A": {
                "fanout_indices": common_ac,
                "per_fanout": ratios_ca,
                "mean": m_ca,
                "ci95_low": lo_ca,
                "ci95_high": hi_ca,
                "method": f"t-based 95% CI, n={len(ratios_ca)}, df={len(ratios_ca)-1}",
                "ratio_of_means": (sum(c_totals[i] for i in common_ac) / sum(a_totals[i] for i in common_ac)) if common_ac and sum(a_totals[i] for i in common_ac) > 0 else None,
            },
        },
        "missed_after_serialisation": missed,
        "any_missed_after_serialisation": any_missed,
        "warm_probe_summary": warm_probe_summary,
        "branch1_warm_fanouts": branch1_warm,
        "g5_closed": (not any_missed and all(per_layout[L]["n_fanouts"] >= 8 for L in LAYOUTS)),
    }
    return result


def write_analysis(path: str | Path, analysis: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(DEFAULT_ROWS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    rows = load_rows(args.rows)
    analysis = analyse(rows)
    write_analysis(args.out, analysis)
    print(json.dumps({"n_rows": analysis["n_rows"], "B/A mean": analysis["ratios"]["B_over_A"]["mean"],
                      "CI": [analysis["ratios"]["B_over_A"]["ci95_low"], analysis["ratios"]["B_over_A"]["ci95_high"]],
                      "any_missed": analysis["any_missed_after_serialisation"],
                      "g5_closed": analysis["g5_closed"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
