# METADATA --- replay-record-not-decision

> **Note on names.** Build tooling and intermediate directories named in this file are author-side and are **not distributed** with the submission.


> **STATUS 2026-10-16 (earlier pass):** the figures and paths in this file are *dated build history* — each reflects the unit that wrote it. The shipped payload was re-measured from disk and the current values are in the **Update 2026-10-16 (earlier pass)** section at the end of this file; where the two disagree, that section is authoritative. Nothing was deleted.


Package `replay-record-not-decision`.  Source: `MANUSCRIPT.md`
(not modified by this unit).  Converter: `md2tex.py`, driven by the per-package
registry `PACKAGES`.  This paper did not previously have a `submission/` directory.

Command: `python3 md2tex.py --package replay-record-not-decision`
Tarball (separate manual step, exactly as for the other two papers):
`tar -czf submission/replay-record-not-decision.tar.gz -C submission main.tex`

## Shipped files, measured
| file | bytes | sha256 |
|---|---|---|
| `main.tex` | 28604 (superseded 20631) | `2059e12bda2612a4bcbe3cbb490dc5538a56d6754c71d3f48cab3ce3b74fcf7a` (superseded `0520d2059734f8381227fdf0bff51fd006bb88b46635419b7dbc07ddd5bdd0d5`) **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `main.tex` is 32,350 B / sha256 `ac74384c…`]** |
| `ABSTRACT.txt` | 1673 | `6625cd913dc9e6c51d80dedd84f5861bbafae3564ed943a4e4f5d433675d189c` |
| `ABSTRACT_METADATA.txt` | 1594 | `9765d28e0ca851084b327beaa5734b422634a8989a2799810035f3da795445dd` |
| `replay-record-not-decision.tar.gz` | 10254 (superseded 7215) | `48bc61ed4551ed3cc517f787df4c82144e5e8a8ef575eedd543951406a8beed3` (superseded `7294cad8a3d8cbb0c4e933643767ba9e454cceadb391c1137f9b4454bc62270c`) | **[2026-10-19 (UREFRESH1): SUPERSEDED — the bundle was stale and has been rebuilt from the current `main.tex` (32,350 B / `ac74384c…`): **11,425 B** / sha256 `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` / md5 `720164891c8996a8bf7437ba81588602`.]**

Tarball members: exactly one, `main.tex`; extracted bytes compare equal to the shipped `main.tex`
(`cmp`, no output).

## What the paper promises to ship --- derived from `AVAILABILITY.md`
- Released record bytes total **1,261,035** (`1,197,797 + 63,238`, line 22).
- `decision-variants.jsonl` --- 1,197,797 B / 3,040 lines / sha256 `c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7` (line 17).
- `l1-head-to-head.jsonl` --- 63,238 B / 380 lines / sha256 `6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7` (line 18).
- Withheld: the stimulus fixture (145,031 B, line 32)
  and the analysis script (8,856 B, line 37).
- Licence: the paper's own text is CC BY 4.0 (author decision, 2026-10-15) and so is the released
  subset's content; the main repository stays proprietary and closed (lines 54, 56).
This payload ships only the paper's LaTeX and abstract artefacts; the record files themselves are
released separately and were **not** copied by this unit.

## Citations --- zero external
`cite_anchors=()`, `expected_bib_count=0`, `bib_source="none"`.  Measured on the shipped LaTeX: **[2026-10-16: SUPERSEDED — the shipped paper now uses `expected_bib_count=8`, `bib_source="bibtex_file"` (`REFERENCES.bib`); see the an earlier pass update in `BUILD_NOTES.md`]**
0 `\\cite`, 0 `\\bibitem`, no `thebibliography` environment.  The manuscript names arXiv 2605.20173 **[2026-10-16: SUPERSEDED — measured on the current shipped LaTeX: 8 `\bibitem`, 8 `\cite`, `thebibliography` present]**
once, quoted from the pre-registration and explicitly **not** independently fetched; it is not a
bibliographical entry.  So the anchor table is empty because the manuscript makes no in-text
citation, and the citation guard is expressed positively (see BUILD_NOTES.md) rather than disabled.

## Author
The shipped package carries one author line, `\author{Aswin Ram Kalugasala Moorthy}`
(`submission/main.tex:12`) — the author’s own name, supplied verbatim, name only, no affiliation.
**SUPERSEDED WORDING (retained as dated history; it was accurate before the author supplied the name):**
~~No author block.  `AVAILABILITY.md:24`: "**No author block is supplied with this manuscript.** The
byline has not been provided. No name, no..." and `MANUSCRIPT.md` section 7.  So `author_line=None`
and the generator emits no `\author`.  The other two packages emit the placeholder slot
`\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`; that form is deliberately **not** used here,
because this paper’s own documents forbid inventing one.~~
(Corrected 2026-10-16 by an earlier pass; the `author_line` field is now set per package, see BUILD_NOTES.md.)

## De-naming
16 literal per-package `dename_rules` describe internal working records instead of naming them, e.g.
`` `EXP#7-replay-divergence.md:16-17` `` -> "the pre-registration record, \\S1".  The released DATA
filenames (`decision-variants.jsonl`, `l1-head-to-head.jsonl`) are deliberately **not** de-named:
`AVAILABILITY.md` ships them, so they are public material, not internal records.

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
- Payload regenerated with `python3 md2tex.py --package replay-record-not-decision`; two independent runs were
  byte-identical to each other and to the shipped file (`cmp`), and the rebuilt tarball's single
  member is byte-identical to the on-disk `main.tex` (`cmp` after extraction).
- New `main.tex`: **20956 bytes**, sha256 `d72db59f4883970bf5221495d67b7907157152c94ce58a9b525cda8df7912898`.
  New `replay-record-not-decision.tar.gz`: **7311 bytes**, sha256 `c78d4a1f92ceb0e868e4775f542a2ab7c2d8625ad6f4315ba41e611b7a50fa09` (container digest is not bit-reproducible; the member is).
- Invariants re-proven: bibitems/cited-keys/uncited as before, 0 non-ASCII, `\begin`/`\end` balanced,
  exactly one `\author` line, and the numeric-literal multiset of `main.tex` is unchanged (only the
  33-char byline replaced the 46-char placeholder: −13 bytes).


---

## Update 2026-10-16 --- Comments field

This sheet had no `Comments` field. There is now one worth recording: **10 pages**, built with
Tectonic (`tectonic -r 1 --keep-logs`, exit 0) and installed at
`rendered/replay-record-not-decision.pdf` (91,552 bytes, A4).
The older "no TeX toolchain exists in this workspace" wording in `BUILD_NOTES.md` is dated history.


---

## Update 2026-10-16 — measured build-record correction

A build pass re-measured the shipped payload **from disk** and corrected every figure or path in
this file that no longer matches it. Nothing was deleted: superseded values above remain as dated build
history, and the table gives the old value beside the current one. No measured number, claim, reference,
bibliography entry or `main.tex` byte was changed — records only.

Converter in use: `md2tex.py` (44,777 bytes, sha256
`97d34349f11ad15a1af2cf0b5bbbf61def02beb6b1a5ebb3f32de7778bfa63e4`) — **[2026-10-18: SUPERSEDED — the converter on disk is now 45,845 B / sha256 `5dfcdc46219f7e49d64547b57ce3391f9f2aa5d06f5849447ac5943d7a21acc9`]** this file already named it
correctly; the earlier build tree is a **retired build directory**.

| Figure | Superseded value | Measured 2026-10-16 (current) |
|---|---|---|
| `submission/main.tex` | 20,631 B; then 20,956 (earlier pass) | **28,604 B**, sha256 `2059e12bda2612a4bcbe3cbb490dc5538a56d6754c71d3f48cab3ce3b74fcf7a`, 241 lines **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 32,350 B / sha256 `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934`]** |
| bibliography | "0 `\cite`, 0 `\bibitem`, no `thebibliography`" | **8 `\bibitem`, 8 `\cite`**, `expected_bib_count=8`, `bib_source="bibtex_file"` |
| `submission/replay-record-not-decision.tar.gz` | 7,215 B; then 7,311 / 9,642 | **10,254 B**, sha256 `48bc61ed4551ed3cc517f787df4c82144e5e8a8ef575eedd543951406a8beed3`, exactly 1 member `main.tex` | **[2026-10-19 (UREFRESH1): SUPERSEDED — rebuilt from the current `main.tex` (32,350 B / `ac74384c…`): **11,425 B** / sha256 `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` / md5 `720164891c8996a8bf7437ba81588602`, exactly 1 member `main.tex`.]**
| PDF | "no TeX toolchain / not compiled to PDF" | **exists** `rendered/replay-record-not-decision.pdf`: 91,552 B, **10 pages**, A4 595.28 x 841.89 pts, sha256 `85f13e8c450579a73a852194dfdc151d104db3afa9459495ae994b59697fc17a` **[2026-10-18: SUPERSEDED — the installed PDF is now 91,551 B / sha256 `4c5acbec547c04797026ae997fa68569966c05fb1070b0fa33ab7f174ea5e345` (10 pp, A4)]** |
| `MANUSCRIPT.md` | not previously recorded | 21,094 B, sha256 `3ef35a0606d4068930b5a9cf088fd96698e493ab3613e1d4f0c6f0f228f5a081` **[2026-10-18: SUPERSEDED — current `MANUSCRIPT.md` is 22,638 B / sha256 `846316589b99013627705ab41c0acb309872724797bf4f5b2572828b3387f305`, 340 lines]** |

Left in place deliberately, because dated history is correct as history: the original reproduction block,
the an earlier pass size/hash series, the an earlier pass tarball digest `b9a89837…` (container digests are not
bit-reproducible; the member is), and the the earlier PDF digest `94cc3b3d…` (the PDF was recompiled after
an earlier pass; page count matches (10 pp) but the size does not — the recompiled PDF is 91,551 B, one byte below the 91,552 B recorded here). **[2026-10-18: SUPERSEDED — the "size matches" half of this claim was one byte off; current PDF is 91,551 B / sha256 `4c5acbec547c04797026ae997fa68569966c05fb1070b0fa33ab7f174ea5e345`.]** ~~The an earlier pass `main.tex` digest `eb63dd17…` still matches the file.~~ **[2026-10-18: SUPERSEDED — `eb63dd17…` no longer matches; current `submission/main.tex` is 28,604 B / sha256 `2059e12bda2612a4bcbe3cbb490dc5538a56d6754c71d3f48cab3ce3b74fcf7a` (241 lines). **[2026-10-19 (UDOCSYNC1): SUPERSEDED — live `submission/main.tex` is 32,350 B / sha256 `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934`]** `eb63dd17…` was the an earlier pass-era 26,974 B revision.]**


## Update 2026-10-19 (UREFRESH1) — upload bundles rebuilt from the current `main.tex`

The upload bundles were stale (`main.tex` older than the live source). Rebuilt from
`submission/main.tex` **32,350 B** / sha256 `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934`; both bundles hold exactly
one member `main.tex` byte-identical to it. Superseded values were retained above as dated history.

| Bundle | Size | sha256 | md5 | change |
|---|---|---|---|---|
| `replay-record-not-decision.tar.gz` | 11,425 B | `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` | `720164891c8996a8bf7437ba81588602` | **CHANGED** |
| `replay-record-not-decision-preprints.zip` | 11,379 B | `63044528d554ac5f2a6507e3d06708f3be44aba7e0fba7a3e43be4953260173d` | `b79732d135650ca176f30bb62a64f764` | CHANGED |
