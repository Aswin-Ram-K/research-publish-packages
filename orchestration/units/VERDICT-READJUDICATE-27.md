# UNIT `VERDICT-READJUDICATE-27`

**Contract (as received).** Re-adjudicate the 27 failed closures that demonstrably delivered — extended to 29 by the
scope addendum — by **running their own acceptance commands today** and recording only what actually happens.
OFFLINE: zero inference requests. Bound 34 tool calls.

## Rules applied
- One outcome per unit from {pass, fail, not-runnable, stale-tree}; never a backdated row, never an invented sha.
- `pass` requires the unit's own command to have run now and exited 0. Existing artefacts never earn a PASS.
- No live request (marked `not-runnable: live` after reading the command) and no mutating command.

## Result
29 adjudicated: **10 pass · 1 fail · 1 stale-tree · 17 not-runnable**. 8 verdict rows recorded (7 PASS, 1 FAIL exit-1).
3 passes could not be recorded at all because the gate refuses their command form (`command-not-allowed`).

## Deliverables
- `docs/VERDICT-READJUDICATION.md`
- `experiments/ptr-engine/measure/VERDICT-READJUDICATION.json`
- `orchestration/handoffs/VERDICT-READJUDICATE-27.json`, `orchestration/journals/VERDICT-READJUDICATE-27.jsonl`

## Bound
29 of 34 calls. No unit handoff, card, journal or foreign measurement file edited; `PROBE-CP3-V6` left unrepaired.
