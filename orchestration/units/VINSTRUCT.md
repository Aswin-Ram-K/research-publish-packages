# UNIT VINSTRUCT - recompute instructed vs strict fetch-policy result

**Objective.** Confirm or refute the claim that the instructed fetch policy underperforms the strict policy on both TX-AGG and TX-HOP.

**Bound:** 50 tool calls. **Offline:** 0 HTTP requests. **No rows/fixtures/scorer modified.**

**Verdict:** confirmed. Instructed scores lower than strict at both scoring levels.

| Fixture | Level | strict | instructed |
|---|---|---|---|
| TX-AGG | contract/value (48 checkpoints) | 4/48 | 1/48 |
| TX-HOP | contract/value (48 checkpoints) | 9/48 | 5/48 |

Engagement: instructed issued fewer fetches (TX-AGG 22 vs 29 fetching turns; TX-HOP 17 vs 28) and fewer total fetch rows (49 vs 82; 18 vs 30). Row integrity verified: all 319 instructed rows carry fetch_policy=instructed, tools_mode=on:fetch, temperature=0, seed=42, correct task_id and fixture_sha256. No early termination: instructed runs reached final turns (100/180) with no failed_turn or truncation; strict AGG had 2 truncated/failed turns. Five no-fetch checkpoint turns inspected (TX-AGG turns 6,9,10,12,13): rendered POLICY line quoted in handoff; model either answered with a wrong/stale NUM or abstained (NONE), i.e. ignored the instruction rather than fetching.

**Deliverables:** `orchestration/handoffs/VINSTRUCT.json`, `orchestration/units/VINSTRUCT.md`.
