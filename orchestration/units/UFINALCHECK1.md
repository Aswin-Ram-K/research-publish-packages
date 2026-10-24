# Unit UFINALCHECK1 — adversarial pre-submission audit

**Purpose (one):** Read-and-report audit of the three paper submission payloads, the Zenodo
deposit bundle and the released data package, before the author submits. Not the author of any
of it. **Do not fix anything.**

**Scope / checks (per paper):**
1. Three-file contract: tarball has exactly one member, byte-identical to `submission/main.tex`
   (`cmp`), bytes+sha256 for main.tex, tarball, PDF, ABSTRACT.txt, ABSTRACT_METADATA.txt,
   METADATA.md, BUILD_NOTES.md.
2. No placeholder/internal artifact ships: `AUTHOR SLOT`, `TO BE SUPPLIED`, `AUTHOR NAME`,
   `TO CONFIRM`, `AUTHOR TO`, `TBD`, `TODO`, `FIXME`, `XXX`, unit ids `U[A-Z]+[0-9]`, `scratch/`.
3. Byline: exactly one `\author` line per paper, real name; `AUTHOR SLOT` count in PDF text == 0.
4. Bibliography: `\bibitem` count, `\cite` count, distinct cited keys, undefined==0, uncited==0.
5. PDF real: page count, page size, title/abstract/"Use of AI tools" present, no raw LaTeX /
   `\cite` / `??` leak. Compare sentences with hyphens dropped on BOTH sides.
6. Cross-file consistency: stale sizes/digests in METADATA.md / BUILD_NOTES.md unless labelled
   superseded.
7. ABSTRACT_METADATA.txt <= 1920 chars; ABSTRACT.txt == PDF abstract; report both counts.
8. Release package: file count, total bytes, MANIFEST.json self-consistency, counts.bytes_total.
9. Deposit bundle: contents, size, whether paper files match current submission/.

**Hard constraints:** `/home/zer0null/Duval` strictly read-only, never run git against it, never
a bare `git status`. Write nothing outside this workspace. Do not fix. Exclude `archive/` from
"shipped payload" claims.

**Declared write paths:** `scratch/ufinalcheck1/**`, `orchestration/units/UFINALCHECK1.md`,
`orchestration/handoffs/UFINALCHECK1.json`.

**Hard bound:** 30 tool calls. Findings written incrementally to `scratch/ufinalcheck1/findings.md`.

**Status:** started.
