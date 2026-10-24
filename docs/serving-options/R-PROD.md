# R-PROD — what production teams actually run (serving configs, cache settings spelled out)

> **STALE NOTE — superseded for the model-vs-engine question.** Written 2026-10-21 as offline research:
> **no live requests, no measured cells**. The measured answer is
> [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`, `papers/context-cache/MANUSCRIPT.md` §9b): on one shared
> 32k/71-turn 2x2 the **engine** sets the per-turn uncached bill (**+1,225.18** tokens/turn,
> **2.6738x**, 0.9115 of the 1,344.16 grand mean) and the model main effect is **+275.83** — only
> **+3.61** of it under SGLang, where both checkpoints share the 64-token grid. Read the rest of this
> note as dated background on **flag mechanics**, not as evidence about cost. What remains current: its
> launch-flag descriptions. What is **not** current: any suggestion that the model is the lever.

**Unit:** R-PROD · offline research only · **0 live requests**, no Occamy connection, no lock taken.
**Baseline compared against:** single SGLang deployment, GB10-class node, Qwen3.5-MoE hybrid attention,
`page_size=1`, plain radix cache, `chunked_prefill_size=8192`, no HiCache, no LMCache.
**Collected:** 2026-10-21, from vendor docs, stack repos, team blogs and official benchmark recipes.

Stability signal vocabulary:
`production` = vendor/operator ships it as the reference deployment path (validated or nightly E2E);
`benchmark-only` = official recipe whose purpose is a published number, not a service;
`reported-only` = a claim we could not pin to a reproducible flag set / measurement.

---

## 1. Table of reference configs

### A. SGLang HiCache — official recipes (LMSYS / SGLang team)
Source: [SGLang HiCache blog, 2025-09-10](https://www.lmsys.org/blog/2025-09-10-sglang-hicache/)

**A1 — DeepSeek-R1, 8×H20-3e, 3FS backend** (long-context QA, `loogle_wiki_qa`):

```
python3 -m sglang.launch_server --model-path /DeepSeek-R1/ --tp 8 --page-size 64 \
--context-length 65536 --chunked-prefill-size 6144 --mem-fraction-static 0.85 \
--enable-hierarchical-cache --hicache-ratio 2 \
--hicache-io-backend kernel --hicache-mem-layout page_first \
--hicache-storage-backend hf3fs --hicache-storage-prefetch-policy wait_complete
```

**A2 — Qwen3-235B-A22B-Instruct-2507, 8×H800 + 8×mlx5 RDMA, Mooncake** (multi-turn; `bench_multiturn.py`
with `--num-clients 80 --num-rounds 10 --request-length 2048 --request-rate 16 --ready-queue-policy random`):

```
python3 -m sglang.launch_server --model-path $MODEL_PATH --tp 8 --page-size 64 \
--enable-hierarchical-cache --hicache-ratio 2 \
--hicache-storage-prefetch-policy timeout --hicache-storage-backend mooncake
```

- **Tuned for:** A1 long-context document QA; A2 multi-turn conversation with P/D-disaggregation-like
  request pattern (`--output-length 1`).
- **Measured:** SGLang's own run — "up to **6× throughput** improvement and up to **80% reduction in TTFT**".
  Community, in the same post: Novita AI, Qwen3-Coder-480B coding agent (dialogues >25K tokens, ~8 turns):
  **TTFT −56%, inference throughput 2×, cache hit rate 40% → 80%** with HiCache+3FS. Ant Group,
  DeepSeek-R1-671B with Mooncake under PD-disaggregated serving: **84% TTFT reduction vs full re-computation**.
- **Stability:** `production` (vendor recipe + two named production deployments). `--hicache-ratio 2`
  = host tier is 2× the GPU KV pool; `page_first` layout is what makes CPU↔storage I/O efficient.
- **Single-GB10 delta:** drop `--tp 8`; `--page-size 64` is the recipe value (SGLang's radix default is 1);
  `hf3fs`/`mooncake` need a storage cluster → replace with the local `HiCacheFile` backend or CPU-only
  (`--hicache-ratio 2`, no storage backend). `--mem-fraction-static 0.85` assumes ≥140 GB of HBM — not
  transferable to one GB10.

### B. SGLang official HiCache ablation harness
Source: [sgl-project/sglang `benchmark/hicache/README.md`](https://github.com/sgl-project/sglang/blob/main/benchmark/hicache/README.md)

Four arms, `bench_multiturn.py`, Qwen2.5-14B-Instruct:

```
--disable-radix-cache              # no cache
--schedule-policy fcfs             # radix on, first-come-first-serve
                                   # (default: radix on + long-prefix-match policy)
--enable-hierarchical-cache        # HiCache on
```

- **Tuned for:** multi-turn / shared-prefix reuse (`--enable-multiturn`, `--enable-shared-prefix`,
  loogle long-dependency QA, sharegpt/ultrachat).
- **Measured:** none in the README — it is a harness. The README does state the governing condition:
  "the performance gain of hierarchical caching depends on the **ratio of reusable tokens to GPU memory
  capacity**… the larger the model and the more constrained the GPU memory, the greater the benefit".
- **Stability:** `benchmark-only` — but this is the canonical same-harness ablation, i.e. the cheapest way
  to make our 64-token grid comparable to a published recipe.
- **GB10 delta:** none — the arms are flag-only and hardware-agnostic. Note the harness itself says the
  round-robin conversation order is chosen to maximise reuse distance, i.e. it is the *hardest* case for
  a FIFO scheduler (a useful stress setting, not a representative one).

### C. SGLang session-aware radix cache (multi-turn / agent sessions)
Source: [SGLang docs — Session-Aware Radix Cache](https://docs.sglang.io/docs/advanced_features/session_radix_cache)

```
python3 -m sglang.launch_server --model-path MODEL_PATH --enable-session-radix-cache
# client: same top-level "session_id" on every request; POST /close_session at session end
```

- **Mechanism (quoted):** "registers reusable KV to a session and evicts unreferenced KV before KV still
  referenced by an active session. Session references are **soft protection, not memory pins**."
  Implemented only by `UnifiedRadixCache`. The `session_id` labels cache references only — it does not
  append or reconstruct context, so each request must still carry the full prompt.
- **Tuned for:** long-lived multi-turn/agent sessions under memory pressure.
- **Measured:** none published.
- **Stability:** `production` feature in the server (documented, on by flag), no deployment numbers.
- **GB10 delta:** flag-only; requires the unified radix cache path. **Relevance to our baseline:** this is
  the production answer to "LRU evicted the one session that mattered" — it protects by *reference*, not
  by pinning, which matches what we observe (no suffix recovery) without needing a new engine.

### D. llm-d — optimized baseline + tiered prefix cache (CNCF, Red Hat/Google/IBM/CoreWeave/NVIDIA)
Sources: [llm-d README](https://github.com/llm-d/llm-d), [Optimized Baseline](https://llm-d.ai/docs/well-lit-paths/foundations/optimized-baseline),
[Tiered Prefix Cache](https://llm-d.ai/docs/well-lit-paths/foundations/tiered-prefix-cache)

- **Reference layout:** Qwen3-32B, **2 replicas × TP=2 (4×H100 80 GB)**, router with
  *prefix-cache-affinity filter* + *token-load scorer*, both at built-in defaults; saturation override
  keyed on `peakPrefillThroughput` (must be re-measured per model/hardware).
- **Tiered cache, exact selectors:** `CONNECTOR=native` (vLLM `OffloadingConnector`; SGLang HiCache is the
  SGLang arm), `VARIANT=cpu` (HBM→CPU) or `fs` (HBM→CPU→ReadWriteMany filesystem through
  `TieringOffloadingSpec`).
- **Tier sizes (quoted):** NVIDIA vLLM native overlay **300 GiB** `cpu_bytes_to_use` per replica; AMD/Intel/TPU
  100 GiB; **SGLang `--hicache-size=200` (GB per tensor-parallel rank)**, i.e. `--enable-hierarchical-cache`
  plus `--hicache-size`; LMCache `LMCACHE_MAX_LOCAL_CPU_SIZE` (GiB per TP rank). vLLM keeps the CPU tier in
  `/dev/shm`, so it counts against the pod memory limit; changing tier size requires changing the pod memory
  *and* the router's `lruCapacityPerServer`.
- **Measured (v0.5/v1.0 release reporting):** **13.9× throughput** with hierarchical KV offloading at
  250 concurrent users vs GPU-only on 4×H100; **3× output throughput / 2× faster TTFT** with prefix-cache-aware
  routing vs round-robin (Llama 3.1 70B, 4×MI300X); 50k output tok/s on 16×16 B200 wide-EP.
- **Stability:** `production` — nightly E2E workflows per accelerator/engine combination, versioned guides,
  v1.0 released.
- **GB10 delta:** the router and multi-replica layout are the point of llm-d and are meaningless on one node;
  what transfers is the **sizing discipline** (`cpu_bytes_to_use` / `--hicache-size` in GB per TP rank, matched
  to the pod memory limit) and the offload connector choice.

### E. vLLM Production Stack + LMCache (the reference K8s stack)
Sources: [production-stack README](https://github.com/vllm-project/production-stack),
[helm/values.yaml](https://github.com/vllm-project/production-stack/blob/main/helm/values.yaml),
[tutorial 05 — KV offload with LMCache](https://github.com/vllm-project/production-stack/blob/main/tutorials/05-offload-kv-cache.md)

Exact values from `tutorials/assets/values-05-cpu-offloading.yaml`:

```yaml
repository: "lmcache/vllm-openai"; tag: "latest"
modelURL: "mistralai/Mistral-7B-Instruct-v0.2"; replicaCount: 1
requestCPU: 10; requestMemory: "40Gi"; requestGPU: 1; pvcStorage: "50Gi"
vllmConfig:
  enableChunkedPrefill: false
  enablePrefixCaching: false      # <- off: LMCache owns the cache
  maxModelLen: 16384
lmcacheConfig:
  enabled: true
  cpuOffloadingBufferSize: "20"   # GB
```

Helm chart defaults that matter for stability: `gpuMemoryUtilization: 0.95`, `maxNumSeqs: 32`,
`dtype: bfloat16`, `tensorParallelSize: 2`, `v0: "1"` (vLLM v0 flag), PVC `50Gi`, image `lmcache/vllm-openai`.

- **Tuned for:** single-model chat (Mistral-7B), CPU-tier KV offload; the router does round-robin /
  session-ID / prefix-aware routing.
- **Measured:** none in the tutorial ("Benchmark the Performance Gain of CPU Offloading (Work in Progress)") →
  the *gain* claim is `reported-only`; the *config* is `production` (helm reference path).
- **Notable inversion:** the reference offload tutorial explicitly disables vLLM prefix caching because the
  external cache (LMCache) is the cache. Two cache layers on the same KV is not the production pattern.
- **GB10 delta:** no K8s/helm needed — this is a values-file translation of
  `vllm serve … --kv-transfer-config <LMCache connector>` with a 20 GB CPU buffer.

### F. vLLM native tiered offloading (v0.22+)
Source: [vLLM blog — Tiered KV Cache Offloading, 2026-09-10](https://vllm.ai/blog/2026-09-10-tiered-kv-offloading),
usage guide `docs.vllm.ai/en/latest/features/kv_offloading_usage/`

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
  --kv-transfer-config '{
    "kv_connector_extra_config": {
      "spec_name": "TieringOffloadingSpec",
      "cpu_bytes_to_use": 107374182400,
      "secondary_tiers": [{"type": "fs", "root_dir": "/mnt/kv-cache"}]
    }
  }'
# object store: {"type":"obj","bucket":"my-kv-cache","endpoint_override":"http://minio:9000"}
# peer:         {"type":"p2p","host":"10.0.0.1","port":5710}
```

- **Design facts that change measurements:** unit of transfer is a **chunk**, default = one accelerator block,
  `blocks_per_chunk` configurable; host primary tier is a real **LRU/ARC cache** (not a staging buffer);
  reload queries secondary tiers in configured order and returns `RETRY` while promoting; host layout is
  **canonical** (TP=2 and TP=4 nodes produce identical host chunks); hybrid layers (sliding-window, Mamba/SSM,
  MLA) are normalised to a fixed byte size per chunk — sliding-window layers reload only their window.
- **Tuned for:** long-context + multi-turn, cross-node sharing and P/D.
- **Measured:** blog has a "Performance — Scaling to More Users" section; we did not extract a number from it
  in this pass → treat the throughput claim as `reported-only` here.
- **Stability:** `production` (shipped since v0.22, documented usage guide, Prometheus metrics for per-tier hit
  rates and transfer latency).
- **GB10 delta:** fully applicable — `cpu_bytes_to_use` 100 GiB is a host-DRAM sizing choice, and the `fs`
  tier can be a local directory. This is the only engine here whose CPU tier is inside the engine process
  and needs no K8s.

### G. NVIDIA Dynamo — agentic single-GPU recipe (closest structural match to our baseline)
Sources: [Dynamo recipes index](https://github.com/ai-dynamo/dynamo/blob/main/recipes/README.md),
[Qwen3.6-35B-A3B recipe](https://github.com/ai-dynamo/dynamo/blob/main/docs/fern/pages/recipes/model-recipes/qwen3-6-35b-a3b.mdx),
[deploy manifest](https://github.com/ai-dynamo/dynamo/blob/main/recipes/qwen3.6-35b-a3b/sglang/agg-gb200-mtp/deploy.yaml)

Exact SGLang args (GB200 manifest, 1 GPU, hybrid GDN+MoE — same architecture class as our Qwen3.5-MoE):

```
python3 -m dynamo.sglang
  --model-path nvidia/Qwen3.6-35B-A3B-NVFP4 --served-model-name nvidia/Qwen3.6-35B-A3B-NVFP4
  --trust-remote-code --tp-size 1
  --attention-backend trtllm_mha --moe-runner-backend flashinfer_cutlass
  --kv-cache-dtype fp8_e4m3
  --reasoning-parser qwen3 --dyn-reasoning-parser qwen3 --tool-call-parser qwen3_coder
  --mamba-radix-cache-strategy extra_buffer
  --speculative-algorithm EAGLE --speculative-num-steps 3 --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 4
  --host 0.0.0.0 --port 30000
```

- **No cache-tuning flags are set:** no `--mem-fraction-static`, no `--chunked-prefill-size`, no `--page-size`
  (so page size 1), no `--enable-hierarchical-cache`. The cache discipline is entirely
  `--mamba-radix-cache-strategy extra_buffer` (hybrid/SSM state) + `--kv-cache-dtype fp8_e4m3`.
- **Tuned for:** agentic coding traces — `64k_400_90kv_agent_new_noschedule_short_15perc.jsonl`:
  **64K input, 400 output, 90% KV reuse, concurrency 32, 3,541 requests** (131 expected context-length failures).
- **Measured (p50):**

  | GPU | checkpoint / precision | out tok/s/GPU | tok/s/user | p50 ITL | p50 TTFT |
  |---|---|---|---|---|---|
  | B200 | NVFP4 + FP8 KV | 2,988.50 | 115.81 | 8.93 ms | 286.90 ms |
  | GB200 | NVFP4 + FP8 KV | 3,035.98 | 114.03 | 8.97 ms | **156.07 ms** |
  | H200 | FP8 + BF16 KV | 1,332.03 | 61.90 | 17.32 ms | 360.31 ms |

  (MTP runs with *simulated* acceptance `acc_len=3.3153` — the TTFT/ITL numbers are therefore not
  pure-PD numbers and must not be compared to non-speculative baselines without saying so.)
- **Stability:** `benchmark-only` manifests (published recipe, NVIDIA-maintained) but the surrounding Dynamo
  stack is `production`. Distinguished: the *flags* are a served configuration; the published table is a benchmark.
- **GB10 delta:** GB10 is Blackwell-class, so `trtllm_mha` + NVFP4 + `fp8_e4m3` KV plausibly apply, but
  attention/MoE backends are the most hardware-specific part — fall back to SGLang defaults if
  `trtllm_mha`/`flashinfer_cutlass` are unavailable. Drop EAGLE if the NVFP4 checkpoint ships no draft head.
  **`--mamba-radix-cache-strategy extra_buffer` is the one flag we should copy blindly** — it is the recipe's
  only cache-behaviour choice and it exists because the model is hybrid.

### H. NVIDIA Dynamo — agentic cache policy and measured hit rates
Source: [Full-Stack Optimizations for Agentic Inference with NVIDIA Dynamo, 2026-04-17](https://developer.nvidia.com/blog/full-stack-optimizations-for-agentic-inference-with-nvidia-dynamo/)

Request-side contract (the part a harness controls, not a server flag):

```json
"nvext": {
  "agent_hints": { "osl": 256, "speculative_prefill": true, "priority": 10 },
  "cache_control": { "type": "ephemeral", "ttl": "1h" }
}
```

- **Measured hit rates (quoted):** Claude Code — "after the first API call that writes the conversation prefix
  to KV cache, every subsequent call to the same worker hits **85–97%** cache. Agent teams (or swarms) push
  this further with **97.2% aggregate cache hit rate across 4 Opus teammates**. An **11.7× read/write ratio**".
  Described as a "write-once-read-many (WORM) access pattern".
- **Router requirement:** "Without cache-aware routing, turn 2 of a conversation has a **~1/N chance** of
  landing on the same worker as turn 1" (N = workers). Global KV index (Flash Indexer) → KV-aware placement.
- **Cache tiers:** GPU → CPU → local NVMe → remote storage; `cache_control` pins a prefix on a worker for a TTL
  (only `ephemeral` today, to match Anthropic's API); lifecycle-aware eviction drops ephemeral KV from
  subagent termination / context summarisation.
- **Stability:** `reported-only` for the hit-rate numbers (managed API infrastructure + NVIDIA-internal Codex/
  Claude Code harnesses; no reproducible flag set), `production` for the nvext API contract.
- **Why it matters for us:** 85–97% is only reachable if the prompt is *append-only*. A renderer that rewrites
  the preamble every turn cannot see these numbers regardless of server config — this is the strongest
  published evidence that hit rate is a **prompt-layout** property first, a cache-config property second.

### I. Official benchmark recipes — MLPerf Inference (datacenter, LLM)
Sources: [MLPerf Inference: Datacenter](https://mlcommons.org/benchmarks/inference-datacenter/),
[llama2-70b reference implementation](https://github.com/mlcommons/inference/blob/master/language/llama2-70b/README.md)

Pinned parameters: `--scenario Offline|Server`, `--total-sample-count 24576`, `--mlperf-conf mlperf.conf`,
`--user-conf user.conf`, dataset OpenOrca preprocessed with `--seqlen_limit=1024` and 24,576 samples.

- **What it teaches:** the reproducibility gold standard deliberately measures **cold cache** — 24,576 unique
  prompts, ISL capped at 1024, Server scenario with a TTFT/TPOT latency constraint. There is no prefix-reuse
  dimension in the metric. So MLPerf is *not* a source of cache configurations; it is the reason
  "benchmark number" and "cache hit rate" are not comparable across papers unless both say which they measure.
- **Stability:** `benchmark-only` (by construction).
- **GB10 delta:** none transferable.

### J. Production trace evidence — KVCache in the Wild (USENIX ATC'25)
Source: [arXiv:2506.02634](https://arxiv.org/abs/2506.02634) — characterization at "one of the leading LLM
service providers" (provider anonymised; authors from Shanghai Jiao Tong / Huawei).

- **Findings (quoted/paraphrased):** KV reuses are **skewed across requests**; "reuses between **single-turn
  requests are equally important** as multi-turn requests"; reuse time and probability are diverse globally
  but **predictable per request category**; "the overall cache size required for an ideal cache hit ratio is
  **moderate**"; a workload-aware eviction policy beats LRU under limited capacity.
- **Stability:** `reported-only` — strongest large-scale trace evidence available, but no flag set and no
  reproducible deployment.
- **Why it matters:** "moderate ideal cache size" argues against buying hit rate with a huge HiCache ratio;
  "single-turn reuse matters as much as multi-turn" argues against optimising only conversation sessions.

### K. Hybrid-attention caveat, from the Dynamo recipes index
Source: [recipes/README.md](https://github.com/ai-dynamo/dynamo/blob/main/recipes/README.md)

Recipes enumerate the hybrid models and what they set: Qwen3.5-122B-A10B "Hybrid GDN+MoE, NVFP4 + FP8 KV,
KV-aware routing; **agentic profile**"; Qwen3.8-2.4T-A95B "Hybrid gated-delta-net + 512-expert MoE (262K ctx),
FP8 weights + FP8 KV … KV-aware routing + prefix caching"; GLM-5.3 "B200 HiCache CPU offload"; DeepSeek-V4.1-Flash
vLLM "**prefix-cache retention tuning**". DeepSeek-R1 recipes are WideEP (TP=8/16, 16–32×H200).

- **Stability:** `production` (NVIDIA-maintained, benchmarked per recipe).
- **Why it matters:** on hybrid (GDN/SSM) models every recipe pairs a KV precision choice with a *hybrid-specific*
  radix/state strategy — never a stock radix cache. Our baseline runs a hybrid model with a plain radix cache;
  that is the single largest divergence from every production recipe collected here.

---

## 2. Quantified stability caveats (the failure class we already hit)

1. **`--mem-fraction-static` is a knife-edge, and the floor is computed, not documented.**
   SGLang defines `mem_fraction_static = (model weights + KV pool) / GPU capacity`, and the docs' rule of thumb is
   "reserving **5–8 GB** for activations is typically sufficient" — verify by reading the startup line and checking
   `available_gpu_mem`; 5–8 GB is healthy, 10–20 GB means you under-allocated the KV pool, too low risks OOM
   ([hyperparameter tuning](https://docs.sglang.io/docs/advanced_features/hyperparameter_tuning)). There is **no
   published numeric floor**: it depends on weights, CUDA-graph buffers and activation peaks. Our box reported
   minimum viable **0.4993** against a configured **0.500** — i.e. we were inside the rounding/overhead band, not
   at a documented limit. Production recipes avoid that band entirely: 0.85 for 8×H20 DeepSeek-R1, or **no
   override at all** for the 1×GB200 hybrid recipe (Dynamo G). Lesson for reproduction: either leave the default
   heuristic, or set the fraction high and verify `available_gpu_mem` in 5–8 GB — never hand-pick a value near
   the computed floor.
2. **Scheduler conservativeness has documented thresholds.** `token usage > 0.9` is the health target; frequent
   `token usage < 0.9` with `#queue-req > 0` → decrease `--schedule-conservativeness` to ~0.3; repeated
   `KV cache pool is full. Retract requests.` → increase to ~1.3; **~1 retraction per minute is acceptable**
   (same docs). This is the only published numeric stability envelope we found for SGLang scheduling.
3. **Eviction is leaf-only and cannot pin.** "Eviction only ever considers evictable leaves… the root is never
   evictable… a policy only scores. It does not decide how much to free, and it cannot pin KV in memory — a node
   protected by the policy is still evicted if reclaiming everything else is not enough"
   ([eviction policies](https://docs.sglang.io/docs/advanced_features/radix_eviction_policy)). Session references
   are explicitly "soft protection, not memory pins". So a cache-hit grid that ends at 64 tokens can be a
   *capacity* result, not a matcher result.
4. **Recency synchronisation is the documented agentic eviction cliff.** RR-Evict (arXiv:2609.32278) reports that
   accesses to one agent's cached history refresh its nodes together, so LRU concentrates eviction on a few agents'
   private histories; a returning agent must recompute "nearly its entire accumulated context", producing a large
   TTFT outlier "even if most other requests retain substantial cache reuse". Same symptom class as our missing
   suffix recovery. `reported-only` (paper, not a deployment).
5. **Position-sensitive prompts can void the cache on unchanged content.** Irminsul (arXiv:2605.05696) reports
   operators seeing "cache-hit regressions ranging from moderate slowdowns to severe **TTFT spikes of 10–16 s on
   unchanged content**" when token positions shift between turns. `reported-only`. Design implication: prompt
   layout (stable prefix, append-only delta) is a stability control, not a micro-optimisation.
6. **Page size is a granularity/throughput trade, and our 1 is the odd one out.** Every HiCache recipe pins
   `--page-size 64`; the 1-GPU Dynamo recipe leaves the default (1). Mechanism (inference, not measured here):
   larger pages amortise per-token bookkeeping and I/O, but a reusable suffix shorter than a page cannot be
   matched — so page size bounds the finest suffix a cache can recover. Any page-size experiment must hold the
   grid's token granularity fixed or the comparison is confounded.
7. **Hybrid/SSM models need a hybrid cache strategy.** The only production single-GPU hybrid recipe sets
   `--mamba-radix-cache-strategy extra_buffer`; no recipe runs a GDN/Mamba hybrid on a stock dense radix cache
   (Dynamo G, K). If our suffix recovery gap is architectural, no amount of radix tuning will close it and the
   comparison must be run with the hybrid strategy set.

---

## 3. The five configurations to reproduce first, ranked by stability × informativeness

| # | Configuration | Why this one | Stability | Single-GB10 change |
|---|---|---|---|---|
| 1 | **Dynamo Qwen3.6-35B-A3B SGLang agg (1×GB200)** — `--tp-size 1 --attention-backend trtllm_mha --moe-runner-backend flashinfer_cutlass --kv-cache-dtype fp8_e4m3 --mamba-radix-cache-strategy extra_buffer`, EAGLE 3/1/4, no mem-fraction/chunked-prefill/page-size override | The only published single-GPU, hybrid-MoE, agentic config with a **90% KV-reuse trace and p50 TTFT 156 ms**; identical architecture class to our model, and its published flags are a *served* configuration, not a tuning experiment | `benchmark-only` (manifests) on a `production` stack | Swap backends to whatever SGLang supports on GB10; keep `--mamba-radix-cache-strategy extra_buffer`, drop EAGLE if no draft head. Replay with the same 64K/400/90%-reuse/concurrency-32 shape |
| 2 | **SGLang HiCache DeepSeek-R1 recipe, collapsed to 1 GPU** — `--enable-hierarchical-cache --hicache-ratio 2 --hicache-io-backend kernel --hicache-mem-layout page_first`, storage backend → local file | Tests the hypothesis behind our whole phase: does a host tier recover suffix reuse that GPU-only radix loses? Official recipe, two named production deployments, 6×/80% headline | `production` | Drop `--tp 8`; `--page-size 64` → decide explicitly (keep 1 for a clean single-variable test); `--mem-fraction-static 0.85` → default or 0.9 with `available_gpu_mem` check; `hf3fs` → `HiCacheFile` |
| 3 | **llm-d tiered prefix cache, SGLang arm** — `--enable-hierarchical-cache --hicache-size=<GB per TP rank>` with tier size matched to pod memory and router `lruCapacityPerServer` | Gives the **sizing discipline** (GB per TP rank, not a ratio) from a nightly-validated path, plus the 13.9× @250-user number as an upper-bound claim to falsify on one node | `production` | Single replica → drop the router entirely; `--hicache-size` scaled to host DRAM (e.g. 32–64 GB); keep the tier-size ↔ memory-limit coupling |
| 4 | **SGLang official HiCache ablation (4 arms)** — `--disable-radix-cache` / `--schedule-policy fcfs` / default LPM / `--enable-hierarchical-cache` on `bench_multiturn.py` | Cheapest way to make our 64-token grid comparable to a published harness; tells us whether our plateau is the matcher or the capacity, using the vendor's own stress generator | `benchmark-only` | None — flag-only; use Qwen2.5-14B-Instruct as published, then our model |
| 5 | **vLLM Production Stack + LMCache (20 GB CPU buffer, `enablePrefixCaching: false`)** | Cross-engine control and the strongest signal about **cache ownership**: the reference stack turns the in-engine cache *off* when an external cache is present. If our baseline's behaviour is an artefact of SGLang's radix design, this is where it shows | `production` (config), gain `reported-only` | No K8s: translate values to `vllm serve --kv-transfer-config <LMCache>` with `cpuOffloadingBufferSize: 20`; if the model is unsupported on vLLM-on-GB10, substitute the engine-native `TieringOffloadingSpec` (F) as the control |

**Deliberately not in the first five:** MLPerf (J/I — cold-cache by construction, nothing to reproduce) and the
Dynamo nvext `cache_control` TTL policy (H — a harness contract, not a server flag; worth adopting as prompt-layout
discipline once a config is chosen). KVCache-in-the-Wild (J) is evidence, not a config.

**Cross-cutting recommendation for the next phase:** every config above that runs our model must set the
hybrid/SSM cache strategy before any radix comparison is meaningful (caveat 7) — otherwise "no suffix recovery"
may be measuring an unsupported cache path rather than a cache-capacity limit.

---

## Evidence

- Tool calls used: 32 of 45 (4 misc, 4 `local_web_search` queries, 24 `local_web_crawl` fetches). **0 live model
  requests; no Occamy connection; `.occamy.lock` not taken.**
- Distinct primary sources crawled: 24 (LMSYS/SGLang docs + blog + benchmark README, vLLM docs/blog/production-stack
  repo + helm values + tutorial, llm-d repo + two well-lit-path guides, NVIDIA Dynamo repo + recipes index +
  recipe doc + deploy manifest + technical blog, MLCommons benchmark page + llama2-70b reference README,
  arXiv:2506.02634).
- Configs with exact flags/values recorded: **11** (A1, A2, B, C, D, E, F, G, H, I, K).
- Primary (first-party) sources: **24 of 24**; the two arXiv items are third-party papers and are marked
  `reported-only`.
