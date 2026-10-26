# VERIFICATION REPORT 19 (UVER19) — in progress

Unit under verification: **UBIJ3** (coherent-bijection transform, `scratch/ubij3/tree-three-r2`).
Status: **IN PROGRESS** — started 2026-10-15-ish. Written early per unit instruction; updated as checks land.

Scope: re-run everything. Bound: 30 tool calls.
Invariant under test: *the text the model actually reads must not change.*

## Checklist
- [ ] measure.sh reproduces UBIJ3 numbers
> **Note 2026-10-16:** `scratch/ubij3/measure.sh` was removed by UPACK1 — it crashed on a `KeyError` (`m["routeB"]` where the key is `routeB_primary`) and read `second-labeller/cases.json`, which is not shipped. See `scratch/upack1/MEASURE_SH_REMOVAL.md`.
- [ ] census re-derived (own scanner or validated scanner)
- [ ] guard delta re-derived
- [ ] stimulus-only digest 26c5ddcb…
- [ ] RED→GREEN guard abort exit 3, no tree written
- [ ] tool exit codes in emitted tree
- [ ] metrics from stored labels
- [ ] digest moved/unmoved table
- [ ] packaging surface 309/240/187 + 44 files + 11 dirs + imajev 42
- [ ] K01..K10 = 3676 all trees, 0 inside
- [ ] ≥12 records model-facing text byte-identical
- [ ] MANIFEST.json counts.files 42 / missing verifier defect

(placeholder)
