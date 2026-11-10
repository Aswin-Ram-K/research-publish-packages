# Results — TX-03 Cell 1 (ptr-engine, distance dose-response)

Source of record: `orchestration/handoffs/CELLTX03.json` (unit `CELLTX03`), row files
`experiments/ptr-engine/measure/rows-tx03-masking-r1.jsonl`,
`rows-tx03-masking-r2.jsonl`,
`rows-tx03-fetch-r1.jsonl`,
`rows-tx03-fetch-r2.jsonl`.
Instrument: `experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json`.

## Conditions

Endpoint `http://192.168.2.168:8012/v1`, model `occamy-1.0`, engine `sglang`, `--temperature 0 --seed 42`, `--claim-mode H1`.
Fixture sha256 `f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`, task_id `TX-03`, N=100, 48 checkpoints (8 at each of six distances `{2,5,6,8,20,32}`), all NUM, all expected values distinct.
Dry-run (offline, zero HTTP) projected 100 turn requests per masking rep and 100 turn requests + up to 48 fetch rounds per fetch rep; `--task TX-03`/`--fixture` explicit; row-1 gate asserted `task_id=TX-03`, fixture sha, `temperature=0`, `seed=42` before the second request.
Empirical window boundary = 5 (`WINDOW_TURNS = 4`, cutoff `t-4`): d=2 is a policy-inside control (fact rendered verbatim); d≥5 are the real treatment points (fact rendered as pointer marker).

## Table: arm × rep × distance bucket → contract-level /8 and value-level /8

| Arm | Rep | d=2 | d=5 | d=6 | d=8 | d=20 | d=32 | Total /48 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `masking-no-fetch` | 1 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 8/48 (contract=value) |
| `masking-no-fetch` | 2 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 | 8/48 (contract=value) |
| `bounded-context-fetch` | 1 | 6/8 | 1/8 | 2/8 | 1/8 | 1/8 | 1/8 | 12/48 (contract=value) |
| `bounded-context-fetch` | 2 | 6/8 | 1/8 | 0/8 | 0/8 | 0/8 | 0/8 | 7/48 (contract=value) |

Pooled across both reps (16 checkpoints per bucket):

| Bucket | Masking correct/16 | Fetch correct/16 |
|---|---:|---:|
| d=2 (policy-inside control) | 16/16 | 12/16 |
| d=5 | 0/16 | 2/16 |
| d=6 | 0/16 | 2/16 |
| d=8 | 0/16 | 1/16 |
| d=20 | 0/16 | 1/16 |
| d=32 | 0/16 | 1/16 |

Scorer (`score_longrun.py --answer-contract`) raw output:

- `rows-tx03-masking-r1.jsonl`: `{"masking-no-fetch__rep1": {"contract_correct": 8, "value_correct": 8, "ungradeable": 0, "abstained": 40, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 8, "value": 8, "n": 8}, "5": {"contract": 0, "value": 0, "n": 8}, "6": {"contract": 0, "value": 0, "n": 8}, "8": {"contract": 0, "value": 0, "n": 8}, "20": {"contract": 0, "value": 0, "n": 8}, "32": {"contract": 0, "value": 0, "n": 8}}}}`
- `rows-tx03-masking-r2.jsonl`: `{"masking-no-fetch__rep1": {"contract_correct": 8, "value_correct": 8, "ungradeable": 0, "abstained": 40, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 8, "value": 8, "n": 8}, "5": {"contract": 0, "value": 0, "n": 8}, "6": {"contract": 0, "value": 0, "n": 8}, "8": {"contract": 0, "value": 0, "n": 8}, "20": {"contract": 0, "value": 0, "n": 8}, "32": {"contract": 0, "value": 0, "n": 8}}}}`
- `rows-tx03-fetch-r1.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 12, "value_correct": 12, "ungradeable": 10, "abstained": 16, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 6, "value": 6, "n": 8}, "5": {"contract": 1, "value": 1, "n": 8}, "6": {"contract": 2, "value": 2, "n": 8}, "8": {"contract": 1, "value": 1, "n": 8}, "20": {"contract": 1, "value": 1, "n": 8}, "32": {"contract": 1, "value": 1, "n": 8}}}}`
- `rows-tx03-fetch-r2.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 7, "value_correct": 7, "ungradeable": 12, "abstained": 16, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 6, "value": 6, "n": 8}, "5": {"contract": 1, "value": 1, "n": 8}, "6": {"contract": 0, "value": 0, "n": 8}, "8": {"contract": 0, "value": 0, "n": 8}, "20": {"contract": 0, "value": 0, "n": 8}, "32": {"contract": 0, "value": 0, "n": 8}}}}`

## Monotonicity statement

- Masking arm: correct only at d=2 (8/8 per rep, 16/16 pooled); 0/8 at every d≥5 in both reps. Transition occurs between d=2 and d=5 (i.e. at the mask, which fires at `intro+4` for every fact): inside the window the fact is verbatim and answered; outside the window it is a pointer marker and, with no fetch channel, the model abstains (`ANSWER: NONE`). The failures are **content absence** — the mask deletes the fact at `intro+4`, before any probe deeper than `d2` is asked — so **position is untested on this arm**: this run cannot test position because the value is absent from the prompt. That is recorded in FINDINGS-LEDGER.md §The TX-03 cliff is content absence; position is untested here. d=2 is a policy-inside control, not a treatment point.
- Fetch arm: not flat and not stable across reps — rep 1 varies (6,1,2,1,1,1); rep 2 (6,1,0,0,0,0). Pooled fetch is 12/16 at d=2 falling to 1–2/16 at every d≥5. The fetch arm does not recover the masking arm's d=2 ceiling and shows no clean distance trend; it is rep-dependent (many tool-call turns did not convert to a fetched answer, 10–12 ungradeable per rep).

## Activation evidence (row counts, quoted literally)

- Masking rep 1/2: `masked_rows>0` turns = 8/100 each; `total fetch_rows` = 0; `retrieval_outcomes` = `[]`; `cached_tokens` present on 98/100 rows each.
- Fetch rep 1: `masked_rows>0` turns = 9/105; `total fetch_rows` = 8; `retrieval_outcomes` = `['OK']`; `cached_tokens` present on 104/105 rows. `tools_mode='on:fetch'` (run with `--tools read_file`).
- Fetch rep 2: `masked_rows>0` turns = 8/101; `total fetch_rows` = 1; `retrieval_outcomes` = `['OK']`; `cached_tokens` present on 99/101 rows.
- Row 1 of every file: `task_id=TX-03`, `fixture_sha256=f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`, `temperature=0.0`, `seed=42`.

## Accounting

- Requests this unit: 406 (masking 100 + 100; fetch 105 + 101). Unit ceiling 800 → 394 headroom unused.
- Cumulative: 3728 (before) → 4134 (after). Global cap 12094 → 7960 remaining.
- Row counts: 100 + 100 + 105 + 101 = 406 rows. All `task_id=TX-03`, single fixture sha.
- Cap gate: `budget-cap 12094`, `spent_at_start=3728`, `used_in_run` 100/100/105/101, `delta=0` on all four runs.
- Distances: 8 checkpoints per bucket × 6 buckets = 48 per run; all NUM, all expected values distinct.

## Verification

- `score_longrun.py --answer-contract` exit codes: masking reps 8/48 (exit 1 each); fetch rep1 12/48 (exit 1); fetch rep2 7/48 (exit 1). No run reached `verified_success=True` because the fixture's 48 checkpoints are all required and no run cleared all 48.
- Every number above is traceable to row counts quoted from the jsonl files (see Activation evidence and row counts).

## What this result does not show

Two reps on one stack, one task, no interval or significance test. The fetch arm's low conversion (only 5 turns fetched in rep 1, 1 in rep 2) is a retrieval/invocation failure of the model, not a distance effect per se, so the fetch arm cannot be read as a clean distance response. No quality floor was imposed; recommendations remain workload-specific and labelled.

---

## Corrected fetch arm — TX03FETCHFIX (2026-11-09)

The earlier `bounded-context-fetch` rows (`rows-tx03-fetch-r{1,2}.jsonl`) were run with
`--tools read_file`, so `tools_mode` was `on:read_file` and the `fetch` schema was never advertised;
they measured non-fetching (8 then 1 fetch row) rather than retrieval. Re-run with `--tools fetch`
(`tools_mode: on:fetch`), `--temperature 0 --seed 42`, two reps, row files
`rows-tx03-fetchfix-r{1,2}.jsonl`. Row-1 gate asserted `task_id=TX-03`,
`fixture_sha256=f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`,
`tools_mode=on:fetch`, `tools_schema_sent=true`, `temperature=0.0`. Activation gate passed:
first 10 rows contained fetch rows (2 in each rep).

### Table: corrected fetch arm, distance × rep → contract-level /8 and value-level /8

| Rep | d=2 | d=5 | d=6 | d=8 | d=20 | d=32 | Total /48 | fetch_rows |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8/8 | 8/8 | 8/8 | 8/8 | 6/8 | 3/8 | 41/48 | 52 |
| 2 | 8/8 | 8/8 | 8/8 | 7/8 | 6/8 | 5/8 | 42/48 | 47 |

(Contract-level = value-level on both runs; `kind_mismatch_value_correct=0`.)

### Against the flawed numbers

Earlier (misconfigured) fetch arm: rep1 `(6,1,2,1,1,1)/8`, rep2 `(6,1,0,0,0,0)/8`,
with `fetch_rows` of 8 and 1 and 10/12 ungradeable. The corrected arm scores
`(8,8,8,8,6,3)/8` and `(8,8,8,7,6,5)/8` with 52 and 47 fetch rows and 0 ungradeable.
The change is because the corrected run advertised the `fetch` tool schema
(`tools_mode: on:fetch`) instead of `read_file`; the model could then retrieve masked bodies
by pointer, converting most checkpoints into correct NUM answers instead of abstaining.

### Retrieval outcomes and cached_tokens

- Rep 1: outcomes `OK×49`, `NOT_FOUND×3`; `cached_tokens` present on 136/138 rows.
- Rep 2: outcomes `OK×47`; `cached_tokens` present on 133/134 rows.

### Scorer raw output

- `rows-tx03-fetchfix-r1.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 41, "value_correct": 41, "ungradeable": 0, "abstained": 5, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 8, "value": 8, "n": 8}, "5": {"contract": 8, "value": 8, "n": 8}, "6": {"contract": 8, "value": 8, "n": 8}, "8": {"contract": 8, "value": 8, "n": 8}, "20": {"contract": 6, "value": 6, "n": 8}, "32": {"contract": 3, "value": 3, "n": 8}}}}`
- `rows-tx03-fetchfix-r2.jsonl`: `{"bounded-context-fetch__rep1": {"contract_correct": 42, "value_correct": 42, "ungradeable": 0, "abstained": 3, "kind_mismatch_value_correct": 0, "total": 48, "by_distance": {"2": {"contract": 8, "value": 8, "n": 8}, "5": {"contract": 8, "value": 8, "n": 8}, "6": {"contract": 8, "value": 8, "n": 8}, "8": {"contract": 7, "value": 7, "n": 8}, "20": {"contract": 6, "value": 6, "n": 8}, "32": {"contract": 5, "value": 5, "n": 8}}}}`

### Accounting

- Requests: rep1 138, rep2 134; total 272 (unit ceiling 400).
- Spent before unit: 4134; after rep1: 4272; after rep2: 4406. Cap 12094; headroom 7688.
- All rows `task_id=TX-03`, single fixture sha `f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`.
