# Results — TX-02 Cell 1 (ptr-engine, dose-response)

Source of record: `orchestration/handoffs/CELLTX02.json` (unit `CELLTX02`), row files
`experiments/ptr-engine/measure/rows-tx02-masking-r1.jsonl`,
`rows-tx02-masking-r2.jsonl`,
`rows-tx02-fetch-r1.jsonl`,
`rows-tx02-fetch-r2.jsonl`.
Instrument: `experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json`.

## Conditions

Endpoint `http://192.168.2.168:8012/v1`, model `occamy-1.0`, engine `sglang`, `--claim-mode plumbing`.
Fixture sha256 `dd267a049a876a4fee9979fd8336488a180048e9a3db9d11d46446c6b8111662`, task_id `TX-02`, N=88, 48 checkpoints (12 per distance {2,8,20,32}).
Dry-run (offline, zero HTTP) projected 88 requests per masking rep and 88 turn requests + up to 48 fetch rounds per fetch rep; `--fixture`/`--task` explicit; first row asserted `task_id=TX-02` and the on-disk sha before any second request.

## Table: arm × rep × distance bucket → correct/12

| Arm | Rep | d=2 | d=8 | d=20 | d=32 | Total correct/48 | Score (`score_longrun`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `masking-no-fetch` | 1 | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 | 12/48 |
| `masking-no-fetch` | 2 | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 | 12/48 |
| `bounded-context-fetch` | 1 | 12/12 | 4/12 | 7/12 | 5/12 | 28/48 | 28/48 |
| `bounded-context-fetch` | 2 | 0/12 | 0/12 | 0/12 | 1/12 | 1/48 | 1/48 |

Per-bucket totals (both reps pooled, 24 checkpoints per bucket):

| Bucket | Masking correct/24 | Fetch correct/24 |
|---|---:|---:|
| d=2 | 24/24 | 12/24 |
| d=8 | 0/24 | 4/24 |
| d=20 | 0/24 | 7/24 |
| d=32 | 0/24 | 6/24 |

Full bucket detail (checkpoints=12 each, per rep):

- Masking rep 1/2: d=2 12 correct / 0 wrong / 0 abstained / 0 ungradeable; d=8,20,32 each 0 correct / 0 wrong / 12 abstained / 0 ungradeable.
- Fetch rep 1: d=2 12 correct / 0 wrong / 0 abstained / 0 ungradeable; d=8 4 correct / 0 wrong / 8 abstained / 0 ungradeable; d=20 7 correct / 1 wrong / 4 abstained / 0 ungradeable; d=32 5 correct / 1 wrong / 6 abstained / 0 ungradeable.
- Fetch rep 2: d=2 0 correct / 12 wrong / 0 abstained / 0 ungradeable; d=8 0 correct / 11 wrong / 1 abstained / 0 ungradeable; d=20 0 correct / 10 wrong / 2 abstained / 0 ungradeable; d=32 1 correct / 10 wrong / 1 abstained / 0 ungradeable.

## Monotonicity statement

- Masking arm: monotone non-increasing in distance — 12/12 at d=2, then 0/12 at d=8/20/32 in both reps. *(Labelled, not rewritten: this is not a depth or attention gradient; the step is the eviction boundary at `intro+4`, as the boundary statement below states. The failures are **content absence** — the mask deletes the fact at `intro+4`, before any probe deeper than `d2` is asked — so **position is untested on this arm**: this run cannot test position because the value is absent from the prompt. That is recorded in FINDINGS-LEDGER.md under `### The TX-03 cliff is content absence; position is untested here`.)*
- Fetch arm: not flat and not stable across reps — rep 1 varies (12, 4, 7, 5) and rep 2 collapses to (0, 0, 0, 1) because the model drifted to `ANSWER: TEXT VAL_A=…` instead of `ANSWER: NUM …`, so 43 of 48 fetch-rep-2 checkpoints are wrong on format rather than value. Neither "monotone masking + flat fetch" holds; the fetch arm is rep-dependent.

## Activation evidence (row counts, quoted literally)

- Masking rep 1/2: `masked_rows>0` turns = 12/88 each; `total fetch_rows` = 0; `retrieval_outcomes` = `[]`; `cached_tokens` present on 86/88 rows.
- Fetch rep 1: `masked_rows>0` turns = 13/110; `total fetch_rows` = 47; `retrieval_outcomes` = `['NOT_FOUND', 'OK']`; `cached_tokens` present on 108/110 rows. `tools_mode='on:fetch'`, `tools_schema_sent=True`, `tools_declared=True` on row 1.
- Fetch rep 2: `masked_rows>0` turns = 16/114; `total fetch_rows` = 55; `retrieval_outcomes` = `['NOT_FOUND', 'OK']`; `cached_tokens` present on 111/114 rows.
- Masking row 1 (rep 1): `task_id=TX-02`, `fixture_sha256=dd267a049a876a4fee9979fd8336488a180048e9a3db9d11d46446c6b8111662`, `tools_declared=False`, `tools_schema_sent=False`, `tools_mode='off'`, `masked_rows=0`, prompt contains no turn-1 tool bodies (fact introduced at turn 1, masked only after the 4-turn window).

## Accounting

- Requests this unit: 400 (masking 88 + 88; fetch 110 + 114). Hard ceiling 600 → 200 headroom unused.
- Cumulative: 3328 (before) → 3728 (after). Global cap 12094 → 8366 remaining.
- Row counts: 88 + 88 + 110 + 114 = 400 rows. All `task_id=TX-02`, single fixture sha.
- Cap gate: `spent_at_start=3328`, `used_in_run` 88/88/110/114, `delta=0` on all four runs.

## Verification

- `score_longrun.py` exit codes: masking reps 1 (12/48, exit 1), 2 (12/48, exit 1); fetch rep 1 (28/48, exit 1); fetch rep 2 (1/48, exit 1). No run reached `verified_success=True` because the fixture's 48 checkpoints are all required and no run cleared all 48.

## What this result does not show

Two reps on one stack, one task, no interval or significance test. The fetch arm's rep-2 collapse is a format-compliance failure of the model, not a retrieval failure (fetches still returned `OK`), so it cannot be read as a pure distance effect. No quality floor was imposed; recommendations remain workload-specific and labelled.

## Two-level scoring (contract vs value) — re-score of four row files

Extended `score_longrun.py` with `score_answer_contract_rows` (contract-level = kind NUM AND value matches; value-level = value matches regardless of emitted kind). Literal scorer output:

- `rows-tx02-masking-r1.jsonl`: `{"masking-no-fetch__rep1": {"contract_correct": 12, "value_correct": 12, "ungradeable": 0, "abstained": 36, "kind_mismatch_value_correct": 0, "total": 48}}`
- `rows-tx02-masking-r2.jsonl`: `{"masking-no-fetch__rep1": {"contract_correct": 12, "value_correct": 12, "ungradeable": 0, "abstained": 36, "kind_mismatch_value_correct": 0, "total": 48}}`
- `rows-tx02-fetch-r1.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 28, "value_correct": 28, "ungradeable": 0, "abstained": 18, "kind_mismatch_value_correct": 0, "total": 48}}`
- `rows-tx02-fetch-r2.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 1, "value_correct": 36, "ungradeable": 0, "abstained": 4, "kind_mismatch_value_correct": 35, "total": 48}}`

### Contract-line drift verdict

Reproduced as a prompt-level defect? **Not reproduced.** The harness adds `CHECKPOINT_CONTRACT_LINE` on every checkpoint turn in both the dry-run path (`run_longrun.py:2827`) and the live path (`run_longrun.py:3084`), including turns that later take the ARM-D fetch follow-up (`_followup_msgs` built from `info["prompt"]` which already carries the line). The r2 collapse (43/48 `ANSWER: TEXT VAL_*=...`) is therefore attributed to endpoint/model sampling nondeterminism, not to a missing contract line; the contract line is present identically on every asked turn. The fix applied is idempotency (`checkpoint_prompt` no longer double-appends when re-invoked on a tool-follow-up prompt) plus a presence test.

### Boundary statement (masking arm)

`masking-no-fetch` correct count as a function of distance: 12/12 at d=2, 0/12 at d=8, 0/12 at d=20, 0/12 at d=32 (both reps). Distances d=2 fall inside the unmasked recent-turn window (`WINDOW_TURNS = 4`, cutoff `t-4`, `masked_rows = 0`); distances d=8, 20, 32 fall outside it and are fully masked. This is a policy boundary, not a recall result.
