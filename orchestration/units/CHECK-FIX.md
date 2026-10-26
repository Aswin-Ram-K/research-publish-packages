# CHECK-FIX — make `best_config_build.py --check` compare DERIVED fields only

**Bound:** 15 tool calls. **Live requests:** zero (checker + test only, no GX10, no curl).

## Problem
`--check` compared whole setup entries for dict equality:
`tools/best_config_build.py:341` — `same = json.loads(cur)["setups"] == doc["setups"]`.
A sibling card backfilled `unc_ci` / `ci_source` / `ci_arm` / `ci_note` (and `evidence.ci_method`,
`evidence.ci_rows_selector`) into O1/O2/O4. Those are MEASURED, not functions of argv, so the
rebuilder can never reproduce them → permanent `False`, exit 1 on the project's highest-value
acceptance command.

## Change
- `DERIVED = {model, engine, engine_version, argv, config_id, config_sha256, rows_sha256, unc_naive_history}`
- `MEASURED = {hit, unc_per_turn, unc_ci, ci_source, ci_arm, ci_note, n_rows, evidence, optimised_from, grid_unit, status, reason, tried, grid_unit_meaning, resolved_block_size, resolved_block_size_source, endpoint_seen, headline_arm, note_grid}`
- `compare()` walks DERIVED only, prints `SKIPPED measured fields (not compared): ...`, and for any
  key in neither set prints `WARN <setup>.<key>`. New `--strict` turns that warning into a failure
  (`STRICT: unknown key(s) present -> FAIL`). New `--config <path>` lets tests diff a `/tmp` copy.
- `grid_unit` is listed in both sets by the brief; it is a gcd of observed rows, so MEASURED wins —
  recorded explicitly as `GRID_IS_MEASURED`.

## Evidence (red -> green)
| case | output | exit |
|---|---|---|
| real file | `CHECK setups identical to disk: True` | 0 |
| real file `--strict` | `True` | 0 |
| RED sha256 | `FAIL O1.config_sha256: built='f2efaaac…' disk='0000…'` → False | 1 |
| RED argv | `FAIL O1.argv: … disk=['sglang','serve','--port','9999']` → False | 1 |
| GREEN restore | `True` | 0 |
| bogus key, non-strict | `WARN O1.invented` + `True` | 0 |
| bogus key, `--strict` | `WARN O1.invented` + `STRICT … FAIL` + `False` | 1 |
| `pytest tests/test_best_config_check.py -q` | `7 passed` | 0 |

`state/config/best-config.json` was NOT edited; `unc_ci`/`ci_source` stay.
