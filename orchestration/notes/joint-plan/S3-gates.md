# S3 — Validity gates 0.1–0.11 audit (offline, 0 requests)

Scope: `/home/zer0null/research extractor` (branch research/next-candidates-2026-10-24 @ f17663d). No files modified. No requests sent.

## 1. Per-gate verdicts

| Gate | Verdict | Evidence | Missing capability / smallest close |
|---|---|---|---|
| 0.1 positive control can pass | **FAIL** (owner decision) | `longrun/QUALITY-POSITIVE-CONTROL.md` truth table: pos-full verified_success=false, 0/3 accuracy; pos-exact-only passes 3/3; `score_longrun.py:174-176` exact whole-content match vs fixture answer_marker not read (`score_longrun.py` 0 hits for answer_marker); `grade_v2.py` accepts prose so graders mutually exclusive. | Align one contract: either score_longrun reads `answer_marker`/structured `answers`, or fixture checkpoints use `match: contains`. Files: `longrun/score_longrun.py`, `longrun/tasks-v3/runtime-v3/LR-01.v3.json` (fixture change mints generation, approval (d)). Effort: medium. |
| 0.2 ≥12 decidable checkpoints gradeable | **PASS** (code) / fixture-dependent | `longrun/grade_v5.py:_derive_one` now has constant_value/count_classes/call_inside_function/call_at_line/no_attr_call_inside_function. `derive_truth` yields 12 cells on `tasks-v6/LR-01.v7.json` (verified). `docs/CHECKPOINT-COVERAGE.md §6` records the 4 that historically needed branches. | On `tasks-v5/runtime-v5/LR-01.v6.json` the same 4 (cp.5.t14, cp.7.t20, cp.11.t42 NONE; cp.10.t36 call_at_line) now derive; v7 adds `answer_form`. No code change needed. |
| 0.3 fixture wall priced from measured growth | **PARTIAL / UNVERIFIED** | Turn counts verified against fixture files: LR-01=48, LR-02=64, LR-03=56, LR-04=40, LR-05=72, LR-06=60. `run_longrun.py` wall logic at :1153-1241; `project_wallclock.py`. Gen-6 wall was declared padding (10,616 vs live base 5,628-6,139). | Dry-run evidence that each treatment reaches its wall inside its horizon is not on disk. Assess with `python3 experiments/ptr-engine/longrun/run_longrun.py --dry-run --fixture ... --arm ... --reps 1` (exit 0 prints would_send_total) plus `project_wallclock.py`. Effort: small. |
| 0.4 four fingerprints frozen | **FAIL** | Manifest sample `manifests/arm-rp-20261026T0335Z-transcript-grow-r1.json`: fields model.name/engine/endpoint, renderer (api/max_tokens/etc), engine_flags, fixture.sha256, prereg.sha256. No model revision/quant digest, tokenizer file hash, chat-template hash, renderer module content digest, engine image digest. | Extend `run_longrun.py:build_manifest` (:1498) and `cell.py:stage_harness` (:374) to compute+freeze all four; placeholders are a hard stop. Files: `longrun/run_longrun.py`, `longrun/cell.py`. Effort: medium. |
| 0.5 replicate identity | **PARTIAL** | `run_longrun.py` run_id includes rep (`{run_base}-{arm}-r{rep}`, :3093); row carries `"rep": rep` (:1949); `read_cell_rows` filters by (run_id,task_id,arm,rep) (:2133). | No pre-analysis assertion that row count = cells × turns × reps. Add assertion in `report_run` (:2853) or `analyze_stats`. Files: `longrun/run_longrun.py`, `longrun/analyze_stats.py`. Effort: trivial. |
| 0.6 activation gating | **PARTIAL** | `run_longrun.py:treatment_fire_turns` (:1390), `treatment_refusals` (:1420), `check_treatments` (:1464) gate launch; `tools/run_a_star.py:541` markers evicted_turns/digest_rows/masked_rows/fetch_rows. | Predicates are not stamped on run rows and exclusion is not computed from a stamp (run_longrun.py make_row :1877 carries no activation markers; no retrieval_outcomes/oracle_injections). Add activation fields to make_row and a computed exclusion rule. Files: `longrun/run_longrun.py`, `longrun/analyze_stats.py`. Effort: medium. |
| 0.7 budget preflight | **PARTIAL** | `longrun/cell.py:stage_budget` (:~760) prices via runner `--dry-run` and parses would_send_total; `exit_codes.EXIT_PREFLIGHT=2`; `tools/request_ledger.py` implements exclusions. | No single ledger-rebuild + per-arm arithmetic + cap-set-before-first-call path verified; `REQUEST-LEDGER.json` is a 2026-10-28 snapshot. Reconcile ledger (R3) before any call. Files: `tools/request_ledger.py`, `longrun/cell.py`. Effort: small. |
| 0.8 independent verifier assigned | **PASS** | `longrun/score_longrun.py` exit codes EXIT_TAMPERED=2, EXIT_INPUT=3 (lines 59, 1009-1010); tamper scope recorded. | Verifier process/person still must be assigned by operator (process exists). |
| 0.9 scorer can express retrieval miss + abstention | **FAIL** | Grep `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` in `longrun/*.py` and `longrun/tools/*.py` = 0 matches. `KINDS = ("artifact","fact","constraint","repair")` at score_longrun.py:58; no abstention/retrieval check kind. | Add retrieval-outcome vocabulary (OK/NOT_FOUND/STALE_OR_REVOKED/SCOPE_UNGRANTED) to run rows + scorer kinds/verdicts + red→green control (fabricated answer must fail before abstention passes). Files: `longrun/score_longrun.py`, `longrun/run_longrun.py` (make_row), grade path. Effort: medium. |
| 0.10 prototype extension offline-deterministic | **PARTIAL** | Implemented+tested: alignment append planner `quantise.choose_padding`/`predict_billed` (unit tests `tests/test_quantise.py`); deterministic index digest across 2 processes/2 roots (`tests/test_determinism.py`, compile.py). | Not implemented/tested: fetch batching by body tokens; retrieval-outcome vocabulary; deterministic resume unit test (resume code exists in run_longrun.py:2139 but no test). Add tests + implementation. Files: `ptr_engine/quantise.py`, `longrun/run_longrun.py`, new tests. Effort: medium. |
| 0.11 law package re-derived | **PASS** | Recompute command in `research-seed-concepts/README.md:140-148` reproduces exactly: sglang 301 `{0:218,2048:2,4096:2,6144:2,7680:1,7936:2,8000:8,8064:66}`; vllm 86 `{-1056:1,0:85}` (verified this session). | None. |

## 2. Checkpoint coverage (12 items)

Names (from `docs/CHECKPOINT-COVERAGE.md §2` and `tasks-v6/LR-01.v7.json`):
1. cp.0.t06 (T6, CALL) `ledger.record_resolution(...)` — gradeable (call_inside_function)
2. cp.1.t08 (T8, CALL) `scope.block()` — gradeable
3. cp.2.t12 (T12, NUM) DEFAULT_MAX_REFS=64 — gradeable (constant_value)
4. cp.3.t14 (T14, NONE) resolve() does not call record_refusal() — needs no_attr_call_inside_function branch (now present)
5. cp.4.t18 (T18, NUM) PtrLedger* count=6 — gradeable (count_classes)
6. cp.5.t20 (T20, NONE) _refuse() does not call resolved_count() — needs no_attr branch
7. cp.6.t24 (T24, NUM) Ptr* count=31 — gradeable
8. cp.7.t26 (T26, NUM) PtrLaw* count=5 — gradeable
9. cp.8.t32 (T32, NUM) PtrUnknown* count=2 — gradeable
10. cp.9.t36 (T36, CALL) `ledger.resolved_count()` at line 141 — needs call_at_line branch (now present)
11. cp.10.t42 (T42, NONE) _refuse() does not call scope.block() — needs no_attr branch
12. cp.11.t46 (T46, CALL) `_refuse` calls record_refusal(...) — gradeable

Today all 12 derive in grade_v5 (verified: 12 cells on v7). The 4 that historically required NONE/call_at_line branches are items 4, 6, 10, 11.

## 3. Abstention / retrieval scoring

Claim (`VALIDATION-ROADMAP.md:57`) that `abstain|retrieval_miss|STALE|REVOKED|NOT_FOUND` has 0 matches in scorer: **CONFIRMED** (grep over `longrun/*.py` + `longrun/tools/*.py` = 0). `KINDS` = artifact/fact/constraint/repair only; `grade_v5` has no abstention verdict branch. To close gate 0.9, must add: (a) retrieval-outcome vocabulary on run rows (OK/NOT_FOUND/STALE_OR_REVOKED/SCOPE_UNGRANTED) + masked_entry{ref,since_turn}; (b) scorer kinds/verdicts for `abstained_correctly` and `retrieval_miss`; (c) red→green control: fabricated answer fails the extension before an abstention can pass it. Files: `longrun/score_longrun.py`, `longrun/run_longrun.py` (make_row), `longrun/grade_v5.py`. Effort: medium.

## 4. Fixture wall (turn supply)

Verified against fixture files (not docs):
- LR-01: 48 turns → cannot supply 60-turn cell.
- LR-02: 64 turns → can supply 60.
- LR-03: 56 turns → cannot supply 60.
- LR-04: 40 turns → cannot supply 60 (can supply 30).
- LR-05: 72 turns → can supply 60.
- LR-06: 60 turns → can supply 60.

Thus 60-turn horizon available on 3 tasks (LR-02, LR-05, LR-06) only; 10/30 available on all six. Matches roadmap. Dry-run wall-reachability inside horizon remains UNVERIFIED (command above).

## 5. Gen-7 readiness

Prerequisites from `JOINT-SERVING-CONTEXT-PLAN.md:35` / `docs/STATE.md §1`:
- v9 wall: **NOT implemented** (fixtures exist only through v8; no v9 wall fixture). Effort: medium (owner approval (d)).
- rep identity: **PARTIAL** (run_id + rows carry rep; no pre-analysis row-count assertion). Effort: trivial.
- activation gating: **PARTIAL** (offline treatment_fire_turns + launch gate exist; no runtime activation stamp/exclusion rule). Effort: medium.
- stamp rule: **IMPLEMENTED** (`tools/grader_identity.py`, `tests/test_grader_stamp.py`).

## 6. Offline work order (before first paid request)

1. Gate 0.1 positive-control alignment (owner decision) — `longrun/score_longrun.py`, fixture answer contract. medium.
2. Gate 0.9 abstention/retrieval scorer extension — `longrun/score_longrun.py`, `longrun/run_longrun.py`, `longrun/grade_v5.py`. medium.
3. Gate 0.4 fingerprint freeze in manifest — `longrun/run_longrun.py` (build_manifest), `longrun/cell.py` (stage_harness). medium.
4. Gate 0.10 fetch batching + retrieval vocabulary + resume test — `ptr_engine/quantise.py`, `longrun/run_longrun.py`, new tests. medium.
5. Gate 0.6 activation predicate stamp + computed exclusion — `longrun/run_longrun.py` (make_row), `longrun/analyze_stats.py`. medium.
6. Gate 0.5 rep identity assertion — `longrun/run_longrun.py` (report_run), `longrun/analyze_stats.py`. trivial.
7. Gate 0.7 ledger rebuild + per-arm arithmetic + caps — `tools/request_ledger.py`, `longrun/cell.py`. small.
8. Gate 0.3 dry-run wall verification — `longrun/run_longrun.py --dry-run`, `longrun/project_wallclock.py`. small.
9. Gen-7 fixture v9 wall (approval (d)) — fixtures + adapt_*.py. medium.

No requests, service changes, fixture/grader modifications, or budget changes were performed in this audit.