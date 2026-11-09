# UNIT LIVE-SMOKE-CELL

**Purpose.** Prove the rebuilt `cell.py` pipeline end-to-end (preflight -> harness digest -> budget -> run -> `grade_v5` -> `analyze_stats` -> record) with one cheap 48-turn cell. Smoke test of the harness, not a result.
**Bound.** <=18 tool calls, <=130 requests, 2 live attempts max. No harness file edited.

## Environment
`GET http://192.168.2.168:8012/v1/models` -> **HTTP 200 in 0.005398s**, `data[0].id=occamy-1.0`, `max_model_len=131072` (card said `occamy-1.0-NVFP4`; the served id differs, endpoint served fine).
Harness digest (stage 2): `231b0ae11477e85c9e27886d82ea0896138abde7891617584a5a04aee97342d8`, files `analyze_stats.py, client.py, fixture, grade_v5.py, run_longrun.py, tools/det_verify.py`.

## STAGE 1 - offline rehearsal (0 requests) - PASS, exit 0
`cell.py --offline experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl --arm pointer-stable --fixture .../LR-01.v5.json --budget 0`
Record: `experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.{json,md}`

```
arm pointer-stable  (rows n=72)
  ttft_p50 n=72  158.19ms [146.19, 200.61]  (ttft dropped: 0 null, 0 unavailable)
  ttft_p95 n=72  435.27ms [346.51, 529.89]
  accuracy  UNDECIDABLE (n=0 decidable turns; 72 rows carry no decidable outcome)
```
Refusal printed: `arm pointer-stable accuracy: no decidable turns (n=0)`. Grade line: `acc=1/3 decidable=3 text=0 verified=False`.

**The card's p95 premise did not hold.** The expected "explicit p95 refusal because <60 usable timings" did not occur, correctly: the rows yield **n=72 usable timings**, and `analyze_stats.py:223` refuses only when `n < MIN_N or n*(1-q) < TAIL_MIN` - for p95 that is `n*0.05 < 3`, i.e. **n < 60**. At n=72 a p95 is admissible by the module's own rule (`analyze_stats.py:28-29`: "48*0.05 = 2.4 < 3 ... first admissible p95 at n=60"). Printing it is compliance, not a conductor defect. The refusal that *was* exercised is the accuracy refusal.

**Reported inconsistency (not patched):** the grader reports `decidable=3` while the analyser reports `n=0 decidable turns` over the same rows - two decidability accounts disagree.

## STAGE 2 - live cell - PARTIAL at 6/48 turns
`cell.py --arm pointer-stable --fixture .../LR-01.v5.json --turns 48 --reps 1 --budget 130 --endpoint http://192.168.2.168:8012/v1`
Rows: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl` (6 rows). **Requests spent 6/130.** No cell record: the conductor never reached stage 5, so no live `cell-*.json` exists.

| turn | ttft_ms (source) | first_token_kind | cached_tokens (source) | wall_ms | prompt/comp tokens |
|---|---|---|---|---|---|
| 1 | 631.764 (first_delta) | reasoning | None | 218187.3 | 3101 / 7771 |
| 2 | 675.56 (first_delta) | reasoning | 256 (prompt_tokens_details) | 40056.7 | 3880 / 1415 |
| 3 | 399.599 (first_delta) | reasoning | 3008 (prompt_tokens_details) | 24110.3 | 4323 / 856 |
| 4 | 198.35 (first_delta) | reasoning | 3776 (prompt_tokens_details) | 7803.7 | 4346 / 275 |
| 5 | 198.434 (first_delta) | reasoning | 3776 (prompt_tokens_details) | 475873.3 | 4326 / **16384** |
| 6 | 138.249 (first_delta) | reasoning | 4160 (prompt_tokens_details) | 379528.3 | 4312 / **13126** |

Mean turn wall **191s**. Turns 5-6 ran to the **16384 completion-token cap** (reasoning is unbounded up to the cap), which is why a "cheap" smoke cell projects to ~2.5-5h for 48 turns. The unit stopped the job at T6 rather than hold the cell lock for hours.

## STAGE 3 - row fields
- `ttft_ms` present with `ttft_source=first_delta` on all 6 rows, and **never equal to `wall_ms`** on any multi-second turn -> the old fallback is not back.
- `first_token_kind=reasoning` on all 6; **no turn began with a tool call**, so no `tool_call` value exists yet (none should).
- `cached_tokens` + `cached_source=prompt_tokens_details` from turn 2 (SGLang), `metrics_scrape` populated on every row, `engine_metrics_before/after` present.
- **`answer_kind` on a checkpoint turn: UNVERIFIED** - the first checkpoint is T12 and the cell stopped at T6. This is the material gap of this unit; offline rows did exercise the grader/analyser instead.

## Verdict
Transport/plumbing is trustworthy: TTFT provenance, cached-token provenance, engine metrics, and the record path all work, and the analyser refuses rather than inventing numbers. What is *not* yet proven live is checkpoint answer capture plus a live grade/analyse/record cycle. Recommended next cell: `--turns 12` with a reasoning/max-token cap.
