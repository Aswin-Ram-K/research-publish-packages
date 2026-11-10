# VLLM-PROBE

Read-only feasibility. Output: $CAMPAIGN/notes/VLLM-FEASIBILITY.md.

Key result: vLLM parses occamy config (EngineArgs.create_model_config -> Qwen3_5MoeForConditionalGeneration, modelopt_fp4) without GPU. CacheBlend flags quoted from LMCache 0.5.2 source. FreeToken not installed -> UNVERIFIED. Recommendation: bounded vLLM+CacheBlend smoke, sequential, restore baseline.
