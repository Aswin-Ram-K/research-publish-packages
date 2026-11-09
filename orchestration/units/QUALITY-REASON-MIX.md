# Unit QUALITY-REASON-MIX

**Status:** done · **Bound:** ≤30 tool calls, 0 inference requests — used 29 calls, 0 requests.
**Date:** 2026-10-26 · **Tag:** automated / verdict (offline, read-only on every grade document).

## One purpose

Decide whether H3's checkpoint metric measures pointer mechanics or answer-format
compliance, by tabulating *why* every checkpoint check fails, per arm, per grid,
from the grade documents already on disk.

## Deliverables

| path | role |
|---|---|
| `experiments/ptr-engine/tools/reason_mix.py` | tabulator + classifier + offline arm-blindness probe |
| `experiments/ptr-engine/measure/QUALITY-REASON-MIX.json` | every `(grid, arm, checkpoint)` row with the grader's `reason` verbatim |
| `experiments/ptr-engine/measure/tests/test_reason_mix.py` | 12 tests, reprodubibility of the published JSON |
| `docs/QUALITY-REASON-MIX.md` | the finding |
| `orchestration/handoffs/QUALITY-REASON-MIX.json` | report-back |
| `orchestration/journals/QUALITY-REASON-MIX.jsonl` | journal |

## Result

Primary population (8 post-T3 `grade_v5` documents, real grids only, 66 cells):
`pointer-stable` 2 passes / 24 non-passes (21 `never_answered`, 1 contract);
other three arms 0 passes / 42 non-passes (**42 `never_answered`, 0 contract, 0
wrong value**). All 75 cells across 11 documents: 63 `never_answered`, **0
`answered_wrong_value`**, 3 contract, 0 undecidable, **0 unclassifiable**.

`bucket 3 / non-pointer non-passes = 0/42 = 0.0 %` → the card's 60 % condition is
**not met**. H3 as frozen compares **answer production**, not pointer mechanics and
not (on the reason strings as written) contract compliance. All three pointer
successes are the same checkpoint (`cp.0.t12`, `ANSWER: 64`, gate `num_equal`); a
`transcript-grow` arm passes the same fixture 3/3 the moment it writes the contract
form (two demo documents), and the grader is arm-blind (probed offline:
`identical_for_both_arms: true`).

Smallest change **named, not made**: publish a per-arm `answered_ratio` beside every
accuracy. H3's frozen 2-of-12 margin can only change via a `PARM-1` errata
(precedent `67e4cd7f`).

## Hard rules honoured

- Offline: 0 requests, no live run, no fixture edit, no grader edit, no published
  document rewritten.
- Every classification carries the grader's `reason` string verbatim in the JSON.
- `unclassifiable` = 0; the one reason/parse-error contradiction is flagged in
  `reason_disagreement_cells` and its sensitivity is reported rather than guessed.
- Percentages carry numerator, denominator and source document.

## Blocker / next

None. `next_unit_hint`: the `never_answered` wall (63/66) is a *runner/prompt-epoch*
question, not an arm question — the 8 cells v4 could read but v5 calls `prose_only`
name the seam. Separately, the pre-T3 document `cell-pointer-stable-20261026T145722Z`
carries a parse error (`not_a_contract_form`) the on-disk `grade_v5.py` cannot emit;
that is a recorded gap for whoever owns grader provenance.
