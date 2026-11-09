# UNIT RUNAWAY-POLICY — the runaway counter must count what it is named for

Card: `95341eb5` · execution `bb2143ee` · 2026-10-26 · offline, zero inference requests, no live cell.

## Objective (as carded)
`--runaway-turns 2` aborted cell 1 of `RUN-A*` at T27 on two 4,096-token `length` truncations while
`turns_over_180s` was 0. Decide, on measurement, what the guard is for; make its counter, its names and
its message say what it does; keep the historical 16,384-token / 475 s hazard caught by a named bound.

## Bound and kill condition
26 tool calls. Journal first, handoff within 6 calls of the end, verdict row before the handoff write.
Do not start while `RUN-A*` holds `run_longrun.py`; if still running, report blocked. Never edit
`PARM-1*`, the fixture, graders, analyser, `REQUEST-LEDGER.json`, rows or published numbers. Never ask
the user. Never weaken a guard without naming the mechanism that replaces its bound.

## Precondition check
`task_board_get RUN-A` → not found by that id; `task_board_list query=RUN-A` → `ad212412`/`RUN-A*`
`status=done`, `latestExecution.endedAt=1793039625939`, `result=succeeded`. The grid no longer holds
`run_longrun.py`, so this unit ran. `GATES-MESSAGE-CONSISTENCY` (running) writes gate sentences in
`cell.py`; this unit did not touch `cell.py`.

## Decision
Option **B**: `length` truncation at `--max-tokens` is DATA and never counted; the abort fires on a
**wall-time runaway** (a turn whose stream `--turn-wall-cap` closed), with a second counter for a server
that ignores the ceiling (`completion_tokens > max_tokens`).

## Deliverables
- `experiments/ptr-engine/longrun/run_longrun.py` — `wall_runaways` + `ceiling_violations`,
  `_ceiling_violation()` replacing `_runaway_signature()`, abort message naming turns by index and why.
- `experiments/ptr-engine/longrun/tests/test_runaway_policy.py` — 3 tests, red A / red B / green.
- `docs/RUNAWAY-POLICY.md` — semantics, incident history, options A/B/C priced, recommendation, bounds.
- `measure/RUNAWAY-POLICY.json` — licence measurement (census, rates, binomials, sha256).
