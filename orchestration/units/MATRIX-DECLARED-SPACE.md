# UNIT MATRIX-DECLARED-SPACE

**Purpose.** MATRIX-HONESTY claimed a "declared cell space" of 92 cells, but harvested the arm
axis from the rows themselves (`tools/matrix_audit.py:122`), so a fabricated arm — and a row
carrying `cp.99.t99` — was admitted as declared. This unit moves the population onto artefacts
that are not the rows and adds a fifth state, `extraneous_cell` (exit 11).

**Hard bound.** ≤28 tool calls, zero inference requests, no network, no `git`.

**Write paths (exactly).**
`experiments/ptr-engine/tools/matrix_audit.py` (card said `longrun/matrix_audit.py`; the module
lives in `tools/`, which is what the verifier's `:122` line citation points at),
`experiments/ptr-engine/longrun/tests/test_matrix_audit.py`,
`docs/MATRIX-DECLARED-SPACE.md`, `experiments/ptr-engine/measure/MATRIX-HONESTY.json`,
`orchestration/units/MATRIX-DECLARED-SPACE.md`,
`orchestration/handoffs/MATRIX-DECLARED-SPACE.json`,
`orchestration/journals/MATRIX-DECLARED-SPACE.jsonl`.

**Read-only.** every row file, every grade file, every fixture; `grade_v5.py`,
`cell.py`, `run_longrun.py`, `client.py`, `analyze_stats.py`, `fixture_coverage.py`,
`handoff_lint.py`, `det_verify.py`, `frozen_tree.py` untouched.

**Declared space.** arms: `run_longrun.py:64` `ARMS` + `:862` refusal, and the run-manifest
`arm`/`rows_path` pairing (`manifests/*.json`); checkpoints: `fixtures/LR-01.json:283`
(`checkpoints`) and `:303` (`repair`); rep: 1 per the fixture's single-run contract.

**Result.** `extraneous_cell` 0 on the real corpus (92 pairs, 9 batches); before/after figures
identical 5 / 38 / 29 / 7 / 13 = 92, overall 5/43 = 11.6 %; exit 0 clean, **11** non-clean,
1 `--strict`; 17 tests pass.
