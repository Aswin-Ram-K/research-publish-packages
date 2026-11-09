# GRID-BUDGET-RECHECK

**Purpose.** Reconcile `V8-DRYRUN-REFREEZE`'s G1 line `1,154/4,320` with `BUDGET-SCHEDULE`'s A\* = 792,
decompose the difference, and decide how many reps of the frozen 48-turn design fit 3,219 remaining.

**Bound.** 18 tool calls, 0 requests, offline. Met: 15 calls, 0 requests (`AUDIT_NETWORK_EVENTS=0 []` x4).

**Write paths.** `experiments/ptr-engine/measure/GRID-BUDGET-RECHECK.json`, `docs/GRID-BUDGET-RECHECK.md`,
`orchestration/units/GRID-BUDGET-RECHECK.md`, `orchestration/handoffs/GRID-BUDGET-RECHECK.json`,
`orchestration/journals/GRID-BUDGET-RECHECK.jsonl`.

**Findings.**
1. 1,154 = 1,101 already spent + 48 turns + 5 follow-up allowance (`cell.py:875`, `:888`, `:124`;
   `request_ledger.py:599`). The command named one arm (`--arm transcript-grow`), so it is not a
   four-arm rep price either.
2. 792 = 576 x 1.374532 = 791.73 -> 792 marginal, per rep 264. The 1,374532 factor omits the
   **1,101 spent baseline**; its rate also differs from the gate's by exactly 232/801 (the 232 unmarked
   request rows the gate never charges).
3. Gate-enforced price per (arm, rep) cell = 48 + 5 = 53. reps 1/2/3 -> 212/424/636 new requests,
   remaining 3,007/2,795/2,583. **3 reps fit.**
4. H3 at 3 reps: 9 checkpoint ids -> 36 paired items, b+c >= 6 satisfied. 1 rep would be 3 ids
   (not evaluable).
5. G1 enforces `would_spend <= 3,219` (`cell.py:1167-1175`), i.e. the dry-run arithmetic; the multiplier
   is never read.

**Verdict: PASS.**
