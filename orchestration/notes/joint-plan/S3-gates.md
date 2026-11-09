# S3 Gates — validity gates 0.1–0.11 audited against code today

Offline audit (0 requests, 0 service changes). Evidence is file+line from the real checkout.

## 1. Per-gate verdicts

| gate | verdict | evidence (file:line) | missing capability / smallest change |
|---|---|---|---|
| 0.1 positive control can pass | **FAIL** | `longrun/QUALITY-POSITIVE-CONTROL.md:1-7` (`PATH-CANNOT-SAY-YES`); `longrun/score_longrun.py:19-23` (`match_answer` exact); `:174-176` (entire turn content compared); fixture `answer_marker` required (`QUALITY-POSITIVE-CONTROL.md:11-12`) | Grader and fixture contract mutually exclusive. Owner decision (fixture/grader change mints a generation). Smallest change: teach `score_longrun.py` the `answer_marker` line, or split a structured `answers` field the scorer reads. |
| 0.2 ≥12 decidable checkpoints all gradeable | **PASS** | `longrun/grade_v5.py:661-696` (`call_at_line` branch); `:700-734` (`no_attr_call_inside_function` NONE branch); verified `derive_truth` returns 12/12 on `tasks-v6/LR-01.v8.json` (run below); `longrun/score_longrun.py:749-797` (`mirror_answer_contract` grades all 12). Stale doc claim of 8/12: `docs/CHECKPOINT-COVERAGE.md:106` | None for code. (Doc is stale; update it.) |
| 0.3 fixture wall priced from measured growth | **FAIL** | `docs/GRID-GAP-DIAGNOSIS.md:7-13,34-94`; `tasks-v6/LR-01.v8.json` `wall_tokens_by_arm` all `10616` priced from declared padding (`wall_tokens_basis.per_arm_rule`); measured rows `rows-cell-transcript-grow-*.jsonl` growth 46.6–97.6 tok/turn ⇒ 48–113 turns to wall | v9 fixture priced from measured growth at live base. Owner decision (mints gen 7). No v9 file exists (search: none). |
| 0.4 four fingerprints frozen | **FAIL** | `longrun/run_longrun.py:1521-1526` model carries only name/endpoint/engine/tokenizer="server-reported"; `:1537-1544` engine_flags `knowable: ctx/cap/block…server build flags are not exposed`; `:1828-1847` `provenance_for` leaves unknowns as `"unknown"` | Capture model id+revision/quant digest, tokenizer files+chat-template hash, renderer module content digest, engine image digest+exact flags. Smallest change: extend manifest `model`/`renderer`/`engine_flags` and `provenance_block`. |
| 0.5 replicate identity | **PARTIAL** | `longrun/run_longrun.py:3107-3111` run_id `run_base-arm-r{rep}` includes rep; `:2133-2134` `read_cell_rows` filters `(run_id, task_id, arm, rep)` | Runner supports rep identity. Missing: explicit pre-analysis assertion `row_count == cells × turns × reps` (no code found; searched `longrun/*.py`, `tools/*.py`). Effort: trivial. |
| 0.6 activation gating | **PARTIAL** | `tools/run_a_star.py:603-625` `ARM_TREATMENT` covers 4 arms; `:651-693` `treatment_due`/`precondition10`; `:703-751` `cell_stamp`/`stamp_cell` | Predicates `masked_rows`, `fetch_rows`, `oracle_injections`, `retrieval_outcomes`, `masked_entry` have zero code references (grep over `experiments/ptr-engine`). Need add row fields + gating for arms C/D/E. Effort: medium. |
| 0.7 budget preflight | **PARTIAL** | `measure/REQUEST-LEDGER.json`: spent 2591, remaining 1729; `measure/RESERVATIONS.json`: requested 1500, granted 1500, `ledger_remaining_at_reservation` 1729; `longrun/run_longrun.py:503` `build_cap_gate` | 1500 granted > 1729 remaining at reservation time; consumption untracked (S2). Available capacity unknown. Reconcile ledger+reservation or mark unknown. Effort: medium. |
| 0.8 independent verifier assigned | **PASS** | `longrun/score_longrun.py:58-59` exit codes; `:350` stub refusal; `:805-849` tamper detection + exit 2; `:1007-1009` `EXIT_TAMPERED` | `score_longrun.py` is an independent process (ran none of the arms); fixture digest checked at score time. |
| 0.9 scorer expresses retrieval miss + abstention | **FAIL** | grep `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` in `longrun/score_longrun.py` and `longrun/grade_v5.py` = **0 matches**; `score_longrun.py:58` `KINDS = ("artifact","fact","constraint","repair")` | Add retrieval-outcome vocabulary (`OK`/`NOT_FOUND`/`STALE_OR_REVOKED`/`SCOPE_UNGRANTED`) and abstention verdicts (`abstained_correctly`) to scorer + red→green control (fabricated answer must fail extension before abstention passes). Effort: medium. |
| 0.10 prototype extension offline-deterministic | **PARTIAL** | `ptr_engine/quantise.py` `choose_padding` (alignment pad, residue 0/1) exists; `tests/test_determinism.py:46` two processes/two roots agree | Implemented: alignment pad + index digest determinism. Missing: fetch batching by body tokens, retrieval-outcome vocabulary, deterministic resume unit tests. Effort: medium. |
| 0.11 law package re-derived | **PASS** | recomputed from `experiments/miss-law/rows.jsonl`: sglang 301 measure rows residual `{0:218, 2048:2, 4096:2, 6144:2, 7680:1, 7936:2, 8000:8, 8064:66}`; vllm 86 measure rows residual `{-1056:85, 0:1}` (sign convention predicted−observed). Command: `python3 -c` recomputing `uncached - ((prev_prompt_tokens % B)+L_app)` over measure rows | Reproduces. |

Verification command used for 0.2:
```
python3 -c "import sys,os,json; sys.path.insert(0,'experiments/ptr-engine/longrun'); sys.path.insert(0,'experiments/ptr-engine/tools'); import grade_v5; f=grade_v5.load_fixture('experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json'); t=grade_v5.derive_truth(f); print(len(t), [c['id'] for c in t])"
```
Output: `12 [...]` (all derive truth).

Verification command used for 0.11:
```
python3 -c "import json,collections; rows=[json.loads(l) for l in open('experiments/miss-law/rows.jsonl') if l.strip()]; print('sglang', collections.Counter(r['uncached_tokens']-((r['prev_prompt_tokens']%64)+r['L_app']) for r in rows if r['server']=='sglang' and r['role']=='measure' and not r.get('error')))"
```

## 2. Checkpoint coverage (12 checkpoints, v8 fixture)

All 12 are gradeable today via `grade_v5.derive_truth` + `mirror_answer_contract`:

| id | turn | kind | gradeable today? |
|---|---|---|---|
| cp.0.t06 | 6 | CALL | yes |
| cp.1.t08 | 8 | CALL | yes |
| cp.2.t12 | 12 | NUM | yes |
| cp.3.t14 | 14 | NONE | yes (branch now implemented) |
| cp.4.t18 | 18 | NUM | yes |
| cp.5.t20 | 20 | NONE | yes (branch now implemented) |
| cp.6.t24 | 24 | NUM | yes |
| cp.7.t26 | 26 | NUM | yes |
| cp.8.t32 | 32 | NUM | yes |
| cp.9.t36 | 36 | CALL (call_at_line) | yes (branch now implemented) |
| cp.10.t42 | 42 | NONE | yes (branch now implemented) |
| cp.11.t46 | 46 | CALL | yes |

Historically (per `docs/CHECKPOINT-COVERAGE.md:106`) 4 needed `NONE`/`call_at_line` branches; those branches now exist in `grade_v5.py:661-734`, so all 12 grade today.

## 3. Abstention / retrieval scoring (gate 0.9)

Zero matches confirmed for `abstain|retrieval_miss|STALE|REVOKED|NOT_FOUND` in `score_longrun.py` and `grade_v5.py`. `KINDS` is only `artifact`/`fact`/`constraint`/`repair`. To close gate 0.9, add: (a) retrieval-outcome scoring (`OK`/`NOT_FOUND`/`STALE_OR_REVOKED`/`SCOPE_UNGRANTED`), (b) abstention verdicts (`abstained_correctly`), (c) a red→green control where a fabricated answer fails the extension before an abstention can pass.

## 4. Fixture wall (read from fixture files, not doc)

Max turn counts per fixture (`longrun/fixtures/LR-*.json` `.turns`):
- LR-01: 48 turns
- LR-02: 64 turns
- LR-03: 56 turns
- LR-04: 40 turns
- LR-05: 72 turns
- LR-06: 60 turns

60-turn cell available only on LR-02, LR-05, LR-06 (matches plan). v8 fixture `wall_tokens=3838`, `wall_tokens_by_arm` all 10616 (declared padding). Measured growth in `rows-cell-transcript-*-*.jsonl` is 46.6–97.6 tok/turn, needing 48–113 turns to reach 10616 — wall unreachable in horizon (gen-6 defect). v9 fixture (measured-growth wall) not yet authored; owner decision.

## 5. Gen-7 readiness (four prerequisites)

- v9 wall: **not implemented** (no v9 file; wall still declared padding).
- rep identity: **implemented** (run_id includes rep; rows carry rep).
- activation gating: **partial** (4 arms gated; masked/fetch/oracle predicates absent).
- stamp rule: **implemented** (`cell_stamp`/`stamp_cell` in `tools/run_a_star.py:703-751`; `score_longrun` tamper exit 2 / stub exit 3).

## 6. Offline work order (before first paid request)

1. Fix positive control (fixture/grader agreement) — `longrun/QUALITY-POSITIVE-CONTROL.md`, scorer `score_longrun.py` — owner decision — medium.
2. Author v9 fixture with measured-growth wall — `longrun/tasks-v*/LR-01.v9.json` (new) — owner decision — medium.
3. Add abstention + retrieval-miss scoring — `longrun/score_longrun.py`, `longrun/grade_v5.py` — medium.
4. Freeze full fingerprints in manifest — `longrun/run_longrun.py:1500-1560` — medium.
5. Add missing activation predicates (masked_rows, fetch_rows, oracle_injections, retrieval_outcomes) — `run_longrun.py` rows + `tools/run_a_star.py` — medium.
6. Reconcile ledger vs reservation / compute available — `measure/REQUEST-LEDGER.json`, `measure/RESERVATIONS.json` — medium.
7. Add row-count assertion `cells × turns × reps` to analyzer — `longrun/analyze_stats.py` or `tools/run_a_star.py` — trivial.
8. Refresh stale `docs/CHECKPOINT-COVERAGE.md` (8/12 claim) — docs — trivial.
9. Re-derive law residual table (done; command above) — trivial.