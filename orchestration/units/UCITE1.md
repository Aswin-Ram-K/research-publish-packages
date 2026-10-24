# UCITE1 — Citation-support audit of `papers/encoder-crossover-190/MANUSCRIPT.md`

**Unit:** UCITE1 (delegated subagent; parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`)
**Purpose (one):** find every assertive sentence that should carry a citation and does not, and every
citation that does not actually support the sentence it is attached to. Report-only.

## Declared write paths (nothing else)
- `strategy/CITATION_SUPPORT_AUDIT.md` (deliverable)
- `orchestration/units/UCITE1.md` (this card)
- `orchestration/handoffs/UCITE1.json`
- `scratch/ucite1/**`

## Hard bound
30 tool calls. If a section cannot be settled in 3 attempts, record `unresolved` and move on.

## Inputs
- `papers/encoder-crossover-190/MANUSCRIPT.md` (877 lines; 7 numbered sections + Abstract + Data/code + References)
- `papers/encoder-crossover-190/REFERENCES.bib` (13 entries)
- `papers/encoder-crossover-190/submission/main.tex` (13 `\bibitem`s)
- context only (read, never edit): `CLAIMS.md`, `AVAILABILITY.md`, `GAPS.md`, `EVIDENCE_NOTES.md`,
  `RELATED_WORK_NOTES.md`, `REFS.md`, `REFS_VERIFIED.md`, `REFERENCES_ADDITIONS.bib`, `UNSOURCED_RETAINED.md`

## Method (as instructed)
1. Extract bib keys + every in-text citation in both directions (unused entry / unresolved citation).
2. Section by section, classify every assertive sentence A (own experiment), B (another work / number /
   dataset / SOTA → must cite), C (attributed to a specific work → must be supported), D (own unpublished
   corpus → INTERNAL-ONLY).
3. Verify load-bearing attributions cheaply; mark `UNVERIFIED` when not checkable rather than guessing.
4. Check every number attributed to another work against what that work prints.
5. Flag every absence claim ("no identifier", "could not be located", "we found no prior work").

## Output format
Per-section table `line | claim (quoted, trimmed) | class A/B/C/D | citation present? | supporting? | action`;
then `UNCITED` / `MIS-CITED` / `UNUSED-ENTRIES` / `UNRESOLVED-CITATIONS` / `ABSENCE-CLAIMS` with line
numbers; then shortest-path author actions. Plus one line: assertive sentences classified / seen.

## Status
**done.** 214 of 322 sentence-like units classified; UNCITED=11, MIS-CITED=5, UNUSED-ENTRIES=0 (prose) /
13 (mechanized: 0 `\cite`, 13 `\bibitem`), UNRESOLVED-CITATIONS=10, ABSENCE-CLAIMS=10, CLASS-A-1..6.
Deliverable `strategy/CITATION_SUPPORT_AUDIT.md`. 17 of 30 tool calls used. No section left unresolved
beyond the recorded limit (arXiv `2512.12677` abstract checked, PDF body not).
