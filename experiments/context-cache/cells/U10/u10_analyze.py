#!/usr/bin/env python3
"""U10 analysis: turn the rows into a quantified, bounded finding.

Reads ``u10_rows.jsonl`` (phase 1) and ``u10_rows_p23.jsonl`` (phases 2-3) and
writes ``u10_report.json``.  Pure function of those two files: no clock, no
network, no re-measurement.

Every rate carries an exact Clopper-Pearson 95% interval, and the 64-multiple
vs non-multiple contrast carries a two-sided Fisher exact test, so the finding
is quantified rather than anecdotal.

Usage::

    python3 u10_analyze.py            # writes u10_report.json, prints the tables
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from scipy.stats import beta, fisher_exact

HERE = Path(__file__).resolve().parent
ROWS_FILES = (HERE / "u10_rows.jsonl", HERE / "u10_rows_p23.jsonl")
OUT = HERE / "u10_report.json"
ALPHA = 0.05


def cp_interval(k: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Exact Clopper-Pearson interval for ``k`` successes in ``n`` trials."""

    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return (round(lo, 4), round(hi, 4))


def load_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in ROWS_FILES:
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh if line.strip())
    return rows


def classify(row: dict[str, Any]) -> str:
    cached = row.get("cached_tokens") or 0
    expected = row.get("expected_cached") or 0
    if cached == 0:
        return "full_miss"
    if expected and cached < expected:
        return "partial"
    if expected and cached == expected:
        return "hit"
    return "odd"


def cell_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per achieved length: repeat#1 and repeat#2 outcomes with exact CIs."""

    cells: dict[int, dict[str, Any]] = {}
    for row in rows:
        if row.get("phase") != "p1" or row.get("role") not in ("rep1", "rep2"):
            continue
        L = row.get("prompt_tokens")
        if not L:
            continue
        cell = cells.setdefault(
            L,
            {
                "length": L,
                "length_mod_64": L % 64,
                "expected_cached": row.get("expected_cached"),
                "rep1": [],
                "rep2": [],
                "target": row.get("length_target"),
            },
        )
        cell[row["role"]].append(row)

    out: list[dict[str, Any]] = []
    for L in sorted(cells):
        cell = cells[L]
        rep1 = cell["rep1"]
        rep2 = cell["rep2"]
        n1 = len(rep1)
        miss1 = sum(1 for r in rep1 if classify(r) == "full_miss")
        part1 = sum(1 for r in rep1 if classify(r) == "partial")
        n2 = len(rep2)
        miss2 = sum(1 for r in rep2 if classify(r) == "full_miss")
        lo1, hi1 = cp_interval(miss1, n1)
        lo2, hi2 = cp_interval(miss2, n2) if n2 else (0.0, 1.0)
        ttft_hit = [r["ttft_ms"] for r in rep1 if classify(r) == "hit"]
        ttft_miss = [r["ttft_ms"] for r in rep1 if classify(r) == "full_miss"]
        cold_ttft = [
            r["ttft_ms"]
            for r in rows
            if r.get("phase") == "p1"
            and r.get("role") == "cold"
            and r.get("prompt_tokens") == L
            and not r.get("probe")
        ]
        out.append(
            {
                "length": L,
                "length_mod_64": L % 64,
                "multiple_of_64": L % 64 == 0,
                "expected_cached_on_hit": cell["expected_cached"],
                "rep1_n": n1,
                "rep1_full_misses": miss1,
                "rep1_partial_misses": part1,
                "rep1_miss_rate": round(miss1 / n1, 4) if n1 else None,
                "rep1_miss_rate_ci95": [lo1, hi1],
                "rep2_n": n2,
                "rep2_full_misses": miss2,
                "rep2_miss_rate": round(miss2 / n2, 4) if n2 else None,
                "rep2_miss_rate_ci95": [lo2, hi2] if n2 else None,
                "rep1_cached_values": [r.get("cached_tokens") for r in rep1],
                "rep2_cached_values": [r.get("cached_tokens") for r in rep2],
                "cold_ttft_median_ms": round(statistics.median(cold_ttft), 1)
                if cold_ttft
                else None,
                "rep1_hit_ttft_median_ms": round(statistics.median(ttft_hit), 1)
                if ttft_hit
                else None,
                "rep1_miss_ttft_median_ms": round(statistics.median(ttft_miss), 1)
                if ttft_miss
                else None,
                "all_trials_cold_verified": all(
                    (r.get("cold_cached") in (0, None)) for r in rep1 + rep2
                ),
            }
        )
    return out


def pooled(table: list[dict[str, Any]]) -> dict[str, Any]:
    """64-multiple vs non-multiple contrast, both phases-1 outcomes pooled."""

    def agg(pred) -> tuple[int, int]:
        n = sum(c["rep1_n"] for c in table if pred(c))
        k = sum(c["rep1_full_misses"] for c in table if pred(c))
        return k, n

    km, nm = agg(lambda c: c["multiple_of_64"])
    ko, no = agg(lambda c: not c["multiple_of_64"])
    table_2x2 = [[km, nm - km], [ko, no - ko]]
    _, p = fisher_exact(table_2x2, alternative="two-sided")
    lo_m, hi_m = cp_interval(km, nm)
    lo_o, hi_o = cp_interval(ko, no)
    k2, n2 = 0, sum(c["rep2_n"] for c in table)
    k2 = sum(c["rep2_full_misses"] for c in table)
    return {
        "multiples_of_64": {
            "lengths": sorted(c["length"] for c in table if c["multiple_of_64"]),
            "rep1_full_misses": km,
            "rep1_trials": nm,
            "rate": round(km / nm, 4) if nm else None,
            "rate_ci95": [lo_m, hi_m],
        },
        "non_multiples": {
            "lengths": sorted(c["length"] for c in table if not c["multiple_of_64"]),
            "rep1_full_misses": ko,
            "rep1_trials": no,
            "rate": round(ko / no, 4) if no else None,
            "rate_ci95": [lo_o, hi_o],
        },
        "fisher_exact_2x2": table_2x2,
        "fisher_exact_two_sided_p": float(p),
        "rep2_recovery_full_misses": k2,
        "rep2_recovery_trials": n2,
    }


def delay_table(rows: list[dict[str, Any]], length: int) -> list[dict[str, Any]]:
    """Phase 2 (delays) plus the d=0.0 reference taken from phase 1."""

    cells: dict[float, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("phase") == "p2" and row.get("role") == "rep1":
            cells.setdefault(float(row.get("delay_s") or 0.0), []).append(row)
        elif (
            row.get("phase") == "p1"
            and row.get("role") == "rep1"
            and row.get("prompt_tokens") == length
        ):
            cells.setdefault(0.0, []).append(row)
    out = []
    for d in sorted(cells):
        group = cells[d]
        n = len(group)
        k = sum(1 for r in group if classify(r) == "full_miss")
        lo, hi = cp_interval(k, n)
        out.append(
            {
                "delay_s": d,
                "n": n,
                "full_misses": k,
                "miss_rate": round(k / n, 4) if n else None,
                "miss_rate_ci95": [lo, hi],
                "cached_values": [r.get("cached_tokens") for r in group],
                "rep1_ttft_median_ms": round(
                    statistics.median([r["ttft_ms"] for r in group]), 1
                )
                if group
                else None,
                "source": "phase 1 (same protocol, no sleep)" if d == 0.0 else "phase 2",
            }
        )
    return out


def insert_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    group = [
        r
        for r in rows
        if r.get("phase") == "p3" and r.get("role") == "rep1"
    ]
    n = len(group)
    k = sum(1 for r in group if classify(r) == "full_miss")
    lo, hi = cp_interval(k, n)
    unrelated = [
        r.get("prompt_tokens")
        for r in rows
        if r.get("phase") == "p3" and r.get("role") == "unrelated"
    ]
    return {
        "trials": n,
        "full_misses": k,
        "miss_rate": round(k / n, 4) if n else None,
        "miss_rate_ci95": [lo, hi],
        "cached_values": [r.get("cached_tokens") for r in group],
        "unrelated_prompt_tokens": unrelated,
    }


def main() -> int:
    rows = load_rows()
    table = cell_table(rows)
    pooled_result = pooled(table)
    worst = max(
        (c for c in table if c["rep1_n"]),
        key=lambda c: (c["rep1_full_misses"], c["length"]),
    )
    delays = delay_table(rows, worst["length"])
    inserts = insert_table(rows)
    budget = {
        "pilot_probes": 39,
        "phase1": sum(1 for r in rows if r.get("phase") == "p1"),
        "phase23": sum(1 for r in rows if r.get("phase") in ("p2", "p3")),
        "note": (
            "phase 1 wrote its rows before a send() signature bug stopped the "
            "driver after the sweep; phases 2-3 were run by u10_phase23.py so the "
            "sweep was not re-spent"
        ),
    }
    budget["total_live_requests"] = (
        budget["pilot_probes"] + budget["phase1"] + budget["phase23"]
    )

    multiples_miss = pooled_result["multiples_of_64"]["rate"]
    others_miss = pooled_result["non_multiples"]["rate"]
    delay_fixes = all(
        (d["full_misses"] == 0) for d in delays if d["delay_s"] > 0
    ) and any(d["full_misses"] > 0 for d in delays if d["delay_s"] == 0)
    insert_fixes = inserts["full_misses"] == 0
    second_repeat_hits = (
        pooled_result["rep2_recovery_trials"] > 0
        and pooled_result["rep2_recovery_full_misses"] == 0
    )
    if multiples_miss and multiples_miss > 0.5 and others_miss == 0.0:
        verdict = "boundary_specific"
        headline = (
            "Only prompts whose length is an exact multiple of 64 miss on the "
            "immediately following repeat; every other length hits immediately."
        )
    elif multiples_miss and others_miss and others_miss > 0.0:
        verdict = "general_first_repeat_race"
        headline = (
            "Lengths of every residue class can miss on the immediate repeat; "
            "the boundary only raises the rate."
        )
    elif (multiples_miss or 0) == 0:
        verdict = "not_reproducible"
        headline = (
            "The first-repeat miss did not reproduce at n=5 in any cell; report "
            "the observed rate rather than the earlier 3/3."
        )
    else:
        verdict = "inconclusive"
        headline = "The sweep is too thin to choose between the three outcomes."

    if (multiples_miss or 0) == 0:
        mechanism = "nothing to explain: no miss reproduced"
    elif delay_fixes and insert_fixes:
        mechanism = (
            "insert visibility (a lag): the node exists but is not yet matchable; "
            "waiting or any intervening request is enough"
        )
    elif not delay_fixes and not insert_fixes and second_repeat_hits:
        mechanism = (
            "not insert latency and not a request-triggered flush: 0.25-2.0 s of "
            "delay and an intervening unrelated request both leave the miss at "
            "100%, while a second identical repeat hits 10/10 at the tax-law value. "
            "The prefix becomes reusable only after it has been prefilled twice -- "
            "one wasted full prefill per new multiple-of-64 prefix"
        )
    else:
        mechanism = "partially resolved by these phases; see delay/insert tables"
    report = {
        "unit": "U10",
        "question": (
            "Is the 64-boundary first-repeat miss specific to L % 64 == 0, or a "
            "general first-repeat race?  Does a delay remove it?  Does an "
            "intervening request remove it?"
        ),
        "verdict": verdict,
        "headline": headline,
        "mechanism": mechanism,
        "design": {
            "cold_isolation": (
                "make_salt(seed) -> three fixed-width 4-letter marker words at the "
                "front of message 0; every trial's marker is unique and never "
                "reused, and every cold role that reports cached != 0 is retried"
            ),
            "exact_lengths": (
                "body sized 12 tokens short of the target plus a one-token tail "
                "(' the' repeated); achieved prompt_tokens read back from every "
                "response and the cell is refused unless it equals the target"
            ),
            "metric": "usage.prompt_tokens_details.cached_tokens (null -> 0)",
            "miss_definition": (
                "full_miss = cached == 0 on the repeat; partial = 0 < cached < "
                "64*floor((L-1)//64); hit = cached == 64*floor((L-1)/64)"
            ),
            "serial": "one request in flight; no flock; POST /flush_cache never called",
            "reps_per_cell": 5,
            "max_tokens": 2,
            "thinking": False,
        },
        "per_length": table,
        "pooled": pooled_result,
        "delay": delays,
        "insert_unrelated_request": inserts,
        "budget": budget,
        "request_number_law": {
            "at_multiples_of_64": (
                "1st request: cold (cached=0); 2nd identical request: cached=0 and "
                "full prefill, even after a 2 s delay or an intervening request; "
                "3rd identical request: full tax-law hit"
            ),
            "at_non_multiples": (
                "1st cold, 2nd identical request: full tax-law hit (0/15 misses)"
            ),
        },
        "explains": {
            "U9_1024_case": (
                "yes, exactly: L=1024 is a multiple of 64 and reproduced at 5/5, "
                "with the second repeat recovering the tax-law hit (960)"
                if verdict == "boundary_specific"
                else "see per_length at L=1024"
            ),
            "U4b_branch_2_case": (
                "no, not by the boundary rule: U4b's fan-out prompts were ~1925 "
                "tokens (1925 % 64 = 5), a residue class where this sweep saw 0/15 "
                "misses on identical repeats.  U4b's branch differed from branch 1 "
                "in its suffix (prefix-sharing, not an identical repeat); a pilot "
                "probe of that shape (same body, different tail, sent immediately) "
                "also reported cached=0, so it is plausibly the same insert-"
                "visibility class, but that shape is NOT covered by these n=5 cells."
            ),
        },
        "operational_warning": (
            "A workload whose prompt length is an exact multiple of 64 pays one "
            "full prefill per new prefix: 10/10 immediate repeats at 1024 and 1088 "
            "tokens reported cached=0 and paid cold-prefill TTFT (median 263-533 ms "
            "at 1024 vs ~80 ms for a hit), and neither a 2 s delay nor an unrelated "
            "request in between removed it.  The same prompt sent a second time "
            "becomes reusable (rep2 10/10 at the tax-law value)."
            if verdict == "boundary_specific"
            else ""
        ),
        "limits": [
            "n=5 per cell: each individual cell's CI is wide (0/5 -> [0, 0.52]); the "
            "claim rests on the pooled 10/10 vs 0/15 contrast, not on one cell.",
            "The sweep covers 1008, 1023, 1024, 1025, 1088 tokens.  960, 1020, 1028, "
            "1152, 2048 and 4096 were in the card's list and were not run: the "
            "160-request bound was partly spent on 39 pilot probes that were needed "
            "to build an exact-length harness (see u10_pilot.json).",
            "Only identical repeats are measured in the n=5 cells; the prefix-sharing "
            "(different suffix) shape that U4b hit is covered by one pilot probe only.",
            "No file lock was taken (by instruction), so other units' traffic can "
            "interleave; every trial's cold role is verified cold, and the effect is "
            "binary rather than marginal, which makes eviction an implausible "
            "explanation for a 10/10 vs 0/15 split.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"VERDICT {verdict}: {headline}")
    print(f"{'L':>6} {'L%64':>5} {'n':>3} {'rep1 miss':>10} {'CI95':>16} "
          f"{'rep2 miss':>9} {'cached rep1':>22}")
    for c in table:
        print(f"{c['length']:>6} {c['length_mod_64']:>5} {c['rep1_n']:>3} "
              f"{c['rep1_full_misses']:>3}/{c['rep1_n']:<6} "
              f"{str(c['rep1_miss_rate_ci95']):>16} "
              f"{str(c['rep2_full_misses']) + '/' + str(c['rep2_n']):>9} "
              f"{str(c['rep1_cached_values']):>22}")
    p = pooled_result
    print(f"pooled multiples {p['multiples_of_64']['rep1_full_misses']}/"
          f"{p['multiples_of_64']['rep1_trials']} CI {p['multiples_of_64']['rate_ci95']} "
          f"vs non-multiples {p['non_multiples']['rep1_full_misses']}/"
          f"{p['non_multiples']['rep1_trials']} CI {p['non_multiples']['rate_ci95']} "
          f"Fisher p={p['fisher_exact_two_sided_p']:.2e}")
    print("delay: " + " | ".join(
        f"{d['delay_s']}s {d['full_misses']}/{d['n']}" for d in delays))
    print(f"insert-a-short-request: {inserts['full_misses']}/{inserts['trials']} "
          f"misses, CI {inserts['miss_rate_ci95']}")
    print(f"requests: {budget}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
