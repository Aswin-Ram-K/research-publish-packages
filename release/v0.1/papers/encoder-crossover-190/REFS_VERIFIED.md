# REFS_VERIFIED.md — UREFS · the four `UNSOURCED` items, searched and verified

**Unit:** UREFS. **Date all fetches made:** **2026-10-15** (UTC). Target `the read-only target repository`
**read-only**: HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` before and after; `status --porcelain`
identical both times (4 pre-existing untracked entries: `.ci-trunk.txt`, `.relay/`,
`docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `docs/migration/` — attributed to the unrelated
concurrent session, **not** to this unit; no tracked file modified).

**Rule applied:** every identifier below was **seen on a page this unit — or its declared delegate — fetched**.
Nothing is reconstructed from memory. Where a claim could not be discharged, it is `NOT FOUND` and the
queries are listed. §2 and §6 record work done by delegated subagent `c1b0bcc5`; that is stated explicitly
wherever it is relied on.

**Scope note.** `OPEN_QUESTIONS.md` Q5 numbers four items; `REFS.md` counts four `UNSOURCED` works
(A3, A4, B1, B2) plus **one load-bearing claim with no citation at all** (B3 — the literature-search claim).
This unit treats **five** objects: Q5.1 / B3 (the absence claim), A3 (125M-RoBERTa), A4 (the counter-case,
the highest-priority target), B1 (GLiNER) and B2 (GLiClass).

| Item | Status | Identifier observed |
|---|---|---|
| Q5.1 / B3 — external backing for "no published measurement…" | **NOT FOUND** (no survey or search record located) | — (3 adjacent works identified, listed below) |
| A3 — 125M RoBERTa beats fine-tuned LLaMA2-7B, 94.27 vs 70.87 on 77-class intent | **FOUND** (by delegated scholarly search; see §2a) | Benayas, Sicilia & Mora-Cantallops, *Language Resources and Evaluation* **59**(3):2007–2030, 2024, DOI **10.1007/s10579-024-09796-y**; preprint DOI **10.21203/rs.3.rs-3865391/v1** |
| A4 — equal-fine-tuning-effort counter-case (ADE, 93.1 vs 89.2, 152 vs 87 ex/s) | **FOUND** | Paul Simmering blog post, **2025-01-12**, `https://simmering.dev/blog/modernbert-vs-llm/` (no DOI, **not peer-reviewed**) |
| B1 — GLiNER | **FOUND** (and a **new** GLiNER2 identifier found on the cited model card) | GLiNER: arXiv **2311.08526**; NAACL 2024, pp. 5364–5376, DOI **10.18653/v1/2024.naacl-long.300**. GLiNER2: arXiv **2507.18546** |
| B2 — GLiClass | **FOUND** | arXiv **2508.07662** (11 Aug 2025) |

---

## 1. Q5.1 / `REFS.md` §B3 — external backing for "no published measurement was found…" — **NOT FOUND**

**What the corpus claims** (`DECIDER_STACK_DECISION.md` §11.6, commit `ad301ae`): *"No published measurement
was found of a small encoder beating a fine-tuned generative model on a typed single-label decision —
verified-absent, and the second lane checked it explicitly."*

**What was needed:** either the recorded search protocol (databases, queries, dates, inclusion rules) or an
external **survey** that establishes the same absence. **Neither was located.** I ran **two** survey-framed
searches (below) and read the closest candidates. No survey was found that surveys
encoder-vs-**fine-tuned**-generative comparisons on typed single-label decisions — the closest works buy the
*prompted*-baseline half of the claim, not the absence.

**Adjacent works found (all fetched, all real; none discharges the absence claim):**

- **Kostina, Dikaiakos, Stefanidis & Pallis (2025), "Large Language Models For Text Classification: Case
  Study And Comprehensive Review", arXiv:2501.08457**, submitted 14 Jan 2025,
  `https://arxiv.org/abs/2501.08457`. Abstract verbatim: *"we evaluate the performance of different LLMs in
  comparison with state-of-the-art deep-learning and machine-learning models… We find that LLMs, particularly
  Llama3 and GPT-4, can outperform traditional methods in complex classification tasks, such as multiclass
  classification, though at the cost of longer inference times."* The HTML carries: *"we compare decoder-only
  models with RoBERTa, an encoder-only baseline for text classification"*. **Bears on the paper:** this is an
  encoder-vs-LLM text-classification study, but the LLM arms are **prompted** — it is evidence *for* the
  prompted-baseline half of §11.6, **not** a survey establishing the absence of a fine-tuned comparison.
- **Li, Sleem, Gentile, Nichil & State (2025), "Small Language Models in the Real World: Insights from
  Industrial Text Classification", ACL 2025 Industry Track, pp. 971–982, DOI 10.18653/v1/2025.acl-industry.68**,
  `https://aclanthology.org/2025.acl-industry.68/` (abstract page fetched; the PDF would not parse as text).
  Abstract verbatim: *"we conduct a comprehensive evaluation of prompt engineering and supervised fine-tuning
  methods for transformer-based text classification… we examine the strengths and limitations of smaller
  models, with particular attention to both their performance and their efficiency in Video Random-Access
  Memory (VRAM) utilization"*. **Bears on the paper:** the closest thing found to an *equal-effort* study —
  it evaluates **both** prompting **and** supervised fine-tuning for smaller models in industrial settings —
  but it is an evaluation, not a proof of absence, and its per-task results were not retrieved by this unit.
- **Weller, Ricci, Marone, Chaffin, Lawrie & Van Durme, "Seq vs Seq: An Open Suite of Paired Encoders and
  Decoders", arXiv:2507.11412** (v2 12 Mar 2026; comments: **Accepted to ICLR'26**),
  `https://arxiv.org/abs/2507.11412`. Abstract verbatim: *"we find that encoder-only models excel at
  classification and retrieval tasks while decoders excel at generative tasks… a 400M encoder outperforms a
  1B decoder on MNLI"*, under *"the same recipe for both encoder-only and decoder-only models"*. **Bears on
  the paper:** this is the strongest *matched-training-recipe* external support for the encoder-wins side,
  and it is peer-reviewed — but its headline classification task is **MNLI (3-way)**, not a typed
  single-label decision over N = 2–8 named options, so it does not make the corpus's absence claim true or
  false; it does give the paper a citable, peer-reviewed anchor for "encoders excel at classification at
  matched compute".

**Queries run (item 1):** `survey small language models versus LLMs text classification fine-tuning
efficiency encoder-only`; `Li Sleem Gentile Nichil State "Small Language Models in the Real World" industrial
text classification arXiv`.

**Consequence for the manuscript:** the current hedge — *"we were able to locate"* / *"no published
measurement was found"* — is the correct phrasing and **must be kept**. This unit could **not** upgrade it to
*"no such work exists"*, and could **not** supply a survey that would let it. The absence remains an internal,
unrecorded search. `REFERENCES.bib`'s `source_decider_stack_2026` entry (internal errata as the citation) stays
as-is; the three works above are candidates for §2.2 *if* the paper wants external, citable neighbours.

---

## 2. A3 — "125M RoBERTa beats a fine-tuned LLaMA2-7B on 77-class intent (94.27 vs 70.87, 29–108× faster)"

**Status: `FOUND` — §2a is the authoritative result.** This unit's own web-search path returned **nothing**
(13 queries: exact-number, quoted-phrase, Banking77/roberta-base framings, plus a DuckDuckGo-HTML crawl that
timed out), so the item was delegated to subagent `c1b0bcc5` with a ≥ 8-phrasing instruction and a mandate to
try scholarly APIs. **The delegate found the source on the scholarly route; the exact-number web queries never
reach it.** The negative is kept below as the record of what a web-search-only search could and could not
reach — it is *not* the item's final status.

**Queries this unit ran before delegating:** `RoBERTa 125M beats fine-tuned LLaMA2-7B 77-class intent
classification 94.27`; `Banking77 intent classification RoBERTa versus fine-tuned LLaMA2-7B comparison encoder
wins`; `"the performance gap grows with the number of classes" intent classification encoder LLM`; `Banking77
77 intents fine-tuned LLaMA-2 7B low accuracy RoBERTa 94% intent classification paper`; `"Intent Detection in
the Age of LLMs" fine-tuned encoder Banking77 comparison`; `intent detection small encoder outperforms
fine-tuned large language model 77 classes faster arXiv 2024`; `fine-tuned RoBERTa base versus fine-tuned
LLaMA 2 intent classification accuracy gap number of classes study`; `"94.27" "70.87" intent classification`;
`encoder 108 times faster than fine-tuned LLM intent classification 125M parameters`; `large language models
intent classification number of classes performance gap encoder baseline empirical`; `"125M" RoBERTa
"LLaMA2-7B" intent classification fine-tuned comparison`; `"performance gap grows with the number of
classes"`; plus one DuckDuckGo-HTML crawl for `"94.27" "70.87" intent classification` (timed out). A candidate
that search surfaced — *"Intent Detection in the Age of LLMs"*, arXiv:2410.01627 / ACL EMNLP 2024 Industry
`2024.emnlp-industry.114` — is **not** the source (different datasets, TODS rather than Banking77).

### 2a. The source (found by delegate `c1b0bcc5`; identifiers from the fetched PDF and the Crossref API)

- **Title:** *A Comparative Analysis of Encoder Only and Decoder Only Models in Intent Classification and
  Sentiment Analysis: Navigating the Trade-Offs in Model Size and Performance*.
- **Authors:** Alberto Benayas, Miguel Ángel Sicilia, Marçal Mora-Cantallops (Computer Science Dept.,
  University of Alcalá, Spain).
- **Peer-reviewed version:** ***Language Resources and Evaluation* (Springer), vol. 59, issue 3,
  pp. 2007–2030, 2024; DOI `10.1007/s10579-024-09796-y`** (Crossref metadata; Unpaywall confirms the journal
  article is OA via the preprint).
- **Preprint:** Research Square, posted **2024-01-17**, **DOI `10.21203/rs.3.rs-3865391/v1`**,
  `https://www.researchsquare.com/article/rs-3865391/v1.pdf` (fetched; `latest.pdf` re-fetched and
  re-verified). **No arXiv version exists** (arXiv API author/title search returned nothing).
- **URLs actually fetched:** the two Research Square PDFs above, plus the Crossref API for both DOIs.
- **Verbatim excerpt — Table 2, "F1-Score macro and micro averaged, for the Intent Classification task"**
  (columns SNIPS / ATIS / **Banking** / Massive; the paper states Banking has **77 classes**):

  > `RoBERTa 98.57 / 98.57 96.62 / 98.83 94.27 / 94.28 87.15 / 88.23`
  > `LLaMA2 Fine-Tuned 99.00 / 99.00 79.60 / 96.21 70.87 / 72.17 73.42 / 79.92`
  > `LLaMA2 Zero-Shots 84.47 / 81.92 60.74 / 88.27 30.85 / 27.24 42.87 / 40.95`
  > `LLaMA2 Few-Shots 90.24 / 89.14 70.78 / 87.61 47.40 / 45.00 58.41 / 54.33`

- **⭐ The same table carries the paper's own prompted-vs-fine-tuned contrast, on the same 77-class task** —
  and it points the way this paper's thesis predicts: on Banking, prompted LLaMA2 scores **30.85 (zero-shot)**
  and **47.40 (few-shot)**, fine-tuning it reaches **70.87**, and the **encoder wins at 94.27**. That makes
  item A3 simultaneously (i) the source the corpus quoted, and (ii) **peer-reviewed, same-task evidence that
  the comparison class — prompted versus fine-tuned — is what moves the result**, which is precisely the
  artefact this paper diagnoses. §2.1 should use it that way.

- **Verbatim excerpt — §4.1, the sentence the corpus quotes:** *"The performance gap between RoBERTa and all
  LLaMA2 approaches grows with the number of classes in the dataset. On one hand, datasets with a reduced
  number of classes, like SNIPS with 7 classes, offer no difference in performance between RoBERTa and
  LLaMA2. On the other hand, a dataset like Banking with 77 classes shows the biggest performance gap."*
- **Verbatim excerpt — Table 7:** *"Latency multiples taking RoBERTa inference time as a baseline. Calculated
  on a single T4 GPU machine."* → `Fine-Tuned LLaMA2 10 29x / 25 56x / 50 108x` — **this is the corpus's
  "29–108× faster"** (fine-tuned LLaMA2 at 10 vs 50 max output tokens).
- **How it bears on the paper — SUPPORTS, with four detail corrections the writer must not smooth over:**
  1. **"125M RoBERTa" is the corpus's figure, not the paper's.** The paper writes *"RoBERTa-base typically
     comprises approximately 110-120 million parameters"*; the string *125M* does not appear in it. Write
     "RoBERTa-base (≈ 110–120M)" or keep "125M" only as the corpus's paraphrase.
  2. **"+23.4 F1" is the corpus's arithmetic** (94.27 − 70.87 = 23.40), not printed in the paper.
  3. **"F1" is macro-and-micro averaged.** The paper's 94.27 / 70.87 pair are the **macro** figures
     (micro: 94.28 / 72.17).
  4. **The speedup is a serving measurement, not an architecture property:** single T4 GPU, fine-tuned LLaMA2
     at 10 vs 50 max output tokens; the paper also frames latency generally as *"one to two orders of
     magnitude"*. "Banking" = **BANKING77** (77 intents).
- **Consequence for the manuscript:** item A3 is now **citable**, and it is one of the paper's *own-direction*
  corroborations (an encoder beating a fine-tuned 7B, with the gap growing in the number of classes) — so it
  is worth keeping, with the four corrections above. It is **peer-reviewed** (Springer LREC), unlike the A4
  counter-case.

---

## 3. A4 — the equal-fine-tuning-effort counter-case — **FOUND** ⭐ (highest-priority target)

- **Identifier observed:** no DOI, no arXiv id, no venue — a **blog post**.
  **Author:** Paul Simmering. **Title:** *"ModernBERT vs LLMs for Detecting Adverse Drug Reactions"*.
  **Published (on the page):** **2025-01-12**. **URL:** `https://simmering.dev/blog/modernbert-vs-llm/`.
  **Fetched:** 2026-10-15 (HTTP 200). Supporting artifacts named on the page: a GitHub directory, a
  Weights & Biases project (`wandb.ai/psimm/modernbert-vs-llm`), and the `ade-benchmark-corpus/ade_corpus_v2`
  dataset. **Not peer-reviewed.**
- **Verbatim excerpt — the results table (all four corpus numbers, exactly):**

  > | Setup | F1 Score (%) | Recall (%) | Precision (%) | Examples/sec | Configuration |
  > |---|---|---|---|---|---|
  > | 1a-modernbert-base | 86.0 | 90.3 | 82.2 | 118 | transformers pipeline, batch size 128 |
  > | 1b-modernbert-large | 89.2 | 91.8 | 86.8 | 87 | transformers pipeline, batch size 128 |
  > | 2-DSPy-25-threads-Llama-3.2-3B-Instruct | 80.7 | 87.9 | 74.6 | 4 | DSPy, 25 threads, vLLM OpenAI server with default settings |
  > | 3-Llama-3.2-3B-Instruct-LoRA | 93.1 | 92.0 | 94.2 | 152 | vLLM, default settings |

- **Verbatim excerpt — equal-effort and the counter-case conclusion:**

  > *"All setups can be trained for under one dollar and in less than 15 minutes. The differences are
  > negligible."* … *"The clear winner of the experiment is the LoRA fine-tuned Llama 3.2-3B. It's the most
  > accurate and the fastest."* … *"Llama 3.2-3B with a fine-tuned LoRA adapter outperformed it in accuracy
  > in this experiment. Its architecture as a decoder-only model is, in theory, less suited for structured
  > tasks. **Did it win by sheer size?** It would be interesting to see what a ModernBERT-3B or -8B model
  > would achieve."*

- **Verbatim excerpt — the throughput caveat (the blog's own, and it is decisive):**

  > *"This is down to vLLM being extremely well optimized and using CUDA graph capturing ahead of inference
  > time. **If that preparation time of 30 seconds is added, it's examples per second go down to 42.**"* …
  > *"Note that this speed comparison was not comprehensive and is dependent on the GPU, the inference library
  > and the exact settings used, such as batch size."*

- **Verbatim excerpt — the blog's prompted arm, which reproduces this paper's actual thesis:**

  > *"Fine-tuning continues to outperform purely prompt-based approaches, even when those are optimized using
  > automated prompt engineering."* (Setup 2, DSPy-optimized few-shot Llama 3.2-3B + vLLM, scored **80.7 F1
  > vs ModernBERT-large's 89.2**.)

- **How it bears on the paper: CONTRADICTS a claim the *corpus* makes; does not contradict the manuscript's
  stated thesis; and it is a novelty threat. See `RELATED_WORK_NOTES.md` for the full engagement.**
  Task: **binary** adverse-drug-reaction sentence classification (ADE corpus, 20,896 unique sentences
  de-duplicated, negatives subsampled to 4,271 to balance, 60/20/20 split) — **N = 2**, and sentences, not
  named options. Fine-tuning effort: ModernBERT-base ≈ 2 min, ModernBERT-large ≈ 3.5 min, Llama LoRA ≈ 8 min
  on one A10G; *"under one dollar and in less than 15 minutes"* for all three — i.e. **the equal-effort
  premise is real**. Model scale: 395M encoder vs **3B** decoder (≈ 7.6× the encoder's parameters).

---

## 4. B1 — GLiNER — **FOUND** (two publications; one partly re-frames the corpus's claim)

### 4a. The GLiNER publication

- **Identifier observed:** arXiv **2311.08526** — *"GLiNER: Generalist Model for Named Entity Recognition
  using Bidirectional Transformer"*, **Urchade Zaratiana, Nadi Tomeh, Pierre Holat, Thierry Charnois**,
  submitted 14 Nov 2023, `https://arxiv.org/abs/2311.08526`. Published version: **NAACL 2024 (Volume 1: Long
  Papers), pp. 5364–5376, DOI 10.18653/v1/2024.naacl-long.300**, `https://aclanthology.org/2024.naacl-long.300/`
  (both pages fetched).
- **Verbatim excerpt (arXiv abstract page, identical on the ACL Anthology page):** *"Leveraging a
  bidirectional transformer encoder, our model, GLiNER, facilitates parallel entity extraction, an advantage
  over the slow sequential token generation of LLMs. Through comprehensive testing, GLiNER demonstrate strong
  performance, outperforming both ChatGPT and fine-tuned LLMs in zero-shot evaluations on various NER
  benchmarks."*
- **How it bears on the paper — SUPPORTS the §11.6 qualification:** GLiNER is a **span-extraction (NER)**
  model, and its advantage is stated against **zero-shot** (prompted) evaluations. The corpus's sentence
  *"GLiNER's win is span extraction (exact-match F1), not a typed single-label decision"* is accurate **for
  this 2023/2024 work**.

### 4b. `fastino/GLiNER2.5-Decide` — the model id the corpus actually names — **also has a publication, and it qualifies the corpus's framing**

- **Identifier observed on the model card:** the HuggingFace page `https://huggingface.co/fastino/GLiNER2.5-Decide`
  (fetched 2026-10-15, HTTP 200) carries the literal metadata line **`arxiv: 2507.18546`** and
  **`License: apache-2.0`**, with pipeline tag *Text Classification* and community tags including
  **`Intent classification`**, *Sentiment Analysis*, *Topic classification*, **`decision-model`**.
- **The cited paper:** arXiv **2507.18546** — *"GLiNER2: An Efficient Multi-Task Information Extraction System
  with Schema-Driven Interface"*, **Urchade Zaratiana, Gil Pasternak, Oliver Boyd, George Hurn-Maloney, Ash
  Lewis**, submitted 24 Jul 2025, `https://arxiv.org/abs/2507.18546`. Abstract verbatim: *"We present GLiNER2,
  a unified framework that enhances the original GLiNER architecture to support named entity recognition,
  **text classification**, and hierarchical structured data extraction within a single efficient model… Our
  experiments demonstrate competitive performance across extraction and **classification tasks** with
  substantial improvements in deployment accessibility compared to **LLM-based alternatives**."*
- **How it bears on the paper — `DIFFERENT` / needs qualification:** the corpus's blanket statement that
  "GLiNER's win is span extraction, not a typed single-label decision" **does not hold for the model it
  actually cites** (`GLiNER2.5-Decide`): GLiNER2 explicitly covers **text classification**, and this variant
  is tagged a *decision model* for *intent classification*. What the abstract does **not** show is the
  comparison class of the "LLM-based alternatives" — this unit **could not determine from the abstract whether
  GLiNER2's classification comparison is against prompted or fine-tuned LLMs**. Recommendation: the paper
  should cite GLiNER (2311.08526) for the span-extraction point and **either** drop the `GLiNER2.5-Decide`
  example **or** re-word so it does not imply the decision-model variant is a span extractor. `REFS.md`'s
  licence note (`cc-by-nc-4.0` for v0/v1 weights) is consistent with an Apache-2.0 model card for a *different*
  artifact; this unit verified only the card's stated licence.

---

## 5. B2 — GLiClass — **FOUND**, and the corpus's sub-claim is **confirmed**

- **Identifier observed:** arXiv **2508.07662** — *"GLiClass: Generalist Lightweight Model for Sequence
  Classification Tasks"*, **Ihor Stepanov, Mykhailo Shtopko, Dmytro Vodianytskyi, Oleksandr Lukashov, Alexander
  Yavorskyi, Mykyta Yaroshenko** (Knowledgator Engineering, Kyiv), submitted **11 Aug 2025**,
  `https://arxiv.org/abs/2508.07662`; full HTML read at `https://arxiv.org/html/2508.07662v1`; project page
  `https://www.knowledgator.com/research/gliclass`. Licence shown on arXiv: CC BY-NC-ND 4.0.
- **Verbatim excerpt (abstract):** *"While generative LLMs have become mainstream for zero-shot classification
  due to their versatility, they suffer from inconsistent instruction following and computational
  inefficiency. Cross-encoders, commonly used as rerankers in RAG pipelines, face a different bottleneck…
  We propose GLiClass, a novel method that adapts the GLiNER architecture for sequence classification tasks."*
- **Verbatim excerpt (§4 Discussion, on the LLM comparison):** *"Table 7 compares GLiClass with large language
  models (LLMs), cross-encoders, and embeddings-based models. GLiClass achieves better scalability and
  efficiency than cross-encoders."* Table 7's LLM column is **qualitative prose only** (e.g. Computational
  Efficiency → LLMs: *"Low; autoregressive generation is computationally intensive, high latency for
  inference"*), with **no model names and no scores**.
- **How it bears on the paper — SUPPORTS the corpus's claim:** the paper's **quantitative** baselines
  (Tables 3–6) are **only four cross-encoder/NLI models** (`deberta-v3-large-zeroshot-v2.0`,
  `deberta-v3-base-zeroshot-v2.0`, `roberta-large-zeroshot-v2.0-c`, `comprehend_it-base`); **no generative
  LLM has a numeric row or column anywhere**, and GPT-4o appears only as an *annotation tool* for training
  data. So *"GLiClass has no measured LLM head-to-head at all (its own comparison table is qualitative)"* is
  **correct**, and the writer should phrase it as an argument from absence, as `REFS.md` §B2 already directs.
  **One correction to `REFS.md` §B2:** its parenthetical implies embedding-based/SetFit methods are the
  quantitative baselines — they too appear **only** in the qualitative Table 7.

---

## 6. Delegated search records

### 6a. `c1b0bcc5` — item A3 (125M RoBERTa) → **FOUND** (result in §2a)

Channels that worked: **Crossref API** (what located the paper), arXiv API, Semantic Scholar API, Brave
Search HTML, Bing RSS/HTML, Unpaywall. Blocked/empty: Google & Google Scholar (429/JS), DuckDuckGo html/lite
(timeout), grep.app (Vercel checkpoint), Startpage/Ecosia (bot wall), searchcode (404), Mojeek (403), and —
notably — **every exact-number web query** (`"94.27" "70.87"`) on Bing, Brave and the local SearXNG. The
source is reachable **only** by the scholarly route.

### 6b. `4ffdb149` — item B2 (GLiClass tables) → **CONFIRMED** (result in §5)

Read all seven tables of arXiv:2508.07662v1 in full: quantitative baselines are the four cross-encoders only;
no generative LLM has a numeric entry anywhere; the sole GPT-4o appearance is as a training-data annotator
(§2.2). Also noted: Tables 3 and 4 use slightly different dataset rows (`spam` vs `enron_spam`, `banking` vs
`banking77`), so their grand averages are not strictly paired — a footnote-level caveat, not a problem for
this paper.

---

## 7. What this unit did **not** do

- Did not edit `REFERENCES.bib` (a later unit merges; additions are in `REFERENCES_ADDITIONS.bib`).
- Did not find a survey that would let the paper claim "no such work exists" — item Q5.1 / B3 stays
  `NOT FOUND`, and the paper's *"we were able to locate"* hedge stays.
- Did not verify the four already-sourced identifiers' titles/authors (`2602.06370`, `2512.12677`,
  `2309.03882`, `2305.13971`) — `OPEN_QUESTIONS.md` Q5 assigns that to a human as bibliography hygiene, and
  it is outside this unit's one purpose.
- Did not resolve the `fastino/GLiNER2.5-Decide` "~340M card vs 486M safetensors" discrepancy, or the
  `cc-by-nc-4.0` vs Apache-2.0 weighting question — both are licence/size questions, not sourcing gaps.
- Did not read the full text of arXiv:2501.08457, arXiv:2410.01627, ACL `2025.acl-industry.68`, or
  arXiv:2311.08526 beyond the fetched abstract/HTML fragments; the characterisations above stop at what was
  seen. (For A3, the delegate read the full PDF — §2a says so explicitly.)
