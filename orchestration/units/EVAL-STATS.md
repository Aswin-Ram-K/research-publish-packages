# UNIT EVAL-STATS — make the harness incapable of quoting a number it cannot support

**Card:** EVAL-STATS (Part C of a three-card wave honouring the shared row contract v1).
**Automated, offline:** zero inference requests; tests use synthetic rows only.
**Status:** done. Bound ≤28 tool calls; 18 used. No request issued.

## Objective

Add a pure-function statistics layer — `experiments/ptr-engine/longrun/analyze_stats.py`
plus its guard suite — so that a reported estimate cannot be printed without its `n`
and a two-sided interval, and so that a significance test is refused unless the data
can actually license it.

Deliverables (exact write paths, nothing else touched):

- `experiments/ptr-engine/longrun/analyze_stats.py`
- `experiments/ptr-engine/longrun/tests/test_analyze_stats.py`
- `orchestration/units/EVAL-STATS.md` (this card)
- `orchestration/handoffs/EVAL-STATS.json`

## What was built

| Function | Contract |
|---|---|
| `wilson_ci(k, n, level=0.95)` | Wilson score interval → `(point, lo, hi)`; at `k=0` → `[0, 0.5615]`, at `k=n` → `[0.4385, 1]` — never zero-width. |
| `quantile_ci(values, q, resamples=10000, seed=20261020, stats=None)` | Percentile-bootstrap interval → `(point, lo, hi, n)`. Null / NaN / inf entries are **dropped and counted** (`stats["dropped_null"]`), never coerced to 0. Also reports the distribution-free order-statistic rank span (`stats["rank_span"]`). Raises `InsufficientSamples` when `n < 20` or `n*(1-q) < 3`. |
| `rank_span(n, q, level)` | Binomial order-statistic ranks; reproduces the survey figure **43–48 = p89.6–p100 at n=48, q=0.95**. |
| `mcnemar_exact(pairs)` | Exact two-sided McNemar on paired item outcomes → `(b, c, p)`; refuses (`RefusedTest`) when `b+c < 6`, naming the discordant count. The refusal **carries** `.b/.c/.p` so the arithmetic stays visible. |
| `mcnemar_p(b, c)` | The exact two-sided binomial tail alone (no licensing gate); `mcnemar_p(3,0) = 0.25`. |
| `pass_hat_k(n, c, k)` | Unbiased `1 − C(n−c,k)/C(n,k)`, guarded: `n−c < k` → `1.0` by definition, bad `k`/`c` → `ValueError`. |
| `paired_by_turn(rows_a, rows_b)` | Pairing on `turn_index` (fallback `turn`) → `(pairs, stats)` reporting formed / missing-key / duplicate / unpaired. |
| `render_estimate(...)` | **The single enforcement point.** Raises `BareMetricError` for a missing/short `n`, a missing endpoint, an inverted interval, or a point outside its interval. Every number in the CLI passes through it. |
| CLI | `python3 analyze_stats.py --rows ROWFILE…` → per arm `n`, p50, p95 **with bootstrap CI + dropped-null count + order-stat span**, accuracy `passed/decidable` with a Wilson interval, and one McNemar line (or explicit refusal) per arm pair. |

## Estimability rule (the one place it lives: `quantile_ci`)

```
n >= 20                        # minimum for ANY reported quantile
n * (1 - q) >= 3               # at least 3 observations above a tail quantile
```

For p95 this refuses at **n = 48** (`48 × 0.05 = 2.4 < 3`) and first accepts at **n = 60**.
The refusal message is exact and test-pinned:

```
refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0)
and n*(1-q)=2.4 < 3; minimum n for p95 is 60
```

## Contract tolerance

Rows are read with `.get()` throughout; every v1 field (`ttft_ms`, `ttft_source`,
`first_token_kind`, `cached_tokens`, `cached_source`, `engine_metrics_before/after`,
`answer_kind`, `answer_value`, `answer_raw`, `answer_parse_error`, `answer_turn`) may be
absent or null. `ttft_source == "unavailable"` is dropped even when a wall-clock fallback
number sits in `ttft_ms`, and is counted separately from a null. Accuracy is
`passed / decidable`, where a row with no decidable outcome (no boolean `passed`/`ok`/
`correct`, and not a NUM answer with an `expected`) leaves the denominator instead of
being charged as a failure; at `decidable = 0` the CLI prints `UNDECIDABLE` rather than
a ratio.

## Two internal contradictions in the card, and how they were resolved

1. *"refuse when `b + c < 6`"* vs *"`mcnemar_exact` returns p≈0.25 for b=3,c=0"* — both
   cannot hold in one return path. Resolution: `mcnemar_p(3,0) = 0.25` is the pure
   arithmetic (public), while `mcnemar_exact` refuses at 3 discordant pairs and attaches
   the same `p=0.25` to the exception. No chi-square fallback anywhere.
2. *"refuse when `n < 20`"* vs *"test (c): `InsufficientSamples` at n=48"* — 48 is not
   below 20, so a pure `n < 20` rule could not produce the required red test. Resolution:
   the documented tail-mass clause (`n*(1-q) >= 3`), which is exactly the arithmetic the
   survey used to call p95 at n=48 unestimable, and which fixes the first admissible p95
   at n=60. Both clauses raise the same typed exception with the same message shape.

## Evidence (all commands run from `experiments/ptr-engine/longrun`)

- `python3 experiments/ptr-engine/longrun/tests/test_analyze_stats.py` → **8/8 passed** (also `pytest -q` → `8 passed in 0.11s`).
- Red→green, each mutation of a copy of the module kills exactly its own guard via
  `ANALYZE_STATS_PATH`:
  - tail-mass/min-n clause deleted → `test_insufficient_samples_at_48_exact_message` **FAILS** (7/8);
  - interval requirement in `render_estimate` deleted → `test_render_estimate_refuses_bare` **FAILS** (7/8);
  - `b + c < 6` gate deleted → `test_mcnemar_exact_025_and_refusals` **FAILS** (7/8).
- CLI on synthetic 48-row arm: `ttft_p95 REFUSED at n=48 …`; on a 70-row arm: `ttft_p95
  n=70 1100.11ms [651.52, 1634.20]` and `McNemar exact: b=0 c=10 p=0.00195`.
- Bare-print attempt `render_estimate('ttft_p95', 482.73, None, None, 48)` →
  `BareMetricError: … an interval is required`.

## Left untouched, by instruction — the existing bare-p95 printer

`experiments/ptr-engine/longrun/analyze_longrun.py:307` computes `p95` as an
interpolated percentile with **no interval** (`"p95": round(pct(ttft, 0.95), 2)`), and
`analyze_longrun.py:368-369` prints it as `p95=%s` with `n` but **no CI**. Not edited;
the wiring is a separate card.

## Not done / next

- No row writer was touched, so live row files do not yet carry the v1 contract fields;
  this module tolerates their absence, which is the point.
- `docs/EXTERNAL-EVAL-PRACTICE.md` is unchanged; the estimability rule is documented in
  the module docstring and here, and should be promoted into METRICS.md by whoever wires
  the CLI in.
