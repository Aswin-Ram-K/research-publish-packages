# HARNESS-MAP — the experiment harness as it actually runs

> **BANNER — the line numbers in this body are HISTORICAL (added 2026-10-26 by `HARNESS-MAP-LINEREFS`).**
> `run_longrun.py` has grown from 1,653 to 3,008 lines since the body was written, so its `:NNN` citations below are
> stale. The authoritative positions are in **`## Line-reference refresh (2026-10-26)`** at the end of this file;
> follow that section for where the code is, and read the body for what the map claimed.


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
| 2 | **Prereg** | `experiments/ptr-engine/LONGRUN-PREREG.md`, `TASKS-V2-PREREG.md`, `ANCHOR-PREREG-V2.md`; checked by `experiments/ptr-engine/tools/anchor_prereg_check.py` | `python3 experiments/ptr-engine/tools/anchor_prereg_check.py` | predictions P1–P4, request budget | prereg markdown; `LONGRUN-PREREG.json:total_requests=500` | `ESTIMATE` < 1 s (pure file read; no timer taken) | 0 | `LONGRUN-PREREG.json`, `ANCHOR-PREREG.json` |
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
| 1 | `python3 experiments/ptr-engine/longrun/cell.py prereg --task LR-01 --predictions predictions.json --budget 96` | a machine-readable prereg exists, records the predicted direction, and the request budget is fixed **before** any row; refuses to overwrite a prereg that already has rows | rounds 6, 18, 37, 14 (4 cards, 0 requests) |
| 2 | `python3 experiments/ptr-engine/longrun/cell.py author --task LR-01 --schema v5` | one fixture file carrying turns, checkpoints, **answer contract**, and acceptance checks as machine fields; a reachability check proves every checkpoint fact is stated in a turn before any request | rounds 7, 10, 15, 19, 24, 28, 29 (7 cards) |
| 3 | `python3 experiments/ptr-engine/longrun/cell.py check --task LR-01 --arm pointer-stable` | dry-run manifest + pairwise-unique request bodies + reachability + contract presence, **zero requests**; exit 2 on any missing precondition | rounds 9, 17, 20, 33 (4 cards) |
| 4 | `python3 experiments/ptr-engine/longrun/cell.py run --task LR-01 --arm pointer-stable --tools read_file --budget 96` | a cell runs under one frozen harness digest, writes a pre-request intent row per request (no orphan requests), stamps `fixture_sha256` + `harness_sha256` on every row, and refuses `--resume` across a digest change | rounds 13, 20, 21, 22, 26, 30 (6 cards, 617 requests) |
| 5 | `python3 experiments/ptr-engine/longrun/cell.py grade --cell cells/LR-01/pointer-stable --primary det_verify` | one headline, from the decidable instrument; v3/v4 emitted as secondary with lineage asserted; `contract_violation` reported separately from wrong answers; refuses a fixture whose sha does not match the rows | rounds 23, 27, 36, 39 (4 cards + the v3/v4/R2 chain) |
| 6 | `python3 experiments/ptr-engine/longrun/cell.py verify --cell cells/LR-01/pointer-stable --red-green <guard>` | a red→green proof on one guard, the author's commands re-run in a clean shell (`env -i`), and a **verdict handoff written by the tool**, so the verifier cannot fail to persist | round 40 (5 cards) + the hand-written `VERDICTS.md` row |
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

## Line-reference refresh (2026-10-26)

Unit `HARNESS-MAP-LINEREFS`, HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3`. **This section is authoritative for positions; the body is not.**
The body was written when `run_longrun.py` was 1,653 lines; at HEAD it is **3,008 lines** (`wc -l`), so its later
`run_longrun.py:NNN` citations are displaced by 500-700 lines. A citation that *resolved* was still wrong: line 1191
exists, it is just no longer `make_row` (which is at 1781). `body_unchanged: true` marks a stale citation left in the
body on purpose — this card may append, never rewrite the historical record — and this table is its correction.

**Method.** Every symbol below was resolved at HEAD by AST (`def`/`class`/module assignment) to its first/last line;
a 3-line proof excerpt is quoted in §E. A symbol that did not resolve would be `unlocated`: **0 of 31 stale body
anchors and 0 of the 13 stages are `unlocated`**. The card's two extra symbols resolve too —
`_gate_finish` at `run_longrun.py:516-575` (E-_gate_finish), `derive_stop_reason` at `client.py:141-181` (E-derive_stop_reason).

### A. The 13 stages at HEAD

| # | stage | symbol → HEAD range | proof |
|---:|---|---|---|
| 1 | **Preflight** — `stage_preflight` | `experiments/ptr-engine/longrun/cell.py:247-325` | E-stage_preflight |
| 2 | **Harness freeze** — `stage_harness` (list `HARNESS_FILES`) | `experiments/ptr-engine/longrun/cell.py:329-350` + `experiments/ptr-engine/longrun/cell.py:128-134` | E-stage_harness E-HARNESS_FILES |
| 3 | **Budget / G1 ledger** — `stage_budget` → `eval_gate_ledger` → `request_ledger.main` | `experiments/ptr-engine/longrun/cell.py:354-417` + `experiments/ptr-engine/longrun/cell.py:1215-1305` + `experiments/ptr-engine/tools/request_ledger.py:787-854` | E-stage_budget E-eval_gate_ledger E-request_ledger_main |
| 4 | **G2 projection** — `stage_projection` → `eval_gate_projection` | `experiments/ptr-engine/longrun/cell.py:813-815` + `experiments/ptr-engine/longrun/cell.py:683-810` | E-stage_projection E-eval_gate_projection |
| 5 | **G3 prereg** — `eval_gate_prereg` | `experiments/ptr-engine/longrun/cell.py:1390-1507` | E-eval_gate_prereg |
| 6 | **Run** — `stage_run` → `run_cell` (cap guard `_gate_finish`) | `experiments/ptr-engine/longrun/cell.py:1571-1644` + `experiments/ptr-engine/longrun/run_longrun.py:2191-2661` + `experiments/ptr-engine/longrun/run_longrun.py:516-575` | E-stage_run E-run_cell E-_gate_finish |
| 7 | **Row writing** — `make_row` / `append_row` | `experiments/ptr-engine/longrun/run_longrun.py:1781-1970` + `experiments/ptr-engine/longrun/run_longrun.py:1998-2013` | E-make_row E-append_row |
| 8 | **Grade** — `stage_grade` → `grade_v5.main` (`derive_truth`) | `experiments/ptr-engine/longrun/cell.py:1648-1667` + `experiments/ptr-engine/longrun/grade_v5.py:1081-1113` + `experiments/ptr-engine/longrun/grade_v5.py:553-583` | E-stage_grade E-grade_v5_main E-derive_truth |
| 9 | **Analyse** — `stage_analyse` → `analyze_stats.main` (`turn_latency_rows`,`quantile_ci`) | `experiments/ptr-engine/longrun/cell.py:1671-1740` + `experiments/ptr-engine/longrun/analyze_stats.py:1620-1842` + `experiments/ptr-engine/longrun/analyze_stats.py:805-908` + `experiments/ptr-engine/longrun/analyze_stats.py:350-410` | E-stage_analyse E-analyze_stats_main E-turn_latency_rows E-quantile_ci |
| 10 | **Record** — `stage_record` | `experiments/ptr-engine/longrun/cell.py:1775-1854` | E-stage_record |
| 11 | **Launcher** — `run_a_star.main` | `experiments/ptr-engine/tools/run_a_star.py:636-835` | E-run_a_star_main |
| 12 | **Verdict binding** — `tree_freeze.wrap` / `freeze` → `verdict_scope.run` | `experiments/ptr-engine/tools/tree_freeze.py:413-471` + `experiments/ptr-engine/tools/tree_freeze.py:183-213` + `experiments/ptr-engine/tools/verdict_scope.py:198-231` | E-wrap E-freeze E-verdict_scope_run |
| 13 | **Request ledger report** — `build_report` | `experiments/ptr-engine/tools/request_ledger.py:571-713` | E-build_report |

### B. `old → current` — every stale body citation (31 rows)

| path | symbol | old | current | status | proof | body_unchanged | body citation |
|---|---|---:|---|---|---|---|---|
| experiments/ptr-engine/longrun/run_longrun.py | load_fixture | 123 | 137-177 | corrected | E-load_fixture | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | ARMS | 52 | 66 | corrected | E-ARMS | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | PREDICTIONS | 57 | 71-80 | corrected | E-PREDICTIONS | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | TOOL_CALLS_PER_TURN | 203 | 220 | corrected | E-TOOL_CALLS_PER_TURN | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | TOOL_FETCH_ROUNDS_PER_ARM | 207 | 230 | corrected | E-TOOL_FETCH_ROUNDS_PER_ARM | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | TOOL_FETCH_ROUNDS_PER_TURN | 214 | 236 | corrected | E-TOOL_FETCH_ROUNDS_PER_TURN | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | BudgetExhausted | 250 | 293-294 | corrected | E-BudgetExhausted | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | serve_from_prompt | 507 | 839-860 | corrected | E-serve_from_prompt | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | fetch_rounds | 569 | 901-1046 | corrected | E-fetch_rounds | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | build_manifest | 859 | 1404-1495 | corrected | E-build_manifest | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | write_manifest | 938 | 1498-1509 | corrected | E-write_manifest | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | run_dry | 1344 | 2057-2169 | corrected | E-run_dry | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | run_cell | 1445 | 2191-2661 | corrected | E-run_cell | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | Planner | 709 | 1050-1197 | corrected | E-Planner | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | send_chat | 1026 | 1541-1549 | corrected | E-send_chat | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | make_row | 1191 | 1781-1970 | corrected | E-make_row | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | append_row | 1296 | 1998-2013 | corrected | E-append_row | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | read_cell_rows | 1303 | 2016-2032 | corrected | E-read_cell_rows | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | resume_start | 1322 | 2035-2041 | corrected | E-resume_start | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | system_prompt_line | 731 | 1072-1074 | corrected | E-system_prompt_line | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | turn_user | 176 | 198-203 | corrected | E-turn_user | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | turn_block | 184 | 206-207 | corrected | E-turn_block | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | smoke_help | 1795 | 2848-2851 | corrected | E-smoke_help | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | budget_projection | 1479 | 476-480 | corrected | E-budget_projection | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | budget_projection | 1484 | 476-480 | corrected | E-budget_projection | true | `run_longrun.py` |
| experiments/ptr-engine/longrun/run_longrun.py | durable_spend | 1499 | 2286-2289 | corrected | E-durable_spend | true | `run_longrun.py` |
| experiments/ptr-engine/tools/det_verify.py | FIXTURE | 57 | 60 | corrected | E-FIXTURE | true | `det_verify.py` |
| experiments/ptr-engine/tools/det_verify.py | CHECK_ORDER | 72 | 74-76 | corrected | E-CHECK_ORDER | true | `det_verify.py` |
| experiments/ptr-engine/tools/det_verify.py | CHECK_WHY | 566 | 568-580 | corrected | E-CHECK_WHY | true | `det_verify.py` |
| experiments/ptr-engine/tools/det_verify.py | answer_slot_end | 132 | 136-146 | corrected | E-answer_slot_end | true | `det_verify.py` |
| experiments/ptr-engine/measure/run_cells.py | prediction_row | 10 | 14-16 | corrected | E-prediction_row | true | `measure/run_cells.py` |

Not in the table because they still resolve at HEAD: `adapt_v4.py:69` (`adapt_v4`), `adapt_v4.py:88` (`main`)
and `grade_v4.py:105` (the `marker_missing` branch).

### C. V3's #5 and #6, re-pointed at HEAD

V3's proofs do not resolve: `cell.py` line 223 is now the loop body of `_count_rows`, `cell.py` lines 721-734 is now G2's
verdict dict, and `run_longrun.py` line 1465 is a provenance comment. Each item is re-pointed; the one whose proof
re-points to a partial mechanism is downgraded.

| item | V3 state | V3 proof | at HEAD | classification now |
|---|---|---|---|---|
| #5 budgets in three currencies | closed | `cell.py:721-734` (no longer the ledger) | `cell.py:1215-1305 eval_gate_ledger()` reads `budget.cap`/`reserve` from the artefact and sets `counting_tool` to `request_ledger.py`; `request_ledger.py:571-713 build_report()` owns the count (E-eval_gate_ledger, E-build_report) | **closed** — one currency; proof re-pointed |
| #6 mid-cell code-version mixing | closed | `cell.py` line 223 (harness digest); `run_longrun.py` line 1465 (resume refusal) | `cell.py:128-134 HARNESS_FILES` (5 files + fixture) and `run_longrun.py:2231-2234` `RESUME REFUSED` on a manifest-sha mismatch (E-HARNESS_FILES, E-durable_spend) | **narrowed** — `cell.py` is not in its own `HARNESS_FILES` list (`measure/HARNESS-PIN.json:digest_recipe`), so the conductor's bytes are unbound and can still mix mid-cell; the 5 listed files + fixture are bound and resume refuses across a digest change |

`body_unchanged: true` for both: `docs/HARNESS-MAP-V3.md` is another unit's record and is not in this card's
write paths, so its text keeps the stale numbers and **this section is the correction**.

### D. The guard

`python3 experiments/ptr-engine/tools/harness_map_check.py --check` walks every `file:line [symbol]` citation in
`docs/HARNESS-MAP.md` and exits **1** when the line is blank, comment-only, outside the file, or outside the body of
the symbol the citation names; when a symbol has a row in §A/§B, that row's `current` range wins. A **forward-only
baseline** (`measure/HARNESS-MAP-LINEREFS.json :: guard.baseline`, 21 entries) freezes the misses that
existed when the guard was written, so history does not fail today; a citation that is not baselined must pass.
Measured: **before = exit 1** (25 unbaselined misses of 67 citations); a `/tmp` copy with one
citation re-pointed to a blank line = **exit 1**; the corrected file = **exit 0**.

**What it cannot catch (named limit):** a moved-but-non-empty line whose citation carries no symbol, and a line that
still happens to hold the named token. The body has such citations (bare `:1499`, prose-only cells); they pass a
position check until someone re-derives them. The guard checks *where a citation points*, not whether the prose
around it still describes the code there.

### E. Proof excerpts

**E-stage_preflight** — `experiments/ptr-engine/longrun/cell.py:247-325`

```python
def stage_preflight(args):
    """Refuse (2) any fixture that cannot be graded, naming the exact key."""
    try:
        fixture = _load_fixture(args.fixture)
    except (OSError, json.JSONDecodeError) as exc:
        raise Abort(2, "1/7 preflight", "fixture does not parse: %s: %s"
                    % (_repo_rel(args.fixture), exc))

    sp = fixture.get("system_prompt")
    if not isinstance(sp, str) or not sp.strip():
        raise Abort(2, "1/7 preflight",
                    "fixture lacks a non-empty 'system_prompt' (key 'system_prompt' "
                    "is absent or empty) - a cell without it sends an unreadable "
                    "prompt; refusing to run it")

    arms = _runner_arms()
    if arms and args.arm not in arms:
        raise Abort(2, "1/7 preflight", "arm %r is not one of the runner's arms %s"
                    % (args.arm, list(arms)))

    checkpoints = fixture.get("checkpoints") or []
    if not checkpoints:
        raise Abort(2, "1/7 preflight", "fixture declares no 'checkpoints'")

    for idx, cp in enumerate(checkpoints):
        cid = str(cp.get("id") or "cp.%d" % idx)
        turn = cp.get("turn")
        if not isinstance(turn, int) or turn <= 0:
            raise Abort(2, "1/7 preflight", "checkpoint %s has no integer 'turn'" % cid)
        q = cp.get("question")
        if not isinstance(q, str) or not q.strip():
            raise Abort(2, "1/7 preflight", "checkpoint %s has no non-empty 'question'" % cid)
        # v5 derives truth from the source tree; `expected` is its documented form.
        if cp.get("truth") is None and cp.get("expected") is None:
            raise Abort(2, "1/7 preflight",
                        "checkpoint %s has no 'truth' (and no 'expected' documenting it)"
                        % cid)
        if not cp.get("answer_spec"):
            raise Abort(2, "1/7 preflight", "checkpoint %s has no 'answer_spec' to derive "
                        "its truth from the source tree" % cid)

    # Truth must be DERIVABLE from the pinned source tree by AST, per checkpoint.
    # The derivation is grade_v5.derive_truth (canonical); we call it, never copy it.
    sys.path.insert(0, HERE)
    try:
        import grade_v5  # noqa: E402
    except Exception as exc:  # pragma: no cover - import would be a broken tree
        raise Abort(2, "1/7 preflight", "cannot import grade_v5 for truth derivation: %s" % exc)

    for idx, cp in enumerate(checkpoints):
        cid = str(cp.get("id") or "cp.%d" % idx)
        one = dict(fixture)
        one["checkpoints"] = [cp]
        try:
            derived = grade_v5.derive_truth(one)
        except SystemExit as exc:
            raise Abort(2, "1/7 preflight", "checkpoint %s truth is not derivable: %s"
                        % (cid, exc.code))
        except Exception as exc:
            raise Abort(2, "1/7 preflight", "checkpoint %s truth is not derivable from the "
                        "source tree: %s: %s" % (cid, type(exc).__name__, exc))
        if not derived:
            raise Abort(2, "1/7 preflight", "checkpoint %s derived no truth" % cid)

    # The answer contract the grader enforces must be IN the system prompt:
    # a contract the model never sees is a contract the grader invents.
    contract = fixture.get("answer_contract") or {}
    forms = contract.get("forms") or ["ANSWER: NUM <integer>", "ANSWER: CALL ",
                                      "ANSWER: NONE", "ANSWER: TEXT"]
    missing = [f for f in forms if f not in sp]
    if missing:
        raise Abort(2, "1/7 preflight", "the answer contract is not in the system prompt: "
                    "missing form(s) %s" % missing)

    truth = grade_v5.derive_truth(fixture)
    detail = {"checkpoints": len(truth), "turns": [t["turn"] for t in truth],
              "kinds": [t["kind"] for t in truth],
              "system_prompt_chars": len(sp), "fixture_version": fixture.get("fixture_version")}
    return fixture, truth, detail
```

**E-stage_harness** — `experiments/ptr-engine/longrun/cell.py:329-350`

```python
def stage_harness(args, fixture):
    """Freeze every measurement input; refuse (2) on a moved digest."""
    files = {}
    for path, name in HARNESS_FILES:
        if not os.path.exists(path):
            raise Abort(2, "2/7 harness", "harness file is missing: %s" % _repo_rel(path))
        files[name] = _sha256_file(path)
    files["fixture"] = _sha256_file(args.fixture)

    combined = hashlib.sha256()
    for name in sorted(files):
        combined.update(("%s:%s\n" % (name, files[name])).encode("utf-8"))
    digest = combined.hexdigest()

    if args.expect_harness and args.expect_harness != digest:
        raise Abort(2, "2/7 harness",
                    "harness changed mid-cell: --expect-harness %s but the current "
                    "digest is %s (files: %s)"
                    % (args.expect_harness, digest, ", ".join(sorted(files))),
                    {"expected": args.expect_harness, "actual": digest,
                     "files": files})
    return {"harness_sha256": digest, "files": files}
```

**E-HARNESS_FILES** — `experiments/ptr-engine/longrun/cell.py:128-134`

```python
HARNESS_FILES = (
    (os.path.join(HERE, "run_longrun.py"), "run_longrun.py"),
    (os.path.join(HERE, "client.py"), "client.py"),
    (os.path.join(HERE, "grade_v5.py"), "grade_v5.py"),
    (os.path.join(HERE, "analyze_stats.py"), "analyze_stats.py"),
    (os.path.join(ENGINE, "tools", "det_verify.py"), "tools/det_verify.py"),
)  # the fixture is added per invocation: it is the 6th measurement input
```

**E-stage_budget** — `experiments/ptr-engine/longrun/cell.py:354-417`

```python
def stage_budget(args):
    """Ask the RUNNER's own dry-run what the cell would send; refuse (3) over budget."""
    if args.budget is None:
        raise Abort(3, "3/7 budget", "--budget is required for a live cell (offline mode "
                    "skips stages 3-4)")
    argv = [sys.executable, RUNNER, "--dry-run", "--fixture", args.fixture,
            "--arms", args.arm, "--reps", str(args.reps)]
    # BUDGET-TURN-SCOPE: price the cell the LIVE path will actually run. stage_run caps a
    # partial cell at --turns (same condition, read the same way: n_turns set AND different
    # from the fixture's N); this argv used to omit it, so the runner priced the fixture.
    n_turns = int(args.turns or 0)
    fixture_n = 0
    try:
        fixture_n = int(_load_fixture(args.fixture).get("N") or 0)
    except (OSError, json.JSONDecodeError):
        pass
    truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
    if truncated:
        argv += ["--max-turns", str(n_turns)]
    if args.endpoint:
        argv += ["--base-url", args.endpoint]
    rc, out, err = _run(argv, purpose="preflight_self_check", phase="3/7 budget",
                        label="budget-dry-run")
    m = re.search(r"would_send_total=(\d+)", out or "")
    if rc != 0 or not m:
        raise Abort(3, "3/7 budget", "the runner's --dry-run produced no would_send_total "
                    "(exit %d): %s" % (rc, (err or out or "").strip().splitlines()[-1:]))
    would = int(m.group(1))
    # The runner's --dry-run cannot see the flag it was just handed: run_dry prices
    # range(1, fixture["N"] + 1) (run_longrun.py:2079) and prints int(fixture["N"])
    # (run_longrun.py:2121-2127), so --max-turns moved the LIVE run and left the price at
    # N. Scope the TURN component here, in one line: remove exactly the turns that will
    # not run, priced at the runner's own per-arm N. Digest requests and tool follow-ups
    # stay priced (never under-state what has already been committed). `priced_n` is read
    # from the runner's own line, so a runner that honours --max-turns later makes this a
    # no-op instead of a double discount.
    priced_n = max([int(x) for x in re.findall(r"N=(\d+)", out or "")] or [fixture_n])
    if truncated and priced_n > n_turns:
        would -= (priced_n - n_turns) * _arms_count(args.arm) * int(args.reps or 1)
    required = int(math.ceil(would * (1.0 + BUDGET_HEADROOM)))

    spent, nfiles = 0, 0
    if os.path.isdir(MEASURE):
        for name in sorted(os.listdir(MEASURE)):
            if name.startswith("rows-") and name.endswith(".jsonl"):
                spent += _count_rows(os.path.join(MEASURE, name))
                nfiles += 1
    remaining = PROJECT_QUOTA - spent
    after = remaining - would

    detail = {"would_send_total": would, "headroom": BUDGET_HEADROOM,
              "required_with_headroom": required, "budget": args.budget,
              "quota_project": PROJECT_QUOTA, "quota_spent_best_effort": spent,
              "quota_rows_files": nfiles, "quota_remaining": remaining,
              "quota_after_this_cell": after, "quota_basis":
              "best-effort: project cap %d minus rows on disk in %s (%d files); the "
              "runner reports no quota" % (PROJECT_QUOTA, _repo_rel(MEASURE), nfiles)}
    if required > args.budget:
        raise Abort(3, "3/7 budget",
                    "would_send_total=%d +%.0f%% headroom = %d exceeds --budget %d "
                    "(project quota remaining %d, best-effort)"
                    % (would, BUDGET_HEADROOM * 100, required, args.budget, remaining),
                    detail)
    return detail
```

**E-eval_gate_ledger** — `experiments/ptr-engine/longrun/cell.py:1215-1305`

```python
def eval_gate_ledger(args):
    """G1 — the projected request cost must fit the ledger's remaining quota.

    The cost is the cell's own shape (turns x arms x reps) PLUS the fetch follow-up
    allowance, because the ledger counts a follow-up as a billed request. The decision
    is taken by ``request_ledger.build_report`` over the very row files the artefact
    lists, so the gate cannot drift from the tool that owns the counting; a refusal
    reuses the ledger's own exit code (4 = EXIT_OVER).
    """
    stage = "3a/7 G1 ledger gate"
    doc, digest = _load_gate_artefact(LEDGER_ARTEFACT, GATE_LEDGER, stage, "ledger-cap")
    budget = doc.get("budget") or {}
    if "cap" not in budget:
        raise Abort(2, stage, "%s ledger-cap: artefact has no budget.cap (%s) — cannot "
                    "gate blind" % (GATE_LEDGER, _repo_rel(LEDGER_ARTEFACT)))
    reserve_raw = budget["reserve"] if "reserve" in budget else 0
    ok, facts = validate_g1(getattr(args, "turns", None), getattr(args, "reps", None),
                            _arms_count(getattr(args, "arm", None)),
                            getattr(args, "fetch_followup_allowance", None),
                            budget.get("cap"), reserve_raw, ratio=FETCH_FOLLOWUP_RATIO)
    verdict = {
        "gate": GATE_LEDGER, "what": "ledger-cap", "ok": False,
        "turns_total": facts.get("turns_total"), "arms": facts.get("arms"),
        "fetch_followup_allowance": facts.get("allowance"),
        "would_spend": facts.get("would_spend"),
        "spent": None, "cap": facts.get("cap"), "reserve": facts.get("reserve"),
        "headroom": None, "projected": None, "remaining": None,
        "artefact": _repo_rel(LEDGER_ARTEFACT), "artefact_sha256": digest,
        "flag": "--turns / --reps / --fetch-followup-allowance (or a larger cap in the "
                "ledger)",
    }
    if not ok:
        _refuse_from_operands(verdict, facts, 4, verdict["flag"])
        return verdict
    turns, reps, arms = facts["turns"], facts["reps"], facts["arms"]
    turns_total = facts["turns_total"]
    allowance = facts["allowance"]
    would_spend = facts["would_spend"]
    ledger = _ledger_module()
    try:
        report = ledger.build_report(_ledger_row_paths(doc), facts["cap"],
                                     facts["reserve"], would_spend)
    except Exception as exc:                      # RowsUnreadable and anything else
        raise Abort(2, stage, "%s ledger-cap: the ledger's own counter could not read "
                    "its row files (%s); an uncountable budget must refuse, never allow"
                    % (GATE_LEDGER, exc))
    b = report["budget"]
    # GATES-MESSAGE-CONSISTENCY: ONE sentence family per verdict, chosen by the verdict's
    # own `ok`. This branch used to print the refusal sentence unconditionally, so an
    # ADMITTED cell recorded "this cell needs 1,154 requests ... but only 4,320 remain:
    # shortfall -3,166 requests" -- where 1,154 is the CUMULATIVE spend after the cell,
    # 4,320 is the cap (limit = cap - reserve), and a negative shortfall is no shortfall.
    unspent = b["cap"] - b["reserve"] - b["spent"]     # spendable BEFORE this cell
    if b["within_budget"]:
        g1_consequence = (
            "G1 admits: this cell's own %s requests (would_spend: %d turn(s) x %d arm(s) "
            "x %d rep(s) = %d requests, plus a %d-request fetch follow-up allowance, "
            "ceil(%d turns x 68/801) unless --fetch-followup-allowance overrides it) are "
            "added to the %s requests already spent, so cumulative spend after this cell "
            "(projected) is %s requests against a limit of %s requests (cap %s - reserve "
            "%s): the cell fits, leaving %s requests of headroom after it, of which %s "
            "were unspent before it"
            % (_num(b["would_spend"]), turns, arms, reps, turns_total, allowance,
               turns_total, _num(b["spent"]), _num(b["projected"]),
               _num(b["headroom"]), _num(b["cap"]), _num(b["reserve"]),
               _num(b["remaining"]), _num(unspent)))
    else:
        g1_consequence = (
            "this cell would need %s requests (would_spend: %d turn(s) x %d arm(s) x %d "
            "rep(s) = %d requests, plus a %d-request fetch follow-up allowance) on top "
            "of the %s requests already spent, taking cumulative spend (projected) to %s "
            "requests against a limit of %s requests (cap %s - reserve %s): shortfall %s "
            "requests, so it must not send"
            % (_num(b["would_spend"]), turns, arms, reps, turns_total, allowance,
               _num(b["spent"]), _num(b["projected"]), _num(b["headroom"]),
               _num(b["cap"]), _num(b["reserve"]),
               _num(b["projected"] - b["headroom"])))
    verdict.update({
        "gate": GATE_LEDGER, "what": "ledger-cap", "ok": bool(b["within_budget"]),
        "spent": b["spent"], "headroom": b["headroom"], "projected": b["projected"],
        "remaining": b["remaining"],
        "counting_tool": _repo_rel(REQUEST_LEDGER_TOOL),
        "computed": "%s requests" % _num(b["projected"]),
        "limit": "%s requests (cap %s - reserve %s - spent %s)"
                 % (_num(b["headroom"]), _num(b["cap"]), _num(b["reserve"]),
                    _num(b["spent"])),
        "short": "%s %s/%s requests" % (GATE_LEDGER, _num(b["projected"]),
                                       _num(b["headroom"])),
        "consequence": g1_consequence,
    })
    return verdict
```

**E-stage_projection** — `experiments/ptr-engine/longrun/cell.py:813-815`

```python
def stage_projection(args, budget):
    """Enforce G2: refuse (8) when the calibrated wall clock exceeds --max-wall."""
    return _enforce(eval_gate_projection(args, budget), "3b/7 projection", 8)
```

**E-eval_gate_projection** — `experiments/ptr-engine/longrun/cell.py:683-810`

```python
def eval_gate_projection(args, budget):
    """Evaluate G2: does the CALIBRATED wall clock fit --max-wall?

    TASK 3 of HARNESS-GUARDS projected `projected_requests x --turn-wall-cap`, i.e. it
    multiplied every request by the live abort threshold. That is a worst case, not a
    forecast: a 48-turn cell projected 8,640 s and was refused, and the 60-turn operator
    comparison projected 10,800 s — so the guard refused the very experiments it exists to
    protect. PROJECTION-CALIBRATION replaces the multiplier with
    ``--projected-turn-wall`` (default 60 s), or the p90 of a prior row file when
    ``--projected-from`` names one; the worst case is still PRINTED next to it, uncensored.

    ``--turn-wall-cap`` keeps its meaning unchanged: :func:`stage_run` still hands it to
    the runner, which still aborts any live turn that reaches it. The projection does not
    weaken that abort; it only stops billing every turn at the abort threshold.

    It runs after :func:`stage_budget` because it consumes that stage's
    ``would_send_total`` and must never preempt a budget refusal (exit 3) with exit 8.
    Nothing live has been sent at this point: the only process run so far was the
    offline `--dry-run`.
    """
    stage = "3b/7 projection"
    _doc, digest = _load_gate_artefact(PROJECTION_ARTEFACT, GATE_PROJECTION, stage,
                                       "projection")
    defaults = _doc.get("defaults") or {}
    # Operands are read RAW: converting with float()/int() before validation is exactly
    # how a hostile value used to become an admission (or an uncaught ValueError).
    turns = _as_int(getattr(args, "turns", None), 0)
    reps = _as_int(getattr(args, "reps", None), 1)
    requests = _as_int((budget or {}).get("would_send_total"), 0)
    if requests <= 0:
        requests = turns * reps
    mode = thinking_mode(args)
    proj_turn, source, kind, override = projected_turn_wall(
        args, defaults, PROJECTION_ARTEFACT, digest)
    ok, facts = validate_g2(getattr(args, "max_wall", None),
                            getattr(args, "turn_wall_cap", None), proj_turn, requests)
    cap_turn = facts.get("turn_wall_cap")
    max_wall = facts.get("max_wall")
    verdict = {
        "gate": GATE_PROJECTION, "what": "projection", "ok": False,
        "turns": turns, "reps": reps, "projected_requests": requests,
        "projected_wall_s": facts.get("projected"),
        "worst_case_wall_s": (int(round(requests * cap_turn)) if cap_turn else 0),
        "max_wall_s": max_wall, "turn_wall_cap_s": cap_turn,
        "projected_turn_wall_s": proj_turn,
        "thinking_mode": mode,
        "projected_turn_wall_source": kind,
        "projected_from_file": source if kind == "p90" else None,
        "projection_override": override,
        "projection": "projected_requests x projected_turn_wall(thinking mode)",
        "artefact": _repo_rel(PROJECTION_ARTEFACT),
        "artefact_sha256": digest,
    }
    if not ok:
        # GATE-CHAIN-FIX D1 made a non-positive ceiling a refusal instead of a bypass;
        # GATE-OPERAND-VALIDATION makes EVERY operand that can switch G2 off a refusal:
        # max_wall, turn_wall_cap, projected_turn_wall and the request count, whether the
        # value arrived as a flag, a p90 or the artefact. There is no unlimited mode.
        _refuse_from_operands(verdict, facts, 8,
                              "--max-wall / --turn-wall-cap / --projected-turn-wall")
        return verdict
    projected = facts["projected"]
    requests = facts["requests"]
    worst = int(round(requests * cap_turn))
    line = ("turns=%d projected_requests=%d projected_wall~=%ds "
            "(cap-per-turn %.0fs -> worst case %ds) cap=%ds "
            "projected-turn-wall=%.1fs source=%s thinking=%s%s%s"
            % (turns, requests, projected, cap_turn, worst, int(max_wall),
               proj_turn, kind, mode,
               (" file=%s" % source) if kind == "p90" else "",
               " OVERRIDE" if override else ""))
    print("cell: 3b/7 projection %s" % line, flush=True)
    # GATES-MESSAGE-CONSISTENCY: the allow and refuse families are chosen by `ok`, never
    # by which computation ran. The old sentence said "exceeds the allowed 2880s" on a
    # verdict that was ADMITTED at the boundary (V-GATE-CHAIN-2: allow 2,880, refuse
    # 2,881) and called the 48-turn multiplier "48 request(s)". Requests are the
    # runner's would-send count and are named as requests; turns are named as turns.
    admitted = max_wall > 0 and projected <= max_wall
    #: G2's allow family: what the projection is made of, and that it fits.
    g2_allow = (
        "G2 admits: projected wall %d s = %d requests to send (%d turn(s) x %d "
        "rep(s)) x %.1f s calibrated per-turn wall for thinking %s (source %s), "
        "within the %d s allowed by --max-wall by %d s of slack. The worst case "
        "priced at the %.0f s per-turn abort is %d s; that abort still kills any "
        "live turn that reaches it"
        % (projected, requests, turns, reps, proj_turn, mode, kind, int(max_wall),
           int(max_wall) - projected, cap_turn, worst))
    #: G2's refuse family: the same numbers, stated as the refusal they are.
    g2_refuse = (
        "projected wall %d s = %d requests to send (%d turn(s) x %d rep(s)) x "
        "calibrated per-turn wall %.1f s for thinking %s (source %s) exceeds the "
        "allowed %d s by %d s: this cell would spend its whole budget waiting on "
        "runaway turns"
        % (projected, requests, turns, reps, proj_turn, mode, kind, int(max_wall),
           projected - int(max_wall)))
    verdict.update({
        "ok": (max_wall > 0 and projected <= max_wall),
        "projected_requests": requests, "projected_wall_s": projected,
        "worst_case_wall_s": worst,
        "line": line,
        "computed": "%d s" % projected,
        "limit": "%d s (--max-wall)" % int(max_wall),
        "flag": ("--projected-turn-wall / --thinking / --max-wall" if override else
                 "--thinking / --projected-from p90 / --max-wall"),
        "short": "%s %s s of %s s" % (GATE_PROJECTION, _num(projected),
                                      _num(int(max_wall))),
    })
    if not (max_wall > 0):
        # GATE-CHAIN-FIX D1: the old verdict was
        # `ok = not (max_wall > 0 and projected > max_wall)`, which ALLOWED a non-positive
        # ceiling -- `--max-wall 0` and `--max-wall -1` switched G2 off. Neither the help
        # text nor docs/GATE-CHAIN.md declares an "unlimited" mode, so a ceiling of zero
        # or less is a REFUSAL, named as such, never a bypass.
        verdict.update({
            "ok": False,
            "computed": "--max-wall=%s s" % _num(max_wall),
            "limit": "a positive ceiling (> 0 s)",
            "short": "%s max-wall=%s s (non-positive)" % (GATE_PROJECTION, _num(max_wall)),
            "consequence": ("--max-wall %s is not a wall: a ceiling of zero or less is "
                            "not 'unlimited' and does not disable the gate. Pass a "
                            "positive number of seconds; there is no unlimited mode"
                            % _num(max_wall)),
        })
    elif verdict["ok"]:
        verdict["consequence"] = g2_allow
    else:
        verdict["consequence"] = g2_refuse
    return verdict
```

**E-eval_gate_prereg** — `experiments/ptr-engine/longrun/cell.py:1390-1507`

```python
def eval_gate_prereg(args, fixture):
    """G3 — the cell's own n must support the claim it will make, under PARM-1.

    H1 (p95 TTFT) is admissible only at n >= ``analyze_stats.min_n_for(0.95)`` = 60;
    at n < 60 the estimator itself raises InsufficientSamples, so a smaller cell may not
    claim it. H2 (per-turn prompt work) is a ratio over completed turns: n >= 1. H3
    (quality) is unadjudicable below 8 of the 12 checkpoints, so a fixture carrying
    fewer than 8 checkpoints cannot support it. A cell that declares NO hypothesis is
    refused with exit 12 -- G3's own code, distinct from preflight's 2: silence is not a
    claim you may spend on.
    """
    stage = "3c/7 G3 prereg gate"
    doc, digest = _load_gate_artefact(PREREG_ARTEFACT, GATE_PREREG, stage, "prereg")
    hyps = doc.get("hypotheses") or {}
    claim = _resolved_claim(args)
    if isinstance(claim, Exception):                 # absent/empty/none/unknown
        # The module's refusal text is the refusal: G3's own code (12), G3's own stage,
        # verbatim -- so no caller can mistake this for a different gate's decision.
        text = str(claim)
        return {
            "gate": GATE_PREREG, "what": "prereg", "rule_id": doc.get("rule_id"),
            "rule_sha256": doc.get("rule_sha256"),
            "hypothesis": str(getattr(args, "hypothesis", "") or ""),
            "hypothesis_source": "refused:claim_mode.resolve_claim",
            "n": 0, "artefact": _repo_rel(PREREG_ARTEFACT), "artefact_sha256": digest,
            "flag": "--hypothesis smoke|plumbing|H1|H2|H3",
            "thresholds": {}, "ok": False, "exit": claim.code,
            "claim": None, "comparison_eligible": False, "mode": None,
        # The DECISION is the module's; the refusal still names the same facts it
        # always named (computed/limit), and carries the module's sentence VERBATIM.
        "computed": _refusal_computed(args, hyps),
            "limit": _refusal_limit(args, hyps),
            "short": "%s n=0 (no claim declared)" % GATE_PREREG,
            "consequence": _refusal_consequence(args, hyps, text),
            "refusal_message": text,
            "refusal_stage": claim.stage, "refusal_code": claim.code,
        }
    name = claim.claim
    source = "flag:--hypothesis (%s)" % claim.mode
    min_n_h1, h1_basis = _h1_min_n()
    checkpoints = len((fixture or {}).get("checkpoints") or [])
    ok, facts = validate_g3(claim.claim, getattr(args, "turns", None),
                            getattr(args, "reps", None), checkpoints, hyps,
                            min_n_h1=min_n_h1, h1_basis=h1_basis,
                            smoke=claim.is_smoke)
    n = facts.get("n") or 0
    verdict = {
        "gate": GATE_PREREG, "what": "prereg", "rule_id": doc.get("rule_id"),
        "rule_sha256": doc.get("rule_sha256"),
        "hypothesis": name, "hypothesis_source": source, "n": n,
        "claim": claim.claim, "comparison_eligible": claim.comparison_eligible,
        "mode": claim.mode,
        "artefact": _repo_rel(PREREG_ARTEFACT), "artefact_sha256": digest,
        "flag": "--hypothesis / --turns / --reps",
        "thresholds": facts.get("thresholds") or {},
    }
    branch = facts.get("branch")
    if branch == "smoke":
        # ALLOWED, and non-comparable by declaration: the module builds this verdict so
        # the smoke branch has one author, not two.
        smoke = dict(_claim_module().smoke_prereg_verdict(verdict, n))
        smoke.update({"claim": claim.claim, "comparison_eligible": False,
                      "mode": claim.mode, "exit": 0})
        return smoke
    if not ok and branch == "operand":
        # turns/reps must be POSITIVE INTEGERS before any n is computed: turns=0 used to
        # reach the H3 branch, which only counted checkpoints, and ran in full.
        _refuse_from_operands(verdict, facts, 12, "--turns / --reps")
        return verdict
    if not ok and branch == "silence":
        verdict.update({
            "ok": False, "n": 0,
            "computed": "hypothesis=none declared",
            "limit": "a named hypothesis (%s)" % (", ".join(sorted(hyps)) or "H1|H2|H3"),
            "short": "%s n=%d (no hypothesis)" % (GATE_PREREG, n),
            "consequence": ("a live cell spends requests on a claim it must name; no "
                            "hypothesis was declared, and silence is not a claim you may "
                            "spend on"),
        })
        return verdict
    if not ok and branch == "unknown":
        verdict.update({
            "ok": False, "computed": "hypothesis=%s" % name,
            "limit": "one of %s" % ", ".join(sorted(hyps)),
            "short": "%s n=%d (unknown %s)" % (GATE_PREREG, n, name),
            "consequence": "PARM-1 does not define hypothesis %r" % name,
        })
        return verdict

    min_n = facts.get("min_n")
    if branch == "H1":
        ok = n >= min_n
        verdict["thresholds"] = {
            "estimator": facts["thresholds"].get("estimator"),
            "admissibility": facts["thresholds"].get("admissibility"),
            "ranking_rule": facts["thresholds"].get("ranking_rule"),
            "min_n": min_n, "q": 0.95, "basis": facts["thresholds"].get("basis"),
        }
        verdict["consequence"] = (
            "PARM-1 admits H1 (p95 TTFT, q=0.95) only at n >= %d completed turns; this "
            "cell would have n=%d, so its own n cannot support the claim it would state"
            % (min_n, n))
    elif branch == "H3":
        verdict["consequence"] = (
            "PARM-1's H3 returns no verdict below %d decidable of 12 checkpoints; this "
            "fixture carries %d checkpoint(s), so the claim is unsupportable"
            % (min_n, checkpoints))
    else:
        verdict["consequence"] = (
            "PARM-1's %s needs at least %d completed turn per arm; this cell would have "
            "n=%d" % (name, min_n, n))
    verdict.update({
        "ok": ok,
        "computed": "n=%d" % n,
        "limit": "n >= %d" % min_n,
        "short": "%s n=%d %s %d" % (GATE_PREREG, n, "≥" if ok else "<", min_n),
    })
    return verdict
```

**E-stage_run** — `experiments/ptr-engine/longrun/cell.py:1571-1644`

```python
def stage_run(args, rows_path, gate_manifest=None):
    """Invoke run_longrun.py UNCHANGED, streaming its output through."""
    argv = [sys.executable, RUNNER, "--fixture", args.fixture, "--arms", args.arm,
            "--reps", str(args.reps), "--rows", rows_path,
            "--turn-wall-cap", str(float(args.turn_wall_cap)),
            "--runaway-turns", str(int(args.runaway_turns)),
            "--thinking", thinking_for_runner(args)]
    if args.endpoint:
        argv += ["--base-url", args.endpoint]
    n_turns = int(args.turns or 0)
    fixture_n = 0
    try:
        fixture_n = int(_load_fixture(args.fixture).get("N") or 0)
    except (OSError, json.JSONDecodeError):
        pass
    truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
    if truncated:
        argv += ["--max-turns", str(n_turns)]
    claim = _resolved_claim(args)
    claim_fields, claim_sidecar = None, None
    if not isinstance(claim, Exception):
        # The resolved claim travels WITH the run: one record, written once, beside the
        # rows file the runner writes. analyze_stats reads it and refuses a claim="none"
        # cell by name (incomparable_claim), so a smoke cell's numbers can be reported
        # and can never be pooled with an H1/H2/H3 arm.
        claim_fields = {"claim": claim.claim,
                        "comparison_eligible": claim.comparison_eligible,
                        "mode": claim.mode}
        claim_sidecar = rows_path + ".claim.json"
        try:
            with open(claim_sidecar, "w", encoding="utf-8") as fh:
                json.dump({"claim": claim.claim,
                           "comparison_eligible": claim.comparison_eligible,
                           "mode": claim.mode,
                           "resolver": "claim_mode.resolve_claim",
                           "rows_path": _repo_rel(rows_path),
                           "note": ("one claim decision per invocation; a claim=none "
                                    "cell is reported on its own and never compared")},
                          fh, indent=1, sort_keys=True)
                fh.write("\n")
        except OSError:
            claim_fields, claim_sidecar = claim_fields, None
    # CLAIM-ROW-STAMP: thread the ALREADY-resolved claim (cell's cached record, one
    # parse in claim_mode) to the runner, so every row it writes is stamped.
    _claim_rec = _resolved_claim(args)
    if not isinstance(_claim_rec, Exception):
        argv += ["--claim-mode", "smoke" if _claim_rec.is_smoke else _claim_rec.claim]
    print("cell:   invoking: %s" % " ".join(argv), flush=True)
    proc = subprocess.run(argv)
    rc = proc.returncode
    # THE runner launch, and the only one: it carries the gate record it ran under, so
    # a launch with no gate record is detectable rather than merely discouraged.
    SPAWNS.record(argv=argv, purpose="runner_launch", phase="4/7 run",
                  pid=getattr(proc, "pid", None), label="run_longrun",
                  gate_record=gate_manifest)
    detail = {"argv": argv, "exit": rc, "rows_path": _repo_rel(rows_path),
              "rows_written": _count_rows(rows_path),
              "turns_requested": n_turns, "turns_truncated": truncated,
              "claim": claim_fields,
              # absolute, not repo-relative: the sidecar lives beside the rows file,
              # which may be outside the repo (a scratch out_dir) and `_repo_rel` would
              # then invent a "../../.." path that cannot be opened.
              "claim_sidecar": (claim_sidecar
                                if claim_sidecar and os.path.exists(claim_sidecar)
                                else None)}
    if rc != 0:
        # The runner's OWN codes are propagated distinctly: collapsing them into one
        # number is how a runaway abort became indistinguishable from a crash.
        code = rc if rc in _RUNNER_CODES else exit_codes.EXIT_RUNNER_CRASH
        raise Abort(code, "4/7 run",
                    "run_longrun.py exited %d (%s) — rows kept at %s"
                    % (rc, exit_codes.describe(rc) if rc in _RUNNER_CODES
                       else "unmapped runner failure", _repo_rel(rows_path)), detail)
    return detail
```

**E-run_cell** — `experiments/ptr-engine/longrun/run_longrun.py:2191-2661`

```python
def run_cell(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str) -> int:
    # TREATMENTS LAUNCH PRECONDITION: same assertion the dry run applies, applied to the
    # real launch too — a cell that would spend 48 requests on its control path refuses
    # BEFORE the manifest is frozen and before any request is sent.
    rc_t, lines = check_treatments(fixture, arm, HORIZON_TURNS)
    for line in lines:
        print(line)
    if rc_t != 0:
        print(f"LAUNCH REFUSED (exit {rc_t}): the {arm} treatment cannot fire inside "
              f"{HORIZON_TURNS} turns at this fixture's wall; no request was sent.",
              file=sys.stderr)
        return rc_t
    fixture = fixture_for_arm(fixture, arm)
    manifest_path = cfg.manifest_path or os.path.join(cfg.manifest_dir, run_id + ".json")
    rows = read_cell_rows(rows_path, run_id, fixture["task_id"], arm, rep) if cfg.resume else []
    # WIRE-CAP-GATE: the gate exists BEFORE the frozen manifest is written, so the declared
    # allocation and the run-start spend are part of the manifest the cell is stamped with.
    try:
        gate = build_cap_gate(cfg, fixture, arm, rows_path)
    except CapUsageError as exc:
        print(f"CAP GATE USAGE: {exc} — the run did not start, no request was sent",
              file=sys.stderr)
        return 3
    except CapRowsUnreadable as exc:
        print(f"CAP GATE ROWS: {exc}", file=sys.stderr)
        print("CAP GATE ROWS: nothing counted — an unreadable row file makes the spent "
              "total unknowable; no request was sent", file=sys.stderr)
        return 5
    if cfg.resume and rows and os.path.exists(manifest_path):
        with open(manifest_path, "rb") as fh:
            data = fh.read()
        manifest_sha = sha256_bytes(data)
        # The cap-gate addendum written at exit names the sha the ROWS were stamped with,
        # so a resume after that addendum is still verifying the same frozen manifest.
        try:
            frozen_sha = (((json.loads(data.decode("utf-8")) or {}).get("cap_gate") or {})
                          .get("frozen_sha256"))
        except (ValueError, AttributeError):
            frozen_sha = None
        stamped = rows[0].get("run_manifest_sha256")
        if stamped != manifest_sha and stamped != frozen_sha:
            print(f"RESUME REFUSED: manifest {manifest_path} sha {manifest_sha} does not match the "
                  f"rows ({stamped})", file=sys.stderr)
            return 5
        print(f"resume: reusing frozen manifest {manifest_path} sha256={manifest_sha}")
    else:
        try:
            data, manifest_sha = write_manifest(
                manifest_path,
                build_manifest(cfg, fixture, arm, rep, run_id, rows_path,
                               cap_gate=gate.manifest_block()))
        except OSError as exc:
            print(f"MANIFEST ABORT: cannot write {manifest_path}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            print("MANIFEST ABORT: the run did not start — no request was sent (Consonance: no "
                  "frozen manifest, no result).", file=sys.stderr)
            return 3
        print(f"manifest: {manifest_path} ({len(data)} B) sha256={manifest_sha}")
    print(f"cap-gate: allocation={gate.allocation} cap={gate.cap} reserve={gate.reserve} "
          f"spent_at_start={gate.spent_at_start} headroom={gate.headroom} "
          f"files={len(gate.paths)} (per-request brake armed before the first send)")

    planner = Planner(arm, fixture, dry_run=False)
    start = 1
    if rows:
        start = resume_start(rows) + 1
        planner.replay(rows)
        print(f"resume: cell has turns 1..{start - 1}; continuing at {start}")
    n_turns = cell_turns(cfg, fixture)
    # The cell's structural request projection.  It is ALSO the default allocation, so the
    # in-memory brake and the old `sent >= budget` abort cannot disagree about the ceiling.
    budget = projected_requests(cfg, fixture, arm)
    sent = 0
    fetch_rounds_used = 0
    fetch_cache: dict = {}
    # PROBE-CP3-V6 (b): the per-turn cap, and the follow-up REQUEST allowance that funds
    # every round (billed or prompt-served) without letting a burst starve the checkpoints.
    per_turn_cap = fetch_rounds_per_turn(cfg)
    cp_turns = checkpoint_turns(fixture)
    followup_pool = fetch_rounds_per_arm(cfg)
    followups_bought = followups_spent(rows) if tools_enabled(cfg) else 0
    if tools_enabled(cfg) and rows:
        # DURABLE ROUND COUNTING.  `--resume` used to reset this to 0, so a resumed arm
        # executed 20 fetches while the counter reported 8/8.  Every follow-up row is
        # fsync'd, so the cell's own rows are the ledger; the frozen manifest's counter
        # is honoured too and the LARGER of the two wins, so neither a reset manifest
        # nor a short row file can re-open the round budget.
        derived = fetch_rounds_spent(rows)
        frozen = 0
        try:
            with open(manifest_path, "rb") as fh:
                frozen = int(((json.load(fh) or {}).get("tools") or {})
                             .get("fetch_rounds_used") or 0)
        except (OSError, ValueError, TypeError, AttributeError):
            frozen = 0
        fetch_rounds_used = max(frozen, derived)
        print(f"resume: fetch rounds already spent={fetch_rounds_used}/"
              f"{fetch_rounds_per_arm(cfg)} (manifest={frozen} derived_from_rows={derived}); "
              "--resume does not reset the counter")

    wall_cap = float(getattr(cfg, "turn_wall_cap", 0) or 0)
    runaway_turns = max(1, int(getattr(cfg, "runaway_turns", 2) or 2))
    # RUNAWAY-POLICY (docs/RUNAWAY-POLICY.md): two DIFFERENT events are counted
    # separately because they cost different things, and one former "runaway" is data.
    #   wall_runaways      -- a turn whose stream --turn-wall-cap CLOSED (client.py:530
    #                         raises TurnWallCap). This is the cost hazard the guard was
    #                         built for: the 16,384-token / 475,873 ms turn of
    #                         LIVE-SMOKE-CELL, now bounded per turn AND counted here.
    #   ceiling_violations -- a response that finished ABOVE --max-tokens, i.e. a server
    #                         that IGNORED the ceiling: unbounded tokens, no row-level
    #                         bound. Counted against the same limit.
    #   A `length` truncation AT the ceiling is NOT counted: it is bounded data
    #                         (measured: 2 turns of 27 in cell 1 of RUN-A*).
    wall_runaways = 0
    wall_runaway_turns = []
    ceiling_violations = 0
    ceiling_violation_turns = []

    def _runaway_detail():
        return ("wall-time runaways %d/%d [%s]; ceiling violations %d/%d [%s]"
                % (wall_runaways, runaway_turns,
                   "; ".join(wall_runaway_turns) or "none",
                   ceiling_violations, runaway_turns,
                   "; ".join(ceiling_violation_turns) or "none"))

    def _escalate(turn_no, exc, part, kind="turn"):
        # ONE loud line: the turn, its wall time, its completion tokens and the cap.
        print(f"RUNAWAY T{turn_no} ({kind}): wall={exc.wall_s:.1f}s "
              f"completion_tokens={part.get('completion_tokens')} "
              f"cap={wall_cap:.1f}s — stream CLOSED, turn ABORTED, row recorded "
              f"error=turn_wall_cap truncated=true "
              f"(wall-time runaways {wall_runaways}/{runaway_turns})",
              file=sys.stderr)

    def _ceiling_violation(row):
        """Predicate 2, NARROWED BY RUNAWAY-POLICY: a response ABOVE the ceiling.

        A `length` truncation AT the ceiling (`truncated` and completion_tokens ==
        cfg.max_tokens) is DATA, not a runaway: the turn finished inside
        --turn-wall-cap, spent exactly max_tokens, and the row records
        ``stop_reason=length`` so a grader marks that answer wrong or absent. The other
        47 turns are unaffected by it. Measured: 2 of 27 turns in cell 1 of RUN-A*.

        What STILL counts is the server IGNORING the ceiling (completion_tokens >
        cfg.max_tokens): unbounded tokens with no row-level bound on cost. See
        docs/RUNAWAY-POLICY.md, option B.
        """
        comp = int(row.get("completion_tokens") or 0)
        ceiling = int(cfg.max_tokens)
        if comp > ceiling:
            return ("completion_tokens %d EXCEEDED the max_tokens ceiling %d"
                    % (comp, ceiling))
        return None

    for t in range(start, n_turns + 1):
        info = planner.build(t)
        turn = info["turn"]
        # The fixture marks a checkpoint with kind == "checkpoint" and names it in
        # fixture["checkpoints"], not with a per-turn "checkpoint" key: reading only
        # turn.get("checkpoint") left is_checkpoint False on every row (found here at T12).
        declared = next((c for c in fixture.get("checkpoints") or []
                         if int(c.get("turn", -1)) == int(t)), None)
        is_answer_turn = int(t) in cp_turns
        if is_answer_turn:
            # ANSWER-CONTRACT (v5): the checkpoint question arrives now, and the turn
            # itself says the tools are off. The injected text carries no expected value.
            info["prompt"] = checkpoint_prompt(fixture, t, info["prompt"])
        extras = {"is_checkpoint": bool(turn.get("checkpoint")) or turn.get("kind") == "checkpoint"
                  or declared is not None,
                  "checkpoint": turn.get("checkpoint") or declared,
                  "answer_turn": is_answer_turn,
                  "lease": info.get("lease"), "evicted": info.get("evicted"),
                  # TREATMENTS: compaction is visible on the TURN row it happened on; the
                  # `kind == "digest"` rows stay exactly as they were (this adds, never
                  # replaces), so a reader filtering turn rows can still see the wall.
                  "digest_at": t if info["digest_request"] is not None else None}
        digest_attempts = 0
        while info["digest_request"] is not None and digest_attempts < 2:
            if sent >= budget:
                print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                      file=sys.stderr)
                return 4
            msg = info["digest_request"]
            try:
                gate.acquire(t, "digest")
            except CapRefusal as exc:
                return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
            try:
                resp = send_chat(cfg, msg)
            except client.TurnWallCap as exc:
                sent += 1
                part = exc.as_response(cfg)
                wall_runaways += 1
                wall_runaway_turns.append("T%d (digest, wall %.1fs > cap %.1fs)"
                                          % (t, exc.wall_s, wall_cap))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, part, part["content"], "digest",
                    manifest_sha,
                    dict(extras, error="turn_wall_cap", prompt_sha256=sha256_text(
                        msg[1]["content"]), turn_wall_cap_s=wall_cap,
                         runaway_abort=True)))
                _escalate(t, exc, part, "digest")
                print(f"RUNAWAY ABORT after T{t}: a planning request ran past the wall "
                      f"cap; {_runaway_detail()}; {t}/{n_turns} turns reached, partial "
                      f"rows kept at {rows_path}", file=sys.stderr)
                return 6
            except RequestFailure as exc:
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "digest", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         prompt_sha256=sha256_text(msg[1]["content"]))))
                print(f"TURN FAILED (digest) T{t}: {exc} — cell stopped, failure row recorded",
                      file=sys.stderr)
                return 4
            sent += 1
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "digest", manifest_sha,
                dict(extras, prompt_sha256=sha256_text(msg[1]["content"]))))
            print(f"  [T{t}] digest request sent (prompt_tokens={resp['prompt_tokens']})")
            planner.digest = resp["content"]
            planner.raw = planner.raw[-4:]
            digest_attempts += 1
            info = planner.build(t)

        if sent >= budget:
            print(f"BUDGET ABORT at T{t}: {sent} requests already sent (budget {budget})",
                  file=sys.stderr)
            return 4
        # WIRE-CAP-GATE: the per-request brake, immediately BEFORE the wire.  Not per-run:
        # a run-level preflight cannot see the mid-run divergence (6 vs 130 on dbed0e9d).
        try:
            gate.acquire(t, "turn")
        except CapRefusal as exc:
            return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
        try:
            resp = send_chat(cfg, planner.messages(info["prompt"]))
        except client.TurnWallCap as exc:
            # TASK 2: past --turn-wall-cap the stream is closed by the client's context
            # manager; the partial fold is recorded, the turn aborted, and the cell ends
            # with exit 6 once --runaway-turns WALL-TIME runaways have been seen.
            sent += 1
            part = exc.as_response(cfg)
            wall_runaways += 1
            wall_runaway_turns.append("T%d (wall %.1fs > cap %.1fs)"
                                      % (t, exc.wall_s, wall_cap))
            fail_extra = dict(extras, error="turn_wall_cap",
                              prompt_sha256=sha256_text(info["prompt"]),
                              turn_wall_cap_s=wall_cap)
            if wall_runaways >= runaway_turns:
                # STOP-REASON-HOLES: the row that ENDS the run on --runaway-turns is a
                # runaway abort; a capped turn that the run survives stays turn_wall_cap.
                fail_extra["runaway_abort"] = True
            if is_answer_turn:
                fail_extra.update(checkpoint_answer_fields(None))
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, part, part["content"], "turn",
                manifest_sha, fail_extra))
            _escalate(t, exc, part)
            if wall_runaways >= runaway_turns:
                print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; "
                      f"{sent} request(s) sent, {t}/{n_turns} turns reached, partial "
                      f"rows kept at {rows_path}", file=sys.stderr)
                return 6
            continue
        except RequestFailure as exc:
            fail_extra = dict(extras, http_status=exc.status, error=str(exc),
                              prompt_sha256=sha256_text(info["prompt"]))
            if is_answer_turn:
                fail_extra.update(checkpoint_answer_fields(None))
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, None, None, "turn", manifest_sha,
                fail_extra))
            print(f"TURN FAILED T{t}: {exc} — cell stopped, failure row recorded", file=sys.stderr)
            return 4
        sent += 1
        # FETCH-CHANNEL: if the turn asked for the exact lines it needs, serve them.
        # The FINAL response of the turn is what the row records and what the planner
        # replays, so a checkpoint answer lives on the checkpoint turn's own row;
        # every follow-up request is appended BEFORE that row with kind="tool-followup"
        # and fetch_followup=true, so `by_turn[t]` still resolves to the real answer.
        turn_calls: list[dict] = []
        followup_rows: list[dict] = []
        rounds_this_turn = 0
        prompt_serves = 0
        # ROW-ATTRIBUTION (docs/ROW-MODEL.md): hold the INITIAL send's own response
        # object.  `fetch_rounds` rebinds `resp` to the last follow-up, so without this
        # reference the turn's first request would leave no measurement of its own --
        # the defect DEDUPE-ROOT-CAUSE proved.  Never reassigned.
        initial_resp = resp
        if tools_enabled(cfg) and not is_answer_turn:
            # ANSWER-CONTRACT (v5): tools are unavailable on a checkpoint turn, so no
            # <tool_call> is executed and no follow-up request is bought.
            pinned = pinned_views(fixture, info["prompt"])

            def _may_request(_t=t):
                # Pool of follow-up requests, minus one held back for every declared
                # checkpoint this cell has not reached yet: a T3 recon burst may spend
                # the slack, never T46's last request.
                reserved = sum(1 for ct in cp_turns if ct > _t)
                return followups_bought + reserved < followup_pool

            try:
                (_m, resp, sent, fetch_rounds_used, turn_calls,
                 followup_rows) = fetch_rounds(
                    cfg, fixture, arm, rep, run_id, t, manifest_sha, extras,
                    planner.messages(info["prompt"]), resp, sent, budget, fetch_rounds_used,
                    fetch_cache, pinned, per_turn_cap, _may_request, gate)
                followups_bought += len(followup_rows)
                rounds_this_turn = len(followup_rows)
                prompt_serves = sum(1 for c in turn_calls
                                    if c.get("served_from") == "prompt")
            except CapRefusal as exc:
                # The refusal lands MID-turn: this turn's own request already reached the
                # wire and is billed, so its row is written before the run stops — rows
                # written stay equal to the requests legitimately made.
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, resp, resp.get("content"), "turn",
                    manifest_sha, dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                                       cap_refused_mid_turn=True)))
                return _cap_stop(exc, gate, manifest_path, manifest_sha, rows_path)
            except BudgetExhausted as exc:
                print(f"BUDGET ABORT at T{t}: {exc}", file=sys.stderr)
                return 4
            except client.TurnWallCap as exc:
                sent += 1
                part = exc.as_response(cfg)
                wall_runaways += 1
                wall_runaway_turns.append("T%d (tool-followup, wall %.1fs > cap %.1fs)"
                                          % (t, exc.wall_s, wall_cap))
                # ROW-ATTRIBUTION: the turn's initial send already reached the wire and
                # is measured on its own row ahead of the wall-capped follow-up's.
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha,
                    dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                         send_index=0, initial_send=True,
                         row_measurement_source="turn-initial",
                         next_request_kind="tool-followup")))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, part, part["content"],
                    "tool-followup", manifest_sha,
                    dict(extras, error="turn_wall_cap", fetch_followup=True,
                         turn_wall_cap_s=wall_cap,
                         **({"runaway_abort": True}
                            if wall_runaways >= runaway_turns else {}))))
                _escalate(t, exc, part, "tool-followup")
                if wall_runaways >= runaway_turns:
                    print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; "
                          f"{t}/{n_turns} turns reached, partial rows kept at "
                          f"{rows_path}", file=sys.stderr)
                    return 6
                continue
            except RequestFailure as exc:
                # ROW-ATTRIBUTION: the initial send is measured even when the follow-up
                # that failed ended the cell; a failed follow-up has no measurement.
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, initial_resp,
                    initial_resp.get("content") if initial_resp else None,
                    "turn-initial", manifest_sha,
                    dict(extras, prompt_sha256=sha256_text(info["prompt"]),
                         send_index=0, initial_send=True,
                         row_measurement_source="turn-initial",
                         next_request_kind="tool-followup")))
                append_row(rows_path, make_row(
                    cfg, fixture, arm, rep, run_id, t, None, None, "tool-followup", manifest_sha,
                    dict(extras, http_status=exc.status, error=str(exc),
                         fetch_followup=True)))
                print(f"TURN FAILED (fetch follow-up) T{t}: {exc} — cell stopped, failure row "
                      "recorded", file=sys.stderr)
                return 4
        row_extra = dict(extras, prompt_sha256=sha256_text(info["prompt"]))
        # ROW-ATTRIBUTION: ONE ROW PER SEND.  With k >= 1 follow-ups this turn made
        # k+1 requests: the initial send (row_initial, below), follow-ups 1..k-1
        # (their own ``kind="tool-followup"`` rows) and follow-up k, whose row IS this
        # turn row.  The row count is unchanged from the pre-fix writer (k+1), but no
        # two rows now share one measurement: the last follow-up is no longer written
        # twice (once as tool-followup, once mirrored here).
        attributed = bool(followup_rows) and attribute_initial_send()
        row_extra["send_index"] = len(followup_rows)
        row_extra["row_measurement_source"] = (
            "tool-followup" if followup_rows else "turn-initial")
        if attributed:
            # This row stands in the last follow-up request's slot, so the durable
            # markers that request carried ride here: fetch_rounds_spent counts
            # ``fetch_followup`` rows, and resume must not lose the last round.
            last = followup_rows[-1]
            row_extra["fetch_followup"] = True
            row_extra["fetch_round_final"] = True
            row_extra["final_round_billed"] = last.get("billed_round")
            row_extra["final_round_prompt_served"] = last.get("prompt_served")
        if is_answer_turn:
            row_extra.update(checkpoint_answer_fields(resp))
        if tools_enabled(cfg) and not is_answer_turn:
            row_extra["tool_calls"] = turn_calls
            row_extra["fetch_rounds_used"] = fetch_rounds_used
            row_extra["fetch_rounds_this_turn"] = rounds_this_turn
            row_extra["fetch_prompt_serves"] = prompt_serves
            row_extra["fetch_rounds_cap_per_turn"] = per_turn_cap
            suppressed = sum(1 for c in turn_calls if c.get("followup_suppressed"))
            if suppressed:
                # RECORD-STOP-REASON: a follow-up request the allowance refused writes no
                # row of its own; the count rides the turn row, whose stop_reason is the
                # response that ended the turn.
                row_extra["fetch_suppressed"] = suppressed
        row = make_row(cfg, fixture, arm, rep, run_id, t, resp, resp["content"], "turn", manifest_sha,
                       row_extra)
        # STOP-REASON-HOLES: predicate 2 (the ceiling-consume signature) ends the cell on
        # --runaway-turns.  The row that ends it is a runaway abort, not a plain length
        # stop, so it is labelled before it is written (no historical row is touched).
        signature = _ceiling_violation(row)
        if signature and ceiling_violations + 1 >= runaway_turns:
            row["stop_reason"] = client.STOP_REASON_RUNAWAY_TURN
            row["truncated"] = client.truncated_for(row["stop_reason"])
            row["runaway_abort"] = True
        if attributed:
            # ROW-ATTRIBUTION: the initial send's own row, written in wire order ahead
            # of the follow-ups it triggered.  It is the ONLY row that measures the
            # turn's own request; ``kind="turn-initial"`` never existed before, so no
            # historical row is re-meant and no historical file is touched.
            initial_extra = dict(
                extras, prompt_sha256=sha256_text(info["prompt"]),
                send_index=0, initial_send=True,
                row_measurement_source="turn-initial",
                fetch_rounds_this_turn=len(followup_rows),
                next_request_kind="tool-followup")
            if is_answer_turn:
                initial_extra.update(checkpoint_answer_fields(initial_resp))
            append_row(rows_path, make_row(
                cfg, fixture, arm, rep, run_id, t, initial_resp,
                initial_resp.get("content") if initial_resp else None,
                "turn-initial", manifest_sha, initial_extra))
        # follow-ups 1..k-1 get their own rows; follow-up k's row is the turn row below.
        for frow in (followup_rows[:-1] if attributed else followup_rows):
            append_row(rows_path, frow)
        append_row(rows_path, row)
        planner.record(t, resp["content"])
        # RUNAWAY-POLICY predicate 2: only a response ABOVE the ceiling counts. A
        # `length` truncation AT the ceiling is data and falls straight through.
        if signature:
            ceiling_violations += 1
            ceiling_violation_turns.append("T%d (%s)" % (t, signature))
            print(f"RUNAWAY T{t}: {signature} — a server that ignored the max_tokens "
                  f"ceiling (ceiling violations {ceiling_violations}/{runaway_turns})",
                  file=sys.stderr)
            if ceiling_violations >= runaway_turns:
                print(f"RUNAWAY ABORT after T{t}: {_runaway_detail()}; {sent} request(s) "
                      f"sent, {t}/{n_turns} turns reached, partial rows kept at "
                      f"{rows_path}", file=sys.stderr)
                return 6
        print(f"  [T{t}] prompt={row['prompt_tokens']} cached={row['cached_tokens']} "
              f"ttft_ms={row['ttft_ms']} src={row['content_source']} "
              f"finish={row['finish_reason']} stop={row['stop_reason']} "
              f"truncated={row['truncated']} "
              f"lat={row['latency_s']} comp={row['completion_tokens']}")
        if is_answer_turn:
            print(f"  [T{t}] answer_contract kind={row['answer_kind']} "
                  f"value={row['answer_value']!r} error={row['answer_parse_error']}")
        if tools_enabled(cfg) and turn_calls:
            done = sum(1 for c in turn_calls if c.get("executed"))
            print(f"  [T{t}] tool_calls={len(turn_calls)} executed={done} "
                  f"fetch_followups={len(followup_rows)} fetch_rounds_used={fetch_rounds_used}"
                  f"/{fetch_rounds_per_arm(cfg)} prompt_served={prompt_serves} "
                  f"rounds_this_turn={rounds_this_turn}/{per_turn_cap if per_turn_cap else 'inf'} "
                  f"requests_sent={sent} followups={followups_bought}/{followup_pool}")
    if tools_enabled(cfg):
        print(f"requests_sent={sent} (budget {budget}; fetch rounds "
              f"{fetch_rounds_used}/{fetch_rounds_per_arm(cfg)})")
    # WIRE-CAP-GATE: reconcile the run's own count against the rows the next run will read.
    _rec, cap_rc = _gate_finish(gate, manifest_path, manifest_sha, rows_path)
    return cap_rc
```

**E-_gate_finish** — `experiments/ptr-engine/longrun/run_longrun.py:516-575`

```python
def _gate_finish(gate: RequestCapGate, manifest_path: str | None, manifest_sha: str | None,
                 rows_path: str) -> tuple[dict, int]:
    """Reconcile at exit, write the final counts into the run manifest, return (rec, rc)."""
    try:
        rec = gate.reconcile()
    except CapRowsUnreadable as exc:
        print(f"CAP GATE ROWS at exit: {exc}", file=sys.stderr)
        return {"delta": None, "error": str(exc)}, 5
    print(f"cap-gate: allocation={gate.allocation} cap={gate.cap} reserve={gate.reserve} "
          f"spent_at_start={gate.spent_at_start} used_in_run={gate.used_in_run} "
          f"spent_after={rec['spent_after']} delta={rec['delta']}", file=sys.stderr)
    rc = 0
    if manifest_path and os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            prior = ((doc.get("cap_gate") or {}).get("frozen_sha256"))
            block = gate.manifest_block(reconciled=rec)
            # The addendum names the bytes the ROWS were stamped with, so a later
            # --resume can still verify the frozen manifest it started from.
            block["frozen_sha256"] = prior or manifest_sha
            doc["cap_gate"] = block
            data, final_sha = write_manifest(manifest_path, doc)
            print(f"cap-gate: final counts recorded in {manifest_path} "
                  f"({len(data)} B) sha256={final_sha}", file=sys.stderr)
        except (OSError, ValueError, TypeError) as exc:
            print(f"CAP GATE MANIFEST: cannot record the final counts in {manifest_path}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            rc = EXIT_CAP_DIVERGENCE
    if rec["delta"] > 0:
        # A row no request bought: the ledger and the run disagree about MONEY.  This is a
        # bug, not a rounding, and it fails the run.
        print(f"CAP GATE RECONCILE DIVERGENCE (delta=+{rec['delta']}): the run counted "
              f"{gate.used_in_run} request(s) but the rows gained "
              f"{rec['spent_after'] - rec['spent_at_start']} (spent_at_start="
              f"{rec['spent_at_start']} spent_after={rec['spent_after']} rows={rows_path}). "
              f"A divergence is a bug, not a rounding error.", file=sys.stderr)
        rc = EXIT_CAP_DIVERGENCE
    elif rec["delta"] < 0:
        # Requests that reached the wire whose rows could not be written before the run
        # stopped (a refusal can land mid-turn).  That makes the ledger UNDERSTATE the
        # spend, so the next gate check would see more headroom than exists: this is a
        # refusal (exit 9), not a printout.  Anything else lets a run walk past the gate
        # by dropping a row.
        headroom_before = gate.cap - gate.reserve - rec["spent_at_start"]
        headroom_after = gate.cap - gate.reserve - rec["spent_after"]
        print(f"CAP GATE UNRECORDED (delta={rec['delta']}) — refusing, exit "
              f"{EXIT_CAP_DIVERGENCE}: {-rec['delta']} request(s) reached the wire but "
              f"their rows were not written before the run stopped "
              f"(used_in_run={gate.used_in_run} rows_gained="
              f"{rec['spent_after'] - rec['spent_at_start']} headroom_before="
              f"{headroom_before} headroom_after={headroom_after} rows={rows_path}); "
              f"rows were not persisted, so the ledger cannot be trusted for the next "
              f"check — it would grant {-rec['delta']} request(s) beyond the true "
              f"headroom.", file=sys.stderr)
        rc = EXIT_CAP_DIVERGENCE
    else:
        print(f"cap-gate: reconciled — the run's count {gate.used_in_run} equals the rows "
              f"gained {rec['spent_after'] - rec['spent_at_start']} (delta 0)", file=sys.stderr)
    return rec, rc
```

**E-make_row** — `experiments/ptr-engine/longrun/run_longrun.py:1781-1970`

```python
def make_row(cfg, fixture, arm, rep, run_id, t, resp, content, kind, manifest_sha, extra):
    if resp is None:
        # A failed turn has no measurement: null, never a measured zero.
        cached, cached_normalized, prompt, uncached = None, None, None, None
    else:
        # The client's seam value is authoritative and is carried UNCHANGED: a measured
        # 0 stays 0, an unattributed None stays null (never imputed). The legacy
        # null-semantics reading is preserved beside it as ``cached_tokens_normalized``
        # so rows written before the wiring keep a comparable column.
        cached = resp.get("cached_tokens")
        cached_normalized = normalize_cached_tokens(resp.get("raw_cached"), cfg.engine)
        prompt = resp.get("prompt_tokens")
        uncached = None if (prompt is None or cached is None) else int(prompt) - int(cached)
    expected, cp_question = checkpoint_expected(fixture, t)
    # RECORD-STOP-REASON: WHY this ended, one closed-vocabulary word, and ``truncated``
    # derived FROM it so the two can never disagree.  null only when no response exists.
    stop_reason = stop_reason_for_row(resp, extra)
    truncated = None if resp is None else client.truncated_for(stop_reason)
    if resp is None:
        # A failed request is a failed turn with no channel measurement.
        content_raw = reasoning_raw = ""
        r_tok = c_tok = None
        tok_method = None
        answer_source = "none"
        failed_turn = True
        expected_present = False
        answer_verified = None
    else:
        content_raw = resp.get("content_raw") or ""
        reasoning_raw = resp.get("reasoning") or ""
        bpt = float(fixture.get("bytes_per_token") or 4.0477)
        c_tok, tok_method = count_channel_tokens(content_raw, bpt)
        r_tok, _ = count_channel_tokens(reasoning_raw, bpt)
        expected_present = bool(contains_expected(reasoning_raw, expected)) if expected else False
        content_has_expected = bool(contains_expected(content_raw, expected)) if expected else False
        if content_raw.strip():
            answer_source = "content"
        elif reasoning_raw.strip() and (not truncated or expected_present):
            # Reasoning-only completion: usable ONLY when it finished, or when it
            # literally carries the checkpoint's expected value.  Marked, not clean.
            answer_source = "reasoning-fallback"
        else:
            answer_source = "none"
        # "length" without the expected value is an incomplete answer = failed turn,
        # on either channel; it must never enter a latency average as a success.
        failed_turn = bool(truncated and not (expected_present or content_has_expected))
        answer_verified = (bool(content_has_expected or expected_present)
                           if expected is not None else None)
    # RECORD-STOP-REASON item 3: when a ceiling/empty/HTTP stop left NO usable content,
    # the row carries the sha of whatever content it has (the EMPTY string's sha when
    # there is none) and a completion count, so an empty generation is self-evident
    # without cross-file arithmetic.  ``stop_evidence`` marks that reading.
    no_usable_content = not ((content_raw or "").strip() or (reasoning_raw or "").strip())
    stop_evidence = bool(no_usable_content and stop_reason in (
        client.STOP_REASON_LENGTH, client.STOP_REASON_EMPTY, client.STOP_REASON_HTTP_ERROR))
    if content is not None:
        recorded_content = content
    else:
        recorded_content = "" if stop_evidence else None
    completion_recorded = resp.get("completion_tokens") if resp else None
    if stop_evidence and completion_recorded is None:
        # no stream ever delivered a usage chunk: the count is what the CLIENT observed (0)
        completion_recorded = 0
    # CLAIM-ROW-STAMP: the claim decision reaches EVERY row literal built here --
    # turn-initial, turn, tool-followup and failure rows alike. A cfg without a
    # resolved claim (a direct make_row call) is stamped the conservative
    # non-comparable shape, never a comparable one.
    claim_fields = (claim_mode.row_fields(cfg.claim)
                    if getattr(cfg, "claim", None)
                    else {"claim": claim_mode.CLAIM_NONE,
                          "comparison_eligible": False})
    row = {
        "arm": arm, **claim_fields, "task_id": fixture["task_id"], "rep": rep, "turn": t,
        "prompt_tokens": prompt,
        "cached_tokens": cached,
        "uncached_tokens": uncached,
        "ttft_s": round(resp["ttft_s"], 6) if resp and resp.get("ttft_s") is not None else None,
        "latency_s": round(resp["latency_s"], 6) if resp else None,
        "completion_tokens": completion_recorded,
        "content_sha256": (sha256_text(recorded_content)
                           if recorded_content is not None else None),
        # REQUEST-IDENTITY (docs/REQUEST-IDENTITY.md): what was SENT, beside the hash of
        # what came back.  ``request_sha256`` is the client's sha256 over the exact wire
        # bytes; a response that was recorded twice from ONE send carries the same value
        # on both rows.  A row whose body was not retained says ``unknown`` and false --
        # never a guess.  Deliberately absent from every rows file written before this
        # field existed; history is NOT backfilled.
        "request_sha256": (resp.get("request_sha256")
                           if resp and resp.get("request_sha256")
                           else client.REQUEST_SHA_UNKNOWN),
        "request_identity_complete": bool(resp and resp.get("request_identity_complete")),
        "content": content,
        "fixture_sha256": fixture["_sha256"],
        "run_manifest_sha256": manifest_sha,
        "token_source": resp.get("token_source") if resp else "absent",
        "ts": iso(utc_now()),
        # extras (analysis may use; never replace the contracted keys)
        # instrument-fix fields: TTFT per row, both channels, truncation provenance
        "ttft_ms": resp.get("ttft_ms") if resp else None,
        # WIRE-CLIENT seam v1: carried from the client unchanged, exact names. A null
        # ttft_ms with ttft_source="unavailable" must reach the row as null -- wall_ms is
        # reported separately and is NEVER substituted for it.
        "ttft_source": resp.get("ttft_source") if resp else None,
        "first_token_kind": resp.get("first_token_kind") if resp else None,
        "cached_source": resp.get("cached_source") if resp else None,
        "cached_tokens_normalized": cached_normalized,
        "engine_metrics_before": resp.get("engine_metrics_before") if resp else None,
        "engine_metrics_after": resp.get("engine_metrics_after") if resp else None,
        "wall_ms": resp.get("wall_ms") if resp else None,
        "metrics_scrape": client.resolve_metrics_scrape(cfg),
        "content_source": resp.get("content_source") if resp else None,
        "reasoning": resp.get("reasoning") if resp else None,
        "reasoning_sha256": sha256_text(resp["reasoning"]) if resp and resp.get("reasoning") else None,
        "finish_reason": resp.get("finish_reason") if resp else None,
        # RECORD-STOP-REASON: the closed vocabulary, the per-choice finish reasons, and the
        # ceiling AS SENT on the request -- a 128-token cap stop is now readable here.
        "finish_reasons": resp.get("finish_reasons") if resp else None,
        "stop_reason": stop_reason,
        "truncated": truncated,
        # STOP-REASON-HOLES: rule 3 must be computable from the row ALONE.  The ceiling
        # as sent wins; the configured cap is the only fallback, never None.
        "max_tokens": (resp.get("max_tokens")
                       if (resp is not None and resp.get("max_tokens") is not None)
                       else int(cfg.max_tokens)),
        "stop_evidence": stop_evidence,
        "completion_tokens_source": (
            "usage" if (resp is not None and resp.get("completion_tokens") is not None)
            else ("client_observed" if stop_evidence else None)),
        # reasoning-policy fields: per-channel split, the verdict, and its provenance
        "reasoning_tokens": r_tok,
        "content_tokens": c_tok,
        "channel_token_method": tok_method,
        "answer_source": answer_source,
        "failed_turn": bool(failed_turn),
        "timing_usable": bool(resp is not None and resp.get("ttft_ms") is not None
                              and not failed_turn),
        "expected": expected,
        "expected_question": cp_question,
        "expected_present": expected_present,
        "answer_verified": answer_verified,
        "reasoning_policy": _REASONING_POLICY,
        "stream": bool(cfg.stream),
        # thinking switch: rows from different settings must NEVER be pooled; a later
        # analysis must be able to read the setting from the row alone.
        "thinking": thinking_setting(cfg),
        "run_id": run_id, "engine": cfg.engine, "kind": kind,
        "is_checkpoint": bool(extra.get("is_checkpoint")), "checkpoint": extra.get("checkpoint"),
        "cached_reported": bool(resp and resp.get("raw_cached") is not None),
        "usage_missing": bool(resp and resp.get("usage_missing")),
        "lease": extra.get("lease"), "evicted": extra.get("evicted"),
        # TREATMENTS: the turn a digest was requested on (null on every other row), written
        # beside `evicted` so compaction is visible WITHOUT a `kind == "digest"` row.
        "digest_at": extra.get("digest_at"),
        "prompt_sha256": extra.get("prompt_sha256"),
        "http_status": extra.get("http_status"), "error": extra.get("error"),
    }
    # ANSWER-CONTRACT (v5): the five contracted fields are ALWAYS present, so a
    # checkpoint cell is machine-decidable from the row alone (null on a non-answer turn).
    row["answer_turn"] = bool(extra.get("answer_turn"))
    row["answer_kind"] = extra.get("answer_kind")
    row["answer_value"] = extra.get("answer_value")
    row["answer_raw"] = extra.get("answer_raw")
    row["answer_parse_error"] = extra.get("answer_parse_error")
    if extra.get("fetch_followup"):
        # FETCH-CHANNEL: a follow-up model request served a tool result (real request).
        row["fetch_followup"] = True
    if extra.get("tool_calls") is not None:
        row["tool_calls"] = extra["tool_calls"]
    if extra.get("fetch_rounds_used") is not None:
        # FETCH-CHANNEL: durable round spend on a --tools row (absent on a tools-off row).
        row["fetch_rounds_used"] = extra["fetch_rounds_used"]
    # PROBE-CP3-V6: the (b) cap and the (a) no-bill split, readable from the row alone.
    for key in ("fetch_rounds_cap_per_turn", "fetch_rounds_this_turn", "fetch_prompt_serves",
                "billed_round", "prompt_served",
                # ROW-ATTRIBUTION: which HTTP request of the turn this row measured.
                "send_index", "initial_send", "row_measurement_source",
                "fetch_round_final", "final_round_billed", "final_round_prompt_served",
                "next_request_kind"):
        if extra.get(key) is not None:
            row[key] = extra[key]
    if extra.get("runaway_abort"):
        # STOP-REASON-HOLES: this row is the one that tripped --runaway-turns and ended
        # the cell; the harness event (`error`) stays the wall cap/signature that fired.
        row["runaway_abort"] = True
    # ROW-PROVENANCE: this row names what produced it -- arm, model, endpoint, fixture
    # identity, the harness digest, the ceiling, the thinking switch and the tool mode --
    # so a later analysis READS the era instead of inferring it from file mtimes.  An
    # absent value is the string "unknown" plus provenance_complete=false, never null.
    row.update(provenance_for(cfg, fixture, arm))
    return row
```

**E-append_row** — `experiments/ptr-engine/longrun/run_longrun.py:1998-2013`

```python
def append_row(path: str, row: dict) -> None:
    # ROW-SEQ: one integer per WRITE POSITION in the file, assigned once per row object.
    # A double append of one request is visible as two lines sharing ``request_sha256``
    # AND ``row_seq``; a genuine re-send keeps the same request hash but is a NEW row and
    # takes the next integer.
    key = os.path.abspath(path)
    if "row_seq" in row:
        # The same row object written a second time: keep its seq (that is the evidence).
        _ROW_SEQ[key] = max(_row_seq_high_water(path), int(row["row_seq"]))
    else:
        row["row_seq"] = _row_seq_high_water(path) + 1
        _ROW_SEQ[key] = row["row_seq"]
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
```

**E-stage_grade** — `experiments/ptr-engine/longrun/cell.py:1648-1667`

```python
def stage_grade(args, rows_path, out_dir, stamp):
    grade_path = os.path.join(out_dir, "cell-%s-%s.grade-v5.json" % (args.arm, stamp))
    argv = [sys.executable, GRADER, "--rows", rows_path, "--fixture", args.fixture,
            "--out", grade_path]
    rc, out, err = _run(argv, purpose="other", phase="5/7 grade", label="grade_v5")
    detail = {"argv": argv, "exit": rc, "output": (out or "").splitlines(),
              "stderr": (err or "").splitlines()[-20:],
              "grade_path": _repo_rel(grade_path)}
    if rc != 0:
        raise Abort(10, "5/7 grade", "grade_v5.py exited %d: %s"
                    % (rc, (err or out or "").strip()))
    verdicts = {}
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("acc=") or " acc=" in line:
            parts = line.split()
            if parts:
                verdicts[parts[0]] = line
    detail["verdicts"] = verdicts
    return detail
```

**E-derive_truth** — `experiments/ptr-engine/longrun/grade_v5.py:553-583`

```python
def derive_truth(fixture):
    """Per-checkpoint truth, each with the AST derivation that establishes it."""
    paths = _source_map(fixture)
    resolve_path, errors_path = paths["resolve.py"], paths["errors.py"]
    rt, rsha = dv.parse_module(resolve_path)
    et, esha = dv.parse_module(errors_path)
    cache = {resolve_path: (rt, rsha), errors_path: (et, esha)}
    out = []
    for idx, cp in enumerate(fixture.get("checkpoints") or []):
        spec = cp.get("answer_spec") or {}
        kind = spec.get("kind")
        derive = spec.get("derive") or {}
        cid = str(cp.get("id") or ("cp.%d.t%s" % (idx, cp.get("turn"))))
        documented = cp.get("expected")
        cell = {"id": cid, "turn": int(cp.get("turn", -1)), "kind": kind,
                "documented_expected": documented, "elided_kwargs": []}
        try:
            _derive_one(cell, spec, kind, derive, cid, documented, paths, cache)
        except KeyError as exc:                       # never a bare KeyError
            _spec_error(cid, spec, "missing derive key %s" % exc,
                        derive.get("file") or resolve_path)
        shas = {"resolve.py": rsha, "errors.py": esha}
        for p, (_, sha) in sorted(cache.items()):
            base = os.path.basename(p)
            if base not in shas:
                shas[base] = sha
        cell["source_sha256"] = shas
        out.append(cell)
    if not out:
        raise SystemExit("fixture_truth_mismatch: fixture declares no checkpoints")
    return out
```

**E-stage_analyse** — `experiments/ptr-engine/longrun/cell.py:1671-1740`

```python
def stage_analyse(args, rows_path, out_dir, stamp, grade_path=None):
    json_path = os.path.join(out_dir, "cell-%s-%s.analysis.json" % (args.arm, stamp))
    argv = [sys.executable, ANALYZE, "--rows", rows_path, "--json", json_path]
    # The accuracy population is the GRADER's checkpoint cells, not the rows:
    # the analyser must consume grade_v5's verdicts, never re-derive them.
    if grade_path:
        argv += ["--grade", grade_path]
    rc, out, err = _run(argv, purpose="other", phase="6/7 analyse",
                        label="analyze_stats")
    if rc != 0:
        raise Abort(11, "6/7 analyse", "analyze_stats.py exited %d: %s"
                    % (rc, (err or out or "").strip()))

    doc = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except json.JSONDecodeError:
            doc = {}

    # The card's contract: per arm print n, dropped-null, p50, p95 WITH interval,
    # accuracy passed/decidable WITH Wilson interval; per pair a McNemar line or
    # its refusal. Anything unavailable must be a printed REFUSAL, never a number.
    checks, refusals = [], []
    for arm, entry in (doc.get("arms") or {}).items():
        checks.append({"arm": arm, "n_rows": entry.get("n_rows")})
        t = entry.get("ttft") or {}
        nulls = t.get("dropped_null")
        if nulls is None:
            refusals.append("arm %s: dropped-null count not reported" % arm)
        for key in ("p50", "p95"):
            est = entry.get(key) or {}
            if est.get("point") is not None and est.get("lo") is not None:
                checks.append({"arm": arm, key: {"point": est["point"],
                                                 "lo": est["lo"], "hi": est["hi"],
                                                 "n": est.get("n")}})
            elif est.get("refused"):
                refusals.append("arm %s %s: %s" % (arm, key, est["refused"]))
            else:
                refusals.append("arm %s %s: analyze_stats printed neither a number "
                                "nor a refusal" % (arm, key))
        acc = entry.get("accuracy") or {}
        if acc.get("decidable", 0) > 0:
            checks.append({"arm": arm, "accuracy": "%s/%s"
                           % (acc.get("passed"), acc.get("decidable"))})
            if "wilson95" not in (out or ""):
                refusals.append("arm %s accuracy: Wilson interval not printed" % arm)
        else:
            refusals.append("arm %s accuracy: no decidable turns (n=0)" % arm)
    for rec in doc.get("pairs") or []:
        if rec.get("mcnemar"):
            checks.append({"pair": "%s vs %s" % (rec.get("arm_a"), rec.get("arm_b")),
                           "mcnemar": rec["mcnemar"]})
        else:
            refusals.append("pair %s vs %s McNemar refused: %s"
                            % (rec.get("arm_a"), rec.get("arm_b"), rec.get("refused")))
    if not doc.get("arms"):
        refusals.append("analyze_stats reported no arms at all for %s"
                        % _repo_rel(rows_path))

    for line in refusals:
        print("cell:   REFUSAL %s" % line, flush=True)

    return {"argv": argv, "exit": rc, "output": (out or "").splitlines(),
            "stderr": (err or "").splitlines()[-20:],
            "analysis_path": _repo_rel(json_path), "checks": checks,
            "refusals": refusals,
            "populations": {arm: (entry.get("accuracy") or {})
                            for arm, entry in (doc.get("arms") or {}).items()}}
```

**E-turn_latency_rows** — `experiments/ptr-engine/longrun/analyze_stats.py:805-908`

```python
def turn_latency_rows(rows, meta_out=None):
    """THE per-turn TTFT selector -> (selected_rows, meta). Every latency path uses it.

    One row per TURN, never per send: `kind="turn-initial"` wins when the row
    model provides it; otherwise the legacy `kind="turn"` row is selected and the
    figure is labelled `definition_fallback: true`. `kind="tool-followup"` rows
    are always dropped (and counted), so a k-follow-up turn contributes exactly
    one sample rather than k+1.

    The meta record is what makes the definition machine-checkable:
        definition, definition_version, mode, definition_fallback,
        n_input, n_selected, explicit_initial_rows, fallback_rows,
        mirrored_rows, dropped_followup, dropped_turn_followup,
        dropped_duplicate, turns_without_turn_row, dropped_not_a_row,
        dropped_foreign_kind

    `mirrored_rows` is the subset of fallback rows that belong to a turn which
    ALSO has follow-up rows: those are the rows where the fallback is not merely
    unproven but known to quote the last this-turn send. A cell can therefore be
    fallback=TRUE with mirrored_rows=0 (a tools-off cell, unaffected in value).
    """
    meta = {
        "definition": TTFT_DEFINITION,
        "definition_version": TTFT_DEFINITION_VERSION,
        "mode": "empty",
        "definition_fallback": False,
        "n_input": 0, "n_selected": 0,
        "explicit_initial_rows": 0, "fallback_rows": 0, "mirrored_rows": 0,
        "dropped_followup": 0, "dropped_turn_followup": 0,
        "dropped_duplicate": 0,
        "turns_without_turn_row": 0, "dropped_not_a_row": 0,
        "dropped_foreign_kind": 0,
    }
    followup_turns = set()
    groups = {}          # key -> {"turn-initial": [rows], "turn": [rows]}
    unkeyed = []         # no turn identity: never merged with a keyed turn
    for row in rows or ():
        if not isinstance(row, dict):
            meta["dropped_not_a_row"] += 1
            continue
        meta["n_input"] += 1
        kind = row.get("kind")
        key = _turn_key(row)
        if kind == FOLLOWUP_ROW_KIND:
            meta["dropped_followup"] += 1
            if key is not None:
                followup_turns.add(key)
            continue
        if kind is not None and kind not in TURN_ROW_KINDS:
            meta["dropped_foreign_kind"] += 1
            continue
        if key is None:
            unkeyed.append(row)
            continue
        if kind == "turn" and row.get("send_index") not in (None, 0):
            # The one-row-per-send model writes the LAST follow-up as kind='turn'.
            meta["dropped_turn_followup"] += 1
        slot = groups.setdefault(key, {"turn-initial": [], "turn": []})
        slot["turn-initial" if kind == "turn-initial" else "turn"].append(row)

    selected = []
    for key, slot in groups.items():
        bucket = slot["turn-initial"] or slot["turn"]
        if not bucket:
            meta["turns_without_turn_row"] += 1
            continue
        meta["dropped_duplicate"] += len(bucket) - 1
        chosen = bucket[0]
        # The OTHER kind's row for this turn is a second send, not a duplicate
        # measurement: the last follow-up is written as kind='turn' in the
        # one-row-per-send model.
        for other in (slot["turn"] if slot["turn-initial"] else slot["turn-initial"]):
            if other.get("send_index") in (None, 0):
                meta["dropped_duplicate"] += 1
        selected.append(chosen)
        if slot["turn-initial"]:
            meta["explicit_initial_rows"] += 1
        else:
            meta["fallback_rows"] += 1
            if key in followup_turns:
                meta["mirrored_rows"] += 1
    # Rows with no turn identity cannot be attributed to a turn; they are kept
    # (a legacy single-send file may not carry `turn`) and counted as fallback,
    # because nothing proves they are a turn's own initial request.
    for row in unkeyed:
        selected.append(row)
        if row.get("kind") == "turn-initial":
            meta["explicit_initial_rows"] += 1
        else:
            meta["fallback_rows"] += 1

    meta["n_selected"] = len(selected)
    meta["definition_fallback"] = meta["fallback_rows"] > 0
    if not selected:
        meta["mode"] = "empty"
    elif meta["fallback_rows"] == 0:
        meta["mode"] = "turn-initial"
    elif meta["explicit_initial_rows"] == 0:
        meta["mode"] = "fallback-turn"
    else:
        meta["mode"] = "mixed"
    if meta_out is not None:
        meta_out.update(meta)
    return selected, meta
```

**E-quantile_ci** — `experiments/ptr-engine/longrun/analyze_stats.py:350-410`

```python
def quantile_ci(values, q, resamples=RESAMPLES, seed=SEED, stats=None):
    """Percentile-bootstrap interval for a quantile -> (point, lo, hi, n).

    `values` may contain None / NaN / inf (an unavailable first stream delta is
    NOT a zero): such entries are dropped, and the count is reported. Pass a
    dict as `stats` to receive it (and the rank span) without changing the
    4-tuple return:

        stats["dropped_null"]      number of null/non-finite entries dropped
        stats["input"]             entries supplied
        stats["used"]              n actually used (== returned n)
        stats["rank_span"]         (lo_rank, hi_rank) reference interval
        stats["rank_span_pct"]     the same span as percentages
        stats["resamples"]         bootstrap resamples drawn

    Raises `InsufficientSamples` when n < 20 or n*(1-q) < 3.
    """
    if not (0.0 < q < 1.0):
        raise ValueError("quantile_ci: q must be in (0,1), got %r" % (q,))
    raw = list(values or ())
    vals = []
    dropped = 0
    for v in raw:
        if v is None or isinstance(v, bool):
            dropped += 1
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            dropped += 1
            continue
        if not math.isfinite(f):
            dropped += 1
            continue
        vals.append(f)
    n = len(vals)
    if n < MIN_N or n * (1.0 - q) < TAIL_MIN:
        raise InsufficientSamples(_insufficient_message(n, q))
    vals.sort()
    point = _quantile_sorted(vals, q)
    rng = random.Random(seed)
    boot = []
    for _ in range(int(resamples)):
        sample = rng.choices(vals, k=n)
        sample.sort()
        boot.append(_quantile_sorted(sample, q))
    boot.sort()
    alpha = (1.0 - LEVEL) / 2.0
    lo = _quantile_sorted(boot, alpha)
    hi = _quantile_sorted(boot, 1.0 - alpha)
    # the percentile interval always brackets the point; clamp defensively
    lo, hi = min(lo, point), max(hi, point)
    if stats is not None:
        lo_r, hi_r = rank_span(n, q)
        stats.update({
            "input": len(raw), "used": n, "dropped_null": dropped,
            "rank_span": (lo_r, hi_r),
            "rank_span_pct": (lo_r / n * 100.0, hi_r / n * 100.0),
            "resamples": int(resamples),
        })
    return point, lo, hi, n
```

**E-stage_record** — `experiments/ptr-engine/longrun/cell.py:1775-1854`

```python
def stage_record(args, stamp, frames, record, analysis, grade, budget, harness, run):
    out_dir = args.out_dir
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        raise Abort(7, "7/7 record", "the record directory %s could not be created: %s"
                    % (_repo_rel(out_dir), exc))
    json_path = os.path.join(out_dir, "cell-%s-%s.json" % (args.arm, stamp))
    md_path = os.path.join(out_dir, "cell-%s-%s.md" % (args.arm, stamp))
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1, sort_keys=True)
            fh.write("\n")
    except OSError as exc:
        raise Abort(7, "7/7 record", "the cell record %s could not be written: %s"
                    % (_repo_rel(json_path), exc))

    lines = ["# CELL %s — %s" % (args.arm, stamp), "",
             "- fixture: `%s`" % _repo_rel(args.fixture),
             "- arm: `%s`  turns: %s  reps: %s  mode: %s"
             % (args.arm, args.turns, args.reps,
                "offline (%s)" % _repo_rel(args.offline) if args.offline else "live"),
             "- harness_sha256: `%s`" % harness["harness_sha256"],
             "- harness files: %s" % ", ".join("`%s`" % k for k in sorted(harness["files"])),
             "- requests actually used: **%s**" % record["requests_used"], ""]
    lines.append("## stages")
    lines.append("")
    for fr in frames:
        lines.append("- `%s`" % fr["line"])
    if budget:
        lines += ["", "## budget", "",
                  "would_send_total=%s  budget=%s  required_with_headroom=%s  "
                  "quota_remaining=%s (%s)"
                  % (budget["would_send_total"], budget["budget"],
                     budget["required_with_headroom"], budget["quota_remaining"],
                     budget["quota_basis"])]
    gates = record.get("gates") or {}
    if gates.get("verdicts"):
        lines += ["", "## gate chain (verdicts taken before the runner was invoked)", ""]
        for v in gates["verdicts"]:
            lines.append("- `%s %s` computed=%s limit=%s artefact=`%s` sha256=`%s`"
                         % (v["gate"], "allow" if v.get("ok") else "refuse",
                            v.get("computed"), v.get("limit"), v.get("artefact"),
                            v.get("artefact_sha256")))
        hyp = record.get("hypothesis") or {}
        if hyp:
            lines.append("- hypothesis: `%s` (%s), n=%s, rule_sha256=`%s`"
                         % (hyp.get("name"), hyp.get("source"), hyp.get("n"),
                            hyp.get("rule_sha256")))
        if gates.get("manifest"):
            lines.append("- manifest: `%s`" % gates["manifest"])
    lines += ["", "## grade (verbatim)", "", "```"]
    lines += grade["output"] or ["(no output)"]
    lines += ["```", "", "## analysis (verbatim)", "", "```"]
    lines += analysis["output"] or ["(no output)"]
    lines += ["```"]
    if analysis["refusals"]:
        lines += ["", "## refusals (numbers withheld on purpose)", ""]
        lines += ["- %s" % r for r in analysis["refusals"]]
    try:
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError as exc:
        raise Abort(7, "7/7 record", "the cell markdown %s could not be written: %s"
                    % (_repo_rel(md_path), exc))
    out = {"json": _repo_rel(json_path), "markdown": _repo_rel(md_path)}
    if not args.no_cell_handoff:
        # Stage 7 also reports the cell in the unit shape, beside the other handoffs.
        out["handoff"] = _repo_rel(write_handoff(
            "CELL-%s-%s" % (args.arm, stamp), "done",
            [out["json"], out["markdown"]],
            {"command_or_count": "exit 0; requests_used=%s; refusal_lines=%d"
             % (record["requests_used"], len(analysis["refusals"])),
             "commands": [" ".join(record.get("_argv") or []) or
                          "python3 experiments/ptr-engine/longrun/cell.py --arm %s"
                          % args.arm]},
            next_hint="re-run with --expect-harness %s to prove the harness has not moved"
            % harness["harness_sha256"],
            write_paths=[out["json"], out["markdown"]]))
    return out
```

**E-wrap** — `experiments/ptr-engine/tools/tree_freeze.py:413-471`

```python
def wrap(paths, out, argv, stream=None, verdict_row=False):
    """freeze -> run argv -> classify AGAINST THE BEFORE FREEZE -> one JSON record."""
    if not argv:
        raise Refused("--wrap needs a command after `--`: nothing to run, nothing to judge")
    stream = stream or sys.stdout
    before_path = out + ".before.json"
    after_path = out + ".after.json"
    # THE BASELINE. Refuses here (exit 2, no record, command never started) when a
    # declared path is missing -- never a baseline of nothing, never a phantom digest.
    before = freeze(paths, before_path)
    root = before.get("root")
    head, dirty = _git_head(root) if verdict_row else (None, None)
    if verdict_row and head is None:
        sys.stderr.write("WARNING: could not read git HEAD; the row's sha is `unstamped`\n")
    elif verdict_row and dirty:
        sys.stderr.write("WARNING: dirty tree at HEAD %s; the row names a commit that does "
                         "not contain these bytes\n" % head)
    witness = _witness(paths, root)
    started = _now()
    try:
        exit_code = subprocess.call(argv)
    except OSError as exc:
        record = _record(argv, None, before_path, after_path, before, None, [],
                         VERDICT_FAILED, started, str(exc))
        _write_record(out, record)
        stream.write("tree_freeze: could not run %r: %s\n" % (argv[0], exc))
        return record, EXIT_USAGE
    rows = classify(before, root=root)          # <-- the BEFORE freeze is the baseline
    created = _created_rows(paths, root, before, witness)
    rows = rows + created
    after = _after_document(before, rows)
    _write_document(after_path, after)
    detail = [dict(r) for r in rows if r["state"] != SAME]
    verdict = classify_verdict(exit_code, bool(detail))
    record = _record(argv, exit_code, before_path, after_path, before, after, detail,
                     verdict, started, None)
    _write_record(out, record)
    for row in created:
        stream.write("tree_freeze: declared set did not cover new file %s "
                     "(state=created, sha256 %s); report it, do not read it as absent\n"
                     % (row["path"], row["after"]))
    if verdict == VERDICT_MOVED:
        code = EXIT_TREE_MOVED
    elif verdict == VERDICT_PASS:
        code = EXIT_OK
    else:
        code = EXIT_CMD_FAILED
    stream.write("tree_freeze: verdict=%s exit_code=%s changed=%d record=%s\n"
                 % (verdict, exit_code, len(detail), out))
    if verdict in (VERDICT_MOVED, VERDICT_FAILED_AND_MOVED):
        stream.write("tree_freeze: UNSTAMPED -- %d path(s) moved, deleted or created while "
                     "the command ran; this result names bytes that no longer exist. "
                     "Re-run against the settled tree; do not re-read this run as a "
                     "verdict.\n" % len(detail))
    if verdict_row:
        line, human = verdict_row_view(argv, record, rows, head, dirty)
        stream.write(line + "\n")
        stream.write(human + "\n")
    return record, code
```

**E-freeze** — `experiments/ptr-engine/tools/tree_freeze.py:183-213`

```python
def freeze(paths, out):
    """Digest every path and write the freeze document. Refuses a path that is not there."""
    if not paths:
        raise Refused("refusing to freeze an empty set: a freeze of nothing names nothing")
    root = os.getcwd()
    files = []
    for path in paths:
        target = _resolve(root, path)
        if not os.path.exists(target):
            raise Refused(
                "refusing to freeze a path that does not exist: %r (resolved %r). A freeze "
                "records the bytes it saw; a phantom digest would later be "
                "indistinguishable from a file deleted mid-run." % (path, target))
        if not os.path.isfile(target):
            raise Refused("refusing to freeze a non-regular file: %r is not a file" % (path,))
        st = os.stat(target)
        files.append({
            "path": path,
            "sha256": sha256_of(target),
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
        })
    doc = {"at": _now(), "root": root, "tool_version": TOOL_VERSION,
           "files": files, "tree_sha256": tree_sha256(files)}
    out_dir = os.path.dirname(os.path.abspath(out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return doc
```

**E-build_report** — `experiments/ptr-engine/tools/request_ledger.py:571-713`

```python
def build_report(paths: list[str], cap: int, reserve: int, would_spend: int,
                 *, deduction_rule_sound=None, sound_rule_evidence=None) -> dict:
    files = []
    suppressed_all: list[dict] = []
    # Sorting by file NAME, never by directory-listing order.
    for path in sorted(paths, key=lambda p: os.path.basename(p)):
        entry = scan_file(path)
        suppressed_all.extend(entry.pop("suppressed"))
        files.append(entry)

    total_rows = sum(f["rows"] for f in files)
    requests_raw = sum(f["requests"] for f in files)
    requests_dedup = sum(f["requests_deduplicated"] for f in files)
    total_assumed = sum(f["assumed_billed"] for f in files)
    duplicate_excess = requests_raw - requests_dedup
    files_deduped = sum(1 for f in files if f["rule_status"] == "decided")
    files_na = sum(1 for f in files if f["rule_status"] == "not_applicable")
    headroom = cap - reserve

    # --- the ONE place a deduction is authorised -----------------------------------------
    # `requests` is what anything may spend against. It equals the RAW count unless a sound
    # rule is both flagged AND evidenced. The de-duplicated number is still computed and
    # still published -- in `diagnostic`, with `deducted: false` -- because a reversal that
    # hides the figure it reversed cannot be audited.
    deduct, deduction_reason = deduction_permitted(deduction_rule_sound, sound_rule_evidence)
    requests_published = (requests_raw - duplicate_excess) if deduct else requests_raw
    deducted_excess = duplicate_excess if deduct else 0

    projected = requests_published + would_spend
    projected_raw = requests_raw + would_spend
    projected_dedup = requests_dedup + would_spend

    candidate_rows = []
    for entry in files:
        for row in entry.get("duplicate_rows") or []:
            candidate_rows.append(dict(row, deducted=bool(deduct), reason=deduction_reason))

    return {
        "unit": "REQUEST-LEDGER",
        "requests_raw": requests_raw,
        "requests_deduplicated": requests_dedup,
        "requests": requests_published,
        "remaining_raw": headroom - projected_raw,
        "remaining": headroom - projected,
        "remaining_deduplicated": headroom - projected_dedup,
        "duplicate_excess": duplicate_excess,
        "dedup_rule": DEDUP_RULE,
        "deduction_rule_sound": bool(deduct),
        "deduction": {
            "applied": bool(deduct),
            "candidate_excess": duplicate_excess,
            "deducted_requests": deducted_excess,
            "reason": deduction_reason,
            "evidence_required": DEDUCTION_EVIDENCE_KEY,
            "evidence_note": DEDUCTION_EVIDENCE_NOTE,
            "publishes": "requests == requests_raw unless a sound rule with evidence is present",
        },
        "diagnostic": {
            "deducted": False,
            "why": ("kept visible so the reversal is auditable; NOT subtracted from spend "
                    "because the rule is unsound as a request-identity test"),
            "requests_deduplicated": requests_dedup,
            "duplicate_excess": duplicate_excess,
            "remaining_deduplicated": headroom - projected_dedup,
            "per_file_excess": {
                f["file"]: f["duplicate_excess"] for f in files if f["duplicate_excess"]
            },
            "per_file_deducted": {
                f["file"]: (f["duplicate_excess"] if deduct else 0)
                for f in files if f["duplicate_excess"]
            },
            "reason": deduction_reason,
            "evidence_note": DEDUCTION_EVIDENCE_NOTE,
            "rows": candidate_rows,
        },
        "files_deduped": files_deduped,
        "files_not_applicable": files_na,
        "dedup_decision": {
            "decidable_when": (
                "every row in the file carries a non-empty content_sha256 and a "
                "millisecond-resolution ts"
            ),
            "files_deduped": files_deduped,
            "files_not_applicable": files_na,
            "files_not_applicable_names": [
                f["file"] for f in files if f["rule_status"] == "not_applicable"
            ],
            "count_discrepancy": (
                "The REQUEST-LEDGER-2 card (and TVS-REGRADE's headline) say 9 decidable files and "
                "5 legacy files. A direct schema census says 11 and 3: the three files that cannot "
                "be decided are rows-baseline, rows-equalinfo and rows-live, all of which carry a "
                "second-resolution ts_utc and no content_sha256. The published arithmetic -- 30 "
                "excess rows, 1,071 de-duplicated requests -- is identical either way, because "
                "every one of the 30 excess rows sits in a decidable file."
            ),
        },
        "rule": RULE,
        "counting": {
            "counted_kinds": list(COUNTED_KINDS),
            "exclusion_markers": ["billed:false", "followup_suppressed", "served_from:prompt"],
            "not_exclusion_markers": {
                "billed_round": "fetch-ROUND accounting; a pinned serve is still a request",
                "fetch_followup": "marks a row that IS a real follow-up request",
                "prompt_served": "cache-accounting counter, not served_from",
                "is_checkpoint": "NOT a billing marker: checkpoint rows are genuine calls",
            },
            "assumed_billed_means": (
                "row carries no recognised kind marker; counted because an unmarked row that "
                "reached the wire must not vanish from the budget"
            ),
        },
        "marker_reconciliation": _marker_reconciliation(files),
        "budget": {
            "cap": cap,
            "reserve": reserve,
            "headroom": headroom,
            "spent": requests_published,
            "spent_deduplicated": requests_dedup,
            "spent_raw": requests_raw,
            "would_spend": would_spend,
            "projected": projected,
            "projected_raw": projected_raw,
            "projected_deduplicated": projected_dedup,
            "remaining": headroom - projected,
            "remaining_raw": headroom - projected_raw,
            "remaining_deduplicated": headroom - projected_dedup,
            "within_budget": projected <= headroom,
        },
        "total": {
            "files": len(files),
            "rows": total_rows,
            "requests": requests_published,
            "requests_raw": requests_raw,
            "requests_deduplicated": requests_dedup,
            "duplicate_excess": duplicate_excess,
            "assumed_billed": total_assumed,
            "files_deduped": files_deduped,
            "files_not_applicable": files_na,
        },
        "per_file": files,
        "files": files,  # back-compat alias; identical rows, never a second derivation
        "suppressed": suppressed_all,
    }
```

**E-derive_stop_reason** — `experiments/ptr-engine/longrun/client.py:141-181`

```python
def derive_stop_reason(finish_reason, *, content_present, completion_tokens=None,
                       max_tokens=None, error_code=None, tool_calls_present=False):
    """WHY the response ended, in ONE word of the closed vocabulary.

    Precedence, most causally specific first:

    1. ``error_code`` -- a harness/transport code already in the vocabulary wins: the
       harness or the wire ended it, not the model.
    2. The server's own ``finish_reason`` when it maps (``stop``/``length``/``tool_calls``/
       ``content_filter``); an unmappable string becomes ``unknown``.
    3. NO finish chunk but at least one ``tool_calls``/``function_call`` delta: the model
       DID produce a call, so the stream is ``tool_calls`` -- never ``empty_response``.
    4. NO finish chunk at all, and ``completion_tokens >= max_tokens``: the generation ran
       into the completion ceiling and the server closed without a final chunk -- this is
       exactly the 128-token case that used to look like a refusal, so it is ``length``.
    5. NO finish chunk, no tool-call delta and no usable content: ``empty_response`` --
       nothing was produced at all.
    6. Anything else: ``unknown``.  Never guessed.
    """
    if isinstance(error_code, str) and error_code in STOP_REASONS:
        return error_code
    if isinstance(finish_reason, str) and finish_reason.strip():
        key = finish_reason.strip().lower()
        if key in _FINISH_REASON_TO_STOP:
            return _FINISH_REASON_TO_STOP[key]
        if key in STOP_REASONS:
            return key
        return STOP_REASON_UNKNOWN
    if tool_calls_present:
        # STOP-REASON-HOLES: a dispatched tool call whose stream carried no finish chunk
        # and no assistant text is a PRODUCTION, not a silent refusal.
        return STOP_REASON_TOOL_CALLS
    if completion_tokens is not None and max_tokens is not None:
        try:
            if int(completion_tokens) >= int(max_tokens):
                return STOP_REASON_LENGTH
        except (TypeError, ValueError):
            pass
    if not content_present:
        return STOP_REASON_EMPTY
    return STOP_REASON_UNKNOWN
```

**E-load_fixture** — `experiments/ptr-engine/longrun/run_longrun.py:137-177`

```python
def load_fixture(path: str) -> dict:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise FixtureError(f"cannot read fixture {path}: {exc}") from exc
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureError(f"fixture {path} is not JSON: {exc}") from exc
    if doc.get("stub") or not doc.get("items"):
        raise FixtureError(
            f"fixture {path} is a STUB (no items/turns). The real fixture tree is card "
            "2a6c4761's deliverable; use a constructed fixture with --fixture."
        )
    for key in ("schema", "task_id", "N", "bytes_per_token", "system_prompt",
                "items", "turns"):
        if key not in doc:
            raise FixtureError(f"fixture {path} missing required key {key!r}")
    # WALL-KEY: the wall may be declared per arm instead of once at top level. A fixture
    # that declares neither is unlaunchable; one that declares ONLY `wall_tokens_by_arm`
    # is complete (the top-level key is a legacy/cross-arm hint, not a requirement).
    if "wall_tokens" not in doc and not (isinstance(doc.get("wall_tokens_by_arm"), dict)
                                        and doc["wall_tokens_by_arm"]):
        raise FixtureError(f"fixture {path} declares neither 'wall_tokens' nor a non-empty "
                           "'wall_tokens_by_arm' — no arm has a wall")

    if doc["schema"] != "consonance.longrun-fixture/1":
        raise FixtureError(f"unsupported fixture schema {doc['schema']!r}")
    if not doc["items"] or not all({"id", "body"} <= set(it) for it in doc["items"]):
        raise FixtureError("fixture items must be non-empty {id, body} objects")
    turns = sorted(doc["turns"], key=lambda t: int(t["turn"]))
    if [int(t["turn"]) for t in turns] != list(range(1, int(doc["N"]) + 1)):
        raise FixtureError("fixture turns must be numbered 1..N contiguously")
    for t in turns:
        if not isinstance(t.get("question"), str) or not t["question"]:
            raise FixtureError(f"fixture turn {t['turn']} has no question")
    doc["turns"] = turns
    doc["_path"] = os.path.abspath(path)
    doc["_sha256"] = sha256_bytes(raw)
    return doc
```

**E-ARMS** — `experiments/ptr-engine/longrun/run_longrun.py:66-66`

```python
ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen")
```

**E-PREDICTIONS** — `experiments/ptr-engine/longrun/run_longrun.py:71-80`

```python
PREDICTIONS = {
    "transcript-grow": ("P2: A's tokens-to-verified-success >= 1.5x C's; at N=60 it hits the "
                        "window/cap and repairs from a front-truncated prefix."),
    "transcript-compact": ("P4: B lands within 2x of C on p95 TTFT but fails t30 where its "
                           "digest dropped the turn-2 code."),
    "pointer-stable": ("P1: C's p95 TTFT <= 0.5x A's, cached share >= 0.80 after turn 12; "
                       "P2: A's tokens-to-verified-success >= 1.5x C's."),
    "lease-reopen": ("P3: D has the lowest p95 TTFT but loses t30/t60 accuracy unless the "
                     "<=400-token state line carries the turn-2 fact and the turn-24 correction."),
}
```

**E-TOOL_CALLS_PER_TURN** — `experiments/ptr-engine/longrun/run_longrun.py:220-220`

```python
TOOL_CALLS_PER_TURN = 2
```

**E-TOOL_FETCH_ROUNDS_PER_ARM** — `experiments/ptr-engine/longrun/run_longrun.py:230-230`

```python
TOOL_FETCH_ROUNDS_PER_ARM = 48
```

**E-TOOL_FETCH_ROUNDS_PER_TURN** — `experiments/ptr-engine/longrun/run_longrun.py:236-236`

```python
TOOL_FETCH_ROUNDS_PER_TURN = 3
```

**E-BudgetExhausted** — `experiments/ptr-engine/longrun/run_longrun.py:293-294`

```python
class BudgetExhausted(RuntimeError):
    """A fetch follow-up would exceed the request budget."""
```

**E-serve_from_prompt** — `experiments/ptr-engine/longrun/run_longrun.py:839-860`

```python
def serve_from_prompt(view: dict, call: dict) -> dict:
    """Answer a call from the lines the prompt already carries. `{record, block, text}`.

    The block is shaped exactly like a real `<tool_result>` so the arm reads it the same
    way, with `base="prompt" served_from="prompt"` naming its provenance.  `executed` is
    False and `billed` is False: nothing was read from disk and no fetch round was spent.
    """
    body = "\n".join(view["lines"][view["first"]:view["last"]])
    rec = {"path": call["path"], "start_line": call["start_line"], "end_line": call["end_line"],
           "executed": False, "truncated": False, "billed": False, "served_from": "prompt",
           "base": "prompt", "pinned_item": view.get("item_id"),
           "pinned_lines": f'{view["start"]}-{view["end"]}',
           "lines_returned": view["last"] - view["first"]}
    if len(body) > TOOL_READ_CAP_CHARS:
        body = body[:TOOL_READ_CAP_CHARS]
        rec["truncated"] = True
    path_attr = call["path"].replace('"', "'")
    attrs = (f'for="read_file" path="{path_attr}" lines="{call["start_line"]}-{call["end_line"]}"'
             ' base="prompt" served_from="prompt"')
    if rec["truncated"]:
        attrs += ' truncated="true"'
    return {"record": rec, "block": f"<tool_result {attrs}>\n{body}\n</tool_result>", "text": body}
```

**E-fetch_rounds** — `experiments/ptr-engine/longrun/run_longrun.py:901-1046`

```python
def fetch_rounds(cfg, fixture, arm, rep, run_id, t, manifest_sha, extras, messages, resp,
                 sent, budget, rounds_used, served=None, pinned=None, per_turn_cap=None,
                 may_request=None, gate=None):
    """Run the bounded read_file channel after one model turn.

    Bounds (PROBE-CP3-V6): <= TOOL_CALLS_PER_TURN (2) calls per turn, at most
    `per_turn_cap` fetch rounds per turn (0 = unbounded, the pre-V6 behaviour), and
    <= fetch_rounds_per_arm(cfg) (default 48) BILLED rounds per arm.  One follow-up model request
    is bought per round, so `requests_sent = turn requests + follow-ups bought + digests`.

    (a) SERVE FROM THE PROMPT.  `pinned` is what the planner actually pinned into THIS
    turn's prompt (see pinned_views).  A call whose range lies wholly inside a pinned body
    is answered from that body: the record carries `served_from="prompt"`, the block
    carries the same lines, nothing is read from disk and NO ROUND IS BILLED.  It still
    rides the one follow-up request a round would have bought, because a result the model
    never sees is not a result — that request is drawn from the follow-up allowance
    (`may_request`), not from the round budget.

    (b) PER-TURN CAP.  `per_turn_cap` rounds per turn; the rest are refused host-side with
    `error="per_turn_round_cap"`, so one recon burst can no longer spend the cell.

    A duplicate fetch is never re-bought: an identical call (same path+range) later in
    the SAME turn, or one whose content is already in the conversation from an earlier
    turn (`served`, carried across turns by the caller), returns the same <tool_result>
    with `cached="true"` and spends neither a round nor a request.

    Returns (messages, resp, sent, rounds_used, turn_calls, followup_rows) — unchanged
    arity, so the V5 offline test still binds.  The per-turn counters are derived by the
    caller from the records (`served_from="prompt"` count) and from `len(followup_rows)`.
    """
    turn_calls: list[dict] = []
    followups: list[dict] = []
    cap = TOOL_FETCH_ROUNDS_PER_TURN if per_turn_cap is None else int(per_turn_cap)
    if not tools_enabled(cfg):
        return messages, resp, sent, rounds_used, turn_calls, followups
    root = os.getcwd()
    engine_root = os.path.join(root, ENGINE_ROOT_REL)
    if not os.path.isdir(engine_root):
        engine_root = None
    if served is None:
        served = {}
    pinned = list(pinned or [])
    content = resp.get("content") or ""
    pending = parse_tool_calls(content)
    rounds_this_turn = 0
    prompt_serves = 0
    while pending:
        if cap > 0 and rounds_this_turn >= cap:
            # (b) This turn has already bought its rounds: refuse the rest, spend nothing.
            for call in pending:
                turn_calls.append({"path": call["path"], "start_line": call["start_line"],
                                   "end_line": call["end_line"], "executed": False,
                                   "truncated": False, "billed": False,
                                   "error": "per_turn_round_cap"})
            pending = []
            break
        batch, overflow = limit_calls(pending)
        turn_cache: dict = {}
        round_calls: list[dict] = []
        blocks: list[str] = []
        fresh = 0
        served_now = 0
        for call in batch:
            key = (call["path"], call["start_line"], call["end_line"])
            if key in turn_cache:
                res = _cached_result(turn_cache[key], "turn")
            elif key in served:
                res = _cached_result(served[key], "conversation")
            else:
                view = find_pinned_view(pinned, call) if TOOL_SERVE_FROM_PROMPT else None
                if view is not None:
                    res = serve_from_prompt(view, call)
                    served_now += 1
                    turn_cache[key] = res
                    served[key] = res
                elif rounds_used + fresh >= fetch_rounds_per_arm(cfg):
                    # The per-arm ROUND budget is spent.  This refusal is per CALL, not per
                    # turn: a range the prompt already carries still costs no round, so the
                    # T46 checkpoint read stays servable after the round budget is gone
                    # (the exact v5 starvation this unit exists to remove).
                    rec = {"path": call["path"], "start_line": call["start_line"],
                           "end_line": call["end_line"], "executed": False,
                           "truncated": False, "billed": False,
                           "error": "fetch_budget_exhausted"}
                    round_calls.append(rec)
                    blocks.append('<tool_result error="fetch_budget_exhausted"/>')
                    continue
                else:
                    res = execute_tool_call(call, root, engine_root)
                    fresh += 1
                    turn_cache[key] = res
                    if res["record"].get("executed"):
                        served[key] = res
            round_calls.append(res["record"])
            blocks.append(res["block"])
        for call in overflow:
            round_calls.append({"path": call["path"], "start_line": call["start_line"],
                                "end_line": call["end_line"], "executed": False,
                                "truncated": False, "error": "turn_call_cap"})
        turn_calls.extend(round_calls)
        if fresh == 0 and served_now == 0:
            # Everything asked for is already in the conversation: serve it, bill nothing.
            pending = []
            break
        if may_request is not None and not may_request():
            # The follow-up allowance is exhausted (or fully reserved for later declared
            # checkpoints).  Refusing gracefully keeps the cell intact; the served records
            # still say what the turn asked for.
            for rec in round_calls:
                if rec.get("served_from") == "prompt" or rec.get("executed") or rec.get("cached"):
                    rec["followup_suppressed"] = "request_allowance"
            pending = []
            break
        next_messages = messages + [
            {"role": "assistant", "content": content},
            {"role": "user", "content": "\n".join(blocks)
             + "\n\nUse the tool result above. Answer the QUESTION now, within the word budget."},
        ]
        if sent >= budget:
            raise BudgetExhausted(f"fetch at T{t} would exceed the request budget of {budget}")
        # WIRE-CAP-GATE: a follow-up is a REAL request and bills separately, so the brake
        # must see it too.  Reserved (and possibly refused) BEFORE the send.
        if gate is not None:
            gate.acquire(t, "tool-followup")
        resp = send_chat(cfg, next_messages)
        sent += 1
        rounds_this_turn += 1
        if fresh:
            rounds_used += 1
        else:
            prompt_serves += 1
        messages = next_messages
        content = resp.get("content") or ""
        followups.append(make_row(
            cfg, fixture, arm, rep, run_id, t, resp, content, "tool-followup", manifest_sha,
            # ROW-ATTRIBUTION: the 0-based position of THIS request inside the turn --
            # the initial send is send_index 0, the -th follow-up is send_index -.  A
            # later analysis can therefore address one HTTP request by (turn, send_index)
            # instead of guessing from row order.
            dict(extras, prompt_sha256=sha256_text(next_messages[-1]["content"]),
                 fetch_followup=True, tool_calls=round_calls,
                 billed_round=bool(fresh), prompt_served=int(served_now),
                 send_index=int(rounds_this_turn),
                 fetch_rounds_cap_per_turn=cap)))
        pending = parse_tool_calls(content)
    return messages, resp, sent, rounds_used, turn_calls, followups
```

**E-build_manifest** — `experiments/ptr-engine/longrun/run_longrun.py:1404-1495`

```python
def build_manifest(cfg, fixture: dict, arm: str, rep: int, run_id: str, rows_path: str,
                   cap_gate: dict | None = None) -> dict:
    return {
        # WIRE-CAP-GATE: the declared allocation and the run-start spend are frozen in the
        # manifest BEFORE the first request; the running and final counts are added to this
        # same block at exit by _gate_finish (additive; no existing key changes meaning).
        **({"cap_gate": cap_gate} if cap_gate is not None else {}),
        "schema": "consonance.longrun-manifest/1",
        "run_id": run_id,
        "created_utc": iso(utc_now()),
        "dry_run": bool(cfg.dry_run),
        # Thinking switch (consonance.longrun-manifest/1, added RUNNER-THINKING-FLAG).
        # "auto" = the key is absent from the request body (byte-identical to pre-flag runs);
        # rows from different settings must never be pooled, so it is frozen here AND per row.
        "thinking": thinking_setting(cfg),
        # WIRE-CLIENT: the effective /metrics-scrape value, resolved by the client's own
        # precedence rule (CLI flag > PTR_METRICS_SCRAPE > default). Frozen here and
        # stamped on every row, because rows scraped with the counters and rows without
        # them must never be silently pooled.
        "metrics_scrape": client.resolve_metrics_scrape(cfg),
        "arm": arm,
        "rep": rep,
        "N": int(fixture["N"]),
        "model": {
            "name": cfg.model,
            "endpoint": cfg.base_url.rstrip("/"),
            "engine": cfg.engine,
            "tokenizer": "server-reported (usage.prompt_tokens); no client tokenizer",
        },
        "renderer": {
            "api": "POST /chat/completions",
            "stream": bool(cfg.stream),
            "include_usage": bool(cfg.stream),
            "temperature": 0,
            "max_tokens": int(cfg.max_tokens),
            "thinking": thinking_setting(cfg),
            "chat_template_kwargs": thinking_kwargs(thinking_setting(cfg)),
            "messages": "system + user; content is one user string per turn",
        },
        "engine_flags": {
            "ctx_window": int(fixture.get("window_tokens", 131072)),
            "design_cap_tokens": int(fixture["wall_tokens"]),
            "cache_block_tokens": 64,
            "concurrency_B": 64,
            "source": "LONGRUN-PREREG §0/§2; RECORD.md C5 (cached = P1 - P1 mod 64)",
            "knowable": "ctx/cap/block from the prereg; server build flags are not exposed via /v1",
        },
        "fixture": {
            "path": fixture["_path"],
            "sha256": fixture["_sha256"],
            "schema": fixture["schema"],
            "task_id": fixture["task_id"],
            "bytes_per_token": float(fixture["bytes_per_token"]),
            "wall_tokens": int(fixture["wall_tokens"]),
        },
        "prereg": {
            "path": "experiments/ptr-engine/LONGRUN-PREREG.md",
            "sha256": sha256_file("experiments/ptr-engine/LONGRUN-PREREG.md")
            if os.path.exists("experiments/ptr-engine/LONGRUN-PREREG.md") else None,
        },
        "prediction": PREDICTIONS[arm],
        # ROW-PROVENANCE: the SAME nine-field block every row carries, published once per
        # cell, so a later reader can read a cell's provenance from the manifest instead
        # of re-deriving it row by row.  ``fixture_id`` is <task_id>.<fixture_version>,
        # ``harness_sha256`` is the digest cell.py would freeze for this tree.
        "provenance": provenance_for(cfg, fixture, arm),
        "rows_path": rows_path,
        # FETCH-CHANNEL: present only on a --tools run, so a tools-off manifest keeps
        # the exact bytes it had before this flag existed.
        **({"tools": {"names": tool_names(cfg), "max_calls_per_turn": TOOL_CALLS_PER_TURN,
                      "max_fetch_rounds_per_arm": fetch_rounds_per_arm(cfg),
                      # PROBE-CP3-V6 (b): a recon burst may not spend the cell.  Frozen here
                      # and stamped on every row as `fetch_rounds_cap_per_turn`.
                      "max_fetch_rounds_per_turn": fetch_rounds_per_turn(cfg),
                      # PROBE-CP3-V6 (a): a range already inside the pinned prompt bodies is
                      # served from the prompt and bills no round.
                      "serve_from_prompt": bool(TOOL_SERVE_FROM_PROMPT),
                      # the follow-up REQUEST allowance (rounds + prompt serves share it),
                      # with one request reserved for every not-yet-reached declared
                      # checkpoint so no earlier burst can starve T12/T24/T46.
                      "followup_request_pool": fetch_rounds_per_arm(cfg),
                      "followup_reserve_per_checkpoint": True,
                      # durable spend: frozen at creation, and on --resume the counter is
                      # max(this, rounds derived from the cell's own rows)
                      "fetch_rounds_used": 0,
                      "path_bases": ["workspace", ENGINE_ROOT_REL],
                      "duplicate_fetch": "cached, billed once per turn",
                      "read_cap_lines": TOOL_READ_CAP_LINES,
                      "read_cap_chars": TOOL_READ_CAP_CHARS,
                      "followups_are_requests": True}}
           if tools_enabled(cfg) else {}),
    }
```

**E-write_manifest** — `experiments/ptr-engine/longrun/run_longrun.py:1498-1509`

```python
def write_manifest(path: str, doc: dict) -> tuple[bytes, str]:
    """Write the frozen manifest atomically; fail loudly (never start a run without it)."""
    data = (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return data, sha256_bytes(data)
```

**E-run_dry** — `experiments/ptr-engine/longrun/run_longrun.py:2057-2169`

```python
def run_dry(cfg, fixture: dict, cells: list[tuple[str, int]]) -> int:
    root = os.path.join("/tmp/longrun-previews", fixture["task_id"])
    order: list[str] = []
    reps_by_arm: dict[str, int] = {}
    for arm, _rep in cells:
        if arm not in reps_by_arm:
            order.append(arm)
            reps_by_arm[arm] = 0
        reps_by_arm[arm] += 1
    previews: dict[str, list[str]] = {arm: [] for arm in order}
    counts: dict[str, dict] = {}

    # TREATMENTS LAUNCH PRECONDITION — printed FIRST, before a single preview body is
    # rendered, and fatal.  A dry run that reaches no hook is not a preview of a cell; it
    # is the announcement that the cell would measure its control path for 48 turns.
    print("TREATMENT REACHABILITY AT THE FROZEN HORIZON (offline, from the fixture)")
    unreachable = 0
    for arm in order:
        rc, lines = check_treatments(fixture, arm, HORIZON_TURNS)
        for line in lines:
            print(line)
        unreachable = unreachable or rc
    if unreachable:
        print(f"\nLAUNCH REFUSED (exit {EXIT_TREATMENTS_UNREACHABLE}): a treatment cannot fire "
              f"inside {HORIZON_TURNS} turns at this fixture's wall. Do not raise the horizon "
              "(PARM-1 line 137) and do not raise the wall until it fits: change the fixture's "
              "treatment inputs, or run an arm whose treatment does fire. No request was sent.",
              file=sys.stderr)
        return EXIT_TREATMENTS_UNREACHABLE
    print()

    # RUN-DRY-TURN-SCOPE: the preview loops over EXACTLY the turns the live cell would
    # execute — `cell_turns`, the same one definition `run_cell` and `projected_requests`
    # read.  It is not `fixture["N"]` and it is not a second `min()` here: a preview that
    # prices 48 turns for a `--max-turns 12` cell gates a cell that cannot exist.
    n_turns = cell_turns(cfg, fixture)

    for arm in order:
        fx = fixture_for_arm(fixture, arm)
        planner = Planner(arm, fx, dry_run=True)
        c = {"reps": reps_by_arm[arm], "digest_requests": 0, "wall_turn": None,
             "trunc_turn": None, "post_wall": None}
        counts[arm] = c
        for t in range(1, n_turns + 1):
            info = planner.build(t)
            if t in checkpoint_turns(fixture):
                # ANSWER-CONTRACT (v5): identical injection to run_cell, so the preview
                # body is the body a checkpoint turn would really send.
                info["prompt"] = checkpoint_prompt(fixture, t, info["prompt"])
            body = preview_body(cfg, planner, info["prompt"])
            digest_body = None
            if info["digest_request"] is not None:
                c["digest_requests"] += 1
                digest_body = json.dumps(request_body(cfg, info["digest_request"]), sort_keys=True,
                                         indent=2, ensure_ascii=False)
                if c["wall_turn"] is None:
                    c["wall_turn"] = t
                    dpath = os.path.join(root, arm, f"wall-{t:02d}-digest-request.json")
                    dbytes, dsha = preview_write(dpath, digest_body)
                    print(f"  [{arm}] first wall at T{t}: digest request {dbytes} B sha256={dsha} ({dpath})")
            if len(previews[arm]) < 3:
                previews[arm].append(sha256_text(body))
                path = os.path.join(root, arm, f"turn-{t:02d}.json")
                nbytes, digest = preview_write(path, body)
                user0 = info["prompt"].replace("\n", " ")[:100]
                print(f"  [{arm}] T{t}: {nbytes} B sha256={digest} user=\"{user0}\"")
                if cfg.show_prompts:
                    print(body)
            if arm == "transcript-grow" and c["trunc_turn"] is None and info["evicted"]:
                c["trunc_turn"] = t
                print(f"  [{arm}] first FIFO truncation at T{t}: evicted {info['evicted']} history block(s)")
            if arm == "transcript-compact" and c["wall_turn"] is not None and c["post_wall"] is None:
                c["post_wall"] = (t, sha256_text(body))
                ppath = os.path.join(root, arm, f"post-wall-{t:02d}.json")
                pbytes, psha = preview_write(ppath, body)
                print(f"  [{arm}] post-wall body at T{t}: {pbytes} B sha256={psha} "
                      "(digest text is a placeholder offline; the digest REQUEST above is exact)")
            # simulate the answer the model would have produced
            planner.record(t, f"<<answer from turn {t}: not produced in dry-run>>")

    print("\nREQUEST COUNTS (what --dry-run would send)")
    total = 0
    for arm in order:
        c = counts[arm]
        turns = n_turns * c["reps"]
        extra = c["digest_requests"] * c["reps"]
        cell_total = turns + extra
        total += cell_total
        assert turns == n_turns * c["reps"], "turn count must be the cell's turns x reps"
        # Full cell (n_turns == fixture N): the line is byte-identical to before this unit.
        scope = (f"N={fixture['N']} x reps={c['reps']}" if n_turns == int(fixture["N"])
                 else f"N={fixture['N']} --max-turns={n_turns} x reps={c['reps']}")
        print(f"  {arm:19s} turn_requests={turns} ({scope})  "
              f"digest_requests={extra}  cell_total={cell_total}")
    print(f"  would_send_total={total}")
    if tools_enabled(cfg):
        # Offline there is no model turn, so no <tool_call> can be parsed and no fetch
        # is possible: the cap below is the ceiling, not a predicted spend.
        print(f"  tool_channel={','.join(tool_names(cfg))} fetch_rounds_cap="
              f"{fetch_rounds_per_arm(cfg)} (per arm) fetch_rounds_cap_per_turn="
              f"{fetch_rounds_per_turn(cfg)} serve_from_prompt={bool(TOOL_SERVE_FROM_PROMPT)} "
              f"max_calls_per_turn={TOOL_CALLS_PER_TURN} "
              f"fetch_requests_in_this_preview=0 (no model turn offline)")

    print("\nPREVIEW PAIRWISE (first three request bodies; 0/3 differ = identical)")
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            diff = sum(1 for x, y in zip(previews[a], previews[b]) if x != y)
            note = ""
            if (a, b) == ("transcript-grow", "transcript-compact"):
                note = "  <- identical BY DESIGN before B's first wall"
            print(f"  {a} vs {b}: {diff}/3 differ{note}")
    return 0
```

**E-Planner** — `experiments/ptr-engine/longrun/run_longrun.py:1050-1197`

```python
class Planner:
    """Builds the next prompt for one arm from the answers already recorded."""

    def __init__(self, arm: str, fixture: dict, dry_run: bool):
        self.arm = arm
        self.fixture = fixture
        self.dry_run = dry_run
        self.answers: list[str] = []
        self.bpt = float(fixture["bytes_per_token"])
        self.wall_tokens = int(fixture["wall_tokens"])
        self.wall_bytes = self.wall_tokens * self.bpt
        # B state
        self.digest: str | None = None
        self.raw: list[str] = []
        # D state
        self.walls = list(fixture.get("lease_reopen_turns") or [])
        self.lease_state = ""
        self.lease = 1
        self.lease_start = 1

    # -- helpers ---------------------------------------------------------
    def messages(self, user: str) -> list[dict]:
        return [{"role": "system", "content": self.fixture["system_prompt"]},
                {"role": "user", "content": user}]

    def record(self, t: int, answer: str) -> None:
        while len(self.answers) < t - 1:
            self.answers.append("")
        self.answers.append(answer)
        if self.arm == "transcript-compact":
            self.raw.append(turn_block(t, self.fixture["turns"][t - 1], answer))

    def _b_base(self) -> str:
        if self.digest:
            return f"DIGEST OF EARLIER TRANSCRIPT\n{self.digest}\n\n"
        return working_set_block(self.fixture) + "\n\n"

    def _distill(self, upto_turn: int) -> str:
        """Host-side state line (no request): pointers + the tail of this lease's answers."""
        lines = ["POINTERS: " + ", ".join(it["id"] for it in self.fixture["items"])]
        start = max(self.lease_start, upto_turn - 6)
        for i in range(start, upto_turn):
            text = (self.answers[i - 1] or "").replace("\n", " ")[:200] if i - 1 < len(self.answers) else ""
            if text:
                lines.append(f"T{i}: {text}")
        return "\n".join(lines).encode("utf-8")[:1800].decode("utf-8", "ignore")

    def replay(self, rows: list[dict]) -> None:
        """Rebuild prompt state from a partial cell (resume) — no requests."""
        for row in rows:
            t = int(row.get("turn") or 0)
            content = row.get("content") or ""
            if (self.arm == "lease-reopen" and t in self.walls and self.lease_start <= t):
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            if row.get("kind") == "digest":
                self.digest = content
                self.raw = self.raw[-4:]
            else:
                self.record(t, content)

    # -- build -----------------------------------------------------------
    def build(self, t: int) -> dict:
        turn = self.fixture["turns"][t - 1]
        arm = self.arm
        info: dict = {"t": t, "turn": turn, "digest_request": None, "evicted": 0,
                      "lease": None, "prefix_sha256": None}
        if arm == "transcript-grow":
            parts = [working_set_block(self.fixture)]
            parts += [turn_block(i, self.fixture["turns"][i - 1], self.answers[i - 1])
                      for i in range(1, t) if i - 1 < len(self.answers)]
            current = turn_user(t, turn)
            evicted = 0
            # FIFO over HISTORY, never over the pinned working set.  `parts[0]` is the
            # fixture's pinned corpus; popping it (the pre-v8 `parts.pop(0)`) means the
            # first eviction of any firing grow cell deletes the corpus the checkpoints are
            # answered from, so the arm would measure amnesia, not eviction.  Index 0 is
            # therefore pinned and the oldest HISTORY block goes first.  This cannot alter
            # any row already on disk: `evicted > 0` on 0 rows of the pinned corpus.
            while len(parts) > 1 and est_tokens("\n\n".join(parts + [current]), self.bpt) > self.wall_tokens:
                parts.pop(1)
                evicted += 1
            text = "\n\n".join(parts + [current])
            if est_tokens(text, self.bpt) > self.wall_bytes:
                keep = int(self.wall_bytes)
                cut = text.encode("utf-8")[-keep:]
                text = cut.decode("utf-8", "ignore").split("\n", 1)[-1]
                evicted += 1
            info["evicted"] = evicted
            info["prompt"] = text
            return info

        if arm == "transcript-compact":
            current = turn_user(t, turn)
            base = self._b_base()
            window = base + "\n\n".join(self.raw + [current])
            if t > 1 and est_tokens(window, self.bpt) > self.wall_tokens:
                transcript = base + "\n\n".join(self.raw)
                instruction = (
                    "COMPRESS the transcript below into at most 700 tokens. Preserve every item id, "
                    "every audit/retention code, and every correction.\n\nTRANSCRIPT:\n" + transcript
                )
                info["digest_request"] = self.messages(instruction)
                if self.dry_run:
                    self.digest = "<<digest produced by the digest request at this turn (dry-run placeholder)>>"
                    self.raw = self.raw[-4:]
                    base = self._b_base()
            info["prompt"] = base + "\n\n".join(self.raw + [current])
            return info

        if arm == "pointer-stable":
            upto = min(t + 1, len(self.fixture["items"]))
            bodies = "\n".join(body_block(it) for it in self.fixture["items"][:upto])
            prefix = f"INDEX\n{index_lines(self.fixture)}\n{bodies}"
            info["prefix_sha256"] = sha256_text(prefix)
            tail = ["STATE"]
            for i in range(max(1, t - 3), t):
                ans = self.answers[i - 1] if i - 1 < len(self.answers) else ""
                tail.append(f"T{i}: {ans.replace(chr(10), ' ')[:120]}")
            if len(tail) == 1:
                tail.append("(no prior turns in this lease)")
            note = turn.get("note")
            if note:
                tail.append(f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}")
            tail.append(f"QUESTION (T{t}): {turn['question']}")
            info["prompt"] = prefix + "\n\n" + "\n".join(tail)
            return info

        if arm == "lease-reopen":
            if t in self.walls and self.lease_start <= t:
                self.lease_state = self._distill(t)
                self.lease = 1 + sum(1 for w in self.walls if w <= t)
                self.lease_start = t
            info["lease"] = self.lease
            note = turn.get("note")
            text = f"INDEX\n{index_lines(self.fixture)}\n"
            if self.lease_state:
                closed = min([w for w in self.walls if w <= t], default=0)
                text += f"\nLEASE STATE (closed at T{closed})\n{self.lease_state}\n"
            text += "\n"
            if note:
                text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
            text += f"QUESTION (T{t}): {turn['question']}"
            info["prompt"] = text
            return info

        raise ValueError(f"unknown arm {arm!r}")
```

**E-send_chat** — `experiments/ptr-engine/longrun/run_longrun.py:1541-1549`

```python
def send_chat(cfg, messages: list[dict]) -> dict:
    """Send one request through the single streaming implementation (client.send_chat).

    Deliberately a one-line delegation: every measured field on the returned dict —
    ttft_ms, ttft_source, first_token_kind, cached_tokens, cached_source,
    engine_metrics_before/_after, wall_ms — is produced by client.py and passed through
    to the row unchanged by make_row().
    """
    return client.send_chat(cfg, messages)
```

**E-read_cell_rows** — `experiments/ptr-engine/longrun/run_longrun.py:2016-2032`

```python
def read_cell_rows(rows_path: str, run_id: str, task_id: str, arm: str, rep: int) -> list[dict]:
    rows: list[dict] = []
    if not os.path.exists(rows_path):
        return rows
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (row.get("run_id"), row.get("task_id"), row.get("arm"), row.get("rep")) == (
                    run_id, task_id, arm, rep):
                rows.append(row)
    return rows
```

**E-resume_start** — `experiments/ptr-engine/longrun/run_longrun.py:2035-2041`

```python
def resume_start(rows: list[dict]) -> int:
    if not rows:
        return 0
    if any(row.get("error") for row in rows):
        raise SystemExit("RESUME REFUSED: this cell already holds a failed row; a failure is "
                         "recorded, not retried past the budget. Start a new --run-id.")
    return max(int(row.get("turn") or 0) for row in rows)
```

**E-turn_user** — `experiments/ptr-engine/longrun/run_longrun.py:198-203`

```python
def turn_user(t: int, turn: dict) -> str:
    text = ""
    note = turn.get("note")
    if note:
        text += f"[WORK NOTE {note.get('id', 'n' + str(t))}]\n{note['body']}\n"
    return text + f"QUESTION (T{t}): {turn['question']}"
```

**E-turn_block** — `experiments/ptr-engine/longrun/run_longrun.py:206-207`

```python
def turn_block(t: int, turn: dict, answer: str) -> str:
    return f"{turn_user(t, turn)}\nANSWER (T{t}): {answer}"
```

**E-FIXTURE** — `experiments/ptr-engine/tools/det_verify.py:60-60`

```python
FIXTURE = os.path.join(LONGRUN, "fixtures", "LR-01.json")
```

**E-CHECK_ORDER** — `experiments/ptr-engine/tools/det_verify.py:74-76`

```python
CHECK_ORDER = ("cp.0.t12", "cp.1.t24", "cp.2.t46", "acc.cp1", "acc.cp2", "acc.cp3",
               "acc.1", "acc.2", "acc.3", "acc.4", "acc.n2b", "acc.n3b..acc.n3e",
               "repair.t30")
```

**E-CHECK_WHY** — `experiments/ptr-engine/tools/det_verify.py:568-580`

```python
CHECK_WHY = {
    "cp.0.t12": "literal value of DEFAULT_MAX_REFS, read by ast.literal_eval",
    "cp.1.t24": "ast.ClassDef count matching the fixture's own class pattern",
    "cp.2.t46": "callee + keyword names of the single record_refusal call in _refuse",
    "acc.cp1": "asserts the same AST-derived DEFAULT_MAX_REFS value as cp.0.t12; its "
               "own probes compare against the derived value, never the fixture string",
    "acc.cp2": "asserts the same AST-derived Ptr* class count as cp.1.t24; own probes",
    "acc.cp3": "asserts the same AST-derived call shape as cp.2.t46; own probes",
    "acc.1": "DEFAULT_MAX_REFS == 64, the same AST fact as acc.cp1 (a distinct "
             "fixture entry, so it is counted separately); own probes",
    "acc.4": "ast.FunctionDef count of `def test_*` in the acc.n3d pinned path "
             "(tests/test_scope.py), compared as a number; own probes",
}
```

**E-answer_slot_end** — `experiments/ptr-engine/tools/det_verify.py:136-146`

```python
def answer_slot_end(segment):
    """End of the leading clause after the marker: up to `;` or a sentence period."""
    lead = len(segment) - len(segment.lstrip())
    end = len(segment)
    semi = segment.find(";", lead)
    if semi >= 0:
        end = min(end, semi)
    dot = re.search(r"\.(?=\s|$)", segment[lead:])
    if dot:
        end = min(end, lead + dot.start())
    return end
```

**E-request_ledger_main** — `experiments/ptr-engine/tools/request_ledger.py:787-854`

```python
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.cap < 0 or args.reserve < 0 or args.would_spend < 0:
        print("usage error: --cap, --reserve and --would-spend must be >= 0", file=sys.stderr)
        return EXIT_USAGE
    if args.reserve > args.cap:
        print(
            f"usage error: --reserve {args.reserve} exceeds --cap {args.cap} (no headroom exists)",
            file=sys.stderr,
        )
        return EXIT_USAGE

    pattern = resolve_pattern(args.pattern)
    paths = sorted(globmod.glob(pattern), key=lambda p: os.path.basename(p))
    if not paths:
        print(f"usage error: no row files matched {pattern!r}", file=sys.stderr)
        return EXIT_USAGE

    try:
        report = build_report(paths, args.cap, args.reserve, args.would_spend)
    except RowsUnreadable as exc:
        print(f"row file error: {exc}", file=sys.stderr)
        print("nothing counted: an unreadable row file makes the total unknowable", file=sys.stderr)
        return EXIT_ROWS

    payload = json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n"

    if args.write:
        parent = os.path.dirname(os.path.abspath(args.write))
        if parent and not os.path.isdir(parent):
            print(f"usage error: output directory does not exist: {parent}", file=sys.stderr)
            return EXIT_USAGE
        try:
            with open(args.write, "w", encoding="utf-8") as handle:
                handle.write(payload)
        except OSError as exc:
            print(f"usage error: cannot write {args.write}: {exc}", file=sys.stderr)
            return EXIT_USAGE

    if not args.quiet:
        print_table(report)
        if args.json:
            print(payload, end="")

    budget = report["budget"]
    if not budget["within_budget"]:
        print(
            "OVER BUDGET: "
            f"spent={budget['spent']} + would_spend={budget['would_spend']} = {budget['projected']} "
            f"> cap={budget['cap']} - reserve={budget['reserve']} = {budget['headroom']} "
            f"(over by {budget['projected'] - budget['headroom']}) "
            f"[spent={budget['spent']} would_spend={budget['would_spend']} "
            f"cap={budget['cap']} reserve={budget['reserve']} headroom={budget['headroom']}] "
            f"(spent is the RAW count; the de-duplicated diagnostic figure is "
            f"{budget['spent_deduplicated']} and is NOT deducted -- the duplicate rule is "
            f"unsound as a request-identity test)",
            file=sys.stderr,
        )
        return EXIT_OVER

    if not args.quiet:
        print(
            f"within budget: {budget['projected']} <= {budget['headroom']} "
            f"({budget['remaining']} left; spent is the RAW count, de-duplicated diagnostic "
            f"{budget['spent_deduplicated']} is NOT deducted)",
        )
    return EXIT_OK
```

**E-grade_v5_main** — `experiments/ptr-engine/longrun/grade_v5.py:1081-1113`

```python
def main(argv=None):
    ap = argparse.ArgumentParser(description="ANSWER-CONTRACT v5 grader (offline)")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    fixture = load_fixture(args.fixture)
    rows = [json.loads(line) for line in open(args.rows, encoding="utf-8") if line.strip()]
    doc = grade_rows(fixture, rows)
    doc["rows_file"] = args.rows
    doc["fixture_file"] = args.fixture
    # Stamp BEFORE the file is opened. If the stamp cannot be computed the run
    # refuses (exit 3) instead of emitting a document nobody can date.
    try:
        stamp_document(doc, args.rows)
    except StampError as exc:
        sys.stderr.write("grade_v5: refusing to write an unstamped document: %s\n" % exc)
        return 3
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
    for arm, a in doc["arms"].items():
        print("%-20s acc=%s decidable=%d(pass %d, fail %d) undecidable=%d "
              "missing=%d text=%d verified=%s reasons=%s" % (
            arm, a["checkpoint_accuracy"], a["decidable"], a["passed"], a["failed"],
            a["undecidable"], a["missing"], a["text_reported"], a["verified_success"],
            ",".join(x["reason"] for x in a["failing_reasons"]) or "-"))
    for c in doc["cells"]:
        print("  %-12s T%-3d %-6s %-24s asserted=%r expected=%r  [%s]" % (
            c["id"], c["turn"], c["verdict"], c["reason"], c["asserted"], c["expected"],
            (c["derivation"].get("text") if isinstance(c["derivation"], dict) else "")))
    return 0
```

**E-analyze_stats_main** — `experiments/ptr-engine/longrun/analyze_stats.py:1620-1842`

```python
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Per-arm n / p50 / p95-with-CI / accuracy-with-Wilson CI / "
                    "exact McNemar. Refuses to print a bare point estimate.")
    ap.add_argument("--rows", nargs="+", default=None,
                    help="one or more row JSONL files")
    ap.add_argument("--json", default=None, help="write the analysis as JSON here")
    ap.add_argument("--grade", default=None,
                    help="grade_v5.py output JSON: accuracy population comes from "
                         "its checkpoint cells, never re-derived from rows")
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    ap.add_argument("--assume-comparable", action="store_true",
                    help="OVERRIDE LOUDLY: compare cells whose load-bearing "
                         "provenance differs. The run records provenance_override: "
                         "true and the differing fields in stdout AND in --json, so "
                         "the override is visible in the artefact. There is no "
                         "environment variable and no default-on.")
    ap.add_argument("--check-definition", action="store_true",
                    help="report (and exit 3 on) any row set that violates the "
                         "per-turn TTFT definition contract; exits 0 when every "
                         "cell can be selected exactly as defined")
    ap.add_argument("--manifest", action="append", default=None,
                    help="cell manifest carrying usable_for (repeatable); the "
                         "primary carrier, and it outranks the census")
    ap.add_argument("--no-census", action="store_true",
                    help="do not consult measure/GRID-CELL-SANITY.json for an "
                         "unstamped cell's usable_for")
    ap.add_argument("--stamp-rows", default=None,
                    help="write this cell's usable_for into its manifest and exit")
    ap.add_argument("--usable-for", default=None,
                    help="comma-separated analyses for --stamp-rows; empty string "
                         "stamps usable_for: [] (cell is excluded by name)")
    ap.add_argument("--usable-for-reason", default=None)
    ap.add_argument("--manifest-out", default=None,
                    help="manifest to stamp; default: the one whose rows_path "
                         "matches --stamp-rows")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pooled", action="store_true",
                    help="READ A DERIVED ARTEFACT: pool_reps.py writes pooled-*.jsonl "
                         "with derived: true; without this flag such a file is refused "
                         "so a derived view is never read as a measured cell")
    args = ap.parse_args(argv)

    if args.stamp_rows:
        uf = [x.strip() for x in (args.usable_for or "").split(",") if x.strip()]
        man = write_cell_manifest_usable_for(
            args.stamp_rows, uf, reason=args.usable_for_reason,
            manifest_path=args.manifest_out, dry_run=args.dry_run)
        print("stamped usable_for=%r into %s%s"
              % (man.get(USABLE_FOR_FIELD),
                 os.path.basename(man.get("_manifest_path") or args.manifest_out
                                  or args.stamp_rows),
                 "  (dry-run, nothing written)" if args.dry_run else ""))
        return 0
    if not args.rows:
        raise SystemExit("--rows is required (or --stamp-rows)")

    # HONESTY RULE (POOL-REPS-TOOL): a derived pooled artefact is not a measurement.
    # It is readable only when the caller says, explicitly, that it wants the derived
    # view -- otherwise a derived n=144 would silently outrank the measured cells it
    # was built from.
    if not args.pooled:
        for path in args.rows:
            if is_derived_rows(path):
                raise SystemExit(
                    "refused: %s is a DERIVED artefact (derived=true, "
                    "purpose=%r), not a measured cell; pass --pooled to analyse the "
                    "pooled view explicitly" % (os.path.basename(path), "H1 pooled R-all"))

    grade = None
    if args.grade:
        with open(args.grade, encoding="utf-8") as fh:
            grade = json.load(fh)
        if not isinstance(grade, dict) or "cells" not in grade:
            raise SystemExit("--grade %s is not a grade_v5 document (no `cells`)"
                             % args.grade)

    rows, files = [], []
    for path in args.rows:
        per_file = []
        with open(path, "rb") as fh:
            blob = fh.read()
        for line in blob.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # half-written tail: never fatal
            if isinstance(obj, dict):
                per_file.append(obj)
        files.append((path, len(per_file), per_file))
        rows.extend(per_file)

    print("analyze_stats  rows=%d  files=%d" % (len(rows), len(files)))
    print("  definition[%s]: %s" % (TTFT_DEFINITION_VERSION, TTFT_DEFINITION))
    for path, count, _per_file in files:
        print("  %s  rows=%d" % (os.path.basename(path), count))

    if args.check_definition:
        bad = 0
        for path, _count, file_rows in files:
            violations = definition_violations(file_rows)
            if violations:
                bad += 1
                print("  DEFINITION VIOLATION  %s  %d finding(s)"
                      % (os.path.basename(path), len(violations)))
                for v in violations:
                    print("    - %s" % v)
            else:
                print("  definition ok  %s" % os.path.basename(path))
        if bad:
            print("  %d file(s) violate the per-turn TTFT definition" % bad)
            return 3
        print("  every file satisfies the per-turn TTFT definition")
        return 0

    # Per-arm provenance, resolved through the SAME row->manifest->cell ladder
    # `row_provenance.py` uses. An arm fed by two files whose provenance differs
    # gets an UNKNOWN cell for the differing fields: the merged arm genuinely has
    # no single provenance, and refusing is the honest answer.
    # --- usable_for: exclude unusable cells BY NAME before any statistic ------
    manifests = load_cell_manifests(args.manifest)
    files, cell_usability = select_usable_cells(
        files, manifests=manifests, sanity=(False if args.no_census else None))
    for rec in cell_usability:
        if rec["excluded"]:
            print("  usable_for EXCLUDED  %s  %d row(s) NOT analysed  source=%s  "
                  "usable_for=[]  reason=%s"
                  % (rec["name"], rec["rows"], rec["source"],
                     rec["reason"] or "(none recorded)"))
        elif rec["usable_for"] is None:
            print("  usable_for unstamped  %s  (included: no usability stamp on "
                  "disk -- not a certification)" % rec["name"])
        else:
            print("  usable_for %s  %s  source=%s" %
                  (rec["usable_for"], rec["name"], rec["source"]))
    if not files:
        names = ", ".join(r["name"] for r in cell_usability) or "(none)"
        print("  usable_for EXCLUDED every cell: no usable cells (%s)" % names)
        raise SystemExit("no usable cells: every input cell is stamped "
                         "usable_for: [] -- refusing rather than printing an "
                         "empty table as success (%s)" % names)
    rows = [row for _p, _c, file_rows in files for row in file_rows]

    provenance = {}
    for path, _count, file_rows in files:
        for arm, cell in provenance_cells(file_rows, path).items():
            if arm not in provenance:
                provenance[arm] = dict(cell)
                continue
            prev = provenance[arm]
            provenance[arm] = {
                n: (prev[n] if prev[n] == cell[n] else PROVENANCE_UNKNOWN)
                for n in PROVENANCE_LOAD_BEARING}

    if args.assume_comparable:
        print("  !! PROVENANCE OVERRIDE: --assume-comparable is ON; every "
              "comparison below whose load-bearing provenance differs is computed "
              "ANYWAY and records provenance_override: true + the differing fields.")

    claim_refusal = None
    for path, _count, file_rows in files:
        try:
            require_comparable_claim(file_rows, os.path.basename(path), path)
        except IncomparableClaim as exc:
            if claim_refusal is None:
                claim_refusal = exc
            print("  CLAIM REFUSAL  %s" % exc)
    report = analyze(rows, resamples=args.resamples, grade=grade,
                     provenance=provenance,
                     assume_comparable=args.assume_comparable,
                     claim_refusal=claim_refusal, rows_path=None)
    for arm in sorted(report["arms"]):
        print("")
        for line in _format_arm(report["arms"][arm]):
            print(line)
    if report["pairs"]:
        print("")
        for rec in report["pairs"]:
            for line in _format_pair(rec):
                print(line)
    if report["quantile_comparisons"]:
        print("")
        for rec in report["quantile_comparisons"]:
            for line in _format_quantile_comparison(rec):
                print(line)

    incomparable = sum(1 for r in report["quantile_comparisons"] + report["pairs"]
                       if r.get("refused_kind") == INCOMPARABLE_PROVENANCE)
    if incomparable:
        print("")
        print("  %d comparison(s) REFUSED as %s: no interval, no verdict"
              % (incomparable, INCOMPARABLE_PROVENANCE))

    serialisable = {"n_rows": report["n_rows"], "arms": {}, "pairs": [],
                    "quantile_comparisons": report["quantile_comparisons"],
                    "incomparable_provenance_count": incomparable,
                    "definition": report["definition"],
                    "provenance_override": bool(args.assume_comparable),
                    "assume_comparable": bool(args.assume_comparable),
                     "cell_usability": cell_usability}
    if args.assume_comparable:
        serialisable["provenance_override_differing"] = sorted({
            f for rec in report["quantile_comparisons"] + report["pairs"]
            if rec.get("provenance_override")
            for f in (rec.get("provenance") or {}).get("differing") or []})
    for arm, e in report["arms"].items():
        serialisable["arms"][arm] = {
            "n_rows": e["n_rows"],
            "provenance": e["provenance"],
            "definition_fallback": e["definition_fallback"],
            "ttft": {k: v for k, v in e["ttft"].items() if k != "values"},
            "p50": {k: v for k, v in e["p50"].items() if k != "values"},
            "p95": {k: v for k, v in e["p95"].items() if k != "values"},
            "accuracy": e["accuracy"],
        }
    serialisable["pairs"] = report["pairs"]
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(serialisable, fh, indent=1, sort_keys=True)
    return 0
```

**E-run_a_star_main** — `experiments/ptr-engine/tools/run_a_star.py:636-835`

```python
def main():
    global FIX
    ap = argparse.ArgumentParser(description="RUN-A* / GRID-SHAPE driver")
    ap.add_argument("--tools", default="", metavar="LIST",
                    help="tool channel(s) to enable through the shim; '' (default) = "
                         "the historical tools-off launch, unchanged; 'read_file' = "
                         "the GRID-SHAPE corrected shape")
    ap.add_argument("--cell", type=int, default=0,
                    help="run only cell N (1..%d); 0 = the whole grid in order"
                         % len(CELLS))
    ap.add_argument("--dry-run", action="store_true",
                    help="pass --dry-run to every cell.py launch and send nothing")
    ap.add_argument("--budget", type=int, default=108,
                    help="per-cell ledger allocation handed to cell.py (default 108); the stage 3/7 gate compares ceil(would_send_total x 1.10) against it, so this is a ledger allocation, not a request ceiling")
    ap.add_argument("--hypothesis", default=None,
                    metavar="H1|H2|H3|smoke|plumbing",
                    help="the claim every cell declares (default H2; the canary spells "
                         "smoke, which makes no claim and can never be pooled)")
    ap.add_argument("--canary", action="store_true",
                    help="the 12-turn era-B canary: ONE 12-turn cell per arm "
                         f"(4 arms = 48 requests), --hypothesis smoke, --max-wall {CANARY_MAX_WALL} "
                         "(RUN-A-STAR-2's gate before the grid)")
    ap.add_argument("--max-wall", type=float, default=None,
                    help="per-cell wall ceiling handed to cell.py "
                         f"(default 2880; {CANARY_MAX_WALL} when --canary)")
    ap.add_argument("--fixture", default=FIX,
                    help="fixture path, repo-relative (default: the v8 LR-01 grid fixture)")
    a = ap.parse_args()
    FIX = a.fixture
    # LAUNCHER-GEN5-WIRE: both records are GATES and they fire before any plan is
    # built, so a launcher that cannot read (or does not agree with) its records
    # never reaches the cell loop -- and never prints a plan as if it could.
    pinned_digest()
    grid_record()
    # CANARY-ARGV-WIRING: the claim is resolved ONCE, here, and lands in the argv.
    if a.canary:
        a.hypothesis = a.hypothesis or "smoke"
        a.max_wall = CANARY_MAX_WALL if a.max_wall is None else a.max_wall
        a.turns = 12
        # CANARY-ARMS-WIRING: one 12-turn cell per arm. The priced component is
        # 4 x 12 = 48 requests. The canary used to be `a.cell = a.cell or 1` -- ONE
        # arm -- so pointer-stable was gated and the other three reached the grid
        # ungated. --cell no longer narrows the canary; it is ignored with a note.
        cells = [(n, arm, rep) for n, (arm, rep) in enumerate(CELLS, 1) if rep == 1]
        if a.cell:
            say("canary ignores --cell %d: the canary is one 12-turn cell per arm "
                "(arms=%d cells=%s turns=%d requests=%d)"
                % (a.cell, len(cells), ",".join(str(c[0]) for c in cells),
                   a.turns, len(cells) * a.turns))
    else:
        a.hypothesis = a.hypothesis or "H2"
        a.max_wall = 2880 if a.max_wall is None else a.max_wall
        a.turns = 48
        cells = [(n, arm, rep) for n, (arm, rep) in enumerate(CELLS, 1)
                 if not a.cell or n == a.cell]
    if a.tools and a.tools != "read_file":
        raise SystemExit("unsupported --tools %r; run_longrun.py supports read_file "
                         "only (run_longrun.py:2798)" % a.tools)
    if not cells:
        raise SystemExit("--cell must be 1..%d" % len(CELLS))
    canary_requests = len(cells) * a.turns if a.canary else 0
    if a.canary:
        say("canary arms=%d cells=%s turns=%d requests=%d claim=%s"
            % (len(cells), ",".join(str(c[0]) for c in cells), a.turns,
               canary_requests, a.hypothesis))
    if a.tools:
        say("tools=%s shim=%s" % (a.tools, ensure_shim()))
    if a.dry_run:
        # OFFLINE: cell.py --dry-run prints G1/G2/G3 and sends nothing.
        # DRYRUN-REFUSAL (LAUNCH-CANARY-WALL): cell.py's dry run always exits 0 --
        # its own documented contract is that "exit 0 means the PREVIEW ran, not that
        # the gates allow" (cell.py:1964-1975, docs/GATE-CHAIN.md §7). Counting `rc`
        # alone therefore printed `refused=0` for a canary whose G2 line said
        # `WOULD-REFUSE`, i.e. a blocked launch reported green. A gate's WOULD-REFUSE
        # verdict is the refusal: it counts, and it makes the launcher exit non-zero.
        # Exit 1 is the code this launcher already uses for a dry run that saw a cell
        # fail (`return 0 if not bad else 1`); 2 stays cell.py's preflight/G3 code
        # (cell.py:14-15, exit_codes.EXIT_TABLE) and is not the launcher's to reuse.
        bad = 0
        # LAUNCHER-GEN5-WIRE: the price comes from the record and is printed BEFORE
        # any cell is previewed, beside the remaining figure it is drawn from, so the
        # dry run and the record cannot disagree in opposite directions. A record
        # without price.total refuses by name (grid_record), never a blank line.
        _rem, _basis, _cap = remaining_basis()
        say(price_line(_rem, _basis, _cap, cells=len(cells)))
        for n, arm, rep in cells:
            rec = run_cell(arm, rep, n, a.tools, a.budget, a.hypothesis,
                           dry_run=True, turns=a.turns, max_wall=a.max_wall)
            refused = bool(rec["would_refuse"])
            say("DRY cell %d %s r%d rc=%s%s %s"
                % (n, arm, rep, rec["rc"],
                   " WOULD-REFUSE=%d" % len(rec["would_refuse"]) if refused else "",
                   " | ".join(rec["gates"]) or "no gate line"))
            bad += 1 if (rec["rc"] != 0 or refused) else 0
        say("DRY END cells=%d refused=%d requests=0 claim=%s turns=%d max_wall=%s "
            "canary_arms=%d canary_requests=%d" %
            (len(cells), bad, a.hypothesis, a.turns, a.max_wall, len(cells),
             canary_requests))
        return 0 if not bad else 1
    spent0 = spend()
    base_remaining, rem_basis, rem_cap = remaining_basis()
    say(price_line(base_remaining, rem_basis, rem_cap, cells=len(cells)))
    results, warm, stops = [], {}, []
    say("start spent_rows=%d cells=%d fixture=%s tools=%s canary=%s claim=%s "
        "turns=%d max_wall=%s remaining_basis=%s" %
        (spent0, len(cells), FIX, a.tools or "off", a.canary, a.hypothesis,
         a.turns, a.max_wall, rem_basis))
    jline(event="grid_start", spent_rows=spent0, cells=len(cells),
          budget_per_cell=a.budget, hypothesis=a.hypothesis, tools=a.tools or "off",
          canary=a.canary, turns_per_cell=a.turns, max_wall=a.max_wall,
          canary_requests=canary_requests,
          wall_cap_expected=CAP_WALL, fetch_allowance=FETCH_ALLOWANCE if a.tools else 0)
    for n, arm, rep in cells:
        remaining = base_remaining - (spend() - spent0)
        if remaining < 264:
            stops.append({"rule": 1, "remaining": remaining, "before_cell": n})
            say("STOP rule 1: remaining=%d" % remaining)
            jline(event="stop_rule_1", remaining=remaining, before_cell=n)
            break
        # GRID-STAMP-WIRING: the previous cell must SHOW its stamp before this cell
        # is allowed to spend a request (exit 4, naming the manifest path).
        if results:
            check_previous_stamp(results[-1], n)
        if rep == 1 and arm not in warm:
            warm[arm] = warmup(arm)
        rec = run_cell(arm, rep, n, a.tools, a.budget, a.hypothesis,
                       turns=a.turns, max_wall=a.max_wall)
        rec["remaining_after"] = base_remaining - (spend() - spent0)
        rec["warmup_ms"] = warm.get(arm)
        results.append(rec)
        jline(event="cell", **{k: rec.get(k) for k in
                               ("cell", "arm", "rep", "rc", "dur_s", "rows_file",
                                "design_cap_tokens", "tools_in_manifest", "stats",
                                "analysis", "treatment_preflight", "remaining_after",
                                "usable_for_stamp")})
        save(results, {"spent_rows_before": spent0, "warmups": warm, "stops": stops,
                       "tools": a.tools or "off", "budget_per_cell": a.budget,
                       "hypothesis": a.hypothesis})
        ar = rec.get("analysis") or {}
        say("CELL %d %s r%d rc=%s dur=%ss remaining=%s p95=%s acc=%s markers=%s" % (
            n, arm, rep, rec["rc"], rec["dur_s"], rec["remaining_after"],
            (ar.get("p95") or {}).get("point"), ar.get("accuracy"),
            (rec.get("stats") or {}).get("markers")))
        if rec["rc"] != 0:
            stops.append({"rule": 7, "cell": n, "rc": rec["rc"]})
            say("STOP rule 7: cell %d exited %s" % (n, rec["rc"]))
            jline(event="stop_rule_7", cell=n, rc=rec["rc"], tail=rec["stdout_tail"])
            break
        if rec.get("design_cap_tokens") not in (None, CAP_WALL):
            stops.append({"rule": "wall-source", "cell": n,
                          "design_cap_tokens": rec.get("design_cap_tokens")})
            say("STOP wall source: %r" % rec.get("design_cap_tokens"))
            break
        if a.tools and rec.get("tools_in_manifest") not in (None, ["read_file"]):
            stops.append({"rule": "tools-not-on-the-wire", "cell": n,
                          "tools_in_manifest": rec.get("tools_in_manifest")})
            say("STOP tools not on the wire: %r" % rec.get("tools_in_manifest"))
            jline(event="stop_tools_missing", cell=n,
                  tools_in_manifest=rec.get("tools_in_manifest"))
            break
        if rep == 1:
            m = (rec.get("stats") or {}).get("markers") or {}
            need = {"transcript-grow": m.get("evicted_turns", 0) > 0,
                    "transcript-compact": m.get("digest_rows", 0) > 0,
                    "lease-reopen": m.get("lease_ge2_turns", 0) > 0,
                    "pointer-stable": True}[arm]
            if not need:
                stops.append({"rule": "precondition-10", "arm": arm, "markers": m})
                say("STOP precondition 10: %s cell 1 no mechanism %s" % (arm, m))
                jline(event="stop_mislabel", arm=arm, markers=m)
                break
        if n == 4:
            ga = [x for x in results if x["arm"] == "pointer-stable" and x["rep"] == 1][0]
            gb = [x for x in results if x["arm"] == "transcript-grow" and x["rep"] == 1][0]
            if ga.get("grade_path") and gb.get("grade_path"):
                v = h3_veto(os.path.join(ROOT, ga["grade_path"]),
                            os.path.join(ROOT, gb["grade_path"]))
                say("H3 rep-1 %s" % json.dumps(v))
                jline(event="h3_rep1", **v)
                if v["veto"]:
                    stops.append({"rule": 4, **v})
                    say("STOP rule 4: H3 veto at rep 1")
                    break
    spent1 = spend()
    save(results, {"spent_rows_before": spent0, "spent_rows_after": spent1,
                   "new_requests": spent1 - spent0,
                   "remaining": base_remaining - (spent1 - spent0),
                   "remaining_basis": rem_basis, "remaining_cap": rem_cap,
                   "warmups": warm,
                   "stops": stops, "cells_planned": len(cells),
                   "tools": a.tools or "off", "budget_per_cell": a.budget,
                   "hypothesis": a.hypothesis})
    jline(event="grid_end", cells_run=len(results), spent_rows_before=spent0,
          spent_rows_after=spent1, new_requests=spent1 - spent0,
          remaining=base_remaining - (spent1 - spent0), remaining_basis=rem_basis,
          remaining_cap=rem_cap, warmups=warm, stops=stops)
    say("END cells=%d new_requests=%d remaining=%d remaining_basis=%s cap=%s "
        "stops=%s" % (len(results), spent1 - spent0,
                    base_remaining - (spent1 - spent0), rem_basis, rem_cap, stops))
    return 0
```

**E-verdict_scope_run** — `experiments/ptr-engine/tools/verdict_scope.py:198-231`

```python
def run(paths, argv, record_path=None, stream=None):
    """freeze -> run -> classify -> scope block. -> (payload, exit code)."""
    stream = stream or sys.stdout
    if not paths:
        raise Refused("refusing a verdict with no bytes: `run` needs at least one --paths "
                      "value (a row that names no bytes is the defect this tool exists for)")
    if not argv:
        raise Refused("`run` needs a command after `--`: nothing to run, nothing to judge")
    record_path = record_path or os.path.join(
        tempfile.gettempdir(), "verdict_scope.%d.%d.json" % (os.getpid(), time.time_ns()))
    try:
        record, code = tree_freeze.wrap(paths, record_path, argv, stream=stream,
                                       verdict_row=False)
    except tree_freeze.Refused as exc:
        raise Refused(str(exc))
    try:
        with open(record["freeze_before"], encoding="utf-8") as fh:
            before_document = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refused("the wrapper's before freeze is unreadable: %s" % (exc,))
    payload, block = payload_for(record, before_document, before_document.get("root"), stream)
    stream.write(json.dumps(payload, separators=(",", ":"), sort_keys=False) + "\n")
    stream.write("verdict=%s exit=%s moved=%d scope_paths=%d head_is_meaningful=%s record=%s\n"
                 % (block["verdict"], payload["exitCode"], len(block["moved"]),
                    len(block["paths"]), payload["head_is_meaningful"], record_path))
    if block["moved"]:
        stream.write("verdict_scope: UNSTAMPED -- %d path(s) moved while the command ran; "
                     "this row names bytes that no longer exist. Re-run against the "
                     "settled tree; do not re-read this run as a verdict.\n"
                     % len(block["moved"]))
        return payload, EXIT_TREE_MOVED
    if record.get("exit_code") is None:
        return payload, EXIT_USAGE
    return payload, int(record["exit_code"])
```

**E-system_prompt_line** — `experiments/ptr-engine/longrun/run_longrun.py:1072-1074`

```python
        return [{"role": "system", "content": self.fixture["system_prompt"]},
                {"role": "user", "content": user}]

```

**E-smoke_help** — `experiments/ptr-engine/longrun/run_longrun.py:2848-2851`

```python
    ap.add_argument("--smoke", action="store_true",
                    help="4 arms x 3 turns = 12 requests; per-row table with reasoning/content "
                         "token split and answer_source; non-zero exit if any row has "
                         "answer_source == 'none'")
```

**E-budget_projection** — `experiments/ptr-engine/longrun/run_longrun.py:476-480`

```python
    budget = n_turns + (expected_digests(fixture) if arm == "transcript-compact" else 0)
    if tools_enabled(cfg):
        budget += fetch_rounds_per_arm(cfg)
    return budget

```

**E-durable_spend** — `experiments/ptr-engine/longrun/run_longrun.py:2286-2289`

```python
        fetch_rounds_used = max(frozen, derived)
        print(f"resume: fetch rounds already spent={fetch_rounds_used}/"
              f"{fetch_rounds_per_arm(cfg)} (manifest={frozen} derived_from_rows={derived}); "
              "--resume does not reset the counter")
```

**E-prediction_row** — `experiments/ptr-engine/measure/run_cells.py:14-16`

```python
* A PREDICTION row is appended and fsynced BEFORE each measure request: ``P1`` from
  the padding arithmetic, ``L`` from the pre-registered framing constant (LAW.md s2).
  A prediction recorded after the fact is worthless, so it is its own row.
```

### F. Residual

**Line numbers are not stable identifiers.** They are offsets into a file that is still growing (`run_longrun.py`:
1,653 → 3,008 lines in one day), and every append silently falsifies citations below it. A future map should anchor
on `file::symbol` (`experiments/ptr-engine/longrun/run_longrun.py::make_row`), which survives movement; the guard
already prefers the symbol to the line when both are available. **Converting the whole document to symbol anchors is
deliberately not done tonight** — the body is historical evidence, and a wholesale rewrite would replace what the map
claimed with what it claims now, losing the drift record this section preserves.

