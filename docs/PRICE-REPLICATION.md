# PRICE-REPLICATION — what the next 288–792 requests should buy

**Unit** `PRICE-REPLICATION` · **cost** 0 inference requests · **edits** `RUN-A*`, `PARM-1`,
`BUDGET-SCHEDULE`'s artefacts, every rows/grade file: **0** · machine-readable twin:
[`price-replication.json`](../experiments/ptr-engine/measure/price-replication.json).

`BUDGET-SCHEDULE` priced **A\*** at 4 arms × 48 turns × 3 reps = **792 requests** (the live `RUN-A*`
card prices the same 576 turns at **~800** because the v8 fixture adds 6 digest rows). The standing
default is "run A\*". That default was set before anything measured how much information a turn
actually carries.

`P95-POWER-FROM-ROWS` (PASS `f17663d1`) then measured, from the rows already on disk, three things
that change the price of every option below:

1. **The H1 pair separates at n = 48 already** — 100 % disjoint at 48, 60 and 144 on
   `rows-longrun-c`, with the observed intervals disjoint by **254 ms** (`docs/P95-POWER.md:88-90`,
   `:127-137`). The 792-request grid does not *buy* the separation; it re-buys it.
2. **Effective n is ~⅓ of raw** — median lag-1 **0.417**, Fisher-z pooled **0.37**: raw 48 is worth
   **22.1**, raw 144 is worth **66.2** (`docs/P95-POWER.md:164-171`). Under the *noisier* H1 arm's own
   lag-1 (**0.6423**, `c::pointer-stable`) the same 144 raw timings are worth **31.4**.
3. **The effect may be grid-specific** — the 315.29 ms p50 / 530.0 ms p95 gap appears on
   `rows-longrun-c` only; `-v3` shows 32.39 ms p50 / −2.35 ms p95 and `-v4` 11.99 ms / −57.65 ms, and
   neither separates the pair at any n ≤ 384 (`docs/P95-POWER.md:127-131`).

This card does not re-open a threshold. It re-prices **reps and arms** only, and every schedule that
could only work by relaxing a rule is marked `not admissible` with the clause it would need.

## 1. Inputs, each with its path

| quantity | value | source |
|---|---|---|
| quota cap | 4,320 | [`REQUEST-LEDGER.json`](../experiments/ptr-engine/measure/REQUEST-LEDGER.json) → `budget.cap` |
| spent (raw) | 1,101 | same → `budget.spent` |
| **remaining (raw)** | **3,219** | same → `budget.remaining` |
| de-duplicated remaining (not used) | 3,249 | `LEDGER-CONSERVATIVE` (`f505519f`) forbids subtracting the 30 rows; priced against the raw figure |
| per-turn request factor | **1.374532** | [`BUDGET-SCHEDULE.md`](../experiments/ptr-engine/measure/BUDGET-SCHEDULE.md) §1 (1,101 ÷ 801 turn rows) |
| turns per arm per rep | **48** | [`PREREG-ARM-RUN.md`](PREREG-ARM-RUN.md):137 (PARM-1, fixture `N = 48`) |
| H1 raw-n floor | **60** | `PREREG-ARM-RUN.md`:37 (`n·(1−q) ≥ TAIL_MIN = 3` at q = 0.95) |
| lag-1 pooled / median | 0.37 / 0.417 | `docs/P95-POWER.md`:164 |
| lag-1 pointer-stable (C) | 0.6423 | `docs/P95-POWER.md`:150 |
| lag-1 transcript-grow (A) | 0.1071 | `docs/P95-POWER.md`:152 |
| wall per turn, thinking off | p50 2.9 s · mean 27.5 s · p90 38.1 s · policy 60 s | `BUDGET-SCHEDULE.md` §2 |

Effective n is `n_eff = n(1−r)/(1+r)` (`docs/P95-POWER.md:164`). Two columns are carried throughout
because they disagree, and the disagreement is the finding:

| raw timings per arm | effective @ pooled r = 0.37 | effective @ C's own r = 0.6423 | effective @ A's own r = 0.1071 |
|---|---|---|---|
| 48 (1 rep) | 22.07 | 10.45 | 38.71 |
| 96 (2 reps) | 44.15 | 20.91 | 77.43 |
| **144 (3 reps)** | **66.22** | **31.36** | **116.14** |
| 192 (4 reps) | 88.29 | 41.82 | 154.85 |
| 240 (5 reps) | 110.36 | 52.27 | 193.56 |
| **288 (6 reps)** | **132.44** | **62.73** | **232.28** |
| **432 (9 reps)** | **198.66** | **94.09** | **348.41** |

**The answer to "does 3 reps = 288 requests clear effective 60?" is: only under the pooled r.**
144 raw timings are worth 66.22 if the whole corpus' dependence is used, and **31.36** if
`pointer-stable`'s own measured lag-1 is used — i.e. **half** the floor, on the very arm whose interval
must be the tight one. 3 reps is not enough on a worst-case reading; **6 reps (288 raw → 62.73)** is the
smallest N that clears 60 under the binding arm, and **9 reps (432 raw → 94.09)** is the smallest that
clears it *comfortably* (≥ 1.5× the floor).

## 2. The schedule table

Costs are at factor 1.374532 (conservative). "Turns" = model turns; requests = ⌈turns × factor⌉.
`+CTX` shapes keep all four arms in the grid — `transcript-compact` (B) and `lease-reopen` (D) at the
minimum 2 reps — because PARM-1:150-152 defines the adjudicating grid as *all four arms*.

| # | shape | turns | **requests** | remaining after | raw/arm (pair) | eff @pooled | eff @C's r | H3 pairs | admissible |
|---|---|---|---|---|---|---|---|---|---|
| A\* | 4 arms × 3 reps | 576 | **792** (card: ~800) | 2,427 | 144 | 66.22 | 31.36 | 36 | ✅ |
| PAIR-3 | 2 arms × 3 reps | 288 | **396** | 2,823 | 144 | 66.22 | 31.36 | 36 | ❌ four-arm clause |
| PAIR-6 | 2 arms × 6 reps | 576 | **792** | 2,427 | 288 | 132.44 | 62.73 | 72 | ❌ four-arm clause |
| PAIR-9 | 2 arms × 9 reps | 864 | **1,188** | 2,031 | 432 | 198.66 | 94.09 | 108 | ❌ four-arm clause |
| **PAIR-3+CTX-2** | pair 3 + ctx 2 | 480 | **660** | 2,559 | 144 (ctx 96) | 66.22 | 31.36 | 36 | ✅ **T1** |
| PAIR-4+CTX-2 | pair 4 + ctx 2 | 576 | **792** | 2,427 | 192 (ctx 96) | 88.29 | 41.82 | 48 | ✅ |
| **PAIR-6+CTX-2** | pair 6 + ctx 2 | 768 | **1,056** | 2,163 | 288 (ctx 96) | 132.44 | 62.73 | 72 | ✅ **T2 target** |
| PAIR-9+CTX-2 | pair 9 + ctx 2 | 1,056 | **1,452** | 1,767 | 432 (ctx 96) | 198.66 | 94.09 | 108 | ✅ |
| A\*-LITE | 4 arms × 2 reps | 384 | **528** | 2,691 | 96 | 44.15 | 20.91 | 24 | ✅ (weakest) |
| C | 4 arms × 1 rep | 192 | **264** | 2,955 | 48 | 22.07 | 10.45 | 12 | ❌ n=48 refused |
| SMOKE-1R | 2 arms × 1 rep | 96 | **132** | 3,087 | 48 | 22.07 | 10.45 | 12 | ❌ reps ≥ 2 |

Wall, thinking off (turns × the per-turn percentiles in §1 — this reproduces `BUDGET-SCHEDULE`'s
published rows exactly, which is the cross-check on the arithmetic):

| shape | p50 | mean | p90 | 60 s policy |
|---|---|---|---|---|
| A\* / PAIR-4+CTX-2 (576) | 0.46 h | 4.40 h | 6.10 h | 9.60 h |
| PAIR-3+CTX-2 (480) | 0.39 h | 3.67 h | 5.08 h | 8.00 h |
| PAIR-6+CTX-2 (768) | 0.61 h | 5.87 h | 8.13 h | 12.80 h |
| A\*-LITE (384) | 0.31 h | 2.93 h | 4.06 h | 6.40 h |
| C (192) | 0.16 h | 1.47 h | 2.03 h | 3.20 h |

### What each option can and cannot adjudicate

- **A\* (792/800).** Can: H1, H2, H3 (36 pairs, 12/12 decidable v8 truths). Cannot: a 12–32 ms p50
  difference at any n ≤ 384 (`docs/P95-POWER.md:127-131`); and it cannot test whether the C-grid effect
  *recurs* — it is one grid, on a fixture era (v8) that the existing grids (v2 ids) cannot be compared
  with under `same_provenance()`. It spends 3 reps of one run per arm and calls that replication; the
  turns within a run are worth ~⅓ each, so its 144 raw timings carry ~⅓ the information its request
  count suggests.
- **PAIR-3 (396).** The power card's own recommendation (`docs/P95-POWER.md:196-199`). It buys exactly
  what A\* buys on H1 and H3 for 396 fewer requests — and it is **not admissible**: it drops B and D
  from the grid, which PARM-1:150-152 names. Price it as the lower bound on a conformant design, not as
  a schedule.
- **PAIR-3+CTX-2 (660)** — the recommendation. Conformant; costs 132 more than PAIR-3 and 132 less than
  A\*; spends its turns on **runs of the pair** (3 independent runs per arm) instead of on depth inside
  a cell; yields rep-level p50 recurrence and 36 H3 pairs. It does **not** reach effective 60 under
  C's own lag-1 (31.36) — that is what tranche 2 is for, and it is a measured limit, not a defect of
  the schedule.
- **PAIR-4+CTX-2 (792).** A like-for-like swap at **A\*'s exact price**: same 792 requests, +33 % raw
  pair timings (192 vs 144), −66 % context timings. If the operator wants to spend today's A\* money
  without changing the budget line, this is the shape.
- **PAIR-6+CTX-2 (1,056).** The first admissible shape that clears effective 60 under the binding arm
  (62.73). This is tranche 2's target, and the smallest "not-in-vain" resumption.
- **PAIR-9+CTX-2 (1,452).** Effective 94.09 under the binding arm — the only *comfortable* shape. It
  spends **45.1 %** of the remaining budget on H1 alone and buys nothing for H2/H3 beyond A\*.
- **A\*-LITE (528).** Meets every frozen rule (4 arms, 48 turns, reps 2 = PARM-1:142's floor, 96 raw ≥ 60)
  and fails the power card's overlay (44.15 pooled). Admissible, and the weakest admissible option: its
  H1 interval is the one the 792 grid was supposed to narrow.
- **C (264) / SMOKE-1R (132).** Not adjudications. C is refused by name (48 × 0.05 = 2.4 < 3) and its
  historical grid carried v2 checkpoint ids, so H3 has no denominator (PARM-1:160-165).

## 3. `not admissible` — and the clause each would have to relax

| shape | why it is refused | what it would need |
|---|---|---|
| any 2-arm grid (PAIR-3/6/9, SMOKE-1R) | PARM-1:150-152: the adjudicating grid is "all four arms in the **same** grid with identical `fixture_sha256` and identical reasoning policy" | a PARM-1 relaxation of the four-arm clause |
| any 60-turn shape (B 330, A 990) | PARM-1:137 fixes turns per arm = 48 (fixture `N = 48`); 60 turns needs a new fixture and a re-frozen rule hash | a fixture re-freeze + PARM-1 amendment |
| any reps = 1 shape as an H1 read (C 264, SMOKE-1R 132) | n = 48/arm → 2.4 < `TAIL_MIN` 3 → p95 **refused**, not caveated (PARM-1:37); PARM-1:142 requires reps ≥ 2 | lowering `TAIL_MIN` — forbidden |
| pooling one arm across grid files to reach n = 144 | `docs/P95-POWER.md:56-64` refuses cross-grid pooling; every n > 48 there is an ECDF extrapolation | a pooling rule that does not exist |
| any thinking-on grid | PARM-1:151 — the adjudicating grid is thinking off; a thinking-on run can never support H1 whatever it costs | a new PARM-1 |
| spending against 3,249 instead of 3,219 | the 30-row dedupe rests on `content_sha256`, which hashes assistant content (`run_longrun.py:1493`), not the request; `V-DUPLICATE-RULE` failed it (`f505519f`) | a sound request-identity rule |

## 4. The decision rule, executable

Evaluated on the v8 grid's rows for `pointer-stable` (C) and `transcript-grow` (A), using only the frozen
estimator `quantile_ci(..., q=0.95)` (`analyze_stats.py:187-247`, `resamples=10000`, `seed=20261020`) and
the frozen disjointness rule:

```
step 0  if min(usable_n_C, usable_n_A) < 60:            -> H1 REFUSED (estimator message verbatim); STOP   [S2]
step 1  P2 := CI_C.hi < CI_A.lo                        # pooled per-arm population, n = 144
step 2  for r in 1..3: d_r := p50_C(r) - p50_A(r)      # p50 at n=48 is admissible (24 >= 3); p95 is not
        P1 := (d_1 >= 100) and (d_2 >= 100) and (d_3 >= 100)      # milliseconds
step 3  if P1 and P2:                                  -> PROMOTE: buy tranche 2 (396 requests)
step 4  if not P2:                                     -> STOP. Do NOT run the 792 grid.
                                                          Publish H1 as refused/null on this era.
step 5  if P2 and not P1:                              -> HOLD. No tranche 2, no 792 grid;
                                                          report the separation as a single-grid result.
```

Three notes that keep this honest:

- **The 100 ms gate is a scheduling predicate, not an adjudication threshold.** It gates *spending*,
  never a verdict; failing it asserts nothing about the model. It is placed between the two measured gap
  families — 315.29 ms p50 / 530.0 ms p95 on `rows-longrun-c`, versus 32.39 / 11.99 ms p50 and
  −2.35 / −57.65 ms p95 on `-v3` / `-v4` (`docs/P95-POWER.md:127-131`) — so an effect an order of
  magnitude smaller than the one claimed cannot promote a second tranche.
- **No cross-era comparison enters the rule.** `rows-longrun-c` is the v2-fixture era; this run is the
  v8 era. `same_provenance()` refuses that comparison by name (card `9f2e8259`), so 315.29 ms is quoted
  as the historical effect and never as a comparator in step 2.
- **"The pair effect does not replicate" is the designed stop, not an edge case.** Two of the three
  grids already on disk fail to reproduce it. If a fourth does too, the answer to the operator's
  question is *"the effect is C-grid-specific"*, and that answer costs **660** requests, not 792.

## 5. The recommended spend

**Tranche 1 — `PAIR-3+CTX-2`: 4 arms, pair at 3 reps, context at 2 reps = 480 turns / 660 requests**
(10 cells of 48 turns; 2,559 remain; 2.32 h expected, 3.67 h mean, 5.08 h at p90, 8.0 h at the 60 s
policy; thinking off).

**Tranche 2 — promoted only by §4:** add 3 pair reps = 288 turns / **396 requests**, reaching
`PAIR-6+CTX-2` = 768 turns / **1,056 requests**, 2,163 remaining, effective **62.73** under the
binding arm.

What the next 288–792 requests buy, stated as one line: **three independent runs of each H1 arm inside a
conformant four-arm v8 grid — enough to see whether the 315 ms gap recurs at all, and to read it at
effective n ≈ 66 (pooled) while the second tranche is what lifts the binding arm's own effective n over
60.**

Why not the alternatives, in one line each: *A\* spends 132 more requests to buy 96 more turns of the
same three runs* (depth, worth ~⅓ per turn); *PAIR-3 is 264 cheaper and inadmissible*; *PAIR-4+CTX-2 is
A\*'s exact price with +33 % pair timings and is the right choice only if the operator will not move the
budget line today*; *PAIR-9+CTX-2 is the only comfortable shape and spends 45 % of the budget on H1*.

## 6. Stop rules, in requests

| id | rule | avoids |
|---|---|---|
| **S0** | hard ledger ceiling: before any cell, `remaining ≥ 264` (one 4-arm 48-turn cell at 1.374532). T1+T2 cap at **660 + 396 = 1,056**, leaving **2,163** of 3,219 | all further spend |
| **S1** | refuse to start tranche 2 unless `remaining ≥ 396` | 396 |
| **S2** | after E1–E4 exclusions, if either pair arm's usable n < 60 → H1 refused, STOP. At 3 reps the headroom is **84 exclusions** per arm (58.3 %) | 396 |
| **S3** | H3 veto on rep 1 (b+c ≥ 6 with exact two-sided p < 0.05 and C worse, or C loses > 2 of 12 checkpoints) → abandon the remaining 6 cells; 264 spent, 396 saved | 396 |
| **S4** | either arm's `grade_v5` decidable < 8 of 12 → H3 unadjudicable (PARM-1:113); do not buy further reps | 132 per cell |
| **S5** | any turn `wall_ms/1000 > 180` is excluded, never retried past the cap; the induced n < 60 falls through to S2 | open-ended retries |
| **S6** | ATTACK or V-GATE-CHAIN reports a defect after the run starts → halt at the next cell boundary | remaining cells |
| **S7** | if tranche 1 stops for S2–S6, freeze spend and re-price on a new card; **no automatic tranche 2, no fallback to the 792 grid** | 396–792 |

Ceiling arithmetic for the record: 3,219 − 1,056 = **2,163** if everything promotes; 3,219 − 660 =
**2,559** if the effect does not replicate; 3,219 − 264 = **2,955** if H3 vetoes after rep 1 of the first
four cells.

## 7. The default, revised

> **Default was A\*** (4 arms × 48 turns × 3 reps = 792 requests) **because** PARM-1:137 fixes 48 turns
> and A\* is the exact frozen grid shape, giving 144 raw timings per arm with 84 exclusions of headroom
> and 36 paired checkpoints (`BUDGET-SCHEDULE.md` §3, §5, §7). **Measurement** (`P95-POWER`, PASS
> `f17663d1`) **says** the H1 pair is already 100 % disjoint at n = 48 with a 254 ms observed margin
> (`docs/P95-POWER.md:88-90`, `:127-137`), that effective n is ~⅓ of raw (raw 144 → 66.2 pooled, and
> only **31.4** under the binding arm's own lag-1 0.6423; `:164-171`), and that two of the three grids
> holding the pair do not separate it at all (p50 32.39 / 11.99 ms; p95 −2.35 / −57.65 ms; `:127-131`).
> **Default is now `PAIR-3+CTX-2`** — 4 arms, pair at 3 reps, context arms at 2 reps = 480 turns /
> 660 requests — promoting to `PAIR-6+CTX-2` (768 turns / 1,056 requests) only by §4.

**Which card must carry the change:**

1. **`RUN-A*` card `ad214412-c39c-4a47-afb1-2be328e03b1e`** — its title, description, hard cap (900) and
   `conditional-launch` tags all encode "4 arms × 48 turns × 3 reps = 12 cells / ~792 requests". This is
   the execution carrier; until it is edited, "the default" is whatever that card launches.

   **SUPERSEDED 2026-10-26 (board #960, restated #988).** The sentence above is this §7's description of
   the card's **pre-#960** text, and it must not be reproduced as current. What §7 described was **792
   requests / 12 cells / cap 900**: A\*'s price on the frozen 4-arm × 48-turn × 3-rep grid — still correctly
   priced as 576 turns / **792** requests / 2,427 remaining for *that shape* in
   `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` §2 — plus a hard brake of 900.

   What the card says **now**, quoted from `task_board_get ad214412-c39c-4a47-afb1-2be328e03b1e`:
   - **title** — "tranche 1 PAIR-3+CTX-2 (pair 3 reps, context arms 2 reps) = **10 cells / 480 turns /
     ≈660 requests**";
   - **description** — "ten cells, 480 turns, ≈660 requests"; booked at `--request-allocation ~67` per
     cell with the ledger cap left at its artefact value **4,320**, not 900 (the board's CAP CORRECTION,
     #975: "Hard brake: cap=900" was the card author's own error and is superseded);
   - **preconditions as currently posted** — (1) `WIRE-GATES` PASS, read `docs/GATE-CHAIN.md`;
     (2) gate-refusal semantics: PASS verdict rows from **both** `SPAWN-RECORD-BIND` and `SPAWN-TREE-BIND`
     (`D5`/`D6` now closed), a refusal record covering all of {2,3,4,8,12} and carrying `cell_sha256`,
     `spawn_record_sha256`, `argv` and `tree_sha`, the first two matching the files on disk at launch;
     (3) `WIRE-CAP-GATE`, the brake as prevention under the 4,320 cap; (4) the v8 fixture
     `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`, whose four treatments must fire by T48
     (grow T21 · compact T21 · lease T23 · pointer T2) at `wall_tokens 10616`, never the top-level 3838;
     (5) 12 loadable checkpoint ids (`NUM 5 · CALL 4 · NONE 3`); (6) `EXIT-CODE-TABLE`; (7) the request
     ledger's `remaining ≥ 900` before cell 1 — with the six-handoff pre-launch tag alongside.

   The one sentence a reader needs:

   > A cap of 900 is the cumulative-spend brake, not the run's size: G1 compares cumulative `spent` (1,101 already spent + 48 turns + 5 allowance) against `cap − reserve`, so cap 900 would refuse before spending anything.

2. **`experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` §7 (`Default: A*`)** goes stale — it is the artefact of card
   `21254578-7b0e-4150-9c8f-3f89d31abdd8`, which PARM-1:140 cites as `PENDING: BUDGET-SCHEDULE`. The
   operator edits it; this card does not.
3. **PARM-1:140 (`Reps: PENDING`)** is resolved by naming the split — 3 pair reps / 2 context reps —
   but PARM-1 is **FROZEN**, so it lands as an **additive errata card** in the `PARM-1-ERRATA` style
   (`docs/PARM-1-ERRATA.md`), never as an edit to `docs/PREREG-ARM-RUN.md`.

## 8. What this card does not claim

- It does not claim the 315 ms effect is real or general. It prices the schedule that would find out,
  and the stop rule for the answer "it is not".
- It does not claim any interval from an ECDF extrapolation. Every n > 48 in §1 is a formula applied to
  a measured lag-1, and is labelled as such; no p95 is quoted at n > 48 from these rows.
- It does not lower a threshold. `TAIL_MIN`, `n ≥ 60`, the 48-turn grid, the 2/12 margin, the McNemar
  licence at b + c ≥ 6 and the four-arm clause are untouched; the only new number is a 100 ms
  *scheduling* gate, whose failure means "do not spend more", never "no effect".
- It prices against **3,219 raw**, not 3,249 de-duplicated (`f505519f`).

Zero inference requests were made; no rows, grade or measurement file was edited.
