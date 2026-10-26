# Build notes — paper #7 submission payload (`gated-read-batching`)

> **Note on names.** Build tooling and intermediate directories named in this file are author-side and are **not distributed** with the submission.


> **STATUS 2026-10-16 (earlier pass):** the figures and paths in this file are *dated build history* — each reflects the unit that wrote it. The shipped payload was re-measured from disk and the current values are in the **Update 2026-10-16 (earlier pass)** section at the end of this file; where the two disagree, that section is authoritative. Nothing was deleted.


Everything here was produced from the read-only source tree. No network access, no package
install, no BibTeX run, and no PDF (there is no TeX toolchain — see "Unverified"). **[2026-10-16: SUPERSEDED — a PDF now exists: `rendered/gated-read-batching.pdf`, 107,911 bytes, 13 pages, A4]**

## What was converted, from what, with which command

- **Source (read-only, unmodified):** `MANUSCRIPT.md` —
  **33,165 bytes, 237 lines, 5,399 words** as of an earlier pass's 2026-10-16 edit (the pre-edit reading
  was 33,032 bytes, 238 lines, 5,377 words; superseded — the banner replacement and the pointer
  rewordings moved all three). `CLAIMS.md`,
  `GAPS.md` and `REFS.md` were consulted for the reference list and category context; none
  was modified.
- **Converter:** `md2tex.py`, a paper-specific adaptation of the worked **[2026-10-16: SUPERSEDED — the converter in use is `md2tex.py`; `md2tex.py` is a retired build directory]**
  example `md2tex.py`. It reads the manuscript and writes exactly three **[2026-10-16: SUPERSEDED — `md2tex.py` is a retired worked example; the converter in use is `md2tex.py`.]**
  files into `submission/`: `main.tex`, `ABSTRACT.txt`,
  `ABSTRACT_METADATA.txt`.
- **Exact regeneration command** (run from the workspace root):
  `python3 md2tex.py` **[2026-10-16: SUPERSEDED — run `python3 md2tex.py --package gated-read-batching`]**
- **Exact tarball command:**
  `tar -czf submission/gated-read-batching.tar.gz -C submission main.tex`

## Outputs with size and digest

| File | Bytes | sha256 |
|---|---|---|
| `main.tex` | 36,997 | `0bd57e6c20de7fbda0b7ddcddb0e22e1e3285a968f3f476da629e104b1ec8a2a`  **[2026-10-16: SUPERSEDED — current `main.tex` is 39133 bytes / sha256 `d321f8c3e5500518d8bf75783ce8e3620078d52af51d543a8cbf11748624c0c9`]** **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 39,351 B / sha256 `9235ec53…`]** |
| `ABSTRACT.txt` | 2,120 | `59ef6d55d64d6a3c3b500ffb653e8f85c11fca9e841b1ff37fc8b43c0ef1a6e9` |
| `ABSTRACT_METADATA.txt` | 1,884 | `05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962` |
| `gated-read-batching.tar.gz` | 13,189 | `ede2f3a5a08dd82b505f961480f640722654a123e322a0bcf60422a05ea59585`  **[2026-10-16: SUPERSEDED — current tarball is 13,916 bytes / sha256 `8267b766a1d1c8779bbc7bec2b0b6506504c0f1a376fd33ba3268860a8281e2c`]** |
| `METADATA.md`, `BUILD_NOTES.md` | — | hand-written metadata, not converter output |

## Reproducibility (both proven, not asserted)

- The converter was run twice from the same source; `cmp` between the two runs' `main.tex`
  is clean — `REPRODUCIBLE: run1 vs run2 byte-identical`.
- The tarball holds **exactly one member**, `main.tex`, and
  `cmp <(tar -xzOf submission/gated-read-batching.tar.gz main.tex) submission/main.tex`
  is clean — the archive is not stale relative to the on-disk file.
- **Caveat, stated so it is not mistaken for staleness:** re-running `tar -czf` changes the
  *container* digest, because gzip embeds a timestamp. The *member* bytes are what must
  match, and they do.

## Conversion decisions

- **Sections/headings:** manual numbers in the markdown (`## 3. Method`) are stripped and
  LaTeX auto-numbering is used, so sections come out 1–7 and every in-text "§3.3"/"§4.1"
  cross-reference still points at the right place. `## Abstract` becomes an `abstract`
  environment; `## References` becomes `\section*{References}` plus
  `\renewcommand{\refname}{}` so the `thebibliography` heading does not appear twice.
- **Bibliography:** no `.bib` file exists, so the manuscript's own numbered reference list
  (13 entries) is inlined as `\bibitem{ref1} … \bibitem{ref13}` inside `thebibliography`.
  No BibTeX run, no `\bibliography`, no network.
- **Citations:** every in-text literature mention is wired to a real `\cite`, using an
  explicit anchor table (author-year phrase → key). Counts on the shipped file: **13
  `\bibitem`, 14 `\cite` calls, 13 distinct keys, 0 uncited `\bibitem`, 0 `\cite` without a
  `\bibitem`** — deliberately repairing the previous paper's "13 `\bibitem`, 0 `\cite`"
  defect.
- **ASCII-only output:** 9 distinct non-ASCII characters in the source were mapped —
  en dash → `--`, em dash → `---`, × → `$\times$`, ± → `$\pm$`, − → `$-$`, → → `$\to$`,
  ≥ → `$\ge$`, ∈ → `$\in$`, ì → `` \`i ``. The shipped `main.tex` contains **0** non-ASCII
  bytes.
- **Drafting artefacts:** the converter drops the leading `**Status:** draft manuscript …`
  banner (sanitisation rule S1; **superseded by an earlier pass** — the source now carries a neutral `**Scope:**` line, so S1 no longer fires and that line now ships) and removes internal unit identifiers (rule S2; 2 internal unit-id strings in the §3.2 correction markers). It also flattens the one markdown link
  (`[`REFS.md`](REFS.md)` → its label) and may not print local paths or workspace directory
  names; a guard hard-fails if any survive. a `grep -c` over the internal-pointer pattern class (unit ids, workspace-relative
  paths, absolute host paths, drafting banners) on `main.tex` returns **0**.
- **`\*` footnote marker** on the source line beginning `\* Accuracy is misleading …` is
  converted to `$^{*}$` so it prints as a raised asterisk instead of a LaTeX error.
- **Quotes** are paired: straight `"…"` becomes LaTeX `` ``…'' ``.

## Guards (all hard-fail, so a bad build cannot ship silently)

Unmapped non-ASCII in source; non-ASCII in output; bibliography not exactly `ref1..ref13`;
any uncited `\bibitem`; any `\cite` key with no `\bibitem`; unbalanced `\begin`/`\end`;
unbalanced braces; forbidden-pattern hits (internal unit id, `scratch`, draft/status
banner, any local path); residual markdown `**`; author-slot count ≠ 1 or slot string
absent; `ABSTRACT_METADATA.txt` non-ASCII, multi-line, or outside 1–1,920 chars.

## Counts on the shipped `main.tex`

0 non-ASCII; 13 `\bibitem`; 14 `\cite`; 7 `\section`; 14 `\subsection`; 2 `\section*`;
`\begin`/`\end` 19/19; braces **402/402** (the pre-correction reading was 403/403;
superseded); 8 `tabular`; 12 `itemize`; 4 `enumerate`; 1 author placeholder slot **at that time — SUPERSEDED: the shipped `main.tex:12` now carries `\author{Aswin Ram Kalugasala Moorthy}`, i.e. 0 placeholder slots**; 0
forbidden-pattern hits.

## Unverified — what this build does NOT establish

- **No compilation was attempted and no PDF exists.** `pdflatex`, `latexmk`, `xelatex`, **[2026-10-16: SUPERSEDED — `rendered/gated-read-batching.pdf` exists: 107,911 bytes / 13 pages / sha256 `ab6da66616c5913b6c9b46940b0e512dcbf6dfa7b1e4d0f4fcc05e5bdcdaa49c`]** **[2026-10-18: SUPERSEDED — the installed PDF is now sha256 `6bf7c2c22646bca3b8282848dd6c7dfc1b98d5523c6a06e6c3f0ca4addec0f81` (107,911 B, 13 pp, A4)]**
  `tectonic` and `bibtex` are all absent from this host (`which` found none), nothing was
  installed, and no PDF was fabricated. Therefore: no page count, no overfull/underfull box **[2026-10-16: SUPERSEDED — a PDF now exists: `rendered/gated-read-batching.pdf`, 107,911 bytes / 13 pages.]**
  check, no compile-time error check. This mirrors the correct outcome for the previous
  paper. The Comments field on arXiv will need a page count the author measures elsewhere.
- **The ~1,920-character metadata-abstract cap was not re-verified** against arXiv's help
  pages; `ABSTRACT_METADATA.txt` is 1,883 characters, which satisfies the cap as stated in
  this unit's instructions.
- **The tarball container digest is not bit-reproducible** (gzip timestamp), though its
  single member is byte-identical to `main.tex`.
- **Reference completeness** (surnames-only entries, truncated author lists) and each
  reference's venue are reproduced exactly as the manuscript carries them; they were not
  independently verified here.

## Left for the author (reported, not silently changed)

1. ~~The single author placeholder in `main.tex` — name only, no affiliation, not anonymised.~~
   **RESOLVED 2026-10-16:** the shipped `main.tex:12` carries `\author{Aswin Ram Kalugasala
   Moorthy}` — name only, no affiliation, not anonymised. No author action remains on this item.
2. Licence, date, category, endorsement — none supplied by the manuscript.
3. *(Superseded by an earlier pass — see the revision section below.)* Three internal-document pointers (`CLAIMS.md`, `GAPS.md G-25`, `REFS.md`) formerly remained in the
   body prose: they are not filesystem paths, and an arXiv reader cannot resolve them. They
   were kept because the surrounding text is substantive. Source-level fixes recommended but
   **not applied** (this unit must not edit the manuscript): delete the `**Status:**` banner
   and the two `an earlier pass` strings from `MANUSCRIPT.md`. **the outcome of that pass:** the three pointers were removed/reworded as recorded below; the `**Status:**` banner was replaced with a neutral `**Scope:**` line; the two `an earlier pass` correction markers in §3.2 were deliberately **kept** — they are dated provenance, as instructed.

## Revision (2026-10-16T21:58:30Z): internal pointers retired, draft banner neutralised

Source edits in `MANUSCRIPT.md` only (no other source file touched). `MANUSCRIPT.md:3` `**Status:** draft manuscript …` → `**Scope:** prepared from a closed 2026-09-30 measurement run. Single model, single corpus, single task family. Short note / workshop scope.` (neutral — S1 no longer fires, so this line now ships as the paper's opening scope statement); `MANUSCRIPT.md:84`, inside the dated `[correction 2026-10-15: …]` marker, `stated in full at GAPS.md G-25.` → `stated in full in this record's internal gap log (entry G-25; an internal working record not included in the released material).` — the marker's date, unit id and correction content are unchanged; `MANUSCRIPT.md:127` drops ` in `CLAIMS.md``, keeping the traceability statement, 71/73 and the C48/C65 locators; `MANUSCRIPT.md:223` `maintained in [REFS.md](REFS.md).` → `maintained in this record's internal reference notes (an internal working record not included in the released material).`; `MANUSCRIPT.md:225` `(Venue not verified — see REFS.md.)` → `(Venue not verified.)`. The two `an earlier pass` markers in §3.2 were **kept** (dated provenance). The manuscript now contains **0** occurrences of `CLAIMS.md`, `GAPS.md`, `REFS.md`, `EVIDENCE_NOTES.md`, `OPEN_QUESTIONS.md`, `REFERENCE_NOTES.md`, `UNSOURCED_RETAINED.md` or a bare a bare workspace-relative path (siblings searched for; none present). No number, claim, citation or result meaning changed.

| File | Bytes | sha256 | previous (superseded) |
|---|---|---|---|
| `main.tex` | 37291 | `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4` | 36,997 / `0bd57e6c20de7fbda0b7ddcddb0e22e1e3285a968f3f476da629e104b1ec8a2a` |
| `gated-read-batching.tar.gz` | 13270 | `0899f5b6252f68ac076e67eea1e9b325a5fcd8b9959c0515b861882106969c18` | 13,189 / `ede2f3a5a08dd82b505f961480f640722654a123e322a0bcf60422a05ea59585` |
| `ABSTRACT.txt` | 2120 | `59ef6d55d64d6a3c3b500ffb653e8f85c11fca9e841b1ff37fc8b43c0ef1a6e9` | 2,120 / `59ef6d55d64d6a3c3b500ffb653e8f85c11fca9e841b1ff37fc8b43c0ef1a6e9` |
| `ABSTRACT_METADATA.txt` | 1884 | `05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962` | 1,884 / `05ce7038056235b3bd52dd1f3dac3c048698701eac35cd779b3198192c88e962` |

Proof after the edit the earlier pass's own commands: `python3 md2tex.py` run twice, `cmp <guarded-run>/run1.tex submission/main.tex` clean; `tar -czf submission/gated-read-batching.tar.gz -C submission main.tex` rebuilt, `cmp <(tar -xzOf <tarball> main.tex) main.tex` clean; 13 `\bibitem`, 14 `\cite` calls across 13 distinct keys, 0 uncited `\bibitem`, 0 `\cite` without `\bibitem`, 0 non-ASCII bytes, exactly 1 author placeholder, `\begin`/`\end` 19/19. **The tarball container digest is not bit-reproducible** (gzip embeds a timestamp); its single member `main.tex` is byte-identical to the on-disk file. The converter now reports `dropped drafting banner(s): 0` because the source banner is neutral, and it still strips the two internal unit ids (`removed internal unit ids: ['<unit-id>']`).

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
- Payload regenerated with `python3 md2tex.py --package gated-read-batching`; two independent runs were
  byte-identical to each other and to the shipped file (`cmp`), and the rebuilt tarball's single
  member is byte-identical to the on-disk `main.tex` (`cmp` after extraction).
- New `main.tex`: **37278 bytes**, sha256 `165549a22d27b35ad6a4e2efe3f3457f806bb464fa7f16b493f9f79c3a515a67`.
  New `gated-read-batching.tar.gz`: **13252 bytes**, sha256 `cda7357cdcbd2b421c157983c7438c68534ca6dbeea795a5b40d2b7a2595dda9` (container digest is not bit-reproducible; the member is).
- Invariants re-proven: bibitems/cited-keys/uncited as before, 0 non-ASCII, `\begin`/`\end` balanced,
  exactly one `\author` line, and the numeric-literal multiset of `main.tex` is unchanged (only the
  33-char byline replaced the 46-char placeholder: −13 bytes).


## Update 2026-10-16 --- PDF compiled and installed

The "no TeX toolchain" statements above are **dated history**. A toolchain is now present at
`tectonic`. `main.tex` was rebuilt with
`tectonic -r 1 --keep-logs -o <outdir> submission/main.tex`
(`HOME`, `TMPDIR`, `TECTONIC_CACHE_DIR` exported inside the workspace; **without**
`-Z continue-on-errors`): exit **0**, **0** `Undefined control sequence`, **0** LaTeX `!` errors.
The PDF is installed at `rendered/gated-read-batching.pdf` --- **107,911 bytes, 13 pages, A4
(595.28 x 841.89 pts), sha256 `86a288e886afa2a27b45c3f429e4db4a9aad9fddfd88ddb6591ab3ce7f492770`**.


---

## Update 2026-10-16 — measured build-record correction

A build pass re-measured the shipped payload **from disk** and corrected every figure or path in
this file that no longer matches it. Nothing was deleted: superseded values above remain as dated build
history, and the table gives the old value beside the current one. No measured number, claim, reference,
bibliography entry or `main.tex` byte was changed — records only.

Converter actually in use: `md2tex.py` (44,777 bytes, sha256
`97d34349f11ad15a1af2cf0b5bbbf61def02beb6b1a5ebb3f32de7778bfa63e4`). **[2026-10-18: SUPERSEDED — the converter on disk is now 45,845 B / sha256 `5dfcdc46219f7e49d64547b57ce3391f9f2aa5d06f5849447ac5943d7a21acc9`]** `md2tex.py`
still exists on disk but is a **retired build directory**, not the current converter.

| Figure | Superseded value | Measured 2026-10-16 (current) |
|---|---|---|
| converter | `md2tex.py` | `md2tex.py` (44,777 B, sha256 `97d34349…`) **[2026-10-18: SUPERSEDED — 45,845 B / sha256 `5dfcdc46…`]** |
| `submission/main.tex` | 36,997 B; then 37,291 / 37,278 | **39133 B**, sha256 `d321f8c3e5500518d8bf75783ce8e3620078d52af51d543a8cbf11748624c0c9`, 290 lines **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 39,351 B / sha256 `9235ec53e581edf0884e7ca9d85e6be696a148d9599f0465af02f7927f635277`]** |
| bibliography | 13 `\bibitem`, 14 `\cite` | matches: 13 `\bibitem`, 14 `\cite` over 13 distinct keys, 0 uncited |
| `submission/gated-read-batching.tar.gz` | 13,189 B; then 13,270 / 13,252 | **13,916 B**, sha256 `8267b766a1d1c8779bbc7bec2b0b6506504c0f1a376fd33ba3268860a8281e2c`, exactly 1 member `main.tex` | **[2026-10-19 (UREFRESH1): SUPERSEDED — the upload bundle was stale and has been rebuilt from the current `main.tex`: now **14,011 B** / sha256 `cdce3f010e8779a2f291dc4abe654cbc3517c905dc77b2a3a94f60e14e4ed010` / md5 `30c4c8d331dba03de4a7edd051b4dc11`, still exactly 1 member `main.tex`, byte-identical to the live file. The 13,916 B / `8267b766…` bundle held the superseded 39,133 B / `d321f8c3…` revision; the live file is 39,351 B / `9235ec53…`.]**
| PDF existence | "No compilation was attempted and no PDF exists" | **exists** `rendered/gated-read-batching.pdf`: 107,911 B, **13 pages**, A4 595.28 x 841.89 pts, sha256 `ab6da66616c5913b6c9b46940b0e512dcbf6dfa7b1e4d0f4fcc05e5bdcdaa49c` **[2026-10-18: SUPERSEDED — installed PDF is now sha256 `6bf7c2c22646bca3b8282848dd6c7dfc1b98d5523c6a06e6c3f0ca4addec0f81` (107,911 B, 13 pp)]** |
| `MANUSCRIPT.md` | 33,165 B | matches: 33,165 B, sha256 `2a4cc287e8509b2cf2492cf1edff989ff57f352d8d0d2d2bf7666de023b8a2a7` **[2026-10-18: SUPERSEDED — current `MANUSCRIPT.md` is 34,867 B / sha256 `34f4ae280264ac91d6d9306c4df5fab9ea995e5a381458cdc2dfd9a03a971ef2`, 263 lines]** |

Left in place deliberately, because dated history is correct as history: the original outputs table, the
an earlier pass revision table digits, the an earlier pass size/hash series, and the the earlier PDF digest `86a288e8…`
(the PDF was recompiled after an earlier pass; size and page count happen to match, the digest does not).



## Update 2026-10-19 (UREFRESH1) — upload bundles rebuilt from the current `main.tex`

The two upload bundles were stale revision drift: each held an **older** `main.tex` than the live
`papers/gated-read-batching/submission/main.tex`. Nothing above was deleted; this section supersedes every earlier
`gated-read-batching.tar.gz` / `gated-read-batching-preprints.zip` figure in this file.

Live source (unchanged by this unit, and itself confirmed current — regenerating it twice with
`python3 tools/package/md2tex.py --package gated-read-batching` is `cmp`-clean and reproduces it byte-for-byte):
`submission/main.tex` **39,351 B** / sha256 `9235ec53e581edf0884e7ca9d85e6be696a148d9599f0465af02f7927f635277` / md5 `da080f1195801aa3e3c3100edcecb191`.

| Bundle | Size | sha256 | md5 | change |
|---|---|---|---|---|
| `gated-read-batching.tar.gz` | 14,011 B | `cdce3f010e8779a2f291dc4abe654cbc3517c905dc77b2a3a94f60e14e4ed010` | `30c4c8d331dba03de4a7edd051b4dc11` | **CHANGED** (bundle was stale) |
| `gated-read-batching-preprints.zip` | 14,094 B | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` | `09f535a4d84c439cc801f5097994c9c4` | unchanged (already current) |

* Superseded submission tarball: 13,916 B / sha256 `8267b766a1d1c8779bbc7bec2b0b6506504c0f1a376fd33ba3268860a8281e2c`.
* Superseded preprints zip: 14,094 B / sha256 `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5`.
* Tarball recipe (verified by reproducing the pre-rebuild container byte-for-byte): `tar -czf <out> -C <submission dir> main.tex` (this paper's own documented recipe, confirmed by reproducing the pre-rebuild bundle byte-for-byte from its extracted member); built twice -> `BYTE-IDENTICAL`; exactly one member, `main.tex`.
* Zip recipe (verified by reproducing the pre-rebuild container byte-for-byte on the sample where the member was already current): `zip -X -q <out> main.tex`; built twice -> `BYTE-IDENTICAL`; exactly one member, `main.tex`.
* Member proof: unpacking both bundles yields one member `main.tex` whose sha256 **equals** the live `submission/main.tex` above.
