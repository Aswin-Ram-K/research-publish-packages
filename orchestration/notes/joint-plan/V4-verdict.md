# V4 Independent Verification Verdict

**Unit:** V4-VERIFY · **Date:** 2026-11-07 · **Target:** `experiments/ptr-engine/research-seed-concepts/JOINT-SERVING-CONTEXT-PLAN.md` §9.1.1 + `experiments/ptr-engine/measure/rows-*.jsonl` · **Overall:** `pass`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Rows exist and parse (exactly 5) | PASS | Extracted the single fenced ```json``` block under §9.1.1; `json.loads` succeeded; 5 row objects. |
| 2 | Required content of a valid row | PASS | Row 1 (`run-2026-11-07-D-LR05-60-rep2-turn41`): dims `arm`="D", `stack`="SGLang-occamy-1.0-memfrac0.45-fp8", `task_id`="LR-05"; ids `call_id`/`run_id`+`task_id`; quality `verified_success`+`exit_cause`/`retrieval_miss`/`abstained_correctly`/`tokens_to_verified_success`; cache `cached_tokens`=38640 (null-capable). |
| 3 | Both null branches shown | PASS | Unknown branch: A row `cached_tokens`=null, `null_semantics`="endpoint :8014 -> null = unknown", `uncached`=null, basis "not derived (cached unknown)". Measured branch: D row `cached_tokens`=38640, `uncached`=2610, basis "derived = prompt - cached". No null written as 0; `uncached` carries `uncached_basis`. |
| 4 | Invalid row retained | PASS | Row 4 (`run-2026-11-07-D-LR05-60-rep3-turn09`): `instrument_status`="INVALID-INSTRUMENT", `exclusion_reason`="activation predicate failed: fetch_rows = 0 for arm D on this cell (treatment never fired)"; measurement fields null (not 0). |
| 5 | Missing cell retained | PASS | Row 5: `task_id`="LR-01", `horizon`=60, `instrument_status`="UNAVAILABLE", `exclusion_reason`="fixture LR-01 supplies 48 turns; 60-turn horizon unavailable — not imputed"; all measurements null. |
| 6 | Non-citability | PASS | Heading reads "Illustrative result rows (shape examples — no measurement, not evidence)"; closing sentence states rows are "illustrative shapes carrying no measured value and are never citable as results." |
| 7 | No collateral change | PASS | §7 fenced JSON still parses as 20 objects (L0–L19); figures present: core `12,094.2`, with candidates `13,020.2`. §9.1.1 span lines 281–512 (232 lines) accounts for the 321→554 growth (233 lines) within one trailing-newline line. |
| 8 | Non-perturbation (correct evidence) | PASS | `rows-*.jsonl`: 41 files, 2,591 rows, latest `ts`=2026-10-28T03:35:42.114Z, newest file mtime 2026-10-27 22:35:42 UTC. No new row, no later timestamp, no rows-file mtime after that date. Under `experiments/` and `docs/`, only the plan doc has mtime today (2026-11-07 16:24). |
| 9 | Red→green guard | PASS | `/tmp` copy with `exclusion_reason` deleted → check 4 fails ("no invalid instrument row"). Separate copy with `stack` removed from row 1 → check 2 fails ("missing dim stack"). Both restored/removed. |

## Defects found

None. All nine checks reproduce.

## Conclusion

`pass`: §9.1.1 contains five illustrative, non-citable rows meeting the required content, null, invalid-row and missing-cell rules; §7 unchanged at 20 objects with figures intact; row store untouched (2,591 rows, last ts 2026-10-28T03:35:42.114Z).
