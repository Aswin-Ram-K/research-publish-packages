# RefusalFix

- status: done
- artifacts: experiments/ptr-engine/longrun/grade_v5.py (parse_answer_contract updated to treat NOT-AN-ANSWER as NONE refusal)
- evidence: parse_answer_contract now returns answer_kind=NONE for both "ANSWER: NONE" and "ANSWER: NOT-AN-ANSWER"
- blocker: none
- next_unit_hint: Gate01Close
- write_paths: experiments/ptr-engine/longrun/grade_v5.py, orchestration/units/REFUSALFIX.md, orchestration/handoffs/REFUSALFIX.json