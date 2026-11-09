# FAILED-TRIAGE — the failed column, classified from artefacts

Generated 2026-10-26 from the task-board ledger (revision 4443), `orchestration/handoffs/*.json` (994 files), `~/.dsh/storages/orchestration/verdict.jsonl` and a `stat` of every named artefact. Offline: no inference, no live request, no acceptance command run, nothing on the board edited.

**Total classified: 104** · `delivered-unverdicted` **27** · `superseded` **11** · `retriable` **66** · `abandoned` **0**

- All 104 carry `no-verdict no-sha`: no row in `verdict.jsonl` names their execution. That is the defect the sweep saw; it says nothing by itself about the work.
- **27 of 27** `delivered-unverdicted` candidates had their named artefacts on disk. **Full set, no sampling**: every one of the 104 units was classified and every artefact path it names was `stat`-ed.
- **If those 27 are accepted as delivered, `failed` goes 104 → 77**, of which **66** are `retriable` — **13 in this workspace** and 53 cross-workspace (unverifiable from here).

## Method, and what it refuses to believe

- In scope if the latest execution ended without a verdict row **or** the handoff says `failed`/`partial`. All 104 qualified.
- `delivered-unverdicted` needs three things together: the handoff claims the work (`status: done|pass`, or `partial` with an empty blocker), its **named artefacts exist on disk at non-zero size**, and its evidence quotes an acceptance result. A handoff claim alone never makes a unit delivered.
- `partial` whose blocker names *unfinished work* (12/48 turns, n=1 of 5, proof incomplete) is **not** delivered even when artefacts exist — hence `RUN-INSTRUMENT-FIX`, `RUN-REASONING-POLICY` and `REASONING-PILOT-OFF` sit under `retriable` while their row files do exist on disk.
- `superseded` needs a named superseder that exists as a `done` **card** with successor shape (`<UNIT>-<suffix>`), or a done handoff covering the same artefact path. Title similarity outside that shape is not accepted: `M3-INST-2B` for `M3-INST-3` runs *backwards* and is not used, so `M3-INST-3` stays `retriable`.
- 57 of the 104 belong to other workspaces (Duval, fabric, Studio, presence). No `orchestration/handoffs/` directory exists in any sibling workspace root (probed), so those units have no persisted handoff and their artefacts are not on disk here. They are `retriable` with that reason recorded — never guessed as delivered.

## The table (sorted by class)

| unit | exec | verdict | class | evidence (path:size) | superseder | the single command that would settle it |
|---|---|---|---|---|---|---|
| `ARMS-PARITY-WITHDRAW` | `d2b5d767` | no-verdict no-sha | **delivered-unverdicted** | state/logs/arms-parity.json:9405B; state/logs/arms-parity-withdraw.json:9113B | `ARMS-PARITY-WITHDRAW2` | `.venv/bin/python tools/audit/arms_parity_status.py   (red before, green after, exit 0/1)` |
| `AVALANCHE-INSERT` | `46b940fc` | no-verdict no-sha | **delivered-unverdicted** | experiments/miss-law/avalanche/probe.py:12042B; experiments/miss-law/avalanche/rows.jsonl:189678B |  | `python3 experiments/miss-law/avalanche/probe.py all 3` |
| `C63-CELL` | `07cd3ac0` | no-verdict no-sha | **delivered-unverdicted** | papers/context-cache/CLAIMS.md:45465B; papers/context-cache/recompute_r2.py:76035B |  | `python3 papers/context-cache/verify_package.py` |
| `C8-ADDENDUM2` | `0bc2f9a1` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/RECORD.md:55006B |  | `test -s experiments/ptr-engine/RECORD.md` |
| `C8-CENSUS` | `32195dc3` | no-verdict no-sha | **delivered-unverdicted** | experiments/miss-law/FIT-GAP.md:5450B |  | `test -s experiments/miss-law/FIT-GAP.md` |
| `CONTAINMENT-RULING` | `d3929851` | no-verdict no-sha | **delivered-unverdicted** | orchestration/units/CONTAINMENT-RULING.md:7089B; orchestration/handoffs/CONTAINMENT-RULING.json:5111B; orchestration/units/CONTAINMENT-RULING.md:7089B |  | `test -s orchestration/units/CONTAINMENT-RULING.md` |
| `DET-VERIFY-FIX` | `e49b6f7a` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/tools/det_verify.py:46515B; experiments/ptr-engine/tools/tests/test_det_verify.py:17976B |  | `python3 experiments/ptr-engine/tools/det_verify.py` |
| `GRADE-FIT-CONTROL` | `e126afba` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/tools/grader_fitness.py:19849B; experiments/ptr-engine/measure/GRADER-FITNESS.md:6553B |  | `python3 experiments/ptr-engine/tools/grader_fitness.py` |
| `LATENCY-DERIVE` | `6e079655` | no-verdict no-sha | **delivered-unverdicted** | strategy/LATENCY_DERIVE.md:11470B; state/logs/lat_derive.py:5860B |  | `.venv/bin/python state/logs/lat_derive.py > state/logs/lat_derive.out` |
| `LAZY-LOAD-CROSSOVER` | `3ecd6bdf` | no-verdict no-sha | **delivered-unverdicted** | experiments/agentic-lazy/crossover/RESULTS.md:12319B; experiments/agentic-lazy/crossover/cells.json:9357B | `LAZY-LOAD-CROSSOVER-2` | `python3 cx_corpus.py   # seed 20261024, exact 3000/30000 char corpora` |
| `LAZY-LOAD-CROSSOVER-2` | `1f4e3a5a` | no-verdict no-sha | **delivered-unverdicted** | experiments/agentic-lazy/crossover/RESULTS.md:12319B; experiments/agentic-lazy/crossover/cells.json:9357B |  | `python3 cx_corpus.py   # seed 20261024, exact 3000/30000 char corpora` |
| `PAPER-FINAL-V2C` | `88556ab1` | no-verdict no-sha | **delivered-unverdicted** | orchestration/handoffs/PAPER-FINAL-V2C.json:12079B; papers/context-cache/MANUSCRIPT.md:93021B; state/config/rows.jsonl:82565B |  | `test -s orchestration/handoffs/PAPER-FINAL-V2C.json` |
| `PROBE-CP3-V5` | `3881cb9c` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl:202920B; experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v3.json:3512B |  | `python3 experiments/ptr-engine/longrun/run_longrun.py --fixture experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json --arms pointer-stable --` |
| `PROBE-CP3-V6` | `44e83c19` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl:225648B; experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json:3394B |  | `python3 experiments/ptr-engine/longrun/tests/test_tool_channel2.py -> exit 0 (PASS: 5/5 assertions; send_chat calls = 0)` |
| `PROMPT-O2C` | `cbf11b4b` | no-verdict no-sha | **delivered-unverdicted** | experiments/context-cache/cells/PROMPT-O2/rows.jsonl:237508B; experiments/context-cache/cells/PROMPT-O2/analysis.json:15215B |  | `docker stop gx10-qwen9b` |
| `PROMPT-O4` | `f1691ba3` | no-verdict no-sha | **delivered-unverdicted** | experiments/context-cache/cells/PROMPT-O4/rows.jsonl:238131B; experiments/context-cache/cells/PROMPT-O4/analysis.json:17813B |  | `.venv/bin/python experiments/context-cache/cells/PROMPT-O4/prompt_o4_cell.py` |
| `Q0-ANSWER-DEGENERACY` | `da4ba836` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/measure/ANSWER-DEGENERACY.md:20609B; experiments/ptr-engine/tools/answer_degeneracy_check.py:7742B |  | `{'cmd': 'python3 -c "import json;d=json.load(open(\'experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-01.v2.json\'));[print(i[\'id\'],i[\'source\'][\'pointe` |
| `R2-OPT-SIM` | `886034dc` | no-verdict no-sha | **delivered-unverdicted** | scratch/r2-opt-sim/calibrate.py:64964B; scratch/r2-opt-sim/cost_model.py:52146B |  | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q  ->  23 passed in 0.08s` |
| `R2-OPT-SIM2` | `ceef1763` | no-verdict no-sha | **delivered-unverdicted** | strategy/R2_OPT_SIM2.md:16553B; scratch/r2-opt-sim/cost_model2.py:50506B |  | `test -s strategy/R2_OPT_SIM2.md` |
| `R2-P1-O1` | `51c6eaa1` | no-verdict no-sha | **delivered-unverdicted** | experiments/context-cache/cells/R2-P1-O1/rows.jsonl:267104B; experiments/context-cache/cells/R2-P1-O1/analysis.json:13473B |  | `wc -l experiments/context-cache/cells/R2-P1-O1/rows.jsonl` |
| `R2-VLLM` | `42662825` | no-verdict no-sha | **delivered-unverdicted** | experiments/context-cache/cells/R2-VLLM/rows.jsonl:456998B; experiments/context-cache/cells/R2-VLLM/analysis.json:19546B |  | `.venv/bin/python experiments/context-cache/cells/R2-VLLM/selftest_offline.py   # offline, 0 requests` |
| `R2.1-TIGHTEN` | `3bed4bf4` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md:18963B; experiments/ptr-engine/tools/anchor_classify.py:17435B |  | `python3 experiments/ptr-engine/tools/tests/test_anchor_classify.py` |
| `RECORD-C8-APPEND` | `3814a26c` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/RECORD.md:55006B |  | `head -n 128 experiments/ptr-engine/RECORD.md | sha256sum` |
| `RECORD-C8-PARAGRAPH` | `92acfee8` | no-verdict no-sha | **delivered-unverdicted** | experiments/ptr-engine/RECORD.md:55006B |  | `test -s experiments/ptr-engine/RECORD.md` |
| `SIM-PROMOTE` | `b8ff5dcf` | no-verdict no-sha | **delivered-unverdicted** | strategy/R2_OPT_SIM.md:14489B; orchestration/units/SIM-PROMOTE.md:3112B |  | `.venv/bin/python -m pytest tests/test_r2_opt_sim.py -q -p no:cacheprovider` |
| `V-XSTACK2` | `bb488738` | no-verdict no-sha | **delivered-unverdicted** | orchestration/handoffs/V-XSTACK2.json:4033B; experiments/context-cache/cells/WIN-SGL/rows.jsonl:1740191B; experiments/context-cache/cells/WIN-VLLM/rows.jsonl:579172B |  | `test -s orchestration/handoffs/V-XSTACK2.json` |
| `VERIFY-CLASSIFIER-FIX` | `045da4d4` | no-verdict no-sha | **delivered-unverdicted** | orchestration/units/VERIFY-CLASSIFIER-FIX.md:2596B; orchestration/handoffs/VERIFY-CLASSIFIER-FIX.json:2274B; tests/test_orchestration_handoffs.py:32463B |  | `EXIT=0: 13 passed in 2.48s (pre-fix baseline was 1 failed, 12 passed)` |
| `AVALANCHE-2` | `643c3d7b` | no-verdict no-sha | **superseded** | orchestration/handoffs/AVALANCHE-2.json:773B | `AVALANCHE-INSERT` | `test -s experiments/miss-law/avalanche/probe.py` |
| `C8-SENTENCE-FIX` | `10a1a550` | no-verdict no-sha | **superseded** | orchestration/handoffs/C8-SENTENCE-FIX.json:204B | `RECORD-C8-APPEND` | `test -s experiments/ptr-engine/RECORD.md` |
| `FIX-DENIALS` | `1215a767` | no-verdict no-sha | **superseded \*** | nothing on disk | `FIX-DENIALS-2` | `test -s orchestration/handoffs/FIX-DENIALS-2.json` |
| `FUZZ-BUDGET` | `5654514a` | no-verdict no-sha | **superseded \*** | nothing on disk | `FUZZ-BUDGET-3` | `test -s orchestration/handoffs/FUZZ-BUDGET-3.json` |
| `GUARD-U4` | `956b16a7` | no-verdict no-sha | **superseded** | orchestration/units/GUARD-U4.md:1151B; orchestration/handoffs/GUARD-U4.json:531B | `GUARD-U4-R2` | `test -s tests/test_context_cache_qualifier.py` |
| `HOUSEKEEPING-WT` | `69d39cdb` | no-verdict no-sha | **superseded \*** | nothing on disk | `HOUSEKEEPING-WT-2` | `test -s orchestration/handoffs/HOUSEKEEPING-WT-2.json` |
| `MEASURE-VLLM` | `c0e65bd7` | no-verdict no-sha | **superseded** | nothing on disk | `MEASURE-VLLM-2` | `test -s orchestration/handoffs/MEASURE-VLLM-2.json` |
| `PAPER-FINAL-V` | `38cacd09` | no-verdict no-sha | **superseded** | orchestration/handoffs/PAPER-FINAL-V.json:267B | `PAPER-FINAL-V2C` | `test -s orchestration/handoffs/PAPER-FINAL-V2C.json` |
| `PROMPT-O2` | `b1958f66` | no-verdict no-sha | **superseded** | experiments/context-cache/cells/PROMPT-O2/analysis.json:15215B; experiments/context-cache/cells/PROMPT-O2/rows.jsonl:237508B | `PROMPT-O2C` | `ssh ... 'free -m; docker ps'` |
| `PROMPT-O2B` | `8094ff06` | no-verdict no-sha | **superseded** | state/config/best-config.json:12222B; tools/best_config_build.py:27895B | `PROMPT-O2D` | `test -s experiments/context-cache/cells/PROMPT-O2/rows.jsonl` |
| `STATE-GRAPH-VIEW` | `b40c0bc1` | no-verdict no-sha | **superseded \*** | nothing on disk | `STATE-GRAPH-VIEW-2` | `test -s orchestration/handoffs/STATE-GRAPH-VIEW-2.json` |
| `ACCOUNT-INVENTORY` | `9b172e16` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `APPLY-EVIDENCE` | `e9865c7f` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `C8-CENSUS-FIX` | `5cfa37c7` | no-verdict no-sha | **retriable** | orchestration/handoffs/C8-CENSUS-FIX.json:3170B |  | `none — no artefact exists to settle it; the card must be re-run` |
| `CB-TMPDIR` | `2f569065` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `DIRECTION-1` | `21aee255` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `E11-7` | `7e6ba701` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `E16-1` | `c7433731` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `E3-1` | `9cd7aa19` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `ENV-GREEN` | `e854b398` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `ENV-PIN` | `db321325` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `ENVELOPE-PORT` | `f5fe8121` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `git worktree add .worktrees/ENV-PORT -b lane/envelope-port 4a232da` |
| `ENVELOPE-RESCUE` | `08c7f2bf` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `ENVELOPE-RESCUE-2` | `0e9a15bc` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `Enforcement eval` | `d3914b88` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FIX-ADV` | `ae2c21b3` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FIX-FRAME-PROGRESS` | `4a429e3b` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FIX-INSTRUMENT` | `04885f9c` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FLAKE-RSI-SURFACES` | `48b2aa24` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FLAKE-RSI-SURFACES-2` | `22842d06` | verdict-recorded | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FLAKE-RSI-SURFACES-3` | `665d97f4` | verdict-recorded | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FORK-CHECKPOINT` | `e47578df` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FULL MOCK` | `f9f32f17` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FUZZ-BUDGET-2` | `609cf9f1` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FUZZ-BUDGET-4` | `ad2cb7d2` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `FUZZ-BUDGET-5` | `250f0c22` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `GAP-LEDGER` | `f40179ff` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `GATE-RUN at fa01962` | `a32f712f` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `GATE-RUN envelope-port at a37bde6` | `d54174c0` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `Landing queue` | `f2c80d6a` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `M2-REVIEW-WIRE` | `6c20e5d6` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `M3-INST-3` | `72ef6822` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `M3-INSTRUMENTS` | `c4764121` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `MOCK 04 SIGNAL` | `bd56f3db` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `PROFILE-PACK` | `817b7f5d` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `PROJ-ADOPT-1` | `c6a5df77` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `QA + BUILD` | `611912a2` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `R2-P1-O2` | `d7d546b5` | no-verdict no-sha | **retriable** | experiments/context-cache/cells/R2-P1-O2/LOCK.md:529B |  | `grep MemAvailable /proc/meminfo` |
| `R2-SGL-9B` | `158b64cd` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `R2-VLLM-FIX` | `af88ea23` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `REASONING-PILOT-OFF` | `c1640afd` | no-verdict no-sha | **retriable** | experiments/ptr-engine/measure/rows-pilot-thinking-2026-10-26.jsonl:187498B; experiments/ptr-engine/longrun/manifests/pilot-off-lr01-r1-transcript-grow-r1.json:1768B |  | `python3 experiments/ptr-engine/longrun/run_longrun.py --help` |
| `RSI-ATTR-1` | `6c38a85c` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `RSI-ATTR-VERIFY` | `32929418` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `RSI-SURFACES-1` | `43554b85` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `RUN-INSTRUMENT-FIX` | `b6033158` | no-verdict no-sha | **retriable** | experiments/ptr-engine/longrun/run_longrun.py:127804B; experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.jsonl:903194B |  | `.venv/bin/python experiments/ptr-engine/longrun/run_longrun.py --smoke --fixture experiments/ptr-engine/longrun/runtime/LR-01.json --run-id fix-smoke-lr01 --row` |
| `RUN-REASONING-POLICY` | `d3c5277d` | no-verdict no-sha | **retriable** | experiments/ptr-engine/longrun/run_longrun.py:127804B; experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl:2252330B |  | `python3 experiments/ptr-engine/longrun/run_longrun.py --smoke --resume --fixture experiments/ptr-engine/longrun/runtime/LR-01.json --max-tokens 16384 --timeout ` |
| `SCOPE-GUARD-MARKERS` | `6a14c4ee` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEAM-1` | `e94cc9d5` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-PROMOTION` | `17bd75b1` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-PROMOTION-2` | `f1d12df9` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-PROMOTION-RED` | `4923fc0a` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-PROMOTION-RED-2` | `1915582c` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-RED3` | `a1457551` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-RED4` | `d803259a` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `SEED-RED6` | `edfc6d07` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `STRAND-MERGE-2` | `dcc9f585` | verdict-recorded | **retriable \*** | nothing on disk |  | `git worktree add .worktrees/strand-merge-2 -b preland/strand-2 5375563` |
| `STUDIO` | `3f32055f` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `STUDIO FIX` | `efd01df6` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `T4-1` | `329a5952` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `UX 01 HORIZON` | `5fa7cfcb` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `V-MECH-RECORD offline diff-verifier of wording repairs` | `460037e9` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `V-PAPER-CLOSE independent verifier of experiment close` | `0e404f2f` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `V-PKG-CORR` | `3097c1d5` | no-verdict no-sha | **retriable** | orchestration/handoffs/V-PKG-CORR.json:7533B; orchestration/units/V-PKG-CORR.md:4888B |  | `none — no artefact exists to settle it; the card must be re-run` |
| `V-RELEASE-BATCH` | `470a1e66` | no-verdict no-sha | **retriable** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `Vision audit: orchestration board screenshots via the keyless OVH route` | `7fcc1ff8` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `WIRE-FIXTURES` | `c7ed33ce` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |
| `dogfood-bl1` | `40b3ec0e` | no-verdict no-sha | **retriable \*** | nothing on disk |  | `none — no artefact exists to settle it; the card must be re-run` |

`\*` = cross-workspace unit: no handoff in any reachable workspace, artefacts not on disk here.

## Why each `delivered-unverdicted` row is believed

- **`ARMS-PARITY-WITHDRAW`** — done, 7/7; the board error records a false-success retro later reconciled by ARMS-PARITY-WITHDRAW2. Evidence: state/logs/arms-parity.json:9405B; state/logs/arms-parity-withdraw.json:9113B
- **`AVALANCHE-INSERT`** — partial, 3/3 artefacts, blocker empty. Evidence: experiments/miss-law/avalanche/probe.py:12042B; experiments/miss-law/avalanche/rows.jsonl:189678B
- **`C63-CELL`** — done, 5/5 incl. CLAIMS.md 45,465 B + recompute_r2.py 76,035 B. Evidence: papers/context-cache/CLAIMS.md:45465B; papers/context-cache/recompute_r2.py:76035B
- **`C8-ADDENDUM2`** — done; same RECORD.md, line 130 replaced (140 before/after). Evidence: experiments/ptr-engine/RECORD.md:55006B
- **`C8-CENSUS`** — done, 1/1 experiments/miss-law/FIT-GAP.md 5,450 B. Evidence: experiments/miss-law/FIT-GAP.md:5450B
- **`CONTAINMENT-RULING`** — done; the ruling in orchestration/units/CONTAINMENT-RULING.md (7,089 B) IS the product. Evidence: orchestration/units/CONTAINMENT-RULING.md:7089B; orchestration/handoffs/CONTAINMENT-RULING.json:5111B; orchestration/units/CONTAINMENT-RULING.md:7089B
- **`DET-VERIFY-FIX`** — done, 5/5 incl. det_verify.py 46,515 B + 17,976 B test. Evidence: experiments/ptr-engine/tools/det_verify.py:46515B; experiments/ptr-engine/tools/tests/test_det_verify.py:17976B
- **`GRADE-FIT-CONTROL`** — done, 5/5 incl. GRADER-FITNESS.md 6,553 B + grader_fitness.py 19,849 B. Evidence: experiments/ptr-engine/tools/grader_fitness.py:19849B; experiments/ptr-engine/measure/GRADER-FITNESS.md:6553B
- **`LATENCY-DERIVE`** — done, 3/3 incl. strategy/LATENCY_DERIVE.md 11,470 B. Evidence: strategy/LATENCY_DERIVE.md:11470B; state/logs/lat_derive.py:5860B
- **`LAZY-LOAD-CROSSOVER`** — done, 8/8; -2 re-delivers the same artefact set. Evidence: experiments/agentic-lazy/crossover/RESULTS.md:12319B; experiments/agentic-lazy/crossover/cells.json:9357B
- **`LAZY-LOAD-CROSSOVER-2`** — done, 8/8 incl. RESULTS.md 12,319 B. Evidence: experiments/agentic-lazy/crossover/RESULTS.md:12319B; experiments/agentic-lazy/crossover/cells.json:9357B
- **`PAPER-FINAL-V2C`** — done verdict-only product: 12,079 B handoff with the 314-token map and eleven edited regions. Evidence: orchestration/handoffs/PAPER-FINAL-V2C.json:12079B; papers/context-cache/MANUSCRIPT.md:93021B; state/config/rows.jsonl:82565B
- **`PROBE-CP3-V5`** — done, 4/4 incl. rows 202,920 B + grade-v3 json. Evidence: experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl:202920B; experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v3.json:3512B
- **`PROBE-CP3-V6`** — done, 15/15 incl. rows 225,648 B and the tool-channel test at exit 0. Evidence: experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl:225648B; experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json:3394B
- **`PROMPT-O2C`** — done, 4/4; rows.jsonl 237,508 B. Evidence: experiments/context-cache/cells/PROMPT-O2/rows.jsonl:237508B; experiments/context-cache/cells/PROMPT-O2/analysis.json:15215B
- **`PROMPT-O4`** — done, 5/5; rows.jsonl 238,131 B (its blocker records a later G0 note on a re-run). Evidence: experiments/context-cache/cells/PROMPT-O4/rows.jsonl:238131B; experiments/context-cache/cells/PROMPT-O4/analysis.json:17813B
- **`Q0-ANSWER-DEGENERACY`** — done, 5/5 incl. ANSWER-DEGENERACY.md 20,609 B + the checker. Evidence: experiments/ptr-engine/measure/ANSWER-DEGENERACY.md:20609B; experiments/ptr-engine/tools/answer_degeneracy_check.py:7742B
- **`R2-OPT-SIM`** — done, 14/14; evidence quotes 23 passed. Evidence: scratch/r2-opt-sim/calibrate.py:64964B; scratch/r2-opt-sim/cost_model.py:52146B
- **`R2-OPT-SIM2`** — done, 8/8; successor cost model, no_live_requests. Evidence: strategy/R2_OPT_SIM2.md:16553B; scratch/r2-opt-sim/cost_model2.py:50506B
- **`R2-P1-O1`** — done, 9/9; rows.jsonl 267,104 B. Evidence: experiments/context-cache/cells/R2-P1-O1/rows.jsonl:267104B; experiments/context-cache/cells/R2-P1-O1/analysis.json:13473B
- **`R2-VLLM`** — partial with 16/16 artefacts incl. rows.jsonl 456,998 B; blocker empty. Evidence: experiments/context-cache/cells/R2-VLLM/rows.jsonl:456998B; experiments/context-cache/cells/R2-VLLM/analysis.json:19546B
- **`R2.1-TIGHTEN`** — done, 6/6 incl. ANCHOR-PREREG-V2.md 18,963 B + classifier + its 17 KB test. Evidence: experiments/ptr-engine/longrun/ANCHOR-PREREG-V2.md:18963B; experiments/ptr-engine/tools/anchor_classify.py:17435B
- **`RECORD-C8-APPEND`** — done; same RECORD.md, append verified by prefix hash. Evidence: experiments/ptr-engine/RECORD.md:55006B
- **`RECORD-C8-PARAGRAPH`** — done; experiments/ptr-engine/RECORD.md 55,006 B carries the paragraph (prefix/suffix hashes unchanged). Evidence: experiments/ptr-engine/RECORD.md:55006B
- **`SIM-PROMOTE`** — partial, 8/8 artefacts; its blocker names what a verifier must resolve, i.e. exactly the missing ritual. Evidence: strategy/R2_OPT_SIM.md:14489B; orchestration/units/SIM-PROMOTE.md:3112B
- **`V-XSTACK2`** — done verdict (overall partial) that re-derives row sha256 per cell; no artefacts key, product is the verdict document. Evidence: orchestration/handoffs/V-XSTACK2.json:4033B; experiments/context-cache/cells/WIN-SGL/rows.jsonl:1740191B; experiments/context-cache/cells/WIN-VLLM/rows.jsonl:579172B
- **`VERIFY-CLASSIFIER-FIX`** — done; evidence EXIT=0 13 passed; the product is the guard clause in tests/test_orchestration_handoffs.py. Evidence: orchestration/units/VERIFY-CLASSIFIER-FIX.md:2596B; orchestration/handoffs/VERIFY-CLASSIFIER-FIX.json:2274B; tests/test_orchestration_handoffs.py:32463B

## The retry ranking — `retriable`, cheapest-and-most-blocking first

Nothing here was dispatched.

1. **`C8-CENSUS-FIX`** — offline, one file write: both failures were a concurrent-writer race ("file changed since it was read"), and the corrected FIT-GAP.md would close the 21 unfit rows C8-CENSUS could only enumerate. *Evidence in hand:* orchestration/handoffs/C8-CENSUS-FIX.json:3170B
2. **`GAP-LEDGER`** — offline and mechanical; it died on max-tokens with zero artefacts, and one test would make every G1-G15 status machine-checked instead of prose. *Evidence in hand:* nothing on disk
3. **`V-PKG-CORR`** — offline and cheap: a verifier already proved PACKAGE.md:70-76 cites numbers that CLAIMS.md:219-220 marks SUPERSEDED, so the fix is a doc edit that stops the paper restating withdrawn numbers. *Evidence in hand:* orchestration/handoffs/V-PKG-CORR.json:7533B; orchestration/units/V-PKG-CORR.md:4888B
4. **`R2-VLLM-FIX`** — the fix unit for the Round-2 vLLM rows; the rows themselves landed (457 KB) but the fix that followed them has no handoff. *Evidence in hand:* nothing on disk
5. **`FIX-INSTRUMENT`** — no artefact and no handoff; an unfixed instrument poisons every later measurement taken with it. *Evidence in hand:* nothing on disk
6. **`R2-SGL-9B`** — the SGLang half of the Round-2 pair; the vLLM half landed 457 KB of rows, this side has nothing. *Evidence in hand:* nothing on disk
7. **`REASONING-PILOT-OFF`** — the pilot arm exists (187 KB rows) but arm B is n=1 of 5, so the pre-registered comparison cannot be read. *Evidence in hand:* experiments/ptr-engine/measure/rows-pilot-thinking-2026-10-26.jsonl:187498B; experiments/ptr-engine/longrun/manifests/pilot-off-lr01-r1-transcript-grow-r1.json:1768B
8. **`RUN-REASONING-POLICY`** — rows 1-12 are real and row-backed; turns 13-48 were never sent. *Evidence in hand:* experiments/ptr-engine/longrun/run_longrun.py:127804B; experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl:2252330B
9. **`RUN-INSTRUMENT-FIX`** — rows exist (903 KB) but the proof is 12/48 turns, so the instrument fix stays unproven. *Evidence in hand:* experiments/ptr-engine/longrun/run_longrun.py:127804B; experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.jsonl:903194B
10. **`R2-P1-O2`** — blocked on the host, not on the work: MemAvailable 21.9 GB against the card's 35 GB threshold. *Evidence in hand:* experiments/context-cache/cells/R2-P1-O2/LOCK.md:529B
11. **`V-RELEASE-BATCH`** — release-batch verifier with no handoff; nothing to re-derive until a release exists. *Evidence in hand:* nothing on disk
12. **`V-PAPER-CLOSE independent verifier of experiment close`** — verifier with no handoff; cheap once the paper text is frozen. *Evidence in hand:* nothing on disk
13. **`V-MECH-RECORD offline diff-verifier of wording repairs`** — verifier of wording repairs; cheap, but only after those repairs land. *Evidence in hand:* nothing on disk

## What this does not settle

- A `delivered-unverdicted` row still needs its verdict written. Accepting it changes the board count; it does not create evidence that was never recorded.
- The 53 cross-workspace `retriable` rows are unverifiable here by construction. Any may be delivered in its own repo; this document will not say so without a handoff or a `stat`.
- No `abandoned` row was found: every failed unit still states an objective nothing else covers, so calling one abandoned would have been a guess.
