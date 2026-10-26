# R-CROSS — cross-stack cache-reuse landscape (offline literature survey)

> **STALE NOTE — superseded for the model-vs-engine question.** Written 2026-10-21 as offline research:
> **no live requests, no measured cells**. The measured answer is
> [`MATRIX-2x2.md`](MATRIX-2x2.md) (claim `C63`, `papers/context-cache/MANUSCRIPT.md` §9b): on one shared
> 32k/71-turn 2x2 the **engine** sets the per-turn uncached bill (**+1,225.18** tokens/turn,
> **2.6738x**, 0.9115 of the 1,344.16 grand mean) and the model main effect is **+275.83** — only
> **+3.61** of it under SGLang, where both checkpoints share the 64-token grid. Read the rest of this
> note as dated background on **flag mechanics**, not as evidence about cost. What remains current: its
> launch-flag descriptions. What is **not** current: any suggestion that the model is the lever.

**Unit:** R-CROSS · **Date:** 2026-10-21 · **Requests to Occamy:** 0 · **Experiments:** 0 · **Tool calls used:** 35 / 40
**Method:** `local_web_search` bursts → primary-source crawls (arXiv abs pages, GitHub, USENIX/vendor engineering
blogs). Every number below is tagged with its provenance: `[fetched]` = read off the primary page in this pass,
`snippet` = search-result abstract text, `unverified` = commonly cited but **not** re-checked here.

**Baseline this is measured against (fixed, not changed):** one SGLang deployment, Qwen3.5-MoE hybrid
attention, plain radix cache, no hierarchical cache, no LMCache, `chunked_prefill_size=8192`. Measured: hits
land on a **64-token grid**; a mid-context edit breaks the cache from the edit point onward and lands within
one 64-block; **no suffix-recovery mechanism**. All our measurements are **exact-prefix**.

---

## 1. Method table

| # | Method | Venue / year | Primary URL | Mechanism (one line) | Strongest measured claim | Exact? | On one GB10-class node |
|---|--------|--------------|-------------|----------------------|--------------------------|--------|------------------------|
| 1 | **CacheBlend** | EuroSys 2025 | [arXiv:2405.16444](https://arxiv.org/abs/2405.16444) | Reuse precomputed chunk KVs **regardless of prefix**, selectively recompute a small token subset per layer | TTFT ↓ **2.2–3.3×**, throughput ↑ **2.8–5×** vs full KV recompute (3 LLMs × 4 RAG datasets) `[fetched]`; recompute ≈ **10–15%** of tokens `snippet` | **No** — quality-matched, "closely approximate" | `approximate-only` (needs LMCache/vLLM; no SGLang path) |
| 2 | **Prompt Cache** | MLSys 2024 | [arXiv:2311.04934](https://arxiv.org/abs/2311.04934) | Schema-declared reusable "prompt modules"; attention states cached and re-placed with tracked positions | TTFT ↓ **8×** (GPU) to **60×** (CPU) on doc-QA / recsys prompts, "maintaining output accuracy" `[fetched]` | **No** — later work: cached vs re-encoded encodings "sometimes give different results" `snippet` | `needs-training`/`approximate-only` (prototype) |
| 3 | **EPIC** (LegoLink) | arXiv 2024 (v3) | [arXiv:2410.15332](https://arxiv.org/abs/2410.15332) | Position-independent caching; recompute/correct at each document beginning to kill the stitched-cache "attention sink" | Up to **8× TTFT**, **7× throughput** over existing systems, "negligible or no accuracy loss" `snippet` | **No** — "negligible", not zero | `approximate-only` |
| 4 | **Production hit rates** — DeepSeek-V3/R1 | eng. report, Feb 2025 | [open-infra-index day 6](https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md) | On-disk KV cache for shared prefixes | **342B of 608B input tokens = 56.3%** hit the on-disk KV cache `snippet` | Yes (prefix reuse) | `yes` (that's our stack, minus the disk tier) |
| 4b | **Mooncake** (Kimi) | FAST 2025 | [arXiv:2407.00079](https://arxiv.org/abs/2407.00079) | KVCache-centric disaggregated prefill/decode + DRAM/SSD KV pool | **525%** throughput ↑ in simulated scenarios; Kimi handles **75% more requests** in production `[fetched]` | Yes (prefix reuse) | `needs-cluster` |
| 4c | **vLLM prefix caching** (DigitalOcean) | eng. blog 2026-06-02 | [digitalocean.com/blog/…](https://www.digitalocean.com/blog/reduce-llm-inference-costs-prefix-caching) | Block-hash prefix cache: hash = block tokens + previous block hash; **only full blocks are hashed and reused** | Mechanism only; `block_size` **16** default on CUDA; partial trailing block always recomputed `[fetched]` | Yes (prefix reuse) | `yes` |
| 4d | **Cloudflare Workers AI** prompt caching | product docs | [developers.cloudflare.com/…/prompt-caching](https://developers.cloudflare.com/workers-ai/features/prompt-caching/) | Prefix caching + `x-session-affinity` header for cache affinity | **No published hit-rate number** `[fetched]` | Yes | `yes` (feature exists) |
| 5 | **H2O** | NeurIPS 2023 | [arXiv:2306.14048](https://arxiv.org/abs/2306.14048) | Evict KV, keep heavy hitters + recent window (20% budget) | 20% KV retention, quality near full cache `[fetched]`; throughput multiplier (commonly cited 29×) `unverified` — abstract fetch truncated | **No** — and a "hit" is a token *subset*, so exact prefix matching is impossible by construction | `approximate-only` |
| 5b | **SnapKV** | NeurIPS 2024 | [arXiv:2404.14469](https://arxiv.org/abs/2404.14469) | Per-head clustered important positions chosen from an observation window at the prompt end | **3.6×** generation speed, **8.2×** memory efficiency vs baseline `snippet` | **No** | `approximate-only` |
| 5c | **PyramidKV** | arXiv 2024 (v4) | [arXiv:2406.02069](https://arxiv.org/abs/2406.02069) | Pyramidal layer-wise budgets: more KV in lower layers, less in higher | Matches full-KV on **LongBench retaining only 12%**; at **0.7%** retention beats other compression methods `[fetched]` | **No** | `approximate-only` |
| 6 | **AttentionStore / CachedAttention** | USENIX ATC 2024 | [arXiv:2403.19708](https://arxiv.org/abs/2403.19708) (sibling paper verified) | Hierarchical KV cache across turns, layer-wise preloading + async save to overlap slow-medium access | Specific AttentionStore TTFT number **not captured** (USENIX talk URL 404s) `unverified` | Yes for exact-prefix reuse | `yes` (needs engine support) |
| 6b | **LMCache** | arXiv 2025 (v2 Dec 2025) | [arXiv:2510.09665](https://arxiv.org/abs/2510.09665) | Extracts/stores KV outside GPU for vLLM **and SGLang**; batched movement + compute/IO pipelining; offload + PD disaggregation | Headline numbers not in the fetched abstract portion (commonly cited 3–10× TTFT / 2.5–15× throughput) `unverified` | Yes (prefix reuse) | `yes` (SGLang connector exists; off by default on our box) |
| 7 | **AIBrix** | arXiv 2025 | [arXiv:2504.03648](https://arxiv.org/abs/2504.03648) | Prefix-aware + load-aware routing with a distributed KV cache | **+50% throughput**, **−70% latency** `[fetched]` | Yes (routing only) | `needs-cluster` |
| 7b | **llm-d / GKE Inference Gateway** | project docs | [llm-d.ai/docs/architecture](https://llm-d.ai/docs/architecture) | Prefix-cache-aware routing (heuristic + precise), P2P KV sharing, load-aware scoring on KV utilisation + queue depth | No single measured headline captured `unverified` | Yes | `needs-cluster` |
| 8 | **EAGLE-3** | arXiv 2025 (v3) | [arXiv:2503.01840](https://arxiv.org/abs/2503.01840) | Draft model does direct token prediction with multi-layer feature fusion ("training-time test") | Up to **6.5×** speedup, **~1.4×** over EAGLE-2; chat + reasoning models; SGLang support `[fetched]` | Yes under exact verification (greedy/fixed seed) | `yes` (draft training needed) |
| 8b | **Self-speculative decoding on hybrid LMs** | arXiv 2026 | [arXiv:2605.01106](https://arxiv.org/abs/2605.01106) | Uses the SSM/linear-attention subgraph as a zero-cost internal draft | Parallel hybrids (Falcon-H1) α = **0.68** at k=2 greedy; **sequential hybrids (Qwen3.5) α = 0.038** — an 18× gap `[fetched]` | Yes (lossless verification) | `yes` — but **on our model family it buys almost nothing** |
| 9 | **Hydragen** | ICML 2024 | [arXiv:2402.05099](https://arxiv.org/abs/2402.05099) | Decompose attention over shared prefixes from batch examples | Commonly cited up to 32× throughput on shared-prefix workloads `unverified` | Yes (kernel-level) | `yes` with kernel work |
| 9b | **ChunkAttention** | MLSys 2024 | [arXiv:2402.17463](https://arxiv.org/abs/2402.17463) | Prefix-aware KV with chunked sharing across requests at differing positions | Reported multi-× prefix-sharing speedups `unverified` | Yes | `yes` with kernel work |
| 9c | **CacheGen** | SIGCOMM 2024 | [arXiv:2310.07240](https://arxiv.org/abs/2310.07240) | KV compression + streaming for remote/disk cache fetch | Commonly cited 3.7–4.3× smaller KV, 3.2–3.7× lower TTFT `unverified` | **Approximate** (quantisation) | `approximate-only` |
| 9d | **SAFE-KV** | arXiv 2026 | [arXiv:2610.15186](https://arxiv.org/abs/2610.15186) | Repair a composed non-prefix cache by **re-encoding the causal suffix** from a chosen document | Un-repaired composition preserves only **47.2%** (HotpotQA-500) / **37.8%** (2Wiki-500) of full-prefill answers (Qwen2.5-7B-Instruct); repair restores **99.8%/98.4%**; reuse **exact up to 4 documents**, degrades at 16 `[fetched]` | Repair is behaviour-preserving, but "faithful repair **re-encodes most of the context**" `[fetched]` | `yes` — and it **corroborates** us |
| 9e | **Evaluating KV-reuse accuracy** | arXiv 2026 | [arXiv:2609.31415](https://arxiv.org/abs/2609.31415) | Methodology critique + dataset generator for PIC accuracy loss | Argues current PIC evaluations "fail to faithfully capture the loss of accuracy" and inflate reported effectiveness `[fetched]` | — (meta) | `yes` — cite it when judging rows 1–3 |
| 9f | **KV Packet** | arXiv 2026 | [arXiv:2604.13226](https://arxiv.org/abs/2604.13226) | Treat cached documents as immutable "packets" wrapped in **trainable** soft-token adapters | Near-zero FLOPs, lower TTFT than recompute-based baselines, F1 comparable to full recompute (Llama-3.1, Qwen2.5) `[fetched]` | **No** | `needs-training` |

---

## 2. The three claims most likely to falsify our current results, and the cheapest test for each

Our current conclusions are: (i) hits are quantised to a 64-token grid; (ii) a mid-context edit invalidates
the cache from the edit point onward; (iii) this stack has **no suffix-recovery mechanism** — the suffix must be
re-prefilled. Each candidate below attacks (iii) or the *cost model* behind it.

### F1 — Position-independent chunk reuse would make "the suffix must be re-prefilled" engine-specific, not fundamental
**Claim:** EPIC's LegoLink gives up to **8× TTFT** and **7× throughput** by reusing chunk KVs behind a varying
prefix, with "negligible or no accuracy loss" ([arXiv:2410.15332](https://arxiv.org/abs/2410.15332)); Prompt
Cache reports **8–60×** TTFT reduction with the same premise ([arXiv:2311.04934](https://arxiv.org/abs/2311.04934)).
**Why it is the top threat:** it is the only line of work that directly contradicts (iii) as a *general* statement.
**Cheapest test (≈4–8 requests, one cell, no new hardware, no training):** measure the **upper bound of the win**
before reproducing anything. On the existing harness, run the pair
`P0 = [A(2048) | B(64) | C(512)]`, `P1 = [A′(2048) | B(64) | C(512)]` with `A′` differing from `A` in one
64-token block at offset 1024; record `cached_tokens` and TTFT. The recoverable suffix in `P1` is exactly what a
PIC system would reuse; multiply its length by our measured per-token prefill cost. **If the recoverable suffix
is < ~10% of TTFT at realistic context lengths, PIC is not worth reproducing on this deployment.**
**Kill criterion:** any greedy-token divergence between a stitched path and full prefill on our model ⇒ the
technique is approximate, and our exact-prefix framing stands as scoped. Note
[arXiv:2609.31415](https://arxiv.org/abs/2609.31415) argues the published PIC accuracy numbers are inflated —
audit that before accepting "no accuracy loss".

### F2 — CacheBlend-class selective recompute would falsify "the suffix must be *fully* re-prefilled"
**Claim:** reusing non-prefix chunks while recomputing only **10–15%** of tokens per layer gives TTFT ↓ **2.2–3.3×**
and throughput ↑ **2.8–5×** at quality comparable to full prefill (EuroSys 2025,
[arXiv:2405.16444](https://arxiv.org/abs/2405.16444)).
**Why it matters:** if a 15% recompute budget is enough, our measured "cache breaks from the edit point" is still
true but no longer *expensive* — the reviewer's objection shifts from correctness to budget.
**Cheapest test:** no SGLang path exists, so the cheap test is a **quality probe**, not a systems build —
2 prompts × 3 seeds × {full prefill, R = 0.15} through vLLM+LMCache on the same node, comparing greedy tokens.
If that stack is unavailable, the cheapest substitute is a **paper audit costing 0 requests**: read the EuroSys
PDF's per-task quality table (3 LLMs × 4 datasets) and check whether *any* configuration is byte-exact.
**Kill criterion:** any greedy divergence at a fixed seed ⇒ `approximate-only`; our exact measurements stay the
reference implementation of the honest comparison.

### F3 — Offload economics: if a broken suffix is cheap to recover, our finding's *impact* is bounded
**Claim:** Mooncake's KVCache pool + scheduler lets Kimi handle **75% more requests** in production and up to
**525%** more throughput in simulation ([arXiv:2407.00079](https://arxiv.org/abs/2407.00079)); LMCache and
AttentionStore make cross-query, out-of-GPU KV reuse routine
([arXiv:2510.09665](https://arxiv.org/abs/2510.09665), [arXiv:2403.19708](https://arxiv.org/abs/2403.19708)).
**Why it matters:** our conclusion implies "a mid-context edit forces re-prefill"; if reloading a 64-token block
from CPU/SSD is cheaper than recomputing it, then breakage costs bandwidth, not compute, and the conclusion's
practical weight drops sharply.
**Cheapest test (arithmetic + one measurement):** `bytes(KV per 64-token block on Qwen3.5-MoE) ÷ measured
CPU→GPU/SSD read bandwidth` vs `measured prefill time for 64 tokens at chunked_prefill_size=8192`. Both inputs
are already on disk in our config/measurements.
**Kill criterion:** reload time ≥ recompute time at 64 tokens ⇒ the 64-grid finding keeps full weight and
offloading is a capacity play only.

---

## 3. What a reviewer would name, and what we should scope out explicitly

- **Exactness is the decisive axis, and it separates the field cleanly.** Every method that beats plain prefix
  caching on *reuse freedom* pays for it with approximation: CacheBlend (quality-matched), Prompt Cache
  (encodings differ), EPIC ("negligible" loss), H2O/SnapKV/PyramidKV (token subsets), CacheGen (quantisation).
  **Nothing in this survey recovers a shifted suffix byte-exactly for free.** The only exact mechanisms found
  are (a) hierarchical/remote reuse of the *same* prefix (AttentionStore, LMCache, Mooncake — capacity, not
  position), (b) prefix-sharing kernels (Hydragen, ChunkAttention — same prefix, different batches), and
  (c) **suffix re-encoding** — which is exactly what we say must happen
  ([SAFE-KV](https://arxiv.org/abs/2610.15186): faithful repair "re-encodes most of the context").
- **Cross-stack corroboration of the grid.** DigitalOcean's description of vLLM prefix caching independently
  confirms the structural mechanism we measured: block-chained hashes, **only full blocks are hashed and
  cached**, and "a partial trailing block at the end of a prefix doesn't get reused and is recomputed"
  ([blog](https://www.digitalocean.com/blog/reduce-llm-inference-costs-prefix-caching)). So a quantised hit grid
  is a property of block-hashed prefix caching generally — not an SGLang defect. (Their default block is 16 on
  CUDA; our measured grid is 64.)
- **Production hit rates are reported, but not by the vendors we would expect.** DeepSeek publishes **56.3%**
  (342B/608B input tokens); Mooncake publishes request-level gains for Kimi; **Cloudflare publishes the feature
  but no hit rate**, and SGLang publishes no production hit-rate number we found. Cite DeepSeek as the anchor
  number and treat "Cloudflare/SGLang production hit rate" as an open gap.
- **Cache-aware routing is a fleet-scale effect.** AIBrix (+50% throughput / −70% latency) and llm-d's
  prefix-cache-aware routing both assume **multiple replicas with different caches**. On a single node the
  routing lever is vacuous — record this as `needs-cluster`, not as an untested claim.
- **Speculative decoding does not change prefix-cache granularity, and on our exact model it barely helps.**
  EAGLE-3 reaches up to 6.5×, but a 2026 study of hybrid models measures acceptance α = **0.038** for
  *sequential* hybrids — the Qwen3.5 family — versus **0.68** for parallel hybrids
  ([arXiv:2605.01106](https://arxiv.org/abs/2605.01106)). Spec decode adds a small draft KV and verifies
  against the same target KV, so it is orthogonal to the 64-grid; and **no paper in this pass measured
  prefix-cache reuse × spec decode jointly** — that is a literature gap, not a result.
- **We should state scope-outs explicitly:** approximate PIC (rows 1–3, 5, 5b, 5c), training-based reuse
  (KV Packet), multi-node routing (AIBrix, llm-d, Mooncake), and cross-model KV sharing (DroidSpeak) are all
  **out of scope for a single GB10-class node running an exact-prefix baseline** — each for a stated reason,
  not by omission.

---

## 4. Assumptions and limits of this pass

1. **No experiments, no server contact.** 0 requests to Occamy; no `.occamy.lock` acquired. Every claim is a
   literature claim, tagged with provenance.
2. **`unverified` tags are deliberate.** Where a headline number is widely cited but the fetched page truncated
   before it (H2O 29×, LMCache 3–10×/2.5–15×, AttentionStore, Hydragen, ChunkAttention, CacheGen, llm-d), the
   row says so rather than importing the number from memory.
3. **Some cited arXiv IDs are post-2025** (e.g. 2604.13226, 2605.01106, 2609.31415, 2610.15186). They are
   abstract-level only in this pass; treat as leads to re-check against the published version before citing.
4. **Venue attributions** are taken from the primary page where present (EuroSys 2025, MLSys 2024, FAST 2025,
   ATC 2024, NeurIPS 2023/2024, SIGCOMM 2024). EPIC's venue was not confirmed in this pass — cited by arXiv ID.
5. **Search budget:** 35 of 40 tool calls used (13 `local_web_search` bursts, 6 crawls/scrapes, 2 failed
   `web_search` calls with no `DEEPSEEK_API_KEY`, 1 USENIX crawl 404). The survey is complete against the nine requested items, with the provenance gaps above
   recorded rather than papered over.
