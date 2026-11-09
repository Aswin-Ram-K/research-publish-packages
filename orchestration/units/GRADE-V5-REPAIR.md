# UNIT GRADE-V5-REPAIR

**Status:** partial (deliverables complete; one cross-unit integration gate open)
**Run:** offline, zero inference requests, after `GRADE-V6-DERIVE` (8adcf796) settled.
**Bound:** <=30 tool calls. Journal first, handoff `partial` within 5 calls.

## Objective
Close the three defects `ATTACK-GRADE-V5` (41 probes, FN 0/8, FP 3/22) measured in
`grade_v5.py`: NUM truncation, rows grading themselves from their own convenience
fields, and non-answers counted as `fail` inside the decidable denominator.

## Result
* T1 `NUM` = exact integer equality (`64.99`, `NUM 64.999`, `64.0` -> fail naming the
  value; `0x40` / `six` / `sixty-four` rejected; `64.` still passes).
* T2 verdicts derive from `content` only; disagreeing row fields are a hard error
  naming both (`RowFieldDisagreement`), surfaced per cell as
  `fail/row_fields_disagree_with_content`.
* T3 non-answers are `undecidable` (`no_answer_line`, `prose_only`, `empty_answer`,
  `empty_text`, `empty_num`, `unparseable`); `decidable = pass + fail`, printed beside
  the undecidable/missing counts.
* 41 probes: FN 0/8 -> 0/8, FP 3/22 -> 1/22 (residual P12 has a wrong expectation),
  exit 1 -> 0, defect-class unsatisfied none.
* 12/12 v6 items still derive; all 12 correct answers pass (`test_grade_v6_derive.py`
  14 passed).
* New tests: red 10 failed / 8 passed against a pre-repair copy -> green 18 passed.

## Open
`analyze_stats.py` `graded_n` must adopt `decidable = pass + fail`;
`test_decidability_seam.py:163/190` still assert the old `decidable=3`. Both are outside
this unit's write paths; the seam now refuses (safe) instead of printing a number.

## Write paths (exactly)
`experiments/ptr-engine/longrun/grade_v5.py`,
`experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py`,
`docs/GRADE-V5-REPAIR.md`, `experiments/ptr-engine/measure/GRADE-V5-REPAIR.json`,
`orchestration/units/GRADE-V5-REPAIR.md`,
`orchestration/handoffs/GRADE-V5-REPAIR.json`,
`orchestration/journals/GRADE-V5-REPAIR.jsonl`.
