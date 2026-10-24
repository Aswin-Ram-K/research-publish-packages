# UFIXGR8 — Paper #7 internal-pointer corrections (final prose pass)

**Purpose:** Remove the internal-document pointers that a reader outside this workspace cannot
resolve from the body prose of `papers/gated-read-batching/MANUSCRIPT.md` (`CLAIMS.md`,
`GAPS.md G-25`, `REFS.md`); normalise the `**Status:** draft manuscript …` banner at
`MANUSCRIPT.md:3`; regenerate `papers/gated-read-batching/submission/main.tex` with the paper's
own converter `scratch/uprep7/md2tex.py` (the only regeneration path — `main.tex` is never
hand-edited); rebuild the tarball exactly as UPREP7 did; re-run every proof in UPREP7's handoff;
record the new sizes/digests in `BUILD_NOTES.md` beside the previous ones.

**Declared write paths (exactly these):**
- `papers/gated-read-batching/MANUSCRIPT.md`
- `papers/gated-read-batching/submission/main.tex`
- `papers/gated-read-batching/submission/gated-read-batching.tar.gz`
- `papers/gated-read-batching/submission/BUILD_NOTES.md`
- `orchestration/units/UFIXGR8.md`
- `orchestration/handoffs/UFIXGR8.json`
- `scratch/ufixgr8/**`

**Hard bound:** 12 tool calls. `/home/zer0null/Duval` untouched — no git command of any kind
against it. No TeX toolchain, no installs, no fabricated PDF.

## Occurrences found (whole-manuscript grep, not only UPREP7's three lines)

| Line | Text | Disposition |
|---|---|---|
| 3 | `**Status:** draft manuscript prepared from a closed 2026-09-30 measurement run. …` | Job 2: normalise to a neutral statement (no `Status:`, no `draft`) |
| 84 | `… this is a validity limitation, stated in full at GAPS.md G-25.]**` — inside the dated `[correction 2026-10-15, UFIXGR7: …]` marker | **(a) reword**: pointer → "internal gap log (entry G-25; an internal working record not included in the released material)". Marker date, unit id and correction content preserved verbatim. |
| 127 | `… traced to a source file and line in \`CLAIMS.md\` (exact-line accuracy 71/73; …)` | **(a) reword**: drop the filename; keep traceability, 71/73, C48/C65 |
| 223 | `… maintained in [\`REFS.md\`](REFS.md).` | **(a) reword**: "maintained in this record's internal reference notes (an internal working record not included in the released material)" |
| 225 | `… (Venue not verified — see REFS.md.)` | **(a) reword**: "(Venue not verified.)" |

Siblings searched for and **absent**: `EVIDENCE_NOTES.md`, `OPEN_QUESTIONS.md`,
`REFERENCE_NOTES.md`, `UNSOURCED_RETAINED.md`, bare `scratch/` paths, any other `*.md` name.
No number, claim, citation or result meaning is changed. After the edit no reader-visible
sentence names a file the paper does not ship (`GAPS.md`'s trailing clause sits in a dated
provenance marker, so that one edit is deliberately minimal — date, unit id and correction
content stay).

**Status (as of card write):** discovery done, dispositions chosen; edits, regeneration,
tarball rebuild, proofs and BUILD_NOTES update pending.
