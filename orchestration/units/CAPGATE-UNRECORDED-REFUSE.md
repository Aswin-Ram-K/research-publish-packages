# UNIT `CAPGATE-UNRECORDED-REFUSE` — unrecorded spend refuses

**Objective.** Make the cap gate treat `delta < 0` (requests on the wire with no persisted
row) as a refusal, not a printout, and prove a run cannot start while its ledger disagrees
with the wire.

**Precondition.** `SPAWN-TREE-BIND` (`f9ac6dbf`) settled `done` (board #979/#981); its
handoff reports `cell.py` sha `b549e45e…` at start. `cell.py` now sha256
`e24e867b8fe9eec7d1344f5738d9f04022f9f5d0968fa0f575ab9c30e6edf013` and was NOT edited by this card.

**Write-path deviation (recorded, not hidden).** The card listed
`experiments/ptr-engine/longrun/cell.py`, but the gate's reconcile lives in
`experiments/ptr-engine/longrun/run_longrun.py` (verified: `cell.py` contains no
`RequestCapGate`, `reconcile`, `spent_at_start` or `UNRECORDED`). The measured defect is
`run_longrun.py:518` (`elif rec["delta"] < 0:` → print + `rc` left 0). The fix was
made there; `cell.py` is untouched and its exit-code map propagates the runner's 9
unmodified. Files written: `run_longrun.py`, `experiments/ptr-engine/longrun/tests/test_cap_gate.py`, this card,
`docs/GATE-CHAIN.md`, handoff, journal.

**Change.** `run_longrun.py:526` now prints the five facts (delta, used_in_run,
missing count, headroom_before/headroom_after, rows path), says the ledger cannot be
trusted for the next check, and sets `rc = EXIT_CAP_DIVERGENCE` (9 — reused, no new code).
Safe branches untouched: `delta == 0` → 0; `delta > 0` → `RECONCILE DIVERGENCE` 9;
pre-send `projected > headroom` → 4, zero rows, zero calls.

**Tests (4).** `test_unrecorded_spend_refuses`, `test_reconciled_run_still_succeeds`,
`test_positive_delta_still_diverges`, `test_presend_refusal_unchanged` in
`experiments/ptr-engine/longrun/tests/test_cap_gate.py`. Green: 13 passed, exit 0.

**Hard bound.** 24 tool calls; used 20 (including this write batch).

**Containment.** Offline: 0 inference requests, 0 sockets. No edits to rows, grades,
`REQUEST-LEDGER.json`, `spawn_record.py`, `docs/PARM-1.md`.
