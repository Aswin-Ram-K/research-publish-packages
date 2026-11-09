# UNIT LEDGER-BASELINE-REPIN

**Purpose.** Freeze a second pre-grid baseline at the current spend (1128 / remaining 3192) so
RUN-A-STAR-2's delta measures the tranche only, not the 27 era-A abandoned-cell requests already
banked. The first baseline stays untouched as a dated record; v2 supersedes it by pointer.

**Bound.** 16 tool calls; journal first; verdict row before handoff; offline, zero requests,
no `ask_user_question`.

**Write paths (exactly).**
`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json` ·
`experiments/ptr-engine/tools/ledger_delta.py` · `tests/test_ledger_delta.py` ·
`docs/LEDGER-BASELINE.md` · `orchestration/units/LEDGER-BASELINE-REPIN.md` ·
`orchestration/handoffs/LEDGER-BASELINE-REPIN.json` ·
`orchestration/journals/LEDGER-BASELINE-REPIN.jsonl`

**Tasks.** (1) write v2, never touch v1; (2) quote `ledger_delta.py`'s baseline handling by
`file:line`, default it to v2 while keeping explicit-v1 behaviour; (3) prove delta 0 against v2 and
`+48` in a `/tmp` copy; (4) rows-inventory guard (function + test) or a documented justification;
(5) `docs/LEDGER-BASELINE.md`; (6) no edits to rows files, the ledger artefact, the builder,
`cell.py`, `run_longrun.py`, `run_a_star.py`, `PARM-1*`, `GRID-*.json`, or other published pages.

**Forbidden.** Editing `LEDGER-GRID-BASELINE.json` (dated record), the ledger artefact, rows files.

## Assumption
`LEDGER-GRID-BASELINE-2.json` must also carry a `budget` / `counting` block even though the card's
required keys are top-level: `ledger_delta.py` reads `budget.spent` and `counting.remaining_raw` first,
so a top-level-only file would make `remaining_before` read as 0 and fail the cross-check for the wrong
reason. Both shapes are present; the required top-level keys are unchanged.
