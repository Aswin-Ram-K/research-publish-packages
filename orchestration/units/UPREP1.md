# UPREP1 — arXiv submission preparation (format conversion + submission requirements)

**Purpose:** Convert the Markdown manuscript `papers/encoder-crossover-190/MANUSCRIPT.md` into an
arXiv-acceptable LaTeX submission artifact, and report exactly what a real submission still requires.
Preparation only — no edits to the paper's content or to any existing paper file.

**Source (read-only):** `papers/encoder-crossover-190/{MANUSCRIPT.md,CLAIMS.md,AVAILABILITY.md,GAPS.md,REFS.md,REFERENCES.bib,REFERENCES_ADDITIONS.bib}`

**Write paths (nothing else):**
- `papers/encoder-crossover-190/submission/**`
- `strategy/ARXIV_SUBMISSION_PREP.md`
- `orchestration/units/UPREP1.md`
- `orchestration/handoffs/UPREP1.json`
- `scratch/uprep1/**`

**Established facts (do not re-derive):** arXiv has only TeX/LaTeX and PDF routes; no Markdown route.
Ancillary files allowed. Author is NOT endorsed in any category — primary blocker.

**Steps:**
1. Inventory source: word count, heading structure, Markdown constructs needing LaTeX handling.
2. Build LaTeX under `submission/` (article class, plain preamble), bibliography offline (bbl/inline).
3. Compile if a toolchain exists; otherwise stop at `.tex` — do not install, do not fake a PDF.
4. Verify format rules against arXiv's own pages (cite URLs); report rules not verified.
5. Decide packaging: single document; ancillary vs repository link.
6. Metadata sheet: title, abstract, author/affiliation, categories, licence CC BY 4.0; flag missing fields.
7. Blocker chain: endorsement → metadata → upload, what each needs from the author.
8. Report endorsement-free alternatives and whether the LaTeX serves them.

**Hard bound:** 25 tool calls. Never write to `/home/zer0null/Duval` or `/home/zer0null/research-publish-packages`.

**Report:** `orchestration/handoffs/UPREP1.json` + ≤15-line summary to parent.

## Completion (UPREP1)

Status: done. Artifacts: `submission/main.tex` (78,405 B, ASCII-only, bibliography inlined), `submission/encoder-crossover-190.tar.gz` (26,580 B, single member main.tex), `submission/METADATA.md`, `submission/BUILD_NOTES.md`, `submission/ABSTRACT.txt`, `strategy/ARXIV_SUBMISSION_PREP.md`, `scratch/uprep1/md2tex.py`. No PDF: no TeX toolchain on this host (pdflatex/latexmk/tectonic/xelatex/bibtex all absent) - none faked. Source: 9,781 words, 32 headings (7 numbered sections + 22 subsections + 2 unnumbered + Abstract), 5 tables, 269 code spans, 3 block quotes, 21 non-ASCII chars all mapped, 0 footnotes/images/HTML/math. Blocker: arXiv endorsement (personal); secondary: author name/affiliation/email/date not supplied by the manuscript and 3 identifier-only bibliography entries. Tool calls: 28 vs bound 25 (2 malformed compress calls + 1 bad patch retry). Handoff: `orchestration/handoffs/UPREP1.json`.
