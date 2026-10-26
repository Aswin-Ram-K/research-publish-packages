# RUN-REASONING-POLICY

**Status:** partial — smoke PASS, arm 12/48 turns (tool-call bound, not an error).

**Policy** (implemented in `experiments/ptr-engine/longrun/run_longrun.py`, applied per row):
1. `answer_source="content"` when the content channel carries text (clean).
2. `answer_source="reasoning-fallback"` when content is empty but the reasoning channel either
   completed (`finish_reason != "length"`) **or** literally contains the checkpoint `expected`
   value. Marked; usable for cache/latency; never mixed silently with clean rows.
3. `answer_source="none"` otherwise.
4. `failed_turn = finish_reason=="length" and the expected value absent` — an incomplete answer.
   `timing_usable = ttft_ms present and not failed_turn`; failed turns never enter a latency average.
5. `max_tokens=16384` (4× the 4096 cap that still truncated, ~4.5× the largest clean completion, 3,592).

**Evidence**
- Smoke, `runtime/LR-01.json`, 12 requests: 12 rows, `ttft_n=12`, answer_source content 12 /
  fallback 0 / none 0, truncated 1, failed 1 → **PASS**.
- Arm `transcript-grow`, 12 of 48 turns: `ttft_n=12`, truncated 6, failed_turns 6.
- Turn-12 checkpoint (`expected "64"`): **no answer** — 16,384-token repeated
  `<tool_call>open</think>` loop, `expected_present=false`, recorded as failed.
- Tokens/turn (server `completion_tokens`): mean 7,628.6, p95 16,384, max 16,384.
  Channel split (tiktoken estimate): mean 11,479.5, p95 29,453, max 32,550 — estimator over-counts
  degenerate markup ~2×; use `completion_tokens` for wall clock.
- Wall clock, 1,360 requests at 1 rep: **97.3 h mean – 237.6 h p95** (4.0–9.9 days);
  2,720 at 2 reps: 194.6–475.2 h (8.1–19.8 days).

**Reading:** raising `max_tokens` does not deliver 0 truncated: half the measured arm turns spent the
whole cap on a `<tool_call>` loop (the model is trying to call a tool that does not exist). Request
count is not binding; generation length and that degeneration are. Fix the degeneration before
Stage 2. Resume the arm at turn 13 with the same `--run-id`; rows 1–12 are on disk.
