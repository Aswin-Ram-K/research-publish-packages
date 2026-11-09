# REFUSALFIX2 - out-of-vocabulary refusal laundering
## Claim
parse_answer_contract mapped ANSWER: NOT-AN-ANSWER -> NONE (legacy_refusal_token), inflating abstention scores.
## Change
- grade_v5.py: removed legacy mapping; unknown kind -> answer_kind=OOV, answer_parse_error=out_of_vocabulary, detail.offending_token, answer_raw preserved; bare-numeral NUM path retained.
- grade_v5.py grade_cell: OOV -> verdict=undecidable, ungradeable=True, offending_token surfaced (not pass/fail).
- score_longrun.py answer_of: explicit OOV branch returns raw text (no longer 'NONE'), so scorecard cannot count it as abstention.
- Tests: test_answer_contract expectations updated to out_of_vocabulary; new test_refusal_fix2.py covers NONE/TEXT/NUM64/NUM65/OOV.
## Evidence
Parser: NONE->NONE abst=True; NOT-AN-ANSWER->OOV err=out_of_vocabulary abst=False offending=NOT-AN-ANSWER; TEXT hello->TEXT; NUM64->pass; NUM65->fail num_mismatch.
Scorecard: answer_of(NONE)='NONE'; answer_of(NOT-AN-ANSWER)='ANSWER: NOT-AN-ANSWER' (not NONE).
Red->green: with legacy restored, test_not_an_answer_is_oov_not_refusal fails (None vs OOV); with it removed, 4 passed.
Suite: core subset 36 passed; test_verdict_semantics collection error is pre-existing exit-code partition drift (code 14), unchanged.
