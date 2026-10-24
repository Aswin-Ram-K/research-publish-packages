# UFIXBIB4 — close the two stale byline/bibliography contradictions in paper #2

**Purpose.** Two earlier units reversed paper #2's "citation-free, placeholder byline" decisions
(UBYLINE3 installed `\author{Aswin Ram Kalugasala Moorthy}`; UBIB2 added 8 verified refs, a
related-work subsection, `REFERENCES.bib`, `REFS.md`, and regenerated `submission/main.tex`
byte-identically). Two manuscript sentences and two tests still encode the superseded decisions.
This unit closes both defects without weakening any guard.

**Declared write paths.**
- `papers/replay-record-not-decision/**`
- `tests/test_md2tex.py`
- `orchestration/units/UFIXBIB4.md`, `orchestration/handoffs/UFIXBIB4.json`
- `scratch/ufixbib4/**`

**Hard bound.** 20 tool calls. STOP and report if paper #2's shipped digest has moved from
`f4997c580d84c150bcb8348299c50b828c99321446f9c02dab468406f888145f` at recon time.

**Rules.** `/home/zer0null/Duval` read-only, never `git` against it. `submission/main.tex` is
GENERATED — regenerate only via `python3 tools/package/md2tex.py`. Never weaken, disable or
delete a guard to make a test green; report an honest failure instead.

**Defect A.** `MANUSCRIPT.md:8-9` and `:290-292` say the byline is "a placeholder slot ..." while
`:10` now carries a real author. Fix both to state the truth, retaining the superseded text as
dated history. Regenerate; prove 0 `placeholder slot` in shipped `main.tex` and exactly one
`\author` line reading the real name.

**Defect B.** `tests/test_md2tex.py::test_zero_bibliography_guard` asserts paper #2
`cfg['bib_source'] == 'none'` (now `'bibtex_file'`); the byline/citation test asserts `\cite{`
absent from paper #2 (it now cites). Retarget both to the live invariants:
`expected_bib_count=8`, `expect_zero_bib=False`, 8 `\bibitem`, 8 distinct cited keys, 0 uncited,
0 unresolved. A test that passes because nothing is checked is worse than the one it replaced.

**Status at card time:** recon pending.
