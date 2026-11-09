# LATENCY-REPORT-2 — re-derive the latency report on de-duplicated rows

**Automated, offline.** Zero inference requests, zero network. **Bound:** 28 tool calls.

## Why
`TVS-REGRADE` measured 30 defensible duplicate request rows (rule R: identical
`(ts, content_sha256, prompt_tokens, completion_tokens)` within one file, first kept), moving the
ledger 1,101 → 1,071. The same rows are the `n` behind every interval in
`measure/LATENCY-REPORT.json`, whose own hint names G7 V4-TOOLS (`pointer-stable`) as the cell that
reaches the p95 floor only by counting duplicates.

## Task (as carded)
1. Apply rule R per file; state `rule_status` (`decided` / `not_applicable`, the latter **not** deduped).
2. Re-run `analyze_stats.py` once per grid; report `n_raw`, `n_dedup`, p50 with interval+n, and p95
   with interval+n **or** the refusal text.
3. Enforce the floor (n ≥ 60); a p95 whose n falls under it is **refused by name** and the published
   value is marked **WITHDRAWN**, not replaced.
4. State what survives.
5. Do not re-derive tvs/quality/ledger — cite their owners.

## Write paths (exactly)
`experiments/ptr-engine/measure/LATENCY-REPORT.json`, `docs/LATENCY-REPORT.md`,
`experiments/ptr-engine/tools/latency_report.py`,
`experiments/ptr-engine/longrun/tests/test_latency_dedup.py`,
`orchestration/units/LATENCY-REPORT-2.md`, `orchestration/handoffs/LATENCY-REPORT-2.json`,
`orchestration/journals/LATENCY-REPORT-2.jsonl`.

## Result
G7 68 → **51** (p95 `318.14 [235.00, 526.40] n=68` **WITHDRAWN**, refused at n=51); G8 72 → **70**
(p95 397.41 [273.84, 659.70] n=70); G9 72 → **61** (p95 429.70 [318.80, 477.06] n=61). Cells with a
p95: **3 → 2**, both `pointer-stable`, intervals overlapping, `pairs_with_p95` unchanged at 0.
Rule status: 11 files `decided`, **3** legacy files `not_applicable` (brief said 5 — miscount, the 232
legacy rows reproduce exactly).
