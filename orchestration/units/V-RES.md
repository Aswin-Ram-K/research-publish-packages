# V-RES — independent re-fetch of the four research lanes' load-bearing external claims

**Verifier unit. Author of none of R-SGL / R-VLLM / R-CROSS / R-PROD.** Automated session: no user questions, no
input wait. 0 live requests to Occamy; `.occamy.lock` never touched. All evidence below is re-fetched from the
primary source by this unit on 2026-10-21 (curl of docs / raw GitHub markdown / code / arXiv abs, then local
grep of the fetched bytes — not a re-read of the lane notes' own citations).

**Hard bound:** 30 tool calls. **Write paths (mine alone):** `orchestration/units/V-RES.md`,
`orchestration/handoffs/V-RES.json`, plus conditional append to `orchestration/VERDICTS.md`.

**Method note (reusable):** `docs.sglang.io` HTML *is* fetchable in full (1.6 MB, 96,788 chars of text after tag
strip) — the lanes' "mkdocs nav truncation" was a crawler symptom, not a page limit. Raw markdown/code paths
(`docs/cookbook/autoregressive/Qwen/*.mdx`, `vllm/config/cache.py`) are cheaper and exact. GitHub
`git/trees/main?recursive=1` found the real file paths without guessing (SGLang 12,649 entries, Dynamo 9,019).

## Checks

| # | Claim | Verdict | Primary source re-fetched |
|---|---|---|---|
| 1 | `--mamba-radix-cache-strategy extra_buffer` real, paired with `--page-size 64` | **pass** | docs.sglang.io/advanced_features/server_arguments.html; raw `docs/cookbook/autoregressive/Qwen/Qwen3.5.mdx` |
| 2 | `FLA_CHUNK_SIZE=64` **and** `--mamba-track-interval` (recipes 64) are one grid | **overstated** | server_arguments.html (default **256**); Qwen3.5.mdx:134; Qwen3.8-Flash-Next.mdx |
| 3 | vLLM `DEFAULT_BLOCK_SIZE=16`, `--prefix-match-unit`, `--enable-mamba-shared-prefix-checkpoint` | **pass** | raw `vllm/config/cache.py:182`; `vllm/engine/arg_utils.py:1424,1435`; `docs/features/automatic_prefix_caching.md:16-35` |
| 4 | Dynamo Qwen3.6-35B-A3B single-GPU SGLang flag set + 156.07 ms / 3035.98 tok/s/GPU | **pass** (one scope correction) | raw `recipes/qwen3.6-35b-a3b/sglang/agg-gb200-mtp/deploy.yaml`; `docs/fern/pages/recipes/_catalog/recipes/qwen3-6-35b-a3b.yaml:60` |
| 5 | HiCache "up to 6× / 80%" as the headline win | **overstated** | lmsys.org/blog/2025-09-10-sglang-hicache/ (wording exact; **zero** occurrences of "hybrid" or "Mamba") |
| 6 | α=0.038 sequential vs 0.68 parallel (arXiv:2605.01106) | **overstated** | arxiv.org/abs/2605.01106 abstract (numbers exact; mechanism is *component-aware self*-speculation, not MTP) |

## 1 — flag and pairing: pass

`server_arguments.html`: "`--mamba-radix-cache-strategy` The strategy to use for mamba scheduler. `auto` currently
defaults to `no_buffer`. … 2. `extra_buffer` supports overlap schedule by allocating extra mamba state buffers …
2a. `extra_buffer` is strictly better for non-KV-cache-bound cases". `Qwen3.5.mdx:134`: "**V2 (`extra_buffer`)**:
Enables overlap scheduling and branching point caching with `--mamba-radix-cache-strategy extra_buffer
--page-size 64`." The flag, the value, and the pairing are all verbatim in the primary docs. The "our
`extra_buffer` + `page_size=1` is undocumented" consequence stands. R-SGL quoted "strictly superior" where the
docs say "strictly better" (Qwen3.5 cookbook) — cosmetic, not load-bearing.

## 2 — the two 64s: overstated (the only check that changes a design decision)

- `FLA_CHUNK_SIZE` = 64: **reproduced**. `Qwen3.5.mdx:134`: "`--page-size` must satisfy `FLA_CHUNK_SIZE %
  page_size == 0` or `page_size % FLA_CHUNK_SIZE == 0` (`FLA_CHUNK_SIZE` is currently 64)."
- `--mamba-track-interval`: **exists**, but "The interval (in tokens) to track the mamba state during decode. Only
  used when `--mamba-radix-cache-strategy` is `extra_buffer`. Must be divisible by `page_size` if set, and must be
  >= `speculative_num_draft_tokens` when using speculative decoding. **256** Type: int". Default is **256**, not 64.
- Only one of three cookbooks sets 64: `Qwen3.8-Flash-Next.mdx` — "`--mamba-track-interval 64`: **the default of 256
  tokens** satisfies the constraints … at the cost of **coarser prefix-cache reuse of the recurrent state**."
  `Qwen3.5.mdx` and `Qwen3.8.mdx` never set it (0 and 1 occurrences, prose only).

So the two 64s are **two independent knobs that coincide only when a recipe deliberately picks 64**; the shipped
grid is 256. R-SGL's parenthetical "(published Qwen3.8 recipes use 64)" is true for Flash-Next only. The
mechanism survives as a *hypothesis* (the docs themselves frame 64 as "finer reuse vs ~40% smaller KV pool", which
is the right direction), but the default-256 fact is a free discriminator: **if the live server never set
`--mamba-track-interval`, the mamba grid is 256 and cannot produce `64*floor((L-1)/64)`.** That is readable from
`/get_server_info` / the startup argv with **0 restarts** — do that before any page-size sweep.

## 3 — vLLM: pass

`cache.py:182`: `DEFAULT_BLOCK_SIZE: ClassVar[int] = 16`. `arg_utils.py:1424` registers `--prefix-match-unit`,
`:1435` registers `--enable-mamba-shared-prefix-checkpoint`. `automatic_prefix_caching.md:18`: "With prefix caching
enabled, Mamba state is stored only on the Mamba block grid, so a prefix-cache hit can resume only at a block
boundary. `--enable-mamba-shared-prefix-checkpoint` also stores a checkpoint at the shared-prefix junction".
`:33`: "`--prefix-match-unit` … sets the granularity at which prefix-cache keys are computed. When unset it
defaults to the greatest common divisor of the prefix-cacheable KV cache group block sizes." Names and meanings
match R-VLLM. **Omitted relaxation:** the checkpoint is "off by default, and takes effect only when … EAGLE/MTP
speculative decoding on the Mamba group … `--prefix-match-unit` smaller than the Mamba block size". R-VLLM never
states the MTP precondition — which matters, because check 6 is about whether MTP is worth running at all.

## 4 — Dynamo manifest: pass, with a simulated-acceptance caveat

Real published manifest, not a blog paraphrase: `recipes/qwen3.6-35b-a3b/sglang/agg-gb200-mtp/deploy.yaml`, image
`nvcr.io/nvidia/ai-dynamo/sglang-runtime:1.4.0`, `replicas: 1`, `nvidia.com/gpu: "1"`, flags verbatim —
`--tp-size 1`, `--attention-backend trtllm_mha`, `--moe-runner-backend flashinfer_cutlass`, `--kv-cache-dtype
fp8_e4m3`, `--mamba-radix-cache-strategy extra_buffer`, `--speculative-algorithm EAGLE 3/1/4`, and no
page-size / mem-fraction / chunked-prefill override. Numbers are published in the catalog: "summary: 3035.98
output tok/s/GPU, 111.47 user tok/s P50, TTFT P50 156.07 ms at concurrency 32 (3,541-request agentic trace,
**simulated acc_len=3.3153** from SpeedBench coding)"; the model-recipes table has the same GB200 row 3,035.98 /
156.07 ms next to `agg-gb200-mtp/deploy.yaml`. Correction to record: the benchmark runs with a **simulated**
speculative acceptance length (`SGLANG_SIMULATE_ACC_LEN`), so 156.07 ms is a modelled projection, not a measured
EAGLE run — cite it as "published recipe target under simulated acc_len 3.32", not as a served measurement. Also
corroborates R-PROD §326: the Qwen3.8 cookbook says naming `trtllm_mha` explicitly "returns early" and "drops that
paired page size", so this manifest runs page size 1 by construction.

## 5 — HiCache 6×/80%: overstated (scope, not wording)

Wording is the blog's own: "In our measurements, HiCache achieved up to 6× throughput improvement and up to 80%
reduction in TTFT, closely mirroring the results reported by the community." But the same page's evidence base is
dense/MLA: "we tested the DeepSeek-R1-671B model under PD-disaggregated deployment" (Ant Group, 84% TTFT
reduction) and Novita's "Qwen3-Coder-480B" (TTFT −56%, 40%→80% hit rate). The strings "hybrid" and "Mamba" occur
**zero times** on the page. So the 6×/80% is a DeepSeek-R1-class result, **not** a GDN-hybrid result; both lanes use
it as the phase headline without that label. Keep it only as "published for dense/MLA 671B-class models under
HiCache + external storage"; it is not evidence that a host tier recovers the suffix reuse a GDN hybrid loses.

## 6 — speculation: numbers pass, the inference does not

Abstract verbatim: "Parallel hybrids achieve acceptance rates of alpha = 0.68 at draft length k=2 under greedy
decoding, while sequential hybrids yield only alpha = 0.038 -- an 18x gap". Title: "Component-Aware Self-Speculative
Decoding in Hybrid Language Models"; the mechanism is "isolating the SSM/linear-attention subgraph as a zero-cost
internal draft" on **Falcon-H1 (parallel)** and **Qwen3.5 (sequential)**. **Adjudication of the R-SGL/R-CROSS
contradiction: the evidence does not support either headline as written, and it is closer to R-SGL.** 0.038 is an
acceptance rate for *component-aware self-speculation*, a drafterless scheme — not for MTP/NEXTN, a trained
multi-token head the paper never tests. The paper also reports, on the same sequential family, "For sequential
hybrids, generic LayerSkip achieves 12x higher acceptance rates than the component-aware strategy" (≈0.46, i.e.
usable). R-CROSS's "on our model family it buys almost nothing" therefore over-generalises a negative result about
one drafting mechanism into a verdict on all speculation; R-SGL's "gate NEXTN/MTP on confirming the checkpoint
ships MTP weights" is the position the evidence supports. Consequence for check 3: vLLM's shared-prefix checkpoint
*requires* EAGLE/MTP, so "MTP is not a lever" and "use `--enable-mamba-shared-prefix-checkpoint`" cannot both be
adopted as written.

## Not reproducible / unverifiable by this unit

- The NVIDIA developer blog URL the R-PROD commands cite
  (`developer.nvidia.com/blog/full-stack-optimizations-for-agentic-inference-with-nvidia-dynamo/`) contains **none**
  of the flag strings or numbers (24,900 chars of text, 0 hits for `trtllm_mha`, `156.07`, `Qwen3.6`). The claim is
  nevertheless true — via the Dynamo repo manifest and catalog, not via that blog. Attribution in the lane note is
  the thing that is wrong, not the fact.
- SGLang's `FLA_CHUNK_SIZE` constant was not located in source from the cookbook text alone (the docs state it; no
  source path was opened for it). Docs-level evidence only.
