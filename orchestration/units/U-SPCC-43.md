# U-SPCC-43 — the fetch arm's inline follow-up and the budget exit both reconcile

## Defect
`U-SPCC-42` fixed the main turn loop and recorded two remaining gaps in its own
handoff. Both are the same accounting hole: the programme cap is enforced on ROW
COUNTS, so a paid call with no row is invisible spend.

1. **`bounded-context-fetch`'s inline follow-up path.** In `run_cell`'s
   `arm == arm_cd.ARM_D` block, `arm_cd.service_fetches` runs AFTER the turn's own
   request was paid for, and the turn's row was written only once the whole block had
   returned. Anything that unwound out of the block before the follow-up send — a
   malformed fetch call (`ValueError: fetch request missing tool_call_id`), an
   unrenderable fetch result — propagated out of `run_cell` with `sent` already
   incremented, leaving **one paid request with no row and the run with no
   reconciliation at all** (`cap_gate.reconcile` stayed `None`). `bounded-context-fetch`
   is one of the three arms in E1, so an E1 run could undercount spend through it.
2. **`BudgetExhausted`.** Four exits (`digest`, `turn`, the D arm's follow-up, and
   `fetch_rounds`) printed `BUDGET ABORT` and returned 4 without reconciling, so a
   budget-exhausted run reported no delta at all.

## Change
- `_persist_d_turn_row(...)` writes the D arm's `kind="turn-initial"` row — the row the
  completed path already writes for the turn's own send — so the schema and the row
  count are unchanged.
- The D arm's fetch-service prefix (`service_fetches` + assistant/tool message
  construction) is wrapped: on any `Exception` the turn's row is persisted, a
  `TURN FAILED (fetch service)` line is printed, and the run leaves through
  `_abort_stop(4, ...)` so it reconciles.
- All four `BudgetExhausted` exits now return `_abort_stop(4, gate, manifest_path,
  manifest_sha, rows_path)` instead of a bare `4`.

No cap-gate semantics changed, no ceiling raised, no bypass added, no fetch semantics
changed, no row field added or removed.

## Evidence
Red (pre-fix, `git show HEAD:...run_longrun.py`):
```
FAILED ...::test_budget_exhausted_exit_reconciles - TypeError: 'NoneType' object is not subscriptable
FAILED ...::test_service_failure_persists_the_turn_row - ValueError: fetch request missing tool_call_id
2 failed, 3 passed in 0.21s
```
The `TypeError` is `manifest["cap_gate"]["reconcile"]` being `None`: the run wrote its
manifest at start and never reconciled. The `ValueError` is the paid send's row never
being written because the exception left `run_cell`.

Green (post-fix): `5 passed in 0.18s`.

Acceptance suite (`test_fetch_arm_row_persistence` + `test_paid_row_persistence` +
`test_arm_cd_wiring` + `test_cap_gate`): `27 passed, 3 subtests passed`.

Full longrun dir: `875 passed, 2 failed` — the same two pre-existing failures
`U-SPCC-42` recorded: `test_request_ledger::TestRealCorpus::test_g` (correctly red on
spend over the tool default cap) and
`test_journal_lint::test_census_over_the_live_corpus_is_reported` (other agents' handoff
JSONs outside the frozen journal baseline).

`python3 tools/doc_check.py` → exit 0.

## Deltas
| path | before | after |
|---|---|---|
| `service_fetches` unwind (1 paid send) | 0 rows, no reconciliation (`reconcile=None`) | 1 row, `delta=0` |
| `BudgetExhausted` exit (1 paid send) | 1 row, no reconciliation (`reconcile=None`) | 1 row, `delta=0` |
| completed fetch cell | 2 sends, 2 rows, `delta=0` | 2 sends, 2 rows, `delta=0` (unchanged) |

## Left alone
`except RequestFailure` precedes `except client.TurnWallCap` in the D arm's follow-up
handler, and `TurnWallCap` subclasses `RequestFailure`, so the wall-cap handler is dead
code: a wall-capped follow-up is recorded as a plain failure and loses its partial fold
and its runaway accounting. Row count is unaffected (the failure row is written), so it
is not an accounting hole — but it is a real defect in the same block.
