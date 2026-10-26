# REFS.md — UPAPER1a · external works the corpus cites for the A3 result

**Rules applied here:** every entry names **where in the corpus** it was found (file:line, inside
`the read-only target repository`, read-only). **No BibTeX was invented and no field was filled in from memory.** An
entry whose venue/identifier I could not locate in the corpus is marked **`UNSOURCED`**, per the unit card.
Identifiers are transcribed **verbatim** from the corpus, including arXiv IDs; where an ID is surprising I
say so rather than "correcting" it.

---

## A. The load-bearing sources the thesis stands on

### A1. The N-dependent encoder-vs-LLM crossover table — **the "published small encoder wins" result**

- **Where cited:** `docs/DECIDER_STACK_DECISION.md §11.2` (line ~448–462) — *"The cleanest source
  ([2602.06370](https://arxiv.org/abs/2602.06370)) measures it directly"*.
- **Identifier:** arXiv **2602.06370** (verbatim from the corpus; the corpus gives **no title, no authors,
  no venue**).
- **What the corpus takes from it:** N=2 frontier LLM wins/ties; N=4 encoder wins (AG News 94.11–94.63 vs
  91.35; p50 108–197 ms vs 332–1435 ms; $5.73–10.44 vs $276–1272 per 1M); N=14 encoder wins more (DBPedia
  99.27–99.40 vs 98.83).
- **Why it is load-bearing for A3:** this table is the actual artefact the paper's thesis attacks — it is
  **encoder vs API LLM**, i.e. a **prompted** baseline. `DECIDER_STACK_DECISION.md:471–473` states
  *"the N-dependent crossover table in §11.2 is encoder-versus-**API LLM**, i.e. prompted."*
- **Status: SOURCED (identifier only).** ⚠ The writer must verify title/authors/venue independently before
  putting it in a bibliography — **that information is not in the corpus.** (The corpus also carries
  `docs/research/GATED_READ_PROVENANCE.md` as the project's citation-audit file; this ID does **not** appear
  there.)

### A2. The corroborating throughput source

- **Where cited:** `docs/DECIDER_STACK_DECISION.md §11.2` (line ~461) — *"([2512.12677](https://arxiv.org/abs/2512.12677))"*.
- **Identifier:** arXiv **2512.12677** (verbatim; no title/authors/venue in the corpus).
- **What the corpus takes from it:** ModernBERT-base classifies patents at 93.45 samples/s vs Llama-3.2-3B's
  1.88 and Qwen3-4B's 1.26; distilling a fine-tuned 3B into ModernBERT-base retains ≥97 % of teacher F1 at
  ~45× throughput.
- **Status: SOURCED (identifier only).** Same caveat as A1.

### A3. The 125M-RoBERTa-beats-fine-tuned-LLaMA2-7B corroboration

- **Where cited:** `docs/DECIDER_STACK_DECISION.md §11.2` (line ~458–460) — *"a 125M RoBERTa beats a
  fine-tuned LLaMA2-7B on **77-class** intent (**94.27 vs 70.87**, +23.4 F1) and is **29–108× faster**"*.
- **Identifier: none given.** No arXiv ID, no author, no venue anywhere in the cited passage.
- **Status: `UNSOURCED`.** The number is quoted in the corpus but its source is not identified. **Do not
  cite it** without an independent source.

### A4. The honest counter-case — equal fine-tuning effort favours the LLM

- **Where cited:** `docs/DECIDER_STACK_DECISION.md §11.2` (line ~464–468) — *"with equal fine-tuning effort
  and vLLM, Llama-3.2-3B-LoRA beat ModernBERT-large on **both** F1 (93.1 vs 89.2) **and** throughput (152 vs
  87 ex/s) on ADE classification."*
- **Identifier: none given.** No ID, author, or venue in the passage (the corpus calls it *"the first lane's
  own honest counter-case"*).
- **Status: `UNSOURCED`.**
- **Why the writer must care:** this is the corpus's own admission that *"an encoder always wins" is false*,
  and it is the strongest single threat to a one-sided reading of A3 — it is a **fine-tuned vs fine-tuned**
  comparison that goes the *other* way. A3's defence is that it is a different task (ADE, N not stated) and a
  different data point, but the paper should not pretend it does not exist.

---

## B. The named models the "no published comparison exists" claim rests on

### B1. GLiNER (and `fastino/GLiNER2.5-Decide`)

- **Where cited:** `docs/DECIDER_STACK_DECISION.md:470–471` (*"GLiNER's win is **span extraction
  (exact-match F1), not a typed single-label decision**"*); licence/id notes at `:256` and `:269`
  (`fastino/GLiNER2.5-Decide`, Apache-2.0, ~340M card vs 486M safetensors — *"unresolved"*; *"GLiNER v0/v1
  weights are `cc-by-nc-4.0`, not MIT"*).
- **Identifier:** a HuggingFace model id only. **No paper, arXiv ID, author, or venue located.**
- **Status: `UNSOURCED` as a bibliographic reference** (the *model card* is identified; the *publication* is
  not). The A3 thesis depends on this work's *task type* (span extraction, not typed single-label decision),
  so it needs a real citation.

### B2. GLiClass

- **Where cited:** `docs/DECIDER_STACK_DECISION.md:471–472` — *"GLiClass has **no measured LLM head-to-head**
  at all (its own comparison table is qualitative)"*.
- **Identifier: none given.** No model id, arXiv ID, author, or venue in the corpus.
- **Status: `UNSOURCED`.** Note this is an argument from **absence** ("its own comparison table is
  qualitative"), which the writer should phrase as such.

### B3. The "no published measurement was found" claim itself

- **Where stated:** `docs/DECIDER_STACK_DECISION.md:473–475` — *"**No published measurement was found of a
  small encoder beating a fine-tuned generative model on a typed single-label decision** — verified-absent,
  and the second lane checked it explicitly."*; echoed at `ad301ae` (*"Nobody has published the comparison we
  need, so our 190-case fixture remains the load-bearing evidence"*).
- **Status: SOURCED as an internal claim, but it is a claim about a literature search, not a citation.** The
  search protocol, databases, and query terms are **not recorded in the corpus**. A reviewer cannot audit
  "verified-absent". §A3 and `LEARNINGS.md:262` render this as *"The literature says a small fine-tuned
  encoder beats an LLM at N ≥ 4"* with **no citation at all inside the EXP#12 document or its evidence tree**.
  **This is the single largest sourcing gap in the paper** and is recorded in `GAPS.md` §"discovered".

---

## C. Works cited for the *method* traps (usable if the paper keeps a method/limitations section)

### C1. PriDe — option-ID token bias

- **Where cited:** `docs/DECIDER_STACK_DECISION.md:415` and `:500` — *"**Option-ID token bias** (PriDe,
  [2309.03882](https://arxiv.org/abs/2309.03882), ICLR 2024)"*; and *"**PriDe** estimates the option-ID prior
  by permuting…"*.
- **Identifier:** arXiv **2309.03882**, **ICLR 2024** (verbatim from the corpus; no title/authors).
- **Status: SOURCED (identifier + venue).**
- **Relevance to A3:** grounds the position/order-bias concern that the order-permutation probe measures
  (pass-1 flips: 138/142/101/135/81 → final: 0 for candidates, 58 for majority-class).

### C2. GCD — grammar-constrained decoding

- **Where cited:** `docs/DECIDER_STACK_DECISION.md:494–495` — *"[2305.13971](https://arxiv.org/abs/2305.13971),
  EMNLP 2023"* and *"[ACL 2025 Industry](https://aclanthology.org/2025.acl-industry.34)"*.
- **Identifiers:** arXiv **2305.13971**, **EMNLP 2023**; **ACL 2025 Industry track** (aclanthology
  `2025.acl-industry.34`).
- **Status: SOURCED (identifiers + venues).** No titles/authors in the corpus.
- **Relevance to A3:** the "CD's reach ends where schema conformance ends" citation for method learning M8 —
  only needed if the paper discusses decoding constraints. A3 itself does not use GCD.

---

## D. What is NOT in the corpus (explicitly)

- **No bibliography, `.bib`, or reference-manager file** was found covering the encoder-crossover result.
  `docs/research/EXP#12-evidence/` (26 files) contains **zero** external citations; neither does
  `experiments/EXP#12-typed-channel-comparison.md`. All sourcing for the thesis lives in
  `docs/DECIDER_STACK_DECISION.md §11.2/§11.6` and the commit messages `ad301ae` / `995fbd1` / `a5ef1b2`.
- **No "second fixture" or external typed-decision benchmark is named anywhere** — the A3 ask for one is
  open, and the corpus offers no candidate to cite in its place.
- One reference I checked and found **only as an internal audit record, not for this result**:
  `docs/research/GATED_READ_PROVENANCE.md` carries full-ish citations (Toolformer 2302.04761/NeurIPS 2023;
  Mallen et al. 2212.10511/ACL 2023; Adaptive-RAG 2403.14403/NAACL 2024; RouteLLM 2406.18665/ICLR 2025;
  Yue & Yao 2503.15551/Findings of ACL 2025). **These support the gated-read/staged-decider result, not the
  encoder-crossover result**, and I did not verify them further. Listed here only so a later unit does not
  mistake them for A3's sources.

## Summary

| | count |
|---|---|
| references sourced (identifier/venue located in corpus) | **4** (A1 2602.06370, A2 2512.12677, C1 PriDe 2309.03882 ICLR 2024, C2 GCD 2305.13971 EMNLP 2023 + ACL 2025 Industry) |
| references unsourced | **4** (A3 125M-RoBERTa claim, A4 equal-effort counter-case, B1 GLiNER, B2 GLiClass) |
| load-bearing claim with **no** citation inside the EXP#12 corpus | **1** ("the literature says …" — see B3) |
