# INSTRUCTCELL

- Status: done
- Unit: instructed fetch policy comparison on TX-AGG and TX-HOP
- Write paths: experiments/ptr-engine/measure/rows-agg3-instructed.jsonl, experiments/ptr-engine/measure/rows-hop3-instructed.jsonl, experiments/ptr-engine/research-seed-concepts/RESULTS-FETCH-INSTRUCTED.md, orchestration/units/INSTRUCTCELL.md, orchestration/handoffs/INSTRUCTCELL.json

## Evidence

Row-1 gate: task_id TX-AGG/TX-HOP, fixture_sha256 match, temperature 0, seed 42, tools_mode on:fetch, fetch_policy instructed — PASS both.

Activation gate: AGG 22 fetching turns (<40, shortfall 18); HOP 17 (<40, shortfall 23) — FAIL both.

Scoring:
- AGG instructed: contract 1/48, value 1/48 (d2 0, d6 0, d20 0, d32 1).
- HOP instructed: contract 5/48, value 5/48 (d2 3, d6 2, d20 0, d32 0).

Strict baseline: AGG 4/48 (29 fetching, 82 fetches); HOP 9/48 (28 fetching, 30 fetches).

Requests: AGG 122, HOP 197, total 319. Observed spent before 6528, after 6847.

## Blocker

None. Activation floor not met; runs reported but not counted as retrieval results.

## Next unit hint

None; instructed policy not worth adopting for these task kinds.
