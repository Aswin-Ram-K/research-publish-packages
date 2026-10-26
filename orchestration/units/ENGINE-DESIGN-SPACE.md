# ENGINE-DESIGN-SPACE

**Bound** 22 tool calls, 0 requests, 0 experiments. Used ~17 calls. **Writes** `papers/context-cache/ENGINE-DESIGN-SPACE.md` (86 lines), this card, the handoff. Read-only otherwise; MANUSCRIPT/CLAIMS/GAPS/SERVING-BRIEF/PACKAGE/R-CROSS/RECORD untouched.
**Objective** Turn the prose discussion of other caching engines (§10a.3-10a.4) into a decision: per mechanism, which measured law it would break, whether that is settleable here, and by what one measurement.
**Laws tested against** L1 append cost `R=(P1 mod B)+L` (SGLang 64, vLLM +1056) `experiments/miss-law/LAW.md:7-12`; L2 settled null semantics `experiments/ptr-engine/RECORD.md:155`; L3 fetch-rewrites-prefix (1.84x, 0.602 vs 0.182 s) `RECORD.md:161-163`; L4 64-grid + page_size null (887/888) `PACKAGE.md` §4.

## Result

14 mechanisms. **3** `TESTABLE-HERE` — vLLM `--prefix-match-unit`, LMCache, HiCache. **6** `TESTABLE-ONLY-ELSEWHERE` — CacheBlend, EPIC/LegoLink, AttentionStore, `session_radix_cache`, SGLang eviction policies, SAFE-KV. **5** `NOT-TESTABLE-HERE` — Prompt Cache, H2O, SnapKV, PyramidKV, Mooncake.

Only three mechanisms can reach a decision on this box, and they are all about **cost of recovery**, not about reuse freedom: the five approximate-reuse engines (rows 1/2/3/5/5b/5c) all require an engine path or a training run the box does not have, and Mooncake requires a cluster.

## GAPS.md:505-511 ruling

`SERVING-BRIEF.md:123` stands. `PACKAGE.md:93-99` already withdrew the "rejected on configuration" wording on 2026-10-23 (CACHE-AUDIT) and now says HiCache was "not attempted" — so GAPS is quoting a superseded sentence in the present tense. GAPS should be restated; neither the brief nor §4 changes. The rejection that genuinely fails is `LAUNCH-SGLANG.md:107-150` (sourceless error string, absent from the cited thread for build `0.0.0.dev1+g4ccff141d`).

## Shortlist

1. vLLM `--prefix-match-unit` — **2-4 requests** on `:8014` (production `:8012` occamy untouched). Decides whether L1's vLLM `+1056` is an engine law or a launch default.
2. LMCache/HiCache offload break-even — **0 requests**, arithmetic on `state/config/live-server-config.json` + existing rows. Decides whether L3's 3.3x penalty is compute or bandwidth.

## UNSOURCED

HiCache `cached_tokens` semantics on an L2 hit; measured host→device bandwidth; `:8014`'s non-production status (assumed, per `DO_NOT_REDO` #5 naming `:8012`).
