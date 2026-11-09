# UNIT RUNNER-WALL-KEY

**Purpose.** Prove which wall key the runner reads (per-arm vs top-level) before 800
requests ride on it. Offline, zero requests. Triggered by `V-FIXTURE-V8`'s `next_unit_hint`
(F3): v8 declares `wall_tokens: 3838` *and* `wall_tokens_by_arm: {...: 10616}`; 3838 is
below v8's own first prompt (3848), so a fallback fires the wall at ~turn 2.

**Hard bound.** ≤22 tool calls, 0 requests. Used 19 calls, 0 requests.

**Write paths (exactly).**
`experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_wall_key.py`,
`experiments/ptr-engine/measure/RUNNER-WALL-KEY.json`, `docs/RUNNER-WALL-KEY.md`,
`orchestration/units/RUNNER-WALL-KEY.md`, `orchestration/handoffs/RUNNER-WALL-KEY.json`,
`orchestration/journals/RUNNER-WALL-KEY.jsonl`.

**Findings.**
1. Resolution order: per-arm (`run_longrun.py:1186-1195`) → top-level (`:1197`, legacy
   only) → no schema default on this path → no hard-coded token constant.
2. `cell.py` reads no token wall at all; it only handles the wall clock.
3. Two defects read the top-level key: the silent `by_arm.get(arm, fixture["wall_tokens"])`
   fallback, and the dry-run `build_manifest(cfg, fixture, ...)` at `:2826`, which froze
   `design_cap_tokens=3838` in `dryrun-LR-01-*-r1.json` for a cell built at 10616.
4. Fixed all four sites in `run_longrun.py`; red→green in `experiments/ptr-engine/longrun/tests/test_wall_key.py`.

**Not edited.** `tasks-v6/LR-01.v8.json` (audited). No fixture edits, no network.

**Recommendation.** Keep the top-level 3838 as a "below-first-prompt, do not use" marker
enforced by refusal; future fixtures should omit it (the loader now accepts by-arm-only).

**Status.** done. Verdict: PASS.
