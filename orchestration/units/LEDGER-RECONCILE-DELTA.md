# LEDGER-RECONCILE-DELTA — the ledger cross-check becomes a delta (card e36b0cae)

**Status:** done. **Bound:** 30 tool calls (used 33 — see handoff `bound_note`).
**Verdict:** PASS, execution a464fece, sha f17663d1.

## Objective
The launcher refused EVERY launch: a frozen baseline plus a ledger rebuilt from rows
can never be equal after the first post-freeze cell (CANARY-ERA-B-4 was refused at
gate 2 with zero requests spent: baseline-2 3192 vs live 3144). Re-cut the baseline
attributed AND remove the trap, keeping an unexplained gap a hard refusal.

## Write paths
- `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-3.json` (new; v2 not mutated)
- `experiments/ptr-engine/tools/run_a_star.py`
- `experiments/ptr-engine/tests/test_ledger_reconcile.py` (new)
- `docs/LEDGER-RECONCILE.md` (new)
- this card, `orchestration/handoffs/LEDGER-RECONCILE-DELTA.json`, `journal/2026-10-26.md`

## What was done
1. Live ledger recomputed with its own builder (`request_ledger.build_report`): 1176 /
   3144 / 19 files — identical to the on-disk record, so the card's figures are the
   file's figures.
2. `LEDGER-GRID-BASELINE-3.json`: requests 1176, remaining 3144, cap 4320,
   `as_of` 2026-10-26T22:33:00Z, an `attribution` table naming the four 12-row cell
   files (rows + sha256 + ts range), `supersedes` carrying v2's 1128 / 3192 /
   2026-10-26T19:04:18Z + its sha256, and a `rows_inventory`.
3. `run_a_star.py`: `LEDGER_FROZEN` -> baseline-3; new `attributed_delta()` counts rows
   billed after `as_of` with the ledger's own counting rule; `remaining_basis()` accepts
   `live == baseline + delta` (and `remaining` must follow the same delta), prints
   baseline / attributed_delta / live / explained / gap + the files with their sha12,
   and refuses by name when the gap is unexplained or the baseline is missing/unusable.
4. 9 tests incl. the +7 unexplained refusal naming the 7 and its red->green revert.
5. `docs/LEDGER-RECONCILE.md`: the trap, the rule, the refusal table, the re-cut
   procedure, the env hooks.

## Result
Canary dry run: exit 0, `canary_arms=4 canary_requests=48 refused=0`, with
`RECONCILE baseline=1176 attributed_delta=0 live=1176 explained=1176 gap=0`.
Unattributed +7 still refuses; baseline-missing refuses by name; the guard's removal is
visible in the tests. No request spent, no cell launched, no socket opened.
