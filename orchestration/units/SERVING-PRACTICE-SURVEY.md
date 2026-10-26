# SERVING-PRACTICE-SURVEY — serving/measurement practice, surveyed and adjudicated

**Status:** done (see `orchestration/handoffs/SERVING-PRACTICE-SURVEY.json`).
**Mode:** offline research unit. **Zero inference requests** were made; neither endpoint was contacted.
Nothing outside this unit's three declared write paths was modified.

## Purpose

The operator directive (message m00372) says: learn from the internet how models/agents and serving
setups are tested, and incorporate the validated findings. `EVAL-PRACTICE-SURVEY` covers grading; this
unit covers **serving and measurement**.

It exists because the project's headline claim — pointer chunking beats transcript growth, expressed as
p95 TTFT per turn (`transcript-grow` 838.85 ms vs `pointer-stable` 356.12 ms, `transcript-compact`
224.08 ms, `lease-reopen` 201.78 ms, **n = 48 turns per arm**) — is only worth what its measurement
discipline is worth. If the field's harnesses measure TTFT a different way, warm up differently, or
would call n = 48 indefensible, the thesis inherits that debt.

## Scope

1. Metric definitions (TTFT, ITL/TPOT, e2e, throughput) and how each is actually measured.
2. Load generators: `vllm bench serve`, SGLang `bench_serving`, NVIDIA GenAI-Perf; warmup, rate,
   concurrency, `--ignore-eos`, output-length control.
3. Prefix-cache observability: `usage.prompt_tokens_details.cached_tokens`, vLLM
   `prefix_cache_hits/queries`, SGLang `sglext.cached_tokens_details` (`--cache-report`), and what
   cannot be attributed.
4. Tail statistics: order-statistic CIs, bootstrap, paired designs, and the arithmetic for n = 48.
5. Known confounds: cold start/compile, warmup order, batching interference, clock skew, quantisation.
6. Tool calling as a serving feature: `tool_choice` modes, `--enable-auto-tool-choice`,
   `--tool-call-parser` differences, harness-vs-model attribution.

Out of scope: making any live request, editing the runner, changing the endpoint configuration.

## Method

Sources read as **source, not tutorial**: the servers' own benchmark scripts and metrics docs at `main`,
GenAI-Perf's published metric table, NumPy's documented quantile estimator, and the local runner chain
(`experiments/context-cache/{client,runner,analyze}.py`, `src/resextract/context/meter.py`,
`src/resextract/doctor.py`, `config/resextract.toml`). Quantile CIs were computed here from
`Bin(n, 0.95)` and an exponential-tail SE, not quoted from a blog. Vendor documentation is marked
**[vendor]**; contested or version-dependent behaviour is quarantined into its own section.

## Deliverable

`docs/EXTERNAL-SERVING-PRACTICE.md` — findings by the six areas with cited primary sources, an
ADOPT/REJECT/MODIFY table naming the real artifact each row touches, a measurement protocol a later
card can implement, the sample-size answer with arithmetic, and a blunt list of what this repo
mis-measures today.

## Headline results (short)

- vLLM's bench latches TTFT on the first chunk carrying `choices` (empty text allowed); SGLang's on the
  first **non-empty** text; GenAI-Perf defines it only as "first response". The repo matches SGLang's
  rule, then **falls back to `wall_ms`** when no content delta arrives — so tool-call and reasoning
  turns enter the p95 sample as end-to-end latency (`client.py:128-139`).
- At n = 48 the 95 % CI for p95 is the interval between the **43rd and 48th** order statistics — i.e.
  p89.6 to p100. Separating 838.85 from 356.12 rests on ~3 tail observations; z ≈ 2.52 on an
  exponential-tail model, with no pairing and no warmup discipline behind it.
- **n ≈ 384/arm** (~19 samples above p95) is the pragmatic floor; **n ≈ 1000/arm** (~50 above p95) makes
  the headline defensible. Costs: 1536 / 4000 measured requests for four arms versus 192 today — tens
  of minutes on the same box, i.e. never a budget problem.
- First instrumentation change to make: latch TTFT on the first `choices` delta and delete the
  `wall_ms` fallback; then scrape `/metrics` `prefix_cache_hits/queries` per cell so a TTFT win can be
  attributed to cache reuse rather than to a shorter prompt.

## Bound

≤45 tool calls. Used 33 (research, downloads, local reads, three writes). One deviation recorded: two
`curl` downloads issued before a `cd` landed in the session directory and were removed in the same run;
`ls` confirmed neither file existed afterwards.

## Write paths

- `docs/EXTERNAL-SERVING-PRACTICE.md`
- `orchestration/units/SERVING-PRACTICE-SURVEY.md`
- `orchestration/handoffs/SERVING-PRACTICE-SURVEY.json`
