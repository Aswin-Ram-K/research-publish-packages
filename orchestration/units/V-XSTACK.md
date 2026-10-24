# V-XSTACK — cross-stack cell verification

**Unit:** V-XSTACK (verifier) · **Batch:** cross-stack · **Author of none of the checked cells**
**Date (UTC):** 2026-10-23 · **Bound:** 40 tool calls / ≤8 network calls, no engine restarts, no model requests
**Status:** done — verdict **fail**

## Objective

Re-check the three delivered cross-stack cells — WIN-SGL (S1 warm_retry_empty_sleep / S2
warm_retry_empty_sleep_universal), WIN-VLLM (V1/V2/V3 pager+flag space), TUNED (production /tune) — on
six checks: declared law vs rows, measured granularity vs launched config, claims vs delivered rows,
identity schema, launch-config pre/post match through restore, and G0-before-battery.

## Checks run (all offline except two permitted GETs)

1. Re-derived every grid/law from `experiments/context-cache/cells/*/rows.jsonl` (sha256 checked against
   the handoffs' `rows_sha256`): SGLang gcd 64/128/64, vLLM gcd 1088/1056/2096, TUNED replay law 64.
2. Recomputed the headline numbers: 351/880 odd multiples of 64, 0.6011 multiple-of-128 fraction, 729.2 /
   746.0 / 725.7 mean-uncached, vLLM 20/20 · 11/11 · 5/5, TUNED 10/30 exact replay.
3. Flipped every delivered claim line by line against the rows (claims.py): all reproduce except the
   TUNED page_size claim.
4. Diffed `tuned-pre.json` vs `tuned-restored.json` (481 keys) and read the V1/V2/V3 restore records.
5. G0: grepped the cell code for gates; found none in SGL/TUNED; located the only SGLang G0 (`u2_gate.py`,
   mtime 2026-10-20 18:05) and the in-cell vLLM gate.
6. Identity schema red→green: one battery row stripped of `stack`/`config_id` in a scratch copy; the
   shipped analyzer accepts it (exit 0) and silently drops it from the config bucket.

## Evidence (verbatim key lines)

- `S1 g=64 battery exact 6/888, max|res| 1408; warm probe 8/8 exact` — `scratch/vxstack/out_grid2.txt`
- `V1 gcd 1088=136*16 / D/8; law 20/20 rep1 (clamp max(0,…) load-bearing); battery 122/284 exact, 161 at −1088`
- `TUNED replay g=64: 10/30 exact, 19 rows cached=0, max|res| 8641; 289/289 rows stack=None config_id=None`
- `tuned-pre vs tuned-restored: 477/481 keys identical; 4 differ only (max_total_num_tokens 1620892→1440049, random_seed, internal_states, startup_time)`
- `red: exit 0, S1 900→899, n_rows_total still 1800; green: exit 0, analysis identical to committed`
- `GET :8012/health 200, /v1/models occamy-1.0 max_model_len 131072`

## Red→green (guard under test)

`win_sgl_analyze.py` as shipped: delete `stack`+`config_id` from one S1 battery row → **no rejection**
(exit 0); the row is dropped from S1's bucket (900→899, n_battery 888→887, n_steady 880→879, grid verdict
changes) while `n_rows_total` still counts 1800. Restore the row → analysis reproduces the committed
`analysis.json` exactly. The guard that should reject an unattributable row does not exist.

## Verdict

**fail** — TUNED claims `page_size 1 / no-grid` while its own delivered replay rows match the G3 64-token
law (10/30 exact, 19 evicted-to-0); its 289 replay rows also lack `stack`/`config_id` and the analyzer
accepts them silently. S1/S2/TUNED have no in-cell G0; the only SGLang gate (2026-10-20 18:05) predates
their protocol and the box has restarted repeatedly since. Launch restore is clean; all other numbers
reproduce. Full report: [`orchestration/handoffs/V-XSTACK.json`](../handoffs/V-XSTACK.json).
