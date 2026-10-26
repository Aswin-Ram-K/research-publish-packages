# HARNESS-MAP — the experiment harness as it actually runs

Unit `HARNESS-MAP`, 2026-10-26. **Read-only**: zero live requests, zero subagents, and nothing in
this repository was modified except this map and its two orchestration artefacts. Every cost below
carries its basis — a command that was run with its wall-clock, a row count from a row file, or a
count read from `orchestration/handoffs/*.json`. Where a number is inferred it is marked
`ESTIMATE` with its derivation.

**Why this document exists.** The project has been patching the quality judge in isolation.
`grade_v3` measures FN 30.8 % / FP 45.5 % and `grade_v4` FN 26.9 % / FP 50.0 % on 28 hand-written
probes (`experiments/ptr-engine/measure/GRADER-FITNESS.md`), and the repaired deterministic
verifier still fails on unseen prose forms (`orchestration/handoffs/V-DET-2.json`). Both failures
have the same root: **the harness never constrained the shape of the answer, and every judge is
being asked to recover meaning from free prose it cannot parse.** This map measures that harness so
the next change is argued against facts.

---

## 0. Inventory (measured)

| quantity | value | basis |
|---|---|---|
| unit handoffs on disk | **931** JSON files (`orchestration/handoffs/`) | `ls orchestration/handoffs/*.json \| wc -l` |
| unit cards on disk | **855** (`orchestration/units/`) | `ls orchestration/units/*.md \| wc -l` |
| experiment-chain handoffs (LR-01 / quality) | **52** | timeline sweep below, by unit-name match |
| ptr-engine row files | **13** | `experiments/ptr-engine/measure/rows-*.jsonl` |
| rows (= live requests) across those 13 files | **1095** | one row per request, counted per file |
| rows in the **longrun** chain only (13 runs) | **863** | 192+192+96+96+68+72+72+40+29+6 = 863 |
| fixture runtime generations for LR-01 | **4** + 2 tools variants = **16** runtime files | `fixtures/` (6) · `tasks-v2/runtime-v2/` (6) · `tasks-v3/runtime-v3/` (1) · `tasks-v4/runtime-v4/` (3) |

Per-row request cost is exact and mechanical: `run_longrun.py:1191 make_row()` writes one row per
HTTP request, and a tool fetch buys a second row (`fetch_followup`), so `wc -l rows*.jsonl` **is**
the request count. That is why every live-request figure in this document is an integer, not an
estimate.

---

## 1. Stage table

One row per stage that turns a question into a graded row. "Established by" names the handoff that
built it. Wall-clock is **measured** unless marked `ESTIMATE`.

| # | stage | owner (`path:line`) | driving command | inputs | outputs (real paths) | wall-clock | request cost | established by |
|---|---|---|---|---|---|---|---|---|
| 1 | **Authored fixture** | `experiments/ptr-engine/longrun/fixtures/LR-01.json` (data; validated by `run_longrun.py:123 load_fixture`) | none (authored JSON) | corpus bodies, 48 turns, 3 checkpoints, 1 repair, 12 acceptance entries | `fixtures/LR-0{1..6}.json` | n/a | 0 | `LONGRUN-TASK-SUITE.json` |
| 2 | **Prereg** | `experiments/ptr-engine/longrun/LONGRUN-PREREG.md`, `TASKS-V2-PREREG.md`, `ANCHOR-PREREG-V2.md`; checked by `experiments/ptr-engine/tools/anchor_prereg_check.py` | `python3 experiments/ptr-engine/tools/anchor_prereg_check.py` | predictions P1–P4, request budget | prereg markdown; `LONGRUN-PREREG.json:total_requests=500` | `ESTIMATE` < 1 s (pure file read; no timer taken) | 0 | `LONGRUN-PREREG.json`, `ANCHOR-PREREG.json` |
| 3 | **Fixture adaptation** (authoring → runtime) | `experiments/ptr-engine/longrun/adapt_v4.py:69 adapt_v4()`; imports `adapt_v3.py` → `adapt_fixture.py`; CLI `adapt_v4.py:88 main()` | `python3 experiments/ptr-engine/longrun/adapt_v4.py --all --out experiments/ptr-engine/longrun/tasks-v4/runtime-v4` | `fixtures/LR-01.json` (+ `fixture_version`, `answer_budget`, `answer_marker`) | `tasks-v4/runtime-v4/LR-01.v4.json` (+ `.tools.json`, `.tools2.json`); stamps `fixture_sha256` | **0.02 s** (measured invocation reaching argparse) — full write not timed to avoid touching the tree | 0 | `FIXTURE-ADAPTER.json`, `V3-FIXTURE.json` |
| 4 | **Pre-run gate** (manifest + dry run) | `run_longrun.py:859 build_manifest()`, `:938 write_manifest()`, `:1344 run_dry()` | `python3 experiments/ptr-engine/longrun/run_longrun.py --dry-run --fixture …/LR-01.v4.json --tools read_file --manifest-dir /tmp/hm-manifests` | adapted fixture, arms, reps, flags | `longrun/manifests/<run-id>.json` (**frozen manifest — no manifest, no result**); printed request bodies | **0.06 s** | **0** (prints `would_send_total=48`) | `LONGRUN-HARNESS.json` (`request_counts.would_send_total=242`) |
| 5 | **Runner core** | `run_longrun.py:1445 run_cell()`, `:709 Planner`, `:1026 send_chat()`, `:1191 make_row()`, `:1296 append_row()` | `python3 experiments/ptr-engine/longrun/run_longrun.py --fixture …/LR-01.v4.json --arms pointer-stable --reps 1 --tools read_file --rows experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl --run-id <id>` | manifest, messages, `--max-tokens 16384`, `--timeout 900` | `measure/rows-longrun-v6-tools.jsonl` (one row/request, fsynced) | **367.3 s** for 72 rows (v6); **316.1 s** for 68 rows (v4-tools); mean 5.1 s/row, p95 11.4 s, mean TTFT 213 ms | **1 row = 1 request**; 48 turn rows + 24 follow-up rows = 72 | `LONGRUN-HARNESS.json`, `RUN-STAGE1-LR01.json` |
| 6 | **Arm definitions** | `run_longrun.py:52 ARMS`, `:57 PREDICTIONS` | `--arms transcript-grow,transcript-compact,pointer-stable,lease-reopen` | — | arm labels stamped on every row/manifest | — | multiplies (5) by 4 | `LONGRUN-PREREG.json`, `ENGINE-DESIGN-SPACE.json` |
| 7 | **Tool channel** (serve-from-prompt, round caps, budget) | `run_longrun.py:507 serve_from_prompt()`, `:569 fetch_rounds()`, `:203 TOOL_CALLS_PER_TURN=2`, `:207 TOOL_FETCH_ROUNDS_PER_ARM=24`, `:214 TOOL_FETCH_ROUNDS_PER_TURN=3`, `:250 BudgetExhausted` | `--tools read_file [--fetch-rounds-per-turn N]` | model `<tool_call>` JSON in a turn's content; pinned working set | extra rows `kind="tool-followup"`; `<tool_result>` injected; `tool_calls[]` census on the turn row | folded into (5): ~1 extra round-trip per follow-up | **1 follow-up = 1 request**; measured 24 bought in V5 and V6 | `FETCH-CHANNEL.json`, `FETCH-CHANNEL-FIX.json`, `PROBE-CP3-FETCH.json`, `PROBE-CP3-V5.json`, `PROBE-CP3-V6.json` |
| 8 | **Row writing** | `run_longrun.py:1191 make_row()` / `:1296 append_row()`; `:1303 read_cell_rows()`, `:1322 resume_start()` | implicit in (5) | response payload, usage, manifest sha | `measure/rows-longrun-*.jsonl`; row keys include `fixture_sha256`, `run_manifest_sha256`, `content_sha256`, `latency_s`, `ttft_ms`, `tool_calls` | µs/row | 0 | `LONGRUN-HARNESS.json`, `RUN-INSTRUMENT-FIX.json` |
| 9 | **Grading R1 — `grade_v3`** | `experiments/ptr-engine/longrun/grade_v3.py:376 main()`, `:26 MARKER_RE = ^ANSWER:`, `:127 judge()`, `:216 judge_repair()`, `:256 judge_constraints()`, `:292 grade_arm()` | `python3 experiments/ptr-engine/longrun/grade_v3.py --rows …/rows-longrun-c-2026-10-26.jsonl --fixtures …/tasks-v4/runtime-v4 --out /tmp/hm-g3.json` | rows + fixture(s) | `<rows>.grade-v3.json` | **0.05 s** | **0** (offline) | `GRADER-V3.json`, `GRADER-V3.md` |
| 10 | **Grading R2 — `grade_v4`** | `experiments/ptr-engine/longrun/grade_v4.py:262 main()`, `:105 marker check`, `:236` `not_applicable` branch | same shape, `--out /tmp/hm-g4.json` | rows + fixtures that declare `answer_marker` | `<rows>.grade-v4.json` | **0.07 s** | 0 | `GRADE-V4-R2.json`, `R2.1-TIGHTEN.json` |
| 11 | **Deterministic verifier — `det_verify`** | `experiments/ptr-engine/tools/det_verify.py:528 verify_probe()`, `:869 build()`, `:69 DECIDABLE`, `:72 CHECK_ORDER`, `:566 CHECK_WHY`, `:481 check_numeric`, `:492 check_call`, `:218 negation_in` | `python3 experiments/ptr-engine/tools/det_verify.py --out /tmp/hm-det.json` | probes + AST of the pinned engine (`ptr_engine/resolve.py:39`, `errors.py:15-142`) | `measure/det-verify-matrix.json` default; `/tmp/hm-det.json` here | **0.05 s** | 0 | `DET-VERIFY.json`, `DET-VERIFY-FIX.json`, `V-DET.json` (fail), `V-DET-2.json` |
| 12 | **Matrix / coverage builder** | `det_verify.py:869 build()` → coverage computed **in code** from `CHECK_HANDLERS` over `CHECK_ORDER`, not asserted in prose | same command as (11) | `CHECK_ORDER` (13 entries), `grader-fitness.json` | `measure/det-verify-matrix.json` (`coverage_summary` 8/13) | 0.05 s (shared) | 0 | `DET-VERIFY.json`, `GRADE-FIT-CONTROL.json` |
| 13 | **Grader-fitness control** | `experiments/ptr-engine/tools/grader_fitness.py` (340 lines) | `python3 experiments/ptr-engine/tools/grader_fitness.py` | 28 probes × 4 fixtures, replaying each grader's real CLI | `measure/grader-fitness.json` (122 403 B) | `ESTIMATE` ≈ 4 × 0.07 s ≈ 0.3 s + probe I/O (not timed) | 0 | `GRADE-FIT-CONTROL.json` |
| 14 | **Cross-run re-grade / census** | `orchestration/handoffs/REGRADE-DET.json` procedure: import `det_verify.Truth()` + `verify_probe`, no logic re-implemented | (documented procedure, no script committed) | 9 row files + 4 grade grids + `LR-01.json` | `measure/regrade-det.json` (92 answer cells, 36 missing) | `ESTIMATE` < 5 s (arithmetic over 92 cells, no AST re-parse measured) | 0 | `REGRADE-DET.json` |
| 15 | **Handoff emission** | every unit writes `orchestration/handoffs/<UNIT>.json` — unit shape (7 keys) or verifier shape (`AGENTS.md` §Unit contract rule 5) | the unit's own `write` call; no shared writer exists | unit's own evidence | `orchestration/handoffs/<UNIT>.json` | per-unit, not measured | 0 | `LONGRUN-HARNESS.json` … all 931 |
| 16 | **Handoff guard** | `tests/test_orchestration_handoffs.py` (7-key unit contract + verifier shape, `_read_until_settled` mid-write handling) | `PYTHONPATH=src python3 -m pytest tests/test_orchestration_handoffs.py -q` | every `orchestration/handoffs/*.json` + frozen baselines in `state/logs/` | pass/fail; **measured 12 passed, 1 FAILED** | **3.08 s** | 0 | `U8.15`, `U8.18`, `U8.35` |
| 17 | **Verification step** (independent verdict) | a **different** unit re-runs the author's commands and writes a verdict handoff (`orchestration/handoffs/V-*.json`, `overall: pass\|fail\|partial`); recorded by hand in `orchestration/VERDICTS.md` (4010 lines) | the verifier's own commands, re-derived | author's handoff, disk state | `orchestration/handoffs/V-*.json` + `orchestration/VERDICTS.md` row | one full card per verification | 0 (verifiers are usually offline) | `V-ENGINE-P0.json`, `V-DET.json`, `V-DET-2.json` |
| 18 | **Session/card reconciler** | `tools/board/session_recon.py` | `python3 tools/board/session_recon.py` | board ledger, live sessions, handoff mtimes | recon report (card-subagent, settled-lag) | not run here (would touch board state) | 0 | `AGENTS.md` rule (b)(c) |

### Failure modes, per stage

| stage | model is slow | fetch is refused | fixture is stale | grade is unreproducible |
|---|---|---|---|---|
| runner (5) | `--timeout 900` per request; `latency_s` recorded; truncation flagged, not hidden (`finish_reason="length"` + `truncated:true`) | — | `load_fixture` rejects a stub/missing key with exit 2; **but a *wrong-but-valid* fixture is accepted** (see §3.10) | — |
| tool channel (7) | follow-up round trip doubles latency | **silent refusal, model not told why**: `turn_call_cap` (236 measured), `range_out_of_bounds` (2), `path_not_found` (10), `fetch_budget_exhausted` — the model just sees an error attribute and keeps going | pinned-item views are bound to the fixture, so a changed fixture invalidates `served_from="prompt"` | — |
| graders (9,10) | — | — | **does not verify lineage**: no grader reads the row's `fixture_sha256` (grep: no hit for `fixture_sha256` in `grade_v3.py`/`grade_v4.py`/`det_verify.py`) | grade files carry no input digest; `regrade_reproducible:true` in `PROBE-CP3-V6.json` was proven **by hand** (dict equality with `generated_at` stripped), not by the tool |
| det_verify (11) | — | — | pins `LR-01.json` by path only (`det_verify.py:57 FIXTURE`), so a regenerated fixture silently changes ground truth | same: no digest of the probes recorded in the matrix |
| handoff guard (16) | — | — | frozen baselines in `state/logs/` classify old gaps by shape | **guard is currently RED**: `test_no_new_contract_key_gaps` fails on `V2-RUNTIME.json`, `V3-FIXTURE.json`, `V3-PILOT.json` missing `overall`,`checks` |

---

## 2. The cell lifecycle as it actually is today

Counted from `orchestration/handoffs/*.json` mtimes plus the card ids they quote. The chain below is
the one that produced the current graded LR-01 cells — from `LONGRUN-PREREG` (2026-10-26 01:29) to
`REGRADE-DET` (09:21), i.e. **7 h 52 m of wall-clock and 40 card rounds**.

**Baseline: 40 card rounds · 863 live requests · 0 of 40 rounds produced both a graded and an
independently verified trustworthy cell** — the last verifier (`V-DET-2`) is `partial`.

| round | card | purpose | outcome | live requests |
|---:|---|---|---|---:|
| 1 | `QUALITY-ARM` (10-25 00:39) | build the quality arm | done | — |
| 2 | `V-QUALITY-ARM` (02:34) | verify it | partial | 0 |
| 3 | `QUALITY-INSTRUMENT-V2` (19:01) | second instrument | done | — |
| 4 | `RECORD-V3-APPEND` (21:09) | reconcile record | done | 0 |
| 5 | `QUALITY-TEXT` (23:27) | text-side quality metric | done | — |
| 6 | `LONGRUN-PREREG` (01:29) | predictions P1–P4, 500-request budget | done | 0 |
| 7 | `LONGRUN-TASK-SUITE` (01:32) | author fixtures LR-01..06 | done | 0 |
| 8 | `QUALITY-SCORER` (01:36) | scorer | done | 0 |
| 9 | `LONGRUN-HARNESS` (01:37) | the runner; dry-run `would_send_total=242` | done | 0 |
| 10 | `FIXTURE-ADAPTER` (01:46) | authored → runtime fixture | done | 0 |
| 11 | `ENGINE-DESIGN-SPACE` (01:49) | arm design | done | 0 |
| 12 | `SCORE-ADAPTER` (02:30) | scorer adapter | **partial** | 0 |
| 13 | `RUN-STAGE1-LR01` (02:40) | first live grid 4 arms × 48 | done, but **140/192 rows truncated** | **192** |
| 14 | `METRICS-V2` (03:58) | read stage 1 | done: `answer_source_absent_rows=192` | 0 |
| 15 | `ACCEPTANCE-AS-CHECKS` (04:01) | turn acceptance into checks | done (12 entries declared) | 0 |
| 16 | `DESIGN-V3` (04:07) | redesign: reasoning policy | done: `total_requests=204` | 0 |
| 17 | `RUN-C-PLAN` (04:15) | plan the C grid | done | 0 |
| 18 | `TASKS-V2-PREREG` (04:27) | v2 prereg (bounded answer tier) | done | 0 |
| 19 | `V2-RUNTIME` (04:34) | v2 runtime fixtures | done | 0 |
| 20 | `RUN-INSTRUMENT-FIX` (04:40) | fix truncation (`max_tokens` ladder) | **partial**; 1 row lost to a NameError crash | **42** |
| 21 | `RUN-REASONING-POLICY` (05:02) | reasoning-channel policy | **partial**; 2 requests sent with no row (1 harness restart re-sent T3) | **26** |
| 22 | `RUN-C-V2` (05:43) | the C grid | **partial** (1 truncated pointer-stable row, 14 lease-reopen) | **192** |
| 23 | `GRADE-RESCORE-V2` (05:47) | score C | done | 0 |
| 24 | `V3-FIXTURE` (05:52) | v3 fixture | done | 0 |
| 25 | `QUALITY-POSITIVE-CONTROL` (05:56) | check the metric can say yes | done | 0 |
| 26 | `V3-PILOT` (06:01) | 2-arm pilot on v3 | done | **96** |
| 27 | `GRADER-V3` (06:02) | grade the grid | done (0/3 everywhere) | 0 |
| 28 | `PLANT-REACHABILITY` (06:08) | can the plant fact reach a checkpoint? | done | 0 |
| 29 | `FIXTURE-REACHABILITY-FIX` (06:14) | **fixture revision** | done | 0 |
| 30 | `RUN-V4-GRID` (06:41) | v4 grid, 2 arms | done: 96 requests, 8 truncated | **96** |
| 31 | `FETCH-CHANNEL` (06:49) | add the `read_file` tool channel | done | 0 |
| 32 | `PROBE-CP3-FETCH` (07:06) | probe cp.2 at T46 | done: `fetch_budget_exhausted` 136 | **68** (+48 control) |
| 33 | `FETCH-CHANNEL-FIX` (07:16) | raise budget 8→24, add engine-root path base | done | 0 |
| 34 | `PROBE-CP3-V5` (07:26) | re-probe | done, but 24 rounds all spent in turn 3 → refused at T46 | **72** |
| 35 | `Q0-ANSWER-DEGENERACY` (08:11) | can any judge be gamed by a degenerate answer? | done | 0 |
| 36 | `PROBE-CP3-V6` (08:29) | serve-from-prompt + per-turn cap | done: 4 rounds left at T46 — **quality unchanged 1/3** | **72** |
| 37 | `ANCHOR-PREREG` (08:30) / 38 `V-ANCHOR-PREREG` (08:37) | anchor-answer prereg + verify | done / partial | 0 |
| 39 | `GRADE-V4-R2` (08:37) → `R2.1-TIGHTEN` (08:49) → `GRADE-FIT-CONTROL` (08:50) → `V-R2.1` (08:53) | R2 grader, tighten, then **grade the graders** | done / done / done / partial | 0 |
| 40 | `DET-VERIFY` (09:00) → `V-DET` (09:03, **fail**) → `DET-VERIFY-FIX` (09:13) → `V-DET-2` (09:20, **partial**) → `REGRADE-DET` (09:21) | deterministic verifier + independent audit + cross-run regrade | done / fail / done / partial / done | 0 |

**Rounds that cost live requests: 8 of 40** (13, 20, 21, 22, 26, 30, 32, 34, 36 → nine cards, 863
requests). **Rounds that cost zero live requests: 31 of 40.** So the dominant cost is *not* the
model — it is 31 cards of authoring, re-authoring, instrument repair and verification wrapped
around 9 measurement cards. Per unit of measurement: 863 requests / 40 cards ≈ 21.6 requests and one
full card of process per measurement card.

**Manual hand-steps per cell (the steps no tool performs):** (a) write the prereg prose; (b) author
the fixture JSON; (c) adapt it to runtime JSON; (d) run dry-run and eyeball the printed bodies;
(e) launch the run; (f) run each grader separately; (g) hand-assemble the cross-run table
(`REGRADE-DET`'s procedure is *prose in a handoff*, not a script); (h) write the handoff JSON by
hand; (i) get a **different** unit to re-run the commands; (j) record the verdict in the 4010-line
`orchestration/VERDICTS.md` by hand. **10 hand-steps per cell, of which exactly 3 (e, f, part of g)
are executed by a tool.**

---

## 3. Ranked inefficiencies

Ranked by **card rounds, then live requests**. "Smallest change" is the least work that removes the
cost, not the best possible design.

| # | inefficiency | costs (card rounds · live requests) | evidence | smallest change | risk |
|---:|---|---|---|---|---|
| 1 | **The answer shape is never constrained; the grader parses free prose.** `fixtures/LR-01.json` carries **no `system_prompt` key at all** (`d['system_prompt']` → `KeyError`), so the 192-row config-C grid and the 96-row v3/v4 grids that produced the central result ran with **no instruction about answer form**. Where the marker is specified it lives in prose inside a 1 500-character system prompt. | **13 rounds · 386 requests** (GRADER-V3, GRADE-V4-R2, R2.1-TIGHTEN, GRADE-FIT-CONTROL, V-R2.1, V-ANCHOR-PREREG, ANCHOR-PREREG, DET-VERIFY ×5, Q0) | `GRADER-FITNESS.md` §1 (FN 30.8 %→26.9 %, FP 45.5 %→50.0 %); measured marker census: **13 of 72** v6 rows carry an `ANSWER:` line (my count from `rows-longrun-v6-tools.jsonl`, agrees with `PROBE-CP3-V6.json:evidence.live.marker_lines`); v3 79/96 → v4-tools 14/68 → v5 6/72 | fix the answer string in the prompt (§4) and parse it instead of prose | a rigid contract could hide a real failure mode: a model that *knows* the answer but mis-formats now scores 0 where prose scored 1 — so the contract must be validated by a smoke run before it is grading truth |
| 2 | **Fixture re-authoring, four generations before any checkpoint could pass.** v1 → v2 (bounded tier) → v3 (reachability) → v4 (slice widened) + 2 tools variants = **16 runtime files, 4 generations**, and every generation invalidates prior rows. | **10 rounds · 96 wasted requests** (TASKS-V2-PREREG, V2-RUNTIME, V3-FIXTURE, PLANT-REACHABILITY, FIXTURE-REACHABILITY-FIX, ACCEPTANCE-AS-CHECKS, FIXTURE-ADAPTER, SCORE-ADAPTER, DESIGN-V3, V3-PILOT) | `PLANT-REACHABILITY.json`, `FIXTURE-REACHABILITY-FIX.json`, `V3-FIXTURE.json`; row files carry 4 distinct `fixture_sha256` prefixes (`72c3832d`, `0a07db1b`, `07abab0b`, `5a5f8c4b`, `a592a48f`, `5bf5f639`) | **fixture schema v5 with the answer contract and the acceptance checks as first-class machine fields**, versioned in one file per task, with a reachability check run by the dry-run (`anchor_prereg_check.py`) before any request is spent | a schema change re-labels historical rows; needs an explicit "v5 rows are not pooled with v4" rule |
| 3 | **Answerless acceptance checks: 36 of 92 checkpoint cells are `missing`, and 7 of the 13 declared checks are never even emitted.** | **4 rounds · 0 requests** but it destroys the value of 386+ requests already spent: every arm's `checkpoint_accuracy` is computed over 3 of 12 declared checks | `regrade-det.json:enumeration` = `answer_cells 92 / triples 56 / missing_cells 36`, `answerless_acceptance_ids` = acc.1..4, acc.cp1..3; my count on `rows-longrun-v6-tools.grade-v3.json`: 9 checks emitted of 13, **5 with a boolean decision, 4 emitted `pass:null`** | put the 12 acceptance checks **into the turn script as checkpoint turns** so each has an answer row, or delete them from the fixture | adding turns lengthens each cell (proportional request cost) |
| 4 | **The tool channel silently refuses what the model asks for, and the model is never told why.** | **5 rounds · 260 requests** (FETCH-CHANNEL, PROBE-CP3-FETCH 116, FETCH-CHANNEL-FIX, PROBE-CP3-V5 72, PROBE-CP3-V6 72) | `PROBE-CP3-V6.json:evidence.live.turn_tool_calls_census`: **371 tool_call entries, 236 `turn_call_cap`, 10 `path_not_found`, 2 `range_out_of_bounds`, 31 `followup_suppressed`** — i.e. **63 % of 371 calls were refused**, and V5's entire checkpoint read was refused `fetch_budget_exhausted` at T46 | cap per **call**, not per turn, and inject a refusal reason into the `<tool_result>` the model reads (`<tool_result error="turn_call_cap" hint="max 2 calls per turn; merge ranges"/>`) | a hint is extra prompt tokens per refusal; and a model that adapts changes the arm's behaviour mid-grid unless the hint text is frozen in the manifest |
| 5 | **Budget ledgers are counted in three incompatible currencies** (requests, fetch rounds, per-turn rounds), so a cell can be "in budget" and starved. | **3 rounds · 144 requests** | `run_longrun.py:207` `TOOL_FETCH_ROUNDS_PER_ARM=24` vs `:1479 budget = n_turns + digests` vs `:1484 budget += TOOL_FETCH_ROUNDS_PER_ARM`; `PROBE-CP3-V5.json` `budget=76, headroom=4`, but the *round* budget was gone at T46 | one ledger: `requests_sent` vs the card's declared request budget, with rounds derived from it (rounds = budget − turns) | a single ledger must be frozen per run or resumed cells re-open it (`:1499` already tries to prevent this) |
| 6 | **Mid-cell code-version mixing: the first 12 requests of V6 were graded by a harness that no longer exists.** | **0 extra rounds · 12 wasted requests** (6 % of V6) | `PROBE-CP3-V6.json:evidence.live.requests_breakdown`: "the cell ran 1-6 before a mid-run code correction (12 requests) then resumed 7-48 with `--resume`" | **stamp a harness digest on every row** (the row already carries `run_manifest_sha256`; the runner source is not hashed) and refuse `--resume` across a digest change | adds a hard failure where today it silently continues — a resumed cell will now sometimes refuse to resume, which is correct but costs a card to reconcile |
| 7 | **No grader checks line-of-descent, so re-grading under the wrong fixture is silently accepted.** | **2 rounds · 0 requests**, and it can invalidate any request ever spent | measured: `grep fixture_sha256 grade_v3.py grade_v4.py det_verify.py` → **no hit**; I ran `grade_v3 --rows rows-longrun-c-2026-10-26.jsonl --fixtures tasks-v4/runtime-v4` and got a clean `0/3 marker_missing` for all four arms instead of a lineage error | one assertion in `grade_arm`/`build`: `rows[0].fixture_sha256` must equal `sha256(fixture)` — exit 4 otherwise | none material; it turns a silent wrong number into an error |
| 8 | **Handoff stubs strand on restart; rows are lost at the boundary.** | **2 rounds · 44 requests** (RUN-INSTRUMENT-FIX 42 with 1 lost row; RUN-REASONING-POLICY 26 with **2 requests sent and no row**) | `RUN-REASONING-POLICY.json:evidence.requests_sent_without_row=2`, `lost_requests_reason` "1 harness restart during the smoke (T3 of transcript-grow re-sent), 1 deliberate stop with T13 in flight"; `RUN-INSTRUMENT-FIX.json` `nameerror_crash_lost_row=1` | write a **PRE-REQUEST intent row** (the pattern `measure/run_cells.py:10` already documents and uses) so a kill can never lose the request/incur an orphan | doubles row count for a moment; needs a reconciler that marks unmatched intents |
| 9 | **The acceptance gate is undecidable by construction for 5 of 13 checks, so the "verified" flag cannot mean what it says.** | **2 rounds · 0 requests** | `det_verify.py:566 CHECK_WHY` (8 decidable) vs `UNDECIDABLE_WHY`: acc.2 (execution claim), acc.3 (runtime count), acc.n2b (edit provenance — the exact check that failed lexically), acc.n3b..e (no_write over 4 paths), repair.t30 (dialogue commitment). `regrade-det.json:limits[0]` excludes repair.t30 from every accuracy, so accuracies are `/3` | split the gate: **answer-decidable** checks graded from text, **artefact-decidable** checks graded from a hash/log sidecar the runner writes | the runner must record provenance (writes, test exits) — a real feature, not a rename |
| 10 | **The runner's own verification guard is red and not runnable out of the box.** | **1 round · 0 requests**, but it defeats stage 17 | measured: `python3 -m pytest tests/test_orchestration_handoffs.py` → `ModuleNotFoundError: No module named 'resextract'` (needs `PYTHONPATH=src`); with it: **12 passed, 1 failed** — `test_no_new_contract_key_gaps` names `V2-RUNTIME.json`, `V3-FIXTURE.json`, `V3-PILOT.json` missing `overall`,`checks` | make the PYTHONPATH part of the test invocation (a `conftest.py` path insert or `pyproject` test config), then repair the three verifier-shape handoffs | none; a red guard is the state that lets the next gap in |
| 11 | **Reasoning-channel spend dominates wall-clock and truncates at the cap.** | **3 rounds · 68 requests** (DESIGN-V3, RUN-INSTRUMENT-FIX, RUN-REASONING-POLICY) | measured from rows: `rows-longrun-2026-10-26-policy.jsonl` = **13 309 s of request wall-clock for 40 rows (mean 332.7 s, p95 614.8 s)** vs the same grid with reasoning off `rows-longrun-c` = 3 836 s for 192 rows (mean 20.0 s). `max_tokens` ladder 128 → 1024 → 4096 → 16384 (`--max-tokens` help text) | pin the thinking flag **on** only for reasoning arms and record `thinking` per row (already stamped), never pool | arm comparability: a thinking-on cell is not the same instrument as thinking-off |
| 12 | **Every grade is recomputed by a third tool; the three disagree and none is authoritative.** | **4 rounds · 0 requests** (DET-VERIFY, V-DET, DET-VERIFY-FIX, V-DET-2) | headline from `regrade-det.json`: on `rows-longrun-v6-tools.jsonl` pointer-stable, **det_verify 2/3, grade_v3 1/3, grade_v4 2/3**; on config-C **det_verify 1/3 vs both graders 0/3** | declare `det_verify` the **primary** where it is decidable (8/13), and make v3/v4 report only the undecidable remainder — one headline number per cell | loses the v3/v4 history as a comparable series; needs the old files kept as dated observations |
| 13 | **Cross-run regrade is a hand-written procedure, not a command.** | **1 round · 0 requests**, but it is the only path from 9 row files to one table | `REGRADE-DET.json:i` — "instrument imported and called via `det_verify.verify_probe`; no matching logic re-implemented" — the loop lives in prose, and `regrade-det.json:generated_by` names no script | commit it as `experiments/ptr-engine/tools/regrade.py --runs <glob> --out …` | none; it is transcription of a procedure that already ran |
| 14 | **Re-authoring the prereg prose per generation** (`LONGRUN-PREREG.md`, `TASKS-V2-PREREG.md`, `ANCHOR-PREREG-V2.md`, plus errata in `ANCHOR-PREREG-V2-ERRATA.md`). | **4 rounds · 0 requests** | four prereg documents, one already needing an errata file; `LONGRUN-PREREG.json:total_requests=500` set against a `would_send_total` of 242 then re-planned at 204 (`DESIGN-V3.json`) | **machine prereg**: predictions and budgets as JSON next to the fixture, checked by `anchor_prereg_check.py` in the dry-run | prose preregs carry reasoning a JSON field loses; keep the prose as a comment field |

Ranking rationale: #1 and #2 are ranked above the request-heavy #4 because they cost **23 card rounds
between them** and make every one of the 863 requests un-interpretable; a request is only worth what
the grader can read out of it.

---

## 4. Where the answer format is decided — and what a machine-checkable contract would be

### 4.1 Where it is decided today (and where it is not)

| location | what it does | verdict |
|---|---|---|
| `experiments/ptr-engine/longrun/fixtures/LR-01.json` | **contains no `system_prompt` key** (verified: `KeyError: 'system_prompt'`) | **nothing is decided here** |
| `experiments/ptr-engine/longrun/run_longrun.py:731` | `return [{"role": "system", "content": self.fixture["system_prompt"]}, …]` — the system prompt is *the fixture's*, passed through verbatim | the runner constrains **nothing** |
| `experiments/ptr-engine/longrun/run_longrun.py:176 turn_user()` / `:184 turn_block()` | writes the *history* as `ANSWER (T{t}): {answer}` — a different shape from the one graded | **the harness teaches a shape it does not accept** |
| `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json:answer_marker` | `{"line_regex": "^ANSWER:[ ]*\\S.*$", "required": true}` — a declaration | decided here, but only for fixtures that declare it |
| the same file's `system_prompt` (composed by `adapt_v4.py:69 adapt_v4()`) | one prose sentence: "End every answer with a final line: **ANSWER: <the value, or NOT-AN-ANSWER>**. The value must appear in that line, never only inside a pasted code block." | **this sentence is the only place the model is told anything** |
| `experiments/ptr-engine/longrun/grade_v3.py:26` | `MARKER_RE = re.compile(r"^ANSWER:\s*\S.*$")` | enforced **post hoc**, on free prose |
| `experiments/ptr-engine/longrun/grade_v3.py:73 number_in()` | rejects `"ANSWER: 64."` because of the full stop | an accident of the parse, not a spec |
| `experiments/ptr-engine/tools/det_verify.py:86 answer_segment()`, `:132 answer_slot_end()`, `:149 asserted_number()`, `:218 negation_in()` | three hand-written prose readers that must guess where the claim ends | three independent re-derivations of the same ambiguity |

**Consequence, measured:** the marker appears in **79/96** rows on the v3 fixture, **14/68** once the
tool channel is on (`v4-tools`), **6/72** in V5 and **13/72** in V6. Turning the tool channel on
**destroys format compliance from 82 % to 18 %** — because format compliance was never a contract,
only a sentence the model could drop when it had a file to read.

### 4.2 The contract a later card should impose

One line per turn, no prose, fixed token order, `key=value` only. Two forms:

```
ANSWER: NUM <integer>                      # numeric checkpoints, no unit, no period, no trailing prose
ANSWER: CALL <callee>(k1=v1, k2=v2, ...)   # call-shape checkpoints, keys in fixture order
ANSWER: NONE                               # the model cannot establish it (an explicit abstain)
```

Rules, all machine-checkable with one regex each and no semantics:

1. exactly one line, matched by `^ANSWER: (NUM \S+|CALL \S+\(.*\)|NONE)$`, terminating the turn;
2. the line is the **last** non-empty line (today's `last_nonempty_line()` already assumes this);
3. for `CALL`, the callee is the dotted name and the keys appear in the fixture's declared order —
   the grader compares the ordered token list, never a substring;
4. the key order and the expected callee are **in the fixture**, not in the grader;
5. any answer without a valid contract line is `contract_violation` (a distinct reason, not
   `marker_missing`), and is retried **once** with a one-line format reminder appended to the same
   conversation — one extra request, only on violation, capped at one per cell.

### 4.3 What it costs in completion tokens

Basis: measured `completion_tokens` over `rows-longrun-v6-tools.jsonl` — **12 615 tokens / 72 rows =
175.2 tokens per row**. A minimal `ANSWER: NUM 64` line is 4 tokens; `ANSWER: CALL
ledger.record_refusal(scope=..., serialized_ref=..., code=...)` is `ESTIMATE` 12–16 tokens
(tokenised shape, not measured). Against today's compliance rate, the contract adds
**4–16 completion tokens per turn — 2–9 % of the measured 175.2-token mean** — and removes the
re-ask entirely for the 82 % of turns that already comply. The one-retry-on-violation path costs at
most 1 extra request per cell (measured baseline 72 → 73 requests, +1.4 %). It *saves* tokens
wherever a model today writes a 150-word preamble to hedge an answer it could state in 8 tokens:
the fixture already budgets 150/400 words, and the v4 system prompt explicitly asks for "the value
alone", so the ceiling is not new spend, it is a ceiling the harness stops having to trust.

### 4.4 Verifier failure classes it removes

| class | evidence it exists | removed by |
|---|---|---|
| `marker_missing` on turn answers (59/72 v6 rows) | my census; `grade_v3.py:142`,`:182`; cp.1.t24 `FAIL marker_missing` | rule 1 + rule 5 retry |
| numeral-present-but-value-wrong FP (`ANSWER: 64 is wrong; the default is 32 refs.` accepted) | `GRADER-FITNESS.md` §3 cp.0.t12 | `NUM <int>` slot: one integer, no surrounding text to scan |
| trailing-period FN (`ANSWER: 64.` rejected) | `GRADER-FITNESS.md` §3 cp.0.t12 | rule 1 forbids the period; the regex is anchored |
| negation FP (`ANSWER: do not call ledger.record_refusal…` accepted) | `GRADER-FITNESS.md` §3 cp.2.t46 | `CALL …` has no negation slot — a denial must be `NONE` |
| ordering clause undecidable (`before re-raising`) | `regrade-det.json:limits[1]` | an explicit `order=` key in the order list |
| lexical-evasion FP/denial FN (`trimmed` vs `never deleted`) | `GRADER-FITNESS.md` §3 acc.n2b | **not** removed by text — belongs to the artefact tier (#9); the contract forces the model to *declare* `ANSWER: NUM 0` distinct tests removed, which is checkable against the provenance sidecar |
| `repair.t30` undecidable (dialogue commitment) | `regrade-det.json:limits[0]` | `ANSWER: CALL restore_guard(...)` makes the commitment a token the grader can compare — decidable as text, if the fixture declares the expected call |

### 4.5 The diff a later card would make

- `experiments/ptr-engine/longrun/fixtures/*` — add `answer_contract: {form: "num"|"call", keys: [...], callee: "…"}` per checkpoint;
- `experiments/ptr-engine/longrun/adapt_v4.py:69` — replace the prose sentence with one generated line: `End every answer with exactly one line: ANSWER: <form>` (the form comes from the checkpoint, not from prose);
- `run_longrun.py` — add `--require-contract`, freeze it in the manifest, stamp `contract_checked: true` on each row, and implement the single retry;
- `grade_v3.py:26` — `MARKER_RE` → `CONTRACT_RE`; emit `contract_violation` instead of `marker_missing`;
- `det_verify.py:86-160` — collapse `answer_segment`/`answer_slot_end`/`asserted_number` into a contract parse; keep the prose readers only for legacy row files;
- `fixtures/LR-01.json` — add `system_prompt` (today it has none, so config-C was instructed by nothing).

**Not implemented here.** This card specifies; it does not change the harness.

---

## 5. The target pipeline

Goal: **one command per cell**, from prereg to graded-and-verified, with each command's guarantee
stated and the sections-2 rounds it collapses named.

| # | command | guarantees | replaces (rounds from §2) |
|---:|---|---|---|
| 1 | `python3 experiments/ptr-engine/tools/cell.py prereg --task LR-01 --predictions predictions.json --budget 96` | a machine-readable prereg exists, records the predicted direction, and the request budget is fixed **before** any row; refuses to overwrite a prereg that already has rows | rounds 6, 18, 37, 14 (4 cards, 0 requests) |
| 2 | `python3 experiments/ptr-engine/tools/cell.py author --task LR-01 --schema v5` | one fixture file carrying turns, checkpoints, **answer contract**, and acceptance checks as machine fields; a reachability check proves every checkpoint fact is stated in a turn before any request | rounds 7, 10, 15, 19, 24, 28, 29 (7 cards) |
| 3 | `python3 experiments/ptr-engine/tools/cell.py check --task LR-01 --arm pointer-stable` | dry-run manifest + pairwise-unique request bodies + reachability + contract presence, **zero requests**; exit 2 on any missing precondition | rounds 9, 17, 20, 33 (4 cards) |
| 4 | `python3 experiments/ptr-engine/tools/cell.py run --task LR-01 --arm pointer-stable --tools read_file --budget 96` | a cell runs under one frozen harness digest, writes a pre-request intent row per request (no orphan requests), stamps `fixture_sha256` + `harness_sha256` on every row, and refuses `--resume` across a digest change | rounds 13, 20, 21, 22, 26, 30 (6 cards, 617 requests) |
| 5 | `python3 experiments/ptr-engine/tools/cell.py grade --cell cells/LR-01/pointer-stable --primary det_verify` | one headline, from the decidable instrument; v3/v4 emitted as secondary with lineage asserted; `contract_violation` reported separately from wrong answers; refuses a fixture whose sha does not match the rows | rounds 23, 27, 36, 39 (4 cards + the v3/v4/R2 chain) |
| 6 | `python3 experiments/ptr-engine/tools/cell.py verify --cell cells/LR-01/pointer-stable --red-green <guard>` | a red→green proof on one guard, the author's commands re-run in a clean shell (`env -i`), and a **verdict handoff written by the tool**, so the verifier cannot fail to persist | round 40 (5 cards) + the hand-written `VERDICTS.md` row |
| 7 | `python3 experiments/ptr-engine/tools/regrade.py --runs 'experiments/ptr-engine/measure/rows-*.jsonl' --out measure/regrade.json` | the cross-run table is a command, reproducible byte-for-byte from the row files | rounds 23, 38, 40's regrade (3 cards) |

**Collapse:** today 40 rounds → **6 commands + 1 verifier card per cell** (the verifier must remain a
separate unit; `AGENTS.md` "Verification independence" forbids self-approval). The 31 zero-request
cards collapse to commands 1–3 and 7; the 9 measurement cards collapse to commands 4–5; only the
independent verdict stays a card, and it shrinks because command 6 hands it the artefact.

**What must stay a card even then:** the phase-gate call, and the independent verifier — both are
process requirements, not tooling gaps.

---

## 6. What I could not determine

1. **Live wall-clock of a *current* run.** Every timing in §1 for stages 5–7 is derived from
   `latency_s` already recorded in the row files (v6: 367.3 s / 72 rows). I did not send a request,
   so I cannot say what a run costs against the endpoint **today**; the endpoint's state is known
   only through dated observations in earlier handoffs and the row timestamps.
2. **The card-round count is a lower bound.** I counted `orchestration/handoffs/*.json` by mtime and
   unit name. A card that produced **no handoff** is invisible to that method — and `AGENTS.md`
   records that exact failure ("three wasted units … its verdict could not be persisted at all").
   `ESTIMATE`: the true count is 40 + (unpersisted cards), and I cannot bound how many there were.
3. **Whether `V-DET-2`'s `partial` blocks the cell.** The last verifier is `partial`; I read its
   status from the directory, not its body. I can therefore state "no round produced a
   graded-and-verified trustworthy cell" but **not** which specific checks are still open.
4. **`grader_fitness.py` and `run_cells.py` wall-clock.** Both were listed but not timed (the first
   writes `grader-fitness.json` in the repo, the second is the miss-law driver outside this cell).
   Marked `ESTIMATE` in §1; the graders and `det_verify` *were* timed.
5. **`adapt_v4.py` full write time.** The CLI rejects an argumentless invocation, and a real run
   writes into `tasks-v4/runtime-v4/` — a repository path this card may not touch. Measured only the
   0.02 s to reach argparse.
6. **The `--smoke` path's real cost.** The help text says 12 requests; I did not run it (it is live).
   The 12 is quoted from `run_longrun.py:1795`, not measured here.
7. **`session_recon.py` was not run** (it reads board state and writes a report); its cost and its
   current verdicts are unknown to this map.
8. **Why marker compliance falls from 82 % (tools off) to 18 % (tools on)** is measured, not
   explained. I can name the census but not the mechanism; a probe would have to compare turn
   lengths and tool-call counts per turn, and I did not spend requests on it.
9. **No claim about the current state of the Occamy endpoint** (`192.168.2.168:8012`): this card
   sent zero requests, so anything I wrote about it would be a stale quotation.

---

## Appendix — measurements actually taken (reproducible)

```
ls orchestration/handoffs/*.json | wc -l                  -> 931
ls orchestration/units/*.md     | wc -l                  -> 855
wc -l experiments/ptr-engine/measure/rows-*.jsonl        -> 1095 rows over 13 files
/usr/bin/time python3 experiments/ptr-engine/longrun/run_longrun.py --dry-run \
    --fixture …/tasks-v4/runtime-v4/LR-01.v4.json --tools read_file \
    --manifest-dir /tmp/hm-manifests                     -> WALL 0.06 s, 0 requests
/usr/bin/time python3 experiments/ptr-engine/longrun/grade_v3.py \
    --rows …/rows-longrun-c-2026-10-26.jsonl --fixtures …/tasks-v4/runtime-v4 \
    --out /tmp/hm-g3.json                                -> WALL 0.05 s
/usr/bin/time python3 experiments/ptr-engine/longrun/grade_v4.py … --out /tmp/hm-g4.json
                                                         -> WALL 0.07 s
/usr/bin/time python3 experiments/ptr-engine/tools/det_verify.py --out /tmp/hm-det.json
                                                         -> WALL 0.05 s
PYTHONPATH=src python3 -m pytest tests/test_orchestration_handoffs.py -q
                                                         -> WALL 3.08 s, 12 passed 1 failed
python3 -m pytest tests/test_orchestration_handoffs.py -q -> ModuleNotFoundError: resextract
row-derived timings (sum of latency_s): rows-longrun-v6-tools 367.3 s / 72 rows;
    rows-longrun-v6 mean 5.1 s, p95 11.4 s; v4-tools 316.1 s / 68; policy 13309.3 s / 40
marker census ('ANSWER:' in row.content): v3 79/96, v4 78/96, v4-tools 14/68, v5 6/72, v6 13/72
grade_v3 on v6 pointer-stable: 9 checks emitted of 13 declared, 5 boolean, 4 null
```
