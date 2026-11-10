# VCURVE — independent verification of TX-03 dose-response curve

**Unit.** `VCURVE` · offline verification only, no HTTP, no row/fixture/scorer edits.
**Objective.** Independently confirm or refute the six-distance x two-arm curve claimed for TX-03 (masking vs fetch) by recomputing every cell with `score_longrun.py`, validating denominators, config, leak, and failure modes.
**Write paths.** `orchestration/handoffs/VCURVE.json`, `orchestration/units/VCURVE.md`.

## Procedure

1. Recomputed all 4 reps with `score_longrun.py --answer-contract` (commands + outputs in handoff).
2. Validated config on every row: tools_mode, tools_schema_sent, temperature, seed, task_id, fixture_sha256 (matches file sha256).
3. Checked fetch_rows totals (52 and 47) and retrieval-outcome distribution (r1 OK=49/NOT_FOUND=3; r2 OK=47).
4. Masking: tools_mode=off, fetch_rows=0, 8 turns with masked_rows>0 (8 tool-output turns), 0/8 buckets all NONE abstentions, 0 ungradeable.
5. Denominator: fixture 48 checkpoints, 8 per distance; checkpoint_prompt injected questions on exactly 48/100 turns, 8 per distance; 48 checkpoint rows per file.
6. Leak check on 5 correct d=32 fetch successes: fetched body contains expected VAL_F; masking arm 0/8 at same distances.

## Verification

- Recomputed table identical to claimed table for all 4 reps x 6 distances.
- Denominator: 8 checkpoints per bucket, all asked.
- Failure mode: masking 0/8 buckets are abstentions (NONE), contract-valid, no ungradeable rows.
- Verdict: REPRODUCED EXACTLY.

## Notes

- retrieval_omitted=True on most fetch turns and 3 NOT_FOUND outcomes (wrong ref formats: doc-fact-02@1, @knowledge:item-1@1) are secondary observations, not curve invalidators.
- No model requests, service restarts, target writes, or fixture/grader modifications performed.
