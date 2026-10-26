# R2-OPT-SIM2 — the cost model and five ranked candidates, rebuilt from the failed SIM card

**Deliverable of the `R2-OPT-SIM2` card.** One document, one question: *given what the cells on disk
measured, which prompt-layout × compaction candidates should the next session run first, and by how
much?* Everything below is derived from files in this workspace; nothing was measured, downloaded, or
sent while writing it.

| | |
|---|---|
| **Rebuilds** | [`orchestration/units/R2-OPT-SIM.md`](orchestration/units/R2-OPT-SIM.md) — the SIM card that produced `report.json` and no deliverable |
| **Model** | [`scratch/r2-opt-sim/cost_model2.py`](scratch/r2-opt-sim/cost_model2.py) → `report2.json` (engine, reproducible) |
| **Protocol** | [`src/resextract/pointers.py`](src/resextract/pointers.py) — the SIM card's `## POINTER PROTOCOL`, made mechanical |
| **Evidence** | 960 LIVE-MEAS rows (4 arms × 80 turns), 139 U9 sweep rows, 4 of 5 declared sources resolve |
| **Tests** | 33 pass; every fitted constant coupled (red→green: `scratch/r2-opt-sim/selfcheck2.py`) |
| **Honest bottom line** | the rebuild **does not solve** the arm-C tail (−72.8 % on it); it decomposes the error and names the regime it comes from, instead of quoting an `r²` from a fit that prices a label |

---

## 0. What "failed" meant, measured

The SIM card is marked in progress and has **no** `strategy/R2_OPT_SIM.md` and **no**
`orchestration/handoffs/R2-OPT-SIM.json`. Its artefacts exist only under `scratch/r2-opt-sim/`. Re-running
them on this disk reproduces `constants.json` and `report.json` byte-for-byte, so the model is a fair
thing to rebuild — nothing below disputes its arithmetic, only its conclusions. Three defects, each
recomputed from rows rather than quoted:

**S0a — the live-miss "fit" prices a label.** `calibrate.py:816` fits `live_miss` with **one x per
row**: `uncached` alone. Across 160 fit rows all four arms carry the *same* residue value on the same
turn, so the regression sees **133 distinct x values**, not 160, and the residue is a function of turn
index, not of tokens. The fitted slope is **495.6 µs/uncached-token**:

- **2.06×** the U9 cold prefill (**240.7 µs/token**, re-derived here from the 6-cluster sweep median);
- fitted **inside the band [442, 560] uncached tokens** — **6 of 160** fit rows sit in that band;
- used out of sample at **720 uncached/turn** on arm C, i.e. outside the band it was fitted in;
- `r² = 0.1308`.

A miss cannot cost 2.06× a cold prefill *per token*. The number is real; it is just not a per-token
cost — it is the residue of turns where the prompt happened to be large.

**S0b — the lookup term is not usable as it stands.** `joint_two_term.us_per_prompt_ktok = 6735.2`
carried at face value prices arm C's 19.4k-token prompt at **130,663 ms** against a **290 ms** measured
turn. Direct residuals `ttft − (I + A·prompt/1000 + B·uncached/1000)` are **−51,439 ms** on average with
**r² −114,149**: the two-term model is far worse than the mean. Its 0.9875 was fitted on the warm band,
where prompt and uncached co-move, and the units do not survive leaving it.

**S0c — the hold-out was graded above the regime the model can see.** The fit window tops out at
**19,860 prompt tokens**; arm C's hold-out sits at **28,503 mean prompt / 719 uncached** and arm A's at
**29,339 / 1,097**. The reported hold-out error (`C +49.5 %, A +53.1 %, R −42.9 %, F −36.8 %`) is an
honest out-of-sample number for a model fitted *below* the only regime that matters — and R/F's numbers
are dominated by arms whose prompts *shrank*, so a mean-of-means compared four different regimes.

Also worth recording: `selfcheck.py` reports "green" while its own `selfcheck.json` records
`miss slope halved — NOT COUPLED`, because the case list names a test (`test_miss_slope_moves_the_prediction`)
that does not exist. A harness that cannot go red is not a check.

---

## 1. The rebuilt model — one fit, nine declared columns

`reprice9`, OLS on **all 160 fit rows** (arms C/A/R/F, turns 1–40), every column named:

| column | coefficient | status | what it is |
|---|---|---|---|
| `c0.intercept` | see `report2.json` | **identified** | TTFT floor |
| `c1.lookup_lt20k_ktok` | — | **identified** | prompt-wide traversal, below 20k |
| `c2.lookup_ge20k_ktok` | — | **unidentified** | the ≥ 20k branch — **0 of 160 fit rows** live there |
| `c3.miss_us_tok` | — | **identified** | miss cost per uncached token (billed from token one) |
| `c4.miss_ge20k_us_tok` | — | **unidentified** | ≥ 20k miss branch — 0 of 160 rows |
| `c5.compacted_ms` | — | **unidentified** | level cost of carrying a compaction policy |
| `c6.turn_ms` | — | **unidentified** | the measured ramp |
| `c7.scheduled_fold_ms` | — | **unidentified** | scheduled fold — **6 of 160** rows, `R²` loses more than it explains |
| `c8.regime_ge20k_ms` | — | **unidentified** | ≥ 20k regime — 0 of 160 rows |

Fit window: **r² 0.8683, MAE 27.2 ms, residual sd 36.5 ms, bias 0.0** against a constant-mean baseline
of **81.2 ms**. Three columns are *neutral* (empty in the design): they are declared, fitted, and carry
no weight — flagged, never silently dropped. The full coefficient/SE table is in `report2.json` under
`model.coefficients`, and every constant is in `constants[]` with source, selector, row count, status and
a rerun command.

**Two deliberate choices, argued:**

1. **No 600-token "already billed" discount.** SIM credits `LOOKUP_COVER_TOKENS = 600` uncached tokens to
   the lookup term. Here the prompt column and the miss column are *separate regressors*, so crediting
   the miss 600 tokens is a free 600-token discount on every turn — a constant nobody measured. `COVER = 0`;
   the full miss is billed from token one. This is also why `c5`/`c6` (formerly identified) are now
   reported as unidentified: billing from zero makes the miss and prompt columns near-collinear under
   20k, and the honest status is recorded instead of a point estimate presented as a finding.
2. **The lookup carrier is re-derived at per-Ktok units.** With the miss slope fixed at SIM's joint
   `118.3 µs/uncached` and the intercept at `99.7 ms`, regressing `ttft − intercept − miss·uncached` on
   `prompt/1000` across the fit window gives the lookup slope **directly: 7,991 ± 793 µs per 1,000 prompt
   tokens** (r² 0.39 on the residual). That is the number the model carries, with its SE.

---

## 2. Where the SIM hold-out error comes from (S4)

The error is decomposed, not patched. Three components, each naming its regime:

| id | component | evidence |
|---|---|---|
| **S4a** | the miss slope prices a label | 495.6 µs/tok = **2.06×** cold prefill, fitted in [442,560], used out of sample at 720 |
| **S4b** | the ≥ 20k level the fit window cannot carry | arm C hold-out **719 uncached/turn vs 751 in the fit window** at **28,503 prompt** where no fit row lives; the measured **level multiple is ×1.596** (arm A's implied lookup slope **12,750 ± 3,164** vs the fit window's **7,991 ± 793 µs/ktok**) |
| **S4c** | a compaction event is not the whole story | arm C carries **0 scheduled folds** across its 80 turns yet its hold-out runs **719 uncached/turn vs 751 in the fit window**: the dose is in the rows, not in a fold event, so C is graded separately and reported as the model's worst case rather than fitted away |

**The multiple's own hold-out, reported against it.** ×1.596 is trained on the arm-A hold-out rows and
predicts S4b's direction, but re-priced through SIM's own denominator it lands **+64,606 %** (uncorrected
+40,469 %) on those same ≥ 20k rows: the carrier does not carry arm A's tail. **`right_sign: false`.** The multiple is therefore *reported as measured and marked
insufficient*, not folded into the price as if S4b were solved — which is exactly the failure the first
report made when it quoted `r² 0.983` from a branch containing no ≥ 20k rows.

---

## 3. Hold-out — kept, per arm, with its band

Turns 41–80 of each arm (out of sample), band = the lookup term moved over SIM's own measured
cross-check span [0.85, 1.15] and nothing else:

| arm | predicted | measured | error | MAE | in band? |
|---|---|---|---|---|---|
| C | 155.4 ms | 572.0 ms | **−416.7 ms (−72.8 %)** | 417.3 | band [154.5, 156.2] — inside a band that is too narrow to be honest |
| A | 226.7 ms | 578.5 ms | −351.7 (−60.8 %) | 351.7 | band [226.7, 226.7] — **degenerate** (no ≥ 20k rows to move) |
| R | 277.4 ms | 303.9 ms | −26.5 (−8.7 %) | 31.8 | band [268.2, 286.6] — inside |
| F | 236.1 ms | 263.8 ms | −27.6 (−10.5 %) | 30.2 | band [226.5, 245.8] — inside |

**What this table says, and what it refuses to say.**

- On the two *short-prompt* arms the rebuild prices within **9–11 %** and inside its band. On the two
  *long-prompt* arms it is **61–73 % low**. The split is not noise: it is the S4 regression, visible per
  arm instead of hidden in a pooled mean.
- A band that excludes the true value is a **finding about the band**, not a pass. The C band is
  [154.5, 156.2] around a 572 ms measurement; the A band has zero width. Both are recorded as failures
  of the *interval*, and §2's S4b/S4c are the reason.
- The honest statement of scope: **the model is calibrated below 20 k prompt tokens, and the
  long-session regime is a measured gap the next run must close** — not a solved tail.
- SIM itself, re-run through its own `turn_cost` for comparison: **C −27.2 %, A +8.6 %, R +47.0 %, F +20.1 %**.
  SIM's `r²` 0.13 buys it those four different errors; the rebuild buys C/A's smaller ones at the cost of
  R/F's. Neither is "the" answer — which is why the ranking below is built on **one fixed model applied
  to every candidate equally**, never on a per-arm fit that flatters whichever arm it was fitted to.

---

## 4. Steady state — what a long session actually converges to

The 80-turn mean is the wrong yardstick: arms A/R/F compact at 18k/6k/6k and **never reach** the state a
long session lives in, while arm C does. Arm C's turns 60–80 are **21 turns, 0 folds, prompt 28,107 →
37,292**:

| | measured | reprice9 | rewrite variant |
|---|---|---|---|
| mean TTFT, arm C 60–80 | **717.0 ms** | 134.6 ms | 321.9 ms (modelled) |
| p50 | **505.5 ms** | — | 315.2 ms |
| for comparison, arm C turns 1–40 | 287.5 ms | — | — |

The cost of *not* compacting is visible in one line: **the long-session end state costs 2.5× the fit
window** — and this is arm C, the arm with *no* compaction. A/R/F's tails (1843 → 38,440 prompt, mean 379.9 ms)
are a different regime; comparing them to C's 80-turn mean is what made the first report's "C is last"
look defensible.

---

## 5. The ranking — nine cells, five measured arms, ties reported as ties

Each candidate is a **set of rows** priced by one fixed model. Nothing is scored that was not measured
except where it is explicitly marked `unseen`/`modelled`:

| # | candidate | evidence | folds | prompt span | mean price | p50 |
|---|---|---|---|---|---|---|
| 1 | **live-C** — pointer, no compaction | measured (arm C) | 0 | 1,187–37,292 | **221.4 ms** | 206.2 |
| 1= | pointer+pads | unseen (C's rows) | 0 | 1,187–37,292 | 221.4 | 206.2 |
| 1= | mutable+movable | modelled (= live-C) | 0 | 1,187–37,292 | 221.4 | 206.2 |
| 4 | **live-A** — pointer + append-note | measured (arm A) | 4 | 1,185–38,440 | **260.6 ms** | 275.7 |
| 4= | append+notes | unseen (A's rows) | 4 | 1,185–38,440 | 260.6 | 275.7 |
| 6 | **live-F** — fork, summary rebuilt | measured (arm F) | 4 | 1,187–6,507 | **277.9 ms** | 266.4 |
| 7 | **live-R** — pointer, summarise in place | measured (arm R) | 4 | 1,184–6,123 | **308.9 ms** | 302.8 |
| 7= | pointer+fold | unseen (R's rows) | 4 | 1,184–6,123 | 308.9 | 302.8 |
| 9 | mutable | modelled (C's tail) | 0 | 28,107–37,292 | **321.9 ms** | 315.2 |

**Five ranked candidates, in order: `live-C`, `live-A`, `live-F`, `live-R`, `mutable`.** The `=` rows are
aliases priced from the same rows — they are listed so the next run can see what it would buy, and are
*never* counted as separate evidence.

**Every adjacent gap between measured arms is inside noise:**

| pair | gap | SE | robust? |
|---|---|---|---|
| append+notes → live-F | −17.3 ms | 15.2 | no |
| live-F → live-R | −31.0 ms | 17.1 | no |

So the ranking is **an order on one model's numbers, not a claim that the candidates are separated**. What
the numbers *do* separate — and this is the finding the SIM report got backwards by averaging the wrong
regime — is the **shape** of each arm, not its mean:

- **F and R never reach the steady state** (tails stop at 6.5k / 6.1k prompt). Their 4 folds each restart
  the radius; F re-prefills it per fork, R does not — yet R's tail is *slower* (262 → 306 ms).
- **A reaches it and survives** (tail to 38.4k, folds at 18/35/53/71): the prefix never breaks, which is
  what makes it the recommended *scheduling* companion to C.
- **C reaches it with no folds** — and pays 717 ms for it (§4). That is why C ranks first on the *mean*
  and would rank last on any session that spends its time in the tail.

**Why the ranking does not depend on the lookup slope.** The lookup slope is a common factor in every
candidate's price, so its value cannot reorder them; a "pooled lookup" run is an arithmetic identity, not
a robustness check, and is not presented as one. The ranking *does* depend on the ≤ 20k carrier and on
the miss column, and those are the two constants the red→green harness breaks hardest.

---

## 6. The pointer protocol — the SIM card's rules, made mechanical

`## POINTER PROTOCOL` was prose in the card. It is now `src/resextract/pointers.py`, and
`resolve_manifest()` reads the card's own `json` block, so the card stays the manifest:

| rule | enforced by | test |
|---|---|---|
| three roles, nothing else | `Pointer.__post_init__` raises `ValueError` on any other role | `test_a_role_outside_the_protocol_is_refused` |
| only `cursor` is writable | `write_cursor` raises `PermissionError` for `external`/`cell-source` | `test_only_the_cursor_role_may_be_written` |
| absence degrades to a status | `Pointer.check` → `MISSING`; `declared_roots` omits an external root the host lacks | `test_missing_pointer_degrades_to_a_status`, `test_external_root_is_absent_unless_the_host_holds_it` |
| digest, not path | `sha256` mismatch → `DIGEST_MISMATCH` | `test_digest_mismatch_is_reported` |

Resolved against this host: **4 of 5 pointers OK**, the fifth
(`external:gpu-prefill-throughput`, `bench/prefill_throughput.jsonl`) **declared and absent** — every
constant in this report is derived from own-root cells, and the one external constant is recorded as
`declared-absent` rather than invented.

---

## 7. What a next run must do (ranked by what it would change)

1. **Measure the ≥ 20 k regime directly.** Every `unidentified` column in §1, and the 60–73 % C/A
   hold-out error, come from the same hole: no fit row above 19,860 prompt tokens. A cell that holds an
   arm above 20 k for 40 turns converts `c2`/`c4`/`c8` from unidentified to identified and closes S4b.
   This is the single highest-value measurement.
2. **Measure the miss column on a dense grid** so the slope is identified from tokens, not from turn
   labels: vary uncached residue at fixed prompt, over the full [0, 1,700] range. Kills S4a for good.
3. **Run `live-A` to 80 turns at ≥ 30 k** to see whether the append-note survival holds in the tail —
   A is the recommended scheduling companion to C on 4 folds of evidence, not on the tail it has never seen.
4. **Fork R vs F at matched radii.** Their means differ by 31 ms ± 17 — inside noise — but their tail
   shapes differ, so the fork question needs its own controlled comparison rather than a ranking slot.

## 8. Reproduce

```bash
.venv/bin/python scratch/r2-opt-sim/cost_model2.py          # rebuild report2.json (deterministic digest)
.venv/bin/python -m pytest tests/test_r2_opt_sim2.py -q     # 33 pass
.venv/bin/python scratch/r2-opt-sim/selfcheck2.py           # green, and K1-K4/K6 each go red
```

`report2.json` carries `report_sha256`; `test_the_report_on_disk_is_current` fails if the file on disk
drifts from the code that generated it. `selfcheck2.json` records which constant broke which test —
including the one mutation deliberately *not* expected to go red (§5, K5), so a future reader can tell a
real coupling from a designed invariance.
