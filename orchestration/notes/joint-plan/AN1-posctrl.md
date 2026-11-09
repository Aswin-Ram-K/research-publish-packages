# AN1 — POSCTRL-LR01 positive-control diagnosis

## 1. Row schema inspection (step 1)

Rows: `experiments/ptr-engine/measure/rows-posctrl-2026-11-08.jsonl`, 48 rows, arm `masking-no-fetch`, task `LR-01`, rep 1, gen v4.

- **Rendered prompt**: NOT stored in any row field. Only `prompt_sha256` (sha256 of the prompt) and `prompt_tokens` (count) are present. Assistant text is in `content` (max 1275 chars). `cached_tokens` is null for all 48 rows (`cached_tokens_normalized=0`, `cached_reported=false`); `prompt_tokens` is the only token-count field.
- `content_sha256`, `request_sha256`, `fixture_sha256`, `run_manifest_sha256`, `harness_sha256` are hashes only.
- `is_checkpoint` is true on exactly 3 rows (turns 12, 24, 46); `answer_turn` true on the same 3; `answer_raw`/`answer_kind`/`answer_value` populated only there. `masked_rows`=0 and `masked_entry=[]` on all 48 rows. `tools_mode=off`, `tools_declared=false`.

**Reconstruction (deterministic, verified, no model calls):** `Planner.build(t)` from `run_longrun.py` + `checkpoint_prompt` for checkpoint turns, with `self.answers` replayed from row `content`, reproduces every row's `prompt_sha256` with 0 mismatches across 48/48 turns. Fixture used: `tasks-v4/runtime-v4/LR-01.v4.json` (sha256 matches row `fixture_sha256`). Prompts are therefore recoverable on disk deterministically; no prompt text was ever persisted.

## 2. Per-turn presence table (graded turns 12, 24, 46)

Presence = substring in the reconstructed prompt (verified hash match).

| token | T12 | T24 | T46 | turns present /48 |
|---|---|---|---|---|
| `PtrNotAReferenceError` | yes | yes | yes | 48/48 |
| `PTR_NOT_A_REFERENCE` | yes | yes | yes | 48/48 |
| `test_scope.py` | yes | yes | yes | 48/48 |
| `test_negative_controls.py` | yes | yes | yes | 48/48 |
| `exit 0` | **no** | **no** | **no** | 0/48 |
| `def test_` | yes | yes | yes | 48/48 |
| `ledger` | yes | yes | yes | 48/48 |

`exit 0` is absent from every prompt because it occurs only in the fixture's `acceptance.checks` regex (expected pattern), never in the working set or any turn body.

## 3. Fixture working set + masking

- Working set (`working_set_block`) contains: `PtrNotAReferenceError` (3), `PTR_NOT_A_REFERENCE` (1), `test_scope.py` (2), `test_negative_controls.py` (2), `def test_` (11), `ledger` (44). `exit 0`: 0. All present tokens are in the always-prepended working set, so they survive every turn regardless of masking.
- `WINDOW_TURNS=4` / `mask_old_turns`: because the fixture turns carry **no** `tool_outputs` (`tos=[]` for all 48 turns) and tools are off, `masked_turns` is empty at every graded turn; `masked_rows=0` on all rows. **Masking never engaged.** No turn carrying any token was masked at T12/T24/T46 (none were masked at all).
- Specific facts are derivable in-prompt: errors.py body lists 31 `Ptr*` classes (model answered 21); resolve.py body contains `DEFAULT_MAX_REFS = 64` and the `_refuse` body calling `ledger.record_refusal(scope=..., serialized_ref=text, code=error.code)`.

## 4. Per graded turn: on-contract?

| turn | on-contract? | answer (quoted ≤120 chars) | expected | verdict |
|---|---|---|---|---|
| T12 | yes | `ANSWER: NUM 64` | 64 | correct |
| T24 | yes | `ANSWER: NUM 21` | 31 | wrong value |
| T46 | yes | `ANSWER: CALL _refuse(ledger=ledger, scope_name=scope.name, text=presented, error=error)` | `ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)` | wrong (restated signature, not inner call) |

All 3 graded answers are syntactically on-contract (ANSWER: <kind> <value>). Only 1/3 is value-correct. Across all 48 turns, 45 contain "ANSWER: NOT-AN-ANSWER" (off-contract fallback); only the 3 checkpoint turns produced a contracted answer. Assistant content contains none of `PtrNotAReferenceError`/`PTR_NOT_A_REFERENCE`/`exit 0`/`def test_` and only 1 `ledger` across all 48 turns.

## 5. Verdict

**Both, compliance-side dominant.** 6 of 7 required tokens were present in every one of the 48 prompts (including all 3 graded turns) and the masking arm never masked anything, yet the model restated zero of them in its answers (0/48 for 4 tokens, 1/48 for `ledger`). The model had the facts and did not use them → compliance-side for `PtrNotAReferenceError`, `PTR_NOT_A_REFERENCE`, `test_scope.py`, `test_negative_controls.py`, `def test_`, `ledger`. Prompt-side for `exit 0` only: 0/48 prompts contained it (it lives only in the acceptance-check regex, never in the working set), so no model could have restated it. Counts: 1 prompt-side token, 6 compliance-side tokens.

## 6. Cheapest legitimate next step (proposal only — not executed)

The current run is not a valid masking positive control: `masked_rows=0` on all 48 rows because the fixture carries no tool outputs, so nothing was ever masked. Re-running with a larger window changes nothing. The cheapest legitimate control to isolate compliance is a **one-request-per-checkpoint diagnostic**: 3 requests, each presenting only the complete working set + one checkpoint question (no transcript history, no masking, tools off), to test whether the model answers when the facts are isolated. Cost = **3 requests** (a 1-request first probe at T12 costs 1 and suffices to confirm the hypothesis).
