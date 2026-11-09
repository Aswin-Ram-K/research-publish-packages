# COLD-START-SCORE — the inheritance gap, measured

Scores `COLD-START-PROBE` against the eight-item rubric frozen before it ran. Offline: 0 requests,
0 spawns, nothing repaired. Marks are decided from the artefact, never from the probe's own `status`.

## Score: **4.5 / 8**

| # | Item | Mark | Value | Settled by |
|---|---|---|---|---|
| 1 | Objective + verdict | `GAP_DISHONEST` | 0 | `OPERATOR-BRIEF.json` verdict.overall; `P95-POWER.json` per_grid_summary |
| 2 | Spend | `CORRECT` | 1 | `REQUEST-LEDGER.json` |
| 3 | Three holds | `HALF` | 0.5 | `RUN-A*` card description; `GATE-CHAIN.md` §11 |
| 4 | Withdrawals | `HALF` | 0.5 | `WITHDRAWN.json`; `withdrawn_index.py` |
| 5 | Next card + price | `WRONG` | 0 | `task_board_get ad214412`; `PRICE-REPLICATION.md:170` |
| 6 | Frozen thresholds | `CORRECT` | 1 | `PARM-1-ERRATA.md:223-230` |
| 7 | Phantom path | `CORRECT` | 1 | `docs/BUDGET-SCHEDULE.md` absent; `measure/` copy present |
| 8 | Verdict row | `HALF` | 0.5 | `VERDICTS.md:4166-4173, :4216-4233` |

Totals: 3 `CORRECT`, 3 `HALF`, 1 `WRONG`, 0 `GAP_HONEST`, 1 `GAP_DISHONEST`.

## What was got right

The spend is read exactly, including the trap: 1,101 raw / 4,320 cap / 3,219 remaining, with the
1,071 de-duplicated figure kept as a non-deducted diagnostic (`deduction_rule_sound false`). The
withdrawal register, the checker and its two exit codes are right. Four or more frozen thresholds are
exact. And a real phantom was found without repair: `docs/BUDGET-SCHEDULE.md` is cited by
`PRICE-REPLICATION.md:222` and `handoffs/PRICE-REPLICATION.json:27` but lives only in `measure/`.

## The failure worth having

Item 1 is the card's reason for existing. The probe writes `silent` and says "there is NO verdict word
for the thesis". The record is not silent: `OPERATOR-BRIEF.json` records `"overall": "not adjudicable"`
with the missing measurement named, and `P95-POWER.json` supplies the H2 limb the probe omitted — two
of three grids do **not** separate the pair (p50 32.39 / 11.99 ms, p95 −2.35 / −57.65 ms), so H2's sign
is unstable. A gap asserted where the record is clear is `GAP_DISHONEST`, not an honest silence.
Item 5 fails the other way: it trusts `PRICE-REPLICATION` §7's description of the card's *old* text and
asserts the card still prices 792 requests / 12 cells, after the board edit (#960) had already written
660 / 10 cells into the card itself.

## The one thing a fresh session gets wrong, and the smallest edit that would prevent it

**The thesis verdict.** A competent fresh session reads `STATUS.md` and `VERDICTS.md` — the pair it is
told to read first — finds per-hypothesis mechanisms, the 134-row batch aggregate and a gate-chain
blocker chain, and concludes either that no thesis-level verdict exists or that the aggregate *is* the
verdict. It then cannot tell why 660 requests are being held. **Smallest edit (reported, not made):** one
line in the objective section of `orchestration/STATUS.md` — "Operator thesis: `not adjudicable` on H1,
H2 and H3; missing measurement = one four-arm grid with ≥60 usable timings per arm; do not read the
batch aggregate as its verdict." This is a one-line addition to a file the successor already opens; it
would have moved item 1 from `GAP_DISHONEST` to `CORRECT` and made the hold legible.

**Is the record sufficient for a successor today? No.** One fact is missing from the first-read pair:
the explicit thesis-verdict line above. Everything else the probe got wrong (the card's price, the
hold-clearing cards) is present on the card and in the board thread — discoverable, just not first-read.
