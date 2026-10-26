# METRICS.md — the five dashboard metrics (METRICS-V2)

Declared **before** any valid long-run curve exists. This dashboard sits *under* the frozen
decision rule and can never relax it. Every number has an explicit `n`; a metric with a smaller
`n` than the row count is reported with its own `n`, never pooled silently.

Frozen rule (untouched): `pointer-stable` wins only on p95 TTFT ≥2× better than `transcript-grow`
at the final turn, tokens-to-verified-success no worse, checkpoint accuracy no worse.
## 1. TTFT percentiles — p50 · p95 · p99 · max
- **What:** per-turn time-to-first-token in ms (`ttft_ms`, else `ttft_s × 1000`).
- **Why beyond the mean:** the mean hides the tail stall an operator feels; `max` names the worst
  turn and `p99` exposes it without letting one outlier become the whole story.
- **Computation:** linear-interpolated percentile per arm over timing-usable rows; `n` printed.
- **Failure mode:** p95/p99 over 48 turns are **estimated** from ≤48 samples (policy file today
  n=3–7): a hint, not a bound. Failed turns stay in the latency distribution and are also charged.
## 2. Cached share at depth
- **What:** `cached_tokens / prompt_tokens` per turn, mean per **early / middle / late** third of
  the observed turn list (contiguous bands, `n` and turn range per band).
- **Why beyond an average:** the cache story is a trend; one average lets early warmth hide a
  late collapse.
- **Computation:** per-turn ratio, then band means.
- **Failure mode:** thirds of a partial run are not thirds *of the task*; a band with n=1 is an
  anecdote, and trend is unestablished when any band is empty.
## 3. `tokens_to_verified_success`
- **What:** Σ(uncached prompt + completion) turn 1 → the checkpoint that **verifies** (exact match
  to `runtime/LR-01.json`, whitespace-stripped). Repairs are charged to the causing arm because
  every turn up to the verifying checkpoint counts.
- **Why beyond tokens/turn:** it charges waste (repair, re-reads) to the causer and stops at
  success, not at the log's end.
- **Failure mode:** `None` when no checkpoint verifies — never imputed from a partial run.
## 4. `time_to_verified_success_s`
- **What:** wall clock, Σ `latency_s` turn 1 → verifying checkpoint — the metric the operator
  feels and which was previously reported nowhere.
- **Why beyond TTFT:** TTFT is one turn; this is the elapsed cost of reaching a trusted answer.
- **Failure mode:** undefined on no-verify; one stalled turn can dominate (see `max`).
## 5. Failure-charged aggregation
- **Failed turn:** `answer_source == "none"` **or** `truncated == true`, with no expected value
  present. A run that never verifies is **charged at worst case**: observed cost plus, for each
  turn unobserved up to N, the run's largest per-turn tokens and latency. Never dropped.
- **Why:** dropping failures rewards crashing; worst-case charging makes a failed arm lose.
  Printed in analyser JSON under `failed_turn_rule`.
## 6. Per-depth checkpoint accuracy
- **What:** exact match at each depth separately (¼ turn 12, ½ turn 24, end turn 46), with the
  expected value, observed answer quote, `answer_source` and `n_observed`.
- **Why beyond pooled accuracy:** pooled accuracy hides the depth decay the thesis is about.
- **Failure mode:** `NOT_OBSERVED` (n=0) is neither 0% nor 100%; it is no evidence.
## 7. False-claim rate
- **What:** checkpoint/verify rows asserting completion or an answer while that checkpoint's
  expected value is absent → count, quoted claim, `answer_source`.
- **Why:** for an agentic system, confident success with nothing to check it against is the
  trust metric, not a style issue.
- **Failure mode:** regex over emitted text; a claim phrased outside the patterns is missed. It
  under-counts, never over-counts, by design.
## 8. VALIDITY block (per file)
`truncated_rows`, `answer_source_none_rows`, `answer_source_absent_rows`, `ttft_missing_rows`,
`max_tokens_seen`, `completion_tokens_max`, `empty_content_rows`, completeness (`PARTIAL` when
`max_turn < N`), verdict **VALID / INVALID-INSTRUMENT** with reason. Invalid files' per-arm
metrics are **withheld** — instrument-failure evidence, never a point. Stage 1
(`rows-longrun-2026-10-26.jsonl`) → `INVALID-INSTRUMENT`: no `answer_source`, no `max_tokens`,
completions capped at 128, 99/192 rows without TTFT.
## What this dashboard may NOT be used for
- It may **not** relax, re-weight, or re-interpret the frozen decision rule.
- It may **not** convert a `partial` run into a `pass`; `NOT_OBSERVED` is not a result.
- It may **not** pool arms or rows whose instrument settings differ: `max_tokens` is recorded per
  row group and a mismatch splits it with `POOLING REFUSED` (demonstrated on
  `rows-longrun-2026-10-26-fix.jsonl`, 4096 vs 16384).
- It may **not** average a withheld `INVALID-INSTRUMENT` file into any comparison, nor treat p95
  from a short partial run as decision-grade.
