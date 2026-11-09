# ENDPOINT-STATE — serving stack as of 2026-10-26T17:00:47+00:00

**Verdict: `warm`.** Sampled live at 2026-10-26T17:00:47+00:00 against the grid's endpoint `http://192.168.2.168:8012/v1` (model `occamy-1.0`, SGLang). Two billed requests, cap three.

## Who is serving what

| | `:8012` (grid endpoint) | `:8014` |
|---|---|---|
| `/v1/models` | HTTP 200 — id `occamy-1.0`, max_model_len 131072, owned_by `sglang` | HTTP 200 — id `qwen3.5-9b`, max_model_len 32768, owned_by `vllm` |
| `/health` | HTTP 200, 0-byte body | HTTP 200, 0-byte body |
| `/metrics` | HTTP 200, 79271 bytes | HTTP 200, 57390 bytes |
| start evidence | no `process_start_time_seconds`, **no absolute start time exposed** | `process_start_time_seconds` = `1792838668.5` → 2026-10-24T10:44:28+00:00, age **54.27 h** |
| cumulative since process start | **4,649 requests** (3,717 non-stream + 932 streaming after the pair, 4,647 before), 24,438,211 cumulative prefill tokens, 849,396 streaming generated tokens, 946 streaming TTFT observations | prefix-cache hits 4,114,176 tokens |

`:8012` exposes no uptime gauge, so warmth is inferred from counters a restart would have zeroed: 4649 requests and ~24.4 M prefill tokens of history are still accumulated, and the TTFT histogram holds 946 streaming observations (p50 ≈ 0.159 s, p95 ≈ 0.696 s). The process is the one that served the campaign, not a fresh one.

## The warm-up pair (`/v1/completions`, stream, `max_tokens` 8, temperature 0, 5-token prompt)

| req | TTFT ms | total ms | prompt tok | completion tok | cached tok |
|---|---|---|---|---|---|
| 1 (first touch) | 149.8 | 343.6 | 5 | 8 | not reported |
| 2 (identical repeat) | 99.3 | 258.1 | 5 | 8 | not reported |

Same text out (`" Paris, a city renowned for its iconic"`), so the comparison is like-for-like. The repeat is **50.5 ms faster (−34 %)** — a first-touch penalty of exactly the size a warm-up absorbs, not a cold start.

Cache credit: `usage` on `:8012` carries no `cached_tokens` field at all. Aggregate credit **is** live: `sglang:cached_tokens_total{cache_source="device"}` = **18,626,432** credited tokens against ~24,438,211 cumulative prefill tokens (**76.2 %**), with `sglang:kv_cache_memory_usage_gb` = **14.44 GB resident** — the radix cache is populated, not flushed by a restart. `sglang:cache_hit_rate` is a per-last-request **gauge** that reads 0.0 when idle, so it is not the credit signal.

Per-request credit for the repeat is **not** observable: `usage` carries no `cached_tokens` field and the pair was not bracketed by a `cached_tokens_total` baseline, and streaming `sglang:prompt_tokens_total` moved by exactly +10 over the two 5-token prompts, which does not distinguish cached from processed tokens. So the "repeat prefix credited" leg of `warm` is satisfied **in aggregate**, not per request — the verdict does not rest on that leg alone.

### Correction (2026-10-26, after CACHE-CREDIT-CHAT)

The paragraph above stands as what was measured — and the reading it implies, that per-request credit cannot be had on `:8012`, is **wrong**, on the endpoint rather than on the engine. A later probe, `measure/CACHE-CREDIT-CHAT.json` (unit `CACHE-CREDIT-CHAT`, `requests_used: 2`, sampled at 2026-10-26T17:04:37Z — the same hour as this document), sent two byte-identical 2,106-token prompts to the runner's own **`POST /v1/chat/completions`** (`max_tokens` 4, `temperature` 0) and observed credit directly: **request 2 returned `usage.prompt_tokens_details.cached_tokens = 2048`** (request 1 returned `prompt_tokens_details: null`), and the cumulative **`sglang:cached_tokens_total` delta was exactly 2048** over that request while request 1's delta was 0 and its `sglang:uncached_prompt_tokens_histogram_sum` delta was exactly 2106. So per-request credit **is** observable on `:8012`, through `/v1/chat/completions`'s `prompt_tokens_details.cached_tokens` and, corroborating it, as a `sglang:cached_tokens_total` delta. It is **not** observable through `/v1/completions`' usage object, which carries `prompt_tokens` / `completion_tokens` / `total_tokens` / `reasoning_tokens` and no `prompt_tokens_details` — and `/v1/completions` is what the original probe (and the warm-up pair above) read. The cost of the proof was **2 requests of the 4 allowed**; the streamed pair was never spent, because the non-stream pair already showed credit (`stream_skipped_because`). The previously published cached share recomputes exactly from `measure/TVS.json`'s own definition `sum(cached_tokens)/sum(prompt_tokens)` over rows whose `cached_tokens` is non-null: **93,568 / 109,780 = 0.852323** (`matches_published_0_8523: true`). The runner already speaks that endpoint and that field: `longrun/client.py:661` posts `/chat/completions`, `client.py:604-613` reads `usage.prompt_tokens_details.cached_tokens`, `client.py:339-340` sets `stream_options={'include_usage': True}` when streaming, and `run_longrun.py:1760-1762` writes row keys `prompt_tokens` / `cached_tokens` / `uncached_tokens` (`uncached = prompt − cached`, `None` when either is `None`). Evidence: `experiments/ptr-engine/measure/CACHE-CREDIT-CHAT.json` against `experiments/ptr-engine/measure/ENDPOINT-STATE.json`.

**Consequence for the programme:** H2's cache-inclusive limb **is** measurable on the frozen runner as it stands, so no harness change is needed for H2 and no card may decline to report the cached share on the grounds that the endpoint cannot supply it.

## What this means for the 792-request grid

no cold-start contamination expected: spend one throwaway 8-token warm-up request per arm before cell 1 is recorded (1 of 792), and discard nothing else; the first-touch penalty measured here is ~50 ms on a 5-token prompt (34% relative), which is exactly the size that a per-arm warm-up absorbs.

## Two traps recorded

1. **`/v1/models` `created` is not a start time.** `created` advanced 1793033947 → 1793034047 between two `/v1/models` calls ~100 s apart, while `:8014` has provably been up 54.27 h (`process_start_time_seconds`). Never read `created` as uptime — it is stamped at listing/request time.
2. **`/health` was HTTP 200 / 0 bytes today on both ports**, so the earlier `000`/no-body observation is not reproducible now, and `/health` alone still would not be evidence either way. `/v1/models` remains the authority.

## Cost

- Billed inference requests: **2 of 3** (pair only; no third, because the second request showed no different prompt-token treatment).
- Ledger: `spent=1101`, `remaining=3219` of `cap=4320`, **before and after** — the ledger counts rows under `experiments/ptr-engine/measure/rows-*.jsonl`, and this unit wrote no rows; the 2 requests above are outside it and are reported here.

Git HEAD at write time: `f17663d1fed0162a7dc3c5a0a58d372c710974c3`.

Cache aggregate checked at 2026-10-26T17:02:23+00:00 UTC; JSON holds the exact metric lines.
