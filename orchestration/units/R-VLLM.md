# R-VLLM — vLLM / LMCache / Mooncake serving options (offline research)

**Status:** done (card written during the run; note + handoff are the artifacts).

## Purpose (one only)
Offline web research: what vLLM and the LMCache / Mooncake ecosystem offer at the
cache and serving layer, and the measured performance each claims, so a later phase can
pick serving setups comparable to our SGLang 64-token-grid baseline.
**No experiments. Zero contact with the Occamy server (no requests, no lock, no connection).**

## Hard bound
- Max 40 tool calls. Actual: see handoff `evidence.commands` length.
- Offline only: `local_web_search` for discovery, `local_web_crawl` / `web_fetch` on primary
  sources (docs.vllm.ai, raw GitHub docs + config source, arXiv, llm-d).
- Stop condition: if a primary source could not be fetched in two attempts, record the gap
  and move on rather than substituting a summary site.

## Write paths (mine alone)
- `orchestration/units/R-VLLM.md` (this card)
- `docs/serving-options/R-VLLM.md` (the note)
- `orchestration/handoffs/R-VLLM.json` (the handoff)
Touched nothing else; `docs/serving-options/` created by me.

## Method
1. Parallel `local_web_search` bursts to locate primary URLs (6 queries in one block).
2. Primary fetches preferred as **raw Markdown / RST / Python source from the upstream repo**:
   `docs.vllm.ai` HTML pages return a ~10 KB mkdocs nav before the body, so `local_web_crawl`
   truncates before any content — measured twice, lesson recorded. Raw
   `raw.githubusercontent.com/vllm-project/vllm/main/docs/...` worked first try.
3. `vllm/config/cache.py` read directly to pin the block-size default and the prefix-match
   semantics to source rather than prose.
4. Numbers only from the paper abstract, the upstream README, or the upstream docs. Vendor
   blog claims kept separate and labelled.

## Coverage checklist
1. vLLM APC: block size, hash chain, granularity — **covered**
2. KV connector / transfer, backend list — **covered**
3. LMCache: architecture, tiers, compression, numbers, cost — **covered**
4. Mooncake: architecture, transfer engine, FAST'25 result, drop-in vs whole-system — **covered**
5. Disaggregated P/D in vLLM + cache economics — **covered**
6. Prefix/KV-aware routing (production stack, llm-d; AIBrix **not verified** — flagged as gap)
7. Speculative decoding (eagle3 / ngram / suffix / mtp), KV footprint + reuse interaction — **covered (qualitative only)**
8. Chunked prefill + interaction with prefix caching — **covered**

## Notes to self
- The single most load-bearing finding is `DEFAULT_BLOCK_SIZE = 16` in
  `vllm/config/cache.py` plus `prefix_match_unit` ("the finest token boundary a prefix-cache
  hit can land on"). Our 64-token grid is not vLLM's default grid, and for a hybrid-attention
  model the Mamba state may only checkpoint on a much coarser grid.
- Deliberately did not benchmark anything; every number in the note is attributed to a source.
