# OPEN_QUESTIONS.md — human decisions owed before candidate #3 can be submitted

Unit **UPAPER1b**. Nothing below was decided by an agent. Each item names who can decide it and what
changes once it is decided.

---

## Q1. ✅ **DECIDED — primary `decider-4b` baseline = 0.6789 (same-run)** (author, 2026-10-15)

**No longer open.** The author declared **0.6789** primary, on exactly the grounds below: it is the **only
auditable** figure and **is** the paired McNemar partner. **0.6684 (historical/published)** is now reported as
a **secondary / robustness** figure tied to its pre-registration role, with its non-re-scorability stated
plainly. The former `[PENDING AUTHOR SIGN-OFF]` markers were **retired** from `MANUSCRIPT.md` and
`CHECKLIST.md`; the manuscript's title block now carries the dated declaration. The reasoning is kept here as
the recorded rationale.

- **Why 0.6789 (chosen):** per-case rows re-score exactly (`reproducesAt3dp = true`,
  `absoluteDifference = 4.7e−05`); same 190 cases and same option orders as the heads; the stricter bar.
- **Why 0.6684 was the alternative:** it is the **published** number and the number **F1 was pre-registered
  against** (`EXP#12-typed-channel-comparison.md:95`). Declaring a baseline after F1 fired is a
  pre-registration-integrity question.
- **Cost of 0.6684, now carried as a caveat rather than a choice:** `REPORT.md:189` — it **cannot be
  re-scored**; no per-case rows exist.
- **The conclusion does not change:** 0.3474 loses to both; −0.3316 > 2× either MDE.
- **Title figure — changed, flagged:** the working title's *"by 0.32"* (0.6684 arithmetic) became **"by 0.33"**
  (declared primary, 0.3316). This was an author-delegated call; revert it if the original number is wanted.

**Which sentences would change if the declaration were ever revisited** (0.6684 promoted; also listed in
`MANUSCRIPT.md` §3.3):

1. **Title** — currently "by 0.33" (declared primary, 0.3316); would revert to "by 0.32" (0.3210).
2. **Abstract, "Headline" sentence** — the clause naming 0.6789 as primary and 0.6684 as published.
3. **Abstract, "Against the *published* … 0.3210" sentence** — becomes the primary figure.
4. **§4.2 table caption** and the primary-baseline row.
5. **§4.2** sentence fixing Δ = −0.3316 to the same-run arm.
6. **§5.1 first paragraph** — which baseline the shortfall is measured against.
7. **§6.3** — the baseline choice belongs in the pre-registration story.

## Q2. ⚠ **Choose the paper's licence** (and resolve the AGPL-3.0 mismatch)

The supporting code and evidence tree are **AGPL-3.0**; the manuscript's licence is **unchosen**. Releasing
the paper under a permissive licence while it points at an AGPL-3.0 repository may be fine — AGPL covers
code, not prose — but it must be a **stated decision**, not a default. Related: confirm the right to publish
quotations and fixture excerpts with the source project's owner. (`CHECKLIST.md` §4.)

### Q2a. ✅ **DECIDED — licence = CC BY 4.0** (author, 2026-10-15) — *[added by ULIC, 2026-10-15]*

**OPEN PAPER + WITHHELD IMPLEMENTATION.** The paper is posted under **CC BY 4.0**; code, model weights and
data are **not released**. The full analysis — every licence option compared, the TMLR conflict, the
AGPL point, the O-1 impact — is [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md).

- **It is the only option compatible with TMLR.** TMLR's author guide, fetched 2026-10-15, verbatim: *"All
  TMLR submissions, from the time of submission to final publication, are licensed under CC BY 4.0. At all
  times, copyright is retained by the authors."* arXiv's licence page, same date, verbatim: *"The license
  chosen is irrevocable and cannot be changed."* → **a restrictive first posting cannot be undone**, so the
  licence is effectively chosen at *first* posting. `LICENSE_ANALYSIS.md` §1.4.
- **The AGPL-3.0 sub-question is closed, including the false alarm.** `the read-only target repository/LICENSE` is
  AGPL-3.0 and `CITATION.cff` names `the source repository's GitHub URL`, but that repository returns
  **HTTP 404** to an unauthenticated request (verified 2026-10-15, both the HTML and the API URL) and the
  author confirms it has been kept **private**. **AGPL has therefore triggered no obligation to the public.**
  `LICENSE_ANALYSIS.md` §1.6.
- **Still owed (see Q2b).**

### Q2b. ⚠ **OPEN and BLOCKING FOR SUBMISSION — the disclosure scope** — *[added by ULIC, 2026-10-15]*

The licence question is closed; **this is now the load-bearing decision**. "Code/weights/data withheld" is in
tension with the manuscript's own availability claims, which still promise that everything is *"re-derivable
from the target repository `the read-only target repository`"*. [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md) §8 lists the
**eleven disclosure items** (`MANUSCRIPT.md` §7 `:562–576`, Data and code availability `:604–608`, §3.1
`:177–195`, §3.2 `:202–225`, §2.2 `:160–164`) and separates the six that **conflict** from the five that are
merely *method*. Two decisions are owed:

1. **Reframe the availability/reproduction statements** — `MANUSCRIPT.md` `:606–608` is now factually wrong
   (*"the paper's own licence is a separate, deliberate choice that a human must still make"*). **ULIC did not
   edit `MANUSCRIPT.md`**; whichever unit owns it must.
2. **Decide whether to publish the minimal reproducibility subset** (the 190-case fixture + schema, the
   evaluation harness and exact commands, the pre-registration) as a **new, small public repository** —
   *without* opening the source repository. This is the only route that restores any **O-1A criterion 5** surface: the
   criterion (2 USCIS-PM M.4) names *"Contributions to repositories of software, data, designs, protocols, or
   other technical resources **with evidence of significant scientific, scholarly, or business-related impact
   in the field**"*, and **a private repository has zero impact evidence**. Withholding protects the
   implementation and forfeits the repository as criterion-5 evidence. The **authorship** criterion (B)(6) is
   unaffected — its own text says *"A petitioner need not provide evidence that the beneficiary's published
   work has been cited to meet this criterion"*, so the arXiv DOI carries it.
3. **Ancillary, from the same analysis:** the Zenodo code-DOI route is off the table as previously scoped
   (`https://help.zenodo.org/docs/github/`, fetched 2026-10-15 — releases are ingested from GitHub); the
   manual-upload alternative would *publish* the code; and the paper must never send reviewers to the 404ing
   `CITATION.cff` URL.

## Q3. **Choose the target workshop / venue**

`PAPER_CANDIDATES.md` §A3 records the strongest venue class as **workshop / short paper** — efficiency, model
selection, or decision routing. This decides the page budget, whether the current length (~6.6k words in
`MANUSCRIPT.md`) must be cut, and the deadline that the **arXiv endorsement** (Q6) has to precede.

## Q4. **Run the fourth arm, or state its absence?**

The obvious reviewer ask: **a trained linear probe on top of a frozen LLM embedding**. This unit searched
the five `eval-*.json` files and `analysis.json` and found **exactly five arms** — three candidates, two
controls — and **no embedding-probe arm**. Options: (a) run it and make it a §4 row; (b) leave §6.5 as
written, which states its absence explicitly. Note that whichever is chosen, the majority-class bar
(0.4526) is the number the new arm must clear.

## Q5. **Find the four unsourced references** (a human must locate these; do not fabricate)

`REFS.md` located identifiers for four external works and **could not** for these four. They are **not** in
`REFERENCES.bib`. Each must be found or the associated sentence softened/removed.

1. **The core literature claim's external backing.** `docs/DECIDER_STACK_DECISION.md` §11.6 and commit
   `ad301ae` state *"every public 'a small encoder wins' result compares the encoder against a prompted
   zero-/few-shot LLM … no published measurement was found of a small encoder beating a fine-tuned
   generative model on a typed single-label decision — verified-absent"*. **This supports the claim** — but
   **the search protocol is not recorded** (databases, query terms, dates, inclusion rules). A human must
   either produce the search record or a survey that establishes the same absence. Until then the paper says
   "we were able to locate", not "no such result exists".
2. **The 125M-RoBERTa-beats-fine-tuned-LLaMA2-7B claim** (94.27 vs 70.87 on 77-class intent, 29–108×
   faster). Quoted in the corpus, **no identifier anywhere**.
3. **The corpus's own honest counter-case** — equal fine-tuning effort + vLLM, Llama-3.2-3B-LoRA beating
   ModernBERT-large on **both** F1 (93.1 vs 89.2) and throughput (152 vs 87 ex/s) on ADE classification.
   **No identifier.** This is the strongest single threat to the thesis and the highest-priority find.
4. **GLiNER** / `fastino/GLiNER2.5-Decide` — a HuggingFace model id, **no publication located**; and
   **GLiClass** — **no identifier at all** (the corpus's claim about it is an argument from *absence*: its
   comparison table is qualitative).

Related but **not** for this paper: the four **sourced** external identifiers are identifier-only
(arXiv `2602.06370`, `2512.12677`, `2309.03882`, `2305.13971`). Their **titles and author lists are not in
the corpus** and were deliberately left blank in `REFERENCES.bib`; a human must complete those entries
(that is bibliography hygiene, not a sourcing gap).

## Q6. **arXiv endorsement + category confirmation**

arXiv **requires endorsement** for a first submission in this area. **`cs.LG` is the likely primary**, but
whether **`cs.LG` is its own endorsement domain is `UNVERIFIED`**, as is the cross-list proposal
(`cs.CL`, `cs.AI`). A human must confirm from the arXiv taxonomy. (`CHECKLIST.md` §3.)

## Q7. **Owe, or commission, an independent human labeller**

κ = 0.9014 is **machine reproducibility of the fixture**, not inter-annotator agreement — the second
labeller was a model (`routeB-blind-model`). A second distinct-model pass (`mimo-v2.6-flash`) returned no
file, so exactly one model pass exists. **An independent human labeller is still owed and
`PAPER_CANDIDATES.md` §F.3 is not discharged** (several candidate papers share this 190-case fixture). Either
run a human labeller, or keep §6.2 and accept that the claim stays explicitly fixture-bound.

---

## Decisions deliberately **not** taken by this unit

- The **paper's licence** (Q2) — a separate deliberate choice from the AGPL-3.0 code licence.
  - *[added by ULIC, 2026-10-15]* **Subsequently DECIDED by the author: CC BY 4.0** ("open paper + withheld
    implementation"). See **Q2a** above and [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md). The decision was not
    taken by an agent; it was relayed by the author. **Q2b (the disclosure scope) remains open and is
    blocking for submission.**
- Whether to run the **fourth arm** (Q4) — a resourcing decision.
- Whether to resolve the **ECE convention** (F3 fires on 0.0551, not on 0.1547) — the manuscript presents
  both and names the ambiguity rather than picking one.

**Subsequently decided by the author (2026-10-15):** the **primary baseline = 0.6789** (Q1). It was withheld
by instruction at the time of writing and is now closed.
