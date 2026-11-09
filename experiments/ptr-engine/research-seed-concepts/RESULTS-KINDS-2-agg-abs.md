# RESULTS-KINDS-2 — TX-AGG and TX-ABS, masking vs fetch (one replication each)

## Fixtures and run identity

| Fixture | task_id | fixture_sha256 | N (turns) | checkpoints |
|---|---|---|---|---|
| TX-AGG.v1.json | TX-AGG | `178042c254f7b732f57603985de35adf8e3722f80507219103c0f7b259e81b03` | 100 | 48 (12 per bucket d∈{2,6,20,32}) |
| TX-ABS.v1.json | TX-ABS | `dacd814b18f3ba8bd856ea73f6262b5850758f4e8ed42f8dd7479e222bab9535` | 100 | 48 (12 per bucket d∈{2,6,20,32}) |

Run parameters (all four runs): `temperature=0.0`, `seed=42`, model `occamy-1.0-NVFP4`, engine `sglang`, claim-mode `none`, generation `gen-7`. Masking arm: `--tools` absent (`tools_mode` `off`). Fetch arm: `--tools fetch` (`tools_mode` `on:fetch`). Replication: `rep=1` for every row.

Row-1 gate: every row carries the fixture's `task_id`, the fixture's `fixture_sha256`, `temperature=0.0`, `seed=42`, and the expected `tools_mode` (`off` for masking, `on:fetch` for fetch). Verified on first row of each file. No row failed `request_identity_complete`.

## Activation gates

| Fixture | Arm | fetch_rows (rows with fetch_rows>0) | masked_rows (rows with masked_rows>0, sum) | Gate | Verdict |
|---|---|---|---|---|---|
| TX-AGG | masking-no-fetch | 0 | 39 (sum 51) | fetch 0 required | PASS |
| TX-AGG | bounded-context-fetch | 29 | 58 (sum 664) | fetch ≥40 | **FAIL** (does not count as measuring retrieval) |
| TX-ABS | masking-no-fetch | 0 | 12 (sum 12) | fetch 0 required | PASS |
| TX-ABS | bounded-context-fetch | 42 | 18 (sum 36) | fetch ≥40 | PASS |

AGG fetch arm produced 29 fetching turns (fetch_rows sum 82) and 4 retrieval outcomes all `OK` plus one `NOT_FOUND` and one `STALE_OR_REVOKED` (77 `OK`/4 `NOT_FOUND`/1 `STALE_OR_REVOKED` across the run), but only 29 turns with `fetch_rows>0`, below the 40-turn activation floor. Per instructions this run is reported but does not count as measuring retrieval. ABS fetch arm met the floor with 42 fetching turns (fetch_rows sum 50; retrieval outcomes 46 `OK`/3 `NOT_FOUND`/1 `SCOPE_UNGRANTED`).

## Scoring — contract-level / value-level (out of 12 per bucket)

### TX-AGG

| distance | masking contract | masking value | fetch contract | fetch value |
|---|---|---|---|---|
| 2 | 0/12 | 0/12 | 0/12 | 0/12 |
| 6 | 0/12 | 0/12 | 0/12 | 0/12 |
| 20 | 0/12 | 0/12 | 1/12 | 1/12 |
| 32 | 0/12 | 0/12 | 3/12 | 3/12 |
| **total** | **0/48** | **0/48** | **4/48** | **4/48** |

AGG failure split (48 checkpoints per arm):

| Arm | correct | wrong value | abstention (NONE) | ungradeable |
|---|---|---|---|---|
| masking-no-fetch | 0 | 20 | 28 | 0 |
| bounded-context-fetch | 4 | 22 | 18 | 4 |

By bucket (wrong value / abstention / ungradeable; correct shown only where nonzero):

- masking: d2 10 wrong + 2 abstain; d6 5 wrong + 7 abstain; d20 3 wrong + 9 abstain; d32 2 wrong + 10 abstain.
- fetch: d2 10 wrong + 2 abstain; d6 5 wrong + 7 abstain; d20 4 wrong + 5 abstain + 2 ungradeable + 1 correct; d32 3 wrong + 4 abstain + 2 ungradeable + 3 correct.

Partial-sum check: of the 42 wrong values across both arms, only 3 equal a subset sum of the four member `VALUE`s of the group (three of four members); none equals a single omitted or duplicated member. The remaining wrong values are not simple partial sums.

Two fetch-arm turns truncated at the token limit (`turn 91`, `turn 97`, `stop_reason=length`) and are counted as failed turns; their checkpoints score as ungradeable/abstention per the row.

### TX-ABS

| distance | masking contract | masking value | fetch contract | fetch value |
|---|---|---|---|---|
| 2 | 3/12 | 3/12 | 6/12 | 6/12 |
| 6 | 0/12 | 0/12 | 6/12 | 6/12 |
| 20 | 0/12 | 0/12 | 3/12 | 3/12 |
| 32 | 0/12 | 0/12 | 0/12 | 0/12 |
| **total** | **3/48** | **3/48** | **15/48** | **15/48** |

ABS five-way classification (48 checkpoints per arm):

| Arm | correct refusal (NONE on absent) | false refusal (NONE on answerable) | correct value | wrong value | ungradeable |
|---|---|---|---|---|---|
| masking-no-fetch | 12 | 24 | 3 | 9 | 0 |
| bounded-context-fetch | 8 | 7 | 15 | 16 | 2 |

Per bucket (masking):

| distance | correct refusal | false refusal | correct value | wrong value | ungradeable |
|---|---|---|---|---|---|
| 2 | 3 | 6 | 3 | 0 | 0 |
| 6 | 3 | 8 | 0 | 1 | 0 |
| 20 | 3 | 5 | 0 | 4 | 0 |
| 32 | 3 | 5 | 0 | 4 | 0 |

Per bucket (fetch):

| distance | correct refusal | false refusal | correct value | wrong value | ungradeable |
|---|---|---|---|---|---|
| 2 | 3 | 2 | 6 | 1 | 0 |
| 6 | 3 | 1 | 6 | 2 | 0 |
| 20 | 2 | 1 | 3 | 6 | 0 |
| 32 | 0 | 3 | 0 | 7 | 2 |

Refusal accuracy: masking arm refuses on all 12 absent checkpoints (12/12 correct refusals) but also refuses on 24 of the 36 answerable checkpoints, so it **over-refuses** (false-refusal rate 24/36 = 66.7%). Fetch arm refuses on 8 of 12 absent checkpoints (8/12 = 66.7% correct refusals) and on 7 of 36 answerable checkpoints (7/36 = 19.4% false refusals); its refusals are **partially accurate** — more frequent on absent than answerable checkpoints — but not indiscriminate, with 2 absent checkpoints yielding ungradeable empty responses and 2 yielding hallucinated values.

## Requests spent and row accounting

A request row is any row in the file (each row is one model request). `kind=turn` rows are answer-bearing (primary or follow-up answer rows); `kind=turn-initial` rows are intermediate requests that issued a tool call (`stop_reason=tool_calls`) and carry no answer. Both cost a request.

| Run | Rows (= requests) | Breakdown |
|---|---|---|
| TX-AGG masking | 100 | 100 turn |
| TX-AGG fetch | 142 | 113 turn + 29 turn-initial |
| TX-ABS masking | 100 | 100 turn |
| TX-ABS fetch | 142 | 100 turn + 42 turn-initial |
| **Total (this unit)** | **484** | |

Masking fetch_rows = 0 on both (no retrieval). Fetch fetch_rows sums: AGG 82, ABS 50. Retrieval outcomes: AGG 77 OK / 4 NOT_FOUND / 1 STALE_OR_REVOKED; ABS 46 OK / 3 NOT_FOUND / 1 SCOPE_UNGRANTED.

## Artifacts

- `experiments/ptr-engine/measure/rows-agg2-2026-11-09.jsonl`
- `experiments/ptr-engine/measure/rows-abs2-2026-11-09.jsonl`

## Limitations

- Single replication per arm (`rep=1`); no rerun was performed, so variance across replications is unmeasured.
- AGG fetch arm failed its activation gate (29 fetching turns < 40), so it does not count as measuring retrieval; its 4/48 is reported but not a retrieval result.
- AGG fetch arm had 2 truncated turns (`turn 91`, `turn 97`) and ABS fetch arm had 2 ungradeable empty responses; these are retained, not suppressed.
- One model/engine only (`occamy-1.0-NVFP4` on `sglang`); no cross-model or cross-engine replication.
- All runs are generation `gen-7` on a single machine; no independent replication or cross-site reproduction.