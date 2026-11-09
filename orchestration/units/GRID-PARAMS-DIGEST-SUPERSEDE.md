# UNIT `GRID-PARAMS-DIGEST-SUPERSEDE`

Persisted copy of the card this unit ran (card 76c99a71-310b-4f42-b8ae-5c6061d526fd, execution a3fdaab5).
Offline: zero requests, zero live cells, no network. Automated session: no questions asked.

## Objective

Make `experiments/ptr-engine/measure/GRID-PARAMS.json` stop quoting a harness digest that is not the
pin's, **without deleting the record of the old one**, and take `launch_contract_diff --check` to exit 0.

## Measured defect (from `LAUNCH-CONTRACT-DIFF`, 9e52d155)

| where | digest | generation |
|---|---|---|
| `measure/HARNESS-PIN.json:9` + `tools/run_a_star.py:51` + `docs/GRID-RUNBOOK.md:68,:119` + bytes on disk | `fa6fd8cc…37e8ac` | 4 |
| `measure/GRID-PARAMS.json` `harness_pin.harness_sha256` | `2b4d4808…c23871` | 3 (written 18 min earlier) |

Cost already paid: `LIVE-CANARY-4ARM` refused at cell.py stage 2/7, twice.

## Hard bound

One digest field, one supersedes block, four write paths, ~20 tool calls. If the recomputed digest did
not equal the pin's, the unit was to STOP (moving tree, not this card's job).

## Result — partial

The GRID-PARAMS half is done: the file now quotes the pin's digest, keeps the old one, and the
`harness_pin_digest` row stopped disagreeing (measured exit 0 at 19:44:10Z). But `grade_v5.py` — one of
`cell.py`'s six `HARNESS_FILES` — moved at **19:44:44Z**, three minutes later, so `HARNESS-PIN.json`
generation 4 no longer matches the bytes and the row is red again for a reason this card may not fix
(`HARNESS-PIN.json` is on its do-not-edit list). Final measured state: exit 1, one disagreement,
`harness_pin_digest fa6fd8cc… (pin) | a3fa2ee0… (bytes) | 2b4d4808… (preserved)`. **Owner: a
generation-5 pin-bump card.**

1. **Recomputed before editing** from `cell.py:128-135` `HARNESS_FILES` + the fixture, sorted
   `name:sha256\n` → `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac` = the pin's
   `harness_sha256`, generation 4, and all six per-file shas equal the pin's rows. Tree not moving.
2. **Additive edit** confined to lines 158-176 (`harness_pin`): live digest → the pin's; old digest and
   all six generation-3 values preserved in a dated `harness_pin.supersedes` block with the verbatim
   reason; a `read_the_pin_at` pointer beside the field.
3. **Key path kept**: `harness_pin.harness_sha256` is read by `tools/launch_contract_diff.py:308` and
   `tests/test_launch_contract_diff.py:63,90`, so the card's "rename the field" branch would have broken
   the probe. The "add a pointer" branch was used instead.
4. **`--check`**: exit 1 before (row `DISAGREES harness_pin_digest fa6fd8cc… | 2b4d4808…`), exit 0 right
   after the edit (22 numbers: AGREES=15, DISAGREES=0, STALE-BY-DESIGN=7), exit 1 again from 19:45Z
   because `grade_v5.py` moved at 19:44:44Z — the pin, not `GRID-PARAMS.json`, is now the stale record.
   The two other rows that were red at 19:39Z (`per_cell_budget`, `per_arm_round_cap`) were closed by a
   **concurrent peer** (`run_a_star.py` 19:42:11Z, `docs/GRID-PARAMS.md` 19:42:20Z), not by this unit.
5. **No other number moved**: 54 → 57 numeric leaves, all deltas are generation labels inside
   `harness_pin`; of the 12 checks that extract a value out of this file, only `harness_pin_digest` moved.

## Write paths

`experiments/ptr-engine/measure/GRID-PARAMS.json` · `orchestration/units/GRID-PARAMS-DIGEST-SUPERSEDE.md` ·
`orchestration/handoffs/GRID-PARAMS-DIGEST-SUPERSEDE.json` · `orchestration/journals/GRID-PARAMS-DIGEST-SUPERSEDE.jsonl`

## Did not touch

`HARNESS-PIN.json`, `cell.py`, `run_a_star.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, any
fixture, `PARM-1*`, any threshold, every published markdown page, `GRID-SHAPE.json`,
`measure/LAUNCH-CONTRACT-DIFF.json` (not regenerated).

## Carried forward

- `docs/GRID-RUNBOOK.md:82-95` still narrates the pre-fix state ("GRID-PARAMS.json says at
  `harness_pin.launch_must_pass`: `--expect-harness 2b4d4808…`") — needs a doc-sync card.
- `tests/test_launch_contract_diff.py:66` anchors on `(default 67)`, which `run_a_star.py:367` no longer
  contains; and no test reddens if `harness_pin.harness_sha256` regresses to `2b4d4808…`.
- The two other DISAGREES rows (`per_cell_budget`, `per_arm_round_cap`) were closed by a concurrent peer
  at 19:42:11Z / 19:42:20Z, not by this unit (attribution test in the handoff).
