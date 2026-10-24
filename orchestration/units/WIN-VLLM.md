# WIN-VLLM — vLLM 0.27.1 pager/flag space on a dense-but-hybrid 9B

**Card.** Engine unit `WIN-VLLM` of the context-cache batch. Characterise the vLLM 0.27.1
prefix-cache pager and flag space, and compare its grid law with SGLang's
`64*floor((L-1)/64)` on the same battery.

**Write paths:** `experiments/context-cache/cells/WIN-VLLM/**`, `state/config/qwen9b-*.json`,
`state/config/V*-server-info.json`, `orchestration/units/WIN-VLLM.md`,
`orchestration/handoffs/WIN-VLLM.json`, `experiments/context-cache/.occamy.lock` (held during
batteries only).

**Hard bound:** 900 live requests. Used **692** (V1 358, V2 312, V3 22); every row `status 200`.
Launch attempts: V1, V2 (NVFP4 9B at block 64 / 16) and V3 (occamy on vLLM, 40 min / 3 attempts).

## What was launched

Production `gx10-qwen9b` was stopped (never removed) and each variant ran on `:8014->30000` with
the production mounts copied verbatim plus `/home/zer0null/models/qwen3.5-9b-nvfp4:/model-nvfp4:ro`,
the production command line copied verbatim from `docker inspect`, and only
`--model`, `--quantization modelopt_fp4`, `--block-size` and `--enable-prompt-tokens-details`
differing. After every variant: `docker start gx10-qwen9b`, then health/models/metrics proof
(`logs/<ID>-restore.json`). `gx10-occamy-nvfp4` (`:8012`) was never touched; its health was
checked after every step.

## Result in one line each

- **V1** (`--block-size 64`): the engine resolved `block_size=1088` (`mamba_block_size=64`), so the
  flag does **not** set the effective block. Instrument works. Law `1088*(floor(L/1088)-1)` for
  `L mod 1088 != 0`, **0** at exact multiples — 20/20 points; SGLang's
  `64*floor((L-1)/64)` matches 0/20. Battery (4 arms x 71 turns): hit 0.8689-0.8691,
  uncached 2229-2233 tokens/turn, gcd 1088.
- **V2** (`--block-size 16`): resolved `block_size=1056` (`mamba_block_size=16`) — exactly what
  production derives with no flag. Instrument works. Same law form at 1056 — 11/11 points.
  Battery: hit 0.8679-0.8687, uncached 2237-2250 tokens/turn, gcd 1056.
- **V3** (occamy NVFP4 MoE on vLLM 0.27.1): **attempt 1 failed** on the production MTP flag —
  `RuntimeError: No Qwen3Next layer found in the model.layers.` (`qwen3_5_mtp.py:321` ->
  `qwen3_next.py:754`). Attempt 2 without `--speculative-config` **loaded** (22.41 GiB, 142 s) and
  served `occamy-1.0` on `:8020`; resolved block 2096, law `2096*floor(L/2096)` (5/5 points, **no**
  one-block deficit — the deficit is a property of the 9B configuration, not of vLLM).
- **Against SGLang**: S0/page_size 1 at 32k records hit 0.9592 and 721.9 uncached tokens/turn; the
  vLLM 9B battery pays ~3.1x that. Different model, so this is a stack-level contrast, not a
  same-weights one.

## Method notes

- The gate prompt must span ≥2 resolved blocks: a 211-token probe returns `cached=0` because
  nothing is a complete block, which is the engine's rule, not an instrument failure. Both gates
  are kept in `rows.jsonl` (salt `gate-win-vllm` = negative control, `gate-large-win-vllm` = gate).
- The 64k depth is **not runnable** under the launch invariant `--max-model-len 32768`; the 32k
  battery is truncated at turn 71/74 because turn 72 renders a ~32,919-token prompt. The
  truncation is computed offline from `/tokenize` (no request spent on an unserveable turn) and
  recorded in `logs/battery-plan.json`.
- Battery prompts are byte-identical to G3's (same corpus, salts 3201-3204, renderer), so vLLM
  rows and SGLang rows are comparable prompt-for-prompt.
