# WAVE-ABC-VERIFY — verifier result (measure log)

Independent re-check of `HARNESS-FIX-CLIENT`, `ANSWER-CONTRACT`, `EVAL-STATS`. Offline: zero inference requests.
Verdict: **partial** — all tests, the contract table, the source-mutation proof, the statistics refusals and the
write-path audit reproduce; the TTFT fix is not wired into the executed harness.

## 1. TTFT latch

`client.py` is clean: the only clock-to-ttft assignment is `client.py:321`, guarded by
`if kind is not None and ttft is None`; the non-streamed branch deliberately sets `None` (`client.py:410`);
`wall` at `client.py:330`/`:401` never becomes ttft. No wall-clock fallback.

`run_longrun.py` still runs its own inline loop and never imports `client`; its latch is
`run_longrun.py:1084-1085` — `if (piece_c or piece_r) and ttft is None` — blind to a first delta that carries
only `tool_calls`. So defect 1 is closed in a module that no measured row goes through.

Hostile streams, own chunks: tool_calls-first 200.0 ms `tool_call`; `""`→`"x"` latched at the second (350.0 ms);
usage+`[DONE]` only → `None`/`unavailable`; `reasoning_content` 275.5 ms `reasoning`;
`tool_calls=[{id:"", function:{arguments:""}}]` **counts** (list truthiness, `client.py:287`) at 333.0 ms;
`tool_calls: []` does not.

## 2. Answer contract — 11 forms

pass: `NUM 64`, `NUM 64.`, `NUM  064`, `NUM 64 (resolve.py:39)`, contract line + trailing prose,
reordered CALL **with source value texts**.
fail: reordered CALL with `code=code, serialized_ref=serialized_ref` (value mismatch, not order),
wrong callee `ledger.add`, two ANSWER lines, `NUM 063`.
never pass: `TEXT …` → verdict `text`.
Order is explicitly not graded (`grade_v5.py:374-376`, `_parse_call` sorts at `:117`); `kwargs_as_written` is reported.

## 3. Truth follows the source

`/tmp/wabc/src`: `DEFAULT_MAX_REFS = 99`, `PtrError`→`BoomError` → derived expectations 99 and 30 (was 31).
Leaving the documented strings alone makes `derive_truth` raise
`fixture_truth_mismatch: cp.0.t12 documents '64' but the AST derives 99` — no fixture copying.

## 4. Statistics refuse

- `wilson_ci(0,3)` = (0.0, 0.0, 0.561497); `wilson_ci(3,3)` = (1.0, 0.438503, 1.0).
- p95 refused at n=48 (ranks 43-48, p89.6-p100.0, n(1-q)=2.4<3) and at n=59; first accepted n=60.
- `mcnemar_p(3,0)` = 0.25; `mcnemar_exact` refuses b=3,c=0 (attaches p=0.25), refuses b=2,c=1 (p=1.0), returns
  (6,0,0.03125) at six discordant pairs.
- null `ttft_ms` dropped and counted `([100.0,200.0],1,0)` — never 0. Pre-v5 rows (no `answer_kind`,
  no `cached_tokens`) analyse without raising.

## 5. Contained writes

`git status --porcelain` = 19 entries: the three cards' declared paths + concurrent `PUSH-TO-REMOTE*` files.
Restricted status over `tasks-v4/`, `tasks/`, `tasks-v2/`, `det_verify.py`, `grade_v3.py`, `grade_v4.py`,
`analyze_longrun.py`, `measure/` is empty. `run_longrun.py` diff is 96 insertions of tools-off/contract plumbing,
no hunk near the TTFT latch. No unauthorised write.

## 6. Invariants

v5 `system_prompt` (2376 chars) carries the four ANSWER forms; `64`, `31`, `error.code`, `serialized_ref`,
`scope_name`, `record_refusal`, `DEFAULT_MAX_REFS` absent from everything the model sees. `TEXT` verdict is
`text`, and `grade_v5.py:438` counts only `pass`. Parse failures set `answer_parse_error` → `fail/answer_not_contract`.

Tests reproduced: 8/8, 26/26, 16/16, 8/8; `--red` grade 8/16 FAILED. `--red` contract prints 26 RED cases but
mislabels its counter as `0/26 assertions FAILED` — the one reporting defect found.
