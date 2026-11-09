# UNIT NEVER-ANSWERED-ROOT-2

## Objective
Re-issue of NEVER-ANSWERED-ROOT (settled partial with no table). Explain the 63
never_answered cells of QUALITY-REASON-MIX's primary T3 population **from the turn text**,
and deliver the 63-row table that the first unit owed. Offline, zero requests, read-only on
every existing file.

## Deliverables
1. 63-row table (grid, arm, checkpoint, turn, row_kind_set, completion_tokens, max_tokens,
   content_chars, numerals, bucket) with per-arm/per-grid totals and the prose right/wrong split.
2. Discriminator by rows era / fixture contract / arm, plus a one-sentence verdict.
3. The grade_v4 -> grade_v5 seam: quote fragments, rule tightening vs regression.
4. A ten-line design for a contract that records wrong answers as wrong.
5. Journal + handoff.

## Write paths
docs/NEVER-ANSWERED-ROOT.md, experiments/ptr-engine/measure/NEVER-ANSWERED-ROOT.json,
experiments/ptr-engine/tools/never_answered.py, orchestration/units/NEVER-ANSWERED-ROOT-2.md,
orchestration/handoffs/NEVER-ANSWERED-ROOT-2.json,
orchestration/journals/NEVER-ANSWERED-ROOT-2.jsonl

## Hard bound
28 tool calls, 0 network requests, no edits to rows / grade documents / graders / fixtures.

## Result
done - see orchestration/handoffs/NEVER-ANSWERED-ROOT-2.json
