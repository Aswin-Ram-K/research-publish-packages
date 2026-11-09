# UNIT `PRICE-REPLICATION` — re-price the arm schedule against measured power

**Board card:** `942c0f78-00c8-4d90-b734-0d80930edbee` · **execution** `97de3e12-6bf2-40af-bad3-5b943b9377eb`
**Bound:** 22 tool calls (used 18) · **Requests:** 0 inference (offline re-pricing) · **Status:** done

## Objective

`P95-POWER-FROM-ROWS` (PASS `f17663d1`) measured that the H1 pair separates at n = 48 with a 254 ms
margin, that effective n ≈ ⅓ of raw, and that 2 of 3 grids do not reproduce the effect. The standing
default ("run A\*", 792 requests, `RUN-A*` card `ad214412`) predates that measurement. Re-price the
candidate schedules and recommend what the next 288–792 requests buy.

## Hard rules honoured

- No edit to `RUN-A*`, `PARM-1`, `BUDGET-SCHEDULE`'s artefacts, or any rows/grade file
  (`artefact_edits` in the JSON is 0 across all five).
- No frozen threshold lowered: `TAIL_MIN`/n ≥ 60 (PARM-1:37), 48 turns (PARM-1:137), the 2/12 margin,
  the b+c ≥ 6 McNemar licence, and the four-arm grid clause (PARM-1:150-152) are untouched. Schedules
  that could only work by relaxing one are marked `not admissible` with the clause named.
- Every option priced against `REQUEST-LEDGER.json` **raw 3,219** remaining (not the unsound 3,249).

## Write paths (exactly)

`docs/PRICE-REPLICATION.md` · `experiments/ptr-engine/measure/price-replication.json` ·
`orchestration/units/PRICE-REPLICATION.md` · `orchestration/handoffs/PRICE-REPLICATION.json` ·
`orchestration/journals/PRICE-REPLICATION.jsonl` · `/tmp/**`

## Result

- **Table:** 11 shapes priced with cost, raw n, effective n under three dependence estimates, H3 pairs,
  wall, and what each adjudicates (`docs/PRICE-REPLICATION.md` §2).
- **Recommended first tranche:** `PAIR-3+CTX-2` — 4 arms, pair at 3 reps, context at 2 reps =
  **480 turns / 660 requests / 2,559 remaining**; effective n 66.22 pooled, **31.36** under the binding
  arm's own lag-1.
- **Tranche 2 on promotion:** +3 pair reps (288 turns / 396 requests) → `PAIR-6+CTX-2` = 768 turns /
  **1,056 requests**, effective **62.73** under the binding arm (the first admissible shape that clears
  60 there).
- **Decision rule:** promote iff pooled p95 intervals disjoint in the C-lower direction (P2) **and** all
  three reps show a p50 gap ≥ 100 ms (P1); `not P2` → STOP, no 792 grid; `P2 and not P1` → HOLD.
- **Default revised:** from A\* to `PAIR-3+CTX-2`. Execution carrier to edit:
  `RUN-A*` card `ad214412-c39c-4a47-afb1-2be328e03b1e`; record text `BUDGET-SCHEDULE.md` §7 (card
  `21254578`); the reps split needs an **additive PARM-1 errata** (PARM-1 is frozen).

## Evidence

`python3 -c '…'` (recorded as the verdict row) re-derives every derived number in
`experiments/ptr-engine/measure/price-replication.json` from its own inputs and byte-compares the
canonical re-serialisation with the file — exit 0. Its wall arithmetic reproduces
`BUDGET-SCHEDULE.md` §2's published rows exactly (A\* 576 turns = 4.40 h mean / 6.10 h p90 / 9.60 h
policy; C 192 turns = 1.47 / 2.03 / 3.20 h), which is the independent cross-check that the per-turn
percentiles and the factor were applied as that card applied them.
