# UNIT CELLTX03

**Purpose.** Distance dose-response on TX-03: does fetch-by-pointer recover facts that masking loses, as a function of fact-to-query distance {2,5,6,8,20,32}? Two arms, two reps each. Format-determinism fix in place.

**Bound.** <=800 live requests. Actual: 406 requests (masking 100+100; fetch 105+101). 0 requests beyond fetch channel's own.

## Accounting
- Fixture: experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json sha256 f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3
- Rows files: experiments/ptr-engine/measure/rows-tx03-masking-r1.jsonl (100), rows-tx03-masking-r2.jsonl (100), rows-tx03-fetch-r1.jsonl (105), rows-tx03-fetch-r2.jsonl (101)
- task_id all TX-03; single fixture sha; cap 3728 -> 4134 (+406). Global cap 12094, 7960 remaining.
- Dry-run first (offline, zero HTTP) projected 100 per masking rep and 100 turn + up to 48 fetch rounds per fetch rep.
- Row-1 gate: asserted task_id=TX-03, fixture sha, temperature=0, seed=42 on first request before continuing.

## Results (correct/8 per bucket)
- masking-no-fetch rep1/rep2: d2 8/8, d5 0/8, d6 0/8, d8 0/8, d20 0/8, d32 0/8.
- bounded-context-fetch rep1: d2 6/8, d5 1/8, d6 2/8, d8 1/8, d20 1/8, d32 1/8.
- bounded-context-fetch rep2: d2 6/8, d5 1/8, d6 0/8, d8 0/8, d20 0/8, d32 0/8.

## Activation
- Masking r1/r2: masked_rows>0 turns=8 each; fetch_rows=0; outcomes []; cached_tokens present 98/100 each.
- Fetch r1: masked_rows>0 turns=9; fetch_rows=8; outcomes ['OK']; cached_tokens present 104/105.
- Fetch r2: masked_rows>0 turns=8; fetch_rows=1; outcomes ['OK']; cached_tokens present 99/101.

## Claim
Masking arm transitions from correct to incorrect between d=2 and d=5 (policy window boundary 5): correct at d=2 only, 0 at all d>=5. Fetch arm is not flat across distance and is rep-dependent (rep1 6/1/2/1/1/1, rep2 6/1/0/0/0/0). d=2 flagged as policy-inside control. Full results: experiments/ptr-engine/research-seed-concepts/RESULTS-TX03-CELL1.md.
