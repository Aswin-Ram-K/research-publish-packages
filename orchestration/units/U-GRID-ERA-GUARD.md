# U-GRID-ERA-GUARD — make era mixing impossible to print, and prove it

**Card:** `059b2049-3ea3-4a32-86cc-4b0d3d0f2375` · **Execution:** `b19daa1b-cdc2-4520-9a02-8b55397771e4`
**Input:** `orchestration/handoffs/V-GRID-REPORT.json` (`emitter_unsound`, attempt 4).
**Bound:** 28 tool calls. **Offline:** 0 requests.

## Purpose

`V-GRID-REPORT` attempt 4 fed the grid report two eras (fixture `sha256` v7 and v8). H1 split
them correctly; H2 still printed `ratio **2.5000**`, TVS printed `100800.0`, and `refusals`
was `[]`. Era A is degeneration-confounded (`GRID-SHAPE-TOOLS`), era B is the first
comparable grid — a pooled number over both is not a measurement.

## Contract

1. Reproduce attempt 4 and quote the printed line; if unreproducible, say so.
2. Fix the cause **at the layer that prints**: a pooled term may print a number only for cells
   whose declared provenance agrees. A mixed set produces a **named refusal**
   (`refused_mixed_era`) naming each era present and the cell that introduced it, and prints
   no interval, no accuracy, no `n`.
3. Keep every existing refusal (absent `usable_for`, `usable_for: []`, `stop_reason=length`,
   `n_eff` floor, decidable < 8/12, zero-answer arm, no verified success). Re-run the
   attacker's eight cases: all classify as before **except** 4, which must move to
   `refused_correctly`.
4. Do not weaken a threshold; do not touch `analyze_stats.py`, `grade_v5.py`, `cell.py`,
   `run_longrun.py`, any fixture, row, or published page.
5. Tests: one per refusal path touched, each with a quoted red→green; a single-era report
   still prints its numbers; a mixed set made by **concatenating** two single-era rows files
   is refused.
6. Verdict row before the handoff, absolute interpreter path.

## Write paths

`experiments/ptr-engine/tools/run_grid_report.py` ·
`experiments/ptr-engine/tests/test_grid_report_era_guard.py` (new) ·
`docs/GRID-REPORT-ERA-GUARD.md` (new) · this card · `orchestration/handoffs/U-GRID-ERA-GUARD.json` ·
`orchestration/journals/U-GRID-ERA-GUARD.jsonl`

## Result

`done`. Gate added before H2/TVS/verbosity (`mixed_provenance`); `REFUSAL_MIXED_ERA` is a
first-class refusal row; unknown load-bearing fields are non-poolable too. 7 new tests + the
13 pre-existing report tests green; attempt 4 moved from printed-number to `refused_correctly`;
the seven other attacker cases classify as before. `tests/tmp` scratch only — no fixture, row
or page touched.
