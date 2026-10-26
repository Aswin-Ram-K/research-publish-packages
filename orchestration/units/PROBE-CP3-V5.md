# PROBE-CP3-V5 — does a delivering fetch channel let pointer-stable answer CP3 at T46?

## Objective
One arm (`pointer-stable`, rep 1, 48 turns, `--tools read_file`) on fixture
`experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json`, after the
FETCH-CHANNEL-FIX (engine-relative path resolution + durable round counter). Measure the
per-turn fetch spend curve, quote the CP3 (T46) exchange, grade with `grade_v3.py`, and state
whether a real fetch channel makes the pointer arm more or less expensive per verified success.

## Hard bound
76 requests (48 turns + ≤24 fetch follow-ups + 4 slack). Kill the cell if a turn costs > 600 s
(enforced with `--timeout 600`). One arm, one rep; no fixture, check, marker-rule, `max_tokens`
or grader edits.

## Command actually run
```
python3 experiments/ptr-engine/longrun/run_longrun.py \
  --fixture experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json \
  --arms pointer-stable --reps 1 --tools read_file \
  --rows experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl \
  --run-id v5tools2-pointer-stable \
  --thinking off --max-tokens 4096 --timeout 600
```
(`--resume` appended after the harness restart described in the handoff.)

## Write paths
- `experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl` (new row file)
- `experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v3.json` (new grade)
- `experiments/ptr-engine/longrun/manifests/v5tools2-pointer-stable-pointer-stable-r1.json` (runner-written)
- `orchestration/units/PROBE-CP3-V5.md`, `orchestration/handoffs/PROBE-CP3-V5.json`

## Result (one line)
The channel delivers (`base="engine"`, real `_refuse` body at T1), but the arm spent all 24
rounds by **turn 3**, so every checkpoint read (T12, T24, T46) was refused
`fetch_budget_exhausted`: CP3 unanswerable, 0/3 checkpoints, 72 requests.
