# VLLM-PROBE — vLLM / CacheBlend / FreeToken feasibility (same weights)

Zero model requests. Zero container starts. Zero restarts of `gx10-occamy-nvfp4`. Evidence gathered via read-only SSH to gx10 plus local source reads.

## 1. vLLM contains the architecture?

vLLM 0.22.1rc1.dev112+g3f0a91bb9 on host at `/home/zer0null/.local/lib/python3.12/site-packages/vllm`.

- Registry: `model_executor/models/registry.py:562`:
  `"Qwen3_5MoeForConditionalGeneration": ("qwen3_5", "Qwen3_5MoeForConditionalGeneration"),`
- Hybrid: `model_executor/models/qwen3_5.py:73` imports `IsHybrid`; `:554` `class Qwen3_5ForConditionalGeneration(Qwen3VLForConditionalGeneration, IsHybrid):`
- NVFP4 quant: `model_executor/layers/quantization/modelopt.py:1005` `class ModelOptNvFp4Config(ModelOptQuantConfigBase):`; `:1046` `return "modelopt_fp4"`.
- Linear attention layer handling: `model_executor/models/qwen3_5.py:120` `class Qwen3_5DecoderLayer(Qwen3NextDecoderLayer)`; `:137` `if self.layer_type == "linear_attention":`.

Conclusion: architecture registered and hybrid/linear-attention + modelopt_fp4 supported in vLLM source.

## 2. Can vLLM parse occamy config without loading weights?

Command (on gx10):
```
python3 -c "from vllm.engine.arg_utils import EngineArgs; ...; ea=EngineArgs(model=..., trust_remote_code=True, quantization='modelopt_fp4', dtype='bfloat16', max_model_len=4096, enforce_eager=True, gpu_memory_utilization=0.01); mc=ea.create_model_config(); print(mc.architectures, mc.hf_config.model_type, mc.quantization, mc.max_model_len)"
```
Output:
```
INFO ... Resolved architecture: Qwen3_5MoeForConditionalGeneration
['Qwen3_5MoeForConditionalGeneration'] qwen3_5_moe modelopt_fp4 4096
OK parse
```
No GPU allocation occurred (gpu_memory_utilization=0.01, config-only). Full weight load / CUDA init remains UNVERIFIED.

## 3. What would vLLM prefix caching give us?

vLLM prefix caching reuses KV only for a common prefix shared across requests. It cannot serve a reordered/disjoint chunk without recomputation. CacheBlend is the mechanism that provides non-prefix reuse via selective recomputation. Label prefix caching as prefix-only; do not claim disjoint reuse.

## 4. CacheBlend (LMCache 0.5.2)

Source: `/home/zer0null/.cache/uv/sdists-v9/pypi/lmcache/0.5.2/.../src`.

- Flags: `enable_blending` (bool), `use_layerwise` (bool), `blend_recompute_ratios`, `blend_thresholds`, `blend_check_layers`, `blend_min_tokens`, `blend_special_str` (`lmcache/v1/config.py:121-145`).
- Adapter: `lmcache/integration/vllm/vllm_v1_adapter.py:539` `self.enable_blending = config.enable_blending`; `:541` asserts gpu_connector; `:542` `LMCBlenderBuilder.get_or_create(...)`; `:836` `if self.enable_blending: self.blender.blend(...)`.
- Requirement: `use_layerwise=True` (layer-wise activations) and vLLM attention backend; `utils.py:381` `if use_mla and config.use_layerwise and config.enable_blending: raise ValueError("We haven't supported MLA with Cacheblend yet...")`.
- Hybrid (occamy) satisfaction: UNVERIFIED. vLLM marks Qwen3.5 as IsHybrid; CacheBlend's blender path is exercised on standard architectures. Whether hybrid linear-attention layers satisfy layer-wise activation requirements is not established by source inspection. Treat as needs bounded smoke.

## 5. FreeToken

FreeToken is NOT installed on gx10 (no files, no binary, no python import found). Per inventory it is a consumer/edge MoE engine with OpenAI-compatible /v1/*, supports Qwen3.5/Qwen3.6/Qwen3.8, GB10 unified memory via --moe-strategy. Concrete API, semantic-anchor caching correctness, and non-prefix reuse are UNVERIFIED (no pinned source available to quote). Label unsupported/unverified, not negative.

## 6. Verdict table

| Engine | Same weights? | Can start w/o disturbing baseline? | Ports/mem headroom | Non-prefix reuse? | Mechanism | Needs bounded smoke? |
|---|---|---|---|---|---|---|
| SGLang (baseline) | yes (running) | n/a (baseline) | 110 GiB cap; ~73 GiB used, ~48 GiB available | prefix (radix) only | RadixAttention | no |
| vLLM baseline | parsed config OK; full load UNVERIFIED | sequential only; cannot run concurrently with SGLang (48 GiB free insufficient for a second ~?GB model; SGLang capped 110/121 GiB) | needs separate port; restore baseline after | prefix only | vLLM prefix cache | yes |
| vLLM + CacheBlend | same as vLLM | same | same | yes (selective recomputation) | LMCBlender | yes (hybrid unknown) |
| FreeToken | unknown (not installed) | unknown | unknown | advertised semantic-anchor; unverified | unknown | separate unit |
| SGLang HiCache | same weights | could enable (currently disabled) | same container | prefix storage only | HiCache | maybe |

Memory arithmetic: total 121 GiB; SGLang container `--memory=110g`; system shows ~73 GiB used, ~48 GiB available. A second engine cannot safely run concurrently; variants must be sequential with baseline stopped/restored. Concurrent run would risk OOM and disturb baseline.

## Recommendation

Worth a bounded attempt: **vLLM baseline + CacheBlend on occamy**, sequentially (stop baseline, start vLLM on a separate port, verify, restore baseline), because config parse succeeded and CacheBlend is the only path to non-prefix reuse. Strongest single piece of evidence: `EngineArgs.create_model_config()` resolved `Qwen3_5MoeForConditionalGeneration` with `quantization=modelopt_fp4` and `max_model_len=4096` without GPU allocation.

FreeToken: UNVERIFIED (not installed) — do not attempt in this campaign; separate bounded unit if desired. SGLang HiCache: prefix-only, not a non-prefix solution. Do not claim CacheBlend works on occamy hybrid until smoke confirms.

Bounded attempt spec: stop baseline container (snapshot argv first), run vLLM with `--quantization modelopt_fp4 --dtype bfloat16 --max-model-len 4096 --enforce-eager --gpu-memory-utilization 0.45 --port 8013 --trust-remote-code`, then LMCache with `enable_blending=True use_layerwise=True`; probe `/v1/models` and a cold/repeat/reordered-chunk sequence; restore baseline via saved docker run; verify health. If restore fails, stop all experimentation.
