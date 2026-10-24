# UCITE4 — Close paper #3's unfollowable citations (final planned edit)

**Purpose:** Make every citation in paper #3 (`papers/encoder-crossover-190/`) either followable to a
file that ships in `scratch/uneutral10/package/` (29 files) or plainly attributed as deliberately
withheld. No citation may look followable and not be.

**Hard bound:** 25 tool calls. Unclassifiable target → mark UNKNOWN, report, do not guess.

**Write paths (only these):**
- `papers/encoder-crossover-190/MANUSCRIPT.md`
- `papers/encoder-crossover-190/submission/**`
- `scratch/ucite4/**`
- `orchestration/units/UCITE4.md`
- `orchestration/handoffs/UCITE4.json`

**Never:** invent a line/section number; hand-edit `main.tex`; edit papers #1/#2, `tools/package/**`,
`scratch/uneutral10/package/**`, or the released archive; change any number/claim/table/figure;
network APIs.

## Residual list to verify (from prior unit)
1. Dev-curve pair `1.1288 → 1.1235` claimed unshipped (0 hits `1.1287`/`devCurveTrainLoss` in package)
   while dev accuracies + `0.4750` *are* followable at the cited section.
2. `lint-report.json` and `harness/data/lint-report.json` — reported not shipping.
3. `results/DEFECT-EVIDENCE.json` — reported self-declaring exclusion.

## Tasks
1. Complete citation inventory from a *command*, both directions (shipping/not + byte size).
2. Close every unfollowable citation (repoint where verified, else attribute to withheld harness).
3. Edit MANUSCRIPT.md only → regenerate LaTeX via `python3 tools/package/md2tex.py --package encoder-crossover-190`.
4. Rebuild tarball with `tar --mtime=@0 --sort=name -cf - -C <dir> main.tex | gzip -n -9`, twice, prove
   byte-identity; report sizes + sha256.
5. Prove minimality of diff; report numeric-literal multiset delta exactly; confirm claim values unchanged
   (`0.6789`, `0.3474`, `0.4526`, `0.6684`, `4.167`, `0.33`, `0.32`, `152,000`; 13 `\bibitem` / 23 `\cite` /
   13 distinct / 0 uncited / 0 unresolved).
6. Tectonic compile (`scratch/utex1/bin/tectonic`, no `-Z continue-on-errors`): exit code, `Undefined
   control sequence` count, `!` count, page count. `PYTHONPATH=src pytest tests/test_md2tex.py -q`.
7. Report same class for papers #1/#2 — report only, no edits, no released artifact to point at.
8. Name downstream stale artifacts without rebuilding.

## Status
- [x] Card written (tool call 1)
- [x] Inventory (29 files; every shipping citation resolved + sized)
- [x] Verify 3 residual items — all three close: train-loss pair *does* ship at REPORT.md:151
      (prior 0-hit was a grep typo, `1.1287`); lint-report and DEFECT-EVIDENCE confirmed absent
      (DEFECT-EVIDENCE is NOT self-declaring — it only has note/passes/setfitIntermediates)
- [x] Edits (8 citation-only hunks) + md2tex (guard PASSED: 13/23/13/0/0)
- [x] Tarball ×2 byte-identical (28,536 B, sha256 0d470f7b…)
- [x] Minimality (diff = only the 8 hunks) + literal multiset 1152→1155 (+3: 151+2, 100+2, 107+1, 95−2)
- [x] Compile (exit 0, 0 undefined, 0 `!`, 25 pages) + pytest (`7 passed in 0.67s`)
- [x] Papers #1/#2 class reported, not edited (no released artifact for either)
- [x] Stale artifacts named, not rebuilt
- [x] Handoff written
