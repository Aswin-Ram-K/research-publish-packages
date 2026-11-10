# U-SPCC-65 — record E2 and E3 in the ledger and the three state pages

## Why

E2 (`U-SPCC-62`, commit `878ea5f`) and E3 (`U-SPCC-64`, commit `44c297a`) both ran and both
reported their numbers in their own unit docs, but neither wrote the ledger or the state
pages. This unit records them, exactly as measured, with no re-scoring and no new requests.

## What was written

- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — two 7-column rows
  (E2, E3). Column count before and after: `15×10, 7×3, 21×7` → `15×10, 7×3, 23×7`.
- `docs/STATE.md` — `## U-SPCC-62` and `## U-SPCC-64` sections; `Last updated` line moved to
  U-SPCC-65.
- `journal/2026-11-10.md` — the same two sections.
- `orchestration/STATUS.md` — the same two sections.

## E2 — the "accuracy flat" prediction is falsified

| C | value | contract | NONE | wrong | billed | compactions |
|---:|---:|---:|---:|---:|---:|---:|
| 12 | 18/48 | 18/48 | 28 | 2 | 16,655 | 8 |
| 24 | 20/48 | 17/48 | 28 | 0 | 15,807 | 4 |
| 48 | 36/48 | 34/48 | 12 | 0 | 15,703 | 2 |

Cost monotone, −5.72% total, almost all in the first step. Accuracy **not flat**: 37.5% →
41.7% → 75.0%, +33.3 pp, far outside ±2/48. Mechanism is `NONE` 28 → 28 → 12, not wrong
answers. Deepest passing distance 8 → 20 → 32. No mid-turn compaction; first fire at
13/25/49 matching `U-SPCC-59`. The predicted turnover point was not reached inside
{12,24,48}.

## E3 — the cliff is eviction, not position

| arm | value | contract | NONE | wrong | billed |
|---|---:|---:|---:|---:|---:|
| `spcc` | 48/48 | 48/48 | 0 | 0 | 17,129 |
| `masking-no-fetch` | 42/48 | 42/48 | 0 | 6 | 16,265 |

Per-distance contract: `spcc` 10/10, 10/10, 10/10, 9/9, 9/9 at d2/d8/d20/d32/d64; masking
9/10, 8/10, 8/10, 8/9, 9/9. Control holds: `masked_rows` 0, `compactions` 0, `evicted` 0, no
`[MASKED` marker, `expected_present` 96/96 true including all nine d64 probes.

**Verdict, stated plainly: the cliff is eviction, not position.** At d64 with the body
present both arms score 9/9, including the deepest probe at turn 99 (`cp.TX-04.f05.d64`,
expected 4054, got 4054). The cliff vanishes. The model can retrieve a fact it was given at
distance 64; it fails when the fact has been taken away.

**Second result.** The arms differ by 6/48 (12.5 pp) with **no distance gradient** — failures
at d2/d8/d20/d32, d64 perfect in both. All six are well-formed `ANSWER: NUM` with plausible
wrong values (four cross-document, two within-document confusions), no abstentions. This is a
prompt-format attribution effect, not a residual cliff, and must not be pooled with it.

**Scoring note.** `score_longrun.score_answer_contract_rows` returns `denominator_mismatch`
on a multi-arm rows file (it sums distinct checkpoint ids across every `(arm, rep)` key: 96
vs 48). Graded per arm, the only reading satisfying its own denominator rule.

## Verification

`python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Not done

No re-scoring, no new requests, no edit to `PREREG-SPCC.md` or `PREREG-SPCC.json`.
