# UPREPRINT2 — byline, Conflicts of Interest, page-1 keywords; regenerate + prove

**Bound:** 30 tool calls. **Used:** 24. **Status:** partial (papers #2/#7 have no recorded keyword set; card forbids inventing).
**Write paths:** papers/*/MANUSCRIPT.md, papers/*/submission/**, papers/*/preprints/**, papers/*/rendered/**, tools/package/md2tex.py, tests/test_md2tex.py, strategy/LATEX_TOOLCHAIN.md, strategy/PREPRINTS_SUBMISSION.md, scratch/upreprint2/**, this card, own handoff.
**Forbidden (honoured):** papers/encoder-crossover-190/released/**, /home/zer0null/Duval, git state changes, uploads, tectonic -Z.

## Jobs
1. Byline via the converter registry (single source of truth): `PACKAGES[*]["author_line"]` now the same three lines for all three packages; `tests/test_md2tex.py` pins each package exactly; red proof = drop the email from one registry entry on a copy -> test FAILS.
2. "Conflicts of Interest": requirement quoted from Preprints.org's own page, then satisfied by RENAMING the existing declaration section (heading + mirror label) and moving it to sit just before the reference list; declaration sentence untouched.
3. Keywords on page 1: paper #3's 8 recorded keywords (strategy/DEPOSIT_METADATA.md §1/§2) emitted right after `\maketitle`; #2/#7 have no recorded set anywhere -> none added (reported, not invented).

## Evidence
- `python3 -m pytest tests/test_md2tex.py --noconftest -q` -> `7 passed`.
- Red: `MD2TEX_TOOL=scratch/upreprint2/md2tex_noemail.py ... -q` -> `FAILED ... AssertionError: gated-read-batching: registry byline is not the shared three-line byline (affiliation+contact required for every package)`.
- Strict compile from clean zip extraction, `-r 1 --keep-logs` (no `-Z`): EXIT=0 / Undefined=0 / `!`=0, pages 25 / 13 / 10.
- Zips: 1 member each (`main.tex`), extracted == submission (`cmp`).
- Numeric: MANUSCRIPT.md unchanged ×3; main.tex #3 unchanged, #7 +1 token `1603`, #2 +1 token `1603` (byline email, not a measurement).
- Cite metrics identical pre/post ×3.
