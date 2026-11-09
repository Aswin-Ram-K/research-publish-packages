# VDIST48 — TX-02.v1 independent audit

Verdict: **fail** — the nine requested checks pass, but a separate blocking fixture defect leaves 26 of 48 checkpoints unprompted.

Target: `experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json`
Checker/test: `experiments/ptr-engine/longrun/check_pointer_fixtures.py`, `experiments/ptr-engine/longrun/tests/test_tx02_distance.py`

No fixture, checker, or test file was edited. The duplicate guard was disabled only via the checker's `disabled={"duplicate_expected"}` argument.

## Blocking finding (outside the nine-item checklist)

`TX-02.v1.json` declares 48 checkpoints and 48 `checkpoint_turns` entries, but only **22 unique turns**:

```
checkpoint_turns len 48 unique 22
duplicate counts {9: 2, 12: 2, 15: 2, 18: 2, 21: 3, 24: 3, 27: 3, 30: 3, 33: 4, 36: 4, 39: 3, 42: 3, 45: 2, 48: 2, 51: 2, 54: 2}
```

The runner asks only the **first** checkpoint question at a turn. Both `run_longrun.py:2059 checkpoint_expected` and `run_longrun.py:2104 checkpoint_prompt` use `next(cp for cp in checkpoints if cp["turn"] == t)`. `score_longrun.py:846` then grades **all 48** checkpoints against that single per-turn answer.

Concrete T9 example:

```
T9 checkpoints:
  cp.TX-02.f01.d8  2001  What is VAL_B of doc-fact-01?
  cp.TX-02.f03.d2  2008  What is VAL_A of doc-fact-03?
checkpoint_expected(9): ('2001', 'What is VAL_B of doc-fact-01?')
T9 prompt checkpoint question: ['What is VAL_B of doc-fact-01?']
second question present: False
unreached_count 26
```

`cp.TX-02.f03.d2` is never asked at T9; it is graded against the T9 answer to the *other* question. The same collision repeats at every duplicate turn.

Unasked checkpoint IDs:

```
cp.TX-02.f03.d2, cp.TX-02.f04.d2, cp.TX-02.f05.d2, cp.TX-02.f05.d8,
cp.TX-02.f05.d20, cp.TX-02.f06.d2, cp.TX-02.f06.d8, cp.TX-02.f06.d20,
cp.TX-02.f07.d2, cp.TX-02.f07.d8, cp.TX-02.f07.d20, cp.TX-02.f08.d2,
cp.TX-02.f08.d8, cp.TX-02.f08.d20, cp.TX-02.f09.d2, cp.TX-02.f09.d8,
cp.TX-02.f09.d20, cp.TX-02.f10.d2, cp.TX-02.f10.d8, cp.TX-02.f10.d20,
cp.TX-02.f11.d2, cp.TX-02.f11.d8, cp.TX-02.f11.d20, cp.TX-02.f12.d2,
cp.TX-02.f12.d8, cp.TX-02.f12.d20
```

This is a fixture/test defect, not a checker-style typo: the new test counts 48 checkpoints but never asserts one checkpoint per turn, and `check_pointer_fixtures.py` has no unique-turn check. The existing v6 coverage test does assert `len(set(turns)) == 12`; TX-02 needs the equivalent.

### Additional checker gaps

- `check_pointer_fixtures.py` accepts `ANSWER: TEXT 2000` for an integer expected value; it compares only the parsed value, not the answer kind against the expected type. Observed:

```
'ANSWER: TEXT 2000' errs= [] count= 0
'ANSWER: NUM 2000' errs= [] count= 0
"ANSWER: TEXT '2000'" errs= ['checkpoint cp.TX-02.f01.d2 answer_form value "\'2000\'" != expected \'2000\''] count= 1
```

- It does not verify that `checkpoints[].question` is the question the runner actually injects.
- It does not check that `checkpoint_turns` is unique.

## 1. Counts

Measured from `turn - fact_introduction_turn`, not the declared `distance` field:

```
checkpoint_count 48
distance counts {2: 12, 8: 12, 20: 12, 32: 12}
distance measured mismatches []
```

Pass.

## 2. Uniqueness

```
distinct 48 of 48
collisions {}
```

Pass.

## 3. Leak

Searched every expected value against the system prompt, every `items[].body`, every turn `question`, and every OTHER turn's `tool_outputs[].body`. Zero hits.

```
leak count 0
```

Per value (all `leak=False`):

```
cp.TX-02.f01.d2 2000 False    cp.TX-02.f01.d8 2001 False    cp.TX-02.f01.d20 2002 False    cp.TX-02.f01.d32 2003 False
cp.TX-02.f02.d2 2004 False    cp.TX-02.f02.d8 2005 False    cp.TX-02.f02.d20 2006 False    cp.TX-02.f02.d32 2007 False
cp.TX-02.f03.d2 2008 False    cp.TX-02.f03.d8 2009 False    cp.TX-02.f03.d20 2010 False    cp.TX-02.f03.d32 2011 False
cp.TX-02.f04.d2 2012 False    cp.TX-02.f04.d8 2013 False    cp.TX-02.f04.d20 2014 False    cp.TX-02.f04.d32 2015 False
cp.TX-02.f05.d2 2016 False    cp.TX-02.f05.d8 2017 False    cp.TX-02.f05.d20 2018 False    cp.TX-02.f05.d32 2019 False
cp.TX-02.f06.d2 2020 False    cp.TX-02.f06.d8 2021 False    cp.TX-02.f06.d20 2022 False    cp.TX-02.f06.d32 2023 False
cp.TX-02.f07.d2 2024 False    cp.TX-02.f07.d8 2025 False    cp.TX-02.f07.d20 2026 False    cp.TX-02.f07.d32 2027 False
cp.TX-02.f08.d2 2028 False    cp.TX-02.f08.d8 2029 False    cp.TX-02.f08.d20 2030 False    cp.TX-02.f08.d32 2031 False
cp.TX-02.f09.d2 2032 False    cp.TX-02.f09.d8 2033 False    cp.TX-02.f09.d20 2034 False    cp.TX-02.f09.d32 2035 False
cp.TX-02.f10.d2 2036 False    cp.TX-02.f10.d8 2037 False    cp.TX-02.f10.d20 2038 False    cp.TX-02.f10.d32 2039 False
cp.TX-02.f11.d2 2040 False    cp.TX-02.f11.d8 2041 False    cp.TX-02.f11.d20 2042 False    cp.TX-02.f11.d32 2043 False
cp.TX-02.f12.d2 2044 False    cp.TX-02.f12.d8 2045 False    cp.TX-02.f12.d20 2046 False    cp.TX-02.f12.d32 2047 False
```

Pass as specified. Note: this does not cure the unprompted-checkpoint defect above.

## 4. Gradability

All 48 use `ANSWER: NUM <integer>` and parse to the expected integer. No spaces or line breaks in values.

```
gradability issues: 0
kind counts Counter({'NUM': 48})
unique answer_form prefixes Counter({'NUM': 48})
answer_form exact mismatches 0
expected values with whitespace []
```

Pass as specified, but 26 of these checkpoints are never prompted, so their gradability is theoretical until the duplicate-turn defect is fixed.

## 5. Masking reach (distance 32)

Checkpoint `cp.TX-02.f01.d32`: checkpoint turn 33, introduction turn 1, distance 32. `ArmCDState.mask_old_turns(33)` produced `masked_rows=10`. The actual `Planner("masking-no-fetch").build(33)` prompt estimated 1010 tokens, contained no `2003`, and contained exactly one `[MASKED doc-fact-01@r1]` marker. Rendering the introduction turn with the same marker construction used by the runner:

```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
[MASKED doc-fact-01@r1]
ANSWER (T1):
```

```
fact survives in rendered fragment? False
marker present? True
body present? False
```

Pass. The marker replaced the fact body; no unmasked `doc-fact-01` body remained.

## 6. Load

```
loaded task_id TX-02 turns 72 checkpoints 48
```

Pass. `load_fixture` accepted the fixture.

## 7. Red -> green (duplicate guard)

Mutated checkpoint 2 to duplicate checkpoint 1's expected value and answer form.

With the guard disabled:

```
WITH GUARD DISABLED (disabled={'duplicate_expected'}):
errs: []
accepted: True
```

Restored guard:

```
RESTORED GUARD (default):
errs: ["duplicate expected value '2000' (checkpoints 'cp.TX-02.f01.d2' and 'cp.TX-02.f01.d8')"]
rejected: True
```

Pass.

## 8. Budget reality check

Using fixture `bytes_per_token=4.0914` and the transcript-grow planner:

```
first checkpoint turn 3  -> 296 estimated tokens
last checkpoint turn 66  -> 2115 estimated tokens
max over turns 1..72     -> 2165 estimated tokens at T72
with short expected answers, max -> 1566 estimated tokens at T66
endpoint window          -> 32768 tokens
```

The 32768-token window at `http://192.168.2.168:8014` cannot bind for this fixture: the largest estimated prompt is 2165 tokens. The fixture's own `wall_tokens=4312` is also above that maximum.

Separate activation risk: if this fixture is intended to exercise all five arms, transcript-grow/compact never reach `wall_tokens=4312`, so their treatments do not activate. The test suite does not check this. This does not change the 32768 answer; it is a distinct concern.

Caveat: counts use the fixture's declared byte/token estimator and placeholder answers; real short answers reduce the maximum.

## 9. Requested pytest

Command:

```
/home/zer0null/research extractor/.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_tx02_distance.py -q
```

Literal output:

```
..........                                                               [100%]
10 passed in 0.04s
```

Pass, but the suite does not detect the 26 unprompted checkpoints.

## Could not reproduce

None. All nine requested checks were executed against the real fixture. No HTTP request was made, no service was restarted, and the fixture/checker/test files were not modified.
