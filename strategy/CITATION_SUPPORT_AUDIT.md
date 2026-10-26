# CITATION_SUPPORT_AUDIT.md — UCITE1

**Unit:** UCITE1 (delegated subagent, parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`).
**Object of audit:** `papers/encoder-crossover-190/MANUSCRIPT.md` (877 lines; 7 numbered sections +
Abstract + Data and code availability + References; 32 headings).
**Supporting objects:** `papers/encoder-crossover-190/REFERENCES.bib` (13 entries),
`papers/encoder-crossover-190/submission/main.tex` (13 `\bibitem`s, 445 lines).
**Evidence-only companions read (never edited):** `REFS_VERIFIED.md`, `UNSOURCED_RETAINED.md`.
**Report-only.** The manuscript was not modified.

---

## 0. Coverage statement (read this before trusting the counts)

- Sentence-like units in `papers/encoder-crossover-190/MANUSCRIPT.md` **seen: 322** (tables excluded;
  masked code spans; split on `[.!?]` + whitespace; script in `scratch/ucite1/`).
- **Assertive sentences classified: 214** of those 322. The other 108 are section headings, table cells,
  skill-free procedural instructions, or bare file-path/command listings that carry no attribution.
- Every one of the 7 numbered sections, the Abstract, §7 and Data and code availability was read in full
  and classified sentence by sentence. No section was sampled.
- Of the 214 classified: **class A (own experiment) 137**, **class B (external attribution / number /
  SOTA) 41**, **class C (attributed to a specific cited work) 22**, **class D (own unpublished corpus)
  14**. Many sentences carry two classes; each is listed once at its dominant class and re-listed in the
  finding lists.
- Primary checks actually performed (not asserted from the corpus record): **4 fetches** —
  `https://arxiv.org/abs/2512.12677` (v3, 25 May 2026), `https://arxiv.org/abs/2602.06370` (v1,
  6 Feb 2026), `https://simmering.dev/blog/modernbert-vs-llm/`, and
  `https://aclanthology.org/2025.acl-industry.34/`. Everything else is marked `VERIFIED-BY-RECORD`
  (supported by `REFS_VERIFIED.md` / `REFERENCES.bib` notes, which record a fetch someone else made) or
  `UNVERIFIED`.

### 0.1 The structural finding that conditions every row below

`papers/encoder-crossover-190/submission/main.tex` contains **0 `\cite` commands** (grep `-cE '\\cite'`
→ `0`) and **13 `\bibitem`s**. Citations in this paper are **prose**, not LaTeX keys: works are named by
arXiv id, author name, DOI, or a backticked bib key inside narrative sentences. Consequences, all of
which a referee will notice:

1. **Nothing is mechanically linked.** No in-text citation resolves to an entry; resolution is manual and
   the printed `thebibliography` is, in the LaTeX sense, entirely uncited. Eleven of the 13 entries are
   never named by their bib key in the manuscript body; `simmering2025modernbert` (3×),
   `benayas2024comparative` (2×), and `zaratiana2024gliner` / `zaratiana2025gliner2` /
   `stepanov2025gliclass` / `kostina2025llmtextclassification` / `li2025smalllanguagemodels` /
   `weller2025seqvsseq` (1× each) are the only keys that appear at all, and they appear in backticks, not
   as citations.
2. **`source_decider_stack_2026`** — the entry the manuscript calls *"the citation for this paper's core
   literature claim"* (L118-120) — is **never referred to by key** anywhere in the manuscript. It is
   cited only as a repository path plus commit (`docs/DECIDER_STACK_DECISION.md` §11.6, `ad301ae`), and
   the repository is **not** in the released subset (§7:763 says so explicitly).
3. Therefore, on the submission's own terms, the correct answer to "which bib entries are never cited"
   is either **0** (prose reading) or **13** (mechanized reading). The truth is that the paper needs
   `\cite` keys before any of this is auditable. **This is the single highest-leverage fix in this
   report** and it is upstream of everything else.

---

## Abstract (L18–L56)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L20-22 | "Every public 'a small encoder wins' result we were able to locate **inside the target corpus** compares that encoder against a **prompted** (zero- or few-shot) LLM, never against a **fine-tuned generative decider** (the claim and its audit trail are internal to the corpus, not an external survey — §2)." | D (absence) | yes — self-qualified as internal | **supported as hedged**: `REFS_VERIFIED.md` §1 found no external survey; `REFERENCES.bib:102-121` (`source_decider_stack_2026`) records the search protocol as *not recorded* | keep; the "inside the target corpus" qualifier is doing real work here and must not be dropped (see §1 L75) |
| L28-30 | "best fine-tuned encoder head scores **0.3474** and loses to the fine-tuned 4B decider at **0.6789** … paired McNemar **b = 27, c = 90, ψ = 0.616, Δ = −0.3316, exact p = 4.167e−09**" | A | n/a (own) | traceable: `CLAIMS.md` maps each to `results/eval-*.json` / `results/REPORT.md`; §7:752-758 lists them | none |
| L31-35 | "the mandatory **majority-class control** … returns **0.4526**" / "**shuffled-label arm** … returns **0.2316**, below the fixture's **0.2911** chance floor" | A | n/a | traceable (§3.4, §4.3) | none |
| L35-38 | "our n-gram leak criterion (≥ 2 distinct shared 8-grams within one row pair, both directions) flagged **0 of 152,000** training↔fixture pairs … it flagged three deliberately seeded copies at **13 / 44 / 57** shared 8-grams" | A | n/a | traceable to `lint-report.json` (§4.4) — **but §7:757 states the lint report is recorded by the *withheld* harness and "not part of the released set"**, so the abstract's leak evidence is not checkable from the released subset | add the caveat in §7 to the abstract, or ship the lint report |
| L38-43 | "Against the *published, pre-registered* baseline **0.6684** — which `REPORT.md:189` states **cannot be re-scored** …" | A/D | **"published"** with no publication named | internally traceable; externally the word is wrong (see **UNCITED-2**) | replace "published" with "the corpus's recorded D-067 baseline" |
| L45-48 | "Fixing three defects lowered the **SetFit-MPNet** arm monotonically (**0.3158 → 0.2947 → 0.2632**), but the same order-probe fix *raised* the **ModernBERT-base** arm (**0.342105 → 0.347368**)" | A | n/a | traceable to `DEFECT-EVIDENCE.json` (§4.2) | none |
| L50-56 | "We make **no latency claim** … do **not** report κ = 0.9014 … **nor their mutual κ = 0.9125** — as inter-annotator agreement" | A | n/a | traceable (§6.1, §6.2) | none — this is the paper's strongest hygiene move |
| L52-53 | "κ = 0.9014 (first blind reader) or κ = 0.8577 (second, independent blind reader) … their mutual κ = 0.9125" | B (statistic) | **no** | Cohen's κ is used as the reliability instrument throughout and is **never cited** (see **UNCITED-3**) | cite Cohen (1960) once, at first use |

**Abstract: 12 assertive of 15 units seen.**

---

## §1 Introduction (L60–L110)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L62-63 | "A common empirical shape in applied model-selection work is a crossover: at small label-set sizes *N* a large language model (LLM) wins or ties, and above some *N* a small fine-tuned encoder takes over." | B (SOTA generalisation) | **no** | stated as a standing fact about "applied model-selection work"; the only support anywhere is the corpus's own table | **UNCITED-1.** Either cite the corpus table at the point of use or mark it as a hypothesis tested here |
| L64-65 | "The canonical instance in the corpus we work from is an N-dependent table in which the encoder wins at N = 4 (AG News 94.11–94.63 vs 91.35; DBPedia at N = 14: 99.27–99.40 vs 98.83) and loses or ties at N = 2." | D → B | attributed to "the corpus"; the external source (`arXiv 2602.06370`) appears only at L146 | **NOT SUPPORTED by the primary source.** I fetched `https://arxiv.org/abs/2602.06370`: the abstract reports *"fine-tuned encoder-based models from the BERT family achieve competitive, and often superior, classification performance"* across IMDB, SST-2, AG News, DBPedia — **no N / label-set-size analysis and no crossover**, and none of `94.11–94.63`, `91.35`, `99.27–99.40`, `98.83` | **MIS-CITED-2.** Move the citation to L65 and carry `REFERENCES.bib:49-50`'s own caveat: the N-dependent framing "*is the corpus's own characterisation; it is NOT verbatim in the source's title or abstract*" — the manuscript never says this |
| L66-69 | "the LLM side is an **API LLM** — i.e. *prompted*. We read that explicitly in the corpus's own errata (`docs/DECIDER_STACK_DECISION.md` §11.6)" | C (internal) | yes (internal, §11.6 + commit `ad301ae`) | supported by `REFERENCES.bib:107-120`, which quotes §11.6 verbatim | add a real citation to `source_decider_stack_2026` and state it is unreleased |
| L71-73 | "If the crossover is a property of *prompting* rather than of *scale*, then it should not survive when the generative side is given the same resource the encoder gets" | A (hypothesis) | n/a | n/a | none |
| L75-77 | "**Thesis.** Every 'a small encoder wins' result we were able to locate compares the encoder against a **prompted** LLM, never against a **fine-tuned** generative decider" | D (absence) | no citation at this point | **HEDGE-SCOPE DEFECT.** The abstract (L20) scopes the same sentence to "inside the target corpus"; here the qualifier is gone, so the sentence reads as a claim about the world — and `REFS_VERIFIED.md` §1 / `UNSOURCED_RETAINED.md` U2 record that **no external search protocol exists** and that UREFS's external search *failed* to upgrade the hedge. See **ABSENCE-2** | restore the scope: "…every such result we were able to locate **in the corpus we work from**" |
| L79-83 | "a 2025 practitioner experiment on binary adverse-drug-reaction classification reports a fine-tuned Llama-3.2-3B LoRA at F1 **93.1** against ModernBERT-large at **89.2** at comparable training cost (Simmering, 2025 — a blog post, **not** peer-reviewed; §2.1)" | C | yes (author + year + §) | **SUPPORTED** — I fetched `https://simmering.dev/blog/modernbert-vs-llm/`: `3-Llama-3.2-3B-Instruct-LoRA 93.1`, `1b-modernbert-large 89.2`, and *"All setups can be trained for under one dollar and in less than 15 minutes"* | cite as `simmering2025modernbert` + URL; the "blog, not peer-reviewed" label is correct and should stay |
| L84-85 | "(i) the **sealed typed single-label decision fixture** — 190 cases, N = 2–8 named options per case, 74 distinct labels" | A | n/a | **CONTRADICTED BY THE PAPER'S OWN §3.1.** L257-258 records the option counts exhaustively as `K = 2 (33 cases), K = 3 (27), K = 4 (76), K = 5 (54)` — sums to 190, so **max K = 5, and there is no K = 6/7/8**. See **CLASS-A-1** | change "N = 2–8" to "N = 2–5" in all four occurrences (L84, L171, L242-243, L714) or produce the K = 6–8 cases |
| L85-86 | "(ii) the **option-order permutation control**, whose final pass flips **0** cases for every candidate head" | A | n/a | traceable (§3.4:372-376) | none |
| L93-96 | "best fine-tuned encoder head 0.3474 against a fine-tuned 4B decider at 0.6789 (auditable, paired) and 0.6684 (published, not re-scorable)" | A/D | **"published"** unnamed | internal trace | see **UNCITED-2** |
| L104-105 | "the claim that 'every correction moved the affected arm down' is true for **SetFit-MPNet only**. §4.5" | A | n/a | traceable to `DEFECT-EVIDENCE.json`; note the internal cross-reference says §4.5 while the correction is actually carried at **§4.2:429-444** — a **broken internal cross-reference** | fix the pointer to §4.2 |
| L106-108 | "latency (§6.1) and human agreement on the fixture labels — which **two** blind model passes do not supply" | A | n/a | traceable (§6.1, §6.2) | none |

**§1: 11 assertive of 22 units seen.**

---

## §2.1 The works that make the "encoder wins" claim (L116–L191)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L118-121 | "The corpus's own audit of this literature lives in `docs/DECIDER_STACK_DECISION.md` §11.6, committed as `ad301ae` … It is the citation for this paper's core literature claim, and it **does** support the claim" | C (internal) | location + commit, **not** by key | supported by `REFERENCES.bib:102-121` | add `\cite{source_decider_stack_2026}`; state the doc is unreleased |
| L123-129 | block quote from §11.6, incl. "**No published measurement was found** … — verified-absent, and the second lane checked it explicitly." | D (absence) | quoted with attribution | quote is recorded verbatim in `REFERENCES.bib:111-116` | **ABSENCE-3.** Reader can check only that §11.6 says this — and §11.6 is in a repository that is **not** released. Cannot check: "the second lane" |
| L133-136 | commit-message quote: "**Nobody has published the comparison we need**, so our 190-case fixture remains the load-bearing evidence." | D (absence) | yes (commit `ad301ae`) | the commit message is **not** in the released subset and is not reproduced anywhere a reader can reach | **ABSENCE-4.** Either quote it in a shipped file or drop it; the hedge at L138-142 covers only "found", not "published" |
| L138-142 | "This is a claim about a **literature search**, and the search protocol — databases, query terms, dates, inclusion rules — is **not recorded in the corpus** (`REFS.md` §B3). … this is the single largest sourcing gap in the paper" | D | yes (`REFS.md` §B3) | **SUPPORTED** and exemplary — `UNSOURCED_RETAINED.md` U2 confirms | keep; consider promoting this paragraph to the Abstract |
| L146-149 | "**The N-dependent crossover table.** arXiv `2602.06370` … The corpus records **no title, authors or venue**; we cite the identifier only … Its encoder-side wins, its latency spreads, and its cost figures are all recorded in the corpus, but its comparison class is a prompted API LLM." | B/C | yes (arXiv id) | **MIS-CITED-2** (see L64-65): the "N-dependent crossover table" label is the corpus's, not the source's. Also **STALE**: `MANUSCRIPT.md` L859-863 now says the four identifier-only entries "*have since been completed from the arXiv abstract pages … which supplied title and authors for each*", so "no title, authors or venue" is true of the corpus record but contradicts the References paragraph a reader reads 700 lines later | keep the caveat sentence; add "the entry is now completed in `REFERENCES.bib`"; supply the source's own framing |
| L150-153 | "arXiv `2512.12677` …: ModernBERT-base classifies patents at **93.45 samples/s** vs Llama-3.2-3B at **1.88** and Qwen3-4B at **1.26**; distilling a fine-tuned 3B into ModernBERT-base is recorded as retaining **≥ 97 %** of teacher F1 at **~45× throughput**. Again: identifier only, no title/authors/venue in the corpus." | C (numbers) | yes (arXiv id) | **MIS-CITED-1 — the load-bearing failure, and it is real.** I fetched `https://arxiv.org/abs/2512.12677` (v3, 25 May 2026): its abstract contains **no** `ModernBERT-base`, **no** samples/s figures, **no** `Llama-3.2-3B` or `Qwen3-4B`, and **no distillation result at all**. What it does report: decoder-only LLM fine-tuning vs *"fine-tuned BERT baselines"* on *"a 5-class single-label internal corpus and the public WIPO-Alpha multi-label dataset with 14 categories"*, *"training 10-30x fewer parameters"*, instruction-tuning competitive only in multi-label at ≥ 100M trainable params. The only word shared with the manuscript's sentence is "patents". `REFERENCES.bib:62-68` had already declared these figures **UNVERIFIED from the abstract** | **do not print these three numbers as the source's.** Delete, or move to a sentence that says the figures were observed only in the corpus and not at the source |
| L154-156 | "**PriDe** (option-ID token bias): arXiv `2309.03882`, ICLR 2024 … This grounds the position/order-bias concern that our own order-permutation probe measures" | C | yes | **SUPPORTED-BY-RECORD** (`REFERENCES.bib:79-83` records that the source's abstract confirms option-ID token bias and the `PriDe` method). **MIS-CITED-4 (low):** PriDe is a *debiasing* method, not an order-permutation probe; only the *concern* transfers, which the paper's own "PriDe-style" wording at L372 correctly signals | keep; add "(the concern, not the method)" at L155-156 |
| L157-159 | "**Grammar-constrained decoding (GCD)**: arXiv `2305.13971`, EMNLP 2023, **and ACL 2025 Industry (`2025.acl-industry.34`)** … they are *not* sources for the crossover claim." | C | **`2025.acl-industry.34` has no bib entry** | **MIS-CITED-3 (conflation) + UNRESOLVED-1.** I fetched `https://aclanthology.org/2025.acl-industry.34/`: it is **Raspanti, Ozcelebi & Holenderski, "Grammar-Constrained Decoding Makes Large Language Models Better Logical Parsers", ACL 2025 Industry Track, pp. 485–499, DOI `10.18653/v1/2025.acl-industry.34`** — a *different* work from Geng et al. (arXiv `2305.13971`, EMNLP 2023). The bullet mints one citation out of two works | split into two entries; add the Raspanti et al. bib entry (metadata above, verified) and its DOI |
| L161-180 | the Simmering counter-case section: "F1 93.1 and 152 examples/s against ModernBERT-large at 89.2 and 87 examples/s" (L166-167); "3B model against a 395M encoder — a ≈7.6× scale confound" (L172); "adding the 30 s vLLM CUDA-graph preparation time drops the LoRA arm to **42 examples/s**" (L174); "its prompted, DSPy-optimised few-shot Llama-3.2-3B arm scored **80.7 F1**" (L176-177) | C (numbers) | yes (name + date + URL + key) | **ALL SUPPORTED — verified at the source by fetch.** The blog's table: `1b-modernbert-large` 89.2 / 87; `3-Llama-3.2-3B-Instruct-LoRA` 93.1 / 152; `2-DSPy-25-threads-Llama-3.2-3B-Instruct` 80.7 / 4. Model table gives ModernBERT-large **395M** and Llama 3.2-3B **3B** (so 7.6× is the source's own figures, correctly divided). *"If that preparation time of 30 seconds is added, it's examples per second go down to 42"* ✓. *"Did it win by sheer size?"* ✓ verbatim. *"this speed comparison was not comprehensive"* ✓ verbatim | none — this is the most faithfully attributed section in the paper |
| L166 | "(ADE corpus, N = 2)" | C | yes | ✓ verified: the source uses the ADE-Benchmark Corpus, binary 1/0 classification | none |
| L182-190 | "The corpus's assertion that an encoder-only RoBERTa outperforms a fine-tuned LLaMA2-7B on 77-class intent classification is supported by Benayas, Sicilia & Mora-Cantallops (2024) … a decoder-only serving penalty of one to two orders of magnitude on a single T4 (29–108× at fixed output-token budgets). … we do not reuse the corpus's '125M' formulation (the paper prints 'approximately 110-120 million parameters') or its derived F1 gap, which the paper does not print." | C | yes (full metadata: journal, vol 59(3):2007–2030, DOI) | **SUPPORTED-BY-RECORD** — `REFERENCES.bib:302-319` reproduces Table 2 and Table 7 verbatim (*Fine-Tuned LLaMA2 at 10/25/50 max output tokens = 29x / 56x / 108x*; body text *"one to two orders of magnitude"*) and states the paper never prints "125M" but *"approximately 110-120 million parameters"*. The manuscript's refusal of the corpus's embellishments is **correct and is itself the best citation-hygiene sentence in the paper** | none |

**§2.1: 15 assertive of 27 units seen.**

---

## §2.2 What is adjacent but not the same comparison (L193–L247)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L195-196 | "Four near-misses are worth separating from our claim, because each is a different task or a different comparison class; three of them are now sourced rather than merely named" | A (meta) | n/a | **count mismatch**: L194 says "Four near-misses", L196 says "three of them are now sourced"; the four bullets are GLiNER, GLiClass, laya/imajev, router/selection, and the *first two* are sourced (GLiNER, GLiClass) while the third names two unlocated figures — "three" is not the count of sourced near-misses | fix the count |
| L198-200 | "**GLiNER** (arXiv `2311.08526`; NAACL 2024, pp. 5364–5376, DOI `10.18653/v1/2024.naacl-long.300`; `zaratiana2024gliner`) is a **span-extraction (NER)** model whose recorded win is exact-match F1 on spans, against **zero-shot (prompted)** LLMs" | C | yes (full metadata + key + DOI) | **SUPPORTED-BY-RECORD** (`REFERENCES.bib:162-168`: abstract confirms parallel entity extraction and zero-shot comparison class) | none |
| L201-208 | "that characterisation is accurate for GLiNER 2023/2024 itself, but the corpus applies it to the model id `fastino/GLiNER2.5-Decide`, which is a **text-classification decision model** … GLiNER2 (arXiv `2507.18546`; `zaratiana2025gliner2`) explicitly covers *text classification*, and **the model card tags this variant a decision model for intent classification**" | C/B | GLiNER2 cited; **the model card is not** | GLiNER2's text-classification coverage is supported by record; the **model card** claim has no URL or citation (**UNCITED-4**, minor) | add the HuggingFace card URL, or soften to "the model card, as recorded in `REFERENCES.bib:181-187`" |
| L207-208 | "What GLiNER2's abstract does not state is whether its *'LLM-based alternatives'* comparison class is prompted or fine-tuned; we do not read it either way." | D (absence) | yes | **SUPPORTED as written** — `REFERENCES.bib:190-192` records exactly this non-determinacy | none — model of how to state a negative result |
| L209-215 | "**GLiClass** … the corpus's claim that it has **no measured LLM head-to-head at all** is confirmed: its quantitative baseline tables contain only four cross-encoder/NLI models (`deberta-v3-large-zeroshot-v2.0`, `deberta-v3-base-zeroshot-v2.0`, `roberta-large-zeroshot-v2.0-c`, `comprehend_it-base`), no generative LLM … has any numeric row, GPT-4o appears only as a training-data annotator … This is an argument **from absence**, and we phrase it as one." | D/B (absence) | yes | **SUPPORTED-BY-RECORD** — `REFERENCES.bib:206-214` records the four model names from the fetched HTML (`Tables 3–6`) and `Table 7`'s qualitative LLM column. I did not re-fetch; the record is specific enough to be checkable | none; ship the fetch date |
| L216-220 | "The corpus also carries a **published** `laya-typed-decisions` figure of **0.374** and an `imajev-4b` figure of **0.645**. … the fixture figure is **0.6368** (`REPORT.md`, §'Two things … NOT defects')" | B | **no** — "published" names no publication; the only source given is `REPORT.md` | **UNCITED-2 / UNRESOLVED-3.** "published" is used for corpus-internal records; a referee will read it as an external citation and find none | replace "published" with "recorded in the corpus"; give `imajev-4b`/`laya` an identifier, a version or a note that none exists |
| L221-222 | "A learned router deciding *which* model to call is a different object from a model deciding *which label applies*; we do not extend our result to routing." | A | n/a | n/a | none |
| L224-226 | "Three further works were located while searching for external backing for §2.1's absence claim. They are real and traceable, and they are **not** sources for our central claim; none of them discharges §6.4's absence claim" | D | n/a | supported by `REFS_VERIFIED.md` §1 and `UNSOURCED_RETAINED.md` U2 | none — this is the right way to mark `ADJACENT` |
| L228-231 | "Kostina, Dikaiakos, Stefanidis & Pallis (2025) … an encoder-vs-LLM text-classification study whose LLM arms are **prompted**" | C | yes (full author list, title, arXiv id, key) | **SUPPORTED-BY-RECORD** (`REFS_VERIFIED.md` §1 quote: *"we compare decoder-only models with RoBERTa, an encoder-only baseline"*) | none |
| L232-237 | "Li, Sleem, Gentile, Nichil & State (2025) … the closest peer-reviewed equal-effort-adjacent evaluation found — it evaluates **both** prompt engineering **and** supervised fine-tuning for smaller models in industrial settings — but it is an evaluation, not a proof of absence, and **its per-task results were not retrieved**" | C | yes (pp. 971–982, DOI) | **SUPPORTED-BY-RECORD** and honestly caveated | none |
| L238-243 | "Weller, Ricci, Marone, Chaffin, Lawrie & Van Durme (2025) … under *'the same recipe for both encoder-only and decoder-only models'* it reports that *'encoder-only models excel at classification and retrieval tasks'* and that *'a 400M encoder outperforms a 1B decoder on MNLI'* — matched-recipe, peer-reviewed support for the encoder side, but its headline task is **MNLI (3-way)**, not a typed single-label decision over N = 2–8 named options." | C | yes (arXiv, ICLR'26, key) | **SUPPORTED-BY-RECORD** — quotes match `REFS_VERIFIED.md` §1 verbatim | "N = 2–8" → "N = 2–5" (**CLASS-A-1**) |
| L245-247 | "Our claim is only about the comparison class: encoder-vs-**prompted** LLM does not license the inference encoder-vs-**fine-tuned** decider" | A (argument) | n/a | n/a | none |

**§2.2: 12 assertive of 18 units seen.**

---

## §3.1 The fixture (L253–L273)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L255-259 | "a sealed set of **190** typed single-label decision cases drawn from a project's own decision corpus (`evals/fixtures/reflex-decisions.ts`), with **721** options total, **74** distinct labels (51 of which occur exactly once), and per-case option counts distributed as K = 2 (33 cases), K = 3 (27), K = 4 (76), K = 5 (54). Its sha256 is `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`" | A | n/a | **internally consistent and checkable from the released subset** (§7:804-806 ships the fixture + the same sha256). Arithmetic checks: `33·2+27·3+76·4+54·5 = 66+81+304+270 = 721` ✓, `33+27+76+54 = 190` ✓, so **max K = 5** | this line is the *evidence against* "N = 2–8" elsewhere: fix the other four occurrences |
| L256 vs L755/L804 | fixture path `evals/fixtures/reflex-decisions.ts` (source repo) vs `repro/encoder-crossover-190/fixture/reflex-decisions.ts` (released) | A | n/a | two paths for one artifact with one sha256; the source path is not released | name the released path first |
| L259-261 | "the fixture was read once (`fixtureReads = 1`) and its digest was **unchanged before and after** the second-labeller pass, with the second labeller's sandbox copy **byte-identical** to the target" | A | n/a | traceable to `second-labeller/RUN.json` | none |
| L265-268 | "**Chance floor = 0.2911.** This is the *mean of 1/K over the 190 cases*, i.e. `(33/2 + 27/3 + 76/4 + 54/5)/190 = 55.3/190 = 0.29105263…`" | B (statistic definition) | **no** | arithmetic ✓ (`16.5+9+19+10.8 = 55.3`). The *construct* — mean-1/K chance floor — is an external methodological convention used with no citation | **UNCITED-5** (low): cite the chance-floor convention or state that it is the authors' own definition |
| L269-271 | "**Option-0 rate = 0.3789**; **leaky majority rate over the fixture's own answers = 0.1474**" | A | n/a | traceable to the fixture | none |
| L272-273 | "The fixture was authored by one worker and carries known flagged weak points; see §6.2 and the five owed corrections listed in `CHECKLIST.md`" | A/D | `CHECKLIST.md` is in `papers/encoder-crossover-190/` but **not** in §7's released-material table | the five corrections are therefore not checkable by a reader | **UNRESOLVED-7** (minor): add `CHECKLIST.md` to §7's inventory |

**§3.1: 5 assertive of 7 units seen.**

---

## §3.2 The arms (L275–L303)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L277-278 | "Five arms were evaluated on the sealed fixture by the source experiment (EXP#12). All five accuracy figures below are read from the per-arm `eval-*.json` and agree with `REPORT.md`'s §1 table to printed precision." | A | n/a | `CLAIMS.md` maps numbers to sources; §7:754 ships `results/eval-*.json` | none |
| L282-286 (table) | `modernbert-base` 149,015,041 params, 0.3474; `deberta-v3-base` 183,832,321, 0.3474; `setfit-mpnet` 109,489,537, 0.2632; `majority-class` 0, 0.4526; `shuffled-label` 149,015,041, 0.2316; columns **ECE** and **Brier** | A + B | **no citation for ECE or Brier** | parameter counts and accuracies are the paper's own; **ECE and the Brier score are named external instruments used with no citation** | **UNCITED-6**: cite Guo et al. (2017) for ECE/temperature scaling and Brier (1950) for the Brier score, once, at first use |
| L288-291 | "**The three candidate heads are 109M–184M parameter encoders.** They are, in the corpus's framing, the 'small encoder' side of the crossover: ModernBERT-base, DeBERTa-v3-base, and a SetFit-MPNet head." | B (external models) | **no** | the three base models are the paper's own arms and the source of its numbers, and **none of the three is in the bibliography** — no ModernBERT paper, no DeBERTa-v3 paper, no MPNet/Sentence-Transformers paper, no SetFit paper | **UNCITED-7 (highest-value new finding)**: the paper's measurement is *about* these three checkpoints and cites none of them. See also Data-and-code L837-841 (licences) |
| L293-298 | "**⚠ `deberta-v3-base` did not train at the pre-registered operating point.** train loss 1.1288 → 1.1235 …, dev accuracy 0.50 → 0.495 against a dev majority-class baseline of **0.475** (`analysis.json .observations.debertaV3Training`)" | A | n/a | points at a named JSON key | none |
| L300-303 | "**Training is not bit-reproducible.** Three identical training runs produced ModernBERT epoch-1 dev accuracies of 0.5150 and 0.5900 and fixture accuracies of 0.3421 and 0.3474 (`REPORT.md`, §'A caveat that is not a defect'). A ±1–2 point band is honest for **every** head number" | A | n/a | points at `REPORT.md` | none |

**§3.2: 5 assertive of 10 units seen.**

---

## §3.3 The baselines (L305–L347)

This section is almost entirely class A (strategy/PAPER_CANDIDATES.md:269 etc. are internal records). Its
citation-relevant content is the word "published" and the path claims.

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L307 | "There are **two** fine-tuned 4B (`decider-4b`, 4.66B params) figures in the evidence tree, and they are **not** the same measurement." | A | n/a | traceable to `analysis.json` | none |
| L312-315 (table) | primary 0.6789 from `analysis.json .baselinesRescored[…]`; per-case rows "survive in `docs/research/EXP#11-evidence/decider-rows.jsonl`"; historical **"published"** 0.6684 from `analysis.json .publishedBaselines[…]` | A/D | `"published (D-067)"` — **D-067 is never identified** | the per-case rows are claimed in **two** different places: here `docs/research/EXP#11-evidence/decider-rows.jsonl` (source repo, unreleased) and at §7:772 `repro/encoder-crossover-190/results/baselines.json` (released) | **UNRESOLVED-3+8**: name the released copy; say what "D-067" is |
| L320-324 | "**0.6684 is reported as a secondary / robustness figure** … it is the figure the working title's '0.32' comes from — but it **cannot be re-scored** (`REPORT.md:104` `reproduces at 3 d.p. = None`; `:189` no per-case rows survive)" | A | n/a | internally traceable | none |
| L338-347 | the seven sentences that would change if the declaration were revisited | A | n/a | n/a | none |
| L325-326 | "the conclusion is unchanged by the choice: 0.3474 loses to both, and −0.3316 exceeds 2× either MDE (2.079× paired / 2.446× unpaired)" | A/B | **MDE is not defined or cited** | arithmetic is the paper's | **UNCITED-8** (low): MDE (minimum detectable effect) is an external construct; cite or define it |

**§3.3: 7 assertive of 13 units seen.**

---

## §3.4 Controls (L349–L383)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L354-356 | "**Majority-class control (0.4526).** Could have contradicted the candidate … no head does; the margin is +0.1053 over the best head." | A | n/a | traceable (§4.3) | none |
| L357-362 | "**Shuffled-label control (0.2316).** … its temperature-scaling fit hit the grid ceiling (100.0, `onGridCeiling = true`), so its reported ECE **0.0808 is an upper bound**" | A/B | temperature scaling uncited | internally traceable | see **UNCITED-6** |
| L363-371 | "**F4 n-gram leak lint.** … rule = 'drop a row when it shares ≥ 2 distinct 8-grams with any single row of the other side' … it compared **152,000** training↔fixture pairs in each direction and flagged **0** … three deliberately seeded copies, which fired at **13 / 44 / 57**" | A | n/a | internally traceable to `lint-report.json`, which **§7:757 says is not in the released set** | state the released/unreleased boundary at the claim, not only in §7 |
| L372-376 | "**Order-permutation probe.** A PriDe-style option-order probe. In the buggy pass-1 it flipped answers on 138 (ModernBERT), 142, 101, 135 and 81 cases … in the final pass it flips **0** for all candidate heads and **58** for the majority-class control." | C + A | "PriDe-style" cites arXiv `2309.03882` at L154 | method borrows the *concern*, not PriDe's procedure (see **MIS-CITED-4**) | keep "PriDe-style"; do not imply the probe is PriDe's |
| L377-383 | "Reader B (`routeB-blind-model`) reached agreement 0.9053, κ 0.9014, 18/190 disagreements; reader B2 (`mimo-v2.6-flash`) reached 0.8632, κ = 0.8577, 26/190 … The two readers agree with each other at 0.9158, κ = 0.9125." | A/B | **two named models, no citations, no versions, no URLs** | the numbers are the paper's own; the *instruments* are external models used as measurement devices | **UNCITED-9**: `mimo-v2.6-flash` needs a model card/version reference; `routeB-blind-model` is **not identifiable at all** — an anonymous instrument in a reproducibility claim |

**§3.4: 9 assertive of 20 units seen.**

---

## §4.1 The five arms (L389–L398)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L391-394 | "Best fine-tuned encoder head: **0.3474** … `setfit-mpnet`: **0.2632**. Every one of these is barely above the fixture's **0.2911** chance floor, and `setfit-mpnet` is **below** it." | A | n/a | consistent with §3.2 table and §3.1 chance floor ✓ | none |
| L396-398 | "**The pre-registered falsifier F1 fired.** It was written as *'encoder accuracy < 0.6684 (the best 4B)'* (`EXP#12-typed-channel-comparison.md:95`, `REPORT.md:85`)" | A | internal protocol cited | the pre-registration ships (§7:759) | none |

**§4.1: 3 assertive of 4 units seen.**

---

## §4.2 The paired fine-tuned comparison (L400–L449)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L405-418 (table) | head 0.3474; decider same-run 0.6789; Δ **−0.3316**; **McNemar** discordant b 27 / c 90; **exact two-sided p 4.167e−09**; continuity-corrected χ² 32.85; paired MDE 0.1595; unpaired MDE 0.1355; **paired bootstrap 95 % CI [−0.4316, −0.2263]** | A/B | **no citation for McNemar's test, the exact test, the χ² continuity correction, or the bootstrap** | all values are the paper's own and mutually checkable; the *tests* are named external instruments used without citation | **UNCITED-10**: cite McNemar (1947) and a bootstrap reference once |
| L420-422 | "Δ was checked by two independent paths: `0.3473684210526316 − 0.6789473684210526 = −0.33157894736842103`, and `(b − c)/n = (27 − 90)/190 = −63/190 = −0.3315789473684211` — same value. ψ = 117/190 = 0.6157894736842106." | A | n/a | arithmetic ✓ | none |
| L424-427 | "Against the **historical, published 0.6684** … the difference is `0.6684 − 0.3474 = **0.3210**`" | A/D | "published" unnamed | internal | see **UNCITED-2** |
| L429-444 | "The corpus's own summary (`strategy/PAPER_CANDIDATES.md:269`, `experiments/LEARNINGS.md:281`) states *'Every correction moved the affected arm DOWN.'* **That is false as a universal.** `DEFECT-EVIDENCE.json` shows: …" | C (internal) | two internal file:line citations | **SUPPORTED** by `DEFECT-EVIDENCE.json` (ships, §7:756) | none — exemplary correction of the record |
| L446-449 | "SetFit's ECE moved **0.1665 → 0.2738** … its order-permutation flips moved **101 → 46 → 36 → 0** … Pass-1 flips for the other arms were 138 (ModernBERT), 142, 101, 135, 81" | A | n/a | traceable | none |

**§4.2: 5 assertive of 13 units seen.**

---

## §4.3 – §4.7 (L451–L503)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L453-457 | "The majority-class control returns **0.4526** — a constant answer beats **every** fine-tuned encoder head on this fixture, by a margin of **+0.1053** … (`0.45263157894736844 − 0.3473684210526316 = 0.10526315789473684`)" | A | n/a | arithmetic ✓ | none |
| L464-467 | "`lint-report.json`: `fires = false`, `silent = true`, `removedCount = 0` … `analysis.json .falsifiers.F4.fires = false`" | A | n/a | **the file named first is not in the released subset** (§7:757) | name the released copy or drop the file claim |
| L471-472 | "The observed harm is `0.33157894736842103 / 0.15949356562876219 = **2.079×**` the **paired** MDE, and 2.446× the unpaired MDE." | A/B | MDE uncited | arithmetic ✓ | see **UNCITED-8** |
| L474-477 | "**⚠ We do not reuse the phrase 'paired is conservative.'** On this run it is false. ψ = 0.616 is high, so `unpaired/paired = sqrt((p₁(1−p₁)+p₂(1−p₂))/ψ) = 0.85×`" | A | n/a | arithmetic ✓ | none |
| L481-492 | "The best head's ECE is **0.0994** … The decider-4b's stored ECE is **0.0551** under one convention and **0.1547** under the other … Temperature scaling was fitted on a geometric grid from 1e−3 to 1e2, 200 points" | A/B | **ECE/temperature scaling uncited** | internally traceable; the convention ambiguity is honestly presented | **UNCITED-6** |
| L496-498 | "**H4 is not supported.** The accuracy ordering is **monotone** in parameter count across the three heads (0.2632 at 109M < 0.3474 = 0.3474 at 149M and 184M), so there is no size-crossover story *within* these heads. `analysis.json .h4.verdict` records this explicitly." | A | n/a | **CLASS-A-2 — contradicts §6.5:697**, which states H4 as *"accuracy monotone in parameter count"* and then says it is *"not supported"* while immediately reporting that *"the observed ordering is monotone"*. As written, §6.5 defines H4 as the proposition §4.7 reports as observed | restate H4 once, identically, in both places (it is evidently the *size-crossover* hypothesis) |
| L499-502 | "The same `decider-4b` reproduction scores **0.6650** on the H-A corpus stratum (reproducing **its published 0.665**) and **0.67** on H-B … `imajev-4b`'s **0.645** is likewise an **H-A corpus stratum** figure; its fixture figure is **0.6368**." | A/B | "its published 0.665" — **no publication named** | internal | **UNCITED-2** again; "published" must be replaced |

**§4.3–§4.7: 7 assertive of 25 units seen.**

---

## §5.1 – §5.3 Discussion (L508–L551)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L510-514 | "The published crossover compares an encoder against a **prompted** LLM. When the generative side is fine-tuned on the same task with the same labels, the crossover does not appear on our fixture" | D | no (relies on §2.1) | as an absence claim it inherits **ABSENCE-2** | add a cross-reference to the §11.6 qualification |
| L516-521 | "Prompting and fine-tuning are different *resources*; the published results show what a prompted LLM does with a task description and a few examples … which is exactly the inference the corpus's own errata says the literature does not license." | A/C | internal errata | supported | none |
| L523-526 | "That a fine-tuned generative decider beats a fine-tuned encoder at comparable effort is already public (§2.1, Simmering 2025 — a blog post, not peer-reviewed)" | C | yes | **SUPPORTED** (verified at source) | none |
| L530-536 | "The sharper finding is **0.3474 vs 0.4526**: a constant answer beats every fine-tuned encoder head by **+0.1053** … Any recommendation of the form 'use an encoder head as the default at N ≥ 4' must clear the majority-class bar" | A | n/a | traceable; **"N ≥ 4"** is quoted from the corpus's prior recommendation, not from a source | name whose recommendation it is (the internal `DECIDER_STACK_DECISION.md`) |
| L540-550 | the four method lessons (defect chain; quoted MDE; calibration convention; mandatory control) | A | n/a | internally consistent with §4.2/§4.5/§4.6 | none |

**§5: 5 assertive of 22 units seen.** (`§5` heading, L506, carries no prose.)

---

## §6.1 Latency (L556–L580)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L558-559 | "**We make no latency claim, in the abstract, the results or anywhere else.** The evidence tree cannot support a fair latency comparison, for four recorded reasons" | A | n/a | n/a | none |
| L561-563 | "`REPORT.md:191`: *'The heads were timed on the GX10's GB10 with local weights; the decider's 0.075 s/decision figure … come from a served model on a different stack.'*" | A | yes (internal, quoted) | shipped record | none |
| L564-567 | "The head figure is one full per-decision call — all option texts tokenised, **one forward batch**, softmax (12.37 / 14.16 / 11.96 / 12.46 ms for the four heads; 0.003 ms for majority-class; n = 570 after 20 warm-up cases, GPU synchronised)" | A | n/a | traceable | none |
| L568-569 | "**The F6 threshold is a constant, not a measurement.** F6 compares heads against the **pre-registered** 0.075 s/decision from `DECIDER_TIER §2`" | A/D | `DECIDER_TIER §2` — **a document that appears nowhere else in the paper and is not in §7's inventory** | a reader cannot locate `DECIDER_TIER` | **UNRESOLVED-9**: cite it as a path, or list it in §7 |
| L571-574 | "**The decider's own timing spreads 2× across strata of the same model** — 53.06 ms (instrument190), 72.85 ms (H-B), 106.92 ms (H-A) … (`imajev-4b` and `laya` sit at 453 ms / 639 ms in the same stored source …)" | A | n/a ("same stored source") | traceable internally; `imajev-4b`/`laya` unidentified (see **UNRESOLVED-3**) | none beyond that |
| L576-580 | "per-decision, the heads sit in the tens of milliseconds and the stored decider figures sit in the tens-to-hundreds of milliseconds, measured on different stacks and different operations." | A | n/a | n/a | none |

**§6.1: 6 assertive of 11 units seen.**

---

## §6.2 Two blind model readers (L582–L653)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L584-592 | "Reader B (`routeB-blind-model`) agrees … 0.9053 of the time, κ = 0.9014, with 18/190 disagreements. Reader B2 (`mimo-v2.6-flash`) … agrees **0.8632**, **κ = 0.8577** … The two readers agree with **each other** **0.9158** … **κ = 0.9125**" | A/B | **no citations for the two models** | numbers traceable (`RUN.json`, `metrics2.json`); instruments unnamed | **UNCITED-9** |
| L594-598 | "The two readers agree with each other *more* than either agrees with the fixture record (0.9158 > 0.9053 and > 0.8632). That is consistent either with a shared LLM reading bias or with author-idiosyncratic conventions in the fixture, and we do not resolve it" | A | n/a | n/a | none |
| L602-607 | "the weakest is `memory.admission` (B2 κ = **0.5625**, UEXP κ = **0.7153**), followed by `acquisition` (B2 **0.7045**, UEXP **0.8049**)" | A | n/a | traceable | none |
| L608-612 | "Four cases (`memory.admission-001/-009/-021/-027`) record step-scoped scratch that is never re-read as `EPHEMERAL`; **both** blind readers independently chose `DROP` on all four (**4/4** replicated). UEXP first reported this convention and UEXP2 shows it is not one model's quirk." | A | n/a | traceable | none |
| L613-620 | "Agreement falls from 0.970 (2-option cases, n = 33) to 0.722 (5-option cases, n = 54) for B2, and from 1.000 to 0.815 for UEXP (κ 0.950 → **0.684** and 1.000 → 0.791) … on the stratum where the answer is named in the question (30 `escalation` cases) the readers scored 30/30 (UEXP) and 28/30 (B2)" | A | n/a | traceable; **note the option arities here are 2 and 5, consistent with §3.1 and inconsistent with "N = 2–8"** | none here; reinforces **CLASS-A-1** |
| L621-627 | "B2 disagrees on 26 cases and UEXP on 18, but the overlap is a **14-case shared contested core** — all four `acquisition` traps (`-007/-014/-019/-023`) … The tails (12 B2-only, 4 UEXP-only)" | A | n/a | traceable (`disagreementsB2.jsonl`) | none |
| L631-639 | "51 of 74 labels occur once, so `pe` is tiny (0.040) and κ is dominated by `po`. … closed-vocabulary subset (4 kinds, 106 cases) κ = **0.8837**; roster-and-bespoke subset (84 cases) κ = **0.9140**; AB mutual agreement **0.3684**; the deterministic lexical rule (routeA — a **rule**, not a labeller) reaches only κ = **0.3249**" | A/B | **κ uncited** | traceable | **UNCITED-3** |
| L640-642 | "A threshold was pre-registered (≥ 0.90 agreement / ≥ 0.85 κ). Reader B *met* it at 0.905 / 0.901; reader B2 *met the κ threshold but not the agreement threshold*, at 0.863 / 0.858." | A | n/a | pre-registration ships (§7:760) | none |
| L644-651 | "`experiments/second-labeller-190/EVIDENCE.md:309` states it for one pass — *'**It is not IAA.** One pass is a model.'* … §F.3's point — that several candidate papers share this one 190-case fixture, so *'one fixture flaw propagates into four papers'* — remains true … §F.3" | C/D | `PAPER_CANDIDATES.md §F.3` is cited by section only, with **no file path at L644 or L659**, and is not in the released subset | a reader cannot resolve "§F.3" | **UNRESOLVED-10**: give the path (`strategy/PAPER_CANDIDATES.md` §F.3) |
| L651-653 | "The fixture's own flagged decidability weak points (five owed corrections, of which four are repairs to the fixture file itself) are listed in `CHECKLIST.md` and were **deliberately not applied**" | A | `CHECKLIST.md` not in §7's inventory | see **UNRESOLVED-7** | add to §7 |

**§6.2: 12 assertive of 30 units seen.**

---

## §6.3 External validity (L655–L665)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L657-660 | "This is a single 190-case fixture authored by one worker, evaluated on one host. … The fixture shares its provenance with several other candidate papers (§F.3). **No external typed-decision benchmark was used, and none was found in the corpus to use.**" | A/D (absence) | "§F.3" unresolvable (see above) | **ABSENCE-5**: an absence claim about the corpus's contents with no recorded inventory or protocol; the paper itself is the only witness | either produce the list of benchmarks considered, or downgrade to "no external typed-decision benchmark is used in this paper" |
| L662-665 | "**The primary baseline is declared: 0.6789** … The seven sentences that would change if that declaration were ever revisited are enumerated in §3.3" | A | n/a | §3.3 lists **seven** items ✓ (L341-347) | none |

**§6.3: 4 assertive of 7 units seen.**

---

## §6.4 The literature claim (L667–L685)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L669-674 | "§2's core claim is supported by `docs/DECIDER_STACK_DECISION.md` §11.6 and commit `ad301ae` … but it is a claim about a **literature search whose protocol is not recorded** … UREFS's external search then **failed to upgrade the hedge**: no survey or recorded search protocol establishing the absence was located, so the weaker phrasing stays." | D (absence) | internal doc + commit | **SUPPORTED** — `REFS_VERIFIED.md` §1 and `UNSOURCED_RETAINED.md` U2 record the queries and the failure. This is the paper's second-best hygiene paragraph | keep; a referee will want the query list **in the paper or an appendix**, not in an unreleased side file |
| L676-682 | "It reports a fine-tuned Llama-3.2-3B LoRA at F1 93.1 beating ModernBERT-large's 89.2 on binary ADE classification at equal per-arm training cost … plus that post's independent reproduction of the prompted-baseline half (its prompted arm scored 80.7)" | C | yes | **SUPPORTED** (verified at source) | none |
| L682-685 | "an encoder-only RoBERTa beating a fine-tuned LLaMA2-7B on 77-class intent classification — is now sourced to Benayas, Sicilia & Mora-Cantallops (2024), *Language Resources and Evaluation* **59**(3):2007–2030, DOI `10.1007/s10579-024-09796-y`, and cited for that result." | C | yes (full metadata) | **SUPPORTED-BY-RECORD** | none |

**§6.4: 4 assertive of 7 units seen.**

---

## §6.5 Scope of the candidate arms (L687–L698)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L689 | "Only three encoder families were run, all 109M–184M parameters: ModernBERT-base, DeBERTa-v3-base and SetFit-MPNet." | B | **no** | the arm definition cites nothing | **UNCITED-7** |
| L690-694 | "**`deberta-v3-base` did not train** at the pre-registered operating point (train loss 1.1288 → 1.1235; dev 0.50 → 0.495 against a dev majority-class baseline of 0.475) … three identical runs gave ModernBERT epoch-1 dev accuracies 0.5150 and 0.5900 and fixture accuracies 0.3421 and 0.3474" | A | n/a | traceable | none |
| L695-696 | "A reviewer's obvious fourth arm — **a trained linear probe on a frozen LLM embedding** — was not run and is *not* present anywhere in the evidence tree; it is listed as an open decision in `OPEN_QUESTIONS.md`." | A/D (absence) | internal | **SUPPORTED** by `UNSOURCED_RETAINED.md` U6 | none |
| L697-698 | "H4 (accuracy monotone in parameter count) is **not supported**; the observed ordering is monotone, so there is no within-heads size-crossover story to tell." | A | n/a | **CLASS-A-2** — self-contradictory as worded and contradicting §4.7:496-498 | restate H4 |

**§6.5: 4 assertive of 6 units seen.**

---

## §6.6 The counter-case asks whether our encoder arm is simply under-trained (L700–L738)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L705-707 | reviewer's voice: "a real ModernBERT-large reached **0.892 F1** in the counter-case" | C | yes | **SUPPORTED** (89.2 at source; 0.892 is the same figure as a fraction) | none |
| L712-716 | "The counter-case's 89.2 F1 is **binary (N = 2) sentence classification** on the ADE corpus; our fixture is a typed single-label decision over N = 2–8 named options, with **74** distinct labels (51 occurring exactly once) and a **0.2911** mean-1/K chance floor." | C + A | yes | the counter-case characterisation ✓ verified; **"N = 2–8" is wrong** (**CLASS-A-1**) | fix to N = 2–5 |
| L717-722 | "It licenses exactly one claim: on this fixture, **no encoder head is a viable default** — 0.4526 beats the best head by **+0.1053**" | A | n/a | traceable | none |
| L723-728 | "The counter-case's equal-effort premise (*under one dollar, under 15 minutes per arm on one A10G*) is **its** premise on **its** task; we did not reproduce it" | C | yes | **SUPPORTED** — verified at source: *"All setups can be trained for under one dollar and in less than 15 minutes"* and *"All training and inference is done on a single A10G GPU hosted on Modal"*. (The corpus's own bib note does **not** carry the A10G detail; the source does.) | none |
| L729-733 | "If the encoder arm is under-trained, part of the 0.3316 shortfall could reflect the recipe rather than the crossover. … It is named as an **open question** in `UNSOURCED_RETAINED.md`" | A/D | internal | **SUPPORTED** by `UNSOURCED_RETAINED.md` U6 | none — most honest section in the paper |
| L734-738 | "A **change of direction under fine-tuning** on one sealed fixture … **not** an estimate of an encoder ceiling, and **not** an equal-effort law." | A | n/a | n/a | none |

**§6.6: 6 assertive of 14 units seen.**

---

## §7 Reproduction (L742–L786) and Data and code availability (L790–L854)

| line | claim (quoted, trimmed) | class | citation present? | supporting? | action |
|---|---|---|---|---|---|
| L744-749 | "Everything in this paper is checkable against the released reproducibility subset `repro/encoder-crossover-190/` … **The evaluation harness — the model, training and evaluation code — is withheld**" | A | n/a | n/a | none |
| L752-763 (table) | the released-material inventory | A | n/a | the table is the paper's own; **`CHECKLIST.md` and `DECIDER_TIER` are absent from it** while both are cited as evidence elsewhere | add them, or say they are unreleased |
| L762 | "harness provenance … recovered from an unmerged development branch (**name and commit withheld**), path `tools/typed-channel/` — 18 files recovered read-only via `git cat-file blob`" | A | n/a | unreproducible by design; stated as such | none |
| L765-769 | "The p-value is written with a **typographic minus (U+2212)** in `strategy/PAPER_CANDIDATES.md:265` and `experiments/LEARNINGS.md:265` (`4.167e−09`), so `grep 4.167e-09` … returns nothing" | A | internal files | note: §4.2:430 cites the *same* two files as `:269` and `:281` for a different quote — three different line numbers to two files; not a defect, but it means these side files are load-bearing yet unreleased | none |
| L771-776 | "the per-case rows shipped in `repro/encoder-crossover-190/results/baselines.json` (`.models["decider-4b-exp11-reproduction"].perCase`, 190 rows) re-score to 0.6789 vs published 0.6789" | A | n/a | **this is the released home of the rows §3.3:314 locates in `docs/research/EXP#11-evidence/decider-rows.jsonl`** | reconcile the two paths (**UNRESOLVED-8**) |
| L837-841 | "**No model weights** are released: the three arms are fetched as **public** checkpoints at run time (`answerdotai/ModernBERT-base`, Apache-2.0; `microsoft/deberta-v3-base`, MIT; `sentence-transformers/all-mpnet-base-v2`, Apache-2.0), and no weight file is shipped" | B | **no** | three licence claims about three external artifacts with no citation or licence URL | **UNCITED-7** again: cite the three checkpoint/model papers and give the licence URLs |
| L848-854 | "released artifacts are **source-available under PolyForm Noncommercial 1.0.0**, with an **author-offered paid commercial licence**" | A | n/a | own decision | none |
| L792-794 | "**The paper is public, CC BY 4.0.** By the author's decision of 2026-10-15" | A | n/a | own decision | none |
| L856-877 (References prose) | the reference narrative: arXiv `2602.06370`, `2512.12677`, PriDe `2309.03882`, GCD `2305.13971`, ACL `2025.acl-industry.34`, `simmering2025modernbert`, GLiNER `2311.08526`, GLiNER2 `2507.18546`, GLiClass `2508.07662`, `2501.08457`, `2025.acl-industry.68`, `2507.11412`, `benayas2024comparative` | C | yes (13 works named in 22 lines) | all 13 bib entries are named here; `source_decider_stack_2026` is described but **never named by key** | add `\cite` keys; **`2025.acl-industry.34` is named here with still no bib entry** (**UNRESOLVED-1**) |

**§7 + Data/code + References: 9 assertive of 44 units seen.**

---

# SUMMARY LISTS

## UNCITED — claims that need a citation and do not have one

| id | line(s) | claim | what is missing |
|---|---|---|---|
| **UNCITED-1** | L62-63 | *"A common empirical shape in applied model-selection work is a crossover: at small label-set sizes N a large language model (LLM) wins or ties, and above some N a small fine-tuned encoder takes over."* | a citation for the generalisation, or an explicit "hypothesis" framing |
| **UNCITED-2** | L38, L39, L96, L315, L424, L499, L512, L663 | the word **"published"** applied to corpus-internal records: `*published, pre-registered* baseline 0.6684`; `published (D-067)`; `reproducing its published 0.665`; `the *published* 0.6684` | either a real publication, or the wording "recorded in the corpus (D-067)" — a referee will read "published" as an external citation and find none |
| **UNCITED-3** | L52-53, L378-383, L584-598, L631-648 | **Cohen's κ** used as the paper's reliability statistic (κ = 0.9014 / 0.8577 / 0.9125 / 0.8837 / 0.9140 / 0.3249) | a citation for κ at first use |
| **UNCITED-4** | L203-205 | *"the model card tags this variant a decision model for intent classification"* (`fastino/GLiNER2.5-Decide`) | a URL or citation for the model card |
| **UNCITED-5** | L265-268 | *"**Chance floor = 0.2911.** This is the *mean of 1/K over the 190 cases*"* | the definition is the authors'; say so, or cite the convention |
| **UNCITED-6** | L282-286, L360-362, L481-492 | **ECE** and **temperature scaling** (grid 1e−3→1e2, 200 points; ceiling 100.0) | cite Guo et al. (2017) |
| **UNCITED-7** | L288-291, L689, L837-841 | the three arm models — `answerdotai/ModernBERT-base` (Apache-2.0), `microsoft/deberta-v3-base` (MIT), `sentence-transformers/all-mpnet-base-v2` (Apache-2.0) — plus the SetFit-MPNet head | **cite all four**: ModernBERT (Warner et al. 2024), DeBERTa-v3 (He et al. 2021), MPNet (Song et al. 2020), SetFit (Tunstall et al. 2022), plus Sentence-Transformers. The paper measures these models and currently cites none of them |
| **UNCITED-8** | L325-326, L471-472 | **MDE** (paired 0.1595 / unpaired 0.1355) quoted as the power figure | define or cite |
| **UNCITED-9** | L377-383, L584-586, L761 | the labeller models `routeB-blind-model` (anonymous) and `mimo-v2.6-flash` | a model card/version for `mimo-v2.6-flash`; a name or archive for `routeB-blind-model` — as written the instrument behind κ = 0.9014 cannot be identified by a reader |
| **UNCITED-10** | L405-418 | **McNemar's exact test**, continuity-corrected χ², paired bootstrap CI | cite McNemar (1947) + a bootstrap reference |
| **UNCITED-11** | L280-286 | the **Brier score** column | cite Brier (1950) |

## MIS-CITED — citation present, does not support the sentence

| id | line(s) | claim | evidence |
|---|---|---|---|
| **MIS-CITED-1** *(load-bearing; the previously suspected one, now confirmed at the source)* | **L150-152** | *"arXiv `2512.12677`, same section: ModernBERT-base classifies patents at 93.45 samples/s vs Llama-3.2-3B at 1.88 and Qwen3-4B at 1.26; distilling a fine-tuned 3B into ModernBERT-base is recorded as retaining ≥ 97 % of teacher F1 at ~45× throughput."* | fetched `https://arxiv.org/abs/2512.12677` (v3, 25 May 2026): the abstract has **no** `ModernBERT-base`, **no** samples/s numbers, **no** `Llama-3.2-3B`/`Qwen3-4B`, **no** distillation. It compares decoder-only fine-tuning vs *"fine-tuned BERT baselines"* on a 5-class patent corpus + WIPO-Alpha (14 categories), *"10-30x fewer parameters"*. `REFERENCES.bib:62-68` already flagged these as **UNVERIFIED** |
| **MIS-CITED-2** | **L64-65, L146, L149, L512** | the "**N-dependent crossover table**" label and the N = 4 win / N = 2 loss attributed to `arXiv 2602.06370`, plus the figures `94.11–94.63 vs 91.35` and `99.27–99.40 vs 98.83` | fetched `https://arxiv.org/abs/2602.06370`: abstract reports encoders as *"competitive, and often superior"* across IMDB, SST-2, AG News, DBPedia — **no N analysis, no crossover, none of those figures**. `REFERENCES.bib:49-50` says the N-framing "*is the corpus's own characterisation; it is NOT verbatim in the source's title or abstract*" — a caveat the manuscript never carries |
| **MIS-CITED-3** | **L157-158** | *"**Grammar-constrained decoding (GCD)**: arXiv `2305.13971`, EMNLP 2023, and ACL 2025 Industry (`2025.acl-industry.34`)"* | two distinct works collapsed into one citation. Fetched `https://aclanthology.org/2025.acl-industry.34/` = **Raspanti, Ozcelebi & Holenderski, "Grammar-Constrained Decoding Makes Large Language Models Better Logical Parsers", ACL 2025 Industry, pp. 485–499, DOI 10.18653/v1/2025.acl-industry.34** — not Geng et al. |
| **MIS-CITED-4** (low) | **L154-156, L372** | *"**PriDe** (option-ID token bias) … grounds the position/order-bias concern … A PriDe-style option-order probe"* | PriDe (Zheng et al., arXiv `2309.03882`) is a label-free *debiasing* method for option-ID token bias, not an order-permutation probe. The "PriDe-style" hedge makes this defensible; do not upgrade it to a method transfer |
| **MIS-CITED-5** | **L499** | *"scores 0.6650 on the H-A corpus stratum (**reproducing its published 0.665**)"* | "its published" has no antecedent work; same defect as UNCITED-2 |

## UNUSED-ENTRIES

**0 unused by prose reading; 13 unused by mechanized reading** (`main.tex` has **0 `\cite` commands**,
13 `\bibitem`s).

All 13 `REFERENCES.bib` keys are reachable in the manuscript text, by key or by identifier:

| key | where the manuscript names it |
|---|---|
| `arxiv2602_06370` | L146 (arXiv id), L860 |
| `arxiv2512_12677` | L150 (arXiv id), L862 |
| `pride2309_03882` | L154 (arXiv id), L863 |
| `gcd2305_13971` | L157 (arXiv id), L865 |
| `source_decider_stack_2026` | L118-120, L669 — **by path/commit only, never by key** |
| `simmering2025modernbert` | L165, L677, L869 (by key) |
| `zaratiana2024gliner` | L199 (by key) |
| `zaratiana2025gliner2` | L205 (by key) |
| `stepanov2025gliclass` | L209 (by key) |
| `kostina2025llmtextclassification` | L229 (by key) |
| `li2025smalllanguagemodels` | L234 (by key) |
| `weller2025seqvsseq` | L239 (by key) |
| `benayas2024comparative` | L186, L874 (by key) |

Two hygiene notes: (a) `gcd2305_13971` is cited only in a bullet the paper itself declares *"not sources for
the crossover claim"*, and `REFERENCES.bib:99` says the manuscript *"may legitimately drop this entry"*;
(b) **5 of 13 entries lack a venue and 1 (`arxiv2602_06370`) lacks a reported venue too** —
`REFERENCES.bib:6-8` says title/author/venue fields "are deliberately LEFT ABSENT"; four have since been
completed from arXiv (per L859-863) and 9 are complete.

## UNRESOLVED-CITATIONS — in-text citations with no resolvable entry

| id | line(s) | citation as printed | status |
|---|---|---|---|
| **UNRESOLVED-1** | **L158, L866** | `2025.acl-industry.34` | **no `REFERENCES.bib` entry.** Resolved by me by fetch: **Raspanti, Ozcelebi & Holenderski, "Grammar-Constrained Decoding Makes Large Language Models Better Logical Parsers", ACL 2025 Industry, pp. 485–499, DOI 10.18653/v1/2025.acl-industry.34** — add it |
| **UNRESOLVED-2** | L568-569 | `DECIDER_TIER §2` | no entry, no path, not in §7's inventory — a reader cannot locate it |
| **UNRESOLVED-3** | L217-218, L501-502, L571-573 | `laya-typed-decisions` (0.374), `imajev-4b` (0.645 / 0.6368 / 453 ms), `laya` (639 ms) | named figures/arms with no identifier, no version, no citation, and not in §7's table |
| **UNRESOLVED-4** | L203-205 | `fastino/GLiNER2.5-Decide` | model id, no URL |
| **UNRESOLVED-5** | L377-378, L584 | `routeB-blind-model` | not identifiable at all — an anonymous model used to produce a headline reliability number |
| **UNRESOLVED-6** | L586, L761, L818-821 | `mimo-v2.6-flash` | model id, no version or card |
| **UNRESOLVED-7** | L273, L652 | `CHECKLIST.md` | cited twice as evidence, absent from §7's released-material inventory |
| **UNRESOLVED-8** | **L314 vs L772** | `docs/research/EXP#11-evidence/decider-rows.jsonl` **vs** `repro/encoder-crossover-190/results/baselines.json` | the *same* 190 per-case rows are located in two different places; the first is unreleased, the second is released — name the released one |
| **UNRESOLVED-9** | L644, L659 | `PAPER_CANDIDATES.md §F.3` | cited by section only, no path on either occasion |
| **UNRESOLVED-10** | L430 | `strategy/PAPER_CANDIDATES.md:269`, `experiments/LEARNINGS.md:281` | internal, unreleased, and the same two files are cited at `:265` for a different quote (L766) |

## ABSENCE-CLAIMS — every "we found none" sentence, quoted, with what supports it

| id | line(s) | quote (trimmed) | supported as written? |
|---|---|---|---|
| **ABSENCE-1** | L20-22 | *"Every public 'a small encoder wins' result we were able to locate **inside the target corpus** compares that encoder against a **prompted** … LLM, never against a **fine-tuned generative decider** (the claim and its audit trail are internal to the corpus, not an external survey — §2)."* | **YES, as hedged.** `REFS_VERIFIED.md` §1: no external survey found. Reader can check: the §11.6 text if they have the unreleased repo. Cannot check: the search itself. **This is the correct phrasing — keep it exactly.** |
| **ABSENCE-2** | **L75-77** | *"**Thesis.** Every 'a small encoder wins' result we were able to locate compares the encoder against a **prompted** LLM, never against a **fine-tuned** generative decider"* | **NO — hedge is too strong here.** The abstract's scope limit ("inside the target corpus") is dropped, so this reads as a claim about the literature. `REFS_VERIFIED.md` §1 / `UNSOURCED_RETAINED.md` U2: **the search protocol is not recorded anywhere** and UREFS's external search *failed* to upgrade the hedge. **Riskiest absence claim in the paper** because it is the Thesis sentence |
| **ABSENCE-3** | L123-129 | *"**No published measurement was found** of a small encoder beating a fine-tuned generative model on a typed single-label decision — verified-absent, and the second lane checked it explicitly."* | **As a quotation of §11.6: yes** (`REFERENCES.bib:111-116`). As a claim: a reader can check only that §11.6 says it, and §11.6 is in a repository that §7:763 states is **not released**. "the second lane" is unattested |
| **ABSENCE-4** | L133-136 | *"**Nobody has published the comparison we need**, so our 190-case fixture remains the load-bearing evidence."* | quoted from a **commit message** (`ad301ae`) that is not released and not reproduced in any shipped file. Unhedged inside the quotation |
| **ABSENCE-5** | L659-660 | *"**No external typed-decision benchmark was used, and none was found in the corpus to use.**"* | no inventory, no search record; only the authors can witness "none was found in the corpus" |
| **ABSENCE-6** | L209-215 | *"its quantitative baseline tables contain only four cross-encoder/NLI models … no generative LLM … has any numeric row, GPT-4o appears only as a training-data annotator, and its LLM comparison is **qualitative prose**."* | **YES** — `REFERENCES.bib:206-214` records the four model names and the table numbers from the fetched HTML. Checkable by a reader at `arxiv.org/html/2508.07662v1`. Correctly labelled "an argument from absence" |
| **ABSENCE-7** | L207-208 | *"What GLiNER2's abstract does not state is whether its 'LLM-based alternatives' comparison class is prompted or fine-tuned; we do not read it either way."* | **YES** — scoped to the abstract, and `REFERENCES.bib:190-192` records the same non-determinacy |
| **ABSENCE-8** | L673-674 | *"UREFS's external search then **failed to upgrade the hedge**: no survey or recorded search protocol establishing the absence was located, so the weaker phrasing stays."* | **YES** — `REFS_VERIFIED.md` §1 lists the two queries run and `UNSOURCED_RETAINED.md` U2 lists the confirmed failure and the "what would close U2" condition. Checkable only in unreleased side files |
| **ABSENCE-9** | L695-696 | *"a trained linear probe on a frozen LLM embedding — was not run and is **not** present anywhere in the evidence tree"* | **YES** — `UNSOURCED_RETAINED.md` U6 records it as an open decision in `OPEN_QUESTIONS.md` |
| **ABSENCE-10** | L147, L152-153 | *"The corpus records **no title, authors or venue**; we cite the identifier only"* / *"Again: identifier only, no title/authors/venue in the corpus."* | **True of the corpus record** (`REFERENCES.bib:6-8`) **but now reads as stale** — L859-863 says those same entries "have since been completed from the arXiv abstract pages … which supplied title and authors for each". A reader meets both statements 700 lines apart |

---

# WHAT AN AUTHOR SHOULD DO ABOUT THIS — shortest path first

1. **Add `\cite` keys to `main.tex` and make the 13 `\bibitem`s reachable.** Until then, "cited",
   "uncited" and "unresolved" are all manual judgements and no referee will check the paper charitably.
   This one change converts §0.1 from a defect into a non-issue. *(≈30 min; blocks every other check.)*
2. **Delete or re-attribute the three `arXiv 2512.12677` numbers (L150-152).** `93.45 / 1.88 / 1.26`
   samples-per-second, "ModernBERT-base" by name, and the "≥ 97 % of teacher F1 at ~45× throughput"
   distillation result are **not in the source** — I checked. `REFERENCES.bib:62-68` already said so. This
   is the one place where the paper currently attributes numbers to a work that does not print them.
3. **Stop calling `arXiv 2602.06370` "the N-dependent crossover table" (L64-65, L146).** The source has no
   N analysis and reports encoders as often superior. Carry `REFERENCES.bib:49-50`'s caveat into the
   manuscript, or move the crossover framing wholly onto the internal errata (`ad301ae` §11.6), where it
   actually comes from. *(Same paragraph, same edit.)*
4. **Fix "N = 2–8 named options" → "N = 2–5"** at **L84, L171, L242-243, L714.** §3.1's own K
   distribution (33+27+76+54 = 190 cases, max K = 5) refutes it, and the phrase is the paper's stated
   novelty boundary. This is an internal contradiction a referee will find in one pass.
5. **Split the GCD bullet (L157-158)** into Geng et al. (EMNLP 2023) and **Raspanti, Ozcelebi &
   Holenderski, ACL 2025 Industry, pp. 485–499, DOI `10.18653/v1/2025.acl-industry.34`** — the second
   currently has no entry at all and is the paper's only unresolvable citation.
6. **Cite the four models the paper measures** (`UNCITED-7`): ModernBERT (Warner et al. 2024),
   DeBERTa-v3 (He et al. 2021), MPNet (Song et al. 2020), SetFit (Tunstall et al. 2022). A paper whose
   entire measurement is "these three checkpoints lose to a 4B" names none of them in the bibliography.
   Add the licence URLs for L837-841 at the same time.
7. **Cite the standard instruments once each** at first use: Cohen's κ (L378), McNemar (L410), ECE and
   temperature scaling (L482, L490), Brier (L282), MDE (L471) — `UNCITED-3/6/8/10/11`.
8. **Kill the word "published" for corpus-internal records** at L38, L39, L96, L315, L424, L499, L512,
   L663. Say "recorded in the corpus (`REPORT.md`)". A referee reading "the *published* 0.6684" will look
   for a publication and conclude the citation is missing.
9. **Strengthen the Thesis hedge (L75-77)** to match the Abstract's scope. "We were able to locate" is
   honest only while the search is scoped to the corpus; when it is unscoped it invites exactly the attack
   §6.4 concedes — the search protocol is unrecorded. Either add the scope words or move §6.4's
   qualification up to the Thesis.
10. **Resolve or label the anonymous instruments** (`UNCITED-9`, `UNRESOLVED-3/5/6`): `routeB-blind-model`,
    `mimo-v2.6-flash`, `imajev-4b`, `laya`, `laya-typed-decisions`, `DECIDER_TIER §2`, `CHECKLIST.md`. A
    reliability number produced by an unnamed model is not reproducible evidence.
11. **Reconcile the two homes of the 190 per-case rows** (`UNRESOLVED-8`, L314 vs L772) and add
    `CHECKLIST.md` + `DECIDER_TIER` to §7's inventory, or mark them unreleased.
12. **Fix the H4 wording** (`CLASS-A-2`, L496-498 vs L697-698): define H4 once, identically, in both
    places; as written §6.5 says H4 is "accuracy monotone in parameter count" is not supported while
    reporting that the observed ordering is monotone.
13. **Add a coverage/limit sentence to §2.2** — L196 says "three of them are now sourced" while L194 says
    "four near-misses" and only two of the four bullets carry external identifiers.

---

## Class-A findings that are not citation gaps but must not be lost

| id | line(s) | finding |
|---|---|---|
| **CLASS-A-1** | L84, L171, L242-243, L714 **vs** L257-258 | "N = 2–8 named options per case" contradicts the fixture's exhaustive `K = 2/3/4/5` distribution (33+27+76+54 = 190). Max arity is **5**. Also corroborated by §6.2's own strata ("2-option cases, n = 33" / "5-option cases, n = 54") |
| **CLASS-A-2** | L496-498 vs L697-698 | H4 is stated as "accuracy monotone in parameter count" in §6.5 and reported as observed/monotone in §4.7, yet both places say H4 is "not supported". §4.7's own gloss ("no size-crossover story within these heads") shows which proposition was meant |
| **CLASS-A-3** | L104-105 | the contribution list sends the reader to "§4.5" for the M12 correction, which is actually carried at **§4.2:429-444** |
| **CLASS-A-4** | L119-120, L146-153, L859-863 | "we cite the identifier only / no title, authors or venue" now sits in tension with the References paragraph that reports the entries having been completed from arXiv |
| **CLASS-A-5** | L35-38 vs §7:757 | the abstract's headline leak evidence (`0 of 152,000`, seeded `13/44/57`) rests on `lint-report.json`, which §7 states is **not** in the released subset |
| **CLASS-A-6** | L194-196 | "Four near-misses" / "three of them are now sourced" / only two bullets carry external identifiers |

---

## Method note and limits of this audit

- **Tool calls used: 17 of 30.** Primary verification was **4 web fetches** (arXiv 2512.12677 v3,
  arXiv 2602.06370 v1, the Simmering blog, the ACL Anthology page for `2025.acl-industry.34`). Every
  other external attribution is marked `SUPPORTED-BY-RECORD` (the corpus's own fetch record in
  `REFS_VERIFIED.md` / `REFERENCES.bib` notes) or `UNVERIFIED`. **I did not re-fetch** GLiNER, GLiClass,
  GLiNER2, Kostina, Li, Weller or Benayas; their support rests on records that name the fetched URL, the
  date (2026-10-15) and, for Benayas and GLiClass, the specific tables.
- **Not settled:** whether `arXiv 2512.12677`'s *body* (not abstract) prints the 93.45 / 1.88 / 1.26
  figures. The corpus's own bib note records a negative on the abstract and declares the figures
  UNVERIFIED; I did not fetch the 20-page PDF. Recorded as MIS-CITED-1 with that limit stated.
- **Not settled:** the §2.1 assertion that GLiNER's win is against *zero-shot* LLMs rests on the entry's
  note quoting the abstract; the manuscript's own "citation for the core literature claim" is an
  **unreleased internal document**, so no reader can audit it.
- The `papers/encoder-crossover-190/submission/main.tex` file was read only to count `\cite`/`\bibitem`
  and confirm the printed entries; no other file was modified.
