# UNIT SCOREAGGABS — Score AGG and ABS cells from existing rows

**Date:** 2026-11-09 · **Live requests:** 0 (offline) · **Zero model requests**

## Objective
Score the AGG and ABS cells from existing row files; write results document and handoff.
No re-run; rows are the evidence.

## Write paths
- `experiments/ptr-engine/research-seed-concepts/RESULTS-KINDS-2-agg-abs.md`
- `orchestration/units/SCOREAGGABS.md`
- `orchestration/handoffs/SCOREAGGABS.json`

## Key results
AGG masking-no-fetch: contract/value 0/48 (all buckets 0). AGG bounded-context-fetch: 4/48 (d2 0/12, d6 0/12, d20 1/12, d32 3/12); activation FAILED (29 fetching turns < 40).
ABS masking-no-fetch: 3/48 (d2 3/12, rest 0); over-refuses (24 false refusals / 36 answerable).
ABS bounded-context-fetch: 15/48 (d2 6/12, d6 6/12, d20 3/12, d32 0/12); activation PASSED (42 fetching turns).
Request rows: AGG 100 + 142; ABS 100 + 142; total 484.