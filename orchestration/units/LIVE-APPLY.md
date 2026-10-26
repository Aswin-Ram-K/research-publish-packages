# LIVE-APPLY
Purpose: append four adjudicated layers (C1, endpoint null semantics, C2, C5) to experiments/ptr-engine/RECORD.md from measured rows.
Bound: 20 tool calls. Append-only; sentinels preserved; revert from /tmp on any prefix change.
Evidence: orchestration/handoffs/LIVE-CELLS-2.json; experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl; RECORD.md.
Write paths: RECORD.md, orchestration/handoffs/LIVE-APPLY.json, this card.
Deliverables: 4 layers with per-number source; prefix sha before/after; sentinel counts; LIVE-APPLY.json.
