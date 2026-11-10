# U-SPCC-42 — paid rows are persisted before the refusal unwinds

## Defect
The programme cap is enforced on ROW COUNTS (`tools/request_ledger.py` sums
`measure/rows-*.jsonl`). A paid call that produces no row is invisible spend.
`U-SPCC-40` measured `delta=-4` on a fetch-heavy three-arm cell: a mid-turn
`CapRefusal` propagated out of `fetch_rounds` before the rows for the follow-up
requests already sent in that turn were written.

## Mechanism
`fetch_rounds` accumulated follow-up rows in a local `followups` list and returned
them only on normal exit. `gate.acquire(t, "tool-followup")` raising `CapRefusal`
meant the caller's `followup_rows = fetch_rounds(...)` assignment never completed,
so the caller's handler saw `[]` and wrote only the turn row. N sends, 1 row.

## Change
- `_flush_partial_followups(followups, resp, row_sink, exc=None, keep_last=True)`
  persists the rows already bought and attaches `partial_followups` / `partial_resp`
  to the exception.
- `fetch_rounds(..., row_sink=None)` flushes before the budget abort, before a
  `CapRefusal` from `gate.acquire`, and before a transport failure unwinds.
  `keep_last=True` leaves the final follow-up row to the caller's turn row (the
  completed path's slot model), so the row count is unchanged.
- `run_cell` passes `row_sink=lambda _r: append_row(rows_path, _r)` and its
  `CapRefusal` / `BudgetExhausted` handlers now write the turn's own send
  (`turn-initial`) plus the turn row that stands in the last follow-up's slot,
  carrying that request's durable markers (`fetch_followup`, `send_index`,
  `fetch_round_final`).

No cap-gate semantics changed, no ceiling raised, no bypass added.

## Evidence
Red (pre-fix, `git show HEAD:...run_longrun.py`):
```
CAP REFUSED at T1 (tool-followup) ... allocation=2 used_in_run=2
cap-gate: ... spent_after=101 delta=-1
CAP GATE UNRECORDED (delta=-1) — refusing, exit 9
CAP REFUSED at T1 (tool-followup) ... allocation=3 used_in_run=3
cap-gate: ... spent_after=101 delta=-2
CAP GATE UNRECORDED (delta=-2) — refusing, exit 9
3 failed, 2 passed, 1 subtests passed
```
Green (post-fix): `3 passed, 3 subtests passed`.

Acceptance suite: `38 passed, 1 failed` — the only failure is
`test_request_ledger::TestRealCorpus::test_g`, correctly red on spend over the tool
default cap and left alone.

Full longrun dir: `870 passed, 2 failed` — `test_g` (known red) and
`test_journal_lint::test_census_over_the_live_corpus_is_reported` (pre-existing:
other agents' handoff JSONs are not in the frozen journal baseline).

`python3 tools/doc_check.py` → exit 0.
