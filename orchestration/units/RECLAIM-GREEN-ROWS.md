# UNIT `RECLAIM-GREEN-ROWS`

**Purpose.** Test whether the nine measured-green failed cards can be converted into verdict rows
retroactively, and report exactly what the board permits and what it refuses. Offline: zero inference requests.

**Input.** `experiments/ptr-engine/measure/FAILED-COLUMN-RECLAIM.json` — nine `finished_once_and_still_green`
cards plus `PROBE-CP3-V6` (the one `finished_once_but_red_today`). Command per card taken from that census,
never from memory.

**Procedure.** (1) read each card's stored command and recorded sha; (2) re-run it from the repo root today and
capture the literal exit plus the output tail — a command that no longer runs is `not_runnable_today`, not a
pass; (3) on exit 0, attempt `orchestration_verdict record` with that command, `exitCode 0` and the measured
`git rev-parse HEAD`; (4) on a refusal, record the text in full — no workaround, no ledger edit, no fabricated
sha; (5) on non-zero, record nothing and mark `still_red`.

**Result.** 9/9 green today, 1/1 red (`PROBE-CP3-V6`, unchanged). 2 rows recorded, 7 refused by the evidence
allow-list, 1 still red. Both recorded cards had settled executions, which is the answer to the question.

**Write paths (exactly).**
`experiments/ptr-engine/measure/RECLAIM-GREEN-ROWS.json` · `docs/RECLAIM-GREEN-ROWS.md` ·
`orchestration/units/RECLAIM-GREEN-ROWS.md` · `orchestration/handoffs/RECLAIM-GREEN-ROWS.json` ·
`orchestration/journals/RECLAIM-GREEN-ROWS.jsonl`

**Forbidden.** No edit to another card, its handoff, the ledger, `exit_codes.py`, or any rows/grade file; no
invented sha; no live request; no `ask_user_question`.

**Bound.** ≤26 tool calls. **Kill condition.** If the board refuses all nine, that is a complete result.

**Verdict.** `python3 -m pytest tests/test_orchestration_handoffs.py -q` (validates this unit's handoff as
machine-readable JSON) at HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3`.
