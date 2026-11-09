# UNIT GRADE-V5-T4-DECORATION (repair T4: decoration is not a value)

**Status:** done · **Requests:** 0 · **Network:** none · **Bound:** one grader file, one test file,
one measurement; stop if a relaxation would move a threshold, a kind branch, the
decidable/fail semantics, the non-answer rule, the `turn_missing` rule or an exit code.

## Defect (measured, not hypothesised)
`orchestration/handoffs/ERA-B-GRADE-REHEARSAL.json`: 64 correct-answer rows → 50 pass / 14 not,
11 of them card-required shapes. `e2` CALL + provenance `(...)` 0/4, `b` trailing period on CALL
4 fail + on NONE 3 undecidable, `f` `NONE — <justification>` 0/3. Every rejected row asserts the
same value as a passing row; `NUM 64.` passed all along (`_integral_numeral`: the lone period is
punctuation) while `CALL_RE` anchored on `\)\s$` and the NONE branch compared the whole first
token. The contract rewarded emitting nothing extra and punished citing provenance.

## What was done
One decoration pass, `grade_v5._strip_decoration`, called ONCE from
`parse_answer_contract` before the head split / kind branches:
(a) strip one trailing `.` (not `..`) on every kind; (b) strip a balanced trailing `(...)` or a
trailing citation from the imported `dv.citation_spans`, only while the remainder is still a
complete answer of the SAME kind; (c) keep `NONE` a denial across a `—`/`-`/`;`/`(` justification
UNLESS the payload carries a value (numeral, dotted name, callable `(`, snake_case token).
Every removed fragment is recorded in `cell["decoration_stripped"]`.

## Evidence
- 64/64 correct rows pass (was 50/64); 0/9 negative controls pass (unchanged).
- 6 red cases still fail with their verbatim reasons: `kwarg_value_mismatch:serialized_ref`,
  `num_mismatch`, `callee_mismatch`, `answer_not_contract:trailing_after_none`,
  `num_not_integer:64.5`, `unparseable`.
- Era-A re-derivation of `measure/cell-pointer-stable-20261026T145722Z.grade-v5.json`:
  pristine vs repaired → **0 deltas** (pristine grader reconstructed byte-for-byte, sha
  `056eb605…`, and it reproduces the stored pin exactly). Stored 1/3 vs re-derived 1/1 is
  pre-existing version drift (that file has `grader_sha256: null`).
- Combined harness digest moved: pin with pristine grader `fa6fd8cc…` (= stored),
  with repaired grader `a3fa2ee0…`. Regenerate the pin AFTER this card and
  `BUDGET-STAGE-MAX-TURNS` have both landed.

## Known, reported, not taken
`tests/test_era_b_grade_rehearsal.py` pins the pre-repair grader sha AND asserts the pre-repair
rejections (5 tests) — outside this card's write paths, so it now fails by design. Regenerating
`measure/ERA-B-GRADE-REHEARSAL.json` and updating that file is a separate decision for its owner.

## Write paths
`experiments/ptr-engine/longrun/grade_v5.py` · `experiments/ptr-engine/tests/test_grade_v5_decoration.py`
· `orchestration/units/GRADE-V5-T4-DECORATION.md` · `orchestration/handoffs/GRADE-V5-T4-DECORATION.json`
· `orchestration/journals/GRADE-V5-T4-DECORATION.jsonl` · `experiments/ptr-engine/measure/GRADE-V5-T4-MATRIX.json`
