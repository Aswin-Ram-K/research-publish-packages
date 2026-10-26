# ROBERTA_CLAIM_SOURCING.md — UBEN1 · the `benayas2024comparative` contradiction, settled from primary sources

**Unit:** UBEN1. **Date of fetches:** 2026-10-15 (UTC). **AI-assisted? no — attempts are recorded.**
**Rule:** every identifier quoted below was seen on a page this unit fetched. Nothing is reconstructed from memory.
**No paper file was edited.** `REFERENCES.bib`, `main.tex`, and the release trees are untouched.

---

## 1. The contradiction, verbatim, as it stood

**Site 1 — `papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib:109-145` (the entry is complete and records FOUND):**

```
@article{benayas2024comparative,
  author    = {Benayas, Alberto and Sicilia, Miguel {\'A}ngel and Mora-Cantallops, Mar{\c c}al},
  title     = {A Comparative Analysis of Encoder Only and Decoder Only Models in Intent Classification and
               Sentiment Analysis: Navigating the Trade-Offs in Model Size and Performance},
  journal   = {Language Resources and Evaluation},
  volume    = {59},
  number    = {3},
  pages     = {2007--2030},
  year      = {2024},
  publisher = {Springer},
  doi       = {10.1007/s10579-024-09796-y},
  url       = {https://doi.org/10.1007/s10579-024-09796-y},
  note      = {FOUND (REFS.md A3 / OPEN\_QUESTIONS.md Q5.2 — the corpus's ``125M RoBERTa beats a fine-tuned
               LLaMA2-7B'' claim). Located and read by delegated subagent \texttt{c1b0bcc5} on 2026-10-15 via
               the Crossref API; ...
```
and its own four caveats (`:135-140`): *"(1) the paper never prints ``125M''; it says RoBERTa-base is ``approximately 110-120 million parameters''; (2) ``+23.4 F1'' is the corpus's arithmetic (94.27 $-$ 70.87), not printed; (3) the 94.27/70.87 pair are the MACRO figures (micro are 94.28/72.17); (4) the speedup is a serving measurement on one T4 at fixed output-token budgets..."*

**Site 2 — `papers/encoder-crossover-190/UNSOURCED_RETAINED.md:12` (and `:21-24`):**

```
| U1 | **125M RoBERTa beats fine-tuned LLaMA2-7B, 94.27 vs 70.87 on 77-class intent (29–108× faster)** | **NOT FOUND** | **Dropped** from the argument; **not cited**; explicitly named as unsourced and dropped (§2.1 new paragraph, §6.4) | §2.1, §6.4 |
```
```
## U1 — the 125M-RoBERTa claim (94.27 vs 70.87) — **dropped, not cited**
```

**Site 3 — `papers/encoder-crossover-190/REFERENCES.bib:21-23`:**

```
% STILL NOT INCLUDED, on purpose (no locatable identifier: UREFS could not source it — see
% REFS_VERIFIED.md §2): the 125M-RoBERTa 94.27 vs 70.87 on 77-class intent claim. It is recorded as
% unsourced in `UNSOURCED_RETAINED.md` and is not used in the manuscript's argument.
```
Note this comment cites `REFS_VERIFIED.md §2` as its authority for NOT FOUND — the same document whose status table says FOUND.

**Site 4 — `papers/encoder-crossover-190/REFS_VERIFIED.md:22` (the opposite finding):**

```
| A3 — 125M RoBERTa beats fine-tuned LLaMA2-7B, 94.27 vs 70.87 on 77-class intent | **FOUND** (by delegated scholarly search; see §2a) | Benayas, Sicilia & Mora-Cantallops, *Language Resources and Evaluation* **59**(3):2007–2030, 2024, DOI **10.1007/s10579-024-09796-y**; preprint DOI **10.21203/rs.3.rs-3865391/v1** |
```

**Site 5 — `papers/encoder-crossover-190/submission/BUILD_NOTES.md:54-55` (the deliberate exclusion):**

```
8. `benayas2024comparative` (present only in `REFERENCES_ADDITIONS.bib`) is **excluded**, matching
   the added paper's own statement that the 125M-RoBERTa claim "is not in the bibliography and is
   not used". The merged `REFERENCES.bib` already omits it.
```

**The stale downstream site — `main.tex:428`** (quoted in `strategy/BIBLIOGRAPHY_REPAIR.md:122`): *"The one corpus work that still has **no** locatable identifier --- the 125M-RoBERTa 94.27 vs 70.87 claim --- is **not** in the bibliography"*.

**Three independent `NOT FOUND`/drop claims (sites 2, 3, 5) against one `FOUND` claim (site 4).** The entry itself (site 1) is on the FOUND side.

---

## 2. The manuscript clause the entry would support

`papers/encoder-crossover-190/MANUSCRIPT.md:182-190`, quoted in full:

> **One item remains unsourced, and we do not cite it.** The corpus's claim that a 125M RoBERTa beats a
> fine-tuned LLaMA2-7B on 77-class intent (**94.27 vs 70.87**, 29–108× faster) still has **no locatable
> identifier**. UREFS ran 13 primary queries plus a delegated search of ≥ 8 further phrasings (exact-number,
> quoted-phrase, and Banking77/roberta-base framings, plus Semantic Scholar and OpenAlex lookups) and located
> no page carrying those numbers; the most plausible candidate (arXiv `2410.01627`, EMNLP 2024 Industry)
> evaluates intent detection on different datasets and does not carry them. The figure is **corroborating
> rather than load-bearing** for our thesis, so we **drop it from the paper's argument and do not cite it**;
> it is recorded as unsourced in `UNSOURCED_RETAINED.md` and §6.4. GLiNER and GLiClass, previously unsourced,
> now have identifiers and are treated in §2.2.

Numbers the clause asserts: **125M** parameters; **94.27 vs 70.87**; **29–108×**; **77-class** intent.

`papers/encoder-crossover-190/MANUSCRIPT.md:681-683` (§6.4), quoted in full:

> One figure the corpus carried is still uncited because no source could be located for it: the
> 125M-RoBERTa 94.27 vs 70.87 claim. It is **dropped from the argument** and recorded in
> `UNSOURCED_RETAINED.md` rather than attributed to an unverified source.

---

## 3. The primary source

**DOI resolution:** `curl -sSI -L https://doi.org/10.1007/s10579-024-09796-y` → **HTTP 200** (resolves; not dead, not paywalled at the resolver). The DOI is live.

**Crossref record** (`api.crossref.org/works/10.1007/s10579-024-09796-y`, HTTP 200, 23,210 bytes):

| field | value from Crossref |
|---|---|
| DOI | `10.1007/s10579-024-09796-y` |
| title | *A comparative analysis of encoder only and decoder only models in intent classification and sentiment analysis: navigating the trade-offs in model size and performance* |
| authors | Alberto Benayas; Miguel Angel Sicilia; Marçal Mora-Cantallops |
| container | *Language Resources and Evaluation* |
| volume/issue/pages | **59** / **3** / **2007-2030** |
| published | **2024-12-07** |
| type / publisher | `journal-article` / Springer Science and Business Media LLC |
| abstract | **not carried by Crossref** (`NONE IN CROSSREF`) |

**Every Crossref field matches the `REFERENCES_ADDITIONS.bib:109-119` entry exactly** — authors, title, journal, 59(3):2007–2030, 2024, Springer, DOI. The entry is not a fabrication; it is the right paper.

**Open-access preprint fetched and read** (Springer's own article page hides the tables behind the subscription; the CC-BY preprint does not): `https://www.researchsquare.com/article/rs-3865391/v1.pdf` → **HTTP 200, 285,470 bytes, PDF 1.7, 13 pages**, posted 2024-01-17, DOI `10.21203/rs.3.rs-3865391/v1`, CC-BY 4.0. Verbatim abstract:

> Intent classification and sentiment analysis stand as pivotal tasks in natural language processing, with applications ranging from virtual assistants to customer service. The advent of transformer-based models has significantly enhanced the performance of various NLP tasks, with encoder-only architectures gaining prominence for their effectiveness. More recently, there has been a surge in the development of larger and more powerful decoder-only models, traditionally employed for text generation tasks. This paper aims to answer the question of whether the colossal scale of newer decoder-only language models is essential for real-world applications by comparing their performance to the well established encoder-only models, in the domains of intent classification and sentiment analysis. Our results shows that for such natural language understanding tasks, encoder-only models in general provide better performance than decoder-only models, at a fraction of the computational demands.

**The numbers, each checked separately, from the preprint's own Table 2** (extracted with `pdftotext -layout`; lines 337–339 of the extraction):

```
Model                    SNIPS            ATIS             Banking          Massive
RoBERTa                  98.57 / 98.57    96.62 / 98.83    94.27 / 94.28    87.15 / 88.23
LLaMA2 Fine-Tuned        99.00 / 99.00    79.60 / 96.21    70.87 / 72.17    73.42 / 79.92
```

| manuscript asserts | source says | verdict on that number |
|---|---|---|
| 77-class intent | `Banking  Intent Classification  10003  3080  77` (Table 1, extraction line 287) | **carried** |
| **94.27** | RoBERTa Banking **94.27**/94.28 — the **macro** figure | **carried by the source**, but **on the do-not-cite list** |
| **70.87** | LLaMA2 Fine-Tuned Banking **70.87**/72.17 — the **macro** figure | **carried by the source**, but **on the do-not-cite list** |
| 29–108× faster | Table 7: Fine-Tuned LLaMA2 at 10 tokens = **29x**, at 50 tokens = **108x**, single T4 | **carried** (serving measurement, fixed output-token budgets) |
| 125M RoBERTa | line 215: RoBERTa "comprises approximately **110-120 million parameters**" | **NOT carried — the paper never prints "125M"** |
| +23.4 F1 | never printed; 94.27 − 70.87 is the corpus's arithmetic | **NOT carried** |
| gap grows with classes | extraction line 313: "a dataset like Banking with 77 classes shows the biggest per-formance gap" | **carried** |

---

## 4. The do-not-cite constraint, stated plainly

`94.27` and `70.87` are on this workspace's do-not-cite list as unsourced. That list is real and load-bearing: `orchestration/units/UPAPER9.md:65` — *"The do-not-cite list forbids the 94.27/70.87 numbers. Two units contradict; merging forces argument edits"*; `orchestration/units/UFIXBIB2.md:31` — *"reintroduce 125M-RoBERTa 94.27/70.87 (do-not-cite, unsourced)"*.

**This is the crux, and it cuts both ways.** The primary source *does* carry 94.27 and 70.87 in Table 2 — so the "unsourced" premise behind the do-not-cite list is factually stale. But the task's hard constraint forbids reintroducing them, and the do-not-cite list is a policy decision that this unit has no authority to overturn. So: **the figures are source-backed but remain barred.** Any rewrite must cite the paper for its *result* without reprinting the barred pair. The two are not in conflict once the paper is cited qualitatively — and the arithmetic gap "94.27 vs 70.87" in the clause is exactly what must not come back.

---

## 5. Verdict: **(b) rewrite it**

**Why not (a):** the entry *is* the right source, but the clause cannot be merged and cited as it stands — it asserts *"still has no locatable identifier"*, which the DOI's HTTP 200 and the Crossref record falsify outright. And it asserts **125M**, which the paper never prints; the paper says *"approximately 110-120 million parameters"*.

**Why not (c):** the source exists, resolves, is peer-reviewed, is same-task (BANKING77, 77 intents), and reports the encoder-over-decoder result the corpus claimed. Nothing here is unsupported in substance.

**(b) is the only verdict consistent with the evidence and the hard constraint.** The source says something materially different from the clause: same direction, different size wording, macro-not-unspecified F1, and a serving-measurement speedup rather than a general one.

**The exact minimal edit the paper would need.** Replace `MANUSCRIPT.md:182-190` — the whole paragraph beginning *"**One item remains unsourced, and we do not cite it.**"* — with:

> **One corpus claim is now sourced, and we cite it for its result.** The corpus's assertion that an encoder-only RoBERTa outperforms a fine-tuned LLaMA2-7B on 77-class intent classification is supported by Benayas, Sicilia & Mora-Cantallops (2024), *A comparative analysis of encoder only and decoder only models in intent classification and sentiment analysis*, *Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y` (`benayas2024comparative`). On BANKING77 (77 intents) the paper reports the encoder-only arm ahead of the fine-tuned decoder-only arm, and a decoder-only serving penalty of one to two orders of magnitude on a single T4. We cite it for that peer-reviewed, same-task encoder-over-decoder result; we do not reuse the corpus's "125M" formulation (the paper prints "approximately 110-120 million parameters") or its arithmetic "+23.4 F1" gap, which the paper does not print.

and replace `MANUSCRIPT.md:681-683` (§6.4) with:

> The corpus claim that was carried without an identifier — an encoder-only RoBERTa beating a fine-tuned LLaMA2-7B on 77-class intent classification — is now sourced to Benayas, Sicilia & Mora-Cantallops (2024), *Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y`, and cited for that result.

and correct `main.tex:428`, which still says the claim *"still has **no** locatable identifier"* — false as of this unit.

**Accompanying record edits (not this unit's to make):** `UNSOURCED_RETAINED.md:12,21-24` (U1 status `NOT FOUND`→`FOUND`, dropped→cited), `REFERENCES.bib:21-23` (delete the stale "STILL NOT INCLUDED, on purpose" comment), `BUILD_NOTES.md:54-55` (the exclusion premise is void), and merge `REFERENCES_ADDITIONS.bib:109-145` into `REFERENCES.bib` — **with the `94.27`/`70.87` strings kept out of both the printed paper and the new reference entry's printed text**, and the entry's `note` retained as a working note only. **That merge is not performed here** (write-path ban).

**Status: COMPLETE (not partial).** The DOI resolved; the primary source was fetched in full; every asserted number was checked against it individually.
