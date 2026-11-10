# U-SPCC-9D — backfill adjudication of six settled-but-unverdicted units

**Verdict: `pass` (adjudication delivered; ritual test 1 failed → 10 passed)** · 2026-11-10 · HEAD `17182ffc760bb`

## Target

`experiments/ptr-engine/longrun/tests/test_verdict_ritual.py::LiveLedgerTest::test_no_new_unverdicted_closure_since_the_baseline`
was red with six `done` handoffs whose closed executions carried no verdict row:
`VERDICT-BACKFILL-FIXTURE-GENERATIONS`, `BUDGET-48-WIRE`, `V-GRID-REPORT`, `HARNESS-MAP-LINEREFS`,
`CAPGATE-CELL-LABEL`, `GRID-2-FINAL`.

## What was done

1. Read all six handoffs; recorded status, claimed artefacts, and whether the `evidence` block pastes command
   output or only asserts.
2. Verified every claimed artefact on disk (size + sha256) and, where the unit named one, re-ran its own check at
   HEAD. 0 live requests, 0 network, 0 container restarts.
3. Grepped `orchestration/VERDICTS.md` for prior adjudication: **none** existed for five of the six;
   `GRID-2-FINAL` appeared only in a prose paragraph (line 4316), never as a verdict row.
4. Appended `## Batch: backfill adjudication of six settled units (2026-11-10)` to `orchestration/VERDICTS.md`
   — appended only, no existing row rewritten or reordered.
5. Discovered the mechanism the ticket mis-stated: the ritual test's `verdict_keys` come from
   `~/.dsh/storages/orchestration/verdict.jsonl`, **not** from `VERDICTS.md`. Appending rows to the page alone
   leaves the test red. So six rows were appended to that ledger, one per closure key, each naming the command
   actually run at HEAD and its real exit code, prefixed `[U-SPCC-9D backfill adjudication, not the unit's own
   frozen command]`.

## Verdicts

| Unit | Verdict |
|---|---|
| `VERDICT-BACKFILL-FIXTURE-GENERATIONS` | pass — `pytest .../test_build_fixture.py -q` 5 passed, exit 0; artefacts 2,869/3,391/1,521 B |
| `BUDGET-48-WIRE` | superseded — `RUNNER-ROUNDS-48` implemented its `next_unit_hint`; `--fetch-rounds-per-arm` now at `run_longrun.py:3858`, pool 24→48 at `:230`; `GRID-PARAMS.json` 44,876 B / 22 keys loads exit 0 |
| `V-GRID-REPORT` | partial — report substantive (8 attempts, 3 findings) but its `/tmp/vgfinal/attack.py` harness is gone; era-pooling finding now guarded (`20 passed`) |
| `HARNESS-MAP-LINEREFS` | partial (stale-tree) — guard now `FAIL (15 unbaselined)`, exit 1, `2 failed, 3 passed`; cited lines `cell.py:1671`, `run_longrun.py:1072` are blank at HEAD |
| `CAPGATE-CELL-LABEL` | pass — `25 passed, 15 subtests passed`, exit 0 |
| `GRID-2-FINAL` | pass — `21 passed in 1.43s`, exit 0; record 24,572 B matches the handoff counts |

## Red→green

`test_verdict_ritual.py` before: `1 failed, 9 passed`. After: `10 passed`.

## Residuals (stated, not papered over)

- The `HARNESS-MAP-LINEREFS` row carries `exitCode 1` on purpose: its guard fails at HEAD. The `partial` verdict
  and the row agree; neither claims a green it does not have.
- `BUDGET-48-WIRE` has no runnable acceptance command. Its row records the JSON-load check it named; the
  substance is carried by the `superseded` verdict, not by a passing test.
- Two of six units (`V-GRID-REPORT`, `HARNESS-MAP-LINEREFS`) could not be re-measured to their own claim: one
  harness was `/tmp`-only and deleted, one pin has rotted. Neither is upgraded to `pass`.
