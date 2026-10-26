# RUN-V4-GRID — first live quality run against an answerable v4 fixture

**Purpose.** Prove `grade_v3.py` can score a v4 log (6 controls), then run exactly two arms
(`transcript-grow`, `pointer-stable`) over `tasks-v4/runtime-v4/LR-01.v4.json`, 48 turns each,
and classify the checkpoint outcomes.

**Bound.** 96 requests (48 x 2 arms), soft cap 100, wall clock 90 min, 30 tool calls.
Endpoint `http://192.168.2.168:8012/v1`, model `occamy-1.0-NVFP4`, thinking off, max_tokens 4096.

**Write paths.** `experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.*`,
`experiments/ptr-engine/longrun/controls/v4/**`, `experiments/ptr-engine/longrun/manifests/v4-*`,
`/tmp/**`, own handoff and this card.

**Result.** Gate PASS (pos-full true 3/3; five negatives false with distinct reasons).
96 rows, 0 failed turns. Verdict **SPLIT**: pointer-stable answers CP1 ("ANSWER: 64");
both arms refuse CP2; CP3 is refused by transcript-grow and carries no marker line in
pointer-stable (unexecuted `<tool_call>` blob). 8 pointer-stable turns truncated at 4096.
Handoff: `orchestration/handoffs/RUN-V4-GRID.json`.
