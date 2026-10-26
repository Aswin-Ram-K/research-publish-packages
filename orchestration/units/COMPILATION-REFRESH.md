# UNIT COMPILATION-REFRESH

Purpose: make `papers/context-cache/COMPILATION.md` current with the four measurements that landed
after its 00:26Z generation, and teach the generator to discover the 2026-10-26 row files itself.

Bound: 20 tool calls (used exactly 20). Automated session: no questions asked, no requests sent.

## What changed
- `experiments/ptr-engine/tools/build_compilation.py`, still stdlib-only: globs
  `experiments/ptr-engine/measure/rows-*.jsonl`; indexes each file from its own rows (row count,
  unit, models, per model x cell x role cells, uncached sums, turn-reps, correctness, error rows);
  takes status from the file's `unit` field through a declared verdict table; rewrites two marker
  regions (`rows-index`, `rows-relations`). An unknown unit prints `NOT-PARSED <path>`, never a guess.
- `COMPILATION.md`: new generated section P; stamp extended to
  `ROWS | CLAIMS | READY | WITHDRAWN | ROWFILES | MEASURED | INVALID`.
- `COMPILATION-RELATIONS.md`: new generated section 8 (8.1 live, 8.2 equalinfo, 8.3 baseline, 8.4 non-relations).

## Verification
- `python3 experiments/ptr-engine/tools/build_compilation.py` -> exit 0, twice.
- Two consecutive runs: diff empty on both index files; stdout differs only in the
  rewritten/unchanged word. Idempotent.
- Counts unchanged for claim rows (ROWS 87 / CLAIMS 69 / READY 60 / WITHDRAWN 7: no claim row added);
  new row-file ledger: 3 files, 232 rows, MEASURED 2, INVALID-BY-DESIGN 1.
- `NOT-PARSED` survives for the same 7 JSON artefacts (U13, U14, M4-analysis, G1-analysis,
  E1-corpus, C1-corpus, V1-corpus).
- Derived figures reproduce the handoff numbers: equalinfo occamy C0F 1,911 vs R 3,524 uncached per
  turn-rep (1.844x); live cell A cached 320 / 58-77 uncached; cell B 260-256=4; cell C 6,336 = 6x1,056.

## Next
Citable claim rows for these cells need `CLAIMS.md`, outside this unit's write paths. `RECORD.md`
reads 169 lines with 0 occurrences of `BASELINE-COST`, so that layer is still unfoldable by an index.
