# MISS-LAW-2 — the vLLM `+1056` term, re-derived with a second instrument

**Unit:** MISS-LAW-2 · **Server:** vLLM 0.27.1, `qwen3.5-9b`, `http://192.168.2.168:8014` (sole writer)
**Evidence:** `experiments/miss-law/vllm2/rows.jsonl` (133 rows, one per request, `flush()`+`fsync` per row),
`summary.txt` (full run log), `metrics_raw.txt` (the `/metrics` snapshot the inventory is taken from),
scripts `probe2.py` (stage 1) and `probe3.py` (stage 2). `B = 1056` taken from the parent law.
No `/flush_cache`, no restart, no write to `:8012`, no touch of `/home/zer0null/Duval`.

**Verdict in one line.** The `+1056` **survives**, and it now has an *independent* instrument behind it —
not a second counter, but **time**: at a fixed total prompt length, crossing a block multiple changes the
server's own TTFT by **+190 ms** when the bill changes by 1052 tokens (0.18 ms/token, matching the
independently measured cold-prefill slope of 0.17 ms/token), and the "no `+1056`" alternative predicts a
4-token difference, ≈0.7 ms. **Two corrections** come with it: (a) `request_prefill_kv_computed_tokens`
is **not** an independent instrument — it agrees with the cached counter to the token on all 74 measure
rows and is an exact identity in aggregate; (b) the **residue-{0,1} avalanche that MISS-LAW attributes to
SGLang also exists on vLLM** (`cached = 0`, the whole prompt re-billed), so the vLLM half of the law needs
that discontinuity added.

---

## 1. What the server actually exposes — inventory with units

`GET /metrics` → 663 lines. Every cache-related series, with the unit read off the HELP line **and**
checked against live values (not inferred from the name — that is how `prefix_cache_hits_total` was
mistaken for a block counter):

| series | TYPE | unit | what it measured here |
|---|---|---|---|
| `vllm:prompt_tokens_cached_total` | counter | **TOKENS** | the parent law's instrument A |
| `vllm:prefix_cache_hits_total` | counter | **TOKENS** | `HELP …in terms of number of cached tokens`; **identical** to the row above |
| `vllm:prefix_cache_queries_total` | counter | **TOKENS** | `HELP …number of queried tokens`; **identical** to `prompt_tokens_total` |
| `vllm:prompt_tokens_by_source_total{source="local_cache_hit"}` | counter | **TOKENS** | identical to `prompt_tokens_cached_total` |
| `vllm:prompt_tokens_by_source_total{source="local_compute"}` | counter | **TOKENS** | identical to `prompt_tokens_total − cached` |
| `vllm:prompt_tokens_by_source_total{source="external_kv_transfer"}` | counter | **TOKENS** | 0 throughout (no KV connector) |
| `vllm:prompt_tokens_total` | counter | **TOKENS** | total prompt tokens seen |
| `vllm:request_prefill_kv_computed_tokens` | **histogram** | **TOKENS** | `HELP …new KV tokens computed during prefill (excluding cached tokens)`; `_sum`/`_count`/`_bucket`, buckets `1,2,5,10,20,50,100,200,500,1000,2000,5000,10000,20000,+Inf` |
| `vllm:request_prompt_tokens` | **histogram** | **TOKENS** | per-request prompt length |
| `vllm:time_to_first_token_seconds` | **histogram** | **SECONDS** | per-request TTFT, buckets `0.001…2560` |
| `vllm:iter*`, `vllm:request_generation_tokens`, `…per_output_token_seconds` | histograms | tokens / s | not cache |
| `vllm:kv_cache_usage_perc` | gauge | **fraction (0–1)** | KV memory occupancy; read 0.0 after every completed request, so it carries no per-request token information |
| `vllm:external_prefix_cache_*`, `vllm:mm_cache_*` | counters | tokens / **items** | inactive here (0) |
| `vllm:cache_config_info` | gauge | label carrier | advertises `block_size="1056"` |
| `*_created` (every family) | gauge | **unix timestamp** | scrape/creation time, not a measurement |

**Absent on this build:** any `gpu_prefix_cache_hit_rate` gauge, any **block** counter, any `_rate` series,
and any per-request cache field. `usage.prompt_tokens_details` is **present-but-`null` on non-stream
responses** (28 rows) and **absent entirely from the streamed usage chunk** (105 rows) — so the parent
law's "`null` on every request" is right in substance and slightly imprecise in shape.

**The identity check, on live totals over this run** (952,868 prompt tokens):

```
cached 325248 == prefix_cache_hits 325248 == by_source{local_cache_hit} 325248
queries 952868 == prompt_tokens_total 952868
by_source{local_compute} 627620 == 952868 - 325248
request_prefill_kv_computed_tokens_sum 627620 == by_source{local_compute} 627620
```

So **five names, one number, and one identity.** The parent law's warning was not strong enough: it is not
that two counters count tokens, it is that every cache series published here is a restatement of the same
`num_cached_tokens` value plus arithmetic.

## 2. Instruments, and which one is actually independent

| id | observable | per-request? | independent of A? |
|---|---|---|---|
| **A** | `Δvllm:prompt_tokens_cached_total` → `unc_c = usage.prompt_tokens − Δcached` | yes (serial writer) | — the parent instrument |
| **B** | `Δvllm:request_prefill_kv_computed_tokens_sum` → `unc_k` (with `_count` = 1 confirming one sample, `_bucket` giving the bucket) | yes | **NO.** Measured, not assumed: `unc_k − unc_c = 0` on **74/74** measure rows, and the aggregate is an exact identity (§1). It restates A. Recorded because it is the quantity that *names* compute, and because it proves A's arithmetic is not off by a bookkeeping constant — but it is **not** corroboration and is never counted as such below. |
| **C1** | `Δvllm:time_to_first_token_seconds_sum`, `_count` = 1 per request → **server-side TTFT** | yes | **YES.** Time, not bookkeeping. No cache counter feeds it. |
| **C2** | client wall clock of a non-stream `max_tokens=1` request (stage 2) | yes | **YES.** Host-side physics; ≈ TTFT because decode is one token. |

Instrument C is what the mandate asked for and did not have. Its discriminating power comes from a
*differential at fixed total length*: the request at `P1 = 7390` (prompt 7403) and the request at
`P1 = 7394` (prompt 7407) differ by **4 tokens of total prompt** but by **1052 tokens of compute** under the
law. If the `+1056` were an accounting artefact, TTFT would differ by ~4 tokens' worth (≈0.7 ms). It differs
by **191 ms**.

*Honesty note on stage 1:* my streamed-TTFT parser returned `None` for every stage-1 row (an SSE
`delta.content` check that this build's first chunk does not satisfy). Stage 1 therefore uses **server**
TTFT (C1); stage 2 uses **client** wall clock (C2) on non-stream requests. Both are reported; neither is
back-filled.

## 3. Plateau, step, and both instruments side by side

Reps pooled (2 per cell, 4 where a cell was repeated in stage 2). `+B term = unc − (P1 mod B) − L`; the
parent law predicts `+B = 1056`. `pred` is the parent law's `(P1 mod B) + 1056 + L`.

| P1 | P1 mod 1056 | cached | unc | pred | **+B term** | TTFT srv (ms) | wall (ms) |
|---|---|---|---|---|---|---|---|
| 6334 | 1054 | 4224 | 2123 | 2123 | **1056** | 394.4 | 484.6 |
| 6336 | **0** | **0** | **6349** | 1069 | 6336 | 1238.1 | 1294.0 |
| 6337 | **1** | **0** | **6350** | 1070 | 6336 | 1240.9 | 1301.5 |
| 6338 | 2 | 5280 | 1071 | 1071 | **1056** | 205.9 | 217.0 |
| 7000 | 664 | 5280 | 1733 | 1733 | **1056** | 320.4 | 333.1 |
| 7200 | 864 | 5280 | 1933 | 1933 | **1056** | 361.5 | 425.6 |
| 7330 | 994 | 5280 | 2063 | 2063 | **1056** | 382.9 | 485.2 |
| 7386 | 1050 | 5280 | 2119 | 2119 | **1056** | 402.7 | 447.1 |
| 7390 | 1054 | 5280 | 2123 | 2123 | **1056** | 402.2 | 467.7 |
| 7391 | 1055 | 5280 | 2124 | 2124 | **1056** | 404.3 | 488.2 |
| 7392 | **0** | **0** | **7405** | 1069 | 7392 | 1789.8 | 1859.2 |
| 7393 | **1** | **0** | **7406** | 1070 | 7392 | 1790.0 | 1855.2 |
| 7394 | 2 | 6336 | 1071 | 1071 | **1056** | 211.0 | 223.3 |
| 7398 | 6 | 6336 | 1075 | 1075 | **1056** | 212.3 | 222.9 |
| 7450 | 58 | 6336 | 1127 | 1127 | **1056** | 216.0 | 229.0 |
| 8446 | 1054 | 6336 | 2123 | 2123 | **1056** | 410.4 | 444.7 |
| 8448 | **0** | **0** | **8461** | 1069 | 8448 | 2221.7 | 2324.1 |
| 8449 | **1** | **0** | **8462** | 1070 | 8448 | 2222.7 | 2299.7 |
| 8450 | 2 | 7392 | 1071 | 1071 | **1056** | 216.2 | 229.2 |

**The plateau re-test.** `cached` is flat at **5280** at every primed length below the multiple — 7000, 7200, 7330,
7386, 7390, 7391, two reps each, character-for-character what the parent law reported for 7000…7330, and it extends to 7391. The
step is at `P1 = 7392 = 7 × 1056`, not at 7396: `cached` goes 5280 → (7392 avalanche) → **6336** at 7394.
The parent law bracketed the step between 7330 and 7396; this narrows it to the exact block multiple.

**The step with the second instrument.** `cached` (A) and TTFT (C) agree, and the agreement is quantitative:

| band | P1 low → high | Δunc | Δ TTFT srv | implied ms/token | Δ wall | implied ms/token |
|---|---|---|---|---|---|---|
| 6 × B | 6334 → 6338 | 1052 | **+188.9 ms** | 0.1796 | +270.6 ms | 0.2572 |
| 7 × B | 7390 → 7394 | 1052 | **+191.2 ms** | 0.1817 | +242.4 ms | 0.2304 |
| 8 × B | 8446 → 8450 | 1052 | **+195.6 ms** | 0.1859 | +240.3 ms | 0.2284 |

An independent cold-prefill calibration (`CAL-T`, unique nonces, no cache): 1000 tok → 174.4 ms,
2000 → 332.9, 3000 → 512.6, 5000 → 858.2, i.e. **0.171 ms/token** over 1000–5000. The boundary differential
implies **0.180–0.186 ms/token**, within 6–9 % of it, at three separate block indices. The alternative
("the last block is not really re-billed, only the 4-token length change is") predicts ≈0.7 ms and is
excluded by a factor of ~270.

*Why no global linear fit:* across the full 1000–8450 range the cold TTFT is convex (per-token prefill cost
rises with length: 0.29 ms/tok at 8450 vs 0.17 at 2000), so a single `a + b·computed` line has ±300 ms
residuals and cannot be used as a predictor. That is exactly why the differential design — same total
length, one multiple crossed — is the right one and the only one quoted.

## 4. Does the `+1056` grow with the number of appends?

No. It is **exactly 1056** in every measure row that is not in an avalanche cell: 12 rows across six
successive one-token appends in a single session (`G2`, rounds k=1…6) and 6 rows across a session whose
appends cross a block multiple (`G3`: n=300 → n=100 → n=1, with `cached` stepping 5280 → 6336 at k=3).

| session | k | P (previous) | L | cached | unc | `+B term` |
|---|---|---|---|---|---|---|
| G2-r0 | 1→6 | 7000 → 7065 | 13 | 5280 | 1733 → 1798 | **1056, 1056, 1056, 1056, 1056, 1056** |
| G3-r0 | 1 | 7000 | 312 | 5280 | 2032 | **1056** |
| G3-r0 | 2 | 7312 | 112 | 5280 | 2144 | **1056** |
| G3-r0 | 3 | 7424 | 13 | 6336 | 1101 | **1056** |

So the term is **per request, not cumulative**: it does not grow with round count (6 rounds), and it does
not change when the history crosses a block multiple. That rules out "one block of lookahead is consumed
per append and accumulates"; what survives is "**one block's worth of the prefix is recomputed on every
request, forever**".

**Which of the two candidate mechanisms it is, is not decidable from the counters** — and this is worth
stating rather than guessing. The identical-repeat test (`G4`: the same measure request twice) returned
`cached = 5280` **both times**, i.e. the second, byte-identical request still recomputed 1733 tokens.
"Stored but never matched" and "never stored" predict the same number here. What *is* decidable is that the
compute is real (§3) and that it never amortises. At `P1 = 7394`, whose identical re-send is `G6-r0-same`,
`unc = 1058` — 1056 + the 2-token residue — on a prompt the server had already served twice.

## 5. The result that contradicts the parent law: vLLM avalanches at `P1 mod B ∈ {0,1}` too

The parent law reports `R = P1 + L` (whole prefix re-billed) for **SGLang** when `P1 mod 64 ∈ {0,1}`, and
reports no such term for vLLM. It is there on vLLM, at three block indices, two residues deep:

| P1 | mod 1056 | cached | unc | unc − L | TTFT srv |
|---|---|---|---|---|---|
| 6336 | 0 | 0 | 6349 | **6336 = P1** | 1238 ms |
| 6337 | 1 | 0 | 6350 | **6337 = P1** | 1241 ms |
| 7392 | 0 | 0 | 7405 | **7392 = P1** | 1790 ms |
| 7393 | 1 | 0 | 7406 | **7393 = P1** | 1788 ms |
| 8448 | 0 | 0 | 8461 | **8448 = P1** | 2222 ms |
| 8449 | 1 | 0 | 8462 | **8449 = P1** | 2225 ms |

`P1 mod B = 2` recovers immediately (6338, 7394, 8450 → `cached` back to the plateau value). This is the
same residue-{0,1} rule as SGLang at `page_size = 1`, and the timing instrument confirms it is not a
reporting glitch: TTFT at 7392/7393 is **1.79 s**, against **211 ms** for 7394 whose prompt is longer
(7407 vs 7405). An 8.5× TTFT jump for a −2-token change in prompt length cannot be bookkeeping.

**The avalanche is in insertion, not in matching-across-an-append** (`G6`, identical re-send of the prime,
no append):

| cell | prime P | res | identical re-send | append after it |
|---|---|---|---|---|
| 7392 | 7392 | 0 | `cached = 0`, unc 7392, TTFT 1.79 s | `cached = 5280`, unc 2125 |
| 7394 | 7394 | 2 | `cached = 6336`, unc 1058, TTFT 211 ms | `cached = 6336`, unc 1071 |

At residue 0 a **byte-identical** re-send of the prime matches nothing — the engine had not made the
prime's blocks reusable — whereas at residue 2 the same construction matches 6336. Two further facts from
the same test: the avalanche cell recovers one request later but **one block low** (5280 where the law says
6336, i.e. `unc = 2125` instead of 1069), so a post-avalanche session is not simply "cold once and then
normal". Reported as measured; the mechanism inside the block-hash/insertion path is not claimed here.

## 6. Controls

- **Cold control** (`G5`, nonce broken between prime and measure): `cached = 0`, `unc = 7013 = P`, TTFT
  1.71–1.72 s, on both reps. Both instruments identify a miss; the timing scale for a full 7013-token
  prefill is ~1.71 s.
- **Sole-writer serialisation**: every request is one delta window (scrape → one request → scrape);
  `kvcomp_count_delta = 1` and `ttft_server_count_delta = 1` on **133/133** rows, `errors = 0`, which is the
  proof that deltas are attributable to exactly one request.
- **Reps**: 2 per cell (4 for cells repeated in stage 2); no spread in `cached` within any cell
  (checked: `cached` is identical across reps in every cell).

## 7. The model I now believe

For vLLM / `qwen3.5-9b`, prefix caching on, `B = 1056`, a request that repeats a prefix of `P1` tokens and
appends `L` more is billed, in tokens actually computed:

```
P1 mod B >= 2 :   uncached = (P1 mod B) + B + L          <- the +1056 term, unchanged
P1 mod B in {0,1}: uncached = P1 + L                     <- avalanche, whole prefix re-billed
```

with `B = 1056` confirmed by a plateau at every length below the multiple (7000, 7200, 7330, 7386,
7390, 7391 → 5280) and a step at exactly
`7 × 1056 = 7392`, and `cached = (floor(P1/B) − 1) × B` for residues ≥ 2 at block indices 6, 7 and 8.

**On the original `+1056`:**

- **It survives** as the residue-≥2 term, and not as a restatement: instrument B is an identity of A (this
  unit deliberately declines to count it), while instrument C — TTFT at fixed total length — independently
  measures the 1052-token compute step at three block indices at 0.180–0.186 ms/token against a separately
  measured 0.171 ms/token cold-prefill slope, a ~270× discrimination against the no-`+1056` alternative.
- **It needs one correction:** the law's vLLM half is missing the residue-{0,1} avalanche that its SGLang
  half carries. The vLLM grid in the parent law stepped `P1` through 7000…7396 but never landed on 7392
  itself, and its payload grid held `P1` fixed at 7000 (residue 664), so the discontinuity was invisible.
- **It was not an artefact of the single instrument** — but the single instrument was weaker than it
  looked, and the corroboration that *was* available (a second counter) is worthless: `request_prefill_kv_
  computed_tokens` is the same number under a different name. Publishable limitation that remains: the
  *mechanism* (one block of lookahead vs a re-billed resident block) is not separated, because every series
  this build exposes collapses to `num_cached_tokens`; only time is independent, and time cannot tell
  "never stored" from "stored and not matched".

**Residual open question** (for a fresh unit, not this one): at residue {0,1} the prime's blocks are not
reusable even for a byte-identical re-send, and recover one request later one block low. That is an
insertion-path defect, and it is bigger than the `+1056` term it sits next to.
