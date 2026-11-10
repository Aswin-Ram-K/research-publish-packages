# Cache accounting probe — CONTEXT-SERVING-CAMPAIGN

Endpoint: http://192.168.2.168:8012, model occamy-1.0, SGLang 0.0.0.dev1+g4ccff141d.
Server flags relevant: `--enable-cache-report` (true), `--enable-metrics` (true),
`uses_mamba_radix_cache=True`, `mamba_radix_cache_strategy=extra_buffer`,
`mamba_track_interval=256`, `max_mamba_cache_size=64`, `chunked_prefill_size=8192`.
Budget used: 22 preflight requests (of 48); 8 + 14 = 22 total spent including prior.

## Hypothesis 1 — request shape / reporting parameter

Question: does the server report cached tokens only when the request asks for it?

Source (inside container):
- `/sgl-workspace/sglang/python/sglang/srt/server_args.py:1382-1387`
  `enable_cache_report: A[bool, "Return number of cached tokens in usage.prompt_tokens_details for each openai request.", NS("serving")] = False`
- `/sgl-workspace/sglang/python/sglang/srt/entrypoints/openai/usage_processor.py:23-28` `_details_if_cached` returns `PromptTokensDetails(cached_tokens=count)` only when `count > 0`, else `None`.
- `/sgl-workspace/sglang/python/sglang/srt/entrypoints/openai/usage_processor.py:40-52` `calculate_response_usage(..., enable_cache_report=False, ...)` populates `cached_details` only when `enable_cache_report` is true.
- `/sgl-workspace/sglang/python/sglang/srt/entrypoints/openai/serving_chat.py:1899-1903` calls `calculate_response_usage(..., enable_cache_report=self.tokenizer_manager.server_args.enable_cache_report, ...)`.
- `/sgl-workspace/sglang/python/sglang/srt/entrypoints/openai/protocol.py:354` and `:798` `return_cached_tokens_details: bool = False`.
- `/sgl-workspace/sglang/python/sglang/srt/entrypoints/openai/protocol.py:801` `return_meta_info: bool = False`.

Request fields tested (top-level and extra_body):
- `return_meta: true`, `return_cached_tokens: true`, `extra_body: {"return_cached_tokens": true}` are not real parameters; ChatCompletionRequest has no `model_config extra=...` (default ignore), so they are silently ignored (requests returned 200, no error).
- Real fields: `return_meta_info=true` exposes `choices[].meta_info.cached_tokens`; `return_cached_tokens_details=true` exposes `sglext.cached_tokens_details` (device/host/storage split).

Conclusion: `usage.prompt_tokens_details.cached_tokens` is controlled by the **server** flag
`--enable-cache-report`, not by any request field. When that flag is on and a cache hit occurs,
the field appears by default (verified with a default-field request, no extra fields).

Commands / request shapes:
1. Default fields, 1280-token aligned prompt (repeat hit):
   `POST /v1/chat/completions` body `{"model":"occamy-1.0","messages":[{"role":"user","content":<1280-tok prompt>}],"max_tokens":256,"temperature":1.0,"seed":42,"stream":false}`
   -> `raw_usage.prompt_tokens_details = {"cached_tokens": 1152}` (attempt `611dbe81-...`).
2. With `return_meta_info=true, return_cached_tokens_details=true`:
   attempt `9849fab4-...`: `raw_usage.prompt_tokens_details = {"cached_tokens": 1280}`,
   `sglext.cached_tokens_details = {"device": 1280, "host": 0}`.

Per-request snippet (hit):
```json
{"prompt_tokens": 1290, "total_tokens": 1546, "completion_tokens": 256,
 "prompt_tokens_details": {"cached_tokens": 1280}, "reasoning_tokens": 253}
```
Per-request snippet (miss / no hit):
```json
{"prompt_tokens": 153, "total_tokens": 458, "completion_tokens": 305,
 "prompt_tokens_details": null, "reasoning_tokens": 296}
```

## Hypothesis 2 — is the cache actually cold/disabled?

Byte-identical repeat of a 45-token prompt 3 times (same salt, minimal gap):
metrics `sglang:prefill_effective_tokens_total` device_hit stayed 0.0 across all three;
`uncached_prompt_tokens_histogram_count` +1 each (13->14->15->16); `cache_hit_rate` 0.0.
Per-request `meta_info.cached_tokens = 0` for all three. So for short prompts there is
genuinely no device hit.

But for a 1280-token prompt that is an exact multiple of the track interval, a byte-identical
repeat produces a real hit:
- cold request: device_hit 0 -> 0 (no prior entry); uncached +1.
- repeat request: device_hit 0 -> 1280; `usage.prompt_tokens_details.cached_tokens = 1280`.

So the cache is NOT globally disabled; reuse happens when the prompt is long enough and aligned.

Metric delta around the two identical 1280-token requests:
- before cold: input=890, device_hit=0
- after cold:  input=2180 (+1290), device_hit=0 (+0)
- after repeat: input=2190 (+10), device_hit=1280 (+1280)

`sglang:cache_hit_rate` remained 0.0 for every snapshot despite device_hit increments;
it is not a reliable per-phase indicator here. Use
`sglang:prefill_effective_tokens_total{mode="device_hit"}` deltas instead.

## Hypothesis 3 — Mamba/hybrid interference

Source:
- `mamba_radix_cache.py` (extra_buffer strategy) and `hybrid_linear_attn_backend.py:151,406-408`
  tracking condition `seq_lens % mamba_track_interval == 0` (mamba_track_interval=256).
- `batch_result_processor.py:1194` `assert track_seqlen % get_exec().mamba.mamba_track_interval == 0`.
- `schedule_batch.py:2477` `req.cached_tokens += pre_len - req.already_computed`.

Observed:
- 45-token prompt: no hit (prefix not reaching a track boundary).
- 1280-token prompt (exact multiple of 256): full 1280-token hit.
- 2816-token prompt (exact multiple of 256): partial hit 1152/2826 tokens.
  Delta: cold input +2826, device_hit +0; repeat input +1674, device_hit +1152.

So hits require the shared prefix to reach a mamba track boundary (multiple of 256 tokens);
longer prompts may be only partially reusable (likely mamba cache capacity / max_mamba_cache_size=64).

## Hypothesis 4 — prompt size / chunked prefill

- `--chunked-prefill-size 8192`. Tested 1280 and 2816 shared tokens (both below 8192).
  Both show device hits; 2816 only partially (1152). Chunked prefill is not the gating factor;
  mamba track alignment / cache capacity is.

## Final verdict

`PER_REQUEST_FIELD_AVAILABLE`

- The per-request field `usage.prompt_tokens_details.cached_tokens` is available and reports
  >0 on real hits, with no special request field, provided the server was started with
  `--enable-cache-report` (currently true). The server-side parameter that turns it on is
  `enable_cache_report` (`server_args.py:1382`).
- Request-level `return_cached_tokens_details=true` additionally exposes the device/host/storage
  breakdown via `sglext.cached_tokens_details`; `return_meta_info=true` exposes
  `choices[].meta_info.cached_tokens`.

## What the context screen may claim

- Cache savings can be measured per request when `usage.prompt_tokens_details.cached_tokens`
  is present and >0; compute hit ratio as `cached_tokens / prompt_tokens` per request.
- Missing/null `prompt_tokens_details` means unknown, not a measured miss: report a conservative
  range `[0, prompt_tokens]` for that request and exclude it from hit-ratio denominators, or
  label as unknown. Never silently set cached=0 as a measured hit/miss.
- `sglang:cache_hit_rate` gauge is unreliable here (stayed 0.0); phase-level hit ratio must be
  computed from `sglang:prefill_effective_tokens_total{mode="device_hit"}` deltas divided by
  input-token deltas, per phase, with cold/warm ordering documented. Do not flush the shared
  cache; use unique salts/namespaces or a dedicated instance.
- Short prompts (< track interval, ~256 tokens) and unaligned prefixes cannot claim cache
  savings; expect 0/unknown. Long aligned prefixes (>= 256 tokens, ideally exact multiples of
  256) can claim measured hits; longer prompts may be only partially reusable.
- Losers/non-hits must remain visible; do not pool with historical CCS C rows.

## Reconciliation

- 22 intents, 21 successful rows, 1 failed attempt (`580eaf90-...`, recorded failed),
  22 spent. Counts agree with ledger. Rows: `run/rows/preflight.jsonl`.
- Watcher emitted `rows_missing`/`intent_row_mismatch` alerts because the envelope stores
  paths under `paths.rows.preflight` / `paths.intents.preflight`, while watcher resolves only
  top-level `rows_path`/`intents_path`; this is a pre-existing watcher/envelope mismatch and
  does not invalidate the rows (counts reconciled manually above).
