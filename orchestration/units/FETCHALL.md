# FETCHALL — fetch-all-markers D-arm rule + TX-01 cell

Status: done

## Step 1 (offline)
- D checkpoint instruction changed in `run_longrun.checkpoint_prompt`: when markers are present the model MUST issue, in a single round, one fetch call for EVERY `[MASKED <ref>]` marker, then answer from returned bodies; answering before fetching every marker is `retrieval_omitted`. C instruction unchanged.
- Offline proof: turn-20 instruction text captured for both arms; scripted two-call round parsed to 2 fetch calls with one follow-up carrying both tool results; `retrieval_omitted` False when all markers fetched, True when any skipped.
- `retrieval_omitted` now counts partial fetches via `marker_refs` extracted from the pre-checkpoint prompt.

## Step 2 (live)
- C: `masking-no-fetch`, 48 turns, 48 requests.
- D: `bounded-context-fetch`, 48 turns, 53 requests (5 checkpoint follow-ups).
- Model: occamy-1.0, 192.168.2.168:8012/v1, 1 rep, TX-01.

## Step 3 (grading)
- C: 0/12 pass, 12 fail, 0 ungradeable.
- D: 3/12 pass, 9 fail, 0 ungradeable.
- D passes: T20 RETRY_LIMIT=3, T24 MAX_BATCH_SIZE, T28 PtrMissingRefError.

## Step 4 (accounting)
- rows = requests sent = 101; cap 2739 -> 2840; all rows task_id TX-01, single fixture sha 44a1b435...; no void.

## Claim
bounded-context-fetch recovered 3 of 12 checkpoint facts that masking-no-fetch missed (RETRY_LIMIT, MAX_BATCH_SIZE, PtrMissingRefError), while masking-no-fetch answered ANSWER: NONE at all 12 checkpoints. This run does not show significance or generalization: it is a single task, single replicate, with no interval estimate, no cross-stack replication, and only 5 of 12 D checkpoints actually fetched all three markers.
