# Unit card — GRADER-V3

**Purpose (one):** build one quality instrument that can pass a correct log and fail four
different wrong logs for four different reasons, and register its rule before running it.
Nothing else. No scoring of new live data, no repair of the old graders, no plan edits.

**Class:** automated session, board card, `workspace-write`. **No human is present.**
`ask_user_question` is never called. **Requests sent: 0** — no network, no endpoint, no model.

**Bound:** 24 tool calls. Kill condition: if the six controls do not land as specified after a
full pass, report what did land and which control is wrong (`partial`); never fabricate a green.

## Ordered method (order is the deliverable)

1. Read the real shapes first: row schema, the six fixtures, `checkpoints[]`, `acceptance.checks`,
   `repair`, and `tasks-v3/LR-01.v3.json`'s `answer_marker`. Confirmed the defect at
   `score_longrun.py:814` (`item.get("match", "exact")`) and that **no shipping fixture carries
   `answer_marker`** (only the v3 pilot fixture does).
2. **Wrote `longrun/GRADER-V3.md`** — the registered rule — before any code and before any
   control. Not edited afterwards, so its mtime stays earlier than all six control results.
3. Implemented `longrun/grade_v3.py` (stdlib only, deterministic, no judge).
4. Built six control logs under `longrun/controls/` **copy-only** from the `pointer-stable` arm
   of `measure/rows-longrun-c-2026-10-26.jsonl` (read-only), and graded all six against
   `tasks-v3/LR-01.v3.json` so the marker rule is exercised.
5. Applied it to the 192-row grid and to the ANSWER-marker pilot, writing two new
   `.grade-v3.json` files and **overwriting no existing verdict**.

## Result

All six controls land as registered: `pos-full` true (3/3, tokens_to_verified_success 13161);
`neg-one` `number_wrong:65`; `neg-marker` `refused_while_knowable`; `neg-truncated`
`truncated_without_value`; `neg-codeonly` `fenced_only`; `pos-exact-only` `marker_missing` ×3.
Grid re-scores 0/3 in all four arms — now with a named competing number per arm instead of a
comparator artefact, and the instrument is proven able to say yes.

## Two corrections made mid-pass (both recorded in the handoff)

- `has_anchor` used `\b`; Python treats `_` as a word char, so `record` never matched inside
  `record_refusal`. Fixed in the code to match the `_`-splitting the rule already specifies.
  The rule file was not touched.
- `neg-marker` needed the value to be *knowable*; the arm never states `31` as a standalone
  token before turn 24, so the control now plants the fact at turn 2 — the turn the fixture
  itself declares in `long_run.planted_at_turn`.

## Write paths (checked against concurrent units)

`longrun/GRADER-V3.md`, `longrun/grade_v3.py`, `longrun/controls/**`,
`measure/*.grade-v3.json` (two new files), `/tmp/build_controls.py`,
`orchestration/handoffs/GRADER-V3.json`, `orchestration/units/GRADER-V3.md`.

**Not written:** `score_longrun.py`, `grade_v2.py`, `run_longrun.py`, any fixture, any plan,
any existing row file. All three graders stay reproducible side by side.
