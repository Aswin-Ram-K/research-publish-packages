# LAUNCH-SGLANG.md — exact launch guide for SGLang `0.0.0.dev1+g4ccff141d`

> **Cost claim?** This guide is **current** for launch flags and mechanics. For the *measured* cost
> consequence of running on SGLang vs vLLM, read [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`): the
> engine, not the model, sets the per-turn uncached bill — **+1,225.18** tokens/turn (**2.6738x**).

**Scope:** research unit R-STACK. No live model requests were made; all facts come from the
local live config (`state/config/live-server-config.json`, U-GRID, sampled 2026-10-21) and
primary SGLang docs/source fetched during this unit. Unverified rows are marked `unknown`.

**Base (S0) launch — the live occamy server (Qwen3.5-MoE hybrid, NVFP4):**

```bash
python -m sglang.launch_server \
  --model-path <MODEL_PATH> \
  --served-model-name occamy-1.0 \
  --host 0.0.0.0 --port 30000 \
  --quantization modelopt_fp4 \
  --kv-cache-dtype fp8_e4m3 \
  --mem-fraction-static 0.45 \
  --max-running-requests 5 \
  --chunked-prefill-size 8192 \
  --max-prefill-tokens 16384 \
  --context-length 131072 \
  --page-size 1 \
  --mamba-radix-cache-strategy extra_buffer \
  --mamba-track-interval 256 \
  --max-mamba-cache-size 64 \
  --disable-chunked-prefix-cache false
```

Live memory baseline (from `live-server-config.json`): weights 23.763 GB, KV cache 12.461 GB,
startup-available 46.203 GB, token capacity 1,306,681 on a 128 GB GB10.

---

## S1 — `--page-size 64`

**Exact command (add to S0):**

```bash
... (S0 flags) --page-size 64
```

**Flag validity for this build:** `--page-size` is a documented SGLang server arg
(`"The number of tokens in a page."`, type int, default 1) — [fetched]
https://docs.sglang.ai/advanced_features/server_arguments.html

**Interaction with live params:**
- `c128_page_size` (live 16) is the *chunked-prefill* page size for the DeepSeek chunked
  prefix cache; it is independent of `--page-size`. Changing `--page-size` to 64 does not
  move `c128_page_size`.
- `_mamba_cache_chunk_size` (live 64) is a separate internal mamba parameter; `--page-size`
  does not change it. Only the KV pager granularity changes.
- `mamba_track_interval` (live 256) must be divisible by `page_size` when set; 256 % 64 = 0,
  so 64 is legal with the live config. If a non-divisible value is used, startup fails
  (exact error text not captured — **unknown**).

**KV waste of 64 vs 1:** with `page_size=64`, KV memory is allocated in 64-token pages, so
each sequence wastes up to 63 tokens of KV capacity (tail page). For long contexts this is
~1.5 % capacity loss; for short requests up to ~98 % of one page. Weights unchanged
(23.763 GB); effective KV capacity drops from 12.461 GB to ~12.27 GB.

**Expected startup failure:** none expected with the live config. If `mamba_track_interval`
is not divisible by 64, startup fails (error text **unknown**).

**One-liner proving the flag took effect (after launch):**

```bash
curl -s http://HOST:PORT/get_server_info | python3 -c "import sys,json; print(json.load(sys.stdin).get('page_size'))"
```

**Verdict: GO** (with tail-page waste caveat). Source: SGLang server_arguments docs [fetched]
https://docs.sglang.ai/advanced_features/server_arguments.html

---

## S2 — hierarchical cache (HiCache)

**Exact flags:**

```bash
... (S0 flags) \
  --enable-hierarchical-cache \
  --hicache-ratio 2.0 \
  --hicache-size 0 \
  --hicache-write-policy write_through \
  --hicache-io-backend kernel \
  --hicache-mem-layout page_first
# optional storage tier:
  --hicache-storage-backend <null|file|mooncake|...>
```

Flag reference (all [fetched] from server_arguments docs):
- `--enable-hierarchical-cache` / `--enable-hicache` — enable HiCache.
- `--hicache-ratio` (default 2.0) — ratio of host KV pool size to device pool size.
- `--hicache-size` (default 0, GB) — overrides `hicache-ratio` if set.
- `--hicache-write-policy` — `write_back` | `write_through` (default `write_through`).
- `--hicache-io-backend` — `direct` | `kernel` (default `kernel`).
- `--hicache-mem-layout` — `page_first` (default, from live config).
- `--hicache-storage-backend` — storage backend (live: `null`).

**Host-RAM requirement:** with `hicache-ratio 2.0` and the live device KV pool of 12.461 GB,
the host KV pool is ~2.0 × 12.461 ≈ **24.9 GB of host RAM**. If `hicache-size` is set
(e.g. 24), it overrides the ratio.

**Load-bearing question — does HiCache support hybrid mamba/linear-attention checkpoints
at all?**

**NO — not for hybrid mamba checkpoints in this build.** Evidence:

- GitHub issue #12826 (closed due to inactivity) comment by `riZZZhik` (2026-04-02):
  "Qwen 3.5 still doesn't support HiCache" with the runtime error:
  ```
  File ".../sglang/srt/mem_cache/hiradix_cache.py", line 97, in __init__
      raise ValueError(f"HiRadixCache only supports MHA and MLA yet")
  ValueError: HiRadixCache only supports MHA and MLA yet
  ```
  [fetched] https://github.com/sgl-project/sglang/issues/12826
- PR #21259 (merged 2026-04-14, "[HiCache & HybridModel] mooncake backend support DSA &
  mamba model") adds *mooncake storage-backend* support for mamba/DSA models, but does not
  confirm in-memory HiCache host-pool support for hybrid mamba. [fetched]
  https://github.com/sgl-project/sglang/pull/21259
- Current SGLang `main` `unified_radix_cache` supports MHA and hybrid-SWA host stacks and
  carries mamba components in the unified tree, but whether the in-memory HiCache host
  pool accepts a mamba/linear-attention model is not confirmed for build
  `0.0.0.dev1+g4ccff141d`.

**Memory cost (if it worked):** device KV 12.461 GB unchanged + ~24.9 GB host RAM.

**Expected startup failure (for occamy / any hybrid mamba checkpoint):**

```
ValueError: HiRadixCache only supports MHA and MLA yet
```

(confidence: medium — exact text from issue comments; the refactored `main` may phrase it
differently, and build `0.0.0.dev1+g4ccff141d` could not be resolved to a commit.)

**One-liner proving the flag took effect (would only run if startup succeeds):**

```bash
curl -s http://HOST:PORT/get_server_info | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('enable_hierarchical_cache'), d.get('hicache_ratio'))"
```

**Verdict: NO-GO for hybrid mamba checkpoints (occamy).** S2 is removed from the
maintenance window for occamy. It would only become viable after a build that enables
in-memory HiCache for hybrid/linear-attention models. Source: issue #12826 [fetched]
https://github.com/sgl-project/sglang/issues/12826

---

## S3 — chunked prefix cache disable

**Actual CLI arg name:** `--disable-chunked-prefix-cache` (confirmed; default `False`).
Description (docs): "Disable chunked prefix cache feature for deepseek, which should save
overhead for short sequences." [fetched]
https://docs.sglang.ai/advanced_features/server_arguments.html

**Exact command:**

```bash
... (S0 flags) --disable-chunked-prefix-cache
# or explicitly keep enabled:
... (S0 flags) --disable-chunked-prefix-cache false
```

**Flag validity for this build:** the arg exists and defaults to `False`.

**Hybrid legality:** the docs describe this feature as **DeepSeek-specific** ("for deepseek").
occamy is Qwen3.5-MoE hybrid, not DeepSeek. Whether the flag is accepted as a no-op or
rejected for a non-DeepSeek model is **unknown**. The live config records a discrepancy:
top-level `disable_chunked_prefix_cache = false` but `runtime_effective = true`, i.e. the
server internally enables chunked prefix cache regardless of the top-level flag (or the
top-level flag is misreported). This discrepancy is not explained by the docs.

**Memory cost:** none (compute/overhead optimization, not memory).

**Expected startup failure:** unknown — if passed to a non-DeepSeek hybrid model it may be
accepted (no-op) or may error. No error text captured.

**One-liner proving the flag took effect (compare top-level vs runtime-effective):**

```bash
curl -s http://HOST:PORT/get_server_info | python3 -c "import sys,json; d=json.load(sys.stdin); print('top:', d.get('disable_chunked_prefix_cache'), 'runtime:', d.get('disable_chunked_prefix_cache_runtime_effective'))"
```

**Verdict: UNKNOWN** for hybrid (Qwen3.5-MoE) models. Treat as DeepSeek-only. Source:
SGLang server_arguments docs [fetched] https://docs.sglang.ai/advanced_features/server_arguments.html

---

## S4 — dense control: launching `qwen3.5-9b` under SGLang

**Is qwen3.5-9b dense?** Yes — Qwen3.5-9B is a dense transformer (not MoE). The Qwen3.5
family ships dense variants at 4B/9B/27B and MoE variants at 35B-A3B/122B-A10B/397B-A17B.
Confidence: high (standard naming; web search confirms "4B dense model and a 35B
Mixture-of-Experts (MoE) model" for Qwen3.5).

Because it is dense, the mamba-specific flags from S0 do not apply. Dense-relevant launch:

```bash
python -m sglang.launch_server \
  --model-path <QWEN3_5_9B_PATH> \
  --served-model-name qwen3.5-9b \
  --host 0.0.0.0 --port 30001 \
  --kv-cache-dtype fp8_e4m3 \
  --mem-fraction-static 0.45 \
  --max-running-requests 5 \
  --chunked-prefill-size 8192 \
  --max-prefill-tokens 16384 \
  --context-length 131072 \
  --page-size 1
# add --quantization modelopt_fp4 ONLY if an NVFP4 checkpoint is available (unknown)
```

**Memory cost (estimates):**
- Weights: unknown for qwen3.5-9b (BF16 ~18 GB, FP8 ~9 GB, NVFP4 ~4.5 GB if available).
- KV pool: dense 9B uses full MHA attention, so KV per token is larger than occamy's MoE;
  at `mem-fraction-static 0.45` on 128 GB, expect ~15–20 GB KV (vs occamy's 12.461 GB).
  Marked as estimate — not measured.
- No host tier unless HiCache is enabled (and HiCache is MHA/MLA-only; dense MHA qualifies,
  so HiCache *would* be legal here — unlike S2 for occamy).

**Expected startup failure:** if `--quantization modelopt_fp4` is used but no NVFP4
checkpoint exists, startup fails (error text **unknown**). If the checkpoint path is wrong,
standard model-load error.

**One-liner proving the flag took effect:**

```bash
curl -s http://HOST:PORT/get_server_info | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model_path'), d.get('quantization'))"
```

**Verdict: GO** for dense qwen3.5-9b under SGLang (MHA, fully supported). NVFP4
availability is **unknown** — verify checkpoint format before adding `--quantization`.
Confidence: medium (SGLang model support for Qwen3.5 dense not verified from source for
this exact build, but the Qwen3 family is supported). Source: standard Qwen3.5 naming
(web search) + SGLang server_arguments docs [fetched].
