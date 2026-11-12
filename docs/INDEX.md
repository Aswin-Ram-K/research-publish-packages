# INDEX — the map of `docs/`, one row per document

**This page is only the map.** Current state is [`docs/STATE.md`](STATE.md); narrative is [`journal/`](../journal/INDEX.md). Every doc under `docs/` has exactly one row below — a doc added or superseded without a row here is an orphan, and [`tools/doc_check.py`](../tools/doc_check.py) (`python3 tools/doc_check.py`) fails the session on it. A row says *what question the doc answers*, never the answer.
When you supersede a doc: put the banner on the old doc, change its row's status to `superseded (by X)`, and leave the row in place — a superseded record is never deleted.
Status key: `current` = authoritative for its question · `record` = dated finding, register or ledger, valid as data · `historical` = dated snapshot of a past state · `superseded` = a named newer doc answers the same question.

---

## Start here

| doc | why read it | status |
|---|---|---|
| [docs/STATE.md](STATE.md) | the single current-state page: what is live, last measured, blocked, next action | current |
| [docs/INDEX.md](INDEX.md) | this map — one row per doc, so nothing is silently lost | current |
| [docs/GRID-RUNBOOK.md](GRID-RUNBOOK.md) | the commands, exit codes and reconcile-first rules for touching a running or interrupted grid | current |
| [docs/COMPACTION-CACHE-DESIGN.md](COMPACTION-CACHE-DESIGN.md) | the compaction/cache design: why a fold costs a re-fetch and not a prefill, the pin model, the break-even rules, and the E7 A/B | current |
| [docs/AGENTIC-COMPACTION-AB.md](AGENTIC-COMPACTION-AB.md) | the instrument E7 lacks: a model-driven long-horizon episode loop (snapshot root, mechanically derived task keys, early stop, per-episode grading) beside the scripted replay, with the staged cost (400 then 960 requests), the honest accuracy bands at those n, and the five falsifiers; §7 records the two void stage-1 runs and §8 the arm-set change (`spcc` out, `compact` in) and the 1,024-request sizing | design + errata — stage 1 run and void, stage 2 in build |
| [experiments/ptr-engine/research-seed-concepts/PREREG-AGENTIC.md](../experiments/ptr-engine/research-seed-concepts/PREREG-AGENTIC.md) | stage 2 pre-registered before its first request: five arms, 4 tasks × 2 reps, the `lost_then_failed` primary metric, the five falsifiers, and the 1,024-request ceiling inside the 1,107 remaining | pre-registration — 0 requests |
| [experiments/ptr-engine/longrun/agentic_contract.py](../experiments/ptr-engine/longrun/agentic_contract.py) | the row contract and the five arm names (`none`, `masking-no-fetch`, `pinned`, `bounded-context-fetch`, `compact`), with `validate_row` so the runner and the analyser cannot drift; the task schema itself is `consonance.longrun-fixture/2`, owned by `run_longrun.load_fixture` | instrument — 12 tests |
| [experiments/ptr-engine/longrun/agentic_cell.py](../experiments/ptr-engine/longrun/agentic_cell.py) | the episode loop: frozen root, model-chosen `read_file`/`grep`, early stop at the last checkpoint, per-episode grading; accepts only `consonance.longrun-fixture/2` and stamps every row with `harness_sha256` | instrument — 34 tests |
| [experiments/ptr-engine/longrun/tools/build_snapshot.py](../experiments/ptr-engine/longrun/tools/build_snapshot.py) | freezes four trees into `state/snapshots/<sha>/` with a per-file manifest so a read is reproducible; current `172d334b…`, 416 files | instrument |
| [experiments/ptr-engine/longrun/tools/build_agentic_tasks.py](../experiments/ptr-engine/longrun/tools/build_agentic_tasks.py) | builds `tasks-agentic/AG-01..04.v1.json` (four tasks, 16 turns, 4 checkpoints each), deriving each graded value from the snapshot by AST rather than hand-writing it | instrument |
| [experiments/ptr-engine/tools/repin_harness.py](../experiments/ptr-engine/tools/repin_harness.py) | writes `measure/HARNESS-PIN.json` from the tree with history kept under `superseded_generation_<N>`; generation 11 = `a668491a…` | instrument |
| [experiments/ptr-engine/tools/agentic_pin.py](../experiments/ptr-engine/tools/agentic_pin.py) | stage 2's own pin, covering `run_longrun.py` because `agentic_cell.py` imports its tool executor | instrument — 6 tests |
| [experiments/ptr-engine/longrun/tools/analyze_agentic.py](../experiments/ptr-engine/longrun/tools/analyze_agentic.py) | the stage-2 analyser: `lost_then_failed` / `present_then_failed` / `unclassified` attribution, the five falsifiers, and the per-episode void/cost summary; `--rows` and `--episodes` each take several files | instrument — 21 tests |
| [experiments/ptr-engine/measure/AGENTIC-2026-11-11-analysis.md](../experiments/ptr-engine/measure/AGENTIC-2026-11-11-analysis.md) | the stage-2 result table: `none` answers 15/32 checkpoints at 0.800, `pinned` 6/32 at 0.833, `compact` 6/32 at 1.000; **no arm solves a task (0/8 each)** — an earlier "`none` solves 4 of 8" came from the offline grader scoring only answered checkpoints, now fixed and guarded; **the `compact` column is `pinned` plus one summary** (the summary gate was unreachable, so summarisation was not tested); `instrument_ok=True`, falsifier 4 not evaluated | measurement — 385 requests |
| [experiments/ptr-engine/measure/AGENTIC-2026-11-11.json](../experiments/ptr-engine/measure/AGENTIC-2026-11-11.json) | the 16 per-episode records for `pinned` and `compact` (JSONL despite the `.json` name), each carrying its checkpoints, fold count, refetch count and verdict | measurement — machine record |
| [experiments/ptr-engine/measure/AGENTIC-2026-11-11-none.json](../experiments/ptr-engine/measure/AGENTIC-2026-11-11-none.json) | the `none` arm's 8 per-episode records, rebuilt with `agentic_cell.py --offline --tasks …` after the live `--out` was truncated by the next run; now lists all four task checkpoints per episode (unanswered ones `ok=False`), matching the live shape | measurement — 0 requests |
| [experiments/ptr-engine/measure/AGENTIC-PIN.json](../experiments/ptr-engine/measure/AGENTIC-PIN.json) | stage 2's instrument pin: 6 files, `66184059…`, covering `run_longrun.py` and the analyser (`analyze_agentic.py`); keeps superseded digests under `superseded`, including `0c7cd2e8…`, the digest every row of the 385-request cell carries | frozen record |
| [docs/PREREG-ARM-RUN.md](PREREG-ARM-RUN.md) | the frozen arm-comparison design (PARM-1): what may be concluded from which cells | current |
| [docs/GRID-2-FINAL.md](GRID-2-FINAL.md) | the last grid verdict: which 6 of 16 cells are usable and what they do not settle | current |
| [docs/TVS.md](TVS.md) | the metric definition — tokens to verified success, and when it is UNDEFINED | current |
| [docs/OPERATIONS.md](OPERATIONS.md) | how to run the Research Extractor app: config, commands, outputs | current |
| [docs/PLAN.md](PLAN.md) | the app's spec of record: the repo-to-docket pipeline | current |
| [STRUCTURE.md](../STRUCTURE.md) | the filesystem map and the paths that must never move (counts are stale; the layout is right) | current |
| [docs/CURRENT-REPO-STATE.md](CURRENT-REPO-STATE.md) | the branch/HEAD/merge/row-file snapshot taken right after the preservation commit (2026-11-09) | record |

## Grid & census — did the grid launch, and what do its cells measure

| doc | what it is | status |
|---|---|---|
| [docs/GRID-PARAMS.md](GRID-PARAMS.md) | the rev-3 (16-cell) launch parameters the fetch-budget measurement requires | current |
| [docs/GRID-CELL-SANITY.md](GRID-CELL-SANITY.md) | the test that decides whether a cell can be analysed at all | current |
| [docs/GRID-GAP-DIAGNOSIS.md](GRID-GAP-DIAGNOSIS.md) | the three gaps the 16-cell run reported, classified by layer (2026-10-28) | current |
| [docs/GRID-REPORT-ERA-GUARD.md](GRID-REPORT-ERA-GUARD.md) | the rule that no pooled number may be printed across provenances | current |
| [docs/GRID-RUN-2.md](GRID-RUN-2.md) | the 16-cell era-B grid did not launch: the five gaps and their classification | record |
| [docs/TRANCHE-CANARY.md](TRANCHE-CANARY.md) | the pre-tranche canary tool and its N=5 to N=12 correction at :26 | current |
| [docs/CANARY-ERA-B-4.md](CANARY-ERA-B-4.md) | canary attempt 4, the one that ran: 40 of 59 rows carry a structured tool call | record |
| [docs/TRANCH1-DRYRUN-2.md](TRANCH1-DRYRUN-2.md) | the ten cells re-rehearsed under the claim they can carry | record |
| [docs/ERA-B-GRADE-REHEARSAL-2.md](ERA-B-GRADE-REHEARSAL-2.md) | the same 64 correct era-B answers, run against the repaired grader | record |
| [docs/LEASE-REOPEN-23.md](LEASE-REOPEN-23.md) | the lease-reopen arm's own first-cell mechanism check at 23 turns (2026-10-27) | record |
| [docs/FETCH-BUDGET-48.md](FETCH-BUDGET-48.md) | does the 24-round per-arm fetch budget survive a 48-turn tools-on cell | record |
| [docs/PRICE-REPLICATION.md](PRICE-REPLICATION.md) | what the next 288 to 792 requests would buy | record |
| [docs/LAUNCH-PACKAGE.md](LAUNCH-PACKAGE.md) | the go/no-go audit for RUN-A-STAR-2 on a moving tree | record |
| [docs/LAUNCH-CONTRACT.md](LAUNCH-CONTRACT.md) | the scoped judging rules for `launch_contract_diff.py --check` | current |
| [docs/LAUNCH-CONTRACT-DIFF.md](LAUNCH-CONTRACT-DIFF.md) | every number the launch depends on, side by side, as one snapshot | record |
| [docs/LAUNCHER-WIRING.md](LAUNCHER-WIRING.md) | the rule that one number has one owner (`run_a_star.py`) | current |
| [docs/PRECONDITION-10-SCOPE.md](PRECONDITION-10-SCOPE.md) | judge each arm on its own treatment, not on a cross-arm pool | record |
| [docs/FAILED-TRIAGE.md](FAILED-TRIAGE.md) | the failed column classified from artefacts — the fullest of the three censuses | record |
| [docs/NEVER-ANSWERED-ROOT.md](NEVER-ANSWERED-ROOT.md) | what the 63 never-answered cells actually are, read from the turn text | record |

## Harness & instrument — what the runner is, and what a change to it attributes

| doc | what it is | status |
|---|---|---|
| [docs/HARNESS-MAP-V3.md](HARNESS-MAP-V3.md) | the harness as it runs after the instrument batch: file, layer, purpose, line | current |
| [docs/HARNESS-PIN.md](HARNESS-PIN.md) | the harness digest pin and how gen 5 to 6 supersede — what "same harness" means | current |
| [docs/HARNESS-BASELINES.md](HARNESS-BASELINES.md) | the armed baselines that attribute a change before the run happens | record |
| [docs/FIXTURE-GENERATIONS.md](FIXTURE-GENERATIONS.md) | the one-spec-one-generator rule (LR-01) across fixture v6, v7, v8 | current |
| [docs/LOST-FIXTURE.md](LOST-FIXTURE.md) | what the one missing fixture digest (72c3832d…) costs the record; recorded, not repaired | record |
| [docs/EXIT-CODES.md](EXIT-CODES.md) | the `cell.py` exit table, and which module is its truth | current |
| [docs/CELL-STAMP-WIRING.md](CELL-STAMP-WIRING.md) | what a fresh, unstamped grid cell does | record |
| [docs/FROZEN-TREE.md](FROZEN-TREE.md) | verify a snapshot, not a moving tree | current |
| [docs/TREE-FREEZE.md](TREE-FREEZE.md) | a verdict must name the bytes it judged | current |
| [docs/TREATMENTS.md](TREATMENTS.md) | making the four long-run arms reachable at the frozen 48-turn horizon | record |
| [docs/V8-DRYRUN-REFREEZE.md](V8-DRYRUN-REFREEZE.md) | manifest provenance versus the runner's actual wall | record |
| [docs/CONTRACT-DIFF-ABSENCE.md](CONTRACT-DIFF-ABSENCE.md) | ABSENT is a result: how `launch_contract_diff.py` reports a missing field after the `KeyError: 'components'` crash | current |
| [docs/RUNAWAY-POLICY.md](RUNAWAY-POLICY.md) | what the runaway guard is for, decided on measurement (option B) | current |
| [docs/RUNNER-WALL-KEY.md](RUNNER-WALL-KEY.md) | which wall key the runner reads — per-arm, with the legacy fall-through it closes | current |
| [docs/TOOL-CHANNEL-WIRE.md](TOOL-CHANNEL-WIRE.md) | putting the tool schema on the wire and consuming the call that comes back | current |
| [docs/CACHE-CREDIT-CHAT.md](CACHE-CREDIT-CHAT.md) | is per-request cache credit measurable on the runner's own endpoint | record |

## Gates, verifier, verdicts — the door to a live request and what may be believed

| doc | what it is | status |
|---|---|---|
| [docs/GATE-CHAIN.md](GATE-CHAIN.md) | normative: the only door to a live request | current |
| [docs/GATE-LEDGER.md](GATE-LEDGER.md) | what the gate chain has cost and what it has actually prevented | current |
| [docs/V-FIXTURE-V8.md](V-FIXTURE-V8.md) | audit of the fixture RUN-A\* actually grades on | current |
| [docs/V-TOOL-CHANNEL.md](V-TOOL-CHANNEL.md) | the adversarial verdict on the tool-channel fix | record |
| [docs/V-GATE-OPERAND.md](V-GATE-OPERAND.md) | independent attack on the repaired gate | record |
| [docs/V-GATE-REPIN.md](V-GATE-REPIN.md) | the gate precondition, decided on the tree as it stands | record |
| [docs/V-CAPGATE-REFUSE.md](V-CAPGATE-REFUSE.md) | attacking the `delta < 0` refusal | record |
| [docs/V-LEDGER-BASELINE.md](V-LEDGER-BASELINE.md) | independent verification of the ledger baseline | record |
| [docs/V-INSTRUMENTS.md](V-INSTRUMENTS.md) | recomputing the three instruments that govern spend and gating | record |
| [docs/V-REASON-MIX.md](V-REASON-MIX.md) | independent recomputation of the reason-mix table | record |
| [docs/V-STAMP-NEUTRAL.md](V-STAMP-NEUTRAL.md) | is the grader stamp additive | record |
| [docs/ATTACK-GRADE-V5-2.md](ATTACK-GRADE-V5-2.md) | a second, disjoint attack on the repaired `grade_v5` | record |
| [docs/GRADE-V5-REPAIR.md](GRADE-V5-REPAIR.md) | three grader defects closed, and the rule a reader needs | current |
| [docs/GRADE-V6-DERIVE.md](GRADE-V6-DERIVE.md) | making `LR-01.v6.json` gradeable end to end | record |
| [docs/REGRADE.md](REGRADE.md) | one command that re-derives a published grade | current |
| [docs/REGRADE-STAMP-WIRE.md](REGRADE-STAMP-WIRE.md) | how the regrade stamp is wired into the row | record |
| [docs/VERDICT-SCOPE.md](VERDICT-SCOPE.md) | the row must say which bytes it judged | current |
| [docs/VERDICT-SEMANTICS.md](VERDICT-SEMANTICS.md) | a refusal is not a failure | current |
| [docs/VERDICT-READJUDICATION.md](VERDICT-READJUDICATION.md) | do the 29 delivered-but-unverdicted units still pass today | record |
| [docs/VERDICT-RECLAIM.md](VERDICT-RECLAIM.md) | running the refused rows through an allow-listed shell | record |
| [docs/VERDICT-BACKFILL-FIXTURE-GENERATIONS.md](VERDICT-BACKFILL-FIXTURE-GENERATIONS.md) | backfilling the fixture generation onto past verdicts | record |
| [docs/CAPGATE-FOREIGN-RED.md](CAPGATE-FOREIGN-RED.md) | the stale assertion that charged other cards | record |
| [docs/RECLAIM-ACCEPTANCE.md](RECLAIM-ACCEPTANCE.md) | re-measuring three cards charged with the cap-gate red | record |
| [docs/RECLAIM-GREEN-ROWS.md](RECLAIM-GREEN-ROWS.md) | can finished work be un-filed as failed | record |
| [docs/DECIDABILITY-SEAM.md](DECIDABILITY-SEAM.md) | the grader and the analyser disagreed about the same rows | record |
| [docs/PROVENANCE-REFUSAL.md](PROVENANCE-REFUSAL.md) | the comparison gate in `analyze_stats.py` | current |
| [docs/ARM-INTEGRITY.md](ARM-INTEGRITY.md) | do the four arm labels name four behaviours | record |
| [docs/FALSE-PASS.md](FALSE-PASS.md) | register of hollow pass claims | current |
| [docs/HANDOFF-LINT.md](HANDOFF-LINT.md) | the handoff evidence checker | current |
| [docs/HANDOFF-PARTIAL.md](HANDOFF-PARTIAL.md) | making a partial handoff judgeable, with partial codes | current |
| [docs/HANDOFF-SHAPE.md](HANDOFF-SHAPE.md) | how `classify()` decides, and why | current |

## Ledger & accounting — which request a row carries and what it was spent on

| doc | what it is | status |
|---|---|---|
| [docs/ROW-MODEL.md](ROW-MODEL.md) | which row carries which HTTP request | current |
| [docs/ROW-PROVENANCE.md](ROW-PROVENANCE.md) | every row says what produced it | current |
| [docs/REQUEST-IDENTITY.md](REQUEST-IDENTITY.md) | one row, one request — the dedupe field | current |
| [docs/REQUEST-LEDGER.md](REQUEST-LEDGER.md) | the request budget as a number a machine computes, with the reversal section | current |
| [docs/LEDGER-BASELINE.md](LEDGER-BASELINE.md) | the v1 dated record and the v2 current baseline | current |
| [docs/LEDGER-RECONCILE.md](LEDGER-RECONCILE.md) | why the launcher compares a DELTA, not two numbers | current |
| [docs/LEDGER-AFTER-CANARY.md](LEDGER-AFTER-CANARY.md) | the brake was reading a stale number | record |
| [docs/TURN-DEDUP.md](TURN-DEDUP.md) | 48, 46 and 43 are three different questions | current |
| [docs/TURN-CENSUS.md](TURN-CENSUS.md) | how many completed turns this corpus actually holds | record |
| [docs/STOP-REASON.md](STOP-REASON.md) | a stop is explainable from the row alone | current |
| [docs/UNIT-JOURNAL.md](UNIT-JOURNAL.md) | the append-only unit journal tool | current |
| [docs/CHECKPOINT-COVERAGE.md](CHECKPOINT-COVERAGE.md) | the 12 decidable checkpoints, their cost, and the ranking they buy | record |

## Latency & quality — the two halves of the claim, and what each figure is worth

| doc | what it is | status |
|---|---|---|
| [docs/LATENCY-FALLBACK.md](LATENCY-FALLBACK.md) | every latency figure in this corpus is a marked fallback | current |
| [docs/LATENCY-ERA-CENSUS.md](LATENCY-ERA-CENSUS.md) | which TTFT era produced each rows file and each published latency figure | current |
| [docs/TTFT-DEFINITION.md](TTFT-DEFINITION.md) | which row kind defines per-turn latency | current |
| [docs/TVS-RESULTS.md](TVS-RESULTS.md) | the first tokens-to-verified-success results | record |
| [docs/TVS-CENSORED.md](TVS-CENSORED.md) | the censored reading of tokens-to-verified-success | record |
| [docs/P95-POWER.md](P95-POWER.md) | how many turns a cell needs before its p95 can compare two arms | current |
| [docs/POWER-UNDER-TURN-N.md](POWER-UNDER-TURN-N.md) | the power verdict at the denominator the analyser actually uses | current |
| [docs/H1-CONDITIONING.md](H1-CONDITIONING.md) | what the frozen p95 actually averages over, pre-registered | current |
| [docs/PARM-1-ERRATA.md](PARM-1-ERRATA.md) | the denominators made honest before the grid ran | current |
| [docs/PREREG-TRANCHE-1.md](PREREG-TRANCHE-1.md) | the decision procedure for RUN-A\*, frozen before any row existed | current |
| [docs/OPERATOR-BRIEF.md](OPERATOR-BRIEF.md) | the p95 and TVS operator brief, issue 4 | record |
| [docs/PROJECTION.md](PROJECTION.md) | which key of `PROJECTION.json` the gate now reads | record |
| [docs/PROJECTION-CALIBRATION.md](PROJECTION-CALIBRATION.md) | a worst case is not a forecast | current |
| [docs/QUALITY-ERAS.md](QUALITY-ERAS.md) | every published accuracy figure with the grader that produced it | current |
| [docs/QUALITY-CARRY-FORWARD.md](QUALITY-CARRY-FORWARD.md) | era A's answers recomputed under the current grader | record |
| [docs/QUALITY-REASON-MIX.md](QUALITY-REASON-MIX.md) | what does H3 actually measure | record |
| [docs/MATRIX-COVERAGE.md](MATRIX-COVERAGE.md) | the denominator every accuracy in this project must be quoted against | current |
| [docs/MATRIX-DECLARED-SPACE.md](MATRIX-DECLARED-SPACE.md) | the declared cell space, declared outside the rows | current |
| [docs/MODAL-ANSWER.md](MODAL-ANSWER.md) | what each era-A arm's most repeated string grades at the 12 checkpoints | record |
| [docs/ANSWER-DEGENERACY.md](ANSWER-DEGENERACY.md) | repetition of answers per arm and per cell | record |
| [docs/VERBOSITY.md](VERBOSITY.md) | does the grow arm's longer answer explain the TTFT gap | record |
| [docs/PROSE-VALUE-METRIC.md](PROSE-VALUE-METRIC.md) | the quality number a reader would have assumed; errata drafted, unapplied | record |
| [docs/PUBLISHED-NUMBERS.md](PUBLISHED-NUMBERS.md) | every published accuracy whose denominator is not an accuracy denominator | current |
| [docs/WITHDRAWN.md](WITHDRAWN.md) | every number this batch withdrew, with what replaces it | current |
| [docs/WITHDRAWN-SCREEN.md](WITHDRAWN-SCREEN.md) | every published page screened against the withdrawal register | record |
| [docs/ANALYSIS-CONSUMER.md](ANALYSIS-CONSUMER.md) | `usable_for` consumption and the truncated-turn rule | current |
| [docs/ANALYSIS-PATH.md](ANALYSIS-PATH.md) | the post-grid analysis path, rehearsed offline | record |

## Serving & cache matrix — the engine-versus-model bill

| doc | what it is | status |
|---|---|---|
| [docs/serving-options/MATRIX-2x2.md](serving-options/MATRIX-2x2.md) | the measured 2x2: the engine sets the bill, the model only under vLLM | current |
| [docs/serving-options/BEST-CONFIG.md](serving-options/BEST-CONFIG.md) | the four optimised setups, one per cell of the 2 models by 2 engines matrix | current |
| [docs/serving-options/R2-DESIGN.md](serving-options/R2-DESIGN.md) | Round 2: the design, written before the numbers land | current |
| [docs/serving-options/LAUNCH-VLLM.md](serving-options/LAUNCH-VLLM.md) | exact launch guide for vLLM 0.27.1 | current |
| [docs/serving-options/LAUNCH-SGLANG.md](serving-options/LAUNCH-SGLANG.md) | exact launch guide for SGLang `0.0.0.dev1+g4ccff141d` | current |
| [docs/serving-options/TRACK-INTERVAL.md](serving-options/TRACK-INTERVAL.md) | does `--mamba-track-interval` move the cache grid | record |
| [docs/serving-options/FORK-DECISION.md](serving-options/FORK-DECISION.md) | whether to patch SGLang: the three-gap fork gate (each gap to be shown by a failing run), and why the answer today is **no fork** | current |
| [docs/STACK-RECON.md](STACK-RECON.md) | what our serving stack can actually tell us | record |

## App governance — the Research Extractor spec, policy and integrity rules

| doc | what it is | status |
|---|---|---|
| [docs/PLAN_CORRECTIONS.md](PLAN_CORRECTIONS.md) | the verified-deviation ledger (a) to (ct+) against the plan | current |
| [docs/ACCEPTANCE_PROTOCOL.md](ACCEPTANCE_PROTOCOL.md) | how the end-to-end acceptance run is executed and what evidence it must produce | current |
| [docs/LESSONS.md](LESSONS.md) | process findings worth keeping | current |
| [docs/TARGET_POLICY.md](TARGET_POLICY.md) | the Duval admission decision, recorded | current |
| [docs/SECRET_SCAN_POLICY.md](SECRET_SCAN_POLICY.md) | the commit-gate secret-scan policy | current |
| [docs/LIVE_TARGET_NOTES.md](LIVE_TARGET_NOTES.md) | `/home/zer0null/Duval` was under concurrent modification (2026-10-08) | record |
| [docs/RESEARCH-PROTOCOL.md](RESEARCH-PROTOCOL.md) | read the published fact before paying for the measurement | current |
| [docs/EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md](EXTERNAL_WORKSPACE_POINTER_PROTOCOL.md) | the pointer schema for external workspaces | current |
| [docs/PATH-REFS.md](PATH-REFS.md) | the rule that no document may cite a path the tree does not have | current |
| [docs/PATH-REFS-ROUND2.md](PATH-REFS-ROUND2.md) | the ambiguous `wrong_dir` citations, decided by evidence | record |
| [docs/PATH-REFS-COPYTREE.md](PATH-REFS-COPYTREE.md) | why the candidate set itself was the defect | record |

## Prompt system — SYS-OPT rounds and the prompt ceiling

| doc | what it is | status |
|---|---|---|
| [docs/prompt-system/VERSIONS.md](prompt-system/VERSIONS.md) | the SYS-OPT version log and the pre-registered ceiling rule | current |
| [docs/prompt-system/SYS-OPT-RESULTS.md](prompt-system/SYS-OPT-RESULTS.md) | the SYS-OPT round record | record |
| [docs/prompt-system/SYS-OPT-R1B-RESULTS.md](prompt-system/SYS-OPT-R1B-RESULTS.md) | SYS-OPT round 1 (V1) results | record |
| [docs/prompt-system/R2-PROMPT-RESULTS.md](prompt-system/R2-PROMPT-RESULTS.md) | does the pointer index pay, and does padding pay | current |

## Research — what the field already knows

| doc | what it is | status |
|---|---|---|
| [docs/research/ADOPT-HARNESS.md](research/ADOPT-HARNESS.md) | what already exists for the eight bespoke layers, and what that is worth | current |
| [docs/research/ADOPTION-LEDGER.md](research/ADOPTION-LEDGER.md) | every hairy problem this batch met, and whether adoption was considered | record |
| [docs/research/tool-channel-sglang.md](research/tool-channel-sglang.md) | what the SGLang docs actually say about the tool channel | current |
| [docs/EXTERNAL-EVAL-PRACTICE.md](EXTERNAL-EVAL-PRACTICE.md) | what the field knows about evaluating models and agents, and what this repo adopts | current |
| [docs/EXTERNAL-SERVING-PRACTICE.md](EXTERNAL-SERVING-PRACTICE.md) | what the field measures for serving, and what this repo adopts | current |

## Historical & superseded — one line each, so the current doc stays findable

| doc | what it is | status |
|---|---|---|
| [docs/HARNESS-MAP.md](HARNESS-MAP.md) | the harness before the first fix batch; its own banner says line numbers are historical | superseded (by HARNESS-MAP-V2) |
| [docs/HARNESS-MAP-V2.md](HARNESS-MAP-V2.md) | the harness after the first fix batch | superseded (by HARNESS-MAP-V3) |
| [docs/HARNESS-MAP-PREGRID.md](HARNESS-MAP-PREGRID.md) | pre-grid scoreboard; self-admits duplicating V3 at :119 | historical |
| [docs/CANARY-ERA-B.md](CANARY-ERA-B.md) | canary attempt 1: refusal | historical |
| [docs/CANARY-ERA-B-2.md](CANARY-ERA-B-2.md) | canary attempt 2: held, 0 requests | historical |
| [docs/CANARY-ERA-B-3.md](CANARY-ERA-B-3.md) | canary attempt 3: a HOLD verdict rather than a run | superseded (by CANARY-ERA-B-4) |
| [docs/CANARY-ARGV.md](CANARY-ARGV.md) | the claim mode a 12-turn canary must carry — question settled | historical |
| [docs/CANARY-FALSE-POSITIVE.md](CANARY-FALSE-POSITIVE.md) | whether the pre-tranche canary controls the tools-on shape it blesses — settled | historical |
| [docs/TRANCH1-DRYRUN.md](TRANCH1-DRYRUN.md) | the ten-cell grid rehearsed offline | superseded (by TRANCH1-DRYRUN-2) |
| [docs/DRYRUN-TOOLS-SHAPE.md](DRYRUN-TOOLS-SHAPE.md) | tools-on launch rehearsed; a no_go signed against a long-superseded pin | historical |
| [docs/ERA-B-GRADE-REHEARSAL.md](ERA-B-GRADE-REHEARSAL.md) | first asking whether the grader accepts a correct era-B answer | superseded (by ERA-B-GRADE-REHEARSAL-2) |
| [docs/LEASE-REOPEN-12.md](LEASE-REOPEN-12.md) | one 12-turn lease-reopen cell, rep 1, on the gen-6 tree | superseded (by LEASE-REOPEN-23) |
| [docs/GRID-SHAPE.md](GRID-SHAPE.md) | the launch-shape decision; its parameters predate the 16-cell rev 3 | superseded (by GRID-PARAMS) |
| [docs/GRID-BUDGET-RECHECK.md](GRID-BUDGET-RECHECK.md) | two grid prices reconciled on the v1-era price | historical |
| [docs/GRID-REPORT-2.md](GRID-REPORT-2.md) | the generated report over era-A rows (2026-10-26) | superseded (by GRID-2-FINAL) |
| [docs/LEDGER-GRID-BASELINE.md](LEDGER-GRID-BASELINE.md) | the pre-grid spend reading, frozen at v1 — must not be the delta base | superseded (by the later grid baselines) |
| [docs/FAILED-COLUMN.md](FAILED-COLUMN.md) | the failed column read as 60 pieces of unfinished work | superseded (by FAILED-TRIAGE) |
| [docs/UNSTAMPED.md](UNSTAMPED.md) | the failed column read as 97 pieces, zero measured failures | superseded (by FAILED-TRIAGE) |
| [docs/V-PIN-GEN5.md](V-PIN-GEN5.md) | independent attribution of harness pin generation 5 | superseded (pin is now gen 6) |
| [docs/V-FIXTURE-V7.md](V-FIXTURE-V7.md) | re-derivation of the 12 `LR-01.v7` truths | superseded (v8 is in service) |
| [docs/V-GRID-REPORT.md](V-GRID-REPORT.md) | the attack report that found the report emitter unsound | superseded (by GRID-REPORT-ERA-GUARD) |
| [docs/CELL-PY-CERTIFICATE.md](CELL-PY-CERTIFICATE.md) | byte certificate of one past `cell.py` | historical |
| [docs/HANDOFF-SHAPE-BASELINE.md](HANDOFF-SHAPE-BASELINE.md) | the 13 "new gaps" measured at `f17663d1` | historical |
| [docs/HANDOFF-RECOVERY.md](HANDOFF-RECOVERY.md) | what the disk was actually holding on 2026-10-26 | historical |
| [docs/COLD-START-PROBE.md](COLD-START-PROBE.md) | what a fresh session could reconstruct from the record alone | historical |
| [docs/COLD-START-SCORE.md](COLD-START-SCORE.md) | the inheritance gap, measured — pair of the probe above | historical |
| [docs/PLAN_CORRECTIONS_PART2.md](PLAN_CORRECTIONS_PART2.md) | a superseded pointer, merged into the corrections ledger | superseded (by PLAN_CORRECTIONS) |
| [docs/TOOL-CHANNEL-ROOT-CAUSE.md](TOOL-CHANNEL-ROOT-CAUSE.md) | where a tool call stops being a request and becomes prose | superseded (by TOOL-CHANNEL-WIRE) |
| [docs/LATENCY-REPORT.md](LATENCY-REPORT.md) | the p50/p95 report whose own verdicts are withdrawn at :40; publishes 0 p95 | historical |
| [docs/ENDPOINT-STATE.md](ENDPOINT-STATE.md) | the serving-stack snapshot at 2026-10-26T17:00Z | historical |
| [docs/serving-options/R-ENG.md](serving-options/R-ENG.md) | other inference engines: cache granularity, features, stable configs; carries a STALE banner at :3 | superseded (by MATRIX-2x2) |
| [docs/serving-options/R-VLLM.md](serving-options/R-VLLM.md) | vLLM with LMCache/Mooncake: options and claims; STALE banner at :3 | superseded (by MATRIX-2x2) |
| [docs/serving-options/R-SGL.md](serving-options/R-SGL.md) | SGLang cache and serving options: what exists, what it claims; STALE banner at :3 | superseded (by MATRIX-2x2) |
| [docs/serving-options/R-PROD.md](serving-options/R-PROD.md) | what production teams actually run; STALE banner at :3 | superseded (by MATRIX-2x2) |
| [docs/serving-options/R-CROSS.md](serving-options/R-CROSS.md) | cross-stack cache-reuse literature survey; STALE banner at :3 | superseded (by MATRIX-2x2) |
| [docs/serving-options/CROSS-HTTP.md](serving-options/CROSS-HTTP.md) | the vLLM end of GAP G4; STALE banner at :3 | superseded (by MATRIX-2x2) |

---

## Seed packages and experiment homes (outside `docs/`)

Documents the contract requires an index line for that deliberately live outside `docs/` (they are
package prose attached to an experiment, not workspace documents).

| doc | why read it | status |
|---|---|---|
| [experiments/ptr-engine/research-seed-concepts/README.md](../experiments/ptr-engine/research-seed-concepts/README.md) | the 2026-11-06 research seed package: which papers the evidence warrants (two), what each may claim, and the staged validation each needs — plus `EVIDENCE-DOSSIER.md`, `RESEARCH-BRIEF.md`, `SECOND-PAPER-BRIEF.md`, `VALIDATION-ROADMAP.md` beside it | current |
| [experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md](../experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md) | E7's pre-registration: the six-arm real-length A/B (`compact`/`mask`/`retrieval`/`pins`/`pins-recency`/`none`), its predictions, falsifiers, two-stage budget, and the instrument requirements that must hold before the first request | current (gated on the cap decision) |
| [experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json](../experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json) | E7's quality instrument: 220 turns, `L0 ≈ 40.5 k` tokens, `window_tokens = 131072`, 5 decidable checkpoints (4 NUM, 1 CALL) over 28 real `ptr_engine` files; built by `longrun/tools/build_long_fixture.py` (seed 20261111, byte-reproducible, sha256 `55dc768a…`) | current |
| [experiments/ptr-engine/longrun/tasks-v7/TX-04S.v1.json](../experiments/ptr-engine/longrun/tasks-v7/TX-04S.v1.json) | the wider-mismatch fixture a binding *rate* would need: 100 turns, 41 checkpoints, 14 declared delivery/ask mismatches (7 schedule-inherent + 7 decoy), 1 same-document control, 26 with no delivery, `wall_tokens 867`; `tasks-v7/TX-04.v1.json` is read, never written; built by `longrun/tools/build_mismatch_fixture.py` (sha256 `7f41f9b3…`) | current — built and dry-run, **not yet run** |
| [experiments/ptr-engine/tools/predict_answer_slot.py](../experiments/ptr-engine/tools/predict_answer_slot.py) | the answer-slot-binding rule as a 0-request predictor: re-materialises each turn's prompt (both E3 arms rebuilt 100/100 byte-identical) and applies "BOUND iff a *different* document's delivery sits above the slot and carries the asked symbol"; on the masking arm it predicted 5 BOUND, 4 of which were wrong (recall 0.667, precision 0.80), and 0 BOUND on `spcc` | current (U-SPCC-77) |
| [experiments/ptr-engine/longrun/tasks-v7/TX-05C.v1.json](../experiments/ptr-engine/longrun/tasks-v7/TX-05C.v1.json) | the chain-reference fixture: 100 turns, 12 checkpoints (6 reference + 6 carry), `window_tokens 4096` so the pinned arm folds at T24, and a `chain` block whose carry questions name only the step ("using the symbol you identified at step j — do not restate it") so the value is never in the prompt; built by `longrun/tools/build_chain_fixture.py` (sha256 `904b1e62…`) | current — built, linted, dry-run `would_send_total=400` |
| [experiments/ptr-engine/longrun/tools/analyze_chain.py](../experiments/ptr-engine/longrun/tools/analyze_chain.py) | the chain-break classifier: `lost_then_failed` (value absent from the prompt → the fold's fault) versus `present_then_failed` (value present → model error, not the signal), plus `refetch_count` between the reference and carry turns; never defaults an unknown presence to True | current |

---

Archive candidates (recorded as candidates only, never acted on here): the inventory's 25 candidates are a subset of the `historical` and `superseded` rows above. Every superseded row names its replacement, so nothing is lost by a later move to `docs/archive/`.
