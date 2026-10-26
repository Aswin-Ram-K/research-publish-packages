# ORIGINALITY_CHECK — quotation, attribution and idea-origin audit

**Unit:** UPLAG1. **Audited target:** `papers/encoder-crossover-190/MANUSCRIPT.md` (877 lines, source of
truth; rendered form `papers/encoder-crossover-190/submission/main.tex` was **not** inspected).
**Bibliographies:** `papers/encoder-crossover-190/REFERENCES.bib` (13 `@` entries) and
`papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib` (8 entries).
**Mode:** read-only. No file under audit was edited. All findings are reports, not repairs.

**Headline.** Every verbatim quotation I could put my hands on is **accurate and attributed** (7/7 tested
against their sources; §1). The defects are **not** in the quotations — they are in **idea attribution**:
the paper uses **Cohen's κ**, **McNemar's test**, a **bootstrap CI**, **ECE** and a **Brier score** as bare
instrument names with **no originator cited anywhere in the paper or the bibliography** (§3). That is the
class of problem the author named, and it is fixable with five bibliography entries and five clauses.

---

## 1. Quotation inventory

Every block quote, quoted span and quoted phrase found by grep over `^>` lines, `"`/`'` quoted spans,
and `*"…"*` italic-quoted spans. "Marked" = the text is visibly presented as a quotation (quotation marks
or an italic block quote **and** a lead-in verb such as "Verbatim from", "states", "quotes").

| line | quoted text (abbreviated) | marked as quotation? | attributed to a named source? | source present? |
|---|---|---|---|---|
| `MANUSCRIPT.md:123-129` | "Every public 'a small encoder wins' result compares the encoder against a **prompted, zero- or few-shot LLM** …" | **yes** — italic block quote, lead-in "Verbatim from §11.6:" | **yes** — `docs/DECIDER_STACK_DECISION.md` §11.6, commit `ad301ae` | **yes** — `REFERENCES.bib:105` `@misc` titled `DECIDER_STACK_DECISION.md §11.6` |
| `MANUSCRIPT.md:133-136` | "A second independent typed-channel lane ran with a stricter evidence base. Every public 'small encoder wins' result compares the encoder against a PROMPTED zero/few-shot LLM …" | **yes** — italic block quote, lead-in "And from the commit message of `ad301ae`:" | **yes** — commit message, `ad301ae1a5472fa7bd27807fdc7bb15d35f81988` (named at `MANUSCRIPT.md:761`) | **yes** — internal commit, pinned by hash; no bib entry needed |
| `MANUSCRIPT.md:705-707` | "Your best encoder head scores 0.3474 and fails to beat a majority-class control at 0.4526 …" | **yes** — block quote, but it is a **constructed** objection, not a source; lead-in says "we write it here in their voice" | **n/a** — explicitly voiced as a hypothetical reviewer | **n/a** — correctly framed in the lead-in; see fix P5 |
| `MANUSCRIPT.md:68-69` | "the N-dependent crossover table in §11.2 is encoder-versus-**API LLM**, i.e. prompted." | yes | yes — `docs/DECIDER_STACK_DECISION.md` §11.6 | yes |
| `MANUSCRIPT.md:140` | "*we were able to locate*", "*no published measurement was found*" | yes | **n/a** — the paper's own hedging phrases | n/a |
| `MANUSCRIPT.md:10-12` | "*\"by 0.32\"*" (the working title) | yes | **n/a** — the paper's own earlier title | n/a |
| `MANUSCRIPT.md:163-164` | Paul Simmering, *"ModernBERT vs LLMs for Detecting Adverse Drug Reactions"* + URL | yes | **yes** — author, title, date, URL, no DOI/venue stated | **yes** — `REFERENCES.bib:127` `simmering2025modernbert` |
| `MANUSCRIPT.md:168` | "*All setups can be trained for under one dollar and in less than 15 minutes*" | yes | **yes** — Simmering blog (same sentence group) | **yes** |
| `MANUSCRIPT.md:173` | "*Did it win by sheer size?*" | yes | **yes** — "the author names himself" | **yes** |
| `MANUSCRIPT.md:175` | "*this speed comparison was not comprehensive*" | yes | **yes** — same source | **yes** |
| `MANUSCRIPT.md:177-178` | "*Fine-tuning continues to outperform purely prompt-based approaches, even when those are optimized using automated prompt engineering.*" | yes | **yes** — same source sentence group | **yes** |
| `MANUSCRIPT.md:190` | "approximately 110-120 million parameters" (contrasted with the corpus's "125M") | yes | **yes** — Benayas, Sicilia & Mora-Cantallops (2024) | **yes** — `REFERENCES.bib:284` `@article` `benayas2024comparative` |
| `MANUSCRIPT.md:207` | GLiNER2's *"LLM-based alternatives"* | yes | **yes** — "What GLiNER2's abstract does not state …" | **yes** — `zaratiana2025gliner2` (arXiv `2507.18546`) — **quote not independently re-fetched** (§7) |
| `MANUSCRIPT.md:239-241` | "*the same recipe for both encoder-only and decoder-only models*"; "*encoder-only models excel at classification and retrieval tasks*"; "*a 400M encoder outperforms a 1B decoder on MNLI*" | yes (3 spans) | **yes** — Weller et al. (2025), `weller2025seqvsseq` | **yes** — `REFERENCES.bib:257`; **all 3 verified verbatim** against arXiv `2507.11412` (§2) |
| `MANUSCRIPT.md:314` | "*\"cannot be re-scored. No per-case rows for that specific measurement are in the tree\"*" | yes | **yes** — `REPORT.md:189` | **yes** — internal record |
| `MANUSCRIPT.md:322` | "*\"encoder accuracy < 0.6684 (the best 4B)\"*" | yes | **yes** — `EXP#12-typed-channel-comparison.md:95` | **yes** — internal record |
| `MANUSCRIPT.md:424` | "*\"Every correction moved the affected arm DOWN.\"*" | yes | **yes** — `strategy/PAPER_CANDIDATES.md:269`, `experiments/LEARNINGS.md:281` | **yes** — internal records |
| `MANUSCRIPT.md:647-648` | "*\"**It is not IAA.** One pass is a model.\"*" | yes | **yes** — `experiments/second-labeller-190/EVIDENCE.md:309` | **yes** |
| `MANUSCRIPT.md:650` | "*\"one fixture flaw propagates into four papers\"*" | yes | **yes** — `PAPER_CANDIDATES.md` §F.3 | **yes** |
| `MANUSCRIPT.md:363-364` | rule text: "drop a row when it shares ≥ 2 distinct 8-grams with any single row of the other side" | yes | **n/a** — the paper's own instrument rule | n/a |

**Quoted code identifiers and field names.** Every backticked identifier in the manuscript is a path, key
or JSON pointer into the author's own evidence tree (`analysis.json .baselinesRescored[…]`,
`eval-*.json`, `fixtureReads = 1`, `docs/research/EXP#11-evidence/decider-rows.jsonl`, …). These are not
third-party expression and carry no attribution requirement. The **only** third-party identifiers quoted in
the manuscript are model ids used as *data* read out of another paper's tables — `deberta-v3-large-zeroshot-v2.0`,
`deberta-v3-base-zeroshot-v2.0`, `roberta-large-zeroshot-v2.0-c`, `comprehend_it-base`
(`MANUSCRIPT.md:210-211`) — and they are explicitly introduced as the contents of *"its quantitative
baseline tables"* (GLiClass), i.e. attributed to the source they were read from. **PASS.**

**Verdict on §1:** 0 unattributed quotations; 0 misquoted spans among the 7 tested verbatim. **1 cosmetic
defect** (P5): the `:705-707` block quote reads like a source quotation and is a constructed reviewer
voice; the lead-in mitigates it but an explicit "(constructed, not a quotation)" marker would remove the
ambiguity, because the same block-quote + italics formatting is used for real quotations three times in the
same paper.

---

## 2. Borrowed expression that is NOT marked as quotation

### 2a. Method and coverage

Prose 9-grams were extracted mechanically from `MANUSCRIPT.md` after stripping markdown emphasis, tables,
code fences and headings: **5,012 prose 9-grams, 4,984 unique, 4,973 "distinctive"** (≤ 6 stopwords).
Two populations were probed.

### 2b. Population 1 — the cited sources actually fetched (verbatim-quote test)

| source | what was fetched | result |
|---|---|---|
| `https://simmering.dev/blog/modernbert-vs-llm/` (Simmering, 12 Jan 2025) | 64,232 bytes | **4/4 quotations verified present verbatim** — "All setups can be trained for under one dollar and in less than 15 minutes"; "Did it win by sheer size?"; "this speed comparison was not comprehensive"; "Fine-tuning continues to outperform purely prompt-based approaches, even when those are optimized using automated prompt engineering." (One initial mismatch was an artefact of my own double-space normalisation, not of the manuscript.) |
| `https://arxiv.org/abs/2507.11412` (Weller et al., 2025) | 42,952 bytes | **3/3 quotations verified present verbatim** — "the same recipe for both encoder-only and decoder-only models"; "encoder-only models excel at classification and retrieval tasks"; "a 400M encoder outperforms a 1B decoder on MNLI". |

No passage of the manuscript *reproduces* these sources' prose without quotation. The manuscript's prose
around the quotations paraphrases and adds corrections of its own (e.g. the ADE task being binary N = 2, the
≈7.6× scale confound, the vLLM CUDA-graph caveat), which is the right shape.

**Population 1 coverage: 2 of the manuscript's 13 bibliographic sources were fetched. 11 were not** (GLiNER
2024, GLiNER2, GLiClass, PriDe, GCD, the two identifier-only arXiv entries `2602.06370`/`2512.12677`,
Kostina et al. 2025, Li et al. 2025, Benayas et al. 2024). This is a **sample of 2, not a scan**.

### 2c. Population 2 — the author's own earlier artifacts in this workspace

262 files (`papers/encoder-crossover-190/*.md`, `strategy/*.md`, `repro/encoder-crossover-190/**`,
`experiments/**/*.md`, `docs/*.md`; `MANUSCRIPT.md` excluded) were normalised and searched with **40
distinctive 9-grams sampled from the 4,973 available**. **11 probes hit (27.5 %)**, each in a
workspace-internal draft of the *same* paper or of its evidence dossier:

| `MANUSCRIPT.md` line | matching artifact | run |
|---|---|---|
| 24 | `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` | `task 2 1 so we claim no priority for` |
| 148 | `strategy/BIBLIOGRAPHY_REPAIR.md` | `side wins its latency spreads and its cost figures` |
| 233 | `papers/encoder-crossover-190/REFS_VERIFIED.md` | `industrial text classification acl 2025 industry track pp 971` |
| 485 | `papers/encoder-crossover-190/GAPS.md` | `on the stored confidence field 0 0994 0 1547` |
| 591 | `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md` | `0 90 while it still clears the band 1` |
| 611 | `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md` | `it is not one model s quirk the fixture` |
| 626 | `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md` | `a second catalogue of defects the honest reading is` |
| 767 | `papers/encoder-crossover-190/EVIDENCE_NOTES.md` | `167e 09 on those two files returns nothing the` |
| 796 | `strategy/PUBLIC_SCOPE_REDUCTION.md` | `subset ships with the paper at repro encoder crossover` |
| 820 | `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md` | `experiments second labeller 190 run2 json robustness md labelsb2` |
| 859 | `strategy/VERIFICATION_REPORT_33.md` | `been completed from the arxiv abstract pages unit ubib1` |

**Reading.** This is the author reusing the author's own text across drafts of one paper — not plagiarism
of others. It **is** the disclosure question the card names, and it has two parts:

1. **Are these artifacts published?** `strategy/PRIOR_DISCLOSURE_AUDIT.md` records *"Published artifacts |
   **none.** No DOI, no arXiv id, no proceedings entry anywhere in the corpus"* as **true for arXiv/DOI but
   false as to public disclosure**: the author's public GitHub repo **`Aswin-Ram-K/publish-present-compete`**
   (public, MIT, last commit 2026-10-10) carries `WHITEPAPER.md`, `findings/PAPER-DERIVATION.md` and
   `decisions/DECISION_LOG.md`. Whether *this paper's* prose overlaps that public prose is therefore a live
   question, and it is **not answered here** — see the unresolved row below.
2. **The specific hits above are all one-paper-internal** (numbers, evidence paths, limitation wording,
   contract-style phrasing about the licence and scope). A reader who finds both `MANUSCRIPT.md` and
   `LIMITATIONS_UPDATE.md` will find near-identical limitation clauses. That is a **self-overlap disclosure**
   item, not a third-party originality defect, and it is worth one sentence in the paper's data/availability
   section if any of those artifacts become citable artifacts.

**Unresolved:** an attempt to probe the published population directly
(`raw.githubusercontent.com/Aswin-Ram-K/publish-present-compete/main/WHITEPAPER.md` and
`…/findings/PAPER-DERIVATION.md`, plus `https://api.github.com/repos/Aswin-Ram-K/publish-present-compete`)
returned **HTTP 404 on 2026-10-16** for all three. The repo may have been renamed, made private, or deleted
since `PRIOR_DISCLOSURE_AUDIT.md` observed it. **I could not test the public-prose population; the 404 is
reported as observed, and no conclusion is drawn from it.**

---

## 3. Idea attribution — **the findings that matter**

For each of the paper's contributions, the question asked was: *if the procedure has a published origin,
does the manuscript name it?* Five named methods do **not**.

### 3.1 🔴 **Cohen's κ — used nine times, Cohen never named, no citation anywhere**

Used at `MANUSCRIPT.md:52-55`, `:380-382`, `:585-591`, `:631-634`, `:817-819`. Representative sentence
(`MANUSCRIPT.md:584-585`):

> "Reader B (`routeB-blind-model`) agrees with the fixture's hand-authored labels 0.9053 of the time, κ = 0.9014, with 18/190 disagreements."

The manuscript's own pre-registration **does** name it — `repro/encoder-crossover-190/second-labeller/PREREGISTRATION.md:110`:
*"**Cohen's kappa** between recorded labels and Route X labels, over the full label vocabulary"* — so the
name was known to the project and was **dropped from the paper**. `REFERENCES.bib` and
`REFERENCES_ADDITIONS.bib` contain **no** entry for Cohen and no entry whose title mentions agreement,
kappa or reliability. Conventional citation: **Cohen, J. (1960), "A coefficient of agreement for nominal
scales", *Educational and Psychological Measurement* 20(1):37–46.**

This is the sharpest instance of the author's stated worry: κ is the paper's *headline quantitative
protocol* (§5.2 of the abstract-level claim, §6.2) and it is presented as instrument rather than as a
borrowed statistic.

### 3.2 🔴 **McNemar's test — used four times, McNemar never named, no citation**

Used at `MANUSCRIPT.md:6` ("the paired McNemar partner"), `:30` ("with paired McNemar **b = 27, c = 90,
ψ = 0.616, Δ = −0.3316, exact"), `:314`, `:333`, and the results table `:410-411` ("McNemar discordant: b
(head-only correct) **27**"). Conventional citation: **McNemar, Q. (1947), "Note on the sampling error of
the difference between correlated proportions or percentages", *Psychometrika* 12(2):153–157.** The paper
reports an **exact two-sided p** (`:417`), which conventionally also cites the exact-binomial treatment
(e.g. the continuity-corrected vs exact distinction the paper itself discusses at `:419`, "continuity-corrected
χ² | 32.85") — at minimum McNemar (1947) plus one sentence stating that the exact version is the binomial
test on the discordant pair.

### 3.3 🔴 **Bootstrap confidence interval — no resampling reference, scheme unnamed**

`MANUSCRIPT.md:418`: "paired bootstrap 95 % CI of the difference | **[−0.4316, −0.2263]** (excludes 0)".
Conventional citation: **Efron, B. (1979), "Bootstrap methods: another look at the jackknife", *Annals of
Statistics* 7(1):1–26** (or Efron & Tibshirani 1993 for the percentile/BCa variants). The manuscript does
not say which resampling scheme was used or with how many resamples, so a reader cannot reproduce the
interval **and** cannot attribute it.

### 3.4 🔴 **ECE and Brier score — two metric names, neither defined nor sourced**

`MANUSCRIPT.md:280` table header: `| arm | role | params | accuracy | 95 % CI | ECE | Brier |`; §4.6
(`:479-493`) uses ECE as the deciding quantity of falsifier F3. "ECE" and "Brier" appear **only** as column
headers — no definition, no bin count, no citation. Conventional citations: **Guo, Pleiss, Sun & Weinberger
(2017), "On Calibration of Modern Neural Networks", ICML** (the ECE definition, including the number of
bins — the paper's F3 verdict hinges on it) and **Brier, G. W. (1950), "Verification of forecasts expressed
in terms of probability", *Monthly Weather Review* 78(1):1–3.**

### 3.5 🟠 **The per-arm 95 % CIs — method unnamed**

`MANUSCRIPT.md:280-286` gives `[0.2842, 0.4211]`, `[0.2789, 0.4211]`, `[0.2053, 0.3263]`, `[0.3842,
0.5263]`, `[0.1737, 0.2895]` with **no statement of the interval method**. Conventionally **Wilson (1927)**
or **Clopper & Pearson (1934)** for a binomial proportion; for n = 190 the choice is visible in the third
decimal, and the paper elsewhere demands exactly this kind of convention-naming (§4.6's "the convention must
be named wherever the claim appears"). Self-inconsistent, and cheap to fix.

### 3.6 🟠 **The MDE / power calculation is presented as a derivation with no source**

`MANUSCRIPT.md:416-417`: "**paired** MDE (the quoted figure) | **0.1595**"; `:470-472`:
"`unpaired/paired = sqrt((p₁(1−p₁)+p₂(1−p₂))/ψ) = 0.85×`". The paper corrects a convention claim about
paired-vs-unpaired MDE, which makes the *derivation* load-bearing. No reference for the power formula.
Conventional: a power-analysis reference for the two-proportion / paired-proportion case (standard texts;
for effect-size conventions, Cohen 1988).

### 3.7 🟠 **The F4 n-gram-overlap lint rule is presented as the paper's own instrument rule**

`MANUSCRIPT.md:363-364`: 'rule = "drop a row when it shares ≥ 2 distinct 8-grams with any single row of the
other side", applied **in both directions**, threshold 2'. The rule is the author's own parameterisation,
but the *genre* — n-gram-overlap benchmark-contamination detection — is a published convention (the 13-gram
overlap convention popularised by GPT-3, Brown et al. 2020; the contamination literature, e.g. Sainz et al.
2023). The manuscript frames the whole falsifier family as its own design (`:99` "This control, the typed
fixture and the order-permutation probe are the parts of the paper we claim"), which is legitimate for the
fixture and the control, but a one-line "in the style of the standard n-gram-overlap contamination check"
with a citation would remove the ambiguity.

### 3.8 ✅ **The one idea that IS attributed, and it is the main borrowed one**

`MANUSCRIPT.md:372`: "**Order-permutation probe.** A **PriDe-style** option-order probe." — and
`MANUSCRIPT.md:154-156` names **PriDe** (arXiv `2309.03882`, ICLR 2024) as the source of the
position/order-bias concern, with the citation landings in the corpus (`DECIDER_STACK_DECISION.md:415`,
`:500`). `REFERENCES.bib:71` carries the entry (`pride2309_03882`) and `:82` records that the manuscript's
"PriDe (option-ID token bias)" attribution was checked. **This is exactly the pattern the other five
methods need.**

### 3.9 Checked and found clean (no citation conventionally required)

- **Majority-class / constant-answer control** (`MANUSCRIPT.md:451-461`) and **shuffled-label control**
  (`:320-322`) — universal baseline practice, not a named method; the paper also credits the constant-answer
  framing to its own §1.2 reasoning. ✅
- **The fixture itself** (190 typed single-label cases, K = 2–8, 74 labels, drawn from the project's own
  `evals/fixtures/reflex-decisions.ts`) — the author's own instrument. ✅
- **The κ/agreement band ladder** (band 1 = κ ≥ 0.85, band 2 = 0.75 ≤ agreement < 0.90) — I looked for a
  published banding convention and found none matching; Landis & Koch (1977) band at 0.81 ("almost
  perfect"), which is *not* this ladder. It reads as the author's own pre-registered thresholds, which is
  fine — but because κ banding *is* conventionally attributed, one clause ("our thresholds, not a published
  scale") closes the question permanently.
- **Neutralisation / redaction** (`MANUSCRIPT.md:637`, one clause) — the author's own procedure, documented
  in `strategy/DTAG_NEUTRALISATION.md` / `strategy/NEUTRALIZATION_REPORT.md`; the attribution risk there is
  to the *sources of the redaction list*, not to the method, and that is a different unit's scope.
- **Pre-registration** (§3.4, §6.2) — the practice is named as the author's; no published protocol is
  borrowed.

---

## 4. Figure / table / licence reuse

- **No figure and no reproduced table exists in the manuscript.** Checked by reading every section header
  (`MANUSCRIPT.md:1-877`) and grepping for `reproduced|adapted from|reprinted|permission|Figure [0-9]`:
  **zero hits**. All three tables (`:280-286`, `:311-315`, `:330-335`, `:407-421`) are derived from the
  author's own `repro/encoder-crossover-190/results/*` records. **No reproduction permission is needed,
  and no third-party figure/table licence is engaged.**
- **Licences of the sources actually fetched:**
  - `simmering.dev` blog (`https://simmering.dev/blog/modernbert-vs-llm/`) — **no licence statement was
    found on the fetched page**; the manuscript takes only four short verbatim quotations with full
    attribution (author, title, date, URL). Quotation with attribution into a CC BY 4.0 paper is permitted
    by ordinary quotation/citation practice; **no table or figure is taken from it**, so no reproduction
    licence is needed. Recorded as: *licence unknown, quotation-only use, no reproduction.*
  - arXiv `2507.11412` (Weller et al.) — arXiv deposits carry the arXiv non-exclusive distribution licence
    (or the author's chosen CC licence, which varies per paper); the manuscript takes **three short
    verbatim quotations**, correctly attributed. **Quotation-only, permitted.** I did **not** check the
    per-paper CC selector on the abs page, so "CC BY" is **not** asserted for this source.
- **The paper's own licence is settled:** `MANUSCRIPT.md:792` — "**The paper is public, CC BY 4.0.**" Nothing
  in the borrowed material is incompatible with publishing under CC BY 4.0, because nothing is reproduced.

---

## 5. Third-party code, model and data names

| artefact named in the manuscript | where | third-party attribution / licence record | consistent? |
|---|---|---|---|
| `modernbert-base`, `ModernBERT-large` (answerdotai) | `:280`, `:289`, `:706` | `repro/encoder-crossover-190/LICENCE_TODO.md` + `harness/tcmodel.py`: `answerdotai/ModernBERT-base` **Apache-2.0**; no weights shipped | **partly** — the paper names the arm but quotes **no licence and no checkpoint citation**; see P6 |
| `deberta-v3-base` (microsoft) | `:281`, `:296` | `microsoft/deberta-v3-base` **MIT** | **partly** — same gap |
| `setfit-mpnet` | `:282` | `sentence-transformers/all-mpnet-base-v2` **Apache-2.0** | **partly** — same gap; note the paper's label `setfit-mpnet` compresses two third-party things (SetFit's training recipe *and* MPNet weights) into one arm name |
| `decider-4b` (4.66 B params) | `:307`, `:314` | **no record** — the base checkpoint is never named, and the harness is withheld (`:757`) | **incomplete** — not a misattribution, but the headline baseline is an unnamed third-party model |
| `mimo-v2.6-flash` (reader B2) | `:586`, `:819` | **no record**, not in either bibliography | **gap** — a third-party model used as a labelled reader, named once with no provenance beyond a source-tree path |
| GLiNER / GLiNER2 / GLiClass / PriDe / GCD / LLaMA-3.2-3B / Qwen3-4B / GPT-4o | §2.1–2.2 | `zaratiana2024gliner`, `zaratiana2025gliner2`, `stepanov2025gliclass`, `pride2309_03882`, GCD arXiv `2305.13971` + `2025.acl-industry.34` | ✅ named correctly and cited; **no artefact is passed off as the author's own** |
| the 190-case fixture and its content | §3.1 | drawn from the project's own `evals/fixtures/reflex-decisions.ts`; covered by the CC BY 4.0 paper decision per `LICENCE_TODO.md:14-16` | ✅ |
| harness code (`tools/typed-channel/`, 18 files) | §7 | **withheld**; recovered read-only from git blob `a5ef1b28…`; `INTEGRITY.md` records all 18 sha256s | ✅ consistent — the paper says it is withheld, and it says so plainly |

**Verdict:** nothing third-party is presented as the author's own. The defects are the reverse —
**under-attribution**: three released checkpoints and one named inference model carry licences the *subset*
records and the *paper* omits. `LICENCE_TODO.md` is the boundary case: it says **"Do not publish this subset
until this file is resolved"** (the *code* licence is open), while the paper's Data-availability section
(`:790-800`) describes the subset as shipping with the paper. The paper must not imply the subset is
publishable as-is while `LICENCE_TODO.md` says otherwise.

---

## 6. Prioritised fix list

| # | priority | fix | where |
|---|---|---|---|
| P1 | 🔴 **must** | Name **Cohen's κ** at first use and cite **Cohen (1960)**; add the bib entry. The repro artifact already names it (`second-labeller/PREREGISTRATION.md:110`), so this is a copy-back. | `MANUSCRIPT.md:52-55`, `:585`, bibliography |
| P2 | 🔴 **must** | Cite **McNemar (1947)** where "paired McNemar" first appears, and state that the "exact two-sided p" is the exact binomial version. | `MANUSCRIPT.md:30`, `:410-411` |
| P3 | 🔴 **must** | Cite **Efron (1979)** for the bootstrap CI and state the resampling scheme and resample count. | `MANUSCRIPT.md:418` |
| P4 | 🔴 **must** | Cite **Guo et al. (2017)** for ECE (with the bin count) and **Brier (1950)** for the Brier score; currently two unnamed column headers decide falsifier F3. | `MANUSCRIPT.md:280`, `:479-493` |
| P5 | 🟠 should | Mark the `:705-707` block quote explicitly as a constructed reviewer objection, not a quotation. | `MANUSCRIPT.md:700-707` |
| P6 | 🟠 should | State the checkpoint licences and cite the model releases (ModernBERT, DeBERTa-v3, SetFit/MPNet) in §3.2 or Data availability; carry the `harness/tcmodel.py` licence record into the paper. Reconcile the paper's "subset ships with the paper" with `LICENCE_TODO.md`'s **"Do not publish this subset until this file is resolved."** | `MANUSCRIPT.md:275-304`, `:790-800` |
| P7 | 🟠 should | Name the interval method for the per-arm 95 % CIs (Wilson or Clopper–Pearson) — the paper demands convention-naming of others but not of itself. | `MANUSCRIPT.md:280` |
| P8 | 🟡 nice | Cite the power-analysis source for the MDE formula, or show the derivation inline. | `MANUSCRIPT.md:469-478` |
| P9 | 🟡 nice | One clause noting the F4 n-gram rule is in the style of the standard n-gram-overlap contamination check. | `MANUSCRIPT.md:363-364` |
| P10 | 🟡 nice | One clause stating the 0.90/0.85 band ladder is the author's own pre-registered threshold, not a published scale. | `MANUSCRIPT.md:589-592` |
| P11 | 🟡 nice | Name the `decider-4b` base checkpoint (4.66 B params) or state plainly that it is unnamed because the harness is withheld; give `mimo-v2.6-flash` provenance. | `MANUSCRIPT.md:307`, `:586` |
| P12 | 🟡 nice | If any `papers/encoder-crossover-190/*.md` or `strategy/*.md` artifact becomes a citable release, disclose the self-overlap with `MANUSCRIPT.md` (11/40 probes hit). | Data availability |

**Repairs are not in scope for this unit** — nothing under audit was edited.

---

## 7. Limits of this check — what a reader must NOT conclude

**Populations actually searched**

1. `MANUSCRIPT.md` in full, mechanically (grep for block quotes, inline quoted spans, quoted identifiers)
   and by reading all 877 lines' headers plus the method, results, limitations and availability sections.
2. **Two of thirteen** cited sources, fetched and substring-tested: the Simmering blog (64,232 bytes) and
   arXiv `2507.11412` (42,952 bytes). **7 verbatim quotations tested, 7 confirmed accurate.**
3. **262 workspace files** of the author's own earlier artifacts, probed with **40 distinctive 9-grams
   sampled from 4,973 available**; 11 hits, all one-paper-internal drafts.
4. Three URLs of the author's public GitHub prose — **all HTTP 404, unresolved**.

**Probe counts:** 40 external-artifact probes, 7 source-quotation probes, 5,012 prose 9-grams extracted.

**What was NOT tested — do not read this document as a clean bill**

- **11 of 13 cited sources were not fetched**, including every non-open source (Kostina et al. 2025, Li et
  al. 2025, Benayas et al. 2024 are paywalled/DOI-only; the two identifier-only arXiv ids
  `2602.06370` / `2512.12677` have no title or authors in the corpus and were not located). **Unmarked
  paraphrase of those sources is untested.** `MANUSCRIPT.md:207`'s GLiNER2 quotation
  ("LLM-based alternatives") was **not** re-fetched.
- **40 probes over 4,973 available 9-grams is a 0.8 % sample.** A probe ratio above zero is a signal about
  *where* to look, not a scan. Nothing here licenses the sentence "no unmarked borrowing exists".
- **I did not search the open web or any plagiarism service** for the manuscript's prose. Parallel
  independent invention is not detection-relevant, but a single externally published source that matches
  the manuscript's prose would have been missed by every test above.
- **The published-prose population could not be read** (404). If `publish-present-compete` is public under
  another path or a rename, the self-overlap question in §2c(1) is open.
- **`submission/main.tex` was not audited.** The audit target is the Markdown source of truth; if `main.tex`
  carries material absent from `MANUSCRIPT.md` (a figure, an appendix, extra quotations), that material is
  outside this check.
- **The withdrawn/withheld material was not audited** — `experiments/**`, `harness/data/*` and the withheld
  `tools/typed-channel/` tree. Third-party text quoted only inside those is outside scope.
- **Reader B's own model is unnamed in the manuscript** (`routeB-blind-model`), so I cannot test whether its
  output or prompt text borrows from another work.

**Plain statement.** Tested: the manuscript's quotations against the two sources I could fetch (all
accurate, all attributed); its identifiers (all its own); its prose against its own earlier drafts (11/40
probes near-verbatim, same-paper self-reuse); its method names against their origins (five uncited:
Cohen's κ, McNemar, bootstrap, ECE, Brier — plus three methodology statements with no convention named).
Not tested: the other eleven sources, the open web, the public GitHub prose (404), and the rendered LaTeX.
