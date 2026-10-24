# DENSE-SGL — qwen3.5-9b under SGLang (the missing 2x2 cell)

Config P1, container `ds-sgl-qwen9b`, SGLang image
`sha256:72457f09d20efcd34cdf005f71811a25efe771ccc5dd0c93f8ac112569e00ad7`,
model `/home/zer0null/models/qwen3.5-9b-nvfp4` (NVFP4, `modelopt_fp4`), tp 1,
context-length 65536, mem-fraction-static 0.22. Served as `qwen3.5-9b`.
Prompts byte-identical to WIN-VLLM (seeds 3201-3204) and WIN-SGL (salts/glyphs).

Live run: 894 requests, **all HTTP 200, zero non-200, exit 0**.
- gate 2 + grid 22 + probe 12 = 36 single-shot calibration rows
- battery 860 = 4 arms (R/A/C/H) x 32k(71 servable of 74) + 64k(144 servable of 148)
Elapsed 435s. Request cap 950; used 894. Lock held for the live phase.

## 1. The cache law is ENGINE-determined, not model-determined

This is the headline. The grid/probe rows (identical to WIN-VLLM's probe targets) fit

    cached(L) = L - (L mod 64)          gcd of all cached values = 64

decisively, and **reject** the hybrid-block law that vLLM produced for this exact
same model weights. SGLang page_size=1 (confirmed in server-info) still reports
cached in clean multiples of 64 — the same page-64 law occlamy showed under
SGLang in WIN-SGL/G3.

| L | SGLang cached (this cell) | vLLM cached (WIN-VLLM, same model) |
|-----|---------------------------|-------------------------------------|
| 67  | 64                        | 0 (hybrid lag)                      |
| 129 | 128                       | 0                                   |
| 193 | 192                       | 128                                 |
| 502 | 448                       | 320                                 |
| 1002| 960                       | 640                                 |
| 1102| 1088                      | 640                                 |
| 1166| 1152                      | 1088                                |
| 1294| 1280                      | 1088                                |

vLLM on this model caches 1056/1088-step chunks (`1056*(floor(L/1056)-1)` family,
a `mamba_block_size` artifact of the hybrid attention/mamba layers). SGLang ignores
that structure and pages at 64 regardless. **Same weights, same GB10, same 64k
context — two engines report fundamentally different cached-token geometry.**

Consequence for the 2x2 matrix: the engine column dominates the cache law; the
model row does not. Any prefix-cache reasoning that assumes the engine reports the
model's native block granularity is wrong.

## 2. Battery: hit rate and uncached/turn

| arm | policy                    | n   | hit     | uncached/turn |
|-----|---------------------------|-----|---------|---------------|
| R   | summarise_in_place        | 215 | 0.9730  | 754.5         |
| A   | append_note               | 215 | 0.9733  | 746.5         |
| C   | none (append-only)        | 215 | 0.9731  | 751.1         |
| H   | hybrid                    | 215 | 0.9734  | 742.8         |
| all |                           | 860 | **0.9732** | **748.7**   |

Max depth reached 65176 tokens (64k arm, servable 144/148).

Cross-cell comparison (same model qwen3.5-9b, different engine):

- DENSE-SGL (SGLang): hit 0.9732, uncached/turn 748.7
- WIN-VLLM (vLLM 0.27.1): hit 0.868-0.869, uncached/turn ~2230

SGLang cuts uncached work per turn ~3x on the same weights, because it reuses
prefix at 64-token granularity where vLLM's hybrid mamba-block reporting leaves
~2230 tokens uncached per turn. Compaction arm differences are within noise
(0.9730-0.9734): at this hit rate the compaction policy no longer matters — the
engine's prefix reuse dominates.

## 3. Verification

- rows.jsonl: 894 rows, every one `status=200`, fsynced per append.
- grid law fit: 846/852 cached>0 rows deviate from L-L%64 only where a repeated
  prefix shorter than the full prompt applies (grid probes with warm cache);
  gcd of the entire cached set = 64 exactly.
- Production restored: `restore('P1')` -> ok=True, occamy_8012=200,
  qwen9b_vllm_8014=200, config_ok=True (id + max_model_len + block_size 1056).
  The `ds-sgl-qwen9b` variant container was stopped and removed; `gx10-qwen9b`
  was `docker start`-ed back (never removed).
- Lock `.occamy.lock` released after the live phase.
