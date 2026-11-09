# UNIT TX03FETCHFIX

**Purpose.** Re-run the TX-03 `bounded-context-fetch` arm with the correct `--tools fetch`
selector after the earlier runs advertised `read_file` instead, and report the corrected
distance dose-response.

**Bound.** <=400 live requests. Actual: 272 (rep1 138, rep2 134).

## Accounting
- Fixture: experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json sha256 f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3
- Rows files: experiments/ptr-engine/measure/rows-tx03-fetchfix-r1.jsonl (138), rows-tx03-fetchfix-r2.jsonl (134)
- task_id all TX-03; single fixture sha; cap 4134 -> 4406 (+272). Global cap 12094, 7688 remaining.
- Row-1 gate: task_id=TX-03, fixture sha, tools_mode=on:fetch, tools_schema_sent=true, temperature=0.0, seed=42.
- Activation gate: first 10 rows contained fetch rows (2 each rep); total fetch_rows 52 (rep1) and 47 (rep2) >= 40.

## Results (correct/8 per bucket)
- bounded-context-fetch rep1: d2 8/8, d5 8/8, d6 8/8, d8 8/8, d20 6/8, d32 3/8 (41/48).
- bounded-context-fetch rep2: d2 8/8, d5 8/8, d6 8/8, d8 7/8, d20 6/8, d32 5/8 (42/48).

## Activation
- Rep1: masked_rows>0 turns=14; fetch_rows=52; outcomes OK×49, NOT_FOUND×3; cached_tokens present 136/138.
- Rep2: masked_rows>0 turns=14; fetch_rows=47; outcomes OK×47; cached_tokens present 133/134.

## Correction
Earlier fetch numbers (6,1,2,1,1,1 and 6,1,0,0,0,0) were measured with --tools read_file
(tools_mode on:read_file); corrected runs use --tools fetch (tools_mode on:fetch).
