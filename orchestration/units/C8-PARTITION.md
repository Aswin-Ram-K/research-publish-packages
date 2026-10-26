# C8-PARTITION — disjoint partition of the 774 miss-law rows

**Unit.** C8-PARTITION · automated, offline, zero requests · bound: 16 tool calls · status: done.
**Closes:** gap #5 of `orchestration/GAPS-INVENTORY.md` (the withdrawn C8 bookkeeping reading needed a disjoint sum).
**Writes:** `experiments/miss-law/FIT-GAP-V2.md` (append §7) · `experiments/miss-law/FIT-GAP.md` (6-line tombstone prepended, rest byte-intact) · this card · `orchestration/handoffs/C8-PARTITION.json`.

## Objective
Partition all 774 rows of `experiments/miss-law/rows.jsonl` into disjoint classes summing exactly once, with a stated
predicate per class; state the law identity holding per class; append §7 to V2; turn FIT-GAP.md into a tombstone.

## Result
| # | class | rows |
|---|---|---:|
| 1 | no `L_app` (prime/warm/cold) | 387 |
| 2 | fit, cache not reported | 83 |
| 3 | fit, reported, residual 0 | 160 |
| 4 | fit, reported, residual ≠ 0 | 144 |
| | **sum** | **774** |

Identity `A` (`uncached == prompt − cached`) holds 304/304 reported + 83/83 null (cached=0).
Identity `P` (`uncached == residue + L_app`) holds **0** of 387 fit rows — the record's claim, confirmed.

## Bound honoured
16 tool calls or fewer; no `ask_user_question`; no writes outside the four declared paths.

## Method
`residual(r) = cached_tokens − floor(prompt_tokens/grid)*grid`, grid 64 sglang / 1056 vllm (V2 §2's definition);
partition on `r.get('L_app') is None`, `r['cached_tokens'] is None`, `residual == 0`. Assertions on the sum, the
server columns, and the whole-grid-multiple property are asserted in the generating script, not assumed.
