# vLLM + LMCache / Mooncake — serving and cache options, and what they claim

> **STALE NOTE — superseded for the model-vs-engine question.** Written 2026-10-21 as offline research:
> **no live requests, no measured cells**. The measured answer is
> [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`, `papers/context-cache/MANUSCRIPT.md` §9b): on one shared
> 32k/71-turn 2x2 the **engine** sets the per-turn uncached bill (**+1,225.18** tokens/turn,
> **2.6738x**, 0.9115 of the 1,344.16 grand mean) and the model main effect is **+275.83** — only
> **+3.61** of it under SGLang, where both checkpoints share the 64-token grid. Read the rest of this
> note as dated background on **flag mechanics**, not as evidence about cost. What remains current: its
> launch-flag descriptions. What is **not** current: any suggestion that the model is the lever.

**Unit:** R-VLLM · **Mode:** offline web research, no experiments, no contact with the Occamy server
· **Baseline it must be comparable to:** SGLang, Qwen3.5-MoE hybrid attention, `page_size=1`, plain radix
cache, no hierarchical cache, `chunked_prefill_size=8192`, cache hits recorded on a **64-token grid**.

Every row below names the exact flag, the mechanism, and one *measured* number with its workload. Where the
upstream docs give no number, the row says so instead of inventing one. Vendor blog numbers are labelled
vendor. Everything was read from primary sources (upstream docs in the repo, upstream config source, paper
abstracts/README) — no summary sites.

---

## 1. Options table

| # | Option | Exact flag / config key | What it changes mechanically | Strongest measured claim (number + workload) | Source | Single-node, single-GPU | Risk / cost |
|---|---|---|---|---|---|---|---|
| 1 | **vLLM automatic prefix caching (APC)** | `--enable-prefix-caching` (on by default in V1: `enable_prefix_caching: bool = True`); `--prefix-caching-hash-algo {sha256,sha256_cbor,xxhash,xxhash_cbor}` (default `sha256`) | KV cache is cut into blocks of `--block-size` tokens; each block is keyed by `hash(parent_hash, block_tokens, extra_hashes)` — a *chained* hash, so a block is reusable only if its whole prefix is identical. **Only full blocks are cached**; eviction is LRU over a free-block queue, and blocks of a finished request are queued newest-first so the last (most specific) block dies first. | No number in the docs — the doc's own claim is qualitative ("almost a free lunch", "does not reduce performance", and it explicitly **cannot** help decode-heavy or non-shared-prefix workloads). Treat 15× (row 4) as the measured upper bound for the same mechanism when a tier is added. | `docs/features/automatic_prefix_caching.md`, `docs/design/prefix_caching.md`, `vllm/config/cache.py` (vLLM main) | **yes** | Boot flag; changes output *scheduling*, not logits. Hash is per-deployment (pickle-based `sha256` is not reproducible across vLLM versions — use `sha256_cbor` if the benchmark must be replayable). |
| 2 | **Block size / hit granularity** (the comparison point) | `--block-size` (**`DEFAULT_BLOCK_SIZE = 16`** in `CacheConfig`); `--prefix-match-unit N` (finest token boundary a prefix-cache hit may land on; defaults to the gcd of the prefix-cacheable groups' block sizes); `--enable-mamba-shared-prefix-checkpoint` | Sets the *matching* grid, independent of storage. `prefix_match_unit` can be **finer than the physical block** ("e.g. 32 vs a 1024-token hybrid-model block") as long as every group's block size is divisible by it; `cache_hit_alignment_tokens` records where hits actually land (`hash_block_size` with partial hits, else the scheduler block size). For hybrid Mamba/attention models the Mamba state is only stored on the Mamba block grid, so a hit can normally resume only at a block boundary — the shared-prefix checkpoint lifts that to the shared-prefix junction. | Not a performance claim; it is the knob that determines whether our 64-token law is even expressible (see §2). | `vllm/config/cache.py` (`block_size`, `prefix_match_unit`, `hash_block_size`, `cache_hit_alignment_tokens`), `docs/features/automatic_prefix_caching.md` ("Hybrid Mamba models", which uses `--prefix-match-unit 64` and calls 64 "a reasonable starting point") | **yes** | Must divide every KV-cache group's block size (validated at startup, error names the offending sizes). On a hybrid model the *physical* block can be ~1024 tokens, so `--prefix-match-unit` is not optional if you want sub-block reuse. |
| 3 | **KV connector / KV transfer** | `--kv-transfer-config '{"kv_connector":"<name>","kv_role":"kv_both","kv_connector_extra_config":{...}}'`; 9 connector types in the current docs: `ExampleConnector`, `LMCacheConnectorV1`, `LMCacheMPConnector`, `NixlConnector` (UCX/GDS backends), `MooncakeConnector`, `MoRIIOConnector` (ROCm), `MultiConnector`, `OffloadingConnector`, `FlexKVConnectorV1` | Splits the engine into *kv producer* and *kv consumer*: the connector moves KV blocks between instances, or to a storage tier, instead of recomputing them. Abstractions: `Connector`, `LookupBuffer` (`insert` non-blocking / `drop_select` blocking), `Pipe` (`send_tensor`/`recv_tensor`). Scheduler-side and worker-side connectors run in different processes; transfer is layer-by-layer. | No throughput number (this is plumbing). Its one hard claim is a **negative** one, stated in the docs: "Disaggregated prefill **DOES NOT** improve throughput." | `docs/features/disagg_prefill.md` (vLLM main) | **needs-restart** (boot-time config; single-process `OffloadingConnector` does work on one GPU) | Extra process/sidecar, a second failure domain, and a transfer path that must beat recompute — on a single GPU there is nothing to transfer between, so only the offload flavour is meaningful. |
| 4 | **LMCache** | `--kv-transfer-config '{"kv_connector":"LMCacheConnectorV1",...}'` (NIXL underneath) or the standalone server `LMCacheMPConnector`; new in-engine offload path `--kv-offloading-backend lmcache --kv-offloading-size <GiB>` (`KVOffloadingBackend = Literal["native","lmcache"]`); `pip install lmcache` | Extracts KV out of the engine into a **tiered store** — GPU → CPU RAM → local SSD → remote (Redis/Valkey, Mooncake, InfiniStore, S3-compatible, NIXL, GDS) — and reuses it across queries *and across engine instances*. Adds non-prefix reuse (CacheBlend: reuse cached blocks at any position, selectively recompute) and a pluggable `SERDE` interface for compression / token dropping. Engine-independent daemon: cache survives engine crashes. | **"up to 15× improvement in throughput"** with vLLM across multi-round question answering and document analysis. Same paper's enterprise observation: **context truncation halves the prefix-cache hit ratio**. | [arXiv:2510.09665](https://arxiv.org/abs/2510.09665); `github.com/LMCache/LMCache` README | **needs-restart** for CPU tier; **needs-extra-storage-layer** for disk/remote tier | Capacity is no longer free: the tier is a real memory/IO budget and the miss path is now a *read* (an independent SSD characterisation reports warm TTFT 27 ms → 93 ms when `O_DIRECT` makes the read cost explicit — [arXiv:2610.21249](https://arxiv.org/abs/2610.21249)). Token-dropping/compression is lossy unless using CacheBlend's recompute. |
| 5 | **Mooncake** | In vLLM: `MooncakeConnector` (P/D transfer) and `MooncakeStoreConnector` (shared pool); installed from PyPI as `pip install mooncake-transfer-engine` (CUDA-versioned wheels) | A **KVCache-centric disaggregated architecture**, not a flag: separate prefill and decode clusters + a disaggregated cache pool built from the cluster's otherwise-idle CPU/DRAM/SSD; a KVCache-aware scheduler that maximises effective throughput subject to SLOs, plus prediction-based early rejection under overload. Two reusable pieces: **Transfer Engine** (unified batched data movement over TCP/RDMA/NVLink/EFA/NVMe-oF/…, multi-NIC aggregation, topology-aware paths) and **Mooncake Store** (distributed KV/weight store with replication + eviction). | **"up to a 525% increase in throughput in certain simulated scenarios while adhering to SLOs"**, and **"75% more requests"** under real Kimi workloads ([arXiv:2407.00079](https://arxiv.org/abs/2407.00079)); the ACM TOS version reports 59%–498% effective request capacity and +115%/+107% requests on A800/H800. Transfer Engine: **87 GB/s** on 4×200 Gbps RoCE and **190 GB/s** on 8×400 Gbps (2.4× / 4.6× TCP) moving 40 GB ≈ the KV of 128k tokens on LLaMA3-70B. FAST'25 **Best Paper** ("Trading More Storage for Less Computation", pp. 155–170). | `github.com/kvcache-ai/Mooncake` README; arXiv abstract; `docs.vllm.ai` disagg connectors | **needs-multi-node** for the architecture; **needs-extra-storage-layer** for Mooncake Store. The *connector* alone can be pinned on one node, but there is nothing to disaggregate there. | Whole-system change: needs a real fabric (RDMA) and a store deployment to show its numbers. On one GPU the measurable part is only "Mooncake Store as an L2 tier behind LMCache" — i.e. row 4 with a heavier backend. |
| 6 | **Disaggregated prefill/decode (vLLM)** | 2 vLLM instances + `--kv-transfer-config` with a P/D connector; the docs' usage example drives it through `kv_transfer_params` (`do_remote_decode` / `do_remote_prefill`); optional `prompt_token_ids` reuse to skip double tokenisation | Physically separates the compute-bound prefill from the memory-bound decode so `tp`/`pp` can be tuned for TTFT without touching ITL, and tail ITL stops being polluted by prefill insertions. **Cache economics:** it does *not* create cache reuse — it spends KV-transfer bandwidth to buy latency isolation, and the decode side now holds blocks it did not compute. | Docs: "**DOES NOT improve throughput**" (the honest claim). Where it was measured: llm-d reports **up to 70% higher tokens/sec** vs standard vLLM (GPT-OSS on B200, AWS) and **10–30%** on identical MI300X infrastructure (GPT-OSS-120B, Llama-3.3-70B, Oracle) — vendor benchmarks. | `docs/features/disagg_prefill.md`; `github.com/llm-d/llm-d` README (performance highlights) | **needs-multi-node** (two engines) | Doubles the deployment surface; the transfer must beat recompute; the docs themselves call the feature **experimental**. |
| 7 | **Prefix-aware / KV-aware routing** | vLLM Production Stack router: *prefix-aware routing* (same prefix → same instance, even if the cache was evicted) and *KV cache aware routing* (route to the instance with the highest KV-cache hit rate, using per-instance cache state / LMCache `instanceId`); llm-d: Gateway API Inference Extension endpoint-picker with prefix-cache + load-aware scoring, plus predicted-latency scheduling | Turns the prefix cache from a per-instance property into a *fleet* property: the router has to know which replica holds which blocks, so it needs KV events or a shared index. Difference that matters: prefix-aware is sticky and can pin to an evicted cache; KV-aware scores actual hit rate and degrades to load balancing when nothing matches. | llm-d: **3× higher output throughput and 2× faster TTFT** with prefix-cache-aware routing vs round-robin — Llama 3.1 70B on 4× AMD MI300X (Tesla / Red Hat); **13.9× throughput** with hierarchical KV offloading at 250 concurrent users on 4× H100; **40% lower TTFT and ITL** with predicted-latency scheduling. All vendor benchmarks. | `docs.vllm.ai/projects/production-stack/.../kv-cache-aware-routing`, `.../prefix-aware-routing`; `github.com/llm-d/llm-d` README | **needs-multi-node** (≥2 instances; the router itself is a pod) | Only pays off with skewed, repeated prefixes; a bad router is worse than round-robin. Requires a cache index / KV event stream, i.e. another moving part. AIBrix's equivalent was **not verified** in this unit (search budget; flagged gap). |
| 8 | **Speculative decoding** | `--speculative-config '{"method":"eagle3"\|"ngram"\|"suffix"\|"mtp"\|"draft_model"\|\"dard\"..., "model":..., "num_speculative_tokens":N}'`; `ngram` also takes `prompt_lookup_min/max` (default 5/5), `suffix` takes `suffix_decoding_max_tree_depth` (24) etc. | Adds a drafter that proposes N tokens and a verifier that accepts a prefix of them. **KV footprint:** each verified step holds KV for the *proposed* tokens too, so transient KV per sequence grows roughly by `num_speculative_tokens`; the block table stays append-only, and rejected tokens are truncated, not cached. **Reuse:** APC still keys on exact block hashes, so speculation does not change *which* blocks hit — it changes how many tokens one forward pass covers, which is why acceptance length, not hit rate, moves TTFT. | Docs give **no number** — only a qualitative Low/Medium/High table (EAGLE and MTP "high gain" at low QPS; ngram "medium gain" at high QPS). Vendor blog claims **up to 2× longer acceptance length vs EAGLE 3** on long-context workloads (EAGLE 3.1, vllm.ai, 2026-05-26) — *not independently verified here*. | `docs/features/speculative_decoding/README.md` (vLLM main); vllm.ai EAGLE-3.1 post (vendor, unverified) | **yes** (`ngram` needs no extra model and no extra VRAM; `eagle3`/`mtp` need a head or native MTP support) | Drafter costs VRAM and can *lose* at high QPS (docs say ngram/suffix are the high-QPS-safe options); lossless only for the standard rejection sampler (FLy is lossy). If cache measurement uses TTFT, speculation confounds it. |
| 9 | **Chunked prefill** | `--max-num-batched-tokens N` (chunked prefill itself is **on by default in V1 "whenever possible"**); `--enable-chunked-prefill` remains in older versions | Splits a long prefill across scheduler steps and co-batches the chunks with decodes; decodes are scheduled first. **Interaction with APC:** chunking changes *when* a block becomes full, not the key — a block is only inserted into the cache table once it is full, so a chunk boundary inside a block delays that block's availability by at most one step; the hit grid is still `block_size`/`prefix_match_unit`. | Docs: no throughput number, but concrete tuning guidance — smaller `max_num_batched_tokens` (e.g. 2048) → better ITL; larger → better TTFT; **"> 8192" recommended for optimal throughput** on small models / large GPUs. | `docs/configuration/optimization.md` ("Chunked Prefill") | **yes** | Our baseline already runs 8192, so this is the one knob that is already matched — keep it fixed when comparing grids, or the comparison measures scheduling instead of caching. |

---

## 2. The block-size contrast (why this is the load-bearing difference)

| | SGLang baseline (ours) | vLLM V1, default | vLLM, matched arm |
|---|---|---|---|
| Storage unit | `page_size=1` token pages under a radix tree | KV blocks of `block_size` tokens; **default 16** | `--block-size 64` |
| Match unit (where a hit can land) | measured empirically to be a **64-token grid** | 16 tokens (block hash); only **full** blocks are reusable | 64 tokens via `--block-size 64`, or `--prefix-match-unit 64` when the physical block is coarser |
| Key | radix path over tokens | `sha256(parent_hash ‖ block_tokens ‖ extra_hashes)`, chained | same |
| Hybrid attention (our model) | one radix over the whole sequence | Mamba/SSM state is checkpointed **only on the Mamba block grid** — the physical block for a hybrid model can be ~1024 tokens, so a hit normally resumes only at that boundary; `--enable-mamba-shared-prefix-checkpoint` + `--prefix-match-unit 64` lift it to the shared-prefix junction | same, with 64-token resume |
| Eviction | radix LRU | LRU over the free-block queue; **newest/most-specific block freed first** | same |

Consequences for our measured laws:

1. **The grid is a parameter of the measurement, not of the model.** At default vLLM the finest law we can
   express is 16 tokens; a 64-token hit-rate curve measured on vLLM/16 is *not* the same experiment as ours.
   The apples-to-apples arm is `--block-size 64` (or `--prefix-match-unit 64`), and the scientific arm is a
   sweep 16 / 32 / 64 — that sweep is the direct test of "our laws are grid-dependent".
2. **Chained hashing makes the hit set a prefix-closed set.** Unlike a radix over 1-token pages, a partial
   block can never hit, so at `block_size=64` the expected hit length is `64·floor(L/64)` for a shared prefix
   of length `L`. Our 64-token grid should therefore *reproduce* on vLLM/64 — if it does not, the difference
   is in eviction or in the hybrid-state checkpointing, not in the grid.
3. **The hybrid-model caveat is the one that can silently invalidate the comparison.** If the Mamba state is
   only checkpointed on a ~1024-token grid, vLLM/64 will look far worse than SGLang at 64 for Qwen3.5-MoE and
   the obvious (wrong) conclusion is "vLLM's cache is worse". `--enable-mamba-shared-prefix-checkpoint` exists
   precisely for this case and should be on in every arm of this model.
4. **16 is also a cost.** Four times as many blocks means four times the hash-table entries and a finer
   eviction granularity — more chances to keep a stale tail block, and more per-block metadata. It is not a
   free win over 64; it is a different point on the capacity/granularity trade-off.

---

## 3. The three setups from this ecosystem most worth benchmarking against the 64-token SGLang baseline

**Setup A — vLLM V1 APC with a `--block-size` sweep {16, 32, 64} at `--max-num-batched-tokens 8192`.**
Why first: it is the only arm that isolates the variable we actually care about. Same model, same chunk
budget, same measurement grid code; only the cache grid moves. If our 64-token laws are grid artefacts they
will move with the grid here; if they are workload artefacts they will not. Runs on one GPU, one process,
no extra dependency, ~minutes per arm. *This is the arm I would run first and the one I would trust most.*

**Setup B — vLLM + LMCache CPU tier** (`--kv-offloading-backend lmcache --kv-offloading-size <GiB>`, or
`LMCacheConnectorV1` if the standalone daemon is wanted). Why second: our baseline is explicitly "no
hierarchical cache", and LMCache is the ecosystem's answer with the strongest published number (15×
throughput on multi-round QA / document analysis). It decomposes the question our baseline cannot answer:
*is the win from a finer grid, or simply from more cache capacity?* A CPU tier changes capacity only, so
A-vs-B separates granularity from capacity. Single node, no disk needed for the first pass (disk/remote is
the `needs-extra-storage-layer` variant). Watch the miss path: a tier turns a cache miss into an I/O.

**Setup C — vLLM hybrid-model arm: `--prefix-match-unit 64 --enable-mamba-shared-prefix-checkpoint`.**
Why third, and why it is not optional for *our* model: Qwen3.5-MoE is hybrid attention. Without the
shared-prefix checkpoint, the Mamba state pins hits to the physical block grid (which the vLLM source
describes as potentially 1024 tokens for a hybrid model) and every 64-token conclusion is contaminated by a
state-checkpointing artefact. This arm is cheap (a flag), single-GPU, and it is the difference between
"vLLM reuses less" and "vLLM cannot express our grid for this model family". The docs themselves pick 64 as
the starting value, which makes the arm directly comparable to our baseline.

**Explicitly deferred (not "no", just not on one GPU):** KV-aware routing (llm-d / Production Stack router)
is where the 3×/2× numbers live, and P/D disaggregation is where the "does not improve throughput" claim can
be reproduced — both need ≥2 instances. They belong in the phase after A–C, once we know whether the grid or
the capacity is doing the work.

---

## 4. Gaps and assumptions recorded by this unit

- **AIBrix** was not verified: discovery returned federated-search noise, and the call budget went to primary
  vLLM/Mooncake/LMCache sources instead. Its prefix-cache routing is claimed to be equivalent in mechanism to
  llm-d's; that claim is *unverified* here and should not be cited as measured.
- **Speculative decoding has no upstream measured number** in the docs; only a qualitative table. The EAGLE-3.1
  "2× acceptance length" figure is a vendor blog, not reproduced.
- \*\*No vLLM APC throughput number exists in the docs.\*\* The 15× figure is LMCache's, i.e. APC *plus a tier*;
  using it as an APC-alone number would overstate it by an unknown factor.
- All "measured" figures are **as published by the project or paper**, not reproduced by us. Vendor benchmarks
  (llm-d, vLLM blogs, LMCache blog) are labelled as such in the table.
- Docs version read: vLLM `main` (docs banner v0.32.0), `vllm/config/cache.py` on `main`, LMCache `dev`
  README, Mooncake `main` README. Flags can drift between releases; pin the version before benchmarking.
