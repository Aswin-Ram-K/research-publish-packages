<!-- Pre-registration, sections 1-9 ONLY.
     Source: the read-only target repository (HEAD 907fa39)
     Cut at "## 10. Results" — the frozen pre-registered protocol, not the appended results.
     Sections 10/11 (appended results and the CLOSE resolution) are in ../results/REPORT.md. -->

# P03 comparison: does a fine-tuned encoder head beat our 4B deciders?

**Branch:** the pre-registration branch, cut from the integration tip `79c1c7d`.
**Pre-registered:** 2026-10-04, BEFORE any code runs. This file is **never edited afterwards**; results are
appended and the resolution is recorded at the end.

**Why this experiment and not a 4B fine-tune.** The operator approved the **~1 GPU-hour encoder
comparison** (open decision **D-5**). The literature says a small encoder wins at N ≥ 4 on accuracy,
latency *and* cost — but **every public "small encoder wins" result compares the encoder against a
*prompted* zero-/few-shot LLM, never against a fine-tuned generative decider**, and GLiNER's win is span
extraction rather than a typed single-label decision. **No published measurement covers the comparison we
need.** Our own data points the other way: our 421M encoder-style `laya-typed-decisions` scored **0.374**
against our fine-tuned 4B's **0.6684**. So this is genuinely open, and our fixture is the load-bearing
evidence.

---

## 1. The one sentence this experiment exists for

**For a typed decision with 2–8 options, does a fine-tuned encoder decision head reach or beat our 4B
generative deciders on the same held-out instrument — and does its native per-option distribution buy
better calibration?**

## 2. Hypotheses

- **H1 (accuracy).** A fine-tuned encoder head reaches **≥** the 4B deciders' accuracy on the fixture.
  *Stated against the null in both directions*: the literature supports an encoder at N ≥ 4, our own
  421M result contradicts it, and the comparison that would settle it has not been published.
- **H2 (calibration).** The encoder's per-option distribution is **better calibrated** (lower ECE, lower
  Brier) than the generative deciders' — because its options are **output neurons over a softmax**, so the
  four measured contaminants of generative probability extraction (option-ID token bias, symbol-set bias,
  order sensitivity, surface-form competition) **do not exist by construction**.
- **H3 (latency).** The encoder is **faster per decision** than the 4B (one forward pass, no decode loop).
- **H4 (diagnostic).** Encoder accuracy is **not** monotone in parameter count across the three heads,
  mirroring the non-monotonicity we already measured on our own ladder (`K07` **15/28 at 2B →
  11/28 at 4B**).

## 3. Settled results this experiment will NOT re-measure

1. Our 4B deciders' fixture accuracy: **decider-4b 0.6684**, imajev-4b **0.645**, and the reproduction
   **0.6789** in P04 with a new compiler. Taken as given — **and used as the control**.
2. `laya-typed-decisions` (421M, ModernBERT-style encoder) at **0.374**. Taken as given.
3. Constrained decoding on a *decision* field improves accuracy or is neutral, and on a *reasoning* field
   it is destructive (GSM8K 86.5 → 23.4). We are not re-running that; see
   the read-only target repository's typed-channel note §11.
4. **M8**: a competent model handed an answerable prompt stops being a router; the fix is a typed channel.

## 4. The instrument, and the contamination problem it creates

**The instrument is `P05`** — 190 cases, sha256
`076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`, the same instrument our 4Bs scored on.
It is **never trained on, never used for model selection, and touched once** at the end.

**This forces the training corpus to be something else.** Training an encoder on the instrument would
destroy its independence and make every number here worthless. The corpus is:

**P04's generated corpus** — 1,000 construction-F54 cases, seed `20261004`, digest
`c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66`, 210 families / 18 clans, split
600 revision / 200 H-A / 200 H-B **by family**. Three properties make it the right choice:

- **The F54 is computed, not judged** — no model is the ground truth, so training on it cannot inherit a
  teacher's errors.
- **The contamination lint has already been run in this direction**: revision-corpus vs the 190 fixture
  removed **0 rows** on a ≥2-shared-8-gram rule, over 114,000 pairs. **Re-run it for the training split
  and report it** — this is F4 below.
- It is already in the tree with its manifest, so the corpus is auditable.

**Split, by family, no family straddling:** train on **600 revision + 200 H-A**; use **200 H-B
(unseen families)** as a development set for early stopping; **the 190 fixture is the sealed test set.**

## 5. Method

1. **Candidates** (all permissive, all ≤ 400M — verified licences in
   the read-only target repository's typed-channel design note §4):
   - `answerdotai/ModernBERT-base` — **Apache-2.0**, 149M
   - `microsoft/deberta-v3-base` — **MIT**
   - **SetFit-style** (frozen sentence-transformer + logistic head) as the **labels-thin arm**, because
     SetFit reaches within ~1 point of a 3B prompted model at 110M with ~30 s of training
2. **A majority-class baseline** and a **shuffled-label control** are mandatory arms (see §7).
3. **Training**: supervised classification over the option set, **epoch 1 as the pre-registered operating
   point** (every source found reports epoch 1 optimal for encoder fine-tunes), early stopping on the H-B
   development split. Temperature scaling fitted on H-B for calibration.
4. **Evaluation**: the sealed 190 fixture, once, per candidate. Report **accuracy, ECE, Brier, and per-class
   accuracy** alongside the three known baselines from §3.
5. **The comparison is paired** — same 190 cases, same option orders — so the analysis is **McNemar on
   discordant pairs, and the MDE quoted must be the PAIRED one** (**M11**: the unpaired figure overstated
   our blind spot by ~3× and would have excused a detectable harm as noise).
6. **Record the option order asked**, and re-run the fixture with the options permuted for the encoder arm
   only if time allows — **that is an exploratory add-on, reported separately, never folded into H1.**

## 6. Falsifiers

| # | Fires when | Verdict |
|---|---|---|
| **F1** | encoder accuracy **<** 0.6684 (the best 4B) | **H1 is FALSE.** Report the crossover honestly: the encoder does not win on *our* fixture, and say that the published "encoder wins" evidence is encoder-vs-prompted-LLM |
| **F2** | a head's development accuracy **≤ majority-class baseline** | training failed → **VOID for that arm**, not a result about encoders |
| **F3** | encoder ECE **≥** the decider's ECE | **H2 is FALSE** — the "native distribution" argument does not survive contact |
| **F4** | the lint finds **any** ≥2-shared-8-gram overlap between training rows and the fixture | **RUN VOID** — the instrument was contaminated |
| **F5** | the known baselines (§3) are not reproduced when re-scored | **RUN VOID** — the control cannot report zero |
| **F6** | a head's latency is **>** the 4B's measured 0.075 s/decision warm | **H3 is FALSE** |

**A falsifier is required and F1 is the one that matters**: this experiment exists to find out whether the
literature's crossover applies to a *fine-tuned* comparison, and "no" is a publishable, useful answer.

## 7. Instrument validation — the controls must be able to report the opposite

1. **Shuffled-label control**: train one head on randomly permuted labels. It **must** score near chance
   on the fixture. If it scores well, the pipeline leaks or the fixture is trivial.
2. **Majority-class control**: must score at the class base rate, and **its ECE must be poor**. A detector
   that cannot show a badly-calibrated arm cannot certify a well-calibrated one.
3. **Sealed-set discipline**: the fixture is scored **once per candidate**, and the run manifest records
   that it was read exactly once.
4. **The lint runs in both directions** (training→fixture and fixture→training), and is **shown to fire**
   on a seeded copied row before it is trusted to be silent.

## 8. Budget

- **Training**: 3 heads × minutes (encoder fine-tunes measured at 4–53 min in the literature) → well under
  **1 GPU-hour**. **Hard cap: 2 GPU-hours.**
- **Inference**: 190 cases × 3 heads on an encoder = seconds.
- **Model API calls: 0.** This experiment needs no remote model — that is part of why it is the cheap one.
- **Wall clock cap: one working session.** If training has not converged by then, report what exists.

## 9. Out of scope

Any 4B fine-tune (open decision **D-6**, gated on the recorder) · the bounded-substitution-edit experiment
that P04's resolution names as its successor · grammar-constrained generative arms (already measured) ·
span-extraction or NER tasks (GLiNER's wins are a different task shape) · production traffic.

