# UWORD1 — duplicate DOI wording in the Persistent-identifier paragraph

**Unit type:** author-side fix + full artifact regeneration (not a verifier).
**Bound:** 20 tool calls (used 17, including this card). Declared write paths: `papers/encoder-crossover-190/**`,
`scratch/uword1/**`, `scratch/ufixman1/build_archive.sh` (guard pins only — not needed), `strategy/DEPOSIT_ARCHIVE.md`
(not needed), own card + handoff.

## Finding (quoted before any change)

`papers/encoder-crossover-190/MANUSCRIPT.md:858-861`, verbatim before the edit:

> **Persistent identifier: DOI `10.5281/zenodo.23463944`.** The released reproducibility package
> (29 files; no evaluation harness — see Data and code availability) is published on Zenodo under that DOI
> (concept DOI `10.5281/zenodo.23463944`), so the released artifacts carry a persistent identifier as well
> as a licence statement.

Identifier sweep: `grep -n 'concept DOI\|version DOI'` matched **only** this paragraph in `MANUSCRIPT.md`
(plus its derived `main.tex:427` and `rendered/*.html:992`). No other sentence contrasts a version DOI with a
concept DOI or names an identifier twice; the other three mentions sit one per line (`743`, `794`, and after the
fix `858`).

## Fix and why

Folded the concept-vs-version information into the leading label (`DOI` → `concept DOI`) and deleted the
redundant parenthetical. The parenthetical's only unique content was the word *concept* — stated nowhere else in
the manuscript — so deleting it outright would have dropped information; folding it into the label keeps it while
naming the identifier once. No new identifier, no version DOI claimed, persistent-identifier and licence
statements intact. `diff` before→after is exactly `858,861c858,860` in `MANUSCRIPT.md` and one line
(`main.tex:427`) in the payload.

## Artifacts regenerated with project tooling (never hand-patched)

- `main.tex` — `python3 tools/package/md2tex.py --package encoder-crossover-190`, built twice (`cmp` clean):
  **84,747 B / sha256 `419ac0cc7b1c88493cac6fca0c53a72a7a66fd41eaf7b0bd90f9b746c73af3ec`**.
- Tarball — BUILD_NOTES UFIXCITE5 recipe, built twice (`cmp` clean), member byte-identical to `main.tex`:
  **28,567 B / sha256 `fbb0729651becfe40eedfab92bc07d37910c36bbf65ffcca5041d53722ad9d49`**.
- PDF — `scratch/utex1/bin/tectonic -r 1 --keep-logs -o scratch/uword1/pdfout submission/main.tex`
  (`HOME`/`TMPDIR`/`TECTONIC_CACHE_DIR` inside the workspace, no `-Z continue-on-errors`): exit **0**, **0**
  `Undefined control sequence`, **0** `!` lines. **188,793 B / sha256 `bb806e3d…`**.
- HTML — `rendered/convert.py`: **85,998 B / sha256 `8e3c802a23c2f5acb09cee2da97b033a0323cb7de05409f054d49a58244b19ce`**.
- Deposit archive — `BUILD_WORK=scratch/uword1/archive sh scratch/ufixman1/build_archive.sh`: built twice,
  `BYTE-IDENTICAL` to the shipped file; `want_cit` pin `32bee18f…` still matched (CITATION.cff unchanged).
  **159,185 B / sha256 `196f5311…` / md5 `b3b30f66d231924e02706de0eb3fbc15`** (unchanged bytes; the archive
  does not contain the paper text).
- `BUILD_NOTES.md` — dated UWORD1 update appended; earlier figures retained verbatim as history.

## Invariance

Only the removed duplicate DOI's numeric tokens moved: numlit `added={}`, `removed={'10.5281':1}` and raw
digit-runs `removed={'10':1,'23463944':1,'5281':1}` for `MANUSCRIPT.md`, `main.tex` and the PDF text alike.
DOI occurrences 4→3 in each; `concept DOI` 1→1. `\bibitem` 13 / `\cite` 23 / distinct 13 / uncited 0 /
unresolved 0 — unchanged. `check_manifest.py` → all five counts 0, `VERDICT PASS`, exit 0;
`verify/recompute-claims.py` → `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, exit 0.

## Disagreement with the card

The card named `main.tex` 84,695 B / `397713d7…` and the PDF 188,364 B / `752747f8…` as the stale figures.
Measured from disk **before** any edit, the payload was two generations further on: `main.tex` 84,786 B /
`35a1bc96…`, PDF 188,819 B / `80b3f3e4…`, tarball 28,572 B / `6743c918…`.
