#!/usr/bin/env bash
# launch-sglang-spcc.sh — SGLang launch for the SPCC programme.
# Mirrors the captured live invocation of container gx10-occamy-nvfp4
# (image 72457f09d20e, sglang serve). Changes from captured:
#   - adds --enable-hierarchical-cache (host-memory tier; was false live)
# Everything else byte-identical to the captured Args.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Refuse while a memory window is open (supervisor writes MEM-WINDOW.json).
if [[ -f "$HERE/MEM-WINDOW.json" ]]; then
  echo "refusing to start: MEM-WINDOW.json present in $HERE (memory window open)" >&2
  exit 1
fi

# Weights: occamy-1.0-NVFP4 ~ 16-18 GB on disk (NVFP4). KV at fp8_e4m3 over
# 131072 context for a 30B-class MoE with mamba cache (max-mamba-cache-size 64)
# is bounded by --mem-fraction-static. 0.45 of ~121 GB unified = ~54.45 GB,
# leaving weights+KV <= 60 GB with headroom for the host tier. mem-fraction-static
# unchanged from captured (0.45) so this stays inside the 60 GB allowance.
MEM_FRAC=0.45

CMD=(
  sglang serve
  --model-path /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652
  --served-model-name occamy-1.0
  --host 0.0.0.0
  --port 8012
  --tp-size 1
  --trust-remote-code
  --quantization modelopt_fp4
  --dtype bfloat16
  --context-length 131072
  --mem-fraction-static "$MEM_FRAC"
  --kv-cache-dtype fp8_e4m3
  --page-size 1
  --chunked-prefill-size 8192
  --max-running-requests 5
  --mamba-radix-cache-strategy extra_buffer
  --mamba-track-interval 256
  --max-mamba-cache-size 64
  --mamba-ssm-dtype float32
  --attention-backend triton
  --mamba-backend triton
  --mm-attention-backend sdpa
  --moe-runner-backend flashinfer_cutlass
  --cuda-graph-max-bs-decode 8
  --reasoning-parser qwen3
  --tool-call-parser qwen3_coder
  --enable-metrics
  --enable-cache-report
  --enable-hierarchical-cache
)

if [[ "${1:-}" == "--dry-run" ]]; then
  printf '%s\n' "${CMD[*]}"
  exit 0
fi

printf 'about to run: %s\n' "${CMD[*]}"
exec "${CMD[@]}"
