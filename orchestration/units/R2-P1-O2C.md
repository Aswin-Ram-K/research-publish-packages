# R2-P1-O2C — Round-2 prompt factorial, cell 2 (dense 9B, SGLang :8017)

Objective: 5 arms x 71 turns at 32768 = 355 rows on setup O2 (qwen3.5-9b NVFP4, SGLang,
page-size 64, extra_buffer), G0-gated, analysed, then production restored. Bound: 18 tool calls.

Reuse: `experiments/context-cache/cells/R2-P1-O2/prompt_r2p1o2_cell.py` (no third generator).
Arms R/A/C/H/C0 copied verbatim from PROMPT-O2-EXTRA + PROMPT-O4; renderer = VLLM-CELL/vllm_cell.py.

Result: 355 rows (71/arm), 345 with cached>0, 0 non-200, 10 `unavailable` first-turn rows (2/arm),
grid gcd 64. A -69.64 uncached tokens/turn vs R (95% CI -112.52..-26.75, excludes 0) → A cheaper.

Restore: `docker rm -f gx10-p-o2` (already absent) → :8017 000, :8012 200 occamy-1.0,
:8014 200 qwen3.5-9b; both production containers still Up.
