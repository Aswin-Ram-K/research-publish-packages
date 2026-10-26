# SUBMISSION_READINESS.md — the single decision document for `encoder-crossover-190`

**Unit:** UFMT2 · **Date:** 2026-10-16 · **Mode:** report only. **Nothing under `papers/` was edited by this unit.**
**Sources (quoted, not re-derived):** `strategy/FORMATTING_REQUIREMENTS.md` (UFMT1, 40 audited requirement
rows R1–R44, 33 URLs fetched 2026-10-16), `strategy/CITATION_SUPPORT_AUDIT.md` (UCITE1),
`strategy/CITATION_FETCH_VERIFICATION.md` (UCHECK1), `strategy/ORIGINALITY_CHECK.md` (UPLAG1),
`strategy/ORIGINALITY_CHECK_SUPPLEMENT.md` (UPLAG2), `strategy/STYLE_COMPLIANCE.md` (USTYLE1),
`strategy/ARXIV_SUBMISSION_PREP.md` (UPREP1), `strategy/BIBLIOGRAPHY_REPAIR.md` (UBIB1),
`papers/encoder-crossover-190/submission/METADATA.md`, `.../BUILD_NOTES.md`,
`repro/encoder-crossover-190/LICENCE_TODO.md`.

---

## 1. Verdict

**NO — the manuscript is not submittable today.** Three things make it not:

1. **It has no author.** Every author-side field is absent: `papers/encoder-crossover-190/submission/main.tex:12`
   still reads `\author{AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED}`, and
   `papers/encoder-crossover-190/submission/METADATA.md:12-14,16` record Authors, Affiliation, Author email and
   Date as **NOT SUPPLIED**. arXiv rejects anonymous submissions (R6); no venue accepts it.
2. **The arXiv cs.CL endorsement does not exist.** `METADATA.md:22` — *"required and absent — the author is not
   endorsed in any category (primary blocker)"*; `strategy/ARXIV_SUBMISSION_PREP.md:11-22` calls it a *"Hard
   blocker, personal, non-delegable"* requiring a **six-character alphanumeric endorsement code** from a personal
   endorser (R10). The automatic path does not fire.
3. **The bibliography is entirely uncited, and three draft-status paragraphs would ship in the PDF.**
   `main.tex` carries **13 `\bibitem`s and 0 `\cite` commands** (R18, `strategy/FORMATTING_REQUIREMENTS.md:572`;
   `strategy/CITATION_SUPPORT_AUDIT.md:33-53`), so the printed list is uncited in the LaTeX sense; and
   `main.tex:16-18` still prints *"Draft status: submission-candidate…"* and the title-revision note (R17).

Two further facts condition everything below: **no `main.pdf` exists and no TeX toolchain is installed here**
(`pdflatex`, `latexmk`, `tectonic`, `xelatex` all absent — `FORMATTING_REQUIREMENTS.md:549-550`), so no PDF was
ever built and every PDF-dependent requirement is unverified; and the shipped release still contains a file
forbidding publication, `repro/encoder-crossover-190/LICENCE_TODO.md:3` — *"Status: open. Do not publish this
subset until this file is resolved."*

---

## 2. Table A — what only the author can supply

| # | Item | Exact landing place | Req. ID |
|---|---|---|---|
| A1 | Real author name (no honorifics; "Firstname Lastname") | `papers/encoder-crossover-190/submission/main.tex:12` (`\author{…}`); also `submission/METADATA.md:12` | R6 |
| A2 | Affiliation — **city and country only**, inside parentheses; no street address, zip or postal code | `main.tex:12`; metadata form per `METADATA.md:13` | R7 |
| A3 | Author email (needed for the arXiv account **and** the endorsement request) | `submission/METADATA.md:14` | R6/R7 |
| A4 | Date (or a deliberate decision to keep `\date{}` empty) | `main.tex:13` `\date{}`; `submission/METADATA.md:16` | R15 (not stated) |
| A5 | **arXiv cs.CL endorsement — the six-character alphanumeric code** from a personal endorser | `submission/METADATA.md:22`; `strategy/ARXIV_SUBMISSION_PREP.md:11-22` | R10 |
| A6 | Zenodo **DOI** for the data-availability statement | `main.tex:405` `\section*{Data and code availability}` (currently states the licence + subset but cites no DOI) | R36 |
| A7 | Decision on arXiv's **licence menu** (CC BY 4.0 / CC BY-SA 4.0 / CC BY-NC-SA 4.0 / CC BY-NC-ND 4.0 / arXiv perpetual non-exclusive 1.0 / CC Zero) — irrevocable once chosen | `submission/METADATA.md:20` records CC BY 4.0; `strategy/FORMATTING_REQUIREMENTS.md:160-171` | R9 |
| A8 | `decider-4b` **base-checkpoint identity and licence** (4.66 B-param primary baseline; currently described only by parameter count) | `papers/encoder-crossover-190/MANUSCRIPT.md:307`, `:314` (arms/baselines); `:790-800` | R37 / UPLAG2 |
| A9 | `mimo-v2.6-flash` **provenance line** (vendor, version, access date, licence/terms) — reader B2, currently cited nowhere | `MANUSCRIPT.md:586`, `:819` | R43 / UPLAG2 |
| A10 | Keywords (first page must carry them) | first page of the Preprints.org rendering; `MANUSCRIPT.md` has no keyword field | R30 |
| A11 | `Comments` field — pages and figures count (needs the PDF; `METADATA.md:17` says **"NEEDS A NUMBER"**) | `submission/METADATA.md:17` | R6-adjacent |
| A12 | Who labelled the 190-case fixture, under what instruction, and whether it is human-subjects data (ethics/consent basis) — the paper gives only *"one worker"* | `MANUSCRIPT.md:272`, `:584`, `:657` | USTYLE1 CHECK 4 |
| A13 | Complete and active **OpenReview profiles** (affiliation, COI, publication history) for the TMLR route | OpenReview (TMLR); `strategy/FORMATTING_REQUIREMENTS.md:579` | R25 |

---

## 3. Table B — mechanical fixes, in fix order

| # | Fix | Exact landing place | Req. ID |
|---|---|---|---|
| B1 | **Cite the bibliography.** Add a `\cite{…}` at each of the 13 in-text mentions (or cite a subset and delete the rest). 0 `\cite` vs 13 `\bibitem` today. Highest-leverage single fix — it is upstream of every citation finding. | `main.tex` `thebibliography` (13 `\bibitem`; the five repaired ones at `:431-435`), and the 13 prose mentions | R18 |
| B2 | Delete (or move into `BUILD_NOTES.md`) the three front-matter draft-status paragraphs — *"Draft status: submission-candidate…"*, the baseline-declared line, and the `⚠ Title figure, changed deliberately and flagged` note | `main.tex:16-18` | R17 |
| B3 | Replace the author placeholder with the real name/affiliation (see A1–A3) | `main.tex:12` | R6/R7 |
| B4 | Paste **`ABSTRACT_METADATA.txt` (1,195 chars)** into the arXiv metadata abstract field; keep the full **`ABSTRACT.txt` (3,415 chars)** as the PDF abstract. The 1,920-char cap is live and enforced. | `submission/ABSTRACT_METADATA.txt` (field value); `submission/ABSTRACT.txt` (PDF); `submission/METADATA.md:46-49` still says *"NOT verified"* | R4 |
| B5 | Fix `ABSTRACT_METADATA.txt` factual errors: *"kappa 0.347"* → accuracy 0.3474 (κ is a different quantity); *"Five encoder-based arms"* → 3 heads + 2 controls (`majority-class` is a constant answer); 3-s.f. `0.679/0.668/0.105/4.2e-09` → 0.6789/0.6684/0.1053/4.167e-09 | `submission/ABSTRACT_METADATA.txt:1` | R4/R5 |
| B6 | Add a **compute/resources statement** (host, CPU/GPU, memory, wall-clock per arm) — none exists; `MANUSCRIPT.md:723` only says the paper *"reports no tuning-effort or compute study"* | `main.tex` availability/statements block at `:405-427`, before `\begin{thebibliography}` | R39 |
| B7 | Add **competing-interests** declaration (*"The authors declare no competing interests."*) — absent (grep `conflict of interest` = 0) | same block, `main.tex:405-427` | R40 |
| B8 | Add **funding** declaration (or state that no funding was received) — absent (grep `funding`/`grant` = 0) | same block | R41 |
| B9 | Add **author-contributions** statement (CRediT roles for Elsevier routes) — absent | same block | R42 |
| B10 | Add **AI/LLM-use disclosure** — absent for the paper/analysis (the model *labellers* are disclosed, but not AI assistance in producing the paper); and remove the leaked internal pipeline unit IDs `UBIB1`/`UPAPER1c`/`UMERGE1` (`UREFS` also at `:870`) from the reference prose | same block; unit IDs at `MANUSCRIPT.md:859`, `:868`, `:873` | R43 |
| B11 | Remove the *"the comparison class is a prompted API LLM"* stale/edge items only if B1 changes them: `main.tex:428` still says the 125M-RoBERTa 94.27-vs-70.87 claim is *"not in the bibliography"*, while `REFERENCES_ADDITIONS.bib:121-123` records it FOUND with the Benayas DOI | `main.tex:428` | UBIB1 §4.2 |
| B12 | Restore the dropped entry: `benayas2024comparative` is complete in `REFERENCES_ADDITIONS.bib:109-145` (*LREC*… *Language Resources and Evaluation* 59(3):2007–2030, DOI `10.1007/s10579-024-09796-y`) but absent from `REFERENCES.bib` and from `main.tex`'s `thebibliography`, despite `REFERENCES.bib:80-82` claiming the merge | `REFERENCES.bib`; `main.tex` `thebibliography` | UBIB1 §4.1 |
| B13 | **Tarball hygiene rule:** keep `ABSTRACT.txt`, `ABSTRACT_METADATA.txt`, `METADATA.md` and `BUILD_NOTES.md` out of every upload — arXiv publishes whatever is in the package, and these are author-side working files | upload payload only (`main.tex` / `encoder-crossover-190.tar.gz`); `FORMATTING_REQUIREMENTS.md:609-614`, `ARXIV_SUBMISSION_PREP.md:97-98` | R16 |
| B14 | Structural cosmetics: add captions + `Table N` references (5 tables are uncaptioned and unreferenced); retitle §6.3 (still *"…a baseline choice awaiting a human"* while the baseline is declared); remove literal `**not**` from the heading; replace the four `⚠` glyphs (they degrade to ASCII `!`) | `MANUSCRIPT.md:280-286`, `:312-315`, `:330-336`, `:405-418`, `:752-763`; `:655`; `:582` → `main.tex:317`; `MANUSCRIPT.md:10`, `:293`, `:474`, `:488` | USTYLE1 CHECK 5 |
| B15 | Refresh stale build/claim records: `BUILD_NOTES.md:8` says *"864 lines, 66,671 bytes, 9,781 words"* (actual 877 / 68,075) and *"12 bibliography entries"* (actual 13); `main.tex` size is 80,780 B, not 78,405 B | `submission/BUILD_NOTES.md:8` (and its inventory line) | USTYLE1 CHECK 3 #10–11 |

---

## 4. Table C — route-by-route readiness

| Route | Payload it takes | What it still needs | Ready? |
|---|---|---|---|
| **arXiv** (cs.CL primary, cs.LG cross-list) | `encoder-crossover-190.tar.gz` (26,580 B, one member `main.tex`) **or** `main.tex` alone; metadata typed from `ABSTRACT_METADATA.txt` (1,195 chars) + the real author line; licence CC BY 4.0 | author block (A1–A3), date (A4), **cs.CL endorsement code (A5)**, licence decision (A7), Zenodo DOI (A6); fixes B1, B2, B4, B5, B6–B10, B13 | **NO** — blocked by R10 (endorsement) and R6/R7 (no author) |
| **TMLR** (OpenReview) | an **author-built anonymised PDF** produced from `main.tex` moved onto the TMLR LaTeX stylefile/template | **TMLR-stylefile rebuild** (R21 — `main.tex:1` is `\documentclass[11pt]{article}`), **anonymisation** (R22 — no authors, no self-identifying acknowledgements), and **no link to any arXiv version** (the double blind must hold); OpenReview profiles (A13) | **NO** — needs the stylefile rebuild, anonymisation and the un-linked preprint |
| **Preprints.org** | a **zip containing `main.tex`** (self-contained; no `.bib` needed because the bibliography is inlined) | first page must carry title, author list, **abstract, keywords (A10)**, corresponding-author contact and affiliations (R30); licence is fixed CC BY 4.0 (R29); if the arXiv DOI exists first, the *Conference Paper* type is unavailable — submit as a *preprint article* (R31) | **NO** — author block + keywords still missing |
| **Research Square** | **`.doc`, `.docx` or `.pdf` only** — *"We accept the following file formats: .doc, .docx, .pdf."* | **BLOCKED by the format rule**: `main.tex` cannot be uploaded, so a PDF (or DOCX) must be built off-host (R32). Licence default and DOI registrar are **not stated on the fetched pages** | **NO — blocked** by R32 + no PDF exists |
| **OSF Preprints** | `main.pdf`, with the abstract pasted into the form field (≥ 20 chars) | a built PDF; a specific community server must be chosen | **NO** — no PDF exists here |
| **Zenodo** | **any** format/size; a zip holding `main.tex` (+ `main.pdf` if it exists) | licence field is **required** (CC BY 4.0 default, R33); DOI auto-minted by DataCite; ≤ 100 files / 50 GB (R34). The record's contents must stay consistent with `main.tex:405-425` | **CLOSEST TO READY** — no PDF needed; still needs A1/A2/A7 and the `LICENCE_TODO.md` contradiction resolved |

*Route payload list carried from UFMT1 §7 (`strategy/FORMATTING_REQUIREMENTS.md:607-618`). One-line version:
for every route except TMLR the payload is the same two files — `main.tex` and a PDF built from it — plus the
real author block.*

---

## 5. Table D — cannot be checked on this host

**No TeX toolchain exists here** (`pdflatex`, `latexmk`, `tectonic`, `xelatex` all absent) and **no `main.pdf`
exists in the repository**. Therefore **no PDF was ever built and none of the rows below can be verified
locally** — they are *unverified*, never *passing*.

| # | Unverifiable item | Detail / why | Req. ID |
|---|---|---|---|
| D1 | Fonts embedded; outline (TrueType/Type1) not bitmap (Type3) | arXiv: *"You must ensure that all standard and non-standard fonts are included and that outline … rather than bitmap (Type3) fonts are used."* | R13 |
| D2 | Machine-readable / selectable text (not a scanned bitmap) | arXiv submit_pdf: *"PDF must be machine readable"* | R13 |
| D3 | No embedded JavaScript / executables | arXiv: *"PDF files with embedded JavaScript will cause your submission to fail"* | R13 |
| D4 | Single-spaced, 10–14 pt, minimum 1-inch page margin | arXiv format_requirements | R13 |
| D5 | Page count; overfull/underfull boxes; float placement; table overflow; whether any table breaks | 5 `tabular` blocks, none compiled | R44 |
| D6 | **arXiv's own compile succeeding** (TeX Live 2023 / 2025, from the package root) | *"compilation is always done from the root"*; the build has never been run | R1/R44 |
| D7 | `article.cls` behaviour — default numeric `[n]` labels | **5 fetch attempts failed** (`curl` 0 bytes; `mirrors.ctan.org` cross-origin redirect; `mirrors.mit.edu` *"unsupported content type unknown"*; `ftp.fau.de`, `ctan.math.illinois.edu`, `mirror.dogado.de` all 404) and `kpsewhich article.cls` is empty. The default-label claim rests on the kernel source `ltbibl.dtx`, which also says *"The document class must define the thebibliography environment."* | R19 |
| D8 | Total / per-file / extracted size quotas | **not stated on the fetched pages** (`help/sizes.html`, `help/tar.html`). Do **not** repeat 10 MB / 5 MB / 50 MB as a current arXiv rule — those figures are relayed, not re-sourced | R12 |
| D9 | Whether `\today` must be avoided because builds are cached | The rationale is **not stated on any page fetched** for that purpose; the `\date{}` choice is harmless either way | R15 |
| D10 | arXiv compile/processing **time limit** | not found (searched submit_tex, submit_pdf, sizes, 00README) | — |
| D11 | Endorsement cannot be obtained or verified here | needs the author's own arXiv account and a personal endorser | R10 |
| D12 | Author-only facts: real name, affiliation, email, ORCID, COI, funding, AI-use facts, `Comments` page/figure count | `main.tex:12`, `METADATA.md:12-17` | R6/R7/R39–R43 |
| D13 | Venue items the pages themselves do not state | TMLR's DOI policy and the exact `\usepackage` token (style package is only linked as a zip); Research Square's licence default and DOI registrar; OSF's screening duration and size cap; Zenodo's "concept DOI" wording and prefix | — |
| D14 | Reachability of external sources and re-checking of quoted target-repo material | `docs/DECIDER_STACK_DECISION.md` §11.2/§11.6 and `:415/:500/:494-495`, `DECIDER_TIER §2`, `analysis.json`, `REPORT.md:69`, `evals/fixtures/reflex-decisions.ts` are not present at the paths the paper names | R19-adjacent |

---

## 6. Where UCITE1 and UCHECK1 disagree — reconciled

**UCHECK1 fetched the FULL TEXT**, not abstracts: `https://arxiv.org/html/2512.12677v3` (HTTP 200, 357,024 B)
and `https://arxiv.org/html/2602.06370v1` (HTTP 200, 423,961 B), tag-stripped and searched term-by-term with
±130 characters of context, plus a positive-control page (`simmering.dev`, 6/6 controls found)
(`strategy/CITATION_FETCH_VERIFICATION.md:14-31,129-148`).

- **MIS-CITED-1 — REFUTED.** UCITE1 said the three numbers at `MANUSCRIPT.md:150-152` were not the source's
  (`strategy/CITATION_SUPPORT_AUDIT.md:103`). UCHECK1 found **all nine terms printed in the full text**:
  `ModernBERT` ×12, `93.45` ×2 (Table 3 / Table 13), `1.88` ×3, `1.26` ×2, `Llama-3.2-3B` ×28, `Qwen3-4B` ×2,
  `distill` ×16, `97`, `45` (`CITATION_FETCH_VERIFICATION.md:46-65`). The manuscript's attribution is
  **substantively accurate**; UCITE1's finding was a false positive produced by abstract-only checking. The
  residual is precision only: the source writes `Qwen3-4B-Instruct-2507`, and `93.45 samples/s` is the
  **inference throughput on the CLV (5-class patent) corpus**, not WIPO-Alpha (84.48).
- **MIS-CITED-2 — REDUCED to a labelling defect.** UCITE1 said *"none of those figures are printed"*
  (`CITATION_SUPPORT_AUDIT.md:79`). UCHECK1 found **all six** (`94.11`, `94.63`, `91.35`, `99.27`, `99.40`,
  `98.83`) printed at the exact datasets named (`CITATION_FETCH_VERIFICATION.md:86-99`). What survives is that
  **"N-dependent crossover table" is the corpus's coinage, not the source's**: the literal strings
  `N-dependent` and `crossover` occur **0 times** in `2602.06370`'s full text, the source carries a `#Classes`
  column instead, and the encoder **still wins at N = 14** (just by less than at N = 4) — a non-monotonic
  pattern, not a monotone crossover (`CITATION_FETCH_VERIFICATION.md:110-125`).
- **UCITE1's arity finding is weaker than it first looked.** UCITE1's CLASS-A-1 said the paper's *"N = 2–8"*
  contradicts its own §3.1 (`CITATION_SUPPORT_AUDIT.md:84`). But the fixture **schema** declares that range:
  `fixture/DECISION_CASE_SCHEMA.ts:22` reads `/** The 2-8 (never more) options, as short semantic labels. */`
  (verified by grep across the workspace, e.g. `scratch/uneutral7/package/fixture/DECISION_CASE_SCHEMA.ts:22`).
  So the schema **permits** 2–8; the **fixture observes K = 2–5**; and the paper states that observed
  distribution correctly at `MANUSCRIPT.md:257-259` — `K = 2 (33), K = 3 (27), K = 4 (76), K = 5 (54)`, which
  sums to 190 cases and `33·2+27·3+76·4+54·5 = 721` options. *"N = 2–8"* is therefore defensible as the
  fixture's **declared domain** but inconsistent with the observed maximum; the four occurrences
  (`MANUSCRIPT.md:84`, `:171`, `:242-243`, `:714`) are a precision defect, not a contradiction.

**Findings that SURVIVE (still stand):** MIS-CITED-3 — `2025.acl-industry.34` (Raspanti, Ozcelebi &
Holenderski, ACL 2025 Industry, pp. 485–499, DOI `10.18653/v1/2025.acl-industry.34`) is a **different work**
from Geng et al. `2305.13971` and has **no bib entry**, so one bullet mints a citation out of two works
(`CITATION_SUPPORT_AUDIT.md:105`); MIS-CITED-4 (low) — PriDe is a *debiasing* method, not an order-permutation
probe, and only the *concern* transfers; **UNCITED-1** (crossover stated as standing fact, no citation,
`MANUSCRIPT.md:62-63`); **UNCITED-2 / UNRESOLVED-3** (*"published"* 0.6684/D-067 with no publication named,
`:38-43`, `:312-315`, `:424-427`, `:499-502`); **UNCITED-3** (Cohen's κ used 9× and never cited); **UNCITED-6**
(ECE and Brier used as bare column headers); **UNCITED-7 (highest-value new finding)** — four model checkpoints
are measured and none is cited (ModernBERT-base, DeBERTa-v3-base, SetFit-MPNet, plus the unnamed `decider-4b`);
**UNCITED-9** (`mimo-v2.6-flash` and the unidentifiable `routeB-blind-model`); **UNCITED-10** (McNemar, exact
p, χ², bootstrap uncited); **ABSENCE-2 / HEDGE-SCOPE DEFECT** (thesis drops the Abstract's *"inside the target
corpus"* qualifier — `MANUSCRIPT.md:75-77` vs `:20-22`); **ABSENCE-3/4** (core literature claim rests on an
internal doc + commit, unreleased, `:118-142`, `:669-674`); **CLASS-A-2** (H4 stated self-contradictorily at
`:697` vs `:496-498`). UPLAG1/UPLAG2 agree and add: **0 unattributed quotations and 7/7 verbatim quotations
accurate** (`ORIGINALITY_CHECK.md:9-14,55-56`), with the originality defects being **under**-attribution —
five uncited methods (Cohen's κ, McNemar, bootstrap, ECE, Brier) plus three unnamed conventions
(`ORIGINALITY_CHECK.md:131-216`).

---

## 7. What survives as genuinely unresolved (each with its locator)

| # | Unresolved item | Locator |
|---|---|---|
| U1 | **The core literature claim rests on an internal document cited by commit hash** — `docs/DECIDER_STACK_DECISION.md` §11.6, commit `ad301ae1a5472fa7bd27807fdc7bb15d35f81988` — and that repository is **not in the released subset** | `MANUSCRIPT.md:118-121`, `:669-674`, `:763`; `REFERENCES.bib:102-121`; `main.tex:435` (`source_decider_stack_2026`) |
| U2 | **Four model checkpoints are measured but never cited**: `modernbert-base` (Apache-2.0), `deberta-v3-base` (MIT), `setfit-mpnet` (SetFit recipe on `all-mpnet-base-v2`, Apache-2.0), and the primary baseline `decider-4b` (4.66 B params, **checkpoint unnamed and licence unrecorded anywhere**) | `MANUSCRIPT.md:282-286` (arms table), `:289`, `:307`, `:314`; UPLAG2 "Third-party model attribution" |
| U3 | **The thesis sentence drops the Abstract's "inside the target corpus" scope**, so it reads as a claim about the world rather than a hedged absence claim | `MANUSCRIPT.md:75-77` (thesis) vs `MANUSCRIPT.md:20-22` (Abstract) |
| U4 | **Stale release path.** The paper names `repro/encoder-crossover-190/`, which holds **43 files including all 18 harness files** (`repro/encoder-crossover-190/harness/` = exactly 18 files) and **no `verify/recompute-claims.py`**; the sanitised package is the one that has the script and no harness — **29 files** per the UFMT2 card. The 18-file harness count and the missing script are verified in the audits; the 43/29 totals come from the unit card | `MANUSCRIPT.md:745`, `:796`; `strategy/STYLE_COMPLIANCE.md:37-38`, `:65`, `:188-193`; script exists only at `repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py` |
| U5 | **Internal pipeline unit IDs are printed in the reference prose** — `UBIB1`, `UPAPER1c`, `UMERGE1` (and `UREFS` in the same sentence) | `MANUSCRIPT.md:859`, `:868`, `:873`, and `:870` |
| U6 | **`LICENCE_TODO.md` still forbids publication** while the paper says the licence is decided. UPLAG2 settled this as *textual staleness, not a live disagreement*; the closing move is the one the TODO file itself prescribes | `repro/encoder-crossover-190/LICENCE_TODO.md:3` (*"Status: open. Do not publish this subset until this file is resolved."*) vs `MANUSCRIPT.md:848-851` (PolyForm Noncommercial 1.0.0 + paid commercial licence) and `:796`; resolution text at `LICENCE_TODO.md:43-48`; UPLAG2 "SETTLED — the licence contradiction" |
| U7 | **The release-boundary contradiction** — the paper says the evaluation harness is withheld, but `repro/encoder-crossover-190/harness/` contains the 18 harness files including `lint-report.json`, which the paper calls withheld | `MANUSCRIPT.md:748-749`, `:757`, `:762`, `:823-829`, `:834-835`, `:846`; `strategy/STYLE_COMPLIANCE.md:188-193` |
| U8 | **Pointers that do not resolve**: `analysis.json` has no release path (yet most cited keys live in it); `§F.3` exists in no named file; `EXP#12-typed-channel-comparison.md:95` names a file that does not exist; `DECIDER_TIER §2` is never expanded or rooted; `CHECKLIST.md` is not in §7's inventory; the correction-claim citations (`PAPER_CANDIDATES.md:269`, `experiments/LEARNINGS.md:281`) and the p-value gotcha citations (`:265`) all mis-resolve | `MANUSCRIPT.md:295`, `:314`, `:466`, `:487`, `:498`; `:644`, `:649`, `:659`; `:322`, `:396`; `:569`; `:272`, `:651-653`; `:430`, `:766-767`; `strategy/STYLE_COMPLIANCE.md:35-46` |
| U9 | **Companion artifacts state the opposite of the paper** — `CLAIMS.md:38` and `GAPS.md:25-26` say the second model pass *"returned no file"* and *"exactly one model pass exists"*, while the paper reports two readers (κ = 0.8577 / 0.9125, verified real in `experiments/second-labeller-190/metrics2.json`); `GAPS.md:102-134` still presents the baseline as undeclared | `CLAIMS.md:38`, `GAPS.md:25-26`, `GAPS.md:102-134`; `strategy/STYLE_COMPLIANCE.md:96-97` |
| U10 | **Internal-consistency defects**: the H4 self-contradiction (`:697` vs `:496-498`); the *"Four near-misses"* vs *"three of them are now sourced"* count mismatch (`:194` vs `:196`); the broken internal cross-reference to §4.5 where the correction is carried at §4.2 (`:104-105`) | `MANUSCRIPT.md:697`, `:496-498`, `:194`, `:196`, `:104-105`; `CITATION_SUPPORT_AUDIT.md:87,118,229` |

---

## 8. Reconciliation ledger (disagreements between sources of truth)

1. **`ABSTRACT_METADATA.txt` length: 1,195 vs 1,194 characters.** UFMT1 (item 11) and UBIB1 and the UFMT2 card
   say **1,195**; USTYLE1 CHECK 6 says **1,194**. Both agree the file has **186 words**, is pure ASCII, omits the
   word "Abstract", and is far under the 1,920 cap. **Adopt 1,195** (UFMT1's count, taken after UBIB1's repair)
   and record the 1-character difference as a measurement-boundary artefact, not a defect.
2. **arXiv size limits.** `ARXIV_SUBMISSION_PREP.md:62-64` quotes *"10 MB total, 5 MB per file, 50 MB
   extracted"*; `FORMATTING_REQUIREMENTS.md:239-245` records those figures as **"not stated on the fetched
   page"**. **Adopt UFMT1**: the numbers are relayed from older documentation and must not be repeated as a
   current rule. (The package is 26,580 bytes, so no quota endangers it.)
3. **arXiv licence "default".** `ARXIV_SUBMISSION_PREP.md:68-70` says the default is the perpetual
   non-exclusive licence; `FORMATTING_REQUIREMENTS.md:63-71,160-171` says arXiv presents a **menu of six
   options and names no default**, and that the choice is irrevocable (*"The license chosen is irrevocable and
   cannot be changed."*). **Adopt UFMT1** — it is the correction of a prior relay, from the fetched page.
4. **`ABSTRACT.txt` length.** 3,415 text characters (3,416 bytes including the trailing newline) in UFMT1
   (item 12) and 3,415 characters / 524 words in USTYLE1 CHECK 6. **Consistent** — both are the PDF abstract
   and both are over the 1,920 metadata cap.
5. **UCITE1 vs UCHECK1** — reconciled in §6, not silently: UCHECK1's full-text fetch supersedes UCITE1's
   abstract-only method for MIS-CITED-1 and MIS-CITED-2, while MIS-CITED-3/4 and the UNCITED/ABSENCE/CLASS-A
   findings survive.

---

## Appendix Z — dated corrections (UFIXFMT3, 2026-10-16)

**Preserved, not rewritten.** Every value above stands as the value UFMT2 observed on 2026-10-16; the
following are dated corrections that supersede it only where stated.

- **Z1 — tarball size and digest (§4 Table C, arXiv row, line 85).** The quoted *"`encoder-crossover-190.tar.gz` (26,580 B, one member `main.tex`)"* was already stale twice over. Rebuilt by UFIXFMT3 on 2026-10-16 from the current `main.tex` (83,700 B): **28,403 B**, sha256 **`9f757c0391ec9aaa29e1800d37430885fe4adb22f0d6c5d8f461904f105134e1`**, still **exactly one member, `main.tex`**, byte-identical to `papers/encoder-crossover-190/submission/main.tex` under `cmp`. The on-disk tarball immediately before this rebuild was 28,519 B / `171099a5…f51934`. *Note:* the size briefed to this unit (27,253 B) matches no current artefact — the intermediate 26,580 → 27,253 → 28,519 → 28,403 B sequence tracks successive `main.tex` revisions, so quote the digest, not the size alone.
- **Z2 — author-slot line moved (§1 item 1, line 18; §2 Table A rows A1/A2/A4, lines 43, 44, 46; §3 B3, line 65).** The `\author{…}` slot is **no longer at `main.tex:12`**; it is now at **`main.tex:10`** — `\author{AUTHOR SLOT: REAL NAME (INSTITUTION, CITY, COUNTRY) --- TO BE SUPPLIED}`. `\date{}` is at **`main.tex:11`**. Every `main.tex:12` in this document is superseded by `:10` (and `:13` by `:11`).
- **Z3 — the `DEFECT-EVIDENCE.json` claim is resolved (paper side).** The paper-side references that listed or cited the standalone `results/DEFECT-EVIDENCE.json` have been redirected by UFIXFMT3 to the shipped `results/REPORT.md` §D1–D3, with every numeric claim intact: `papers/encoder-crossover-190/AVAILABILITY.md:27`; `CLAIMS.md:84–88`, `:122`; `EVIDENCE_NOTES.md:177`, `:206`, `:212`. The probe is deliberately not part of the released set (`EXCLUDED.md` E12 classes `NOTES-defects.md` and `defect-probe.json` as excluded provenance). `\bibitem` stayed **13** and `\cite` stayed **23** across the regeneration.
- **Z4 — still open, release tree not touched (report only).** The shipped `results/REPORT.md:209` itself still says the flips were *"retained in `results/DEFECT-EVIDENCE.json`"*. Fixing it needs a package rebuild plus a manifest regeneration, and **which tree is authoritative is undecided**: `orchestration/units/UBUILD1.build.sh:134` pins `PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"` — corrected 2026-10-16 by UFIXPIN3; the superseded pre-promotion pin is recorded in `strategy/BUILD_PIN_CHANGE.md` and the frozen unit cards and handoffs — while later units also produced `scratch/utool1/tree-six`, `scratch/udtag1/tree-five` and `scratch/ufix31/pkg`. Worse, the path the paper itself names — `repro/encoder-crossover-190/` — **still contains** `results/DEFECT-EVIDENCE.json` (3,724 B, sha256 `096dec1500693b6e854e3feb7c5fab858b97e7d92cabdb1e23c9455ed940ef35`) with `MANIFEST.json` listing it twice. See `scratch/ufixfmt3/PART3_FINDINGS.md`.
- **Z5 — tarball size and digest; arXiv payload line (§4 Table C, line 85). Supersedes Z1.** Z1's figure
  is itself superseded. Measured from disk 2026-10-19: `papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz`
  is **28,638 B**, sha256 **`5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750`**, md5
  `3c8d38a38cebd15c04d66e32cfdafe72`, still **exactly one member, `main.tex`**, whose bytes equal the live
  `papers/encoder-crossover-190/submission/main.tex` (**84,967 B** / sha256
  `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc`). Table C's `26,580 B` and Z1's
  `28,403 B` / `9f757c03…` are retained above as dated history.
