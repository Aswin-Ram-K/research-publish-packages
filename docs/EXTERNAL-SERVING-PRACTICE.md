# EXTERNAL-SERVING-PRACTICE — what the field measures, and what this repo adopts

Unit: `SERVING-PRACTICE-SURVEY`. **Offline**: zero inference requests were made; the two live
endpoints were not contacted. Sources: the servers' own benchmark code and docs (read as source, not
as a tutorial), NVIDIA GenAI-Perf's published metric table, NumPy's documented quantile definition,
and the local runner chain in `experiments/context-cache/` + `src/resextract/context/meter.py`.
Vendor documentation is marked **[vendor]**; anything I could not verify offline is in
§8 `unverified`. Contested / version-dependent behaviour is in §7, never folded into a flat claim.

The claim under audit: p95 TTFT per turn over **n = 48 turns per arm** —
`transcript-grow` 838.85 ms, `transcript-compact` 224.08 ms, `pointer-stable` 356.12 ms,
`lease-reopen` 201.78 ms.

---

## 1. Metric definitions, and how each is actually measured

**TTFT.** Three definitions are in live use and they are *not* interchangeable:

| Source | TTFT is measured at | Code |
|---|---|---|
| vLLM client benchmark | **first SSE chunk that carries `choices`**, even when the text is empty ("Note that text could be empty here e.g. for special tokens") | `vllm/benchmarks/lib/endpoint_request_func.py`, first-chunk branch ~L254–L290 ([vLLM bench source](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/lib/endpoint_request_func.py)) |
| SGLang client benchmark | **first chunk whose `choices[0]["text"]` is non-empty** — the gate is `if data["choices"][0]["text"]:` | `python/sglang/benchmark/serving.py` ([SGLang bench source](https://github.com/sgl-project/sglang/blob/main/python/sglang/benchmark/serving.py)) |
| GenAI-Perf **[vendor]** | "Time between when a request is sent and when its first response is received" — no statement about empty deltas | [GenAI-Perf README, metric table](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md) |

That difference is not academic: a turn that opens with a **tool call** or with **reasoning tokens**
has no `content` text. Under SGLang's rule the clock keeps running through the whole reasoning phase;
vLLM's Responses-API path avoids exactly that and says so in a comment — *"Reasoning deltas are
included because the server is already decoding when it emits them, so excluding them would report
the whole reasoning phase as time to first token"*
([source](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/lib/endpoint_request_func.py), `_RESPONSES_TOKEN_DELTA_EVENTS`).

**ITL / TPOT.** The definitions genuinely disagree, and vLLM documents the disagreement itself:
`vllm:inter_token_latency_seconds` is "measured between consecutive streamed outputs", while
`vllm:request_time_per_output_token_seconds` is `(end-to-end latency - TTFT) / (output tokens - 1)`;
"these two … differ when an output contains multiple tokens" (i.e. under chunked/continuous batching
or speculative decoding) — [vLLM metrics design](https://docs.vllm.ai/en/latest/design/metrics/).
GenAI-Perf normalises differently again: ITL = "time between intermediate responses for a single
request **divided by the number of generated tokens of the latter response**"
([metric table](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md)).
So "p95 ITL" means *per-chunk gap* in vLLM, *per-token gap* in GenAI-Perf, and *per-token across the
request* if you compute TPOT yourself. Any cross-tool ITL comparison is invalid unless the
chunk-to-token ratio is 1.

**Percentile estimator.** Both server benchmarks produce percentiles with `np.percentile` (vLLM:
`percentiles_ttft_ms = [(p, np.percentile(ttfts or 0, p) * 1000) …]`; SGLang:
`p95_ttft_ms=np.percentile(ttfts or 0, 95) * 1000`). NumPy's default is `method='linear'` — the
Hyndman–Fan type-7 estimator ([NumPy docs](https://numpy.org/doc/stable/reference/generated/numpy.percentile.html)).
This matters for n = 48 (§5): the default interpolates between two order statistics, so p95 is a
*weighted pair*, not one observed value.

**Server-side percentiles are not the same number.** vLLM exports `vllm:time_to_first_token_seconds`
as a **histogram** and openly states that a histogram is "a count of metric samples, recorded in
buckets … the number of requests whose TTFT was <1ms, <5ms, <10ms, <20ms, and so on"
([metrics design](https://docs.vllm.ai/en/latest/design/metrics/)). A p95 read from `histogram_quantile`
is therefore bucket-quantised, and the bucket set can change between releases — usable for a *monotone
sanity check*, not for the arm comparison.

**Which one does this repo match?** None exactly. `experiments/context-cache/client.py:132-134`
latches TTFT on the first **non-empty `delta.content`** (SGLang-bench-like), and
`client.py:138-139` falls back to `ttft_ms = wall_ms` when no content delta ever arrives. That
fallback silently converts a tool-call or reasoning-first turn into a full-latency sample — the exact
failure vLLM's comment warns about, except here it is *unconditional* and *unflagged*.

**Throughput under load** is out of scope for this card's claim (the arms are single-user, one turn
at a time), and the field treats it separately: request throughput = final responses / benchmark
duration, output-token throughput = output tokens / duration, plus vLLM's `request_goodput` computed
against a user-set SLO ([GenAI-Perf table](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md),
[vLLM `calculate_metrics`/goodput](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/serve.py)).
Reporting goodput for a p95-latency experiment would be measuring the scheduler, not the model.

## 2. Load generators and what they actually control

- **`vllm bench serve`** ([source](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/serve.py)) controls
  `--num-warmups` (warmup loop at ~L926: *"Warming up with N requests…"*, executed before the measured
  phase and excluded from the metrics), `--request-rate` with an optional `--burstiness` gamma arrival
  process, `--max-concurrency`, and `--ignore-eos` ("Set ignore_eos flag when sending the benchmark
  request", ~L1832). Ignoring EOS fixes output length so throughput is comparable; it also makes the
  run *not* representative of real stops — which is why it must be recorded per row, not assumed.
- **SGLang `bench_serving`** inverts the default: `ignore_eos` is **on unless `--disable-ignore-eos`**
  (comment "set ignore_eos True by default", payload `"ignore_eos": not args.disable_ignore_eos`),
  and it emits p90/p95/p99 for TTFT, TPOT, ITL and e2e
  ([source](https://github.com/sgl-project/sglang/blob/main/python/sglang/benchmark/serving.py)).
  Two benchmark harnesses on the same box thus produce different output-length distributions by
  default.
- **GenAI-Perf [vendor]** exposes `--warmup-request-count` / `--num-warmup-requests` with **default `0`**
  ([README](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md)) —
  i.e. the tool will happily benchmark a cold, compiling server unless you say otherwise. Defaults are
  not protocol; a measured protocol must state warmup explicitly.
- **What they all do that this repo does not:** separate a warmup phase from the measured phase, pin
  the output length (or record it per row), and record the arrival process (rate/concurrency) so the
  scheduler's queueing is attributable. This repo's runner is strictly sequential
  (`runner.py:198-257`, one `send()` per turn) — good for "no batching interference", but it never
  *records* that fact, so a later reader cannot tell a quiet box from a contended one.

## 3. Prefix caching: what is observable, and what is not

Three independent observability channels exist, and they answer different questions:

1. **Per-response usage.** `usage.prompt_tokens_details.cached_tokens` (OpenAI-compatible). This is
   what `src/resextract/context/meter.py:113-118` reads. Local fact (card-supplied, unverifiable
   offline): the vLLM endpoint on :8014 returns `prompt_tokens_details: null` on **every** row, and
   `normalise_cache` maps `null` → 0 without recording that the field was absent. Consequence: every
   vLLM row is indistinguishable from a cache miss, and its "uncached" figure is the gross prompt.
   Note the code *does* have a top-level fallback for servers that put `cached_tokens` at the top
   level (`meter.py:117-118`), so the null case is a known-shape gap, not an oversight.
2. **Server counters.** vLLM exports `vllm:prefix_cache_queries` and `vllm:prefix_cache_hits`
   (counters) plus `vllm:kv_cache_usage_perc` (gauge) — [metrics design](https://docs.vllm.ai/en/latest/design/metrics/).
   Differencing hits/queries across one cell attributes reuse **at the server**, independent of
   whatever the client thinks the prompt length was. This is the only channel that survives a null
   `prompt_tokens_details`.
3. **SGLang's own cache report.** SGLang's benchmark can ask for it (`--cache-report`) and then reads
   `sglext.cached_tokens_details` — a breakdown of `{device, host, storage}` cached tokens
   ([source](https://github.com/sgl-project/sglang/blob/main/python/sglang/benchmark/serving.py),
   `_extract_cache_from_sglext`). That is strictly richer than `cached_tokens`: it says *where* the
   prefix came from, so a hit that cost an RDMA/fabric fetch is not scored as free.

**What cannot be observed.** Neither channel tells you *whose* prefix was hit. A radix/prefix cache is
shared by every client of the endpoint: turn 12 of `pointer-stable` can hit KV blocks warmed by turn 3
of `lease-reopen` if the invariant head collides. This repo's salt-per-cell
(`runner.py:90-94`, `cell_salt` over `seed:policy:case:depth`) is the right defence and should be kept;
without it the arms would contaminate each other. But a salt only proves *disjointness of the head* —
it does not prove that a TTFT drop is cache reuse rather than a **shorter prompt**. The two are
confounded whenever the arms render different token counts, which is precisely the pointer thesis
(pointer arms carry the same content but a different *rendering*, so `prompt_tokens` differs).

**Attribution rule this implies** (adopted in §4): a TTFT improvement may be called cache reuse only
when (a) `cached_tokens` or the hits/queries delta moves in the claimed direction, (b) `uncached`
tokens are held approximately fixed or explicitly regressed out, and (c) a same-prompt repeat control
reproduces the effect. Otherwise the finding is "this arm rendered a cheaper prompt", which is a
legitimate but different claim.

## 4. ADOPT / REJECT / MODIFY for this repo

Every row names the artifact it touches.

| # | Decision | Artifact | Concrete change | Why |
|---|---|---|---|---|
| 1 | **MODIFY** | `experiments/context-cache/client.py:128-139` | Latch TTFT on the **first chunk that carries any `choices[i].delta`** — content, `tool_calls`, or `reasoning_content` — and record which kind it was (`first_token_kind`). Delete the `ttft_ms = wall_ms` fallback; on no first token, write `ttft_ms = null` + `no_first_token=True` | The current fallback turns a tool-call/reasoning turn into a full-latency p95 sample; vLLM's own bench documents this exact hazard |
| 2 | **MODIFY** | `experiments/context-cache/client.py:85-89` | Build the `httpx.Client` **once per cell run** (keep-alive), outside the timed region; time from "request bytes about to be written" | Today a fresh client (TCP connect, possible DNS/ARP) is created inside the timed window, so every row carries a connection-setup charge and the first row carries compile + handshake |
| 3 | **MODIFY** | `experiments/context-cache/client.py:84-99` | Record `attempts` on the row; a row that needed attempt 2 is flagged, not silently averaged in | A retried request is a different sample (new connection, possibly a warmer cache); the current retry is invisible downstream |
| 4 | **ADOPT** | `src/resextract/context/meter.py:43-62` (`CacheRow`) | Add: `ts_utc`, `attempts`, `first_token_kind`, `details_state` (`present`/`null`/`absent`), `cached_source` (`usage.prompt_tokens_details` / `top_level` / `sglext` / `none`), `engine`, `model`, `config_sha256`, `warmup`, `concurrency`, `ignore_eos`, `server_ttft_ms` | Rows cannot be re-analysed for confounds they never recorded; some cell-local schemas already carry `ts_utc`/`config_sha256`/`cold_null_details` — promote those to the shared row |
| 5 | **ADOPT** | `src/resextract/context/meter.py:96-124` | Keep the clamp, but **never** map "field absent/null" to a silent `0`: record `details_state`, and make cached-vs-uncached claims cite the hits/queries channel instead of `cached_tokens` when `details_state != present` | Otherwise the vLLM arm reads as 100 % cache-miss by construction |
| 6 | **ADOPT** | new probe in `experiments/context-cache/` (+ `config/resextract.toml:7`) | Scrape `/metrics` before and after every cell; store `vllm:prefix_cache_hits`, `vllm:prefix_cache_queries`, `vllm:kv_cache_usage_perc`, `num_requests_running`; on SGLang request `--enable-cache-report` and read `sglext.cached_tokens_details` when present | The only cache observability that survives a null `prompt_tokens_details`, and it also proves the box was idle (running requests = 0/1) during the run |
| 7 | **MODIFY** | `experiments/context-cache/runner.py:198-230` | Add an explicit warmup phase per cell (≈8 turns, discarded), and drop the "turn 1 of rep 1 must miss" assertion into a *warmup row* rather than a measured row | Cold start / first-request compile is currently a measured sample; the docstring's cold-miss contract bakes it in |
| 8 | **ADOPT** | `experiments/context-cache/analyze.py` (no quantile helper today) | Add `quantile_ci(rows, q=0.95, resamples=10000, method="percentile", seed=20261020)` and a report that cannot print a p95 without `n`, CI, and CI width | The repo already has this recipe in two cells — `cells/R2-PROMPT/build_matrix.py:15,172` and `cells/E4/e4_analyze.py:156,183` (bootstrap + Wilson). Two private copies and none in the shared analyser is the drift |
| 9 | **ADOPT** | report/README for any arm comparison | Report **median + p95 + bootstrap CI + n + CI width** together, per arm; never a bare p95 | §5: at n = 48 "p95" is a two-point interpolation whose CI spans p89.6–p100 |
| 10 | **MODIFY** | `src/resextract/doctor.py:383` and `:448` | Probe `GET /v1/models` first; treat `/health` returning 000 as **inconclusive**, not unhealthy | `/health` on :8012 returns 000 while the server is healthy (local fact) — a readiness check that lies is worse than none |
| 11 | **ADOPT** | paired design in `runner.py` cell loop | Interleave the four arms **within a repetition block** and pair by `(case_id, turn, rep_block)` in analysis | Drift on a shared GPU box (thermal, other users) hits all arms equally in a block; pairing removes it (§5) |
| 12 | **REJECT** | any use of `vllm:time_to_first_token_seconds` / SGLang histogram p95 as the arm metric | Do not substitute server-side histogram percentiles for the measured arm comparison; keep them as a monotone sanity check only | Bucket-quantised, bucket set version-dependent |
| 13 | **REJECT** | throughput/goodput metrics for this experiment | Do not report request throughput or goodput for a sequential single-user arm comparison | Measures the scheduler, not the model; the arms are not under load |
| 14 | **MODIFY** | tool-calling rows (vLLM :8014) | Record the server flags in the row's `config_sha256` metadata: vLLM needs `--enable-auto-tool-choice` **and** a `--tool-call-parser`; SGLang exposes `--tool-call-parser` (`python/sglang/srt/server_args.py:379`). Distinguish `HTTP 4xx` (harness/server refusal) from a model-side conforming failure | A refused request is not a model-quality observation; the current vLLM refusal of `tool_choice=auto` is a *serving-config* fact, not a model fact |

## 5. The statistics of a tail — and whether n = 48 can carry the claim

**p95 at n = 48 is defined by two observations.** With NumPy's default (linear, type 7) estimator the
index is `h = (n-1)p + 1 = 47·0.95 + 1 = 45.65`, so the estimate interpolates between the 45th and
46th order statistics, and only **3 observations** (48 − 45) lie above it. A single very large sample
re-pairs the estimate to `(x₄₆, x₄₇)` and moves it by the tail gap. Model-free confidence statement:
the 95 % distribution-free CI for a quantile is `[x_(j), x_(k)]` with `j, k` from the binomial
`Bin(n, p)` tails (`P(B ≤ j−1) ≥ 0.025`, `P(B ≤ k−1) ≤ 0.975`) — the standard order-statistic interval
([quantile estimation](https://en.wikipedia.org/wiki/Quantile#Estimating_quantiles_from_a_sample),
[binomial interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)); percentile
bootstrap is the practical alternative and is what the repo already ships
([`boot.ci` type `"perc"`](https://stat.ethz.ch/R-manual/R-devel/library/boot/html/boot.ci.html)).

| n / arm | expected samples above p95 | 95 % CI ranks `[j,k]` | CI as percentiles |
|---|---|---|---|
| **48** | 2.4 | **[43, 48]** | **p89.6 – p100** |
| 96 | 4.8 | [88, 95] | p91.7 – p99.0 |
| 192 | 9.6 | [177, 188] | p92.2 – p97.9 |
| 384 | 19.2 | [357, 373] | p93.0 – p97.1 |
| 480 | 24.0 | [447, 465] | p93.1 – p96.9 |
| 1000 | 50.0 | [937, 963] | p93.7 – p96.3 |

(Computed here from `Bin(n, 0.95)`; the practical rule it encodes is `n ≳ 20/(1−p) = 400` for p95.)

**Second route, with a tail model.** For an exponential tail the asymptotic quantile SE is
`SE(q̂_p) ≈ √(p(1−p)/n) / f(q_p)`, and with `f(q₀.₉₅) = 0.05/μ` that gives
`SE ≈ 0.63 μ = 0.21·q₀.₉₅` at **n = 48** — i.e. a relative SE of about **21 %** on the headline number.
Fitting μ from the two arms (`μ = p95 / −ln 0.05 = p95 / 2.996`): `transcript-grow` μ ≈ 280 ms →
SE ≈ 176 ms; `pointer-stable` μ ≈ 119 ms → SE ≈ 75 ms.

**Can n = 48 separate 838.85 from 356.12?**
Gap = 482.73 ms; `SE(gap) = √(176.2² + 74.8²) = 191.4 ms` → **z ≈ 2.52**. So on an exponential-tail
model the *point* estimates are nominally separable at the 5 % level — but that is the whole of the
support, and it is not enough, for three reasons: (i) the per-arm 95 % CI covers **p89.6–p100**, so the
interval says "somewhere between the 90th percentile and the maximum"; (ii) the model-free interval is
driven by 3 tail observations out of 48, and the arms differ by hundreds of ms on turns where a single
cold compile or a 4-second stall dominates; (iii) the design is sequential per cell, so the two arms are
measured at different times and any drift is *not* removed by pairing.

**What n makes it defensible.** Target: the CI must not straddle the two arms' point estimates and the
tail must have enough members to be a distribution rather than an anecdote.

- **n ≈ 384 / arm (32 reps × 12 turns)** — pragmatic floor: ~19 samples above p95, CI ≈ p93.0–p97.1.
- **n ≈ 1000 / arm (84 reps × 12 turns)** — recommended for the headline claim: ~50 samples above p95,
  CI ≈ p93.7–p96.3, and the exponential model's relative SE falls to ~15 % (0.63/√(1000/48) ≈ 0.14).
- Below ~200/arm the p95 is a 3–10 point statistic; at 48 it is a 3 point statistic.

**Cost.** Today: 4 arms × 48 turns = **192 measured requests**. At n = 384/arm: 4 × 384 = **1536**
requests (≈ +32 warmup × 4 = 1664 total). At n = 1000/arm: **4000** measured requests (≈ 4032 with
warmup). At the observed sub-second-to-few-second per-turn cost this is **tens of minutes of wall clock**
on the same two endpoints — the constraint on this experiment is not the request budget, it is that the
current n was never chosen.

**Paired design.** Pair by `(case_id, turn, rep_block)` and compare within pair (per-turn delta, then
bootstrap the *deltas*). This is the standard defence for run-to-run variance on a shared box: it
removes drift common to all arms in a block, and it directly tests the thesis ("the same turn under two
renderings"), which an unpaired p95 does not.

## 6. A measurement protocol a later card can implement

1. **Readiness.** `GET /v1/models` returns 200 with the model id (**not** `/health`; see §4 row 10).
2. **Warmup.** ≥8 discarded requests per cell *after* the first successful request (covers compile,
   allocator, CUDA-graph capture, tokenizer cache); a `warmup: true` row set, excluded from analysis.
   If the server was freshly started, also send one maximal-length prompt to force the prefill kernels.
3. **Barrier.** Before each cell, assert quiescence from the server's own gauge: vLLM
   `num_requests_running == 0`; record the value per block. Interleave arms within a block; one
   request in flight at a time; record `concurrency: 1`.
4. **Per-row fields.** `cell, arm, policy, case_id, turn, rep_block, salt, prefix_sha256, prompt_tokens,
   cached_tokens, cached_source, details_state, uncached, ttft_ms, ttft_kind, itl_ms[] (or tpot_ms),
   wall_ms, completion_tokens, status, attempts, ts_utc, engine, model, config_sha256, warmup, ignore_eos,
   server_ttft_ms`.
5. **Cache attribution.** Per cell, take the `/metrics` delta for `prefix_cache_hits` /
   `prefix_cache_queries`; report `hit_rate_server` beside the client-side `cached_tokens` figure and
   flag when they disagree by more than a few %.
6. **Statistics.** Per arm: n, median, p95, bootstrap CI (10 000 resamples, percentile, fixed seed —
   reuse `seed 20261020`), CI width, mean, and the count of samples above p95. Paired per-turn deltas
   for arm-vs-arm. Report the number of rows excluded (failed/retried/warmup).
7. **Never** report a p95 without `n` and a CI; never mix arms measured in different blocks without
   saying so.

## 7. Contested / version-dependent

- **`np.percentile`'s default estimator** — `method="linear"` today; the keyword was `interpolation=`
  before NumPy 1.22, and older vLLM/SGLang runs may have used it. Same number, different name; a
  different `method` changes the p95 at small n by up to one order statistic.
- **vLLM histogram bucket set** — docs say the bucket choice is "most useful to users", i.e. it moves
  between releases; a `histogram_quantile(0.95, …)` series is not comparable across upgrades.
- **`cached_tokens` semantics** — whether chunked-prefill hits, CPU/offload hits, or only GPU radix
  hits are counted has changed across engines and versions; SGLang's `sglext.cached_tokens_details`
  (`device`/`host`/`storage`) exists precisely because the single number is ambiguous.
- **SGLang TTFT gate** — the non-empty-`text` gate is what the current `main` benchmark does; earlier
  versions varied. Treat SGLang-produced TTFT and vLLM-produced TTFT as different metrics.
- **Tool-call streaming shape** — whether the first delta carries `tool_calls` before any content is
  parser- and template-dependent; vLLM and SGLang additionally differ in which `delta` fields are
  populated for reasoning.

## 8. unverified

- That vLLM at `:8014` returns `prompt_tokens_details: null` on *every* row — card-supplied local fact;
  no request was made in this unit to re-check it.
- Whether `:8012` (SGLang) emits `sglext.cached_tokens_details` under this deployment's build; the
  feature exists in the SGLang source read here, but the server's `--enable-cache-report` state and
  version were not checked.
- The exact latency distribution of these arms (the exponential model in §5 is an assumption used to
  produce a *relative* SE; the model-free order-statistic bounds do not depend on it).
- Which SGLang/vLLM release the two servers run — `/health` returning 000 blocked the obvious probe and
  no request was permitted; all version-sensitive claims above are marked as such rather than asserted.
- The truth of the four quoted p95 values themselves: they were taken from the card/handoff record, not
  recomputed from the row files in this unit.

## 9. What this repo is currently mis-measuring (blunt)

1. **Tool-call and reasoning turns are recorded as full latency.** `client.py:128-139` only latches
   TTFT on `delta.content` and falls back to `wall_ms`. Any first-token-less turn (tool call, reasoning
   preamble) enters the p95 sample as an end-to-end latency. This alone can manufacture the
   `transcript-grow` tail.
2. **Connection setup is inside the timed window.** `client.py:85-89` constructs a new `httpx.Client`
   per request after `started = perf_counter()`. Every row includes TCP setup; row 1 of each cell also
   includes server-side compile. The field's harnesses (vLLM, GenAI-Perf) warm up and reuse sessions.
3. **No warmup, and cold start is a measured sample by contract.** `runner.py:227-230` asserts turn 1 of
   rep 1 must miss; there is no warmup phase anywhere in the runner. vLLM's bench runs `--num-warmups`
   before measuring; GenAI-Perf's default of 0 is a trap the protocol must override.
4. **p95 with n = 48 and no CI.** `analyze.py` has no quantile helper at all (its functions are
   `tax_error`, `hit_rate`, `per_turn_series`, `compaction_effect`, `summary_table`), so the p95s were
   computed outside the shared analyser. At n = 48 the 95 % CI spans **p89.6–p100**.
5. **Cache hits are not attributable.** `meter.py` maps a null/absent `prompt_tokens_details` to
   `cached_tokens = 0` with no flag, and nothing scrapes `vllm:prefix_cache_hits/queries`. A TTFT win
   therefore cannot be separated from "the pointer arm rendered fewer prompt tokens" — the core thesis
   is currently unfalsifiable in its own row schema.
6. **Retries are invisible.** `client.py:84-99` silently re-times a failed attempt; the row carries no
   `attempts` field.
7. **Readiness lies.** `doctor.py:383` and `:448` treat `GET /health` as the health signal although
   `:8012` returns 000 while healthy; a healthy box can be declared broken, or a broken one healthy if
   the check is skipped as "optional".
8. **No ITL/TPOT at all.** `CacheRow` carries only `ttft_ms`, `wall_ms`, `completion_tokens`, so TPOT
   `= (wall − ttft)/(completion − 1)` can be derived but the per-chunk ITL the field reports cannot —
   and with `completion_tokens` from `usage` only, a null usage row yields `tpot = 0`.

## 10. Sources

- [vLLM — Metrics design](https://docs.vllm.ai/en/latest/design/metrics/) **[vendor]**
- [vLLM — `vllm/benchmarks/serve.py`](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/serve.py) (warmup, `--ignore-eos`, `np.percentile`, goodput)
- [vLLM — `vllm/benchmarks/lib/endpoint_request_func.py`](https://github.com/vllm-project/vllm/blob/main/vllm/benchmarks/lib/endpoint_request_func.py) (first-chunk TTFT, reasoning-delta note, server-side TTFT passthrough)
- [vLLM — Automatic prefix caching](https://docs.vllm.ai/en/latest/design/prefix_caching/) **[vendor]**
- [vLLM — Tool calling](https://docs.vllm.ai/en/latest/features/tool_calling/) **[vendor]**
- [SGLang — `python/sglang/benchmark/serving.py`](https://github.com/sgl-project/sglang/blob/main/python/sglang/benchmark/serving.py) (TTFT gate, `ignore_eos` default, p90/p95/p99, `--cache-report`, `_extract_cache_from_sglext`)
- [SGLang — `python/sglang/srt/server_args.py`](https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/server_args.py) (`--tool-call-parser`)
- [NVIDIA GenAI-Perf — README metric table](https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md) **[vendor]**
- [NumPy — `numpy.percentile`](https://numpy.org/doc/stable/reference/generated/numpy.percentile.html) (default `method='linear'`, Hyndman–Fan)
- [Quantile estimation from a sample](https://en.wikipedia.org/wiki/Quantile#Estimating_quantiles_from_a_sample) · [Binomial proportion confidence interval](https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval) (order-statistic CI derivation)
- [R `boot::boot.ci`](https://stat.ethz.ch/R-manual/R-devel/library/boot/html/boot.ci.html) (percentile bootstrap)
- Local: `experiments/context-cache/client.py`, `experiments/context-cache/runner.py`, `experiments/context-cache/analyze.py`,
  `experiments/context-cache/cells/R2-PROMPT/build_matrix.py`, `experiments/context-cache/cells/E4/e4_analyze.py`,
  `src/resextract/context/meter.py`, `src/resextract/doctor.py`, `config/resextract.toml`
