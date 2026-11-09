# R2 Serving Inventory — live machine state (read-only observation)

Observation date: 2026-11-07. No service was started/stopped/restarted/reloaded; no config changed; no inference request sent. Commands run: `ps -eo pid,ppid,etime,cmd`, `ss -ltnp`, `rocm-smi` (+ `--showmeminfo`, `--showpids`), `docker inspect/top/exec`, `lspci`, `nvidia-smi` (failed — no NVIDIA driver/GPU), read of `/proc/9738/cmdline` and cgroup, one metadata GET `curl -s http://127.0.0.1:8088/health` (labelled below).

## 1. Live model-serving processes

Only one process on this machine qualifies as a model-serving process.

- **PID (host):** 9738 (container PID 1 inside docker container `5a0ed0108a6c`).
- **Full argv (verbatim, from `/proc/9738/cmdline`):** `python -u /app/server.py `
- **Engine/version:** PyTorch 2.9.1+rocm7.1.1 (HIP 7.1.52802), Transformers 5.15.0, FastAPI/uvicorn (from `/app/server.py` and `/health`). No separate inference engine (no vLLM/SGLang); a thin FastAPI wrapper around `AutoModelForSequenceClassification`.
- **Model weights identity:** `/models/qwen3.5-4b-nli-v2` inside container = `Qwen3_5ForSequenceClassification`, model_type `qwen3_5` (text `qwen3_5_text`), bfloat16, 32 hidden layers, hidden_size 2560, max_position_embeddings 262144, vocab 248320, seq-classification head with labels {contradiction, entailment, neutral}, template `Premise: {premise}\nHypothesis: {hypothesis}`. File: `model.safetensors`. Host path not directly observed (container mount not inspected); container image `sha256:9371dc20c644a82b95137299296eabcd58d7dab552d1935a382739e011a57e2a`.
- **Bound host:port:** 127.0.0.1:8088 (ss: `127.0.0.1:8088` LISTEN, process node? actually docker-proxy; container binds 0.0.0.0:8088 mapped to 127.0.0.1:8088). Metadata GET /health returned `ok:true`, device cuda:0 (ROCm), load_seconds 23.442.
- **Uptime:** container started 2026-10-24T03:06:05Z; process elapsed 14-19:01:58 (ps ELAPSED).
- **Managed by:** plain Docker container (restart policy `no`), cgroup path `0::/system.slice/docker-5a0ed0108a6c...scope`. Not systemd. No unit file found in repo.
- **Config/concurrency:** OPENJEV_BATCH=16, OPENJEV_MAX_LEN=128, OPENJEV_MODEL_DIR=/models/qwen3.5-4b-nli-v2, OPENJEV_DEVICE default cuda:0, port 8088. No max-num-seqs / kv-cache / gpu-memory-utilization (not applicable — transformers eager, single forward pass, no batching engine). A second model dir present in container (`/models/qwen3.5-0.8b-nli-v2s-long`) is NOT loaded.

No SGLang or vLLM process is running. No listener on 8012/8014/8017. `systemctl list-units` for model-like services returned none.

## 2. GPU

`nvidia-smi` FAILED: "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver." No NVIDIA GPU present (`lspci` shows AMD Radeon RX 9070 (Navi 48, 03:00.0) and AMD Granite Ridge integrated (18:00.0)). `/proc/driver/nvidia` absent; no nvidia kernel module. `/dev/nvidiactl` exists but unusable.

`rocm-smi` (AMD):

```
Device 0  Node 1  DID 0x7550  Temp 36.0°C  Power 39.0W  SCLK 918Mhz  MCLK 1258Mhz  Fan 0%  Perf auto  PwrCap 230.0W  VRAM% 8%  GPU% 4%
Device 1  Node 2  DID 0x13c0  Temp 44.0°C  Power 0.014W  SCLK N/A  MCLK 2400Mhz  Fan 0%  Perf auto  PwrCap N/A  VRAM% 3%  GPU% 0%
```

Memory:
- GPU0 VRAM total 17,095,983,104 B (~15.92 GiB); used 10,965,823,488 B (~10.21 GiB); free ~6.13 GiB.
- GPU1 VRAM total 536,870,912 B (512 MiB, iGPU); used 16,814,080 B.

Per-process GPU memory (`rocm-smi --showpids`): PID 9738 python uses 9,421,869,056 B (~8.77 GiB) VRAM on GPU 1 (container's cuda:0 maps to host GPU0). No other KFD process listed.

GPUs are NOT exclusive to this server in the sense of "only consumer": the same GPU0 is used by the desktop/GUI stack implicitly; but no other model-serving or substantial compute tenant is observed. The 0.8b model dir is unused. GPU1 is the iGPU (likely display).

## 3. Other active consumers

- Docker containers: openjev (model), searxng, orbit, cerebro, vegtam, caddy, authelia, pi-agent, nginx site-a/b. None are model-serving except openjev. cerebro (3090) and vegtam (3220) may use GPU? Not observed in rocm-smi pids (only 9738). CPU tenants: many omp agents, chrome, node (8787/8790 keyring), authelia, etc. — not model serving.
- Concurrency/session limits visible: none beyond OPENJEV_BATCH=16 / MAX_LEN=128. No queue config observed.

## 4. Historical O1–O4 (from docs/serving-options/BEST-CONFIG.md)

All four are HISTORICAL MEASUREMENT — not evidence of current live configuration. None is running today.

- **O1** occamy-1.0 (MoE, NVFP4) × SGLang: hit 0.958789, uncached 729.20/turn, naive-history arm 723.39 (A), grid_unit 64, 296 rows, CI [659.16,787.62]. Flags: page_size 1, mamba_radix_cache_strategy extra_buffer, radix_eviction_policy lru, mem_fraction_static 0.45, kv_cache_dtype fp8_e4m3, max_mamba_cache_size 64, max_running_requests 5, context 131072, sglang 0.0.0.dev1+g4ccff141d. Status today: UNAVAILABLE — no SGLang process/container found; no launch script in repo; container `gx10-occamy-nvfp4` not present in docker ps. (BEST-CONFIG notes O1 already live on :8012 historically; not observed now.)
- **O2** qwen3.5-9b (dense, NVFP4) × SGLang: container `gx10-w3-dense9b` at 192.168.2.168:8017 (remote, not this machine), flags --page-size 64 --mamba-radix-cache-strategy no_buffer --max-mamba-cache-size 40 --mem-fraction-static 0.08 --context-length 32768, NVFP4 modelopt_fp4. 284 rows. Status today: UNAVAILABLE (container torn down; :8017 no listener).
- **O3** occamy-1.0 × vLLM: flags --block-size 64 --prefix-match-unit 16 --mamba-cache-mode align --enable-prefix-caching --enable-prompt-tokens-details --kv-cache-dtype fp8 --gpu-memory-utilization 0.34 --max-model-len 32768, no MTP. 71 rows. Status today: UNAVAILABLE.
- **O4** qwen3.5-9b × vLLM NVFP4: config V1 of WIN-VLLM: --block-size 64 --quantization modelopt_fp4 --kv-cache-dtype fp8 --enable-prefix-caching --enable-prompt-tokens-details --gpu-memory-utilization 0.15 --max-num-seqs 6 --max-num-batched-tokens 8192 --max-model-len 32768, image sha256:2c211a1273b4…, with MTP speculative-config. 284 rows; resolved block 1088. Status today: UNAVAILABLE (wv-v1 removed on restore).

Launchability verdict: none of O1–O4 can be launched on this machine today from observed state; engines/models/containers absent. Do not invent equivalents.

## 5. Restart/restore procedure

BEST-CONFIG.md §6 says O2/O4 containers torn down after cells; O1 historically live on :8012; O4's `wv-v1` removed on restore. No unit files or launch scripts for SGLang/vLLM exist in this repo (grep for sglang/vllm launch found none). Restore path is UNDOCUMENTED/UNVERIFIED. For openjev, restore = `docker run` with the env vars above + image sha256:9371...; but no documented command in repo. Mark all restore procedures UNVERIFIED; not executed.

## 6. Guardrails for future exclusive window

- Current per-engine default footprint: openjev only, ~8.77 GiB VRAM on GPU0, torch bfloat16, batch 16, max_len 128.
- Safe GPU memory sweep must snapshot: rocm-smi VRAM used/total per GPU, KFD process list (PID/name/VRAM), docker container list + image digests + env, openjev /health JSON. Restore = same container digest + env + port.
- Fingerprint list to pin for reproducibility: host kernel/driver (ROCm 7.1.52802), container image digest sha256:9371dc20..., model dir contents/config.json, torch/transformers versions, env vars (OPENJEV_MODEL_DIR/BATCH/MAX_LEN/DEVICE/PORT), device name AMD Radeon RX 9070, /health output. For any future SGLang/vLLM launch, additional fingerprints required: image tag/digest, full argv, engine version, model weights path/hash, quantization, GPU memory fraction, context length, kv-cache dtype, block/page size, max-num-seqs, max-model-len, port, and the exact restore command.
- Higher cache memory is a variable to test, not a presumed win (per plan).
- Exclusive window requires: no other GPU tenants (currently only openjev uses GPU0; desktop uses iGPU), isolate experiment sessions, fingerprint every launch, restore exact original config after experiments.

## 7. State explicitly

No process was started, stopped, restarted, reloaded, or reconfigured during this observation. No model completion/inference request was sent (only one metadata GET /health to confirm identity, labelled above). No target repo was written. nvidia-smi was invoked read-only and failed due to absent driver (not a perturbation).