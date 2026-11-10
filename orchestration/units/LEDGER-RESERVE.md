# LEDGER-RESERVE — reconcile request budget and reserve experiment allowance

**Unit.** `LEDGER-RESERVE` · automated session, no human present, offline.
**Objective.** Reconcile every send this workspace has made against `experiments/ptr-engine/measure/REQUEST-LEDGER.json` (authoritative in main checkout), determine the available budget, test cross-tree lock sharing, and implement `reserve.py` (or refuse) without editing the ledger.
**Hard bound.** offline only; no model requests sent.
**Write paths.** `experiments/context-cache/cells/COMBINED-CONTEXT-SERVING/ledger/RECONCILE.json`,
`experiments/context-cache/cells/COMBINED-CONTEXT-SERVING/ledger/reserve.py`,
`experiments/context-cache/cells/COMBINED-CONTEXT-SERVING/ledger/RESERVATION-CCS-2026-11-05.json`,
`orchestration/handoffs/LEDGER-RESERVE.json`, `orchestration/units/LEDGER-RESERVE.md`.

## Findings

- Ledger remaining as read: 1729 (cap 4320, spent 2591, digest 8ebf4ed5…).
- HL-PILOT model calls: 765 (747 in row files + 14 E1B attested + 4 probes attested).
- Other context-cache cells: 15752 call rows across 54 files; 16499 total including HL-PILOT.
- Cross-tree lock: relative path `experiments/context-cache/.occamy.lock` not shared (both exit 0); absolute path shared (worktree 0, main 1).

## Assumptions

- Context-cache sends are enumerated as variance but not netted against the ptr-engine cap: separate experiment families with their own caps; ledger is the only budget instrument and remains authoritative. Available budget = min(2000, 1729) = 1729.
- Reservation uses ledger.remaining, not a recomputed reconciled total, so the experiment can proceed; reported transparently.
