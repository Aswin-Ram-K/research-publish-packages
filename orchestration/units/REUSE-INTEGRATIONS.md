# REUSE-INTEGRATIONS — non-prefix KV reuse: integration procedure matrix

**Verdict:** Only one method actually provides non-prefix reuse on this stack: **vLLM + LMCache CacheBlend** (selective recomputation). FreeToken advertises semantic-anchor reuse but is unverified on occamy. SGLang's own LMCache integration, HiCache, and the mamba-radix knobs are prefix-only and must not be reported as non-prefix solutions. Critical risk: occamy's 32 linear-attention (SSM) layers make hybrid-KV transfer unsupported in LMCache's engine-driven transport (issue #4071, open); CacheBlend's blender path is exercised on standard archs only.

**What was established**
1. SGLang container (`gx10-occamy-nvfp4`) has NO lmcache installed; `--enable-lmcache`/`--enable-hierarchical-cache` switches exist (compiled in) but need the package + daemon. `lmc_radix_cache.py` subclasses `RadixCache` and contains no blend/recompute code → prefix-only storage backend.
2. LMCache is in uv cache only (0.5.2 source + wheels, lmcache_vllm 0.6.2.3). Not installed system-wide. CacheBlend non-prefix reuse requires vLLM connector (`enable_blending`, `use_layerwise`) + `lmcache server --engine-type blend`.
3. FreeToken not installed. Docs support Qwen3.5/Qwen3.6 MoE + GB10 unified memory (`auto→fused`). occamy not in known-good list but "other checkpoints of the same architectures work too." Semantic anchors at special-token boundaries; position correctness claimed only at those boundaries.
4. HiCache supports hybrid/mamba state (PR #21259) but is prefix-only by design ("Reuse requires identical prefix tokens").
5. Baseline mamba-radix knobs (`extra_buffer`/track-interval/max-cache) already on; prefix-only for SSM layers.

**Top 2 candidates with copy-pasteable procedures:** (1) vLLM + LMCache CacheBlend (sequential, §4 of note), (2) FreeToken smoke (§5). Both include cold/repeat/reordered-chunk smokes, negative controls, rollback (baseline restore command frozen in `pins/rollback-baseline.json`).

**Do-not-attempt list:** SGLang+LMCache expecting CacheBlend, HiCache as non-prefix, mamba-radix retuning for non-prefix, concurrent engines, different-model FreeToken as head-to-head, claiming CacheBlend on occamy before smoke.

**Budget:** 0 model calls spent (read-only recon). 0 container starts. 0 restarts.

**Handoff:** `orchestration/handoffs/REUSE-INTEGRATIONS.json`.
**Artifact:** `experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/notes/REUSE-INTEGRATIONS.md`.