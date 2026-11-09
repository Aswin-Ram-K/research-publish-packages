# P3 positive control — recorded-transcript search

Result: **no recorded transcript qualifies** as a positive control. Every 48-turn run with a complete working set fails at least one checkpoint (`cp.t24`/`cp.t46` or `acc.2`–`acc.4`/`repair.main`); the closest complete runs are `rows-longrun-v4-2026-10-26.jsonl [pointer-stable]` (8/12-ish target checks pass but `cp.t24`, `cp.t46`, `acc.2`–`acc.4`, `repair.main` fail) and `rows-longrun-v4-tools-2026-10-26.jsonl [pointer-stable]` (same failures).

## Candidate table (runs with full turn text only)

| run id | fixture | turns | working set complete | verify turn |
|---|---|---:|---|---|
| rows-cell-pointer-stable-20261026T145758Z.jsonl [pointer-stable] | LR-01.v5.json | 6 | yes | no |
| rows-cell-pointer-stable-20261026T182535Z.jsonl [pointer-stable] | LR-01.v8.json | 27 | yes | 3,11,15 |
| rows-cell-pointer-stable-20261026T202040Z.jsonl [pointer-stable] | LR-01.v8.json | 12 | yes | 3,4,5,9 |
| rows-cell-pointer-stable-20261026T204258Z.jsonl [pointer-stable] | LR-01.v8.json | 12 | yes | 2 |
| rows-cell-transcript-compact-20261026T203733Z.jsonl [transcript-compact] | LR-01.v8.json | 12 | yes | no |
| rows-cell-transcript-compact-20261027T004155Z.jsonl [transcript-compact] | LR-01.v8.json | 12 | yes | no |
| rows-cell-transcript-grow-20261026T202444Z.jsonl [transcript-grow] | LR-01.v8.json | 12 | yes | 3,4,5,9,10,11 |
| rows-longrun-2026-10-26-fix.jsonl [transcript-grow] | ? | 3 | no | 3 |
| rows-longrun-2026-10-26-fix.jsonl [transcript-compact] | ? | 3 | no | 2,3 |
| rows-longrun-2026-10-26-fix.jsonl [pointer-stable] | ? | 3 | no | 3 |
| rows-longrun-2026-10-26-fix.jsonl [lease-reopen] | ? | 3 | no | 2,3 |
| rows-longrun-2026-10-26-fix.jsonl [transcript-grow] | ? | 3 | no | 3 |
| rows-longrun-2026-10-26-fix.jsonl [transcript-compact] | ? | 2 | no | 1 |
| rows-longrun-2026-10-26-fix.jsonl [transcript-grow] | LR-01.json | 12 | no | 3,6,9,11 |
| rows-longrun-2026-10-26-policy.jsonl [transcript-grow] | ? | 3 | no | no |
| rows-longrun-2026-10-26-policy.jsonl [transcript-compact] | ? | 3 | no | 3 |
| rows-longrun-2026-10-26-policy.jsonl [pointer-stable] | ? | 3 | no | 2,3 |
| rows-longrun-2026-10-26-policy.jsonl [lease-reopen] | ? | 3 | no | 3 |
| rows-longrun-2026-10-26-policy.jsonl [transcript-grow] | ? | 28 | no | 3,4 |
| rows-longrun-c-2026-10-26.jsonl [transcript-grow] | LR-01.v2.json | 48 | no | 3,4,9,10,15,16,21,22,27,28,30,33,34,39,40,45 |
| rows-longrun-c-2026-10-26.jsonl [transcript-compact] | LR-01.v2.json | 48 | no | no |
| rows-longrun-c-2026-10-26.jsonl [pointer-stable] | LR-01.v2.json | 48 | no | 5,11,12,16,17,22,23,26,29,35,41,47 |
| rows-longrun-c-2026-10-26.jsonl [lease-reopen] | LR-01.v2.json | 48 | no | 4,20,22,25,27,29,34,39,47 |
| rows-longrun-v3-2026-10-26.jsonl [transcript-grow] | LR-01.v3.json | 48 | no | no |
| rows-longrun-v3-2026-10-26.jsonl [pointer-stable] | LR-01.v3.json | 48 | no | 5,21,27,30,32,47,48 |
| rows-longrun-v4-2026-10-26.jsonl [transcript-grow] | LR-01.v4.json | 48 | yes | no |
| rows-longrun-v4-2026-10-26.jsonl [pointer-stable] | LR-01.v4.json | 48 | yes | 8,16,28,48 |
| rows-longrun-v4-tools-2026-10-26.jsonl [pointer-stable] | LR-01.v4.tools.json | 48 | yes | 15,16,17,23,29,39,41,45,47,48 |
| rows-longrun-v5-tools.jsonl [pointer-stable] | LR-01.v4.tools2.json | 48 | yes | 3,29,36,39,40 |
| rows-longrun-v6-tools.jsonl [pointer-stable] | LR-01.v4.tools2.json | 48 | yes | 3,9,15,18,25,26,29,35,48 |
| rows-pilot-thinking-2026-10-26.jsonl [transcript-grow] | LR-01.json | 5 | no | 3 |


## Minimal funded need

- 1 transcript = 48 requests (one per turn), 1 arm, 1 replicate.
- Endpoint/model: `http://192.168.2.168:8012/v1`, model `occamy-1.0` (SGLang), engine digest as pinned.
- Fixture: a complete-working-set runtime fixture (`tasks-v4/runtime-v4/LR-01.v4.json` or `tasks-v6/LR-01.v9.json`); the run must include a verify turn with recorded `exit 0` at turn 16 and/or 48.
- Cost: **48 requests** against the ledger (remaining 9503 -> 9455 after), plus the existing 0-request scorer pass. No fixture/grader change required.
