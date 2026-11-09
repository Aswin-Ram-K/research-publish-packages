# UNIT CAPGATE-CELL-LABEL

- **Purpose:** make a cap-gate refusal NAME ITSELF through `cell.py`, and make the runaway paths reconcile.
  The author is not the verifier; `V-CAPGATE-REFUSE` measured both defects and this card fixes only the
  label and the missing reconcile.
- **Bound:** 30 tool calls (used 29). Offline, zero inference requests, no network to `:8012`/`:8014`.
- **Write paths:** `experiments/ptr-engine/longrun/{exit_codes.py,cell.py,run_longrun.py}`,
  `experiments/ptr-engine/longrun/tests/{test_capgate_label.py,test_exit_codes.py}`, `docs/EXIT-CODES.md`,
  `docs/GATE-CHAIN.md`, `orchestration/{units,handoffs,journals}/CAPGATE-CELL-LABEL.*`.
- **Forbidden and respected:** no `measure/rows-*`, no grade file, no `PARM-1*`, no fixture, no
  `analyze_stats.py`, no `spawn_record` rule, no threshold. No guard was weakened.
- **What was built:**
  1. `EXIT_CAPGATE_UNRECORDED = 14` in `exit_codes.EXIT_TABLE`, with `RUNNER_MAPPED_TO_CELL = {9: 14}`;
     `cell.stage_run()` raises `Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, "4/7 run", "cap gate refused:
     unrecorded spend — <the runner's own delta/headroom line> (runner rc 9) — rows kept at …")`.
     `RUNNER_MAPPED_TO_CRASH[9]` now says where 9 goes; the runner itself still exits 9 (not renumbered).
  2. The four runaway returns in `run_cell` go through `_abort_stop()` → `_gate_finish()` before returning,
     so an aborted run reconciles; a reconcile failure OUTRANKS the abort and exits through the cap-gate code.
  3. Tests: `tests/test_capgate_label.py` (5 tests, (a)-(e)) + `tests/test_exit_codes.py` updated so the
     source scan, the raise sites and the docs table agree in both directions including 14.
- **Verdict row:** `tree_freeze.py --wrap … --verdict-row -- <both suites>` → `exitCode 0`,
  `sha f17663d1fed0162a7dc3c5a0a58d372c710974c3`, `verdict=pass`, `changed=0`.
- **Residual, stated not papered over:** the pre-send exit 4 is STILL unverified end-to-end (only the gate
  and `_cap_stop` exercised directly, the same limit `V-CAPGATE-REFUSE` recorded); `run_cell`'s BUDGET ABORT
  returns 4 without reconciling (same class of hole, outside the four sites this card owned);
  `run_longrun.py` was rewritten by another unit concurrently, so the pins are by sha and content anchors.
