# BIBLIOGRAPHY_REPAIR.md — UBIB1

Unit **UBIB1**, 2026-10-15. Live check was against the very first repository-access evidence for this session.

## 0. Sources actually fetched (primary)

| # | Identifier | URL fetched | HTTP | Result |
|---|---|---|---|---|
| 1 | arXiv 2602.06370 | `https://arxiv.org/abs/2602.06370` | 200 (43,530 B) | resolved |
| 2 | arXiv 2512.12677 | `https://arxiv.org/abs/2512.12677` | 200 (42,575 B) | resolved, **partial** claim match |
| 3 | arXiv 2309.03882 | `https://arxiv.org/abs/2309.03882` | 200 (41,824 B) | resolved |
| 4 | arXiv 2305.13971 | `https://arxiv.org/abs/2305.13971` | 200 (43,169 B) | resolved |
| 5 | arXiv metadata page | `https://info.arxiv.org/help/prep.html` | 200 | abstract limit settled (§5) |

The arXiv **API** (`https://export.arxiv.org/api/query?id_list=...`) was tried first and returned
`HTTP 429` with the body `Rate exceeded.` on two attempts (25 s apart) — including the plain-HTTP form,
which additionally produced 0 bytes because it 301-redirects to HTTPS. The four **abs pages** above were
used instead; they are arXiv's own metadata for the same records, so no third-party substitute was needed.
Raw captures are in `scratch/ubib1/abs_*.html` and `scratch/ubib1/api_all.xml`.

## 1. Metadata as returned (quoted, never invented)

```
2602.06370  Title:   Cost-Aware Model Selection for Text Classification: Multi-Objective Trade-offs
                     Between Fine-Tuned Encoders and LLM Prompting in Production
            Authors: Alberto Andres Valdes Gonzalez          (single author)
            Dateline:[Submitted on 6 Feb 2026]  Comments: 26 pages, 12 figures. Empirical benchmark
                     comparing fine-tuned encoders and LLM prompting for text classification under
                     cost and latency constraints
            Abstract (verbatim, abridged): "...we present a systematic comparison of two contrasting
                     paradigms for text classification: zero- and few-shot prompt-based large language
                     models, and fully fine-tuned encoder-only architectures. We evaluate these approaches
                     across four canonical benchmarks (IMDB, SST-2, AG News, and DBPedia), measuring
                     predictive quality (macro F1), inference latency, and monetary cost..."

2512.12677  Title:   Fine-Tuning Causal LLMs for Text Classification: Embedding-Based vs.
                     Instruction-Based Approaches
            Authors: Amirhossein Yousefiramandi, Ciaran Cooney   (two authors)
            Dateline:[Submitted on 14 Dec 2025; last revised 25 May 2026 (v3)]  Comments: 20 pages, 5 figures
            Abstract (verbatim, abridged): "We explore efficient strategies to fine-tune decoder-only
                     Large Language Models (LLMs) for downstream text classification under resource
                     constraints... Experiments on two patent benchmarks, a 5-class single-label internal
                     corpus and the public WIPO-Alpha multi-label dataset with 14 categories, show that the
                     embedding-head approach matches or exceeds fine-tuned BERT baselines on single-label
                     classification while training 10-30x fewer parameters."

2309.03882  Title:   Large Language Models Are Not Robust Multiple Choice Selectors
            Authors: Chujie Zheng, Hao Zhou, Fandong Meng, Jie Zhou, Minlie Huang
            Dateline:[Submitted on 7 Sep 2023; last revised 22 Feb 2024 (v4)]
            Comments: ICLR 2024 Spotlight
            Abstract (verbatim, abridged): "...modern LLMs are vulnerable to option position changes in
                     MCQs due to their inherent 'selection bias', namely, they prefer to select specific
                     option IDs as answers (like 'Option A')... we propose a label-free, inference-time
                     debiasing method, called PriDe..."

2305.13971  Title:   Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning
            Authors: Saibo Geng, Martin Josifoski, Maxime Peyrard, Robert West
            Dateline:[Submitted on 23 May 2023; last revised 18 Jan 2024 (v6)]
            Comments: Accepted at EMNLP 2023 Main Conference
            Abstract (verbatim, abridged): "...grammar-constrained decoding (GCD) can be used to control
                     the generation of LMs, guaranteeing that the output follows a given structure... we
                     introduce input-dependent grammars..."
```

## 2. The five entries — before / after

### 2.1 `arxiv2602_06370` — RESOLVED
BEFORE (`REFERENCES.bib:25-33`, verbatim):
```bibtex
@misc{arxiv2602_06370,
  eprint       = {2602.06370},
  archivePrefix= {arXiv},
  howpublished = {Cited in \texttt{docs/DECIDER\_STACK\_DECISION.md} \S11.2 (the N-dependent
                  encoder-vs-LLM crossover table)},
  note         = {SOURCED (identifier only). The corpus records NO title, NO authors and NO venue.
                  Load-bearing: this is the crossover table the paper's thesis attacks, and the corpus
                  states its LLM side is an API LLM, i.e. PROMPTED. A human must complete this entry.}
}
```
AFTER (`REFERENCES.bib:25-40`): `author = {Valdes Gonzalez, Alberto Andres}`,
`title = {Cost-Aware Model Selection for Text Classification: Multi-Objective Trade-offs Between Fine-Tuned Encoders and {LLM} Prompting in Production}`, `year = {2026}`, `url = {https://arxiv.org/abs/2602.06370}`, plus a note recording the fetch, the date and the caveat in §3.1.
Inlined (`main.tex:431`) BEFORE: `\bibitem{arxiv2602_06370} arXiv:2602.06370, Cited in \texttt{docs/DECIDER\_STACK\_DECISION.md} \S11.2 (the N-dependent encoder-vs-LLM crossover table). \emph{[Author and/or title not recorded in the corpus --- to be completed before submission.]}`
AFTER: `\bibitem{arxiv2602_06370} Valdes Gonzalez, Alberto Andres, \emph{Cost-Aware Model Selection for Text Classification: Multi-Objective Trade-offs Between Fine-Tuned Encoders and {LLM} Prompting in Production}, 2026, arXiv:2602.06370, \url{https://arxiv.org/abs/2602.06370}.`

### 2.2 `arxiv2512_12677` — RESOLVED (fields) / CLAIM PARTIAL
BEFORE (`REFERENCES.bib:35-41`): identical shape to 2.1, note read `SOURCED (identifier only). No title, authors or venue recorded in the corpus. A human must complete this entry.`
AFTER: `author = {Yousefiramandi, Amirhossein and Cooney, Ciaran}`, `title = {Fine-Tuning Causal {LLM}s for Text Classification: Embedding-Based vs. Instruction-Based Approaches}`, `year = {2025}`, `url = {https://arxiv.org/abs/2512.12677}`.
Inlined BEFORE: `\bibitem{arxiv2512_12677} arXiv:2512.12677, Cited in \texttt{docs/DECIDER\_STACK\_DECISION.md} \S11.2 (throughput corroboration). \emph{[Author and/or title not recorded in the corpus --- to be completed before submission.]}`
AFTER: `\bibitem{arxiv2512_12677} Yousefiramandi, Amirhossein and Cooney, Ciaran, \emph{Fine-Tuning Causal {LLM}s for Text Classification: Embedding-Based vs. Instruction-Based Approaches}, 2025, arXiv:2512.12677, \url{https://arxiv.org/abs/2512.12677}.`

### 2.3 `pride2309_03882` — RESOLVED, citation verified
BEFORE (`REFERENCES.bib:43-50`): no author, no title; note read `SOURCED (identifier + venue, which the corpus records as ICLR 2024) ...`.
AFTER: `author = {Zheng, Chujie and Zhou, Hao and Meng, Fandong and Zhou, Jie and Huang, Minlie}`, `title = {Large Language Models Are Not Robust Multiple Choice Selectors}`, `year = {2023}`, `howpublished = {ICLR 2024 (Spotlight). ...}`, `url = {https://arxiv.org/abs/2309.03882}`.
Inlined BEFORE: `\bibitem{pride2309_03882} arXiv:2309.03882, Cited in \texttt{docs/DECIDER\_STACK\_DECISION.md}:415 and :500 as ``PriDe''. \emph{[Author ... not recorded ...]}`
AFTER: `\bibitem{pride2309_03882} Zheng, Chujie, Zhou, Hao, Meng, Fandong, Zhou, Jie and Huang, Minlie, \emph{Large Language Models Are Not Robust Multiple Choice Selectors}, ICLR 2024 (Spotlight), 2023, arXiv:2309.03882, \url{https://arxiv.org/abs/2309.03882}.`

### 2.4 `gcd2305_13971` — RESOLVED, citation verified
BEFORE (`REFERENCES.bib:52-61`): no author, no title; note read `SOURCED (identifiers + venues, recorded as EMNLP 2023 and ACL 2025 Industry track) ... A human must complete this entry (or drop it as non-load-bearing).`
AFTER: `author = {Geng, Saibo and Josifoski, Martin and Peyrard, Maxime and West, Robert}`, `title = {Grammar-Constrained Decoding for Structured {NLP} Tasks without Finetuning}`, `year = {2023}`, `howpublished = {EMNLP 2023 (Main Conference). ...}`.
Inlined BEFORE: `\bibitem{gcd2305_13971} arXiv:2305.13971, Cited in \texttt{docs/DECIDER\_STACK\_DECISION.md}:494--495, alongside \url{https://aclanthology.org/2025.acl-industry.34}. \emph{[Author ... not recorded ...]}`
AFTER: `\bibitem{gcd2305_13971} Geng, Saibo, Josifoski, Martin, Peyrard, Maxime and West, Robert, \emph{Grammar-Constrained Decoding for Structured {NLP} Tasks without Finetuning}, EMNLP 2023 (Main Conference), 2023, arXiv:2305.13971, \url{https://arxiv.org/abs/2305.13971}.`

### 2.5 `source_decider_stack_2026` — NO AUTHOR EXISTS; not fabricated
BEFORE (`REFERENCES.bib:63-78`): already had `title = {{DECIDER\_STACK\_DECISION.md} \S11.6}` and a `howpublished`; it was flagged "identifier-only" only because it has **no author and no venue** — it is an **unpublished internal document of the read-only target repository**, not a published work, so no author exists in any primary record. `author` is therefore left **absent by design** and the fabricated-placeholder note is replaced with that ruling.
Inlined BEFORE: `\bibitem{source_decider_stack_2026} \emph{{DECIDER\_STACK\_DECISION.md} \S11.6}, \texttt{the read-only target repository/docs/DECIDER\_STACK\_DECISION.md}, \S11.6 (ERRATA on \S11.5); committed as \texttt{ad301ae1a5472fa7bd27807fdc7bb15d35f81988}. \emph{[Author and/or title not recorded in the corpus --- to be completed before submission.]}`
AFTER: `\bibitem{source_decider_stack_2026} \emph{{DECIDER\_STACK\_DECISION.md} \S11.6}, unpublished internal corpus document (no attributable author), \texttt{the read-only target repository/docs/DECIDER\_STACK\_DECISION.md}, \S11.6 (ERRATA on \S11.5); committed as \texttt{ad301ae1a5472fa7bd27807fdc7bb15d35f81988}.`

## 3. Cross-check against the manuscript's own attribution

Citation context read at `papers/encoder-crossover-190/MANUSCRIPT.md:146-159` (§2.2).

| Key | Manuscript says | Source actually is | Verdict |
|---|---|---|---|
| `arxiv2602_06370` | "The N-dependent crossover table ... its encoder-side wins, its latency spreads, and its cost figures ... its comparison class is a prompted API LLM." | zero-/few-shot prompt-based LLM vs fully fine-tuned encoder-only; macro F1 + latency + monetary cost; Pareto/utility | **MATCH** on subject. **CAVEAT:** the abstract never says the crossover depends on label-set size *N*; "N-dependent" is the corpus's characterisation. Benchmarks are IMDB/SST-2 (2-class), AG News (4), DBPedia (14). |
| `arxiv2512_12677` | "ModernBERT-base classifies patents at 93.45 samples/s vs Llama-3.2-3B at 1.88 and Qwen3-4B at 1.26; distilling a fine-tuned 3B into ModernBERT-base ... retaining >= 97 % of teacher F1 at ~45x throughput." | decoder-only LLM fine-tuning for patent classification; embedding-head vs instruction-tuning; 4-bit + LoRA; "matches or exceeds fine-tuned BERT baselines ... training 10-30x fewer parameters" | **PARTIAL MATCH — FLAGGED.** Domain (patent classification) and the decoder-LLM-vs-BERT comparison match, but the abstract contains **no** "ModernBERT-base", **no** 93.45 / 1.88 / 1.26 samples/s and **no** distillation/45x result. Those four figures are **UNVERIFIED from the abstract** and need the PDF body. `MANUSCRIPT.md:150-153` also asserts them as fact. **Do not treat as verified.** |
| `pride2309_03882` | "PriDe (option-ID token bias) ... grounds the position/order-bias concern that our own order-permutation probe measures." | option-ID token bias; introduces the debiasing method literally named **PriDe**; ICLR 2024 Spotlight (arXiv comment field) | **MATCH** (venue and method name both confirmed). |
| `gcd2305_13971` | "Grammar-constrained decoding (GCD) ... A3 does not use GCD; these are listed because the same errata section uses them, and they are not sources for the crossover claim." | GCD for structured NLP tasks without finetuning; EMNLP 2023 Main Conference (arXiv comment field) | **MATCH** (and correctly disclaimed as non-load-bearing). |

## 4. Additional defects the report did not count

1. **A dropped entry.** `benayas2024comparative` (`REFERENCES_ADDITIONS.bib:109-145`) is complete — author, title, *Language Resources and Evaluation* 59(3):2007-2030, DOI `10.1007/s10579-024-09796-y` — but it is **absent from `REFERENCES.bib`** and **absent from `main.tex`'s `thebibliography`**, even though `REFERENCES.bib:80-82` claims UREFS's sourced additions were merged by UPAPER1c. **Not fixed here** (outside the "printed reference list is defective" scope; it is an *omission*, and adding a reference changes the printed list length).
2. **A stale sentence implied by (1).** `main.tex:428` still states: "The one corpus work that still has **no** locatable identifier --- the 125M-RoBERTa 94.27 vs 70.87 claim --- is **not** in the bibliography", while `REFERENCES_ADDITIONS.bib:121-123` records that exact claim as **FOUND** with the Benayas DOI. **Left untouched** — it is a claims/number matter owned by another unit, and §2.2 numbers are out of UBIB1's remit.
3. **No other entry has an empty/placeholder author or title.** Machine-shaped keys are exactly the five already named — four `arxivNNNN_NNNNN` and one `source_*`. All seven other `REFERENCES.bib` entries and all eight `REFERENCES_ADDITIONS.bib` entries carry both `author` and `title`.
4. **`main.tex` is ASCII-clean before and after** (0 non-ASCII bytes). `REFERENCES.bib` does contain pre-existing non-ASCII (`§`, `—`, `⚠`) in notes outside the five repaired blocks; the five repaired blocks and every line written by UBIB1 are pure ASCII.

## 5. arXiv abstract-length ruling — CONFIRMED, 1,920 characters

Source: **`https://info.arxiv.org/help/prep.html`**, §"Abstract: *required*" (anchor `#abstract-required`). Quoted sentence, verbatim:

> "Keep it short — abstracts longer than 1920 characters will not be accepted; abridge your abstract if necessary."

The same page states of the metadata fields generally: *"Our metadata fields only accept ASCII input."*

**Consequence for this manuscript.** The manuscript's abstract is **3,415 characters** (UBIB1 measured 3,420 by naive extraction from `MANUSCRIPT.md`, which includes Markdown emphasis markers; the 3,415 figure is the `.tex` abstract). 3,415 > 1,920, so:

* the **PDF abstract** is unaffected — the limit governs the **metadata/web-submission-form abstract field**, not the typeset PDF;
* the **web-form metadata abstract is over the limit and would be rejected by the submission form**; a **shortened metadata abstract (<= 1,920 chars)** must be prepared for the arXiv submission, while the PDF keeps the full abstract. This is a real blocker for the arXiv submission step, not for the PDF.

**Ruling: the suspected ~1,920 limit is real and current, verified on arXiv's own page.**
