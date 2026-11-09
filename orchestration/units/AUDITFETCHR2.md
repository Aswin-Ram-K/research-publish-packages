# AUDITFETCHR2 — fetch-r1 vs fetch-r2 score collapse

## Recomputed scores
- `rows-tx02-fetch-r1.jsonl`: **28/48** (matches reported).
- `rows-tx02-fetch-r2.jsonl`: **1/48** (matches reported).

## Side-by-side aggregates

| Field | fetch-r1 | fetch-r2 |
|---|---:|---:|
| rows | 110 | 114 |
| distinct turns | 88 | 88 |
| checkpoint turns | 48 | 48 |
| score | 28/48 | 1/48 |
| rows with tool_call_ids | 44 | 52 |
| tool-followup rows | 22 | 26 |
| fetch_rows total | 47 | 55 |
| retrieval outcomes | NOT_FOUND, OK | NOT_FOUND, OK |
| request_error | 0 | 0 |
| failed turns | 0 | 0 |
| tools_mode | on:fetch | on:fetch |
| tools_declared | true | true |
| tools_schema_sent | true | true |
| prompt_tokens sum | 244800 | 271122 |
| cached_tokens present | 108/110 | 111/114 |
| wall_ms sum | 76612.7 | 118807.2 |
| model / engine | occamy-1.0 / sglang | occamy-1.0 / sglang |
| endpoint | http://192.168.2.168:8012/v1 | http://192.168.2.168:8012/v1 |
| fixture_sha256 | dd267a04… | dd267a04… |
| task_id | TX-02 | TX-02 |
| harness_sha256 | 969d7846… | 969d7846… |
| answer_kind (checkpoint final) | NUM 29 / NONE 18 / TEXT 1 | TEXT 43 / NONE 4 / NUM 1 |

## r2 checkpoint classification (48 total)

| Class | Count | By distance |
|---|---:|---|
| answered correctly | 1 | d32: 1 |
| answered wrongly | 43 | d2: 12, d8: 11, d20: 10, d32: 10 |
| abstained | 4 | d8: 1, d20: 2, d32: 1 |
| ungradeable | 0 | — |
| never asked | 0 | — |

Of the 43 wrong, 35 had the correct value but were emitted as `ANSWER: TEXT VAL_*=...` instead of the contracted `ANSWER: NUM ...`; 8 had a wrong value. 36/48 were `answer_verified=true` at value level.

## Fetch calls in r2
Yes. r2 issued fetches: 52 rows with `tool_call_ids`, 26 `tool-followup` rows, 55 total `fetch_rows`, and retrieval outcomes `OK`/`NOT_FOUND`. The “tool stopped being advertised” hypothesis is **not reproduced** (`tools_mode=on:fetch`, `tools_declared=true`, `tools_schema_sent=true` on every row).

## Root cause
**(b) endpoint-side nondeterminism**, not a harness/config difference and not a model-capability difference. All row-level harness/config fields are identical. Turn 1 has identical `prompt_sha256` and 570 prompt tokens in both runs, but different output (`ANSWER: TEXT Working turn 1.` vs `ANSWER: TEXT VAL_A=2000, VAL_B=2001, VAL_C=2002, VAL_D=2003`). r2 then emits `ANSWER: TEXT VAL_*=...` at checkpoints, so `score_longrun` records `answer kind 'TEXT' != expected 'NUM'` for 43/48 checkpoints.

## Separating measurement
Replay turn 1 (and, if it converges, the full r2 cell) on the same endpoint with temperature=0 and a fixed seed. If outputs still differ from r1, the endpoint is nondeterministic beyond sampling; if they match r1, the collapse was sampling noise.
