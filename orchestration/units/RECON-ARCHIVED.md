# RECON-ARCHIVED — unit card

Objective: stop `tools/board/session_recon.py` failing on archived cards so its exit code means
something. Two defects found by reproducing the red run against the real ledger:

1. `find_settled_lag` graded a **non-archived** card's undone column — but `archive` never rewrites
   `status`, so two archived cards (GATE-RUNNER `7a7424d4…`, FIX-PROSE2 `75e1f3b7…`) still read `todo`
   after their last execution ended (`result: cancelled`) and were graded as live lags → `exit=1` on
   cards nobody can act on.
2. Settled-lag offenders were **double-counted** — the branch appended the raw `session-<uuid>` key to an
   offender list that already held the normalized `<uuid>`, and the print loop listed every lagging card a
   second time. Two lagging cards printed four offender lines.

Hard bound: read-only over `~/.dsh`; no card created/moved/settled; ≤45 tool calls; kill condition = if the
real-ledger run cannot be made to reproduce red→green in 3 attempts, STOP and report `partial`.

Write paths: `tools/board/session_recon.py`, `tests/test_session_recon_archived.py`,
`orchestration/handoffs/RECON-ARCHIVED.json`, `orchestration/VERDICTS.md`, `state/logs/session-recon.json`,
plus scratch under `.scratch/recon-archived/`.

Deliverable: red→green→red transcript with exact tails, a live-lag control proving the check is not dead,
and a regression test that fails when the fix is reverted.

## Result

- Archived cards: recorded under `archivedWithSettledExecution` + `summary.archived`, never an offender.
- Real ledger: `exit=1` (offenders=2 lagging=2, 4 offender lines) → `exit=0` (offenders=0 lagging=0
  archived=2, 2 offender lines).
- Control (archived cards kept, one synthetic live unsettled card added): still `exit=1`, 1 offender line —
  the check is live, not deleted.
- `tests/test_session_recon_archived.py`: 10 tests; 3 fail against the pre-fix body.

## Self-verification note

This unit is the author. Per `AGENTS.md` "Verification independence", the verdict below is an
**author self-check, not an independent verdict** — an independent `V-RECON-ARCHIVED` card is the gate.
