# PROMPT-O1 — repair WITHDRAWN (RESTORE-O1, offline)

## Status: the repair was wrong; the corpus is restored

`rows.jsonl` is now `rows.pre-correction.jsonl` (sha256 `dc0774d8...101eff`, 355 rows).
The repaired corpus is kept as `rows.repaired-DO-NOT-USE.jsonl` (sha256 `58c95fae...9269c`)
and must not be cited.

## Why the repair is falsified (re-measured twice, live)

Fresh arm-R re-measurements reproduced the published means: GROUND-TRUTH-R to -0.08 %,
and GROUND-TRUTH-PROMPT = **589.2029** uncached/turn (salt 63564242b54d8609, 69/71
measured, non-200 = 0) vs restored 583.14 (-1.0 %) and vs repaired 391.48 (+50.5 %).

The decisive invariant: **this stack credits cached prefix only in 64-token blocks**.

| corpus | gcd(cached_tokens) | off-grid values |
|---|---|---|
| fresh GROUND-TRUTH-PROMPT | 64 | 0 |
| restored pre-correction | 64 | 0 |
| R2-P1-O1 | 64 | 0 |
| repaired | **1** | **40** (1409, 1793, 2433, 2753, 3777, ...) |

A row set that is off the 64-grid cannot be a value this server reported. The repair
copied gaps from `cells/R2-P1-O1` (itself a 390.80 outlier vs the fresh 589.20), which
also explains why its `R` mean "matched the reference cell's 390.80".

## Withdrawn figures

- `A − R = +137.82` [124.02, 151.61] — **withdrawn**, rests on the repaired cell.
- repaired `R` mean 391.48, hit rate 0.9683 — **withdrawn**.
- the earlier claim `A − R = −53.85 (pointer wins 9.2 %)` is **restored** (it was the
  pre-correction value), see `analysis.json`.

## Restored means (mean uncached tokens / turn, n = 71 per arm)

A 529.2958 · C 547.0845 · R 583.1408 · H 961.9718 · C0 709.8592
**A − R = −53.8451, 95 % CI [−96.6197, −10.4085]** — excludes zero, sign is negative.

## Guard

`papers/context-cache/recompute.py` now asserts the 64-token grid on every
declared-SGLang cell (`assert_sglang_grid`, CLI `grid-invariant`); proof script
`papers/context-cache/grid_guard_selftest.py` shows PASS → FAIL(cached_tokens=1409) → PASS.
Zero live requests were made; GROUND-TRUTH-* and R2-P1-O1 were not modified.
