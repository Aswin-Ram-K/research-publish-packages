# REUSE-INTEGRATIONS — non-prefix KV reuse on this stack (read-only recon)

Unit: REUSE-INTEGRATIONS. Zero model calls. Zero container starts. Zero restarts of `gx10-occamy-nvfp4`. All evidence from read-only SSH to gx10, source inspection of the pinned SGLang image, LMCache uv cache, FreeToken docs/paper, and campaign notes. Rollback spec frozen in `pins/rollback-baseline.json`.

## 0. Constraints that decide everything (do not re-derive)

- Stack: SGLang 0.0.0.dev1+g4ccff141d in image `sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7` on gx10 (NVIDIA GB10, ARM64, 121 GiB unified memory, CUDA 13.0, driver 580.159.03). Baseline serves `occamy-1.0` (Accio-Lab occamy-1.0-NVFP4, Qwen3_5MoeForConditionalGeneration, 40 layers = 32 linear-attention/SSM + 8 full attention, MoE, NVFP4, fp8 KV, 131072 ctx) on `192.168.2.168:8012`. `enable_lmcache=False`, `enable_hierarchical_cache=False`, radix prefix cache ON.
- SGLang and vLLM cannot run concurrently (SGLang capped `--memory=110g`; only ~11 GiB headroom left). Variants are sequential; restore baseline after each. Concurrent start was explicitly NOT attempted (ENGINE-VLLM-ATTEMPT §1-2).
- vLLM 0.22.1rc1.dev112+g3f0a91bb9 is installed on host at `/home/zer0null/.local/lib/python3.12/site-packages/vllm` and already loaded occamy weights successfully (SAME_WEIGHT_VLLM_OK, ENGINE-VLLM-ATTEMPT §3-5): 22.28 GiB in 158.44 s, 2 smoke calls on port 8013. Image `2c211a1273b4` (vLLM 0.27.1) is the only vLLM image on the box.
- LMCache is NOT installed system-wide nor in the SGLang container. Source in uv cache: `lmcache 0.5.2` (sdists/wheels) and `lmcache_vllm 0.6.2.3` (wheels). A disk store exists at `/home/zer0null/.cache/lmcache_disk_store`.
- FreeToken is NOT installed (no binary, no python import). Docs: supports Qwen3.5/Qwen3.6 MoE, GB10 unified memory via `--moe-strategy auto→fused`. occamy is not in the known-good list but "other checkpoints of the same architectures work too."
- Critical risk: occamy has 32 linear-attention (SSM/mamba) layers. Methods that assume uniform full attention may refuse to load or silently corrupt. LMCache engine-driven transport explicitly rejects hybrid-KV models (issue #4071, open). vLLM marks Qwen3.5 as `IsHybrid`. CacheBlend's blender path is exercised on standard archs only (VLLM-FEASIBILITY §4).

## 1. What "non-prefix reuse" means here

- Prefix reuse (RadixAttention, vLLM prefix cache, SGLang HiCache): reuse only when a new request shares an identical token prefix (full blocks, parent-hash chained). Reordered/disjoint chunks miss entirely.
- Non-prefix reuse: reuse a KV segment whose position/order/content changed relative to the donor. Two mechanisms exist in this ecosystem: (i) CacheBlend selective recomputation (LMCache, vLLM connector) — recomputes a fraction at boundaries, approximate; (ii) FreeToken semantic-anchor checkpoints (recurrent state + KV at special-token boundaries) — approximate, anchor-dependent.

## 2. Decision table

| Method | Non-prefix? | Arch support (occamy hybrid/MoE/NVFP4/fp8 KV)? | Enable cost | Risk / quality | Feasible ≤30 calls? |
|---|---|---|---|---|---|
| (a) LMCache via SGLang built-in (`--enable-lmcache` + daemon) | **NO** — prefix-only storage backend. SGLang `lmc_radix_cache.py` subclasses `RadixCache`; no blend/recompute code. CacheBlend is not wired into the SGLang connector. | Yes for prefix reuse (same radix cache as baseline, handles mamba state via base cache). | Install lmcache 0.5.2 into container (pip, ~min); start `lmcache server` daemon on a port; restart SGLang with `--enable-lmcache --lmcache-config-file`. | Low for prefix reuse; provides no non-prefix benefit. Adds a daemon + ZMQ hop. | Yes (prefix cold/warm/repeat). But not a non-prefix candidate. |
| (b) SGLang HiCache (`--enable-hierarchical-cache`) | **NO** — prefix-only + hierarchical storage (L1 GPU / L2 host / L3 storage). Docs: "Reuse requires identical prefix tokens; similar meaning alone is not enough." | Yes — PR #21259 added mamba/recurrent state storage through HiCache for hybrid models. | Add flags to baseline container (`--enable-hierarchical-cache --hicache-ratio 2 --hicache-size 0 --hicache-storage-backend ...`); restart. No second process for L2-only. | Low. Storage tier, not correctness mechanism. Adds memory pressure (L2 host pool). | Yes (prefix). Not non-prefix. |
| (c) SGLang mamba-radix knobs (already on baseline) | **NO** — radix prefix cache for SSM/mamba state. `extra_buffer` keeps branch buffers for prefix sharing. | Yes — this is the baseline mechanism for the 32 linear-attention layers. | Already enabled. `--mamba-radix-cache-strategy extra_buffer --mamba-track-interval 256 --max-mamba-cache-size 64`. | Low. Tuning strategy (extra_buffer vs others) only changes prefix eviction, never disjoint reuse. | N/A (already running; no new calls needed). |
| (d) FreeToken | **UNVERIFIED (advertised)** — "semantic-aware caching": recurrent-state checkpoints anchored at special-token boundaries (thinking/tool-call/turn), reused after context edits; full-attention KV via radix tree. Position correctness claimed at semantic boundaries only; LRU eviction of few slots. | Partial/unknown. Supports Qwen3.5/Qwen3.6 MoE and GB10 unified memory (`auto→fused`). occamy (Accio-Lab NVFP4) not in known-good list but "other checkpoints of the same architectures work too." Modelopt NVFP4 loading path unverified. Linear-attention (gated delta net) is exactly the recurrent state FreeToken checkpoints — plausible fit, but unverified. | Install binary (no pip; release tarball) or build from source; `ft serve --model <occamy snapshot> --port 1919 --moe-strategy auto`. Cold start loads 22.28 GiB. | High. Not API-compatible validation; non-prefix reuse is implicit (anchor-based), not a measured counter; quality must be tested. Hardware supported (GB10 fused). | Maybe — 1 startup attempt + a few requests. If load fails, record and stop; do not retry beyond 2 attempts. |
| (e) vLLM + LMCache CacheBlend | **YES** — selective recomputation non-prefix reuse. Reuses KV of ANY repeated chunk (not only shared prefix) by recomputing a small fraction at boundaries. Targets RAG/multi-doc and reordered chunks. | Unverified for occamy hybrid. vLLM resolves `Qwen3_5MoeForConditionalGeneration` + `modelopt_fp4` (config parse OK, full load OK — SAME_WEIGHT_VLLM_OK). CacheBlend needs `enable_blending=True`, `use_layerwise=True`. Hybrid linear-attention layers may not satisfy layer-wise activation requirements; LMCache issue #4071 shows engine-driven transport rejects hybrid-KV models. vLLM adapter (lmcache_driven/CUDA-IPC) may handle groups but unverified. NVFP4 + fp8 KV unverified for CacheBlend. | Stop baseline; install lmcache 0.5.2 + lmcache_vllm 0.6.2.3 into an isolated venv (uv cache available, no global install); start `lmcache server --engine-type blend --l1-size-gb ...`; start vLLM with LMCache connector config (`enable_blending`); verify. Restore baseline after. | Medium-high. Approximate (not exact) reuse; quality must be measured. Startup ~158 s weight load + autotune. Memory: vLLM needs sequential slot (baseline stopped). | Yes (cold + repeat + reordered-chunk sequence, ~6-12 calls). |

## 3. Already tried (do not contradict)

- HL-PILOT: no serving change tested; ran on production endpoint; `enable_session_radix_cache` deliberately off. Found reuse tracks first divergence (cached ≈ rewrite_offset), masking is a cache bomb, output tokens dominate. SGLang baseline radix prefix cache confirmed.
- CCS: A (verbatim) cheapest per verified success; B typed records cost +31%, C masking +110% due to cache-prefix loss. Arm C emitted digests without persisting bodies (unresolved recovery). Instrument defects (watcher crash, grading holes) later repaired.
- ENGINE-VLLM-ATTEMPT: vLLM 0.27.1 loaded occamy weights (SAME_WEIGHT_VLLM_OK), 2 smoke calls, baseline restored and verified healthy. CacheBlend/LMCache NOT exercised. FreeToken unverified. SGLang HiCache disabled.
- VLLM-FEASIBILITY: vLLM config parse OK; CacheBlend hybrid satisfaction UNVERIFIED; FreeToken not installed; SGLang HiCache prefix-only.
- SERVING-INVENTORY: `enable_lmcache=False`, `enable_hierarchical_cache=False`, `disable_radix_cache=False`. Flags list contains both switches (compiled in).

## 4. Top candidate 1 — vLLM + LMCache CacheBlend (non-prefix, sequential)

Goal: prove non-prefix reuse happens on occamy, measure TTFT/cache on a reordered-chunk sequence, then restore baseline. All commands run on gx10 via SSH. Baseline must be stopped first (snapshot already frozen in `pins/rollback-baseline.json`).

### 4.1 Pre-flight (no mutation)
```bash
# health + model identity (must match pinned snapshot)
curl -s http://192.168.2.168:8012/v1/models
curl -s http://192.168.2.168:8012/get_server_info | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("model_path"))'
# expected: occamy-1.0, /root/.../fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652
```

### 4.2 Stop baseline (snapshot first — already in pins/rollback-baseline.json)
```bash
ssh gx10 'docker stop gx10-occamy-nvfp4 && docker rm -f gx10-occamy-nvfp4'
ssh gx10 'curl -s -o /dev/null -w "%{http_code}" http://192.168.2.168:8012/v1/models'   # expect 000/connection refused
```

### 4.3 Isolated env + install (workspace-local, no global install)
```bash
ssh gx10 '
  python3 -m venv /home/zer0null/.local/share/gx10-occamy/vllm-lmcache-venv
  /home/zer0null/.local/share/gx10-occamy/vllm-lmcache-venv/bin/pip install --no-index --find-links /home/zer0null/.cache/uv/wheels-v6/pypi/lmcache /home/zer0null/.cache/uv/wheels-v6/pypi/lmcache-vllm lmcache lmcache_vllm 2>&1 | tail -5
  /home/zer0null/.local/share/gx10-occamy/vllm-lmcache-venv/bin/python -c "import lmcache, lmcache_vllm; print(lmcache.__version__)"
'
```
Fallback if wheels mismatch: `pip install lmcache==0.5.2` from uv sdists with `--no-build-isolation`. Pin versions in the campaign envelope.

### 4.4 LMCache server (blend engine)
```bash
ssh gx10 '
  nohup /home/zer0null/.local/share/gx10-occamy/vllm-lmcache-venv/bin/lmcache server \
    --host 127.0.0.1 --port 5556 \
    --l1-size-gb 20 --eviction-policy LRU --engine-type blend \
    --supported-transfer-mode lmcache_driven \
    > /home/zer0null/.local/share/gx10-occamy/lmcache-blend.log 2>&1 &
  sleep 3; curl -s http://127.0.0.1:5556/health 2>/dev/null || tail -5 /home/zer0null/.local/share/gx10-occamy/lmcache-blend.log
'
```
Note: blend engine requires `--supported-transfer-mode lmcache_driven` or `auto` (CacheBlend doc). For occamy hybrid (multiple KV groups), `engine_driven` is currently unsupported (issue #4071). Use `lmcache_driven` (CUDA-IPC) which handles groups — but it requires vLLM and LMCache in the same process space; with vLLM 0.27.1 this is the in-process connector path. Verify group handling before claiming.

### 4.5 vLLM with LMCache connector (occamy weights)
```bash
ssh gx10 '
  cat > /home/zer0null/.local/share/gx10-occamy/lmcache-occamy.yaml <<EOF
mp_host: 127.0.0.1
mp_port: 5556
extra_config:
  lmcache.mp.mp_transfer_mode: lmcache_driven
  enable_blending: true
  use_layerwise: true
EOF
  nohup /home/zer0null/.local/share/gx10-occamy/vllm-lmcache-venv/bin/vllm serve \
    /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 \
    --served-model-name occamy-1.0 --host 0.0.0.0 --port 8013 \
    --quantization modelopt_fp4 --dtype bfloat16 --max-model-len 4096 \
    --gpu-memory-utilization 0.5 --enforce-eager --trust-remote-code \
    --kv-cache-dtype fp8_e4m3 \
    > /home/zer0null/.local/share/gx10-occamy/vllm-blend.log 2>&1 &
  # poll readiness (bounded ~3 min)
  for i in $(seq 1 36); do curl -s http://192.168.2.168:8013/v1/models >/dev/null && break; sleep 5; done
  curl -s http://192.168.2.168:8013/v1/models
'
```
If startup fails (hybrid KV rejection, NVFP4 kernel missing, OOM), record exact error from log, stop both processes, restore baseline, spend no model calls.

### 4.6 Smoke that proves reuse actually happened (≤12 calls)
Use three request shapes, temperature 0, max_tokens 64:
1. Cold: prompt = chunk X + chunk Y + chunk Z (novel) → record TTFT, prompt_tokens, cached_tokens (if reported; else unknown), finish_reason.
2. Identical repeat: same prompt → should be full prefix hit; TTFT drops; cached_tokens ≈ prompt_tokens.
3. Reordered: prompt = chunk Y + chunk X + chunk Z (middle chunk moved) → this is the non-prefix test. CacheBlend must reuse Y and Z despite the reorder. Observable: TTFT lower than cold and cached_tokens > 0 (or LMCache server log shows blend hits). If cached_tokens is absent, use TTFT delta + LMCache server hit counter (`/metrics` or log lines) as the observable; label cached as unknown, never zero.

Also perturb one chunk's content (chunk X' ≠ X) → CacheBlend must NOT reuse X'; cached_tokens drops vs the reordered case. This is the negative control that distinguishes non-prefix reuse from accidental prefix reuse.

LMCache server observables to capture: `pins/logs/lmcache-blend-server.log`, hit/miss counters, any "blend" log lines, recomputed-token fraction.

### 4.7 Restore baseline (mandatory)
```bash
ssh gx10 'pkill -f "vllm serve" ; pkill -f "lmcache server" ; docker rm -f gx10-vllm-occamy 2>/dev/null'
# then recreate baseline from frozen restore command:
ssh gx10 'docker run --rm --init --name gx10-occamy-nvfp4 --gpus all --ipc=host --shm-size=32g --memory=110g --ulimit memlock=-1:-1 --publish 192.168.2.168:8012:30000 --volume /home/zer0null/.cache/huggingface:/root/.cache/huggingface --volume /home/zer0null/.local/share/gx10-occamy/sglang-cache:/sglang-cache --env SGLANG_CACHE_DIR=/sglang-cache --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7 sglang serve --model-path /root/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 --served-model-name occamy-1.0 --host 0.0.0.0 --port 30000 --tp-size 1 --trust-remote-code --quantization modelopt_fp4 --dtype bfloat16 --context-length 131072 --mem-fraction-static 0.45 --kv-cache-dtype fp8_e4m3 --chunked-prefill-size 8192 --max-running-requests 5 --mamba-radix-cache-strategy extra_buffer --mamba-track-interval 256 --max-mamba-cache-size 64 --mamba-ssm-dtype float32 --attention-backend triton --mamba-backend triton --mm-attention-backend sdpa --moe-runner-backend flashinfer_cutlass --cuda-graph-max-bs-decode 8 --reasoning-parser qwen3 --tool-call-parser qwen3_coder --enable-metrics --enable-cache-report'
# health check (must pass before any further work)
ssh gx10 'curl -s http://192.168.2.168:8012/v1/models; echo; curl -s http://192.168.2.168:8012/get_server_info | python3 -c "import sys,json;print(json.load(sys.stdin).get(\"model_path\"))"'
```
On restore failure: retry once; if still failing, STOP all experimentation and report exact state. Never run benchmarks while service state unknown.

## 5. Top candidate 2 — FreeToken smoke (exploratory, unverified)

Goal: determine whether FreeToken can load occamy and whether its semantic-anchor caching produces a measurable non-prefix reuse. This is exploratory, not a head-to-head engine comparison (different engine, different memory layout). Use contingency budget only if a different model is needed (per plan §4.2).

### 5.1 Install (workspace-local)
```bash
ssh gx10 '
  mkdir -p /home/zer0null/.local/share/gx10-occamy/freetoken
  cd /home/zer0null/.local/share/gx10-occamy/freetoken
  # download latest release tarball (check https://github.com/FlashML-org/FreeToken/releases)
  curl -L -o freetoken.tgz https://github.com/FlashML-org/FreeToken/releases/latest/download/FreeToken-linux-aarch64.tar.gz
  tar xzf freetoken.tgz
  ls; ./ft --version 2>&1 | head
'
```
If no aarch64 binary exists, build from source in an isolated venv (version-pinned) — do not install globally.

### 5.2 Serve occamy (one bounded attempt)
```bash
ssh gx10 '
  /home/zer0null/.local/share/gx10-occamy/freetoken/ft serve \
    --model /home/zer0null/.cache/huggingface/hub/models--Accio-Lab--occamy-1.0-NVFP4/snapshots/fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652 \
    --port 1919 --moe-strategy auto --enable-cache-report \
    > /home/zer0null/.local/share/gx10-occamy/freetoken.log 2>&1 &
  # bounded wait ~5 min
  for i in $(seq 1 60); do curl -s http://127.0.0.1:1919/v1/models >/dev/null && break; sleep 5; done
  curl -s http://127.0.0.1:1919/v1/models
  tail -20 /home/zer0null/.local/share/gx10-occamy/freetoken.log
'
```
If occamy fails to load (NVFP4/modelopt incompatibility, arch not supported), record exact error and stop. Do not substitute a different model unless contingency budget is explicitly allocated and the result is labeled exploratory-only (per plan §4.2).

### 5.3 Smoke (if loaded)
- `GET /v1/cache/status` — record baseline.
- Send cold prompt with thinking/tool-call boundaries (so anchors exist), then an edited version (thinking block stripped, tool output replaced) → check whether TTFT drops and cache status reports hits. FreeToken's anchors are at special-token boundaries; the edited prefix must end exactly at such a boundary for reuse to fire.
- Negative control: edit mid-block (not at a boundary) → no reuse expected.
- Observable is TTFT delta + `/v1/cache/status` counters (`GET/POST /v1/cache/rebuild`, `POST /v1/cache/flush`). There is no per-request cached_tokens field documented; treat as unknown if absent.

### 5.4 Cleanup
```bash
ssh gx10 'pkill -f "ft serve"; sleep 2'
# restore baseline (same command as §4.7) and health-check
```

## 6. Do NOT attempt (and why)

1. **SGLang `--enable-lmcache` expecting CacheBlend non-prefix reuse.** The SGLang connector (`lmc_radix_cache.py`) subclasses `RadixCache` and contains no blend/recompute code; LMCache is used as a hierarchical storage backend for prefix reuse only. Running `lmcache server --engine-type blend` behind SGLang will not invoke selective recomputation because the client never sends blend requests. Non-prefix: NO. Do not spend calls on it.
2. **SGLang HiCache as a non-prefix solution.** HiCache is prefix-only storage (L1/L2/L3). The docs explicitly require identical prefix tokens. It cannot reuse reordered/disjoint chunks. (It remains useful as a prefix-storage tier and is already a candidate for the serving phase's prefix comparison, but not for non-prefix.)
3. **SGLang mamba-radix strategy retuning for non-prefix.** `extra_buffer`/`no_extra_buffer` only changes SSM state eviction for prefix sharing. No strategy provides disjoint reuse. (Baseline already uses `extra_buffer`; do not claim a non-prefix win from changing it.)
4. **Concurrent SGLang + vLLM.** Arithmetic forbids it (SGLang 110 GiB cap leaves 11 GiB < 22.28 GiB weights). Sequential only. (ENGINE-VLLM-ATTEMPT §1-2.)
5. **FreeToken on a different model as an engine comparison.** A different-model FreeToken test is exploratory only and uses contingency budget; it is not a head-to-head with occamy. Label accordingly (plan §4.2).
6. **Enabling LMCache/HiCache on the production baseline permanently without a smoke.** Requires snapshot + bounded smoke + rollback proof first. No systemd changes, no unrelated services.
7. **Claiming CacheBlend works on occamy hybrid before smoke.** Issue #4071 (open) shows engine-driven transport rejects hybrid-KV models; v1 uniform coverage (#4073) is still pending. Label as unverified until smoke confirms, never as negative.

## 7. Observables summary (what counts as proof of reuse)

| Method | Proof of reuse (must change when middle is perturbed) |
|---|---|
| CacheBlend (vLLM) | Reordered-chunk request shows cached_tokens > 0 (or TTFT drop + LMCache server blend-hit counter) AND a content-perturbed chunk shows NO reuse. |
| FreeToken | `/v1/cache/status` hit count rises on boundary-aligned edit and not on mid-block edit; TTFT drops accordingly. |
| Prefix-only methods | N/A — non-prefix reuse cannot be demonstrated by construction. |

## 8. References (primary sources)

- SGLang LMCache connector README (MP mode, daemon, `--enable-lmcache`, `--lmcache-config-file`): https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/mem_cache/storage/lmcache/README.md
- LMCache CacheBlend (selective recomputation non-prefix): https://docs.lmcache.ai/kv_cache_optimizations/cacheblend.html
- LMCache blending (legacy in-process knobs): https://docs.lmcache.ai/kv_cache_optimizations/blending.html
- LMCache SGLang integration example: https://github.com/LMCache/LMCache/blob/dev/examples/sgl_integration/README.md
- LMCache issue #4071 (engine-driven hybrid KV unsupported): https://github.com/LMCache/LMCache/issues/4071
- LMCache PR #4073 (v1 uniform hybrid coverage, pending): https://github.com/LMCache/LMCache/pull/4073
- SGLang HiCache design: https://github.com/sgl-project/sglang/blob/main/docs/docs/advanced_features/hicache_design.mdx
- SGLang HiCache blog (prefix-only, hybrid/mamba state support via PR #21259): https://www.sglang.io/blog/hicache
- vLLM prefix caching (prefix-only): https://docs.vllm.ai/en/stable/design/prefix_caching/
- FreeToken models doc: https://raw.githubusercontent.com/FlashML-org/FreeToken/main/docs/models.md
- FreeToken paper (semantic anchors): https://arxiv.org/html/2608.16157v1
- FreeToken CLI: https://github.com/FlashML-org/FreeToken/blob/main/docs/cli.md
- Mooncake (storage/sharing layer only): https://kvcache-ai.github.io/Mooncake/deployment/kv-cache-sharing-and-isolation.html
- Campaign: `pins/SERVING-INVENTORY.md`, `pins/rollback-baseline.json`, `notes/VLLM-FEASIBILITY.md`, `notes/ENGINE-VLLM-ATTEMPT.md`, `notes/ENGINE-DOCS.md`
- HL-PILOT REPORT.md, CCS REPORT.md (historical, read-only)

## 9. Feasibility summary for the serving phase (≤288 calls)

- Candidate 1 (vLLM+CacheBlend) is the only path that can demonstrate non-prefix reuse. Budget ~12 calls for smoke + ~12 for negative control + ~12 for a second config = well within 288. If startup fails on hybrid, record and spend 0 calls.
- Candidate 2 (FreeToken) is exploratory; budget ≤30 calls including startup failure. Use contingency if a different model is required.
- Prefix-only methods (HiCache, mamba-radix, SGLang-LMCache) are candidates for the prefix-reuse comparison arm but must not be reported as non-prefix solutions.
