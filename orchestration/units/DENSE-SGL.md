# DENSE-SGL — qwen3.5-9b under SGLang (the missing 2×2 cell)

**Unit:** DENSE-SGL · **Status:** done · **Date:** 2026-10-23
**Write paths:** `experiments/context-cache/cells/DENSE-SGL/**`, `state/config/ds-*.json`, this card, `orchestration/handoffs/DENSE-SGL.json`
**Lock:** `experiments/context-cache/.occamy.lock` held for the live phase, released after.

## Objective

Fill the missing cell of the 2×2 model/engine matrix: run qwen3.5-9b (NVFP4) under
**SGLang**, the one combination not yet measured. Done cells: occamy×SGLang (G3/WIN-SGL),
qwen9b×vLLM (WIN-VLLM V1/V2), occamy×vLLM (WIN-VLLM V3). Prompts byte-identical to the
sibling cells so rows pair across engines.

## What ran

Config P1, container `ds-sgl-qwen9b`, SGLang image
`sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7`, model
`/home/zer0null/models/qwen3.5-9b-nvfp4`, tp 1, context-length 65536, mem-fraction-static 0.22,
served as `qwen3.5-9b`, port 8014 (production vLLM stopped, then restored).

Live run: **894 requests, every one HTTP 200, exit 0**, elapsed 435 s. Request cap 950.
- gate 2 + grid 22 + probe 12 = 36 calibration rows
- battery 860 = 4 arms (R/A/C/H) × 32k(71 servable of 74) + 64k(144 servable of 148), max depth 65176 tokens

## Headline finding — the cache law is ENGINE-determined

SGLang reports `cached(L) = L − (L mod 64)`, gcd of all cached values = **64**, with
page_size=1. This is the *same* page-64 law occlamy showed under SGLang (WIN-SGL/G3),
and it **rejects the hybrid 1056/1088-step law that vLLM produced for this exact same
model weights.** Same weights, same GB10, same 64k context — two engines, two different
cached-token geometries.

| L | SGLang cached | vLLM cached (same model) |
|---|---|---|
| 67 | 64 | 0 |
| 129 | 128 | 0 |
| 193 | 192 | 128 |
| 502 | 448 | 320 |
| 1002 | 960 | 640 |
| 1102 | 1088 | 640 |
| 1294 | 1280 | 1088 |

The vLLM numbers follow `1056*(floor(L/1056)−1)` (a `mamba_block_size` artifact of the
hybrid attention/mamba layers); SGLang ignores that structure and pages at 64 regardless.
**The engine column dominates the cache law; the model row does not.** Any prefix-cache
reasoning that assumes the engine reports the model's native block granularity is wrong.

## Battery

| arm | policy | n | hit | unc/turn |
|---|---|---|---|---|
| R | summarise_in_place | 215 | 0.9730 | 754.5 |
| A | append_note | 215 | 0.9733 | 746.5 |
| C | none | 215 | 0.9731 | 751.1 |
| H | hybrid | 215 | 0.9734 | 742.8 |
| all | | 860 | **0.9732** | **748.7** |

Cross-cell, same weights, different engine: WIN-VLLM (vLLM 0.27.1) hit 0.868–0.869,
uncached/turn ~2230. SGLang cuts uncached work per turn ~3× on identical weights, because
it reuses prefix at 64-token granularity where vLLM's hybrid mamba-block reporting leaves
~2230 tokens uncached per turn. Compaction-arm differences are inside noise (0.9730–0.9734):
at this hit rate the compaction policy no longer matters — engine prefix-reuse dominates.

## Production restore

`restore('P1')` → ok=True; occamy_8012=200, qwen9b_vllm_8014=200, config_ok=True
(id + max_model_len + block_size 1056). Variant container `ds-sgl-qwen9b` stopped and
removed; `gx10-qwen9b` restored via `docker start` (never removed). Lock released.

## Artifacts

- `experiments/context-cache/cells/DENSE-SGL/rows.jsonl` — 894 rows, fsynced per append
- `experiments/context-cache/cells/DENSE-SGL/analysis.md` — full analysis
- `experiments/context-cache/cells/DENSE-SGL/dense_sgl_cell.py`, `launch_dense_sgl.py` — cell code
- `experiments/context-cache/cells/DENSE-SGL/logs/` — P1-launch, P1-summary, battery plans, capture-pre
- `state/config/ds-p1-server-info.json`, `state/config/ds-server-facts-p1.json`
