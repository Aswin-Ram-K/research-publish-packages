# VUTMLR5 — independent verifier of UTMLR5 (TMLR #3 anonymised variant)

**Role:** verifier, NOT author. Author was `UTMLR5`. I try to falsify its claims by re-deriving them.

**Purpose:** re-derive the build of paper #3's anonymised TMLR variant, run the red→green test on the
`\setcitestyle{numbers}` insertion, reproduce compile facts, reproduce the anonymity proof from PDF text,
check the residue claim against the approved `UTMLR2` baseline, and check citation structure.

**Claims under test:**
- B1 cleared by `\setcitestyle{numbers}` inserted *after* `\usepackage{tmlr}` (runtime switch beats
  `tmlr.sty:20`'s own `\setcitestyle{authoryear,...}`; load-time `\PassOptionsToPackage{numbers}{natbib}`
  does not).
- B2 cleared: `SCRUB3` in `scratch/utmlr5/build.py`, 7 rules each matching once; residue
  `private-doc-name` 2, `private-repo-word` 1, all else 0 — said to equal the approved baseline
  (`UTMLR4` was 2/3/5).
- `scratch/utmlr5/tmlr/main.tex` 83,785 B, 476 lines, sha256
  `8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0`; byte-identical across two builds.
- Compile exit 0, 0 `Undefined control sequence`, 0 `!` lines, 0 error lines, 16 pages, PDF 176,971 B,
  sha256 `971a96ae8238e91e2be1982b87892c73e2b915668ed9438c399034253ff3e937`; with
  `SOURCE_DATE_EPOCH=1700000000`, two runs give `0c35ed5603253ec5e049639f1637014999d620f94c445670ef5b8932593eac06`.
- Anonymity from extracted PDF text: listed needles all 0, `Anonymous authors` 1.
- Structure: 23 `\cite`, 23 keys, 13 distinct, 13 `\bibitem`, 0 uncited, 0 unresolved, `analysis.json` 0.
- Numeric multiset 1203 → 1092, distinct 347 → 310, 0 added.

**Hard bound:** 20 tool calls (this card counts as #1). If something cannot be reproduced, report
non-reproduction and what was tried.

**Write paths (nothing else):** `scratch/vutmlr5/**`, `strategy/VERIFICATION_REPORT_TMLR5.md`,
`orchestration/units/VUTMLR5.md`, `orchestration/handoffs/VUTMLR5.json`.

**Do not:** edit `scratch/utmlr1|2|4|5/**`, `papers/**`, `tools/package/**`, released archive; fix anything
(report only); call any network API; write outside listed paths.
