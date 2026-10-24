# R-ENG — the other inference engines: cache granularity, cache features, stable configs

> **STALE NOTE — superseded for the model-vs-engine question.** Written 2026-10-21 as offline research:
> **no live requests, no measured cells**. The measured answer is
> [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`, `papers/context-cache/MANUSCRIPT.md` §9b): on one shared
> 32k/71-turn 2x2 the **engine** sets the per-turn uncached bill (**+1,225.18** tokens/turn,
> **2.6738x**, 0.9115 of the 1,344.16 grand mean) and the model main effect is **+275.83** — only
> **+3.61** of it under SGLang, where both checkpoints share the 64-token grid. Read the rest of this
> note as dated background on **flag mechanics**, not as evidence about cost. What remains current: its
> launch-flag descriptions. What is **not** current: any suggestion that the model is the lever.

**Unit:** R-ENG · **Date:** 2026-10-21 · **Mode:** offline literature research, **0 live requests, 0 experiments, no `.occamy.lock`**
**Scope:** every engine that is **not SGLang and not vLLM**. SGLang-native options are `R-SGL`; engine-independent
techniques (LMCache, cache blending, suffix recovery research) are `R-CROSS`. This note answers one question:
*if we benchmark a second serving setup, which cache granularity do we get, and what is the flag that sets it?*

**Evidence discipline.** Every number below is quoted from a **primary source** — the project's own docs/repo,
the paper, or the vendor's own technical blog (vendor blogs are marked `vendor-measured`). No SEO comparison
blog was used. Anything I could not pin is written **`unverified`** rather than guessed.

---

## 0. The headline

**There is no industry-standard KV block size.** The documented defaults across the engines surveyed are
**128 tokens (TensorRT-LLM), 64 (LMDeploy), "not published" (TGI v3)** — and TensorRT-LLM alone lets you build
all the way down to **2 tokens**. Compare our own SGLang deployment: `page_size=1` yet a measured **64-token
hit grid**. So the 64-grid is *not* a property of "LLM serving" and not a property of paged KV at all — it is
a property of **our** stack. That is the single most useful thing in this note.

> **Hypothesis (mine, untested, cheap to falsify):** the 64-token grid on our deployment is imposed by the
> **hybrid-attention (mamba/linear-layer) state cache**, not by paged KV — `uses_mamba_radix_cache=true` and
> `max_mamba_cache_size=64` are the only 64-shaped knobs in that config while `page_size=1` is 1-shaped.
> Decisive test (not run here): serve a *dense* model on the same SGLang deployment and re-measure the grid.
> If the grid collapses to 1 or 16, the 64 is the hybrid path; if it stays 64, it is the radix/scheduler.
> This matters because it predicts that **on a hybrid-attention model, no engine will give sub-64 reuse
> unless it also manages the linear-attention state at that granularity** — which is exactly why TRT-LLM's
> 2-token blocks may *not* transfer to our model.

---

## 1. Cache mechanics, per engine

| Engine | Cache granularity | What determines it | Cache features |
|---|---|---|---|
| **TensorRT-LLM** | **block = `tokens_per_block`, default 128**; power of 2; **build-time** (`trtllm-build --tokens_per_block 32`). NVIDIA's own blog: blocks "adjustable from 64 down to 2 tokens". Only **full** blocks are shareable. | build-time engine parameter, not a serve-time flag | prefix reuse via **radix search tree** over filled blocks; LRU + prioritised eviction; **host offload** (`--kv_host_cache_bytes`, pinned, "negligible cost on Grace-Hopper"); **KV cache early reuse** (reuse a system prompt *while it is still being generated*); disagg serving; KV-cache connector/compression; sliding-window & **cyclic KV** for long context |
| **LMDeploy (TurboMind)** | **block = `cache_block_seq_len`, default 64** (docs table/`messages.py`); doc example config.ini shows 128 for a llama2 build. Reuse granularity **is exactly one block**: "if the identical prompt prefix is less than one block … there will be no improvement". | `cache_block_seq_len` + KV budget `cache_max_entry_count` (default **0.8** of *free* memory) | paged attention; **prefix caching is OFF by default** (`enable_prefix_caching=False`, both `config.ini` docs and `messages.py`); int4/int8 KV (`quant_policy=4/8`), **TurboQuant** K4V2 (`42`), FP8 MLA (`16`); no hierarchical/offload documented |
| **TGI v3** | block-paged (vLLM-derived PagedAttention kernels); **block size not published** → `unverified` | internal; no user knob | **prefix caching on by default, "zero config"** — docs say "Remove all the flags you are using"; chunking; radix-style prefix lookup "~6 µs"; speculation (Medusa/ngram); **long-term KV retention explicitly listed as future work** |
| **DeepSpeed-FastGen / MII** | **none** — no cross-request reuse; Dynamic SplitFuse chunks a prompt into pieces *within* a request and fuses them with decode tokens each iteration | scheduler chunk size, not a cache parameter | **no prefix cache, no offload, no shared prefix** documented; every new request re-prefills |
| **NVIDIA Dynamo** | **inherits the backend's block size** (routes on KV block/prefix identity) | backend + router config | KV-aware **Smart Router**, Distributed **KV Cache Manager** (offload to CPU / local SSD / network object store, "up to petabytes"), NIXL transfer, disaggregated prefill/decode, Planner autoscaling |
| **llama.cpp / Ollama** | **no blocks** — one contiguous KV per slot; **`--cache-reuse N`** reuses ≥N-token chunks via **KV shifting** (token-level, *not* block-aligned) | `-c` context, `-np` slots, `--cache-reuse N` | disk prompt cache (`--prompt-cache*`), **KV quant** `-ctk/-ctv` (f16 default; q8_0/q4_0/… allowed), context shift; slots do **not** share prefixes |

---

## 2. Stable configuration + strongest measured claim + GB10 verdict, per engine

### 2.1 TensorRT-LLM — the only engine with sub-64 granularity

- **Ships as recommended:** `trtllm-build --use_paged_context_fmha enable` (required for reuse) → `trtllm-serve`.
  In-flight batching ("continuous batching") is the default scheduler; `max_batch_size` sized high at build,
  tuned at runtime; `max_num_tokens` **defaults to 8192** (since v0.11) and is *the* throughput knob;
  `max_seq_len` defaults to `max_position_embeddings` and should not be tuned. KV memory: if neither
  `maxTokens` nor `freeGpuMemoryFraction` is given, **90 % of remaining free GPU memory** goes to KV;
  `--kv_cache_free_gpu_memory_fraction` overrides it (NVIDIA's own DeepSeek-V3 example uses `0.95`).
- **KV reuse is ON by default** (`enableBlockReuse=true` in `KvCacheConfig`; `--enable_kv_cache_reuse true` in
  Triton/gptManager). Two hard limits worth knowing: reuse only becomes possible **after the producing request
  terminates**, and blocks are evicted **LRU** as soon as a new request needs memory — so a burst of
  same-system-prompt requests at high batch size can see *no* reuse.
- **Chunked context:** expressed as the `max_num_tokens` budget under IFB. The older build-time switch is
  `--enable_chunked_context`; the 1.x `trtllm-serve` CLI does not expose a chunking flag (grep of the CLI page:
  0 hits) → **the exact 1.x flag name is `unverified`**.
- **Spec decode:** EAGLE-3 (`max_draft_len`, linear chain or dynamic tree) and MTP; draft checkpoints published
  for Llama 3/4, gpt-oss-120b, **Qwen3**. No speedup number pinned in the docs → `unverified`.
- **Strongest measured claim:** **up to 5× faster TTFT** by reusing a system prompt *while it is still being
  generated* (concurrent-user burst) — `vendor-measured`; and **up to 7 % TTFT** improvement from shrinking
  blocks from 64 → 2 tokens on H100 / Llama-70B. Sources:
  [KV cache reuse](https://nvidia.github.io/TensorRT-LLM/advanced/kv-cache-reuse.html),
  [5× early reuse blog](https://developer.nvidia.com/blog/5x-faster-time-to-first-token-with-nvidia-tensorrt-llm-kv-cache-early-reuse/).
- **GB10 single node:** `needs-restart` — it runs as one process on one node, **but the granularity knob is
  build-time**, so every block-size experiment costs a re-engine + restart. GB10 is Grace-Blackwell/arm64;
  TRT-LLM ships SBSA containers, but **support for a hybrid-attention MoE (Qwen3.5-MoE) is `unverified`** —
  the docs cover sliding-window/cyclic KV, not mamba/linear layers.
- **First flag to change:** **`tokens_per_block` 128 → 2** (rebuild). This is the direct test of whether a
  non-64 grid changes the hit curve.

### 2.2 LMDeploy — same 64-grid as us, but with the cache *off*

- **Ships as recommended:** TurboMind engine, `cache_block_seq_len=64`, `cache_max_entry_count=0.8`
  (fraction of *free* memory since v0.2.1), `cache_chunk_size=-1`, `max_batch_size=64` (2.x default).
  **`enable_prefix_caching` defaults to `False`** in both the `config.ini` doc and `TurbomindEngineConfig` —
  i.e. the project's own default is *no prefix reuse*. This is the single biggest config difference from us.
- **Granularity, quoted:** the docs are explicit that block length *is* the reuse quantum: *"Since k/v block
  is the smallest granularity for reuse in prefix caching, if the identical prompt prefix is less than one
  block (prefix length < cache_block_seq_len), there will be no improvement in inference performance."*
- **KV quant:** `quant_policy=4` (int4) / `8` (int8) / `42` (TurboQuant K4V2) / `16` (FP8 MLA, PyTorch only).
- **Strongest measured claim:** int8 KV ≈ **+27 % RPS**, int4 ≈ **+39 %** on llama2-7b (tp1, bs256, 10 000
  prompts, `benchmark/profile_throughput.py`); TurboQuant on **Qwen3-30B-A3B** (H200, ShareGPT, concurrency 64,
  5 000 req) holds **2 195.8 tok/s vs 2 368.8 baseline (−7.3 %)** at **~5× smaller KV**. Repo changelog also
  claims **1.5× vLLM on H800 for gpt-oss** (MXFP4, `vendor-measured`). Sources:
  [TurboMind config](https://lmdeploy.readthedocs.io/en/latest/inference/turbomind_config.html),
  [KV quant](https://lmdeploy.readthedocs.io/en/latest/quantization/kv_quant.html),
  [README](https://github.com/InternLM/lmdeploy).
- **GB10 single node:** `unverified` — LMDeploy's documented GPU matrix for its quant kernels stops at
  **Hopper (sm90)**; GB10/sm_121 is not listed, and TurboMind ships prebuilt CUDA kernels, so this is a
  source-build risk, not a model-support statement. Qwen3.5 (0.8B–397B) **is** in LMDeploy's supported-model
  table for both TurboMind and PyTorch engines.
- **First flag to change:** **`--enable-prefix-caching True`** (turn the feature on at all), then
  `cache_block_seq_len` 64 → 32/128 to move the grid.

### 2.3 TGI v3 — best measured caching claim, worst model fit for us

- **Ships as recommended:** *nothing*. TGI v3's documented production config is "**zero config**": "Remove all
  the flags you are using … In production, we don't have any flags anymore in our deployments." Defaults that
  still exist: `--max-concurrent-requests 128`; `--max-batch-prefill-tokens` defaults to
  `max_input_tokens + 50`; `--max-input-tokens` defaults to `min(max_allocatable, max_position_embeddings) − 1`.
- **Cache:** prefix caching is always on (no launcher flag exists — grep of the launcher reference: 0 hits);
  chunking is automatic. **Block size is not published** → `unverified`.
- **Strongest measured claim:** **13×** on long prompts — 8×H100, Llama-3.1-70B, 20 requests / 200 k prompt
  tokens, 2nd run (prefix cache warm): **2.0 s vs vLLM 27.5 s**; a single L4 (24 GB) holds **30 k tokens** on
  Llama-3.1-8B vs vLLM's ~10 k. Their own caveats: constrained KV cache causes contention, and replicas need
  sticky sessions or the cache misses. Source:
  [TGI v3 overview](https://huggingface.co/docs/text-generation-inference/en/conceptual/chunking).
- **GB10 single node:** `not-supported-for-this-model` — TGI serves a curated model list; a hybrid-attention
  MoE in our class is not in it (TGI has a Mamba path, but for Mamba/Mistral-class models, not this one).
- **First flag to change:** there is none for caching; the only lever on retention is **`--max-batch-total-tokens`**
  (the KV budget). Worth stating plainly: TGI is a *result* to cite, not a setup we can reproduce on our model.

### 2.4 DeepSpeed-FastGen / DeepSpeed-MII — no cache to compare

- **Design:** Dynamic SplitFuse splits a prompt into chunks and composes each iteration's batch from
  *prompt chunks + decode tokens*, so prefill work is amortised and never idle. That is a **scheduling** trick,
  not a cache: the KV state of a finished request is not preserved for the next one, and no shared-prefix or
  offload path is documented.
- **Strongest measured claim:** **up to 2.3× effective throughput, 2× lower average latency, up to 3.7× lower
  tail latency vs vLLM** — [arXiv 2401.08671](https://arxiv.org/abs/2401.08671) (DeepSpeed-FastGen, 2024).
- **GB10 single node:** `not-supported-for-this-model` — DeepSpeed-Inference targets dense transformer kernels;
  no hybrid-attention/MoE serving path is documented. **Also relevant:** with no prefix reuse, FastGen would
  score *worse* than our baseline on any repeated-prefix workload, so benchmarking it would produce a
  predictable, uninformative result.
- **First flag to change:** none exists — that is the finding.

### 2.5 NVIDIA Dynamo — a routing layer, not an engine (say it clearly)

- **What it is:** "Disaggregated serving, **KV-aware routing**, cache management, and autoscaling" across
  **vLLM, SGLang, TensorRT-LLM** backends. Four components: Planner, **Smart Router** (KV-cache-aware request
  routing), **Distributed KV Cache Manager** (offload to CPU / local storage / networked object store, "up to
  petabytes"), and **NIXL** for transfer.
- **Strongest measured claim:** **up to 30× more requests served** on DeepSeek-R1 671B on **GB200 NVL72** with
  disaggregated serving, and **>2× throughput** for Llama-70B on Hopper — `vendor-measured`
  ([Dynamo blog](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/),
  [docs](https://docs.nvidia.com/dynamo/)).
- **Granularity:** whatever the backend uses; the router keys on KV block/prefix identity, so it **cannot
  recover the suffix** any more than the backend can.
- **GB10 single node:** `needs-cluster` — the measured wins are disaggregation on NVL72-class racks; on one
  node with one replica the KV-aware router has nothing to route between. It becomes interesting only if we
  ever run 2+ replicas, and then only for the router/offload layer, not for cache granularity.
- **First flag to change:** router mode (`--router-mode kv` / `DYN_ROUTER_MODE`) — `unverified` exact spelling.

### 2.6 llama.cpp / Ollama-class — scope-out for throughput, but the one non-block-aligned cache

- **Why it is out of scope for benchmarking:** no paged KV, no per-request block table, `-np` slots split one
  contiguous KV buffer and **do not share prefixes across slots**; throughput claims are not comparable to a
  paged-attention server. Ollama is a llama.cpp runtime and inherits all of the above.
- **Why it is still interesting (and cheap):** **`--cache-reuse N`** — "min chunk size to attempt reusing from
  the cache via **KV shifting**, requires prompt caching to be enabled (**default: 0**)". That is **token-level,
  not block-aligned** reuse: the one mechanism in this survey that does not quantise reuse to a power of two.
  KV quant types are `-ctk/-ctv` (default **f16**; `q8_0`, `q4_0`, `q4_1`, `iq4_nl`, `q5_0`, `q5_1` allowed).
  Source: [llama.cpp server flags](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).
- **Measured claim:** none that transfers — no primary throughput number for our model class. `unverified`.
- **GB10 single node:** `unverified` — builds anywhere, but GGUF conversion of a 397B-class hybrid-attention MoE
  is the blocker, and there is no paged KV to measure.
- **First flag to change:** `--cache-reuse 256` (from 0) plus `-ctk q8_0`.

### 2.7 Engines with a genuinely different cache *granularity*

| Granularity | Engine | Why it matters to our 64-grid |
|---|---|---|
| **2 tokens** (configurable 64→2) | TensorRT-LLM | the only engine that can put a reuse boundary *inside* a 64-block; NVIDIA measures 7 % TTFT from exactly this on Llama-70B |
| **1 token / arbitrary chunk** | llama.cpp `--cache-reuse N` + KV shifting | reuses a partial prefix chunk; the cheapest possible falsification of "no suffix recovery anywhere" |
| **64 tokens** | LMDeploy (default), SGLang (ours, measured) | the coincidence worth explaining — two independent engines landing on 64 suggests a hardware/kernel sweet spot, not a law |
| **16 tokens** (reference only, out of scope) | vLLM / TGI-class paged kernels | the field's *modal* default; if a 16-block engine still shows a 64-grid on our model, the grid is the hybrid path, not the pager |

---

## 3. The three non-SGLang setups that are both stable AND informative to benchmark first

Ranked by *information per unit of risk*. All three are single-node; none needs Occamy; none needs a cluster.

### #1 — TensorRT-LLM, `tokens_per_block` 128 → 2 → 16 (same engine, three builds)
**Why:** it is the only way to vary the reuse quantum *below* 64 without changing engines, so it isolates
granularity as the independent variable. If the hit curve moves off the 64-grid, our SGLang number is an
implementation artifact; if it does not move, the grid is imposed by the model's hybrid attention and every
engine will show it. **Stable config:** `--use_paged_context_fmha enable`, IFB default, `max_num_tokens 8192`,
KV fraction 0.9, `enableBlockReuse` default true. **Cost:** 3 engine builds + restarts. **Risk:** arm64/SBSA
container and Qwen3.5-MoE support are both `unverified` — this is the highest-information *and* highest-setup-risk
option, which is why it is #1 rather than a free win.

### #2 — LMDeploy TurboMind, `enable_prefix_caching=true`, `cache_block_seq_len=64`
**Why:** it is the **cheapest true A/B on the same 64-token quantum**: prefix caching OFF by default, so one
flag flips the deployment from "no cross-request reuse" to "64-block reuse", and the docs state the reuse
quantum *is* the block. It gives us a second engine with our exact grid — the control that tells us whether
64 is generic. **Stable config:** `cache_block_seq_len=64`, `cache_max_entry_count=0.8`, `max_batch_size=64`.
**Cost:** one process. **Risk:** TurboMind's documented kernel matrix stops at sm90; GB10 needs a source build.

### #3 — llama.cpp `--cache-reuse 256` on a short-context slice
**Why:** it is the **falsification test**, not a throughput comparison. Every other engine in this note
quantises reuse; llama.cpp's KV shifting does not. If a mid-context edit can be recovered by reusing a
chunk that is *not* a multiple of 64, then "no suffix-recovery capability" is a statement about our SGLang
config, not about the field — and the next SGLang tuning step becomes obvious. **Cost:** minutes, CPU or GPU.
**Risk:** GGUF conversion of the hybrid MoE; treat a failure to convert as `unverified`, not as a negative result.

**Deliberately not in the top three:** TGI (strongest number — 13× — but our model is not in its supported
list, so we would be benchmarking a different model, not a different cache); FastGen/MII (no cache, predictable
loss on repeated-prefix traffic); Dynamo (needs a cluster to show its claim; it is a router, and it inherits
whatever granularity the backend has).

---

## 4. What I could not verify (do not cite these as fact)

1. **TGI v3 block size.** Not published in the docs; the PagedAttention page only says it reuses vLLM's kernels.
   Any "TGI uses 16-token blocks" statement is an inference from vLLM, not a TGI fact.
2. **TensorRT-LLM's 1.x chunked-prefill flag name.** `trtllm-serve --help` docs show no chunking flag; the 0.x
   `--enable_chunked_context` is documented but I could not confirm its 1.x replacement.
3. **TRT-LLM speculative-decoding speedup.** The docs describe EAGLE-3/MTP and the draft checkpoints (including
   Qwen3) but publish no speedup number.
4. **Arch (arm64/GB10) wheel availability** for TRT-LLM, LMDeploy, TGI. "Ships SBSA containers" / "kernel matrix
   stops at sm90" are inferences from documented support matrices, not from an arm64 install attempt.
5. **Qwen3.5-MoE hybrid-attention support** in any of these engines. LMDeploy's table lists "Qwen3.5
   (0.8B–397B)" and TRT-LLM documents sliding-window/cyclic KV, but **no vendor documents our exact
   hybrid-attention MoE variant** — hence the `unverified` runnability value below rather than a guess.
6. **Absence of prefix caching in FastGen/MII** is an absence-of-evidence claim from the paper + MII docs,
   not a line of code I read.

## 5. Sources (all primary; vendor blogs marked in §2)

1. TensorRT-LLM — [KV cache reuse](https://nvidia.github.io/TensorRT-LLM/advanced/kv-cache-reuse.html) (block default 128, `--tokens_per_block`, offload, LRU)
2. TensorRT-LLM — [KV Cache System](https://nvidia.github.io/TensorRT-LLM/latest/features/kvcache.html)
3. TensorRT-LLM — [Memory usage / free fraction](https://nvidia.github.io/TensorRT-LLM/reference/memory.html) (90 % default)
4. TensorRT-LLM — [Paged attention + in-flight batching scheduler](https://nvidia.github.io/TensorRT-LLM/latest/features/paged-attention-ifb-scheduler.html) (`max_num_tokens` 8192)
5. TensorRT-LLM — [Speculative decoding](https://nvidia.github.io/TensorRT-LLM/latest/features/speculative-decoding.html)
6. TensorRT-LLM — [trtllm-serve CLI](https://nvidia.github.io/TensorRT-LLM/commands/trtllm-serve.html)
7. NVIDIA — [5× faster TTFT with KV cache early reuse](https://developer.nvidia.com/blog/5x-faster-time-to-first-token-with-nvidia-tensorrt-llm-kv-cache-early-reuse/) (blocks 64→2, 7 %)
8. LMDeploy — [TurboMind config](https://lmdeploy.readthedocs.io/en/latest/inference/turbomind_config.html) (block 128 example, prefix caching default False, `cache_max_entry_count`)
9. LMDeploy — [INT4/INT8 KV cache](https://lmdeploy.readthedocs.io/en/latest/quantization/kv_quant.html) (+27 %/+39 % RPS, TurboQuant)
10. LMDeploy — [`lmdeploy/messages.py`](https://github.com/InternLM/lmdeploy/blob/main/lmdeploy/messages.py) (`cache_block_seq_len=64`, `enable_prefix_caching=False`)
11. LMDeploy — [supported models](https://lmdeploy.readthedocs.io/en/latest/supported_models/supported_models.html) (Qwen3.5 listed)
12. LMDeploy — [pipeline / KV budget history](https://lmdeploy.readthedocs.io/en/latest/llm/pipeline.html) (`cache_max_entry_count` 0.8)
13. TGI — [v3 overview: caching & chunking](https://huggingface.co/docs/text-generation-inference/en/conceptual/chunking) (13×, zero config, 30 k on L4)
14. TGI — [launcher reference](https://huggingface.co/docs/text-generation-inference/en/reference/launcher) (`max-batch-prefill-tokens`, 128 concurrent)
15. TGI — [PagedAttention](https://huggingface.co/docs/text-generation-inference/en/conceptual/paged_attention)
16. DeepSpeed — [FastGen, arXiv 2401.08671](https://arxiv.org/abs/2401.08671) (2.3× / 2× / 3.7×)
17. NVIDIA — [Dynamo announcement](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/) (30×)
18. NVIDIA — [Dynamo docs](https://docs.nvidia.com/dynamo/) (KV-aware routing, cache management)
19. llama.cpp — [server flags](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) (`--cache-reuse`, `-ctk/-ctv`)

*No SEO comparison blog was used. The SearXNG instance returned heavy bing spam (Walgreens, restaurant
listings) alongside the yep/google results; every fact above was re-fetched from the primary URL itself.*
