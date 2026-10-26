# FIX-O2-CONFIG

**Purpose:** repoint `state/config/best-config.json → setups.O2` at the real cell
`experiments/context-cache/cells/PROMPT-O2-EXTRA/` (355 rows, 5 arms x 71 turns) instead of
`cells/PROMPT-O2/` (page 1 + no_buffer, the negative control).

**Write paths:** `state/config/best-config.json`, `orchestration/handoffs/FIX-O2-CONFIG.json`, this card.

**Bound:** 10 tool calls. **Done** in 7.

## What was written

- argv: `--page-size 64 --mamba-radix-cache-strategy extra_buffer --max-mamba-cache-size 40
  --mem-fraction-static 0.22 --context-length 32768 --quantization modelopt_fp4 --dtype bfloat16`
  (`--disable-overlap-schedule` dropped — it belongs to the superseded no_buffer launch).
- `config_sha256` 652ff99db16fb7fc90e2649955bf74dbcda4586ee1e13704290cf2b0bc9ab510 (recomputed by `canonical_argv_sha`).
- `hit` 0.9513323861430014, `unc_per_turn` 600.169014084507, `unc_ci` [558.8505379259276, 641.4874902430864] — arm R.
- `grid_unit` 64 (inferred: 64-token state chunk; no EXTRA startup log in the workspace).
- `n_rows` 355, `evidence.rows` / `evidence.analysis` -> the EXTRA cell, `per_arm` for all five arms.
- O1, O3, O4 untouched.

## Finding outside scope

`tools/best_config_build.py` still *builds* O2 from `cells/PROMPT-O2/rows.jsonl` (page 1 + no_buffer), so
`--check` keeps failing on `O2.rows_sha256` plus `O2.argv`/`O2.config_sha256`/`O2.engine_version`/
`unc_naive_history`. The builder is a source file the card forbids writing — a separate unit must repoint it.
