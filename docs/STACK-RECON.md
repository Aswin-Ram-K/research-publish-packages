# STACK-RECON — what our serving stack can actually tell us

**Unit:** `STACK-RECON` · **Checked:** 2026-10-26T09:23–09:31 America/Chicago (UTC-05:00)
**Constraint honoured:** zero inference requests. Every live value below came from an HTTP `GET` on
`/v1/models`, `/metrics`, `/metrics/`, `/version`, `/health`, `/get_server_info`. Nothing was restarted,
no flag changed, no mutating endpoint called.

---

## 0. Corrections to the card's "verified facts"

Three card facts did not survive probing. Replacement values are the ones to use from now on.

| Card said | Probe says | Impact |
|---|---|---|
| SGLang model id `occamy-1.0-NVFP4` | **`occamy-1.0`** (`root: "occamy-1.0"`, `owned_by: "sglang"`, `max_model_len: 131072`) | A client sending `"model": "occamy-1.0-NVFP4"` is rejected. The `NVFP4` string only exists in the HF path (`models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652`) and in `quantization: "modelopt_fp4"`. |
| SGLang `/health` returns `000` even when healthy | `/health` → **200** (empty body). `/v1/models` → 200. `/version` → **404** `{"detail":"Not Found"}` | `/health` is usable for liveness again; `/version` is *not* available on SGLang. |
| vLLM returns `prompt_tokens_details: null` "on every row" | True of the *response*, but the engine **does** count cached tokens: `vllm:prompt_tokens_cached_total` = 4,114,176 of 8,324,862 prompt tokens (**49.4 % lifetime, token-weighted**) | This is the single most important finding: the `null` is a response-schema/protocol artifact, not an absence of cache. See §4. |

---

## 1. Live probe — status codes (verbatim)

| Endpoint | :8012 SGLang | :8014 vLLM |
|---|---|---|
| `/v1/models` | 200 | 200 |
| `/metrics` | 200 | 200 |
| `/metrics/` | 200 | 200 |
| `/version` | **404** | 200 → `{"version":"0.27.1"}` |
| `/health` | 200 | 200 |
| `/get_server_info` | 200 (32,588 bytes) | **404** (22-byte error body) |

Both servers bind on `192.168.2.168` only; loopback is dead (already established, re-confirmed
implicitly — every probe above is remote).

---

## 2. SGLang :8012 — engine truth from `/get_server_info`

Build: `version = "0.0.0.dev1+g4ccff141d"` (dev build; docs lag it — see §3 caveat).

Cache-relevant config, verbatim:

```
enable_cache_report             = true
disable_radix_cache             = false        # radix prefix cache ACTIVE
page_size                       = 1            # token-granular, no block quantisation
radix_eviction_policy           = "lru"
uses_mamba_radix_cache          = true
enable_hierarchical_cache       = false
enable_lmcache                  = false
hicache_size                    = 0
kv_cache_dtype                  = "fp8_e4m3"
quantization                    = "modelopt_fp4"
attention_backend               = "triton"
chunked_prefill_size            = 8192
max_running_requests            = 5
mem_fraction_static             = 0.45
schedule_policy                 = "fcfs"
schedule_conservativeness       = 1.0
context_length                  = 131072
skip_server_warmup              = false        # server-side warmup RAN
stream_response_default_include_usage = false  # streaming rows omit usage unless asked
tool_call_parser                = "qwen3_coder"
disable_cuda_graph              = false
cuda_graph_max_bs_decode        = 8
```

Two of these decide whole measurement questions:

- `page_size = 1` → SGLang cache hits are **token-granular**. A pinned prefix hits at whatever token
  boundary it shares; there is no block quantisation to worry about.
- `max_running_requests = 5` and `mem_fraction_static = 0.45` → queueing at 5 concurrent. Any arm that
  runs >5 concurrent requests is measuring queue wait, not prefill.

---

## 3. The metric lists (the core deliverable)

### 3.1 SGLang :8012 — 72 metric families

Verbatim names with declared type, filtered to the five asked-for areas. `sglang:` prefix.

**Prefix cache**
```
sglang:cached_tokens_total              counter   HELP: "Number of cached prompt tokens by source (device/host/storage)."
sglang:cache_hit_rate                   gauge     HELP: "The prefix cache hit rate."
sglang:evicted_tokens_total             counter
sglang:prefill_effective_tokens_total   counter   HELP: "Effective prefill tokens with retracted-request re-counts excluded,
                                                    updated on each log interval. mode: device_hit, host_hit, storage_hit, input.
                                                    Windowed prefix cache hit rate = rate(sum of *_hit) / rate(sum of all modes);
                                                    per-tier rate uses a single *_hit mode in the numerator."
sglang:uncached_prompt_tokens_histogram histogram HELP: "Histogram of uncached (compute) prompt token length."
sglang:prompt_tokens_histogram          histogram
sglang:generation_tokens_histogram      histogram
```

**KV cache / pressure**
```
sglang:kv_used_tokens          gauge   "Number of actively used token slots in the KV cache pool."
sglang:kv_available_tokens     gauge   "Number of free token slots in the KV cache pool."
sglang:kv_evictable_tokens     gauge
sglang:max_total_num_tokens    gauge
sglang:num_used_tokens         gauge
sglang:num_pages               gauge
sglang:page_size               gauge
sglang:token_usage             gauge   "The token usage."
sglang:full_token_usage        gauge
sglang:pending_prealloc_token_usage gauge
sglang:swa_used_tokens / sglang:swa_available_tokens / sglang:swa_evictable_tokens / sglang:swa_token_usage   gauge
sglang:mamba_used_tokens / mamba_available_tokens / mamba_evictable_tokens / mamba_usage   gauge
sglang:kv_cache_memory_usage_gb gauge
sglang:new_token_ratio         gauge
sglang:utilization             gauge
sglang:fwd_occupancy           gauge
```

**Queue depth**
```
sglang:num_queue_reqs                   gauge   "The number of requests in the waiting queue."
sglang:num_running_reqs                 gauge
sglang:num_paused_reqs                  gauge
sglang:num_retracted_reqs               gauge
sglang:num_decode_prealloc_queue_reqs   gauge
sglang:num_decode_transfer_queue_reqs   gauge
sglang:num_prefill_bootstrap_queue_reqs gauge
sglang:num_prefill_inflight_queue_reqs  gauge
sglang:num_grammar_queue_reqs           gauge
```

**Tokens & requests**
```
sglang:prompt_tokens_total       counter   "Number of prefill tokens processed."        labels: is_streaming
sglang:generation_tokens_total   counter                                                labels: is_streaming
sglang:num_requests_total        counter                                                labels: is_streaming
sglang:num_aborted_requests_total counter
sglang:realtime_tokens_total     counter
sglang:gen_throughput            gauge
sglang:http_requests_total / http_responses_total / http_requests_active
```

**Latency / TTFT**
```
sglang:time_to_first_token_seconds    histogram   "Histogram of time to first token in seconds."
sglang:e2e_request_latency_seconds    histogram
sglang:queue_time_seconds             histogram
sglang:inter_token_latency_seconds    histogram
sglang:per_stage_req_latency_seconds  histogram
sglang:eviction_duration_seconds      histogram
```

**Startup / JIT contamination**
```
sglang:startup_time_seconds   gauge, phase={load_weight, kv_cache_allocation, scheduler_e2e, tokenizer_e2e}
sglang:startup_cuda_graph_time_seconds  gauge
sglang:startup_available_gpu_memory_gb  gauge
sglang:cuda_graph_passes_total  counter, mode={decode_cuda_graph, prefill_cuda_graph, prefill_none}
sglang:is_cuda_graph          gauge
sglang:graph_memory_usage_gb  gauge
sglang:spec_accept_length / spec_accept_rate / spec_num_draft_tokens / spec_num_steps / spec_cap_length
```

Live values at 09:26 (idle box, engine warm):

```
max_total_num_tokens        1.514599e+06
kv_available_tokens         48752.0        # free slots right now
kv_used_tokens              0.0
num_running_reqs            0.0
num_queue_reqs              0.0
cache_hit_rate              0.0            # <<< windowed, and empty window reads 0
token_usage                 0.0
utilization                 0.0
cached_tokens_total{cache_source="device"}              1.8611456e+07
prompt_tokens_total{is_streaming="false"}               1.8823105e+07
prompt_tokens_total{is_streaming="true"}                5.592818e+06
num_requests_total{is_streaming="false"}                3717.0
num_requests_total{is_streaming="true"}                 924.0
generation_tokens_total{is_streaming="true"}            809553.0
startup_time_seconds{phase="load_weight"}               106.61
startup_time_seconds{phase="kv_cache_allocation"}       0.913
startup_time_seconds{phase="scheduler_e2e"}             155.68
startup_time_seconds{phase="tokenizer_e2e"}             160.42
cuda_graph_passes_total{mode="prefill_cuda_graph"}      4768.0
cuda_graph_passes_total{mode="decode_cuda_graph"}       590017.0
cuda_graph_passes_total{mode="prefill_none"}            18.0
```

Derived, with its caveat spelled out: `1.8611456e7 / (1.8823105e7 + 5.592818e6) = 18.611456/24.415923
= 76.2 %` lifetime token-weighted cache coverage. **Caveat:** the numerator carries no `is_streaming`
label while the denominator is split by it, so the counter-side ratio is a pooled approximation, not the
engine's own hit rate. The engine's own definition is the `prefill_effective_tokens_total` mode ratio
(see HELP text above) or the windowed `cache_hit_rate` gauge.

### 3.2 vLLM :8014 (v0.27.1) — ~120 families

**Prefix cache — the decisive ones**
```
vllm:prefix_cache_queries_total        counter  "Prefix cache queries, in terms of number of queried tokens."
vllm:prefix_cache_hits_total           counter  "Prefix cache hits, in terms of number of cached tokens."
vllm:external_prefix_cache_queries_total counter
vllm:external_prefix_cache_hits_total    counter  "External prefix cache hits from KV connector cross-instance cache sharing..."
vllm:prompt_tokens_cached_total        counter  "Number of cached prompt tokens (local + external)."
vllm:prompt_tokens_by_source_total     counter  "Number of prompt tokens by source."   label: source
vllm:mm_cache_hits_total / mm_cache_queries_total counter
vllm:cache_config_info                 gauge    Info-style; value always 1, config in labels
```

**KV cache / pressure**
```
vllm:kv_cache_usage_perc        gauge   "KV-cache usage. 1 means 100 percent usage."
vllm:num_preemptions_total      counter
vllm:engine_sleep_state         gauge, label sleep_state={awake, weights_offloaded, discard_all}
```

**Queue depth**
```
vllm:num_requests_waiting              gauge   "Number of requests waiting to be processed."
vllm:num_requests_waiting_by_reason    gauge   reason={capacity, deferred}; "Sum of all reasons equals vllm:num_requests_waiting."
vllm:num_requests_running              gauge
```

**Tokens**
```
vllm:prompt_tokens_total        counter   "Number of prefill tokens processed."
vllm:generation_tokens_total    counter
vllm:request_prompt_tokens      histogram
vllm:request_generation_tokens  histogram
vllm:iteration_tokens_total     histogram
vllm:request_prefill_kv_computed_tokens histogram  "Histogram of new KV tokens computed during prefill (excluding cached tokens)."
```

**Latency / TTFT**
```
vllm:time_to_first_token_seconds          histogram
vllm:e2e_request_latency_seconds          histogram
vllm:request_queue_time_seconds           histogram
vllm:request_prefill_time_seconds         histogram
vllm:request_decode_time_seconds          histogram
vllm:request_inference_time_seconds       histogram
vllm:request_time_per_output_token_seconds histogram
vllm:inter_token_latency_seconds          histogram
vllm:request_success_total                counter, label finished_reason
```

Live values at 09:28:

```
prefix_cache_queries_total                       8.324862e+06
prefix_cache_hits_total                          4.114176e+06
prompt_tokens_total                              8.324862e+06
prompt_tokens_cached_total                       4.114176e+06
prompt_tokens_by_source_total{source="local_compute"}      4.210686e+06
prompt_tokens_by_source_total{source="local_cache_hit"}    4.114176e+06
prompt_tokens_by_source_total{source="external_kv_transfer"} 0.0
kv_cache_usage_perc                              0.0
num_requests_running / waiting / waiting_by_reason  0.0 / 0.0 / 0.0
```

Identity check that makes this trustworthy: `local_compute + local_cache_hit + external_kv_transfer
= 4,210,686 + 4,114,176 + 0 = 8,324,862 = prompt_tokens_total` exactly, and
`prompt_tokens_cached_total == prefix_cache_hits_total == 4,114,176`. So on **this** server the three
cache counters and the prompt-token counter agree to the token. Lifetime hit rate = 49.4 %.

`vllm:cache_config_info` labels (verbatim, abridged):

```
enable_prefix_caching="True"   block_size="1056"   user_specified_block_size="False"
_block_size_resolved="True"    num_gpu_blocks="99"  kv_cache_size_tokens="79122"
gpu_memory_utilization="0.15"  cache_dtype="fp8"    prefix_caching_hash_algo="sha256"
kv_cache_max_concurrency="2.4146341463414633"       kv_offloading_backend="native"
sliding_window="None"          mamba_cache_mode="align"
```

**Block granularity is 1056 tokens** (auto-resolved; the user did not set it). This matters more than
anything else on the vLLM side for the pointer arm: a cache hit can only be credited at a **1056-token
block boundary**, so a pinned range that is not a multiple of 1056 tokens leaves its tail to be recomputed
and the observed `cached_tokens` will not equal the pinned length.

---

## 4. Is per-request cache attribution available today? (Task 1.4)

**SGLang: yes — per request, in the response body, already enabled.**
`enable_cache_report = true` is live, so the OpenAI-compatible response carries
`usage.prompt_tokens_details.cached_tokens` (the field SGLang's own docs show on native `/generate`
usage as `prompt_tokens_details.cached_tokens`). For **streaming** rows the field only appears if the
request sends `stream_options: {"include_usage": true}` — the server default is
`stream_response_default_include_usage = false`, i.e. streaming rows silently lose usage.

**vLLM: no — not in the response today; but the quantity is counted server-side.**
The row schema sees `null`; `vllm:prompt_tokens_cached_total` proves the engine counted 4,114,176 cached
tokens. The only ways to recover a per-request number from vLLM as configured:
- **Delta of the counters across a serialised request** (`prompt_tokens_cached_total` or
  `prompt_tokens_by_source_total{source="local_cache_hit"}` before/after, with exactly one request
  in flight — `kv_cache_max_concurrency` is 2.4, so concurrency must be forced to 1 by the client);
- or enable the per-request metrics surface (`--enable-per-request-metrics`, **requires restart**), which
  keys latency metrics by `request_id` but still does not add a per-request `cached_tokens` field.

**Neither server exposes per-*range* attribution.** No metric names a prompt span, a request id ↔ tokens
mapping, or which pinned range hit. Both are cumulative token counters plus token-length histograms.

---

## 5. Current upstream documentation (checked 2026-10-26)

### 5.1 `prompt_tokens_details.cached_tokens`

- **vLLM** `docs.vllm.ai/en/stable/design/metrics/` (fetched 2026-10-26) documents
  `vllm:prompt_tokens_total`, `prefix_cache_queries`/`hits`, and the `cache_config_info` Info-metric
  pattern, but the metrics page does **not** state when `UsageInfo.prompt_tokens_details` is populated.
  I could not settle the exact population condition from public docs without an inference request, so I
  record it as **unresolved-and-observable-instead**: the same quantity is available from
  `vllm:prompt_tokens_cached_total` regardless of what the response does. Version-dependent: our box is
  vLLM **0.27.1** (`/version`), far ahead of the versions in most public issue threads.
  *Likely causes for `null`, in order of plausibility — all unverified, none requiring a restart to test
  server-side:* (a) the client/row-writer dropped the nested object when the server returned it as an
  absent-optional rather than an object; (b) streaming rows without `stream_options.include_usage`
  (vLLM omits `usage` on stream chunks unless asked — the standard OpenAI-compatible behaviour); (c) a
  version where `prompt_tokens_details` is only filled when the frontend computed cache stats.
- **SGLang** `docs.sglang.io/docs/references/production_metrics` (fetched 2026-10-26) does not document
  `cached_tokens_total` at all, while our dev build `0.0.0.dev1+g4ccff141d` exposes it with a
  `cache_source` label. **Documented behaviour lags the build** — treat the live `/metrics` as the
  authority, not the docs page.

### 5.2 Cache metrics and their known caveats

- **vLLM** (`docs.vllm.ai/en/stable/design/metrics/`): "Every time the prefix cache is queried, we record
  the number of tokens queried and the number of queried tokens present in the cache (i.e. hits). However,
  the metric of interest is the hit rate — i.e. the number of hits per query."
  — i.e. the rate is **token-weighted hits ÷ token-weighted queries**, not block-weighted and not
  request-weighted. The engine's 5-second log line reports hit rate "over the most recent 1k kv-cache
  block queries" — **a sliding window, not lifetime**. The Prometheus counters are cumulative, so a
  per-interval number must come from `rate()` deltas, never from the counter value.
- **SGLang** (`docs.sglang.io/docs/references/production_metrics`): metrics need `--enable-metrics`; ours
  is on. `sglang:cache_hit_rate` is a **gauge** and reads `0.0` on an idle box (docs' own example shows
  `0.0075`) → it is a recent-window value, **never** a lifetime rate. The live HELP text for
  `prefill_effective_tokens_total` gives the authoritative windowed formula
  `rate(sum of *_hit) / rate(sum of all modes)` and warns it is "updated on each log interval".
  `sglang:cached_tokens_total` is a **counter**, cumulative since start, labelled `cache_source`
  (device / host / storage) — device-only here because hierarchical/LMCache are off.

### 5.3 `tool_choice`

- **vLLM** (`docs.vllm.ai/en/stable/features/tool_calling.html`, 2026-10-26): the documented launch is
  `vllm serve ... --enable-auto-tool-choice --tool-call-parser <parser>`. The page has separate sections
  **Named Function Calling**, **Required Function Calling**, **Automatic Function Calling**, **None
  Function Calling** — so named/required selection also ride on the same flag pair plus the chat template.
  Our server refuses `tool_choice=auto` because neither flag is set → **requires-restart with
  `--enable-auto-tool-choice --tool-call-parser <parser>`** (`qwen3_coder` would be the matching parser if
  the vLLM build ships it; verify before restarting).
- **SGLang**: already configured — `tool_call_parser = "qwen3_coder"`, i.e. SGLang's server-side parser is
  active and needs no restart.

### 5.4 Warmup / cold-start contamination

- **SGLang** (`docs.sglang.io`, plus live config): the server runs its own warmup because
  `skip_server_warmup = false`. Effects are measurable rather than assumed: `startup_time_seconds{phase}`
  shows `load_weight 106.6 s`, `kv_cache_allocation 0.91 s`, `scheduler_e2e 155.7 s`,
  `tokenizer_e2e 160.4 s`; `startup_cuda_graph_time_seconds` and `startup_available_gpu_memory_gb` exist
  too. CUDA-graph capture is observable live via `cuda_graph_passes_total{mode}` — the live counters
  (4768 prefill captures, 590,017 decode, **18 `prefill_none`**) show that prefill normally runs under a
  CUDA graph and occasionally does not. A first request after a process start, or one that lands on a
  shape outside the captured batch sizes (`cuda_graph_max_bs_decode = 8`), is contaminated.
- **vLLM**: no explicit warmup flag; cold-start cost is the model load plus graph capture, after which
  `process_start_time_seconds` gives the process epoch so any sample can be filtered by age. vLLM also
  exposes `vllm:request_prefill_kv_computed_tokens`, which is the cleanest **post-warmup** confirmation
  that prefill actually computed new KV (as opposed to replaying cache).

---

## 6. Verdict per measurement (Task 3)

| Measurement we need | Observable today? | Exact source | Row schema must carry | Cost to enable |
|---|---|---|---|---|
| Cached prompt tokens **per request** — SGLang | **yes** | `usage.prompt_tokens_details.cached_tokens` in the chat-completions response (`enable_cache_report=true` already live) | the nested `usage` object verbatim, per row; `stream_options.include_usage` for streaming rows | none (already on); streaming rows need one request-body field |
| Cached prompt tokens **per request** — vLLM | **no** (response); **yes-with-discipline** (counters) | `vllm:prompt_tokens_cached_total` or `vllm:prompt_tokens_by_source_total{source="local_cache_hit"}` delta with exactly 1 request in flight | a pre/post `/metrics` snapshot pair per row, plus a concurrency=1 assertion | none for the delta method; `--enable-per-request-metrics` for id-keyed latency is **requires-restart** |
| Prefix-cache **hit rate** | **yes-with-caveat** | SGLang: `sglang:cache_hit_rate` gauge (windowed) or `sglang:prefill_effective_tokens_total` mode ratio. vLLM: `rate(prefix_cache_hits_total)/rate(prefix_cache_queries_total)` | the two counters scraped at request start/end, not the ratio | none |
| Queue depth **at request time** | **yes-with-caveat** (sampled, not stamped) | `sglang:num_queue_reqs`, `sglang:num_running_reqs`; `vllm:num_requests_waiting`, `vllm:num_requests_waiting_by_reason{reason="capacity"\|"deferred"}` | a scrape timestamp before and after each row, or accept ±scrape-interval noise | none |
| **TTFT** from the server's own view | **yes** (aggregate only) | `sglang:time_to_first_token_seconds`, `vllm:time_to_first_token_seconds` histograms; plus `queue_time_seconds` / `request_queue_time_seconds` and `request_prefill_time_seconds` | histogram bucket deltas per phase, or per-request spans | per-request TTFT attribution: **requires-restart** (`--enable-per-request-metrics` on vLLM) |
| **KV cache pressure** | **yes** | SGLang `kv_used_tokens` / `kv_available_tokens` / `max_total_num_tokens` / `token_usage`; vLLM `kv_cache_usage_perc` | the gauge value + scrape time per row | none |
| Did the prompt **hit cache for the pinned ranges** the pointer arm claims | **NO** — no per-range attribution exists on either server | closest proxies: SGLang `cached_tokens_total` delta + `uncached_prompt_tokens_histogram`; vLLM `prompt_tokens_cached_total` delta + `request_prefill_kv_computed_tokens` | would need a per-request `cached_tokens` field *and* a serialised (concurrency-1) protocol; the range identity is not in any metric | none, but the inference is only valid at concurrency 1 |

Non-mutating endpoints that exist and were **not** called: SGLang `/get_server_info` was read (safe). No
cache-reset endpoint was probed or invoked; SGLang's `flush_cache` and vLLM's `/reset_prefix_cache` are
**mutating** and were deliberately left alone.

---

## 7. The honest bottom line (≤10 lines)

1. **Unobservable today:** per-*range* cache attribution. Neither server names a prompt span, so "the pinned ranges hit cache" cannot be verified from the stack as it stands. It can only be *inferred* by forcing concurrency to 1 and differencing `prompt_tokens_cached_total`.
2. **Unobservable today:** per-request TTFT attribution and per-request queue wait on vLLM (histograms are aggregates); SGLang gives per-request `cached_tokens` but still not per-request TTFT.
3. **Observable, not recorded:** both cache counters, both KV-pressure gauges, both queue gauges. Every one of them is live right now and absent from the row schema.
4. **Recorded but misinterpreted:** `prompt_tokens_details: null` was read as "no cache information", when vLLM is in fact serving at a **49.4 % lifetime token-weighted cache hit rate** (4,114,176 of 8,324,862 prompt tokens) and SGLang at ~76 % pooled. The `null` is a protocol gap, not a cache fact.
5. **Recorded but misinterpreted:** if any analysis used `sglang:cache_hit_rate` as a run-level number, it read a **log-interval window** (0.0 at idle), not a cumulative rate.
6. **Correctness trap for the pointer arm:** vLLM credits hits at **1056-token block granularity**; SGLang at **page_size=1**. The same pinned range therefore reports different `cached_tokens` on the two servers, and on vLLM a non-1056-multiple pin leaves a recomputed tail.
7. **Contamination that must be filtered:** SGLang warmup took ~160 s to `tokenizer_e2e`; `startup_time_seconds` and `process_start_time_seconds` let any first-request sample be excluded by process age.
8. **Verdict:** the pointer arm's cache claim is **not verifiable with what the servers expose per request today** — say so before another 72 requests. The cheapest fix is not a restart: serialize to concurrency 1, snapshot `/metrics` before and after each row, and record the delta. A restart buys per-request latency only.
