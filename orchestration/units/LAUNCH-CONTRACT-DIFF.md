# LAUNCH-CONTRACT-DIFF

**Placement:** unit card (persisted by the unit, per AGENTS.md unit contract).
**Purpose:** one table of every number the launch depends on, every place it appears,
and every disagreement between them — before the grid spends 1,016 requests on a contradiction.
**Bound:** 26 tool calls; offline (0 requests, 0 network); no source edited.

## Write paths
- `experiments/ptr-engine/tools/launch_contract_diff.py`
- `tests/test_launch_contract_diff.py`
- `measure/LAUNCH-CONTRACT-DIFF.json`
- `docs/LAUNCH-CONTRACT-DIFF.md`
- `orchestration/units/LAUNCH-CONTRACT-DIFF.md`
- `orchestration/handoffs/LAUNCH-CONTRACT-DIFF.json`
- `orchestration/journals/LAUNCH-CONTRACT-DIFF.jsonl`

## Read-only inputs
`experiments/ptr-engine/measure/{HARNESS-PIN,GRID-PARAMS,GRID-SHAPE,REQUEST-LEDGER,LEDGER-GRID-BASELINE-2}.json`,
`experiments/ptr-engine/tools/run_a_star.py`,
`experiments/ptr-engine/longrun/{run_longrun.py,cell.py,analyze_stats.py}`,
`docs/{GRID-PARAMS.md,GRID-RUNBOOK.md,GRID-SHAPE.md,GATE-CHAIN.md}`.

## Result
22 numbers: AGREES=15, DISAGREES=3, STALE-BY-DESIGN=4. Disagreements: harness_pin_digest, per_cell_budget, per_arm_round_cap.
Both guard directions proved on a `/tmp` copy (exit 0 / exit 1).
