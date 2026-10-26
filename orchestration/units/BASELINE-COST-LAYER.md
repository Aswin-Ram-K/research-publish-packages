# BASELINE-COST-LAYER

Automated session, no human present, zero requests sent. Bound 16 tool calls (used 12).
Write paths: `experiments/ptr-engine/RECORD.md`, this card, `orchestration/handoffs/BASELINE-COST-LAYER.json`.

## Objective
Append one layer to RECORD.md recording the equal-information baseline: the first measurement where the pointer protocol LOSES on cost.

## Evidence read (nothing else)
- `orchestration/handoffs/C0-EQUALINFO.json`
- `experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl` (100 rows)
- `experiments/ptr-engine/RECORD.md` (append target)
- `orchestration/handoffs/C0-BASELINE.json` (solely to verify the prior-defect clause)

## Procedure
1. Stub both deliverables before any read of the target.
2. `cp experiments/ptr-engine/RECORD.md /tmp/bcl/RECORD.md.bak` (rollback path).
3. Re-derive every card number from the rows with an independent script; trust the rows, not the handoff.
4. Append after the last line; assert `head -n 159 | sha256sum` unchanged, byte-prefix identical, all 12 sentinel occurrence counts unchanged.
5. Record row-wins contradictions; never edit an existing line.

## Result
159 -> 169 lines. Prefix sha before and after: `bb1895d1...53392` (identical). Sentinels 16 -> 16 occurrences.
Contradictions: vLLM nulls 45/45 (card) vs **52/52** (rows); C0F rep2/3 28 vs 28.5 and C0FT 47 vs 46.7 (half-token rounding); "3/3 every arm" holds for occamy only; R TTFT 0.602 includes the cold rep (0.751 without); `fac350e6` absent from disk.

## Rollback
`cp /tmp/bcl/RECORD.md.bak experiments/ptr-engine/RECORD.md`
