# UFIXBYLINE2 — align replay-record-not-decision byline with the other two papers

**Unit:** UFIXBYLINE2  **Bound:** 12 tool calls (this is call 1)
**Write paths:** `papers/replay-record-not-decision/**`, `orchestration/units/UFIXBYLINE2.md`,
`orchestration/handoffs/UFIXBYLINE2.json`, `scratch/ufixbyline2/**`
**Must not touch:** `tools/package/md2tex.py` logic, the other two papers, `/home/zer0null/Duval`, guards.

## Purpose
Author decision (from project memory): **solo authorship, name only, no affiliation.**
`papers/encoder-crossover-190/submission/main.tex:10` and
`papers/gated-read-batching/submission/main.tex:10` both emit
`\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`.
`papers/replay-record-not-decision/submission/main.tex` emits **no `\author`**, and
`AVAILABILITY.md:24`, `MANUSCRIPT.md:8-9`, `MANUSCRIPT.md:289-290` assert that as deliberate.
That was honest when written (no byline decided); the decision is now made, and a paper with no
author line cannot be submitted while the other two carry a placeholder slot.

## Plan
1. Read the third registry entry in `tools/package/md2tex.py`; confirm a per-package `author_line`
   data value is settable without affecting other packages. Change only that entry's data.
2. Regenerate payload twice (`cmp` byte-identical), rebuild tarball (one member `main.tex`),
   convert the new `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}` line verbatim.
3. Correct the three now-false statements (AVAILABILITY.md:24, MANUSCRIPT.md:8-9, :289-290),
   preserving the drafting-time fact as dated history.
4. Prove the other two papers' regenerated `main.tex` are byte-identical to their shipped sha256s:
   encoder-crossover-190 `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a`,
   gated-read-batching `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`.

## Rules
No invented name/affiliation/institution/email. No guard weakened. Build only under `scratch/**`
and the paper's own directory. If the paper should genuinely stay authorless, stop and report.
