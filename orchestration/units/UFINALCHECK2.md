# UFINALCHECK2 — independent re-verification + finish of UFINALCHECK1's defect analysis

**Purpose:** (1) confirm/refute UFINALCHECK1's three defects, (2) run the four checks it never reached,
(3) produce the defect summary it never wrote. Report only — do NOT fix.

**Inputs:** `scratch/ufinalcheck1/findings.md` (49,292 B, sections A–L) — read first.

**Checks in scope:**
- D1: papers #7/#2 carry no declarations — which of the five (Compute, Author contributions, Funding,
  Competing interests, Use of AI tools) each lacks.
- D2: released manifest 28 listed vs counts.files 29 vs on-disk 30 (CITATION.cff, README_DEPOSIT.md unlisted).
- D3: stale "SUPERSEDED — current value is X" notes across all three papers' METADATA.md / BUILD_NOTES.md.
- C4: deposit bundle contents vs current submission/ files (byte-for-byte).
- C5: upload payload vs author-side records; scan payload only for placeholders / U[A-Z]+[0-9] / scratch/.
- C6: imperative instructions to the author in METADATA.md / BUILD_NOTES.md; superseded section or not.
- C7: README_DEPOSIT.md and CITATION.cff accuracy.

**Bound:** 22 tool calls. **Write paths:** `scratch/ufinalcheck2/**`,
`orchestration/units/UFINALCHECK2.md`, `orchestration/handoffs/UFINALCHECK2.json`.
**Rules:** `/home/zer0null/Duval` read-only; never bare `git status`; nothing written outside workspace.
