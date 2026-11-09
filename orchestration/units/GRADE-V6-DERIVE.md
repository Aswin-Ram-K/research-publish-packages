# UNIT `GRADE-V6-DERIVE`

**Status:** done — `LR-01.v6.json` is fully gradeable (12/12).
**Bound:** ≤30 tool calls, zero inference requests. Used 30; 0 requests; 0 cells; 0 rows.
**Tag:** `automated` — no human, no `ask_user_question`, OFFLINE.

## Purpose (one purpose)

The v6 fixture the coverage gate passed has 12 decidable checkpoints, but
`grade_v5.derive_truth` could turn only 8 into truth: the three `NONE` items
(`cp.5.t14`, `cp.7.t20`, `cp.11.t42`) aborted with
`fixture_truth_mismatch: <id> has no usable answer_spec`, and `cp.10.t36`
(`call_at_line`) died with `KeyError: 'function'`. Make the grader able to grade the
fixture it accepted — without re-authoring or editing the fixture.

## Write paths (exactly, as declared)

* `experiments/ptr-engine/longrun/grade_v5.py`
* `experiments/ptr-engine/longrun/score_longrun.py` (the acceptance mirror only)
* `experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py`
* `docs/GRADE-V6-DERIVE.md`
* `orchestration/units/GRADE-V6-DERIVE.md`
* `orchestration/handoffs/GRADE-V6-DERIVE.json`
* `orchestration/journals/GRADE-V6-DERIVE.jsonl`

## What was done

1. **Confirm first.** Re-ran per-item `answer_spec` derivation over all 12 ids and
   reproduced the unit's split **exactly: 8 gradable / 4 not** (no divergence, so the
   unit's report is not the headline). Table in `docs/GRADE-V6-DERIVE.md` §1.
2. **`NONE` branch** (`no_attr_call_inside_function`): truth = boolean absence of the
   named attribute call inside the named function, derived from the AST (attribute
   chains + bare/aliased names). If the attribute *is* called there the truth says so
   and `ANSWER: NONE` grades `fail` naming the attribute and site — never an abort.
3. **`call_at_line` branch**: selects the `ast.Call` at the pinned line and parses
   callee + kwargs through the existing CALL parser; refuses with a named
   `SystemExit` when that line holds no call of the named callee.
4. **`fixture_truth_mismatch` is never silent**: one shape —
   `fixture_truth_mismatch: item <id>: answer_spec kind '<KIND>', rule '<rule>': <detail> (fix the answer_spec at <file>)` —
   for unknown kinds, unknown rules, missing derive keys, documented-vs-AST
   disagreement, and missing functions.
5. **Red→green**: `experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py` (14 tests) — 12/12 derive and grade
   pass/fail correctly; NONE red half; `call_at_line` red half; TEXT never passes; the
   8 pre-change truths asserted unchanged; the score mirror grades 12.
6. **Mirror in `score_longrun.py`**: `mirror_answer_contract` (stage `3b` in `score()`)
   grades every `answer_spec` checkpoint as `acc.derive.<id>` via `grade_v5`;
   no-op on authored fixtures; existing checks untouched.

## Constraints honoured

`LR-01.v5.json` (sha256 `967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567`)
and `LR-01.v6.json` unedited; `cell.py`, `client.py`, `run_longrun.py`,
`analyze_stats.py`, `fixture_coverage.py`, `matrix_audit.py` unedited; NUM and
CALL/`call_inside_function` derivations byte-identical; TEXT still never passes.

## Kill condition / stop

If the 12 ids had not all derived, or the two red halves had not been observed, this
unit was to report `partial` with the remainder named. Neither happened.

## Note (out of scope, pre-existing)

`tests/test_cell.py::test_f_analysis_refusal` fails with
`InsufficientSamples: wilson_ci needs n >= 1 (got n=0)` raised at cell stage 6/7
`analyse`; `derive_truth` runs only in preflight (stage 1/7), so this is not caused by
this change and was not touched (`cell.py` is not in the write paths).
