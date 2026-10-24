# URENDER4 — rebuild rendered artifacts from frozen sources

**Purpose (one):** make every `papers/*/rendered/` artifact match the `submission/main.tex` it claims to be built from.

## Why
All three papers' LaTeX was regenerated since their PDFs were last built (citations repointed, abstract cleaned,
licence sentence rewritten, byline installed). `papers/*/rendered/` therefore ships stale PDFs; one author-side
notes file (`papers/encoder-crossover-190/submission/BUILD_NOTES.md`) still records stale `main.tex` figures.

## Scope / sub-goals
1. Inventory `papers/*/rendered/` (names, sizes, digests, mtimes) + read the established recipe
   (`papers/encoder-crossover-190/rendered/convert.py` or equivalent). **Do not invent a pipeline.**
2. Rebuild all three from current `submission/main.tex` with `scratch/utex1/bin/tectonic`
   (export `TECTONIC_CACHE_DIR`, `TMPDIR`, `HOME` into the workspace; **never** `-Z continue-on-errors`).
   Report literal exit code, `Undefined control sequence` count, `!` count per paper.
3. Install rebuilt artifacts under canonical names in `papers/*/rendered/`; **move** superseded artifacts to
   `papers/*/rendered/_superseded/` with a short README (existing convention).
4. Prove currency from PDF text via `pdftotext`: byline `Aswin Ram Kalugasala Moorthy` count, `AUTHOR SLOT` and
   `TO BE SUPPLIED` == 0, no editorial instruction survives; report page count + page size.
5. Correct stale `main.tex` figures in `papers/encoder-crossover-190/submission/BUILD_NOTES.md`, keeping the
   superseded values as dated history in the existing `[UNIT DATE: SUPERSEDED — …]` style.
6. Report-only: any other file in the three `papers/*/` trees claiming a figure disk contradicts.

## Hard bound
25 tool calls. If the established recipe cannot be found: STOP and report, do not invent a pipeline.

## Write paths (nothing else)
`papers/*/rendered/**`, `papers/encoder-crossover-190/submission/BUILD_NOTES.md`, `scratch/urender4/**`,
`orchestration/units/URENDER4.md`, `orchestration/handoffs/URENDER4.json`

## Do NOT
Edit any `MANUSCRIPT.md`, `submission/main.tex`, `submission/*.tar.gz`, `tools/package/**`,
`scratch/uneutral10/package/**`, or the released archive. Change no number/claim/table/figure.
No network API. Nothing outside the write paths.

## Report back
`orchestration/handoffs/URENDER4.json` with keys: unit, status, artifacts, evidence, blocker, next_unit_hint,
write_paths. ≤15-line summary to parent `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.

## Outcome log
- Recipe found, not invented: canonical PDF = `tectonic -r 1 --keep-logs -o <outdir> .../main.tex`
  (established by UINSTALL3 and by `rendered/_superseded/README.md`); `convert.py` is only the
  MANUSCRIPT.md->HTML derivative pipeline.
- All three rebuilt: exit 0, 0 `Undefined control sequence`, 0 `!` each. Installed at canonical names;
  the three prior PDFs moved (not deleted) to `rendered/_superseded/` with READMEs.
- Only **encoder** was genuinely stale in content (764-line `pdftotext` diff; old PDF predates the
  2026-10-18 main.tex). gated and replay text-diff was 0 lines — reinstalled as instructed, recorded as
  not-stale-in-content.
- `papers/encoder-crossover-190/submission/BUILD_NOTES.md`: main.tex figures 84,223 B / `8374fd28…`
  corrected to 84,695 B / `397713d7…` at :7, :209, :238, and the PDF figure to 188,364 B / `752747f8…`
  at :212, :240 — superseded values kept as dated history; new Update section appended.
- Report-only contradictions found in gated (PDF digest), replay (PDF size+digest, stale main.tex
  digest at CLAIMS.md:189 / METADATA.md:119) and the un-rebuilt 2026-10-16 derivative html/docx/lo.pdf.
- Deviation: tectonic fetched one bundle piece over the network for gated (cached afterwards).
