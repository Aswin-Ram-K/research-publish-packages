# UBIB2 — Related-work section + bibliography for paper #2

## Purpose
Paper #2 `papers/replay-record-not-decision/` ships with zero references. Add a real
related-work subsection to `MANUSCRIPT.md` and a verified bibliography (5–8 real,
verifiable references) wired into the `tools/package/md2tex.py` registry for paper #2,
so the generated `submission/main.tex` contains real `\cite`/`\bibitem` pairs.

## Hard constraints
- **20 tool calls maximum.**
- `/home/zer0null/Duval` STRICTLY READ-ONLY. Never run git against it (not needed here).
- **Never invent a citation.** Every entry verified from a primary source (arXiv abs
  page / ACL Anthology / DOI landing page). Unverifiable candidates are dropped and
  reported as unresolved.
- **No measured number may change.** Numeric multiset of `submission/main.tex` before
  == after; prove by token count + digest.
- `\author` count stays exactly 1 and the line stays exactly
  `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`.
- Bibliography must be ASCII (LaTeX escapes for accented names).
- Do not weaken `tests/test_md2tex.py`; report any conflict verbatim.
- `md2tex.py` is the only supported generator.

## Plan
1. Persist card; read MANUSCRIPT + CLAIMS/GAPS/AVAILABILITY + house-style refs.
2. Read md2tex.py paper-#2 registry entry (require_author_slot / citation guard).
3. Search + verify 5–8 real references from primary sources.
4. Capture BEFORE baseline (numeric multiset, author line, non-ASCII) of main.tex.
5. Write related-work subsection + bibliography in project format; wire registry.
6. Regenerate twice; prove byte-identical; prove cite/entry invariants.
7. Prove AFTER == BEFORE (numbers, author, ASCII), tarball member == disk main.tex.
8. Run pytest; report literal result and any conflict.
9. Dated notes in CLAIMS/GAPS/BUILD_NOTES. Write handoff JSON; message parent.

## Declared write paths
- `papers/replay-record-not-decision/**`
- `orchestration/units/UBIB2.md`, `orchestration/handoffs/UBIB2.json`
- `scratch/ubib2/**`
