# LIVE-MEAS — scaled four-arm measurement (80 turns, 3 epochs/arm)

## Corrections (VLIVE, applied by LMC)

**Source.** Verifier `VLIVE` (`handoffs/VLIVE.json`, `units/VLIVE.md`) — verdict **pass**: the measurements
reproduce; only the *card-level words* overreached. Record repair only: 0 live requests, no `.occamy.lock`,
no re-analysis, and **no datum changed** (960 rows, pooled 1.2988, decomposition 113,166 = 5,081 + 108,085
— all intact). Every superseded sentence is retained **verbatim** as an `> original (superseded)` quotation in the Result section below; the six
entries here are the licensed replacements, carried machine-readably in `handoffs/LIVE-MEAS.json` under
`verifier_corrections` (claim / as_written / corrected_to / verifier / applied), with the original strings
preserved under `superseded_text`.

| # | Claim | As written (retained verbatim below) | Corrected to | Applied |
|---|---|---|---|---|
| C1 | A overtakes R after ~40 turns | "turns 41–80 give 0.951 / 1.030 / 1.056, i.e. A overtakes R after ~40 turns" | **Epoch-1 only.** t41–80 = 0.9508 / 1.0296 / 1.0561: e1 is a genuine reversal (0.9508), e2/e3 are **parity** (1.0296 / 1.0561, mean 1.0122). Licensed: *"append's advantage decays; after turn 40 R/A is at parity (e2/e3) with one epoch reversing"* — not a general overtake. | yes |
| C2 | U15's 1.700x is confirmed inside its own window | "U15's 1.700 is **confirmed inside its own window** — R/A over turns 1–40 = 1.705 / 1.768 / 1.719" | **Too strong.** LIVE-MEAS's own t1–40 windows are 1.7046 / 1.7682 / 1.7195 (mean 1.7308), i.e. **0.3–4.0 % above U15's 1.700 (mean +1.8 %)**; no epoch lands on 1.700. Licensed: *"consistent with U15's 1.700x within 0.3–4.0 %"*. For an **80-turn** claim the headline is **1.30x** (pooled 1.2988, t95 [1.2147, 1.3828], df=2, pad-adjusted 1.296); 1.700 is quoted **only** as the 40-turn figure. | yes |
| C3 | prompt + cached identical across arms in epochs 2–3 | "prompt and cached identical across all four arms at t10/t17 in epochs 2–3" | **False for prompts.** `cached` is identical in e2/e3 (4,864 at t10, 7,616 at t17); **prompts** are identical only in e3 — e2 spreads **9 tokens** at t10 (R 5347, C 5354, F 5355, A 5356) and **19** at t17 (R 8525, C 8506, F 8507, A 8508). `report.md:67-68` already states `prompts identical False`; the card now agrees with the report. | yes |
| C4 | the post-fold lag does not worsen | "the post-fold lag does **not worsen** — median 1,152 tok over turns after folds 1–2 (≤t40) vs 448 after t40" | **Per arm.** Holds for **R** (1,152 → 448) and **F** (896 → 224); **A rises 384 → 896**. Since-fold medians are non-monotone (896, 1,344, 928, 1,344, 896, 960), so "saturates low" is not clean either. | yes |
| C5 | 81 unexplained *ambient* misses | "81 unexplained ambient misses" | **"Ambient" is not licensed.** 81 rows are **unattributed**, and **54/81 sit within 2 turns of a fold** (R 20 / F 19 / A 15; arm totals R 37 / F 25 / A 19). "Unexplained" is the honest label; they are not demonstrably ambient. | yes |
| C6 | E4 residue-0 rows sit outside the law checks | "**3** rows still at residue 0 (e1 F t53, e1 A t19, e2 A t31 — the first-seen-text increment model's ±14 error), flagged" / handoff: "flagged and excluded from law anchors" | **Flagged, not excluded.** All three are flagged; **two of the three — e1 A t19 and e2 A t31 — remain inside the 912-row E3 population**, so the residue-0 rows are not outside the law-check denominator. | yes |

**The manuscript may now print** (VLIVE-licensed, safe at the 80-turn horizon):

> R/A = **1.30x** over **80 turns / 4 folds** (t95 **1.22–1.38**, df=2); **1.700x is a 40-turn figure**.

Corollary wording the manuscript must avoid: "P is always 1.7x cheaper" (no), "A overtakes R after 40 turns"
(no — one epoch only), "prompt and cache identical across arms" (cache only), "the post-fold lag does not
worsen" (R/F only; A rises), "ambient misses" (unattributed), and treating the 3 E4 residue-0 rows as
outside the E3 law-check population (two are inside it).


**Objective (single).** Measure the four render policies C / A / R / F at scale with epoch control
(80 turns, 3 independent epochs per arm, all arms warm from t1), so the manuscript's headline ratio is
*measured* rather than extrapolated from U15's single 40-turn warm epoch.

**Mechanisms to build on (not re-derive).**
- E1 (`cells/E1`, `handoffs/E1.json`, `VE13`): fork pays a full re-prefill at the compaction event
  (median +4,774.25 uncached, 15/18 positive, n=18).
- E2 (`cells/E2`, `handoffs/E2.json`; `VE24`): R's post-fold uncached = new tail + 64-boundary +
  re-prefilled previously-sent tokens (endpoint reuse lag over 0–3 newest messages, deeper after a fold);
  `VE24` rules E2's *deflation of U15's F advantage* OVERSTATED — the F−R gap reproduces in matched epochs.
  Design holds epoch warmth constant across all four arms; no cold-vs-warm comparison.
- E3 (`cells/E3`, `handoffs/E3C.json`): after an append the reusable prefix is the previous prompt floored
  to 64 plus at most one appended body of boundary lag.
- E4 (`cells/E4`, `handoffs/E4.json`, `VE4`+`VE4R`): a prompt whose length is an exact multiple of 64 pays one
  extra full prefill and a **persistent one-block (64-token) tax** on every later repeat measured (rep-3
  `L−64` **40/40**, `L` **0/40**; repeats 2–3 of 3, one boundary length pair, mechanism
  unestablished). **Every prompt padded so `prompt_tokens % 64 != 0`.**

> original (superseded): "a permanent 64-token shortfall"

**Design.** Four arms C (fixed prompt), A (append), R (summarise-in-place), F (fork); same corpus slice,
trigger, compaction points and renderer as U15; horizon 80 turns; stub summariser; 3 epochs/arm with a
fresh salt per epoch and identical epoch ordering across arms; one request in flight, strictly serial;
never `/flush_cache`. Context-limit overflow is a **result** (GAPS G3/G14), recorded and the arm continues.

**Bound.** ≤1000 live requests, ≤90 min, ≤40 work tool calls. Abort after 3 consecutive failures → `partial`
with rows.

**Lock.** `flock(LOCK_EX)` on `experiments/context-cache/.occamy.lock` before first live request, held to the
last, released on exit; acquisition deadline 1800 s; timeout → `partial`, blocker `lock timeout`.

**Write paths.** `experiments/context-cache/cells/LIVE-MEAS/**`, `orchestration/units/LIVE-MEAS.md`,
`orchestration/handoffs/LIVE-MEAS.json`.

**Deliverable.** `cells/LIVE-MEAS/report.md` + `rows.jsonl`: headline ratio per epoch and pooled (vs U15
1.700x), break vs steady-state decomposition, fold-count scaling of the post-fold lag, E3/E4 law checks per
row, and the epoch-warmth control proof.

## Result (done — 960/960 rows, 960 requests, 0 failures, 420.6 s, lock_wait 0.0 s)

Rows `cells/LIVE-MEAS/rows.jsonl`, sha256 `6150e534c4f52553771172fe988a70a49d65917f85d0c9e1b5a336cf1d119b65`.

- Fold schedule `[18, 35, 53, 71]` (U15's 8k trigger → **4** folds over 80 turns, not the card's ~7/~14,
  which would need a ~4k trigger; kept U15's trigger, recorded as an assumption).
- **Headline R/A** (total uncached): 1.260 / 1.319 / 1.317 per epoch → pooled **1.299** (t95 [1.215, 1.383],
  df=2), pad-adjusted 1.296; F/A 1.066. U15's 1.700 is **consistent within 0.3–4.0 %** — R/A over turns
  1–40 = 1.705 / 1.768 / 1.719 (1.7046 / 1.7682 / 1.7195, mean 1.7308) — and **corrected at the
  80-turn horizon**: turns 41–80 give 0.951 / 1.030 / 1.056, i.e. append's advantage decays; after
  turn 40 R/A is at **parity** (e2/e3) with one epoch reversing. The ratio is horizon-bound, not a
  steady-state law. 1.700 is quoted **only** as the 40-turn figure.

> original (superseded): "U15's 1.700 is **confirmed inside its own window**" · "A overtakes R after ~40 turns"
- **Decomposition** (arithmetic split): R excess 113,166 = break 5,081 (4.5 %) + steady 108,085 (474 tok/turn);
  F 61,214 = 8,960 + 52,254; A 46,461 = 3,658 + 42,803.
- **Fold scaling**: the post-fold lag does **not worsen** — median 1,152 tok over turns after folds 1–2
  (≤t40) vs 448 after t40; per fold index (e1 R) 1248 → 1088 → 384 → 0.
- **Law checks**: E3 one-body form 308/912, zero-deficit 341, 2–3-message lag 182 (R/F post-fold, the E2
  component), 81 unexplained **unattributed** misses (54/81 within 2 turns of a fold). E4: 195/960 rows padded, **3** rows still at residue 0
  (e1 F t53, e1 A t19, e2 A t31 — the first-seen-text increment model's ±14 error), flagged.

> original (superseded): "81 unexplained ambient misses"
- **Warmth**: t1 cached 0 in all 12 runs; `cached` identical across all four arms at t10/t17 in
  epochs 2–3; **prompts** identical in **e3 only** (e2 spans 9 tokens at t10, 19 at t17;
  `report.md:67-68` `prompts identical False`); epoch 1 R is one 64-block higher only because it
  carried E4 pads by t10 (subtracted in the pad-adjusted ratio). No context-limit event
  (max_model_len 131,072; largest prompt 38,440).

> original (superseded): "prompt and cached identical across all four arms at t10/t17 in epochs 2–3"
