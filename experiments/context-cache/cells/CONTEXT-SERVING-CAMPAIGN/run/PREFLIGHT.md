# Preflight report — CONTEXT-SERVING-CAMPAIGN

## Preconditions
- ledger status --json: preflight remaining 48, total spent 2 (vLLM smoke) at start. Verified.
- Health: GET /v1/models -> occamy-1.0. GET /get_server_info model_path ends with pinned snapshot fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652. Verified.
- Endpoint healthy throughout; no ENDPOINT_UNHEALTHY.

## Envelope revision
- Re-froze run/envelopes/CAMPAIGN.json as revision 4 (supersedes revision 3 sha 3bf263845584d984af533f445256243842298ad55e60bc993f133c74da777db6).
- serving_flags diff rev3 -> rev4: added --enable-metrics, --enable-cache-report (measurement-enabling, not model change; rev3 predates restore).
- health_check output embedded (ok=true).
- limits.max_tokens=3200 (unchanged; no re-freeze for budget).

## Response shape and answer budget (D1 turn 1)
- finish_reason=stop; content non-empty ("\n\n-8\n</think>\n\n-8"); reasoning_content carries the trace (usage reasoning_tokens=296, completion_tokens=305).
- usage verbatim: {"prompt_tokens":153,"total_tokens":458,"completion_tokens":305,"prompt_tokens_details":null,"reasoning_tokens":296}; cached_tokens absent -> null.
- grade: failed (parseable=false; model emitted "-8" not "total=-8"). Budget not exhausted by reasoning (finish_reason=stop), so no max_tokens re-freeze. Calibrated on discovery only.

## Cache behaviour probes (run/preflight_probe.py)
| Probe | prompt_tokens | cached_tokens | completion | finish | ttft_ms |
|---|---|---|---|---|---|
| P1 COLD | 52 | null | 181 | stop | 5016.5 |
| P2 REPEAT 1 | 52 | null | 200 | stop | 5533.4 |
| P2 REPEAT 2 | 52 | null | 201 | stop | 5568.1 |
| P3 SALT DIVERGENCE | 50 | null | 206 | stop | 5740.7 |
| P4 FIRST-BYTE DIVERGENCE | 53 | null | 90 | stop | 2558.6 |

- P2 used 2 repetitions; both returned null cached_tokens (not >0). Cache economics UNPROVEN on per-request field.
- P3/P4 returned null cached (no hit) as expected for divergent prompts.

## Server-side cross-check
- Metrics names examined: sglang:cache_hit_rate (gauge), sglang:prefill_effective_tokens_total (counter by mode: input/device_hit/host_hit/storage_hit), sglang:uncached_prompt_tokens_histogram (count/sum/buckets).
- No sglang:cached_tokens_total or similar cached-token counter exists.
- Delta over P2 (2 repeats): prefill_effective_tokens_total input +104, device_hit +0, host_hit +0, storage_hit +0; uncached_prompt_tokens_histogram_count +2; cache_hit_rate 0.0.
- Per-request cached_tokens (null/absent) does NOT agree with a measured hit: server shows 0 device hits for the two repeat requests. cross_check: per-request field unreliable; server counter shows no reuse.

## First-row gate and supervision
- Watcher run for phase; alive before first send (run/watcher/preflight.jsonl).
- First-row audit: ok=true, mismatches=[]; compared envelope_path, max_tokens (3200), phase (preflight), model (occamy-1.0), engine_fingerprint (25f952a54628dc5ffa29d0c7b57df6d801609709a3aaa6ec8a9eb06e6aceba69), seed (1101).
- Ledger attempts-count == 1 at first-row instant (before second request). Row carries salt (csc-CONTEXT-SERVING-2026-11-05-D1-1101); cached_tokens null stayed null (no real zero observed in preflight data).

## Reconciliation
- intents (6) == rows (6) + recorded failures (0). Spent counter (6) agrees with journal recount.
- Attempt ids: 975f3d92-e740-4e80-af14-6f1c40e9e9b7 (D1), 5bfceb7b-2d8d-4266-823a-e809d9fa93c4 (P1), bd5b13bc-1442-4efe-a398-681bd0c9126a (P2r1), 111fa6f8-93c0-4943-a930-27f6b585ebbc (P2r2), 78e03caf-1b93-460f-85cf-c3dad110127a (P3), 06348fb9-5d99-49d4-a27e-144a955a9509 (P4).
- journal.jsonl preflight phase: 0 synthetic labels.

## Budget
- Preflight spent 6 / 48. Total spent 8 / 1500.

## Test suite
- python3 -m pytest tests/ -q -> 45 passed in 2.97s.

## Verdict
CACHE_FIELDS_UNRELIABLE — per-request cached_tokens is absent (null) for all preflight requests and SGLang server-side metrics show 0 device cache hits even on byte-identical repeats; cache economics cannot be claimed. Endpoint healthy.
