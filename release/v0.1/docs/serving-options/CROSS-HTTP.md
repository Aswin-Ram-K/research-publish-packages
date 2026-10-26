# CROSS-HTTP.md — the vLLM end of GAP G4: what a dense model on a second engine actually recovers

> **STALE — this note's figure is a different vLLM configuration from the matrix cell.** Its
> **1056**-token block and missing per-request `cached_tokens` describe config **`V2`**; the matrix's
> dense-on-vLLM cell is **`WIN-VLLM` / `V1`**, which resolves to **1,088** (CLAIMS `C56`: V1 hot rows are
> 264/264 × 1088 and 0/264 × 1056; V2 is the reverse). The two numbers do not contradict — they are
> different launches. What this note could **not** measure (per-turn append cost, fan-out) has since been
> measured on the same endpoint under a matrix cell: see [`MATRIX-2x2.md`](MATRIX-2x2.md) and claim `C63`.
> What remains current here: the flag mechanics in §2 (why `block_size` resolved itself, and why
> `--enable-prompt-tokens-details` gates reporting). What is **not** current: "at most two cacheable
> blocks" as a general statement about vLLM, which holds only for this 2,500-token probe at block 1056.

**Unit:** CROSS-HTTP · **Mode:** live, over HTTP, **0 restarts, 0 flag changes** · **Live requests used: 9 of 120**
· **Endpoint:** `http://serving-host/v1`, `qwen3.5-9b`, vLLM **0.27.1**, dense (no Mamba state)
· **Compared against:** SGLang `occamy-1.0`, hybrid linear-attention/MoE, `cached = 64*floor((L-1)/64)`

This is the first measurement of the cache question on a **second engine and a second architecture**.
It closes the "no second stack" half of G4 and, by itself, establishes no grid law on vLLM — §3 says
exactly how far it goes.

---

## 1. The short answer

| Question | Answer on this endpoint | Evidence |
|---|---|---|
| Is `usage.prompt_tokens_details.cached_tokens` reported? | **No — absent on 9/9 responses** (`prompt_tokens_details` is `null`, not `0`) | `cells/CROSS-HTTP/rows.jsonl`, every row |
| Does the engine cache anyway? | **Yes.** `vllm:prompt_tokens_cached_total` rises by **exactly 1056** on each repeat, twice independently | `cells/CROSS-HTTP/analysis.json` → `engine_counters` |
| What is the effective block? | **1056 tokens** — not 16, not 64, not 128 | [§2](#2-where-1056-comes-from-and-why-the-flag-is-not-the-whole-story) |
| Does SGLang's `64*floor((L-1)/64)` hold here? | **Not comparable.** A 1056 grid cannot produce the SGLang law at any L | §3 |
| Append cost per turn | **not measurable** — the per-request cache field is absent | §4 |

## 2. Where 1056 comes from, and why the flag is not the whole story

`GET /metrics` (read-only) exposes the launch configuration:

```
vllm:cache_config_info{block_size="1056", _block_size_resolved="True",
  user_specified_block_size="False", enable_prefix_caching="True",
  mamba_block_size="16", mamba_cache_mode="align", mamba_page_size_padded="None",
  cache_dtype="fp8", kv_cache_size_tokens="107095", ...}
```

Three facts follow, and they matter more than the number:

1. `block_size` resolves to **1056** with `user_specified_block_size="False"` — the flags were *not*
   set by hand; this build **derived** the block size itself. The value is consistent with an alignment
   over the model's hybrid layer-type grouping (a multiple of both 16 and the 96-token page
   granularity), but that derivation is **not verified here** and is recorded as a hypothesis, not a
   finding.
2. `--enable-prompt-tokens-details` **is not set**, so the response body omits the field. Per
   `LAUNCH-VLLM.md`, without that flag `cached_tokens` is not populated — the observation matches the
   documented behaviour exactly.
3. The cache is **not absent, only unreported**. The repeat prompt returns in 0.60–0.69× the cold
   send's wall time, and the engine's own counters move on every repeat.

So the finding is **not** "vLLM does not cache" and **not** "the grid is 16/64/128". It is:

> On this endpoint the cache operates on a **1056-token effective block**, and the per-request
> accountant that would let us recover `cached = f(L)` is switched off. Caching is measurable only in
> aggregate.

## 3. The recovered grid versus SGLang's law

The grid was **not** swept: the per-L sweep the card specified needs `cached_tokens` per request, and
that field is absent, so a sweep would have produced 32 rows of `null` at 2 requests per length. What
the counter delta *does* yield is the block size, which is the quantity the sweep was meant to find.

| | SGLang `occamy-1.0` (hybrid) | vLLM `qwen3.5-9b` (dense) |
|---|---|---|
| Effective block recovered | **64** | **1056** |
| Law form | `cached = 64*floor((L-1)/64)`, exact on 44/44 byte-identical repeats | **not recoverable per request**; the counter moves 1056 per repeat, so at most `1056*floor(...)` |
| Per-request accounting | present (`cached_tokens` in the body) | **absent** (`--enable-prompt-tokens-details` not set) |
| Verified at | U2, 314–1,550 tokens | here, 2,504–2,509 tokens, 2 runs |

**The honest comparison is that the two grids are different in kind, not different by a factor.** On
the SGLang side 64 is fine enough to make a per-token law visible; here 1056 is coarse enough that a
2,500-token prompt contains at most two cacheable blocks, and the residual (2,504 − 1,056 = 1,448
tokens) is recomputed every time regardless of how long the prompt is. A dense model removes the
Mamba-state explanation for the SGLang *append* deviation (MANUSCRIPT §8) — but this endpoint cannot
test that deviation, because it reports no per-request residue at all.

## 4. What could not be measured, and why

| Card step | Status | Reason |
|---|---|---|
| 2. Grid sweep 512…8192 | **not run** | Needs `cached_tokens` per request; absent. Running it would have spent ~32 requests to record `null`. |
| 3. Append cost per turn | **not run** | Same missing field; the engine counter is aggregate, so it cannot attribute tokens to a turn. |
| 4. Fan-out, K=8, `B/A` per branch | **not run** | The warm probe must confirm the prefix is *resident* first, and residency can only be read from `cached_tokens`. The card's own precondition is therefore unsatisfiable here (`analysis.json` → `fanout.verdict` = `unmeasurable`, **not** `1.0`). |

**Latency-only fallback (labelled as such — never a cache-hit ratio).** Across two independent probe
runs: cold send 628 / 658 ms, identical repeat 377 / 457 ms → repeat/cold = **0.60** and **0.69**;
a same-length from-scratch control lands at 646 ms (≈1.0× the cold send). A repeat therefore buys
**~31–40 % of wall time**, consistent with one 1056-token block being served from cache and the
2,504-token remainder being recomputed. This is a latency observation and nothing more.

## 5. What would close the remaining gap

One flag, `--enable-prompt-tokens-details`, turns this endpoint into a full cross-engine grid — and it
would let the append and fan-out arms run unchanged. That requires a restart of **another team's**
service, which this unit is forbidden to do. Until then the cross-engine claim is limited to:
*vLLM 0.27.1 on a dense model caches on a 1056-token effective block and does not report it.*

## 6. Reproduce

```bash
python3 experiments/context-cache/cells/CROSS-HTTP/cross_http.py --probe --salt <salt> --bound 8
python3 experiments/context-cache/cells/CROSS-HTTP/cross_http.py --analyse    # 0 live requests
```

Every row carries `stack`, `config_id`, `config_sha256` (`d09e755b…`), `endpoint`, `model`, and a
per-row `row_digest`; the counter deltas are in `cells/CROSS-HTTP/runs/*.json`.
