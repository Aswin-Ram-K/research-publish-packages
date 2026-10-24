# U-LIT-REVIEW — Non-prefix / shared-context KV cache reuse: literature review

**Unit:** U-LIT-REVIEW · **Date:** 2026-10-20 · **Mode:** web research, read-only on repo
**Scope:** citation-grade primary sources for a paper arguing that an agent context engine built on
immutable content-addressed state nodes with append-only deltas achieves high cache reuse *by
construction*, whereas full-transcript replay and opaque provider prompt caching do not, and that
mid-block mutation is unavoidable-but-costly.

**Verification legend** — every row was read from the source page itself (arXiv `/abs/` blockquote,
provider docs markdown, or upstream source/blog). `VERIFIED` = the exact quoted number appears on the
fetched page. `PARTIAL` = claim verified but the number came from the search snippet, not the fetched
body. `UNVERIFIED` = could not fetch (2 attempts) — recorded so it is not silently dropped.

**System under test (given, not re-derived):** SGLang; radix tree is prefix-only; 30 of 40 layers are
linear-attention with recurrent state checkpointed every 64 tokens; no hierarchical/offload backend
(`enable_hierarchical_cache: false`, `hicache_storage_backend: null`).

---

## Main table

| # | Source | Venue/Year | URL | Exact quantitative claim (as verified on page) | What it supports in OUR argument | Verified? |
|---|---|---|---|---|---|---|
| S01 | **CacheBlend** — Yao et al., "Fast LLM Serving for RAG with Cached Knowledge Fusion" | arXiv 2405.16444v3 / 2024 (EuroSys'25) | https://arxiv.org/abs/2405.16444 | Reduces TTFT by **2.2–3.3×** and increases throughput by **2.8–5×** vs full KV recompute "without compromising generation quality", by reusing caches "regardless prefix or not" and selectively recomputing a small token subset. | Baseline for the *value* of non-prefix reuse; also concedes that raw reuse is invalid — it needs selective recomputation. That gap is exactly what our append-only-delta layout avoids. | VERIFIED |
| S02 | **EPIC** — Hu et al., "Efficient Position-Independent Caching" | arXiv 2410.15332 / 2024 | https://arxiv.org/abs/2410.15332 | "existing context caching requires **exact prefix matches** across requests"; EPIC achieves up to **8× TTFT** and **7× throughput** gains over existing systems, negligible/no accuracy loss. | Nails the prefix-only limitation as a *stated property of existing systems* (our SGLang claim generalises). Immutable documents preceded by varying prefixes is literally our "content-addressed node" case. | VERIFIED |
| S03 | **MEPIC** — "Memory Efficient Position Independent Caching" | arXiv 2512.16822 / 2025 | https://arxiv.org/abs/2512.16822 | Prefix caching is "limited by strict prefix matching"; PIC chunk reuse still needs selective recomputation + PE adjustment, so KV for the same chunk *diverges across requests*; reduces HBM by up to **2×** over SOTA PIC (**5×** for long prompts). | The strongest statement that **reuse fidelity degrades even within non-prefix schemes** — supports "mid-block mutation is unavoidable-but-costly" at the storage layer, not just the arithmetic layer. | VERIFIED |
| S04 | **RAGCache** — "Efficient Knowledge Caching for RAG" | arXiv 2404.12457v2 / 2024 (NSDI'25) | https://arxiv.org/abs/2404.12457 | Reduces TTFT by up to **4×** and improves throughput by up to **2.1×** vs vLLM+Faiss; organises knowledge intermediate states in a **knowledge tree** across GPU/host hierarchy. | Precedent that a *tree of immutable knowledge units* (not a token prefix) is the right cache index — our content-addressed nodes are the agent-context analogue. | VERIFIED |
| S05 | **ContextPilot** — "Fast Long-Context Inference via Context Reuse" | arXiv 2511.03475 / 2025 | https://arxiv.org/abs/2511.03475 | Intro states current techniques "either preserve reasoning quality but deliver little KV-cache reuse, or improve reuse at the cost of degraded reasoning quality"; ContextPilot cuts prefill latency by up to **3×** vs SOTA while preserving reasoning quality. | Frames the **cost/fidelity tradeoff as a dichotomy** — the exact tradeoff our design claims to dissolve by construction (reuse is exact because nodes are immutable). | VERIFIED |
| S06 | **SAFE-KV** — "Causal Suffix Repair for Behavior-Preserving Non-Prefix KV Cache Reuse" | arXiv 2610.15186v1 / 2026 | https://arxiv.org/abs/2610.15186 | On Qwen2.5-7B-Instruct, prefix-conditioned composition preserves only **47.2%** of HotpotQA-500 and **37.8%** of 2Wiki-500 full-prefill answers; safe reuse "is exact up to **four documents** and degrades at **sixteen**". Faithful repair re-encodes most of the context, so its operating rule "serves every workload by full prefill". | **The single best fidelity-degradation datum**: naive reuse loses >half its answers, and repair restores fidelity only by paying near-full prefill cost. This is the formal version of "unavoidable-but-costly". | VERIFIED |
| S07 | **LatentRemedy** — "Efficient Remedy For Non-Prefix KV Cache Reuse in Multi-Agent Systems" | arXiv 2610.18014v1 / 2026 | https://arxiv.org/abs/2610.18014 | Directly reusing non-prefix KV across agents with **conflicting tasks** "can severely degrade model performance, causing **up to a 90% drop**"; existing remedies recover only "a limited fraction". | Agent-setting fidelity cost — the case our paper must beat is not RAG documents but *shared agent context under divergent instructions*, which is our workload. | VERIFIED |
| S08 | **TurboRAG** — "Accelerating RAG with Precomputed KV Caches for Chunked Text" | EMNLP 2025 (anthology 2025.emnlp-main.334) | https://doi.org/10.18653/v1/2025.emnlp-main.334 | Reduces TTFT by **up to 9.4×** (average **8.6×**) vs conventional RAG by pre-computing **chunk-level** KV caches and stitching with independent-attention + reordered-RoPE, "preserving answer quality". | Chunk-aligning the content unit to the cache unit is the established scaling lever — our *node* boundary plays the same role, but is content-addressed rather than retrieval-chunked. | PARTIAL (number from OpenAlex metadata snippet; DOI page not fetched) |
| S09 | **Marconi** — Pan et al., "Prefix Caching for the Era of Hybrid LLMs" | **MLSys 2025** (arXiv 2411.19379v3) | https://arxiv.org/abs/2411.19379 | Recurrent layers use "in-place state updates" which "preclude rolling back cache entries for partial sequence overlaps, and instead mandate **only exact-match cache hits**"; Marconi achieves up to **34.4× higher token hit rates** (**71.1%** or **617 ms** lower TTFT) vs SOTA prefix caching. | **Load-bearing for our hybrid claim**: linear-attention layers cannot be rolled back, so reuse collapses to exact-match. Explains *why* our 64-token checkpoint alignment matters, and why misaligned mutation yields 0%. | VERIFIED |
| S10 | **Tail-Replay** — "Escaping the Curse of Linear Attention in Prefix Caching for Hybrid LLMs" | arXiv 2608.30310v2 / 2026 | https://arxiv.org/abs/2608.30310 | Linear-attention recurrent states "cannot be rolled back to arbitrary prefix boundaries"; storing checkpoints means "token-level matches are directly usable only at positions **aligned with stored checkpoints**"; with a **5–10% replay budget** it retains **92.8–99.9%** of full-prefill quality, reaching **9.1–14.3×** at 32K. | The most direct published statement of our stack's mechanism — reuse is quantised to checkpoint boundaries. Also shows the fidelity gradient (92.8–99.9%, i.e. **not exact**) for any non-aligned shortcut. | VERIFIED |
| S11 | **SCBench** — "A KV Cache-Centric Analysis of Long-Context Methods" | **ICLR 2025** (arXiv 2412.10319, comments field) | https://arxiv.org/abs/2412.10319 | Uses test examples with **shared context**, **12 tasks**, **two shared-context modes**, **8 long-context LLMs**, evaluating the full lifecycle: generation / compression / retrieval / **loading**. Notes KV reuse is adopted by vLLM and SGLang and by OpenAI, Microsoft, Google, Anthropic. | The benchmark precedent for evaluating cache reuse as a lifecycle (generation→…→loading), which is what "cache reuse by construction" needs to be measured against, not single-request quality. | VERIFIED |
| S12 | **PrefixBench-H100** — "Characterizing Prefix Reuse and TTFT in H100 LLM Serving" | arXiv 2609.19657v1 / 2026 | https://arxiv.org/abs/2609.19657 | Reproducible benchmark varying shared-prefix length, suffix diversity, arrival pattern, concurrency, output length, cache config; finds cache effectiveness "largely insensitive to concurrency and output length" and that "cross-runtime differences that remain arise above the cache, in the **scheduling layer**"; explicitly not a new caching algorithm. | Calibration source for TTFT/hit-rate curves on our hardware class, and a *negative* result we must engage: if scheduling dominates, the win must come from structural hit-rate, not engine tuning. | VERIFIED |
| S13 | **KV cache management survey** — "A Survey on LLM Acceleration based on KV Cache Management" | arXiv 2412.19442 / 2024 | https://arxiv.org/abs/2412.19442 | Taxonomy of **token-level / model-level / system-level** optimisations (selection, budget allocation, merging, quantization, low-rank; architectural reuse; memory mgmt, scheduling, hardware-aware). | Provides the standard vocabulary to place our contribution; our claim is a *system-level* (structural) reuse argument plus a model-level checkpoint-alignment constraint. | VERIFIED |
| S14 | **Rate–Distortion memory compaction survey** — "What to Keep, What to Forget" | arXiv 2607.08032 / 2026 (submitted 9 Jul 2026) | https://arxiv.org/abs/2607.08032 | Argues KV eviction/quantization, prompt pruning, architectural-state bounding and agent-memory consolidation are "one problem: a rate–distortion decision…at what fidelity, under a resource budget"; at every layer the keep-signal is "attention magnitude or recency" and it "fails in the same way everywhere, by discarding, before the query is known and with no way to undo it"; "the repeated compaction that agents actually perform is almost never measured". | **The best framing for our fidelity half.** Immutable append-only nodes escape the "no way to undo it" failure mode, and the survey's complaint that agent-side repeated compaction is unmeasured is a ready-made gap statement for us. | VERIFIED |
| S15 | **"Remember, Don't Re-read"** — Jabbarvaziri, stateful ReAct agents | arXiv 2606.14945v1 / 2026 | https://arxiv.org/abs/2606.14945 | Stateless design costs **O(n) tokens per iteration and O(n²) total**; stateful agent uses **90% fewer** tokens on HPO (2,492 vs 24,465) and **52% fewer** on code optimisation (627K vs 1,275K) with comparable quality. | Agent-side evidence that **carrying typed persistent state instead of replaying transcript** is the winning structure — the empirical justification for content-addressed stateful nodes over full-transcript replay. | VERIFIED |
| S16 | **OpenAI prompt caching — exactness of `cached_tokens`** | OpenAI docs / live 2026-10-20 | https://developers.openai.com/api/docs/guides/prompt-caching (`.md`) | For models before GPT-5.6: "Reported `cached_tokens` is calculated by subtracting the hidden system tokens from the last matched breakpoint, then **rounding down to the nearest multiple of 128**." For GPT-5.6+: cached-token reporting is "**Exact eligible boundary**, excluding hidden tokens". Minimum cacheable prefix **1,024** visible input tokens (GPT-5.6+). | **Answers the critical question**: the server-reported cached-token count is *not* an exact count on most deployed models — it is quantised down to 128-token blocks. Any paper measuring reuse from `cached_tokens` alone has a ±127-token, downward-biased measurement floor. Our instrumentation must not use it as ground truth. | VERIFIED |
| S17 | **OpenAI prompt caching — invalidation semantics** | OpenAI docs / live 2026-10-20 | https://developers.openai.com/api/docs/guides/prompt-caching | "Cache reuse requires the **entire rendered prefix** to match. If content or a relevant setting changes **before a breakpoint, the prefix after that change cannot match** the existing cache entry." `context_management`/compaction "can prevent reuse from the first changed token onward". Also: maintaining a session "doesn't guarantee a cache hit". | Opaque-provider caching is prefix-only *and* change-intolerant — an early-token edit forfeits the whole suffix, exactly the mid-prompt insertion failure we show for the radix tree. | VERIFIED |
| S18 | **Anthropic prompt caching — TTL, `cache_control`, min length** | Anthropic docs / live 2026-10-20 | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | Default TTL **5 minutes**, refreshed free on use, measured "from the start of the request that writes or reads the cache entry, **not from the end of its response**" (so a 4-min response leaves ~1 min); **1-hour** TTL available at 2× base input. Minimum cacheable length is **per-model: 512 / 1,024 / 2,048 / 4,096** tokens. Writes happen **only at breakpoints** (hash of prefix ending at that block). | The TTL clock eats into the reuse window, and the minimum length means small agent nodes are simply *uncacheable*. Both are constraints our engine must respect when it talks to providers. | VERIFIED |
| S19 | **Anthropic prompt caching — invalidation on early-token change** | Anthropic docs / live 2026-10-20 | https://platform.claude.com/docs/en/build-with-claude/prompt-caching#what-invalidates-the-cache | "**Exact matching:** Cache hits require **100% identical** prompt segments, including all text and images up to and including the block marked with cache control." Hierarchy `tools` → `system` → `messages`; "changes at each level invalidate that level and **all subsequent levels**". Lookback window is **20 blocks** — if the previous write falls >20 blocks behind, "there is no cache hit". | Confirms Anthropic's guarantee is the same prefix-only, invalidate-everything-after model. The 20-block lookback is an additional *silent* miss mode: a long agent turn can push its own prior cache entry out of range. | VERIFIED |
| S20 | **SGLang `RadixCache.match_prefix`** (upstream source) | sgl-project/sglang, read 2026-10-20 | https://github.com/sgl-project/sglang (`python/sglang/srt/mem_cache/radix_cache.py`) | Docstring: "Find the **longest cached prefix** of `key` in the radix tree." Returns a single `MatchResult` with a summed `device_prefix_len = sum(len(v) for v in value)` — **one contiguous hit length**, no interior-hole representation. | Directly grounds "the radix tree is prefix-only (`match_prefix` returns one contiguous hit length)" in the actual API rather than a blog post. Our mid-prompt-insertion → 0% cache claim is a consequence of this signature. | VERIFIED |
| S21 | **LMSYS "Unified Radix Cache"** (SGLang hybrid caching blog) | LMSYS Org / 11 Aug 2026 | https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/ | "A recurrent state is valid only at an **exact prefix checkpoint**"; FULL/SWA/MAMBA components "share the same token prefix, but **not the same reusable boundary**"; forcing a single boundary "either discards valid reuse or **permits invalid reuse**". L3 kept hit rates near **98%** (DeepSeek-V4-Flash) and **96.8%** (Inkling-Small) in later multi-turn rounds; session-aware eviction cut TTFT **2.9%–16.6%** vs HiRadixCache+LRU. | **Corroborates the hybrid checkpoint-boundary mechanism from the vendor's own engineering write-up**, and shows even vendor L3 tiering leaves 2–3.2% of multi-turn hit rate on the table. Note this is a *blog*, not peer-reviewed. | VERIFIED |
| S22 | **SGLang hybrid state management** (PyTorch blog) | PyTorch / SGLang Team, 3 Dec 2025 | https://pytorch.org/blog/hybrid-models-meet-sglang-more-than-full-attention/ | "in-place state updates **preclude the ability to roll back** cache entries for partial sequence matches"; Mamba state is allocated at **request level** and KV at **token level**; `HybridReqToTokenPool` binds a Mamba state to a request to align lifespans. | Explains the *mechanism* behind our checkpoint granularity: state is request-scoped and updated in place, so only checkpoint-aligned boundaries are reusable. Does **not** state the 64-token interval. | VERIFIED (mechanism) / PARTIAL (interval absent) |
| S23 | **JaccardServe** — "Lossless Cross-Request KV Cache Reuse via Position-Aligned Block Injection" | SSRN 7162778 / 2026 | https://www.ssrn.com/abstract=7162778 | Earlier token-reordering approach gave a **44% TTFT reduction** but caused a **60% rate of structural output differences** — "unsuitable for production use". New approach: inject donor KV blocks only when the matching span occupies the **same absolute token position**, so the model "processes the same token sequence it would have processed anyway". | Excellent adversarial datum: **reordering to gain prefix alignment costs 60% output divergence**. Supports the claim that reuse must preserve the exact token sequence — i.e. append-only deltas, not reordering. | **UNVERIFIED** — SSRN returned Cloudflare "Content Blocked" on crawl, and Scrapling `stealthy` returned HTTP 403 "Just a moment…" (2 attempts). Numbers above are from the search-index abstract only; **do not cite until fetched**. |
| S24 | **Prefix-Certificate Retention (PCR)** — "Exact Memory-Time Optimization for Prefix-Cached LM Serving" | arXiv 2610.02766v1 / 2026 | https://arxiv.org/abs/2610.02766 | "a resident block is usable only when the **required preceding prefix is also available**"; a breakpoint theorem extends the construction to all nonnegative timeouts; validated by chronological replay of **39,632** public Mooncake requests. | Theoretical confirmation that cache-value is **path-dependent**, not per-node — which is precisely why immutable nodes + append-only deltas can be priced correctly while a mutated block cannot. | VERIFIED (abstract snippet; full theorem text not read) |
| S25 | **LMCache** — "An Efficient KV Cache Layer for Enterprise-Scale LLM Inference" | arXiv 2510.09665 / 2025 | https://arxiv.org/abs/2510.09665 | Extracts/stores KV caches from **vLLM and SGLang** and shares them across engines; supports cache offloading (prefix reuse) and PD disaggregation; "combining LMCACHE with vLLM achieves up to **15×** improvement in throughput" on multi-round QA / document analysis. | This is the **capability our stack has switched off** (`enable_hierarchical_cache: false`, `hicache_storage_backend: null`). Establishes the headroom left on the table by our current configuration. | VERIFIED (abstract; the 15× figure is quoted from the same abstract) |

---

## Cross-cutting note: is the server-reported cached-token count exact?

This was flagged critical, so it is stated separately. **Answer: it depends on the provider and the model
generation, and on the most widely deployed shape it is NOT exact.**

- **OpenAI, models before GPT-5.6:** `cached_tokens` is *rounded **down** to the nearest multiple of 128*
  (S16). A true hit of 4,095 tokens reports 3,968. The error is one-sided: the count **under-reports**,
  never over-reports, and the bias is up to 127 tokens per request.
- **OpenAI, GPT-5.6 and later:** reporting is an "exact eligible boundary, excluding hidden tokens" (S16).
- **Anthropic:** the docs assert **exact matching** for hits (S19) and expose
  `cache_read_input_tokens` / `cache_creation_input_tokens` such that
  `total = cache_read + cache_creation + input` (S18). **However**, no Anthropic page fetched here states
  whether those token *counts* are exact or approximate. Treat Anthropic's counts as
  **exact-by-contract for matching, unstated for counting**.

Consequence for our measurement design: a provider-reported cached-token count cannot be used as the
ground-truth numerator of a reuse ratio, because on pre-5.6 OpenAI models it is quantised to 128-token
blocks and biased low. Our instrumentation should compute the reuse boundary from the request itself
(e.g. the longest matching node prefix under our content-address scheme) and use provider counts only as
a corroborating, lower-bounded cross-check.

---

## Fidelity / cost tradeoff — the numbers that define the frontier

| Regime | Fidelity | Cost | Source |
|---|---|---|---|
| Naive non-prefix composition | **47.2%** / **37.8%** of full-prefill answers retained | cheap | S06 |
| Non-prefix reuse across conflicting agents | **up to 90%** performance drop | cheap | S07 |
| Reordering tokens to force prefix alignment | **60%** structural output difference | 44% TTFT saved | S23 (UNVERIFIED) |
| Checkpoint-aligned replay (5–10% budget) | **92.8–99.9%** of full prefill | 9.1–14.3× TTFT at 32K | S10 |
| Faithful suffix repair | 99.8–100% | "serves every workload by **full prefill**" | S06 |
| Immutable append-only prefix (by construction) | == full prefill (exact) | 2.2–5× (CacheBlend/EPIC-class) | S01, S02 |

The table is the paper's core argument in one figure: **every point that is cheap is lossy, and every
point that is faithful pays full price** — except reuse that is prefix-exact by construction. That is the
gap our content-addressed, append-only design occupies.

---

## WHERE OUR ARGUMENT IS ALREADY CLAIMED BY SOMEONE ELSE

Ranked by how much of our novelty they consume.

1. **S06 SAFE-KV (arXiv 2610.15186) — highest risk.** It already (a) formalises non-prefix reuse as a
   *behavior-preservation* problem against full prefill as reference, (b) proves uncorrected composition
   degrades with document count, and (c) concludes the faithful repair costs full prefill. Our "reuse
   fidelity is a contract, and cheap reuse breaks it" claim is substantially theirs. **We must position
   as**: they repair a *broken* composition after the fact; we never create the break, because nodes are
   immutable and deltas append-only.
2. **S05 ContextPilot (arXiv 2511.03475) — states our tradeoff dichotomy verbatim.** "Either preserve
   reasoning quality but deliver little KV-cache reuse, or improve reuse at the cost of degraded
   reasoning quality." Any framing of ours that merely *restates* this dichotomy looks derivative. We
   need to show we *dissolve* it rather than trade across it.
3. **S04 RAGCache (/ S03 MEPIC) — already index the cache by immutable content units** (a knowledge tree
   / page-aligned chunk KV). The "content unit, not token prefix, is the cache key" idea is theirs. Our
   delta is the *append-only mutation discipline* and the *agent-context* (not RAG-document) workload.
4. **S09 Marconi + S10 Tail-Replay + S21 LMSYS blog — already describe our hybrid checkpoint constraint.**
   "Recurrent state valid only at exact prefix checkpoints" is published, including by the SGLang vendors.
   Our 64-token alignment observation is an *instance*, not a novelty. Cite, do not claim.
5. **S15 "Remember, Don't Re-read" — already shows stateful carry beats transcript replay** on token cost
   (90% / 52%). Our "full-transcript replay is structurally wrong" is their core finding in an agent
   setting.
6. **S14 rate–distortion survey — already names the fidelity/budget framing** across serving KV, prompts,
   architectural state and agent memory, and already flags that repeated agent compaction is unmeasured.
   If we claim "no one has framed agent-side cache reuse as a fidelity-budget problem", this citation
   contradicts us.

**Net novelty that survives:** the *conjunction* of (i) content-addressed immutable nodes with
append-only deltas as an **engine-level** invariant (not a repair or a heuristic), (ii) the resulting
**exactness guarantee** rather than a measured fidelity percentage, and (iii) mid-block mutation shown as
the **only** lossy operation and quantified at the checkpoint granularity of a specific hybrid stack.
Everything else in the argument has a prior owner and should be cited as such.

---

## Gaps / caveats recorded, not papered over

- **The 64-token checkpoint interval is NOT literature-verified.** S10 and S21 establish that reuse is
  checkpoint-quantised, and S22 confirms request-level in-place state, but none of the fetched sources
  states *64*. Three SGLang source paths probed for the constant (`hiradix_cache.py`,
  `mem_cache/unified_cache/components.py`, `server_args.py`) returned 404 or lacked the symbol. **This
  number remains stack-local (given) and must be cited to an internal measurement, not to the literature.**
- **S08 TurboRAG, S24 PCR** numbers come from abstract/metadata text seen in the fetched page or search
  index; full papers not read.
- **S23 JaccardServe is UNVERIFIED end-to-end** (SSRN Cloudflare). Its 44% / 60% figures are attractive
  for our argument and therefore **especially** must not be cited until the paper is fetched some other
  way (institutional access, author preprint).
- **S12 PrefixBench-H100** reports a *negative* framing (cache effectiveness insensitive to concurrency;
  cross-runtime differences live "above the cache, in the scheduling layer"). This partially undercuts a
  pure hit-rate story and should be answered explicitly rather than omitted.
