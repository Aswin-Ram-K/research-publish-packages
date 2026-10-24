# UNSOURCED_RETAINED.md — UPAPER1c · what is still unsourced after UREFS, and what the manuscript does about it

**Unit:** UPAPER1c, 2026-10-15. **Companion to:** `REFS_VERIFIED.md` (UREFS), `MANUSCRIPT_CHANGES.md`
(this unit's change log), `REFERENCES.bib`.
**Rule applied:** never invent a citation, identifier, number or result. Where no source exists, the item is
recorded here and the manuscript states what it does instead. **No fabricated citation for any item below.**

## Status table

| # | item | UREFS status | what `MANUSCRIPT.md` now does | where |
|---|---|---|---|---|
| U1 | **125M RoBERTa beats fine-tuned LLaMA2-7B, 94.27 vs 70.87 on 77-class intent (29–108× faster)** | **NOT FOUND** | **Dropped** from the argument; **not cited**; explicitly named as unsourced and dropped (§2.1 new paragraph, §6.4) | §2.1, §6.4 |
| U2 | **External backing for "no published measurement exists…" (the absence claim)** | **NOT FOUND** | **Hedged and retained**: *"we were able to locate"* / *"no published measurement was found"*; the hedge's retention is itself stated and justified | §2.1, §6.4; abstract |
| U3 | **Equal-fine-tuning-effort counter-case (ADE, 93.1 vs 89.2)** | **FOUND** (blog post, no DOI) | **Now cited** as a non-peer-reviewed blog post; **no priority** claimed for its direction; its prompted arm (80.7) is used as corroboration | §2.1, §1, §5.1, §6.4 |
| U4 | **GLiNER / `fastino/GLiNER2.5-Decide`** | **FOUND** | Identifiers merged; corpus's span-extraction sentence corrected (accurate for GLiNER 2023/2024, **not** for the GLiNER2 decision-model variant) | §2.2, `REFERENCES.bib` |
| U5 | **GLiClass** | **FOUND** | Identifier merged; the "no measured LLM head-to-head" claim confirmed and phrased as an argument from absence | §2.2, `REFERENCES.bib` |
| U6 | **Is the encoder arm under-trained?** (new, surfaced by U3) | **NOT ANSWERABLE** from the evidence tree | Written into §6.6 in the reviewer's voice and answered only as far as the evidence allows; named as an **open question** | §6.6 |
| — | **Note 2026-10-16 (UMERGE1):** the **U1** row above is superseded, and its 2026-10-15 bytes are retained unchanged. | **FOUND** | U1 is **sourced and cited**: Benayas, Sicilia & Mora-Cantallops (2024), *Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y` (`benayas2024comparative`), merged into `REFERENCES.bib`; cited at §2.1, §6.4 and References. | §2.1, §6.4 |

---

## U1 — the 125M-RoBERTa claim (94.27 vs 70.87) — **dropped, not cited**

**Note 2026-10-16 (UMERGE1):** the section below is the 2026-10-15 record and is retained unchanged. It was
superseded by UBEN1's primary-source fetch: the source was located (DOI `10.1007/s10579-024-09796-y`),
`benayas2024comparative` is merged in `REFERENCES.bib`, and the manuscript now cites it at §2.1/§6.4. The
two Banking77 macro figures remain barred from the manuscript prose by the workspace do-not-cite list.

**Claim as the corpus carried it:** a 125M RoBERTa beats a fine-tuned LLaMA2-7B on 77-class intent
classification, 94.27 vs 70.87, and is 29–108× faster; the performance gap grows with the number of classes.

**UREFS result:** **NOT FOUND.** No page carrying those numbers (94.27, 70.87, +23.4, 29–108×, 77 classes, or
the quoted sentence) was located. The most plausible candidate found by search — *"Intent Detection in the Age
of LLMs"*, arXiv `2410.01627` / ACL EMNLP 2024 Industry `2024.emnlp-industry.114` — evaluates LLMs for intent
detection on real-world TODS datasets, **not** Banking77, and the numbers were not seen on any page fetched. It
is **not** established as the source.

**What the manuscript does:** the figure was **corroborating, not load-bearing**, so dropping it costs the
paper nothing (`REFS_VERIFIED.md` §2 says exactly this). §2.1 now records it as unsourced and **dropped from
the argument**; §6.4 records the same. It is **not** in `REFERENCES.bib` and is **not** attributed to any
internal document as if it were a citation. **A human may still source it later**, in which case §2.1's
paragraph would be replaced by a citation — the item is not deleted from the record, only from the argument.

**Queries already run — do NOT repeat these (13 primary, this unit + one delegated DDG crawl):**

1. `RoBERTa 125M beats fine-tuned LLaMA2-7B 77-class intent classification 94.27`
2. `Banking77 intent classification RoBERTa versus fine-tuned LLaMA2-7B comparison encoder wins`
3. `"the performance gap grows with the number of classes" intent classification encoder LLM`
4. `Banking77 77 intents fine-tuned LLaMA-2 7B low accuracy RoBERTa 94% intent classification paper`
5. `"Intent Detection in the Age of LLMs" fine-tuned encoder Banking77 comparison`
6. `intent detection small encoder outperforms fine-tuned large language model 77 classes faster arXiv 2024`
7. `fine-tuned RoBERTa base versus fine-tuned LLaMA 2 intent classification accuracy gap number of classes study`
8. `"94.27" "70.87" intent classification`
9. `encoder 108 times faster than fine-tuned LLM intent classification 125M parameters`
10. `large language models intent classification number of classes performance gap encoder baseline empirical`
11. `"125M" RoBERTa "LLaMA2-7B" intent classification fine-tuned comparison`
12. `"performance gap grows with the number of classes"`
13. direct DuckDuckGo-HTML crawl for `"94.27" "70.87" intent classification` (timed out)

**Plus a delegated search (subagent `c1b0bcc5`), ≥ 8 further phrasings:** exact-number queries,
quoted-phrase queries, the Banking77/roberta-base framings, plus **Semantic Scholar** and **OpenAlex** API
lookups and direct search-engine crawls. At the time `REFS_VERIFIED.md` was written that search had **not**
returned a located source. **Nothing was found.** Do not repeat these phrasings; a future attempt should start
from the candidate paper's reference list or a citation index, not a keyword search.

---

## U2 — the literature-absence claim — **hedged and retained (do not upgrade)**

**Claim:** *"No published measurement was found of a small encoder beating a fine-tuned generative model on a
typed single-label decision — verified-absent, and the second lane checked it explicitly."*
(`DECIDER_STACK_DECISION.md` §11.6, commit `ad301ae`.)

**UREFS result:** **NOT FOUND.** Neither the recorded search protocol (databases, queries, dates, inclusion
rules) nor an external survey establishing the same absence was located. Two survey-framed searches were run
and the closest candidates read; none discharges the claim. The nearest works buy only the *prompted*-baseline
half:

- **arXiv `2501.08457`** (Kostina et al. 2025) — encoder-vs-LLM text classification, but its LLM arms are
  **prompted**;
- **ACL 2025 Industry `2025.acl-industry.68`** (Li et al. 2025) — evaluates **prompting and supervised
  fine-tuning** for smaller models in industry (the closest equal-effort-adjacent evaluation found), but it is
  an evaluation, **not** a proof of absence, and its per-task results were not retrieved;
- **arXiv `2507.11412`** (Weller et al. 2025, ICLR'26) — the strongest *matched-training-recipe* support for
  the encoder side (*"a 400M encoder outperforms a 1B decoder on MNLI"*), but its headline classification task
  is MNLI (3-way), not a typed single-label decision over N = 2–8 named options.

**What the manuscript does:** keeps the **hedge exactly as written** — *"we were able to locate"*, *"no
published measurement was found"* — and states in §6.4 that UREFS's external search **failed to upgrade the
hedge**, so the weaker phrasing stays. It is **never** upgraded to *"no such work exists"*. The three works
above are cited but explicitly marked **`ADJACENT`** in `REFERENCES.bib` and §2.2, and the manuscript says in
terms that **none of them discharges the absence claim**. `source_decider_stack_2026` (the internal §11.6
errata) remains the citation for the core claim, described as an internal verified-absent audit whose search
protocol is not recorded — **not** as an external survey.

**Queries already run — do NOT repeat these (2 survey-framed, this unit):**

1. `survey small language models versus LLMs text classification fine-tuning efficiency encoder-only`
2. `Li Sleem Gentile Nichil State "Small Language Models in the Real World" industrial text classification arXiv`

**What would close U2:** either the corpus's own recorded search protocol (databases, exact queries, dates,
inclusion rules) — which must be supplied by whoever ran the original literature lane, since it is **not** in
the corpus — or a genuine external survey of encoder-vs-**fine-tuned**-generative comparisons on typed
single-label decisions. Keyword searching alone has now been tried twice and failed.

---

## U6 — the open question the counter-case creates: is the encoder arm under-trained? — **not answerable from this tree**

**Not a citation gap** — an evidence gap. It is recorded here because §6.6 names it as an open question and a
verifier should see it stated plainly:

- The paper's best encoder head is **0.3474**, **below** its own majority-class control (**0.4526**), while the
  sourced counter-case reports a real ModernBERT-large at **0.892 F1** on a *binary* task. Nothing in this
  paper excludes the reading that part of the encoder shortfall reflects the training recipe rather than the
  crossover.
- The evidence tree contains **no tuning-effort or compute study** for the encoder arms, and the paper makes
  **no equal-effort claim** of its own (the counter-case's *"under one dollar, under 15 minutes"* premise is
  its own, on its own task).
- Closing it would need a sweep on this fixture that was **not run** — including the fourth arm already named
  as an open decision in `OPEN_QUESTIONS.md`: **a trained linear probe on a frozen LLM embedding**, which is
  **not present anywhere in the evidence tree** (§6.5).

**What the manuscript does:** §6.6 quotes the reviewer's objection and answers it only as far as the evidence
goes — the 0.892 is a different instrument, the majority-class control licenses only "no head is a viable
default", the ±1–2 point non-reproducibility band is **not** evidence the recipe is adequate, and the
alternative reading **stays open**. No number is invented and no claim beyond the evidence is made.

---

## What is *not* on this list (for the verifier's benefit)

The following were `UNSOURCED` before UREFS and are **now sourced and merged** — they must not reappear here
as gaps: the equal-fine-tuning-effort counter-case (`simmering2025modernbert`), GLiNER
(`zaratiana2024gliner`), GLiNER2 (`zaratiana2025gliner2`), GLiClass (`stepanov2025gliclass`), and the three
`ADJACENT` neighbours. Their identifiers, URLs and verification dates are in `REFS_VERIFIED.md` and
`REFERENCES.bib`. Four identifier-only entries that pre-dated UREFS (`2602.06370`, `2512.12677`,
`2309.03882`, `2305.13971`) are unchanged and remain **incomplete in title/authors/venue because the corpus
did not record them** — that is recorded as bibliography hygiene in `OPEN_QUESTIONS.md` Q5 and is **outside
this unit's purpose**.
