# Engine Documentation Facts (non-prefix / disjoint KV reuse)

## vLLM Automatic Prefix Caching — https://docs.vllm.ai/en/stable/design/prefix_caching
- Mechanism: PREFIX reuse only. Hash-based block cache: each block hash = hash(parent_hash, block_tokens, extra_hashes). Reuse occurs only when a new request shares an identical token prefix (full blocks). Cannot express disjoint/non-prefix reuse.
- Flags: `--enable-prefix-caching` (default in recent versions), `--prefix-caching-hash-algo` (sha256/sha256_cbor/xxhash/xxhash_cbor), request field `cache_salt` for isolation.
- Constraints: full blocks only; hash includes parent, so position/order matters; multi-modality via image hash. No correctness claim for reordered chunks.
- Non-prefix (disjoint) reuse: NO.

## LMCache CacheBlend — https://docs.lmcache.ai/kv_cache_optimizations/cacheblend.html
- Mechanism: SELECTIVE RECOMPUTATION non-prefix reuse. Reuses KV cache of ANY repeated text chunk (not only shared prefix) by selectively recomputing a small fraction of tokens at chunk boundaries. Targets RAG/multi-doc where reusable context is not a clean prefix.
- API/flags: `lmcache server --engine-type blend`; in-process legacy knobs `LMCACHE_ENABLE_BLENDING`; vLLM integration via LMCache connector. Recomputation fraction configurable (blend ratio).
- Constraints: recomputes a fraction at boundaries → approximate (not exact) reuse; quality must be tested. Requires compatible model arch and vLLM.
- Non-prefix (disjoint) reuse: YES, with selective recomputation and quality caveat. Not exact KV reuse.

## SGLang HiCache — https://github.com/sgl-project/sglang/.../hicache_design.mdx
- Mechanism: PREFIX reuse + hierarchical storage (L1 GPU / L2 host / L3 storage). RadixAttention radix tree; HiRadixTree tracks where KV lives. Prefetch from L3; write-back policies. NOT disjoint reuse; prefix-only matching.
- Flags: `--enable-hierarchical-cache`, `--hicache-ratio`, `--hicache-size`, `--hicache-storage-backend` (file/fast_file/mooncake/hf3fs/nixl/aibrix/dynamic/lmcache), `--hicache-storage-prefetch-policy`, `--hicache-write-policy`, `--hicache-io-backend`, `--hicache-mem-layout`, `--enable-lmcache`, `--lmcache-config-file`.
- Constraints: requires --enable-hierarchical-cache (currently false on baseline). L2 is instance-private; cross-instance only via L3 backend. Prefix-only.
- Non-prefix (disjoint) reuse: NO.

## Mooncake — https://kvcache-ai.github.io/Mooncake/deployment/kv-cache-sharing-and-isolation.html
- Mechanism: STORAGE/SHARING layer, not a correctness mechanism. Treats object keys as opaque strings; framework constructs keys. Provides tenant/model/release/request-group isolation (cache_salt).
- API: SGLang `--hicache-storage-backend mooncake` + `extra_backend_tag`; vLLM `MooncakeStoreConnector` with `cache_prefix` and request `cache_salt`. `--enable_multi_tenants`.
- Constraints: sharing correctness depends on framework's key construction; Mooncake itself does not verify disjoint reuse. Requires compatible backend + RDMA/NIC config.
- Non-prefix (disjoint) reuse: Not by itself; storage layer only.

## FreeToken — https://github.com/FlashML-org/FreeToken (README + docs/cli.md)
- Mechanism advertised: "Semantic-Aware Caching" — semantic anchor checkpoints for recurrent state and KV caches, allowing agentic context edits (tool calls, thinking blocks) to avoid redundant context recomputation. Concrete API/position-correctness claim NOT verified from pinned code; only README-level claim. Engine is edge/consumer MoE serving (RTX 30/40/50, GB10 unified memory supported). Supports Qwen3.5/Qwen3.6/Qwen3.8, DeepSeek-V4, GLM-5.2. Cache control: `--cache-type radix|naive`, `GET /v1/cache/status`, `POST /v1/cache/rebuild`, `--enable-cache-report`, `GET/POST /v1/cache/flush`.
- Hardware: consumer GPUs; occamy (Qwen3.5 MoE NVFP4) not in listed supported models. API is OpenAI-compatible on port 1919.
- Non-prefix (disjoint) reuse: UNVERIFIED (advertised only; label unverified, not negative). Position-handling correctness claim: unverified.<|end|><|start|>write to=assistant<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="i">
Writing ENGINE-DOCS.md