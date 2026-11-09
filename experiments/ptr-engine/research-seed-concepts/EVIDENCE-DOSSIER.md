# Evidence dossier — every usable contribution, its record, and its standing

**Purpose.** For each contribution the seed could use, name the dataset or record it comes from, the
claim or section that carries it, the conditions under which it holds, the command that reproduces
it when one is recorded, its current evidentiary status, the contradictory evidence a reviewer will
find, and the role it should play in the paper.

**Compiled:** 2026-11-06. **Requests sent while compiling:** 0. **Files modified:** none outside
this folder.

**Status vocabulary** (used in every row; nothing else is allowed in this folder):

| status | meaning |
|---|---|
| `MEASURED` | a live request produced the number on the date/endpoint stated; a row file or analysis artefact holds it |
| `RECOMPUTED` | derived offline from rows by a named command; exact where stated |
| `RECORD` | a dated record states it and no artefact was re-read for this dossier; valid as a record at its date |
| `INFERENCE` | arithmetic or reasoning from measured inputs, not itself measured; always marked `[INFERENCE]` |
| `PROPOSED-UNTESTED` | a design or protocol with no measurement behind it |
| `REFUTED` | the author's own claim is contradicted by its own rows; do not carry |
| `WITHDRAWN` | was claimed, then withdrawn by a later record; quote only with the withdrawal |

**One fact, one home.** Where a number is owned by `papers/context-cache/CLAIMS.md` this dossier
cites the claim id and does not restate its derivation; where the owner is `experiments/miss-law/`,
`experiments/ptr-engine/RECORD.md` or a handoff, it cites that.

---

## 0. The record base (what exists, and how much of it there is)

| body | size on disk today | owner |
|---|---|---|
| `experiments/miss-law/rows.jsonl` | **774 rows** (387 `measure` with `L_app`, 383 `prime`, 4 controls) | law family, §1 |
| `experiments/miss-law/avalanche/rows.jsonl` | 378 rows, sha256 `8147d195…7b8ba2` | harvested; C9 |
| `experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl` | live cells A–E (27 rows) | C1/C2/C5 closures |
| `experiments/ptr-engine/quality/rows.jsonl` | 115 rows (48 request / 48 prediction / 12 rep / 4 corpus / 3 compaction) | quality arm, §2 |
| 16 gen-6 grid cells | **1,270 request rows**, manifests, 6 usable | §3 |
| `experiments/context-cache/cells/{E1,E2,E3,E4,E4R,LIVE-MEAS,M1-M}` | **5,403 `.jsonl` lines** across seven uncited cells | manuscript fold, §4 |
| Protocol documents (Consonance BRCV) | 356 + 517 lines, both rechecked **PASS**, 0 live calls | §5 |

---

## 1. The append-cost family (`experiments/miss-law/`)

### E-01 — The tail law, SGLang: `uncached = (P1 mod B) + L`, B = 64

| field | value |
|---|---|
| Record | `experiments/miss-law/LAW.md` §1–§3; rows `experiments/miss-law/rows.jsonl`; fit `experiments/miss-law/law_fit.json` |
| Claim as recorded | residual `0` in **186/186** rows (residues 2…63 × 3 reps, P1 8000–8063, L = 13) |
| Recomputed today (2026-11-06) | fit set 387 rows; `sglang` 301 rows, residual distribution `{0: 218, 2048: 2, 4096: 2, 6144: 2, 7680: 1, 7936: 2, 8000: 8, 8064: 66}` — every non-zero residual is an avalanche row billing `P1 + L`; restricting to the **210** non-avalanche residue rows gives residual exactly `{0}` |
| Conditions | one append onto an already-primed prefix; `L = P2 − P1` (never the prefix size); SGLang `occamy-1.0` on `:8012`, `page_size=1`, `enable_cache_report=True`; 3 reps per cell, deterministic |
| Command | the block in [`README.md`](README.md) §Verifying, or `python3 experiments/miss-law/agg.py` (record's own aggregator) |
| Status | **MEASURED + RECOMPUTED** |
| Contradiction | none on the formula. `LAW.md` §8: the 3-rep cells are deterministic, so reps bound transcription error, not sampling variance — do not call it a sampling result |
| Role in F | the paper's measured core (§Results 1) |

### E-02 — The class change at `P1 mod B ∈ {0,1}`

| field | value |
|---|---|
| Record | `LAW.md` §3; `RECORD.md` §2 "Avalanche as the law states it"; rows `rows.jsonl` |
| Measured | residues 0 and 1 miss **6/6**; `uncached` 8,013 / 8,014 against a predicted 13 / 14; recomputed today: **22** residue-{0,1} rows (11 + 11), `cached_tokens: null` in **22/22** |
| Not-rounding control | an *identical repeat* at P1 = 8064 also reports no hit ⇒ the entry is genuinely absent on that instrument |
| Instrument dependence | `POST /generate` `meta_info.cached_tokens` reads `cached = 8,000` at P1 = 8064 and bills `64 + L`; `usage.prompt_tokens_details` reads `null` and bills `P1 + L`. `RECORD.md:114` (C1) records the 5.2× between the readings as **first withdrawn, then UNDECIDABLE**; `orchestration/units/RECON-C1.md` shows the rows fit both residue-0 readings |
| Command | `LAW.md` §"Reproduce" pins `rows.jsonl` and `experiments/miss-law/law_fit.json`; the `/generate` reading is `orchestration/handoffs/BILL-AUDIT.json:evidence.avalanche_corrected` |
| Status | **MEASURED** (class change on both instruments) — **the billed magnitude is instrument-dependent** |
| Role in F | the paper's headline discontinuity, printed with the instrument dependence in the same paragraph. **Never** printed as "8,013 is the cost" or as "both instruments agree" |

### E-03 — It is residue, not position

| field | value |
|---|---|
| Measured | **11/11** misses at P1 ∈ {2048, 2049, 4096, 4097, 6144, 6145, 7681, 7936, 7937, 8000, 8001} — recomputed today, 11/11 with `cached_tokens: null` |
| Block indices | **six**: #32, #64, #96, #120, #124, #125. `LAW.md` §3 prose still says "four separate block indices"; its own list, and the rows, say six (correction 3 in [`README.md`](README.md)) |
| Decisive pair | `P1 − 64` preserves the residue: 7936 (residue 0) misses exactly like 8000 |
| Status | **MEASURED + RECOMPUTED** |
| Role in F | kills the "it is just a page boundary" reading; supports the intervention |

### E-04 — Payload size does not interact with the residue

| field | value |
|---|---|
| Measured | P1 = 8005 (r = 5): n = 16/32/64/128 → 33/49/81/145, each exactly `r + L`; P1 = 8064 (r = 0): n = 64 → 8,140, n = 128 → 8,204 (both `P1 + L`) |
| Status | **MEASURED** (2 reps each) |
| Role in F | the sentence the design rests on: *what you append is nearly free; where you append is not* |

### E-05 — vLLM pays one whole extra block: `(P1 mod B) + B + L`, B = 1056

| field | value |
|---|---|
| Measured | 18 residues × 3 reps; residual exactly `+1056` on the `+0` model, i.e. the `+B` model fits. Recomputed today: **86** fit rows, residual `{−1056: 1, 0: 85}` — 85/86 exact, the one miss the known `vllm B Bprobe-400 rep 0` row (`RECORD.md` C8 residual detail) |
| Cross-engine tax | append ≤ `64 + L` on SGLang vs ≤ `2112 + L` on vLLM; recorded as "~33× more overhead" (2112 / 64 = 33) |
| `B` resolved, not requested | vLLM units **1,088 / 1,056 / 2,096** across three configs, each identified (no row a multiple of the others) — `CLAIMS.md` C55–C57 |
| Instrument caveat | this build returns `prompt_tokens_details: null` on **every** request, so cached tokens come from the delta of `vllm:prompt_tokens_cached_total`, and `vllm:prefix_cache_hits_total` is a token counter on this build too — **the two agree trivially and the numbers rest on one server-side quantity** (`LAW.md` §1). Corroborated independently by a server-TTFT step (+188.9/191.2/195.6 ms per block crossing against a 0.171 ms/token cold-prefill slope, `RECORD.md` §2) |
| Status | **MEASURED**, single-counter caveat attached |
| Contradiction | the ledger's uniform "avalanche = whole prefix" model is right for vLLM and **wrong for SGLang** (`RECORD.md` C2). Carry the engine, never a pooled "append tax" |
| Role in F | the generality sentence and the reason the rule is per-engine. Kill criterion: if `+B` fails independent re-derivation, drop the 33× ratio entirely |

### E-06 — The instrument reads both ways

| field | value |
|---|---|
| Controls | WARM identical repeat: `cached` 8,000 / 8,053 = **99.3 %**; COLD broken prefix: `null` on both requests; 8/8 fresh-nonce prefixes `null`. `/flush_cache` never called, no restart |
| Status | **MEASURED** |
| Role in F | the paper's own red-before-green evidence; also cited by S as the positive example of a control that can report the opposite |

### E-07 — The two-token rule (intervention)

| field | value |
|---|---|
| Record | `LAW.md` §7 |
| Content | never let `P1 mod B ∈ {0,1}`: pad 2 tokens (1 if residue 1) *before* appending; otherwise batch fetches (K appends ≈ `K·B/2`, merging two saves ~32 tokens on SGLang / ~1,584 on vLLM); size payloads by body tokens, not append count |
| Status | **INFERENCE from MEASURED** — arithmetic on the law, not an independently measured intervention. Its saving is positive under **every** reading: ≈64 tokens on the counter reading, ≈`P1 − r` on the null reading [`README.md` correction history; `2026-11-04-candidates.md` corrections table] |
| Contradiction a reviewer will raise | `MANUSCRIPT.md` §8a: "aligning to the grid costs more than it recovers" (pad 94.89 mean vs 74.06 recovered). **Both are true and they price different pads**: §8a prices a 64-token *page-recovery* pad under one workload; the residue rule is a 2-token *cliff-avoidance* pad fired only at residues 0/1. The paper must draw that boundary explicitly (kill criterion (d) in `N1-residue-law.md`) |
| Role in F | §"What a client should do" — the actionable close, stated as a rule, not as a measured win |

### E-08 — The sign flip was the cold arm, not the block boundary

| field | value |
|---|---|
| Measured | the crossover cells reproduce degenerately (`cached = 0` throughout): 2-fetch +44.6 % (published +44.9 %), 6-fetch −95.7 % (published −95.6 %); boundary term ≤ `6 × 63 = 378` tokens against a 10,244-token swing = **≤ 3.7 %**; warm, the law predicts `cached = floor(P/64)·64` in **57/60** rows |
| Source | `LAW.md` §6; `experiments/agentic-lazy/crossover/RESULTS.md:52,54` |
| Status | **MEASURED** (with the 6-fetch rows not on disk — the published aggregates are quoted, and `LAW.md` says so) |
| Role in F | the refuted rival explanation. Also the reason the paper's cost model is about appends, not about fetch count |

---

## 2. The prototype family (`experiments/ptr-engine/`)

### E-09 — The index/bodies ratio, and what it is not

| field | value |
|---|---|
| Measured | 12 bodies / 30,000 B behind a **447 B** index → **67.1141×** (30000/447); compact index **383 B** → 78.3×, i.e. the ratio is an index-encoding choice, not a constant; index sha256 `e08700c9…9bd2` reproduced in 2 processes and 2 roots; 7 named negative-control codes |
| Source | `RECORD.md` §1; `orchestration/handoffs/V-ENGINE-P0.json:checks[2],[3],[5]` |
| Status | **MEASURED** — **bytes only**; not tokens, not cost, not latency |
| Contradiction | the record's own reviewer caveat: `SPEC.md`'s "enforced structurally" was overstated; it is an API surface property plus a behavioural sweep, now backed by 2 issued-ref tests that a registry-backed `recover()` fails |
| Role in F | one sentence in the design section, with the unit stated; never in the results table |

### E-10 — Capability, refusal, and discrimination (the quality arm)

| field | value |
|---|---|
| Design | pre-registered before the first request (`quality/PREREG.json:registered_before_any_request = true`); question fixed: which audit code belongs to `lumen`; expected `AUD-4417`, present only in `@knowledge:k01`; 12 items × 9,000 B; 4 turns × 3 reps × 4 arms; 115 rows |
| Measured | **A** warmpool **3/3**; **B** cap-3 **0/3** with **33** `PTR_STORE_MISS` refusals (11/rep, **0 silent empties**); **C** destructive compaction **3/3** (1 body 9,000 → 273 B); **D** no-body control **0/3**, 0 bodies resolved, answering `756741be` (first 8 hex of `k12`'s digest, echoed off the index) |
| Leak proof | offline, before any request: index sha256 `e81ba025…31d5`, 458 bytes, 12 lines, no `AUD-`, no `lumen`; re-derived by `V-QUALITY-ARM.json:checks[2]` |
| Status | **MEASURED** |
| What it does **not** license | generality past 12 items / 4 turns / one model; anything about a corpus where the *fact-bearing* body is the compacted one (never occurred); and **no token figure at all** (E-11) |
| Role in F | the design's quality evidence, stated as *capability + refusal discipline*, never as "quality-neutral" |

### E-11 — The quality arm's token column is refuted — do not carry

| field | value |
|---|---|
| Refuted | `RESULTS.md:174`'s telescoping identity (stored value 32,401 vs claimed 34,201; residual **+17,193**); `:175`'s "difference is the T1+T2+T3 completions" (those total **6** tokens); `:150`'s "0 avalanches" (C rep2 turn 4 is residue 1, `avalanche True`, `uncached 34,190`, billed 49,594) |
| Root causes | `quality/runner.py` set `L = prompt_tokens + FRAMING` (the whole prefix passed off as the append) — BILL-AUDIT's replay of arm A measured **123** tokens where the arm claimed ~7,087 (**57.6×**); the request-row residue is computed from `templated_prompt_tokens % 64`, which differs from measured `prompt_tokens % 64` in **48/48** rows |
| Status | **REFUTED** (by `V-QUALITY-ARM`, overall `partial`) |
| Role | cited in F only as a methods footnote ("the arm's cost column is not a bill; a corrected runner aborted on its own alignment guard, `quality/rerun-corrected.log:16`"); it is S's case evidence |

### E-12 — The equal-information baseline points against the design

| field | value |
|---|---|
| Measured | `C0-EQUALINFO`, `occamy-1.0-NVFP4`, 100 requests (90 design + 10 instrument-repair), 100 rows, 0 errors: equal-information baseline **C0F mean 1,911** uncached vs pointer arm **R mean 3,524**; ratio **1.8441** |
| Source | `orchestration/handoffs/C0-EQUALINFO.json:evidence`; quoted in the protocol §2 P2 |
| Mechanism named in the source | "each resolve appends a body, so the prefix changes and does not cache" |
| Status | **MEASURED** |
| Role in F | **the honest adversarial result**: a pointer design can be *more* expensive at equal information. In F this is the motivation for the append-shaped design (batch fetches, align, don't re-append per resolve), not an inconvenient footnote. It is also the reason F cannot claim the design is cheaper without the comparative |

### E-13 — Multi-turn cost facts owned by the manuscript (cite, do not re-derive)

| claim | value | owner |
|---|---|---|
| E1 fork vs summarise | median paired **+4,774.25**, CI **[193.5, 4,868.25]**, **15/18**, sign p **0.007538**; excluding event-index 2: 15/15, CI [4,677.5, 4,901.5], p **6.1e-05**; 195 requests / 228 rows / 18 pairs | `experiments/context-cache/cells/E1/e1_analysis.json`; licensed sentence `orchestration/STATUS.md` §7.3 |
| E2 steady split | 37 steady turns: **1,268.9 = 456.2** tail + **34.3** boundary + **778.4** re-prefill, residual **0.0**, additivity `diff 0` (Σ 46,949 both sides); shares 0.3595 / 0.6134 | `experiments/context-cache/cells/E2/analysis.json` |
| E4 / E4R boundary | rep-1 `cached == 0` in **45/45** boundary rows vs **0/40** non-multiples, Fisher **3.4646074215706565e-25**; rep-3 `L−64` **40/40**, `L` **0/40**, CP95 [0.9119, 1.0] | `orchestration/STATUS.md` §7 (VE4/VE4R) |
| LIVE-MEAS horizon | pooled R/A **1.2987865784558326**, t95 **[1.2147, 1.3828]**; t1–40 mean **1.7308** [1.6481, 1.8135]; t41–80 mean **1.0122** [0.8761, 1.1483] | `experiments/context-cache/cells/LIVE-MEAS/analysis.json` |
| C44 | break cost E/F **1.0384615**, gross 1,728.0 / 1,664.0, 2/6 within 10 %; `u15_1_700x_survives_decomposition = False` | `CLAIMS.md` C44 |
| C53 | B/A **6.744331504** [4.04542649, 9.44323652]; C/A 1.105174403; A 123,240 / 102,912 / 20,328, B 123,256 / 0 / 123,256, C 19,792 uncached; 8 × 8 | `CLAIMS.md` C53 |
| C54 | resident 30–31 docs = 258,035–266,636 tokens = 0.1592–0.1645 of 1,620,892 at 1.501724× pressure | `CLAIMS.md` C54 |
| C62 | compaction at a real boundary: **+134.6 … +747.2** uncached/turn on average after it; per turn **−927 … +5,473**; 2,780 rows, 18 compactions, 12 arm-instances | `CLAIMS.md` C62 |
| C64 / C64a | P0 **541.07** / P1 **528.64** / P2 **549.49** uncached per turn; P2−P1 **+20.8429** [10.014, 31.586], 70 pairs, ratio 1.039427; padding **costs** | `CLAIMS.md` C64 |
| C40 / C41 | immediate-repeat misses only at `L ≡ 0 (mod 64)`, 5/5 vs 0/15, Fisher p 3.0593e-07; wider pool 35/35 vs 0/15, p 4.4428e-13 | `CLAIMS.md` C40, C41 |

**Status: MEASURED, owned by `papers/context-cache/`.** F cites these; it does not recompute, re-derive
or restate them. Two consequences the seed must respect: (i) the estimator for C53 is the unweighted
mean of eight per-fan-out ratios, and the ratio of totals is **6.0633608815** — recomputed today;
never print 6.744 as `123,256 / 20,328`; (ii) C62's per-limb band is the range of *twelve arm means*,
not a per-turn range.

---

## 3. The instrument-failure family (the grid, and what it proves)

### E-14 — The gen-6 grid: spent, and `not_adjudicable`

| field | value |
|---|---|
| Census | 16 cells; **6 usable** (lease-reopen, pointer-stable); 8 stamped `[]` (no treatment marker fired); 2 with **no manifest** (`exit 4`) |
| Requests | 1,270 rows across the 16 cells, equal to the ledger delta `1,321 → 2,591` ⇒ **79.375 / cell**; highest single cell **96** |
| H1 | pointer-stable n = 48, lag-1 r **0.2949**, n_eff **26.1356** < 60 ⇒ `not_adjudicable_floor`; p50 **156.151** [146.306, 291.926]; **p95 refused at n = 48** (floor 60). lease-reopen n_eff **60.946**, p50 198.395 [130.843, 270.899] |
| Collapse | **288** turn rows on disk in the usable cells → **96** analysed, `dropped_duplicate = 192`, because `tools/run_grid_report.py:235` dedupes on `(arm, rep, turn_index)` and every cell wrote `rep=1` |
| H2 | frozen rule is C-vs-A; **arm A has 0 usable cells** ⇒ `not_adjudicable`. Within-arm only: pointer-stable cached 5,395.09 vs uncached 355.62 tok/turn (n = 364); lease-reopen 1,497.85 vs 332.28 (n = 184) |
| H3 | the grid's `x/12`, `x/9`, `answered_ratio` are **placeholder zeros**, verbatim — not measurements; `grade_v5` has no admissible emitter for the gate |
| TVS | **UNDEFINED**: `n_verified_success = 0` arm-level and 0 at first checkpoint |
| Overall | **`not_adjudicable`** |
| Command | `experiments/ptr-engine/tools/grid2_final_report.py`; machine twin `measure/GRID-2-FINAL.json` (read for this dossier: `collapse.turns_on_disk_in_usable_cells = 288`, `turns_analysed = 96`, `dropped_by_selector = 192`, `n_eff` 26.1356 / 60.9463) |
| Status | **MEASURED** (the failure), **not** a result about H1–H3 |
| Role | F: why its comparative is unmeasured; the price it puts on a re-run. S: one case of an instrument that could not say yes |

### E-15 — The quality path cannot say yes (`PATH-CANNOT-SAY-YES`)

| field | value |
|---|---|
| Record | `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`; **0 requests** |
| Mechanism | the fixture's v3 contract requires an `ANSWER: <value>` line (`answer_marker.required`), `score_longrun.py` never reads `answer_marker` (0 grep hits, also in `grade_v2.py`), and all three checkpoints lack a `match` key, so they default to `mode = "exact"` and compare the **entire turn content** (`score_longrun.py:814`, `:174-176`) |
| Truth table | `pos-full` → `verified_success false`, 0/3, flips 7 checks (`cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`); `neg-one`, `neg-marker`, `neg-truncated` → the **identical 7** (indistinguishable); `pos-exact-only` → **true**, 3/3, TVS 22,396 — the only shape `score_longrun.py` accepts |
| Mutual exclusivity | `grade_v2.py` requires prose (a line ending `. ! ? )` carrying the number, `GRADE-V2 R1b`), so the only content the scorer accepts fails v2; on v2, `pos-exact-only` scores **3/10** while `neg-marker` and `neg-truncated` score **10/10** |
| Fixture | `longrun/tasks-v3/runtime-v3/LR-01.v3.json`, sha256 `07abab0b…399bd3e0b` |
| Status | **MEASURED** (offline), **REFUTES** every quality arm's pass through this path |
| Consequence | every quality number from any arm — including the protocol's E2 `verified_success` limb — is **void** until a fixture/grader fix passes a red→green control. The fix is an owner decision (checkpoint `match: "contains"` on the marker line, or a structured `answers` field the scorer reads), **not a patch to be made silently** |
| Role | the Stage-0 gate for F's comparative; S's centrepiece |

### E-16 — Four defects in one live grid, and the rule each one implies

| defect | measured consequence | rule it implies |
|---|---|---|
| treatments never fired | 8 cells `usable_for: []`; `evicted_turns = 0`, `digest_rows = 0` over 48 turns; `tasks-v6/LR-01.v8.json` prices its wall from *declared* padding (10,616) while live base is 5,628–6,139 and growth 41–98 tok/turn ⇒ turns-to-wall 73–113 > 48 | a cell is usable only if its treatment predicate is non-zero on its own rows |
| replicate collapse | 288 rows → 96, `dropped_duplicate = 192`; also why p95 is refused | unique `(arm, rep, cell, turn_index)` key, `rep` in `run_id`, pre-analysis row-count assertion |
| absent stamp admitted | `longrun/analyze_stats.py:749` keeps a manifest-less cell and prints it `unstamped`; the two `exit 4` cells were excluded **by name** | absent stamp ⇒ excluded by computed rule, never by name |
| cap-gate under-count | `projected_requests` prices 96 while a tools-on turn bills k+1; the gate refused the 97th | budget reconciled per arm before the first call; a cell that hits its cap mid-run is `INVALID-INSTRUMENT`, not partial data |
| (5th, writer-side) | nested `rows_path` vs the reader's top-level expectation — repaired in `longrun/cell.py` (`experiments/ptr-engine/longrun/cell.py`), outside `HARNESS_FILES`, therefore not a new generation | a reader/writer field mismatch is an instrument fault even when the fix is small |

| Status | **MEASURED** |
|---|---|
| Role | S's case series; F's validation gates (it is why `VALIDATION-ROADMAP.md` stage 0 exists) |

### E-17 — A bill that was not a bill, and a census that was not a census

| field | value |
|---|---|
| C3 | the quality arm's billed column is a recomputation, not a measurement: the model field that would make it one — `usage.prompt_tokens_details.cached_tokens` per turn — never reaches `rows.jsonl` although `experiments/ptr-engine/quality/runner.py:585-596` reads it; `billed_tokens_measured == billed_tokens` is true only by recomputation at `experiments/ptr-engine/quality/runner.py:688` |
| C10 | the arm's residual is **+17,193** against a claimed exact identity; its "completions explain it" claim covers **6** tokens |
| Ledger | 1,270 grid requests **equal** the ledger delta `1,321 → 2,591`, so the census's billing column is a measurement; and `2591/16 = 161.9` charges the grid for its 1,321-request baseline — declined |
| Status | **REFUTED** (C3/C10), **MEASURED** (ledger identity) |
| Role | S: a *plausible* number produced by a self-consistent recomputation is still not a measurement. F: the reason every F figure names its instrument |

### E-18 — Verdict vocabulary is load-bearing

`not_adjudicable` / `not_adjudicable_floor` mean **the instrument failed**, not that the hypothesis
lost. `UNDEFINED` is a missing denominator, never zero. `UNFUNDED` is a budget fact, not a negative
result. `INVALID-INSTRUMENT` is an exclusion, computed from the stamp. **RECORD** (workspace rule,
`AGENTS.md` §4, `docs/PREREG-ARM-RUN.md`) — role: F and S both print these strings and define them
once.

---

## 4. The manuscript and its uncited batches (`papers/context-cache/`)

### E-19 — The drafted paper, as it stands today

| field | value |
|---|---|
| Manuscript | `papers/context-cache/MANUSCRIPT.md` (1,214 lines); title "Where the cache win lives: placement, truncation, and the silent cost of compaction"; sealed 2026-10-24 21:39 |
| Package check run today (2026-11-06) | `.venv/bin/python papers/context-cache/verify_package.py` → `PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none` (exit 0) |
| Recorded count | `RUN.json` `verification/synthesis_recompute.claims = 63`, and the N4 brief quotes "COVERAGE 63" — a **stale count** relative to today's ledger (correction 2 in [`README.md`](README.md)) |
| Scope, from its own abstract | a measurement of **serving-stack economics and context placement**; explicitly **not** a claim about model quality; accuracy is a sensitivity check; compaction policies run an offline stub summariser |
| Status | **RECORD** (package integrity verified today) |
| Role | the 4th, in-progress paper. F cites it and must not duplicate it |

### E-20 — Seven uncited cell batches (the fold N4 proposes)

| cell | rows on disk today | the brief's claim | check |
|---|---:|---|---|
| `experiments/context-cache/cells/E1` | 264 | 18 paired events, 195 requests | `e1_analysis.json` confirms 195 requests / 228 rows / 18 pairs |
| `experiments/context-cache/cells/E2` | 222 | split identity | confirmed (§E-13) |
| `experiments/context-cache/cells/E3` | 264 | not read for this dossier | — |
| `experiments/context-cache/cells/E4` | 395 | 220 requests / 220 rows | `STATUS.md` §7 |
| `experiments/context-cache/cells/E4R` | 360 | 180/180 rows | `STATUS.md` §7 |
| `experiments/context-cache/cells/LIVE-MEAS` | 3,791 | 960 rows pooled | `analysis.json` recomputed here |
| `experiments/context-cache/cells/M1-M` | 107 | cached 512/2,560/5,184/8,512 at edited items 10/50/100/165 | not re-read |
| **total** | **5,403** | brief says **1,892** | **does not reproduce** |

| field | value |
|---|---|
| Uncited? | yes — `grep -rl 'cells/E1\|cells/E2\|cells/E3\|cells/E4\|cells/E4R\|LIVE-MEAS\|M1-M' papers/context-cache/` returns only `RUN.json` |
| Status | **RECORD** for the *gap*; the "1,892 rows" figure is **WITHDRAWN as stated** (use 5,403 `.jsonl` lines, or cite per-cell) |
| Role | a *precondition*, not a paper concept: this is the N4 fold, and it is what makes the manuscript submittable. It belongs to `papers/context-cache/`, not to the seed |

---

## 5. The prospective bounded-context programme (Consonance BRCV)

### E-21 — A design and a protocol, with zero measurements

| field | value |
|---|---|
| Documents | `research/next-candidates/consonance-bounded-context-report.md` (356 lines, **PASS** after one repair) and `consonance-bounded-context-evaluation.md` (517 lines, **PASS** after one repair); both rechecked by units that authored nothing they graded |
| Design (BRCV) | deterministic stable instruction/tool prefix; bounded recent verbatim working set; authoritative versioned external records fetched on demand through deterministic pointers (`id + revision + sha256 + range`); old tool output **masked before any summary**; checkpoint only when a forecast pays for its cache break |
| Protocol content | five paired arms (A full-transcript, B transcript-compact, C masking-no-fetch, D bounded-context-fetch at 2 req/turn, E oracle-evidence), positive and negative controls with thresholds, a worked abstention hypothetical, eleven void conditions |
| What was **not** done | no experiment, no model call, no request, no Rust kernel, no omp interface. Ledger unchanged at 2,591 / 1,729 |
| Budget arithmetic (protocol, not a result) | CON-E1 sweep **36 of ≤60**; CON-E2 **123** = one-rep descriptive, **369** adjudicable, **450** with the 12-checkpoint fixture; comparative **7,560** vs 1,729 ⇒ **4.37× ⇒ `UNFUNDED`**; pilot **≈185** |
| Status | **PROPOSED-UNTESTED** — every number in the protocol is protocol arithmetic |
| Role in F | the falsifiable claim structure and the arm design. F **may not** describe BRCV as validated, may not call the comparative "supported", and must keep the protocol's non-results vocabulary |

### E-22 — What the protocol already refuses to score (and F must inherit)

| class | status in the authored fixtures | treatment |
|---|---|---|
| exact fact recovery | present, all 6 fixtures | usable |
| changed decisions | present as `repair`, 6/6 | usable |
| negative constraints | 3 per fixture, 6/6 | usable |
| multi-hop retrieval | **MISSING** — every checkpoint is a single-source pointer | `UNAVAILABLE`, never scored as success, no fixture fabricated |
| unavailable / stale / revoked source | **MISSING** | `NOT_OBSERVED` until a fixture exists |
| abstention | the scorer cannot express it: case-insensitive grep for `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` returns **0 matches**; the four check kinds are `artifact` / `fact` / `constraint` / `repair` | a **Stage-0 prerequisite** with its own red→green control |

| Status | **RECORD** (protocol) |
|---|---|
| Role in F | the honest "what this design cannot yet be tested on" subsection; also the reason F's validation roadmap begins with a fixture/scorer change |

---

## 6. The filed-publication history (record, not evidence)

| paper | venue | identifier | verification note |
|---|---|---|---|
| `encoder-crossover-190` | Zenodo + Preprints.org + TMLR | `10.5281/zenodo.23463944`; forum `L9GcDGb2fr` | Preprints accepted (editor-reported; HTTP 403 on verification) |
| `replay-record-not-decision` | Zenodo + Preprints.org + TMLR | `10.5281/zenodo.23482511`; forum `U2WjJMH0EK` | Preprints **not** accepted |
| `gated-read-batching` | Zenodo + Preprints.org + TMLR | `10.5281/zenodo.23483314`; forum `q72ZB9ZMqy` | Preprints accepted (editor-reported) |
| filed 2026-10-19 | upload source of truth | `submission-kit/` (9 sha256-verified files) | upload from the kit, never from the paper trees |

**Standing rule** (`strategy/SUBMISSION_RECORD.md:19`): **no filing may assert this work was never
published.** **Status: RECORD.** **Role:** the seed's introduction may not present any of the three as
new work, and the flagship's related-work section names them.

---

## 7. Contradiction register — the six a reviewer will find, and the sentence that survives each

| # | contradiction | what is true | the sentence F may print |
|---|---|---|---|
| 1 | the cliff's magnitude across instruments | the class change is measured on both; the **billed magnitude** is not: `64 + L` (counter field) vs `P1 + L` (null field); the 5.2× is **UNDECIDABLE** | "At residues 0 and 1 the entry is absent on both instruments; what each instrument then bills differs by read field, and the record marks the ratio undecidable." |
| 2 | `L − 64` recovery vs non-reproduction | both true, **different shapes**: recovery is on the **second byte-identical repeat** (E4 rep-2 `cached = 960` ×20; E4R 40/40), while `LAW.md`'s 7,936 row is a **fresh cold prime** with a varying nonce | "A recovered repeat hits at `L − 64`; a fresh prime at residue 0 does not. The law is about the first append onto a primed prefix." |
| 3 | C9 / the fold bucket forbids a "residue→avalanche law" | C9 is **superseded only as a bar to this law**: the constant-nonce design separates residue from `P1` (186/186 in-band, 11/11 invariant across bands). C9 still governs HARVEST's 378-row cell table (`ADOPTION.md:38`) | "Residue was not separable from prompt length in the earlier design; a constant-nonce sweep separated them." |
| 4 | §8a: "aligning costs more than it recovers" | true for a **64-token page-recovery pad**; the residue rule is a **2-token cliff-avoidance pad** fired only at residues 0/1 | "Two different pads. Padding to a grid costs; avoiding the class change is worth more than it costs." |
| 5 | E1 vs C44 | different estimands (paired `uncached(E) − median(neighbours)` on U4 with `pointer`/`pointer_fork`, budget 8000, vs `uncached − (prompt % 64)` on `endtoend.json` with `NAIVE_APPEND`, budget 8192); both reproduce. All six G1 break events have `cached_tokens = 0` on both arms while E1's summarise arm holds 4,352 against the fork arm's 64 — so "which rewrite doesn't matter" is **not** what the rows support [`INFERENCE`] | the manuscript's own scope sentence; F cites both and asserts neither |
| 6 | 1.700× alone vs 1.2988 [1.2147, 1.3828] | the **pair** is supported: 1.700× is a 40-turn figure, 1.2988 the 80-turn pooled ratio (df = 2) | print both, or print neither |

---

## 8. What is measured, what is inferred, what is proposed — the one-paragraph summary

**Measured, on this rig, with rows on disk:** the per-append tail law on two engines including one
extra block on vLLM (85/86 rows; one known miss); the residue-{0,1} class change and its
residue-not-position control (11/11 across six block indices); payload independence at every residue;
the instrument reading high (99.3 %) and low (null) on demand; a capability result (3/3 through one
`fetch`), a named-refusal result (33/33), and a discrimination control (0/3) for the prototype; and,
in the manuscript's own cells, the multi-turn cost facts F cites (E1, E2, E4/E4R, LIVE-MEAS, C44,
C53, C54, C62, C64a).

**Inferred from measured inputs:** the two-token rule's saving; the multi-append extension of the
law; every request estimate in [`VALIDATION-ROADMAP.md`](VALIDATION-ROADMAP.md) traces to the
protocol's own arithmetic and is labelled as such.

**Proposed and untested:** BRCV itself; the five-arm comparative; every envelope (E1/E2) of the
Consonance protocol; the claim that an alignment-aware bounded context is *cheaper at equal
information* — which the one equal-information measurement currently contradicts (1.8441×).

**Refuted, and not to be carried:** the quality arm's token column (57.6× understatement; +17,193
residual); "0 avalanches" for that arm; "162 requests/cell"; "1,892 uncited rows"; "63 claims" as
today's count; the 5.2× as fact; absence as a cross-instrument claim; 8,013 as a universal re-bill.
