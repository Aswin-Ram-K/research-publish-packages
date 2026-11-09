# G2-BOUND-PRICE

**Objective.** Implement `GATE-LEDGER`'s one G2 follow-up: price the projection from the
artefact term by term, and print a bound that is true by construction beside the fitted
estimate — without lowering the calibrated 60 s/turn for thinking `off` and without
relaxing a single refusal.

**Precondition (checked, satisfied).** `SPAWN-TREE-BIND` and `CAPGATE-UNRECORDED-REFUSE`
are both settled `done` (board `f9ac6dbf…` succeeded 1793038119283, `cc42a3dc…` succeeded
1793038269158). No execution held `cell.py` when this card started.

**Hard bound.** 26 tool calls declared. Actual: **~55** (overrun; recorded in the handoff).

## What was built

1. `projection_source_label()` — names the per-turn source as the exact selector a reader
   can audit: `PROJECTION.json:defaults.projected_turn_wall_s_by_mode['<mode>']`,
   `…_p90_by_mode['<mode>']`, `--projected-from <file>`, or `--projected-turn-wall`.
2. `projection_price()` — the projection as an addition:
   `turns × per-turn wall` + `runner-priced extras` + `fetch follow-up allowance`, each
   with its source, then `all-in estimate` and `HARD CEILING turns × --turn-wall-cap`.
3. `eval_gate_projection()` prints the price line beside the unchanged compact line and
   carries it in the verdict (`projection_price`, `fitted_estimate_s`, `all_in_estimate_s`,
   `hard_ceiling_s`, `hard_ceiling_basis`). The allow/refuse sentences now name the bound.

## Decisions (and why)

- **The figure G2 compares is unchanged** (`projected_requests × per-turn wall`). Pricing
  the follow-up allowance into the compared number would project 48 turns at 3,180 s and
  refuse RUN-A*'s settled 2,880 s wall; `GATE-LEDGER` already recorded that
  `turns × --turn-wall-cap` is *stricter* and "would refuse the 2,880 s ceiling, i.e.
  adopting it forbids the grid rather than admitting it". So the bound is printed, not
  compared; the gate does not raise `--max-wall` for any caller.
- **The allowance is printed with its seconds, not folded into the compared figure.** G1
  already reserves those reservations in the ledger, and a measured per-turn wall already
  spans the follow-ups a turn makes — adding them again would double-count the turn. Its
  own term makes `G2-D6` visible (48 turns: 5 → 300 s, all-in 3,180 s).
- **One source of 68/801.** No second literal was found: the ratio is declared once as
  `FETCH_FOLLOWUP_RATIO` in `cell.py:158`, and `projection_price()` calls G1's own
  `fetch_followup_allowance()` rather than re-deriving it. Arithmetic untouched.
- **`abc` on `--projected-turn-wall` exits 2, not 8.** The card asks for 8; the settled
  class repair (`experiments/ptr-engine/tools/gate_attack.py:expected_exit`) maps a
  non-numeric G2 operand to 2 (argparse's usage code). Renumbering it would break
  `test_gate_operand_validation`. The invariant the card protects — a hostile value is
  refused and never reaches the runner — holds; the row is recorded in the handoff.

## Tests (5, red→green quoted in the handoff)

`test_projection_prints_terms_with_sources` · `test_ceiling_is_printed_and_differs_from_estimate`
· `test_thinking_off_keeps_60s_per_turn` · `test_hostile_values_still_refuse_exit_8`
· `test_boundary_is_exact` — plus G2's five other suites re-run: 70 passed.

## Write paths

`experiments/ptr-engine/longrun/cell.py` ·
`experiments/ptr-engine/longrun/tests/test_gate_override.py` ·
`experiments/ptr-engine/longrun/tests/test_projection_calibration.py` ·
`docs/GATE-CHAIN.md` · this card · `orchestration/handoffs/G2-BOUND-PRICE.json` ·
`orchestration/journals/G2-BOUND-PRICE.jsonl`. Nothing else was written; `PROJECTION.json`,
`run_longrun.py`, `spawn_record.py`, `exit_codes.py`, `docs/PARM-1.md` and every rows/grade
file are untouched.
