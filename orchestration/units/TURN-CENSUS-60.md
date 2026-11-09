# UNIT TURN-CENSUS-60

**Purpose.** Decide, by measurement, whether any existing cell in this corpus holds ≥60 completed
turns for an arm, i.e. whether any per-cell p95 can ever be published under the current analyser.

**Bound.** 16 tool calls. Offline: 0 network requests, 0 inference requests. Never ask_user_question.
No edits to any rows file, grade document, analyser, threshold or published page.

**Write paths.** `experiments/ptr-engine/measure/TURN-CENSUS.json`, `docs/TURN-CENSUS.md`,
`orchestration/units/TURN-CENSUS-60.md`, `orchestration/handoffs/TURN-CENSUS-60.json`,
`orchestration/journals/TURN-CENSUS-60.jsonl`.

**Method.** For every `measure/rows-*.jsonl`, pass the file through `analyze_stats.turn_latency_rows`
(the real selector: `kind="turn-initial"`, legacy `kind="turn"` as marked fallback, follow-ups
dropped), group the selected rows by arm, and count turns / usable turns (`stop_reason != "length"`)
/ non-null `ttft_ms` / excluded-length. Floor read from `analyze_stats.min_n_for(0.95)`.

**Result.** 1,128 raw rows → 915 turns. Max usable per cell/arm = **48**. Cells ≥60 = **0**.
Corpus can publish **no** per-cell p95; the only admissible p95 is pooled R-all at n=144.

**Deliverables.** [`TURN-CENSUS.json`](../../experiments/ptr-engine/measure/TURN-CENSUS.json),
[`TURN-CENSUS.md`](../../docs/TURN-CENSUS.md),
[`handoff`](../handoffs/TURN-CENSUS-60.json).
