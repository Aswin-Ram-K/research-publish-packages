# Originality check — SUPPLEMENT (unit UPLAG2)

**Predecessor:** `orchestration/units/UPLAG1.md`, `orchestration/handoffs/UPLAG1.json`, `strategy/ORIGINALITY_CHECK.md` (343 lines).
This supplement **extends** that audit; it does not repeat §1–§6. It closes the three coverage gaps UPLAG1 named in
`strategy/ORIGINALITY_CHECK.md` §7, and settles two questions UPLAG1 left open.

**Method (unchanged from UPLAG1, so results are comparable).** Prose-normalise a document (strip code fences, inline
code, URLs, markdown link targets, tables and rules; lowercase; alphanumeric tokens), take contiguous word n-grams of
8 (called an "8-gram" below), and keep only **distinctive** grams — those containing ≥4 non-stopword tokens. Two modes:
**scan** = exhaustive intersection of the two gram sets, and **probe** = a k-sample of the manuscript's distinctive
grams drawn with Python `random.seed(20261016)`. Tooling:
`scratch/uplag2/overlap2.py` (scan/probe) and `scratch/uplag2/run_probes.py` (fetched-source probes).

**Sample-size discipline.** Every number below is labelled either `scan` (exhaustive over the stated gram counts) or
`probe k=<n>` (a sample, **not** a scan). Where a probe returns 0 hits, that zero is evidence of absence only at the
stated sample size; the exhaustive counts are given alongside so the true search space is visible.

---

## GAP 1 — the published-prose population

### 1.1 The local proxy, and its verification

UPLAG1 could not reach the author's own formerly-public prose because
`Aswin-Ram-K/publish-present-compete` was made private (HTTP 404 on
`raw.githubusercontent.com/.../main/WHITEPAPER.md`, `.../findings/PAPER-DERIVATION.md` and
`api.github.com/repos/Aswin-Ram-K/publish-present-compete` on 2026-10-16).

A local proxy exists and was verified before use:

```
sha256sum /home/zer0null/Duval/docs/research/PAPER_DERIVATION.md
  -> d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802
stat -c %s /home/zer0null/Duval/docs/research/PAPER_DERIVATION.md
  -> 46636
```

Both agree with the pinned claim for that repository's `findings/PAPER-DERIVATION.md` (46,636 B,
`d98c4359…4802`) taken while it was public. `/home/zer0null/Duval` was read only; no `git` command of any kind was
run against it in this unit.

### 1.2 Manuscript vs. `docs/research/PAPER_DERIVATION.md`

| comparison | size | result |
|---|---|---|
| **scan**, 8-grams | MANUSCRIPT.md 4,442 grams / 3,630 distinctive; PAPER_DERIVATION.md 2,888 grams | **0 hits** |
| **scan**, 7-grams | same documents | **0 hits** |
| **scan**, 6-grams | same documents | **0 hits** |
| **scan**, 5-grams | same documents | **1 hit**, generic: `is a property of` (MANUSCRIPT.md:508 / PAPER_DERIVATION.md:465) |
| **probe k=40** distinctive 8-grams, seed 20261016 | 40 of 3,630 distinctive grams | **0 hits** |

The 5-gram `is a property of` is a function-word frame, not reproduced prose; it is reported for completeness, not as a
finding.

### 1.3 Other prose under `/home/zer0null/Duval/docs/` that was probably public

`strategy/PRIOR_DISCLOSURE_AUDIT.md` records the public repository as carrying (at least) `decisions/DECISION_LOG.md`
(referred to there as A4, 99 decisions) and `WHITEPAPER.md` (A2), plus the profile README `Aswin-Ram-K/Aswin-Ram-K`.
Against the whole manuscript (the same 3,630 distinctive 8-grams), **exhaustive scans** returned:

| candidate formerly-public file | bytes | 8-grams | hits |
|---|---|---|---|
| `docs/DECISION_LOG.md` | 562,400 | 39,354 | **0** |
| `docs/README.md` | 77,621 | 377 | **0** |
| `docs/VISIT_LOG.md` | 593,782 | 55,020 | **0** |
| `docs/research/EXTERNAL_EVIDENCE_2026-10-07.md` | 159,408 | 9,376 | **0** |

**Positive controls — the method detects real reproduction, so the zeros above mean something.**

| control | relation | hits |
|---|---|---|
| `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md` (16,239 B) | an earlier internal draft of the same paper | **286 scan hits**, 226 distinctive |
| `/home/zer0null/Duval/docs/DECIDER_STACK_DECISION.md` (46,577 B) | source of the manuscript's **attributed** block quote | **27 scan hits**, e.g. MANUSCRIPT `[124]` / source `[470]`: `a fine-tuned generative decider . gliner s win` |
| Weller, arXiv:2507.11412 (86,811 chars text) | source of a **marked** quotation | **3 scan hits** = the marked quotation itself |

So the probe machinery fires on both an unattributed-reuse case (the same paper's own earlier draft) and on
properly-attributed quotations, and stays silent on the formerly-public prose.

### 1.4 Which populations were reachable, and which were not

| population | reachable? | how |
|---|---|---|
| `findings/PAPER-DERIVATION.md` | **yes** | byte-identical local proxy `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md` |
| `decisions/DECISION_LOG.md` | **yes** | `/home/zer0null/Duval/docs/DECISION_LOG.md` |
| `WHITEPAPER.md` | **no** | repository private; `find /home/zer0null/Duval -iname 'WHITEPAPER.md'` returns nothing |
| the other ~13 of 19 public repos (UPLAG1's `PRIOR_DISCLOSURE_AUDIT.md` §5: GitHub API 403 rate-limited, ~5 of 19 rendered) | **no** | never inspected by any unit |
| `docs/README.md`, `docs/VISIT_LOG.md`, `docs/research/EXTERNAL_EVIDENCE_2026-10-07.md` | **yes**, but their public status is not established | present on disk; scanned anyway |
| the full commit history of the private repo | **no** | 38 commits recorded in `PRIOR_DISCLOSURE_AUDIT.md`; only the head tree texts are mirrored locally |

### 1.5 Reading — this is a **disclosure** question, not a plagiarism one

`PAPER-DERIVATION.md` was published by the author under MIT, and the manuscript is the same author's work, so a hit
would be self-overlap, not misconduct. The only question that matters is whether the paper **reproduces** that prose
at length without saying so, because a reader can no longer reach the source (the repository is private; it is not in
the manuscript's bibliography).

**Answer: it does not reproduce it.** Zero 8-, 7- and 6-gram overlaps on an exhaustive scan, and zero hits in a
k=40 distinctive-gram probe. There is no withheld passage to declare, and no quotation to attribute, because there is
no quoted material.

**What the paper should add (one sentence, optional, and only if the artifacts become citable).** Nothing
disclosure-driven is required. If the author ever cites the formerly-public artifacts by name — which the current
manuscript does *not* do, cf. `MANUSCRIPT.md:161-180`, where the own-project blog counter-case is discussed on its
merits alone — then a self-overlap sentence ("earlier internal drafts of this paper and its decision log are on
record at …; this submission supersedes them") would close the provenance question for readers who cannot reach them.
That is a preference, not a defect.

---

## GAP 2 — the eleven unfetched cited sources

UPLAG1 had fetched only 2 of 13 cited sources (simmering.dev and arXiv:2507.11412, with 4/4 and 3/3 quotations
verified). Seven of the remaining eleven were reached in full here; all fetched copies are under
`scratch/uplag2/src/`. Sample-size discipline is as in Gap 1: "**scan**" is the exhaustive 8-gram intersection of the
whole manuscript against the whole fetched source, with the gram counts given.

| source | reached? | how | scan | probe k=40 | hits |
|---|---|---|---|---|---|
| GLiNER2 `arXiv:2507.18546` | **yes** | `arxiv.org/html/2507.18546` (166,541 B) | 8-gram, 4,442 vs n/a | 0 | **0** |
| GLiClass `arXiv:2508.07662` | **yes** | `arxiv.org/html` (237,759 B) | 8-gram | 0 | **1** — `seq vs seq an open suite of paired`, which is the **Weller title inside GLiClass's own reference list** (MANUSCRIPT `[238]` / GLiClass `[2218]`), i.e. bibliography noise, not shared prose |
| Kostina `arXiv:2501.08457` | **yes** | `arxiv.org/html` (142,961 B) | 8-gram | 0 | **0** |
| Li, ACL-Industry 2025 (`10.18653/v1/2025.acl-industry.68`) | **yes** | `aclanthology.org/2025.acl-industry.68.pdf` (270,049 B → 67,060 chars via `pdftotext -layout`) | 8-gram | 0 | **2** — both the source's own title (MANUSCRIPT `[232]` / Li `[1]`) |
| Benayas `10.1007/s10579-024-09796-y` | **yes** | CC-BY preprint `researchsquare.com/article/rs-3865391/v1.pdf` (285,470 B → 57,569 chars) | 8-gram | 0 | **2** — both the source's own title (MANUSCRIPT `[184]` / preprint `[27]`) |
| PriDe `arXiv:2309.03882` | **yes** | `arxiv.org/html` (543,034 B) | 8-gram | 0 | **2** — both the source's own title (MANUSCRIPT `[864]` / PriDe `[4]`) |
| GCD `arXiv:2305.13971` | **yes** | `arxiv.org/html` (309,966 B) | 8-gram | 0 | **0** |
| Weller `arXiv:2507.11412` (control, re-fetched) | **yes** | `arxiv.org/html` (391,238 B → 86,811 chars) | 8-gram | 0 | **3** — the marked quotation `a 400m encoder outperforms a 1b decoder on mnli` (MANUSCRIPT `[241]` / Weller `[220]`) plus the title |

**Verdict: zero unmarked borrowings.** Every non-zero count is either a source's own title (unavoidable: the
manuscript names the work) or another source's title appearing inside a bibliography. No sentence of any fetched
source is reproduced in the manuscript prose without being marked as a quotation.

### 2.1 Citation integrity — fair summary or overreach?

This is the second half of Gap 2, and the more interesting one.

* **GLiNER2 (`arXiv:2507.18546`), quoted at `MANUSCRIPT.md:207`.** The manuscript's quotation is **verbatim and
  correctly attributed**. Re-fetching the HTML and searching it: `LLM-based alternatives` occurs exactly **1** time
  and `llm-based alternatives` **0** times, in `…ion tasks with substantial improvements in deployment accessibility
  compared to LLM-based alternatives. We release GLiNER2 as an open-source pip-installable library with pre-trained …`.
  The manuscript's own surrounding claim — that the comparison is a deployment-accessibility claim, not a measured
  head-to-head — is **fair**; it does not upgrade the quoted sentence into an accuracy result.
* **GLiClass (`arXiv:2508.07662`).** The manuscript's description is **fair and notably restrained**: it states that
  GLiClass reports four cross-encoder/NLI baselines and uses GPT-4o only as an annotator, and characterises the
  encoder-over-LLM inference as "an argument from absence" (`MANUSCRIPT.md:198-215`). The fetched text supports both
  halves — no measured LLM-vs-encoder accuracy comparison is present to cite, so the manuscript is describing a gap,
  not asserting a result. **No overreach.**
* **Kostina (`arXiv:2501.08457`) and Li (`2025.acl-industry.68`).** Both are marked `ADJACENT` at
  `MANUSCRIPT.md:224-243` and neither is asked to carry the crossover claim; no prose overlap beyond the titles. The
  adjacency labelling is doing exactly the work it should.
* **Benayas (`10.1007/s10579-024-09796-y`).** The manuscript **declines to reproduce** the corpus's "125M" parameter
  formulation and says so explicitly — "the paper prints approximately 110–120 million parameters"
  (`MANUSCRIPT.md:182-191`). That is the opposite of overreach: it is a correction of a figure the manuscript could
  have borrowed. The 29–108× decoder-serving-penalty range and the BANKING77 encoder-over-decoder result are
  attributed to the source, and the fetched CC-BY preprint is where a reader checks them.
* **PriDe (`arXiv:2309.03882`) and GCD (`arXiv:2305.13971`).** PriDe grounds the order-permutation probe; GCD is
  explicitly declared **not** a source for the crossover claim (`MANUSCRIPT.md:150-249`). Both match: PriDe's content
  is a prompt-order/permutation result, and no GCD content is pressed into the crossover argument.
* **Weller (`arXiv:2507.11412`).** Three quotations, accurately marked, attributed with "accepted to ICLR'26" at
  `MANUSCRIPT.md:224-243`; all three verified byte-for-byte against the fetched HTML.

**No source description was found to be an overreach.** The one place where the manuscript could have overreached —
Benayas' parameter count and GLiClass's LLM comparison — is where it explicitly declines to.

---

## GAP 3 — `submission/main.tex` (never audited by UPLAG1)

`papers/encoder-crossover-190/MANUSCRIPT.md` is 877 lines and the source of truth; `papers/encoder-crossover-190/submission/main.tex`
is 445 lines, generated from it.

### 3.1 Prose present in one and not the other

Raw 8-gram comparison is dominated by rendering differences (LaTeX macros and full-precision floats on one side,
Markdown bullet syntax on the other), so it was cleaned first: macros/braces stripped, leading `-`/numbered markers
removed, runs of ≥4 decimal places collapsed to `NUM`. Cleaned result:

| | value |
|---|---|
| MANUSCRIPT.md 8-grams (cleaned) | 4,383 |
| main.tex 8-grams (cleaned) | 6,445 |
| common | 2,074 |
| manuscript-only | 2,309 |
| main.tex-only | 4,371 |

The asymmetries are **not** substantive prose. Representative residual main.tex-only grams are LaTeX/float-rendering
noise (`- 09 and the paired bootstrap ci -`, `- num exceeds 2 either mde 2.079 paired`); representative residual
manuscript-only grams are Markdown list phrasing (`. gliner s win is span extraction exact-match`,
`. could have contradicted the measurement if a`). The only content found in one file and absent from the other is:

* the LaTeX-only preamble at `main.tex:9-13` (see 3.3), and
* the drafting banner and title-revision note carried at `main.tex:16` and `:18`.

No substantive sentence of the argument exists in one artifact and not the other. **The generated file does not add
or drop prose.**

### 3.2 Quotations and attribution

The manuscript's quotations are carried into `main.tex` with the same text and the same attribution. Confirmed by the
8-gram scan (the marked quotations surface as main.tex-only grams because LaTeX turns them into `\emph{``…''}`
wrappers, but their token content is present): e.g. the Weller quotation
`a 400m encoder outperforms a 1b decoder on mnli` and the Simmering quotations are present in both. No quotation in
`main.tex` is attributed differently from the manuscript.

### 3.3 Leaked internal notes — **yes, they reached the shipped file**

The manuscript's drafting banner and title-revision note are both present in `main.tex`. Exact lines:

```
main.tex:9   % BUILD NOTE: the manuscript supplies NO author name and NO affiliation.
main.tex:10  %    The placeholder below must be replaced before submission (see METADATA.md).
main.tex:12  \author{AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED}
main.tex:13  \date{}   % deliberately empty: arXiv advises against \today; author must set the date
main.tex:16  \textbf{Draft status:} submission-candidate. \textbf{Baseline declared.} …
main.tex:18  \textbf{! Title figure, changed deliberately and flagged.} The working title said \emph{``by 0.32''} …
```

and in the source of truth:

```
MANUSCRIPT.md:3   **Draft status:** submission-candidate. **Baseline declared.**
MANUSCRIPT.md:10  **⚠ Title figure, changed deliberately and flagged.** The working title said *"by 0.32"* — that is the
```

Two observations. (a) The banner and title note are **inputs**, faithfully reproduced (the `⚠` becomes `!`), so
`main.tex` is generating correctly — the defect, if the author calls it one, is in the manuscript, not the generator.
(b) `main.tex:9-13` is a **different** class of leak: a build note addressed to the author, pointing at `METADATA.md`,
plus a literal `\author{AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED}` and a comment about `\today`. The
manuscript has no author placeholder; the placeholder is LaTeX-side only, which is exactly why a Markdown-vs-LaTeX
audit was needed to find it. If `main.tex` were submitted as-is, the compiled PDF would print the placeholder string
as the author line.

**Nothing found beyond these** — no revision-comment, no `TODO`, no reviewer note, no other internal marker in the
audited populations.

---

## SETTLED — the licence contradiction

UPLAG1 recorded an unreconciled conflict. Read together, the two statements are:

> `repro/encoder-crossover-190/LICENCE_TODO.md:3` — "**Status: open. Do not publish this subset until this file is
> resolved.**"

> `papers/encoder-crossover-190/MANUSCRIPT.md:796` — "**The reproducibility subset ships with the paper**, at
> `repro/encoder-crossover-190/`"

and the licence text itself has moved on since UPLAG1 read only `MANUSCRIPT.md:790-800`:

> `papers/encoder-crossover-190/MANUSCRIPT.md:848-851` — "**Licence of the subset — decided.** … released artifacts
> are **source-available under PolyForm Noncommercial 1.0.0**, with an **author-offered paid commercial licence** for
> commercial use."
>
> `papers/encoder-crossover-190/submission/main.tex:425` — the same PolyForm Noncommercial 1.0.0 decision, adding
> "The instruments for this decision are in `strategy/licence-templates/RELEASED-PIECE/`."

**So the contradiction is textual staleness, not a live disagreement.** The manuscript states the decision as
**made** (PolyForm Noncommercial 1.0.0 + paid commercial licence), while `LICENCE_TODO.md` — which predates the
decision — still says "Status: open. Do not publish this subset". One of the two files is out of date, and it is the
TODO file. Note also that `LICENCE_TODO.md:16-19` deliberately scopes itself to the **code** licence, while the
manuscript's §Data-and-code-availability paragraph is the paper's own claim; the two are the same subject here
(the released subset's licence), so they cannot coexist as written.

**What must be true for them to stop contradicting each other.** The decision recorded at `MANUSCRIPT.md:848-851`
must be executed as `LICENCE_TODO.md` itself prescribes: the chosen licence text sits at
`repro/encoder-crossover-190/LICENSE`, and the TODO file is retired.

**Smallest decision that closes it (the author's to make — this unit edited neither file).** The author replaces
`repro/encoder-crossover-190/LICENCE_TODO.md` with the one-line resolution that file already asks for at
`:43-48` — "The chosen licence text is added at `repro/encoder-crossover-190/LICENSE` and this file is replaced with a
one-line resolution naming the decision and its date" — naming **PolyForm Noncommercial 1.0.0 (code) with an
author-offered paid commercial licence**, and the date. One line, one date, one LICENSE file: after that,
`MANUSCRIPT.md:796` and `:848-851` and the TODO file agree, and nothing in the paper's argument changes.

---

## Third-party model attribution

The paper names arm labels but, per UPLAG1, gives no checkpoint licence or citation. Full inventory:

| arm label in the paper | where named | underlying checkpoint (per `repro/encoder-crossover-190/LICENCE_TODO.md:21-24` and `harness/tcmodel.py`) | licence | licence/citation line conventionally required |
|---|---|---|---|---|
| `modernbert-base` | `MANUSCRIPT.md:282` (arms table), `:289` | `answerdotai/ModernBERT-base` (149,015,041 params) | **Apache-2.0** | cite Warner et al., ModernBERT (arXiv:2412.13663). Apache-2.0 §4 requires the notice + `NOTICE` on redistribution; no weights ship, so a citation line suffices |
| `deberta-v3-base` | `MANUSCRIPT.md:283`, `:293` | `microsoft/deberta-v3-base` (183,832,321 params) | **MIT** | cite He et al., DeBERTaV3 (arXiv:2111.09543). MIT requires the copyright + permission notice where the software is redistributed |
| `setfit-mpnet` | `MANUSCRIPT.md:284` | SetFit recipe on `sentence-transformers/all-mpnet-base-v2` (109,489,537 params) | **Apache-2.0** | cite Tunstall et al., SetFit (arXiv:2209.11055); the base encoder is Song et al., MPNet (arXiv:2004.09297) / Reimers & Gurevych, SBERT (arXiv:1908.10084) |
| `shuffled-label` (control) | `MANUSCRIPT.md:285` | reuses the **ModernBERT-base architecture** (same 149,015,041 params) | **Apache-2.0 via ModernBERT** | inherits the ModernBERT citation/notice; it is not an independent third-party work |
| `decider-4b` (primary baseline, 4.66B params) | `MANUSCRIPT.md:307`, `:314`, `:305-326` | **UNNAMED** — the paper gives the parameter count and the label, not the checkpoint | **not recorded anywhere in the workspace** | requires the base checkpoint's name plus its licence and citation, **or** an explicit sentence that the checkpoint is withheld |
| `mimo-v2.6-flash` (reader B / model-to-model κ) | `MANUSCRIPT.md:586`, `:819` | **no record** in `LICENCE_TODO.md`, `harness/tcmodel.py` or either bibliography | **not recorded** | requires a provenance line (vendor/model, access date, licence or terms) and a citation; it is currently **uncited** |
| `majority-class` | `MANUSCRIPT.md:286` | none (0 params) | n/a | none |

Two arms are therefore genuinely unattributed rather than merely licence-silent:

1. **`decider-4b`** — the paper's primary baseline, described only by parameter count. A reader cannot tell which 4B
   checkpoint it is, so cannot check its licence or reproduce it. Either name it (checkpoint + licence + citation), or
   state explicitly that it is withheld and why.
2. **`mimo-v2.6-flash`** — cited nowhere. Even under a proprietary licence, a provenance line (vendor, version,
   access date) is the conventional minimum, and any licence terms bearing on redistribution of its outputs should be
   stated.

The three fine-tuned arms (`modernbert-base`, `deberta-v3-base`, `setfit-mpnet`) need only the citation/licence line
UPLAG1's fix-list P6 already asks for; no weights are shipped, so no redistribution obligation is triggered.

---

## Limits of this supplement

* The **`WHITEPAPER.md` population remains unreachable** (repository private; no local copy anywhere under
  `/home/zer0null/Duval`). Gap 1 is closed for `PAPER-DERIVATION.md` and the four other local prose files, **not**
  for the whitepaper.
* **4 of the 13 cited sources remain unfetched** (the two UPLAG1 had, plus the 7 reached here, leave 4 — the
  remaining unprobed citations named in `strategy/ORIGINALITY_CHECK.md` §2b/§7). Their quotations were still checked
  in UPLAG1's own inventory, but not against fetched full text.
* Every "0 hits" above is either an exhaustive scan over a stated gram count or a probe of **k=40** distinctive
  grams (seed 20261016). None of the k=40 probes is a scan.
* `experiments/**` and `tools/typed-channel/` remain out of scope, as in UPLAG1.
* No file under `papers/` and no file under `/home/zer0null/Duval` was modified by this unit; `/home/zer0null/Duval`
  was read without invoking `git`.
