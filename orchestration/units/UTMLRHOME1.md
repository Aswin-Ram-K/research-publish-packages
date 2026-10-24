# UTMLRHOME1 — install the TMLR double-blind variant into a stable home

**Purpose.** The anonymised TMLR variant of paper #1 existed only at `scratch/utmlr6/tmlr/`.
Install it — by copy — at `papers/encoder-crossover-190/tmlr/`, document it, prove the copy is
faithful, recompile from the installed copy alone, and re-prove anonymity from the installed
PDF's own text.

**Bound.** 20 tool calls. **Used: 12.** **Status: done.**

**Write paths.** `papers/encoder-crossover-190/tmlr/**`, `scratch/utmlrhome1/**`,
`orchestration/units/UTMLRHOME1.md`, `orchestration/handoffs/UTMLRHOME1.json`.
Not touched: `scratch/utmlr6/**`, `papers/encoder-crossover-190/released/**`,
`papers/encoder-crossover-190/submission/**`, `/home/zer0null/Duval`.

## Measured (scratch/utmlr6/tmlr, literal output)

| file | bytes | sha256 |
|---|---|---|
| `fancyhdr.sty` | 17086 | `3d2922548e0e5f1a6c5676eda6ebb6dc20d7d305b4d8c2be5f1c833fb1084e6d` |
| `LICENSE` | 11357 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| `main.pdf` | 176971 | `a777d2a30e1f8707d84673d401a8a231cd4526b4ee78f5a1163070961929acdf` |
| `main.tex` | 83785 | `8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0` |
| `tmlr.bst` | 26969 | `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206` |
| `tmlr.sty` | 6560 | `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002` |

`pdfinfo` → `Pages: 16`. **Card agreement:** matches the card on PDF digest, 176971 B, 83785 B and
16 pp. **Disagreement:** the card's file list omits `LICENSE` (11357 B), which is present in
`scratch/utmlr6/tmlr/`; it was installed too, so the copy is complete.

## Installed

`papers/encoder-crossover-190/tmlr/` — 6 copied files + `README.md` (the only new file). Copy, not
move: `scratch/utmlr6/tmlr/` retains all 6 files, and `find … -newermt '2026-10-19 00:10'` returns 0.

Fidelity: `diff -u` of the two sha256 lists is empty; all 6 installed files byte-match their
scratch originals.

## Recompiled from the installed copy alone

Isolated working dir `scratch/utmlrhome1/work/` (only the 4 installed LaTeX inputs copied in) with
workspace-local `HOME`/`TMPDIR`/`TECTONIC_CACHE_DIR`; project route
`scratch/utex1/bin/tectonic -X compile main.tex --only-cached` (no `-Z continue-on-errors`).
Exit 0; `Undefined control sequence` 0; `!` 0; errors 0; 16 pages. The rebuilt PDF differs in
digest from the installed one at **identical size** (176971 B) — `CreationDate` differs
(`Sun Oct 18 23:24:42 2026` → `Mon Oct 19 00:14:31 2026`), so this is an embedded timestamp, not a
content difference. Proof of content equality: extracted text from both is byte-identical
(73178 B, sha256 `cdedf2d2…593c6`).

The Tectonic **resource cache** used for the rebuild was a workspace-local copy
(`scratch/utmlrhome1/cache`, 21,980,729 B) of the build record's cache; the document inputs came
solely from the installed copy.

## Anonymity, from the installed PDF's own text

All zero: `Aswin`, `Kalugasala`, `Moorthy`, `Independent researcher`, `aswinram`, `gmail.com`,
`ORCID`, `github`, `GitHub`, `Zenodo`, `10.5281` (and both `10.5281/zenodo.23463944` /
`…23463945`), `analysis.json`, `ad301ae`, `907fa39`, and hex runs ≥40 chars.
`Ram` shows 25 substring hits but `\bRam\b` is 0 — they are `parameter`, `8-grams`, `program`,
`Grammar`. Raw PDF bytes also give `/Author` 0. **PDF metadata carries no author field** (`pdfinfo`
has no `Author:` line; `pdfinfo -meta` has none). First page reads "Under review as submission to
TMLR" / "Anonymous authors" / "Paper under double-blind review".

**Caveat (non-finding).** The installed PDF text does carry 13 URLs and 7 third-party DOI literals
(`10.1007/s10579-024-09796-y`, `10.18653/v1/2024.naacl-long.300`, `10.18653/v1/2025.acl-industry.68`,
and four `10.48550/arXiv.*` DataCite DOIs) plus `https://simmering.dev/blog/modernbert-vs-llm/` —
every one a citation to *another* author's work. `zenodo.org` 0, `github.com` 0; no link to any
version carrying the author's name. `main.tex:18` is `\author{Anonymous authors}`.

## Not verified

- That the PDF is byte-reproducible across runs (it is not, and cannot be, without timestamp
  normalisation) — equality is shown at the extracted-text level only.
- That `LICENSE` is required to rebuild (it is not an input; it is part of the style bundle).
- Any external/jurisdiction-side TMLR submission mechanics; no network write was made.
