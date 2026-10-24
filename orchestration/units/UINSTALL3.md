# UINSTALL3 — install correct PDFs, retire superseded builds, kill false byline claims

**Purpose.** Make the three papers' deliverables *findable and truthful*: a clean PDF in
`papers/<slug>/rendered/<slug>.pdf`, superseded PDFs quarantined with an explanation, and every
shipped-looking documentation file purged of the false claim that the byline is unfilled.

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 25 tool calls.

## Declared write paths
- `papers/<slug>/rendered/**` (all three slugs)
- `papers/<slug>/AVAILABILITY.md`
- `papers/<slug>/submission/METADATA.md`, `papers/<slug>/submission/BUILD_NOTES.md`
- `orchestration/units/UINSTALL3.md`, `orchestration/handoffs/UINSTALL3.json`
- `scratch/uinstall3/**`

## Rules of engagement
- `/home/zer0null/Duval` strictly read-only; never run git against it.
- `submission/main.tex` is GENERATED — never hand-edit; regenerate via
  `python3 tools/package/md2tex.py --package <slug>`.
- Do not change any measured number, sentence meaning, reference or bibliography entry.
- Persist card first (this file), handoff last, ≤15-line return.

## Starting state (from card)
- `scratch/utex1/bin/tectonic` v0.15.0; needs `TECTONIC_CACHE_DIR`, `TMPDIR`, `HOME` exported
  *inside* the workspace or it dies `Read-only file system (os error 30)`.
- Working command: `scratch/utex1/bin/tectonic -r 1 --keep-logs -o <outdir> papers/<slug>/submission/main.tex`.
  No `-Z continue-on-errors` (it silently deletes unresolvable text).
- UFIXTEX1 left clean PDFs in `scratch/ufixtex1/pdf/<slug>/main.pdf`, NOT in `rendered/`.
- `replay-record-not-decision/submission/main.tex` was regenerated after that compile ⇒ stale.
- `encoder-crossover-190/rendered/encoder-crossover-190-latex.pdf` = superseded letter-size build
  with four broken `§B3`/`§F.3` cross-references ("internal reference notes 3;"). Chrome prints
  (A4, no page numbers, no numbered bibliography, stale byline) also superseded.
- Author: **Aswin Ram Kalugasala Moorthy**. Exactly one `\author{Aswin Ram Kalugasala Moorthy}`
  line; zero `AUTHOR SLOT` / `placeholder slot`.

## Jobs
1. Recompile any paper whose `main.tex` is newer than its PDF; require exit 0, 0 `Undefined control
   sequence`, 0 LaTeX `!` errors.
2. Install clean PDF to `papers/<slug>/rendered/<slug>.pdf`; report bytes/sha256/pages/page size.
3. Move superseded PDFs to `papers/<slug>/rendered/_superseded/` + `README.md`; never delete.
4. Sweep all three papers for false byline claims (`AUTHOR SLOT`, `placeholder`, `to be supplied`,
   `unfilled`, `not supplied`, `absent`, "no author") and correct in place, keeping old wording as
   dated history.
5. Prove from artifacts: byline counts in extracted PDF text, `§B3`/`§F.3` present and corrupted
   forms absent, per-paper `\author`/`\bibitem`/`\cite` counts, `pytest tests/test_md2tex.py -q`,
   and byte-identical regeneration into a scratch dir.

## Progress log
- (start) Surveyed workspace: all three `submission/main.tex` are mtime 2026-10-16T22:40:39, newer
  than every rendered PDF (22:31–22:33) ⇒ **all three need recompiling**, not just replay.
  `papers/replay-record-not-decision/rendered/` does not exist yet and must be created.
