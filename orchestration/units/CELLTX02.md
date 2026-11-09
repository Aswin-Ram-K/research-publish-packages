# UNIT CELLTX02

**Purpose.** First measured dose-response cell on TX-02: does fetch-by-pointer recover facts that masking loses, as a function of fact-to-query distance {2,8,20,32}? Two arms, two reps each.
**Bound.** <=600 live requests. Actual: 400 requests (masking 88+88; fetch 110+114). 0 tool calls beyond fetch channel's own.

## Accounting
- Fixture: experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json sha256 dd267a049a876a4fee9979fd8336488a180048e9a3db9d11d46446c6b8111662
- Rows files: experiments/ptr-engine/measure/rows-tx02-masking-r1.jsonl (88), rows-tx02-masking-r2.jsonl (88), rows-tx02-fetch-r1.jsonl (110), rows-tx02-fetch-r2.jsonl (114)
- task_id all TX-02; single fixture sha; cap 3328 -> 3728 (+400).
- Dry-run first (offline, zero HTTP) projected 88 per masking rep and 88 turn + up to 48 fetch rounds per fetch rep.

## Results (correct/12 per bucket)
- masking-no-fetch rep1/rep2: d2 12/12, d8 0/12, d20 0/12, d32 0/12.
- bounded-context-fetch rep1: d2 12/12, d8 4/12, d20 7/12, d32 5/12.
- bounded-context-fetch rep2: d2 0/12, d8 0/12, d20 0/12, d32 1/12 (format drift to TEXT).

## Activation
- Masking: masked_rows>0 = 12 turns each rep; fetch_rows=0; outcomes [].
- Fetch rep1: masked_rows>0 = 13; fetch_rows=47; outcomes ['NOT_FOUND','OK'].
- Fetch rep2: masked_rows>0 = 16; fetch_rows=55; outcomes ['NOT_FOUND','OK'].
- cached_tokens present: 86/88, 86/88, 108/110, 111/114.

## Claim
Masking arm is monotone in distance (12 at d2, 0 at d8/20/32). Fetch arm is not flat and not stable across reps (rep1 12/4/7/5, rep2 0/0/0/1 due to answer-format drift). Full results: experiments/ptr-engine/research-seed-concepts/RESULTS-TX02-CELL1.md.
