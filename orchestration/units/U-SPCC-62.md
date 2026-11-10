# U-SPCC-62 — E2 cell: compaction interval vs rewrite cost and accuracy

## Why

`PREREG-SPCC.md` §E2 asks whether a larger compaction interval lowers rewrite cost
with no accuracy loss until the interval exceeds the distance at which facts stop
being refetched. `f4de200` (U-SPCC-59) made `COMPACT_EVERY` a parameter and a cell
dimension; this is the first cell that varies it.

## What ran

One cell, three arm-variants of `spcc`, same fixture, same model, only the interval
varying:

```
--fixture tasks-v7/TX-03.v1.json --arms spcc --compact-every 12,24,48 --reps 1
--temperature 0 --seed 42 --model occamy-1.0 --base-url http://192.168.2.168:8012/v1
--claim-mode E2 --budget-cap 12094 --run-id e2-compact-2026-11-10
--rows experiments/ptr-engine/measure/rows-e2-compact-2026-11-10.jsonl
```

Dry-run first: gate admitted `12,24,48 × 100 turns × 1 rep` at `n=300`,
`would_send_total=300`, zero requests.

## Result

300 rows, 300 requests, 0 truncated, 0 failed turns, wall 120.78 s.
Cap-gate reconcile delta 0 on all three cells (spent 9367 → 9467 → 9567 → 9667 of
12094; headroom 2427).

| C | value_correct | contract_correct | NONE | wrong | unparsed | graded | total | requests | billed_tokens | compactions |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 18/48 (37.5%) | 18/48 (37.5%) | 28 | 2 | 0 | 48 | 48 | 100 | 16,655 | 8 |
| 24 | 20/48 (41.7%) | 17/48 (35.4%) | 28 | 0 | 0 | 48 | 48 | 100 | 15,807 | 4 |
| 48 | 36/48 (75.0%) | 34/48 (70.8%) | 12 | 0 | 0 | 48 | 48 | 100 | 15,703 | 2 |

Strict exact-match scorecard (`score_longrun.py`, kind-blind) reads 18/48, 17/48,
34/48; the contract-aware grader credits `kind_mismatch_value_correct` of 0, 3, 2.

## Cost

16,655 → 15,807 → 15,703 billed tokens. **Monotone falling.** −848 (−5.09%) from
C=12→24, −104 (−0.66%) from C=24→48; total −952 (−5.72%). The fall is almost
entirely in the first step; C=24→48 is within noise of flat.

## Accuracy

Value 37.5% → 41.7% → 75.0%; contract 37.5% → 35.4% → 70.8%. Band ±2/48 = ±4.2 pp.
C=48 is +33.3 pp over C=12 on value — far outside the band. **Accuracy is not flat;
it rises steeply with C.** The mechanism is visible in the NONE column: 28 → 28 → 12.
Compaction evicts fetched bodies, so more frequent compaction produces more
abstentions, not more wrong answers (wrong is 2, 0, 0).

## Deepest passing distance

Per-distance passes (value, out of 8 per distance):

| C | d2 | d5 | d6 | d8 | d20 | d32 | deepest passing |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 7 | 4 | 4 | 3 | 0 | 0 | **8** |
| 24 | 7 | 4 | 4 | 3 | 2 | 0 | **20** |
| 48 | 8 | 5 | 7 | 6 | 6 | 4 | **32** |

The deepest passing distance moves with C: 8 → 20 → 32. The refetch horizon is set
by the compaction interval, not by a fixture property.

## Falsifier

- *Cost does not fall monotonically* — **not triggered**; it falls at every step.
- *Accuracy drops before the predicted distance* — **not triggered**; accuracy never
  drops as C grows, it rises.

The falsifier is not triggered, but the hypothesis's **"accuracy flat" prediction is
falsified**: accuracy is not flat, it rises by 33 pp from C=12 to C=48. Compaction is
not accuracy-neutral at small C — it is accuracy-destructive. The turnover point the
hypothesis predicts (larger C eventually hurting) was not reached inside {12,24,48}.

## Control

No compaction fired mid-turn. Every increment lands on a turn boundary:
C=12 at 13,25,37,49,61,73,85,97 (8); C=24 at 25,49,73,97 (4); C=48 at 49,97 (2).
First fire at 13/25/49 matches the verified U-SPCC-59 prediction.

## Not done

No ledger write, no doc write — numbers reported for the main agent to record.
