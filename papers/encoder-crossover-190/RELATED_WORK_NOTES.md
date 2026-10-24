# RELATED_WORK_NOTES.md — UREFS · how §2 should engage the equal-effort counter-case

Unit UREFS, 2026-10-15. Companion to `REFS_VERIFIED.md` §3 and `REFERENCES_ADDITIONS.bib`
(`simmering2025modernbert`). **This is the single most important finding of this unit.** Read it before
touching §2.1.

---

## 1. The counter-case exists, and the corpus quoted it accurately

`OPEN_QUESTIONS.md` Q5.3 and `REFS.md` §A4 called it *"the corpus's own honest counter-case … the strongest
single threat to the thesis and the highest-priority find."* **It is located:**

> **Paul Simmering, "ModernBERT vs LLMs for Detecting Adverse Drug Reactions", published 2025-01-12,
> `https://simmering.dev/blog/modernbert-vs-llm/`** (fetched 2026-10-15). No DOI, no arXiv id, no venue — it
> is a **blog post**, with code on GitHub and results in a public Weights & Biases project.

The corpus's numbers are **exact**: ModernBERT-large **F1 89.2 at 87 examples/s**; fine-tuned
Llama-3.2-3B-Instruct **LoRA F1 93.1 at 152 examples/s** (vLLM); equal training effort, one A10G,
*"under one dollar and in less than 15 minutes"* for every setup. Nothing in `REFS.md` §A4 is misquoted.

## 2. How the paper should engage it — the paragraph §2.1 should carry

Suggested treatment (adapt wording; the facts are the ones to keep):

> *The one public fine-tuned-versus-fine-tuned comparison we were able to locate goes the other way. In a
> practitioner experiment on binary adverse-drug-reaction sentence classification, a fine-tuned Llama-3.2-3B
> LoRA adapter reached F1 93.1 against ModernBERT-large's 89.2, at a comparable training cost (under \$1 and
> under 15 minutes per arm), and — under vLLM with CUDA-graph capture — 152 versus 87 examples/s
> (Simmering, 2025). We take that result seriously and it shapes what we claim. It differs from our setting
> in three ways that matter: (i) its task is binary (N = 2) sentence classification on the ADE corpus, not a
> typed single-label decision over N = 2–8 named options with a per-option label set; (ii) the decoder arm is
> a 3B model, roughly 7.6× the 395M encoder, so architecture and scale are confounded — the author says so
> himself ("did it win by sheer size?"); and (iii) its throughput comparison is a property of the serving
> stack, not the architecture — the author records that adding the 30 s vLLM preparation time drops the LoRA
> arm to 42 examples/s, below ModernBERT-large, and warns that "this speed comparison was not comprehensive".
> We therefore claim no priority for the direction of the result: a fine-tuned generative decider can beat a
> small encoder at equal effort. What we measure is narrower — on our typed-decision fixture the fine-tuned
> encoder head loses by 0.33 — and what we diagnose is narrower still: the published "small encoder wins"
> crossover is measured against a **prompted** LLM. Notably, the same experiment reproduces that half of our
> diagnosis: its DSPy-optimised few-shot Llama arm scored 80.7 F1 against ModernBERT-large's 89.2.*

## 3. Does the counter-case weaken the thesis?

**The manuscript's stated thesis survives. Two things around it do not.** Plainly:

1. **The stated thesis survives, and is in fact corroborated.** The thesis is *"the small-encoder crossover
   is a prompted-baseline artefact"* — i.e. the published encoder-wins results compare a fine-tuned encoder
   against a *prompted* LLM, and the comparison changes direction under fine-tuning. The counter-case
   contains **both halves of that pattern in one experiment**: its prompted arm (few-shot Llama-3.2-3B,
   DSPy-optimised, vLLM) scored **80.7** and lost to ModernBERT-large's **89.2**, exactly as the thesis
   predicts; its fine-tuned arm then won. So the counter-case is not evidence against the artefact diagnosis
   — it is an independent, if non-peer-reviewed, reproduction of it, on a different task. The paper's own
   measurement (encoder 0.3474 vs fine-tuned 4B 0.6789) points the same way.
2. **A narrower claim the *corpus* makes is contradicted, and must not be imported into the paper.**
   `DECIDER_STACK_DECISION.md` §11.2 tries to salvage: *"The supportable claim is narrower: an encoder wins
   at equal **training budget** on closed label sets, and a fine-tuned generative model can match or beat it
   at higher training cost."* The counter-case refutes the second clause: the LoRA arm's training cost was
   **not** higher in any way the source reports (≈ 8 min vs ≈ 3.5 min for ModernBERT-large; *"the differences
   are negligible"*). **Do not carry that sentence into `MANUSCRIPT.md`.** The supportable version is weaker
   and hedged — *at matched training budget, on tasks where a task-specific head is appropriate, a small
   encoder can win against a prompted LLM* — and it should not be stated as a general law.
3. **Novelty risk — say it before a referee does.** "A fine-tuned generative model beats a fine-tuned encoder
   on a classification task" is **already in the public record** (Simmering 2025; and, for the prompted side,
   the corpus's own `2602.06370`). The paper must therefore **not** present the *direction* of its result as
   the contribution. The contribution is the artefact diagnosis plus what is unique to this fixture: a
   **typed single-label decision** over N = 2–8 named options; **option-order permutation** (pass-1 flips
   138/142/101/135/81 → 0 for the candidates); the **majority-class control at 0.4526 beating every encoder
   head by +0.1053**; and native per-option probabilities where the generative deciders must have theirs
   extracted. The blog post has none of those, and §1/§5's contribution list should be checked against that
   list.
4. **One honest weakness the counter-case sharpens — state it in §6, do not bury it.** The paper's best
   encoder head (0.3474) scores **below the majority-class control (0.4526)**. A referee who has read the
   counter-case knows a well-tuned ModernBERT-large can reach **0.892 F1** on a binary classification task.
   The obvious referee question — *"is your encoder arm undertrained, so that your shortfall measures your
   training recipe rather than the crossover?"* — is fair, and the counter-case makes it inevitable.
   The manuscript already reports the majority-class result honestly (that is to its credit and should not be
   softened); §6.5's limitation should say explicitly that the encoder arm's absolute level cannot be read as
   an architecture verdict, that the counter-case's 0.892 is a *different* (binary) task, and that the
   paper's claim is a **change of direction under fine-tuning**, not an estimate of an encoder ceiling.

## 4. What this changes in `OPEN_QUESTIONS.md` Q5 / `REFS.md`

- **Q5.3 is discharged:** the counter-case has an identifier, a URL and a date, with a verbatim excerpt
  (`REFS_VERIFIED.md` §3). It is **not** peer-reviewed; the paper must call it a blog post or a practitioner
  report, and must not dress it as a paper.
- The manuscript's current sentence — *"we name it here, we do not cite it, and we list it in
  `OPEN_QUESTIONS.md` as a reference a human must find"* — **is now obsolete** and should be replaced by the
  citation plus the differentiation paragraph above.
- Because the counter-case exists, the abstract's hedge *"Every public 'a small encoder wins' result we were
  able to locate … compares that encoder against a prompted LLM"* remains **true as written** (the
  counter-case is not a "small encoder wins" result), and **should keep its "we were able to locate"
  qualifier** — see `REFS_VERIFIED.md` §1, where this unit could not upgrade the absence claim to a
  documented search.

## 5. Second find (A3) — §2.1's "unsourced in the corpus" paragraph must shrink from four items to one

The 125M-RoBERTa claim (`REFS.md` §A3) was **located late** by a delegated scholarly search: **Benayas,
Sicilia & Mora-Cantallos, *A Comparative Analysis of Encoder Only and Decoder Only Models in Intent
Classification and Sentiment Analysis*, *Language Resources and Evaluation* 59(3):2007–2030 (2024), DOI
10.1007/s10579-024-09796-y** (preprint 10.21203/rs.3.rs-3865391/v1; no arXiv version) — full detail and the
four detail corrections in `REFS_VERIFIED.md` §2a and `REFERENCES_ADDITIONS.bib`.

Two consequences the merging unit must act on:

1. `MANUSCRIPT.md` §2.1's paragraph *"Unsourced in the corpus, and therefore not cited here"* currently lists
   **four** works. **Three of them now have identifiers** (this one, the counter-case, GLiNER, GLiClass — so
   only the search-protocol/absence item, Q5.1/B3, remains unsourced). The paragraph must be rewritten, not
   merely extended: the paper now cites the counter-case rather than naming it as unfindable.
2. **Use A3 as same-task evidence, not just a corroborating number.** Its Table 2 places four conditions on
   the **same** 77-class Banking task: prompted zero-shot LLaMA2 **30.85**, prompted few-shot **47.40**,
   fine-tuned LLaMA2 **70.87**, fine-tuned encoder **94.27** (macro F1). That is a **peer-reviewed** instance
   of exactly this paper's diagnosis — the comparison *class* moves the result more than the architecture
   does — and it is the strongest single citation §2.1 can carry for the artefact claim. Do not print "125M"
   as the paper's wording (it says ≈ 110–120M) and do not attribute "+23.4 F1" to it (that is the corpus's
   arithmetic).
