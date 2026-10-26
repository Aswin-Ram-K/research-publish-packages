# Unit MTP-CORRECTION

**Status:** done. **Bound:** 20 tool calls.

## Purpose
The Round-1 vLLM cell behind claim C63 ran with `--speculative-config mtp`, but neither
`MANUSCRIPT.md` nor `CLAIMS.md` ever said so (grep: 0 hits). Round 2 re-measured the cell with
MTP removed: 2,230.7782 -> 879.0669 uncached tokens/turn (2.5375x, CI [824.7806, 933.3532]).
C63's engine and model effects were therefore computed on a contaminated cell.

## What changed
1. `recompute.py` — `c63()` rebound to the Round-2 cell (`R2-VLLM-CELL` / `O4` in
   `state/config/rows.jsonl`, stack `vllm-0.27.1`). Added `C63_R2_CELLS`, `C63_R2_STACK`,
   `C63_GCD_OVERRIDE` ({("qwen3.5-9b","vllm"): 1088}), field normalisation in
   `_c63_cell_rows`, prompt-identity contrast restricted to the three Round-1 cells, and
   `C63_SUPERSEDED` carrying the old figures for audit. `EXPECTED["C63"]` re-pinned (43/43).
2. `CLAIMS.md` — C63 rewritten with the corrected figures AND the disclosure in the same
   claim text; superseded values listed beside their replacements.
3. `MANUSCRIPT.md` — abstract paragraph, results table, "engine is the lever", "model effect is
   engine-conditional", "what this licenses", plus a new **MTP is part of this finding**
   paragraph.
4. `SERVING-BRIEF.md`, `docs/serving-options/MATRIX-2x2.md`, `EVIDENCE.md` — same treatment;
   `state/serving-brief.json` ledger S04 relabelled to `R2-VLLM-CELL`.
5. `RUN.json` — `mtp_correction` block with both `superseded` and `corrected`; nothing deleted.
6. Tests — `test_paper_matrix_fold.py` (missing-cell name), `test_c63_ratio_raw_operands.py`
   (independent constants 152.0/548.06 -> -222.8887/-803.65).

## Verification
`recompute.py all` -> 60 claims checked, all match; COVERAGE GUARD PASS 63 claims.
`pytest test_paper_attribution_guard.py test_claims_decompose.py -q` -> 31 passed.
Red->green: pin reverted to 1225.18 -> FAIL 42/43, exit 1; restored -> PASS 43/43, exit 0.
`grep -c mtp` -> 1 in each of CLAIMS.md and MANUSCRIPT.md.
