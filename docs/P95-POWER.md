# P95-POWER — how many turns a cell needs before its p95 can compare two arms

**Unit** `P95-POWER-FROM-ROWS` · **cost** 0 inference requests · read-only on every rows file ·
generator `experiments/ptr-engine/measure/p95_power_gen.py` · data
[`P95-POWER.json`](../../experiments/ptr-engine/measure/P95-POWER.json).

`BUDGET-SCHEDULE` priced **A\*** at 4 arms × 48 turns × 3 reps = **792 requests**, claiming
`n_raw = 144` usable timings per arm for H1. `PARM-1` fixes the H1 gate at disjoint 95 % intervals
with **n ≥ 60 per arm**. This document answers, from rows already on disk, what a p95 interval width
actually is at those n, and whether 144 separate the H1 pair.

## Answer

| question | measured answer |
|---|---|
| usable timings in the largest single (rows file, arm) cell | **48** — nowhere on disk does one cell hold more |
| p95 interval width at **n = 60** | 155–576 ms, depending on the arm (table §3) |
| p95 interval width at **n = 144** | 80–536 ms — a 3–48 % narrowing, and all of it an **ECDF extrapolation**, not an observation |
| two-arm intervals disjoint at **n = 48 / 60 / 144** | **100 % / 100 % / 100 %** on `rows-longrun-c` · **1.3 / 2.7 / 1.6 %** on `-v3` · **4.5 / 5.8 / 12.9 %** on `-v4` |
| lag-1 dependence of `ttft_ms` along turn order | median **0.417**, Fisher-z pooled **0.37** → effective n at raw 144 is **66**, at raw 48 it is **22** |
| verdict | **`A* sufficient`** — narrowly, and only on the grid A\* replicates: the C-grid pair is already disjoint at n = 47/48, so 144 is not what buys the separation |

The load-bearing number is not the width, it is this: **the 315 ms p50 gap the plan is built on is
present in exactly one of the three grids that hold the two H1 arms.** On `rows-longrun-c` the pair
separates at every n tested. On `rows-longrun-v3` and `rows-longrun-v4` — same arms, same instrument,
no tools — the gap is 32 ms and 12 ms and the intervals are **not** disjoint at n = 144 (1.6 % and
12.9 % of resamples), nor at n = 384 (2.8 %, 19.1 %). A\* is powered to reproduce the C-grid effect;
it is *not* powered to detect a 12–32 ms p50 difference, and it cannot be, because that difference
sits under the interval width at any n the budget can afford.

## 1. Source data and what "usable" means

Every `rows-*.jsonl` under `experiments/ptr-engine/measure/`, sha256 recorded before and after the
run — **all 14 unchanged, `rows_files_unchanged: true`** (bytes and lines are in the JSON).

Usable row = `kind == "turn"` **and** `ttft_ms` a positive number **and** `timing_usable is not false`.
Rows dropped by that last clause are counted, not hidden (the `(-k)` column).

| file | lines | sha256[0:16] | usable turn rows per arm (dropped) |
|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | `638c84942e3bcdba` | — (no `kind` field, no `ttft_ms`) |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | `5ac9dd992f5d8715` | pointer-stable:5(-1) |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | `c01c7b4a477fe24b` | — (no `kind`, no `ttft_ms`) |
| `rows-live-2026-10-26.jsonl` | 27 | `3d02b4d473304f00` | — (no `kind`, no `ttft_ms`) |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | `9d4ad90ce34cb781` | lease-reopen:3 · pointer-stable:3 · transcript-compact:4(-1) · transcript-grow:14(-4) |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | `9b1097234bf8d246` | lease-reopen:2(-1) · pointer-stable:3 · transcript-compact:3 · transcript-grow:15(-16) |
| `rows-longrun-2026-10-26.jsonl` | 192 | `bc61d38192d4e431` | **0** — 192 `kind=turn` rows carry `ttft_s` but **no `ttft_ms`** |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | `aa7d6cfe9adedf9e` | lease-reopen:34(-14) · pointer-stable:47(-1) · transcript-compact:48 · transcript-grow:48 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | `80d85fe0e977af16` | pointer-stable:47(-1) · transcript-grow:48 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | `999f298dac8b8356` | pointer-stable:40(-8) · transcript-grow:48 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | `f11391aa2989949f` | pointer-stable:47(-1) · **tools** |
| `rows-longrun-v5-tools.jsonl` | 72 | `586b66f27939bd05` | pointer-stable:47(-1) · **tools** |
| `rows-longrun-v6-tools.jsonl` | 72 | `1e78d75f259afbe0` | pointer-stable:48 · **tools** |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | `6b81a6281ce0b266` | transcript-grow:5(-1) |

Three limits that constrain every number below:

- **No cell holds more than 48 usable timings.** Each rows file is one run per arm, `rep = 1`,
  turns 1…48. The budget's 144 per arm exists nowhere on disk; the only way to reach it is to stack
  the *same* arm across separate grid **files** (three tools grids × 48 pointer-stable), and that is
  pooling across grids, which this analysis refuses. So **every n > 48 in §3 is an ECDF
  extrapolation** — resampling 144 timings from a 48-value empirical distribution assumes that
  48-value ECDF *is* the population, which flattens the tail and understates the true width at 144.
  The extrapolated column is a floor on the width, not an estimate of it.
- **Tools grids are `attribution_disputed`.** In `rows-longrun-v4-tools`, `-v5-tools`, `-v6-tools` a
  `kind=turn` row may carry a follow-up's latency (row model under repair in `TURN-ROW-ATTRIBUTION`),
  and the tools files do contain `kind=tool-followup` rows alongside `turn` rows. Their p95s are
  reported, marked, and **never** used in the power question; no tools distribution is averaged or
  pooled with a non-tools one.
- `rows-longrun-2026-10-26.jsonl` is excluded outright: 192 turn rows, `ttft_ms` absent. Reconstructing
  `ttft_s × 1000` would be a different quantity from an unverified source, so it is not done.

## 2. Observed distributions (the sets the question is asked of)

`rows-longrun-c-2026-10-26` is the 4-arm × 48-turn grid A\* replicates, and it is where the claimed
315 ms p50 gap lives: **p50 = 166.96 ms (pointer-stable) vs 482.24 ms (transcript-grow), gap 315.29 ms**
— the budget's number reproduces exactly.

| set (non-tools) | n | p50 ms | p95 ms | p95 95 % CI (10 000 resamples) |
|---|---|---|---|---|
| `c::pointer-stable` | 47 | 167.0 | 308.9 | 201.3 – 426.2 |
| `c::transcript-grow` | 48 | 482.2 | 838.9 | 679.9 – 849.8 |
| `v3::pointer-stable` | 47 | 168.3 | 232.8 | 190.7 – 391.6 |
| `v3::transcript-grow` | 48 | 200.7 | 230.5 | 210.1 – 492.3 |
| `v4::pointer-stable` | 40 | 187.8 | 284.9 | 204.6 – 560.3 |
| `v4::transcript-grow` | 48 | 199.8 | 227.2 | 210.9 – 776.1 |

Even without resampling: on `c` the two observed intervals are **disjoint with a 254 ms margin**
(426.2 < 679.9). On `v3` and `v4` they overlap almost completely. The H1 effect is real on one grid
and invisible on two others.

## 3. p95 interval width as a function of n

Percentile bootstrap, **10 000 resamples** per (set, n), seed 20261026. `n = 48` is the observed
sample size; `n ≥ 60` is an ECDF extrapolation (see §1).

| set | n obs | width @24 | width @48 | **width @60** | width @96 | **width @144** | width @384 |
|---|---|---|---|---|---|---|---|
| `c::pointer-stable` | 47 | 260.9 | 222.3 | 236.1 | 202.2 | 186.8 | 131.5 |
| `c::transcript-grow` | 48 | 197.4 | 168.3 | 155.2 | 82.4 | 80.5 | 13.6 |
| `v3::pointer-stable` | 47 | 221.5 | 196.5 | 224.5 | 136.4 | 110.7 | 109.7 |
| `v3::transcript-grow` | 48 | 292.1 | 282.3 | 294.9 | 262.2 | 251.2 | 248.5 |
| `v4::pointer-stable` | 40 | 330.9 | 356.3 | 352.8 | 307.4 | 272.4 | 95.1 |
| `v4::transcript-grow` | 48 | 576.7 | 565.1 | 576.2 | 547.6 | 536.5 | 533.0 |
| `v5-tools::pointer-stable` | 47 | 478.0 | 433.3 | 504.6 | 347.9 | 291.0 | 254.5 |

All widths in ms, n and resample count attached. Read them with two cautions:

- **Widths are not monotone in n in the range 24–60.** `v4::pointer-stable` is 330.9 at n = 24 and
  356.3 at n = 48; `v5-tools` goes 433.3 → 504.6 between 48 and 60. Differences under ~20 % between
  n = 24, 48 and 60 are resampling noise plus ECDF quantization (only 40–48 distinct values to draw
  from), not evidence that more data hurts.
- **n = 60 vs n = 144 — what the grid actually buys.** From 60 to 144 the width narrows by 21 %
  (`c::pointer-stable` 236 → 187), 48 % (`c::transcript-grow` 155 → 81), 51 % (`v3::pointer-stable`
  225 → 111), 15 % (`v3::transcript-grow` 295 → 251), 23 % (`v4::pointer-stable` 353 → 272) and
  7 % (`v4::transcript-grow` 576 → 536). Going from the H1 floor of 60 to the plan's 144 does not
  halve the interval on any single arm; it narrows it by a factor between 1.07 and 2.0. And at
  n = 144 the width is still 80–536 ms — comparable to or larger than a 315 ms effect, and far larger
  than the 12–32 ms effect that `v3`/`v4` actually contain.

## 4. The two-arm question, as a power statement

For each grid holding both H1 arms, resample **pairs** of size n, build a 95 % percentile-bootstrap
interval for each p95 (**1000 outer resamples × 200 inner bootstrap draws**), and count how often the
two intervals fail to overlap. That percentage *is* the honest power of the plan.

| grid | p50 gap | p95 gap | disjoint @ n=48 | @ n=60 | @ n=144 | @ n=192 … 384 |
|---|---|---|---|---|---|---|
| `rows-longrun-c` | **315.3 ms** | **530.0 ms** | **100.0 %** | **100.0 %** | **100.0 %** | 100 % at 96/192/288/384 |
| `rows-longrun-v3` | 32.4 ms | −2.4 ms | 1.3 % | 2.7 % | 1.6 % | 2.0 / 1.6 / 2.6 / 2.8 % |
| `rows-longrun-v4` | 12.0 ms | −57.7 ms | 4.5 % | 5.8 % | 12.9 % | 5.6 / 14.6 / 16.6 / 19.1 % |

Stated plainly:

- **At n = 144, on the C grid the intervals are disjoint in 100 % of resamples** — and they are
  already disjoint in 100 % at n = 48. The 792-request plan is not *bought* by 144; the separation is
  purchased at 48, and the extra 96 timings narrow an interval that was never the obstacle.
- **At n = 144, on the v3 grid the intervals are disjoint in 1.6 % of resamples, and on v4 in 12.9 %**
  — even at n = 384 v4 reaches only 19.1 %. If the v3/v4 distributions are the truth, no n the budget
  can afford separates the arms, and the plan would report "no difference" from a null, not from a
  power calculation. That is not a p95 problem: the p95 gap in v3 is −2.4 ms and in v4 −57.7 ms.

## 5. Autocorrelation — measured, not assumed

Turns within a run are not independent. Lag-1 correlation of `ttft_ms` along turn order, computed per
run (each run = 48 consecutive turns, one run per arm per file), then pooled by Fisher z:

| set | n | lag-1 |
|---|---|---|
| `c::pointer-stable` | 47 | 0.642 |
| `c::lease-reopen` | 34 | 0.417 |
| `c::transcript-grow` | 48 | 0.107 |
| `c::transcript-compact` | 48 | −0.041 |
| `v3::pointer-stable` | 47 | 0.662 |
| `v3::transcript-grow` | 48 | 0.475 |
| `v4::pointer-stable` | 40 | 0.362 |
| `v4::transcript-grow` | 48 | 0.489 |
| `v4-tools::pointer-stable` | 47 | 0.509 |
| `v5-tools::pointer-stable` | 47 | 0.460 |
| `v6-tools::pointer-stable` | 48 | 0.292 |
| `policy::transcript-grow` | 15 | 0.194 |
| `fix::transcript-grow` | 14 | −0.004 |

Median **0.417**, Fisher-z pooled **0.37** (13 runs). Effective n from `n_eff = n(1−r)/(1+r)`:

| raw n | implied effective n |
|---|---|
| 48 | **22.1** |
| 60 | 27.6 |
| 144 | **66.2** |
| 384 | 176.6 |

So **effective n is strictly lower than raw n**, and the penalty is severe: the 48-turn cell carries
about **22** independent timings, and the plan's 144 raw timings carry about **66** — which clears the
H1 floor of 60 by 10 %, not by 140 %. The disjointness percentages in §4 are computed by iid
resampling and therefore *overstate* power for the noisier arms; a 100 % at raw n = 48 is better read
as "overwhelming" than as "exact", and it survives the correction only because the C-grid effect
(530 ms on the p95) is roughly seven interval-widths wide at effective n = 22. The arms with lag-1
≈ 0.66 (`v3::pointer-stable`, `c::pointer-stable`) are the ones where extra turns buy least: the
second, third, … turn of a run adds ~1/3 of an independent observation, while a **new run** buys a
fully independent one.

## 6. Verdict

**`A* sufficient`** — with the scope stated, not implied.

1. On the grid A\* replicates (`rows-longrun-c`, 4 arms × 48 turns), the H1 pair is separable at
   n = 48 already: 100 % disjoint at 48, 60 and 144; observed intervals disjoint with a 254 ms
   margin. 144 is not required for the p95 comparison, and effective n ≈ 66 clears the floor of 60.
2. It is **not** a general statement about the arms. Two of the three grids holding the same pair do
   not separate them at n = 144 (1.6 %, 12.9 %) and would need far more than the budget's ceiling;
   `v4` reaches 19.1 % only at n = 384. For a 12–32 ms p50 gap the plan is **underpowered at every n
   tested**, and no n ≤ 384 fixes it at 95 %.
3. Consequence for the budget: **spend on replication across runs, not on depth within one cell.**
   Lag-1 of 0.4–0.66 means the second 48-turn run of an arm adds more information than 96 more turns
   of the first; three reps of 48 (the A\* shape) give ~66 effective timings for 792 requests,
   whereas 144 turns in a single run would give roughly the same raw n at a far higher effective-n
   penalty. If the intent is to *test* whether the 315 ms effect replicates, the cheapest powered
   design is 3 × 48-turn runs of the pair (2 arms, 288 requests), not 4 arms × 144.
4. What would change this verdict: a C-grid replicate that fails to reproduce the 315 ms p50 gap.
   Two of the three existing grids already fail to, which is the finding the budget should absorb
   before spending 792 requests on one more.

## 7. Reproduction

```bash
python3 experiments/ptr-engine/measure/p95_power_gen.py            # rewrites P95-POWER.json
bash experiments/ptr-engine/measure/p95-power-verify.sh            # regenerates ×1 in-repo and diffs
python3 experiments/ptr-engine/tools/p95_power_probe.py            # independent re-derivation of every closed-form number
```

Deterministic (seed 20261026): two consecutive runs produce byte-identical JSON.

`analyze_stats.py` provenance (`method.analyze_stats`): the generator **imports** the module and
digests `os.path.realpath(module.__file__)`, so the sha always names the bytes that were actually
loaded — `sha256_atimport` = `0a9a786102ca870edb3ff714538a512e0ea59534e4ced2f3d012aec0e39b493b`,
`tracked: false`, `dirty: true`.

The earlier value `2c9756f3…` was **withdrawn** by `P95-POWER-DIGEST-FIX`: it was the digest of the
source *path* before that file was edited at 11:45 (the JSON was written at 11:41), and the file is
untracked, so "the digest of `analyze_stats.py` at HEAD" was never a reproducible quantity. The old
value was stale-for-an-earlier-revision **and** unreproducible-because-untracked (cases (a)+(c)), not
taken from a different path. `quantile_ci` is still not used; this generator implements its own
percentile bootstrap, so no statistic here depends on `analyze_stats.py`.

## 8. What the verifier certifies, and what it cannot

`p95-power-verify.sh` certifies one thing: **the committed `P95-POWER.json` is exactly what
`p95_power_gen.py` produces today from the rows on disk** (byte-identical, exit 0/1). It certifies
reproducibility of a computation — that the file and its generating code agree — and nothing else.

It cannot certify that the sampling assumptions behind those numbers hold. It does not check that a
bootstrap of an ECDF extrapolated to n = 144 describes a real 144-turn run (no such run exists: the
largest cell is 48); it does not check that the rows are exchangeable within an arm, that lag-1
dependence is the only dependence, that arms were assigned as the plan says, or that the C-grid effect
generalises to another grid (the `-v3`/`-v4` grids do not separate the pair at all). A green verifier
means "these numbers are the numbers the code computes from these bytes", never "these numbers are
true of the model's latency".

Nothing here edits a rows, grade or measurement file; no inference request was made.
