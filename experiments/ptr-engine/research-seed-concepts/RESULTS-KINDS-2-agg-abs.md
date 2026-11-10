# RESULTS-KINDS-2 — AGG and ABS cells

Source rows (not modified):
- `experiments/ptr-engine/measure/rows-agg2-2026-11-09.jsonl` (TX-AGG, 242 rows: 100 masking + 142 fetch)
- `experiments/ptr-engine/measure/rows-abs2-2026-11-09.jsonl` (TX-ABS, 242 rows: 100 masking + 142 fetch)

Fixtures:
- `experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json` (sha256 `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03`)
- `experiments/ptr-engine/longrun/tasks-v7/TX-ABS.v1.json` (sha256 `dacd814b18f3ba8bd856ea73f6262b5850758f4e8ed42f8dd7479e222bab9535`)

Scorer: `score_longrun.py --answer-contract`. Zero fixture/runner/scorer changes. One replication per arm. `temperature=0`, `seed=42`, `generation=gen-7`.

## 1. Preflight / row-1 gates

Both fixtures load offline; projected counts 100 requests per arm (masking) and 148 per arm (fetch = 100 turns + 48 fetch-round pool). Every first row per (fixture, arm) carries the correct `task_id`, matching `fixture_sha256`, `temperature: 0.0`, `seed: 42`, and the expected `tools_mode` (`off` for masking, `on:fetch` for fetch).

## 2. Activation gates

- Masking arm: `fetch_rows = 0` on all 200 masking rows (AGG and ABS) — gate met.
- Fetch arm: `fetch_rows` first becomes positive at row 10 (AGG) / row 8 (ABS); final totals 82 (AGG) and 50 (ABS) — both ≥ 40 — gate met.

## 3. AGG (TX-AGG) — contract-level and value-level /12

`kind_mismatch_value_correct = 0` in every cell, so the two levels coincide.

| Arm | d=2 (n=12) | d=6 (n=12) | d=20 (n=12) | d=32 (n=12) | Total |
|---|---|---|---|---|---|
| masking-no-fetch contract | 0/12 | 0/12 | 0/12 | 0/12 | 0/48 |
| masking-no-fetch value | 0/12 | 0/12 | 0/12 | 0/12 | 0/48 |
| bounded-context-fetch contract | 0/12 | 0/12 | 1/12 | 3/12 | 4/48 |
| bounded-context-fetch value | 0/12 | 0/12 | 1/12 | 3/12 | 4/48 |

Fetch arm additionally has `ungradeable = 4`, `abstained = 18`; masking arm has `abstained = 28`, `ungradeable = 0`. Multi-round fetch turns: 29 fetch rounds billed as `turn-initial` rows (13 turns with a second billed turn row), so fetch-arm row count is 142 for 100 turns.

### AGG failure-mode split (of 48 checkpoints per arm)

| Mode | masking-no-fetch | bounded-context-fetch |
|---|---:|---:|
| correct value | 0 | 4 |
| arithmetic wrong value | 20 | 22 |
| abstention (`ANSWER: NONE`) | 28 | 18 |
| ungradeable | 0 | 4 |

By bucket (wrong value / abstention / ungradeable):

| Bucket | masking | fetch |
|---|---|---|
| d=2 | 10 / 2 / 0 | 10 / 2 / 0 |
| d=6 | 5 / 7 / 0 | 5 / 7 / 0 |
| d=20 | 3 / 9 / 0 | 4 / 5 / 2 |
| d=32 | 2 / 10 / 0 | 3 / 4 / 2 |

Partial-aggregation check: 1 masking and 2 fetch wrong answers equal a subset-sum of that group's four values; the remaining wrong answers are unrelated magnitudes (not off-by-one-group-member). No masking answer is correct at any distance; the masking arm abstains on 28/48 aggregates.

## 4. ABS (TX-ABS) — contract-level and value-level /12

| Arm | d=2 (n=12) | d=6 (n=12) | d=20 (n=12) | d=32 (n=12) | Total |
|---|---|---|---|---|---|
| masking-no-fetch contract | 3/12 | 0/12 | 0/12 | 0/12 | 3/48 |
| masking-no-fetch value | 3/12 | 0/12 | 0/12 | 0/12 | 3/48 |
| bounded-context-fetch contract | 6/12 | 6/12 | 3/12 | 0/12 | 15/48 |
| bounded-context-fetch value | 6/12 | 6/12 | 3/12 | 0/12 | 15/48 |

### ABS four-way classification (per arm, per bucket)

Counts out of 12 per bucket. Categories: correct refusal = `ANSWER: NONE` on an absent checkpoint; false refusal = `ANSWER: NONE` on an answerable checkpoint; correct value; wrong value; ungradeable.

Masking arm (`masking-no-fetch`):

| Bucket | correct refusal | false refusal | correct value | wrong value | ungradeable |
|---|---:|---:|---:|---:|---:|
| d=2 | 3 | 6 | 3 | 0 | 0 |
| d=6 | 3 | 8 | 0 | 1 | 0 |
| d=20 | 3 | 5 | 0 | 4 | 0 |
| d=32 | 3 | 5 | 0 | 4 | 0 |
| total | 12 | 24 | 3 | 9 | 0 |

Fetch arm (`bounded-context-fetch`):

| Bucket | correct refusal | false refusal | correct value | wrong value | ungradeable |
|---|---:|---:|---:|---:|---:|
| d=2 | 3 | 2 | 6 | 1 | 0 |
| d=6 | 3 | 1 | 6 | 1 | 1 |
| d=20 | 2 | 1 | 3 | 6 | 0 |
| d=32 | 0 | 3 | 0 | 7 | 2 |
| total | 8 | 7 | 15 | 15 | 3 |

The masking arm over-refuses: it emits `ANSWER: NONE` on 24 of the 36 answerable checkpoints (66.7%) and answers correctly on only 3 (all at d=2). It does correctly refuse all 12 absent checkpoints. The fetch arm refuses only 7 answerable checkpoints and correctly refuses 8 of 12 absent ones, but gives a value on 2 absent checkpoints (counted as wrong value) and is ungradeable on 3.

## 5. Request accounting

| File / arm | Rows | Billed requests |
|---|---:|---:|
| AGG masking-no-fetch | 100 | 100 |
| AGG bounded-context-fetch | 142 | 142 |
| ABS masking-no-fetch | 100 | 100 |
| ABS bounded-context-fetch | 142 | 142 |
| **Total this unit** | **484** | **484** |

Unit ceiling 800 requests — 484 spent, 316 unused. Global cap 12,094. Recorded spend across all `rows-*.jsonl` after this unit (row-billing rule) = 6,288; cap-gate ledger reports 6,523. Headroom ≈ 5,571–5,806 depending on ledger.

## 6. Notes / limitations

- Single replicate (rep 1) per cell; no variance estimate.
- ABS fetch arm has 42 billed `turn-initial` rows (multi-round fetches); scorer counts one `turn` row per checkpoint (48), matching the /12 denominators above.
- AGG expected values are aggregates of ≥2 facts; no single tool body contains any expected value (reachability disabled by construction, per KINDAGG).
- No fixture, row, runner, or scorer file was modified; no model request was made beyond the 484 above.
PY