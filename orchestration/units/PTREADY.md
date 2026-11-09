# PTREADY

- Gradeable checkpoints: 0/12. PT fixtures use `ground_truth` not `expected` (score_longrun.py:836-845 marks unverifiable) and lack `answer_spec` (grade_v5.py:596 kind=None → _spec_error). All 12 unverifiable today.
- Masking offline PT-01: markers at turns 5 (2), 6 (1), 10 (1), 25 (1) = 5 markers total; 4 masked turns.
- Instruction line: CHECKPOINT_CONTRACT_LINE (run_longrun.py:2006-2014) supports NUM/CALL/NONE/TEXT. PT checkpoints ask doc values → TEXT form; none require CALL with kwargs.
- Smoke size: 24 completions (12 turns × 2 arms) to reach first checkpoint turn 12 with masking proven by turn 5.
- Biggest risk: 0/12 gradeable → 288-request cell cannot satisfy gate 0.2; fixtures need answer_spec/expected migration first.
