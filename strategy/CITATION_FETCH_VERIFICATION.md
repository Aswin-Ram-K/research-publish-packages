# CITATION_FETCH_VERIFICATION — UCHECK1 full-text re-check of UCITE1's two MIS-CITED findings

**Unit:** UCHECK1. **Purpose:** settle UCITE1's two most serious findings from the **full texts**, not the
abstracts, because UCITE1 explicitly recorded that its own MIS-CITED-1 was **"Not settled: whether
`arXiv 2512.12677`'s *body* (not abstract) prints the 93.45 / 1.88 / 1.26"** (`strategy/CITATION_SUPPORT_AUDIT.md:508`).

**Bottom line: UCITE1's abstract-only method produced a false positive on the paper's most serious
compliance finding.** The numbers it called MIS-CITED-1 are printed in the source's **body and tables**.
This is a method lesson as much as a citation verdict: the audit correctly flagged that an abstract is not
a full text, then concluded from the abstract anyway.

---

## 1. Fetch log (every fetch: URL, HTTP status, bytes, how searched)

| # | URL | HTTP | bytes | role |
|---|-----|------|-------|------|
| 1 | `https://arxiv.org/abs/2512.12677` | 200 | 42,575 | abstract page (reachability only) |
| 2 | `https://arxiv.org/abs/2602.06370` | 200 | 43,530 | abstract page (reachability only) |
| 3 | `https://arxiv.org/html/2512.12677v3` | 200 | **357,024** | **full text searched — CLAIM 1** |
| 4 | `https://arxiv.org/html/2602.06370v1` | 200 | **423,961** | **full text searched — CLAIM 2** |
| 5 | `https://ar5iv.labs.arxiv.org/html/2512.12677` | 200 | 206,627 | alternate renderer (not needed; HTML renderer worked) |
| 6 | `https://ar5iv.labs.arxiv.org/html/2602.06370` | 200 | 377,661 | alternate renderer (not needed) |
| 7 | `https://simmering.dev/blog/modernbert-vs-llm/` | 200 | 64,330 | control spot-checks |

**How fetched:** `curl -sSL --max-time 40 -o <file> -w '%{http_code} %{size_download}'`.
**How searched:** Python tag-strip (`re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>',' ')` then
`re.sub(r'(?s)<[^>]+>',' ')`, `html.unescape`), then case-insensitive `re.finditer` on each literal term,
printing ±130 chars of context. **No site blocked us; the arXiv native HTML renderer (`arxiv.org/html/...`)
worked for both, so ar5iv was not required.** Extracted plain text: 82,090 chars (2512.12677v3),
116,842 chars (2602.06370v1).

Both works exist and are reachable; **neither claim is UNRESOLVED.**

---

## 2. CLAIM 1 — `papers/encoder-crossover-190/MANUSCRIPT.md:150-152` vs `arXiv:2512.12677`

Source title (full text, v3): *"Fine-Tuning Causal LLMs for Text Classification: Embedding-Based vs.
Instruction-Based Approaches"*. Manuscript sentence at L150-152:

> "arXiv `2512.12677`, same section: ModernBERT-base classifies patents at 93.45 samples/s vs
> Llama-3.2-3B at 1.88 and Qwen3-4B at 1.26; distilling a fine-tuned 3B into ModernBERT-base is recorded
> as retaining ≥ 97 % of teacher F1 at ~45× throughput."

### Per-term result (in the FULL TEXT of 2512.12677v3)

| term | result | surrounding sentence (verbatim from full text) |
|------|--------|-----------------------------------------------|
| `ModernBERT` | **FOUND ×12** | "at parity F1, a Llama-3.2-3B teacher runs at ∼2 samples/s versus **ModernBERT-base**'s ∼90 samples/s — a ∼45× gap (Table 13)." Also §4.6: "against four BERT-class baselines (PatentBERT and three **ModernBERT-base** variants) in the main results table." |
| `93.45` | **FOUND ×2** | Table 3 / Table 13 row: "**ModernBERT-base 24.55 93.45 21.51 84.48**", caption "Table 13: Training and inference throughput (samples per second) for CLV and WIPO datasets." (columns = Trn/Inf × CLV/WIPO; 93.45 is ModernBERT-base **Inference on CLV**, the 5-class patent corpus) |
| `1.88` | **FOUND ×3** | "**Llama-3.2-3B** 3.04 **1.88** 2.05 1.37" (same throughput table, Llama-3.2-3B inference on CLV) |
| `1.26` | **FOUND ×2** | "**Qwen3-4B**-Instruct-2507 0.77 **1.26** 0.64 0.83" (same table, inference on CLV) |
| `Llama-3.2-3B` | **FOUND ×28** | "best A1: **Llama-3.2-3B** r=8 at 0.86, vs. PatentBERT 0.854 at 346M trainable"; "**Llama-3.2-3B** 3.2B 12.2M 0.860 0.785" |
| `Qwen3-4B` | **FOUND ×2** | "**Qwen3-4B**-Ins 4.2B 132M .81 .82"; "**Qwen3-4B**-Instruct-2507 0.77 1.26 0.64 0.83" |
| `distill` | **FOUND ×16** | §4.9 "Recovering BERT-class Throughput via **Distillation**"; "plus a knowledge-**distillation** recipe (Section 4.9) that recovers BERT-class throughput at a ≤ 1.5-point F1 cost" |
| `97` | **FOUND** | "The student retains ≥ **97%** of teacher F1 while running at BERT-class throughput (∼90 samples/s vs. ∼2 for the teacher; Table 13)." |
| `45` | **FOUND** | "a ∼**45×** gap (Table 13)" |

### Verdict — CLAIM 1

**ALL NINE TERMS ARE PRINTED IN THE FULL TEXT.** The two throughput constants, the two model names, the
distillation result, the **≥ 97 %** teacher-F1 retention and the **~45×** gap are all in the source —
in the body prose (§4.6, §4.9), in **Table 3** and in **Table 13**, and in the abstract-adjacent
contribution statement. The manuscript's L150-152 attribution is **substantively accurate**.

- UCITE1's **MIS-CITED-1 is REFUTED at the full-text level.** It is a *false positive produced by
  abstract-only checking*: the abstract genuinely does not name ModernBERT and does not carry the
  numbers, but the body and both throughput tables do.
- Two minor precision notes, neither a fabrication: the source writes **`Qwen3-4B-Instruct-2507`**
  where the manuscript writes `Qwen3-4B`; and the manuscript's `93.45 samples/s` is the source's
  **inference** throughput on the **CLV (5-class patent)** corpus (the paper's WIPO-Alpha inference figure
  for the same model is 84.48) — so "classifies patents at 93.45 samples/s" is correct for the CLV corpus
  specifically, and should say so.
- `REFERENCES.bib:62-68`'s "UNVERIFIED from the abstract" note is now **resolved: verified from the body.**

---

## 3. CLAIM 2 — the "N-dependent crossover table" attributed to `arXiv:2602.06370`

Source title (full text, v1): *"Cost-Aware Model Selection for Text Classification: Multi-Objective
Trade-offs Between Fine-Tuned Encoders and LLM Prompting in Production"*. The paper calls this work
"**The N-dependent crossover table**" (`MANUSCRIPT.md:146`). UCITE1 asserted, from the abstract, that it has
"**no N / label-set-size analysis and no crossover, and none of** `94.11–94.63`, `91.35`, `99.27–99.40`, `98.83`".

### Per-term result (in the FULL TEXT of 2602.06370v1)

| term | result | evidence (verbatim) |
|------|--------|---------------------|
| `N-dependent` | **NOT FOUND (0)** | the literal string never appears |
| `crossover` | **NOT FOUND (0)** | the literal string never appears |
| `number of classes` | **NOT FOUND (0)** | but the same concept is carried by a **`#Classes` column** |
| label-cardinality span | **FOUND** | "These datasets span varying **label cardinalities**, dataset sizes, and domain characteristics, providing a representative testbed for structured text classification." |
| Table 1 `#Classes` | **FOUND** | "IMDB Sentiment **2** … SST-2 Sentiment **2** … AG News Topic **4** … DBPedia Ontology **14**"; prompt appendix: "C.3 AG News (**4-way** Topic Classification)", "C.4 DBPedia (**14-way** Ontology Classification)" |
| `94.11` / `94.63` | **FOUND** | AG News table: "F1 Score (%) 94.43 ± 0.10 **94.11 ± 0.07 94.63 ± 0.14** 87.93 … 91.35 ± 0.11 90.56" |
| `91.35` | **FOUND ×6** | "All three encoders cluster around ≈94–95 macro-F1 (best: RoBERTa **94.63** ± 0.14), whereas LLM prompting lags substantially even with few-shot (best LLM: Claude 4.5 ZS **91.35** ± 0.11)" |
| `99.27` / `99.40` | **FOUND** | "RoBERTa **99.27** ± 0.02"; "Table 5 is near-saturated by fine-tuned encoders, with BERT and DistilBERT achieving **99.40** macro-F1 (std ≤ 0.04)" |
| `98.83` | **FOUND ×8** | "LLM prompting remains competitive but consistently below the encoder ceiling (best LLM: Claude 4.5 ZS **98.83** ± 0.04)" |

**Does the outcome vary with N?** Yes, by dataset label cardinality, per-dataset (Tables 2–5):
- **N = 2 (IMDB):** "on a high-signal binary task like IMDB, LLM prompting achieves only **marginal predictive gains** over specialized encoders" (best encoder RoBERTa 94.84).
- **N = 4 (AG News):** "the **clearest specialization advantage** for encoder fine-tuning" — encoders 94.11–94.63 vs best LLM 91.35 (≈3.3-point encoder win).
- **N = 14 (DBPedia):** encoders 99.40/99.33 vs best LLM 98.83 (≈0.6-point encoder win — narrower than N = 4).

The source's own global framing is **not** a crossover: "fine-tuned encoder-based models from the BERT
family achieve **competitive, and often superior**, classification performance"; "encoder specialization
yields **superior accuracy** while simultaneously improving latency and cost, making prompting a
**dominated strategy**".

### Verdict — CLAIM 2 (MIXED)

- **UCITE1's "none of those figures are printed" is REFUTED.** All six cited figures
  (`94.11`, `94.63`, `91.35`, `99.27`, `99.40`, `98.83`) **are** printed in the full text at the exact
  datasets the manuscript names — again an abstract-only artifact.
- **The "N-dependent crossover table" *label* is the corpus's coinage, not the source's.** The source
  contains no string `N-dependent`, no `crossover`, and no single table that orders results by N and shows
  a crossing point. It reports per-dataset results across label cardinalities (2, 4, 14) and states the
  encoder advantage is *narrowest at N = 2* ("only marginal predictive gains" for the LLM) and *widest at
  N = 4* — a non-monotonic, not a monotone-crossover, pattern.
- **The manuscript's directional reading is substantially supported** (encoder wins at N = 4; roughly ties
  at N = 2), but a strict "crossover" (encoder *losing* at large N) is **not** what the source shows — it
  shows the encoder still winning at N = 14, just by less than at N = 4. The caveat
  `REFERENCES.bib:49-50` already carries ("the corpus's own characterisation; **NOT verbatim in the
  source's title or abstract**") should be extended to say it is not verbatim in the **body** either, and
  the label "N-dependent crossover table" should be re-attributed to the corpus.

---

## 4. Control spot-checks — figures UCITE1 verified verbatim (Simmering blog, `simmering2025modernbert`)

Fetched `https://simmering.dev/blog/modernbert-vs-llm/` (HTTP 200, 64,330 bytes). The **positive control**:
the same method that returned "not found" above must be able to return "found" on known-good figures.

| # | control figure (manuscript) | result | verbatim source line |
|---|------------------------------|--------|----------------------|
| 1 | ModernBERT-large `89.2` F1 / `87` examples-s | **CONFIRMED** | "`1b-modernbert-large   89.2   91.8   86.8   87`   transformers pipeline, batch size 128" |
| 2 | Llama-3.2-3B LoRA `93.1` F1 / `152` examples-s | **CONFIRMED** | "`3-Llama-3.2-3B-Instruct-LoRA   93.1   92.0   94.2   152`   vLLM, default settings" |
| 3 | `42 ex/s` after the 30 s vLLM CUDA-graph prep | **CONFIRMED** | "If that preparation time of 30 seconds is added, it's examples per second go down to **42**." |

Two further controls, found incidentally and also confirmed:
`80.7` — "`2-DSPy-25-threads-Llama-3.2-3B-Instruct   80.7   87.9   74.6   4`";
`395M` — "`ModernBERT-large … 395M   ~1.6GB`";
`A10G` — "All training and inference is done on a single **A10G** GPU hosted on Modal. It costs $1.10/h."

**Control result: 6/6 found, 3/3 required spot-checks confirmed.** The method discriminates: it returns
"found" on correct attributions and would return "not found" on absent ones. Therefore the "found"
verdicts in §2–§3 are meaningful, and so is the one genuine negative: the strings `N-dependent` and
`crossover` are absent from 2602.06370's full text.

---

## 5. What UCITE1 should change

1. **MIS-CITED-1 (L150-152): withdraw.** Upgrade to **SUPPORTED-FULL-TEXT**. Keep the numbers; optionally
   add "on the 5-class CLV patent corpus" and use `Qwen3-4B-Instruct-2507`. The genuine residual issue is
   only that `REFERENCES.bib` recorded them as UNVERIFIED — now resolved.
2. **MIS-CITED-2 (L64-65, L146, L149, L512): downgrade to a labelling/nuance defect, not a mis-citation.**
   The figures are printed in the source; the defect is that "N-dependent crossover table" is the corpus's
   label and the source never frames it that way, and the encoder still wins at N = 14.
3. **Method note for the audit itself:** an abstract-only fetch cannot support any "the work does not
   print X" verdict. Both MIS-CITED findings were abstract artifacts. The audit's own L508 reservation
   was correct and should have blocked the finding rather than annotating it.

**Nothing under `papers/` was edited.** This is a report.
