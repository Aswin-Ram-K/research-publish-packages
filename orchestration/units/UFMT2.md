# UFMT2 — Consolidated submission-readiness decision document

**Status:** done · **Date:** 2026-10-16 · **Hard bound:** 20 tool calls (used 19).
**skeleton_written_first:** yes — this card and `orchestration/handoffs/UFMT2.json` were written before any
source was read (see the handoff `evidence.skeleton_written_first`).

## Purpose
Six audits landed with their findings scattered across separate files. This unit consolidates them into ONE
decision document answering the author's question: *is this paper submission-ready, what must I supply, and
what must be fixed?*

## Deliverable
`strategy/SUBMISSION_READINESS.md` — verdict, then Table A (author-only supplies), Table B (ordered mechanical
fixes), Table C (route-by-route readiness), Table D (cannot be checked on this host), the UCITE1↔UCHECK1
reconciliation, the genuinely-unresolved list, and a reconciliation ledger.

## Sources read (quoted, never re-derived)
`strategy/FORMATTING_REQUIREMENTS.md` (UFMT1: 40 rows R1–R44), `strategy/CITATION_SUPPORT_AUDIT.md` (UCITE1),
`strategy/CITATION_FETCH_VERIFICATION.md` (UCHECK1), `strategy/ORIGINALITY_CHECK.md` (UPLAG1),
`strategy/ORIGINALITY_CHECK_SUPPLEMENT.md` (UPLAG2), `strategy/STYLE_COMPLIANCE.md` (USTYLE1),
`strategy/ARXIV_SUBMISSION_PREP.md` (UPREP1), `strategy/BIBLIOGRAPHY_REPAIR.md` (UBIB1),
`papers/encoder-crossover-190/submission/METADATA.md`, `.../BUILD_NOTES.md` (via USTYLE1/UPREP1).

## Verdict recorded
**NO — not submittable today.** Three causes: (1) no author at all (`main.tex:12` placeholder;
`METADATA.md:12-14,16` NOT SUPPLIED); (2) the arXiv cs.CL endorsement is absent (R10, six-character code);
(3) the bibliography is entirely uncited (13 `\bibitem` / 0 `\cite`, R18) and the draft-status paragraphs
ship in the PDF (`main.tex:16-18`, R17).

## Row counts
- Table A: 13 rows (A1–A13)
- Table B: 15 rows (B1–B15)
- Table C: 6 rows (arXiv, TMLR, Preprints.org, Research Square, OSF, Zenodo)
- Table D: 14 rows (D1–D14)

## Verification performed in-unit
- `fixture/DECISION_CASE_SCHEMA.ts:22` quoted `/** The 2-8 (never more) options, as short semantic labels. */`
  — confirming UCITE1's arity finding is weaker than it first looked (schema permits 2–8; the fixture observes
  K = 2–5; the paper states that distribution correctly at `MANUSCRIPT.md:257-259`).
- Every table row carries a file:line or requirement ID; no row is unlocated.

## Constraints honoured
- Nothing under `papers/` was edited; nothing was fixed.
- Disagreements reconciled explicitly in §6 and §8 rather than silently dropped.
- Numbers are quoted from the listed audits; the two counts not present in them (43 files / 29 files) are
  labelled as coming from the UFMT2 unit card.

## Write paths
`strategy/SUBMISSION_READINESS.md`, `orchestration/units/UFMT2.md`, `orchestration/handoffs/UFMT2.json`.
