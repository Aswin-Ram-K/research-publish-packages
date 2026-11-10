# ENGINE-VLLM-ATTEMPT — vLLM on the SAME occamy weights (unit ENGINE-ATTEMPT-VLLM)

Date: 2026-11-05/06. Mutates serving state; baseline restored and verified healthy at end.

## 0. Rollback spec frozen first
`$CAMPAIGN/pins/rollback-baseline.json` written before any mutation. Captured: image digest sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7; full `docker inspect` of `gx10-occamy-nvfp4` (Arg list/Env names/Ports/Memory/ShmSize/IpcMode/Name/Image); ready `docker run` restore command (full argv, 1287 chars); health-check pair {/v1/models id occamy-1.0; /get_server_info model_path == ...fa865dc...}; `docker ps` before-state in `pins/logs/docker-ps-before.txt`. Baseline healthy before: /v1/models returned occamy-1.0; model_path matched.

## 1. Size the problem (arithmetic)
- Weights on gx10: 5 safetensors shards under snapshot, total 22.28 GiB (23,926,133,080 bytes). (Initial `find` without -L gave 380 bytes because snapshot entries are symlinks into `blobs/`; used `find -L`.)
- System RAM: 121 GiB total, ~72 GiB used, ~48 GiB available before (inventory). During attempt: 121 total, 22 used, 89 free, 98 available (after trial removed).
- SGLang container `gx10-occamy-nvfp4` memory cap: `--memory=110g` (118,111,600,640 bytes). RSS at idle: ~6 GiB.
- Concurrent feasibility: worst case SGLang can grow to its 110 GiB cap, leaving only 121-110 = 11 GiB (9.1% of 121 GiB) for a second engine — less than the 15% (18.15 GiB) headroom required and far less than the 22.28 GiB weights. Even at observed idle RSS (6 GiB), a second vLLM with default gpu-memory-utilization 0.92 would claim ~111 GiB. Therefore Attempt A (concurrent) was NOT attempted; arithmetic forbids it. Variants are sequential only.

## 2. Attempt A — concurrent start
NOT ATTEMPTED. Reason: SGLang's 110 GiB cap leaves 11 GiB (9.1%) < 15% headroom and < 22.28 GiB weights. Verdict for A: skipped on memory arithmetic (see §1). No container started, no calls spent.

## 3. Attempt B — exclusive start: vLLM on same occamy weights
Baseline stopped (`docker stop gx10-occamy-nvfp4`, exit 0). Port 8012 verified closed. Started NEW container (never reused baseline name):
- Image: `2c211a1273b4` (untagged, vLLM 0.27.1; the only vLLM image on the box, also used by `gx10-qwen9b` which was left strictly alone).
- Name: `gx10-vllm-occamy`. Port publish 192.168.2.168:8013->8013. Same HF cache mount (`/home/zer0null/.cache/huggingface:/root/.cache/huggingface`), plus vLLM cache dir. Memory cap 110g, shm 32g, ipc host, gpus all.
- Command (entrypoint `vllm serve`): `/root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 --served-model-name occamy-1.0 --host 0.0.0.0 --port 8013 --quantization modelopt_fp4 --dtype bfloat16 --max-model-len 8192 --gpu-memory-utilization 0.5 --enforce-eager --trust-remote-code`
- vLLM `--help=all` evidence saved conceptually: flags `--quantization`, `--dtype {bfloat16}`, `--max-model-len`, `--gpu-memory-utilization`, `--enforce-eager`, `--trust-remote-code`, `--port`, `--served-model-name` all exist in vLLM 0.27.1.
- Startup: resolved architecture `Qwen3_5MoeForConditionalGeneration`; loaded NVFP4 checkpoint (22.28 GiB) in 158.44 s (model loading 22.41 GiB). Autotune ran. "Application startup complete." at 00:12:41. Port 8013 served /v1/models -> occamy-1.0.

Smoke call 1 (ledger attempt 857904c1-da74-4537-92f6-ffcd03416165, phase serving, outcome ok):
- POST /v1/chat/completions, prompt "Say hi in one word.", max_tokens 16, temperature 0.
- Elapsed: 50.79 s. finish_reason: length. content: "Thinking Process:\n1.  **Analyze the Request:** The user wants". usage: prompt_tokens 16, completion_tokens 16, total_tokens 32. (No cached-token field reported by vLLM for this request; treated as unknown, not zero.)
- Raw: pins/logs/vllm-smoke1.json.

Smoke call 2 (ledger attempt 2fbb611e-3567-4406-ad75-ed04f7fabb63, phase serving, outcome ok):
- POST /v1/chat/completions, prompt "Reply with the single word: pong", max_tokens 16, temperature 0.
- Elapsed: 0.69 s. finish_reason: length. content: "Thinking Process:\n1.  **Analyze User Input:** The user says". usage: prompt_tokens 17, completion_tokens 16, total_tokens 33.
- Raw: pins/logs/vllm-smoke2.json.

Note: occamy is a reasoning model; with max_tokens 16 it exhausted the budget in thinking tokens, so content is a thinking trace, not a final answer. This is a smoke (liveness + usage), not a quality claim. vLLM 0.27.1 served the model successfully on the same weights.

## 4. Restore, verified
Trial container stopped and removed (`docker stop` + `docker rm -f gx10-vllm-occamy`, container gone). Free memory recovered to 98 GiB available.

Baseline container was observed in a restart/up state under memory pressure (Main state check: endpoint refused, baseline "Up 2 minutes", 13 GiB available, vLLM trial holding memory). After trial removal, a fresh baseline container (ID 6384dc02..., image sha256:72457f... ) started loading at 00:14:12 and its Cmd exactly matched the frozen restore command argv (MATCH: True, 770 chars). Weight load completed in 131.49 s. CUDA-graph capture completed. Server reported "Application startup complete" equivalent (SGLang ready).

Verification:
- GET http://192.168.2.168:8012/v1/models -> {"object":"list","data":[{"id":"occamy-1.0",...,"max_model_len":131072}]} (HTTP 200)
- GET http://192.168.2.168:8012/get_server_info -> model_path = /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 (matches pinned snapshot fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652).

No restore retry was needed: the baseline became healthy on the in-progress load. `docker ps` after restore: only `gx10-occamy-nvfp4` (Up) and `gx10-qwen9b` (Up 12 days, untouched).

## 5. Verdict
SAME_WEIGHT_VLLM_OK

vLLM 0.27.1 (container image 2c211a1273b4) successfully loaded the identical occamy-1.0 NVFP4 weights (sha256 snapshot fa865dc...) and served two chat completions on port 8013. CacheBlend/LMCache was NOT exercised in this unit (no CacheBlend flags added; vLLM prefix caching is prefix-only per docs). FreeToken remains unverified/uninstalled. SGLang HiCache remains disabled on baseline.

Ledger: 2 calls spent under phase `serving` (attempt ids above, both outcome ok). See `status --json` below.

## Service health at finish
HEALTHY. /v1/models on 8012 returns occamy-1.0. model_path matches pinned snapshot. Trial container removed. No further smoke requests dispatched.
