# UNIT SUPANOMALY — Explain SUP anomalies A/B and characterise HOP

**Date:** 2026-11-09 · **Live requests:** 0 (offline) · **Zero model requests**

## Objective
Explain anomaly A (fetch worse than masking at d=2 in SUP) and anomaly B (single correct masking at d=32), and characterise HOP (16/48). Recompute scores from rows; no fixtures/rows/scorer modified.

## Recomputed scores (score_longrun.py --answer-contract)
SUP masking-no-fetch: contract/value 13/48 (d2 12/12, d6 0/12, d20 0/12, d32 1/12).
SUP bounded-context-fetch: 22/48 (d2 3/12, d6 9/12, d20 5/12, d32 5/12); row-level n 14/12/13/16 (55 rows).
HOP masking-no-fetch: 12/48 (d2 12/12, rest 0).
HOP bounded-context-fetch: 16/48 (d2 9/12, d6 4/12, d20 0/12, d32 3/12).
Confirmed matches reported numbers. kind_mismatch_value_correct=0 in all cells.

## Anomaly A mechanism (SUP d=2 fetch)
At d=2 the fact is inside the verbatim window, so masking arm scores 12/12. The fetch arm scores 3/12 because its tool round-trip retrieves stale revisions (r1) or wrong docs and abstains. Of 12 d=2 checkpoints: 3 correct, 2 stale-value answers (turns 12, 64), 2 wrong-doc answers (turns 20, 21 -> 4000), 5 abstentions (13, 29, 37, 65, 73). Retrieved body is not stored in rows; classification inferred from answer vs expected/stale plus outcome labels (STALE_OR_REVOKED / NOT_FOUND / OK).

## Anomaly B (SUP d=32 masking, turn 58)
Row quoted in handoff. content "ANSWER: NUM 4019", expected 4019, expected_present (reasoning) false, masked_rows 0, marker_refs empty, fetch_rows null. No prompt text is stored in rows, so a direct prompt search is impossible from the artifact; expected_present only covers the reasoning channel and is false. 4019 appears in stored data only in expected/answer/ground_truth. Most plausible: pattern inference (fact-05 VAL_D = 4016+3; model had seen the progression in d=2 examples). Cannot exclude lucky guess; n=1, no variance. Not a scoring artefact (contract match is genuine).

## HOP characterisation
No bucket has earlier fact masked while later fact visible (key distance = value distance + 2). Masking arm perfect only d=2. Fetch arm 16/48 is partial recovery, not robust joining: fetches mostly key docs, with abstentions, wrong VAL indices, and TEXT answers. Supports multi-hop join-under-masking claims; does not support fetch reliability.

## Write paths
- orchestration/handoffs/SUPANOMALY.json
- orchestration/units/SUPANOMALY.md
""" \
