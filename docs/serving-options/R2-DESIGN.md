# R2-DESIGN.md — Round 2: the design, written before the numbers land

**Status:** DESIGN OF RECORD for Round 2 — a **pre-registration**. No Round-2 row exists yet.
This document was written *before* any Round-2 cell ran, so that the arms cannot be chosen after
seeing which ones won.

**What Round 2 is.** Round 1 measured the per-turn cache bill across two engines and two models and
found the engine sets it (C63). It also searched a **narrow** option space: SGLang got `--page-size`
(S1 = 64, S2 = 128, both against production page 1) and exactly one eviction policy (`slru`, at its
default parameter); vLLM got `--block-size`, `--max-model-len`, `--gpu-memory-utilization`,
`--kv-cache-dtype`. That narrowness is **G16**, and G16 is open
(`papers/context-cache/GAPS.md` §G16; `state/gap-ledger.json`). Five read-only research lanes
(R2-A..R2-E, `orchestration/handoffs/R2-*.json`) found the documented option space is considerably
larger than the tried set — and that **two Round-1 rejections rest on a source that does not carry the
claim attributed to it**. Round 2 is the measured answer to G16: it runs the documented options the
package never ran, and it re-tests the two rejections that do not survive their own citation.

**What Round 2 is not.** It is not a rerun of the 2x2 — C63 is measured and Round 2 does not qualify
it. It is not a band extrapolation: every arm runs at **32k, 71 turns**, the schedule C63 and C62
already used, so that a Round-2 arm is comparable to a Round-1 cell on the same turns.

---

## 1. The design rules (fixed now, not negotiable later)

1. **Every arm names its prediction and its direction before it runs.** An arm without a falsifiable
   prediction is not admitted. Predictions are `P1..P9` below.
2. **Every arm has a paired baseline on the same schedule, same 71 turns, same seed.** The
   comparison is the **paired per-turn delta**, `mean(arm) - mean(baseline)` over turns, with a
   percentile bootstrap over the **71 turns** (10,000 resamples, seed `20251023`) — the method C62 and
   C63 already use, so the intervals are comparable rather than merely similar.
3. **One variable per arm.** An arm that changes two flags cannot attribute its result; the two
   interactions that matter are promoted to their own arms (`A5`, `B5`) instead of being bundled.
4. **A null is a result.** An arm whose predicted direction fails to appear is reported as a null and
   **is not** re-run under a different flag hoping for a better outcome. Re-running with a changed
   flag is a *new* arm, and it must be pre-registered as one before it runs.
5. **The kill condition is per arm, not per batch.** An arm that fails to start twice is recorded
   `did-not-start` with its startup signature and the batch continues. A batch that loses one arm is
   still a batch.
6. **A figure that cannot be traced to a row, cell or pinned handoff is written as untraced.**

## 2. The baselines (fixed, and why these)

| Arm | Engine | Config | Why this is the baseline |
|---|---|---|---|
| **S0** | SGLang | live production: `--page-size 1`, `--mamba-radix-cache-strategy extra_buffer`, `--max-mamba-cache-size 64`, `--mem-fraction-static 0.45`, `--max-running-requests 5` (`docs/serving-options/LAUNCH-SGLANG.md:13-30`) | it is the server the paper's SGLang cells already ran against |
| **V1** | vLLM 0.27.1 | `--block-size 16`, `--enable-prefix-caching` (``docs/serving-options/LAUNCH-VLLM.md:13-23`) | the cell C63 reports as 1,088/2,096 resolved block |

Round-1 readings these baselines produced, quoted from C63 and C60 and **not recomputed here**:
SGLang occamy-1.0 0.957153 hit / 729.7641 uncached/turn, hot grid 64; SGLang qwen3.5-9b 0.956941 /
733.3697 / 64; vLLM occamy-1.0 0.901212 / 1,682.7218 / 2,096; vLLM qwen3.5-9b 0.869037 / 2,230.7782 / 1,088
(`papers/context-cache/CLAIMS.md` C63). S0's own replay sits at 739.25 uncached/turn, hit 0.974242 (C60).

## 3. The arms

Each arm is one variable against its baseline. `Lane` names the research handoff that justified it;
`P` names its pre-registered prediction in §4.

### 3.1 SGLang arms (baseline S0)

| Arm | Change | Lane | P | What a GO looks like |
|---|---|---|---|---|
| **A1** | `--mamba-radix-cache-strategy no_buffer` (S = 3 slots/req instead of 5) | R2-A3, R2-B2 | P1 | uncached/turn within noise, **KV token_capacity rises** (~40 % state memory returned) |
| **A2** | `--max-mamba-cache-size 25` (5 req x 5 slots, instead of 64) | R2-A3 | P1 | same as A1 in the other direction: no hit change, capacity returned |
| **A3** | `--radix-eviction-policy lfu` | R2-A3 | P4 | hit rises only if the 71-turn schedule exceeds capacity — **predicted null** |
| **A4** | `--radix-eviction-policy tlru` | R2-A3 | P4 | as A3 (**predicted null**), but this is the documented "agentic / multi-turn" choice, so a null is worth having |
| **A5** | `--enable-int8-mamba-checkpoint` | R2-A3 | P3 | capacity ~2x at fixed memory (the only quantified claim upstream makes); **accuracy unmeasured upstream** — arm carries a quality gate |
| **A6** | `--enable-hierarchical-cache --hicache-ratio 2.0` | G16 / R2-A2 | P2 | **The re-test of the package's unverified rejection.** Round 1 rejected HiCache quoting an error string with no source for this build; the live server already runs `UnifiedRadixCache`, the Mamba-aware tree (`GAPS.md` §G16). Outcome is either "starts and hits" or a **captured** startup error |
| **A7** | `--enable-session-radix-cache` + one stable `session_id` | G16 / R2-A3 | P5 | hit rises with a single stable session; the feature is implemented **only** by `UnifiedRadixCache`, which is what the live server runs |

### 3.2 vLLM arms (baseline V1)

| Arm | Change | Lane | P | What a GO looks like |
|---|---|---|---|---|
| **B1** | `--prefix-match-unit 64` **with** `--block-size 64` (resolves 1,088; 1,088 % 64 = 0) | R2-C, R2-D | P6 | uncached/turn falls well below V1's 2,230.7782 on the dense cell; the 1,088-token floor becomes a 64-token floor |
| **B2** | `--mamba-cache-mode align` stated explicitly (+ read the two startup lines) | R2-D | P8 | **no change predicted** — it is the auto-resolved default; the arm exists to *pin* it, and its evidence is the log line |
| **B3** | `--kv-offloading-size <N>` (native backend) | G16 / R2-C | P4 | **predicted null at 32k** unless V1 is capacity-bound; a positive is itself the finding |
| **B4** | `--enable-prompt-tokens-details` | R2-C | P8 | no hit change; **instrumentation**, makes `cached_tokens` visible per response |
| **B5** | `--block-size 16` + `--prefix-match-unit 32` (resolves 1,056) | R2-D | P7 | **predicted to NOT beat B1** — 1,056 % 64 ≠ 0, so 64 is illegal there and the arm is the "finest clean divisor" control |

`B4` is listed as an arm but is really a switch for every other vLLM arm: if `cached_tokens` is not
visible, the arm cannot be read. It runs first.

### 3.3 The re-tests the package owes itself

Two Round-1 **rejections** are downgraded, not defended, by G16. Round 2 either makes them measured or
records them as "not attempted":

- **HiCache** — `A6`. The old citation (`LAUNCH-SGLANG.md:107-150`) quotes `ValueError: HiRadixCache
  only supports MHA and MLA yet` as "exact text from issue comments" with **no source URL of its own**,
  and that string is not in the cited thread for build `0.0.0.dev1+g4ccff141d` (`GAPS.md` §G16). The
  arm settles it by **starting the server** and capturing whatever happens.
- **`--enable-mamba-shared-prefix-checkpoint`** — **not an arm, and must not become one.** Lanes R2-C
  and R2-D disagree on its first release (R2-C's bisect: absent through v0.30.0, present from
  v0.30.1rc0; R2-D's: first occurrence v0.31.0). The two bisects are **reconcilable, not contradictory**:
  R2-D's never tested `v0.30.1` (it steps `v0.30.0` -> `v0.31.0`), and R2-C's finer bisect finds the flag
  at `v0.30.1rc0`. Both agree it is **absent from v0.27.1**, the tag the
  box runs, so the arm would fail at argument parsing — and neither lane claims it would help: R2-D
  records that even on v0.31+ it requires EAGLE on the mamba group, and no speculative decoding runs
  here. Round 2 records it as **absent-by-version**, with the untested tag named rather than implied.

## 4. Pre-registered predictions

Each prediction can be wrong; that is the point. **Direction** is what a reader may hold us to.

| P | Prediction | Falsified if |
|---|---|---|
| **P1** | Raising or lowering the mamba **slot** budget does not move hit rate at `--max-running-requests 5` (25-30 slots already satisfy 5 requests at 5 slots each; 64 was over-provisioned by ~39). It moves **token capacity** only | hit changes by more than the bootstrap interval width in either direction |
| **P2** | HiCache either fails to start on this build (Mamba-aware tree + hybrid checkpoint) or starts with **no hit gain at 32k**, because 32k fits in device KV | it starts **and** hit rises materially — then Round 1's rejection was wrong for this build, and G16's item 1 is a **Round-1 error**, not a limitation |
| **P3** | `--enable-int8-mamba-checkpoint` roughly doubles cached-prefix capacity **without** moving hit rate at 32k (capacity is not the binding constraint) | hit moves, or capacity does not grow |
| **P4** | At 32k with no compaction firing (C63: no compaction at 32k), **no eviction policy and no offload tier moves hit rate** — there is nothing to evict and nowhere to offload to | any of A3/A4/B3 produces a paired delta whose interval excludes zero |
| **P5** | Session protection moves nothing on a **single** stable session that never contends, but is the only arm that would help if two sessions interleave | no delta on one session **and** no delta under interleaving |
| **P6** | `--prefix-match-unit 64` with `--block-size 64` cuts the dense vLLM cell's uncached/turn by at least half, because it replaces a 1,088-token reuse floor with a 64-token one | delta < 50 % of V1's 2,230.7782, or interval excludes zero in the **wrong** direction |
| **P7** | B5 (1,056 / unit 32) does **not** beat B1 (1,088 / unit 64) — the grid, not the divisor, sets the floor | B5 beats B1 by more than the interval |
| **P8** | B2 and B4 change no number; they change only what is **visible** | either moves `uncached/turn` |
| **P9** | C63's ordering survives every SGLang arm: **no SGLang configuration's uncached/turn reaches vLLM V1's 2,230.7782 on the dense cell** | an SGLang arm lands within +-10 % of it — which would make the engine effect config-conditional, not engine-level |

**P9 is the load-bearing one.** It is the only prediction that tests whether C63's headline ("the
engine sets the bill") is a statement about the *engine* or about the *configurations Round 1 picked*.
If any SGLang arm closes the gap, Round 2's result is that C63 is **configuration-conditional**, and
that must be said in those words.

## 5. Analysis plan, fixed in advance

- Unit of resampling: the **turn** (71 per arm), not the row — C63's own choice.
- Reported per arm: paired per-turn mean delta, its percentile bootstrap CI (10,000 resamples, seed
  `20251023`), the count of positive turns out of 71, and the hot grid gcd.
- An arm **wins** only if its interval excludes zero in the predicted direction **and** the hot grid
  shows the mechanism it claims (gcd 64 for B1; unchanged gcd 64 for SGLang arms).
- Arms are reported **whether or not they were predicted to work**. There is no "exploratory arm"
  category that escapes this table; a new idea is a new pre-registration.
- **Budget.** Each arm replays the 71-turn battery once (71 requests, plus warmup). Rows are recorded
  per arm; no arm runs twice without being re-registered as a replicate.

## 6. What Round 2 may and may not conclude

**May:** that the documented option space was searched and the result was null or not-null, arm by arm;
that a specific rejection (HiCache) was re-tested on this build and the outcome; that C63's engine
effect does or does not survive configuration search.

**May not:** generalise any arm beyond 32k / one GPU / one seed; call a null "the feature does not
work" (a null at 32k says only that 32k does not exercise it); treat `--enable-int8-mamba-checkpoint`'s
capacity claim as verified without the accuracy gate — upstream documents the capacity gain and
documents **nothing** about accuracy (R2-A3).

## 7. Where every number in this document comes from

| Figure | Source |
|---|---|
| 0.957153 / 729.7641 / 64 (SGLang occamy) | `papers/context-cache/CLAIMS.md` C63 |
| 0.956941 / 733.3697 / 64 (SGLang dense) | C63 |
| 0.901212 / 1,682.7218 / 2,096 (vLLM occamy) | C63 |
| 0.869037 / 2,230.7782 / 1,088 (vLLM dense) | C63 |
| 739.25 / 0.974242 (S0 replay) | C60 |
| no compaction at 32k | C63 §9b |
| S1 = 64, S2 = 128, `slru` at default only | `GAPS.md` §G16 |
| HiCache rejection text has no source URL for this build | `GAPS.md` §G16 |
| live server runs `UnifiedRadixCache` | `GAPS.md` §G16, citing `M1-R.json` |
| `--page-size` default 1; 64 is backend/config, not a constant | R2-E |
| `--prefix-match-unit` can go below the physical block | R2-C, R2-D |
| resolved block 1,088 / 1,056 from the mamba-page formula | R2-D |
| slot arithmetic (5 / 4 / 3 slots per request) | R2-A3 |
| int8 capacity claim, accuracy undocumented | R2-A3 |
| `max_mamba_cache_size` is slots, concurrency = slots / ratio | R2-B2 |
| eviction "use when" rows (lfu / tlru / priority) | R2-A3 (pinned `radix_eviction_policy.mdx`) |
| 14 techniques / 12 rules for prompt layout | R2-E |
| shared-prefix-checkpoint absent from v0.27.1 | R2-C (bisect) **and** R2-D (bisect) — they disagree on the first release, not on the absence |

The pinned trace cited by the workspace's standing constraints —
`dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`, 866,816 bytes, 573 records,
sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb` — is **verified on disk at the
time of writing** and is unrelated to the cache figures above; it is named only because a
trace-dependent claim must cite a pinned copy rather than a live path.
