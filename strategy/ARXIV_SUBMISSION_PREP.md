# arXiv submission prep — encoder-crossover-190

Status (UPREP1): a self-contained LaTeX source exists at
`papers/encoder-crossover-190/submission/main.tex`, packaged as
`papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz` (one member, `main.tex`).
**It has never been compiled** — no TeX toolchain is installed on this host — and **the author is
not endorsed**, which is the binding blocker. Nothing has been submitted.

## 1. The blocker chain (in order; each needs something only the author can give)

**Step 1 — Endorsement. Hard blocker, personal, non-delegable.**
<https://info.arxiv.org/help/endorsement.html> Endorsement is category-specific and required
because the author has no prior accepted arXiv submission in the category. The automatic path
("you may not need endorsement") fires only if **both** hold: the account is registered with a
**valid institutional email address**, and the person has **authored at least one accepted arXiv
paper** with that email domain. Neither holds here, so the automatic path does not fire and the
submission lands in "endorsement required" state: arXiv emails the author an endorsement code plus
a request they must forward to a **personal endorser** — an established arXiv author with
endorsement privileges in the chosen category who agrees to endorse. What the author must do,
personally: pick the category (cs.CL), find a personal endorser (e.g. an author of one of the
cited works, or a colleague with arXiv submissions), and send them the endorsement request.
**Assume this cannot be worked around.** No amount of packaging skill substitutes for it.

**Step 2 — Metadata and the licence. Author-personal.** Fill `submission/METADATA.md`: author name,
affiliation, account email, the abstract within the field's length cap, comments/page count once
the PDF exists, category confirmation, and the irrevocable CC BY 4.0 licence choice. The manuscript
supplies **no author name or affiliation** — these are hard gaps, not oversights to guess at.

**Step 3 — Upload. Mechanical, but only after 1 and 2.** Paste the abstract, paste the author list,
choose the licence, select cs.CL (+ cs.LG cross-list), upload `main.tex` (or the tarball), let arXiv
run its own (pdf)LaTeX, inspect the auto-built PDF (fonts, table overflow, page count), then press
submit. The submitter must be the author's own arXiv account; co-authors must confirm.

## 2. Format requirements verified against arXiv's own pages

Two routes exist and **no Markdown route does**: TeX/LaTeX <https://info.arxiv.org/help/submit_tex.html>
and PDF <https://info.arxiv.org/help/submit_pdf.html>. TeX is the right route here.

Verified for the **TeX route**:
- The submission must include the source and compile **in the root directory**, not in a
  subdirectory; arXiv warns against nested directories. *Ours: one file, top level.*
- arXiv runs `(pdf)latex` and processes the source; do not upload compiler by-products
  (`.aux`, `.log`, `.out`, `.blg`, `.synctex.gz`, `.dvi`, `.ps`); arXiv strips them. *Ours: ships
  none of these.*
- Avoid `\today`, because arXiv caches the build and the date goes stale. *Ours: `\date{}`.*
- A `00README.XXX` may be needed to select the engine or point at the root file; we do not need
  one, and adding one is not possible to test here. This is unverified for our package.
- Bibliography must resolve without a network round trip: either ship a `.bbl` or inline the
  references. *Ours: fully inlined `thebibliography`, no `.bib` shipped.*
- arXiv's reference harvester reads standard identifiers from the text ("arXiv:1510.00322"), which
  matters for automatic reference linking; our identifier-only entries print in exactly that form.
- The build must finish inside arXiv's compile time limit. *Untestable here.*

Verified for the **resulting PDF** (rules apply to whatever the build produces):
- no embedded JavaScript or executable actions
- **all fonts embedded**
- machine-readable/selectable text: not a scanned bitmap document
- images: at least 100 dpi, no paper wider/taller than 50 in, fewer than 34 MPixels — *n/a, the
  paper has no figures*
- non-embedded external files or `.ps`/EPS inclusions are warned about (e.g. `psfig`) — *n/a*

Verified for **packaging** (<https://info.arxiv.org/help/tar.html>, <https://info.arxiv.org/help/sizes.html>):
- `.tar.gz`/`.zip` accepted, preferably a **single-level** directory; no absolute paths
- size limits: **10 MB total, 5 MB per file, 50 MB extracted** — our package is 26,580 bytes
- ancillary files go in an **`anc/` subdirectory of the source**, are *not* a separate upload, may
  **not** be TeX/PS, and are **not** included in the PDF; images put in `anc/` are not displayed
  (<https://info.arxiv.org/help/ancillary_files.html>)
- licence: <https://info.arxiv.org/help/license/index.html>. The default is arXiv's perpetual
  non-exclusive licence; **CC BY 4.0 is an explicit option and the author's decision**, and
  **cannot be changed after announcement**.
- metadata fields: <https://info.arxiv.org/help/prep.html> (title, abstract, authors, comments,
  journal-ref, DOI, ACM/MSC class, report number, categories/cross-lists)

**Could NOT be verified in this unit:** whether the abstract metadata field still enforces its
~1,920-character cap (our abstract is 3,415 chars); whether the A4/letter page-size rule binds an
auto-built TeX PDF; arXiv's exact auxiliary-file strip list and `00README` conventions (relayed
from prior work, not re-fetched); and everything about the build itself, because nothing here can
compile LaTeX. **The single most valuable next step is running `pdflatex main.tex` twice on a
machine with TeX Live installed**, then checking page count, overfull boxes and table widths.

## 3. Packaging decision

- **One document, yes** — one paper, one `main.tex`, one PDF. Everything needed to compile is in
  that one file (inlined bibliography, no images, no `\input`), so the upload is one source file
  and there is nothing to disambiguate.
- **No ancillary directory.** arXiv's `anc/` is for data/code accompanying the paper, and it is
  subject to the same 10 MB/50 MB caps while contributing nothing to the PDF. The reproducibility
  bundle (`research-publish-packages`) is large, is a **release bundle whose harness is
  deliberately withheld**, and the paper's own *Data and code availability* section already says
  so. Uploading a harness-less snapshot to `anc/` would create a second, subtly different artifact
  that arXiv never versions — worse than no ancillary at all.
- **The bundle belongs in a repository, cited from the paper.** That is also what arXiv's ancillary
  page recommends for data sets and code. Recommended: deposit the release bundle on Zenodo to mint
  a versioned DOI, then put that DOI in the availability section (and in the paper's link). If the
  author later insists on a static snapshot at submission time, add an `anc/README.txt` naming the
  DOI and nothing else.
- **Upload only `main.tex` (or the tarball).** `ABSTRACT.txt`, `METADATA.md` and `BUILD_NOTES.md`
  are author-side working files; if they are uploaded they are published.

## 4. Endorsement-free alternatives (already identified in this workspace)

`strategy/PUBLISH_WITHOUT_ENDORSEMENT.md` lists five routes that need no arXiv endorsement:

- **Preprints.org** — free, moderated preprint server with its own DOI prefix; no endorsement.
- **Research Square** — free Springer Nature preprint server, DOI, screening; no endorsement.
- **Zenodo** — CERN-operated, no gatekeeping, instant DOI; also the natural home for the
  reproducibility bundle, so paper and bundle can be versioned together.
- **OSF Preprints** — free, community-moderated, DOI; can host the preprint plus the bundle files.
- **TMLR via direct OpenReview submission** — the only **peer-reviewed** option that needs no
  prior acceptance elsewhere and no arXiv endorsement.

**Does the LaTeX serve them? Yes, unchanged.** `main.tex` uses only a stock `article` class and
stock packages, no arXiv-specific style files and no arXiv-only front matter, so it compiles
anywhere. Zenodo/Preprints.org/OSF/Research Square all accept a PDF built from it (several also
accept the LaTeX source); TMLR takes the PDF at submission and the LaTeX source for the
camera-ready. The one missing ingredient for every one of these is the same: **a TeX toolchain to
produce the PDF**, which the author must supply. The CC BY 4.0 choice is compatible with all five.

## 5. Author action list (in order)

1. Install TeX Live (or open Overleaf) and run `pdflatex main.tex` twice; fix any overfull tables,
   record page count and warnings. Nothing else in this repo can do it.
2. Fill the **NOT SUPPLIED** fields in `submission/METADATA.md` (author, affiliation, email, date,
   comments/page count).
3. Complete the identifier-only bibliography entries (`arxiv2602_06370`, `arxiv2512_12677`,
   `source_decider_stack_2026`, plus any missing author/title in `pride2309_03882`,
   `gcd2305_13971`) — the arXiv reference harvester cannot resolve them otherwise.
4. Decide whether to keep the three front-matter status paragraphs in the published PDF.
5. Secure an arXiv endorser for cs.CL (or choose an endorsement-free alternative above).
6. Only then: choose CC BY 4.0, upload, inspect arXiv's PDF, submit.
