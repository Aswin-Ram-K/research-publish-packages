# RESULTS-KINDS-2 — TX-SUP and TX-HOP, masking vs fetch (one replication each)

## Fixtures and run identity

| Fixture | task_id | fixture_sha256 | N (turns) | checkpoints |
|---|---|---|---|---|
| TX-SUP.v1.json | TX-SUP | `75ab558b10aaf7712f6dd88824aa3d36f028df1726654e61208f7d7be5d3dc0a` | 103 | 48 (12 per bucket d∈{2,6,20,32}) |
| TX-HOP.v1.json | TX-HOP | `860aad568c97d227a756111c359df19bdd2412e8db44f52644e8b23e2962fca0` | 180 | 48 (12 per bucket d∈{2,6,20,32}) |

Run parameters (all four runs): `temperature=0`, `seed=42`, model `occamy-1.0`, claim-mode `H2`, `--budget-cap 12094`. Masking arm: `--tools` absent (tools_mode `off`). Fetch arm: `--tools fetch` (tools_mode `on:fetch`).

Row-1 gate: every row carries the fixture's `task_id`, the fixture's `fixture_sha256`, `temperature=0.0`, `seed=42`, and the expected `tools_mode` (`off` for masking, `on:fetch` for fetch). Verified on first row of each file.

## Activation gates

| Fixture | Arm | fetch_rows (rows with fetch_rows>0) | Gate (≥40 for fetch arm; 0 for masking arm) | Verdict |
|---|---|---|---|---|
| TX-SUP | masking-no-fetch | 0 | 0 (required) | PASS |
| TX-SUP | bounded-context-fetch | 42 | ≥40 | PASS |
| TX-HOP | masking-no-fetch | 0 | 0 (required) | PASS |
| TX-HOP | bounded-context-fetch | 28 | ≥40 | **FAIL** (does not count as measuring retrieval) |

HOP fetch arm also produced 30 retrieval outcomes (all `OK`) but only 28 fetching turns, below the 40-turn activation floor. Per instructions, this run is reported but does not count as measuring retrieval.

## Scoring — contract-level / value-level (out of 12 per bucket)

### TX-SUP

| distance | masking contract | masking value | fetch contract | fetch value |
|---|---|---|---|---|
| 2 | 11/12 | 11/12 | 1/12 | 1/12 |
| 6 | 0/12 | 0/12 | 10/12 | 10/12 |
| 20 | 0/12 | 0/12 | 3/12 | 3/12 |
| 32 | 0/12 | 0/12 | 4/12 | 4/12 |
| **total** | **11/48** | **11/48** | **18/48** | **18/48** |

SUP stale-recall (answers equal to the fixture's stale value): masking arm 1/48, fetch arm 2/48.

### TX-HOP

| distance | masking contract | masking value | fetch contract | fetch value |
|---|---|---|---|---|
| 2 | 12/12 | 12/12 | 9/12 | 9/12 |
| 6 | 0/12 | 0/12 | 0/12 | 0/12 |
| 20 | 0/12 | 0/12 | 0/12 | 0/12 |
| 32 | 0/12 | 0/12 | 0/12 | 0/12 |
| **total** | **12/48** | **12/48** | **9/48** | **9/48** |

## HOP target-row position distribution

Target row position in the B-table (0-based) across 48 checkpoints:

`{0: 8, 1: 16, 2: 20, 3: 4}` (not uniform; irregular — chain→position map `{1:2,2:0,3:1,4:0,5:2,6:2,7:1,8:2,9:1,10:1,11:2,12:3}`; `chain % 4 == position` is **false**, so the position is not trivially predictable from the chain index, unlike the earlier (voided) fixture).

## HOP masking correlation

Accuracy (contract-correct checkpoints) split by whether the earlier (key) fact was masked (distance ≥ 6):

| Arm | unmasked (d≤5) | masked (d≥6) |
|---|---|---|
| masking-no-fetch | 12/12 | 0/36 |
| bounded-context-fetch | 9/12 | 0/36 |

Both arms answer correctly only when the earlier fact is inside the masking window (unmasked); accuracy is 0/36 on masked checkpoints.

## Requests spent and cap arithmetic

| Run | Rows (= requests) |
|---|---|
| TX-SUP masking | 103 |
| TX-SUP fetch | 145 (103 turn + 42 fetch) |
| TX-HOP masking | 180 |
| TX-HOP fetch | 208 (180 turn + 28 fetch) |
| **Total (this unit)** | **636** |

Cap: 12,094. Pre-unit spent: 5,125. Headroom before: 6,969. Spent this unit: 636 (≤ 800 ceiling). Headroom after: 6,333. Activation-blocked run (HOP fetch) still consumed its 208 requests; no rerun performed (one replication per arm).

## Artifacts

- `experiments/ptr-engine/measure/rows-sup2-masking.jsonl`
- `experiments/ptr-engine/measure/rows-sup2-fetch.jsonl`
- `experiments/ptr-engine/measure/rows-hop2-masking.jsonl`
- `experiments/ptr-engine/measure/rows-hop2-fetch.jsonl`
