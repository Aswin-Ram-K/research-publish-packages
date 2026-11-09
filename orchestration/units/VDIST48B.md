# VDIST48B — TX-02.v1 adversarial audit

Verdict: **pass**.

Target: `experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json`
Checker/test: `experiments/ptr-engine/longrun/check_pointer_fixtures.py`, `experiments/ptr-engine/longrun/tests/test_tx02_distance.py`

No fixture, checker, test, `run_longrun.py`, or `score_longrun.py` was edited. Temporary guard disables were restored; `git diff` for `check_pointer_fixtures.py` is clean.

## 1. Turns
`checkpoint_count=48`; `unique_checkpoint_turns=48`; distance counts `{2:12,8:12,20:12,32:12}`; `measured_distance_mismatches=0`.

## 2. Asked, not just graded
`checkpoint_expected` and `checkpoint_prompt` called for all 88 turns: `turns_with_question=48`; `non_empty_expected=48`; `mismatches=0`.

## 3. Leak
`CPF.validate(fx)=[]` (0 errs); manual leak hits=0 across system prompt, `items[].body`, all turn questions, and other turns' `tool_outputs[].body` for all 48 expected values.

## 4. Masking reach
`Planner('masking-no-fetch').build(33)`: `masked_rows=6`; marker `[MASKED doc-fact-01@r1]` present; expected `2003` absent from rendered prompt. Fragment:
```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
[MASKED doc-fact-01@r1]
ANSWER (T1): 
```

## 5. Kind/type
`answer_kind counts {NUM:48}`; expected type counts `{NUM:48}`; TEXT checkpoints=0; TEXT survival vacuous.

## 6. Guards red/green
- duplicate checkpoint turn: disabled -> FAIL (missing `duplicate checkpoint turn`; other errors shown); restored -> 1 passed.
- kind/type mismatch: disabled -> FAIL `errs=[]`; restored -> 1 passed.
- injected question identity: disabled -> FAIL `errs=[]`; restored -> 1 passed.

## 7. Budget
Loaded prompt-token estimate (padding answers): transcript-grow turn3=507, turn88=2548; masking-no-fetch turn3=507, turn88=10072. A 32768 window does not bind (max ~10072).

## 8. pytest test_tx02_distance.py
```
.............                                                            [100%]
13 passed in 0.05s
```

## 9. pytest test_tx01*.py
```
.......                                                                  [100%]
7 passed in 0.03s
```

## Not reproducible
None.
