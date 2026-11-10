# U-SPCC-61 — TX-04: the distance-64 fixture for E3

**Status:** DONE. Offline only: 0 endpoint requests, 0 model calls.

## What was built

`PREREG-SPCC.md` §E3 asks whether the observed distance cliff is a property of **position**
or of **eviction**. The existing `tasks-v7/TX-03.v1.json` probes {2, 5, 6, 8, 20, 32} and its
masking arm evicts by design, so it cannot answer the question. TX-04 is the fixture that can:
its deepest probe is at distance **64**, and every fact body is delivered at its introduction
turn and is still present (never masked, never revoked) at every probe turn.

| | |
|---|---|
| path | `experiments/ptr-engine/longrun/tasks-v7/TX-04.v1.json` |
| sha256 | `0c836872225fc0d6198aa86b3c72ec3dfada0b23f2541cde49adc53429703885` |
| bytes | 55191 |
| generator | `experiments/ptr-engine/tools/build_fixture.py --spec …/fixtures-spec/TX-04.spec.json --variant tx04` |
| spec | `experiments/ptr-engine/longrun/fixtures-spec/TX-04.spec.json` |
| base | `tasks-v7/TX-03.v1.json` (`f0a636fe…`), merged over by the `tx04` patch |
| N | 100 turns |
| checkpoints | 48, on 48 distinct turns |
| facts | 12 fact documents |

## Distribution

| distance | checkpoints |
|---:|---:|
| 2 | 10 |
| 8 | 10 |
| 20 | 10 |
| 32 | 9 |
| 64 | 9 |
| **total** | **48** |

8 per distance is 40; the remaining 8 are spread over the three shallowest buckets
(2, 8, 20 each get +2). Deepest probe turn: **99** (`cp.TX-04.f05.d64`, fact-05 introduced at
turn 35).

## Why 12 facts and not 8

`check_pointer_fixtures.validate` rejects two checkpoints on the same turn, and
`test_tx03_distance.py` pins 48 unique checkpoint turns. A checkpoint's turn is
`introduction_turn + distance`, so 8 facts over 5 distances can carry at most **40** unique
probes. 48 probes need at least 10 facts, and 10 facts all using the full 5-distance set is
also infeasible: two facts collide whenever their introduction turns differ by a difference of
two distances (`6, 12, 18, 24, 30, 32`), and no 10-element subset of `[1, 36]` avoids all of
those. TX-04 therefore carries **12** fact documents, each probing **4** of the 5 distances
(omission pattern 2/2/2/3/3 over d2/d8/d20/d32/d64), which yields the 10/10/10/9/9 split with
48 distinct turns. The reasoning is recorded in the fixture itself under `e3_design`.

## Retention

Every fact body is delivered exactly once, at its introduction turn, and never again. No probe
turn carries a masking/forget/evict instruction, no fact document is revoked, and each
checkpoint's revision is live from its introduction turn. So a cliff that persists in TX-04 is
positional; a cliff that vanishes was eviction.

## Index refs

The `b38db8a` invariant holds at the opening turn and at all 48 probe turns: every ref
`arm_cd.world_index_lines` advertises resolves `OK` through the real `ptr_engine.pointer_table`
fetch path. Fact documents become addressable at their introduction turn, so the index is
checked per turn rather than only at turn 1.

## Grading

`answer_spec` derives each expected value from
`experiments/ptr-engine/ptr_engine/tx04_constants.py` (48 constants, `F<fact>_<symbol>`).
`grade_v5.derive_truth` returns 48 cells with 0 mismatches against the documented `expected`
strings — the fixture's truth is re-derivable from source, not asserted.

## Writes

- `experiments/ptr-engine/longrun/tasks-v7/TX-04.v1.json` (new; TX-03 untouched)
- `experiments/ptr-engine/longrun/fixtures-spec/TX-04.spec.json` (new)
- `experiments/ptr-engine/longrun/tests/test_tx04_fixture.py` (new, 12 tests)
- `experiments/ptr-engine/ptr_engine/tx04_constants.py` (new)
- `orchestration/units/U-SPCC-61.md`, `orchestration/handoffs/U-SPCC-61.json`

## Checks run

- `build_fixture.py --check` → `ok: tx03 … f0a636fe…`, `ok: tx04 … 0c836872…` (exit 0)
- `check_pointer_fixtures.py tasks-v7/TX-04.v1.json` → `OK`, 4/4 outcomes, 48 checkpoints
- `pytest experiments/ptr-engine/longrun/tests/test_tx04_fixture.py -q` → 12 passed
- `python3 tools/doc_check.py` → exit 0
