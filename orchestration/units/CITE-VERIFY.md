# UNIT CITE-VERIFY

**Purpose.** Resolve the three `[CITATION NEEDED — verify]` markers in
`papers/context-cache/MANUSCRIPT.md` (lines 887, 906, 911) against real, checkable sources, without
breaking the three line-number-pinned guards.

**Bound.** 30 tool calls; at most 2 fetch attempts per marker.

**Write paths.** `papers/context-cache/MANUSCRIPT.md`, `papers/context-cache/CITATIONS.md`,
`orchestration/units/CITE-VERIFY.md`, `orchestration/handoffs/CITE-VERIFY.json`.

**Kill condition.** Any fix that needs a new line is reported as a blocker, never applied.

## Constraints honoured

- Every edit is an in-place text replacement inside an existing line. `wc -l` is 1214 before and after.
- No number in the manuscript was changed.
- The line carrying the private endpoint (`1937`-era § 11) was not edited; `192.168.2.168:8012` at
  line 993 is untouched by this unit.
- No citation, id or venue was invented. Each was confirmed against the source's own landing page.

## Result: 3 of 3 resolved

| Marker | Line | Resolution |
|---|---|---|
| 1 | 887 | Methodological sentence about the citation policy — restated self-consistently, naming the SGLang attention-backend documentation already cited at line 896. |
| 2 | 906-907 | vLLM/PagedAttention — arXiv:2309.06180, doi:10.1145/3600006.3613165. SGLang/RadixAttention — arXiv:2312.07104. Deleted the now-false clause "not their papers". |
| 3 | 911-912 | Parallel Context Compaction for Long-Horizon LLM Agent Serving — arXiv:2605.23296, doi:10.48550/arXiv.2605.23296. Scope kept to the family premise; the paper's own contribution claim stays unattributed. |

## Incidents

Two self-inflicted edit scripts used off-by-one indices and produced ragged text. Both were caught by
reading the rendered lines, and one was rolled back from a pristine copy (`/tmp/MANUSCRIPT.before.md`,
sha256 `a8dec093…`). No line-count change and no number change occurred at any point.

## Verification

See `orchestration/handoffs/CITE-VERIFY.json`.
