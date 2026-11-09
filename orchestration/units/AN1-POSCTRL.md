# AN1-POSCTRL

**Purpose.** Decide whether POSCTRL-LR01's failure was prompt-side (facts never delivered) or compliance-side (facts in prompt, model did not restate). Zero model requests.

**Bound.** 48 rows, arm `masking-no-fetch`, LR-01 v4. Offline, `.venv/bin/python`. No subagents. Write paths only: this card, `orchestration/notes/joint-plan/AN1-posctrl.md`, `orchestration/handoffs/AN1-POSCTRL.json`.

**Method.**
1. Inspected row schema: no `prompt` field; only `prompt_sha256` + `prompt_tokens`; assistant text in `content`; `cached_tokens` null all 48.
2. Reconstructed prompts deterministically via `Planner.build(t)` + `checkpoint_prompt` with answers replayed from `content`. Verified 0/48 sha256 mismatches. No guessing.
3. Substring-tested 7 tokens in each prompt; summarised counts; checked working set; checked masking state (empty `masked_turns` all turns, `masked_rows=0` all rows).
4. Checked on-contract status + quoted answers for the 3 checkpoint turns (12, 24, 46).

**Findings.** 6/7 tokens present in all 48 prompts; `exit 0` in 0/48. Masking never engaged (no tool outputs in fixture). Graded answers all syntactically on-contract; 1/3 value-correct (T12=64), T24=21 vs 31, T46 restated signature not inner call. 45/48 turns emitted "ANSWER: NOT-AN-ANSWER".

**Verdict.** Both, compliance-side dominant: 6 tokens prompt-present-but-unrestated; 1 token (`exit 0`) prompt-side (never delivered).

**Next.** 3-request one-turn diagnostic (working set only + one checkpoint question per request). Not executed.
