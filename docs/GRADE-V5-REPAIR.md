# GRADE-V5-REPAIR - three defects closed, and the rule a reader needs

Unit `GRADE-V5-REPAIR`, run offline (zero inference requests) after `GRADE-V6-DERIVE`
settled. Input: `ATTACK-GRADE-V5` (41 hand-written probes, FN 0/8, FP 3/22, three
dangerous findings). Output: `experiments/ptr-engine/longrun/grade_v5.py` repaired,
18 new tests red -> green, the 12 v6 items still 12/12.

## The rule, stated once (read this first)

> **A verdict is a function of the row's `content` and the AST-derived truth, and of
> nothing else.** `NUM` passes only on an exact decimal-integer assertion; a row's own
> `answer_kind`/`answer_value` fields may never decide a verdict; and a turn that
> expresses no contracted value is `undecidable`, not `fail` - so it cannot enter the
> decidable denominator, which is `pass + fail` and nothing else.

## T1 - NUM is integer equality

`_integral_numeral()` in `grade_v5.py` accepts only an exact decimal integer.

| answer | verdict | reason |
|---|---|---|
| `ANSWER: 64` | pass | `num_equal` |
| `ANSWER: NUM 64` | pass | `num_equal` |
| `ANSWER: 64.` | pass | a sentence period is punctuation, not a fraction |
| `ANSWER: 64 (resolve.py:39)` | pass | citation dropped, 64 asserted |
| `ANSWER: 64.99` | **fail** | `num_not_integer:64.99` |
| `ANSWER: NUM 64.999` | **fail** | `num_not_integer:64.999` |
| `ANSWER: 64.0` | **fail** | `num_not_integer:64.0` |
| `ANSWER: NUM 0x40` | **fail** | `num_not_integer:0x40` |
| `ANSWER: 0x40`, `ANSWER: six`, `ANSWER: sixty-four` | **undecidable / unparseable** | no integer assertion was made |
| `ANSWER: 640` | **fail** | `num_mismatch` (digit-prefix trap, never read as 64) |

The value the grader saw is carried in the cell (`reason`, and
`answer_parse_detail.rejected_numeral`). Nothing is rounded or truncated: the old
`int(value)` coercion is gone.

## T2 - a row cannot grade itself

`_parsed_from_row` parses `content` **always**. The runner's convenience fields
(`answer_kind`, `answer_value`, `answer_raw`, `answer_parse_error`) are cross-checked,
never trusted:

* fields absent (or equal to the content parse) -> the content parse decides;
* fields **disagree** -> `RowFieldDisagreement`, a hard error naming *both* sides
  (`row claims kind=... value=..., but content ... parses to kind=... value=...`).
  Direct callers get the exception; `grade_rows` records the same error per cell as
  `verdict=fail`, `reason=row_fields_disagree_with_content`, with
  `row_field_conflict={"row": ..., "content": ..., "error": ...}`. It is never a silent
  preference for either side, and one spoofed row cannot abort the whole arm.

Measured: a row whose content is `ANSWER: TEXT something` but whose fields claim
`NUM 64` now grades **fail**, not `pass/num_equal`.

## T3 - non-answers are undecidable

| form | reason | verdict |
|---|---|---|
| empty turn (no `ANSWER:` line, no text) | `no_answer_line` | undecidable |
| prose with no `ANSWER:` line | `prose_only` | undecidable |
| `ANSWER:` with nothing / whitespace after it | `empty_answer` | undecidable |
| `ANSWER: TEXT` with an empty body | `empty_text` | undecidable |
| `ANSWER: NUM` with an empty body | `empty_num` | undecidable |
| `ANSWER: <body in no contract form>` | `unparseable` | undecidable |

Everything else that expresses a value and is wrong stays a **fail**: `ANSWER: 65`,
`ANSWER: 640`, `ANSWER: NUM 0x40`, a CALL with the wrong kwarg, two `ANSWER:` lines
(ambiguous, rejected). A missing turn stays `fail/turn_missing` - the omission rule
(16/16 rejections) is untouched.

The arm summary now reports `decidable = passed + failed` and, beside it, `cells`,
`undecidable`, `undecidable_reasons`, `missing`, `text_reported`. The CLI prints
`acc=1/1 decidable=1(pass 1, fail 0) undecidable=2 missing=0 text=0`. `verified_success`
also requires zero undecidable cells.

## Before / after on the 41 probes

| | before | after |
|---|---|---|
| false negatives (`expect=pass` not passed) | **0/8** | **0/8** |
| false positives (`expect=fail` passed) | **3/22** (P12, P37, P38) | **1/22** (P12) |
| mandatory attacks | 7 LIMITATION-unsat, 8 LIMITATION-unsat, **10 DEFECT-unsat** | 8 SATISFIED, **10 SATISFIED**, defect-class unsatisfied = none |
| tool exit | 1 | 0 |

Two residuals, neither a grader defect:

* **P12** is `expect=fail` while its own note says *"the fixture elides scope; the
  answer may write a literal `...`"*. The fixture's `elided_kwargs` rule (v5 contract,
  unchanged) passes it. The probe expectation is wrong; the grader was not tuned to it.
* **T7** is unsatisfiable by construction: its predicate requires `passed == 0` in the
  `missing_turn` arm (which has two correct turns), computes `undecided` as
  `a["decidable"] != a["decidable"]` (always False), and treats `turn_missing` as
  decidable - which the omission rule requires it to remain.

## Red -> green

```
RED   GRADE_V5_MODULE=<pre-repair copy, 4 reverts>
      pytest experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py -q  ->  10 failed, 8 passed
GREEN pytest experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py -q  ->  18 passed
      pytest experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py -q  ->  14 passed   (12/12 items derive)
```

## Integration caveat (outside this unit's write paths)

`analyze_stats.py` (`graded_n`) still counts non-answers as decidable, so the
DECIDABILITY-SEAM consistency gate now **refuses** (grader decidable=1 vs analyser
graded_n=3) instead of printing a number. `test_decidability_seam.py:163/190` assert the
old `decidable=3` denominator. Both are outside this unit's declared write paths; the
safe failure (a printed refusal, not a wrong percentage) is what the seam exists for.
Until `graded_n` adopts `pass + fail`, the printed accuracy is correct per arm but the
seam will not certify it.
