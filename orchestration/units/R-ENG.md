# R-ENG — other inference engines: cache & scheduling survey (literature only)

**Status:** done (2026-10-21) — 39 tool calls of 45, 0 live requests
**Purpose (one):** Deep web research on the inference engines that are **not SGLang and not vLLM** —
their cache granularity, cache features, scheduling, and the configuration each project ships as
production-stable — so the next phase can pick comparable serving setups. **Zero experiments.**
**Parent:** `session-b61634cb-606d-4220-9b7e-eeb2b9a9e2a7`

## Hard constraints (from card)
- **0 experiments, 0 live requests to Occamy (`192.168.2.168:8012`), no `.occamy.lock`, no connection.**
  Offline research only.
- No writes outside: `orchestration/units/R-ENG.md`, `docs/serving-options/R-ENG.md`,
  `orchestration/handoffs/R-ENG.json`. Touch nothing else in `docs/`.
- Bound: **max 45 tool calls**; parallel search bursts; `local_web_search` first, `local_web_crawl` on
  primary sources (NVIDIA docs/repos, `github.com/InternLM/lmdeploy`, `github.com/microsoft/DeepSpeed-MII`,
  `huggingface/text-generation-inference`, `NVIDIA/TensorRT-LLM`, `docs.nvidia.com/dynamo`, arXiv).
- **Prefer primary sources.** SEO comparison blogs (spheron, particula, atomic.chat, tensormesh,
  listicles) are **not evidence** — if no primary source is reachable, mark the claim `unverified`
  rather than cite the blog.
- Automated session: never ask the user; missing value → conservative default recorded in `assumptions`.

## Baseline under comparison (fixed, not to be changed)
One SGLang deployment, GB10-class single node, Qwen3.5-MoE **hybrid attention**, `max_model_len=131072`.
`page_size=1`, plain radix cache, `enable_hierarchical_cache=false`, `enable_lmcache=false`,
`chunked_prefill_size=8192`, `chunked_prefill_size=8192`, `uses_mamba_radix_cache=true`.
Measured: cache hits land on a **64-token grid**; no suffix recovery; all measurements exact-prefix.

## Method
Parallel search bursts → primary-doc crawls → per-engine record:
default/stable config · cache granularity + what determines it · cache features (prefix reuse /
hierarchical / offload / shared-prefix) · strongest **measured** claim (number + workload + URL) ·
runnability on a single GB10-class node with a hybrid-attention MoE
(`yes` / `needs-restart` / `needs-cluster` / `not-supported-for-this-model`) · the **one flag to change
first** to test its cache behaviour.

Deliverable `docs/serving-options/R-ENG.md`: per-engine table, then
"the three non-SGLang setups that are both stable AND informative to benchmark first".

## Tool-call ledger (running)
| # | call | outcome |
|---|------|---------|
| 1 | `bash` pwd/ls + `read AGENTS.md` | contract read; workspace has 604 unit cards |
| 2 | `bash` ls `docs/serving-options/` | dir exists, **empty** — no prior notes to collide with |
| 3 | `read` `orchestration/STATUS.md` head | SearXNG flagged degraded; Occamy up but off-limits to me |
| 4 | `read` `orchestration/units/R-SGL.md` | sibling = SGLang-native options; no overlap with mine |
| 5 | `read` `orchestration/units/R-CROSS.md` | sibling = engine-independent techniques; LMCache etc. theirs, not mine |
| 6 | `write` this card | card persisted before research |
| 7–10 | `local_web_search` ×4 (TRT / LMDeploy / TGI / FastGen) | **SearXNG noisy** — bing spam (Walgreens, Seattle restaurants) mixed into every query; usable hits were the yep/google ones → every fact re-fetched from the primary URL |
| 11–14 | `local_web_crawl` ×4 (TRT reuse, TRT kvcache, LMDeploy turbomind_config, TGI launcher) | **crawl returns nav-dominated text and truncates before the body** on docs sites — repeated version-picker links ate the whole budget. LMDeploy `_sources/*.md` worked |
| 15–18 | `web_fetch` ×4 (LMDeploy `_sources` md, TGI chunking md, TRT docs md, LMDeploy kv_quant md) | **the winning path**: raw markdown of primary docs. TRT `docs/source/advanced/*.md` 404 (path differs) |
| 19 | `bash` GitHub contents API | 404 — TRT-LLM docs dir name is not `docs/source/advanced` |
| 20–21 | `bash` + inline python (attempts) | helper `/tmp/px.py` does **not persist between bash calls** (fresh sandbox) → inlined the extractor; net 2 wasted calls |
| 22–32 | `bash` inline fetch+strip of primary docs (11 pages) | TRT kv-cache-reuse / kvcache / memory / IFB-scheduler / spec-decode / trtllm-serve CLI / early-reuse blog; LMDeploy messages.py + README; TGI launcher + paged-attention; Dynamo blog + docs landing; llama.cpp server README; arXiv 2401.08671 |
| 33–34 | `bash` hybrid-support probes (TRT attention, LMDeploy supported-models table, TGI supported models) | Qwen3.5 listed by LMDeploy; no vendor documents our hybrid MoE → `unverified`, not a guess |
| 35 | `write` `docs/serving-options/R-ENG.md` | deliverable: per-engine mechanics table, per-engine stable-config/claim/runnability sections, the three benchmark picks, and a "could not verify" list |
| 36–39 | card edits + handoff + JSON validation + report to parent | forced report-back |

## Findings that changed the picture
1. **No standard block size**: TRT-LLM **128** default (build-time, power of 2, `--tokens_per_block 32`, blog: 64→**2**),
   LMDeploy **64** (`cache_block_seq_len`, and reuse quantum *is* the block), TGI **not published**, llama.cpp **no blocks**.
2. **LMDeploy prefix caching ships OFF** (`enable_prefix_caching=False`) — the opposite of our assumption that
   prefix caching is table stakes; it is opt-in there.
3. **TRT-LLM is the only engine that can put a reuse boundary inside a 64-token block** (2-token blocks,
   +7 % TTFT on H100/Llama-70B) — the sharpest available test of whether our 64-grid is an SGLang artifact.
4. **Hypothesis recorded, not claimed:** our 64-grid is more likely the *hybrid-attention state cache*
   (`uses_mamba_radix_cache=true`) than the pager (`page_size=1`); decisive test is a dense model on the same
   SGLang deployment. Left for a later unit — no experiment ran here.

