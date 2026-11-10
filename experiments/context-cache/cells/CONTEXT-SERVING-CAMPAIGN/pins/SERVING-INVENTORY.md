# Serving Inventory — gx10 (occamy-1.0)

## 1. SSH reachability
- `ssh -o BatchMode=yes -o ConnectTimeout=8 gx10 true` → SSH_OK (exit 0). Host gx10 = 192.168.2.168, user zer0null, key ~/.ssh/id_ed25519.

## 2. GPU / VRAM / driver
- GPU: NVIDIA GB10 (Blackwell), nvidia-smi 580.159.03, CUDA 13.0. Driver 580.159.03.
- VRAM: nvidia-smi reports "Not Supported" for total memory on this unified-memory GB10; system RAM 121 GiB. No discrete VRAM figure available from nvidia-smi. Report VRAM as unknown (unified memory).
- Kernel: Linux gx10-163b 6.17.0-1018-nvidia #18-Ubuntu SMP PREEMPT_DYNAMIC ... aarch64 (ARM64).
- RAM: 121 GiB total, 73 GiB used, 4.2 GiB free, 46 GiB buff/cache, 48 GiB available. Swap 47 GiB (7.4 used).
- Disk: / 916 G total, 614 G used, 256 G avail (71%).

## 3. SGLang process + exact launch flags
Container: docker `gx10-occamy-nvfp4` (image sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7), Up 34 hours, port mapping 192.168.2.168:8012 -> 30000/tcp. Inside container SGLang 0.0.0.dev1+g4ccff141d (pip). vLLM not installed in this container.

Full argv (inside container, PID 196246):
```
/usr/bin/python3 /usr/local/bin/sglang serve \
  --model-path /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 \
  --served-model-name occamy-1.0 --host 0.0.0.0 --port 30000 --tp-size 1 \
  --trust-remote-code --quantization modelopt_fp4 --dtype bfloat16 \
  --context-length 131072 --mem-fraction-static 0.45 --kv-cache-dtype fp8_e4m3 \
  --chunked-prefill-size 8192 --max-running-requests 5 \
  --mamba-radix-cache-strategy extra_buffer --mamba-track-interval 256 \
  --max-mamba-cache-size 64 --mamba-ssm-dtype float32 \
  --attention-backend triton --mamba-backend triton \
  --mm-attention-backend sdpa --moe-runner-backend flashinfer_cutlass \
  --cuda-graph-max-bs-decode 8 --reasoning-parser qwen3 --tool-call-parser qwen3_coder
```
Docker run flags: `--rm --init --name gx10-occamy-nvfp4 --gpus all --ipc=host --shm-size=32g --memory=110g --ulimit memlock=-1:-1 --publish 192.168.2.168:8012:30000 --volume /home/zer0null/.cache/huggingface:/root/.cache/huggingface --volume /home/zer0null/.local/share/gx10-occamy/sglang-cache:/sglang-cache --env SGLANG_CACHE_DIR=/sglang-cache --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

## 4. Weights + tokenizer paths and hashes
- Weights path (host): /home/zer0null/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652
- In-container path: /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652
- model.safetensors.index.json sha256: 6a072db415787f572fe6974da66de946bc34a2e12da933658d48cf06c6ddd02c
- tokenizer.json sha256: e9c0c634f3fc6100dda3700704156cbedb265ad82252478e167ea0d39e992d64
- tokenizer_config.json sha256: 7488550a894dcf741616126e322ea31d66cf9457b59ec5825f4c7efdced421f8
- config.json sha256: 0711b34e69806f243d66fa9925153794e8c7f5ce037ae77cd967a16c6727f466
- Architecture: Qwen3_5MoeForConditionalGeneration (model_type qwen3_5_moe). Hybrid: 40 layers, mix of linear_attention (32) and full_attention (8) per layer_types. MoE. NVFP4 quantization (modelopt_fp4, 4-bit float group_size 16). KV cache dtype fp8_e4m3. context_length 131072.

## 5. HiCache active?
- enable_hierarchical_cache = False (from /get_server_info). HiCache is NOT active.
- disable_radix_cache = False → RadixAttention prefix cache IS active (prefix reuse within instance).
- hicache_ratio=2.0, hicache_size=0, hicache_storage_backend=None (irrelevant, disabled).
- enable_lmcache = False.

## 6. vLLM / CacheBlend / FreeToken feasibility for same weights
- vLLM 0.22.1rc1.dev112+g3f0a91bb9 is installed on host (outside container) at /home/zer0null/.local/lib/python3.12/site-packages/vllm. A separate container gx10-qwen9b runs vLLM serving qwen3.5-9b on port 8014 (image 2c211a1273b4). So vLLM is installable/runnable on this host.
- occamy is Qwen3.5 MoE hybrid (linear_attention + full_attention, mamba state). vLLM support for hybrid linear-attention/Mamba models is architecture-dependent and not confirmed here; NVFP4 modelopt weights need vLLM's modelopt_fp4 kernel support. Unknown whether occamy weights load in vLLM — treat as unverified, needs a bounded smoke test.
- LMCache CacheBlend: LMCache 0.5.2 source present in uv cache; integration with vLLM. CacheBlend is selective recomputation non-prefix reuse, requires vLLM + LMCache. Compatibility with occamy hybrid arch unknown.
- FreeToken: consumer/edge MoE engine (RTX 30/40/50, unified-memory GB10 supported via --moe-strategy auto→offload, fused on GB10). Supports Qwen3.5/Qwen3.6/Qwen3.8, DeepSeek-V4, GLM-5.2. occamy-1.0 (Qwen3.5 MoE NVFP4) may be loadable but FreeToken does not serve SGLang/vLLM API-compatible? It does serve OpenAI /v1/* (port 1919 default). Semantic-anchor caching advertised; concrete API for non-prefix reuse not verified. Hardware: GB10 unified memory supported (fused). Not verified for occamy weights.

## RESTORE command (baseline)
Exact docker run (recreate baseline):
```
docker run --rm --init --name gx10-occamy-nvfp4 --gpus all --ipc=host --shm-size=32g --memory=110g --ulimit memlock=-1:-1 --publish 192.168.2.168:8012:30000 --volume /home/zer0null/.cache/huggingface:/root/.cache/huggingface --volume /home/zer0null/.local/share/gx10-occamy/sglang-cache:/sglang-cache --env SGLANG_CACHE_DIR=/sglang-cache --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7 sglang serve --model-path /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 --served-model-name occamy-1.0 --host 0.0.0.0 --port 30000 --tp-size 1 --trust-remote-code --quantization modelopt_fp4 --dtype bfloat16 --context-length 131072 --mem-fraction-static 0.45 --kv-cache-dtype fp8_e4m3 --chunked-prefill-size 8192 --max-running-requests 5 --mamba-radix-cache-strategy extra_buffer --mamba-track-interval 256 --max-mamba-cache-size 64 --mamba-ssm-dtype float32 --attention-backend triton --mamba-backend triton --mm-attention-backend sdpa --moe-runner-backend flashinfer_cutlass --cuda-graph-max-bs-decode 8 --reasoning-parser qwen3 --tool-call-parser qwen3_coder
```
Health check: `curl -s http://192.168.2.168:8012/v1/models` returns model id occamy-1.0; `curl -s http://192.168.2.168:8012/get_server_info` returns JSON with model_path matching. Env vars (names only): SGLANG_CACHE_DIR, HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, PYTORCH_CUDA_ALLOC_CONF. No secret-shaped values observed.