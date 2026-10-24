# UFIXTEX1 — fix text-integrity defect: `\S` control word absorbing the following letter

**Bound:** 25 tool calls. **Status:** in progress.

## Purpose
Tectonic (genuine LaTeX toolchain) reports four `Undefined control sequence` errors in the
generated papers. They are not toolchain problems: `tools/package/md2tex.py` maps the section
sign `§` to the bare control word `\S`, so `§B3` -> `\SB3`. TeX reads `\SB` as ONE control word,
which does not exist. With `-Z continue-on-errors` the compile still writes a PDF and the broken
reference silently loses `§B`: it rendered as `internal reference notes 3;` and
`record .3 is not discharged`. The same defect therefore corrupts cross-references in every
previously shipped PDF. Fix at the source (converter), regenerate, recompile with **zero**
errors (no `continue-on-errors`), add a regression test.

## Declared write paths
`tools/package/md2tex.py`, `tests/test_md2tex.py`,
`papers/{encoder-crossover-190,gated-read-batching,replay-record-not-decision}/**`,
`orchestration/units/UFIXTEX1.md`, `orchestration/handoffs/UFIXTEX1.json`, `scratch/ufixtex1/**`.

## Concurrency
Digests recorded at start (m00005/m00008):
- `tools/package/md2tex.py` sha256 `c23e0b70f17a9fd9a5db9e406efea5ae773ae17115a5b34cbf1ac6e07ab531f7`
- `tests/test_md2tex.py` sha256 `c121dbe5c7cd8634a07554e9676fb8f1d436c7249ef22bd5923a2f7de027089a`
- `papers/encoder-crossover-190/submission/main.tex` `9cab7a4324509423bc9c24ac47e1faa7facff9128659278738ce585a4d35657d`
- `papers/gated-read-batching/submission/main.tex` `165549a22d27b35ad6a4e2efe3f3457f806bb464fa7f16b493f9f79c3a515a67`
- `papers/replay-record-not-decision/submission/main.tex` `f4997c580d84c150bcb8348299c50b828c99321446f9c02dab468406f888145f`
Re-checked before writing; re-check after. `/home/zer0null/Duval` untouched, no `git` run against it.

## Job 1 findings (sweep, m00005)
Full sweep of all three manuscripts, section sign and every escaped special
(`% & _ # \ ~ ^ < >`):
- `papers/encoder-crossover-190/MANUSCRIPT.md`: 63 `§`; **4** are `§` immediately followed by a
  letter -> :127 `§B3`, :638 `§F.3`, :643 `§F.3`, :653 `§F.3`. These are the only instances of
  the defect class in the whole corpus.
- `papers/gated-read-batching/MANUSCRIPT.md`: 0 `§`; `%`,`&`,`#`,`_`,`~`,`\` present but all map to
  control SYMBOLS (`\%`, `\&`, ...) or braced macros (`\textasciitilde{}`, `\ldots{}`,
  `\textbackslash{}`), which cannot absorb a following letter.
- `papers/replay-record-not-decision/MANUSCRIPT.md`: 11 `§`, none followed by a letter.
- Generated `main.tex` sweep `\\[A-Za-z]+(?=[A-Za-z])`: exactly 4 hits, all in
  `papers/encoder-crossover-190/submission/main.tex` at lines 62, 335 (twice), 339.
- `\S` followed by a *digit* (`\S11.2`, `\S6.4`) is harmless: TeX ends a control word at a
  non-letter. Only letters extend the name.

## Planned fix
1. `Converter.esc()` (`tools/package/md2tex.py:356-357`): general terminator pass — a control word
   (backslash + letters) immediately followed by a letter gets `{}` inserted, so `\S`+`B` ->
   `\S{}B`. General over the escape output, not a `§`-only patch.
2. `\documentclass[11pt]{article}` (`tools/package/md2tex.py:640`): article defaults to US letter;
   add `a4paper` -> `\documentclass[11pt,a4paper]{article}` (Job 4).
3. Regenerate all three packages; prove byte-identical across two runs.
4. Compile each **without** `-Z continue-on-errors`; require exit 0, 0 `Undefined control sequence`,
   and `§B3`/`§F.3` present in the extracted PDF text.
5. Regression test in `tests/test_md2tex.py`, derived from the converter's own escape tables
   (`SPECIALS` + every package `unicode` map), red on the pre-fix copy kept at
   `scratch/ufixtex1/md2tex_prefix.py`, green on the fixed tool.

## Result (final)
- **Job 1:** only 4 defect sites, all `papers/encoder-crossover-190/MANUSCRIPT.md` (`:127` §B3, `:638`/`:643`/`:653` §F.3); generated hits = `main.tex:62, :335 x2, :339`. No other char in the checked set (`% & _ # \ ~ ^ < >`) escapes into a control word that can absorb a following letter.
- **Job 2:** fixed `Converter.esc` in `tools/package/md2tex.py` (`CONTROL_WORD_ONLY` + per-character `{}` termination); all three papers regenerated, `diff -r` of two runs empty.
- **Job 3:** all three compile with **exit 0** and **0 `Undefined control sequence`** WITHOUT `-Z continue-on-errors`; extracted PDF text reads `§B3` and `§F.3`; corrupted forms = 0.
- **Job 4:** A4 achieved (`595.28 x 841.89 pts`) via `a4paper` + `\pdfpagewidth/\pdfpageheight`; the option alone had left 612x792pt letter.
- **Job 5:** `test_no_control_word_absorbs_a_letter` red on `scratch/ufixtex1/md2tex_prefix.py` (4 hits), green on the fix; full file `7 passed`.
- Residual (warning class, pre-existing): 4 long path words overhang the encoder right page edge by <=4.4pt.
