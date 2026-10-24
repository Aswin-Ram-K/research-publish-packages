# R-PROD — production serving configurations (offline research)

**Parent:** session-b61634cb-606d-4220-9b7e-eeb2b9a9e2a7
**Purpose (one):** collect concrete, stable, widely-deployed LLM-serving configurations with cache
settings spelled out, so the baseline (single SGLang, GB10-class, Qwen3.5-MoE hybrid attention,
`page_size=1`, plain radix cache, `chunked_prefill_size=8192`, no HiCache, no LMCache) can be compared
against what production teams actually run. **No experiments. 0 live requests. No Occamy. No lock.**

## Hard bound
Max **45 tool calls**, parallel search bursts. Kill condition: if a config cannot be pinned to a
primary source (vendor doc / team blog / stack repo / official benchmark recipe) in 3 tries, drop it
and record `reported-only` at most. Offline only: `local_web_search` → `local_web_crawl` of primary
sources.

## Write paths (mine alone)
- `orchestration/units/R-PROD.md` (this card)
- `docs/serving-options/R-PROD.md` (the note)
- `orchestration/handoffs/R-PROD.json`

## Deliverable shape
1. Table of reference configs: team+URL, exact cache/scheduling flags quoted, workload tuned for,
   measured number if any, single-GB10 delta, stability signal (`production` / `benchmark-only` /
   `reported-only`).
2. "The five configurations to reproduce first, ranked by stability × informativeness".
3. Evidence line: sources checked, configs with exact flags, primary sources, tool calls.

## Progress log
- [x] card written
- [x] search burst (vLLM/llm-d, SGLang/HiCache, Dynamo, MLPerf, agentic hit-rate reports) — 4 queries
- [x] primary-source crawls — 24 fetches (vendor docs/blogs, stack repos, helm values, deploy manifests, benchmark recipes)
- [x] note + ranked five — `docs/serving-options/R-PROD.md`
- [x] handoff + parent message

## Result
Status: **done**. 32/45 tool calls used. 11 configs with exact flags. The decisive finding for the
next phase: every production recipe for a hybrid (GDN/Mamba) model sets a hybrid-specific cache
strategy (`--mamba-radix-cache-strategy extra_buffer` in the Dynamo recipe) — our baseline runs a
plain radix cache on a hybrid model, which is the largest divergence from all collected configs and a
plausible cause of the missing suffix recovery. Second finding: the reference production stack turns
`enablePrefixCaching` OFF when an external cache (LMCache) owns the KV — cache ownership must not be
split. Third: `--mem-fraction-static` has no published numeric floor; production recipes either leave
the default or run 0.85 with `available_gpu_mem` in 5–8 GB, never a hand-picked value near the
computed minimum (our 0.500 vs 0.4993 case).
