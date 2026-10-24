# R-STACK — exact launch guides for SGLang and vLLM

Purpose: produce copy-pasteable launch guides for configs S1–S4 (SGLang) and V1–V2 (vLLM 0.27.1) so maintenance-window units can launch each config first time.

Hard constraints: 0 live model requests; no .occamy.lock; no launch/restart/stop; no SSH to GX10. Read live-server-config.json only, did not re-probe. Did not edit prior R-*.md surveys; added new files only.

Write paths:
- docs/serving-options/LAUNCH-SGLANG.md
- docs/serving-options/LAUNCH-VLLM.md
- orchestration/units/R-STACK.md
- orchestration/handoffs/R-STACK.json

Key results:
- S1 --page-size 64: GO (tail-page waste ~1.5%; mamba_track_interval 256 divisible by 64; does not move c128_page_size 16 or _mamba_cache_chunk_size 64).
- S2 HiCache: NO-GO for hybrid mamba (occamy) — HiRadixCache only supports MHA/MLA; error "ValueError: HiRadixCache only supports MHA and MLA yet". Removes S2 from window.
- S3 --disable-chunked-prefix-cache: UNKNOWN for hybrid (DeepSeek-specific per docs; live reports top-level false but runtime_effective true).
- S4 qwen3.5-9b: GO (dense; SGLang supports Qwen3.5 dense; NVFP4 availability unknown).
- V1: GO for block-size 16/64, prefix-match-unit 64, enable-prefix-caching, max-num-batched-tokens; NO-GO for --enable-mamba-shared-prefix-checkpoint (not in 0.27.1).
- V2: LIKELY GO (medium confidence) for loading Qwen3.5-MoE NVFP4 (modelopt + Qwen3_5MoeForCausalLM registered); cached_tokens = usage.prompt_tokens_details.cached_tokens when --enable-prompt-tokens-details set; second model feasible with lowered gpu-memory-utilization.

Sources: SGLang server_arguments docs [fetched], GitHub issue #12826 [fetched], PR #21259 [fetched], vLLM v0.27.1 cache.py/arg_utils.py/registry.py/quantization dir/serving.py [fetched], live-server-config.json [read].