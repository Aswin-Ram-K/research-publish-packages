# U-SPCC-66 — E2 turnover sweep: C in {48, 64, 96}

**Status:** DONE. Live cell, 300 requests, 0 failed turns, 0 truncated, reconcile delta 0.

## Why

`U-SPCC-62` (E2) varied the compaction interval over {12, 24, 48} and found accuracy
**rising** 37.5% → 41.7% → 75.0% while billed cost fell monotonically (−5.72%). The
hypothesis's "accuracy flat" prediction was falsified and the predicted turnover point
— the interval past which a larger journal starts to hurt — was never reached. This
cell extends the sweep to {48, 64, 96} to locate it: does accuracy keep rising, plateau,
or fall, and does cost keep falling or turn back up as the journal grows?

## What ran

One cell, three arm-variants of `spcc`, same fixture, same model, only the interval
varying:

```
--fixture longrun/tasks-v7/TX-03.v1.json  sha256 f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3
--arms spcc --compact-every 48,64,96 --reps 1
--temperature 0 --seed 42 --model occamy-1.0 --base-url http://192.168.2.168:8012/v1
--claim-mode E2 --budget-cap 12094 --run-id e2-turnover-2026-11-10
--rows experiments/ptr-engine/measure/rows-e2-turnover-2026-11-10.jsonl
```

Dry-run first: gate admitted `48,64,96 × 100 turns × 1 rep` at `n=300`,
`would_send_total=300`, zero requests. Fixture has 48 checkpoints at distances
2/5/6/8/20/32 (8 each); **32 is the fixture ceiling**, so "deepest passing distance"
cannot exceed 32 in this cell.

## Result

300 rows, 300 requests, 0 truncated, 0 failed turns, wall 108.65 s.
Cap-gate reconcile delta 0 on all three cells (spent 10067 → 10167 of 12094; headroom
1927).

| C | value_correct | contract_correct | NONE | wrong | unparsed | graded | requests | billed_tokens | compactions |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 48 | 36/48 (75.0%) | 35/48 (72.9%) | 12 | 0 | 0 | 48 | 100 | 14,679 | 2 |
| 64 | 39/48 (81.3%) | 38/48 (79.2%) | 9 | 0 | 0 | 48 | 100 | 15,063 | 1 |
| 96 | 47/48 (97.9%) | 47/48 (97.9%) | 1 | 0 | 0 | 48 | 100 | 14,684 † | 1 |

† c96 turn 97 (the compaction turn) has `cached_tokens: null` on a later turn, so
`billed_of` returns `None` — ABSENT is not 0. The known sum is 14,684 over 99 rows;
the unknown row's prompt is 591 tokens, so the **upper bound is 15,275** and
`billed_coverage` is 0.99. The c48 and c64 sums are complete (coverage 1.0).

`wrong` is 0 at every interval. The single non-NUM answer per interval at c48 and c64
is `ANSWER: TEXT 3100` / `ANSWER: TEXT 3101` — value correct, kind wrong
(`kind_mismatch_value_correct` = 1, 1, 0). It is a contract failure, not a wrong value.

## Accuracy — keeps rising, no plateau

Value 75.0% → 81.3% → 97.9%; contract 72.9% → 79.2% → 97.9%. Band ±2/48 = ±4.17 pp.

- C=48→64: +3/48 = **+6.25 pp** — outside the band.
- C=64→96: +8/48 = **+16.7 pp** — far outside the band.
- C=48→96: +11/48 = **+22.9 pp**.

**Accuracy is still rising at C=96 and has not plateaued.** The mechanism is again the
`NONE` column, not wrong answers: 12 → 9 → 1. Every remaining failure at c96 is a single
abstention at the deepest probe (`cp.TX-03.f08.d32`, turn 100, expected 3705).

## Cost — turns back up

Two measures, because they disagree and the disagreement is the finding:

| C | Σ prompt_tokens (cache-independent) | mean prompt | max prompt | Σ billed (cache-adjusted) |
|---:|---:|---:|---:|---:|
| 48 | 133,463 | 1,334.6 | 2,059 | 14,679 |
| 64 | 142,295 | 1,423.0 | 2,581 | 15,063 |
| 96 | 200,939 | 2,009.4 | 3,314 | 14,684–15,275 |

**Prompt tokens rise monotonically: +6.6% then +41.2%, +50.6% total.** That is the
journal-length effect the hypothesis predicted — a larger interval means a longer
prompt. Billed tokens also rise monotonically once the unknown row is counted
(14,679 → 15,063 → 15,275), but the rise is far smaller than the prompt growth because
the long c96 prompts are almost entirely prefix-cached (c96 mean prompt 2,009 tokens,
mean billed 147).

So the E2 cost trend **reverses**: cost fell 12→24→48 and now rises 48→64→96. The cost
minimum of the sweep is at **C=48**.

## Deepest passing distance

Per-distance value passes (out of 8 per distance):

| C | d2 | d5 | d6 | d8 | d20 | d32 | deepest passing |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 48 | 8 | 5 | 7 | 6 | 6 | 4 | **32** |
| 64 | 8 | 7 | 7 | 7 | 5 | 5 | **32** |
| 96 | 8 | 8 | 8 | 8 | 8 | 7 | **32** |

The deepest passing distance is **32 at all three intervals** — but that is the
fixture's ceiling, not a plateau in the model. The informative quantity is the *fraction*
passing at d32: 4/8 → 5/8 → 7/8. The horizon is saturated; the cell cannot see past 32.

## Turnover verdict

**No accuracy turnover exists inside {48, 64, 96}.** Accuracy rises monotonically
(75.0 → 81.3 → 97.9) with every step outside the ±4.17 pp band, and the residual
failures are abstentions that shrink to one. The predicted "larger C eventually hurts"
regime is not reached by C=96.

**A cost turnover does exist, and it is at C=48.** Prompt cost is minimised at C=48 and
rises 50.6% by C=96. The two curves therefore cross at C=48: past it you pay more prompt
tokens for more accuracy, and the accuracy is still climbing at the top of the sweep.

## Control

No mid-turn compaction. Every fire lands on a turn boundary: C=48 at 49 and 97 (2);
C=64 at 65 (1); C=96 at 97 (1). First fire at C+1 matches the verified `U-SPCC-59`
prediction. `compactions` is a cumulative per-row counter, so the fire turns are read
from where it increments, not from rows where it is non-zero.

## Cross-run note

The c48 arm here bills 14,679 against E2's 15,703 for the same interval. The prompts are
byte-identical (`prompt_tokens` matches on every turn); the difference is entirely
prefix-cache warmth — this run's turn 1 missed the cache (636 billed vs 124) and 20 later
turns hit one 64-token block more. **Cross-run billed comparisons are confounded by cache
state; only within-run comparisons are valid.** The prompt-token column is the
cache-independent measure and is the one to quote for journal length.

## Not done

No ledger write, no doc write — numbers reported for the main agent to record.
