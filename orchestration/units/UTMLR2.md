# UTMLR2 — TMLR-compliant anonymised variant (built on `tmlr.sty`)

**Unit card (persisted by the unit, first tool action).** Parent: `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.
Spec of record: `strategy/TMLR_POLICY.md` (primary-source TMLR rules) + the UTMLR2 card.
Hard bound: 30 tool calls (used 29). Status: **done**. Nothing submitted anywhere; no accounts, no credentials.

## Deliverable
| | |
|---|---|
| Variant | `scratch/utmlr2/tmlr/main.tex` — 476 lines, 83 644 bytes, sha256 `16a19a2d7e3fccdf9acef8d9a9affd328cf38ae9fb252be5f81edc24790e6b7f` |
| Style files (verbatim upstream) | `scratch/utmlr2/tmlr/{tmlr.sty,tmlr.bst,fancyhdr.sty,LICENSE}` |
| Source of truth (unmodified) | `scratch/utmlr1/anonymous/main.tex` — 468 lines, 84 206 bytes, sha256 `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9` |
| Build artefacts | `scratch/utmlr2/tmlr/main.pdf` (16 pages, 178 203 bytes), `scratch/utmlr2/tmlr/tectonic.log` |
| Evidence JSON | `scratch/utmlr2/evidence.json` (style-file digests, replacements, numeric guard, residue sweep, compile facts) |
| Scripts | `scratch/utmlr2/make_tmlr2.py` (pass 1 + measurement), `scratch/utmlr2/fix_tmlr2.py` (pass 2) |

## 1. Style file (MANDATORY per TMLR's submissions page)
- URL: `https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip` → redirect `https://codeload.github.com/JmlrOrg/tmlr-style-file/zip/refs/heads/main`.
- ZIP **694 659 bytes**, sha256 `48f9f972cc812d2cfc8032a78578c2f5d8939b92fbd4f61095e8cbeb3394f92d`.
- `tmlr.sty` sha256 `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002`;
  `tmlr.bst` sha256 `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206`.
- Repo contents: `LICENSE README.md fancyhdr.sty main-accepted.pdf main.bib main.pdf main.tex math_commands.tex tmlr.bst tmlr.sty`.
- Applied: `\documentclass[11pt,a4paper]{article}` + `\pdfpagewidth/\pdfpageheight` + `inputenc/fontenc` → `\documentclass[10pt]{article}` + `\usepackage{tmlr}` + `\usepackage{hyperref}`; `\sloppy` dropped (tmlr.sty sets it).
- **Proof the style is in force:** page 1 of the PDF carries tmlr.sty's own running head `Under review as submission to TMLR` and its hardcoded `Anonymous authors / Paper under double-blind review` block (tmlr.sty ignores `\@author`).
- One adaptation was required by tmlr.sty: it loads `natbib[authoryear]`, so all **13** `\bibitem{key}` became `\bibitem[Author(Year)]{key}` (numeric-style bibitems abort with `Package natbib Error: Bibliography not compatible with author-year citations` — that was the only failing state seen, exit 1, and it is fixed).

## 2. Page-1 LLM-use footnote (TMLR FAQ requires it)
- Added as an unmarked `\blfootnote{...}` immediately after `\maketitle` (macro defined in the preamble; unmarked so no stray title mark appears).
- Wording: *"Use of AI tools. Large language model (LLM) systems were used to assist in designing and implementing the analysis and the experiment, and to help draft and edit this manuscript. All AI-assisted output was checked and verified by the author, who takes full responsibility for the entire content of this paper. The LLM systems are not authors and are not credited as contributors."* — names no harness, repository, host, model route or date.
- Verified in the **page-1** text layer: `pdftotext -f 1 -l 1 main.pdf` contains "Use of AI tools. Large language model (LLM) systems were used…" (page 1, not only the back matter). The back-matter paragraph is retained but genericised.

## 3. Author-identifying residue removed — 83 literal substitutions over three passes
- `docs/DECIDER_STACK_DECISION.md` — **13 sites** (not 6): L28, L52, L69, L71 (×2), L72, L347, L391, L450, L453–L456, L457 (`bibitem`) → anonymous "internal errata note"; citation key `source_decider_stack_2026` → `source_corpus_errata_2026`; the quoted commit-message attribution and the `\S11.2/:415/:500/:494--495` locators dropped.
- Commit ids `ad301ae`, `ad301ae1a5472fa7bd27807fdc7bb15d35f81988`, `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`; fixture digests `076164ac…b4796` and `89e77a8e…d8e169` → "recorded in the supplementary material".
- Internal paths: `evals/fixtures/reflex-decisions.ts`, `tools/typed-channel/`, `harness/data/lint-report.json`, `strategy/licence-templates/RELEASED-PIECE/`, `EXP#12-typed-channel-comparison.md:95`, `REFERENCES.bib`, `DECIDER_TIER \S2`, `git cat-file blob` → neutral descriptions (paths **inside** the submitted package, e.g. `results/`, `fixture/`, `verify/recompute-claims.py`, were kept: they are reviewer-reachable).
- Private record names/locators: "paper-candidates record :265/:269", "experiment-learnings record :265/:281", "second-labeller-190 source experiment tree's evidence record :309", "this record's internal checklist" → "an internal working record" / "two internal working records".
- Host `GX10 gx10-163b`, GPU `GB10` → "local workstation GPU" / "single workstation host (one consumer-grade GPU)".
- Harness/model routes `DeepSeek Harness`, `deepseek-v4.1-flash`, `step-5-preview-free` → genericised; `mimo-v2.6-flash` **retained deliberately** (a public model identifier, not author-identifying, and it is an experimental detail the reader needs).
- `Zenodo DOI pending` sentences (L375, L407, L427) → "No persistent identifier is asserted in this submission"; "released reproducibility package/package/set/subset/material/artifacts" → "anonymised supplementary material / submitted …".
- Dated personal decisions: `(author decision, 2026-10-15)`, `(author decision 2026-10-15)`, `(author, 2026-10-15)` → `(declared)`; the dated CC-BY licence sentence de-personalised.
- `target repository` / `source repository` → "originating project"; "the target corpus" → "the corpus we studied".

## 4. Numeric guard — re-baselined, and it MOVED (measured, not assumed)
Literal-multiset guard over the whole `.tex`, two strip modes:
| mode | before | after | distinct before→after | removed | added | identical |
|---|---|---|---|---|---|---|
| `env-strip` (drop `thebibliography`) | 1198 | **1086** | 340 → **304** | 56 | **0** | **False** |
| `refs-section-strip` (cut at `\section*{References}`) | 1146 | **1035** | 340 → **304** | 56 | **0** | **False** |

Movers (all from stripped identifiers): 64-hex and 40-hex digest fragments (`076164`, `53`, `130953345`, `481`, `88`, `93`, `465`, `7430308`, `99`, `4796`, `5472`, `27807`, `35`, `81988`, `976`, `89`, `24`, `06345`, `45485`, `013799`, `08`, `806`, `9`, `075`, `7709`, `169`, `163`), `301` (5→0, `ad301ae`), `907` (2→0), `2026` (7 removed), `15` (8), `10` (11), `8` (5), `7` (5), `12` (2, `EXP#12`), `51` (2), `265` (2), `269`, `281`, `309`, `415`, `500`, `494`, `495`, `4.1`, `2.6` (net 1), `190` (31→30), `74` (35→33), `256` (from removed `sha256` hex mentions), `11`, `5`, `2`, `4`, `6`, `77`, `36`, `39`.
**Claim-bearing values are untouched** (occurrence counts identical before→after): `0.6789` 25, `0.3474` 27, `0.4526` 13, `0.6684` 19, `0.9014` 4, `0.8577` 4, `0.9053` 3, `0.8632` 3, `0.9158` 3, `0.9125` 5, `4.167` 7, `4.1668` 2, `0.33` 26, `0.32` 25, `0.3249` 2, `152,000` 4, `721` 1. The two exceptions (`190` 31→30, `74` 35→33) are removals of a private *record name* ("second-labeller-190", `…:74`), not of a claim instance. Structure unchanged: 23 `\cite` calls, 13 distinct keys, 13 bibitems, 0 uncited, 0 unresolved.

## 5. Compile — Tectonic 0.15, literal results
`TECTONIC_CACHE_DIR=$PWD/scratch/utex1/cache TMPDIR=$PWD/scratch/utex1/tmp HOME=$PWD/scratch/utex1/home scratch/utex1/bin/tectonic -X compile main.tex` (run from `scratch/utmlr2/tmlr`; no `--interaction`, no `-Z continue-on-errors`):
- **literal exit code 0**
- `Undefined control sequence` count **0**
- LaTeX `!` line count **0**; `error:` lines **0**
- **16 pages** (pdfinfo; letter 612×792), `main.pdf` 178 203 bytes
- warnings only: 27 Overfull / 32 Underfull hbox. Cause of the worst ones (174 pt at L390/L396): unbreakable `\texttt{…}` path strings in the 0.48-`\textwidth` p-columns of the provenance table (L386–L400); cosmetic, pre-existing in kind, and the tmlr text block is *wider* than the stock article one.
- The single failing intermediate state (exit 1) was the natbib author-year error quoted in §1, fixed by adding the 13 labels.

## 6. Survey check (TMLR banned surveys as of 2026-09-01) — judgement: **not a survey**
Reason: the paper contributes one sealed-fixture *measurement* and its falsification ladder (declared primary baseline `0.6789`, secondary `0.6684`, prompted-baseline artefact diagnosis, defect chain D1–D3, pre-registered protocol `EXP#12`), not a synthesis of a literature. It has a Related-work section of two short subsections whose stated job is to locate the one claim it corrects; there is no taxonomy, no coverage claim, no search protocol, and the abstract says the claim "and its audit trail are internal to the corpus, not an external survey — §2". The word "survey" never appears as a self-description. Residual risk: a TMLR editor could read the literature-facing §2 plus the "every public result we located" sentence as a mini-review; if challenged, the defence is the single-fixture negative result and the declared, pre-registered primary endpoint.

## 7. Remaining author-identifying strings: **none found**
Full-file sweep (post-build, `evidence.json:residue_sweep_final`): author name 0, ORCID 0, private-document name 0, Zenodo/DOI 0, GitHub/GitLab 0, host name 0, commit-SHA 0, 40/64-hex digest 0, internal path 0, `target/source repository` 0, dated decision 0, preprint 0, email 0, `git` 0. Two benign hits remain and are **not** identifying: `mimo-v2.6-flash` at `scratch/utmlr2/tmlr/main.tex:201` and `:325` (public model id, kept on purpose), and the phrase "the target fixture" at `:297` (the ML noun for the predicted label). The 13 URLs are public citation links (arXiv, ACL Anthology, a personal blog).

## Compliance verdict against `strategy/TMLR_POLICY.md`
1. Mandatory style file — **met** (§1, running head is the proof). 2. Page-1 LLM footnote — **met** (§2). 3. No link to an author-identifying version — **met** (§3: no DOI/Zenodo/released-package/personal-decision provenance survives). 4. Double-blind integrity — **met** (no author, affiliation, email, ORCID, host, repo or commit identifiers). 5. Clean build — **met** (exit 0, 0 errors).
