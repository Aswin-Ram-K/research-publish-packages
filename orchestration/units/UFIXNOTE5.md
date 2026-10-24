# UFIXNOTE5 — clear stale figures; quarantine stale derivative artifacts

**Purpose:** verify + fix stale recorded byte sizes / sha256 / page counts in three papers' author-side
records; move stale non-LaTeX derivatives into `rendered/_superseded/`.
**Hard bound:** 12 tool calls.
**Write paths:** the two papers' submission METADATA.md/BUILD_NOTES.md, replay CLAIMS.md,
`papers/*/rendered/**`, `scratch/ufixnote5/**`, `orchestration/units/UFIXNOTE5.md`,
`orchestration/handoffs/UFIXNOTE5.json`. Nothing else.
**Do NOT:** touch MANUSCRIPT.md, main.tex, *.tar.gz, encoder-crossover-190, tools/package, released archive;
no network; no body number/claim changes.

## Plan
1. Measure all recorded values against disk (sha256/size/pages/line counts) for all three papers.
2. Fix real contradictions in place with `[UNIT DATE: SUPERSEDED — …]` dated history.
3. Report non-real contradictions as correct.
4. Quarantine stale derivatives to `rendered/_superseded/` + README matching encoder-crossover-190 style.
5. Prove MANUSCRIPT.md / main.tex untouched via before/after size+sha256.
