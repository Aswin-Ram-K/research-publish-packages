# UNIT GRID-STAMP-WIRING

**Card:** fa4f3fd0-b961-413f-8d0e-b54a2d3a1e55 · **Execution:** 51cde27a-3824-42ef-a309-7eef19f85877
**Bound:** <=24 tool calls · **Mode:** automated, OFFLINE (`--dry-run` only, /tmp fixtures, 0 requests)

## Objective
Settle whether the grid launcher (`experiments/ptr-engine/tools/run_a_star.py`) stamps each
cell's `usable_for`; wire it through the existing helper if not; and make an unstamped
previous cell REFUSE the next launch rather than be included.

## Why
`analyze_stats.py:749` (`excluded = analyses is not None and len(analyses) == 0`) is False
when `usable_for` is absent, so an unstamped cell is INCLUDED in every comparison.
`analyze_stats.py:1753` prints it as `unstamped ... (included)`. `cell.py` is frozen, so the
writer already lives beside the consumer: `analyze_stats.write_cell_manifest_usable_for`
(`:777`). RUN-A-STAR-2 made stamping prose; this unit turns it into a mechanism.

## Do this
1. Read `run_a_star.py`, answer `stamped` / `not-stamped` / `stamped-but-only-on-success` with `file:line`.
2. Build one `/tmp` manifest WITH `usable_for: []` and one WITHOUT the key; show which `analyze_stats` excludes.
3. If not wired, call the existing helper (never reimplement; never edit `analyze_stats.py`, `cell.py`, `run_longrun.py`).
4. Refuse to start the next cell when the previous manifest lacks the key (non-zero + manifest path).
5. Tests `tests/test_grid_stamp_wiring.py`, >=6 cases incl. red->green and dry-run 0 requests.
6. Name the residual (hand-launched cell bypasses the stamp) for `docs/GRID-RUNBOOK.md`; do not edit the runbook.

## Write paths
`experiments/ptr-engine/tools/run_a_star.py` · `tests/test_grid_stamp_wiring.py` ·
`experiments/ptr-engine/measure/GRID-STAMP-WIRING.json` · `orchestration/units/GRID-STAMP-WIRING.md` ·
`orchestration/handoffs/GRID-STAMP-WIRING.json` · `orchestration/journals/GRID-STAMP-WIRING.jsonl`

## Result
`not-stamped` before the card. Now: complete cell -> `['h1','h2','h3']` + reason; abandoned /
zero-marker / stop_reason-degenerate -> `[]` + the condition; unstamped previous manifest ->
`SystemExit(4)` naming the path. 10 tests green, 0 requests.
