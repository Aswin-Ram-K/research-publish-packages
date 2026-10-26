# Build notes — Markdown -> LaTeX conversion (earlier pass)

> **Note on names.** Build tooling and intermediate directories named in this file are author-side and are **not distributed** with the submission.


> **STATUS 2026-10-16 (earlier pass):** the figures and paths in this file are *dated build history* — each reflects the unit that wrote it. The shipped payload was re-measured from disk and the current values are in the **Update 2026-10-16 (earlier pass)** section at the end of this file; where the two disagree, that section is authoritative. Nothing was deleted.


Converter: `md2tex.py` (reproducible; re-running rewrites `main.tex`). **[2026-10-16: SUPERSEDED — the converter in use is `md2tex.py`; `md2tex.py` is a retired build directory]**
Nothing in `MANUSCRIPT.md` was edited or deleted. Output: `main.tex` (78,405 bytes, ASCII-only). **[2026-10-16: SUPERSEDED — current `main.tex` is 84,223 bytes / sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`] **[an earlier pass 2026-10-18: SUPERSEDED — the current `main.tex` is 84,695 bytes / sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`, 467 lines]** **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 84,967 B / sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc`]**

## Source inventory (`MANUSCRIPT.md`)

- 864 lines, 66,671 bytes, **9,781 words** (whitespace-delimited). **[2026-10-16: SUPERSEDED — current `MANUSCRIPT.md` is 71,110 bytes / sha256 `8ba18a51f4b841a59cff73ee71a22d61a67cd7e0cb411a35495ba37f59d5d636`; line/word counts not re-derived here]**
- **32 headings**: 10 level-2, 22 level-3. Level-2 in order: *Abstract*; *1. Introduction*;
  *2. Related work*; *3. Method*; *4. Results*; *5. Discussion*; *6. Limitations*;
  *7. Reproduction*; *Data and code availability*; *References* — i.e. **7 numbered sections and
  22 numbered subsections**, plus 2 unnumbered sections.
- Constructs converted: **5 pipe tables** (44 source lines), **269 code spans**, **3 block quotes**
  (14 lines), **45 bullet items**, **16 ordered-list items**, 9 horizontal rules, 12 bibliography
  entries.
- Absent, so nothing to convert: **0 footnotes, 0 images, 0 raw HTML, 0 inline/display math
  (`$...$`), 0 raw-LaTeX passthrough, 0 nested lists**.
- **21 distinct non-ASCII characters**, all mapped, 0 left over:
  § → `\S`; κ → `$\kappa$`; ≈ → `$\approx$`; ≥/≤ → `$\ge$`/`$\le$`; × → `$\times$`; ± → `$\pm$`;
  → → `$\to$`; ↔ → `$\leftrightarrow$`; Δ → `$\Delta$`; ψ → `$\psi$`; χ → `$\chi$`; ² → `$^{2}$`;
  ₁/₂ → `1`/`2`; … → `\ldots{}`; em dash → `---`; en dash → `--`; ✅ → `$\checkmark$`;
  **⚠ (U+26A0) → ASCII `!`** (4 occurrences — the only substitution that changes a glyph to a
  different character; use XeLaTeX/LuaLaTeX or a symbol package if the warning sign is wanted).

## Conversion decisions (all reversible; the source is untouched)

1. `\documentclass[11pt]{article}` + `inputenc`/`fontenc`/`amsmath`/`amssymb`/`url`/`array` only.
   `url` is needed because six bibliography entries print URLs; `array` only for ragged-right
   `p{...}` table columns. No exotic packages, no arXiv style files, no images.
2. Manual section numbers are **stripped** ("## 3. Method" -> `\section{Method}`) so LaTeX's
   automatic numbering reproduces the manuscript's exactly (1–7 with the same subsection numbers),
   which keeps every in-text cross-reference ("§3.3", "§4.5", "§11.6") correct by construction.
3. `## Abstract` -> `abstract` environment. `## Data and code availability` and `## References` ->
   `\section*` (unnumbered), so they do not shift the numbered sequence.
4. The three front-matter status paragraphs (draft-status line, the `classify-encoder` primary-
   baseline declaration, the title-figure warning) are reproduced **verbatim** ahead of the
   abstract. They are candidate deletions for the final submission; they were not deleted because
   this unit's instruction is to preserve the manuscript's words.
5. **Bibliography is inlined** as a `thebibliography` environment generated from `REFERENCES.bib`
   (12 entries). No `\cite` keys exist in the manuscript (sources are named in prose and by
   back-ticked corpus key), so all 12 entries print as the reference list — exactly what the
   manuscript's prose *References* section describes. Consequence: **nothing but `main.tex` is
   needed to compile; no BibTeX/Biber run and no network round trip.**
6. `references.bib` is deliberately **not** shipped: arXiv's advice is that a bare `.bib` with no
   `\bibliography` call means you forgot to run BibTeX. All content is inlined instead.
7. The `.bib` `note = {...}` fields (long internal annotations, e.g. "SOURCED (identifier only) ...
   a human must complete this entry") are **not printed** — they are working notes, not paper
   text, and `REFERENCES.bib`'s own header says "Do not submit until they are completed".
   Entries still missing an author and/or title carry a visible
   `[Author and/or title not recorded in the corpus --- to be completed before submission.]`
   marker; these include the identifier-only `arxiv2602_06370`, `arxiv2512_12677` and the internal
   `source_decider_stack_2026`. **The printed reference list is therefore not submission-ready for
   those entries** — the author must complete them.
8. `benayas2024comparative` (present only in `REFERENCES_ADDITIONS.bib`) is **excluded**, matching
   the added paper's own statement that the 125M-RoBERTa claim "is not in the bibliography and is
   not used". The merged `REFERENCES.bib` already omits it.
   **Note 2026-10-16 (an earlier pass):** superseded. an earlier pass proved from the primary source (DOI
   `10.1007/s10579-024-09796-y`) that the claim does have a locatable identifier; `benayas2024comparative`
   is now merged into `REFERENCES.bib` and the printed list carries 13 `\bibitem` entries. The three lines
   above are the 2026-10-15 build record and are retained unchanged. The `.bib` `note` fields remain
   unprinted working notes (item 7 above still holds).
9. Straight double quotes are paired into LaTeX ``...''; apostrophes are left as `'` (LaTeX renders
   them as the right single quote). LaTeX specials (`& % $ # _ { } ~ ^ \`) are escaped in prose and
   code spans; `\textbackslash{}` is used for the one literal backslash (`grep -P '\x{2212}'`).
10. ~~Author block is a placeholder (`AUTHOR NAME TO BE SUPPLIED \\ AFFILIATION TO BE SUPPLIED`) and
    `\date{}` is empty; both must be replaced by the author.~~ **SUPERSEDED 2026-10-16: the author
    block is filled — `main.tex:12` carries `\author{Aswin Ram Kalugasala Moorthy}` (name only, no
    affiliation); `\date{}` is still empty.** `\sloppy` is set to reduce overfull
    boxes from long file paths in narrow table columns.

## Structural self-checks on `main.tex` (no compiler involved)

- braces balanced **1020 / 1020**; 0 lines with unbalanced braces
- `\begin`/`\end` environment counts match exactly; 0 residual non-ASCII; 0 residual `**`;
  0 unpaired straight quotes; 0 residual markdown backticks (the 174 backtick characters are
  LaTeX opening double quotes)
- 7 `\section{`, 22 `\subsection{`, 2 `\section*{`, 5 `tabular`, 12 `\bibitem`, 1 `abstract`, **[2026-10-16: SUPERSEDED — current `main.tex` carries 13 `\bibitem` (23 `\cite` over 13 distinct keys), not 12]**
  1 `thebibliography`, 3 `quote`, 13 `itemize`, 3 `enumerate`
- **Not verified by a compiler**: no TeX toolchain exists on this host (`pdflatex`, `latexmk`,
  `tectonic`, `xelatex`, `bibtex` all absent). No PDF was produced and none was faked; page count **[2026-10-16: SUPERSEDED — a PDF now exists: `rendered/encoder-crossover-190.pdf`, 184,933 bytes, 25 pages, A4]**
  and overfull-box warnings are unknown until someone runs `pdflatex main.tex` twice.

## Packaging

`encoder-crossover-190.tar.gz` (26,580 bytes) contains exactly one member, `main.tex`, at the top **[2026-10-16: SUPERSEDED — current tarball is 28,556 bytes / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed`, exactly 1 member `main.tex`]** **[2026-10-18: SUPERSEDED — the figure recorded above is itself now stale: the tarball is now 28,554 B / sha256 `76dfe5dbcdc46b4b2da394ca5f9d1a3ce72da3a81f0e37a0034c33367a09e42b`, exactly 1 member `main.tex`. The 28,556 B / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed` figure above was already stale when measured from disk before this unit's edit (28,536 B / sha256 `0d470f7b532904085c3056f7a63fe5240a87d0d63e7337dfb1239cc912d81bde`). See the an earlier pass update at the end of this file.]**
level — far inside arXiv's 10 MB total / 5 MB per file / 50 MB extracted limits, and single-level
as `tar.html` requires. `ABSTRACT.txt` and `METADATA.md` are **author-side working files only**:
everything in an arXiv source upload is published, so do not upload the `submission/` directory
wholesale — upload `main.tex` alone, or this tarball.

## Update 2026-10-16 — formatting requirements R6/R7/R17/R18/R36/R39–R43

Supersedes items 4, 5 and 10 above; the earlier numbers are retained as the earlier build record.
`MANUSCRIPT.md` **was** edited this time (the earlier note that it wasn't is historical), and
`md2tex.py` was extended. `main.tex` is regenerated, never hand-patched.

- **R17** — the three front-matter status paragraphs (`main.tex:16-18` before, from
  `MANUSCRIPT.md:3`/`:10`) are **deleted from the source**; the body now opens directly with the
  abstract. No fact was dropped: the baseline declaration and the deliberate title-figure change are
  stated in §3.3 and in the abstract, and a new methods sentence at the end of §3.3 says so
  explicitly. Item 4 above is therefore superseded.
- **R18** — `md2tex.py` now carries a 13-entry `CITE_ANCHORS` table; each anchored in-text mention
  becomes a real `\cite{key}`. `main.tex` now has **13 `\bibitem` and 23 `\cite` occurrences over
  exactly 13 distinct keys, with no uncited key and no `\cite` lacking a `\bibitem`**. The converter
  hard-fails on either condition, so this cannot regress silently. Item 5 above is superseded.
- **R6/R7 (SUPERSEDED — see the an earlier pass update at the end of this file)** — one author slot only: `\author{AUTHOR SLOT: REAL NAME (INSTITUTION, CITY, COUNTRY) ---
  TO BE SUPPLIED}`. No name was invented; the exact paste string is in `METADATA.md`. Item 10 above
  is superseded.
- **R36 + R39–R43** — six new unnumbered sections after *Data and code availability*: *Persistent
  identifier* (Zenodo DOI slot, pending), *Compute and resources*, *Author contributions*,
  *Funding*, *Competing interests*, *Use of AI tools*. Six `AUTHOR TO CONFIRM` markers remain; they
  are tabulated in `METADATA.md`.
- **Internal unit IDs** — `an earlier pass`, `UPAPER1c`, `an earlier pass` removed from the reference-list prose; every
  citation fact kept.
- **Stale release path** — the reproduction and data-availability sections now describe the package
  that actually ships: **29 files, no evaluation harness**, containing `verify/recompute-claims.py`.
  No local scratch path is named anywhere.

Main.tex is now **83,774 bytes**, sha256
`30e162b4cc6d7b3ae97d03141f3a35e808222be8b6d5a90d439878ba9ce85646`. Regenerating twice gives a
byte-identical file (`cmp` clean), and the regenerated `main.tex` has **0 non-ASCII characters**,
balanced `\begin`/`\end` (**32/32**), **13 `\bibitem`**, and none of the draft-status strings. The
tarball was rebuilt: **28,631 bytes, exactly one member (`main.tex`)**; `ABSTRACT.txt`,
`ABSTRACT_METADATA.txt`, `METADATA.md` and `BUILD_NOTES.md` are not inside it. Still not compiled —
no TeX toolchain exists on this host, so page count remains unknown.

## Update 2026-10-16 — author slot is now name-only

Supersedes the **R6/R7** author-slot wording above and the size/hash figures in the an earlier pass update.
The author's standing decision is **name only, no affiliation**, matching paper #7
(`submission/main.tex:10`). `md2tex.py:300` now emits
`\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}` and `main.tex` was regenerated (never hand-edited)
by `python3 md2tex.py`. The **only** changed line versus the pre-change file is the author
line (proven by diff). Item 10 above was already historical under an earlier pass and remains so.
Previous values, retained: an earlier pass recorded `main.tex` 83,774 bytes / sha256
`30e162b4cc6d7b3ae97d03141f3a35e808222be8b6d5a90d439878ba9ce85646`; the actual pre-correction file was
83,700 bytes / sha256 `087aedf10ed06762018fd3da1019ff30317e1fbeed6e62fe6559dcd20b5fd3f1`, tarball
28,403 bytes / sha256 `9f757c0391ec9aaa29e1800d37430885fe4adb22f0d6c5d8f461904f105134e1`.
New values are recorded in the author-line handoff record.

## Update 2026-10-16 (earlier pass) — shipped-instrument digest corrected; main.tex regenerated

The shipped-instrument digest in `MANUSCRIPT.md` §7 (and hence `main.tex`) was stale: removing five
comments from `fixture/reflex-decisions.ts` in the shipped package changed its bytes, and
`MANIFEST.json` was regenerated. `MANUSCRIPT.md` now cites the regenerated digest `89e77a8e…e169`
(81,439 bytes), and `main.tex` was regenerated (never hand-patched) by
`python3 md2tex.py`. Running the converter twice gave a byte-identical file (`cmp`
clean). New `main.tex`: 83,832 bytes, sha256
`90db2cd4e7fa6a63d4b91e2c0636c3879de54fc2a4e7f55fcbf2cce4197c9b86`. The tarball was rebuilt with
exactly one member (`main.tex`) whose bytes match the source: 28,569 bytes, sha256
`d5e49ad5a96c478d280579c79d5c6e542d3ca770146b62c7c0ae498a9783e795`. Earlier size/hash figures above
are retained as the dated build record.

---

## Update 2026-10-16 — author slot FILLED; earlier instruction REVERSED by the author

The text above recording that the author slot is unfilled and "must not be filled by an agent" is
**superseded by the author's own instruction**. It is retained above as history; nothing was deleted.
The author supplied the name verbatim, name only, no affiliation:

    \author{Aswin Ram Kalugasala Moorthy}

- Shipped line: `submission/main.tex:10` — exactly one `\author` line, equal to the
  string above. No affiliation, no comma, no initial, no reordering.
- Single source of truth: the per-package `author_line` value in `md2tex.py`
  (all three packages carry the identical value; `require_author_slot=True` enforces exactly one
  `\author` line equal to it, so a different name, a missing byline or a second line each hard-fail).
- Payload regenerated with `python3 md2tex.py --package encoder-crossover-190`; two independent runs were
  byte-identical to each other and to the shipped file (`cmp`), and the rebuilt tarball's single
  member is byte-identical to the on-disk `main.tex` (`cmp` after extraction).
- New `main.tex`: **84345 bytes**, sha256 `9cab7a4324509423bc9c24ac47e1faa7facff9128659278738ce585a4d35657d`.
  New `encoder-crossover-190.tar.gz`: **28526 bytes**, sha256 `8f76901a6e33803f165d1917983bbe1986503a4851b9a84640ede6a06125ced6` (container digest is not bit-reproducible; the member is).
- Invariants re-proven: bibitems/cited-keys/uncited as before, 0 non-ASCII, `\begin`/`\end` balanced,
  exactly one `\author` line, and the numeric-literal multiset of `main.tex` is unchanged (only the
  33-char byline replaced the 46-char placeholder: −13 bytes).


## Update 2026-10-16 --- PDF compiled and installed

The "no TeX toolchain" statements above are **dated history**. A toolchain is now present at
`tectonic`. `main.tex` was rebuilt with
`tectonic -r 1 --keep-logs -o <outdir> submission/main.tex`
(`HOME`, `TMPDIR`, `TECTONIC_CACHE_DIR` exported inside the workspace; **without**
`-Z continue-on-errors`): exit **0**, **0** `Undefined control sequence`, **0** LaTeX `!` errors.
The PDF is installed at `rendered/encoder-crossover-190.pdf` --- **183,863 bytes, 24 pages, A4
(595.28 x 841.89 pts), sha256 `0d874106d7d0db0d7356a24e2156c48c826630cc9394aff1786696c0d763b5fb`**.


---

## Update 2026-10-16 — measured build-record correction

A build pass re-measured the shipped payload **from disk** and corrected every figure or path in
this file that no longer matches it. Nothing was deleted: superseded values above remain as dated build
history, and the table gives the old value beside the current one. No measured number, claim, reference,
bibliography entry or `main.tex` byte was changed — records only.

Converter actually in use: `md2tex.py` (44,777 bytes, sha256
`97d34349f11ad15a1af2cf0b5bbbf61def02beb6b1a5ebb3f32de7778bfa63e4`). `md2tex.py`
still exists on disk but is a **retired build directory**, not the current converter.

| Figure | Superseded value | Measured 2026-10-16 (current) |
|---|---|---|
| converter | `md2tex.py` | `md2tex.py` (44,777 B, sha256 `97d34349…`) |
| `submission/main.tex` | 78,405 B; then 83,774 / 83,700 / 83,832 / 84,345 | **84,223 B**, sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`, 467 lines **[an earlier pass 2026-10-18: SUPERSEDED — current `main.tex` is 84,695 bytes / sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`, 467 lines]** **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 84,967 B / sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc`]** |
| bibliography | 12 `\bibitem` (earlier pass) | **13 `\bibitem`**, 23 `\cite` over 13 distinct keys |
| `submission/encoder-crossover-190.tar.gz` | 26,580 B; then 28,631 / 28,403 / 28,569 / 28,526 | **28,556 B**, sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed`, exactly 1 member `main.tex` **[2026-10-18: SUPERSEDED — measured 2026-10-16: the tarball is now 28,554 B / sha256 `76dfe5dbcdc46b4b2da394ca5f9d1a3ce72da3a81f0e37a0034c33367a09e42b`, exactly 1 member `main.tex`. The 28,556 B / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed` figure above was already stale when measured from disk before this unit's edit (28,536 B / sha256 `0d470f7b532904085c3056f7a63fe5240a87d0d63e7337dfb1239cc912d81bde`). See the an earlier pass update at the end of this file.]** |
| PDF | "no toolchain / no PDF / page count unknown" | **exists** `rendered/encoder-crossover-190.pdf`: 184,933 B, **25 pages**, A4 595.28 x 841.89 pts, sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44` **[an earlier pass 2026-10-18: SUPERSEDED — the installed PDF is now 188,364 B, 25 pages A4, sha256 `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1`; the 184,933 B build is preserved at `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-58c22c90.pdf`]** |
| `MANUSCRIPT.md` | 66,671 B / 864 lines / 9,781 words (earlier pass) | **71,110 B**, sha256 `8ba18a51f4b841a59cff73ee71a22d61a67cd7e0cb411a35495ba37f59d5d636` (line/word counts not re-derived) |

Left in place deliberately, because dated history is correct as history: the earlier build record, the
an earlier pass / an earlier pass / an earlier pass / an earlier pass size-and-hash series, and the the earlier PDF values (183,863 B,
24 pages, sha256 `0d874106d7d0db0d7356a24e2156c48c826630cc9394aff1786696c0d763b5fb`) — the PDF was
recompiled after an earlier pass, which is why size and page count moved too.


---

## Update 2026-10-17 --- AI-tools disclosure names the tools

Supersedes the AI-use wording (a bare "generative-AI assistant") and the size/hash figures above; every
earlier figure is retained as dated build history. `MANUSCRIPT.md` **was** edited (the *Use of AI tools*
paragraph only --- one paragraph, first-person register, tools named); `main.tex` was regenerated, never
hand-patched, with `python3 md2tex.py --package encoder-crossover-190` (two runs byte-identical,
and identical to the shipped file).

Tool line as installed: **DeepSeek Harness**, chiefly `deepseek-v4.1-flash`, with `step-5-preview-free` and
`mimo-v2.6-flash` as subagent routes, in **October**. The bare year is deliberately not printed: a standalone
`2026` is a numeric literal and would break the mandated bibliography-stripped numeric-invariance check
(variant probe: `October 2026` adds exactly one literal, `2026`).

| Figure | Value after an earlier pass |
|---|---|
| `submission/main.tex` | **84,223 bytes**, sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1` **[an earlier pass 2026-10-18: SUPERSEDED — current `main.tex` is 84,695 bytes / sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`, 467 lines]** **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 84,967 B / sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc`]** |
| `submission/encoder-crossover-190.tar.gz` | **28,556 bytes**, sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed`, exactly 1 member `main.tex`, byte-identical to the shipped file **[2026-10-18: SUPERSEDED — recorded by the an earlier pass table: the tarball is now 28,554 B / sha256 `76dfe5dbcdc46b4b2da394ca5f9d1a3ce72da3a81f0e37a0034c33367a09e42b`, exactly 1 member `main.tex`. The 28,556 B / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed` figure above was already stale when measured from disk before this unit's edit (28,536 B / sha256 `0d470f7b532904085c3056f7a63fe5240a87d0d63e7337dfb1239cc912d81bde`). See the an earlier pass update at the end of this file.]** |
| `rendered/encoder-crossover-190.pdf` | **184,933 bytes**, 25 pp A4, sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44` **[an earlier pass 2026-10-18: SUPERSEDED — the installed PDF is now 188,364 B, 25 pp A4, sha256 `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1`; prior build preserved at `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-58c22c90.pdf`]** (the first compile at this size, sha256 `49c96ca737a2df6f73818b434c42e03091d7bb2ddf696afbdeaa3def6a92b60b`, was replaced on re-run; the two differ only in the embedded PDF creation date/ID) |
| numeric multiset (bibliography stripped) | pre vs post: **added=0, removed=0**, shared=763 (full-file multiset also identical) |
| compile | `tectonic -r 1 --keep-logs -o <outdir> .../main.tex`, exit **0**, **0** `Undefined control sequence`, **0** LaTeX `!` |

### Correction 2026-10-17 (re-run)

This unit ran twice. The section above was written by the first run, which installed `MANUSCRIPT.md`,
`main.tex`, the tarball and the PDF but never wrote the disclosure handoff record; by the time of
the re-run `MANUSCRIPT.md` was back on the previous disclosure text and `main.tex` was back to the pre-edit
bytes, so the work was redone from the old paragraph. The re-run reproduces, byte-identically, `main.tex`
(84223 B, sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`, 467 lines) and the
tarball (28556 B, sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed`, exactly 1 member
`main.tex`, byte-identical to the shipped file) **[2026-10-18: SUPERSEDED — recorded by the re-run: the tarball is now 28,554 B / sha256 `76dfe5dbcdc46b4b2da394ca5f9d1a3ce72da3a81f0e37a0034c33367a09e42b`, exactly 1 member `main.tex`. The 28,556 B / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed` figure above was already stale when measured from disk before this unit's edit (28,536 B / sha256 `0d470f7b532904085c3056f7a63fe5240a87d0d63e7337dfb1239cc912d81bde`). See the an earlier pass update at the end of this file.]**, and reinstalls the PDF (184933 B, 25 pp A4, sha256
`58c22c90...`). No generator change (`md2tex.py` unmodified); the paragraph ships at
`main.tex:447`. Numeric multiset with the bibliography stripped: pre 763 / post 763 / shared 763, **added 0,
removed 0** (the full-file multiset is also unchanged). Tectonic exit code 0, `Undefined control sequence`
count 0, LaTeX `!` count 0. `\author` lines 1; `\bibitem` 13, `\cite` occurrences 23, distinct cited 13,
uncited 0, unresolved 0. `pytest tests/test_md2tex.py -q` -> `7 passed in 0.68s`.

---

## Update 2026-10-18 (earlier pass) — tarball figure measured from disk and corrected

Supersedes the `submission/encoder-crossover-190.tar.gz` size/hash figures above; nothing above was
deleted. Unit an earlier pass measured the tarball from disk **before editing anything**, then rebuilt it after
the `MANUSCRIPT.md` edit with
`tar --mtime=@0 --sort=name -cf - -C <submission dir> main.tex | gzip -n -9` (built twice,
byte-identical; the single member is byte-identical to the on-disk `main.tex`).

| Quantity | Value |
|---|---|
| stale figure recorded above | 28,556 B / sha256 `dc4da66c401497ab7bfe882a210664df0f111d76fc26f14cd1905023de8360ed` |
| measured from disk before this unit's edit | 28,536 B / sha256 `0d470f7b532904085c3056f7a63fe5240a87d0d63e7337dfb1239cc912d81bde` (already matched the on-disk shipped tarball) |
| **current** (after `MANUSCRIPT.md` edit, regeneration and rebuild) | **28,554 B** / sha256 `76dfe5dbcdc46b4b2da394ca5f9d1a3ce72da3a81f0e37a0034c33367a09e42b` |

Exactly 1 member, `main.tex`, at the top level. The converter is unchanged (`md2tex.py`);
the payload was regenerated, never hand-patched, and the regeneration was run twice to prove determinism.


---

## Update 2026-10-18 (an earlier pass) — rendered PDF rebuilt from the current `main.tex`

`submission/main.tex` changed after the PDF recorded above was built, so that PDF was stale.
Re-measured from disk **2026-10-18** and rebuilt with the established recipe
`tectonic -r 1 --keep-logs -o <outdir> submission/main.tex`
(`TECTONIC_CACHE_DIR`, `TMPDIR`, `HOME` inside the workspace; **no** `-Z continue-on-errors`):
exit **0**, **0** `Undefined control sequence`, **0** LaTeX `!`.

| Figure | Value after an earlier pass |
|---|---|
| `submission/main.tex` | **84,695 bytes**, sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`, **467 lines** |
| `rendered/encoder-crossover-190.pdf` | **188,364 bytes**, **25 pp** A4 (595.28 x 841.89 pt), sha256 `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1` |
| extracted-text proof | byline `Aswin Ram Kalugasala Moorthy` x1; `AUTHOR SLOT` x0; `TO BE SUPPLIED` x0; `AUTHOR TO CONFIRM` x0; `Replace this paragraph` x0; `names no author` x0 |

Superseded build preserved at
`rendered/_superseded/encoder-crossover-190-tectonic-prior-main-58c22c90.pdf` (184,933 B, 25 pp A4,
sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44`); its extracted text differs
from the installed build in **764** lines (GNU `diff`). The `84,223 B` / `8374fd28…` and `184,933 B` /
`58c22c90…` figures above are retained as dated history.

---

## Update 2026-10-18 — duplicate-DOI wording fixed; all derived artifacts regenerated

The *Persistent identifier* paragraph named the identifier twice in one sentence, so it read as though two
identifiers were in play. **Fix applied:** the concept-versus-version information was **folded into the leading
label** (`DOI` -> `concept DOI`) and the redundant parenthetical **deleted** — not simply dropped, because
`concept DOI` appears nowhere else in the manuscript (identifier sweep: `grep -n 'concept DOI|version DOI'`
matched this paragraph only), so deleting the parenthetical outright would have lost that information.
The identifier is now named **once**, the persistent-identifier and licence statements are intact, and no
new identifier was introduced. `MANUSCRIPT.md:858-860` before -> after (verbatim):

    - **Persistent identifier: DOI `10.5281/zenodo.23463944`.** The released reproducibility package
    - (29 files; no evaluation harness — see Data and code availability) is published on Zenodo under that DOI
    - (concept DOI `10.5281/zenodo.23463944`), so the released artifacts carry a persistent identifier as well
    - as a licence statement.
    + **Persistent identifier: concept DOI `10.5281/zenodo.23463944`.** The released reproducibility package
    + (29 files; no evaluation harness — see Data and code availability) is published on Zenodo under that DOI,
    + so the released artifacts carry a persistent identifier as well as a licence statement.

`diff` of the pre-edit `MANUSCRIPT.md` against the shipped one -> only `858,861c858,860`
(and the corresponding single-line change at `main.tex:427`); nothing else in either file moved.

### Superseded figures, kept verbatim as dated history

| Figure | Earlier "current" value recorded above | Measured from disk **before** this unit's edit (already stale) | **Current** after regeneration |
|---|---|---|---|
| `submission/main.tex` | 84,695 B / sha256 `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca` | **84,786 B** / sha256 `35a1bc966f6e8f1333085a696fe97557e52215da8553ca20ad7bc84d329d926a` | **84,747 B** / sha256 `419ac0cc7b1c88493cac6fca0c53a72a7a66fd41eaf7b0bd90f9b746c73af3ec` **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 84,967 B / sha256 `2b5d049e…`]** |
| `rendered/encoder-crossover-190.pdf` | 188,364 B / sha256 `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1` | **188,819 B** / sha256 `80b3f3e4199f4ab8b4d807e0a2e04ecd4e447e55fa956bf88b0985f339794152` | **188,793 B** / sha256 `bb806e3d6190a076b27819157a325cad11e83535074948763c2030f6a6dbcb70` |

**Disagreement with the unit card, reported:** the card named 84,695 B / `397713d7…` and 188,364 B /
`752747f8…` as the stale "current" figures in this file. Measured from disk before any edit, the payload was
already **two generations** past those: `main.tex` was 84,786 B / `35a1bc96…`, the PDF 188,819 B /
`80b3f3e4…`, and the tarball 28,572 B / `6743c918…` (not the `28,554 B` / `76dfe5db…` recorded above either).
The pre-edit PDF is preserved at
`rendered/_superseded/encoder-crossover-190-tectonic-prior-main-80b3f3e4.pdf`.

### Current measured values (all regenerated by the project's own tooling, never hand-patched)

| Artifact | Value |
|---|---|
| `MANUSCRIPT.md` | **71,481 B**, sha256 `2790b2b8e365a5842646da1e04438cb528c9e5b3c7ac074d3d14d8bdd0e99268` (pre-edit: 71,513 B / `5b2bf36f…`, −32 B) |
| `submission/main.tex` | **84,747 B**, sha256 `419ac0cc…` **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 84,967 B / sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc`]** (built twice by `python3 md2tex.py --package encoder-crossover-190`; `cmp` clean) |
| `submission/encoder-crossover-190.tar.gz` | **28,567 B**, sha256 `fbb0729651becfe40eedfab92bc07d37910c36bbf65ffcca5041d53722ad9d49`, exactly 1 member `main.tex`, byte-identical to the on-disk file | **[2026-10-19 (UREFRESH1): SUPERSEDED — the upload bundle was stale and has been rebuilt from the current `main.tex`: now **28,638 B** / sha256 `5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750` / md5 `3c8d38a38cebd15c04d66e32cfdafe72`, still exactly 1 member `main.tex`, byte-identical to the live file. The 28,567 B / `fbb07296…` bundle held the superseded 84,747 B / `419ac0cc…` revision of `main.tex`; the live file is 84,967 B / `2b5d049e…`.]**
| `rendered/encoder-crossover-190.pdf` | **188,793 B**, sha256 `bb806e3d6190a076b27819157a325cad11e83535074948763c2030f6a6dbcb70`; tectonic exit **0**, `Undefined control sequence` count **0**, LaTeX `!` count **0** (`tectonic -r 1 --keep-logs -o <outdir> submission/main.tex`; `HOME`, `TMPDIR`, `TECTONIC_CACHE_DIR` inside the workspace; no `-Z continue-on-errors`) |
| `rendered/encoder-crossover-190.html` | **85,998 B**, sha256 `8e3c802a23c2f5acb09cee2da97b033a0323cb7de05409f054d49a58244b19ce` (via `rendered/convert.py`) |
| `released/encoder-crossover-190-released.tar.gz` | **159,185 B**, sha256 `196f5311a9b5446af44bafdd688f00035e11f5ec2912f20233e5fa8feedc9a34`, md5 `b3b30f66d231924e02706de0eb3fbc15`; rebuilt twice via `the deposit build script (author-side)` -> `BYTE-IDENTICAL` to the shipped file; `want_cit` pin `32bee18f…` **still matched** (CITATION.cff unchanged — confirmed, not assumed) **[2026-10-19 (UENCFIX2): SUPERSEDED — the shipped archive was rebuilt from the corrected `CITATION.cff` (the two internal orchestration unit ids are gone): now **159,182 B**, sha256 `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877`, md5 `b4dac172003233d7d6c8c78c909b5594`, 37 members / 31 files; `want_cit` re-pinned to `91a64a20…` and provenance re-proved by a fresh script build (`cmp` exit 0). The 159,185 B / `196f5311…` / md5 `b3b30f66…` figures above are kept as dated history.]** |

### Invariance proof (only the wording moved)

Project tokenizers (`(?<![\w.\-])\d+(?:\.\d+)?(?![\w])` and `\d+`), before vs after:

- `MANUSCRIPT.md`: numlit 880 -> 879, shared 879, added `{}`, removed `{'10.5281': 1}`; raw digit-runs 1693 -> 1690, removed `{'10': 1, '23463944': 1, '5281': 1}`, added `{}`
- `main.tex`: numlit 835 -> 834, added `{}`, removed `{'10.5281': 1}`; raw digit-runs 1851 -> 1848, removed `{'10': 1, '23463944': 1, '5281': 1}`, added `{}`
- PDF extracted text: numlit 1005 -> 1004, added `{}`, removed `{'10.5281': 1}`; raw digit-runs 1886 -> 1883, removed `{'10': 1, '23463944': 1, '5281': 1}`, added `{}`

The only numeric tokens removed are the deltas of the **deleted duplicate DOI occurrence**; every other literal
is unchanged, so no published measurement moved. `10.5281/zenodo.23463944` occurrences: **4 -> 3** in
`MANUSCRIPT.md`, `main.tex`, the HTML and the PDF text (each remaining mention on its own line: `743`, `794`,
`858`); `concept DOI` remains 1 -> 1. Citation counts unchanged: `\bibitem` **13**, `\cite` **23**, distinct
**13**, uncited **0**, unresolved **0**.

### Archive verification

`python3 check_manifest.py --package <ABSOLUTE extracted archive root>` ->
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit **0**.
`verify/recompute-claims.py` inside the extraction -> `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`,
exit **0**.


## Update 2026-10-19 (UREFRESH1) — upload bundles rebuilt from the current `main.tex`

The two upload bundles were stale revision drift: each held an **older** `main.tex` than the live
`papers/encoder-crossover-190/submission/main.tex`. Nothing above was deleted; this section supersedes every earlier
`encoder-crossover-190.tar.gz` / `encoder-crossover-190-preprints.zip` figure in this file.

Live source (unchanged by this unit, and itself confirmed current — regenerating it twice with
`python3 tools/package/md2tex.py --package encoder-crossover-190` is `cmp`-clean and reproduces it byte-for-byte):
`submission/main.tex` **84,967 B** / sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc` / md5 `4baeca180840b4626561b8210c915cf5`.

| Bundle | Size | sha256 | md5 | change |
|---|---|---|---|---|
| `encoder-crossover-190.tar.gz` | 28,638 B | `5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750` | `3c8d38a38cebd15c04d66e32cfdafe72` | **CHANGED** (bundle was stale) |
| `encoder-crossover-190-preprints.zip` | 28,712 B | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `5c483d8cd71bfbfa12596725a2c58f69` | unchanged (already current) |

* Superseded submission tarball: 28,567 B / sha256 `fbb0729651becfe40eedfab92bc07d37910c36bbf65ffcca5041d53722ad9d49`.
* Superseded preprints zip: 28,712 B / sha256 `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f`.
* Tarball recipe (verified by reproducing the pre-rebuild container byte-for-byte): `tar --mtime=@0 --sort=name -cf - main.tex | gzip -n -9` (this paper's own documented recipe, confirmed by reproducing the pre-rebuild bundle byte-for-byte from its extracted member); built twice -> `BYTE-IDENTICAL`; exactly one member, `main.tex`.
* Zip recipe (verified by reproducing the pre-rebuild container byte-for-byte on the sample where the member was already current): `zip -X -q <out> main.tex`; built twice -> `BYTE-IDENTICAL`; exactly one member, `main.tex`.
* Member proof: unpacking both bundles yields one member `main.tex` whose sha256 **equals** the live `submission/main.tex` above.

---

## Update 2026-10-19 (UDOCSYNC1) — live `submission/main.tex` digest re-established

The 2026-10-19 bundle refresh (recorded as UREFRESH1 in the tarball row of the inventory above) rebuilt the
upload containers from the live `main.tex`, but this file's own build records still quoted the previous
revision. Re-measured from disk 2026-10-19:

| Artifact | Live value |
|---|---|
| `submission/main.tex` | **84,967 B**, sha256 `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc` |
| `submission/encoder-crossover-190.tar.gz` | **28,638 B**, sha256 `5bc51590bbf9eb4daf0dfc3828eb1bb38f963ca8a06b5cc951e1fa0855982750`, md5 `3c8d38a38cebd15c04d66e32cfdafe72`, exactly 1 member `main.tex` |
| `preprints/encoder-crossover-190-preprints.zip` | **28,712 B**, sha256 `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f`, md5 `5c483d8cd71bfbfa12596725a2c58f69`, exactly 1 member `main.tex` |

Every earlier "current" value of `submission/main.tex` recorded above (`84,223 B` / `8374fd28…`,
`84,695 B` / `397713d7…`, `84,747 B` / `419ac0cc…`) is retained above as dated history and is superseded by
the row above. No measured result was changed and no paper prose was touched.
