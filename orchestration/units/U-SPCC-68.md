# U-SPCC-68 — record the E2 turnover sweep in the ledger and the three programme docs

**Status:** DONE. Documentation unit; 0 endpoint requests, 0 model calls.

## Why

`U-SPCC-66` ran the E2 turnover sweep (`measure/rows-e2-turnover-2026-11-10.jsonl`, commit
`abc1578`, 300 requests, delta 0) and left the numbers in its handoff. This unit records them
where the programme reads them: one row in `FINDINGS-LEDGER.md`, and a section in
`docs/STATE.md`, `journal/2026-11-10.md` and `orchestration/STATUS.md`.

## What was recorded

| C | value | contract | NONE | wrong | billed | compactions | fire turns | prompt tokens |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 48 | 36/48 (75.0%) | 35/48 | 12 | 0 | 14,679 | 2 | 49, 97 | 133,463 |
| 64 | 39/48 (81.3%) | 38/48 | 9 | 0 | 15,063 | 1 | 65 | 142,295 |
| 96 | **47/48 (97.9%)** | 47/48 | 1 | 0 | 14,684 known / 15,275 upper | 1 | 97 | 200,939 |

- **No accuracy turnover inside {48,64,96}.** Accuracy rises monotonically 75.0 → 81.3 →
  97.9; both steps outside the ±2/48 (±4.2 pp) band (+6.25 pp, +16.7 pp). Residual failures
  are abstentions, not wrong answers: NONE 12 → 9 → 1, wrong 0 throughout.
- **A cost turnover exists and sits at C=48.** Prompt tokens 133,463 → 142,295 → 200,939
  (+50.6%). The curves cross at C=48: past it you pay more prompt tokens for more accuracy,
  and accuracy is still climbing.
- **d32 is the fixture ceiling, not a horizon.** Deepest passing distance is 32 for all three
  (TX-03 distances 2/5/6/8/20/32). The informative quantity is the fraction passing at d32:
  4/8 → 5/8 → 7/8. The only C=96 failure is one abstention at `cp.TX-03.f08.d32` (turn 100).

## The rule this unit adds

**Cross-run billed-token comparisons are confounded even when prompts are byte-identical.**
C=48 bills 14,679 here versus 15,703 in E2 (U-SPCC-62) for byte-identical prompts
(`prompt_tokens` match on every turn). The gap is prefix-cache warmth, not work. Therefore
**only within-run comparisons are valid, and prompt tokens are the cache-independent
measure.** This qualifies E2's −5.72% cost claim — that comparison was within a single cell,
so it stands — but no billed figure from one cell may be compared to another.

## Verification

- `awk -F'|' '/^\|/ {print NF-2}'` on the ledger: 7-column rows 23 → 24, 10- and 3-column
  rows unchanged.
- `python3 tools/doc_check.py` → `OK docs clean`, exit 0.
