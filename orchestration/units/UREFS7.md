# UREFS7 — Re-verify candidate #7 (Gated Read Batching) numbers against raw records

## Purpose
Candidate #7 of `strategy/PAPER_CANDIDATES.md`: *"Batching binary gates is free; routed extraction cuts
context 15.3× and exposure to 0/20"*. Its card says round-2 experiments are needed but the author has
ruled out new experiments, so the paper must be packaged from round-1 material with the missing round
declared as a limitation. Before drafting, establish which recorded numbers are actually supported by
raw records on disk.

## Scope
1. Enumerate every number asserted in `papers/gated-read-batching/` (MANUSCRIPT.md, CLAIMS.md, GAPS.md,
   REFS.md, DISCLOSURE_CHANGES.md) and candidate #7's section of `strategy/PAPER_CANDIDATES.md`, with file:line.
2. Locate the raw record for each (state/, experiments/, repro/, dockets/, target docs/research/experiments/).
   Confirm/refute the re-triage ask that the 3,040-output corpus and `l1-head-to-head.jsonl` live under
   `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/`.
3. Re-derive each number from raw with command + literal output (numerator/denominator for ratios).
4. Classify: reproduced · not-reproduced · cannot-locate · derived-not-recorded.
5. State what a manuscript may/may not assert; whether 15.3× and 0/20 survive.

## Write paths (exactly)
- `strategy/GATED_READ_REVERIFY.md` (new)
- `orchestration/units/UREFS7.md`
- `orchestration/handoffs/UREFS7.json`
- `scratch/urefs7/**`

## Hard bound
30 tool calls. Report-only. No writes under `papers/`. No git against `/home/zer0null/Duval`.
Stop condition: a headline number whose raw record cannot be located within 5 attempts →
`cannot-locate`, record the search, move on.

## Report-only constraints
No drafting/editing papers, no LaTeX, no pipeline runs, no fixing wrong records (report file:line + measurement;
put the fix in `next_unit_hint`).

## Status
in_progress
