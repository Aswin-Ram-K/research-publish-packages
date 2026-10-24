# The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control

---

## Abstract

Every public "a small encoder wins" result we were able to locate inside the target corpus compares that
encoder against a **prompted** (zero- or few-shot) LLM, never against a **fine-tuned generative decider**
(the claim and its audit trail are internal to the corpus, not an external survey — §2). That a fine-tuned
generative decider can beat a fine-tuned encoder at comparable effort is **already public** — a 2025
practitioner blog post reports exactly that on a binary ADE task (§2.1) — so we claim **no priority for the
direction**; what we claim is this fixture, its controls and its diagnosis. We measure the fine-tuned
comparison on a sealed typed-single-label decision fixture.

**Headline.** The best fine-tuned encoder head scores **0.3474** and loses to the fine-tuned 4B decider at
**0.6789** — the **declared primary baseline** (author decision 2026-10-15), the auditable same-run arm —
with paired McNemar **b = 27, c = 90, ψ = 0.616, Δ = −0.3316, exact
p = 4.167e−09**. The control that could have contradicted this is the mandatory **majority-class control**,
and it did contradict the candidate's framing of itself: majority-class returns **0.4526**, beating *every*
fine-tuned encoder head by **+0.1053**. The second control that could have contradicted the measurement is
the **shuffled-label arm**, and it moved the other way from a spurious win: it returns **0.2316**, below the
fixture's **0.2911** chance floor. A third control guards instrument integrity: our n-gram leak criterion
(≥ 2 distinct shared 8-grams within one row pair, both directions) flagged **0 of 152,000** training↔fixture
pairs — and, to show the criterion can fire, it flagged three deliberately seeded copies at **13 / 44 / 57**
shared 8-grams (pair maxima). Against the *published, pre-registered* baseline **0.6684** — which
**cannot be re-scored** from the tree — the same head loses by **0.3210** ("0.32") against the **secondary** baseline **0.6684**.
**The two figures use two baselines and must not be read as one:** the headline **0.3316** ("0.33") is
computed against the **declared primary 0.6789**, while **0.3210** ("0.32") is computed against the
**secondary/published 0.6684**, which is the pre-registered F1 threshold and which
cannot be re-scored from the tree.

**Correction carried.** Fixing three defects lowered the **SetFit-MPNet** arm monotonically
(**0.3158 → 0.2947 → 0.2632**), but the same order-probe fix *raised* the **ModernBERT-base** arm
(**0.342105 → 0.347368**). The universal claim "every correction moved the affected arm down" is false; the
SetFit arm returned the opposite direction from the ModernBERT arm, which is the control on that claim.

**Not in this paper.** We make **no latency claim**: the encoder heads were timed locally in one forward
batch while the 4B figures come from a served stack's stored rows, so the tree cannot support a fair
latency comparison (see §6.1). We also do **not** report κ = 0.9014 (first blind reader) or κ = 0.8577
(second, independent blind reader) — nor their mutual κ = 0.9125 — as inter-annotator agreement: both
labellers were **models**, so this is machine reproducibility of the fixture, not human agreement. The
second reader **partially** replicates the first: the κ magnitude holds (both ≥ 0.85) but the exact 0.90
headline does not. An independent human labeller is still owed (§6.2).

---

## 1. Introduction

A common empirical shape in applied model-selection work is a crossover: at small label-set sizes *N* a
large language model (LLM) wins or ties, and above some *N* a small fine-tuned encoder takes over. The
canonical instance in the corpus we work from is an N-dependent table in which the encoder wins at N = 4
(AG News 94.11–94.63 vs 91.35; DBPedia at N = 14: 99.27–99.40 vs 98.83) and loses or ties at N = 2. The
table's decisive property for this paper is not its numbers but its **comparison class**: the LLM side is an
**API LLM** — i.e. *prompted*. We read that explicitly in the corpus's own errata
(`docs/DECIDER_STACK_DECISION.md` §11.6 — source repository, not in the released package): *"the N-dependent crossover table in §11.2 is
encoder-versus-**API LLM**, i.e. prompted."*

If the crossover is a property of *prompting* rather than of *scale*, then it should not survive when the
generative side is given the same resource the encoder gets — supervised fine-tuning on the same task and
the same labels. That is the hypothesis this paper tests, and the result is negative for the crossover.

**Thesis.** Every "a small encoder wins" result we were able to locate compares the encoder against a
**prompted** LLM, never against a **fine-tuned** generative decider; under the fine-tuned comparison the
crossover does not appear on our fixture.

**Novelty, stated narrowly.** We claim **no priority for the direction** of the result. That a fine-tuned
generative model can beat a small fine-tuned encoder on a classification task is already in the public
record: a 2025 practitioner experiment on binary adverse-drug-reaction classification reports a fine-tuned
Llama-3.2-3B LoRA at F1 **93.1** against ModernBERT-large at **89.2** at comparable training cost
(Simmering, 2025 — a blog post, **not** peer-reviewed; §2.1). What is new here is narrower, and it is what we
claim: (i) the **sealed typed single-label decision fixture** — 190 cases, N = 2–8 named options per case,
74 distinct labels — rather than binary sentence classification; (ii) the **option-order permutation
control**, whose final pass flips **0** cases for every candidate head; and (iii) the **majority-class
control**, which outranks **every** encoder head (0.4526 vs 0.3474, +0.1053) — a result the public
counter-case does not contain. The contribution is the **artefact diagnosis on this fixture**, not the
discovery that a fine-tuned generative decider can win.

**Contributions.**

1. A like-for-like **fine-tuned vs fine-tuned** measurement on a sealed typed-single-label decision
   fixture: best fine-tuned encoder head 0.3474 against a fine-tuned 4B decider at 0.6789 (auditable,
   paired) and 0.6684 (published, not re-scorable). The *direction* is already public (§2.1); what is new is
   this fixture and its controls. §4.1–§4.2.
2. The finding that the **majority-class control beats every candidate head** (0.4526 vs 0.3474, +0.1053) —
   so the interesting claim is not merely "the encoder loses to the 4B" but "the encoder loses to a
   constant answer". This control, the typed fixture and the order-permutation probe are the parts of the
   result for which we claim priority. §4.3.
3. A **calibration** result whose verdict is **convention-dependent**: F3 fires on one stored ECE
   convention (head 0.0994 ≥ decider 0.0551) and does *not* fire on the other (0.0994 < 0.1547). We present
   both and name the ambiguity rather than resolving it. §4.6.
4. A **negative method result (M12)**, carried as a correction to the corpus's own summary: the claim that
   "every correction moved the affected arm down" is true for **SetFit-MPNet only**. §4.5.
5. An explicit statement of what the evidence **cannot** support: latency (§6.1) and human agreement on the
   fixture labels — which **two** blind model passes do not supply, since the second only **partially**
   replicates the first (§6.2).

The paper is deliberately narrow. It is a single-fixture, single-host negative result, and §6 says so.

---

## 2. Related work

### 2.1 The works that make the "encoder wins" claim

The corpus's own audit of this literature lives in `docs/DECIDER_STACK_DECISION.md` §11.6, committed as
`ad301ae` ("errata — the encoder recommendation was stronger than the evidence supports"). It is the
citation for this paper's core literature claim, and it **does** support the claim — with an important
qualification about its strength. Verbatim from §11.6:

> *"Every public 'a small encoder wins' result compares the encoder against a **prompted, zero- or few-shot
> LLM** — not against a **fine-tuned generative decider**. GLiNER's win is **span extraction (exact-match
> F1), not a typed single-label decision**; GLiClass has **no measured LLM head-to-head** at all (its own
> comparison table is qualitative); and the N-dependent crossover table in §11.2 is encoder-versus-**API
> LLM**, i.e. prompted. **No published measurement was found of a small encoder beating a fine-tuned
> generative model on a typed single-label decision** — verified-absent, and the second lane checked it
> explicitly."*

And from the commit message of `ad301ae`:

> *"A second independent typed-channel lane ran with a stricter evidence base. Every public 'small encoder
> wins' result compares the encoder against a PROMPTED zero/few-shot LLM, not against a fine-tuned
> generative decider … Nobody has published the comparison we need, so our 190-case fixture remains the
> load-bearing evidence."*

**Qualification, stated rather than buried.** This is a claim about a **literature search**, and the search
protocol — databases, query terms, dates, inclusion rules — is **not recorded in the corpus**
(this record's internal reference notes §B3; an internal working record not included in the released material). We therefore write "*we were able to locate*" and "*no published measurement was found*",
not "*no such result exists*". A reviewer cannot audit a "verified-absent" claim whose search is unreported;
this is the single largest sourcing gap in the paper (§6.4; recorded in this record's internal open-questions log, an internal working record not included in the released material).

The specific works, with the identifiers the corpus actually carries:

- **The N-dependent crossover table.** arXiv `2602.06370`, cited at `DECIDER_STACK_DECISION.md` §11.2. The
  corpus records **no title, authors or venue**; we cite the identifier only and flag the entry as
  incomplete in `REFERENCES.bib`. Its encoder-side wins, its latency spreads, and its cost figures are all
  recorded in the corpus, but its comparison class is a prompted API LLM.
- **A corroborating throughput result.** arXiv `2512.12677`, same section: ModernBERT-base classifies
  patents at 93.45 samples/s vs Llama-3.2-3B at 1.88 and Qwen3-4B at 1.26; distilling a fine-tuned 3B into
  ModernBERT-base is recorded as retaining ≥ 97 % of teacher F1 at ~45× throughput. Again: identifier only,
  no title/authors/venue in the corpus.
- **PriDe** (option-ID token bias): arXiv `2309.03882`, ICLR 2024, cited at `DECIDER_STACK_DECISION.md:415`
  and `:500`. This grounds the position/order-bias concern that our own order-permutation probe measures
  (§3.4, §4.5).
- **Grammar-constrained decoding (GCD)**: arXiv `2305.13971`, EMNLP 2023, and ACL 2025 Industry
  (`2025.acl-industry.34`), cited at `DECIDER_STACK_DECISION.md:494–495`. A3 does not use GCD; these are
  listed because the same errata section uses them, and they are *not* sources for the crossover claim.

**The counter-case, now sourced — and what it does to our claim.** The strongest single threat to a
one-sided reading of our thesis is no longer unsourced, and we engage it rather than name it. It is a
**practitioner blog post, not a paper**: Paul Simmering, *"ModernBERT vs LLMs for Detecting Adverse Drug
Reactions"*, published 12 January 2025, `https://simmering.dev/blog/modernbert-vs-llm/` — **no DOI, no
venue, not peer-reviewed**, cited as `simmering2025modernbert`. On binary adverse-drug-reaction sentence
classification (ADE corpus, N = 2) it reports a fine-tuned **Llama-3.2-3B-Instruct LoRA at F1 93.1 and 152
examples/s** against **ModernBERT-large at 89.2 and 87 examples/s**, with equal fine-tuning effort per arm
(*"All setups can be trained for under one dollar and in less than 15 minutes"*). **We claim no priority for
the direction of that result** — a fine-tuned generative decider can beat a small fine-tuned encoder at
comparable effort, and it is already public. Three properties separate its setting from ours: (i) its task is
**binary (N = 2) sentence classification**, not a typed single-label decision over N = 2–8 named options;
(ii) its decoder is a **3B** model against a 395M encoder — a ≈7.6× scale confound the author names himself
(*"Did it win by sheer size?"*); and (iii) its throughput edge is a **serving-stack** property: the author
records that adding the 30 s vLLM CUDA-graph preparation time drops the LoRA arm to **42 examples/s**, below
ModernBERT-large, and warns that *"this speed comparison was not comprehensive"*. Most importantly, the same
experiment **reproduces half of our diagnosis**: its prompted, DSPy-optimised few-shot Llama-3.2-3B arm
scored **80.7 F1**, below ModernBERT-large's 89.2 — *"Fine-tuning continues to outperform purely prompt-based
approaches, even when those are optimized using automated prompt engineering."* The counter-case is therefore
not evidence against the prompted-baseline artefact: it is an independent, if non-peer-reviewed,
reproduction of it on a different task, and it simultaneously sets the novelty boundary we accept above.

**One corpus claim is now sourced, and we cite it for its result.** The corpus's assertion that an
encoder-only RoBERTa outperforms a fine-tuned LLaMA2-7B on 77-class intent classification is supported by
Benayas, Sicilia & Mora-Cantallops (2024), *A comparative analysis of encoder only and decoder only models
in intent classification and sentiment analysis*, *Language Resources and Evaluation* **59**(3):2007–2030,
DOI `10.1007/s10579-024-09796-y` (`benayas2024comparative`). On BANKING77 (77 intents) the paper reports the
encoder-only arm ahead of the fine-tuned decoder-only arm, and a decoder-only serving penalty of one to two
orders of magnitude on a single T4 (29–108× at fixed output-token budgets). We cite it for that
peer-reviewed, same-task encoder-over-decoder result; we do not reuse the corpus's "125M" formulation (the
paper prints "approximately 110-120 million parameters") or its derived F1 gap, which the paper does not
print. GLiNER and GLiClass, previously unsourced, now have identifiers and are treated in §2.2.

### 2.2 What is adjacent but not the same comparison

Four near-misses are worth separating from our claim, because each is a different task or a different
comparison class; three of them are now sourced rather than merely named:

- **Span extraction vs typed single-label decision.** **GLiNER** (arXiv `2311.08526`; NAACL 2024,
  pp. 5364–5376, DOI `10.18653/v1/2024.naacl-long.300`; `zaratiana2024gliner`) is a **span-extraction (NER)**
  model whose recorded win is exact-match F1 on spans, against **zero-shot (prompted)** LLMs — a span
  extractor and a typed decision head are not competing on the same object. **One correction to the corpus's
  wording applies here:** that characterisation is accurate for GLiNER 2023/2024 itself, but the corpus
  applies it to the model id `fastino/GLiNER2.5-Decide`, which is a **text-classification decision model** —
  GLiNER2 (arXiv `2507.18546`; `zaratiana2025gliner2`) explicitly covers *text classification*, and the model
  card tags this variant a decision model for intent classification. We therefore cite GLiNER (2023/2024) for
  the span-extraction point and do **not** rest the claim on the decision-model variant. What GLiNER2's
  abstract does not state is whether its *"LLM-based alternatives"* comparison class is prompted or
  fine-tuned; we do not read it either way.
- **No measured LLM head-to-head.** **GLiClass** (arXiv `2508.07662`, 11 Aug 2025; `stepanov2025gliclass`)
  adapts the GLiNER architecture to sequence classification, and the corpus's claim that it has **no measured
  LLM head-to-head at all** is confirmed: its quantitative baseline tables contain only four cross-encoder/NLI
  models (`deberta-v3-large-zeroshot-v2.0`, `deberta-v3-base-zeroshot-v2.0`,
  `roberta-large-zeroshot-v2.0-c`, `comprehend_it-base`), no generative LLM (and no embedding/SetFit model)
  has any numeric row, GPT-4o appears only as a training-data annotator, and its LLM comparison is
  **qualitative prose**. This is an argument **from absence**, and we phrase it as one.
- **Prompted/typed deciders vs fine-tuned generative deciders.** The corpus also carries a published
  `laya-typed-decisions` figure of **0.374** and an `imajev-4b` figure of **0.645**. The `laya` figure is a
  *prompted/typed* baseline, not a fine-tuned decider. The `imajev` **0.645 is the H-A corpus stratum, not a
  fixture number** — the fixture figure is **0.6368** (`REPORT.md`, §"Two things … NOT defects") — and we do
  not place 0.645 in any fixture table. Conflating the two would be a straight numerical error.
- **Single-label decision vs router/selection.** A learned router deciding *which* model to call is a
  different object from a model deciding *which label applies*; we do not extend our result to routing.

**Adjacent, citable neighbours — marked `ADJACENT` in `REFERENCES.bib`.** Three further works were located
while searching for external backing for §2.1's absence claim. They are real and traceable, and they are
**not** sources for our central claim; none of them discharges §6.4's absence claim:

- **Kostina, Dikaiakos, Stefanidis & Pallis (2025)**, *"Large Language Models For Text Classification: Case
  Study And Comprehensive Review"*, arXiv `2501.08457` (`kostina2025llmtextclassification`): an encoder-vs-LLM
  text-classification study whose LLM arms are **prompted** — it supports the prompted-baseline half, but it is
  not a survey establishing the absence of a fine-tuned-generative comparison.
- **Li, Sleem, Gentile, Nichil & State (2025)**, *"Small Language Models in the Real World: Insights from
  Industrial Text Classification"*, ACL 2025 Industry Track, pp. 971–982, DOI
  `10.18653/v1/2025.acl-industry.68` (`li2025smalllanguagemodels`): the closest peer-reviewed
  equal-effort-adjacent evaluation found — it evaluates **both** prompt engineering **and** supervised
  fine-tuning for smaller models in industrial settings — but it is an evaluation, not a proof of absence, and
  its per-task results were not retrieved.
- **Weller, Ricci, Marone, Chaffin, Lawrie & Van Durme (2025)**, *"Seq vs Seq: An Open Suite of Paired
  Encoders and Decoders"*, arXiv `2507.11412`, accepted to ICLR'26 (`weller2025seqvsseq`): under *"the same
  recipe for both encoder-only and decoder-only models"* it reports that *"encoder-only models excel at
  classification and retrieval tasks"* and that *"a 400M encoder outperforms a 1B decoder on MNLI"* —
  matched-recipe, peer-reviewed support for the encoder side, but its headline task is **MNLI (3-way)**, not a
  typed single-label decision over N = 2–8 named options.

Our claim is only about the comparison class: encoder-vs-**prompted** LLM does not license the inference
encoder-vs-**fine-tuned** decider — and the one public fine-tuned-vs-fine-tuned counter-case (§2.1) is
engaged, not ignored.

---

## 3. Method

### 3.1 The fixture

The instrument is a sealed set of **190** typed single-label decision cases drawn from a project's own
decision corpus (`evals/fixtures/reflex-decisions.ts` in the source repository — not in the
released package; the shipped copy is `fixture/reflex-decisions.ts`), with **721** options total, **74** distinct labels
(51 of which occur exactly once), and per-case option counts distributed as K = 2 (33 cases), K = 3 (27),
K = 4 (76), K = 5 (54). Its sha256 is
`076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`; the fixture was read once
(`fixtureReads = 1`) and its digest was **unchanged before and after** the second-labeller pass, with the
second labeller's sandbox copy **byte-identical** to the target.

Three instrument properties matter for reading the numbers, and one is routinely misread:

- **Chance floor = 0.2911.** This is the *mean of 1/K over the 190 cases*, i.e.
  `(33/2 + 27/3 + 76/4 + 54/5)/190 = 55.3/190 = 0.29105263…`. It is **not** the majority-class prior. Do not
  conflate the **0.2911** floor with the **0.4526** majority-class control; they are different constructs
  computed from different things.
- **Option-0 rate = 0.3789**; **leaky majority rate over the fixture's own answers = 0.1474** (the rate at
  which the most common *fixture answer*, not option 0, is "always guess" — it is not the majority-class
  control either).
- **Label decidability is imperfect.** The fixture was authored by one worker and carries known flagged
  weak points; see §6.2 and the five owed corrections listed in this record's internal checklist (an internal working record not included in the released material).

### 3.2 The arms

Five arms were evaluated on the sealed fixture by the source experiment (EXP#12). All five accuracy figures
below are read from the per-arm `eval-*.json` and agree with `REPORT.md`'s §1 table to printed precision.

| arm | role | params | accuracy | 95 % CI | ECE | Brier |
|---|---|---|---|---|---|---|
| `modernbert-base` | candidate | 149,015,041 | **0.3474** | [0.2842, 0.4211] | 0.0994 | 0.2110 |
| `deberta-v3-base` | candidate | 183,832,321 | **0.3474** | [0.2789, 0.4211] | 0.1629 | 0.2458 |
| `setfit-mpnet` | candidate | 109,489,537 | **0.2632** | [0.2053, 0.3263] | 0.1536 | 0.2109 |
| `majority-class` | **control** | 0 | **0.4526** | [0.3842, 0.5263] | 0.2026 | 0.2661 |
| `shuffled-label` | **control** | 149,015,041 | **0.2316** | [0.1737, 0.2895] | 0.0808 | 0.1797 |

**The three candidate heads are 109M–184M parameter encoders.** They are, in the corpus's framing, the
"small encoder" side of the crossover: ModernBERT-base, DeBERTa-v3-base, and a SetFit-MPNet head. The
`shuffled-label` control reuses ModernBERT-base's architecture and parameter count (149,015,041) but is
trained on shuffled labels.

**⚠ `deberta-v3-base` did not train at the pre-registered operating point.** Its own recorded evidence:
train loss 1.1288 → 1.1235 over the two logged points (`results/REPORT.md:151`), dev accuracy 0.50 → 0.495 against a dev
majority-class baseline of **0.475** (`results/REPORT.md` §"Development curve (H-B, unseen families)", `:182`). Its 0.3474 must be
read as **"did not train"**, not "trained and failed to transfer". We do not present it as a completed arm;
it is listed to be complete about what was run and is excluded from the headline. The headline arm is
`modernbert-base`.

**Training is not bit-reproducible.** Three identical training runs produced ModernBERT epoch-1 dev
accuracies of 0.5150 and 0.5900 and fixture accuracies of 0.3421 and 0.3474 (`REPORT.md`, §"A caveat that is
not a defect"). A ±1–2 point band is honest for **every** head number in this paper, and all of our
conclusions have margins far larger than that band.

### 3.3 The baselines: two `decider-4b` figures, and which number uses which

There are **two** fine-tuned 4B (`decider-4b`, 4.66B params) figures in the evidence tree, and they are
**not** the same measurement. Both are real. The paper must say which figure each number uses, because they
differ by 0.0105 and the two candidate headline figures — **0.3210** ("0.32") and **0.3316** ("0.33") — come
from **different** ones. **The primary is declared: 0.6789.**

| baseline | value | source | re-scorable? | used for |
|---|---|---|---|---|
| **same-run reproduction** (F0_decider frame) | **0.6789** | `results/REPORT.md:39` (published), `:42` (re-scored), `:99` (`reproduces at 3 d.p. = True`) | **Yes** — per-case rows survive in the target repository's per-case decider rows; re-scored 0.6789 vs published 0.6789, `reproducesAt3dp = true`, `absoluteDifference = 4.7e−05` | **✅ DECLARED PRIMARY BASELINE** (author, 2026-10-15); the paired McNemar partner; Δ = −0.3316 ("0.33") |
| **historical, published (D-067)** | **0.6684** | `results/REPORT.md:36` (published row) | **No** — `REPORT.md:104`: `reproduces at 3 d.p. = None`; `REPORT.md:189`: *"cannot be re-scored. No per-case rows for that specific measurement are in the tree"* | the pre-registered F1 threshold the falsifier was written against; the source of **0.3210** ≈ "0.32" |

**✅ PRIMARY BASELINE DECLARED (author decision, 2026-10-15): 0.6789 (same-run).** It is the primary because
it is the **only auditable** figure and because it is the arm the paired test is actually computed against
(`results/REPORT.md:63`, `:64` — paired against the primary `decider-4b`
reproduction, on the
*same 190 cases, same option orders* as the heads). **0.6684 is reported as a secondary / robustness figure**,
retained for its **pre-registration role**: F1 was pre-registered against it
(`preregistration/EXP12-typed-channel-comparison-prereg.md:100`: *"encoder accuracy < 0.6684 (the best 4B)"*), and it is the figure
the working title's "0.32" comes from — but it **cannot be re-scored** (`REPORT.md:104`
`reproduces at 3 d.p. = None`; `:189` no per-case rows survive), which is why it is not primary. **The
conclusion is unchanged by the choice:** 0.3474 loses to both, and −0.3316 exceeds 2× either MDE (2.079×
paired / 2.446× unpaired).

**Every number, tied to its baseline:**

| statement | baseline | figure |
|---|---|---|
| headline shortfall (title, abstract) | **0.6789** — declared primary | **Δ = −0.3316** ("0.33") |
| paired McNemar: b = 27, c = 90, ψ = 0.616, p = 4.167e−09, paired MDE 0.1595 | **0.6789** — declared primary | computed against the primary |
| pre-registered falsifier F1 | **0.6684** — secondary | best head 0.3474 < 0.6684 → **F1 fires** |
| working title's "0.32" | **0.6684** — secondary | `0.6684 − 0.3474 = 0.3210` |
| H-A / H-B corpus strata (0.6650 / 0.67) | **not** fixture numbers | reported separately in §4.7 |

**If the declaration were ever revisited (0.6684 promoted to primary), these sentences change** — kept
explicit so the edit is mechanical:

1. Title — "by 0.33" (declared primary, 0.3316) would revert to "by 0.32" (0.3210).
2. Abstract, "Headline" sentence — the clause naming 0.6789 as declared primary and 0.6684 as secondary.
3. Abstract, "Against the *published* … 0.3210" sentence — would become the primary figure.
4. §4.2 table caption and the primary-baseline row.
5. §4.2 sentence fixing Δ = −0.3316 to the same-run arm.
6. §5.1 first paragraph (which baseline the shortfall is measured against).
7. §6.3 (single-fixture limitation) — the baseline choice is part of the pre-registration story.

**The declaration lives here, where the numbers are used.** This section is the paper's statement of the
declared primary baseline (**0.6789**, author decision 2026-10-15) and of the deliberate title-figure
change (the title uses **0.33** against the primary; **0.32** is the secondary-baseline arithmetic); the
abstract restates both, and no third baseline figure is introduced anywhere in the paper.

### 3.4 Controls — each one is asked what it would have shown

A control that cannot report the opposite is decoration. Three controls are load-bearing here, plus
fixture-reliability and leak-detection probes:

- **Majority-class control (0.4526).** Could have contradicted the candidate: if any head exceeded 0.4526,
  the "encoder head is a viable default" reading would survive on this fixture. **It returned the opposite:**
  no head does; the margin is +0.1053 over the best head.
- **Shuffled-label control (0.2316).** Could have contradicted the measurement: if a head trained on
  *shuffled* labels scored at or above the 0.2911 chance floor, the fixture would be leaking label signal
  through some channel other than the intended task, and every accuracy number above the floor would be
  suspect. **It returned the opposite:** 0.2316 **< 0.2911**, below chance. Note the associated calibration
  caveat: its temperature-scaling fit hit the grid ceiling (100.0, `onGridCeiling = true`), so its reported
  ECE **0.0808 is an upper bound** on the calibration reachable by that arm, not a fitted value.
- **F4 n-gram leak lint.** Could have contradicted instrument integrity: rule = "drop a row when it shares
  ≥ 2 distinct 8-grams with any single row of the other side", applied **in both directions**, threshold 2.
  Over the real comparison it compared **152,000** training↔fixture pairs in each direction and flagged
  **0**, removing 0 rows (and 160,000 training↔dev pairs, also 0). Could it ever fire? The positive controls:
  three deliberately seeded copies, which fired at **13 / 44 / 57** shared 8-grams. **Read those as
  per-pair maxima**: 13 is the state-only copy's total *and* its max-pair count; 44 and 57 are the
  **max-pair** counts of the boilerplate-only and whole-row copies, whose totals are 220 and 233. A novel
  row shared 0 grams with anything (negative control). So the lint fires when it should and is silent when it
  should be — F4 not firing means the run is **not void**.
- **Order-permutation probe.** A PriDe-style option-order probe. In the buggy pass-1 it flipped answers on
  138 (ModernBERT), 142, 101, 135 and 81 cases depending on arm; in the final pass it flips **0** for all
  candidate heads and **58** for the majority-class control. The control retaining flips is the right
  behaviour: a constant-answer arm is genuinely order-sensitive by construction, so a probe that reported 0
  flips for *it* would be broken.
- **Two blind model readers — machine reproducibility only.** Reader B (`routeB-blind-model`) reached
  agreement 0.9053, κ 0.9014, 18/190 disagreements; reader B2 (`mimo-v2.6-flash`) reached 0.8632, κ =
  0.8577, 26/190 — a **partial** replication whose exact "0.90" headline degrades by ~4 points. The two
  readers agree with each other at 0.9158, κ = 0.9125. Both are **models**, not independent humans, so
  neither figure — and not the model-to-model κ either — is **inter-annotator agreement** (§6.2). The
  deterministic lexical route (`routeA`) is not a labeller at all: it is a **rule**, and its κ = 0.3249 is
  the floor a rule-only approach reaches.

---

## 4. Results

### 4.1 The five arms on the sealed fixture

Best fine-tuned encoder head: **0.3474** (`modernbert-base`; `deberta-v3-base` ties it at 0.3474 but did not
train — §3.2). `setfit-mpnet`: **0.2632**. Every one of these is barely above the fixture's **0.2911**
chance floor, and `setfit-mpnet` is **below** it. The controls bracket the candidates: `majority-class`
**0.4526** above, `shuffled-label` **0.2316** below.

**The pre-registered falsifier F1 fired.** It was written as *"encoder accuracy < 0.6684 (the best 4B)"*
(`preregistration/EXP12-typed-channel-comparison-prereg.md:100`, `REPORT.md:85`); the best head is 0.3474, so F1 fires against the
published figure — and, separately, 0.3474 < 0.6789, so it fires against the auditable one too.

### 4.2 The paired fine-tuned comparison

Against the **same-run reproduction, 0.6789** — the paired partner on the same 190 cases and the same option
orders:

| statistic | value |
|---|---|
| accuracy A (head) | 0.3474 (`0.3473684210526316`) |
| accuracy B (decider, same-run) | 0.6789 (`0.6789473684210526`) |
| accuracy difference Δ | **−0.3316** (`−0.33157894736842103`) |
| McNemar discordant: b (head-only correct) | **27** |
| McNemar discordant: c (decider-only correct) | **90** |
| both correct / neither correct | 39 / 34 (rows sum to 190) |
| discordant total / discordance ψ | 117 / **0.616** |
| exact two-sided p | **4.167e−09** (`4.166817880507353e-09`) |
| continuity-corrected χ² | 32.85 |
| **paired** MDE (the quoted figure) | **0.1595** |
| unpaired MDE (shown only to make the correction visible) | 0.1355 |
| paired bootstrap 95 % CI of the difference | **[−0.4316, −0.2263]** (excludes 0) |

Δ was checked by two independent paths: `0.3473684210526316 − 0.6789473684210526 =
−0.33157894736842103`, and `(b − c)/n = (27 − 90)/190 = −63/190 = −0.3315789473684211` — same value.
ψ = 117/190 = 0.6157894736842106.

Against the **historical, published 0.6684** — the pre-registered F1 threshold, and the figure the working
title's "0.32" comes from — the difference is `0.6684 − 0.3474 = **0.3210**`. That is the **secondary /
robustness** figure and the pre-registered F1 threshold. **The declared primary baseline (0.6789) gives
Δ = −0.3316 ("0.33"), and every paired statistic in the table above is computed against it.**

**A correction we must carry, not a claim we may repeat.** The corpus's own summary
(the paper-candidates record :269 and experiment-learnings record :281) states *"Every correction moved the
affected arm DOWN."* **That is false as a universal.** The released `results/REPORT.md`
carries the defect write-up (the standalone `results/DEFECT-EVIDENCE.json` is **not** part of the
released set), and it shows:

- `setfit-mpnet` moved **down**: **0.3158 → 0.2947 → 0.2632** (the sequence of *distinct* values; the
  intermediate table carries **two** 0.3158 variants, one before and one after the order-probe itself was
  fixed). Its chain also has two 0.3158 entries, so the quoted three-number chain is the distinct-value
  sequence, not three table rows.
- `modernbert-base` moved **UP**: **0.342105** (pass 1, buggy order probe) → **0.347368** (final) once the
  order-probe bug was fixed.

So the correct statement is: **"every correction moved the *SetFit* arm down"**, or equivalently *"all three
defects flattered the candidate"* — the *defects* all favoured the candidate, but the *fixes* did not lower
every arm. The SetFit arm is the control that returned the expected direction; the ModernBERT arm is the
control that refuted the universal quantifier. We state the corrected version throughout and repeat it in
§5.3. The baseline declaration is **not** implicated here; this correction stands regardless of baseline.

Related numbers in the same chain: SetFit's ECE moved **0.1665 → 0.2738** (worse as accuracy dropped), with
the *final* 0.2632 arm at ECE **0.1536**; its order-permutation flips moved **101 → 46 → 36 → 0**, so the
final arm is order-stable. Pass-1 flips for the other arms were 138 (ModernBERT), 142, 101, 135, 81; the
final pass reports **0** for all candidate arms.

### 4.3 The control that beats the candidates

The majority-class control returns **0.4526** — a constant answer beats **every** fine-tuned encoder head on
this fixture, by a margin of **+0.1053** over the best one
(`0.45263157894736844 − 0.3473684210526316 = 0.10526315789473684`). This is the result we consider hardest
to explain away, and it is why the paper's claim is stronger than "the 4B wins": on this fixture, the
encoders are not merely behind the fine-tuned decider, they are behind a **fixed** decision rule.

`shuffled-label` returns **0.2316**, i.e. `0.23157894736842105` — **below** the 0.2911 chance floor, which
is the direction that keeps the instrument credible (§3.4).

### 4.4 Leak detection (F4)

`harness/data/lint-report.json` (withheld harness; not in the released set): `fires = false`, `silent = true`, `removedCount = 0`; forward and reverse each compared
152,000 pairs and flagged 0. Positive controls fired at 13 / 44 / 57 (pair maxima; totals 13 / 220 / 233);
the negative control (a novel row) shared 0 grams. `results/REPORT.md:95` (`fires = False`), `:134` (the lint record) — the run is
**not void** on the leak criterion.

### 4.5 Power

The observed harm is `0.33157894736842103 / 0.15949356562876219 = **2.079×**` the **paired** MDE, and
2.446× the unpaired MDE. The conclusion holds against either.

**⚠ We do not reuse the phrase "paired is conservative."** On this run it is false. ψ = 0.616 is high, so
`unpaired/paired = sqrt((p₁(1−p₁)+p₂(1−p₂))/ψ) = 0.85×` — the **paired MDE (0.1595) is the LARGER** of the
two, not the smaller. The *requirement* to quote the paired figure (method learning M11) still stands; the
*justification* that it is the lenient or conservative choice does not. We say what the numbers are.

### 4.6 Calibration — and the convention that decides it

The best head's ECE is **0.0994** (`0.09936282184403895`). The decider-4b's stored ECE is **0.0551** under
one convention and **0.1547** under the other. The pre-registered F3 falsifier therefore **flips**:

- on `probabilities[choice]`: head 0.0994 **≥** decider 0.0551 → **F3 fires**;
- on the stored `confidence` field: 0.0994 **<** 0.1547 → **F3 does not fire**.

Same rows, opposite verdicts. `results/REPORT.md:11` records `fires: ["F1", "F3"]` and the state
**CLOSE**: F1 and F3 fired; F2, F4, F5 and F6 did **not**. **⚠ We flag this ambiguity rather than resolving
it.** The paper's calibration claim is conditional on the convention, and the convention must be named
wherever the claim appears. Temperature scaling was fitted on a geometric grid from 1e−3 to 1e2, 200 points;
per-arm temperatures are 1.0970 (ModernBERT), 0.0036 (DeBERTa — did not train), 39.63 (SetFit), 1.0
(majority-class), 100.0 (shuffled-label, on grid ceiling).

### 4.7 Two further recorded findings

- **H4 is not supported.** The accuracy ordering is **monotone** in parameter count across the three heads
  (0.2632 at 109M < 0.3474 = 0.3474 at 149M and 184M), so there is no size-crossover story *within* these
  heads. `results/REPORT.md:109` records this explicitly.
- **The H-A/H-B strata.** The same `decider-4b` reproduction scores **0.6650** on the H-A corpus stratum
  (reproducing its published 0.665) and **0.67** on H-B. These are **corpus strata**, not fixture numbers,
  and we do not compare them to fixture accuracy. `imajev-4b`'s **0.645** is likewise an **H-A corpus
  stratum** figure; its fixture figure is **0.6368**.

---

## 5. Discussion

### 5.1 The crossover is a property of the baseline, not of the model class

The published crossover compares an encoder against a **prompted** LLM. When the generative side is
fine-tuned on the same task with the same labels, the crossover does not appear on our fixture: the encoder
is **0.3316** behind on the **declared primary baseline (0.6789)** and **0.3210** behind on the
**secondary, published one (0.6684)**. The effect size is not marginal under either pairing: Δ = −0.3316 exceeds
**2×** either MDE, with exact p = 4.167e−09, and the paired bootstrap CI [−0.4316, −0.2263] excludes zero.

The honest reading is narrower than "encoders are worse". Prompting and fine-tuning are different
*resources*; the published results show what a prompted LLM does with a task description and a few
examples, and this paper shows what happens when that constraint is removed on this one fixture. The
crossover may well be a real property of the prompting regime. What we have shown is that it does not
transfer for free to the fine-tuning regime — which is exactly the inference the corpus's own errata says
the literature does not license.

**We claim no priority for the direction.** That a fine-tuned generative decider beats a fine-tuned encoder
at comparable effort is already public (§2.1, Simmering 2025 — a blog post, not peer-reviewed). What this
fixture contributes is the artefact diagnosis and, sharper than the direction, the majority-class control
that beats every candidate head (§5.2) — neither of which the counter-case contains.

### 5.2 The majority-class control is the sharpest result

We expected the interesting comparison to be encoder vs fine-tuned 4B: **0.3474 vs 0.6789**. The sharper
finding is **0.3474 vs 0.4526**: a constant answer beats every fine-tuned encoder head by **+0.1053**, and
`setfit-mpnet` (0.2632) sits **below** the 0.2911 chance floor. This reframes the paper. It is not
"the 4B is better than the encoder"; it is "on this fixture the encoder heads fail to beat a fixed rule, and
the fine-tuned 4B is the only arm that is clearly doing the task". Any recommendation of the form "use an
encoder head as the default at N ≥ 4" must clear the majority-class bar on the target fixture first — a bar
that costs one re-score to compute and that the corpus's prior recommendation had not cleared.

### 5.3 Method lessons, including one correction to the record

- **A defect chain can favour the candidate without lowering every arm.** We carry the corrected statement:
  the corrections lowered the **SetFit** arm (0.3158 → 0.2947 → 0.2632) and **raised** the ModernBERT arm
  (0.342105 → 0.347368). The universal form of the claim ("every correction moved the affected arm DOWN") is
  false and is not repeated anywhere in this paper.
- **The quoted MDE is the paired one; it is not the lenient one here.** ψ = 0.616, `unpaired/paired = 0.85×`.
  Quote the paired figure because M11 requires it, not because it flatters the conclusion.
- **A calibration verdict can be decided by a storage convention.** F3 fires on `probabilities[choice]` and
  not on `confidence` — same rows, opposite verdicts. Any calibration claim must name the field it reads.
- **A mandatory control is only meaningful if it can win — and here it did.** The majority-class control beat
  every candidate. The design lesson is to pre-register the control's *ability to contradict*, not just its
  presence.

---

## 6. Limitations

### 6.1 Latency was out of scope, and the evidence could not support it

**We make no latency claim, in the abstract, the results or anywhere else.** The evidence tree cannot
support a fair latency comparison, for four recorded reasons:

1. **Never co-measured.** `REPORT.md:191`: *"The heads were timed on the GX10's GB10 with local weights; the
   decider's 0.075 s/decision figure and the re-scored 0.0531 s/decision on these rows come from a served
   model on a different stack."*
2. **Different unit of work.** The head figure is one full per-decision call — all option texts tokenised,
   **one forward batch**, softmax (12.37 / 14.16 / 11.96 / 12.46 ms for the four heads; 0.003 ms for
   majority-class; n = 570 after 20 warm-up cases, GPU synchronised). The decider figure is a served
   autoregressive decode loop. Those are not the same operation.
3. **The F6 threshold is a constant, not a measurement.** F6 compares heads against the **pre-registered**
   0.075 s/decision (`results/REPORT.md:107`, which records the `DECIDER_TIER` §2 figure), so F6 not firing (`fires = false`) only says 12–14 ms < 75 ms.
   It is not evidence from a head-to-head.
4. **The decider's own timing spreads 2× across strata of the same model** — 53.06 ms (instrument190),
   72.85 ms (H-B), 106.92 ms (H-A) — which by itself shows the timing was not controlled. (`imajev-4b` and
   `laya` sit at 453 ms / 639 ms in the same stored source, but comparing them to the local head timings
   would repeat the same category error.)

The strongest defensible statement is the uninteresting one: per-decision, the heads sit in the tens of
milliseconds and the stored decider figures sit in the tens-to-hundreds of milliseconds, measured on
different stacks and different operations. That is not a result, so latency is dropped and named here
instead. Closing it would need a 4B decider re-measured on the same host under the same per-decision
protocol.

### 6.2 Two blind model readers: machine reproducibility of the fixture, **not** inter-annotator agreement

**Two** blind model passes now exist. Reader B (`routeB-blind-model`) agrees with the fixture's
hand-authored labels 0.9053 of the time, κ = 0.9014, with 18/190 disagreements. Reader B2
(`mimo-v2.6-flash`), run later on the same blinded inputs, agrees **0.8632** of the time, **κ = 0.8577**,
with **26/190** disagreements. The two readers agree with **each other** **0.9158** of the time, **κ =
0.9125** — a genuinely new, model-to-model quantity. The *magnitude* of the first result therefore
replicates (both readers land at κ ≥ 0.85), but the exact "0.90" headline does **not**: reader B2 sits 4.2
points lower on agreement and 4.4 points lower on κ, and the pre-registered ladder would place it in band 2
(0.75 ≤ agreement < 0.90) while it still clears the band-1 κ threshold. We report this as a **partial
replication** and give **both** readers, not one of them as "the" figure.

The two readers agree with each other *more* than either agrees with the fixture record (0.9158 > 0.9053
and > 0.8632). That is consistent either with a shared LLM reading bias or with author-idiosyncratic
conventions in the fixture, and we do not resolve it: a high model-to-model κ is equally consistent with two
models sharing a *wrong* convention. What it does rule out is treating the fixture's conventions as
self-evident, and it is why those conventions should be read as conventions rather than as ground truth.

Four further findings bound how the labels should be read:

- **The weak dimensions are the same for both readers, and the weakest is `memory.admission`** (B2 κ =
  **0.5625**, B κ = **0.7153**), followed by `acquisition` (B2 **0.7045**, B **0.8049**). The other
  five of the seven kinds (`escalation`, `topology`, `worker.class`, `context.package`,
  `capability.family`) are stronger for both readers. Consistent weakness across two independent machine
  readers points at the **fixture**, not at the readers: label soundness is dimension-dependent, and the
  dependence looks like a property of the instrument.
- **The `memory.admission` tier boundary is a real, replicated ambiguity — the top repair item.** Four
  cases (`memory.admission-001/-009/-021/-027`) record step-scoped scratch that is never re-read as
  `EPHEMERAL`; **both** blind readers independently chose `DROP` on all four (**4/4** replicated). B
  first reported this convention and B2 shows it is not one model's quirk. The fixture's tier vocabulary
  for scratch that is never re-read is not pinned down by the questions.
- **Accuracy tracks option arity for both readers — but the effect is confounded with kind.** Agreement
  falls from 0.970 (2-option cases, n = 33) to 0.722 (5-option cases, n = 54) for B2, and from 1.000 to
  0.815 for B (κ 0.950 → **0.684** and 1.000 → 0.791). The 5-option stratum is dominated by the
  closed-roster kinds `memory.admission` and `acquisition` — the two hardest kinds for independent semantic
  reasons — so this is **not** clean evidence of option-wording exploitation, and on the stratum where the
  answer is named in the question (30 `escalation` cases) the readers scored 30/30 (B) and 28/30 (B2),
  which is not how a surface-cue matcher behaves. But the gradient is real and it **weakens any blanket
  "the labels are sound" claim** for high-arity closed-roster kinds: soundness is measurably lower there.
- **Disagreement structure, not just its count.** B2 disagrees on 26 cases and B on 18, but the overlap
  is a **14-case shared contested core** — all four `acquisition` traps (`-007/-014/-019/-023`),
  `topology-018`, `capability.family-004/009`, `context.package-004`, `worker.class-023`, the four
  `EPHEMERAL`/`DROP` cases above, and `memory.admission-018` (`DROP→EPISODIC`). The tails (12 B2-only,
  4 B-only) are scattered and read as
  reader-specific noise, not as a second catalogue of defects. The honest reading is "14 shared contested
  cases plus two small reader-specific tails", not "26 defects".

Two further honest caveats:

- The **pooled** κ is weak on its own: 51 of 74 labels occur once, so `pe` is tiny (0.040) and κ is
  dominated by `po`. The informative figures are the stratified ones: closed-vocabulary subset (4 kinds,
  106 cases) κ = **0.8837**; roster-and-bespoke subset (84 cases) κ = **0.9140**; AB mutual agreement
  **0.3684**; the deterministic lexical rule (routeA — a **rule**, not a labeller) reaches only κ = **0.3249**
  (agreement 0.3421), and in 4 of the 18 disagreements routeA backs the fixture record. Route A is a
  **tokeniser-overlap rule** rather than a model, so its κ moves by a few thousandths with how the fixture's
  text is spelled and cased — the measured range across our neutralisation rounds was 0.319886… to 0.324881…
  — an order of magnitude smaller than its ≈0.33 separation from the decider, so no conclusion rests on the
  exact value.
- A threshold was pre-registered (≥ 0.90 agreement / ≥ 0.85 κ). Reader B *met* it at 0.905 / 0.901; reader
  B2 *met the κ threshold but not the agreement threshold*, at 0.863 / 0.858. But a met threshold on a
  **model** pass — or on two — does not convert it into human agreement.

**An independent human labeller is still owed, and the paper-candidates record §F.3 is not discharged.**
the second-labeller-190 source experiment tree's evidence record :309 states it for one pass — *"**It is not IAA.** One pass is
a model."* — and two passes do not change that: **κ = 0.9125 between two models is still not
inter-annotator agreement and must never be cited as such.** Two models can share a wrong convention as
easily as a right one, and this result bounds *machine* reproducibility for exactly two models on exactly
one fixture. §F.3's point — that several candidate papers share this one 190-case fixture, so *"one fixture
flaw propagates into four papers"* — remains true, and its call for a second independent **human** labeller
is not discharged by either pass. The fixture's own flagged decidability weak points (five owed
corrections, of which four are repairs to the fixture file itself) are listed in this record's internal checklist (an internal working record not included in the released material) and were
**deliberately not applied**, because the target repository is strictly read-only.

### 6.3 External validity: one fixture, one host, and a baseline choice awaiting a human

This is a single 190-case fixture authored by one worker, evaluated on one host. If a reviewer judges the
fixture unrepresentative, the claim reduces to "on these 190 cases" — still a publishable negative result,
but a smaller one. The fixture shares its provenance with several other candidate papers (§F.3). No external
typed-decision benchmark was used, and none was found in the corpus to use.

**The primary baseline is declared: 0.6789** (author decision, 2026-10-15) — the auditable same-run figure.
**0.6684** is carried as a secondary / robustness figure and as the pre-registered F1 threshold, and it cannot
be re-scored. The seven sentences that would change if that declaration were ever revisited are enumerated in
§3.3; the conclusion does not depend on the choice.

### 6.4 The literature claim is an internal verified-absent audit; its counter-case is a sourced blog post

§2's core claim is supported by `docs/DECIDER_STACK_DECISION.md` §11.6 and commit `ad301ae`, which state it
as an errata on the corpus's own earlier recommendation. It **does** support the claim as written — but it is
a claim about a **literature search whose protocol is not recorded**: databases, query terms, dates and
inclusion rules are absent from the corpus. We write "we were able to locate" rather than "no such work
exists", and our external search then **failed to upgrade the hedge**: no survey or recorded search
protocol establishing the absence was located, so the weaker phrasing stays.

The corpus's own equal-fine-tuning-effort counter-case, previously without an identifier, is now located and
cited — as a **blog post**, deliberately not dressed as a paper (§2.1, `simmering2025modernbert`). It reports
a fine-tuned Llama-3.2-3B LoRA at F1 93.1 beating ModernBERT-large's 89.2 on binary ADE classification at
equal per-arm training cost, and we **claim no priority for that direction**. Our thesis is therefore
supported by **one** fine-tuned-vs-fine-tuned data point against the crossover on our own fixture, plus that
post's independent reproduction of the prompted-baseline half (its prompted arm scored 80.7) — **not** by a
survey. The corpus claim that was carried without an identifier — an encoder-only RoBERTa beating a fine-tuned
LLaMA2-7B on 77-class intent classification — is now sourced to Benayas, Sicilia & Mora-Cantallops (2024),
*Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y`, and cited for that
result.

### 6.5 Scope of the candidate arms

Only three encoder families were run, all 109M–184M parameters: ModernBERT-base, DeBERTa-v3-base and
SetFit-MPNet. **`deberta-v3-base` did not train** at the pre-registered operating point (train loss
1.1288 → 1.1235, `results/REPORT.md:151`; dev 0.50 → 0.495 against a dev majority-class baseline of 0.475), so it is not a completed
arm and we do not rely on it. **Training is not bit-reproducible** — three identical runs gave ModernBERT
epoch-1 dev accuracies 0.5150 and 0.5900 and fixture accuracies 0.3421 and 0.3474 — so a **±1–2 point band**
applies to every head number here. All conclusions have margins far larger than that band, but a reader
should not treat 0.3474 as exact. A reviewer's obvious fourth arm — **a trained linear probe on a frozen LLM
embedding** — was not run and is *not* present anywhere in the evidence tree; it is listed as an open
decision in this record's internal open-questions log (an internal working record not included in the released material). H4 (accuracy monotone in parameter count) is **not supported**; the
observed ordering is monotone, so there is no within-heads size-crossover story to tell.

### 6.6 The counter-case asks whether our encoder arm is simply under-trained

A reviewer who has read the equal-effort counter-case can put the objection in one sentence, and we write it
here in their voice rather than waiting for it:

> *"Your best encoder head scores 0.3474 and fails to beat a majority-class control at 0.4526, while a real
> ModernBERT-large reached **0.892 F1** in the counter-case. Is your encoder arm under-trained — so that your
> shortfall measures your training recipe rather than the crossover you claim to be diagnosing?"*

We **cannot fully answer that objection from our evidence, and we do not pretend to.** What we can say is
bounded, item by item:

- **The 0.892 is a different instrument and is not comparable.** The counter-case's 89.2 F1 is **binary
  (N = 2) sentence classification** on the ADE corpus; our fixture is a typed single-label decision over
  N = 2–8 named options, with **74** distinct labels (51 occurring exactly once) and a **0.2911** mean-1/K
  chance floor. Absolute accuracy or F1 across those two instruments is not a like-for-like comparison in
  either direction, and we do not use it as one.
- **What the majority-class control licenses — and what it does not.** It licenses exactly one claim: on this
  fixture, **no encoder head is a viable default** — 0.4526 beats the best head by **+0.1053**, computed on
  the same 190 cases and the same option orders. It does **not** license the claim that `modernbert-base` is
  well tuned, that 0.3474 is an encoder ceiling, or that an encoder could not reach a higher absolute level
  on this fixture under a better recipe. We report the encoder arm's absolute level as an observed value
  under one recorded recipe, **not as an architecture verdict**.
- **What we do not establish about tuning effort.** This paper reports **no tuning-effort or compute study**
  for the encoder arms. The counter-case's equal-effort premise (*under one dollar, under 15 minutes per arm
  on one A10G*) is **its** premise on **its** task; we did not reproduce it, and we make no equal-effort claim
  of our own. Training non-reproducibility (§6.5: three identical runs gave fixture accuracies 0.3421 and
  0.3474, a ±1–2 point band) bounds how much a single head number can carry — but a ±1–2 point band is
  **not** evidence that the recipe is adequate, and we do not offer it as such.
- **The reviewer's alternative reading stays open.** If the encoder arm is under-trained, part of the 0.3316
  shortfall could reflect the recipe rather than the crossover. Nothing in this paper excludes that reading.
  It is named as an **open question** in this record's internal unsourced-claims log (an internal working record not included in the released material); closing it would need a tuning-effort sweep
  on this fixture — including the fourth arm named in §6.5, a trained linear probe on a frozen LLM embedding,
  which was **not run** — and we did not run one.
- **What the claim therefore is.** A **change of direction under fine-tuning** on one sealed fixture, plus
  the prompted-baseline artefact diagnosis — **not** an estimate of an encoder ceiling, and **not** an
  equal-effort law. It does not depend on 0.3474 being the best an encoder can do; it depends on the paired
  fine-tuned comparison, the majority-class control, and the fact that the published encoder-wins results
  compare the encoder against a **prompted** LLM.

---

## 7. Reproduction

Everything in this paper is checkable against the released reproducibility package — **29 files, no
evaluation harness**, carrying the sealed 190-case fixture and its schema, the verification tooling
(`verify/recompute-claims.py`), the pre-registered protocols, the per-arm result records the claims cite,
and the second-labeller evidence (Zenodo DOI `10.5281/zenodo.23463944` — see Data and code availability). The
full, copy-pasteable command list with verbatim outputs is this record's internal evidence notes (an internal working record not included in the released material);
This record's internal claims map (an internal working record not included in the released material) maps each number to its source file and key. **The evaluation harness — the model, training and
evaluation code — is withheld, so the subset verifies the recorded results but cannot regenerate them.** The
load-bearing material is:

| what | where (all paths are within the released package unless noted) |
|---|---|
| per-arm metrics | `results/eval-{modernbert-base,deberta-v3-base,setfit-mpnet,majority-class,shuffled-label}.json` |
| instrument, comparisons, resolution, falsifiers, H4 | `fixture/reflex-decisions.ts`; `results/REPORT.md`; the per-arm and control records in `results/` |
| defect chain | `results/REPORT.md` (the D1-D3 defect write-up); the standalone `results/DEFECT-EVIDENCE.json` is **not** part of the released set |
| leak lint | recorded by the withheld harness (`harness/data/lint-report.json`); not part of the released set |
| narrative report | `results/REPORT.md` |
| pre-registered protocol | `preregistration/EXP12-typed-channel-comparison-prereg.md` |
| second-labeller reliability (reader B) | `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,PREREGISTRATION.md}` |
| second-labeller robustness (reader B2; **not** in the released subset) | the source experiment tree's second-labeller robustness records |
| harness provenance (**the harness itself is withheld**; recorded for integrity) | recovered from an unmerged development branch (name and commit withheld), path `tools/typed-channel/` — 18 files recovered read-only via `git cat-file blob` |
| the core literature claim (source repository, not released) | `docs/DECIDER_STACK_DECISION.md` §11.6; commit `ad301ae1a5472fa7bd27807fdc7bb15d35f81988` |

**Search gotcha, recorded so a replicator does not conclude a number is absent.** The p-value is written with
a **typographic minus (U+2212)** in the paper-candidates record :265 and the experiment-learnings record :265
(`4.167e−09`), so `grep 4.167e-09` on those two files returns nothing; the machine-readable sources
(`results/REPORT.md:63`, `:64`) use an ASCII hyphen. Grep for `4.1668` or `4.167` instead, or use
`grep -P '\x{2212}'`.

**What reproduces exactly.** The same-run decider baseline: the per-case rows shipped in
`results/baselines.json`
(`.models["decider-4b-exp11-reproduction"].perCase`, 190 rows) re-score to 0.6789 vs published 0.6789,
`reproducesAt3dp = true`, `absoluteDifference = 4.7e−05`. The historical 0.6684 does **not** — no per-case
rows survive for it (`REPORT.md:104`, `:189`), which is why it is the **secondary** figure and not the
declared primary — **0.6789** (author decision, 2026-10-15).

**Instrument integrity checks a replicator should re-run.** Fixture sha256 unchanged before/after the second
labeller pass and byte-identical sandbox copy; F4 silent over 152,000 pairs in both directions while firing
at 13/44/57 on the seeded copies; row identity `39 + 27 + 90 + 34 = 190`; chance floor recomputed as
`(33/2 + 27/3 + 76/4 + 54/5)/190`.

**Read-only discipline.** The source repository was treated as strictly read-only: no writes, no `git` state
changes. HEAD before and after: `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; working-tree changes present both
times are **unattributed-to-this-unit** untracked files from a concurrent session and are recorded in
this record's internal checklist (an internal working record not included in the released material).

---

## Data and code availability

**The paper is public, CC BY 4.0.** By the author's decision of 2026-10-15 the manuscripts in this series are
released under **Creative Commons Attribution 4.0 International**. The paper's own licence is therefore
settled, and it is **not** a separate open question awaiting a human decision.

**The released reproducibility package ships with the paper** (29 files; **no evaluation harness**; Zenodo
DOI `10.5281/zenodo.23463944` — see the persistent-identifier paragraph below). It is deliberately
minimal: it carries the sealed fixture, `verify/recompute-claims.py` and the second labeller's
`parse_fixture.py` and `compare.py`, the `results/` records the claims rest on, the pre-registered protocols
and a `README.md` — what a reviewer needs to **check** the recorded measurement, and nothing of the system
the measurement is about. **A reader therefore cannot retrain the arms, cannot re-render the model inputs,
and cannot re-run the evaluation pipeline: what is released verifies the results, it does not reproduce
them.**

- **The instrument and its schema** — `fixture/reflex-decisions.ts`, the shipped copy of the sealed
  190-case fixture (shipped sha256
  `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169`; the as-audited source it was derived from is sha256
  `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`), and
  `fixture/DECISION_CASE_SCHEMA.ts`.
- **The verification tooling and the commands** — `verify/recompute-claims.py`, which recomputes the cited
  values from the shipped `results/` records, plus the copy-pasteable command list in
  this record's internal evidence notes (an internal working record not included in the released material) and the subset's own `README.md`. The evaluation harness
  (18 files) with its frozen `data/` is **withheld**, not shipped.
- **The pre-registered protocols** — `preregistration/EXP12-typed-channel-comparison-prereg.md` (EXP#12
  §1–§9), and `second-labeller/PREREGISTRATION.md`.
- **The results** — the five per-arm sealed-190 records (`results/eval-*.json`) and the re-scored controls
  with their **per-case** rows (`results/baselines.json`), so the declared primary baseline **0.6789** is
  auditable from the released material alone.
- **The second-labeller evidence** — `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json}`
  (reader B), the record behind the κ = 0.9014 result, which §6.2 states is machine reproducibility of the
  fixture and **not** inter-annotator agreement. The **second** model reader (B2, κ = 0.8577; model-to-model
  κ = 0.9125) is recorded in the source experiment tree at
  the source experiment tree's second-labeller robustness records
  and is **not** part of this released subset.

**Honest limitation: the harness does not ship, so the measurement cannot be re-run.**
The six Python steps (`prepare.py`, `train.py`, `evaluate.py`, `analyze.py`, `defect-probe.py`, `collect.py`),
the two TypeScript steps (`export-fixture.ts`, `lint.ts`) and the harness's frozen `data/` are **withheld**.
The subset ships their **outputs** — the sealed fixture and the per-arm and control records in `results/` —
and `verify/recompute-claims.py` recomputes every cited value from those records. What a reader cannot do is
retrain an arm, re-render the model inputs, or re-run the evaluation pipeline. We do not claim that the
measurement is re-runnable.

**A provenance fact a reader should not have to guess.** The EXP#12 harness is **not on the source
repository's default branch**: the experiment closed that branch unmerged (its name and commit are
withheld), at path `tools/typed-channel/`, and that path does not exist on trunk. The 18 harness files were
recovered **read-only from the git object store** (`git cat-file blob`) and are **not** part of the released
set; a reader should not assume they are on the default branch.

**Withheld by policy — deliberately, not by oversight.** The **agent-state kernel / runtime implementation**
(the target repository's withheld implementation directories) is the system the measurement is about, and it is not released. **No model weights**
are released: the three arms are fetched as **public** checkpoints at run time
(`answerdotai/ModernBERT-base`, Apache-2.0; `microsoft/deberta-v3-base`, MIT;
`sentence-transformers/all-mpnet-base-v2`, Apache-2.0), and no weight file is shipped or present in the source
repository's tree. The source repository's 26-file evidence tree is likewise not released. The full boundary
is enumerated in the subset's accompanying exclusion inventory — 15 exclusion classes, including traces, run artefacts,
scratch trees and vendor code. **Checking** this paper's claims requires the **fixture, the verification
tooling and the result records**; it does **not** require the kernel, the weights, or the training pipeline.
**Reproducing the measurement is not possible from the released material**, because the harness is withheld.

**Licence of the subset — decided.** The **content** — the fixture and the paper's own material — is covered
by CC BY 4.0, and **the paper's own text is CC BY 4.0**. The **code** licence for the subset is a
**different** question, and it is now settled: released artifacts are **source-available under PolyForm
Noncommercial 1.0.0**, with an **author-offered paid commercial licence** for commercial use. The **main
repository stays fully proprietary and closed**; the source repository's own `LICENSE` governs it and its
terms this paper neither restates nor resolves. The instruments for this decision ship with the released package, at its root:
`LICENSE`, `COMMERCIAL.md` and `CONTRIBUTING.md`.

## Persistent identifier

**Persistent identifier: concept DOI `10.5281/zenodo.23463944`.** The released reproducibility package
(29 files; no evaluation harness — see Data and code availability) is published on Zenodo under that DOI,
so the released artifacts carry a persistent identifier as well as a licence statement.

## Compute and resources

All encoder-arm measurements reported here were run on a **single host** (`GX10 gx10-163b`, NVIDIA GB10 GPU);
the fine-tuned 4B decider figures are re-scored from stored rows produced by a **served stack on different
hardware** and were **not** co-measured here (§6.1). Per-decision head timing is one batched forward call over
all option texts, 20 warm-up cases and 3 × 190 = 570 timed cases with the GPU synchronised (§6.1). The three
encoder arms are public Hugging Face checkpoints fetched at run time; no model weights ship (see Data and code
availability). This paper reports **no tuning-effort or compute study** for the encoder arms (§6.6).
The training harness is **withheld from release** and no training run was **re-executed** for this paper, so
wall-clock training time per arm, GPU memory footprint, and any energy measurement are **not recorded in the
released record**; those figures are stated here as unrecorded rather than filled with an estimate.

## Author contributions

**Author contributions.** This manuscript is by a single author, **Aswin Ram Kalugasala Moorthy**. The research
question and the direction of the work are the author's; the author carried out and directed the work and wrote
the paper, and takes responsibility for its content. No further contribution record exists and no CRediT roles
are stated.

## Funding

**Funding.** This research received no external funding. No funding body, grant number or institutional support
is recorded anywhere in this workspace, and none is claimed.

## Use of AI tools

**Use of AI tools.** In October, I used large language models through DeepSeek Harness (chiefly
`deepseek-v4.1-flash`, with `step-5-preview-free` and `mimo-v2.6-flash` as subagent routes) in two ways: to
help design and implement the analysis and the experiment, and to help draft and edit this manuscript. The
research idea, the experimental design, and all editorial decisions are my own. I checked and verified all
AI-assisted output, and I take full responsibility for the entire content of this paper. The AI systems are
not authors and are not credited as contributors.

## Conflicts of Interest

**Conflicts of Interest.** The author declares no competing interests.

## References

Only sources whose identifier or location was actually observed are cited. The corpus's four external
identifier-only entries have since been completed from the arXiv abstract pages, which supplied title and
authors for each: arXiv `2602.06370` (Valdes Gonzalez, *Cost-Aware Model Selection
for Text Classification: Multi-Objective Trade-offs Between Fine-Tuned Encoders and LLM Prompting in
Production*); arXiv `2512.12677` (Yousefiramandi and Cooney, *Fine-Tuning Causal LLMs for Text
Classification: Embedding-Based vs. Instruction-Based Approaches*); PriDe, arXiv `2309.03882` (Zheng et al.,
*Large Language Models Are Not Robust Multiple Choice Selectors*; ICLR 2024 Spotlight); and GCD, arXiv
`2305.13971` (Geng et al., *Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning*;
EMNLP 2023 Main Conference), ACL 2025 Industry `2025.acl-industry.34`. The internal corpus document that
carries the core literature claim (`DECIDER_STACK_DECISION.md` §11.6, commit `ad301ae`) is the citation for
that claim. The bibliography now also carries
the equal-effort counter-case (**`simmering2025modernbert`** — a **blog post, not peer-reviewed**, cited as
such), **GLiNER** (arXiv `2311.08526`; NAACL 2024, pp. 5364–5376, DOI `10.18653/v1/2024.naacl-long.300`),
**GLiNER2** (arXiv `2507.18546`) and **GLiClass** (arXiv `2508.07662`). Three further entries are marked
**`ADJACENT`** in `REFERENCES.bib` and are **not** sources for the central claim: arXiv `2501.08457`, ACL 2025
Industry `2025.acl-industry.68`, and arXiv `2507.11412` (ICLR'26). The bibliography carries it as a 13th
entry: **`benayas2024comparative`** — Benayas, Sicilia & Mora-Cantallops (2024), *A comparative analysis of
encoder only and decoder only models in intent classification and sentiment analysis*, *Language Resources
and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y` — the peer-reviewed, same-task
encoder-over-decoder study that sources the corpus claim; it is cited in §2.1 and §6.4.
