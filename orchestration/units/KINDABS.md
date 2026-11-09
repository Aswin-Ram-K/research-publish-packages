# KINDABS — absent-fact measurement fixture

**Purpose.** Fixture `TX-ABS` where 12 of 48 checkpoints ask about a fact that was never recorded; the only correct answer is `ANSWER: NONE`. Distances {2,6,20,32}, 12 checkpoints per bucket, 3 absent + 9 answerable per bucket (36 answerable NUM values, all distinct). Zero live requests.

**Write paths.**
- `experiments/ptr-engine/longrun/tasks-v7/TX-ABS.v1.json`
- `experiments/ptr-engine/longrun/tests/test_tx_abs.py`
- `orchestration/units/KINDABS.md`
- `orchestration/handoffs/KINDABS.json`

**Invariant (kind-specific).** For each absent checkpoint, a mechanical search over every tool body, question and item body finds no candidate value (the referenced `VAL_G` appears in no body, item body, or system prompt); for each answerable checkpoint, exactly one body supplies its value. Absent checkpoints use `ANSWER: NONE` / `answer_spec.kind = NONE`; answerable use NUM.

**Scorer distinction.** `score_longrun.eval_fact` compares `answer_kind` to `answer_spec.kind`. A correct abstention has `answer_kind == "NONE"` (parsed by `grade_v5.parse_answer_contract` for a bare `ANSWER: NONE` with no trailing tokens) and passes against `expected_kind == "NONE"`. An out-of-vocabulary reply (`ANSWER: MAYBE ...`) parses as `answer_kind == "OOV"` with `answer_parse_error == "out_of_vocabulary"` and is graded `ungradeable`, never as a correct NONE. Thus a correct NONE is a contract-compliant absence, while an OOV refusal is an ungradeable parse failure.

**Checker.** Absent cps cannot satisfy `duplicate_expected`, `gradability`, or `reachability` (NONE is repeated and has no source value / kind mismatch / no source value). Validated with `CPF.validate(fx, disabled={"duplicate_expected","gradability","reachability"})` → OK, outcomes all four, checkpoints=48, N=100.

**Evidence.**
- checker: `TX-ABS.v1.json: OK` (disabled set above), outcomes=['NOT_FOUND','OK','SCOPE_UNGRANTED','STALE_OR_REVOKED'], checkpoints=48, N=100.
- pytest: `test_tx_abs.py` 9 passed.
- rows: 48 unique turns; 3 absent per bucket (12 total); 9 answerable per bucket (36 total); 36 distinct answerable values.
- mechanical absence proof: `VAL_G` appears in no tool body, item body, or system prompt; each answerable value appears in exactly one body.

**Blocker.** none. None. (disabled checker checks noted above).