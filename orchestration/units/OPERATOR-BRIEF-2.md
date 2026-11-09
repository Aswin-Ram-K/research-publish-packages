# OPERATOR-BRIEF-2 — re-issue the operator page

**Status:** done. **Requests:** 0 (OFFLINE: zero inference requests, zero network). **Bound:** 30 tool calls.
**Trigger:** task board card, automated tag; no human, never ask a question.

## Objective

Replace `docs/OPERATOR-BRIEF.md` (issue 1) with an issue-2 page (~2 pages) reflecting six changes: de-duplicated
spend (1 071 of 4 320, raw 1 101), the priced adjudicating grid A\* (792 requests), `tokens_to_verified_success`
now produced for 3 of 23 pairs, quality 5/43 on the defensible denominator, H1/H2/H3 all still
`not adjudicable` for three different reasons, and a corrections section.

## Write paths (exactly)

- `docs/OPERATOR-BRIEF.md`
- `experiments/ptr-engine/measure/OPERATOR-BRIEF.json`
- `orchestration/units/OPERATOR-BRIEF-2.md`
- `orchestration/handoffs/OPERATOR-BRIEF-2.json`
- `orchestration/journals/OPERATOR-BRIEF-2.jsonl`

## Method

Every figure was re-read from a named artefact and the path written beside it. The two figures that had no
independent derivation — the uncached prompt tokens per completed turn — were **re-derived from the rows
files** (`rows-longrun-c-2026-10-26.jsonl`, `rows-longrun-v3-2026-10-26.jsonl`) rather than carried forward
from issue 1. No threshold, verdict, frozen artefact, grader, fixture or rule hash was changed.

Disagreements left visible rather than rounded away: raw vs de-duplicated spend (1 101 / 1 071), and A\*'s
remaining (2 427 as the schedule prices it against the raw ledger, 2 457 on de-duplicated spend).

## Bound and outcome

Used 21 tool calls of 30. No partial: every required section exists and every cell carries a path.
