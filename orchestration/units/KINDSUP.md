# Unit `KINDSUP`

**One purpose:** author the superseded-fact memory fixture `TX-SUP.v1.json` (a value is revised later; the correct answer is the latest value) plus its offline test.

## Write paths
`experiments/ptr-engine/longrun/tasks-v7/TX-SUP.v1.json` · `experiments/ptr-engine/longrun/tests/test_tx_sup.py` · `orchestration/units/KINDSUP.md` · `orchestration/handoffs/KINDSUP.json`

## Design
- 12 fact documents (`doc-fact-01..12`), each with 4 attributes `VAL_A..VAL_D`.
- Each document has two revisions: rev1 carries the stale value, rev2 carries the current value; rev2 is introduced in a later tool output.
- 48 checkpoints on 48 unique turns, 12 per distance `{2,6,20,32}`; each checkpoint is placed after the final revision and asks for the current (latest) value.
- Stale value differs from expected for every checkpoint and is present in the fixture (initial revision body).
- All 48 expected values distinct; NUM-only answers.

## Evidence
- checker: `experiments/ptr-engine/longrun/tasks-v7/TX-SUP.v1.json: OK`
- pytest: `19 passed in 0.07s`

## Status
done
