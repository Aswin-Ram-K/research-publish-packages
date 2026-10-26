# Unit V2-RUNTIME — bounded-tier runtime fixtures

**Status:** done. **Bound:** 18 tool calls (used 11). **Zero inference requests, zero curl.**

## Purpose
`tasks-v2/LR-0{1..6}.v2.json` are authored in `consonance.fixture/1`, which `run_longrun.py`
refuses (`load_fixture` requires `consonance.longrun-fixture/1` + `N`, `wall_tokens`,
`bytes_per_token`, `system_prompt`, `items`). This unit builds the runtime counterpart under
`tasks-v2/runtime-v2/` without touching the v1 `fixtures/`/`runtime/` tier or the adapter/runner
/ scorer.

## Deliverable
`experiments/ptr-engine/longrun/adapt_v2.py` — imports `adapt_fixture.py` (pin loading, pointer
slice, digest verify, tiktoken bytes/token, `instruction`→`question`) and overrides only:
- `system_prompt` = `adapt_fixture.SYSTEM_PROMPT` + `\n\n` + `answer_budget.system_prompt_addition`
  (the only channel that reaches the request: `run_longrun.py:210` sends
  `fixture["system_prompt"]` verbatim as the system message);
- carry-through of `answer_budget`, `acceptance` (incl. `checks_structured`,
  `negative_constraints`), `checkpoints`, `class`/`objective`, `long_run`, `fixture_version`;
- N = `len(turns)`, asserted equal to `long_run.turns` (mismatch refuses);
- filename `LR-0N.v2.json`; `derived_from.path` relative to the longrun dir (cwd-independent bytes).

Required keys are refused loudly (exit 1, fixture + key named): `schema`, `task_id`, `sources`,
`turns`, `checkpoints`, `acceptance`, `answer_budget`, plus `acceptance.checks_structured`,
`acceptance.negative_constraints`, `answer_budget.system_prompt_addition`.

## Evidence
- `adapt_v2.py --all` → 6 files, all `budget_in_system_prompt=True`, checks_structured
  12/8/8/9/9/9, N 48/64/56/40/72/60. Second run → identical six sha256 (idempotent).
- `run_longrun.py --dry-run --thinking off --show-prompts` on LR-01 → **exit 0**,
  `would_send_total=192` (4 arms × N=48). Budget sentence present in all 12 printed preview
  bodies, inside `messages[0].content`.
- `score_longrun.py` zero-byte log → **exit 3**, `{"error": "run log is empty"}` (input error, no
  scorecard). Two answer-less rows → exit 1, `verified_success: false`,
  `unverifiable_required: ["fixture.digest"]` (missing run-start digest). Adding
  `{"fixture_sha256": <runtime sha>}` → `unverifiable_required: []`, tally `{pass: 11, fail: 12}`:
  **zero unverifiable task checks — the tier is decidable.**

## Findings / handoff
- `BUDGET_NOT_IN_PAYLOAD` does **not** apply: the runner does not rebuild the system prompt.
- `run_longrun.py` does not count answer words against `answer_budget`; the budget is carried in
  the fixture and instructed in the prompt, but enforcement must live in the scorer or a post-run
  pass. Named, not patched.

## Write paths
`longrun/adapt_v2.py`, `longrun/tasks-v2/runtime-v2/LR-0{1..6}.v2.json`,
`orchestration/handoffs/V2-RUNTIME.json`, `orchestration/units/V2-RUNTIME.md`.
