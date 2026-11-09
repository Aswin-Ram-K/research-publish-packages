# UNIT LATENCY-REPORT — the latency half, assembled offline

**Status:** partial (deliverable complete; two quantities are not producible from these rows) · **Bound:** ≤28 tool calls · **Used:** 22 · **Requests sent: 0** · **Network: none**

## Why this unit exists

The operator's `FINAL-GOAL` (`a2b5ff2d`, board #438) asks for **p50 and p95 TTFT per turn** and **tokens-to-verified-success**
for the four arms on long runs at equal-or-better verified quality. The quality half is recorded as undecidable for the
historical grids (`MATRIX-HONESTY`, `6e839685`), but the **latency half had never been assembled at all** — and it can be,
because the rows exist. Nothing in this unit ran a cell.

## What was done

1. Inventoried every `experiments/ptr-engine/measure/rows-*.jsonl`: **%d files / %d rows** (long-run chain 10 files / 863 rows),
   sha256 per file in the report. `rows-longrun-2026-10-26.jsonl` verified still `bc61d381…`.

2. Defined the **grid** = (fixture sha256, tools on/off, harness era, arm) and invoked
   `experiments/ptr-engine/longrun/analyze_stats.py --rows <one grid> --json <out>` **once per grid** — 10 invocations — so
   its internal group-by-arm can never pool two grids that share an arm name.

3. Reported per cell: arm, grid, `n` (turn rows, stated), `requests`, p50, p95, interval or **verbatim refusal**, the
   analyser's order-statistic span, prompt/completion tokens, and mean TTFT with its own n (AD HOC, §8.4 of the report).

4. Quality per cell from `MATRIX-HONESTY`'s declared cells: denominator = the 3 truth checkpoints, because `repair.t30`
   is judge-undecidable in all 13 run/arm pairs. `measured` (13) / `undecidable` (10) / `not_graded` (1).

5. `tokens_to_verified_success` = **NOT PRODUCED** with its mechanical reason and the three conditions that would create it.

## What the rows actually say

- **24 cells / 10 grids.** p50 is licensed in **12** cells; p95 in **3** — and those three are the *single-arm* tools-on
  grids G7/G8/G9 (n = 68/72/72). **No two-arm grid clears the analyser's p95 bar**: all sit at n = 48 per arm, where
  `48·(1−0.95) = 2.4 < 3` and `quantile_ci` refuses.
- **Eight within-grid pairs** are comparable, all at p50, all with tools off, all with disjoint per-arm intervals.
- **G1 is a pure loss:** 192 turn rows across all four arms, and `ttft_ms` is null on every one (a `ttft_s` column exists on
  93). `ttft_values` reads `ttft_ms` only, so both quantiles are refused at **n = 0** for every arm. It was **not** rescued by
  hand-converting `ttft_s`.
- **The one comparison:** G4/RUN-C-V2 — grow p50 **482.24 ms** vs stable **167.02 ms**, diff −315.22 ms, intervals disjoint.
  The p95s on record (838.85 / 356.12 ms) stay *reported*, not measured: the analyser refuses that quantile at this n and
  `WIRE-CLIENT` (`orchestration/units/WIRE-CLIENT.md:16`) rules those numbers out of reuse.
- **A correction carried into the report:** the operator's note that `pointer-stable` had the higher total prompt tokens does
  **not reproduce** — in G4 grow carries 901,109 prompt tokens against stable's 104,468.

## Decisions and their reasons

- **Never pool.** One analyser invocation per grid; a pooled p95 would measure the harness history, not an arm.
- **Never hand-compute a refused quantile.** Every refusal is quoted verbatim, including its rank span, instead of a number.
- **Do not convert `ttft_s` → `ttft_ms`** to rescue G1: that is an AD HOC quantile wearing the analyser's authority.
- **Quality denominator:** exclude `repair.t30` everywhere (judge-undecidable in all 13 pairs), use the 3 truth checkpoints,
  and mark every `measured` cell `full_run: false` / PARTIAL GRID. No cell claims `measured` without printing its denominator.
- **No substitute metric** for `tokens_to_verified_success`; tokens-per-checkpoint and tokens-per-decidable-checkpoint are
  different quantities and naming one of them the operator's metric is the defect this report exists to prevent.

## Write paths (exactly)

`docs/LATENCY-REPORT.md` · `experiments/ptr-engine/measure/LATENCY-REPORT.json` · `orchestration/units/LATENCY-REPORT.md` ·
`orchestration/handoffs/LATENCY-REPORT.json` · `orchestration/journals/LATENCY-REPORT.jsonl`. No row file, grade file,
fixture, `cell.py`, `run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`, `fixture_coverage.py`, `matrix_audit.py`,
`handoff_lint.py` or `det_verify.py` was written.

## Remainder (why partial)

`tokens_to_verified_success` cannot exist on this corpus (zero denominator in every grid); no within-grid p95 pair exists at
n = 48; the tools-on dimension is **single-arm** because `transcript-grow` was never run with tools on. §7 of the report lists
what the next cell must record (n ≥ 60 per arm in one grid, tools-on grow, `ttft_ms` + `ttft_source` on every row, one
`max_tokens` and one fixture per file, decidable `repair.t30`, and a quantile-difference routine in the analyser).

