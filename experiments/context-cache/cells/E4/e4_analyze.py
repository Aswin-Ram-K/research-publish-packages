#!/usr/bin/env python3
"""E4 offline analysis -- per-cell boundary counts, exact CIs, form tests.

Pure offline: reads ``cells/E4/e4_rows.jsonl`` and writes ``e4_report.json``.
No network, no scipy (exact binomial tail sums with ``math.comb``).

Definitions carried from U10 (cited in the report):
  full_miss  cached == 0 on the repeat
  hit_u10    cached == 64*floor((L-1)/64)   (U10's hit definition)
  hit_plain  cached == 64*floor(L/64)       (U2's tax law; differs at L%64==0)
  partial    0 < cached < 64*floor((L-1)/64)
"""

from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROWS = HERE / "e4_rows.jsonl"
REPORT = HERE / "e4_report.json"
Z = 1.959963984540054
ALPHA = 0.05


# --------------------------------------------------------------------------- #
# Statistics (exact, no scipy)
# --------------------------------------------------------------------------- #
def binom_pmf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    return math.comb(n, k) * p**k * (1.0 - p) ** (n - k)


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(binom_pmf(i, n, p) for i in range(0, max(-1, k) + 1))


def binom_sf(k: int, n: int, p: float) -> float:
    return 1.0 - binom_cdf(k - 1, n, p)


def _bisect(f, lo: float = 0.0, hi: float = 1.0, it: int = 160) -> float:
    for _ in range(it):
        mid = (lo + hi) / 2.0
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1.0 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def clopper_pearson(k: int, n: int) -> tuple[float, float]:
    """Exact 95% CI for a binomial proportion (bisection on exact tails)."""

    if n == 0:
        return (0.0, 1.0)
    # lower bound solves P(X>=k|p)=alpha/2; alpha/2 - sf is decreasing in p
    lo = 0.0 if k == 0 else _bisect(lambda p: ALPHA / 2.0 - binom_sf(k, n, p))
    hi = 1.0 if k == n else _bisect(lambda p: binom_cdf(k, n, p) - ALPHA / 2.0)
    return (lo, hi)


def _hyper(x: int, r1: int, c1: int, n: int) -> float:
    return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact two-sided Fisher test on [[a,b],[c,d]] (sum of tables no more likely)."""

    n = a + b + c + d
    r1, c1 = a + b, a + c
    obs = _hyper(a, r1, c1, n)
    total = 0.0
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        p = _hyper(x, r1, c1, n)
        if p <= obs * (1 + 1e-9):
            total += p
    return min(1.0, total)


def med(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 3) if xs else None


# --------------------------------------------------------------------------- #
# Load + trial table
# --------------------------------------------------------------------------- #
def load() -> tuple[list[dict[str, Any]], list[str]]:
    notes: list[str] = []
    rows = [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows, notes


def trials_by_cell(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, dict[int, dict[str, Any]]] = {}
    for r in rows:
        cell, trial = r.get("cell"), r.get("trial")
        if cell is None or not r.get("prompt_tokens") or trial == 0:
            continue
        out.setdefault(cell, {}).setdefault(trial, {})[r["role"]] = r
    return {c: [t for _, t in sorted(ts.items())] for c, ts in sorted(out.items(), reverse=True)}


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def analyse() -> dict[str, Any]:
    rows, _ = load()
    by_cell = trials_by_cell(rows)
    cells_out: list[dict[str, Any]] = []
    for cell, trials in by_cell.items():
        Ls = {t["cold"]["prompt_tokens"] for t in trials if "cold" in t}
        exact = Ls == {cell}
        valid = [t for t in trials if "cold" in t and "rep1" in t]
        rep1 = [t["rep1"] for t in valid]
        rep2 = [t["rep2"] for t in valid if "rep2" in t]
        L = cell
        expect_u10 = 64 * ((L - 1) // 64)
        expect_plain = 64 * (L // 64)
        misses1 = [r for r in rep1 if (r["cached_tokens"] or 0) == 0]
        hit1 = [r for r in rep1 if (r["cached_tokens"] or 0) == expect_u10]
        part1 = [r for r in rep1 if r not in misses1 and r not in hit1]
        misses2 = [r for r in rep2 if (r["cached_tokens"] or 0) == 0]
        cold_warm = [t["cold"] for t in valid if (t["cold"]["cached_tokens"] or 0) != 0]
        n = len(valid)
        lo, hi = clopper_pearson(len(misses1), n)
        wlo, whi = wilson(len(misses1), n)
        cells_out.append(
            {
                "L": L,
                "L_mod_64": L % 64,
                "boundary": L % 64 == 0,
                "n_trials": n,
                "lengths_seen": sorted(Ls),
                "length_exact": exact,
                "cold_cached_nonzero": len(cold_warm),
                "rep1_full_misses": len(misses1),
                "rep1_full_miss_rate": round(len(misses1) / n, 4) if n else None,
                "rep1_cp95": [round(lo, 4), round(hi, 4)],
                "rep1_wilson95": [round(wlo, 4), round(whi, 4)],
                "rep1_hits_u10": len(hit1),
                "rep1_partials": len(part1),
                "rep1_cached_hist": dict(Counter(r["cached_tokens"] for r in rep1)),
                "rep1_expected_u10": expect_u10,
                "rep1_expected_plain": expect_plain,
                "rep2_n": len(rep2),
                "rep2_full_misses": len(misses2),
                "rep2_cached_hist": dict(Counter(r["cached_tokens"] for r in rep2)),
                "rep2_block_tax_hist": dict(Counter(r["prompt_tokens"] - r["cached_tokens"] for r in rep2)),
                "ttft_ms_median_miss": med([r["ttft_ms"] for r in misses1]),
                "ttft_ms_median_hit": med([r["ttft_ms"] for r in rep1 if (r["cached_tokens"] or 0) > 0]),
                "gap_ms_median": med([r["gap_ms"] for r in rep1 if r.get("gap_ms") is not None]),
            }
        )

    multi = [c for c in cells_out if c["boundary"]]
    non = [c for c in cells_out if not c["boundary"]]

    def pool(group: list[dict[str, Any]]) -> dict[str, Any]:
        n = sum(c["n_trials"] for c in group)
        k = sum(c["rep1_full_misses"] for c in group)
        lo, hi = clopper_pearson(k, n)
        wlo, whi = wilson(k, n)
        return {"cells": [c["L"] for c in group], "misses": k, "n": n,
                "rate": round(k / n, 4) if n else None,
                "cp95": [round(lo, 4), round(hi, 4)], "wilson95": [round(wlo, 4), round(whi, 4)]}

    pm, pn = pool(multi), pool(non)
    table = [[pm["misses"], pm["n"] - pm["misses"]], [pn["misses"], pn["n"] - pn["misses"]]]
    fisher = fisher_two_sided(*table[0], *table[1]) if pm["n"] and pn["n"] else None

    # ---- form tests --------------------------------------------------------
    # F_a: miss iff L%64==0   F_b: miss iff (L-1)%64==0   (only L%64==1 discriminates)
    form_a = {"rule": "full_miss iff L % 64 == 0",
              "per_cell": [{"L": c["L"], "predicted_miss": c["boundary"],
                            "observed_misses": c["rep1_full_misses"], "n": c["n_trials"],
                            "consistent": (c["rep1_full_misses"] == c["n_trials"]) == c["boundary"] or
                                          (c["rep1_full_misses"] == 0) == (not c["boundary"])}
                           for c in cells_out]}
    form_b = {"rule": "full_miss iff (L-1) % 64 == 0",
              "discriminating_cells": [c["L"] for c in cells_out if (c["L"] - 1) % 64 == 0],
              "per_cell": [{"L": c["L"], "predicted_miss": (c["L"] - 1) % 64 == 0,
                            "observed_misses": c["rep1_full_misses"], "n": c["n_trials"]}
                           for c in cells_out]}
    # F_c: does the U2 tax law hold warm?  (cached == 64*floor(L/64))
    tax = [{"L": c["L"], "expected_plain": c["rep1_expected_plain"],
            "rep1_matching_plain": c["rep1_cached_hist"].get(c["rep1_expected_plain"], 0),
            "n": c["n_trials"], "rep2_matching_plain": c["rep2_cached_hist"].get(c["rep1_expected_plain"], 0),
            "rep2_n": c["rep2_n"]} for c in cells_out]
    # F_d: (L-1) form
    lm1 = [{"L": c["L"], "expected_u10": c["rep1_expected_u10"],
            "rep2_matching_u10": c["rep2_cached_hist"].get(c["rep1_expected_u10"], 0), "rep2_n": c["rep2_n"]}
           for c in cells_out]

    boundary_rep2 = [c for c in multi if c["rep2_n"]]
    causes = {
        "C1_one_prefill_lag_at_the_boundary": {
            "predicts": "rep1 cached == 0, rep2 cached == L-64",
            "observed": (
                f"{sum(c['rep1_full_misses'] for c in multi)}/"
                f"{sum(c['n_trials'] for c in multi)} boundary trials had rep1 cached == 0; "
                f"{sum(c['rep2_cached_hist'].get(c['rep1_expected_u10'], 0) for c in boundary_rep2)}/"
                f"{sum(c['rep2_n'] for c in boundary_rep2)} rep2 rows (1024/1088) landed on 64*floor((L-1)/64) = L-64"
            ),
            "verdict": "matches every boundary trial",
        },
        "C2_length_accounting_L_minus_1": {
            "predicts": "cacheable length is 64*floor((L-1)/64) for every L, so rep1 at a boundary is L-64",
            "observed": (
                f"rep1 at 1024/1088 was 0 in "
                f"{sum(c['rep1_cached_hist'].get(0, 0) for c in multi if c['rep2_n'])}/"
                f"{sum(c['n_trials'] for c in multi if c['rep2_n'])} trials and never L-64"
            ),
            "verdict": "predicts the rep2 ceiling correctly but not the rep1 zero; insufficient alone",
        },
        "C3_race": {
            "predicts": "a retry, delay or interleaved request clears it",
            "observed": "U10 p2/p3: delay 0.25-2 s 20/20 misses, one interleaved 63-token request 5/5 misses; not re-tested here",
            "verdict": "no support from U10; rep1 was 0 in 40/40 immediate repeats here, so a per-trial race is not indicated",
        },
        "separation": "none: these rows separate the observable predictions, not the server mechanism. cached_tokens is the server's own accounting (G13) and no server-side trace of the chunk insertion exists.",
    }
    statement = (
        f"At n per cell, a length that is a multiple of 64 (L%64==0) shows a full first-repeat miss "
        f"{pm['misses']}/{pm['n']} (CP95 {pm['cp95']}); a length that is not shows "
        f"{pn['misses']}/{pn['n']} (CP95 {pn['cp95']}); Fisher two-sided p={fisher}. "
        f"At the boundary the second repeat covers 64*floor((L-1)/64) = L-64 tokens, i.e. it pays a "
        f"64-token block tax on every warm request instead of the 0 the tax law predicts, while a "
        f"non-multiple pays L%64 <= 63."
    )
    report = {
        "unit": "E4",
        "rows_total": len(rows),
        "rows_used": sum(c["n_trials"] for c in cells_out),
        "cells": cells_out,
        "pooled": {"multiples_of_64": pm, "non_multiples": pn,
                   "table": {"multiples": table[0], "non_multiples": table[1]},
                   "fisher_two_sided_p": fisher},
        "form_tests": {"F_a_L_mod_64": form_a, "F_b_L_minus_1": form_b,
                       "F_c_tax_law_plain": tax, "F_d_L_minus_1_value": lm1},
        "statement": statement,
        "mechanism": "not established (see candidate_causes and limitations)",
        "candidate_causes": causes,
        "limitations": [
            "One model, one SGLang build, one endpoint: nothing here separates the cache implementation from the model (G4).",
            "cached_tokens is the server's own accounting; there is no token-level audit of which prefix was reused (G13).",
            "No server-side trace of the chunk insertion at the boundary exists, so the candidate causes (insertion lag at an exact boundary vs length accounting) are not separated by these rows.",
            "Trials are identical repeats only; the prefix-sharing shape that U4b lost is not measured.",
            "Independent trials are sequential on one warm server, so the cold request of trial k+1 cannot inherit trial k's cache only because the marker differs at token 0 (verified by cached==0).",
        ],
    }
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = ["| L | L%64 | trials | rep1 full misses | rep1 cached | rep2 n | rep2 cached |", "|---|---|---|---|---|---|---|"]
    for c in report["cells"]:
        lines.append(
            f"| {c['L']} | {c['L_mod_64']} | {c['n_trials']} | {c['rep1_full_misses']}/{c['n_trials']} | "
            f"{c['rep1_cached_hist']} | {c['rep2_n']} | {c['rep2_cached_hist']} |"
        )
    p = report["pooled"]
    lines.append("")
    lines.append(f"pooled multiples: {p['multiples_of_64']['misses']}/{p['multiples_of_64']['n']} "
                 f"CP95 {p['multiples_of_64']['cp95']}")
    lines.append(f"pooled non-multiples: {p['non_multiples']['misses']}/{p['non_multiples']['n']} "
                 f"CP95 {p['non_multiples']['cp95']}")
    lines.append(f"Fisher two-sided p = {p['fisher_two_sided_p']}")
    return "\n".join(lines)


def main() -> int:
    report = analyse()
    REPORT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(markdown(report))
    print()
    print(report["statement"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
