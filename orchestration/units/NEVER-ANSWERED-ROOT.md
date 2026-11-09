# UNIT `NEVER-ANSWERED-ROOT` — why is there no answer to grade?

**Status:** done · **Offline:** 0 requests, read-only on every existing file · **Bound:** ≤26 tool calls.

## Objective
Classify all **63** `never_answered` cells of the `QUALITY-REASON-MIX` primary T3 population
(8 `rows-longrun-*` grids) **from the rows**, not from the grade documents' reason strings; print
the 63-row table and per-arm/per-grid tallies; name any cell whose bucket contradicts its grader
reason; then decide whether the wall is an **arm**, **fixture-contract**, or **harness-epoch**
property, with the v4/v5 seam ruled on (correct / regression).

## Method
- Cell list and checkpoint truth from `measure/QUALITY-REASON-MIX.json` + the 8 grade-v5 documents;
  every bucket from the cell's own turn row (`per_turn[-1]`, the same "last row wins" rule as
  `grade_v5.grade_rows`).
- Buckets: `turn_absent`, `empty_completion`, `cap_hit` (incl. the historical **128-token stage-1
  cap**, which the stage-1 runner recorded only as `completion_tokens == 128` with no
  `max_tokens` field — `run_longrun.py:2698`), `reasoning_only`, `tool_loop`,
  `prose_asserts_value` (a *stated* number or call, after stripping `#L39` line refs, byte sizes,
  pointer handles, code fences and `<tool_call>` blocks), `prose_other`, `no_answer_no_prose`.
- Era from the row (`max_tokens` field present?), contract from the row's `fixture_sha256`
  (`LR-01.v2` declares `answer_marker: null`; v3+ require it).

## Write paths
`docs/NEVER-ANSWERED-ROOT.md` · `experiments/ptr-engine/measure/NEVER-ANSWERED-ROOT.json` ·
`experiments/ptr-engine/tools/never_answered.py` · `orchestration/units/NEVER-ANSWERED-ROOT.md` ·
`orchestration/handoffs/NEVER-ANSWERED-ROOT.json` · `orchestration/journals/NEVER-ANSWERED-ROOT.jsonl`

## Result (one line)
The wall is a **harness-epoch and contract artefact, not an arm property**; the v4/v5 seam is
**mixed** — correct tightening on 11/17 cells, regression on 6/17.
