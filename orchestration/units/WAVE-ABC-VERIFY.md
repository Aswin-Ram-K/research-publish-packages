# UNIT WAVE-ABC-VERIFY — independent verifier, three-card harness rebuild

Card: `9b52517a-13ba-4e04-9184-9f7de5710cbf`. Verifier, not author. Bound ≤34 tool calls, zero inference requests.
Targets verified: `HARNESS-FIX-CLIENT.json`, `ANSWER-CONTRACT.json`, `EVAL-STATS.json` — by re-running commands, not by reading prose.

## Result: overall `partial`

Reproduced: all four test counts (8/8, 26/26, 16/16, 8/8) and both `--red` runs; the answer contract's 11 hostile forms; the AST truth-follows-source mutation; the statistics refusals; the write-path audit; the v5 invariants.
Not reproduced / overstated: the TTFT fix is in `client.py` only — `run_longrun.py` never imports it, so the executed harness still runs the old tool-call-blind latch at `run_longrun.py:1084-1085`. The `--red` counter line prints a contradictory "0/26 assertions FAILED".

## Attack 1 — every ttft assignment and its guard

| path:line | assignment | guard |
|---|---|---|
| `experiments/ptr-engine/longrun/client.py:305` | `ttft = None` | function init in `collect_stream` |
| `client.py:320-321` | `ttft = clock() - t0` | `if kind is not None and ttft is None` — first delta carrying any member of `TOKEN_DELTA_KEYS = ("content","reasoning_content","tool_calls")` (`client.py:63`) |
| `client.py:330` | `wall = clock() - t0` | **not** ttft; reported separately (`wall_ms`) |
| `client.py:393` | `ttft = None` | init in `send_chat` |
| `client.py:410` | `ttft, first_token_kind = None, None` | `if not cfg.stream:` — a non-streamed turn is `unavailable`, never a wall-clock stand-in |
| `client.py:417` | `ttft = folded["ttft"]` | `else:` streamed path, value from `collect_stream` |
| `client.py:472-474` | `ttft_ms` / `ttft_source` | derived by `ttft is not None` |
| `experiments/ptr-engine/longrun/run_longrun.py:1054` | `ttft = None` | non-streamed branch |
| `run_longrun.py:1059` | `ttft = None` | streamed branch init |
| `run_longrun.py:1084-1085` | `ttft = time.perf_counter() - t0` | `if (piece_c or piece_r) and ttft is None` — the OLD latch, still the live path |
| `run_longrun.py:1133-1134,1300,1311,1324` | `ttft_s`/`ttft_ms`/`timing_usable` | pure projections of the above |

No `perf_counter` delta is assigned to ttft outside a first-token branch anywhere. "No wall-clock fallback" holds in both files.
**But** `grep -n "import client\|client.send_chat" run_longrun.py` returns nothing: the new latch is dead code for the harness. The tool-call-blind hypothesis is closed only in the module, not in the rows the harness produces.

## Attack 2 — hostile fake streams (`/tmp/wabc`, my own chunks)

| case | observed |
|---|---|
| first delta `tool_calls` | `ttft_ms=200.0`, `kind='tool_call'` |
| `content:""` then `content:"x"` | `ttft_ms=350.0` (latched at the second), `kind='content'` |
| usage-only + `[DONE]` via `send_chat` | `ttft_ms=None`, `ttft_source='unavailable'`, `first_token_kind=None`, `wall_ms=2500000.0` |
| `reasoning_content:"think"` | `ttft_ms=275.5`, `kind='reasoning'` |
| `tool_calls=[{id:"", function:{arguments:""}}]` | **counts**: `ttft_ms=333.0`, `kind='tool_call'` — `token_kind` tests list truthiness (`client.py:287`), not id/argument content |
| `tool_calls: []` | `ttft_ms=None` — an empty list is not a token |
| `request_body` stream | `stream_options={'include_usage': True}` (`client.py:127`) |

## Attack 3 — 11 contract forms against real fixture truth

| # | answer | verdict / reason |
|---|---|---|
| 1 | `ANSWER: NUM 64` | pass / num_equal |
| 2 | `ANSWER: NUM 64.` | pass / num_equal (64) |
| 3 | `ANSWER: NUM  064` | pass / num_equal (64) |
| 4 | `ANSWER: NUM 64 (resolve.py:39)` | pass / num_equal — citation dropped |
| 5 | `ANSWER: CALL ledger.record_refusal(code=code, scope=scope_name, serialized_ref=serialized_ref)` | **fail / kwarg_value_mismatch:code** — order is fine; the *values* (`code`, `serialized_ref`) are not the source texts (`error.code`, `text`) |
| 5b | same reordered, correct values | pass / call_equal, `kwargs_as_written=['code','scope','serialized_ref']` |
| 6 | `ANSWER: CALL ledger.add(...)` | fail / callee_mismatch |
| 7 | two ANSWER lines | fail / answer_not_contract, `answer_parse_error='multiple_answer_lines'` |
| 8 | `ANSWER: TEXT the answer is 64` | verdict **`text`** / text_not_auto_passed — never a pass |
| 9 | contract line + trailing sentence | pass / num_equal |
| 10 | bare `64`, no ANSWER line | fail / answer_not_contract, `no_answer_line` |
| 11 | `ANSWER: NUM 063` | fail / num_mismatch |

**Reordered-kwargs decision (author's, `grade_v5.py:374-376`):** order is a formatting rule, not a truth rule — kwargs are sorted (`_parse_call`, `grade_v5.py:117`) and `kwargs_as_written` is reported, not graded. Code agrees with the docstring; verified by 5b vs written-order both passing. The card's literal form 5 fails for a different reason (value text), which is strict by design.

## Attack 4 — truth follows the source

Copied `resolve.py` + `errors.py` to `/tmp/wabc/src`, set `DEFAULT_MAX_REFS = 99`, renamed `PtrError` → `BoomError`, pointed a fixture copy's `sources` at that tree.
- unchanged documented expectations → `derive_truth` raises `fixture_truth_mismatch: cp.0.t12 documents '64' but the AST derives 99` — the values are recomputed, not copied.
- with expectations updated → `cp.0.t12 expected=99` (`/tmp/wabc/src/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 99`), `cp.1.t24 expected=30` (`count(^Ptr\w*$) = 30`, was 31). **Values moved.** AST-derived claim holds.

## Attack 5 — statistics refuse

- `wilson_ci(0,3)` → `(0.0, 0.0, 0.5614970317550454)`; `wilson_ci(3,3)` → `(1.0, 0.4385029682449546, 1.0)`.
- `quantile_ci` n=48 → `InsufficientSamples: refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`; n=59 also refused (same tail-mass clause); n=60 accepted `(56.05, 51.2, 59.0, 60)`.
- `mcnemar_p(3,0)` = 0.25. `mcnemar_exact(b=3,c=0)` **refuses** with `RefusedTest` carrying `b=3, c=0, p=0.25`; `(2,1)` refuses with `p=1.0`; `(6,0)` returns `(6, 0, 0.03125)`. Design is coherent: pure p in `mcnemar_p`, refusal below 6 discordant pairs.
- null `ttft_ms` rows: `ttft_values([100, None, 200])` → `([100.0, 200.0], 1, 0)` — dropped and counted, never coerced to 0.
- pre-v5 rows (no `answer_kind`, no `cached_tokens`): `analyze()` returns a report, no raise.

## Attack 6 — write paths

`git status --porcelain` = 19 entries, all under the three cards' declared paths plus a concurrent `PUSH-TO-REMOTE`/`PUSH-TO-REMOTE-2` unit's own files. `git status --porcelain -- tasks-v4 tasks tasks-v2 tools/det_verify.py grade_v3.py grade_v4.py analyze_longrun.py measure/` is **empty**. No historical fixture, row, grade, or analyser touched. `run_longrun.py` diff = 96 insertions around tools-off/contract plumbing, no hunk near the ttft latch. No `unauthorised` write attributable to this wave.

## Attack 7 — invariants

- (a) v5 `system_prompt` (2376 chars) contains `ANSWER: NUM`, `ANSWER: CALL`, `ANSWER: NONE`, `ANSWER: TEXT`. `64`, `31`, `error.code`, `serialized_ref`, `scope_name`, `record_refusal`, `DEFAULT_MAX_REFS` are absent from system_prompt **and** every turn question. `Ptr` appears — it is the class-name pattern the question must name, not the answer.
- (b) `grade_v5.py:438` counts `passed` as `sum(1 for c in arm_cells if c["verdict"] == "pass")`; `TEXT` grades `verdict="text"` (`grade_v5.py:340-343`), so it can never be counted.
- (c) parse failures set `answer_parse_error` and grade `fail / answer_not_contract` (`grade_v5.py:336-337`); forms 7/10 above confirm, and `run_longrun.py:1349` persists the field into rows.

## Red/green reproduced

`test_answer_contract.py --red` prints 26 RED cases then `0/26 assertions FAILED` — a mislabelled counter (it claims zero failures while the next line says 26/26 fail); the red evidence itself is real. `test_grade_v5.py --red` → 8/16 FAILED, RED CONFIRMED.

## Assumptions (automated session)

- `/tmp` is per-invocation here, so every hostile test was written and run in the same shell call; no artefacts survive under `/tmp/wabc`.
- A file changed by another concurrently running card (`PUSH-TO-REMOTE*`) is reported as out-of-wave, not as this wave's unauthorised write.
