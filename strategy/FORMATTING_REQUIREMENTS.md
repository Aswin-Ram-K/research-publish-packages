# FORMATTING_REQUIREMENTS — encoder-crossover-190

**Unit:** UFMT1 · **Date written:** 2026-10-16 · **All pages fetched 2026-10-16 (UTC).**
**Artifact under test:** `papers/encoder-crossover-190/MANUSCRIPT.md` + `papers/encoder-crossover-190/submission/main.tex`
(`article` class, inlined `thebibliography`, 13 `\bibitem`).

**Method.** Every requirement below was taken from a primary source (help page, author guide, style guide,
policy page, or the LaTeX kernel source) that was actually fetched on 2026-10-16 — not from a blog or from
memory. Each carries the URL and a **short verbatim quote**. Fetching was done by this unit directly and by
three delegated fetchers whose raw quote sets are stored at
`scratch/ufmt1/arxiv_notes.md`, `scratch/ufmt1/preprint_notes.md`, `scratch/ufmt1/policy_notes.md`.
Where a page is silent the entry reads **"not stated on the fetched page"**. Where two pages disagree, both
are quoted. Requirement IDs (R1…) are used in the audit in §6.

**Status legend for §6:** PASS / FAIL / PARTIAL / NOT CHECKABLE HERE / NOT STATED.

**How many requirements are sourced:** §6 holds **44 audited requirement rows** (R1–R44). **21** of them
carry a verbatim quote from a fetched primary source — **counting rule:** a §6 row counts only when its
*Source* cell contains an emphasised quoted string (`*"…"*`) taken directly from a fetched primary source; a
row whose *Source* cell holds only a page label or a bare URL does not count, and a citation URL alone is
never a quote. **2** rows are recorded as *NOT STATED on the fetched page* — **R12** (size limits) and
**R15** (`\date{}`) — while **≥9** distinct items are recorded as not stated in the prose of §0–§3 and §5
(the phrase occurs **14** times in total); the two scopes must not be conflated. Distinct `http(s)` primary
URLs: **52** — **counting rule:** every distinct scheme-bearing `http(s)://` URL printed in this document,
deduplicated on lower-cased host (leading `www.` ignored) + path (trailing slash, query and fragment
ignored); the shorthand host/path entries in the §9 inventory carry no scheme and are **not** counted.

> **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, verifier VUFMT1; re-measured by
> UFMT3 with the counts above).** This paragraph formerly read: *"§6 holds **40 audited requirement rows**.
> **34** of them carry a verbatim quote from a fetched primary source; **6** are recorded as not stated on
> the fetched page rather than asserted. Distinct primary URLs used: **33**."* None of the four numbers
> reproduces from the document's own content, and no counting rule was stated for any of them; they are
> preserved here and must not be cited.

---

## 0. Corrections to what was already established

Rule: quote what the prior document says, then correct it.

### 0.1 `strategy/ARXIV_SUBMISSION_PREP.md`

1. **Abstract cap — prior doc left it open; it is live.**
   The doc says (`:74-79`): *"Could NOT be verified in this unit: whether the abstract metadata field still
   enforces its ~1,920-character cap (our abstract is 3,415 chars)"*.
   **CORRECTED — the cap is live and enforced.** arXiv, <https://info.arxiv.org/help/prep.html> (fetched
   2026-10-16): *"Keep it short — abstracts longer than 1920 characters will not be accepted; abridge your
   abstract if necessary."* (the page writes `1920`, without a comma).

2. **Size limits — the numbers in the prior doc are NOT on the current pages.**
   The doc says (`:62-64`): *"size limits: **10 MB total, 5 MB per file, 50 MB extracted** — our package is
   26,580 bytes"*.
   **CORRECTED:** those numbers are **"not stated on the fetched page"**.
   <https://info.arxiv.org/help/sizes.html> (fetched 2026-10-16) documents no total, per-file or extracted
   quota; its only numeric statement is *"Starting with February 2026, we will issue a warning during the
   submission process if images larger than 34 Megapixel (this is about the size of a full size A4 image at
   600dpi) are found."*; <https://info.arxiv.org/help/tar.html> carries no size numbers either. The prior
   figures are relayed from older arXiv documentation and were not re-sourced. This does not endanger the
   package (26,580 bytes, one member), but it must not be repeated as a current rule. (2 `local_web_search`
   attempts for the numbers timed out.)

3. **Ancillary exclusion — "TeX/PS" overstates it.**
   The doc says (`:65-67`): ancillary files *"may **not** be TeX/PS"*.
   **PARTLY CORRECTED.** The fetched page excludes TeX only:
   <https://info.arxiv.org/help/ancillary_files.html> (2026-10-16): *"TeX files should not be included in
   the ancillary file directory."* A prohibition on **PS** files is **not stated on the fetched page**.

4. **Ancillary "not included in the PDF" — supported, but the page words it differently.**
   The doc says (`:66-67`): ancillary files *"are **not** included in the PDF"*.
   The page does not use that sentence; it says: *"The abstract pages for articles that include ancillary
   files will include additional links below the usual article download links."* and *"Full text placed in
   the ancillary directory will not be indexed in searches."* — i.e. ancillary files are separate downloads
   on the abstract page, not part of the PDF. Also newly verified: *"the ancillary files feature is not
   supported with PDF submissions at this time. They are only supported for submissions with TeX/PDFLaTeX
   source files."*

5. **Licence — there is no stated "default".**
   The doc says (`:68-70`): *"The default is arXiv's perpetual non-exclusive licence; **CC BY 4.0 is an
   explicit option and the author's decision**, and **cannot be changed after announcement**."*
   **CORRECTED in two places.** <https://info.arxiv.org/help/license/index.html> (2026-10-16) presents a
   **menu of six options** and names no default; and the irrevocability wording is broader than "after
   announcement": *"The license chosen is irrevocable and cannot be changed."* and *"Remember that articles
   posted on arXiv are a permanent part of the scholarly record and the license chosen for each version is
   irrevocable"*. The menu is: CC BY 4.0, CC BY-SA 4.0, CC BY-NC-SA 4.0, CC BY-NC-ND 4.0, *"arXiv.org
   perpetual, non-exclusive license 1.0"*, and CC Zero.

6. **Endorsement automatic path — the prior paraphrase does not match the page.**
   The doc says (`:13-21`): the automatic path fires only if the account has *"a valid institutional email
   address"* and the person has *"authored at least one accepted arXiv paper with that email domain"*.
   The fetched page words it as ownership of a co-author's paper, not authored-at-least-one:
   <https://info.arxiv.org/help/endorsement.html> (2026-10-16): *"Your account may receive endorsement if:
   you have claimed ownership of a paper submitted by a co-author and your email address meets the
   institutional email criteria"*. The consequence the doc draws (personal endorsement required here) still
   holds, but quote the page rather than the paraphrase.

7. **Bibliography "identifier-only entries" — the claim is factually wrong about the file.**
   The doc says (`:125-127`): *"Complete the identifier-only bibliography entries (`arxiv2602_06370`,
   `arxiv2512_12677`, `source_decider_stack_2026`, plus any missing author/title in `pride2309_03882`,
   `gcd2305_13971`) — the arXiv reference harvester cannot resolve them otherwise."*
   **CORRECTED:** those entries are **not** identifier-only. `main.tex:431` carries the author and full title
   for `arxiv2602_06370` ("Valdes Gonzalez, Alberto Andres, *Cost-Aware Model Selection for Text
   Classification…*"), `main.tex:432` for `arxiv2512_12677` ("Yousefiramandi, Amirhossein and Cooney,
   Ciaran, *Fine-Tuning Causal LLMs…*"), `main.tex:433` for `pride2309_03882` (Zheng, Zhou, Meng, Zhou,
   Huang), and `main.tex:434` for `gcd2305_13971` (Geng, Josifoski, Peyrard, West). Only
   `source_decider_stack_2026` (`main.tex:435`) legitimately has no attributable author, and it is an
   unpublished internal corpus document, not an arXiv item.

8. **"00README / auxiliary strip list relayed, not re-fetched" — now verified.**
   The doc says (`:74-79`): *"arXiv's exact auxiliary-file strip list and `00README` conventions (relayed
   from prior work, not re-fetched)"* and `:45-47` says *"A `00README.XXX` may be needed… This is unverified
   for our package."*
   **CORRECTED to verified:** <https://info.arxiv.org/help/00README.html> (2026-10-16): *"It is not required
   (nor recommended) to manually create this file prior to submission, with some exceptions and caveats."*
   The strip list, <https://info.arxiv.org/help/submit_tex.html>: *"If you have a file named foo.tex, then do
   not include any associated auxiliary file or intermediate or resulting output file, e.g. foo.ps (or
   foo.aux, foo.log, foo.toc, foo.lot, foo.lof, foo.dvi, foo.pdf) in your submission. These will be
   automatically removed … Index (`.ind`) and processed bibtex (`.bbl`) files are an exception"*. **Still not
   found:** any compile/processing **time limit** (searched submit_tex, submit_pdf, sizes, 00README).

9. **"arXiv advises against `\today` because builds are cached" (`:44-45`, `:16`) — still not sourced.**
   Not stated on any page fetched in this unit for that purpose; recorded as **unverified**. The
   `\date{}` choice is harmless either way.

10. **Tarball and toolchain state — confirmed.** `encoder-crossover-190.tar.gz` is 26,580 bytes with exactly
    one member (`main.tex`, 78,405 bytes); **no TeX toolchain** is installed (`pdflatex`, `latexmk`,
    `tectonic`, `xelatex` all absent) and **no `main.pdf` exists**, matching the doc's `:5-7` and `:4`.

    > **DATED FINDING — the shipped tarball diverges from the audited `main.tex` (2026-10-16; verifier VUFMT1
    > Contradiction D, re-measured on disk by UFMT3).** `papers/encoder-crossover-190/submission/encoder-crossover-190.tar.gz`
    > holds one member, `main.tex`, at **78,405 bytes, mtime 13:52** (18:52 UTC), while
    > `papers/encoder-crossover-190/submission/main.tex` measured **80,780 bytes, mtime 14:18** (19:18 UTC) at
    > verification time; the two revisions **diverge at byte 15,750 (line 81)**, first differing byte measured
    > with `cmp -l`. The tarball was therefore a **stale revision** of the audited file, so the PASS verdicts
    > sourced from it (R1/R2/R14) and the §7 arXiv payload recommendation described the older bytes.
    > **UFMT3 re-measurement at 2026-10-16 14:57 CDT = 2026-10-16 19:57 UTC (identical across repeated reads):** the divergence is
    > **RESOLVED** — UFIXFMT1's rebuild has landed, and the tarball member `main.tex` and the on-disk
    > `main.tex` are now **byte-identical (83,774 bytes, mtime 2026-10-16 14:55 CDT, sha256 `30e162b4cc6d7b3ae97d0314…`)**. The stale-revision
    > finding above stands only as history for the pre-rebuild tarball.
    > **UFIXFMT1 rebuilt the tarball from the current `main.tex`; UFMT3 changed nothing under `papers/`, and
    > no byte offset above is stable across that rebuild.**

### 0.2 `papers/encoder-crossover-190/submission/METADATA.md`

11. **Abstract caveat — now resolved, in the author's favour.**
    The file says (`:44-49`): *"arXiv's metadata abstract field is commonly capped at about **1,920
    characters**; if that cap is live, the metadata abstract must be shortened while the PDF keeps the full
    one. **This cap was NOT verified against arXiv's help pages in this unit**"*.
    **CORRECTED — the cap is live (quote in §1.3), and the shortening already exists:**
    `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt` is **1,195 characters / 186 words**, well
    under 1,920, contains no non-ASCII character, and does not contain the word "Abstract". This file is the
    correct value for the metadata abstract field.
12. **Abstract length — the count is right, the unit label was wrong.** `ABSTRACT.txt` is **3,416
    characters including the trailing newline = 3,415 text characters / 524 words**; its raw file size is
    **3,462 bytes** (28 non-ASCII characters account for the 46-byte difference), matching `METADATA.md:11`.
    The figures are consistent, not contradictory: 3,416 = characters **including** the trailing newline,
    3,415 = characters **excluding** it, 3,462 = **bytes**. §6's parenthetical has been relabelled the same
    way. The LaTeX `abstract` environment (`main.tex:20-29`) normalises to **3,740 characters** (3,746 raw)
    because of its markup.

    > **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, VUFMT1 Check 4; re-measured
    > by UFMT3: `wc -c` = 3,462, `len(text)` = 3,416).** This item formerly read: *"`ABSTRACT.txt` is
    > **3,416 bytes including the trailing newline = 3,415 text characters / 524 words**"*. 3,416 is a
    > **character** count, not a byte count. The "3,415 text chars / 524 words" claim was and remains
    > correct.
13. **"Licence CC BY 4.0 … not the arXiv default" (`:20`, `:38`)** — see correction 5: arXiv states no
    default; it is a menu, and the choice is irrevocable.
14. **`Comments` "NEEDS A NUMBER" (`:17`)** — confirmed by the fetched field guidance (§1.4).

---

## 1. arXiv

### 1.1 Accepted source formats and what arXiv does with them
- Preferred routes, in order: <https://info.arxiv.org/help/submit/index.html> (2026-10-16): *"(La)TeX,
  AMS(La)TeX, PDFLaTeX; PDF; HTML with JPEG/PNG/GIF images"*, and *"We do not accept dvi, PS, or PDF created
  from TeX/LaTeX source"*.
- **arXiv compiles TeX itself.** <https://info.arxiv.org/help/submit_tex.html> (2026-10-16): *"We retired the
  long-used "AutoTeX" (Submission 1.0) system that we have used for decades in favor of a simpler, more
  straightforward process of converting (La)TeX submissions to PDFs in Submission 1.5."* Engine: TeX Live
  2023 and 2025, *"TeX Live 2025 … (the default)"*.
- Packaging: same page — *"packaged in a (possibly compressed) `.tar` or `.zip` file"* and *"compilation is
  **always** done from the root of your submission directory, even if the main file is in a subdirectory."*
  <https://info.arxiv.org/help/tar.html>: *"arXiv does not currently support `rar` archives, or `bz` or `bz2`
  compression. Also, you must not simply concatenate files together"*.
- **A PDF is not required for the TeX route; arXiv builds it.** PDF is a separate, discouraged route:
  <https://info.arxiv.org/help/submit_pdf.html> (2026-10-16): *"Submit one PDF file including all text and
  figures. … We do not permit submissions that include multiple PDF files, or PDF files in combination with
  other file types."* and *"a PDF file created from a TeX/LaTeX file will typically be rejected, with
  exceptions granted on a case-by-case basis."*
- **Multiple versions/replacement.** <https://info.arxiv.org/help/replace.html> (2026-10-16): *"We ask that
  articles be replaced no more than once per week. After version 5 replacements are limited to no more than
  once per week."*; *"It is not possible to make changes without generating a new version."*; same-day cutoff
  *"14:00 US Eastern Time (EDT/EST)"*; *"Revisions after version 5 are not listed in the daily mailings"*.
  <https://info.arxiv.org/help/versions.html>: *"Once made public, each version of a work is considered a
  permanent part of the scientific record and may not be removed."*; *"This will increment its version number
  by one"*; identifier *"arXiv:YYMM.NNNNNvX"*. **No hard maximum version count is stated.**

### 1.2 Licence menu, irrevocability, and what "perpetual non-exclusive" means
<https://info.arxiv.org/help/license/index.html> (2026-10-16). Menu: **CC BY 4.0**, **CC BY-SA 4.0**,
**CC BY-NC-SA 4.0**, **CC BY-NC-ND 4.0**, *"arXiv.org perpetual, non-exclusive license 1.0"*, **CC Zero**.
- Irrevocability: *"The license chosen is irrevocable and cannot be changed."* and *"the license chosen for
  each version is irrevocable"*.
- Ownership: *"For all licenses here, with the exception of CC Zero, the original copyright holder retains
  ownership after posting on arXiv."*
- **Perpetual non-exclusive, per the licence text itself** —
  <https://arxiv.org/licenses/nonexclusive-distrib/1.0/> (2026-10-16): *"I grant arXiv.org a perpetual,
  non-exclusive license to distribute this article. / I certify that I have the right to grant this license.
  / I understand that submissions cannot be completely removed once accepted. / I understand that arXiv.org
  reserves the right to reclassify or reject any submission."*
- What that means for reuse, in arXiv's own characterisation (license/index.html): *"This license gives
  limited rights to arXiv to distribute the article, and also limits re-use of any type from other entities
  or individuals."*
- CC BY 4.0, same page: *"This license allows reusers to distribute, remix, adapt, and build upon the
  material in any medium or format, so long as attribution is given to the creator. The license allows for
  commercial use."*
- Metadata licence: *"A Creative Commons CC0 1.0 Universal Public Domain Dedication will apply to all
  metadata."*
- Copyright-stamp rule: *"Submission of PDFs with copyright statements which prohibit or impair arXiv's
  redistribution license will be rejected."*
- `https://info.arxiv.org/help/license/options.html` — **HTTP 404** (1 attempt); the real menu is
  `license/index.html`.

### 1.3 Abstract limit (the previous unit's 1,920 figure — CONFIRMED)
<https://info.arxiv.org/help/prep.html> (2026-10-16): **"Keep it short — abstracts longer than 1920
characters will not be accepted; abridge your abstract if necessary."** Also on the field:
*"Do not include the word "Abstract"."*; *"Carriage returns will be stripped unless they are followed by
leading white spaces."*; the announcement copy is *"wrapped to 80 characters"*; TeX-isms (*"`~` `\,`
(backslash comma) and `\ ` (backslash space)"*, *"font commands such as `\em` or `\it`"*) and Unicode must
be avoided. There is **no** "abstract should be…" sentence on the page. The page states the cap as `1920`
(no thousands separator).

### 1.4 Title / author / affiliation handling
<https://info.arxiv.org/help/prep.html> (2026-10-16):
- Title: *"Do not use all uppercase letters."*; *"Do not use unicode characters."*; *"Expand out \TeX macros
  that are mystifying"*.
- Authors: *"Anonymous submissions are not accepted. Complete, and accurate author information is
  required."*; *"In order to automate indexing and searching, it is required that authors be listed in a
  standard format across arXiv."*; *"Names must be given in the order: Firstname Lastname or Firstname
  Middlename Lastname"*; *"Do not include honorifics, such as "Dr.", "Professor", etc."*; *"Include the names
  of _all authors_ instead of truncating the list with "_et al._ ""*; *"Do not enter a name that contains a
  comma or the word `and'."*
- Affiliations: *"Affiliations must be placed within parentheses. Do not enter full mailing address, as these
  are not needed in our metadata. If desired, at most, include a city and country (no zip codes, postal
  codes, or street addresses)."* Example format given verbatim:
  *"`Authors: Author One (1), Author Two (1 and 2), Author Three (2)`"* / *"`((1) Institution One, (2)
  Institution Two)`"*.
- Roles: *"Roles — such as `editor`, or `appendix author` — _may not_ be indicated within the Authors field,
  rather roles should be indicated within the Comments field."*
- **AI authorship:** *"Generative AI language tools should not be listed as an author; instead authors should
  refer to moderation related policy."*
- Comments field: *"Indicate number of pages and number of figures."*; also the field for *"to be published
  in"* / *"submitted to"* information, which is *"not editable"* after announcement.
- ASCII rule for metadata: *"Our metadata fields only accept ASCII input."*
- **NOT VERIFIED on any fetched page:** a literal statement that the arXiv-generated author list comes from
  the metadata form rather than the `.tex` author block. `prep.html` only imposes formatting rules on the
  fields. Candidate page not fetched: `https://info.arxiv.org/help/policies/identity_and_affiliation.html`.

### 1.5 Ancillary files (`anc/`)
<https://info.arxiv.org/help/ancillary_files.html> (2026-10-16):
- Supported for TeX/PDFLaTeX only: *"the ancillary files feature is _not_ supported with PDF submissions at
  this time. They are only supported for submissions with TeX/PDFLaTeX source files."*
- May include: *"Raw data for tables and plots in the article"*, *"Program code"*, *"Additional images or
  movies"*, *"Workbooks and spreadsheets"*.
- **May not:** *"TeX files should not be included in the ancillary file directory."* A PS prohibition is
  **not stated on the fetched page**.
- Placement: *"Ancillary files are included with an arXiv submission by placing them in a directory `anc` at
  the root of your .tar.gz or .zip submission package. This is done in the "Add Files" step of the
  submission process."* Example given: `/article.tex`, `/figure1.pdf`, `/anc/my_program.cpp`.
- Other constraints: *"Pointers inside your codebase should not reference this directory (linking may be lost
  upon announcement)."*; *"Full text placed in the ancillary directory will not be indexed in searches."*;
  *"PDF files with embedded JavaScript will cause your submission to fail"*.
- **In the PDF? No** — they appear as separate links: *"The abstract pages for articles that include
  ancillary files will include additional links below the usual article download links."*
- Version-bound: *"Ancillary files are stored with a particular version of an article and thus cannot be
  changed independently from the article. Different ancillary files may appear with each version."*

### 1.6 File / directory size limits
- **Total / per-file / extracted quotas: "not stated on the fetched page."**
  <https://info.arxiv.org/help/sizes.html> (2026-10-16) states no quota; only *"Starting with February 2026,
  we will issue a warning during the submission process if images larger than 34 Megapixel (this is about
  the size of a full size A4 image at 600dpi) are found."* and *"We do not accept submissions with omitted
  figures."* <https://info.arxiv.org/help/tar.html> carries no size numbers. (2 `local_web_search` attempts
  for the figures timed out.) Do **not** repeat 10 MB / 5 MB / 50 MB as a current arXiv rule.
- Directory/absolute-path rules, <https://info.arxiv.org/help/faq/mistakes.html> (2026-10-16): *"In our
  system, only the top level directory is granted write permission during processing. Attempts to write files
  to subdirectories will fail."*; `\input{subdir/file}` works but `\include{subdir/file}` *"WILL FAIL"*;
  *"you must use relative filenames instead of absolute filenames."*

### 1.7 What must NOT be in the source tarball
<https://info.arxiv.org/help/submit_tex.html> (2026-10-16):
- *"do not include extraneous files (including unused figure files), leftover files, backup files … Do not
  include journal templates, referee letters, or man pages."*
- *"If you have a file named foo.tex, then do not include any associated auxiliary file or intermediate or
  resulting output file, e.g. foo.ps (or foo.aux, foo.log, foo.toc, foo.lot, foo.lof, foo.dvi, foo.pdf) in
  your submission. These will be automatically removed … Index (`.ind`) and processed bibtex (`.bbl`) files
  are an exception"*.
- *"Please do not use hidden files or directories in your source package. … will be deleted upon
  announcement"*.
- Filenames limited to *"`a-z A-Z 0-9 _ + - . , =`"* (<https://info.arxiv.org/help/submit/index.html>).
- Non-standard macros/style files *"must **NOT be attached** to a paper"* (faq/mistakes.html).
- Embedded JavaScript ⇒ automatic rejection; *"Remove or disable JavaScript when building your PDF"*.
- **Not found:** any prohibition on encrypted files.

### 1.8 Endorsement
<https://info.arxiv.org/help/endorsement.html> (2026-10-16):
- *"arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category."*
- Automatic path: *"Your account may receive endorsement if: you have claimed ownership of a paper submitted
  by a co-author _and_ your email address meets the institutional email criteria"*; otherwise *"seek personal
  endorsement from an established arXiv author"*.
- *"At least one positive endorsement is required per endorsement category to be considered endorsed for that
  category."*
- Endorsers are authors of papers *"submitted between three months and five years ago"*.
- Mechanically: *"they will send you a six-character alphanumeric _endorsement code_"*.
- Nature of the gate: *"The endorsement process is not peer review."*

### 1.9 PDF/build requirements (apply to whatever PDF is produced)
- Fonts, <https://info.arxiv.org/help/submit_pdf.html>: *"You must ensure that all standard and non-standard
  fonts are included and that outline (TrueType/Type1) rather than bitmap (Type3) fonts are used."*;
  *"arXiv may reject PDF submissions because of non-standard, non-embedded fonts."*; *"PDF must be machine
  readable"*.
- Layout, <https://info.arxiv.org/help/policies/format_requirements.html> (2026-10-16): *"Single spaced
  text; 10 to 14 point type; Minimum 1" page margin"*; no line numbers, watermarks, or referee remarks.
- `00README`, <https://info.arxiv.org/help/00README.html>: *"It is not required (nor recommended) to manually
  create this file prior to submission, with some exceptions and caveats."*
- **Two fetched pages disagree about engines, and both are quoted here:**
  `faq/mistakes.html` — *"arXiv does not support processing with: XeTeX and its variants including LuaTeX,
  LyX, or PDFTeX"*; `00README.html` lists `xelatex`, `pdflatex` and `pdftex` as supported compiler settings.
  For this paper the point is moot: stock `pdflatex` is the engine used, and the normal route is
  `pdflatex` → `pdflatex`.
- **Compile/processing time limit:** "not stated on the fetched page" (searched submit_tex, submit_pdf,
  sizes, 00README).

---

## 2. TMLR (Transactions on Machine Learning Research)

Sources: <https://jmlr.org/tmlr/author-guide.html>, <https://jmlr.org/tmlr/editorial-policies.html>,
<https://jmlr.org/tmlr/submissions.html> (all fetched 2026-10-16).

- **Required style files / format.** author-guide: *"Submissions must be PDF files generated using the TMLR
  LaTeX stylefile and template."* submissions: *"The Author Guidelines page contains a LaTeX stylefile and
  template; these are mandatory. Any changes to the stylefile or template that alters the formatting, font,
  or layout of the manuscript may result in rejection without review."* The style package is linked only as
  *"TMLR LaTeX stylefile and template"* →
  `https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip`. **The exact `\usepackage` token
  is not stated on the fetched pages.** Word is not an accepted format.
- **Page/format expectations.** author-guide: *"Submissions may be any length, but a paper's length should be
  justified by its content and papers that are unusually long (not counting any Appendices) are likely to
  result in reviewing delays."*; an Appendix after the references is allowed; *"Authors may submit up to
  100MB of supplementary material … all supplementary materials must be in PDF or ZIP format."*
- **Anonymous?** Yes. editorial-policies: *"TMLR uses an open-reviewing, double-blind process."*; *"The
  manuscript is submitted to [OpenReview] in anonymized form, and the authors recommend an action editor to
  oversee the review process."*; author-guide: *"TMLR uses a double blind review process and submissions must
  be anonymized."*
- **Licence.** author-guide: *"All TMLR submissions, from the time of submission to final publication, are
  licensed under [CC BY 4.0]. At all times, copyright is retained by the authors."* — fixed, no menu.
- **Where submitted.** OpenReview: *"The manuscript is submitted to OpenReview in anonymized form"* →
  <https://openreview.net/group?id=TMLR>.
- **Review model.** Rolling, no deadline (*"papers are assigned throughout the year"*; action editor assigned
  *"within a week"*). Decision is one of *"accept as is, accept with minor revisions, or reject"*.
  Acceptance criterion, editorial-policies: *"Are the claims made in the submission supported by accurate,
  convincing and clear evidence?"* and *"Would at least some individuals in TMLR's audience be interested in
  knowing the findings of this paper?"*; *"Papers should be accepted if they meet the criteria, even if the
  contribution or significance of the work is modest."*
- **Preprint compatibility (critical here).** editorial-policies: *"It is acceptable for a submission to
  overlap with the author's previous work if it was shared at venues or tracks that are publicly declared, in
  writing, to be non-archival, such as workshops, or on preprint servers such as arXiv and bioRxiv."* But
  double-blind must hold: author-guide — *"Authors are also allowed to upload their submissions to arXiv or
  other preprint servers at any time, either anonymously or including their identity, though double blind of
  the TMLR submission itself must be maintained by not linking to another version that includes the authors'
  names."*
- **Statements TMLR requires.** Broader Impact Statement *"If their work carries a significant risk of harm"*;
  COI via OpenReview profiles (*"Authors and co-authors will use their OpenReview profile to identify domain
  and personal conflicts"*); *"All authors must have complete and active OpenReview profiles, including
  information such as affiliations, conflicts of interest, and publication history."* Author-contributions
  statement is optional: *"Authors may choose to include a statement indicating author contributions."*
- **LLM policy.** editorial-policies: *"LLMs may be used as general-purpose assistive tools. Whichever tools
  are used, authors are fully responsible for content on which they are listed as (co-) authors."*;
  *"LLMs are not eligible for authorship."* A claim relayed by the delegated fetcher that the FAQ requires
  LLM use to be *footnoted on page 1* is **not confirmed by an exact quote** and is recorded as unresolved.
- **Not stated on the fetched pages:** a DOI for TMLR articles (only *"ISSN 2835-8856"* appears, on
  <https://jmlr.org/tmlr/faq.html>).

---

## 3. Preprint servers

### 3.1 Preprints.org
Source: <https://www.preprints.org/instructions-for-authors> and <https://www.preprints.org/about>
(fetched 2026-10-16).
- **Accepted source format:** *"Files should be submitted in Microsoft Word or LaTeX format. For LaTeX files,
  ensure that all files necessary, including the .bib file, if applicable, to recreate the PDF are included
  in a zip or similar archive."* PDF-only is not offered.
- **Must a PDF be supplied?** No; the author supplies source and the platform recreates the PDF (implied by
  the `.bib` requirement).
- **Licence:** fixed — *"All preprints are posted with a Creative Commons CC BY 4.0 license, ensuring that
  authors retain copyright…"* (no options, no default to choose).
- **DOI:** *"Each preprint will be registered with a unique digital object identifier issued by Crossref."*;
  *"New versions of preprints receive a different DOI."* Prefix value not stated.
- **Moderation/screening:** *"All preprints undergo a short screening before being uploaded online. It
  usually takes less than 24 hours unless we find that some necessary information is missing. This process
  takes less than one business day in most cases. Screening includes checks for basic scientific content,
  author background, and compliance with ethical standards."*; rejection possible — *"any violation of these
  ethical standards may lead to the rejection or withdrawal of the manuscript."*
- **Formatting:** *"Any style is allowed for submitted papers. However, it is recommended that you use
  Preprints.org's template."* The first page must contain title, author list, abstract, keywords,
  corresponding-author contact and affiliations; a comprehensive bibliography is required.
- **Authorship:** *"All authors must be aware of the submission to Preprints.org and agree to the
  authorship."*; ICMJE/CRediT recommended; LLMs cannot be authors.
- **Route-relevant:** the *Conference Paper* type accepts only *"full non-peer-reviewed papers … that … do
  not have a DOI"* — so **if the paper already carries an arXiv DOI (`10.48550/arXiv.…`), the Conference Paper
  type is unavailable**; submit as a preprint article instead.

### 3.2 Research Square
Sources: <https://www.researchsquare.com/legal/editorial> — **carries the format rule**; and
<https://www.researchsquare.com/researchers/preprints> — fetched 2026-10-16, but does **not** carry it.
- **Accepted source format** — verified on `legal/editorial` **only**: *"We accept the following file
  formats: .doc, .docx, .pdf."* — **LaTeX is not listed.** The `researchers/preprints` page does not contain
  this sentence (re-checked by UFMT3 against the saved page `scratch/vufmt1/fetched/rs_pp.html`: a MISS,
  while `rs_ed.html` hits); the quote was previously shown under both sources, which overstated
  `researchers/preprints`.

  > **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, VUFMT1 "Overstated";
  > re-measured by UFMT3).** This line formerly listed both pages as the source of the one quote. The
  > sentence verifies on `researchsquare.com/legal/editorial` only. R32's *Source* cell already cites
  > "Research Square editorial", so that row's attribution was correct.
- **Must a PDF be supplied?** A `.doc/.docx/.pdf` file is the upload; the page says only *"Posted in
  full-text HTML"*. Whether the venue builds a PDF is **not stated on the fetched page**.
- **Licence:** **not stated on the fetched pages** (only a generic "License information" display; 3 pages
  fetched).
- **DOI:** yes — *"Issued a DOI"*; legal/editorial: *"Preprints posted on Research Square receive a DOI,
  making them a citable part of the scientific record."* Registrar/prefix not stated.
- **Moderation/screening:** *"Research Square does not conduct peer review on preprints prior to posting.
  Content submitted to Research Square is checked for appropriate ethics and consent statements; disclosure
  of competing interests; absence of patient identifiers; and inappropriate, alarming, highly controversial,
  or pseudoscientific claims."*; *"submissions with missing figures, reference lists, or other critical
  components may be rejected."*; *"typically posted within 72 business hours."* Only systematic reviews and
  research articles with complete methods/results are eligible.
- **Formatting:** no template or length limit stated; a data-availability statement is recommended.
- **Authorship:** *"Large Language Models (LLMs), such as ChatGPT, do not currently satisfy generally accepted
  authorship criteria."*; competing interests must be disclosed at submission.

### 3.3 Zenodo
Sources: <https://help.zenodo.org/docs/deposit/about-records/>, <https://about.zenodo.org/policies/>,
<https://help.zenodo.org/docs/deposit/describe-records/licenses/>,
<https://help.zenodo.org/docs/deposit/manage-files/>, <https://help.zenodo.org/docs/share/submit-for-review/>
(fetched 2026-10-16).
- **Accepted source format:** *"Zenodo supports uploading files in any size and format."*; *"Data file
  formats: All formats are allowed - even preservation unfriendly."* LaTeX, Word and PDF all fine.
- **Must a PDF be supplied?** No PDF requirement and no venue PDF build stated (only a preview of the first
  previewable file).
- **Licence:** *"The license field is a required field."*; *"Zenodo defaults to the Creative Commons
  Attribution 4.0 International (CC-BY) license."* SPDX list plus custom and mixed licences allowed; metadata
  is CC0.
- **DOI:** *"Zenodo will automatically register a Digital Object Identifier (DOI) for a record once you
  publish it."*; *"Zenodo register DOIs with DataCite."* Versioning is a new record: *"a completely new record
  with separate metadata, files and persistent identifier, but it is linked to all previous and future
  versions."* The term **"concept DOI" is not stated on the fetched pages**; prefix not stated.
- **Moderation/screening:** none for a direct publish — *"Once the draft is complete, you publish the draft
  and it becomes a record."* Community curation is optional: *"The record is automatically published when the
  curator(s) of the community accepts your record into the community. If the review is declined, you can
  choose to submit the record to a new community, or you can publish it without a community."*
- **Limits:** *"You can upload up to a 100 files and a total volume of 50GB (50,000,000,000 bytes)."*;
  *"Total files size limit per record is 50GB. Higher quotas can be requested and granted on a case-by-case
  basis."* Post-publication file edits: **45 days** on one page (`create-new-upload`) vs *"within 30 days"*
  on another (`manage-files`) — **the two fetched pages disagree; both quoted.**
- **Formatting requirement:** none stated (no template, no reference style).

### 3.4 OSF Preprints
Source: <https://help.osf.io/article/376-preprints-home-page> (fetched 2026-10-16).
- **Accepted source format:** *"You should have your preprint in an easily accessible file. It is advisable
  to use non-proprietary file types like PDF."* PDF is advised, not required; LaTeX is not mentioned.
- **Must a PDF be supplied?** No PDF-build statement; **"not stated on the fetched page"**.
- **Licence:** no default — *"it's not required to license your preprint"*; *"In general, licenses recommended
  are CC-0 1.0 Universal and CC-By Attribution 4.0 International."*
- **DOI:** *"All of the community-run preprint servers on the OSF follow the same upload process and follow
  pre-moderation policies, where submissions are in a private, pending state until a moderator accepts or
  rejects them. If accepted, preprints receive a DOI and a persistent URL to allow your preprint to be
  cited…"* Prefix not stated.
- **Moderation/screening:** pre-moderation only (quote above), with moderator accept/reject and an
  edit-and-resubmit workflow. Screening duration **not stated**.
- **Formatting:** abstract *"at least 20 characters long"* and *"You can't upload an abstract as a file"* —
  it is a form field. One top-level discipline required. No template, length or reference rule stated; size
  cap not stated.
- **Authorship:** *"Before posting a preprint, verify that you have permission from the original author and
  all co-author(s) to share the work."*; authorship order agreed with co-authors; COI disclosed. The posting
  target is one specific community server (PsyArXiv, SocArXiv, MetaArxiv, …), not "OSF" generically.

---

## 4. Best-practice statements for an ML/NLP paper — what is mandatory where

All pages fetched 2026-10-16. "MANDATORY" below means the fetched venue states it as a requirement (often
enforced by desk rejection for a missing checklist/section); "RECOMMENDED" means the venue asks or encourages.

| Statement | Mandatory at | Recommended / other | Key verbatim quote |
|---|---|---|---|
| **Data-availability** | Springer Nature | NeurIPS, Elsevier | SN, <https://www.springernature.com/gp/authors/research-data-policy>: *"All original articles must include a data availability statement"* |
| **Digital-object identifiers in it** | Springer Nature | NeurIPS | SN, <https://www.springernature.com/gp/authors/research-data-policy/data-availability-statements>: *"If your data are in a repository, include hyperlinks and persistent identifiers (e.g. DOI or accession number) for the data where available."*; *"Data citations should include a persistent identifier (such as a DOI), should be included in the reference list using the minimum information recommended by DataCite (Dataset Creator, Dataset Title, Publisher [repository], Publication Year, Identifier [e.g. DOI, Handle or ARK])"* |
| **Licence statement for released artefacts** | TMLR (the paper is CC BY 4.0); ICML (anonymised at submission) | NeurIPS checklist item 12; ACL | NeurIPS, <https://neurips.cc/public/guides/PaperChecklist>: *"State the name of the license (e.g., CC-BY 4.0) for each asset."*; *"If you are releasing assets, you should include a license, copyright information, and terms of use in the package."* ACL, <https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics>: *"Authors are encouraged to clarify usage terms when releasing research artifacts."* |
| **Limitations section** | ACL Rolling Review (desk reject if missing) | NeurIPS (encouraged) | ARR, <https://aclrollingreview.org/cfp>: *"Authors are required to discuss the limitations of their work in a dedicated section titled "Limitations" … Papers without a limitations section will be desk rejected."*; NeurIPS: *"The authors are encouraged to create a separate "Limitations" section in their paper."* |
| **Compute / resources statement** | NeurIPS checklist item 8 (no checklist ⇒ desk reject) | — | NeurIPS, <https://neurips.cc/public/guides/PaperChecklist>: *"For each experiment, does the paper provide sufficient information on the computer resources (type of compute workers, memory, time of execution) needed to reproduce the experiments?"*; *"The paper should provide the amount of compute required for each of the individual experimental runs as well as estimate the total compute."* |
| **Energy / carbon reporting** | **no source found** | — | Not stated as a requirement on any fetched page. NeurIPS only asks authors to *"consider whether their research is going to negatively impact the environment by, e.g., … producing substantial amounts of greenhouse gasses."* The ML Reproducibility Checklist PDF could not be parsed (3 attempts). |
| **Conflict-of-interest declaration** | Nature Portfolio, Elsevier, ACL, NeurIPS | — | Nature Portfolio, <https://www.nature.com/nature-portfolio/editorial-policies/competing-interests>: *"Nature Portfolio journals' require authors to declare any competing financial and/or non-financial interests in relation to the work described."*; *"all authors … are required to include a statement at the end of their published article to declare whether or not they have any competing interests."* (standard sentence: *"The authors declare no competing interests."*). Elsevier, <https://www.elsevier.com/about/policies-and-standards/publishing-ethics>: *"All authors should disclose in their manuscript any financial and personal relationships … that could be viewed as inappropriately influencing (bias) their work."* ACL: *"Authors, reviewers, and editors must confidentially disclose all relevant affiliations and relationships that may constitute conflicts of interest at the time of submission."* |
| **Funding declaration** | Nature Portfolio, Elsevier, NeurIPS camera-ready | — | Nature Portfolio, <https://www.nature.com/nature-portfolio/editorial-policies/funding>: *"Any relevant funding should be declared in a separate funding statement."* NeurIPS, <https://neurips.cc/Conferences/2026/MainTrackHandbook>: *"Funding Transparency Statement — Your Camera Ready paper must include a funding statement and competing interests disclosures."* Elsevier: *"All sources of financial support for the conduct of the research and/or preparation of the article should be disclosed … If the funding source(s) had no such involvement then this should be stated."* |
| **Author-contributions statement** | Nature Portfolio | Elsevier (CRediT at submission); TMLR optional | Nature Portfolio, <https://www.nature.com/nature-portfolio/editorial-policies/authorship>: *"Authors are required to include a statement of responsibility in the manuscript, including review-type articles, that specifies the contribution of every author."* Elsevier, <https://www.elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement>: *"CRediT statements should be provided during the submission process and will appear above the acknowledgment section of the published paper"* (14 roles, Conceptualization … Funding acquisition). |
| **AI/LLM-use disclosure** | ACL/ARR; ICLR 2027; Elsevier; Springer Nature (above low-risk use) | ICML (encouraged); NeurIPS (only if a core-method component) | see below |

### 4.1 AI/LLM-use disclosure — the actual policies
- **ACL / ACL Rolling Review.** <https://aclrollingreview.org/cfp> (2026-10-16): *"Generally, generative AI
  tools do not qualify for authorship. Their use for writing or coding, as well as its scope, must be
  disclosed in the Responsible NLP Checklist. Details should be included in the Acknowledgements section."*
  <https://www.aclweb.org/adminwiki/index.php/ACL_Policy_on_Publication_Ethics>: *"Generative AI tools and
  technologies may not be listed as authors of a submission … fully disclosed in the Acknowledgements section
  - for instance, "Section 3 was written with inputs from ChatGPT.""* → **in the paper (Acknowledgements) plus
  the checklist.**
- **ICLR 2027.** <https://iclr.cc/Conferences/2027/AIPolicyForAuthors> (2026-10-16): *"we require authors to
  disclose AI use in a mandatory section in their paper (this section will not be counted towards the page
  limit)."* → **a dedicated in-paper section and the submission form.**
- **Elsevier.** <https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals>
  (2026-10-16): *"Authors should disclose the use of AI tools for manuscript preparation in a separate AI
  declaration statement included in their manuscript upon submission."*; *"Authors should not list AI tools as
  an author or co-author, nor cite AI tools as an author."* → **separate declaration statement.**
- **Springer Nature / Nature Portfolio.** <https://www.nature.com/nature-portfolio/editorial-policies/ai>
  (2026-10-16): the red / *"Not permitted"* tier includes *"Assigning authorship or accountability to AI
  systems or tools"*; the green tier is *"Permitted. Disclosure enhances trust and transparency"*; the amber
  tier is *"Permitted with human oversight, verification, and transparency through disclosure."*
- **NeurIPS.** <https://neurips.cc/public/guides/PaperChecklist> (2026-10-16): *"Does the paper describe the
  usage of LLMs if it is an important, original, or non-standard component of the core methods …?"*; handbook:
  *"agents and LLMs cannot be authors."*
- **ICML 2025.** <https://icml.cc/Conferences/2025/CallForPapers> (2026-10-16): *"We encourage authors to
  explain any notable ways in which these tools were used in their research methodology. LLMs are not
  eligible for authorship."*
- **arXiv** (metadata field rule, §1.4): *"Generative AI language tools should not be listed as an author;
  instead authors should refer to moderation related policy."*
- **TMLR** (§2): *"LLMs are not eligible for authorship."*
- **Every fetched venue prohibits AI as an author.** Disclosure location differs: ACL/ARR = checklist +
  Acknowledgements; ICLR = in-paper section + form; Elsevier = separate statement; Springer Nature =
  disclosure required above low-risk use; NeurIPS = only when a core-method component; ICML = encouraged.

---

## 5. Reference / citation style for `article` + inlined `thebibliography`

- **Is a hand-inlined `thebibliography` with manual `\bibitem`s acceptable?** Yes — no fetched venue requires
  BibTeX, and some explicitly endorse inlining:
  - **arXiv**, <https://info.arxiv.org/help/submit_tex.html> (2026-10-16): *"…this file should have the
    `\begin{thebibliography}` or similar command within it, and should be called `foo.bbl`"* — the
    *submission-blocked* rule about a missing `.bib` applies only *"if you use BibTeX/Biber"*. Also
    encouraged: *"We strongly encourage you to include arXiv's `YYMM.NNNNN` identifiers in your reference
    list"*.
  - **Springer Nature**, <https://www.springernature.com/gp/authors/campaigns/latex-author-support>
    (2026-10-16): *"For both submission systems the most reliable way to submit references without error is
    to paste the content of a bibliography file (.bbl) into the main .tex document in place of a
    `\bibliography{…}` command."*; *"…check that the bibliography explicitly contains references as bibitems
    … by copying the contents (individual bibitems) … into the bibliography environment within the main .tex
    file."*
  - **Elsevier**, <https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions>
    (2026-10-16): *"Select the Manuscript item type for .tex, .bbl, .bst, .sty, .bib, .cls, .nls, .ilg, and
    .nlo files."* (no BibTeX-only rule); journal reference style is per the Guide for Authors.
  - **TMLR / ICML / NeurIPS / ICLR 2027:** only the venue style file/template and LaTeX are required; BibTeX
    vs `thebibliography` is **"not stated on the fetched pages"**.
- **What `article` + `thebibliography` produces by default.** LaTeX2e kernel source `ltbibl.dtx`,
  <https://raw.githubusercontent.com/latex3/latex2e/develop/base/ltbibl.dtx> (2026-10-16):
  *"\bibitem\marg{name} : Produces a numbered entry cited as \meta{name}."*; *"The former is used for
  bibliographies with citations like [1], [2], etc."*; default label *"\def\@biblabel#1{[#1]}"* and citation
  form *"\def\@cite#1#2{[{#1…}]}"* → **numeric `[n]` labels by default.**
- **Non-compliance risks, each with support:**
  1. **Undefined citations.** A citation whose key has no `\bibitem` renders as
     *"\hbox{\reset@font\bfseries ?}"* plus *"LaTeX Warning: Citation `<key>' on page <n> undefined"*.
     Springer Nature: *"Double check that the argument to the relevant bibitem matches the citation in the
     text before submitting."*
  2. **Ordering is positional/manual.** The printed number is `\the\value{\@listctr}` written per `\item`,
     so there is **no sorting** — entries appear in the order typed — and the environment takes *"the widest
     bibliography label"* as a hand-computed argument (`{99}` here). Reordering the text does not reorder the
     list.
  3. **Missing identifiers.** `\bibitem` has no structured fields, so nothing is auto-filled. Elsevier only
     *"encourage[s] the use of Digital Object Identifiers (DOIs) as reference links"*; Springer Nature
     requires persistent identifiers for **data** citations; ICML requires camera-ready references be
     *"up-to-date, including up-to-date names and venues"* and to *"replace arXiv citations with peer-reviewed
     papers where possible"* (<https://icml.cc/Conferences/2025/AuthorInstructions>).
- **Not resolved:** `article.cls` itself could not be fetched (5 attempts: `curl` returned 0 bytes;
  `mirrors.ctan.org` cross-origin redirect; `mirrors.mit.edu` *"unsupported content type unknown"*;
  `ftp.fau.de`, `ctan.math.illinois.edu`, `mirror.dogado.de` all 404) and no local LaTeX exists to inspect it
  (`kpsewhich article.cls` empty). The default-label claim therefore rests on the kernel source, which states
  that *"The document class must define the thebibliography environment."*

---

## 6. Audit — the current submission against every requirement

Measured state of `papers/encoder-crossover-190/submission/` (2026-10-16): **6 files** —
`ABSTRACT.txt` (3,416 chars incl. trailing newline / 3,462 B), `ABSTRACT_METADATA.txt` (1,195 B), `BUILD_NOTES.md`, `METADATA.md`, `main.tex`
(80,780 B; sha256 begins `0ee1b11f0692474c174e920b`), `encoder-crossover-190.tar.gz` (26,580 B; one member
`main.tex`, 78,405 B; sha256 begins `0b745948ad00a62ec0681869`). **No `main.pdf`. No TeX toolchain**
(`pdflatex`/`latexmk`/`tectonic`/`xelatex` absent). `main.tex` is pure ASCII. **There are zero `\cite`
commands in `main.tex` while 13 `\bibitem`s exist.**

> **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, VUFMT1 Check 4; re-measured by
> UFMT3).** This line formerly read `ABSTRACT.txt` (**3,416 B**). 3,416 is a character count and the file is
> **3,462 bytes**; the counts are reconciled in §0.2 item 12, so the two figures are not contradictory.

| ID | Requirement (route) | Source | Status | Smallest concrete fix |
|---|---|---|---|---|
| R1 | TeX source compiles from the **root**; no nested dirs | arXiv submit_tex: *"compilation is always done from the root"* | PASS | none — `main.tex` is a top-level single member |
| R2 | No compiler by-products / extraneous files in the package | arXiv submit_tex strip list | PASS | none — tarball holds only `main.tex` |
| R3 | Bibliography must resolve without a network round trip | arXiv submit_tex (`.bbl` or `thebibliography`) | PASS | none — bibliography is inlined; no `.bib` needed |
| R4 | **Metadata abstract ≤ 1920 characters** | arXiv prep: *"abstracts longer than 1920 characters will not be accepted"* | **FAIL as it stands** | paste `ABSTRACT_METADATA.txt` (1,195 chars) into the metadata field; keep the full 3,415-char abstract in the PDF |
| R5 | Metadata abstract: no "Abstract" word, ASCII only, no TeX-isms | arXiv prep field rules | PASS | none for `ABSTRACT_METADATA.txt` (ASCII, no "Abstract") |
| R6 | **No anonymous submissions — real author names required** | arXiv prep: *"Anonymous submissions are not accepted."* | **FAIL** | `main.tex:12` `\author{AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED}` → replace with the real name |
| R7 | Affiliations in parentheses, city+country only | arXiv prep: *"Affiliations must be placed within parentheses."* | **FAIL** | supply affiliation; in the metadata form use `Author One (1)` / `(1) Institution, City, Country` |
| R8 | Title: not all-caps, ASCII, no opaque macros | arXiv prep title rules | PASS | none — title is sentence case and ASCII |
| R9 | Licence chosen is **irrevocable** | arXiv license: *"The license chosen is irrevocable and cannot be changed."* | **DECISION REQUIRED** | `METADATA.md`/abstract already record CC BY 4.0; confirm once, then it cannot change |
| R10 | **Endorsement for cs.CL** | arXiv endorsement: *"arXiv requires that users be endorsed…"* | **FAIL (external blocker)** | author requests personal endorsement; requires a six-character endorsement code from an endorser |
| R11 | Ancillary files: TeX may not go in `anc/` | arXiv ancillary: *"TeX files should not be included in the ancillary file directory."* | PASS | none — no `anc/` is shipped |
| R12 | Size limits (total/per-file/extracted) | arXiv sizes/tar | **NOT STATED** | no rule to satisfy; package is 26,580 B anyway |
| R13 | PDF: fonts embedded, machine-readable, no embedded JS, 10–14 pt | arXiv submit_pdf + format_requirements | **NOT CHECKABLE HERE** | build with TeX Live elsewhere, then inspect fonts and page count |
| R14 | `00README` not required | arXiv 00README: *"not required (nor recommended)"* | PASS | none |
| R15 | `\date{}` empty is acceptable | — | NOT STATED | optional: set a date or leave empty; the "avoid `\today`" rationale is unverified here |
| R16 | **Do not publish author-side working files** (everything in the tarball is public) | arXiv (package is the article) | **RISK** | keep `ABSTRACT.txt`, `ABSTRACT_METADATA.txt`, `METADATA.md`, `BUILD_NOTES.md` **out** of the tarball (already true for the tarball; do not switch to uploading the folder) |
| R17 | **Remove draft-status / internal-notes front matter before posting** | arXiv publishes what is uploaded | **FAIL (quality)** | `main.tex:16-18` — the three bold paragraphs beginning *"Draft status: submission-candidate…"* should be deleted (or moved into `BUILD_NOTES.md`) |
| R18 | **Every bibliography entry cited in text** | LaTeX kernel: *"\bibitem … Produces a numbered entry cited as \meta{name}."*; SN: *"the argument to the relevant bibitem matches the citation in the text"* | **FAIL** | 13 `\bibitem`s, **0 `\cite` commands**: add a `\cite{…}` at each of the 13 in-text mentions (or cite a subset and delete the rest) |
| R19 | Inlined `thebibliography` is compliant (no BibTeX requirement) | arXiv submit_tex; Springer Nature LaTeX support | PASS | none |
| R20 | arXiv reference-harvester identifiers (`arXiv:YYMM.NNNNN`) present | arXiv submit_tex *"strongly encourage"* | PASS | none — entries print `arXiv:2602.06370` etc. |
| R21 | TMLR: **PDF built with the TMLR stylefile/template** | TMLR author-guide: *"Submissions must be PDF files generated using the TMLR LaTeX stylefile and template."* | **FAIL** | replace `\documentclass[11pt]{article}` (`main.tex:1`) with the TMLR template; build the PDF on a TeX machine |
| R22 | TMLR: **anonymised submission** | TMLR author-guide: *"TMLR uses a double blind review process and submissions must be anonymized."* | **FAIL** | anonymised build (no authors, no self-identifying links); must **not** link the arXiv version |
| R23 | TMLR: licence CC BY 4.0 from submission | TMLR author-guide: *"All TMLR submissions … are licensed under CC BY 4.0."* | PASS | consistent with the paper's stated CC BY 4.0 |
| R24 | TMLR: arXiv preprint is compatible | TMLR editorial-policies: *"It is acceptable … on preprint servers such as arXiv"* | PASS | none — but keep the TMLR PDF unlinked to the arXiv version |
| R25 | TMLR: all authors need complete OpenReview profiles (affiliation, COI, funding) | TMLR author-guide/editorial-policies | **FAIL (author action)** | author creates/completes the OpenReview profile; single-author case is simple |
| R26 | TMLR: supplementary ≤100 MB, PDF or ZIP, anonymised | TMLR author-guide | NOT APPLICABLE | omit supplementary, or zip an anonymised code/data subset |
| R27 | TMLR: Broader Impact Statement only *"If their work carries a significant risk of harm"* | TMLR author-guide | PASS (conditional) | none stated for this paper |
| R28 | Preprints.org: LaTeX accepted, all files needed included in a zip | Preprints.org instructions | PASS | zip `main.tex` (self-contained; no `.bib` is needed because the bibliography is inlined) |
| R29 | Preprints.org: licence is fixed CC BY 4.0 | Preprints.org about | PASS | consistent |
| R30 | Preprints.org: **first page must carry title, author list, abstract, keywords, corresponding-author contact, affiliations** | Preprints.org instructions | **FAIL** | the same author-block fix as R6/R7, plus add keywords and corresponding-author contact to the first page |
| R31 | Preprints.org: Conference Paper type excludes papers with a DOI | Preprints.org instructions | **CONSTRAINT** | if the arXiv posting happens first, submit as a *preprint article*, not a *Conference Paper* |
| R32 | Research Square: **only `.doc/.docx/.pdf` accepted** | Research Square editorial: *"We accept the following file formats: .doc, .docx, .pdf."* | **FAIL** | supply `main.pdf` (build with TeX outside) or convert to `.docx`; `main.tex` cannot be uploaded |
| R33 | Zenodo: any format; licence required; DOI auto-minted | Zenodo about-records / licenses | PASS | upload the tarball or a zip; licence field must be set (CC BY 4.0 default) |
| R34 | Zenodo: ≤100 files / 50 GB per record | Zenodo manage-files | PASS | trivial (one file) |
| R35 | OSF Preprints: PDF advised; abstract pasted in the form (≥20 chars) | OSF help 376 | PASS (with PDF) | upload `main.pdf`; paste `ABSTRACT_METADATA.txt` (1,195 chars > 20) |
| R36 | Data-availability statement **with persistent identifiers** | Springer Nature research-data policy + statements | **PARTIAL** | `main.tex:405` `\section*{Data and code availability}` states the licence and the subset but cites **no DOI**; mint a Zenodo DOI and cite it |
| R37 | Explicit licence statement for released artefacts | NeurIPS checklist item 12 | PASS | `main.tex:407` (paper CC BY 4.0) and `main.tex:425` (code PolyForm Noncommercial 1.0.0 + paid commercial licence) |
| R38 | Limitations section | ACL/ARR *"desk rejected"* if missing | PASS | `main.tex:302` `\section{Limitations}` with six subsections |
| R39 | Compute/resources statement | NeurIPS checklist item 8 | **FAIL** | no compute statement exists (only `MANUSCRIPT.md:723` *"reports no tuning-effort or compute study"*); add one short paragraph (host, CPU/GPU, memory, wall-clock per arm) |
| R40 | COI declaration | Nature/Elsevier/ACL/NeurIPS | **FAIL** | absent; add *"Competing interests: The authors declare no competing interests."* |
| R41 | Funding declaration | Nature/Elsevier/NeurIPS | **FAIL** | absent; add a funding statement, or state that no funding was received |
| R42 | Author-contributions statement | Nature Portfolio *"required … every author"* | **FAIL** | absent; add an "Author contributions" statement (CRediT roles if Elsevier) |
| R43 | AI/LLM-use disclosure | ACL/ARR, ICLR, Elsevier, Springer Nature (mandatory); ICML/NeurIPS (lighter) | **FAIL** | absent; add an explicit AI-use statement (a one-line "no generative AI was used" is the safe form where disclosure is mandatory) |
| R44 | No PDF-dependent rule can be satisfied without a PDF | — | **NOT CHECKABLE HERE** | build and inspect off-machine |

**Summary: 12 FAILs the author can fix locally, 4 author-action blockers, 2 hard external blockers, 1 partial,
2 not checkable, and **2** §6 rows marked *NOT STATED* (R12, R15) plus **≥9** distinct not-stated
items recorded in the prose, none of which must be invented.**

> **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, VUFMT1 Check 5/6).** This line
> formerly said *"3 "not stated" items"*. §6 carries **2** such rows (R12, R15); the prose records **≥9**
> distinct not-stated items — see the counting rules in the header.

---

## 7. What the single submittable item should be, per route

| Route | One item to submit | Goes in | Must stay out |
|---|---|---|---|
| **arXiv** (cs.CL, cross-list cs.LG) | `encoder-crossover-190.tar.gz` (26,580 B, single member) **or** `main.tex` alone — after the author block, date and draft-status paragraphs are fixed | `main.tex` only; metadata typed from `ABSTRACT_METADATA.txt` (1,195 chars) + the real author line; licence CC BY 4.0 | `ABSTRACT.txt`, `ABSTRACT_METADATA.txt`, `METADATA.md`, `BUILD_NOTES.md`, the tarball itself inside a tarball, any `.aux/.log/.out/.pdf`, and no `anc/` |
| **TMLR** | an **author-built anonymised PDF** from a `main.tex` moved onto the TMLR style template | the PDF (OpenReview upload); optionally a ≤100 MB anonymised PDF/ZIP supplement | author names, affiliations, acknowledgements that identify, and **any link to the arXiv version** |
| **Preprints.org** | a **zip containing `main.tex`** (self-contained; no `.bib` needed) | source on the first page: title, authors+affiliations, abstract, keywords, corresponding-author contact; licence CC BY 4.0 (fixed) | author-side working files (`METADATA.md`, `BUILD_NOTES.md`, `ABSTRACT*.txt`) |
| **Research Square** | **`main.pdf`** (or a `.docx`) | the PDF/DOCX; abstract and metadata in the form | `main.tex` — the venue lists only `.doc/.docx/.pdf` |
| **Zenodo** | a **zip** holding `main.tex` + `main.pdf` (+ the release bundle if desired) | everything intended as the record; licence field CC BY 4.0; DOI auto-minted | harness-less bundle content the paper says is withheld — keep the record's contents consistent with `main.tex:405-425` |
| **OSF Preprints** | **`main.pdf`** | the PDF; the abstract pasted into the form field (≥20 chars); a community server chosen | unpublished working files |

**One-line decision:** for every route except TMLR the same two files are the payload — `main.tex` and a PDF
built from it — plus the real author block. TMLR additionally needs the TMLR style template, an anonymised
build, and no link to the arXiv posting.

> **SUPERSEDED (2026-10-16, source `strategy/VERIFICATION_REPORT_FMT1.md`, VUFMT1 Contradiction D; re-measured
> on disk by UFMT3).** The **arXiv** row above recommends `encoder-crossover-190.tar.gz` as the payload. At
> verification time that tarball's member `main.tex` was a **stale revision** — **78,405 bytes / mtime
> 13:52**, diverging from the then-audited **80,780-byte** `main.tex` (mtime 14:18) at **byte 15,750, line
> 81** — so the payload recommendation described a stale revision. As of UFMT3's measurement at 2026-10-16 14:57 CDT = 2026-10-16 19:57 UTC
> the rebuild has landed — the tarball member and `main.tex` are byte-identical (**83,774 bytes, mtime
> 2026-10-16 14:55 CDT**) — so the payload recommendation is no longer stale.
> The single-member shape still holds, but the rebuilt tarball is **28,631 bytes**, not the
> 26,580 bytes quoted in the arXiv row above — that figure describes the pre-rebuild tarball.

---

## 8. What CANNOT be checked on this machine (stated, not implied)

1. **Every PDF-dependent requirement** (R13, R44): fonts embedded / outline not bitmap, machine-readable
   text, no embedded JavaScript, the 10–14 pt and 1-inch-margin layout rule, page count, overfull tables,
   and arXiv's own compile succeeding. **There is no TeX toolchain here** (`pdflatex`, `latexmk`, `tectonic`,
   `xelatex` all absent) and **no `main.pdf` exists** — nothing in this repository can produce or inspect the
   PDF. These are therefore **unverified**, never "passing".
2. **arXiv size limits (R12):** the current pages state no quota, so there is no rule to test against —
   recorded as *not stated*, not as satisfied.
3. **Endorsement (R10):** cannot be obtained or verified here; it needs the author's own arXiv account and a
   personal endorser, who issues a six-character code.
4. **Author-only facts:** the real name, affiliation, e-mail, ORCID, COI, funding, AI-use facts, and the
   `Comments` page/figure count all depend on information not present in the repository
   (`main.tex:12`, `METADATA.md:12-17`).
5. **Venue items the pages themselves do not state:** TMLR's DOI policy and the exact `\usepackage` token
   (style package is only linked as a zip); Research Square's licence default and DOI registrar; OSF
   screening duration and size cap; Zenodo "concept DOI" wording and prefix.
6. **`article.cls`** could not be fetched (5 attempts) and no local LaTeX exists; the default numeric-label
   claim rests on the LaTeX kernel source, which also states *"The document class must define the
   thebibliography environment."*

---

## 9. Source inventory (all fetched 2026-10-16)

arXiv: `help/submit_tex.html`, `help/submit_pdf.html`, `help/submit/index.html`, `help/tar.html`,
`help/sizes.html`, `help/faq/mistakes.html`, `help/prep.html`, `help/license/index.html`,
`licenses/nonexclusive-distrib/1.0/` (arxiv.org), `help/ancillary_files.html`, `help/endorsement.html`,
`help/replace.html`, `help/versions.html`, `help/00README.html`, `help/policies/format_requirements.html`
(15 pages; `help/license/options.html` → 404; size-limit figures not found; compile-time limit not found).
TMLR: `jmlr.org/tmlr/author-guide.html`, `jmlr.org/tmlr/editorial-policies.html`, `jmlr.org/tmlr/submissions.html`,
`jmlr.org/tmlr/faq.html`.
Preprint servers: `preprints.org/instructions-for-authors`, `preprints.org/about`,
`researchsquare.com/legal/editorial`, `researchsquare.com/researchers/preprints`,
`help.zenodo.org/docs/deposit/about-records/`, `about.zenodo.org/policies/`,
`help.zenodo.org/docs/deposit/describe-records/licenses/`, `help.zenodo.org/docs/deposit/manage-files/`,
`help.zenodo.org/docs/share/submit-for-review/`, `help.osf.io/article/376-preprints-home-page`.
Policies: `springernature.com/gp/authors/research-data-policy`,
`springernature.com/…/research-data-policy/data-availability-statements`,
`neurips.cc/Conferences/2026/MainTrackHandbook`, `neurips.cc/public/guides/PaperChecklist`,
`aclweb.org/adminwiki/…/ACL_Policy_on_Publication_Ethics`, `aclrollingreview.org/cfp`,
`elsevier.com/about/policies-and-standards/research-data`,
`elsevier.com/about/policies-and-standards/publishing-ethics`,
`elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals`,
`elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement`,
`elsevier.com/researcher/author/policies-and-guidelines/latex-instructions`,
`acm.org`-adapted TMLR authorship section (via TMLR editorial-policies),
`nature.com/nature-portfolio/editorial-policies/competing-interests`,
`nature.com/nature-portfolio/editorial-policies/funding`,
`nature.com/nature-portfolio/editorial-policies/authorship`,
`nature.com/nature-portfolio/editorial-policies/ai`, `icml.cc/Conferences/2025/CallForPapers`,
`icml.cc/Conferences/2025/AuthorInstructions`, `iclr.cc/Conferences/2027/AIPolicyForAuthors`,
`iclr.cc/Conferences/2027/AuthorGuidelines`, `springernature.com/gp/authors/campaigns/latex-author-support`.
Kernel: `raw.githubusercontent.com/latex3/latex2e/develop/base/ltbibl.dtx`.

Full verbatim quote sets, including quotes not repeated above, are stored at
`scratch/ufmt1/arxiv_notes.md`, `scratch/ufmt1/preprint_notes.md`, `scratch/ufmt1/policy_notes.md`.
