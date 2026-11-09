# UNIT AUDITMASK12

**Purpose.** Audit why `masking-no-fetch` scored 12/48 on TX-02 (r1/r2) when the same arm scored 0/12 on TX-01. Read-only; no HTTP; no edits to fixture, rows, runner, or scorer.

## Recomputation
Command:
```
/home/zer0null/research extractor/.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --fixture experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json --run experiments/ptr-engine/measure/rows-tx02-masking-r1.jsonl
```
Output: `checkpoint_accuracy 12/48`, `verified_success false`, exit code 1. r2 identical. Independent per-checkpoint recompute (`answer_of` + `match_answer`): r1/r2 d=2 12/12 pass, d=8 0/12, d=20 0/12, d=32 0/12.

## Per-bucket table
| Bucket | r1 | r2 |
|---|---:|---:|
| d=2 | 12/12 | 12/12 |
| d=8 | 0/12 | 0/12 |
| d=20 | 0/12 | 0/12 |
| d=32 | 0/12 | 0/12 |
| Total | 12/48 | 12/48 |

## Per-checkpoint leak test (12 correct, all d=2, r1)
All 12 have `masked_rows=0` in the row and the expected value present in the reconstructed prompt (rows store only `prompt_sha256`; prompt rebuilt via `Planner.build()` from fixture + recorded answers).

| Turn | Intro turn | masked_rows (row) | Value present in prompt | Leak vector |
|---:|---:|---:|---|---|
| 3 | 1 | 0 | yes | intro turn inside 4-turn window: body + prior answer |
| 4 | 2 | 0 | yes | intro turn inside 4-turn window: body + prior answer |
| 7 | 5 | 0 | yes | intro turn inside 4-turn window: body |
| 8 | 6 | 0 | yes | intro turn inside 4-turn window: body |
| 17 | 15 | 0 | yes | intro turn inside 4-turn window: body |
| 18 | 16 | 0 | yes | intro turn inside 4-turn window: body |
| 43 | 41 | 0 | yes | intro turn inside 4-turn window: body |
| 44 | 42 | 0 | yes | intro turn inside 4-turn window: body |
| 53 | 51 | 0 | yes | intro turn inside 4-turn window: body |
| 54 | 52 | 0 | yes | intro turn inside 4-turn window: body |
| 57 | 55 | 0 | yes | intro turn inside 4-turn window: body |
| 58 | 56 | 0 | yes | intro turn inside 4-turn window: body |

Representative fragment (turn 3):
```
QUESTION (T1): Work turn 1.
TOOL OUTPUTS:
TOOL_OUTPUT (doc-fact-01@1): # doc-fact-01
VAL_A = 2000
VAL_B = 2001
VAL_C = 2002
VAL_D = 2003

ANSWER (T1): ANSWER: NUM 2000
```
Row field `expected_present` is False on all 48 checkpoints (it only probes `reasoning_raw`), so it does not flag this leak.

## Masking rule (file:line)
- `experiments/ptr-engine/longrun/arm_cd.py:32` `WINDOW_TURNS = 4`
- `experiments/ptr-engine/longrun/arm_cd.py:166` `cutoff = int(t) - WINDOW_TURNS`
- `experiments/ptr-engine/longrun/arm_cd.py:170` `for i in range(1, cutoff + 1):` (only turns <= cutoff are candidates)
- `experiments/ptr-engine/longrun/arm_cd.py:207-210` a turn is added to `masked_turns` only when it carried `tool_outputs`
- `experiments/ptr-engine/longrun/run_longrun.py:1570-1574` current turn's tool outputs are rendered in full
- `experiments/ptr-engine/longrun/run_longrun.py:1563-1566` a masked turn with no tool outputs still emits its answer
- `experiments/ptr-engine/longrun/run_longrun.py:1558-1562` body is replaced by `[MASKED ...]` only for turns in `masked_turns`

## Verdict
(b) instrument leak. All 12 correct checkpoints are at distance 2, inside the 4-turn unmasked window, so the fact's tool-output body (and for turns 3-4 also the prior model answer) is still in the prompt; `masked_rows=0` at every one of them, so they fail the arm's own activation predicate (`masked_rows>0`) and are not masked-fact successes. The scorer counts them because `answer_of` matches the expected value, but they are unmasked-window reads, not recall of a masked fact. This is why TX-01 (single checkpoint at turn 20, outside the window) scored 0/12 while TX-02's d=2 bucket scores 12/12.
