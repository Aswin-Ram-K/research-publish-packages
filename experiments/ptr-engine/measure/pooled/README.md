# measure/pooled/ -- DERIVED artefacts only, never a measurement

`experiments/ptr-engine/tools/pool_reps.py` writes here:
`pooled-<arm>-<stamp>.jsonl` + `pooled-<arm>-<stamp>.json`.

Rules that make this directory safe:

1. **Derived, not measured.** Every row carries `derived: true`,
   `purpose: "H1 pooled R-all"`, `pooled_arm`, `source_path`, `source_sha256`,
   `source_rep`; the manifest carries `derived: true` and the pooling rule in words.
2. **Never a cell.** No file here is named `rows-*` or `rows-cell-*`. The repo's analysis
   globs are `measure/rows-*.jsonl` (request_ledger, build_compilation, p95_power_gen,
   longrun/tests/test_verbosity), so a `pooled-*` name cannot be swept in by them.
3. **Outside the flat glob.** `glob("measure/*.jsonl")` does not recurse into `pooled/`,
   so no incidental sweep over the flat directory sees these files.
4. **Explicit read only.** `analyze_stats.py --rows <pooled file>` refuses with
   `refused: ... is a DERIVED artefact ...` unless `--pooled` is also passed.

No pooled artefact exists in this directory yet: tranche 1 has not run. The unit's
proof-of-payoff used synthetic reps under `/tmp/pooldemo` precisely so that a
demonstration pool is never mistaken for a grid cell.
