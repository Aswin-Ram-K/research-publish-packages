# UNIT GRID-GAP-DIAG — classify the three GRID-RUN-2 gaps, repair only layer A

**Card:** ee6448b3-eeac-4b6a-adc4-a51ab1720d70 · **Execution:** 4b67552c · **Bound:** 30 tool calls
**Objective.** Before repairing, name the layer (A cell.py / B pinned / C record) for each of the
three GRID-RUN-2 failures, state the gen-7 arithmetic, then repair only what is inside the write paths.

**Result.** Classification done; one repair (rows_path join, layer A, no generation).
Transcript-treatment gap = (B) fixture-design defect (wall priced from declared padding, unreachable
at 48 turns) → v9 → gen 7. `exit 4` = (B) pinned runner projection under-counts billed `turn-initial`
requests. Verdict: `GEN7_REQUIRED_AND_GRID_UNAFFORDABLE`.

**Write paths.** `experiments/ptr-engine/longrun/cell.py`,
`experiments/ptr-engine/tests/test_grid_gap_fix.py`, `docs/GRID-GAP-DIAGNOSIS.md`, this card, handoff,
journal. **Forbidden paths untouched:** run_longrun.py, client.py, analyze_stats.py, grade_v5.py,
fixture, rows, HARNESS-PIN.json, GRID-PARAMS.json, REQUEST-LEDGER.json, baselines, grades, pages,
run_a_star.py.

**Red→green.** 3 failed / 1 passed before the cell.py helper; 4 passed after. The one that passes
before is the defect pin (nested-only record is dropped by the pinned reader).
