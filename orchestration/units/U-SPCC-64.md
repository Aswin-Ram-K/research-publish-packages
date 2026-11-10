# U-SPCC-64 — E3: the cliff is eviction, not position

**Status:** DONE. Live cell, 200 requests, 0 failed turns, 0 truncated.

## Why

`PREREG-SPCC.md` §E3 asks whether the observed distance cliff is a property of **position**
or of **eviction**. E1 already showed the value is *absent from the prompt* at the failing
checkpoints, which is consistent with eviction but does not separate the two explanations:
a model that cannot retrieve at distance 64 would fail either way. E3 removes the
confound — every fact body is delivered at its introduction turn and **never masked and
never compacted**, so at the d64 probe the body is still in the prompt. If the cliff
persists, it is position. If it vanishes, it was eviction.

## Cell

```
--fixture tasks-v7/TX-04.v1.json   sha256 0c836872225fc0d6198aa86b3c72ec3dfada0b23f2541cde49adc53429703885
--arms spcc,masking-no-fetch --window-turns 200 --compact-every 200
--reps 1 --temperature 0 --seed 42 --model occamy-1.0
--claim-mode E3 --budget-cap 12094 --run-id e3-retain-2026-11-10
--rows measure/rows-e3-retain-2026-11-10.jsonl
```

48 checkpoints at d2 10 / d8 10 / d20 10 / d32 9 / d64 9; deepest probe turn 99
(`cp.TX-04.f05.d64`). Window 200 over 100 turns masks nothing; interval 200 compacts
nothing. 200 requests, programme spend 9,667 → 9,867 of 12,094.

## Control check — HOLDS

| check | spcc | masking-no-fetch |
|---|---|---|
| `masked_rows != 0` | 0 rows | 0 rows |
| `compactions != 0` | 0 rows | 0 rows |
| `evicted != 0` | 0 rows | 0 rows |
| `masked_entry` non-empty | 0 rows | 0 rows |
| `[MASKED` in any row | 0 rows | 0 rows |
| `expected_present` at every probe | 96/96 `True` | 96/96 `True` |

`expected_present_source` is `prompt-digit-boundary` on all 96 checkpoint rows: the
runner's own digit-boundary scan found the expected value in the prompt at every probe,
including all nine d64 probes. No masking fired, no compaction fired. The control is
intact — this is a retention cell.

## Per arm

| arm | value_correct | contract_correct | NONE | wrong | unparsed | graded | total | requests | billed_tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spcc | 48 | 48 | 0 | 0 | 0 | 48 | 48 | 100 | 17,129 |
| masking-no-fetch | 42 | 42 | 0 | 6 | 0 | 48 | 48 | 100 | 16,265 |

`billed_tokens` is the whole-cell figure (all 100 rows per arm, `billed_source: reported`).
Reconciliation delta 0 on both arms (`reconcile_delta_total: 0`, within tolerance).

## Per distance — contract_correct / n

| arm | d2 | d8 | d20 | d32 | d64 |
|---|---|---|---|---|---|
| spcc | 10/10 | 10/10 | 10/10 | 9/9 | **9/9** |
| masking-no-fetch | 9/10 | 8/10 | 8/10 | 8/9 | **9/9** |

Measured noise floor on this endpoint: temperature 0 + seed 42 is not reproducible,
±2/48 = ±4.2 pp. Every figure above carries that band.

## Verdict — the cliff is eviction

**At d64 with the body present, both arms score 9/9.** All nine d64 probes are correct in
both arms, including the deepest probe at turn 99 (`cp.TX-04.f05.d64`, expected 4054, got
4054, body present). The cliff does not persist. It vanishes.

This is the clean outcome, not the falsifier: the distance cliff observed in the earlier
cells is a property of **eviction**, not of position. The model can retrieve a fact it was
given at distance 64; it fails when the fact has been taken away. The headline may be
stated as *cannot retrieve what was taken away*, not *cannot retrieve what it was given*.

## Second result — the arms are not identical when both retain

The two arms differ by 6/48 = 12.5 pp (48/48 vs 42/48), which is outside the ±4.2 pp band,
and the difference has **no distance gradient**: the six failures sit at d2, d8, d20 and
d32, and d64 is perfect in both. So this is not a residual cliff — it is an arm-format
effect on attribution:

| checkpoint | d | turn | expected | answered | error kind |
|---|---:|---:|---|---|---|
| `cp.TX-04.f09.d2` | 2 | 30 | 4091 | 4011 | cross-document (f01's VAL_A) |
| `cp.TX-04.f02.d8` | 8 | 10 | 4021 | 4061 | cross-document (f06's VAL_A) |
| `cp.TX-04.f07.d8` | 8 | 39 | 4072 | 4102 | cross-document (f10's VAL_B) |
| `cp.TX-04.f08.d20` | 20 | 31 | 4083 | 4073 | cross-document (f07's VAL_C) |
| `cp.TX-04.f12.d20` | 20 | 73 | 4123 | 4124 | within-document (VAL_C → VAL_D) |
| `cp.TX-04.f02.d32` | 32 | 34 | 4023 | 4022 | within-document (VAL_C → VAL_B) |

Every failure is a well-formed `ANSWER: NUM` with a plausible wrong value — four
cross-document confusions and two within-document symbol confusions. None is an
abstention, none is unparsed. The masking arm's `WORKING SET INDEX` prompt format costs
attribution accuracy at *all* distances, which is a different mechanism from the distance
cliff and must not be pooled with it.

## Scoring note

`score_longrun.score_answer_contract_rows` returns `denominator_mismatch` when handed a
multi-arm rows file: it sums distinct checkpoint ids across every `(arm, rep)` key and
compares that total to the fixture's checkpoint count (96 vs 48 here). The cell was graded
per arm, which is the only reading that satisfies the function's own denominator rule.

## Artifacts

- `experiments/ptr-engine/measure/rows-e3-retain-2026-11-10.jsonl` — 200 rows
- `experiments/ptr-engine/longrun/manifests/e3-retain-2026-11-10-spcc-r1-c200-w200.json`
- `experiments/ptr-engine/longrun/manifests/e3-retain-2026-11-10-masking-no-fetch-r1-c200-w200.json`
