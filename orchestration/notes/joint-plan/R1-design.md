# R1 — Design notes: context arms, cells, validity, gen-6 status

Source basis (all citations are `file:line` or `file §section` against `/home/zer0null/research extractor`):
- `research/next-candidates/consonance-bounded-context-evaluation.md` (517 lines) — primary.
- `experiments/ptr-engine/research-seed-concepts/VALIDATION-ROADMAP.md` (234 lines) — gates/stages.
- `docs/STATE.md`, `docs/GRID-2-FINAL.md`, `docs/GRID-GAP-DIAGNOSIS.md` — gen-6 verdict and ledger.

## 1. Five context arms A–E and the C0F equal-information control

Arm table: `consonance-bounded-context-evaluation.md:320-327` (§6). Request shapes in the last column are per turn.

| Arm | Name (doc) | Definition (doc) | Fetches | Does not fetch | Requests/turn |
|---|---|---|---|---|---|
| A | `full-transcript` | append-only, FIFO at the declared wall (`:322`) | (baseline, no fetch) | — | 1 |
| B | `transcript-compact` | existing digest at cap, recent 4 turns raw (`:323`) | digest | — | 1 + digests |
| C | `masking-no-fetch` | old tool outputs replaced by pointer markers, **no** external fetch (`:324`) | none (masked only) | external fetch | 1 |
| D | `bounded-context-fetch` (BRCV) | frozen prefix, bounded window, pointer table, `fetch` on demand, checkpoint only on forecast (`:325`) | `fetch(ref, range?)` on demand | — | 2 (fetch + answer) |
| E | `oracle-evidence` | same prompt budget as D, needed evidence injected (`:326`) | injection of needed evidence | — | 1 |

Shared requirements for all five: one fixture set/version, one frozen build, four equal fingerprints (`R2`), same verifier and acceptance checks, same prompt-budget accounting (`:328-331`).

Control battery beyond the per-arm pair: identical-repeat cache control for every arm; append cache control for every arm; a holistic positive control (fact present, fetch works, answer correct); a holistic negative control (fact absent from the store, arm must abstain). Each run red first on a deliberately broken log (`:333-336`).

**C0F equal-information control** is not one of A–E; it is the equal-information baseline used as an additional comparison. Source: P2 row `:56` — `C0-EQUALINFO` handoff `orchestration/handoffs/C0-EQUALINFO.json`: C0F **1,911.2** uncached/turn vs R **3,524.0**, ratio **1.8441**. Consequence recorded in the doc: the pointer arm can be **more** expensive at equal information; Arm D must be compared against Arm A at equal information, not against a truncated strawman (`:56`). Stage 3 design repeats this: "Arms and their controls are protocol §6 (A/B/C/D/E + the C0F equal-information baseline as an additional comparison)" (`VALIDATION-ROADMAP.md:153`).

**Activation predicates** (treatment must fire; computed from the stamp, never by name) — `consonance-bounded-context-evaluation.md:132-137` (§3.5):
- A (at cap): `evicted_turns > 0`
- B: `digest_rows > 0`
- C: `masked_rows > 0`
- D: `fetch_rows > 0` and `retrieval_outcomes` non-empty
- E: `oracle_injections > 0`

A cell failing is reported `INVALID-INSTRUMENT` and excluded by rule, not by name; absent stamp ⇒ excluded (`:135-137`). D's rows also carry the fetch-outcome vocabulary (OK / NOT_FOUND / STALE_OR_REVOKED / SCOPE_UNGRANTED) (`:325`, `:407-420`).

## 2. Task set, horizons, replicates; unsupported cells

Tasks: `longrun/fixtures/LR-01..06.json`, classes repo-fix / multi-file-refactor / bug-fix-with-test / constraint-survival / adversarial-debug / doc-sync; lengths 48 / 64 / 56 / 40 / 72 / 60 turns (`:340-342`).

Horizons (`:344-348`):
- 10 turns: 6 tasks — all fixtures supply it.
- 30 turns: 6 tasks — all fixtures supply it.
- 60 turns: **3 tasks** (LR-02 64, LR-05 72, LR-06 60). **LR-01 (48), LR-03 (56), LR-04 (40) cannot supply 60 turns → `UNAVAILABLE`, not imputed** (`:348`).

Replicates: 3 reps per task/arm (`:350`); "6 tasks × 3 rep" at 60 turns is not available and is never written as if it were (`:350-351`).

Additional unavailable fixture classes (§3.8 `:155-161` and `:38`-adjacent): multi-hop retrieval and unavailable/stale/revoked source are **MISSING** from every authored fixture; recorded `UNAVAILABLE` / `NOT_OBSERVED`, never scored as success, no fixture fabricated (`consonance-bounded-context-evaluation.md:157-161`, `VALIDATION-ROADMAP.md:61-63`).

## 3. Exact arithmetic derivation of 420 and 7,560

Doc chain (`consonance-bounded-context-evaluation.md:363-368`):
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

Alternative statement of the same total (`VALIDATION-ROADMAP.md:129-137`):
```
turns per arm per rep over all available cells = 6×10 + 6×30 + 3×60        =   420
four one-request arms (A, B, C, E)          = 4 × 420                     = 1,680 / rep
D at 2 requests per turn (fetch + answer)   = 2 × 420                     =   840 / rep
three reps                                  = 3 × (1,680 + 840)           = 7,560
remaining ledger (recorded 2026-10-28)                                    = 1,729
ratio at the design's own request shape                                   = 4.37×
```

Plan's compact form (verification clause): `3 × (4 × 420 + 2 × 420) = 7,560` — expands to `3 × (1,680 + 840) = 3 × 2,520 = 7,560`, consistent with both doc forms above.

Steps the doc leaves implicit / not stated (flagged, not invented):
- The 6/6/3 task counts per horizon are stated in the horizon table (`:346-348`) but the doc never writes the combined "6 tasks × 3 reps" formula explicitly; the 420 line assumes all six tasks at 10/30 and three at 60.
- 420 excludes B digests and D checkpoints; those are added as `≥7,560` (`:369`), so 7,560 is a lower bound, not an exact total.
- The 2 req/turn for D is grounded only via `BOUNDARY-PREREG.md` "R-pointer" "2 requests/turn (fetch + answer)" (`consonance-bounded-context-evaluation.md:487-488`); the comparative doc does not independently justify it.
- Warmup, retries, failures/aborts, separately counted retries, and the additional real-workflow validation are **not** in the 7,560 figure; they are unpriced/estimate lines (plan §5).
- C0F control cost is **not** included in 7,560; priced separately (plan §5).
- Memory-sweep cells are **not** included in 7,560; priced separately (plan §5).

## 4. Validity gates 0.1–0.11 (VALIDATION-ROADMAP.md §Stage 0, table `:47-59`)

| Gate | Pass condition (condensed) | Source |
|---|---|---|
| 0.1 | positive control can pass: known-good log passes; wrong-value log fails on the value; missing-fact log fails distinguishably; same log scores identically twice; tampered fixture exits 2 | `VALIDATION-ROADMAP.md:49`; protocol `:87-90` |
| 0.2 | ≥12 decidable checkpoints, all gradeable (today grade_v5 grades 8 of 12; 4 need NONE/call_at_line branches) | `VALIDATION-ROADMAP.md:50`; protocol `:95-104`; `docs/CHECKPOINT-COVERAGE.md` |
| 0.3 | fixture wall priced from measured growth: dry run shows each treatment reaching its wall inside the horizon (gen-6's wall was priced from declared padding 10,616 vs live base 5,628–6,139 at 41–98 tok/turn ⇒ 73–113 turns to wall > 48) | `VALIDATION-ROADMAP.md:51`; protocol `:105-114` |
| 0.4 | four fingerprints frozen: model (id + revision/quantisation digest), tokenizer (files/hash + chat-template hash), renderer (content digest module→bytes), engine (image digest + exact flags); placeholders are a hard stop | `VALIDATION-ROADMAP.md:52`; protocol `:116-121` |
| 0.5 | replicate identity: unique `(arm, rep, cell, turn_index)`; `rep` in `run_id`; pre-analysis assertion row count = cells × turns × reps | `VALIDATION-ROADMAP.md:53`; protocol `:125-128` |
| 0.6 | activation gating: per arm the declared predicate non-zero on the cell's own rows; exclusion computed from the stamp, never by name | `VALIDATION-ROADMAP.md:54`; protocol `:132-137` |
| 0.7 | budget preflight: ledger rebuilt, arithmetic printed per arm, caps set before first call; unknown ⇒ zero requests | `VALIDATION-ROADMAP.md:55`; protocol `:139-145` |
| 0.8 | independent verifier assigned: a process/person that ran none of the arms; fixture digest checked at score time; score_longrun.py exits 2 on tamper, 3 on stub | `VALIDATION-ROADMAP.md:56`; protocol `:147-151` |
| 0.9 | scorer can express a retrieval miss and an abstention: `retrieval_miss` / `abstained_correctly` scorable, red→green control (fabricated answer must fail before abstention passes); today grep for `abstain\|retrieval_miss\|STALE\|REVOKED\|NOT_FOUND` returns 0 matches; four check kinds are artifact/fact/constraint/repair | `VALIDATION-ROADMAP.md:57`; protocol `:397-435` |
| 0.10 | prototype extension offline-deterministic: alignment-aware append planner (2-token pad at residue 0/1), fetch batching by body tokens, retrieval-outcome vocabulary, deterministic resume each have unit tests; index digest reproduces across two processes and two roots | `VALIDATION-ROADMAP.md:58` |
| 0.11 | law package re-derived: residual table in README.md §Verifying reproduces (`sglang 301 {0: 218, …}`; `vllm 86 {−1056: 1, 0: 85}`) | `VALIDATION-ROADMAP.md:59` |

Additional (not numbered in 0.1–0.11 but in protocol §3): four fingerprints frozen per run (`:116-121`); replicate identity (`:125-128`); treatment activation proven before analysis (`:132-137`); budget preflight (`:139-145`); independent verification (`:147-151`); fixture classes incl. missing ones (`:153-161`).

## 5. Preregistered admissibility and exclusion rules

- p95 floor: `min_n_for(0.95) = 60`; p95 refused at n=48; gen-6 refused p95 at n=48 (`consonance-bounded-context-evaluation.md:389-393`).
- n_eff on the arm's own turn-ordered series: `n_eff = n(1−r)/(1+r)`; gen-6 pointer-stable n_eff 26.14 vs floor 60 (`:389-392`, `docs/GRID-2-FINAL.md:42-47`).
- Analysis rules (§8, `:437-455`): paired task-level differences within one fixture and fingerprint set, no pooled arm means, no ratio of totals; intervals name method and n (t-based with df stated, bootstrap with seed, Clopper-Pearson for proportions); `df = 2` intervals reported as such; no p95 below floor; no re-pinning after rows seen (fixture/threshold/estimator move ⇒ `retrospective:true`); derived is not measured (`uncached = prompt − cached` is `derived` with formula named, never quoted as measurement); null semantics per endpoint and field (`:8012` null cached = 0; `:8014` null = unknown); generation labels on every row/table (gen-6 and gen-7 never in same column).
- Non-results first-class: `UNDEFINED`, `UNAVAILABLE`, `NOT_OBSERVED`, `INVALID-INSTRUMENT`, `UNFUNDED` — each appears in the table, never replaced by zero/blank (`:444-446`).
- Fresh preregistration needed before new claims: the doc/plan require a separately preregistered rule before drawing new claims rather than silently changing existing ones; `BOUNDARY-PREREG.md` (registered 2026-10-26T01:22-0500, 696 scheduled / 810 ceiling, arms C0-static/C0-trunc/R-pointer/R-pointer-prefetch) is a **separate registered candidate** never pooled with this programme (`consonance-bounded-context-evaluation.md:483-488`). Any new hypothesis/estimator/ablation (e.g. the D-variant without alignment-aware planner, noted `[INFERENCE — adds a sixth arm, must be re-priced]`, `VALIDATION-ROADMAP.md:198-201`) needs its own preregistration before a claim.

## 6. Gen-6 result status (`not_adjudicable`)

- `docs/STATE.md:14-16`: gen-6 16-cell grid measured; verdict **`not_adjudicable`** (2026-10-28).
- `docs/STATE.md:35-43`: H1 `not_adjudicable_floor` (binding arm C: p50 156.151 ms [146.306, 291.926], n=48, lag-1 r=+0.2949 ⇒ n_eff 26.14 < 60; p95 refused at n=48; arm A has 0 usable cells). H2 `not_adjudicable` (frozen rule C-vs-A; A has 0 usable cells). H3 `not_adjudicable` (placeholder zeros, no admissible emitter). TVS `UNDEFINED` (n_verified_success = 0).
- `docs/STATE.md:47-60`: four instrument defects: (1) treatments never fired (8 transcript cells `usable_for: []`, `evicted_turns=0`, `digest_rows=0`; wall priced from declared padding 10,616 vs live base 5,628–6,139 at 41–98 tok/turn ⇒ 73–113 turns to wall > 48); (2) replicate collapse (selector dedupes on `(arm, rep, turn_index)`, every gen-6 cell wrote `rep=1`; 288 turn rows → 96 analysed, `dropped_duplicate=192`); (3) absent stamp admitted (`longrun/analyze_stats.py:749` keeps manifest-less cell); (4) cap-gate projection under-counts (`projected_requests` prices 96, tools-on turn bills k+1; gate refused 97th → 2 cells `exit 4` at T47/T48).
- `docs/GRID-2-FINAL.md:11-36`: census — 6 of 16 usable; 8 stamped `[]`; 2 `ABSENT` (no manifest); 1,270 request rows across 16 cells = ledger delta exactly.
- Rule that fixture/runner changes mint a new generation: `docs/STATE.md:77-82` — any fixture/`run_longrun.py` change **mints generation 7**; gen-6 rows become non-poolable; re-run all-or-nothing per arm. `consonance-bounded-context-evaluation.md:489-491` — gen-6 grid is `not_adjudicable`, its rows are **non-poolable** with gen-7: fixture wall, replicate key and census rule all change; gen-7 requires v9 wall, replicate key, activation gating, stamp rule before a single call. `VALIDATION-ROADMAP.md:229-230` — gen-7 is a separate decision; rows non-poolable with gen 6.

## 7. Result-column inventory the design requires per run

Per horizon and arm (`consonance-bounded-context-evaluation.md:353-359` §6.2): total and peak **logical** prompt tokens; uncached work when observable (else `NOT_OBSERVED`); cache reads; fetch calls and fetch tokens; completion tokens; storage/index size; rebuild cost; end-to-end wall time; time and tokens to independently verified success; quality; abstention; forbidden-action (negative-constraint) results; per-turn and per-segment (pre-boundary / transition / post-boundary) decomposition — **never arm means alone** (`:241-243`, `:355-359`). Any denominator that is zero is `UNDEFINED`, never 0 (`:359`).

Per-call record (worked hypothetical, `:407-420`): `prompt_tokens`, `cached_tokens` (or absent/null per R5), `uncached_prefill_tokens` (null unless engine exposes), `ttft_ms`, `total_ms` (end-to-end latency), `completion_tokens`, `finish_reason`, `verified_success`, `exit_cause` (abstained etc.), plus run-side event rows `retrieval_attempt{ref, outcome}` with outcomes OK/NOT_FOUND/STALE_OR_REVOKED/SCOPE_UNGRANTED, `masked_entry{ref, since_turn}`, and scorer card `retrieval_miss`, `abstained_correctly`, `tokens_to_verified_success` (null when undefined).

Quality/abstention reported as paired task-level differences with intervals (`:358`); null semantics per endpoint and field recorded on every row carrying a null (`:452-453`).

Fields not named in the doc (labelled UNSTATED, do not invent): **warmup** (listed in the plan §4 but no warmup counter appears in §6.2 or the call record — treat as `NOT_OBSERVED`/unstated); **resource usage** beyond storage/index size (no CPU/GPU/memory counter named in §6.2 — treat as `NOT_OBSERVED` unless the inventory supplies it); **reasoning tokens** (doc says completion tokens only; reasoning split not named — UNSTATED); **request count** is the ledger/budget dimension (§3.6, §6.3), not a per-row field in §6.2.

## Notes for the pricing/verifier units

- 7,560 is a **lower bound** and excludes B digests, D checkpoints, warmups, retries, failures/aborts, C0F control, memory-sweep cells, pilot (≈185) and real-workflow validation. Do not present 7,560 as the programme total.
- Four historical configurations O1–O4 are **comparison candidates, not current live config**; their exact model/engine/flags come from `docs/serving-options/BEST-CONFIG.md` and must be distinguished from live observations (plan §2). Live argv/GPU inventory is to be captured separately (R2 unit).
- Ledger: 2,591 spent / 1,729 remaining of 4,320, rebuilt 2026-10-28 (`docs/STATE.md:64-72`); reservations in `experiments/ptr-engine/measure/RESERVATIONS.json` to be reported with recorded fields separately (R3 unit). Do not claim a precise available balance if any component is unknown.
- Gen-6 rows are non-poolable with any newer generation; do not pool (`consonance-bounded-context-evaluation.md:489-491`).
- No live inference, service change, fixture/grader change, or budget increase is authorized by this planning deliverable.
