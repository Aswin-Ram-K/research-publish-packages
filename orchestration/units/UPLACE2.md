# UPLACE2 — apply A1–A4 citation-placement edits to paper #3

**Purpose (one):** apply the already-decided A1–A4 before/after edit pairs from
`strategy/INTERNAL_REFERENCE_PLACEMENT.md`, rewriting the two `REPORT.md:189`
citations inside paper #3's abstract into prose; regenerate LaTeX; prove nothing
else moved.

**Hard bound:** 20 tool calls. Exact-match assertion before each write; STOP and
report if any before-string does not match exactly once.

**Write paths (only):**
`papers/encoder-crossover-190/MANUSCRIPT.md`,
`papers/encoder-crossover-190/submission/**`, `scratch/uplace2/**`,
`orchestration/units/UPLACE2.md`, `orchestration/handoffs/UPLACE2.json`.

**Do NOT:** edit papers #1/#2, `tools/package/md2tex.py`,
`scratch/uneutral10/package/**`, or the released archive; no network APIs;
never hand-edit `main.tex`; never use `-Z continue-on-errors`.

**Steps:** (1) apply A1–A4 with assertions; (2) regenerate via
`python3 tools/package/md2tex.py --package encoder-crossover-190`, rebuild
tarball, build twice, `cmp` for byte-identity, report sizes+sha256;
(3) prove numeric-literal multiset + bibitem/cite counts unchanged;
(4) Tectonic compile, report exit code / undefined-cs count / `!` count / pages;
(5) confirm `REPORT.md:189` gone from abstract extent; (6) run tests;
(7) state whether anonymised TMLR variant is stale.

**Status:** done (14 tool calls of 20). A3/A4 applied with exact-match assertions (A4
before-string has NO trailing space — the doc's trailing space is code-span padding);
main.tex regenerated (84225 B, sha256 ce71230f…) and tarball rebuilt reproducibly
(28452 B, sha256 f660e8eb…; two builds `cmp`-identical). Reverse-regen diff = exactly
one hunk at main.tex:19, byte delta −60 = the two removed 30-byte locators.
`REPORT.md:189` gone from the abstract (body only, main.tex:149 / MANUSCRIPT.md:302).
Tectonic exit 0, 0 undefined, 0 `!`, 25 pages. Tests 7 passed. Bib 13/23/13/0/0
unchanged. Numeric multiset differs by exactly {189: −2} (the two removed locators) —
no published number moved. TMLR variant is stale (already was) and still carries the
citation in its abstract.
