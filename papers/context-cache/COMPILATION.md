# COMPILATION — the living index of findings, evidence and publication readiness

**Purpose.** One row per finding, so a later compilation pass does not re-read 3,000 lines to learn
what may be printed and what may not. Seeded from `papers/context-cache/CLAIMS.md` (69 claim ids),
`papers/context-cache/FOLD-PROPOSAL.md` (buckets + drafted C75–C81), `experiments/ptr-engine/RECORD.md`
(the C-series and its contradictions) and `orchestration/GAPS-INVENTORY.md` (48 gaps). No row here is
new analysis: every row cites a file and line that exist.

**Rebuild.** `python3 experiments/ptr-engine/tools/build_compilation.py` (stdlib only, no network).
It re-derives the *claim* and *status* columns from disk and rewrites the `build:` stamp below.
Never hand-edit a status: the next pass overwrites it.

**Evidence strength** — `MEASURED` (a row file supports it) · `RE-DERIVED` (a unit recomputed it from
rows) · `VERIFIED-OFFLINE` (an independent verifier reproduced it) · `WITHDRAWN` (refuted, kept for
traceability) · `DRAFTED` (written, not ratified) · `UNSUPPORTED`.

**Publication status** — `READY` · `READY-WITH-LIMITATION` · `NOT-PUBLISHABLE` · `BLOCKED-LIVE` ·
`BLOCKED-OPERATOR`. Status is *derived*: strength + whether every claim id resolves in `CLAIMS.md` +
a marker prefixed to the last column — `[lim]` = limitation travels with it, `[live]` = needs a live
cell, `[op]` = needs an operator decision. A measured row with no claim id is `BLOCKED-OPERATOR`:
it is not citable until a claim exists (gap #11 is the precedent).

<!-- build: ROWS 87 | CLAIMS 69 | READY 60 | WITHDRAWN 7 | ROWFILES 3 | MEASURED 2 | INVALID 1 -->

## A. Rendering and run integrity

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C01 | POINTER and NAIVE_APPEND render byte-identically, 760/760 cells, 0 bytes differing | C01 | CLAIMS.md:77 | VERIFIED-OFFLINE | READY | a second rebuild's replay |
| C02 | U5 ran clean: 760 rows, 0 non-200, 190 cases, 4 (depth, condition) pairs | C02 | CLAIMS.md:78 | RE-DERIVED | READY | — |
| C03 | deep summarise and deep fork prompts are identical; 570 distinct prompt digests over 760 rows | C03 | CLAIMS.md:79 | RE-DERIVED | READY | — |
| C13 | U4's driver used one renderer for every arm and never imported the pointer fork | C13 | CLAIMS.md:80 | RE-DERIVED | READY | a fixed-library re-run of U4 |
| C14 | U4 provenance is 438 batch + 13 probe = 451 requests in files; the card's 454 adds 3 smoke sends | C14 | CLAIMS.md:105 | RE-DERIVED | READY | — |
| C36 | U9 resolved six lengths from 139 requests, 0 non-200, 0 errors | C36 | CLAIMS.md:137 | RE-DERIVED | READY | — |

## B. Fan-out placement

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C04 | U4b arm totals and per-branch cached tokens, uncached A 4,648 / B 15,400 / C 4,648 | C04 | CLAIMS.md:86 | RE-DERIVED | READY | — |
| C05 | branching late reproduces the win with no pointer machinery: U4b B/A = 3.3133 | C05 | CLAIMS.md:87 | RE-DERIVED | READY-WITH-LIMITATION | [lim] effect size superseded by C53 |
| C06 | the 3.3133 is not a floor: the counterfactual 5.3922 sits between it and G5's 6.744 | C06 | CLAIMS.md:88 | RE-DERIVED | READY | — |
| C53 | G5 race-free fan-out: B/A = 6.744 [4.045, 9.443], C/A = 1.105, 8 fan-outs x 8 branches | C53 | CLAIMS.md:185 | RE-DERIVED | READY | — |
| C64 | grid-aligned padding costs +20.84 uncached tokens/turn and recovers 78% of its pad | C64 | CLAIMS.md:264 | RE-DERIVED | READY | a second corpus size |

## C. Compaction and content loss

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C07 | MCQ accuracy barely moves across conditions: shallow 66.3%, baseline 72.1%, summarise 70.5%, fork 69.5% | C07 | CLAIMS.md:94 | RE-DERIVED | READY | — |
| C08 | no accuracy delta is significant and none reaches 5 points (max 2.632) | C08 | CLAIMS.md:95 | RE-DERIVED | READY | more samples per case |
| C09 | a gold line planted mid-history is retained 190/190 by baseline and 0/190 by both compacted arms | C09 | CLAIMS.md:96 | RE-DERIVED | READY | — |
| C10 | the 90% agreement flag fired; the identical-prompt arms agree only 91.6% | C10 | CLAIMS.md:97 | RE-DERIVED | READY-WITH-LIMITATION | [lim] the floor limits any accuracy contrast |
| C11 | U4's paired break costs are identical between arms and the permutation test is degenerate (p = 1.0) | C11 | CLAIMS.md:103 | RE-DERIVED | READY | — |
| C12 | the only three nonzero deltas are one 64-token chunk of salt rounding | C12 | CLAIMS.md:104 | RE-DERIVED | READY | — |
| C15 | U13 gives fork a distinct content-addressed marker: b812c99d vs dc591b7e, +175 chars | C15 | CLAIMS.md:107 | RE-DERIVED | READY | — |
| C16 | under the fixed library the two arms differ from turn 12 onward (body equal 11/44 turns) | C16 | CLAIMS.md:106 | VERIFIED-OFFLINE | READY | — |

## D. The decisive comparison (U15)

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C17–C20 | the four arm bills: R 51,172 / F 47,080 / A 30,097 / C 30,523 uncached tokens | C17 C18 C19 C20 | CLAIMS.md:113-116 | RE-DERIVED | READY | — |
| C21 | A beats R by 1.700x on total uncached tokens; R and F are within 8.7% | C21 | CLAIMS.md:117 | RE-DERIVED | READY-WITH-LIMITATION | [lim] causal reading superseded by C44 |
| C22 | only 7.8% of R's excess is break cost, 92.2% is steady state | C22 | CLAIMS.md:118 | RE-DERIVED | READY | — |
| C23 | turns 19-34: R re-prefills 1,659.9 of a 5,811.9 prompt, A 722.9 of 13,146.9 | C23 | CLAIMS.md:119 | RE-DERIVED | READY | prefix-diff instrumentation (gap 24) |
| C24 | the break-only counterfactual would score 1.068x, not 1.700x | C24 | CLAIMS.md:120 | RE-DERIVED | READY-WITH-LIMITATION | [lim] superseded for break cost by C44 |
| C25 | A never shrinks: its prompt grows 1,186 to 19,583 tokens (16.5x) | C25 | CLAIMS.md:121 | RE-DERIVED | READY | — |
| C26 | only the rewriting arms break, at turns 18 and 35 | C26 | CLAIMS.md:122 | RE-DERIVED | READY | — |

## E. Latency

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C27–C32 | hit/miss TTFT at six lengths: 208.7/86.4 ms at 1,024 tokens to 7,541.9/231.6 ms at 31,415 | C27 C28 C29 C30 C31 C32 | CLAIMS.md:128-133 | RE-DERIVED | READY | lengths above 31k (gap 26) |
| C33 | the hit/miss ratio falls as L^-0.7837 (r2 0.9962) | C33 | CLAIMS.md:134 | RE-DERIVED | READY | — |
| C34 | OLS length terms differ by 51.67x; a hit still costs about 4.66 us/token | C34 | CLAIMS.md:135 | RE-DERIVED | READY | — |
| C35 | all 42 paired deltas are positive, sign p = 0.0078 one-sided | C35 | CLAIMS.md:136 | RE-DERIVED | READY | — |

## F. The 64-token grid and the boundary

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C37 | for byte-identical repeats the grid holds exactly: 44/44 warm repeats, 44/44 residual 0 | C37 | CLAIMS.md:143 | RE-DERIVED | READY | — |
| C38 | for appends it fails on every row: 372/372 deviate, residual 832-7,936, median 1,792 | C38 | CLAIMS.md:144 | RE-DERIVED | READY-WITH-LIMITATION | [lim] scope to 931-12,393-token histories (gap 39) |
| C39 | U2 and U4 share no rows, so the two law statements describe different data | C39 | CLAIMS.md:145 | RE-DERIVED | READY | — |
| C40 | only lengths that are a multiple of 64 miss on the immediate repeat (1,024 and 1,088) | C40 | CLAIMS.md:146 | RE-DERIVED | READY-WITH-LIMITATION | [lim] n = 5 per length (gap 27) |
| C41 | the boundary split is not chance: 10/10 vs 0/15, Fisher p = 3.0593e-07 | C41 | CLAIMS.md:147 | RE-DERIVED | READY | — |
| C42 | time and interleaved traffic do not repair the boundary miss | C42 | CLAIMS.md:148 | RE-DERIVED | READY | — |
| C43 | the boundary effect is not a warm-up artefact: 55/55 cold requests with cached 0 | C43 | CLAIMS.md:149 | RE-DERIVED | READY | — |

## G. Cross-stack cache-hit granularity

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C45 | WIN-SGL carries 1,800 rows, 900 per config, all status 200 | C45 | CLAIMS.md:177 | RE-DERIVED | READY | — |
| C46 | WIN-SGL battery: hit 0.9742 / 0.9738, uncached 740.4 / 752.6 per turn, grids 64 / 128 | C46 | CLAIMS.md:178 | RE-DERIVED | READY | — |
| C47 | G3 S0 at production default page_size 1: hit 0.974242, 739.2 uncached per turn, gcd 64 | C47 | CLAIMS.md:179 | RE-DERIVED | READY | an in-cell G0 per cell (gap 38) |
| C48 | WIN-VLLM carries 692 rows across V1/V2/V3, all status 200 | C48 | CLAIMS.md:180 | RE-DERIVED | READY | — |
| C49 | the vLLM grid law per config: gcd 1,088 / 1,056 / 2,096, exact 10/70, 10/26, 15/20 | C49 | CLAIMS.md:181 | RE-DERIVED | READY | — |
| C50 | WIN-VLLM battery: hit 0.869 / 0.868, about 2,231 / 2,246 uncached per turn | C50 | CLAIMS.md:182 | RE-DERIVED | READY | — |
| C51 | SGLang S0 at 32k vs vLLM V1: 3.074x uncached, hit 0.9742 vs 0.8690 | C51 | CLAIMS.md:183 | RE-DERIVED | READY-WITH-LIMITATION | [lim] one band, one seed (gap 23) |
| C52 | TUNED carries 289 rows, grid 64, 10/30 exact, variant wt-slru, policy slru | C52 | CLAIMS.md:184 | RE-DERIVED | READY | — |
| C54 | M4 resident capacity is 30-31 documents = 0.159-0.165 of declared, bounded by the state cache | C54 | CLAIMS.md:186 | RE-DERIVED | READY | — |

## H. Grid laws, second pass

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C55 | the grid unit per stack: S0 64, S1 64, S2 128, V1 1,088, V2 1,056, V3 2,096, TUNED 64 | C55 | CLAIMS.md:196 | RE-DERIVED | READY-WITH-LIMITATION | [lim] S1/S2/TUNED attribution only downgraded (gap 42) |
| C56 | the vLLM unit is identified, not fitted: 1,056 does not divide V1's rows, 1,088 does not divide V2's | C56 | CLAIMS.md:197 | RE-DERIVED | READY | — |
| C57 | SGLang returns multiples of its unit on every hot row at any page size, and page-size 64 does not move the grid | C57 | CLAIMS.md:198 | RE-DERIVED | READY | — |
| C58 | the one condition that moves the grid moves it by exactly one block, with no measured latency effect | C58 | CLAIMS.md:199 | RE-DERIVED | READY | — |
| C59 | TUNED delivers grid 64 with chunked prefix cache disabled, SLRU at 1.505x pressure, replay hits only the newest band | C59 | CLAIMS.md:200 | RE-DERIVED | READY | — |
| C60 | five distinct units across seven stacks, and the unit does not predict per-turn uncached cost | C60 | CLAIMS.md:201 | RE-DERIVED | READY | — |
| C61 | grid guard: 7/7 configs present, no claim rests on a config with no rows | C61 | CLAIMS.md:202 | RE-DERIVED | READY | — |

## I. The compaction boundary, measured live

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C62 | compaction at a real 32k/64k boundary costs +134.6 to +747.2 uncached tokens per turn after it and nothing before it (twelve arm means, not a per-turn range) | C62 | CLAIMS.md:213 | RE-DERIVED | READY-WITH-LIMITATION | [lim] one trigger, one run length, one engine (gap 21) |

## J. The model x engine matrix

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C63 | the engine, not the model, sets the per-turn bill: engine +549.33, model -400.02, interaction -403.63 | C63 | CLAIMS.md:229 | RE-DERIVED | READY-WITH-LIMITATION | [lim] one band, one seed, two checkpoints (gap 23) |
| C65 | the 2x2 survives every Round-2 re-check, re-derived without recompute.py | C65 | CLAIMS.md:265 | VERIFIED-OFFLINE | READY | — |
| C66 | mamba_track_interval is not a grid lever: 256/128/64 all deliver gcd 64 and no arm moves | C66 | CLAIMS.md:266 | RE-DERIVED | READY | — |
| C67 | the pointer index is null against full history on both production setups, costs on vLLM dense, and the edit control costs on O4 | C67 | CLAIMS.md:267 | RE-DERIVED | READY-WITH-LIMITATION | [lim] four setups, one round |
| C68 | the four Round-2 batteries are four distinct configurations, 0 pairs caught by the identity test | C68 | CLAIMS.md:268 | RE-DERIVED | READY | — |
| C69 | the version round at the ceiling is no_signal: V1 costs 1.249x MoE / 1.137x dense and the quality falsification fires | C69 | CLAIMS.md:269 | RE-DERIVED | READY | — |

## K. The pointer-engine fold (drafted, not in CLAIMS.md)

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| C75 | 12 bodies totalling 30,000 B behind a 447 B 12-line index: r = 67.1x | C75 | FOLD-PROPOSAL.md:56 | DRAFTED | BLOCKED-OPERATOR | [op] ratify section 9e; a body-count sweep (gap 9) |
| C76 | the append carries 12 framing tokens: L_app = n_payload + 12 in 387/387 rows | C76 | FOLD-PROPOSAL.md:57 | DRAFTED | BLOCKED-OPERATOR | [op] ratification |
| C77 | warm cells bill cached = P1 - residue and uncached = residue + L; A/B/D 18/15/15 at residues 5/2/2 | C77 | FOLD-PROPOSAL.md:58 | DRAFTED | BLOCKED-OPERATOR | [op] ratification; a residue-1 SGLang cell |
| C78 | quality arm: A 3/3, B 0/3 with 33 named PTR_STORE_MISS, C 3/3, D 0/3 discrimination control | C78 | FOLD-PROPOSAL.md:60 | VERIFIED-OFFLINE | BLOCKED-OPERATOR | [op] ratification |
| C79 | the engine's suite passes 190 tests in 0.22 s on today's tree | C79 | FOLD-PROPOSAL.md:60 | DRAFTED | BLOCKED-OPERATOR | [op] ratification |
| C80 | seven negative controls carry seven distinct codes, one per control class | C80 | FOLD-PROPOSAL.md:69 | DRAFTED | BLOCKED-OPERATOR | [op] ratification |
| C81 | a warmpool root inside the repository is refused PTR_WARMPOOL_INSIDE_REPO with no directory created | C81 | FOLD-PROPOSAL.md:70 | DRAFTED | BLOCKED-OPERATOR | [op] ratification |
| X01 | index sha256 e08700c9...99bd2 is identical across two processes and two warmpool roots | — | RECORD.md:21 | VERIFIED-OFFLINE | BLOCKED-OPERATOR | [op] fold it into C75's evidence or a new claim (gap 11) |

## L. Withdrawn or refuted — kept for traceability

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| W01 | "397 is what the endpoint bills on this append" — refuted: the identical append bills 15/18 at residues 2/5 | — | RECORD.md:114 | WITHDRAWN | NOT-PUBLISHABLE | a residue-0 warm cell (gap 14) |
| W02 | the "5.2x overstatement" of 397 — withdrawn; 397 is the engine's own stored law value | — | RECORD.md:114 | WITHDRAWN | NOT-PUBLISHABLE | — |
| W03 | the bill telescopes as sum(prompt_tokens) + 12(R-1) — refuted: stored 32,401 vs claimed 34,201, residual +17,193 | — | RECORD.md:134 | WITHDRAWN | NOT-PUBLISHABLE | per-turn cached_tokens stored in the rows |
| W04 | 49,594 as a measured bill — it is the engine's own modelled bill for an avalanche turn | — | RECORD.md:134 | WITHDRAWN | NOT-PUBLISHABLE | — |
| W05 | QUALITY-ARM token figures 34,390/34,372/30,652 and the A-vs-C -2 gap are void as costs | — | RECORD.md:118 | WITHDRAWN | NOT-PUBLISHABLE | the C4 re-run (gap 16) |
| W06 | the 57.6x understatement is one unit's server replay, never re-derived | — | RECORD.md:118 | UNSUPPORTED | NOT-PUBLISHABLE | recompute the corrected bill from the law (gap 8) |
| W07 | 78.3x compact index at 383 B is a single-unit figure, outside V-RECORD's confirmed set | — | FOLD-PROPOSAL.md:48 | UNSUPPORTED | NOT-PUBLISHABLE | a second index-format point |
| W08 | a per-turn vLLM TTFT multiple (7.4x) built from a cold prime row against a warm measure row of a different length | — | RECORD.md:145 | WITHDRAWN | NOT-PUBLISHABLE | the residue-1 G6 row (gap 15) |
| W09 | padding predictions r>=34 and PAD_FOR_FREE_RESIDUE=33 rest on a stub calibrated at base P1 66 against measured 325/386/322 | — | RECORD.md:122 | UNSUPPORTED | NOT-PUBLISHABLE | recalibrate against measured padded cells (gap 10) |
| W10 | "no measured padded cycle exists" — false: cells A/B/D are measured padded cycles at pads 60/58/50 | — | RECORD.md:122 | WITHDRAWN | NOT-PUBLISHABLE | — |
| W11 | C8's 321 "rows of concern" partition — the classifying artefact was overwritten and no predicate on disk yields 321 | — | RECORD.md:138 | UNSUPPORTED | NOT-PUBLISHABLE | nothing; unclosable (gap 45) |
| W12 | the "17,552 raw prefix" figure has no field behind it in any row | — | RECORD.md:99 | UNSUPPORTED | NOT-PUBLISHABLE | nothing; never collected (gap 47) |
| W13 | the 141/129 avalanche split and any residue-to-avalanche law — residue is not separable from P1 | — | RECORD.md:132 | UNSUPPORTED | NOT-PUBLISHABLE | a fixed-P1 residue sweep (gap 19) |

## M. Blocked on a live cell — the queue

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| L01 | whether SGLang re-bills one block or the whole prefix at residue 0 is undecided (397 vs 77 vs 13) | — | GAPS-INVENTORY.md:22 | UNSUPPORTED | BLOCKED-LIVE | [live] 3 requests on :8012 at P1 384, L 13 |
| L02 | the 8.5x vLLM penalty rests on one residue-0 pair; no residue-1 warm row exists inside controlled cell G6 | — | RECORD.md:145 | UNSUPPORTED | BLOCKED-LIVE | [live] 2 reps at P1 7393 on :8014 (gap 15) |
| L03 | no compact-UNPADDED cell E exists, so pad-vs-compact rests on a stub | — | GAPS-INVENTORY.md:25 | UNSUPPORTED | BLOCKED-LIVE | [live] 3 reps on :8012, P1_E and R_E recorded |

## N. Blocked on the operator

| id | finding (one clause) | claim | source | strength | status | what would strengthen it |
|---|---|---|---|---|---|---|
| O01 | fold-with-limits and the drafted ids C75-C79 are unratified | — | GAPS-INVENTORY.md:48 | DRAFTED | BLOCKED-OPERATOR | [op] operator signs off section 9e |
| O02 | section 8's universal 372/372 append sentence collides with section 9e's grid-exact 322-386-token appends | C38 | GAPS-INVENTORY.md:47 | RE-DERIVED | BLOCKED-OPERATOR | [op] scope section 8 to 931-12,393-token histories |
| O03 | the G17 collection freeze stands against the G3/G4 remainders it now blocks | — | GAPS-INVENTORY.md:49 | UNSUPPORTED | BLOCKED-OPERATOR | [op] reopen or keep the freeze and print G3/G4 as narrowed |

## O. The 48-gap ledger (not findings; source `orchestration/GAPS-INVENTORY.md`)

| class | n | closes it | source |
|---|---:|---|---|
| CLOSABLE-OFFLINE | 13 | apply what is on disk: engine size, one suite tree, C1/C3 text, FIT-GAP section 2, in-row index hash, C8 partition | GAPS-INVENTORY.md:60 |
| NEEDS-LIVE | 25 | the three-cell :8012 batch, the :8014 G6 residue-1 row, and the G3/G4 remainders | GAPS-INVENTORY.md:60 |
| NEEDS-OPERATOR | 6 | ratify the fold, scope section 8, G17 freeze, the downgrade notes, the endpoint spend | GAPS-INVENTORY.md:60 |
| UNCLOSABLE | 4 | #45 321 partition, #46 index bytes, #47 17,552 prefix, #48 the cold/warm TTFT pair | GAPS-INVENTORY.md:53-56 |
| total | 48 | 0 unclassified | GAPS-INVENTORY.md:60 |

<!-- rows-index:begin -->
## P. Row files measured on 2026-10-26 — generated, never hand-edited
Every number in this section is derived from the rows by `build_compilation.py`, which discovers its inputs by globbing `experiments/ptr-engine/measure/rows-*.jsonl`: no count here is typed by hand and no row file is named anywhere in the script. `uncached` is `prompt_tokens − cached_tokens` with a null `cached_tokens` read as **0** (the LIVE-CELLS-2 null semantics; the row's own `cached_source` field records the endpoint rule). `turn-reps` is the number of distinct `(rep, turn)` pairs, so `uncached/turn-rep` is one turn on one rep — a cell whose file has no `turn` field prints `—` rather than inventing a divisor. A status is never inferred: it comes from the file's own `unit` field through a declared verdict table, and an unknown unit is reported as `NOT-PARSED`.
**Artefact state at this build.** `experiments/ptr-engine/RECORD.md` — 169 lines; `BASELINE-COST` appears 0 time(s) in it, so the baseline-cost layer is not yet folded into the record. Derived by reading the record; re-derived on every run.
### P.1 One line per discovered row file
| row file | rows | unit | status | models | source |
|---|---:|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | `C0-BASELINE` | INVALID-BY-DESIGN | `occamy-1.0-NVFP4`, `qwen3.5-9b` | `orchestration/handoffs/C0-BASELINE.json:101` (fields prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error) |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | `C0-EQUALINFO` | MEASURED | `occamy-1.0-NVFP4`, `qwen3.5-9b` | `experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl` (fields prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context) |
| `rows-live-2026-10-26.jsonl` | 27 | `LIVE-CELLS-2` | MEASURED | `occamy-1.0`, `qwen3.5-9b` | `experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl` (fields prompt_tokens,cached_tokens,cached_reported,answer_correct,error) |

- `rows-baseline-2026-10-26.jsonl` is **INVALID-BY-DESIGN** — C0 never carries k01 in context (turns carry k12, k10, k08 only), so the plain transcript cannot answer by construction — do not cite any figure from this file (source `orchestration/handoffs/C0-BASELINE.json:101`).

### P.2 `rows-baseline-2026-10-26.jsonl` — 105 rows, status INVALID-BY-DESIGN
| model | cell | role | rows | turn-reps | uncached sum | uncached/turn-rep | correct/answered | error rows | source |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `occamy-1.0-NVFP4` | `C` | `—` | 12 | 12 | 16,892 | 1,407 | 0/12 | 0 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |
| `occamy-1.0-NVFP4` | `C0` | `—` | 12 | 12 | 18,553 | 1,546 | 0/12 | 0 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |
| `occamy-1.0-NVFP4` | `R` | `—` | 24 | 12 | 27,825 | 2,318 | 3/24 | 0 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |
| `qwen3.5-9b` | `C` | `—` | 12 | 12 | 23,895 | 1,991 | 0/12 | 0 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |
| `qwen3.5-9b` | `C0` | `—` | 12 | 12 | 56,121 | 4,676 | 0/12 | 0 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |
| `qwen3.5-9b` | `R` | `—` | 33 | 12 | 76,350 | 6,362 | 0/21 | 12 | `rows-baseline-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error |

- 62 of 105 rows carry a null `cached_tokens`, counted as 0.
- 12 row(s) carry a non-empty `error` (`HTTP 400: b'{"error":{"message":"\\"auto\\" tool choice requires --enable-auto-t`).

### P.3 `rows-equalinfo-2026-10-26.jsonl` — 100 rows, status MEASURED
| model | cell | role | rows | turn-reps | uncached sum | uncached/turn-rep | correct/answered | error rows | source |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `occamy-1.0-NVFP4` | `C0F` | `—` | 12 | 12 | 22,934 | 1,911 | 3/12 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |
| `occamy-1.0-NVFP4` | `C0FT` | `—` | 12 | 12 | 560 | 46 | 3/12 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |
| `occamy-1.0-NVFP4` | `R` | `—` | 24 | 12 | 42,288 | 3,524 | 3/24 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |
| `qwen3.5-9b` | `C0F` | `—` | 15 | 12 | 338,628 | 28,219 | 3/15 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |
| `qwen3.5-9b` | `C0FT` | `—` | 12 | 12 | 271,512 | 22,626 | 0/12 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |
| `qwen3.5-9b` | `R` | `—` | 25 | 12 | 57,857 | 4,821 | 0/25 | 0 | `rows-equalinfo-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,turn,rep,answer_correct,error,items_in_context |

- 54 of 100 rows carry a null `cached_tokens`, counted as 0.
- `items_in_context` takes 0, 1, 2, 3, 4, 12.

### P.4 `rows-live-2026-10-26.jsonl` — 27 rows, status MEASURED
| model | cell | role | rows | turn-reps | uncached sum | uncached/turn-rep | correct/answered | error rows | source |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `occamy-1.0` | `A` | `measure` | 7 | — | 407 | — | 0/6 | 1 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `occamy-1.0` | `A` | `prime` | 7 | — | 2,634 | — | 0/7 | 0 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `occamy-1.0` | `A` | `same` | 3 | — | 1,152 | — | 0/3 | 0 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `occamy-1.0` | `B` | `measure` | 4 | — | 268 | — | 0/3 | 1 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `qwen3.5-9b` | `C` | `append` | 2 | — | 14,812 | — | 0/2 | 0 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `qwen3.5-9b` | `C` | `prime` | 2 | — | 14,786 | — | 0/2 | 0 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |
| `qwen3.5-9b` | `C` | `same` | 2 | — | 2,114 | — | 0/2 | 0 | `rows-live-2026-10-26.jsonl`:prompt_tokens,cached_tokens,cached_reported,answer_correct,error |

- 13 of 27 rows carry a null `cached_tokens`, counted as 0.
- `cached_source` values: `absent`, `absent(server omits cached_tokens when 0)`, `metrics.prompt_tokens_cached_total`, `usage.prompt_tokens_details`, `usage.prompt_tokens_details.cached_tokens`.
- 2 row(s) carry a non-empty `error` (`setup: TypeError: Ledger.__init__() missing 1 required positional argument: 'pat`; `target_not_reached P1=385`).

<!-- rows-index:end -->
