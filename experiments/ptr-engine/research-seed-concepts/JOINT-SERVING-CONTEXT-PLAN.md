# Joint Serving + Context Plan — Pricing and Decision Package

**Status banner.** This document is a **pricing/decision package only**. Producing it performed **zero** live inference or completion requests, **zero** service restarts or reconfigurations, **zero** fixture or grader modifications, **zero** ledger or reservation writes, and **zero** target-repo writes. Permission to *plan* use of the running services is **distinct** from authorization to *run* any funded cell; no funded cell may start without a separate written operator decision. The request cap is **deliberately undecided** until this price is read; no live stage starts on an estimated or historical balance. Request counts below are estimates/counts with stated formulas, not quotes for a run.

**Paths.** Real checkout `/home/zer0null/research extractor` (branch `research/next-candidates-2026-10-24` @ `f17663d`). All citations are `file:line` against that checkout.

---

## 1. Scope and status

- **Deliverable:** a priced, decision-ready research programme jointly studying context policy and serving configuration across representative agent workloads, on the current machine plus cross-stack replication. No experiments are run by this document.
- **Authoritative inputs:** `research/next-candidates/consonance-bounded-context-evaluation.md` (arms, cells, arithmetic); `experiments/ptr-engine/research-seed-concepts/VALIDATION-ROADMAP.md` (gates/stages); `docs/serving-options/BEST-CONFIG.md` (O1–O4, historical only); `docs/STATE.md`, `docs/GRID-2-FINAL.md`, `docs/GRID-GAP-DIAGNOSIS.md` (gen-6, ledger).
- **Non-goals:** no new hypothesis, no silently edited p95 rule, no pooling gen-6 with any newer generation, no substitution of an unavailable stack.

## 2. Evidence and operating state (dated facts)

| Fact | Value | Source |
|---|---|---|
| Live model-serving process | PID 9738 (container PID 1, docker `5a0ed0108a6c`), argv `python -u /app/server.py`, PyTorch 2.9.1+rocm7.1.1, Transformers 5.15.0, FastAPI/uvicorn, model `Qwen3_5ForSequenceClassification` (`qwen3_5`), bfloat16, 32 layers, hidden 2560, max_pos 262144, labels {contradiction, entailment, neutral}, template `Premise: {premise}\nHypothesis: {hypothesis}`, file `model.safetensors`, image sha256 `9371dc20c644a82b95137299296eabcd58d7dab552d1935a382739e011a57e2a` | `orchestration/notes/joint-plan/R2-serving.md §1` |
| Bound endpoint | `127.0.0.1:8088`, `/health` ok, device cuda:0 (ROCm), load_seconds 23.442 | `R2-serving.md §1` |
| GPU | AMD Radeon RX 9070 (Navi 48), VRAM total 17,095,983,104 B (~15.92 GiB); used 10,965,823,488 B; free `17,095,983,104 − 10,965,823,488 = 6,130,159,616 B ≈ 5.71 GiB`. GPU1 is a 512 MiB iGPU (18:00.0). No NVIDIA driver/GPU (`nvidia-smi` failed). ROCm 7.1.1, torch 2.9.1+rocm | `R2-serving.md §2` |
| Rerank tenant VRAM | PID 9738 holds 9,421,869,056 B (~8.77 GiB) on GPU0 | `R2-serving.md §2` |
| Free VRAM (upper bound if rerank tenant released) | `17,095,983,104 − 9,421,869,056 = 7,674,114,048 B (~7.15 GiB)` — upper bound only, if PID 9738 (9,421,869,056 B) were released; today 1,543,954,432 B of that is used by other consumers | arithmetic from `R2-serving.md §2` |
| Other tenants | Docker: openjev, searxng, orbit, cerebro, vegtam, caddy, authelia, pi-agent, nginx a/b. Only openjev is model-serving; cerebro/vegtam not observed in rocm-smi pids | `R2-serving.md §3` |
| Generative engine present? | **No.** No SGLang or vLLM process; no listener on 8012/8014/8017; `systemctl` shows no model-like service | `R2-serving.md §1, §4` |
| Historical O1–O4 | All HISTORICAL measurements, none running today (containers absent, no launch scripts in repo). O1 occamy-1.0 × SGLang (`gx10-occamy-nvfp4`, :8012); O2 qwen3.5-9b × SGLang (`gx10-w3-dense9b`, remote 192.168.2.168:8017); O3 occamy-1.0 × vLLM; O4 qwen3.5-9b × vLLM NVFP4 (image sha256 `2c211a1273b4…`, with MTP). Launchability verdict: **none runnable today** | `R2-serving.md §4`; `docs/serving-options/BEST-CONFIG.md` |
| Restore procedure | UNDOCUMENTED/UNVERIFIED for SGLang/vLLM (no unit files or launch scripts in repo). openjev restore = `docker run` with recorded env + image digest, but no documented command in repo | `R2-serving.md §5` |
| Ledger spend | 2,591 requests (as of last row `2026-10-28T03:35:42.114Z`); 14,517,784 prompt tokens; 1,017,166 completion tokens; 41 files; 2,591 rows | `orchestration/notes/joint-plan/R3-ledger.md §3`; `docs/STATE.md §1` |
| Ledger cap | 4,320 (reserve 0); `2,591 + 1,729 = 4,320` | `R3-ledger.md §3`; `docs/STATE.md §1` |
| Ledger "remaining" | 1,729 = **2026-10-28 snapshot**, not an available balance | `R3-ledger.md §4`; `docs/STATE.md §1` ("snapshot 2026-10-28 — must be re-reconciled") |
| Reservation | One: `CCS-2026-11-05`, requested 1,500, granted 1,500, `bound_applied=requested_count`, `operator_cap=2000`, `ledger_remaining_at_reservation=1729`, ts `2026-11-05T08:03:11Z`, `dry_run=false`. Recorded in both `RESERVATIONS.json` and `RESERVATION-CCS-2026-11-05.json` (byte-equivalent, one reservation, not two). No reservation consumer in code; whether the 1,500 were spent is UNKNOWN | `R3-ledger.md §1`; `experiments/ptr-engine/measure/RESERVATIONS.json` |
| Dollar cost | Only recorded figure: declared $0.20/1M uncached input tokens in `state/config/r2-prompt-cost.json`, explicitly "declared, not measured — the box is on-prem". O1–O4 one 71-turn run: $0.007532–$0.023968 | `R3-ledger.md §6.1`; `docs/prompt-system/R2-PROMPT-RESULTS.md §6` |
| Energy cost | Not recorded anywhere | `R3-ledger.md §6.4` |
| Gen-6 status | `not_adjudicable` (2026-10-28); 16-cell grid; 6 of 16 usable; 8 stamped `[]`; 2 `ABSENT` (no manifest); 1,270 request rows = ledger delta exactly; four instrument defects (treatments never fired, replicate collapse, absent stamp admitted, cap-gate under-count) | `docs/STATE.md §1`; `docs/GRID-2-FINAL.md` |
| Gen-7 rule | Any fixture/`run_longrun.py` change mints gen-7; gen-6 rows become non-poolable; re-run all-or-nothing per arm. Gen-7 requires v9 wall, rep identity, activation gating, stamp rule before any call | `docs/STATE.md §1`; `consonance-bounded-context-evaluation.md:489-491` |
| p95 floor | `min_n_for(0.95) = 60`; refused at n=48 (gen-6 pointer-stable n_eff 26.14) | `consonance-bounded-context-evaluation.md:389-393`; `docs/GRID-2-FINAL.md` |

**Consequence (must be stated plainly): the current machine hosts no generative inference engine at all.** The only model-serving process is a sequence-classification reranker (openjev on 8088). Therefore **every current-machine generative cell is gated on deploying an engine**, which is not currently available, not documented, not approved, and not priced here. Measured free VRAM today is 6,130,159,616 B (~5.71 GiB); the upper bound if the rerank tenant were released is 7,674,114,048 B (~7.15 GiB). Engine deployment is priced as a separate blocked line, never assumed.

## 3. Serving inventory and availability matrix

### 3.1 Live (observed 2026-11-07, read-only)

| PID | argv (verbatim) | engine / version | model identity | port | VRAM | manager |
|---|---|---|---|---|---|---|
| 9738 (container PID 1, docker `5a0ed0108a6c`) | `python -u /app/server.py` | PyTorch 2.9.1+rocm7.1.1, Transformers 5.15.0, FastAPI/uvicorn | `Qwen3_5ForSequenceClassification` (qwen3_5), bfloat16, 32 layers, hidden 2560, max_pos 262144, labels {contradiction,entailment,neutral} | 127.0.0.1:8088 | 9,421,869,056 B (~8.77 GiB) on GPU0 | plain Docker, restart policy `no`, cgroup `system.slice/docker-5a0ed…scope`; no unit file in repo |

No SGLang/vLLM process. No listener on 8012/8014/8017. `nvidia-smi` failed (no NVIDIA driver/GPU).

### 3.2 Historical O1–O4 (comparison candidates, NOT current live config)

| ID | model | engine | exact flags (from `docs/serving-options/BEST-CONFIG.md`) | status today |
|---|---|---|---|---|
| O1 | occamy-1.0 (MoE, NVFP4) | SGLang 0.0.0.dev1+g4ccff141d | page_size 1; mamba_radix_cache_strategy extra_buffer; radix_eviction_policy lru; mem_fraction_static 0.45; kv_cache_dtype fp8_e4m3; max_mamba_cache_size 64; max_running_requests 5; context 131072 | UNAVAILABLE — container `gx10-occamy-nvfp4` absent; no launch script; :8012 no listener |
| O2 | qwen3.5-9b (dense, NVFP4) | SGLang | `--page-size 64 --mamba-radix-cache-strategy no_buffer --max-mamba-cache-size 40 --mem-fraction-static 0.08 --context-length 32768`, NVFP4 modelopt_fp4; remote 192.168.2.168:8017 | UNAVAILABLE — container `gx10-w3-dense9b` torn down; :8017 no listener |
| O3 | occamy-1.0 | vLLM | `--block-size 64 --prefix-match-unit 16 --mamba-cache-mode align --enable-prefix-caching --enable-prompt-tokens-details --kv-cache-dtype fp8 --gpu-memory-utilization 0.34 --max-model-len 32768`, no MTP | UNAVAILABLE |
| O4 | qwen3.5-9b NVFP4 | vLLM | config V1 of WIN-VLLM: `--block-size 64 --quantization modelopt_fp4 --kv-cache-dtype fp8 --enable-prefix-caching --enable-prompt-tokens-details --gpu-memory-utilization 0.15 --max-num-seqs 6 --max-num-batched-tokens 8192 --max-model-len 32768`, image sha256 `2c211a1273b4…`, with MTP speculative-config | UNAVAILABLE — `wv-v1` removed on restore |

Launchability verdict: **none of O1–O4 can be launched on this machine today.** Do not invent equivalents. Historical measurements are comparison candidates, not evidence of current live configuration.

### 3.3 Availability matrix (per config)

| config | launchable today? | reason | price status |
|---|---|---|---|
| openjev rerank (9738) | yes (running) | live, observed | n/a (reranker, not generative) |
| O1 | NO | container/image absent, no launch script, no listener | unpriced-unavailable |
| O2 | NO | container torn down, remote host | unpriced-unavailable |
| O3 | NO | no vLLM container/image | unpriced-unavailable |
| O4 | NO | `wv-v1` removed on restore | unpriced-unavailable |
| any new generative engine on this machine | NO | no engine installed; deployment unapproved and unpriced | unpriced-unavailable (prerequisite line) |
| current-machine serving-setting variants (memory fraction, block size, etc.) | NO | require a deployed engine | unpriced-unavailable |
| GPU memory-utilization sweep | NO | require a deployed engine | unpriced-unavailable |

### 3.4 Guardrails for a later funded exclusive window (not executed now)

- **Snapshot before any memory sweep:** `rocm-smi` VRAM used/total per GPU; KFD process list (PID/name/VRAM); docker container list + image digests + env; openjev `/health` JSON. Restore = same container digest + env + port.
- **Fingerprints to pin:** host kernel/driver (ROCm 7.1.52802); container image digest sha256 `9371dc20…`; model dir contents/`config.json`; torch/transformers versions; env vars `OPENJEV_MODEL_DIR/BATCH/MAX_LEN/DEVICE/PORT`; device name AMD Radeon RX 9070; `/health` output. For any future SGLang/vLLM launch, additionally: image tag/digest, full argv, engine version, model weights path/hash, quantization, GPU memory fraction, context length, kv-cache dtype, block/page size, max-num-seqs, max-model-len, port, and the exact restore command.
- **Exclusive window requires:** no other GPU tenants (only openjev uses GPU0 today; desktop uses iGPU), isolate experiment sessions, fingerprint every launch, restore exact original config after experiments.
- **Higher cache memory is a variable to test, not a presumed win.**
- **Restore is UNVERIFIED** — the exact restart commands must be produced and reviewed before any restart is authorised.

## 4. Isolation and restore strategy (for a later funded window)

1. **Exclusive session:** no concurrent GPU tenants; experiment sessions isolated from the rerank tenant and desktop.
2. **Fingerprints pinned (frozen, Gate 0.4):** model (id + revision/quantisation digest), tokenizer (files/hash + chat-template hash), renderer (content digest module→bytes), engine (image digest + exact flags). Placeholders are a hard stop.
3. **Pre-sweep snapshot** (§3.4) captured and stored; restore command recorded.
4. **Restore currently undocumented/unverified** — the exact commands must be produced before any restart is authorised. No restart is performed by this plan.
5. **No pooling across builds/generations/ledger epochs**; gen-6 and gen-7 never share a column.

## 5. Experiment matrix

### 5.1 Arms (from `consonance-bounded-context-evaluation.md §6`)

| Arm | Name | Definition | Fetches | Requests/turn |
|---|---|---|---|---|
| A | `full-transcript` | append-only, FIFO at declared wall | (baseline, no fetch) | 1 |
| B | `transcript-compact` | existing digest at cap, recent 4 turns raw | digest | 1 + digests |
| C | `masking-no-fetch` | old tool outputs replaced by pointer markers, no external fetch | none (masked only) | 1 |
| D | `bounded-context-fetch` (BRCV) | frozen prefix, bounded window, pointer table, `fetch` on demand, checkpoint only on forecast | `fetch(ref, range?)` on demand | 2 (fetch + answer) |
| E | `oracle-evidence` | same prompt budget as D, needed evidence injected | injection of needed evidence | 1 |

Shared requirements: one fixture set/version, one frozen build, four equal fingerprints, same verifier and acceptance checks, same prompt-budget accounting. D's fetch outcomes carry the vocabulary OK / NOT_FOUND / STALE_OR_REVOKED / SCOPE_UNGRANTED.

**C0F equal-information control** is not one of A–E; it is the equal-information baseline used as an additional comparison. Source: P2 row `consonance-bounded-context-evaluation.md:56` — C0F 1,911.2 uncached/turn vs R 3,524.0, ratio 1.8441. Consequence: the pointer arm can be *more* expensive at equal information; Arm D must be compared against Arm A at equal information, not against a truncated strawman.

### 5.2 Tasks, horizons, replicates

Tasks: `longrun/fixtures/LR-01..06.json`, classes repo-fix / multi-file-refactor / bug-fix-with-test / constraint-survival / adversarial-debug / doc-sync; lengths 48 / 64 / 56 / 40 / 72 / 60 turns.

| Horizon | Cells | Note |
|---|---|---|
| 10 turns | 6 tasks | all fixtures supply it |
| 30 turns | 6 tasks | all fixtures supply it |
| 60 turns | **3 tasks** (LR-02 64, LR-05 72, LR-06 60) | **LR-01 (48), LR-03 (56), LR-04 (40) cannot supply 60 turns → `UNAVAILABLE`, not imputed** |

Replicates: 3 reps per task/arm. "6 tasks × 3 rep" at 60 turns is not available and is never written as if it were.

Additional unavailable fixture classes: multi-hop retrieval and unavailable/stale/revoked source are MISSING from every authored fixture; recorded `UNAVAILABLE`/`NOT_OBSERVED`, never scored as success, no fixture fabricated.

### 5.3 Two-level comparison discipline

1. **Context arms compared within one identical stack first** (same model, tokenizer, template, serving config, workload).
2. **Serving settings compared with the context arm held fixed.**
3. **Interactions only from matched cells.**
4. An engine/model/flag change is **never** presented as an isolated engine effect. Confounded engine/model/flag comparisons are not allowed.

### 5.4 Activation predicates (computed from the stamp, never by name)

- A (at cap): `evicted_turns > 0`
- B: `digest_rows > 0`
- C: `masked_rows > 0`
- D: `fetch_rows > 0` and `retrieval_outcomes` non-empty
- E: `oracle_injections > 0`

A cell failing is reported `INVALID-INSTRUMENT` and excluded by rule. Absent stamp ⇒ excluded. D's rows carry the fetch-outcome vocabulary.

### 5.5 Controls (per arm + battery)

Per arm positive/negative controls and falsifiers as in `VALIDATION-ROADMAP.md` Stage 3 table. Plus battery: identical-repeat cache control for every arm; append cache control for every arm; holistic positive control (fact present, fetch works, answer correct); holistic negative control (fact absent from store ⇒ arm must abstain). Each run red first on a deliberately broken log.

## 6. Preregistration and validity gates

Gates 0.1–0.11 (from `VALIDATION-ROADMAP.md §Stage 0`):

| Gate | Pass condition (condensed) | Source |
|---|---|---|
| 0.1 | positive control can pass: known-good log passes; wrong-value log fails on the value; missing-fact log fails distinguishably; same log scores identically twice; tampered fixture exits 2 | `VALIDATION-ROADMAP.md:49`; protocol §3.1 |
| 0.2 | ≥12 decidable checkpoints, all gradeable (today grade_v5 grades 8 of 12; 4 need NONE/call_at_line branches) | `VALIDATION-ROADMAP.md:50`; protocol §3.2 |
| 0.3 | fixture wall priced from measured growth (gen-6 wall priced from declared padding 10,616 vs live base 5,628–6,139 at 41–98 tok/turn ⇒ 73–113 turns to wall > 48) | `VALIDATION-ROADMAP.md:51`; protocol §3.2 |
| 0.4 | four fingerprints frozen: model (id + revision/quantisation digest), tokenizer (files/hash + chat-template hash), renderer (content digest module→bytes), engine (image digest + exact flags); placeholders are a hard stop | `VALIDATION-ROADMAP.md:52`; protocol §3.3 |
| 0.5 | replicate identity: unique `(arm, rep, cell, turn_index)`; `rep` in `run_id`; pre-analysis assertion row count = cells × turns × reps | `VALIDATION-ROADMAP.md:53`; protocol §3.4 |
| 0.6 | activation gating: per arm the declared predicate non-zero on the cell's own rows; exclusion computed from the stamp, never by name | `VALIDATION-ROADMAP.md:54`; protocol §3.5 |
| 0.7 | budget preflight: ledger rebuilt, arithmetic printed per arm, caps set before first call; unknown ⇒ zero requests | `VALIDATION-ROADMAP.md:55`; protocol §3.6 |
| 0.8 | independent verifier assigned: a process/person that ran none of the arms; fixture digest checked at score time; `score_longrun.py` exits 2 on tamper, 3 on stub | `VALIDATION-ROADMAP.md:56`; protocol §3.7 |
| 0.9 | scorer can express a retrieval miss and an abstention: `retrieval_miss`/`abstained_correctly` scorable, red→green control (fabricated answer must fail before abstention passes); today grep for `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` returns 0 matches; four check kinds are artifact/fact/constraint/repair | `VALIDATION-ROADMAP.md:57`; protocol §7 |
| 0.10 | prototype extension offline-deterministic: alignment-aware append planner (2-token pad at residue 0/1), fetch batching by body tokens, retrieval-outcome vocabulary, deterministic resume each have unit tests; index digest reproduces across two processes and two roots | `VALIDATION-ROADMAP.md:58` |
| 0.11 | law package re-derived: residual table reproduces (`sglang 301 {0: 218, …}`; `vllm 86 {−1056: 1, 0: 85}`) | `VALIDATION-ROADMAP.md:59` |

Additional validity rules carried forward:
- **Positive control must pass; wrong-value and missing-fact controls must fail appropriately.**
- **12 gradeable checkpoints.**
- **Measured-growth fixture wall** (not declared padding).
- **Unique `(arm, rep, cell, turn_index)`.**
- **Computed treatment-activation gates.**
- **Independent verification.**
- **Frozen model/tokenizer/renderer/engine fingerprints.**
- **No pooling across incompatible generations.**
- **Gen-6 is `not_adjudicable`** and its rows are non-poolable with any newer generation.
- **A new claim needs fresh preregistration** rather than a silently edited p95 rule. `BOUNDARY-PREREG` (696 scheduled / 810 ceiling) is a separate registered candidate, never pooled. Any new hypothesis/estimator/ablation (e.g. D-variant without alignment-aware planner) needs its own preregistration before a claim.
- **p95 admissibility:** `min_n_for(0.95) = 60`; p95 refused at n=48; n_eff on the arm's own turn-ordered series (`n_eff = n(1−r)/(1+r)`; gen-6 pointer-stable 26.14 vs floor 60).
- **Analysis rules (§8):** paired task-level differences within one fixture and fingerprint set; no pooled arm means; no ratio of totals; intervals name method and n; `df = 2` reported as such; no p95 below floor; no re-pinning after rows seen; derived is not measured (`uncached = prompt − cached` is `derived`); null semantics per endpoint and field (`:8012` null cached = 0; `:8014` null = unknown); generation labels on every row/table.
- **Non-results first-class:** `UNDEFINED`, `UNAVAILABLE`, `NOT_OBSERVED`, `INVALID-INSTRUMENT`, `UNFUNDED` — each appears in the table, never replaced by zero/blank.

## 7. Line-item budget

### 7.1 Derivations (shown, not asserted)

- Turns per arm per rep over available cells: `6×10 + 6×30 + 3×60 = 60 + 180 + 180 = 420`.
- Four one-request arms (A,B,C,E): `4 × 420 = 1,680` per rep.
- D at 2 req/turn: `2 × 420 = 840` per rep.
- Per rep: `1,680 + 840 = 2,520`. Three reps: `3 × 2,520 = 7,560`.
- Plan's compact form: `3 × (4 × 420 + 2 × 420) = 3 × (1,680 + 840) = 3 × 2,520 = 7,560`. ✓
- 7,560 excludes B digests and D checkpoints (≥1 per cell) ⇒ `≥ 7,560` (lower bound, not exact).
- Four-stack arithmetic: `4 × 7,560 = 30,240` (context-comparison requests only, before extras).
- C0F control: `3 × 420 = 1,260` (assumption: one control per cell per replicate).
- Cells per arm per rep: `6 + 6 + 3 = 15`; cell-arms per rep = `15 × 5 = 75`; over 3 reps = 225 cell-arms.

### 7.2 Budget table (machine-readable)

| id | stage | arm/condition | stack | tasks | horizons | reps | formula a×b×c | requests | lower/upper | price status | basis / notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0 | instrument validity (offline) | all (none) | — | — | — | 0 | 0 | 0/0 | priced | `VALIDATION-ROADMAP.md` Stage 0; 0 requests by construction; gates 0.1–0.11 |
| L1 | 1 | law open cell (2-token rule) | SGLang (historical) | 1 probe | 1 | — | ≈9 | ≈9 | 9/9 | unpriced-unavailable | historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a) |
| L2 | 2a | E1 cache-boundary sweep | SGLang (historical) | 1 skeleton | offsets | 3 reps × ≥8 offsets + controls | 36 | 36 | 36/60 | unpriced-unavailable | historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a) |
| L3 | 2b | five-arm instrument pilot | SGLang (historical) | 1 task | 30 turns | 1 rep × 5 arms | `30×4 + 60` + ~5 | ≈185 | 180/190 | unpriced-unavailable | historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a) |
| L4 | 3 | five-arm comparative (A/B/C/D/E) | single runnable stack | 6/6/3 | 10/30/60 | 3 | `3 × (4×420 + 2×420)` | 7,560 | 7,560/≥7,560 | priced | `consonance-bounded-context-evaluation.md §6.3`; excludes digests/checkpoints; **runnable_today = NO** (no generative engine on this machine) |
| L5 | 3 | C0F equal-information control | same as L4 | 6/6/3 | 10/30/60 | 3 | `3 × 420` | 1,260 | 1,260/1,260 | priced | assumption: one control per cell per replicate; not folded into 7,560 |
| L6 | 3 | per-additional-runnable-stack replication | each additional stack | 6/6/3 | 10/30/60 | 3 | `1 × 7,560` | 7,560 | 7,560/7,560 | unpriced-unavailable | no additional runnable generative stack exists today (O1–O4 unavailable); engine deployment unapproved |
| L14 | 3 | D-variant without alignment-aware planner (ablation) | L4 stack | L4 | L4 | L4 | `840 × 3` (D arm only) | 2,520 | 2,520/2,520 | priced | `[INFERENCE]` adds a sixth arm; needs its own preregistration before a claim; re-priced here as a D arm |
| L7 | 3 | four-stack aggregate (if all runnable) | O1+O2+O3+O4 | 6/6/3 | 10/30/60 | 3 | `4 × 7,560` | 30,240 | 30,240/30,240 | unpriced-unavailable | arithmetic reference only; all four stacks unavailable today |
| L8 | 3 | warmups (separate multiplier) | L4 base | L4 | L4 | L4 | `1 × 225 cell-arms` | 225 | 225/225 | priced | assumption: 1 warmup request per cell-arm per stack (assumption, not measured) |
| L9 | 3 | retries (separate multiplier) | L4 base | L4 | L4 | L4 | `0.05 × 7,560` | 378 | 378/756 | priced | assumption: 5% retry rate (assumption, labelled) |
| L10 | 3 | aborts (separate multiplier) | L4 base | L4 | L4 | L4 | `0.02 × 7,560` | 151.2 | 151/302 | priced | assumption: 2% abort rate; fractional = expected value (assumption, labelled) |
| L11 | 3 | failed calls (separate multiplier) | L4 base | L4 | L4 | L4 | included in base | 0 (already counted) | 0/0 | priced | failures/aborts that reach the wire are rows and already counted in 7,560; not double-counted |
| L12 | 3 | current-machine serving-setting variants | this machine | L4 cells | L4 | L4 | `levels × 7,560` (parametric) | unbounded | — | unpriced-unavailable | blocked on engine deployment; levels (e.g. memory fraction, block size) not yet chosen |
| L13 | 3 | GPU memory-utilization sweep | this machine | L4 cells | L4 | L4 | `levels × 7,560` (parametric) | unbounded | — | unpriced-unavailable | blocked on engine deployment; higher cache memory is a variable to test, not a presumed win |
| L15 | 4 | real-workflow validation | TBD | TBD | TBD | TBD | unbounded | unbounded | —/— | unpriced-unbounded | selection criteria and ground truth must be specified before measurement; request counts are estimates until a task envelope is measured |
| L16 | 4 | multi-append sweep (2–3 points) | TBD | TBD | TBD | TBD | tens | tens | — | unpriced-unbounded | `VALIDATION-ROADMAP.md` Stage 4; estimate only |
| L17 | 4 | resting-window arm (manuscript §6a) | TBD | TBD | TBD | TBD | ≈90 | ≈90 | — | unpriced-unbounded | not approved (`N4-finish-flagship.md`) |
| L18 | 4 | BOUNDARY-PREREG (separate candidate) | TBD | TBD | TBD | TBD | 696 (ceiling 810) | 696 | 696/810 | priced (candidate) | never pooled; approval (e) |
| L19 | — | engine deployment prerequisite (this machine) | this machine | — | — | — | n/a | n/a | — | unpriced-unavailable | no generative engine installed; deployment is an unapproved, unpriced decision |

### 7.3 Budget JSON (machine-readable)

```json
[
  {"id":"L0","stage":0,"arm_condition":"instrument validity (offline)","stack":"none","tasks":null,"horizons":null,"reps":null,"formula":"0","requests":0,"lower":0,"upper":0,"status":"priced","candidate":false,"basis":"VALIDATION-ROADMAP.md Stage 0; 0 requests by construction; gates 0.1-0.11"},
  {"id":"L1","stage":1,"arm_condition":"law open cell (2-token rule)","stack":"SGLang (historical)","tasks":1,"horizons":[1],"reps":null,"formula":"~9","requests":9,"lower":9,"upper":9,"status":"unpriced-unavailable","candidate":true,"basis":"historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a)"},
  {"id":"L2","stage":"2a","arm_condition":"E1 cache-boundary sweep","stack":"SGLang (historical)","tasks":1,"horizons":["offsets"],"reps":3,"formula":"36","requests":36,"lower":36,"upper":60,"status":"unpriced-unavailable","candidate":true,"basis":"historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a)"},
  {"id":"L3","stage":"2b","arm_condition":"five-arm instrument pilot","stack":"SGLang (historical)","tasks":1,"horizons":[30],"reps":1,"formula":"30*4+60+~5","requests":185,"lower":180,"upper":190,"status":"unpriced-unavailable","candidate":true,"basis":"historical SGLang stack unlaunchable today (no SGLang/vLLM process, containers absent); recorded estimate only, not a price; approval (a)"},
  {"id":"L4","stage":3,"arm_condition":"five-arm comparative (A/B/C/D/E)","stack":"single runnable stack","tasks":"6/6/3","horizons":"10/30/60","reps":3,"formula":"3*(4*420+2*420)","requests":7560,"lower":7560,"upper":null,"status":"priced","candidate":false,"basis":"consonance-bounded-context-evaluation.md sec6.3; excludes digests/checkpoints; runnable_today=NO (no generative engine on this machine)"},
  {"id":"L5","stage":3,"arm_condition":"C0F equal-information control","stack":"same as L4","tasks":"6/6/3","horizons":"10/30/60","reps":3,"formula":"3*420","requests":1260,"lower":1260,"upper":1260,"status":"priced","candidate":false,"basis":"assumption: one control per cell per replicate; not folded into 7560"},
  {"id":"L6","stage":3,"arm_condition":"per-additional-runnable-stack replication","stack":"each additional stack","tasks":"6/6/3","horizons":"10/30/60","reps":3,"formula":"1*7560","requests":7560,"lower":7560,"upper":7560,"status":"unpriced-unavailable","candidate":false,"basis":"no additional runnable generative stack exists today (O1-O4 unavailable); engine deployment unapproved"},
  {"id":"L7","stage":3,"arm_condition":"four-stack aggregate (if all runnable)","stack":"O1+O2+O3+O4","tasks":"6/6/3","horizons":"10/30/60","reps":3,"formula":"4*7560","requests":30240,"lower":30240,"upper":30240,"status":"unpriced-unavailable","candidate":false,"basis":"arithmetic reference only; all four stacks unavailable today"},
  {"id":"L8","stage":3,"arm_condition":"warmups (separate multiplier)","stack":"L4 base","tasks":"L4","horizons":"L4","reps":"L4","formula":"1*225 cell-arms","requests":225,"lower":225,"upper":225,"status":"priced","candidate":false,"basis":"assumption: 1 warmup request per cell-arm per stack (assumption, not measured)"},
  {"id":"L9","stage":3,"arm_condition":"retries (separate multiplier)","stack":"L4 base","tasks":"L4","horizons":"L4","reps":"L4","formula":"0.05*7560","requests":378,"lower":378,"upper":756,"status":"priced","candidate":false,"basis":"assumption: 5% retry rate (assumption, labelled)"},
  {"id":"L10","stage":3,"arm_condition":"aborts (separate multiplier)","stack":"L4 base","tasks":"L4","horizons":"L4","reps":"L4","formula":"0.02*7560","requests":151.2,"lower":151,"upper":302,"status":"priced","candidate":false,"basis":"assumption: 2% abort rate; fractional = expected value (assumption, labelled)"},
  {"id":"L11","stage":3,"arm_condition":"failed calls (separate multiplier)","stack":"L4 base","tasks":"L4","horizons":"L4","reps":"L4","formula":"included in base","requests":0,"lower":0,"upper":0,"status":"priced","candidate":false,"basis":"failures/aborts that reach the wire are rows and already counted in 7560; not double-counted"},
  {"id":"L12","stage":3,"arm_condition":"current-machine serving-setting variants","stack":"this machine","tasks":"L4 cells","horizons":"L4","reps":"L4","formula":"levels*7560 (parametric)","requests":null,"lower":null,"upper":null,"status":"unpriced-unavailable","candidate":false,"basis":"blocked on engine deployment; levels (e.g. memory fraction, block size) not yet chosen"},
  {"id":"L13","stage":3,"arm_condition":"GPU memory-utilization sweep","stack":"this machine","tasks":"L4 cells","horizons":"L4","reps":"L4","formula":"levels*7560 (parametric)","requests":null,"lower":null,"upper":null,"status":"unpriced-unavailable","candidate":false,"basis":"blocked on engine deployment; higher cache memory is a variable to test, not a presumed win"},
  {"id":"L14","stage":3,"arm_condition":"D-variant without alignment-aware planner (ablation)","stack":"L4 stack","tasks":"L4","horizons":"L4","reps":"L4","formula":"840*3 (D arm only)","requests":2520,"lower":2520,"upper":2520,"status":"priced","candidate":false,"basis":"[INFERENCE] adds a sixth arm; needs its own preregistration before a claim; re-priced here as a D arm"},
  {"id":"L15","stage":4,"arm_condition":"real-workflow validation","stack":"TBD","tasks":"TBD","horizons":"TBD","reps":"TBD","formula":"unbounded","requests":null,"lower":null,"upper":null,"status":"unpriced-unbounded","candidate":false,"basis":"selection criteria and ground truth must be specified before measurement; request counts are estimates until a task envelope is measured"},
  {"id":"L16","stage":4,"arm_condition":"multi-append sweep (2-3 points)","stack":"TBD","tasks":"TBD","horizons":"TBD","reps":"TBD","formula":"tens","requests":null,"lower":null,"upper":null,"status":"unpriced-unbounded","candidate":false,"basis":"VALIDATION-ROADMAP.md Stage 4; estimate only"},
  {"id":"L17","stage":4,"arm_condition":"resting-window arm (manuscript sec6a)","stack":"TBD","tasks":"TBD","horizons":"TBD","reps":"TBD","formula":"~90","requests":90,"lower":90,"upper":90,"status":"unpriced-unbounded","candidate":false,"basis":"not approved (N4-finish-flagship.md)"},
  {"id":"L18","stage":4,"arm_condition":"BOUNDARY-PREREG (separate candidate)","stack":"TBD","tasks":"TBD","horizons":"TBD","reps":"TBD","formula":"696 (ceiling 810)","requests":696,"lower":696,"upper":810,"status":"priced","candidate":true,"basis":"never pooled; approval (e)"},
  {"id":"L19","stage":null,"arm_condition":"engine deployment prerequisite (this machine)","stack":"this machine","tasks":null,"horizons":null,"reps":null,"formula":"n/a","requests":null,"lower":null,"upper":null,"status":"unpriced-unavailable","candidate":false,"basis":"no generative engine installed; deployment is an unapproved, unpriced decision"}
]
```

### 7.4 Total (explicitly a lower bound, not a precise total)

- **Vocabulary (defined once, at the top of §7):** in this document `priced` means the request count is bounded by a stated formula; it never means dollars are known — dollar and energy costs are UNKNOWN for every line. `unpriced-unavailable` = the stack cannot run today so no request count is committed. `unpriced-unbounded` = the count has no envelope yet.
- **Core executable-if-one-stack-exists count:** `L0 0 + L4 7,560 + L5 1,260 + L8 225 + L9 378 + L10 151.2 + L14 2,520 = 12,094.2` requests. Addition term by term: `0 + 7,560 = 7,560`; `7,560 + 1,260 = 8,820`; `8,820 + 225 = 9,045`; `9,045 + 378 = 9,423`; `9,423 + 151.2 = 9,574.2`; `9,574.2 + 2,520 = 12,094.2`.
- **Candidate-only estimates (not part of the core, not approved):** `L1 9 + L2 36 + L3 185 + L18 696 = 926` requests. Core + candidates = `12,094.2 + 926 = 13,020.2` requests — informational reference only, since L1–L3 are `unpriced-unavailable` and L18 is an unapproved separate candidate.
- **Not counted:** `L6` (= `n × 7,560` per additional runnable stack, n = 0 today), `L7` (30,240 arithmetic reference, all four stacks unavailable), `L12`/`L13` (`levels × 7,560`, levels unchosen, engine absent), `L15`/`L16`/`L17` (unbounded), `L19` (deployment prerequisite, n/a).
- **Executable today: 0 requests** — every generative line is gated on L19.
- **Closing:** the core figure is a lower bound over bounded-count lines; it is not a precise programme total, it is not an executable commitment, and it excludes every line whose stack is unavailable or whose envelope is unmeasured.

## 8. Budget ledger reconciliation

Four distinct lines (do not merge):

| line | value | status | source |
|---|---|---|---|
| spent (verified, ledger rows) | **2,591 requests** (as of `2026-10-28T03:35:42Z`; 14,517,784 prompt tok; 1,017,166 completion tok) | verified | `REQUEST-LEDGER.json`; `R3-ledger.md §3` |
| reserved (recorded, spend unverified) | **1,500 requests** (CCS-2026-11-05, `granted_count=1500`, `dry_run=false`, `bound_applied=requested_count`, `operator_cap=2000`) | recorded, unverified | `RESERVATIONS.json`; `R3-ledger.md §1` |
| unknown | post-2026-10-28 spend + reservation actualisation + dollar/energy cost | unknown | `R3-ledger.md §4-5` |
| available | **UNKNOWN** | not computable | `R3-ledger.md §5` |

- `4,320 = cap`; `2,591 + 1,729 = 4,320`. The 1,729 is `cap − spent` under the ledger's own arithmetic, recorded 2026-10-28. It **cannot be claimed as available**: it is a snapshot, the reservation (1,500) was recorded against that same stale snapshot with no spend tracking, and no ledger rebuild has occurred since 2026-10-28.
- Conditional upper bound (not a balance): if the reservation is entirely unspent and no other spend occurred, `1,729 − 1,500 = 229` requests — both premises unverified.
- Dollar cost unknown (only declared $0.20/1M uncached input tokens, explicitly not measured). Energy cost unknown (not recorded anywhere).
- **Reconciliation step required before funding:** rebuild the ledger from `measure/rows-*.jsonl` via `tools/request_ledger.py`, recompute spend, re-verify the reservation against actual rows (or mark it unspent), and recompute `available = cap − spent − verified_reserved`. Until then, `available = UNKNOWN` and zero requests are sent (`VALIDATION-ROADMAP.md` §0 rule 2).

## 9. Results and recommendation method

### 9.1 Required per-run/per-task row schema (all rows retained)

Per horizon and arm (`consonance-bounded-context-evaluation.md §6.2` + §7 worked example):

- **Identifiers:** `call_id`, `run_id`, `arm`, `task_id`, `step`/turn_index, `manifest_id`, `branch_id`, `state_epoch`, `model`, `engine`, `model_fingerprint`, `tokenizer_fingerprint`, `renderer_fingerprint`, `engine_fingerprint`.
- **Three dimensions on every row:** context arm, serving stack, workload/task (all three present; no row omits a dimension).
- **Quality outcome:** `verified_success` (boolean), `exit_cause` (e.g. abstained), `retrieval_miss`, `abstained_correctly`, `tokens_to_verified_success` (null when undefined, never 0).
- **Null-capable cache fields:** `prompt_tokens`, `cached_tokens` (null possible per endpoint semantics), `uncached_prefill_tokens` (null unless engine exposes), `uncached` (derived, formula named, never quoted as measurement).
- **Latency:** `ttft_ms`, `total_ms` (end-to-end latency), client elapsed.
- **Tokens:** `completion_tokens`, fetch calls and fetch tokens.
- **Events:** `retrieval_attempt{ref, outcome}` with outcomes OK/NOT_FOUND/STALE_OR_REVOKED/SCOPE_UNGRANTED; `masked_entry{ref, since_turn}`.
- **Resource:** storage/index size, rebuild cost, end-to-end wall time.
- **Decomposition:** per-turn and per-segment (pre-boundary / transition / post-boundary); never arm means alone.

### 9.1.1 Illustrative result rows (shape examples — no measurement, not evidence)

```json
[
  {
    "call_id": "run-2026-11-07-D-LR05-60-rep2-turn41",
    "run_id": "D-LR05-60-r2",
    "arm": "D",
    "stack": "SGLang-occamy-1.0-memfrac0.45-fp8",
    "task_id": "LR-05",
    "step": 41,
    "turn_index": 41,
    "horizon": 60,
    "rep": 2,
    "manifest_id": "mf-001",
    "branch_id": "b0",
    "state_epoch": 1,
    "model": "occamy-1.0",
    "engine": "SGLang",
    "model_fingerprint": "sha256:0000...model",
    "tokenizer_fingerprint": "sha256:0000...tok",
    "renderer_fingerprint": "sha256:0000...rnd",
    "engine_fingerprint": "sha256:0000...eng",
    "verified_success": true,
    "exit_cause": null,
    "retrieval_miss": false,
    "abstained_correctly": null,
    "tokens_to_verified_success": 18340,
    "ttft_ms": 812.4,
    "total_ms": 9741.9,
    "client_elapsed_ms": 10012.3,
    "prompt_tokens": 41250,
    "cached_tokens": 38640,
    "uncached_prefill_tokens": null,
    "uncached": 2610,
    "uncached_basis": "derived = prompt - cached",
    "completion_tokens": 512,
    "fetch_tokens": 180,
    "retrieval_attempts": 3,
    "retrieval_outcomes": ["OK", "OK", "NOT_FOUND"],
    "activation": {"fetch_rows": 3},
    "storage_index_bytes": 4096,
    "rebuild_cost_ms": 12.5,
    "wall_time_ms": 10012.3,
    "segment": "post-boundary",
    "null_semantics": null,
    "generation": "gen-7 (illustrative)"
  },
  {
    "call_id": "run-2026-11-07-A-LR05-60-rep2-turn41",
    "run_id": "A-LR05-60-r2",
    "arm": "A",
    "stack": "SGLang-occamy-1.0-memfrac0.45-fp8",
    "task_id": "LR-05",
    "step": 41,
    "turn_index": 41,
    "horizon": 60,
    "rep": 2,
    "manifest_id": "mf-001",
    "branch_id": "b0",
    "state_epoch": 1,
    "model": "occamy-1.0",
    "engine": "SGLang",
    "model_fingerprint": "sha256:0000...model",
    "tokenizer_fingerprint": "sha256:0000...tok",
    "renderer_fingerprint": "sha256:0000...rnd",
    "engine_fingerprint": "sha256:0000...eng",
    "verified_success": true,
    "exit_cause": null,
    "retrieval_miss": false,
    "abstained_correctly": null,
    "tokens_to_verified_success": 21000,
    "ttft_ms": 790.1,
    "total_ms": 9400.5,
    "client_elapsed_ms": 9650.2,
    "prompt_tokens": 41250,
    "cached_tokens": null,
    "uncached_prefill_tokens": null,
    "uncached": null,
    "uncached_basis": "not derived (cached unknown)",
    "completion_tokens": 520,
    "fetch_tokens": 0,
    "retrieval_attempts": 0,
    "retrieval_outcomes": [],
    "activation": {"evicted_turns": 12},
    "storage_index_bytes": null,
    "rebuild_cost_ms": null,
    "wall_time_ms": 9650.2,
    "segment": "post-boundary",
    "null_semantics": "endpoint :8014 -> null = unknown",
    "generation": "gen-7 (illustrative)"
  },
  {
    "call_id": "run-2026-11-07-D-LR05-60-rep1-turn22",
    "run_id": "D-LR05-60-r1",
    "arm": "D",
    "stack": "SGLang-occamy-1.0-memfrac0.45-fp8",
    "task_id": "LR-05",
    "step": 22,
    "turn_index": 22,
    "horizon": 60,
    "rep": 1,
    "manifest_id": "mf-001",
    "branch_id": "b0",
    "state_epoch": 1,
    "model": "occamy-1.0",
    "engine": "SGLang",
    "model_fingerprint": "sha256:0000...model",
    "tokenizer_fingerprint": "sha256:0000...tok",
    "renderer_fingerprint": "sha256:0000...rnd",
    "engine_fingerprint": "sha256:0000...eng",
    "verified_success": false,
    "exit_cause": "abstained",
    "retrieval_miss": false,
    "abstained_correctly": false,
    "tokens_to_verified_success": null,
    "ttft_ms": 650.0,
    "total_ms": 7200.0,
    "client_elapsed_ms": 7450.0,
    "prompt_tokens": 30000,
    "cached_tokens": 27000,
    "uncached_prefill_tokens": null,
    "uncached": 3000,
    "uncached_basis": "derived = prompt - cached",
    "completion_tokens": 120,
    "fetch_tokens": 90,
    "retrieval_attempts": 1,
    "retrieval_outcomes": ["OK"],
    "activation": {"fetch_rows": 1},
    "storage_index_bytes": 4096,
    "rebuild_cost_ms": 12.5,
    "wall_time_ms": 7450.0,
    "segment": "pre-boundary",
    "null_semantics": null,
    "generation": "gen-7 (illustrative)"
  },
  {
    "call_id": "run-2026-11-07-D-LR05-60-rep3-turn09",
    "run_id": "D-LR05-60-r3",
    "arm": "D",
    "stack": "SGLang-occamy-1.0-memfrac0.45-fp8",
    "task_id": "LR-05",
    "step": 9,
    "turn_index": 9,
    "horizon": 60,
    "rep": 3,
    "manifest_id": "mf-001",
    "branch_id": "b0",
    "state_epoch": 1,
    "model": "occamy-1.0",
    "engine": "SGLang",
    "model_fingerprint": "sha256:0000...model",
    "tokenizer_fingerprint": "sha256:0000...tok",
    "renderer_fingerprint": "sha256:0000...rnd",
    "engine_fingerprint": "sha256:0000...eng",
    "verified_success": null,
    "exit_cause": null,
    "retrieval_miss": null,
    "abstained_correctly": null,
    "tokens_to_verified_success": null,
    "ttft_ms": null,
    "total_ms": null,
    "client_elapsed_ms": null,
    "prompt_tokens": null,
    "cached_tokens": null,
    "uncached_prefill_tokens": null,
    "uncached": null,
    "uncached_basis": null,
    "completion_tokens": null,
    "fetch_tokens": null,
    "retrieval_attempts": null,
    "retrieval_outcomes": null,
    "activation": {"fetch_rows": 0},
    "instrument_status": "INVALID-INSTRUMENT",
    "exclusion_reason": "activation predicate failed: fetch_rows = 0 for arm D on this cell (treatment never fired)",
    "storage_index_bytes": null,
    "rebuild_cost_ms": null,
    "wall_time_ms": null,
    "segment": null,
    "null_semantics": null,
    "generation": "gen-7 (illustrative)"
  },
  {
    "call_id": null,
    "run_id": null,
    "arm": "D",
    "stack": "SGLang-occamy-1.0-memfrac0.45-fp8",
    "task_id": "LR-01",
    "step": null,
    "turn_index": null,
    "horizon": 60,
    "rep": null,
    "manifest_id": null,
    "branch_id": null,
    "state_epoch": null,
    "model": "occamy-1.0",
    "engine": "SGLang",
    "model_fingerprint": "sha256:0000...model",
    "tokenizer_fingerprint": "sha256:0000...tok",
    "renderer_fingerprint": "sha256:0000...rnd",
    "engine_fingerprint": "sha256:0000...eng",
    "verified_success": null,
    "exit_cause": null,
    "retrieval_miss": null,
    "abstained_correctly": null,
    "tokens_to_verified_success": null,
    "ttft_ms": null,
    "total_ms": null,
    "client_elapsed_ms": null,
    "prompt_tokens": null,
    "cached_tokens": null,
    "uncached_prefill_tokens": null,
    "uncached": null,
    "uncached_basis": null,
    "completion_tokens": null,
    "fetch_tokens": null,
    "retrieval_attempts": null,
    "retrieval_outcomes": null,
    "activation": null,
    "instrument_status": "UNAVAILABLE",
    "exclusion_reason": "fixture LR-01 supplies 48 turns; 60-turn horizon unavailable — not imputed",
    "storage_index_bytes": null,
    "rebuild_cost_ms": null,
    "wall_time_ms": null,
    "segment": null,
    "null_semantics": null,
    "generation": "gen-7 (illustrative)"
  }
]
```

All five rows above are illustrative shapes carrying no measured value and are never citable as results. Every row carries all three dimensions (context arm, serving stack, workload/task). Nulls are distinguishable from zeros and carry their semantics (`:8012` null cached = 0; `:8014` null = unknown). Rows 4 and 5 demonstrate the retention rule: invalid and missing cells remain in the table with an `exclusion_reason` and null measurements, never replaced by a blank or a zero.

### 9.2 Retention and reporting rules

- **Invalid/missing rows stay visible** with an exclusion reason (`INVALID-INSTRUMENT`, `UNAVAILABLE`, `NOT_OBSERVED`, `UNDEFINED`, `UNFUNDED`); none replaced by zero/blank.
- **All rows are retained**, not only Pareto winners.
- **Spread + uncertainty:** distributions for end-to-end latency and TTFT; paired task-level differences with intervals naming method and n (t-based with df stated, bootstrap with seed, Clopper-Pearson for proportions); `df = 2` reported as such; no p95 below floor.
- **Workload-specific recommendations** offered without imposing an unchosen quality floor and without hiding quality regressions.
- **Pareto view** reported alongside spreads, not as a selection that drops rows.
- **Null semantics** recorded on every row carrying a null (`:8012` null cached = 0; `:8014` null = unknown).
- **Generation labels** on every row/table; gen-6 and gen-7 never in the same column.
- **Derived is not measured.** `uncached = prompt − cached` is `derived` with the formula named.

### 9.3 Fields not in the doc (labelled, not invented)

Warmup, resource usage beyond storage/index size, and reasoning-token split are **not named** in §6.2/call record. They are recorded as `NOT_OBSERVED`/`UNSTATED` unless the inventory supplies them. Request count is the ledger/budget dimension, not a per-row field.

## 10. Decisions required from the operator

1. **Fund or not** — approve any live/paid request at all (approval (a)); until then, zero requests.
2. **Cap level** — if funding, by how much above 4,320 (approval (b)); the comparative alone needs ≥7,560, and the core single-stack programme is `12,094.2` (with candidates `13,020.2`), executable today `0`.
3. **Which stacks to attempt despite unavailability** — whether to pursue engine deployment (O1–O4 equivalents or a new engine) on this machine or elsewhere, knowing none is runnable today.
4. **Whether engine deployment on this machine is in scope** — deploying a generative engine consumes the ~5.71 GiB measured free VRAM, conflicts with the rerank tenant, and requires documented, verified restore commands (currently UNVERIFIED).
5. **Separate approval for any fixture/runner change** that would mint a new generation (approval (d)) — gen-7 requires v9 wall, rep identity, activation gating, stamp rule; gen-6 rows become non-poolable.
6. **Whether to run candidate-only pilots first** (L1≈9, L2=36, L3≈185) under approval (a) before any comparative.
7. **Whether the D-variant ablation (L14) and BOUNDARY-PREREG (L18) are in scope** — each needs its own preregistration before a claim.

---

## Acceptance checks (for the verifier)

- `3 × (4 × 420 + 2 × 420) = 3 × (1,680 + 840) = 3 × 2,520 = 7,560` recomputes in §7.1. ✓
- `4 × 7,560 = 30,240` shown in §7.2 L7. ✓
- `420 = 6×10 + 6×30 + 3×60 = 420` shown in §7.1. ✓
- Free VRAM: free today `17,095,983,104 − 10,965,823,488 = 6,130,159,616 B ≈ 5.71 GiB`; `7,674,114,048 B (~7.15 GiB)` only as the upper bound conditional on releasing PID 9738. ✓
- Every unpriced line labelled (`unpriced-unavailable` or `unpriced-unbounded`) in §7.2/§7.3. ✓
- No total stated as precise (§7.4 explicitly a lower bound + named unbounded lines). ✓
- No sentence claims O1–O4 are current; all marked HISTORICAL/UNAVAILABLE (§2, §3.2, §3.3). ✓
- No sentence implies this machine can run a generative arm today (§2 consequence, §3.3, §7.4 caveat). ✓
- Zero model requests, zero service restarts, zero fixture/grader changes, zero ledger writes occurred producing this package (status banner, §1). ✓
- Spend/reserved/unknown/available distinguished as four separate lines (§8). ✓
- Invalid rows retained with exclusion reasons; all rows retained (§9.2). ✓
- At least one illustrative **result row** (§9.1.1) contains all three dimensions, a per-run/task identifier, a quality outcome, and null-capable cache fields; an invalid row and a missing cell are both retained with an `exclusion_reason` and null measurements. ✓
