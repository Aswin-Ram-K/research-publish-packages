# MANUSCRIPT_CHANGES.md — UPAPER1c · what changed in `MANUSCRIPT.md`, sentence by sentence

**Unit:** UPAPER1c. **Date:** 2026-10-15. **Purpose:** apply unit UREFS's reference findings to the
manuscript — merge sources, narrow the novelty claim, add the counter-case weakness.
**Work order:** `REFS_VERIFIED.md`, `RELATED_WORK_NOTES.md`, `REFERENCES_ADDITIONS.bib` (all UREFS).
**Write paths touched by this unit:** `MANUSCRIPT.md`, `REFERENCES.bib`, `MANUSCRIPT_CHANGES.md`,
`UNSOURCED_RETAINED.md`, `orchestration/units/UPAPER1c.md`, `orchestration/handoffs/UPAPER1c.json`.
**Not touched (ULIC owns them):** `CHECKLIST.md`, `OPEN_QUESTIONS.md`, `LICENSE_ANALYSIS.md`.

## Headline counts

| what | count |
|---|---|
| references added to `REFERENCES.bib` | **7** (4 sourced: `simmering2025modernbert`, `zaratiana2024gliner`, `zaratiana2025gliner2`, `stepanov2025gliclass`; 3 marked `ADJACENT`: `kostina2025llmtextclassification`, `li2025smalllanguagemodels`, `weller2025seqvsseq`) |
| pre-existing bib entries preserved | **5 / 5** (unchanged) |
| novelty-claim edits (narrowing / priority-removing) | **8** (C1–C8 below) |
| counter-case engaged | **yes** (C6, C7) |
| weakness added to §6 | **yes** (new §6.6) |
| **existing numbers changed** | **0** — every fixture statistic is copied verbatim; see "Number audit" below |
| new external numbers introduced | 89.2 / 93.1 / 80.7 / 152 / 87 / 42 examples·s⁻¹, 395M vs 3B — all from the sourced blog post only |

---

## C1 — Abstract, first paragraph (novelty scoping)

**Driven by:** `RELATED_WORK_NOTES.md` §3.3 (novelty risk), `REFS_VERIFIED.md` §3.

- **From:** *"…(the claim and its audit trail are internal to the corpus, not an external survey — §2). We
  measure the fine-tuned comparison on a sealed typed-single-label decision fixture."*
- **To:** the same, plus — *"That a fine-tuned generative decider can beat a fine-tuned encoder at comparable
  effort is **already public** — a 2025 practitioner blog post reports exactly that on a binary ADE task
  (§2.1) — so we claim **no priority for the direction**; what we claim is this fixture, its controls and its
  diagnosis."*
- **Why:** the direction is already public (Simmering 2025). The abstract's existing hedge *"we were able to
  locate"* is **kept exactly** — UREFS could not upgrade the absence claim to a documented search
  (`REFS_VERIFIED.md` §1).

## C2 — §1, Thesis sentence (hedge tightened)

- **From:** *"**Thesis.** Every **published** "a small encoder wins" result compares the encoder against a
  **prompted** LLM…"*
- **To:** *"**Thesis.** Every "a small encoder wins" result **we were able to locate** compares the encoder
  against a **prompted** LLM… under the fine-tuned comparison the crossover does not appear **on our
  fixture**."*
- **Why:** matches the corpus hedge that must be retained (`REFS_VERIFIED.md` §1) and confines the claim to
  the fixture measured.

## C3 — §1, new paragraph **"Novelty, stated narrowly."** (inserted after Thesis)

**Driven by:** `RELATED_WORK_NOTES.md` §3.3; task item 2.

- **From:** nothing (paragraph absent).
- **To:** a new paragraph stating **no priority for the direction**, naming the public counter-case, and
  enumerating the three things the paper *does* claim: (i) the **sealed typed single-label decision fixture**
  (190 cases, N = 2–8 named options, 74 distinct labels) rather than binary classification; (ii) the
  **option-order permutation control** (final pass flips **0** for every candidate head); (iii) the
  **majority-class control** (0.4526 vs 0.3474, +0.1053) which the counter-case does not contain.
- **Why:** §1 previously implied the fine-tuned-vs-fine-tuned measurement was itself the novel object. It is
  not; the fixture and its controls are.

## C4 — §1, Contribution 1 (priority removed from the direction)

- **From:** *"…and 0.6684 (published, not re-scorable). §4.1–§4.2."*
- **To:** *"…and 0.6684 (published, not re-scorable). The *direction* is already public (§2.1); what is new is
  this fixture and its controls. §4.1–§4.2."*
- **Why:** same as C3. No number altered.

## C5 — §1, Contribution 2 (the claimed-novel control named)

- **From:** *"…"the encoder loses to a constant answer". §4.3."*
- **To:** *"…"the encoder loses to a constant answer". This control, the typed fixture and the
  order-permutation probe are the parts of the result for which we claim priority. §4.3."*
- **Why:** names the exact scope of the priority claim; +0.1053 unchanged.

## C6 — §2.1, the counter-case paragraph (replaces the "Unsourced in the corpus" paragraph)

**Driven by:** `REFS_VERIFIED.md` §3 (verbatim table), `RELATED_WORK_NOTES.md` §§1–2; task items 1 and 3.
**This is the largest edit.**

- **From (deleted in full):** the paragraph beginning *"**Unsourced in the corpus, and therefore not cited
  here.** `REFS.md` records four works the corpus rests on that have **no locatable identifier**: …"* — which
  named the counter-case as unsourced and said *"we name it here, we do **not** cite it, and we list it in
  `OPEN_QUESTIONS.md` as a reference a human must find."*

> **Note 2026-10-16 (UFIX34, measured by UVER34):** the block above is the 2026-10-15 record of the *deleted* text and is retained unchanged, byte for byte. Its recital ("unsourced … therefore not cited", "four works … no locatable identifier") is **superseded and no longer current**: the counter-case is now sourced and cited as a blog post (§2.1, §6.4), and the U1 125M-RoBERTa item was sourced and merged — see `UNSOURCED_RETAINED.md:18` and `submission/BUILD_NOTES.md:57`. This is a dated historical log, not shipped prose.
- **To:** a paragraph titled *"**The counter-case, now sourced — and what it does to our claim.**"* that:
  1. cites **Paul Simmering, "ModernBERT vs LLMs for Detecting Adverse Drug Reactions", 2025-01-12**,
     `https://simmering.dev/blog/modernbert-vs-llm/`, as a **blog post — no DOI, no venue, not
     peer-reviewed** (`simmering2025modernbert`);
  2. records its numbers exactly as UREFS observed them: fine-tuned Llama-3.2-3B-Instruct LoRA **F1 93.1 /
     152 ex·s⁻¹** vs ModernBERT-large **89.2 / 87 ex·s⁻¹**, equal per-arm effort (*"under one dollar and in
     less than 15 minutes"*);
  3. states **"We claim no priority for the direction of that result"**;
  4. differentiates the three setting differences (binary N = 2 sentences vs N = 2–8 typed options; 3B vs
     395M ≈7.6× scale confound, *"Did it win by sheer size?"*; the throughput edge is a serving-stack
     property — 42 ex·s⁻¹ once the 30 s vLLM preparation is counted, *"this speed comparison was not
     comprehensive"*);
  5. records that the same experiment **reproduces the manuscript's thesis** — its prompted DSPy arm scored
     **80.7** against ModernBERT-large's 89.2 (*"Fine-tuning continues to outperform purely prompt-based
     approaches, even when those are optimized using automated prompt engineering."*).
- **Why:** UREFS discharged Q5.3 (`REF`/`OPEN_QUESTIONS`), so the obsolete "a human must find it" sentence
  had to go. The counter-case corroborates the *artefact* thesis but refutes any priority claim for the
  *direction*.

## C7 — §2.1, new paragraph **"One item remains unsourced, and we do not cite it."**

**Driven by:** `REFS_VERIFIED.md` §2 (A3, NOT FOUND); task item 6.

- **From:** nothing (the item was inside the deleted C6 paragraph).
- **To:** the 125M-RoBERTa claim (**94.27 vs 70.87**, 77-class intent, 29–108×) recorded as still
  unsourced, with UREFS's search recorded (13 primary queries + a delegated ≥8-phrasing search, Semantic
  Scholar/OpenAlex lookups), the closest candidate (arXiv `2410.01627`) noted as *not* the source, and the
  decision stated: **dropped from the argument and not cited** (it is corroborating, not load-bearing).
- **Why:** task item 6 says drop it or attribute it internally and label it unsourced. **Dropped**, per
  UREFS's own recommendation. No fabricated citation was created.

## C8 — §2.2, GLiNER bullet corrected; GLiClass bullet added; ADJACENT paragraph added

**Driven by:** `REFS_VERIFIED.md` §§4–5; `REFERENCES_ADDITIONS.bib`; task items 4, 5, 7.

- **From:** the one-line bullet *"**Span extraction vs typed single-label decision.** GLiNER's recorded win is
  exact-match F1 on spans…"*, under the intro *"Three near-misses in the corpus…"*.
- **To:**
  - intro changed to *"Four near-misses… three of them are now sourced…"*;
  - **GLiNER bullet** now carries the identifiers (**arXiv `2311.08526`; NAACL 2024 pp. 5364–5376, DOI
    `10.18653/v1/2024.naacl-long.300`**) and states the corpus correction explicitly: the span-extraction
    characterisation is accurate for **GLiNER 2023/2024**, but the corpus applies it to
    `fastino/GLiNER2.5-Decide`, which is a **text-classification decision model** (**GLiNER2**, arXiv
    `2507.18546`); the paper rests the span point on GLiNER 2023/2024 and **not** on the decision-model
    variant, and does not read GLiNER2's "LLM-based alternatives" class as prompted or fine-tuned;
  - **new GLiClass bullet** (arXiv `2508.07662`, 11 Aug 2025) confirming *"no measured LLM head-to-head"* by
    the four cross-encoder/NLI baselines and the qualitative LLM table; phrased as an argument from absence;
  - **new ADJACENT paragraph** for arXiv `2501.08457` (prompted LLM arms), ACL 2025 Industry
    `2025.acl-industry.68` (prompting + SFT evaluation, per-task results not retrieved), and arXiv
    `2507.11412` (ICLR'26; *"a 400M encoder outperforms a 1B decoder on MNLI"*), each explicitly marked
    **ADJACENT** and none of them discharging §6.4's absence claim.
- **Why:** task item 4 (merge identifiers), item 5 (corpus correction), item 7 (keep the ADJACENT marking).

## C9 — §5.1, closing paragraph **"We claim no priority for the direction."**

**Driven by:** task item 2 (rewrite §1/§2/§5 sentences that imply priority for the direction).

- **From:** §5.1 ended at *"…which is exactly the inference the corpus's own errata says the literature does
  not license."*
- **To:** the same, plus a short paragraph: the direction is already public (§2.1, a non-peer-reviewed blog
  post); what the fixture contributes is the artefact diagnosis and the majority-class control (§5.2) — "neither
  of which the counter-case contains".
- **Why:** §5 is where the result is interpreted; a reader must not leave it thinking the direction is a
  contribution.

## C10 — §6.4 rewritten (heading + body)

**Driven by:** task item 6 (keep the hedge) and item 1 (counter-case is now sourced).

- **Heading — from:** *"6.4 The literature claim is an internal verified-absent audit, not an external
  survey"* **to:** *"6.4 The literature claim is an internal verified-absent audit; its counter-case is a
  sourced blog post"*.
- **Body — from:** the text stating four works have no locatable identifier and that the counter-case is
  therefore not cited.

> **Note 2026-10-16 (UFIX34, measured by UVER34):** this "From" record of the 2026-10-15 text is retained unchanged and is historical — it is **not** a live statement of fact. "Therefore not cited" is superseded: the counter-case (`simmering2025modernbert`) is now cited as a blog post and the four-works/no-identifier recital was resolved for U1 (`UNSOURCED_RETAINED.md:18`, `submission/BUILD_NOTES.md:57`).
- **Body — to:** the hedge is retained and its retention justified (*"UREFS's external search then **failed to
  upgrade the hedge**"*); the counter-case is cited as a **blog post, deliberately not dressed as a paper**,
  with its 93.1 vs 89.2 numbers and equal per-arm cost; **no priority** is claimed for the direction; the
  thesis is stated to rest on one data point plus the post's reproduction of the prompted half (80.7); and
  the 125M-RoBERTa figure is recorded as dropped and logged in `UNSOURCED_RETAINED.md`.

## C11 — §6, new subsection **6.6 "The counter-case asks whether our encoder arm is simply under-trained"**

**Driven by:** `RELATED_WORK_NOTES.md` §3.4; `REFS_VERIFIED.md` §3; task item 3. **Required addition.**

- **From:** nothing (subsection absent).
- **To:** the reviewer's objection quoted **in the reviewer's voice** — *"your best encoder head scores 0.3474
  and fails to beat a majority-class control at 0.4526, while a real ModernBERT-large reached **0.892 F1** in
  the counter-case. Is your encoder arm under-trained…?"* — answered honestly and in bounded steps:
  1. **0.892 is a different instrument** (binary N = 2 sentences vs N = 2–8 typed options; 74 labels, 51
     singletons; 0.2911 floor) and is not comparable in either direction;
  2. **what the majority-class control licenses** — only that no head is a viable default (+0.1053 on the
     same 190 cases and option orders) — and what it does **not** (it is not evidence the arm is well tuned,
     not a ceiling, not an architecture verdict);
  3. **what the paper does not establish about tuning effort** — no tuning-effort/compute study was run; the
     counter-case's equal-effort premise is *its* premise on *its* task; the ±1–2 point non-reproducibility
     band bounds single head numbers but is **not** evidence the recipe is adequate;
  4. **the reviewer's alternative reading stays open** — part of the 0.3316 could reflect the recipe; named as
     an open question in `UNSOURCED_RETAINED.md`;
  5. **what the claim is** — a **change of direction under fine-tuning** on one sealed fixture plus the
     prompted-baseline artefact diagnosis; not an encoder ceiling and not an equal-effort law.
- **Why:** this objection is now inevitable given a public 0.892 encoder result. It is written by the paper,
  not left for a referee, and the parts the evidence cannot answer are named rather than smoothed over.

## C12 — References section (bibliography description)

- **From:** *"Only sources with an identifier or location found in the corpus are cited… The four works the
  corpus rests on **without** any locatable identifier (the 125M-RoBERTa claim, the equal-effort
  counter-case, GLiNER, GLiClass) are **not** in the bibliography…"*
- **To:** the five pre-existing entries described unchanged; the four newly merged sourced entries named
  (`simmering2025modernbert` — blog post, not peer-reviewed; GLiNER `2311.08526`; GLiNER2 `2507.18546`;
  GLiClass `2508.07662`); the three **`ADJACENT`** entries named; and the 125M-RoBERTa item recorded as the
  **only** remaining uncited corpus work, logged in `UNSOURCED_RETAINED.md`.
- **Why:** the bibliography description had to stop saying the counter-case/GLiNER/GLiClass are absent.

---

## `REFERENCES.bib` merge detail

| action | entries |
|---|---|
| **preserved unchanged** | `arxiv2602_06370`, `arxiv2512_12677`, `pride2309_03882`, `gcd2305_13971`, `source_decider_stack_2026` |
| **added — sourced** | `simmering2025modernbert` (blog post; no DOI — cited as a blog), `zaratiana2024gliner` (arXiv 2311.08526; NAACL 2024; DOI 10.18653/v1/2024.naacl-long.300), `zaratiana2025gliner2` (arXiv 2507.18546), `stepanov2025gliclass` (arXiv 2508.07662) |
| **added — `ADJACENT` marking kept** | `kostina2025llmtextclassification` (arXiv 2501.08457), `li2025smalllanguagemodels` (ACL 2025 Industry; DOI 10.18653/v1/2025.acl-industry.68), `weller2025seqvsseq` (arXiv 2507.11412; ICLR'26) |
| **deliberately NOT added** | the 125M-RoBERTa claim (no source located); the literature-absence claim (no external backing located) |
| file header | updated: the old header said the counter-case/GLiNER/GLiClass were absent; it now documents the merge and what remains absent |

**Verified mechanical facts:** `REFERENCES.bib` has **12** `@`-entries, **12 unique keys**, and balanced
braces (122 `{` / 122 `}` outside comment lines). Style preserved (2-space indent, `archivePrefix`,
`eprint`, `note` carrying the verification status).

## Number audit — `numbers_changed = 0`

Every quantitative claim that existed before this unit is **byte-identical** afterwards. The strings below
were checked present, with the same values, after editing (occurrence counts in the edited manuscript):

`0.6789` (24), `0.6684` (22), `0.3474` (28), `0.4526` (13), `0.2316` (6), `0.2911` (9), `0.1053` (7),
`0.3316` (14), `0.3210` (10), `0.1595` (3), `4.167` (7), `0.6368` (2), `0.6650` (2).

These edits **added** only text and the counter-case's own published numbers (89.2 / 93.1 / 80.7 / 152 / 87 /
42, 395M, 3B, ≈7.6×), all traceable to `REFS_VERIFIED.md` §3 / `REFERENCES_ADDITIONS.bib`
(`simmering2025modernbert`) — the only source for them, and cited as a blog post. No fixture number was
recomputed, rounded, or re-attributed. The declared primary baseline (**0.6789**), the secondary/published
**0.6684**, the dropped latency claim (§6.1), the κ-is-not-IAA framing (§6.2), and the carried M12 correction
(§4.2/§5.3) are all **unchanged**.

**Sentence deliberately NOT imported (task item 1):** `DECIDER_STACK_DECISION.md` §11.2's salvage —
*"an encoder wins at equal **training budget** on closed label sets, and a fine-tuned generative model can
match or beat it at higher training cost"*. The counter-case refutes its second clause (≈8 min LoRA vs ≈3.5
min ModernBERT-large; *"the differences are negligible"*), so the sentence appears **nowhere** in
`MANUSCRIPT.md`. Grep confirms it is absent.
