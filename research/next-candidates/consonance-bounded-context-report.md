# Consonance bounded recoverable context — research report

## 0. Status

| field | value |
|---|---|
| date | **2026-11-03** |
| author unit | `CONSONANCE-BC-REPORT` (worker unit; sibling `CONSONANCE-BC-EVAL` writes the protocol) |
| model calls / live requests made for this document | **0 / 0** — no endpoint, no `curl`, no GPU, no model lock, no server restart |
| evidence cut-off | **2026-10-28** (`docs/STATE.md` is the newest current-state page; nothing after it is cited) |
| deliverable class | **research recommendation + pointer to a testable protocol** — not an implementation, not production readiness, not an authorisation for live traffic |
| what this is not | it does not implement, specify, or assert the existence of a Rust kernel, a stripped-down omp integration, a `ContextManifest` schema, or any Consonance wire API |
| revision | 2026-11-03, post-VReport: E2 budget qualification and two citation fixes; no evidence changed |

Offline verification performed for this document (see §9 for the exact commands and output): `papers/context-cache/recompute.py C53` → `PASS 18/18 values match`; an independent recompute of the eight G5 per-fan-out ratios from `experiments/context-cache/cells/G5/rows.jsonl` (192 rows, sha256 `8fd7f9d2…`) → mean 6.744331504, stdev 3.227761582, ratio-of-totals 6.063360882.

---

## 1. Recommendation, up front

**Proceed to `E1-CACHE-BOUNDARY-SWEEP` (≤60 calls), then `E2-CHECKPOINT-COST` at a budget the owner approves; the handoff's ≤120 buys only a one-rep descriptive probe (123 requests by protocol arithmetic, including 3 checkpoint requests), not a verdict, while an adjudicable 3-rep E2 is 369 calls (450 with the 12-checkpoint fixture) and needs explicit owner approval against the 1,729 requests remaining (dated 2026-10-28) — and nothing else on this evidence.**

1. **Do not build the Rust kernel and do not build the stripped-down omp integration from this evidence.** The direction (a deterministic stable prefix, a bounded verbatim working set, an external content-addressed record, pointers, on-demand fetch, masking before summarisation, conditional checkpoints) is a user-supplied direction with a coherent rationale, but the measured record contains **no** adjudicable comparison of it against a full transcript. The one 16-cell attempt to produce that comparison returned `not_adjudicable` for every hypothesis (H1 `not_adjudicable_floor`, H2 `not_adjudicable`, H3 `not_adjudicable`, TVS `UNDEFINED`) — because the *instrument* failed, not because the design lost. A build decision cannot be taken from a null instrument.
2. **The bounded recoverable context view (BRCV) is a hypothesis with a defined falsifier, not a finding.** What the record does establish is narrower and still useful: payload reduction is not the lever, prefix stability is (F1/F2/F3); a pointer-index prompt can carry structure without the answer (quality arm D 0/3); a retention cap produces honest refusals rather than silent wrong answers (33/33 `PTR_STORE_MISS`); and the cheap-looking arm has so far always been cheap for the wrong reason — because it fetched less, failed, or was measured against a blind cache instrument.
3. **The exact next decision is a two-experiment premise test, not a build.** E1 decides whether "rewrite depth" is a usable predictor of cache reuse; E2 decides whether one compaction checkpoint repays its own rebuild inside 20 steps when measured as **uncached work and time-to-verified-success**, not payload — but E2 decides only when it is run at an adjudicable budget: at ≤120 calls (123 actual by protocol arithmetic) it is a one-rep descriptive cost probe that can neither fire nor clear the falsifier, and the 369–450 adjudicable option needs explicit owner approval. If either falsifier fires, the BRCV premise is restated and Consonance is told before further building.
4. **No-go condition (stated once, detailed in §8):** if E1's reuse is not monotone in rewrite offset, or E2's checkpoint does not repay within 20 steps — measured as uncached work — in an adjudicable E2 run (a 120-call descriptive probe cannot trigger this no-go), or the quality emitter cannot return "yes" on a log that satisfies the fixture's own answer contract, or the four comparability fingerprints cannot be frozen, or the request ledger cannot be reconciled before the run — then no BRCV build is recommended on any timeline, and the honest deliverable is the negative result.
5. **Requests are not the binding constraint; the instrument is.** 1,729 of 4,320 requests remain, the gen-6 grid billed 1,270 (79.375/cell, highest cell 96), and 16 cells at the observed maximum cost 1,536 < 1,729. What stopped gen 6 was eight cells whose treatment never fired and a selector that collapsed 288 turn rows into 96.

---

## 2. Question and scope

**The question.** Can a *bounded* prompt — a stable instruction/tool prefix, a bounded recent verbatim window, and deterministic pointers into an external, versioned, authoritative record — retain the information a long coding task needs, while reducing token growth and end-to-end latency, or at least while not losing? And at what measured cost in cache breaks, rebuilds and retrievals?

**The working hypothesis being tested (not assumed).** A stable prefix plus a bounded hot window plus pointer/fetch access to an external record is *no worse* than a growing transcript at equal task success, and *cheaper per completed turn* whenever the transcript's growth outruns the engine's cache. This is proposed, not established. It is also already contradicted in the one regime where it has been measured cleanly (equal-information, everything fits: 1.8441x dearer, §3 E-13) and in the crossover sweep (negative in 5 of 6 warm cells, §3 E-14).

**Division of labour (the operator's line, recorded in `handoff from consonance/README.md`).** Inference-side and eval-side experiments belong to this workspace; the harness-side build belongs to Consonance. Consonance runs **no** model hosting. This document therefore does inference and cache economics only, and treats Consonance's quality/authority numbers as inputs that must be joined through one record format.

**Hard scope limits for this work.**
- `/home/zer0null/Duval` and every target repository are read-only. No git state change, no `git add/commit/checkout/clean`.
- No live model traffic of any kind. No `curl`. No container change. The production container `gx10-occamy-nvfp4` is not touched (`DO_NOT_REDO.md` #5).
- No editing of frozen records: `CLAIMS.md`, `MANUSCRIPT.md`, `EVIDENCE.md`, `docs/STATE.md`, `docs/GRID-2-FINAL.md`, fixtures, ledgers, rows, manifests, tests.
- Nothing here authorises `BOUNDARY-PREREG`'s 696 requests, which is a separate registered candidate (§4 correction 10).

---

## 3. Evidence ledger

Class vocabulary: **measured** = a row/file/recompute supports the value as stated; **inference** = derived from measured values by a stated rule; **unverified** = no supporting row on disk, or a design not executed. "Workload" names the actual corpus/cell, because a value without its workload is the failure mode this workspace has already paid for.

| id | claim | value | class | date | workload | limitation | source (quoted) |
|---|---|---|---|---|---|---|---|
| E-01 | F1: a re-rendered compact projection cuts payload far more than the bill | payload −24.2 %, billed −2.4 %, **more expensive than the full transcript from step 3 on** | measured (Consonance, registered, CLOSE) | 2026-10-25 handoff | EXP#43 context-cost-under-cache | one experiment, one workspace; no engine fingerprint in the record | "cut **payload** tokens **24.2 %** and **billed** tokens by only **2.4 %**, and was **more expensive than the full transcript from step 3 on**" — `handoff from consonance/MEASURED_FACTS.md` (F1) |
| E-02 | F2: the mechanism — the projection's main call was cold every step | cached 0 of 134 / 426 / 499 / 569 / 663; transcript cached share 0 → .166 → .217 → .350 → .489 | measured | same | same | same | "**exactly 0 cached tokens at every step** — 0 of 134, 0 of 426, 0 of 499, 0 of 569, 0 of 663" — same file (F2) |
| E-03 | F3: a depth change moves the prefix, because the view rides inside it | 48 of 72 prefix bytes moved | measured (instrument) | same | `tools/context/compiler.ts` header; D-086 | instrument observation, not a cost | "moved **48 of 72 prefix bytes**" — same file (F3) |
| E-04 | Pointer index ratio | 30,000 B bodies / 447 B index / 12 items = **67.1141x**; compact index 78.3x at 383 B | measured (artifact bytes only) | 2026-10-25 | 12 bodies ≈ 2,500 B each | **not** a token, cost or latency saving; r is an index-encoding choice, corpus sits at its own crossover by design | "30000/447 = 67.1141 → 67.1x"; "the compact index measures r = 78.3x at 383 B (ENGINE-R1 cell D), so r is an index-encoding choice, not a constant" — `experiments/ptr-engine/RECORD.md` §1 |
| E-05 | Quality arm capability | A 3/3, B (cap-3) 0/3 with 33/33 `PTR_STORE_MISS`, C 3/3, D (no bodies) 0/3 answering the index echo | measured | registered before first request | one fixed question (`AUD-4417`), 12 items × 9,000 B, 4 turns, one model | narrow capability, not a quality curve, not generality | "A **3/3** … B **0/3** … **33** × `PTR_STORE_MISS`"; "D … **0/3 task success, 0 bodies resolved**" — `RECORD.md` §4 |
| E-06 | The quality arm's own token figures are refuted | C rep2 stored 32,401 vs claimed 34,201; residual **+17,193**; T1+T2+T3 completions **6** tokens; "0 avalanches" false (rep records residue 1) | measured (refutation, offline re-derivation) | 2026-10-25 | `quality/rows.jsonl` | no token figure from that arm may be quoted as cost | "the stored value is **32,401** and the residual is **+17,193**"; "those completions total **6** tokens against an 17,193-token gap" — `RECORD.md` §4 |
| E-07 | gen-6 H1 (tail latency) | **`not_adjudicable_floor`**; binding arm pointer-stable p50 156.151 ms [146.306, 291.926], n=48, lag-1 r=+0.2949 ⇒ **n_eff 26.14 < 60**; p95 **refused at n=48** | measured statistic, non-adjudicable verdict | 2026-10-28 | 16-cell grid, occamy/SGLang, 48-turn workload | instrument failure, not a design result | "**H1 verdict: `not_adjudicable_floor`** (binding arm `pointer-stable`, n_eff 26.14 < 60)" — `docs/GRID-2-FINAL.md` §1 |
| E-08 | gen-6 census and price | 6 of 16 usable; 1,270 request rows = the ledger delta exactly; **79.375/cell**; highest cell 96; 16 cells at observed max = 1,536 < 1,729 remaining | measured | 2026-10-28 | same grid | does not price a gen-7 cell whose treatment fires | "Request rows sum to **1270** across the 16 cells, which is the ledger delta exactly" — `docs/GRID-2-FINAL.md` §0 |
| E-09 | Replicate collapse | 288 turn rows → 96 analysed, `dropped_duplicate=192`, because `run_grid_report.py:235` dedupes on `(arm, rep, turn_index)` and every gen-6 cell wrote `rep=1` | measured (instrument defect) | 2026-10-28 | same grid | this is why p95 is refused at n=48 while 192 rows exist | "**288 turn rows → 96 analysed** (`dropped_duplicate=192`)" — `docs/GRID-2-FINAL.md` §1 |
| E-10 | gen-6 H3 and TVS | H3 fields are the literal placeholder strings `x/12`, `x/9`, `answered_ratio`; TVS `UNDEFINED`, `n_verified_success = 0` arm-level and 0 at first checkpoint | measured (that the fields are placeholders) | 2026-10-28 | same grid | denominator undefined; no token count substituted | "No token count is substituted. `n_verified_success` is **0** at arm level and **0** at first-declared-checkpoint level" — `docs/GRID-2-FINAL.md` §4 |
| E-11 | C54 resident capacity | 30–31 docs = 258,035–266,636 tokens = **0.1592–0.1645** of 1,620,892 declared capacity, at **1.501724x** pressure (2,434,133 tokens, 283 docs); binding constraint the state cache (`max_mamba_cache_size` 64) | measured | 2026-10-2x | M4 cell, server-wide working set | **server-wide**, not a per-conversation allowance, not a guaranteed pin, not a universal 260k budget | "`resident_capacity_ratio_of_capacity` W in [30,31] … at 1.501724x pressure … binding constraint state cache (max_mamba_cache_size 64), not KV token capacity" — `papers/context-cache/CLAIMS.md` C54 |
| E-12 | C53 / "G5" fan-out ratio | mean of **8 per-fan-out** B/A ratios = **6.744331504**, stdev 3.227761582, t95 **[4.04542649, 9.44323652]**; ratio of aggregated totals **6.063360882**; A 123,240/102,912/20,328; B 123,256/0/123,256; C 19,792 uncached | measured + recomputed here | 2026-10-2x | G5 cell, 8 fan-outs × 8 branches, single seed | mean-of-ratios ≠ ratio-of-totals; fan-out 5 (14.702) drives the mean; one cell | "B/A = 6.744331504 [4.04542649, 9.44323652]" — `CLAIMS.md` C53; recompute `PASS 18/18` |
| E-13 | Equal-information baseline | plain transcript **1,911.2** uncached/turn vs pointer protocol **3,524.0** = **1.8441x** (the source's rounded figure; exact 3,524.0/1,911.2 = 1.843868); accuracy **3/3 in all three arms** | measured rows, **retrospective** (no `run.json` frozen first) | 2026-10-26 | occamy-1.0-NVFP4, SGLang `:8012`, all 12 bodies in every prompt, nothing truncated | one task, one model; per the contract these runs are `retrospective:true` | "**1.8441x dearer per turn** (3,524.0/1,911.2) … with **accuracy 3/3 in all three arms**" — `papers/context-cache/CONSONANCE-INTEGRATION.md` §A |
| E-14 | Crossover sweep | **NEGATIVE** in the 3k–30k character range on a warm prefix; occamy warm 30k: C0 **7** uncached of 6,471 vs L1 **1,412**; same cell saving_prompt **+26.5 %** vs saving_billed **−7,157.1 %** | measured | 2026-10-2x | 24 runs, 65 rows, **1 rep/cell**, 12 grid cells | no error bars; qwen is cache-blind so its "win" is an instrument artefact | "lazy loading trades a smaller prompt for a larger bill, and growth makes it worse" — `experiments/agentic-lazy/crossover/RESULTS.md` §6 |
| E-15 | Claim health audit | 20 suspect-cell claims: **SAFE 7 / REMEASURED 0 / BLOCKED 13** | measured (offline audit; classes taken from `CACHED-AUDIT2.json`) | 2026-10-2x | six cells, per-arm fire counts | audit log predates one repair; no number edited | "**Verdict: 20 claims reviewed — SAFE 7 / REMEASURED 0 / BLOCKED 13.**" — `papers/context-cache/CLAIM-HEALTH.md` |
| E-16 | Claim sensitivity | 13 BLOCKED claims re-measured offline: **SURVIVES 1 / MOVES 12**; all 12 moves are one direction (flagged credit over-states cached); C23 −20.80 %, C17 −12.57 %, C51 3.074 → 3.018 | measured (offline recompute) | 2026-10-2x | same six cells | repair is an estimator, not a fresh measurement | "**Verdict: 13 claims re-measured three ways offline — SURVIVES 1 / MOVES 12 / UNDECIDABLE 0.**" — `papers/context-cache/CLAIM-SENSITIVITY.md` |
| E-17 | Quality path cannot say yes | `pos-full` (correct answers, fixture's own `ANSWER:` contract) → `verified_success false`, 0/3, 7 failed checks; only a bare-value diagnostic passes (TVS 22,396); the two graders are mutually exclusive | measured (offline replay, 0 requests) | 2026-10-2x | `LR-01.v3.json` + 48-turn pointer-stable rows | the fix is a fixture/grader owner decision, not a patch | "The instrument cannot return yes on a log that follows the fixture's own answer contract" — `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md` |
| E-18 | E1/E2 budgets | E1 ≤ **60** calls, E2 ≤ **120** calls, hard stop after E2 at **180**; full programme 440 (60+120+40+80+60+80) | unverified as executed (**0 calls sent**) | 2026-10-25 (declared) | pre-registration skeletons | budgets are declared, not spent | "**Budget.** ≤ 60 calls" / "**Budget.** ≤ 120 calls" — `handoff from consonance/EXPERIMENTS.md` |
| E-19 | `BOUNDARY-PREREG` | **696** scheduled requests (216 + 300 + 180), ceiling 810, registered 2026-10-26T01:22-0500, **design only** | unverified as executed (registered, never run) | 2026-10-26 | 4 arms × ladder × 3 reps, two endpoints | separate candidate; not E1/E2; must not be pooled | "**Total 696 scheduled requests** — stage 1 = 216 …, stage 2 = 300 …, stage 3 = 180 — ceiling **810**" — `experiments/ptr-engine/BOUNDARY-PREREG.md` §6 |
| E-20 | Append-cost law | SGLang `uncached = (P1 mod 64) + L`, residual **0 in 186/186** rows; vLLM `(P1 mod 1056) + 1056 + L`; `L = n_payload + 12` in **387/387** | measured (fit) | 2026-10-25 | primed-then-append series, two servers | a law about **one append onto a primed prefix**; multi-append extrapolated | "residual 0 in **186/186** rows" — `RECORD.md` §2 |
| E-21 | SGLang residue-0 reuse, and the null rule | cell A `:8012`: prime 384 → append **397** → `cached 320` in **3/3** reps; reuse `64·floor((P1−1)/64)`; SGLang "omits `cached_tokens` when it is 0; null therefore means 0" | measured | 2026-10-26 | `measure/rows-live-2026-10-26.jsonl` cell A | **one endpoint**; the rule does not transfer to vLLM | "SGLang **\"returns prompt_tokens_details but OMITS cached_tokens when it is 0; null therefore means 0\"**" — `RECORD.md` (endpoint-null layer), from `LIVE-CELLS-2.json` |
| E-22 | vLLM cache telemetry | `prompt_tokens_details` null on **0 of 52** rows reporting a cached count → reuse **unknown**, not 0 | measured | 2026-10-26 | `:8014`, qwen3.5-9b | retirement from cache/cost claims; capability only | "on the axis every cache claim depends on, one engine is an instrument and the other is a mute" — `CONSONANCE-INTEGRATION.md` §D |
| E-23 | Fixture inventory | 6 fixtures (`repo-fix`, `multi-file-refactor`, `bug-fix-with-test`, `constraint-survival`, `adversarial-debug`, `doc-sync`), 40–72 turns, **3 checkpoints each**, 3 negative constraints each, 3–4 sources; **0 checkpoints require ≥2 distinct sources**; sources carry `revision`/`sha256`/`pointer` but **no live/stale/revoked status field** | measured (read from the files) | 2026-10-25/26 | `experiments/ptr-engine/longrun/fixtures/LR-01..06.json` | multi-hop retrieval and stale/revoked-source handling are **missing classes**, not passing classes | measured here: `cp_src_multi 0` for all six; `sources[]` keys `id, revision, sha256, pointer, path` |
| E-24 | Checkpoint statistical floor | a 3-checkpoint fixture cannot rank two arms at any number of repeats: exact McNemar minimum two-sided p at `b+c=3` is **0.25**; 12 checkpoints cost +108 requests (v5 36 → v6 144) | measured (exact computation) | 2026-10-26 | v5/v6 fixture comparison | a 12-checkpoint fixture is required for a ranking, not a preference | "At `b+c = 3` the exact McNemar minimum two-sided p is **0.25**" — `docs/CHECKPOINT-COVERAGE.md` |
| E-25 | Padding is measured and loses | same 71-turn SGLang schedule, one request per measured turn: P0 541.07 [501.68, 581.51]; P1 528.64 [521.19, 536.13]; P1+pad P2 549.49 [542.17, 556.80]; **P2−P1 +20.8429 [10.014, 31.586]**, 70 pairs, excludes 0 | measured | 2026-10-2x | production SGLang O1 cell, 71 turns | one substrate, one schedule | "Net, P2 costs **+20.84 uncached tokens per turn** over P1, [+10.01, +31.59]" — `papers/context-cache/MANUSCRIPT.md` §8a (C64) |
| E-26 | Compaction-break cost (workspace mechanism-batch `E1` `fork-break-cost`) | fork vs summarise-in-place median **5,132.75** vs **442.25** uncached; paired median **+4,774.25** (range −2,035..+5,611.5), bootstrap CI **[193.5, 4,868.25]**, **15/18** positive, sign p **0.0075**; excluding the event-index-2 stratum n=15 median +4,839.5, CI [4,677.5, 4,901.5], 15/15, p 6.1e-05 | measured, unit `partial` (VE13 partial) | 2026-10-21/22 | 195 requests / 228 rows / 3 sessions × 38 turns, events [12,17,22,27,32,37]; 36 event rows / 18 pairs | one rig, three sessions, six event indices; **not** the handoff's E2 arms; 7 non-event fork rows retain `cached=64` | "median **5132.75** vs **442.25** uncached; paired median **+4774.25** … 95 % CI **[193.5, 4868.25]** … **15/18** positive, sign p **0.0075**" — `orchestration/STATUS.md` §7.1 |

**What is *not* in this ledger, deliberately.** No p95 from a sample below the frozen floor; no token saving inferred from prompt length; no unregistered reconnaissance promoted; no hosted-provider cache number mixed with an engine KV number; no quality-arm token figure as a cost. Each omission is a trap already paid for (`handoff from consonance/DO_NOT_REDO.md`).

---

## 4. Corrections to earlier claims

Each item quotes the earlier claim, states what the evidence supports, what it does not, and the consequence for the design. These are mandatory and are not softened by anything later in the document.

### 4.1 The `67.1x` is a byte ratio, not a saving

**Earlier claim:** "Measured saving at that corpus: 30000 B of body behind a 447 B index, r = 67.1x, and 78.3x with the compact index." (`experiments/ptr-engine/ADOPTION.md`)

**Supported:** 30,000 body bytes / 447 index bytes / 12 items = 67.1141, and the compact index reaches 78.3x at 383 B. Both are arithmetic over artifacts on disk (`RECORD.md` §1).
**Not supported:** any token, cost, latency or quality saving. The same record says so: "r = 67.1x is a property of 12 bodies of ~2500 B behind a 447 B index; the corpus sits *at* the measured crossover on purpose" and "r is an index-encoding choice, not a constant".
**Consequence for BRCV:** the pointer table's *serialised size* is a design parameter to be optimised (383 B beats 447 B), not a benefit to be claimed. Every benefit claim must be stated in uncached prefill work, cache reads, or time-to-verified-success — never in ratio-of-bytes.

### 4.2 The quality arm's `3/3` is narrow capability, and its token figures are refuted

**Earlier claims:** "A **3/3**" as evidence the pointer design works; and `RESULTS.md`'s "`sum(prompt_tokens) + 12(R−1)` holds exactly … C rep2 raw 34,201", "the difference is the completion of T1+T2+T3", "0 avalanches".

**Supported:** one fixed question (`AUD-4417`) over 12 items × 9,000 B, 4 turns, one model: a model *can* finish a lookup through a 12-line index and one `fetch`, reaching a body it never saw; a retention cap that deletes the bytes yields a **named** refusal (33/33 `PTR_STORE_MISS`) and a correct abstention; and the no-body arm D scores 0/3 while echoing an index digest, so the index carries structure and not the fact.
**Not supported:** generality past 12 items / 4 turns / one model; any quality *curve*; and **no token figure at all** — the stored value is 32,401 not 34,201, the residual is +17,193, the cited completions total 6 tokens, "0 avalanches" is contradicted by the cell's own `per_turn` (residue 1, `avalanche True`, uncached 34,190), and `usage.prompt_tokens_details.cached_tokens` never reaches `rows.jsonl` (`RECORD.md` §4).
**Consequence for BRCV:** the capability result licenses *testing* pointer/fetch (it is not obviously unworkable); it licenses no economics. The 33/33 refusal is the more important half — it is an existence proof that a missing body can produce abstention rather than fabrication, which is exactly the behaviour BRCV's refusal semantics depends on.

### 4.3 gen-6 is `not_adjudicable` and is not evidence either way

**Earlier claim:** "this cycle's binding constraint is the request budget, not the instrument" (declined in `docs/GRID-2-FINAL.md` §6); and more generally any reading of the 16-cell grid as a comparison.

**Supported:** H1 `not_adjudicable_floor` (n_eff 26.14 < 60; p95 refused at n=48); H2 `not_adjudicable` (the frozen rule is C-vs-A and `transcript-grow` has **0** usable cells — the two usable arms only support a within-arm fact, cached ≥ uncached); H3 `not_adjudicable` (placeholder zeros, no admissible emitter); TVS `UNDEFINED` (0 verified successes). Overall `not_adjudicable`.
**Not supported:** any claim that BRCV wins or loses. The grid also does not show the budget binding: 1,270 requests = 79.375/cell, and 16 cells at the highest observed bill cost 1,536 < 1,729 remaining.
**Consequence for BRCV:** gen-6 must not be cited as evidence for or against the design. Its only transferable content is the instrument lesson: **treatments must be shown to fire inside the horizon, and replicate identity must be part of the dedupe key**, before any cell is bought.

### 4.4 C54 is a server-wide resident working set under pressure

**Earlier claim:** quoted as a per-conversation context allowance, a guaranteed pin, or a universal ~260k-token budget.

**Supported:** at 1.501724x pressure (2,434,133 tokens across 283 docs), the resident capacity is 30–31 documents = 258,035–266,636 tokens = **0.1592–0.1645** of 1,620,892 declared capacity, and the binding constraint is the state cache (`max_mamba_cache_size` 64), not KV token capacity; the verdict is `consistent_with_lru`.
**Not supported:** any per-conversation allowance, any guarantee that a conversation's documents stay resident, and any universal token ceiling. The 188.45 token-pool LRU figure is excluded from the claim.
**Consequence for BRCV:** the design may treat residency as a **contended shared resource with an eviction model**, and must carry an internal reformulation path (fetch again, or abstain) for a body that was resident and is not. It must not size a hot window from C54.

### 4.5 A body-store retention pool is not the KV/state cache

**Earlier claim (implicit):** the pointer engine's warmpool/`BodyStore` cap models cache eviction, so a capped arm's behaviour predicts server behaviour.

**Supported:** a retention cap produces `PTR_STORE_MISS` (33/33), a **storage** event with a named code.
**Not supported:** any statement about KV/state eviction. Different mechanism, different failure mode, different cost. `DO_NOT_REDO.md` #7 is explicit that KV state does not transfer across models, quantizations, engines or adapters.
**Consequence for BRCV:** retention policy (what the store keeps) and cache policy (what the engine keeps) are two separate knobs with two separate instruments, and the protocol must report them in separate columns.

### 4.6 Missing cache telemetry is unknown unless endpoint semantics are established

**Earlier claim:** `cached_tokens: null` read as 0.

**Supported:** one endpoint-specific exception — SGLang `:8012` omits `cached_tokens` when the value is 0, proven by cell A (`P1 397` → `cached 320`, 3/3 reps, `cached_reported: true`). On vLLM `:8014`, 0 of 52 rows report a cached count, so its null is **unknown**.
**Not supported:** a universal null→0 mapping. The contract is unambiguous: `cached_tokens` is "**not reported** (unknown) — **never 0**" (`handoff from consonance/INTERFACE_CONTRACT.md` §2).
**Consequence for BRCV:** the record format must carry the null as null plus a `cached_source` note, and any arm on a non-reporting engine may carry quality, gross tokens and latency but **no hit-rate or cache-cost claim**.

### 4.7 An append-only transcript still grows; no universal padding/pinning/no-compaction rule

**Earlier claim:** a shorter prompt is a cheaper prompt; and the derived prescriptions that follow (pad to a safe residue, pin documents, never compact).

**Supported:** cache hits reduce **prefill work**, not token count. The logical input still grows. F1: payload −24.2 % and billed −2.4 %, more expensive from step 3. C0-EQUALINFO: 1,911.2 vs 3,524.0 uncached/turn (1.8441x). Crossover: warm 30k occamy C0 at 7 uncached of 6,471 against L1's 1,412.
**Supported, and newly measured — padding loses:** on the production SGLang O1 cell, same 71-turn schedule, one request per measured turn, P2 = P1 + grid pad costs **+20.84 uncached tokens/turn** over P1 ([+10.01, +31.59], 70 pairs, excludes zero) while recovering only 78.0 % of a mean 94.89-token pad (§3 E-25). A universal padding rule is contradicted by a measured cell, not merely unsupported.
**Not supported:** any of the three derived rules. Pinning is a C54-scope statement (server-wide, contended); "never compact" is contradicted by the premise test being run at all (E2 exists precisely to price a checkpoint); padding is contradicted by C64.
**Consequence for BRCV:** the checkpoint is **conditional and forecast-priced**, and the padding knob is off unless a specific engine/model/offset measurement says otherwise.

### 4.8 Residue behaviour is engine-specific

**Earlier claim:** one avalanche model ("the whole prefix re-bills") applied to every engine.

**Supported:** SGLang (B=64) at residue 0 re-bills **one block** — reuse is `64·floor((P1−1)/64)`; the 397→320 cell settles it in 3/3. vLLM (B=1056) at residue {0,1} re-bills the **whole prefix** with an **8.5x** TTFT jump and recovers at residue 2. The avalanche-magnitude record has an open contradiction (C1/C2), and the padding study is an uncalibrated offline model (C5).
**Not supported:** any universal padding rule, or any statement that residues behave the same across engines or builds.
**Consequence for BRCV:** the view's own renderer must not chase a residue. If residue handling matters for a given engine, it is a measured per-engine parameter of the *checkpoint scheduler*, not a property of the design.

### 4.9 The `6.744` is a mean of eight per-fan-out ratios

**Earlier claim:** 123,256 / 20,328 = 6.744.

**Supported:** C53's headline is the **unweighted mean of the eight per-fan-out B/A ratios** — 5.379888, 5.667647, 6.034483, 5.389356, 14.70229, 6.015625, 5.385475, 5.379888 — mean **6.744331504**, stdev 3.227761582, t-based 95 % CI **[4.04542649, 9.44323652]**, n=8 fan-outs, single seed, one cell. Fan-out 5 (14.702) drives the mean.
**Not supported:** the ratio of aggregated totals, which is **6.063360882**.
**Verified for this document:** `papers/context-cache/recompute.py C53` → `PASS 18/18 values match`; independent recompute from `cells/G5/rows.jsonl` (192 rows, sha256 `8fd7f9d2…`) reproduces all eight ratios, the mean, and the stdev.
**Consequence for BRCV:** quote the estimator and its uncertainty, never a bare ratio of totals, and never as a property of the pointer design — G5 measures a *race-free fan-out layout*, which is one configuration among many.

### 4.10 The 696-call preregistration is a separate candidate, and "E1"/"E2" are overloaded

**Earlier claim (implicit):** `BOUNDARY-PREREG` is the E1/E2 run, or is approved by being registered.

**Supported:** `experiments/ptr-engine/BOUNDARY-PREREG.md` is registered 2026-10-26T01:22-0500 **before any request**, is **design only**, schedules **696** requests (216/300/180) with ceiling 810, and has three refusal points. Registration is not approval and not execution.
**Also supported, and a naming hazard:** the workspace mechanism batch `orchestration/STATUS.md` §7.1 uses `E1` for `fork-break-cost` (195 requests) and `E2` for `cache-forensics` (89 requests), plus `E3` append-deviation, `E4` boundary, `E4R` rep3-probe, `LIVE-MEAS`. **These are not the handoff's E1/E2.**
**Consequence for BRCV:** this document and the sibling protocol use `E1-CACHE-BOUNDARY-SWEEP` and `E2-CHECKPOINT-COST`, state the collision where the short names appear, never pool `BOUNDARY-PREREG` with either, and never cite the workspace `E1` fork-break-cost as if it were the handoff's E1 — it is *prior evidence about checkpoint cost* (§3 E-26), not that experiment.

---

## 5. Proposed system — the bounded recoverable context view (BRCV)

BRCV is a **proposed** arrangement of prompt and storage. Its components are each individually supported somewhere in the record (stable prefix: F2/F3; pointer index: E-04/E-05; refusal on missing body: E-05; conditional checkpoint: E-18's premise test), and the **composition is not measured**. The falsifier is in §8.

### 5.1 Components

1. **Stable prefix.** System instructions, tool schemas and the immutable task contract, byte-identical across turns, changing only at declared epoch boundaries. Rendered by a deterministic renderer with a content fingerprint. (F2/F3 are the reason: "payload size is not the lever; prefix stability is".)
2. **Bounded recent working set.** The last *N* turns verbatim, where *N* or its token budget is a **measured parameter of the workload**, plus task constraints and decisions pinned **by id**, not by prose summary. There is no universal hot-window size in this design; C54 supplies no basis for deriving one, and no cell in the record measures one.
3. **External authoritative record.** Append-only, content-addressed store of observations and artifacts; each entry carries `id`, `sha256`, `revision`, provenance, access scope, timestamps, status (`live`/`stale`/`revoked`) and a token count. Immutable and versioned.
4. **Pointers.** Deterministic compact references (`id` + revision + hash + length/range), access-checked, stable across turns, **no body bytes in the prompt**.
5. **On-demand retrieval.** `fetch(ref, range?)` returns a targeted source range; the host — not the model — validates access, revision and range. Outcomes are explicit: `OK`, `NOT_FOUND`, `REVISION_MISMATCH`, `SCOPE_UNGRANTED`, `STALE_OR_REVOKED`, `BUDGET_EXCEEDED`. Content is never fabricated. Retrieval appends into the **suffix** wherever possible rather than rewriting the prefix.
6. **Masking before summarisation.** An old tool output is replaced by its pointer/marker entry (masked) *before* any lossy summary is attempted. A summary happens only when a checkpoint is forecast to pay for its own cache break and rebuild.
7. **Checkpoint.** Explicit, versioned snapshot/digest, created only when the forecast net saving exceeds the measured cache-break + rebuild + retrieval cost; the checkpoint event is recorded; branches are immutable. No universal "never compact" rule.
8. **Provenance and abstention.** Every assertion carries a source ref + revision. Unavailable or unauthorised evidence yields an explicit refusal or abstention — not a fabricated answer, and not a success.
9. **Mapping to the existing contract** (see 5.3): view identity maps to `manifest_id`/`branch_id`/`parent_branch_id`/`state_epoch`; expansions = fetches; omissions = masked entries; unknowns = unavailable/unauthorised; watermarks = source revisions.
10. **Scaling stated separately** (§6): prompt tokens, external storage, index/retrieval work and rebuild cost scale differently and must be measured separately.

### 5.2 Turn lifecycle

```
render(stable_prefix)            # byte-identical; fingerprint recorded
  + hot_window(turns N-k..N-1)   # verbatim, budget = measured parameter
  + pointer_table(pinned ids)    # no body bytes
  -> request 1
        if the model needs a body: fetch(ref, range?)  # appends to the SUFFIX
        -> request 2 (…)         # only if budget allows; each is a cache event
  -> mask(tool outputs older than the window)   # pointer/marker replaces bytes
  -> checkpoint?  ONLY IF forecast_net_saving > 0
        forecast = (payoff_per_turn x expected_remaining_turns)
                 - (cache_break_cost + rebuild_cost + retrieval_cost)
        if <= 0: do not checkpoint; append instead
  -> record: prompt_tokens, cached_tokens (or null + semantics note),
             uncached (derived, formula named), ttft, completion_tokens,
             verified_success, exit_cause, expansions[], omissions[], unknowns[]
```

Two properties the lifecycle must keep, both from the record rather than from taste. **(a)** Retrieval goes to the suffix, because F2 shows a mid-prefix rewrite is served cold while an append is served warm, and the crossover run shows each fetched body re-billed in full until it lands in the cache. **(b)** The checkpoint is a *forecast*, because E2 exists precisely because nobody has priced one on the handoff's arms, and the adjacent workspace measurement (§3 E-26) says the compaction break is large and one-sided (median +4,774 uncached, 15/18 positive).

### 5.3 Mapping to the contract fields (no new wire API)

Field names come only from `handoff from consonance/INTERFACE_CONTRACT.md` §2–§4. **No `consonance.fetch/1` schema is defined here, and none exists in the record.** `schema/context-manifest.v0.json` and `schema/fixture.v0.json` are **pending** from Consonance — the contract says so: "When our manifest and replay fixture land, this directory gains `schema/context-manifest.v0.json` and `schema/fixture.v0.json`". Until then, "the field names above are the contract, and `prompt_tokens` from your renderer is the joining key."

| BRCV component | `consonance.call/1` field(s) | `consonance.fixture/1` field(s) | status of the mapping |
|---|---|---|---|
| view identity (ordered modules, epoch, policy hash, renderer fingerprint, lease id) | `manifest_id`, `branch_id`, `parent_branch_id`, `state_epoch` | — | contract field names exist; the **manifest schema is pending** |
| stable prefix | `renderer_fingerprint`, `prompt_tokens` (prefix share is `derived`, key names the formula) | `sources[]` for the contract text | prefix share has **no field**; must be derived and labelled |
| hot window (turns, token budget) | `prompt_tokens`; the budget itself has **no field** | `observations[].tokens` for the per-step sizes | budget must be recorded in `run.json` `notes` until the manifest lands — **unverified** |
| pointer table | no field | `sources[].id / revision / sha256 / pointer` | pointers are carried by the fixture's `sources[]` |
| fetch / expansions | no field | `sources[].pointer` is the target | count and token cost must be reported in the verdict page (§5 of the contract) |
| masking (omissions) | no field | `observations[]` (step, kind, sha256, tokens) | masked entries = the omissions set; schema pending |
| unknowns / abstention | `verified_success`, `exit_cause` | `acceptance.checks`, `expected.forbidden_claims` | present today |
| checkpoint event | `state_epoch` increments; `parent_branch_id` links | — | present today |
| cache quantities | `prompt_tokens` (required), `cached_tokens` (absent = unknown), `uncached_prefill_tokens` (measured only if the engine exposes it, else `derived` with the formula named) | — | present today; **the null rule is per-engine** (E-21/E-22) |
| quality | `verified_success`, `exit_cause` | `expected.verified_success`, `acceptance.negative_constraints` | present today; **the emitter is broken** (E-17) until the fixture/grader owner decides |

**What this document does not invent.** No `ContextManifest` schema, no `consonance.fetch/1` request/response shape, no Rust kernel API, no omp interface, no ownership assignment beyond what the handoff documents state. The Rust kernel and the stripped-down omp integration are **user-supplied direction, not verified implementations**; nothing here asserts they exist, expose a tool surface, or accept this contract.

### 5.4 Refusal and abstention semantics

The design's quality claim is not "more answers"; it is "no fabricated answer". Six outcomes, each with a distinct record field so a run cannot confuse them:

- **`NOT_FOUND`** — the reference is not in the store (never a wrong body).
- **`REVISION_MISMATCH`** — the bytes survive but not at the pinned revision (`PTR_REVISION_MISMATCH` already behaves this way in the engine).
- **`SCOPE_UNGRANTED`** — access denied (`PTR_SCOPE_UNGRANTED` exists).
- **`STALE_OR_REVOKED`** — the source's status field says so; requires a status field the current fixtures **do not have** (E-23), i.e. a missing capability, not a passing one.
- **`BUDGET_EXCEEDED`** — the per-turn resolve budget, which must be reported as its own number.
- **Abstention** — the model states it cannot verify, which requires the quality path to be able to record "correct abstention" as a success. Today it cannot (E-17), and H3's field is a placeholder.

---

## 6. Scaling — four quantities, four bounds

A fixed prompt cannot encode arbitrarily or exponentially growing information. External storage extends **accessible** history; it does not extend prompt capacity. Retrieval success is a measured probability, not a guarantee.

| quantity | growth with history length *H* | bound | what must be measured |
|---|---|---|---|
| logical prompt tokens | `O(1)` in *H* **given a fixed window** — with a non-zero constant: prefix + hot window + pointer table + this turn's retrieval results | fixed window ⇒ bounded, but **not zero**; the pointer table itself grows with the number of pinned ids | prefix tokens; hot-window tokens; pointer-table tokens at 12/40/120 items (the prereg's ladder is 22.6k/75.3k/226.0k tokens at 9,000 B/item); retrieval-result tokens per turn |
| external storage | linear in total observations (append-only) | unbounded by design | bytes and entries; index bytes (447 B for 12 items is **one** measurement, not a constant) |
| index/retrieval work | ≥1 fetch per resolved body; request count `1 + fetches` | bounded only by the per-turn resolve budget | fetch count, fetched bytes, and the request multiplier — the crossover run measured 3 requests for 2-of-12 and 7–8 for 6-of-30, and that multiplier is what inverted the bill |
| rebuild cost | per checkpoint event | one break per checkpoint; the break is not amortised by shortening the prompt | uncached tokens paid at the event; steps to repayment, measured as uncached work (§3 E-26 measures +4,774 median for a fork-vs-in-place compaction; E2 is the experiment that prices *this* rig's checkpoint) |

**Two consequences that the report binds itself to.**
1. **Bounded prompt ≠ bounded cost.** The bill is `prompt × (1 − hit)` plus fetch turns; a small prompt that never caches is dearer than a large one that does. Measured twice: F1 (payload −24.2 %, billed −2.4 %) and the crossover run (prompt +26.5 %, bill −7,157.1 % in the same cell).
2. **Accessible history is not resident history.** C54's 30–31 documents are a server-wide working set under 1.5x pressure, and the binding constraint is the state cache. Anything that assumes a fetched body stays resident must re-fetch and re-bill, and the design must be able to say so.

---

## 7. Existing integration and ownership

**What exists, and where.** `handoff from consonance/` (staged **2026-10-25**, **not executed**; source workspace `30b03b80`, repo `/home/zer0null/Duval`, strand `land/rsi-round-1` @ `4a731e4`) carries: the four-fingerprint comparability rule, the `consonance.call/1` per-call record, the `consonance.run/1` frozen envelope (with the `retrospective:true` rule), the `consonance.fixture/1` task-replay format, ten traps, and six pre-registration skeletons. On this side: `experiments/ptr-engine/longrun/run_longrun.py` (one invocation = one task × arm × rep cell; arms `transcript-grow`, `transcript-compact`, `pointer-stable`, `lease-reopen`), `score_longrun.py` (four check kinds; fixture hash tamper exit 2; absence of evidence is failure), and the six `fixtures/LR-0*.json` plus the `tasks-v2/v3/v4/v6` generations.

**What has NOT landed — stated as absence, not as a plan.**
- **manifest schema** `schema/context-manifest.v0.json` — pending from Consonance (the phrase "when our M1 lane lands" is at `handoff from consonance/README.md:27`, not in the contract; `INTERFACE_CONTRACT.md` §6 says it will ship "when our manifest and replay fixture land").
- **fixture schema** `schema/fixture.v0.json` and two byte-identical golden fixtures — pending.
- **Rust kernel** — user-supplied direction; no API, no artifact, no test in this workspace.
- **stripped-down omp integration** — user-supplied direction; not implemented and not asserted.
- **quality emitter** — the path cannot return yes on a conforming log (E-17); a live run through it produces a false negative, so no spend can produce a pass. **This blocks every quality arm**, including E2's `verified_success` limb, until the fixture/grader owner decides.
- **fixture classes** — multi-hop retrieval (0 of 6 fixtures have a checkpoint requiring ≥2 sources) and stale/revoked sources (no status field) are missing classes; they must be recorded missing, not scored as successes.
- **fingerprints in rows** — the four comparability fingerprints are absent from this project's row files (gap B2 in `CONSONANCE-INTEGRATION.md`); only `model` and `token_source` exist.

**Ownership split, as the documents draw it.** Consonance owns **harness, quality and authority** — the manifest, the replay fixtures, the verifier, and whether a task completed and was auditable. This workspace owns **inference and cache economics** — what the serving engine actually charged, on which engine, at which build, with which controls. No individual is named here because no document names one; the units are `Duval/Consonance` and this research workspace.

**The joining key is `prompt_tokens`** from this side's renderer. Every other comparison depends on it, which is why a renderer fingerprint is a comparability condition and not a nicety.

---

## 8. Risks, no-go, and the exact next decision

### 8.1 No-go conditions (any one closes the build question)

1. **E1's falsifier fires** — reuse does not fall monotonically as the first rewritten offset moves earlier (e.g. block alignment only, or all-or-nothing at every offset). Then "rewrite depth" is not a predictor, a checkpoint cannot be priced per-token from depth, and the design's checkpoint trigger has no model.
2. **E2's falsifier fires in an adjudicable E2 run** (never in the ≤120-call, 123-request descriptive probe) — the checkpoint does not repay its rebuild within 20 steps, **or** repays only by shortening the prompt (the gain vanishes when measured as uncached work rather than payload). Then bounded working memory is not an economic win at these task lengths.
3. **The quality emitter cannot say yes** on a log that satisfies the fixture's own answer contract (E-17 stands). Then `verified_success` is undefined, TVS is undefined, and no quality claim of any kind can be made — a capability arm would be measuring the grader.
4. **The four fingerprints cannot be frozen** (model, tokenizer, renderer, engine image + flags). Then arms are different experiments and no comparison is valid, whatever the numbers.
5. **The request ledger cannot be reconciled** before the run (baseline, spend, remaining). Then the run does not start; this workspace's standing rule is that an unreconciled ledger is *unknown*, not a budget.
6. **A required fixture class is missing.** Multi-hop retrieval and unavailable/stale/revoked sources are currently missing (E-23). A protocol that scores them as passing would be fabricating a result; the honest move is to record the class missing and run what exists.

### 8.2 What would change the recommendation

- A gen-7 instrument in which the treatments actually fire **and** replicate identity is in the dedupe key, producing ≥6 usable cells per arm and a decidable H1/H2/H3 **and** a defined TVS. That would convert the design question from "unmeasured" to "measurable", and E2's answer would then decide the economics.
- Any measurement where the pointer/fetch arm is cheaper **in uncached work** than a warm transcript at equal verified success, in a regime where the working set exceeds the window. Nothing in the record shows this yet; the closest positive is a block-granularity artefact at 3k warm (+80.8 %) that reverses at 30k.
- Evidence that the checkpoint break is small on this rig when the checkpoint *replaces* an append rather than duplicating one. §3 E-26 measures a large one-sided break for fork-vs-in-place; E2 is the experiment that says whether that transfers.

### 8.3 The exact next decision

| step | experiment | calls | what it decides | falsifier | controls that must be able to fire |
|---|---|---:|---|---|---|
| 1 | **`E1-CACHE-BOUNDARY-SWEEP`** | ≤ **60** | whether `rewrite_depth` is a usable predictor; per-token vs per-boundary checkpoint pricing | reuse not monotone in rewrite offset, or all-or-nothing | identical → hit ≥ 0.9 P; never-sent → 0; append → ≥ P − k; deliberately mismatched tokenizer → no reuse |
| 2 | **`E2-CHECKPOINT-COST`** | ≤ **120** descriptive (123 actual) / 369–450 adjudicable with owner approval | at 123: a descriptive cost estimate only, no verdict; at 369–450: **the premise** — does one checkpoint repay inside 20 steps as uncached work and time-to-verified-success | no repayment in 20 steps, or repayment only via a shorter prompt — only an adjudicable run can fire it | append arm shows climbing cached share (F2's curve); a no-op checkpoint costs ≈ 0 |
| — | **hard stop** | **180 for the ≤120 probe; an adjudicable E2 supersedes it and needs its own cap** | stop and report after E2's verdict if either falsifier fired; Consonance is told before further building | — | — |

**Separations that must be stated every time these are named.** (i) The handoff's `E1-CACHE-BOUNDARY-SWEEP` / `E2-CHECKPOINT-COST` are **not** the workspace mechanism batch's `E1` `fork-break-cost` / `E2` `cache-forensics` (`orchestration/STATUS.md` §7.1). (ii) They are **not** `experiments/ptr-engine/BOUNDARY-PREREG.md`'s 696-call registered candidate, which remains unexecuted and unapproved. (iii) E3–E6 (440 − 180 = 260 further calls) are **conditional** on the premise surviving.

**Budget context, so nobody re-derives it wrongly.** 1,729 requests remain of 4,320; the gen-6 grid's marginal cost was 79.375/cell with a highest cell of 96; 16 cells at that maximum is 1,536. E1+E2 at their ceilings is 180 for the ≤120 probe; an adjudicable E2 is 369–450. The number that must be re-reconciled before any of this runs is the ledger, not the plan.

**Zero live traffic in this work.** No request was sent, no endpoint contacted, no container touched. The next unit that runs E1 must freeze `run.json` **before** its first call, or the run is `retrospective:true` and must be reported as such.

---

## 9. References

Local, with the anchor quoted in §3. Digest/row counts are given where they pin a file.

| ref | path | anchor |
|---|---|---|
| R1 | `handoff from consonance/README.md` (48 lines) | "staged 2026-10-25, not yet executed. Consonance runs **no** model hosting"; "If you can run only two things, run those two, in that order." |
| R2 | `handoff from consonance/INTERFACE_CONTRACT.md` (98 lines) | "Two arms are comparable **only if all four fingerprints are equal**"; "`cached_tokens` … **not reported** (unknown) — **never 0**" |
| R3 | `handoff from consonance/MEASURED_FACTS.md` (62 lines) | F1/F2/F3 rows; "**F2 + F3 are the load-bearing pair.** … *payload size is not the lever; prefix stability is.*" |
| R4 | `handoff from consonance/EXPERIMENTS.md` (161 lines) | E1/E2 method, falsifier, controls, budgets |
| R5 | `handoff from consonance/DO_NOT_REDO.md` (68 lines) | ten traps, #1 (no savings from prompt length) … #10 (65,536 is a byte budget) |
| R6 | `experiments/ptr-engine/RECORD.md` (169 lines) | §1 ratio and "what r is not"; §2 append law; §4 quality arm; §5 C1/C2/C3 contradictions |
| R7 | `experiments/ptr-engine/ADOPTION.md` (41 lines) | three decisions; "Do not pad the prompt to a 'safe' residue" |
| R8 | `experiments/ptr-engine/BOUNDARY-PREREG.md` | 696 scheduled / ceiling 810; registered 2026-10-26T01:22-0500 |
| R9 | `docs/GRID-2-FINAL.md` (149 lines) | census 6/16; H1 n_eff 26.14; "Request rows sum to **1270**"; §5 price arithmetic |
| R10 | `docs/STATE.md` (217 lines, 2026-10-28) | one line: gen-6 `not_adjudicable`; four instrument defects; ledger 2,591/1,729 |
| R11 | `papers/context-cache/CLAIMS.md` C53 (line 185), C54 (line 186), C64 (line 264) | quoted above |
| R12 | `papers/context-cache/CLAIM-HEALTH.md` (81 lines) | "SAFE 7 / REMEASURED 0 / BLOCKED 13" |
| R13 | `papers/context-cache/CLAIM-SENSITIVITY.md` (67 lines) | "SURVIVES 1 / MOVES 12 / UNDECIDABLE 0" |
| R14 | `papers/context-cache/CONSONANCE-INTEGRATION.md` (76 lines) | §A 1.8441x; §B gaps B1–B4; §D vLLM retirement; §E 440-call plan |
| R15 | `papers/context-cache/MANUSCRIPT.md` §8a (from line 494) | the P0/P1/P2 padding table and "+20.84 uncached tokens per turn" |
| R16 | `experiments/agentic-lazy/crossover/RESULTS.md` | "**Verdict: NEGATIVE.**"; the 12-cell table; §6 |
| R17 | `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md` | "PATH-CANNOT-SAY-YES"; the truth table |
| R18 | `experiments/ptr-engine/longrun/fixtures/LR-01..06.json` | `consonance.fixture/1`; 3 checkpoints, 3 negative constraints, 0 multi-source checkpoints |
| R19 | `docs/CHECKPOINT-COVERAGE.md` | "At `b+c = 3` the exact McNemar minimum two-sided p is **0.25**" |
| R20 | `orchestration/STATUS.md` §7.1 (line 155) | `E1` `fork-break-cost`: 195 requests, median 5,132.75 vs 442.25, paired +4,774.25, CI [193.5, 4,868.25] |

**External sources.** Not read for this document; none is cited. The plan names three (observation masking `arxiv.org/abs/2508.21433`, failure-driven compression `arxiv.org/abs/2510.00615`, long-term-memory evaluation `openreview.net/pdf?id=pZiyCaVuti`); they remain **unverified** here and must be read before any claim about the literature is made. This workspace's own standards (`docs/EXTERNAL-SERVING-PRACTICE.md`, `docs/EXTERNAL-EVAL-PRACTICE.md`) were not re-read for this unit.

**Offline verification commands run for this document (0 network calls).**

```
$ cd "/home/zer0null/research extractor"
$ .venv/bin/python papers/context-cache/recompute.py C53
  ...
  PASS  18/18 values match
# independent per-fan-out recompute from experiments/context-cache/cells/G5/rows.jsonl
# (192 raw rows, sha256 8fd7f9d2534b88d682a44709120ae98dd8f46b9b9678c9a8cae4bf42734faa05)
n_fanouts 8
ratios [5.379888, 5.667647, 6.034483, 5.389356, 14.70229, 6.015625, 5.385475, 5.379888]
mean 6.744331504   stdev 3.227761582
ratio_of_totals 6.063360882
A_tot 20328  B_tot 123256  C_tot 19792
```

A sibling deliverable, `research/next-candidates/consonance-bounded-context-evaluation.md` (unit `CONSONANCE-BC-EVAL`), owns the prospective protocol: paired arms, horizons 10/30/60, three repetitions, no-fetch and stale/revoked controls, the oracle upper-bound arm, and the worked hypothetical fixture. This report points at it rather than duplicating it.
