# LAUNCH-VLLM.md — exact launch guide for vLLM 0.27.1

> **Cost claim?** This guide is **current** for launch flags and mechanics. For the *measured* cost
> consequence of running on SGLang vs vLLM, read [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`): the
> engine, not the model, sets the per-turn uncached bill — **+1,225.18** tokens/turn (**2.6738x**).

**Scope:** research unit R-STACK. No live model requests were made. vLLM 0.27.1 is already
running at `serving-host` serving `qwen3.5-9b`. All facts come from the vLLM v0.27.1
source on GitHub (fetched via raw URLs) and the local live config. Unverified rows are marked
`unknown`.

**Base launch (qwen3.5-9b on vLLM 0.27.1):**

```bash
python -m vllm.entrypoints.openai.api_server \
  --model <QWEN3_5_9B_PATH> \
  --served-model-name qwen3.5-9b \
  --host 0.0.0.0 --port 8014 \
  --block-size 16 \
  --enable-prefix-caching \
  --max-num-batched-tokens 8192 \
  --gpu-memory-utilization 0.9
# add for cache-hit metering:
  --enable-prompt-tokens-details
```

---

## V1 — block size, prefix-match-unit, mamba shared-prefix checkpoint, prefix caching, max-num-batched-tokens

### `--block-size {16,64}`

**Exact command (add to base):**

```bash
... --block-size 16   # default
... --block-size 64
```

**Flag validity for this build:** `--block-size` exists in vLLM 0.27.1 (`DEFAULT_BLOCK_SIZE = 16`
in `vllm/config/cache.py`). Both 16 and 64 are accepted. [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/config/cache.py

**Memory cost:** larger block size (64) reduces per-block metadata overhead but increases
tail waste (up to 63 tokens per sequence). For prefix caching, 64-token blocks mean coarser
hit boundaries — a hit lands only on a 64-token boundary unless `--prefix-match-unit` is
set smaller.

**Expected startup failure:** if the model's head dimension is not divisible by the block
size, vLLM may error (exact text **unknown** — not captured from source).

**One-liner proving the flag took effect:**

```bash
# vLLM logs "Block size: 16" / "Block size: 64" at startup; or check:
curl -s http://HOST:PORT/v1/models
```

**Verdict: GO** for both 16 and 64. Source: vLLM v0.27.1 `cache.py` [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/config/cache.py

### `--prefix-match-unit 64`

**Exact command:**

```bash
... --prefix-match-unit 64
```

**Flag validity for this build:** `--prefix-match-unit` exists in vLLM 0.27.1 (in `CacheConfig`
and `arg_utils`). It sets the finest token boundary a prefix-cache hit may land on; defaults
to the GCD of the prefix-cacheable groups' block sizes. [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/config/cache.py

**Interaction:** with `--block-size 64`, the default `prefix-match-unit` is 64. Setting it
explicitly to 64 makes hits land on 64-token boundaries, matching the SGLang-side
`c128_page_size`-style granularity. The R-VLLM survey recommended 64 as the starting value.

**Memory cost:** none (boundary tuning only).

**One-liner proving the flag took effect:** startup log prints the configured prefix-match
unit (exact log line **unknown**).

**Verdict: GO.** Source: vLLM v0.27.1 `cache.py` + `arg_utils.py` [fetched].

### `--enable-mamba-shared-prefix-checkpoint`

**Exact command:** N/A — this flag does **not exist** in vLLM 0.27.1.

**Flag validity for this build:** verified absent. Grep of
`vllm/entrypoints/openai/cli_args.py` and `vllm/engine/arg_utils.py` at tag `v0.27.1`
returned no match for `enable-mamba-shared-prefix-checkpoint` / `mamba_shared` /
`shared_prefix_checkpoint`. [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/engine/arg_utils.py

**Implication:** in vLLM 0.27.1, hybrid Mamba state is checkpointed only on the Mamba block
grid (~1024 tokens) unless a shared-prefix checkpoint is used — but that capability is not
available in this build. Prefix caching for hybrid Mamba models is therefore limited to
block-grid boundaries. This is a **no-go** for the "shared prefix checkpoint" feature in
0.27.1; it was introduced in a later release.

**Verdict: NO-GO (not available in 0.27.1).** Source: vLLM v0.27.1 `arg_utils.py` [fetched].

### `--enable-prefix-caching`

**Exact command:**

```bash
... --enable-prefix-caching       # default True in vLLM V1
... --no-enable-prefix-caching    # to disable
```

**Flag validity for this build:** exists in vLLM 0.27.1 (`arg_utils.py` / `cli_args.py`).
Default is True in the V1 engine. [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/engine/arg_utils.py

**Memory cost:** prefix cache stores KV blocks in GPU memory; with `gpu-memory-utilization`
headroom, this is part of the KV pool (no separate allocation). Enabling it can reduce
effective KV capacity slightly due to cache overhead.

**One-liner proving the flag took effect:** startup log shows "Prefix caching is enabled"
(exact log line **unknown**).

**Verdict: GO.** Source: vLLM v0.27.1 `arg_utils.py` [fetched].

### `--max-num-batched-tokens`

**Exact command:**

```bash
... --max-num-batched-tokens 8192    # matches SGLang chunked_prefill_size
... --max-num-batched-tokens 16384   # higher for throughput on small models / large GPUs
```

**Flag validity for this build:** exists in vLLM 0.27.1. Chunked prefill is on by default
"whenever possible"; this flag caps the number of tokens per batched forward pass. The
vLLM docs recommend >8192 for optimal throughput on small models / large GPUs. [fetched]
https://docs.vllm.ai/en/v0.27.1/configuration/engine_args/ (version ambiguous — see note)

**Memory cost:** higher values increase peak activation memory during prefill; 16384 may
OOM on a loaded GPU. Keep ≤8192 when sharing the GPU with occamy.

**One-liner proving the flag took effect:** startup log shows "Max num batched tokens: N"
(exact log line **unknown**).

**Verdict: GO.** Source: vLLM v0.27.1 `arg_utils.py` [fetched].

---

## V2 — can vLLM 0.27.1 load a Qwen3.5-MoE hybrid NVFP4 (modelopt) checkpoint at all?

**Answer: likely YES, with medium confidence (source-level evidence only; no runtime
verification — hard constraint: 0 live model requests).**

**Evidence:**
1. Model registry: `Qwen3_5MoeForCausalLM` is registered in vLLM 0.27.1
   (`vllm/model_executor/models/registry.py`, lines 201–202). [fetched]
   https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/model_executor/models/registry.py
2. Quantization: `modelopt.py` and `modelopt_block_quant.py` exist in the v0.27.1
   quantization directory, so the modelopt (NVFP4) quantization path is present. [fetched]
   (directory listing via GitHub API)
3. The R-VLLM survey (v0.32.0 docs banner) noted flag drift risk — verify at runtime.

**Caveats (no-go-ish risks):**
- Hybrid Mamba prefix caching is limited in 0.27.1 (no `--enable-mamba-shared-prefix-checkpoint`),
  so Mamba state is checkpointed only on the ~1024-token Mamba block grid.
- NVFP4 + MoE + hybrid Mamba in a single forward pass may hit untested code paths in 0.27.1;
  the first real launch should be treated as a probe.

**Expected startup failure (if it fails):** model-load or quantization error; exact text
**unknown** (not captured).

**One-liner proving the flag took effect:**

```bash
curl -s http://HOST:PORT/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['id'])"
```

**Verdict: LIKELY GO (medium confidence)** for loading. Prefix caching for hybrid Mamba
is limited. Source: vLLM v0.27.1 `registry.py` + quantization dir [fetched].

### Cache-hit metering field — `prompt_tokens_details.cached_tokens`

**Confirmed for vLLM 0.27.1:** when `--enable-prompt-tokens-details` is set, the OpenAI
usage response includes `prompt_tokens_details.cached_tokens` (populated from
`num_cached_tokens` in the engine output). [fetched]
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/entrypoints/openai/completion/serving.py
https://raw.githubusercontent.com/vllm-project/vllm/v0.27.1/vllm/entrypoints/openai/chat_completion/serving.py

**Without `--enable-prompt-tokens-details`:** the field is not populated (null/absent).
**Known bug:** in recent vLLM versions the field is often null even with the flag; in 0.27.1
the serving code populates it only when `enable_prompt_tokens_details=True` AND
`num_cached_tokens is not None`. [fetched source above]

**One-liner verifying the meter works:**

```bash
curl -s http://HOST:PORT/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5-9b","messages":[{"role":"user","content":"hi"}]}' \
  | python3 -c "import sys,json; u=json.load(sys.stdin)['usage']; print(u.get('prompt_tokens_details'))"
```

### Memory cost of a second resident model on 128 GB GB10 alongside a 12.5 GB KV pool

**Scenario:** occamy (Qwen3.5-MoE NVFP4) is resident (weights 23.763 GB + KV 12.461 GB,
startup-available 46.203 GB). Add a second vLLM instance serving qwen3.5-9b.

**Estimate:**
- qwen3.5-9b weights: ~9 GB (FP8) to ~18 GB (BF16) — unknown format; verify checkpoint.
- vLLM `gpu-memory-utilization` default 0.9 would claim 90 % of 128 GB = 115 GB, which
  conflicts with occamy's ~36 GB. **Must lower it** for the second instance, e.g.
  `--gpu-memory-utilization 0.3` (~38 GB budget).
- After weights (~9–18 GB), ~20–29 GB remains for the second KV pool + activations.
- Total: occamy 36.2 GB + second instance 38 GB ≈ 74 GB, leaving ~54 GB headroom on 128 GB.
  Feasible, but monitor OOM. Marked as estimate — not measured.

**Verdict: GO** (feasible with lowered `gpu-memory-utilization`). Source: live config
`state/config/live-server-config.json` [read] + vLLM v0.27.1 `cache.py` [fetched].
