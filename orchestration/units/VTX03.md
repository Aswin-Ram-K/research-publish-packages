# VTX03 — audit of experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json

- **Status**: pass.
- **Target**: `experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json` (task_id TX-03, gen-7, N=100, 48 checkpoints).

## 1. Asked, not just graded (checkpoint_prompt / checkpoint_expected)

48 of 100 turns returned a question, each paired with its expected value:

| turn | expected | question |
|---:|---|---|
| 3 | 3000 | What is VAL_A of doc-fact-01? |
| 6 | 3001 | What is VAL_B of doc-fact-01? |
| 7 | 3002 | What is VAL_C of doc-fact-01? |
| 9 | 3003 | What is VAL_D of doc-fact-01? |
| 10 | 3100 | What is VAL_A of doc-fact-02? |
| 13 | 3101 | What is VAL_B of doc-fact-02? |
| 14 | 3102 | What is VAL_C of doc-fact-02? |
| 16 | 3103 | What is VAL_D of doc-fact-02? |
| 19 | 3200 | What is VAL_A of doc-fact-03? |
| 21 | 3004 | What is VAL_E of doc-fact-01? |
| 22 | 3201 | What is VAL_B of doc-fact-03? |
| 23 | 3202 | What is VAL_C of doc-fact-03? |
| 25 | 3203 | What is VAL_D of doc-fact-03? |
| 26 | 3300 | What is VAL_A of doc-fact-04? |
| 28 | 3104 | What is VAL_E of doc-fact-02? |
| 29 | 3301 | What is VAL_B of doc-fact-04? |
| 30 | 3302 | What is VAL_C of doc-fact-04? |
| 32 | 3303 | What is VAL_D of doc-fact-04? |
| 33 | 3005 | What is VAL_F of doc-fact-01? |
| 37 | 3204 | What is VAL_E of doc-fact-03? |
| 40 | 3105 | What is VAL_F of doc-fact-02? |
| 44 | 3304 | What is VAL_E of doc-fact-04? |
| 47 | 3400 | What is VAL_A of doc-fact-05? |
| 49 | 3205 | What is VAL_F of doc-fact-03? |
| 50 | 3401 | What is VAL_B of doc-fact-05? |
| 51 | 3402 | What is VAL_C of doc-fact-05? |
| 53 | 3403 | What is VAL_D of doc-fact-05? |
| 54 | 3500 | What is VAL_A of doc-fact-06? |
| 56 | 3305 | What is VAL_F of doc-fact-04? |
| 57 | 3501 | What is VAL_B of doc-fact-06? |
| 58 | 3502 | What is VAL_C of doc-fact-06? |
| 60 | 3503 | What is VAL_D of doc-fact-06? |
| 63 | 3600 | What is VAL_A of doc-fact-07? |
| 65 | 3404 | What is VAL_E of doc-fact-05? |
| 66 | 3601 | What is VAL_B of doc-fact-07? |
| 67 | 3602 | What is VAL_C of doc-fact-07? |
| 69 | 3603 | What is VAL_D of doc-fact-07? |
| 70 | 3700 | What is VAL_A of doc-fact-08? |
| 72 | 3504 | What is VAL_E of doc-fact-06? |
| 73 | 3701 | What is VAL_B of doc-fact-08? |
| 74 | 3702 | What is VAL_C of doc-fact-08? |
| 76 | 3703 | What is VAL_D of doc-fact-08? |
| 77 | 3405 | What is VAL_F of doc-fact-05? |
| 81 | 3604 | What is VAL_E of doc-fact-07? |
| 84 | 3505 | What is VAL_F of doc-fact-06? |
| 88 | 3704 | What is VAL_E of doc-fact-08? |
| 93 | 3605 | What is VAL_F of doc-fact-07? |
| 100 | 3705 | What is VAL_F of doc-fact-08? |

## 2. Structure

- 48 unique checkpoint turns (48 of 48).
- Counts per distance: {2:8, 5:8, 6:8, 8:8, 20:8, 32:8}.
- Distances measured from turn indices: 0 mismatches (`int(turn)-int(intro)==distance`).

## 3. Leak

- 48 expected values checked against system prompt, all turn questions, items[].body, and every other turn's tool_outputs[].body: 0 hits.

## 4. Window boundary (simulation, arm masking-no-fetch)

WINDOW_TURNS=4, cutoff=t-4. Representative fact doc-fact-01:

| distance | turn | masked_rows | body verbatim | marker |
|---:|---:|---:|---|---|
| 2 | 3 | 0 | True | n/a |
| 5 | 6 | 1 | False | [MASKED doc-fact-01@r1] |
| 6 | 7 | 1 | False | [MASKED doc-fact-01@r1] |
| 8 | 9 | 1 | False | [MASKED doc-fact-01@r1] |
| 20 | 21 | 3 | False | [MASKED doc-fact-01@r1] |
| 32 | 33 | 4 | False | [MASKED doc-fact-01@r1] |

Empirical boundary (smallest distance with body replaced by marker): **5**.

## 5. Extremes

- d=5 (turn 6, expected 3001): marker present, expected value absent from rendered prompt.
- d=32 (turn 33, expected 3005): marker present, expected value absent from rendered prompt.

## 6. Budget

- Loaded prompt-token estimate (bpt 4.0914): masking-no-fetch/bounded-context-fetch turn 3 = 92, turn 100 = 1404; transcript-grow turn 100 = 1595.
- wall_tokens = 4312. A 32768-token window does not bind (max observed 1595).

## 7. Tests

- `check_pointer_fixtures.py`: OK (4 outcomes, 48 checkpoints, N=100).
- `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_tx03_distance.py -q`: 15 passed in 0.05s.
- `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_tx01_contrast.py experiments/ptr-engine/longrun/tests/test_tx02_distance.py -q`: 20 passed in 0.07s.
