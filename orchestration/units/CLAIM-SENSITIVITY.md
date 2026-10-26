# CLAIM-SENSITIVITY — do the 13 BLOCKED claims move when the flagged rows are repaired?

**Bound:** 20 tool calls. **Writes:** the four paths in the handoff. **Live requests:** 0 (no GX10, no endpoint, no model lock).

## Objective
For each of C17-C24, C44, C46, C47, C50, C51 recompute the published statistic three ways from the same
`rows.jsonl` — as published, flagged rows excluded, flagged rows repaired — and decide SURVIVES / MOVES /
UNDECIDABLE against a rule stated before the numbers.

## Method
1. Flags from `tools/audit/cached_dedupe.py` (`_arm_results`, whole-file per-arm grouping) — reproduced the
   CLAIM-HEALTH fire counts exactly (U15 7/2/2/1 of 40; G1 13/1 of 132; G3 8/7/7/7 of 222; WIN-SGL 6/5/4/4
   of 444; WIN-VLLM 14/142 per arm).
2. `papers/context-cache/recompute.py` called **unchanged**, only `rows()` monkey-patched to serve the
   variant row lists, so every formula is the published one. C44 recomputed from rows with its
   `analysis.json` definition (`cost_gross = uncached - (prompt % 64)`).
3. Repair: stale credit means the fired row records the previous turn's cache state, so copying that value is
   a no-op (verified). Determinate repair: `cached := prompt_tokens - baseline_gap_p25(arm)`.

## Result
SURVIVES 1 (C44) / MOVES 12 / UNDECIDABLE 0. Worst-case shift: C22 break share 0.0785 -> 0.1006 (+28.15 %).
All 12 MOVES point the same way — credit was over-stated, so published `hit` is low and published `uncached`
is high. Full table: `papers/context-cache/CLAIM-SENSITIVITY.md`; machine copy: `state/logs/claim-sensitivity.json`.
