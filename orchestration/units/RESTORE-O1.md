# RESTORE-O1 — restore the PROMPT-O1 corpus, revert the repair figures, install a grid guard

Automated, offline, bound 18 tool calls. No live requests; GROUND-TRUTH-* and R2-P1-O1 untouched.

## Result
1. `rows.jsonl` restored from `rows.pre-correction.jsonl` (sha256 dc0774d8…, 355 rows, gcd 64, off-grid 0).
   Repaired corpus preserved as `rows.repaired-DO-NOT-USE.jsonl` (sha256 58c95fae…, gcd 1, 40 off-grid).
2. Withdrawn and rewritten: `PROMPT-O1/CORRECTION.md`, `PROMPT-O1/analysis.json` (+137.82 / R=391.48 removed),
   `state/logs/arms-parity.json` (publishable +133.3 marked WITHDRAWN, status key added), new `state/logs/RESTORE-O1.json`.
   No manuscript site existed: `grep -rn "137\.8" papers/ docs/` = 0 before and after.
3. Guard `assert_sglang_grid` in `papers/context-cache/recompute.py` (CLI `grid-invariant`): every declared-SGLang
   row's `cached_tokens` must be a multiple of 64 (0 allowed); evidence files matching repaired/DO-NOT-USE are exempt,
   and cells without an explicit `stack` are not asserted (rows() would back-fill them as SGLang and drag real vLLM
   cells such as R2-VLLM onto a grid that never applied to them).
4. Red→green proved by `papers/context-cache/grid_guard_selftest.py`.
5. R2-P1-O1: identical config_sha256/argv/page-size/mamba/budget/n to PROMPT-O1 → 390.80 is an unexplained
   outlier, not a config difference.
