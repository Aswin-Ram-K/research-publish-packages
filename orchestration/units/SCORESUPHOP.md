# UNIT SCORESUPHOP — Score SUP and HOP cells from existing rows

**Date:** 2026-11-09 · **Live requests:** 0 (offline) · **Zero model requests**

## Objective
Score the SUP and HOP cells from existing row files; write results document and handoff.
No re-run; rows are the evidence.

## Write paths
- `experiments/ptr-engine/research-seed-concepts/RESULTS-KINDS-1-sup-hop.md`
- `orchestration/units/SCORESUPHOP.md`
- `orchestration/handoffs/SCORESUPHOP.json`

## Key results
SUP masking-no-fetch: contract/value 13/48 (d2 12/12, d6 0/12, d20 0/12, d32 1/12).
SUP bounded-context-fetch: 22/48 (d2 3/12, d6 9/12, d20 5/12, d32 5/12).
HOP masking-no-fetch: 12/48 (d2 12/12, rest 0).
HOP bounded-context-fetch: 16/48 (d2 9/12, d6 4/12, d20 0/12, d32 3/12).
Request rows: SUP 103 + 166; HOP 180 + 270. All billed, no suppression markers, raw==dedup.
Stale-value answers (SUP): 3 rows / 2 distinct checkpoints, fetch arm, d=2 only.
Activation gates: masking fetch_rows=0 (met); fetch fetch_rows≥40 (met: 253/104 total).
