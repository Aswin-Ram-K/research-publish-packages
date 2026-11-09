# CANARY-ERA-B-FIX

**Objective.** Make the pre-tranche canary able to judge the **tools-on (era B)** shape, then
re-run the full positive/negative matrix. Offline: zero requests.

**Why.** `CANARY-FALSE-POSITIVE` measured the canary blind on the very shape it must bless:
3 of 3 tools-on files `shape_unknown` at N=5, constant across N in {2,5,8,12}; only N=48 flipped
v4 (T45) and v5 (T29) to `shape_degenerate`. Era B rows carry `finish_reason` only — 0/144 turns
have `stop_reason` or `answer_turn` — so `shape_ok` was structurally unreachable.

**Hard bound.** 24 tool calls; journal first, handoff within 6 calls, verdict row before handoff.
**Write paths.** `experiments/ptr-engine/tools/tranche_canary.py`, `tests/test_tranche_canary.py`,
`docs/TRANCHE-CANARY.md`, `experiments/ptr-engine/measure/CANARY-ERA-B-FIX.json`,
`orchestration/units/CANARY-ERA-B-FIX.md`, `orchestration/handoffs/CANARY-ERA-B-FIX.json`,
`orchestration/journals/CANARY-ERA-B-FIX.jsonl`.
**Never edit:** `run_longrun.py`, `cell.py`, `GRID-SHAPE.json`, fixture, graders, analyser, row files,
published numbers. Never loosen the era A gate.

## What was changed (the reader, not the rule)

1. **Stop-signal precedence** — `("stop_reason", "finish_reason", "truncated", "completion_tokens==max_tokens")`,
   first present field wins, recorded in `stop_signal_source`.
2. **Answer contract per shape** — era A (rows carry `stop_reason`) consumes `parseable_answers`
   (unchanged); era B (wire fields only) consumes `answer_verified`. Both reported separately
   (`answer_verified`, `answer_verified_false`, `parseable_answers`).
3. **Tool-call storm** — `STORM_MIN_CALLS = 110` requested calls in one turn, measured as the
   midpoint of the observed gap (largest contained turn 101 vs storms 116/130) against
   `tools.max_calls_per_turn = 2`.
4. **Era A control untouched** — still `shape_degenerate` at T3, still `completion_ceiling`.

## Acceptance result

- Era A control at N=5: `shape_degenerate`, turn 3, `completion_ceiling` (storm does not fire: its
  turn rows carry `tool_calls: null`).
- Tools-on: `v6` `shape_ok` at N=12 and N=48; `v4` `shape_ok` at N=12 and `shape_degenerate` (T45) at
  N=48; `v5` `shape_unknown` at N=12 (`answer_verified_false` at T12) and `shape_degenerate` (T29) at N=48.
- **At N=5 all three tools-on files stay `shape_unknown`, and that is honest**: the first checkpoint is
  T12, so era B has no answer evidence inside a 5-turn window. Era B is gateable from N=12, not N=5.
- Tests: 13 existing green, 25 total; red→green demonstrated for each new guard (fallback, answer
  contract, storm) by reverting that guard alone.

## Artifacts

See `orchestration/handoffs/CANARY-ERA-B-FIX.json` and
`experiments/ptr-engine/measure/CANARY-ERA-B-FIX.json`.
