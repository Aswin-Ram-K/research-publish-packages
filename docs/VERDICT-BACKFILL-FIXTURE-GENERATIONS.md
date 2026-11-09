# VERDICT-BACKFILL-FIXTURE-GENERATIONS

## Why this card exists

`test_verdict_ritual` asserts that every `done` handoff after `2026-10-26T16:13:05Z` carries a verdict
row. `FIXTURE-GENERATIONS` (`96ec0bcc-9d40-444a-a0f8-c82c7e27f9ec`, exec
`efa8039f-751e-4ceb-b3e5-eaef3df6f8b5`) settled `done` with no row, so the ritual red blocked
`SEAM-TEST-RED`'s recorded suite for every card in the batch:

```
AssertionError {'FIXTURE-GENERATIONS': ['96ec0bcc-…:efa8039f-…']} != {}
```

The missing row is the defect; the red is correct. This unit recovers the card's own acceptance command,
re-runs it today, and records a row **only if it exits 0**.

## 1. Recovered command (verbatim, not invented)

From `orchestration/handoffs/FIXTURE-GENERATIONS.json` → `evidence.commands` (4 entries):

1. `python3 experiments/ptr-engine/tools/build_fixture.py --variant v5 --out /tmp/g5.json && sha256sum /tmp/g5.json`
2. `python3 experiments/ptr-engine/tools/build_fixture.py --variant v6 --out /tmp/g6.json && cmp /tmp/g6.json experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json`
3. `python3 experiments/ptr-engine/tools/build_fixture.py --check`
4. `python3 -m pytest experiments/ptr-engine/longrun/tests/test_build_fixture.py -q`

`orchestration/journals/FIXTURE-GENERATIONS.jsonl` (5 lines) carries phase/did/evidence prose only — no
command strings. So the command set above is the complete recorded evidence, and it exists.

## 2. Re-run today (HEAD `f17663d1`)

| command | exit | decisive line |
|---|---|---|
| `--check` | 0 | `ok:` for all 10 variants; v5 `967cef03…` and v6 `ff89625d…` match the handoff digests |
| `python3 -m pytest … test_build_fixture.py -q` | 0 | `5 passed in 0.45s` |
| `pytest … test_build_fixture.py -q` | 0 | `5 passed in 0.46s` |

The third line is the allow-listed launcher for the same invocation as recorded command 4 — the `pytest`
verb is accepted by the gate where a bare `python3` run is not. The wrapper is this unit's, and contains
nothing that was not already run.

## 3. Row recorded

`PASS` for `96ec0bcc-9d40-444a-a0f8-c82c7e27f9ec` / `efa8039f-751e-4ceb-b3e5-eaef3df6f8b5`, command
`pytest experiments/ptr-engine/longrun/tests/test_build_fixture.py -q`, exit 0, sha `f17663d1`. Recorded
only after the exit code was observed; no row would exist if it had failed.

## 4. Did the blocking assertion clear?

Yes. `test_verdict_ritual.py` alone: **Ran 10 tests, OK, exit 0.**

The full suite is still red, for an unrelated reason:

```
python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_*.py'
-> exit 1, Ran 179 tests, FAILED (failures=1)
FAIL: test_gate_operand_validation.OperandMatrix.test_the_six_named_bypasses_now_refuse_with_zero_live_spawns
AssertionError: 8 != 1 : F1: expected exit 8, got 1 ()
```

That failure is in `test_gate_operand_validation`, which is **not** inside `FIXTURE-GENERATIONS`' write
paths (`LR-01.spec.json`, `tools/build_fixture.py`, `experiments/ptr-engine/longrun/tests/test_build_fixture.py`, `docs/FIXTURE-GENERATIONS.md`,
the unit card, the handoff, the journal). Nothing was edited there; nothing was relaxed in
`test_verdict_ritual.py`.

## Verdict

The governance red that was blocking other cards' verdicts is **cleared**. `SEAM-TEST-RED`'s reclamation is
still blocked, but now by `test_gate_operand_validation` F1 — a different card's defect, named above.
