# V15Gate01 — gate-0.1 answer-contract adjudication

Verifier, zero model requests. Adjudicated current bytes.

## Verdicts

1. `score_longrun.answer_of` (current) delegates to `grade_v5.parse_answer_contract` and returns parsed value:
   - `ANSWER: NUM 64` -> `'64'`
   - `ANSWER: CALL ledger.record_refusal(scope="s", serialized_ref=text, code=error.code), before re-raising` -> raw text (grade_v5 rejects trailing prose as `call_not_parsable`), so answer_of falls through to raw text.
   - Canonical call string for a clean CALL: `ledger.record_refusal(code=error.code, scope="s")`.
   Function body verified at `experiments/ptr-engine/longrun/score_longrun.py:150-186`.

2. Delegation check: `grade_v5.py` line ranges verified on current bytes:
   - `parse_answer_contract` 353-384 (strips ANSWER line, tolerates prose)
   - `_documented_call` 481-486 (find/rfind)
   - `_check_documented_call` 610-621 (callee + kwarg sets, `...` elision)
   - `grade_cell` 768-871 (NUM by value, CALL kwargs order-insensitive)
   Divergence demonstrated: prose input gives score path `fail` (text match) vs grade_v5 `undecidable`. Input `ANSWER: CALL ... code=error.code, scope="s"` (missing serialized_ref) gives both `fail` but for different reasons. So yes, `score_longrun` carries a divergent second grading path despite delegating parsing: it converts the parsed contract back to a string and re-grades with `match_answer`, discarding grade_v5 verdict semantics (undecidable, kind mismatch, kwarg sets, elision). Must delete the conversion + `match_answer` re-grade in `eval_fact` and call `grade_v5.grade_cell` (or truth-derived verdict) instead; keep answer_of only as a display helper or remove it.

3. Red->green: reverted answer_of to raw content -> 4/5 gate tests fail (`test_num_65...`, `test_cp3...`, `test_truncated...`, `test_verify_turn...`); restored -> 5 passed. Wrong value (NUM 65) -> `failed_required=['cp.t12','acc.cp1','acc.1']`. Missing required fact (serialized_ref omitted) -> `failed_required=['cp.t46','acc.cp3']`. Distinguishable by named check id.

4. v4 checkpoints carry `match: exact` consistently in runtime-v4 and default-exact in authored v4; cp3 expected `ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)` is alphabetically ordered. `run_longrun.CHECKPOINT_CONTRACT_LINE` (lines 2008-2012) is stricter than scorer in some places ("emit exactly one line", NUM <integer>) but scorer accepts bare numerals, citations, prose preambles the instruction does not mention; conversely instruction says "anything after that line is not read" while scorer rejects trailing after NONE (`trailing_after_none`). Quote both sides recorded.

5. Whole affected suite: collection error in `test_verdict_semantics.py` (exit-code partition drift, exit code 14 unclassified) unrelated to gate. Relevant gate/answer/grade tests pass (23 passed). Broader run shows pre-existing failures in cap_gate, claim_rows, row_provenance, withdrawn_screen (repeat-identity / screen trips), not caused by this adjudication.

## Overstated / not reproduced
- Advisory claim that `grade_v5` already fully owns these rules is partially true for parsing but false for grading: score_longrun still re-derives verdicts via text match.
- `answer_of` returning "TEST" was not current bytes (current delegates to grade_v5); earlier stale read was wrong.
- Full suite could not be run to completion within tool time cap; reported in batches.

## Ruling
Gate 0.1 scorer contract is now correct on the parsed value, but the code is NOT non-duplicative: delete answer_of's contract-to-string conversion and eval_fact's match_answer re-grade, replacing with grade_v5.grade_cell verdicts.