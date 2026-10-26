# ENGINE-DESIGN-SPACE — the caching-engine design space against our four measured laws

**Unit:** ENGINE-DESIGN-SPACE · **Date:** 2026-10-26 · **Requests to any endpoint:** 0 · **Experiments:** 0
**Purpose.** §10a.3–10a.4 of `MANUSCRIPT.md` describe other caching engines in prose and then stop. This
document takes the step prose never took: for each mechanism, *which of our own measured laws would it
invalidate, could that be settled on this box, and by what one measurement*. Sources are only files opened in
this pass: `docs/serving-options/R-CROSS.md` (row numbers below are its §1 table), `MANUSCRIPT.md:926-960`,
`GAPS.md` G16, `PACKAGE.md` §4, `experiments/miss-law/LAW.md`, `experiments/ptr-engine/RECORD.md`, and
`state/config/live-server-config.json`. Anything not in those is marked `UNSOURCED` rather than paraphrased.

## The four laws, by file

| id | law | where |
|---|---|---|
| **L1** | Append cost `R = uncached = (P1 mod B) + L` (SGLang `B=64`); vLLM adds one whole block, `(P1 mod B) + B + L`, `B=1056`; at `P1 mod B ∈ {0,1}` the whole prefix re-bills (`R = P1 + L`) | `experiments/miss-law/LAW.md:7-12`, `:26-52` |
| **L2** | SGLang **omits** `cached_tokens` when it is 0 — a missing field is a measured zero, never "unknown" | `experiments/ptr-engine/RECORD.md:155` |
| **L3** | A fetch that appends a body rewrites the prefix, so the pointer arm is 1.84× dearer and 3.3× slower TTFT (0.602 s vs 0.182 s) — a property of **prefix-only** reuse | `experiments/ptr-engine/RECORD.md:161-163`; `orchestration/handoffs/C0-EQUALINFO.json:ttft_by_arm` |
| **L4** | Hits land on a **64-token grid** and `--page-size` is a null result: 887/888 rows byte-identical to S0, gcd stays 64 | `PACKAGE.md` §4 ("The pager does not change the grid"); `LAW.md:38-44` |

## The table

| mechanism | source | what it changes about reuse | our law it would break | testable here, no prod-container touch? | the one measurement that settles it | verdict |
|---|---|---|---|---|---|---|
| **CacheBlend** | arXiv:2405.16444; R-CROSS row 1 | reuses chunk KVs **regardless of prefix**, recomputing ~10–15% of tokens per layer | **L3** (a fetch need no longer rewrite the prefix) and **L1** (recompute budget replaces full-suffix prefill) | No — R-CROSS row 1: "needs LMCache/vLLM; no SGLang path" | greedy-token equality at `R=0.15` vs full prefill, 2 prompts × 3 seeds (R-CROSS §2 F2) | `TESTABLE-ONLY-ELSEWHERE` |
| **Prompt Cache** | arXiv:2311.04934; row 2 | reusable schema-declared modules; cached states re-placed with **tracked positions** | **L3**; also **L2**, if position bookkeeping changes what the server reports as cached | No — row 2: prototype, `needs-training`/`approximate-only` | cached-vs-re-encoded encoding equality on one prompt (row 2: "sometimes give different results") | `NOT-TESTABLE-HERE` |
| **EPIC / LegoLink** | arXiv:2410.15332; row 3 | **position-independent** chunks; recompute at each document start to kill the attention sink | **L3** and **L4** — a chunk cache need not land on a prefix grid at all | No — row 3: `approximate-only`, no SGLang path | greedy divergence on a stitched vs full-prefill run (R-CROSS §2 F1 kill criterion) | `TESTABLE-ONLY-ELSEWHERE` |
| **vLLM block-chained hash prefix caching** (+ `--prefix-match-unit`) | R-CROSS row 4c; `MANUSCRIPT.md:900-902`; `R-VLLM.md` rows 1-2 | only **full blocks** are hashed/reused; the *match unit* can be finer than the *storage* block | **L1** (is the vLLM `+B` term a storage-block law or a launch default?) and **L4** (which knob sets the visible grid) | Yes — `:8014` vLLM variant, not the production `:8012` occamy container | same `P1` pair at default vs `--prefix-match-unit 64`; does the extra block shrink? | `TESTABLE-HERE` |
| **H2O** | arXiv:2306.14048; row 5 | evicts KV **tokens**, keeps heavy hitters + recent window (20% budget) | **L1** and **L2** — a "hit" is a token *subset*, so exact-prefix accounting is undefined by construction | No — row 5: `approximate-only`, no engine path | — (needs a token-subset engine; nothing here can express a subset hit) | `NOT-TESTABLE-HERE` |
| **SnapKV** | arXiv:2404.14469; row 5b | per-head clustered important positions from an observation window at the prompt end | **L1**/**L2** (same subset problem) | No — row 5b: `approximate-only` | — | `NOT-TESTABLE-HERE` |
| **PyramidKV** | arXiv:2406.02069; row 5c | layer-wise pyramidal KV budgets | **L1**/**L2** (same subset problem) | No — row 5c: `approximate-only` | — | `NOT-TESTABLE-HERE` |
| **AttentionStore / CachedAttention** | arXiv:2403.19708; row 6 | hierarchical KV **across turns**, layer-wise preloading + async save | none of L1–L4 — exact-prefix, capacity only; **L1** unchanged | No — row 6: "needs engine support"; its own TTFT number is `unverified` in row 6 | TTFT on a repeated turn with preload on vs off; L1 predicts the same bill either way | `TESTABLE-ONLY-ELSEWHERE` |
| **LMCache** | arXiv:2510.09665; row 6b | exact-prefix KV **outside GPU** for vLLM **and SGLang**; batched movement, compute/IO pipelining | not L3's mechanism — but **L3's cost**: recovery becomes a reload, not a recompute | Yes — break-even is arithmetic on disk; live config has `enable_lmcache false` (GAPS) | `bytes(KV per 64-token block) ÷ host→device BW` vs measured 64-token prefill time (R-CROSS §2 F3) | `TESTABLE-HERE` |
| **Mooncake** | arXiv:2407.00079; row 4b | KVCache-centric disaggregated prefill/decode + DRAM/SSD pool | **L1**'s implied capacity story, but only at fleet scale | No — row 4b: `needs-cluster` | — (one node cannot form the pool the result depends on) | `NOT-TESTABLE-HERE` |
| **SGLang HiCache (L1 GPU / L2 host / L3 distributed)** | `GAPS.md:505-511` (pinned `hicache_design.mdx`); `MANUSCRIPT.md:948-952` | adds host and distributed **tiers**; `--hicache-ratio`/`--hicache-size` grow only per-instance private L2 | **L1**'s *cost*, not its bill: the residue-0 avalanche still re-bills the prefix, but paying it in reload rather than compute removes its weight; **L2** is at risk if an L2 hit reports differently — **`UNSOURCED`**: no opened source states HiCache's `cached_tokens` semantics | Yes for the economics (live config: `hicache_ratio 2.0`, `enable_hierarchical_cache false`); No for the hit-rate effect (needs a restart) | the same F3 break-even, plus the `hicache_ratio` L2 size already in `live-server-config.json` | `TESTABLE-HERE` |
| **SGLang `session_radix_cache`** | `GAPS.md:512-518` (pinned `session_radix_cache.mdx`) | registers reusable KV to a **session**; evicts unreferenced KV before KV an active session still references | none of L1–L4 directly — it protects **hit rate under pressure**, i.e. the G5/`max_mamba_cache_size 64` capacity bound | No — effect requires the flag on the serving process (`DO_NOT_REDO` #5 forbids touching it); applicability *is* readable: live `metrics_cache_type = UnifiedRadixCache` (GAPS) | hit ratio under forced eviction, session-protected vs not, same pressure | `TESTABLE-ONLY-ELSEWHERE` |
| **SGLang radix eviction policies (`lru`/`lfu`/`slru`/`priority`/`tlru`)** | `GAPS.md:477-504` (pinned `radix_eviction_policy.mdx`); `MANUSCRIPT.md:956-960` | changes **which** prefix survives pressure; `tlru` protects the "TEL-safe" tail of a conversation | **L4**'s *scope*, not its value: `PACKAGE.md` §4 "slru is indistinguishable from lru" is a statement about one policy at its default, and GAPS records the generalisation to "the eviction policy" as a defect | No — a launch-flag change on the serving process | the same grid measurement under `tlru` at the existing ~1.5× pressure (C59's condition) | `TESTABLE-ONLY-ELSEWHERE` |
| **SAFE-KV suffix re-encoding** | arXiv:2610.15186; row 9d | repairs a composed non-prefix cache by **re-encoding the causal suffix** from a chosen document | breaks **none** — it **corroborates L3**: faithful repair "re-encodes most of the context" (row 9d) | No — no implementation on this box | fraction of context re-encoded vs the un-repaired 47.2%/37.8% answer retention (row 9d) | `TESTABLE-ONLY-ELSEWHERE` |

**Counts.** 14 mechanisms: **3** `TESTABLE-HERE` (vLLM match unit, LMCache, HiCache), **6**
`TESTABLE-ONLY-ELSEWHERE` (CacheBlend, EPIC, AttentionStore, session cache, eviction policies, SAFE-KV),
**5** `NOT-TESTABLE-HERE` (Prompt Cache, H2O, SnapKV, PyramidKV, Mooncake).

**Which laws each verdict touches.** `TESTABLE-HERE` → **L1, L3, L4**. `TESTABLE-ONLY-ELSEWHERE` → **L3**
(every position-independent row attacks prefix-only reuse), **L1** (recompute budget), **L4** (a
position-independent cache has no prefix grid), **L2** (session/offload reporting). `NOT-TESTABLE-HERE` →
**L1/L2/L4** are *unreachable* rather than at risk: a token-subset hit cannot be expressed in exact-prefix
accounting, and Mooncake's pool does not exist on one node.

## The contradiction in `GAPS.md:505-511` — ruling

**The `SERVING-BRIEF.md:123` sentence stands, and the contradiction is already resolved on disk.** GAPS quotes
`PACKAGE.md` §4 as saying HiCache was "rejected on configuration"; `PACKAGE.md:93-99` **withdraws exactly that
wording** ("The earlier wording … is **withdrawn** (CACHE-AUDIT, 2026-10-23)") and replaces it with "**not
attempted**, not 'measured to fail' — treat it as an open option". So §4 today agrees with the brief, and the
surviving defect is only GAPS's quotation of the superseded sentence as present tense. Ruling: the brief's
sentence is correct and should not change; `PACKAGE.md` §4 as corrected should not change; GAPS G16 should
read *"§4 formerly recorded 'a no-go … on configuration'; that wording was withdrawn on 2026-10-23 and §4 now
records the option as not attempted"*, and the load-bearing rejection that does not survive is
`LAUNCH-SGLANG.md:107-150` (quoted error text with no source URL, absent from the cited thread for build
`0.0.0.dev1+g4ccff141d`), not the brief. Evidence: `PACKAGE.md:93-99`; `GAPS.md:521-535`; live
`metrics_cache_type = UnifiedRadixCache`.

## Shortlist — at most two, both `TESTABLE-HERE`, ranked by conclusion-change per request

1. **vLLM `--prefix-match-unit` vs the `+B` term of L1 — 2–4 requests.** L1 says vLLM bills
   `(P1 mod 1056) + 1056 + L`; `MANUSCRIPT.md:900-902` says the *match* unit "can be finer" than the *storage*
   block. If the extra block tracks the match unit, L1's vLLM constant is a **launch default**, not an engine
   law — a conclusion change, not a number. Safety: `:8014` is the vLLM variant serving qwen3.5-9b; the
   production `gx10-occamy-nvfp4` on `:8012` is neither restarted nor stopped (`DO_NOT_REDO` #5). *Assumption:
   `:8014` is non-production — not verified in this unit.*
2. **Offload break-even for LMCache/HiCache — 0 requests.** `bytes(64-token KV block) ÷ host→device bandwidth`
   vs measured 64-token prefill (R-CROSS §2 F3). If reload < recompute, the 3.3× rewrite penalty is a
   **bandwidth** cost and L3 loses practical weight; if not, L3 keeps full weight and offload is capacity only.
   Safety: pure arithmetic on `state/config/live-server-config.json` and existing rows; the bandwidth figure is
   `UNSOURCED` here, so the proposal includes one local pinned-host copy timing **outside** the serving
   container (still 0 requests).

## Limits

- No mechanism was run. Every row's "testable" verdict is about whether the **decisive measurement** is
  executable here, not whether the mechanism is.
- Row attributions to arXiv IDs are R-CROSS's `[fetched]`/`snippet` tags; where R-CROSS itself says
  `unverified` (AttentionStore's TTFT, LMCache's headline multipliers) this document repeats `unverified`
  rather than import a number.
- `UNSOURCED`: HiCache's `cached_tokens` reporting semantics under an L2 hit; the box's measured host→device
  bandwidth.
