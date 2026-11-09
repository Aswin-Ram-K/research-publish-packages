# Consonance bounded-context evaluation — prospective protocol

**Unit:** `CONSONANCE-BC-EVAL`. **Date:** 2026-11-03.

## 0. Status

**PROSPECTIVE PROTOCOL — no experiment has run, no model call, no live request, no authorization to
spend.** Every run envelope below is a **DRAFT template**, not a frozen registration. Nothing in this
file is a result. Where a number appears it is prior evidence with its own source; where a number would
have to come from a future run it is written as a placeholder (`<…>`) or as `UNDEFINED`.

The envelopes become **frozen** only when all four hold:

1. a `consonance.run/1` file is written to its final path **before** the first call
   (`handoff from consonance/INTERFACE_CONTRACT.md` §3: "A run whose `run.json` was written after its
   first call is not a pre-registered run; mark it `"retrospective":true` and expect to be disbelieved");
2. the owner (Consonance) approves the arm set and the call cap for that arm;
3. the budget is reconciled against the live ledger at execution time (§3.6), not against this page;
4. the four fingerprints are filled in with real digests, not placeholders.

Two writers produced this batch. The sibling report is `research/next-candidates/consonance-bounded-context-report.md`;
this file owns the protocol only.

## 1. Binding rules

These are contract, not preference. An arm that violates any one of them is not an arm.

| # | Rule | Source |
|---|---|---|
| R1 | Record formats are `consonance.call/1`, `consonance.run/1`, `consonance.fixture/1`. No new wire API is invented here. | `handoff from consonance/INTERFACE_CONTRACT.md` §2–§4 |
| R2 | Two arms are comparable only if `model_fingerprint`, `tokenizer_fingerprint`, `renderer_fingerprint`, `engine_fingerprint` are all equal. A difference makes it "a different experiment, not a worse arm". | same, §1 |
| R3 | `prompt_tokens` is required on every row; it is the joining key between the two halves. | same, §2 |
| R4 | `cached_tokens` absent means **not reported / unknown**, "never 0". Derived values go under `derived` with the formula named in the key and "may never be quoted as a measurement". | same, §2 |
| R5 | The one established null→0 exception is endpoint- and field-specific: SGLang `:8012` omits `cached_tokens` when the true value is 0, so there `null` means 0 (cell A P1 397 → cached 320, 3/3 reps, `papers/context-cache/CONSONANCE-INTEGRATION.md` B1). On vLLM `:8014`, `null` stays **unknown** (0/52 rows report). This is recorded per endpoint **and per field**; it is never generalised to a schema rule. | `CONSONANCE-INTEGRATION.md` B1; `experiments/ptr-engine/RECORD.md` §C1 |
| R6 | `uncached_prefill_tokens` is filled only when the engine exposes it as a measurement; otherwise `null` and any computed value sits under `derived`. | contract §2 |
| R7 | No pooling across builds, generations, or ledger epochs. Gen-6 rows are non-poolable with anything newer (§10). | `docs/STATE.md`; `docs/GRID-2-FINAL.md` |
| R8 | Controls go **red before green**: each control must be shown able to report the opposite, and control results are reported separately from the primary result. "A control that can only report 'as expected' is not a control." | contract §5.3; `handoff from consonance/EXPERIMENTS.md` preamble |
| R9 | Serial measurement, one lock, one container ("no GPU memory beyond one container"). Heavy jobs are not run in parallel. | `EXPERIMENTS.md` E1 budget |
| R10 | No production-container change, no server restart, no model change. The measurement takes the server as it is and records the fingerprint. | `handoff from consonance/DO_NOT_REDO.md` |
| R11 | A body-store retention pool is **not** the server KV/state cache. `PTR_STORE_MISS` models a store miss, not KV eviction. | `experiments/ptr-engine/ADOPTION.md` |
| R12 | An append-only transcript still grows in logical input; cache hits reduce prefill work, not token count. | `MEASURED_FACTS.md` F1/F2 |

**Naming collision, stated once and enforced below.** `orchestration/STATUS.md` §7.1 already uses `E1`
and `E2` for *workspace mechanism-batch* units — `E1 fork-break-cost` (195 requests) and
`E2 cache-forensics` (89 requests). Those are **not** the handoff's E1/E2. This file writes
`E1-CACHE-BOUNDARY-SWEEP` and `E2-CHECKPOINT-COST` (short: `CON-E1`, `CON-E2`) and never reuses the bare
names for them.

## 2. Prior evidence to reuse, not re-buy

Every row is `measured` on the date and workload named, unless marked otherwise.

| # | Evidence (source) | What it licenses | What it does **not** license | Constrains |
|---|---|---|---|---|
| P1 | **F1/F2** projection run, registered CLOSE (`MEASURED_FACTS.md` F1/F2). Payload cut **24.2 %**, billed cut **2.4 %**, more expensive than the full transcript from step 3; main call cached **0/134, 0/426, 0/499, 0/569, 0/663** while the transcript's cached share climbed **0 → 0.166 → 0.217 → 0.350 → 0.489**. | Payload length is not the bill; an unstable prefix zeroes reuse. | That any specific arm loses; that a projection is unprofitable in general. | Arm C (`masking-no-fetch`) may not claim an economic win from a shorter prompt; it must report `cached_tokens` per turn. |
| P2 | **C0-EQUALINFO** (`orchestration/handoffs/C0-EQUALINFO.json`): equal-information baseline C0F **1,911.2** uncached/turn vs R **3,524.0**, ratio **1.8441**. | The pointer arm can be **more** expensive at equal information. | That the pointer case is dead — it survives only above the window or on cache-hostile history (`ADOPTION.md`). | Arm D must be compared against arm A at equal information, not against a truncated strawman. |
| P3 | **E2 cache-forensics** (workspace, 89 requests): R t19–34 mean uncached **1,658.9375 = 456.6875 tail + 30.25 boundary + 1,172.0 re-prefill** (residual 0.0 on 16/16); **33/37** steady R turns satisfy `cached == 64·floor(prompt_j)`. | A compaction's cost is a **re-prefill** charged at the tail; the block law (64) holds on steady turns. | Any law for appends or for a different engine. | E1 offsets are expressed in tokenizer units and reported in tokens **and** bytes; E2 charges the rebuild as measured uncached work. |
| P4 | **E4 boundary** (220 requests): rep-1 `cached == 0` in **45/45** boundary rows (`1024` 20/20, `1088` 20/20, `1025` 0/20, `1023` 0/20); pooled multiples **45/45** vs non-multiples **0/40**, Fisher **3.4646074215706565e-25**; rep-2 hits only at **`L−64` 40/40**. | A multiple-of-64 prefix boundary is real at rep 1 on this rig. | "Deterministic"; a rule for arbitrary offsets; anything past rep 1. | `rewrite_registers` is a control in every envelope; a one-off measurement is never called a law. |
| P5 | **E4R rep-3** (180/180 rows): `1024` `0 → 960 → 960`, `1088` `0 → 1024 → 1024`; pooled rep-3 **`L−64` 40/40**, **`L` 0/40**, `rep3 == rep2` **40/40**, CP95 **[0.9119, 1.0]**. | Bounded persistence through repeat 3. | "Permanent". Rep-4 was unreachable (5 sends × 40 = the cap). | Repetition count is a measured parameter; the protocol reports 3 reps and says so. |
| P6 | **LIVE-MEAS** (960 rows): pooled R/A **1.2988**, sd **0.03383**, t95 **[1.2147, 1.3828]**, **df = 2**; t1–40 **1.7308** vs t41–80 **1.0122**. | Ratios are horizon-dependent and interval estimates at df=2 are wide. | A horizon-free constant; extrapolation beyond 80 turns. | Horizons 10/30/60 are reported **separately** and never pooled into one ratio. |
| P7 | **C53** (`papers/context-cache/CLAIMS.md` C53, `recompute.py::c53`): B/A **6.744331504** [4.04542649, 9.44323652], C/A **1.105174403**; A 123,240 prompt / 102,912 cached / 20,328 uncached, B 123,256 / 0 / 123,256, C 123,216 / 103,424 / 19,792; 8 fan-outs × 8 branches, single seed. | A branching arm can bill 123,256 uncached with **0** cached. | That 6.744 = 123,256/20,328 — the estimator is the **unweighted mean of 8 per-fan-out ratios** (5.379888, 5.667647, 6.034483, 5.389356, **14.70229**, 6.015625, 5.385475, 5.379888; stdev **3.227761582**); the ratio of aggregated totals is **6.063360882** and fan-out 5 drives the mean. | The analysis uses **paired task-level differences**, not ratio-of-totals and not pooled means (§8). |
| P8 | **C54**: resident capacity **30–31 docs = 258,035–266,636 tokens = 0.1592–0.1645** of **1,620,892** declared, at **1.501724×** pressure (2,434,133 tokens, 283 docs), binding constraint the state cache (`max_mamba_cache_size` 64), verdict `consistent_with_lru`; token-pool LRU 188.45 excluded. | A server-wide resident working-set measurement under one pressure. | A per-conversation context allowance, a guaranteed pin, or a universal 260k-token budget. | No arm may be sized by "we have 260k"; the hot-window budget is a **measured** parameter (§6). |
| P9 | **C62**: compaction at a real 32k/64k boundary costs **+134.6 to +747.2** uncached tokens/turn **on average after it**, nothing before; 2,780 rows, 18 compactions, 12 arm-instances; **per turn** the same segment runs **−927 to +5,473**; 12/12 arms have a turn below baseline; first compaction at turn 71 (32k) / 143 (64k). | The checkpoint cost is real, post-boundary, and **the mean hides the per-turn sign**. | A per-turn range = the range of arm means (the paper states this explicitly); independence from `keep_last`, run length or trigger (one cell's trigger was budget headroom). | E2 reports per-turn and per-segment, and its trigger is a **parameter**, not a constant. |
| P10 | **C64 / `papers/context-cache/MANUSCRIPT.md` §8a** (production SGLang, one request per measured turn, same 71-turn schedule): P0 whole-context **541.07** uncached/turn [501.68, 581.51], mean prompt **12,336.00**; P1 pointer+tail **528.64** [521.19, 536.13], mean prompt **2,326.13**; P2 = P1 + grid pad **549.49** [542.17, 556.80], mean prompt **2,421.03**; **P2−P1 +20.8429** [10.014, 31.586], 70 pairs, ratio of means **1.039427**; P2−P0 **+6.5000** [−34.971, 46.914] (null). **C64a** supersedes the paper's original padding *win* (the arms resent a turn until the pad aligned and recorded only the second send — a cost figure, not a saving). | Grid-aligned padding **costs** ~21 uncached tokens/turn and recovers about four fifths of what it pays. | Any saving; any transfer to another engine, block size or schedule. | **No padding arm and no residue-avoidance rule** anywhere in this protocol; a "pad to 64" instruction in a runner is a defect to report, not a tuning knob. |
| P11 | **Workspace `E1 fork-break-cost`** (mechanism batch, *not* CON-E1; 195 requests / 228 rows / 3 sessions × 38 turns, events `[12,17,22,27,32,37]`, 36 event rows / 18 pairs): fork vs summarise-in-place median **5,132.75** vs **442.25** uncached; paired median **+4,774.25** (range −2,035..+5,611.5), 95 % CI **[193.5, 4,868.25]**, **15/18** positive, sign p **0.0075**; excluding the event-index-2 stratum n=15, median **+4,839.5**, CI **[4,677.5, 4,901.5]**, **15/15**, p **6.1e-05**. | On this rig the *fork* form of a checkpoint is far more expensive than summarise-in-place, and the effect survives on 15/15 events. | That CON-E2's arms (append / one checkpoint / periodic) behave the same; that "checkpoint" is one mechanism (fork ≠ rewrite ≠ digest). | CON-E2 is the premise test and may not be replaced by this prior; the protocol's B arm must state which checkpoint form it uses. |
| P12 | **Quality path** (`experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`): verdict **PATH-CANNOT-SAY-YES**; a valid `pos-full` log fails **7** checks (`cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`); only the bare-value diagnostic `pos-exact-only` passes (`verified_success` true, 3/3, TVS 22,396); `grade_v2.py` is incompatible with that; negatives are indistinguishable from the positive. | The current scorer measures a contract it does not read. | That any quality arm can be scored today. | **Stage-0 kill condition** (§3.1): no quality spend until a fixture/grader fix passes a red→green control. |
| P13 | **Checkpoint coverage** (`docs/CHECKPOINT-COVERAGE.md`): at `b+c = 3` the exact McNemar minimum two-sided p is **0.25**, so a 3-checkpoint fixture "cannot rank two arms at any number of repeats"; v6 adds 9 requests/arm/rep (v5 **36** → v6 **144** across 4 arms × 3 reps, **+108**). | Ranking needs ≥12 decidable checkpoints. | That 12 checkpoints are enough for a small effect; that v6's items are all gradeable (8/12 today). | Arm budgets include the checkpoint requests; a 3-checkpoint fixture is refused for any arm whose verdict is a ranking. |
| P14 | **Gen-6 grid** (`docs/STATE.md`, `docs/GRID-2-FINAL.md`): overall **`not_adjudicable`**; 1,270 requests, **79.375**/cell; four instrument defects (treatments never fired, replicate collapse, absent stamp admitted, cap-gate under-count). | A grid can be fully spent and still not adjudicate. | Any H1/H2/H3 conclusion. | Every prerequisite in §3 exists because one of these defects fired. |

Two engine facts carried forward, because they set what an "observable" is: the SGLang append law
`uncached = (P1 mod 64) + L` with residual 0 in **186/186** rows, and vLLM's
`uncached = (P1 mod 1056) + 1056 + L` with block **1056** (`experiments/ptr-engine/RECORD.md`). They are
engine-specific; the protocol records the formula beside every derived number and never compares across
them.

## 3. Stage 0 — prerequisites and kill conditions (before any call)

Each item is a gate. A failed gate **stops the stage**; it is not a caveat to note later.

### 3.1 The quality path must be able to say yes

`QUALITY-POSITIVE-CONTROL.md` shows that `score_longrun.py` never reads `answer_marker`, defaults the
three v3 checkpoints to `mode = "exact"`, and compares **the entire turn content** to the expected string,
so a log that satisfies the fixture's own required `ANSWER: <value>` line can never pass. Required
before spend, with the control run red first:

- a known-good log **passes** (the `pos-full` form, not the bare-value diagnostic);
- a wrong-value log **fails** on the value, not on formatting;
- a missing-fact log **fails** and is distinguishable from the wrong-value log;
- the same log scores identically twice (determinism), and a tampered fixture exits 2.

If the grader cannot be made to pass a contract-following log, no quality number from any arm is
reportable, and every arm in §6 is **void** before its first call.

### 3.2 Twelve decidable checkpoints

Because `b+c = 3` gives a minimum two-sided p of 0.25 (§2 P13), any arm whose purpose is *ranking* uses a
fixture with ≥12 decidable checkpoints. Today only `tasks-v5/runtime-v5/LR-01.v6.json` and
`tasks-v6/LR-01.v8.json` carry 12; the six authored fixtures under `longrun/fixtures/` carry **3** each
(verified: LR-01 48 turns, LR-02 64, LR-03 56, LR-04 40, LR-05 72, LR-06 60; 3 checkpoints and 3 negative
constraints each). Two consequences the protocol accepts rather than hides:

- **`grade_v5` grades 8 of 12** v6 items; 4 need two branches (`NONE`, `call_at_line`) before a 12-item
  score exists (`CHECKPOINT-COVERAGE.md` §6).
- **The v8 wall is not measured.** `tasks-v6/LR-01.v8.json` sets `wall_tokens = 3838` and
  `wall_tokens_by_arm = 10616` (all four arms) by `prompt_T1 + ceil(mean declared answer padding × 23)`.
  Its own basis block lists measured per-turn growth of **75.021 / 684.362 / 111.787 / 38.532 / 60.681 /
  61.0** tok/turn — an 18× spread — and `docs/STATE.md` records the consequence: live base
  **5,628–6,139** tokens at **41–98** tok/turn implies **turns-to-wall 73–113 > 48**, so the treatments
  never fired (`usable_for: []`, `evicted_turns=0`, `digest_rows=0`).

Gen-7 therefore needs a **v9 wall priced from measured growth of the arm being run** (base + slope ×
turns, with the slope measured on the same fixture), and a dry run that demonstrates each treatment
reaching its wall inside the horizon.

### 3.3 Four fingerprints, frozen per run

`model_fingerprint` (id + revision/quantization digest), `tokenizer_fingerprint` (files/hash + chat
template hash), `renderer_fingerprint` (content digest of the module→bytes code), `engine_fingerprint`
(image digest + exact flags). `R2` applies: a differing fingerprint is a different experiment. Placeholders
in a draft are a hard stop.

### 3.4 Replicate identity

Every cell carries its replicate in the key. The gen-6 selector deduped on `(arm, rep, turn_index)` with
every cell writing `rep=1`, and **288 turn rows → 96 analysed** (`dropped_duplicate=192`); that merge is
also why p95 was refused. The protocol requires a unique `(arm, rep, cell, turn_index)` key, `rep` in the
`run_id`, and a pre-analysis assertion that the row count equals cells × turns × reps.

### 3.5 Treatment activation proven before analysis

For each arm, a cell is usable only if its declared treatment predicate is non-zero on the rows:
`evicted_turns > 0` (A at cap), `digest_rows > 0` (B), `masked_rows > 0` (C), `fetch_rows > 0` and
`retrieval_outcomes` non-empty (D), `oracle_injections > 0` (E). A cell that fails is reported
`INVALID-INSTRUMENT` and **excluded by rule, not by name**. The gen-6 census excluded two `exit 4` cells
by name while `longrun/analyze_stats.py:749` admits a manifest-less cell — both behaviours are refused
here: **absent stamp ⇒ excluded**, and the exclusion is computed from the stamp, not hard-coded.

### 3.6 Budget preflight

Reconcile against the live ledger at execution time
(`experiments/ptr-engine/measure/REQUEST-LEDGER.json`, rebuilt 2026-10-28: **2,591 spent / 1,729
remaining of 4,320**). If the ledger cannot be rebuilt and the arithmetic shown, the budget is **unknown**
and zero requests are sent. A cap is set per arm **before** the first call; a run that reaches its cap
mid-cell exits 4 and that cell is `INVALID-INSTRUMENT`, not a partial result.

### 3.7 Independent verification

No self-graded run. The verifier is a separate process over the frozen rows, with the fixture digest
checked at score time; `score_longrun.py` already exits 2 on tamper and 3 on a stub/incomplete log. The
person or script that ran the arm does not certify its accuracy.

### 3.8 Fixture classes, including the missing ones

| Class | Status in the authored fixtures | Protocol treatment |
|---|---|---|
| exact fact recovery | present (all 6 fixtures) | usable |
| changed decisions | present as `repair` at a declared turn (6/6) | usable |
| negative constraints | present, 3 per fixture (6/6) | usable |
| multi-hop retrieval | **MISSING** — every authored checkpoint is a single-source pointer | the class is reported `UNAVAILABLE`; it is **not** scored as success, and no fixture is fabricated here |
| unavailable / stale / revoked source | **MISSING** | exercised only by the worked sketch in §7 until a fixture exists; result recorded `NOT_OBSERVED` |

## 4. `E1-CACHE-BOUNDARY-SWEEP` (≤ 60 calls)

**Question** (preserved from the handoff): how does cache reuse depend on *where* a rewrite lands, on this
engine and this model?

**Hypothesis:** with a frozen system+project prefix `P` of ~8–12K tokens, reuse falls monotonically as the
first rewritten byte-offset moves earlier, and there is a measurable boundary below which the request is
served effectively cold.

**Method.** One prompt skeleton. Controls first, then a sweep at ≥8 rewrite offsets from tail to head,
offsets expressed **in tokenizer units** and reported in tokens *and* bytes. 3 repetitions each,
alternating order, one frozen build, one container (`R9`). Record `prompt_tokens`, `cached_tokens` (or
absent), `uncached_prefill_tokens` where exposed, `ttft_ms`.

| Element | Definition | Can it report the opposite? | Budget |
|---|---|---|---|
| identical control | byte-identical repeat of the skeleton | yes — a miss here | 3 |
| never-sent control | a prefix never sent before | yes — any hit here | 3 |
| append control | skeleton + `k` appended tokens | yes — reuse below `P − k` | 3 |
| mismatched-tokenizer control | same text, deliberately different tokenizer | yes — any reuse here | 3 |
| sweep | 8 offsets × 3 reps, tail→head | — | 24 |
| **total** | | | **36 (of 60; 24 held for re-runs)** |

**Control thresholds** (`handoff from consonance/EXPERIMENTS.md` §Method/§Controls, restated here so that
"green" is defined): identical → hit **≥ 0.9 of `P`**; append → reuse **≥ `P − k`**, where `k` is the
number of appended tokens; never-sent → **0**; mismatched-tokenizer → **no reuse (0)**. A control without
an explicit threshold is not green — it is unreported, and §9 void item 8 applies.

**Falsifier** (unchanged): reuse does **not** fall monotonically with earlier rewrite offset (e.g. depends
on block alignment only, or is all-or-nothing at every offset). Then `rewrite_depth` is not a usable
predictor, the checkpoint cost model is wrong, and it is replaced by whatever the data does show.

**Decision it buys:** whether the `rewrite_depth` term survives at all, and whether a checkpoint is priced
**per token** or **per boundary**. Drop `rewrite_depth` / price per boundary is a *result*, not a
default.

**Stop rule:** if the identical or never-sent control is red twice, the container is misconfigured — stop,
report `INVALID-INSTRUMENT`, spend nothing further. If two consecutive offsets violate monotonicity in
the same direction, the falsifier has fired: stop the sweep, keep the control rows.

**DRAFT `run.json`** (not frozen; placeholders are deliberate):

```json
{"schema":"consonance.run/1",
 "run_id":"CON-E1-<YYYYMMDD>-<nn>",
 "arm":"CON-E1-CACHE-BOUNDARY-SWEEP",
 "started_utc":"<2026-…T…Z>",
 "git_sha":"<40-hex>",
 "fixture_sha":"sha256:<digest of the prompt skeleton file>",
 "engine_image_digest":"sha256:<image digest>",
 "engine_flags":["--enable-prefix-caching","<…>"],
 "hardware":"<gx10 / GB10, 128 GB unified>",
 "quantization":"<nvfp4>",
 "budgets":{"max_calls":60,"max_cost_usd":0},
 "controls":{"identical_repeat_hits":true,"never_sent_misses":true,
             "append_reuses":true,"rewrite_registers":true},
 "notes":"CON-E1. Offsets in tokenizer units, reported in tokens and bytes. Engine block law recorded beside every derived uncached value. SGLang :8012 null cached = 0; vLLM null = unknown. Thresholds: identical >= 0.9 of P; append >= P - k; never-sent 0; mismatched-tokenizer 0. The mismatched-tokenizer control (no reuse) is declared here in notes, not as a controls key: the contract's controls object has exactly four keys."}
```

The contract's `controls` object has exactly these four keys; additional controls are declared in `notes`
and reported in the control table, never as new keys.

## 5. `E2-CHECKPOINT-COST` (the premise test)

**Question:** what does one compaction checkpoint cost, and over how many steps can it repay that cost?

**Hypothesis:** a checkpoint that rewrites `D` tokens costs ≈ `D × prefill_cost` and saves
`ΔD × (1 − reuse)` per subsequent step, so it repays inside 20 steps for task lengths above ~40 steps and
never repays for short tasks.

**Arms** — same model, same outputs (fixed seed / temperature 0 where possible), same verifier:

| Arm | Definition | Positive control | Negative control | Falsifier | Budget |
|---|---|---|---|---|---|
| **A** append-only | no checkpoint; grows to the declared wall | append shows a **climbing** cached share on this fixture (F2's curve) | a byte-identical repeat must hit | none (baseline; cannot falsify itself) | 40 turn req |
| **B** one checkpoint | one summarise-in-place checkpoint at ~70 % of the turn budget (t≈28 of 40); the **form** must be named (rewrite vs fork — P11 shows fork is ~11.6× the median) | the checkpoint event is recorded (`digest_rows>0`) and post-checkpoint uncached is measurable | a **no-op checkpoint** (rewrite nothing) must cost ≈ 0 | does not repay within 20 steps | 40 + 1 |
| **C** periodic | checkpoints every ~20 steps (t20, t40); t40 is the last turn of a 40-turn fixture, so that checkpoint is recorded and reported but has **zero** post-checkpoint repayment turns and is excluded from the repayment window | second checkpoint's cost is ≤ the first's (learning) | same no-op control | repays only by shortening the prompt when measured as **uncached work** | 40 + 2 |

**Primary measures:** uncached prefill tokens (measured, or `derived` with the formula named), TTFT,
**time-to-verified-success**, per turn and per segment (pre-boundary / transition / post-boundary), not
arm means alone (P9).

**Falsifier** (unchanged): the checkpoint arm does not repay its rebuild within 20 steps, **or** repays
only by making the prompt shorter (the gain vanishes when measured as uncached work rather than payload).
Then "bounded working memory" is not an economic win at these task lengths and the BCF premise is
restated.

**Premise test for M2** — a negative here stops the programme (the handoff calls this "the single most
valuable number in the programme"). It is not a quality arm and cannot be scored as one; its output is a
verdict on the *cost* model.

### 5.1 The 120-call cap cannot also deliver a verdict — arithmetic, and the decision

The handoff caps CON-E2 at **≤ 120 calls** and asks about repayment "inside 20 steps for task lengths
above ~40 steps". A 40-turn fixture with three arms needs:

```
A 40 + B 40 + C 40                                  = 120 turn requests
                 + checkpoint requests (B 1, C 2)   =   3
one rep, as designed                                = 123   > 120
three reps (3 × 123)                                = 369
+ 9 checkpoint/verify requests per arm per rep if a
  12-checkpoint fixture is used (3 arms × 3 reps × 9) = 81
three-rep total with the 12-checkpoint fixture      = 450
```

So there are exactly two honest options, and the protocol does **not** silently pick one:

- **(a) A 120-call run is a one-rep descriptive probe.** It cannot adjudicate the falsifier — the
  workspace's own rule is that one rep is descriptive and never a verdict, and 3 arms × 40 turns × 1 rep
  is already exactly the cap before the 3 checkpoint requests. If (a) is chosen it is labelled
  `DESCRIPTIVE, NOT ADJUDICABLE` in the verdict line, quoted only as a cost estimate, and never as
  "E2 passed/failed".
- **(b) A 3-rep adjudicable CON-E2 needs 369–450 calls**, which exceeds the handoff's stated cap of 120
  and therefore requires an explicit owner decision against the **1,729** requests remaining
  (dated 2026-10-28, to be reconciled at execution time per §3.6).

**Recommendation:** ask the owner for (b) at **450**, because it fits inside 1,729 and because a
descriptive probe cannot fire or clear the falsifier. If the owner declines, run (a) at 123 *only* if a
cost estimate is worth 123 requests, and stamp it descriptive. Note that neither option is approved by
this document.

**DRAFT `run.json`** — one file per arm, same `run_id` stem, `rep` in the id:

```json
{"schema":"consonance.run/1",
 "run_id":"CON-E2-<YYYYMMDD>-arm<A|B|C>-rep<r>",
 "arm":"CON-E2-<A|B|C>",
 "started_utc":"<2026-…T…Z>",
 "git_sha":"<40-hex>",
 "fixture_sha":"sha256:<v9 runtime fixture digest>",
 "engine_image_digest":"sha256:<image digest>",
 "engine_flags":["--enable-prefix-caching","<…>"],
 "hardware":"<gx10 / GB10, 128 GB unified>",
 "quantization":"<nvfp4>",
 "budgets":{"max_calls":<123 for option (a) | {"A":147,"B":150,"C":153} for option (b)>,"max_cost_usd":0},
 "controls":{"identical_repeat_hits":true,"never_sent_misses":true,
             "append_reuses":true,"rewrite_registers":true},
 "notes":"CON-E2, option <a|b>. Checkpoint form: <summarise-in-place | fork | digest>. No-op checkpoint control declared in the control table. Per-turn and per-segment reporting; no arm-mean-only claim."}
```

Option (b) caps are **per arm, not per-run**: arm A 40 turns, arm B 40 turns + 1 checkpoint = 41, arm C
40 turns + 2 checkpoints = 42, each plus 9 checkpoint/verify requests per arm per rep → **A 49 / B 50 /
C 51 per rep**, i.e. **147 / 150 / 153** over 3 reps, **450** in total. A shared 150 cap would strand arm
C at 153 and trip §3.6's mid-cell cap rule, marking the cell `INVALID-INSTRUMENT` rather than producing
data.

## 6. Comparative experiment — five arms (prospective, **UNFUNDED**)

Paired, same-fixture arms. Design contract: the bounded recoverable context view (BRCV) — deterministic
stable prefix; bounded recent verbatim window; immutable content-addressed external records; pointers with
id+revision+sha256+range; on-demand `fetch(ref, range?)` with explicit outcomes; masking before summary;
checkpoint only when a forecast pays for its cache break. Mapped to the existing contract fields only:
manifest/epoch → `manifest_id`/`state_epoch`, branch → `branch_id`/`parent_branch_id`, fetch → an expansion
recorded on the run row, masked entry → an omission, unavailable/unauthorized → an unknown (§7). No
`consonance.fetch/1` schema is invented.

| Arm | Definition | Positive control | Negative control | Falsifier | Requests/turn |
|---|---|---|---|---|---|
| **A** `full-transcript` | append-only, FIFO at the declared wall | byte-identical repeat hits | never-sent prefix misses | none (baseline; cannot falsify itself) | 1 |
| **B** `transcript-compact` | existing digest at cap, recent 4 turns raw | digest fires (`digest_rows>0`); post-digest uncached measurable | no-op digest costs ≈0 | digest never repays within 20 steps | 1 + digests |
| **C** `masking-no-fetch` | old tool outputs replaced by pointer markers, **no** external fetch | masking fires (`masked_rows>0`); marker resolves to a pointer id | a masked fact cannot be answered → must abstain, never invent | no quality-preserving saving vs A | 1 |
| **D** `bounded-context-fetch` | BRCV: frozen prefix, bounded window, pointer table, `fetch` on demand, checkpoint only on forecast | `fetch_rows>0`; `OK` outcome returns the pinned range byte-identically | missing ref → `NOT_FOUND`; revoked → `STALE_OR_REVOKED`; scope → `SCOPE_UNGRANTED` | not non-inferior on verified success **and** not lower in uncached work/time-to-verified-success at 60 turns | 2 (fetch + answer) |
| **E** `oracle-evidence` | same prompt budget as D, needed evidence injected | injection counter >0; same verifier | a fact outside its budget must also abstain; if E answers from parametric memory without an injection the cell is `INVALID-INSTRUMENT` | none (upper-bound diagnostic; not deployable) | 1 |

Shared requirements for all five: one fixture set and version, one frozen build, four equal fingerprints
(`R2`), the same verifier and acceptance checks, and the same prompt-budget accounting. Because D's
`fetch` outcome is an *event*, D's rows also carry the outcome vocabulary — and the scorer must be extended
to read it (§7), which is itself a Stage-0 item.

**Control battery (beyond the per-arm pair):** identical-repeat cache control for every arm; append cache
control for every arm; a holistic positive control (fact present, fetch works, answer correct); a
holistic negative control (fact absent from the store, arm must abstain). Each is run red first on a
deliberately broken log.

### 6.1 Fixtures and horizons

`longrun/fixtures/LR-01..06.json`, shared and versioned (`tasks-v5`/`tasks-v6` runtime forms), classes
repo-fix / multi-file-refactor / bug-fix-with-test / constraint-survival / adversarial-debug / doc-sync;
48 / 64 / 56 / 40 / 72 / 60 turns.

| Horizon | Cells | Note |
|---|---|---|
| 10 turns | 6 tasks | all fixtures supply it |
| 30 turns | 6 tasks | all fixtures supply it |
| 60 turns | **3 tasks** (LR-02 64, LR-05 72, LR-06 60) | **LR-01 (48), LR-03 (56), LR-04 (40) cannot supply 60 turns → `UNAVAILABLE`, not imputed** |

3 reps per task/arm. The 60-turn cell has 3 tasks, so "6 tasks × 3 rep" at 60 turns is not available and
is never written as if it were.

### 6.2 Metrics

Per horizon and arm: total and peak **logical** prompt tokens; uncached work when observable (else
`NOT_OBSERVED`); cache reads; fetch calls and fetch tokens; completion tokens; storage/index size;
rebuild cost; end-to-end wall time; **time and tokens to independently verified success**; quality;
abstention; forbidden-action (negative-constraint) results. Quality and abstention are reported as
paired task-level differences with intervals (§8). Any denominator that is zero is `UNDEFINED`, never 0.

### 6.3 Request arithmetic — why the comparative is unfunded

```
turns per arm per rep over all available cells = 6×10 + 6×30 + 3×60 = 420
four one-request arms (A,B,C,E)               = 1,680 per rep
three reps                                    = 5,040
D at 2 req/turn adds                          = 2 × 420 × 3 = 2,520
total                                         = 5,040 + 2,520 = 7,560
+ B digests and D checkpoints (≥1 per cell)   = ≥7,560
remaining ledger (2026-10-28)                 = 1,729
ratio at the most favourable reading          = 5,040 / 1,729 = 2.92×
ratio with D at 2 req/turn                    = 7,560 / 1,729 = 4.37×
```

Even if D were free, the matrix is ~2.9× the remaining ledger; at the design's own request shape it is
~4.4× (4.37×), and the checkpoint/digest requests only push it further. **The full 6-task × 3-rep × 5-arm
comparative cannot be run on the current ledger and is marked `UNFUNDED`.** It is not scheduled here.

**Separately budgeted pilot (clearly a pilot, not the comparative).** Purpose: prove the instrument —
controls fire red, treatments activate, the scorer can express a retrieval miss. One task at 30 turns, all
five arms, one rep: `30 × 4 + 60 = 180` turn requests + ~5 checkpoint/digest = **≈185**. It yields no
verdict, and its output is an instrument report, not an arm comparison.

**The owner decision, exactly:** (i) fund the comparative at ≥7,560 requests by raising the cap above
4,320, or (ii) fund the 185-call instrument pilot and defer the comparative, or (iii) fund neither. Until
one is chosen in writing, the comparative stays unfunded and unscheduled.

### 6.4 p95 and the tail

The frozen floor is `min_n_for(0.95) = 60`; p95 is refused at n=48 and was refused for gen-6. At 3 reps ×
3 tasks the 60-turn cell has 9 samples — a p95 there is not estimable, and n_eff (gen-6 measured 26.14
against a floor of 60) must be computed and reported for any latency statistic. A reliable tail requires a
separately budgeted run; the protocol reports sample size and full distributions in the meantime.

## 7. Worked hypothetical — required old fact is unavailable

**Sketch, not an authored fixture.** `HYP-ABSENT-01` is used here only to pin the success/abstention
distinction; it is not written to disk and is never scored as a result.

Fixture sketch: 24 turns. At T4 a tool output records the value at `resolve.py#L39` (`DEFAULT_MAX_REFS =
64`). At T12 the body is dropped from the working set and its record is **revoked** (status changes on the
pointer's revision). At T20 a checkpoint asks: *"What is the default per-turn resolve budget in refs?"*
Truth is `64`; the only source is the revoked record.

**Bounded arm D — expected records:**

```json
{"schema":"consonance.call/1","call_id":"…","run_id":"CON-CMP-…-D-rep1","arm":"D",
 "task_id":"HYP-ABSENT-01","step":20,"manifest_id":"sha256:…","branch_id":"sha256:…",
 "state_epoch":4,"model":"<…>","engine":"<…>",
 "model_fingerprint":"sha256:…","tokenizer_fingerprint":"sha256:…",
 "renderer_fingerprint":"sha256:…","engine_fingerprint":"sha256:…",
 "prompt_tokens":<N>,"cached_tokens":<reported|null>,"uncached_prefill_tokens":null,
 "ttft_ms":<t>,"total_ms":<t>,"completion_tokens":<n>,"finish_reason":"stop",
 "verified_success":false,"exit_cause":"abstained"}
```
Run-side event rows for the same turn: `retrieval_attempt{ref:"src/resolve.py@<rev>", outcome:"STALE_OR_REVOKED"}`, `masked_entry{ref:…, since_turn:12}`, and the scorer card adds
`retrieval_miss:"STALE_OR_REVOKED"`, `abstained_correctly:true`, `tokens_to_verified_success:null` (undefined,
not zero). The completion must name the missing evidence; a description of the *instruction* is not an
answer.

**Oracle arm E — expected records:** if the fact is present within E's budget, E injects it at T20,
answers `64`, and is `verified_success:true` with a real `tokens_to_verified_success`. If E's budget
cannot hold the fact (the honest case when the budget is deliberately matched to D), E has no evidence
either and **must also abstain**; an E that answers from parametric memory is `INVALID-INSTRUMENT`, because
the arm's premise is "injected evidence", not "model recall".

**Protocol failure conditions, stated as such:** D producing `64` with `verified_success:true` while the
only record is revoked; D producing `64` without a `retrieval_attempt` row; the scorer recording the D turn
as `verified_success:true` because the text matches the truth string. Today `score_longrun.py` cannot
express the distinction at all — a case-insensitive grep for `abstain|retrieval_miss|STALE|REVOKED|NOT_FOUND`
returns **0 matches**, and the four check kinds are `artifact` / `fact` / `constraint` / `repair`. The
scorer extension that adds `retrieval_miss` / `abstained_correctly` is therefore a **Stage-0 prerequisite**
with its own red→green control (a fabricated answer must fail the extension before an abstention can pass
it).

## 8. Analysis and reporting rules

1. **Paired, task-level differences.** For each task and horizon, compare arms within the same fixture and
   fingerprint set; report the paired difference and its interval. No pooled arm means, no ratio of
   totals (P7 shows the two estimators differ: 6.063 vs 6.744).
2. **Intervals name their method and n** (t-based with df stated, bootstrap with seed, Clopper-Pearson for
   proportions). `df = 2` intervals are reported as such, not widened silently.
3. **First-class non-results:** `UNDEFINED` (no denominator), `UNAVAILABLE` (horizon/fixture absent),
   `NOT_OBSERVED` (engine does not expose it), `INVALID-INSTRUMENT` (control or activation failed),
   `UNFUNDED` (no budget). Each appears in the table; none is replaced by a zero or a blank.
4. **No p95 below the floor** (§6.4); no tail claim from ≤9 samples.
5. **No re-pinning** after rows are seen. A fixture, threshold or estimator that moves after the first call
   makes the run `retrospective:true` and it is labelled so.
6. **Derived is not measured.** `uncached = prompt − cached` is `derived` with the formula named, never
   quoted as a measurement; `uncached_prefill_tokens` stays `null` unless the engine exposed it.
7. **Null semantics per endpoint and field** (`R5`), recorded on every row that carries a null:
   `:8012` null cached = 0; `:8014` null = unknown.
8. **Generation labels** on every row and table: gen-6 and gen-7 are never in the same column.

## 9. What voids the protocol / no-go

Any one of these makes the affected result invalid — not "noisy", not "preliminary":

1. the quality path cannot be made to say yes (§3.1);
2. any fingerprint missing, changed mid-run, or filled with a placeholder;
3. a treatment that did not fire (`usable_for: []`, `digest_rows=0`, `fetch_rows=0`);
4. replicate collapse — `rep` absent from the key, or rows deduped across reps;
5. absent manifest/stamp admitted into the census;
6. budget unreconciled, or a cell that hit its cap mid-run counted as data;
7. a missing fixture class (multi-hop, stale/revoked) scored as success instead of `UNAVAILABLE`/`NOT_OBSERVED`;
8. a control that cannot report the opposite, or a control run only green;
9. any live call before `run.json` is frozen, or a `run.json` written after the first call and not marked
   `retrospective:true`;
10. pooling across builds, generations or ledger epochs;
11. an abstention scored as `verified_success` (or a fabrication scored as anything but failure);
12. a padding/residue-alignment instruction introduced to "improve" a run (P10);
13. `cached_tokens: null` mapped to 0 outside the established endpoint rule.

**No-go for the design itself:** if CON-E2 fires its falsifier, the bounded-working-memory premise is not
an economic win at these lengths and M2 is not justified by cost. If the comparative ever runs and D is
not non-inferior on verified success **and** not lower in uncached work/time-to-verified-success at 60
turns, the bounded view is **not supported** — the correct output is that negative result, not a narrower
claim.

## 10. Relationship to `BOUNDARY-PREREG` and to gen-7

- `experiments/ptr-engine/BOUNDARY-PREREG.md` is **registered** (2026-10-26T01:22-0500) as a design with
  **696 scheduled requests** (stage 1 216, stage 2 300, stage 3 180) and a ceiling of **810**, three
  refusal points, arms `C0-static` / `C0-trunc` / `R-pointer` / `R-pointer-prefetch`. It is a **separate
  registered candidate**: not executed, not approved, not E1, not E2, and not to be pooled with anything
  here. Its `R-pointer` arm's "2 requests/turn (fetch + answer)" is the only place that per-turn request
  shape is grounded, and it is why D is priced at 2.
- The gen-6 grid is `not_adjudicable`, and its rows are **non-poolable** with gen-7: the fixture wall, the
  replicate key and the census rule all change. Gen-7 requires the v9 wall (§3.2), the replicate key
  (§3.4), activation gating (§3.5) and the stamp rule (§3.5) before a single call.
- Neither this protocol nor the comparative schedules either of them. No live request is made, and no
  budget is reserved, by this document.

## 11. References

| Path | Anchor |
|---|---|
| `handoff from consonance/EXPERIMENTS.md` | E1 "Cache reuse … depends on *where* a rewrite lands"; E2 "The checkpoint arm does not repay its rebuild within 20 steps"; budgets 60/120/40/80/60/80 = 440 |
| `handoff from consonance/INTERFACE_CONTRACT.md` | §1 four fingerprints; §2 "`cached_tokens` … **never 0**"; §3 "frozen BEFORE the first call"; §4 `acceptance.negative_constraints`; §5.3 "a control that can only report 'as expected' is not a control" |
| `handoff from consonance/MEASURED_FACTS.md` | F1 payload 24.2 % / billed 2.4 %; F2 "0 of 134, 0 of 426, 0 of 499, 0 of 569, 0 of 663" |
| `handoff from consonance/DO_NOT_REDO.md` | ten traps, incl. "cached_tokens multiple-of-64 is not a defect" |
| `experiments/ptr-engine/RECORD.md` | append law `uncached = (P1 mod 64) + L`, residual 0 in 186/186; vLLM block 1056; C1 null semantics |
| `experiments/ptr-engine/ADOPTION.md` | "67.1x is an index-encoding choice, not a constant"; body store ≠ KV cache |
| `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md` | "PATH-CANNOT-SAY-YES"; `pos-full` fails 7 checks; `pos-exact-only` 3/3, TVS 22,396 |
| `experiments/ptr-engine/longrun/score_longrun.py` | four check kinds `artifact`/`fact`/`constraint`/`repair`; exit 2 on tamper, 3 on stub; no abstention vocabulary |
| `docs/CHECKPOINT-COVERAGE.md` | "at `b+c = 3` the exact McNemar minimum two-sided p is 0.25"; v5 36 → v6 144, +108; 8/12 gradeable |
| `docs/STATE.md` | four instrument defects; ledger "2,591 spent / 1,729 remaining of 4,320"; grid 79.375/cell |
| `docs/GRID-2-FINAL.md` | `not_adjudicable`; H1 p50 156.151 ms [146.306, 291.926], n=48, n_eff 26.14 < 60 |
| `orchestration/STATUS.md` §7.1 | workspace `E1 fork-break-cost` (195 req; medians 5,132.75 vs 442.25; +4,774.25 [193.5, 4,868.25]); `E2 cache-forensics` (89 req, 1,658.9375 = 456.6875 + 30.25 + 1,172.0) |
| `orchestration/STATUS.md` | `E4` 45/45 vs 0/40, Fisher 3.4646074215706565e-25; `E4R` 180/180, `L−64` 40/40, `L` 0/40; `LIVE-MEAS` 1.2988 sd .03383, t1–40 1.7308 vs t41–80 1.0122 |
| `papers/context-cache/CLAIMS.md` | C53 (6.744331504, CI [4.04542649, 9.44323652], stdev 3.227761582); C54 (258,035–266,636 tok, 0.1592–0.1645, 1.501724×); C62 (+134.6..+747.2 mean, per-turn −927..+5,473); C64/C64a (P2−P1 +20.8429 [10.014, 31.586]) |
| `papers/context-cache/MANUSCRIPT.md` §8a | P0 541.07 / P1 528.64 / P2 549.49 uncached per turn; prompts 12,336.00 / 2,326.13 / 2,421.03 |
| `papers/context-cache/CONSONANCE-INTEGRATION.md` | B1 SGLang `:8012` null = 0 (cell A P1 397 → 320, 3/3); B2 fingerprints absent from row files; B3 retrospective runs |
| `experiments/ptr-engine/BOUNDARY-PREREG.md` | REGISTERED 2026-10-26T01:22-0500; 696 scheduled / ceiling 810; `R-pointer` "2 requests/turn (fetch + answer)" |
| `experiments/ptr-engine/longrun/run_longrun.py` | `ARMS = ("transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen")`; `projected_requests` = turns + digests + fetch pool |
| `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `wall_tokens 3838`, `wall_tokens_by_arm 10616`, growth basis 38.532–684.362 tok/turn, `checkpoint_turns_note.count 12` |
