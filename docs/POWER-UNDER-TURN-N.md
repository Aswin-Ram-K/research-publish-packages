# POWER-UNDER-TURN-N — the power verdict at the denominator the analyser uses

**Unit** `POWER-UNDER-TURN-N` · **cost** 0 inference requests, 0 network events, 0 live cells · **edits**
`docs/POWER-UNDER-TURN-N.md`, `experiments/ptr-engine/measure/POWER-UNDER-TURN-N.json`,
`experiments/ptr-engine/tests/test_power_under_turn_n.py`, the unit card, handoff and journal · **touches**
no revision to the analyser, no threshold, no `PARM-1*` clause, no grid card, no ledger, no published page.

**Verdict: `grid_underpowered`.** The 1,016-request launch grid gives the H1 pair **144 raw turns/arm**,
which clears the raw p95 floor (144 ≥ 60) but is worth only **31.36 effective timings** on
`pointer-stable` (lag-1 **0.6423**) — **52 %** of the 60 floor. It clears the floor only under the
**pooled** dependence estimate (`62.89`). The n that would not be is **276 → 288 raw turns/arm**
(6 runs × 48), priced at **1,056 requests** for a conformant four-arm grid.

---

## 1. Why the denominator mattered

`P95-POWER-FROM-ROWS` (PASS `f17663d1`) concluded **`A* sufficient`** from paired-resample disjointness
**100 % at n = 48/60/144**, a **254 ms** margin, median lag-1 **0.417** and `n_eff(144) ≈ 66`. Four later
settled cards changed what `n` counts:

| card | finding |
|---|---|
| `ANALYSIS-CONSUMER-FIX` / `TTFT-KIND-DEFINITION` | per-turn TTFT = **the turn's own initial request** (`kind='turn-initial'`, else the legacy `kind='turn'` row with `definition_fallback`); a `kind='tool-followup'` row is a request **inside** a turn and is never a turn's latency (`ttft-definition/1`) |
| `TURN-CENSUS-60` | max **48 usable turns** per cell per arm; **zero** cells reach `min_n_for(0.95) = 60` |
| `LATENCY-REDERIVE-TRUNCATED` | the tools-on grids are **n = 47 / 47 / 48 turns**, not 68 / 70 / 72 requests |

A power claim whose `n` is not the analyser's `n` is a claim about a different measurement. This unit
re-derives every number from **the same pinned rows** with the analyser's own selector.

## 2. Method (nothing invented, nothing tuned)

- **Selector:** `analyze_stats.turn_latency_rows(rows)` — one row per `(arm, rep, turn_index)`;
  `kind='tool-followup'` dropped and counted; duplicates collapsed.
- **Exclusion:** `stop_reason ∈ {length, runaway_turn}` or `truncated=true` leaves the latency
  population and is counted.
- **Estimator:** `analyze_stats.quantile_ci(values, q, resamples=10000, seed=20261026)`. It refuses when
  `n < MIN_N` or `n·(1−q) < TAIL_MIN = 3`, so a p95 needs **n ≥ 60** and its refusal text is quoted
  verbatim rather than worked around.
- **Resampling:** paired **run-block** bootstrap. A *run* is one `(rows file, arm, rep)` group. Each outer
  pair draws `n` turns per arm by drawing runs with replacement and then turns within the pooled runs; two
  200-resample percentile intervals of p95; **disjoint** when they do not overlap; 1 000 outer pairs.
  **Block count, stated plainly:** every longrun file on disk carries `rep = 1`, so **every arm has
  exactly 1 block** and the run bootstrap is **degenerate** — it collapses to a turn bootstrap. It is
  reported as degenerate, not repaired. The launch grid would have 3 blocks/arm, and the design reading
  uses `n_eff = runs × n_eff_within_run`, which equals `n(1−r)/(1+r)` for a common `r`.
- **Floor diagnostic:** the `n < 60` rows additionally report the fraction computed **without** the tail
  floor, only so the prior request-n card can be compared like for like. Those are **not admissible**
  readings and are labelled as such in the JSON.

## 3. Per-grid, turn-n (arms, n after dedup, n after the stop-reason drop)

`p50`/`p95` are the analyser's point estimates on the turn series; the interval column is
`quantile_ci(..., 0.95)` — refused wherever the floor bites.

| grid | arm | n request filter | n turn (dedup) | n turn after drop | p50 ms | p95 ms | p95 interval |
|---|---|---|---|---|---|---|---|
| `rows-longrun-c` | pointer-stable | 48 | 48 | **47** | 166.96 | 308.86 | **refused** |
| `rows-longrun-c` | transcript-grow | 48 | 48 | **48** | 482.24 | 838.85 | **refused** |
| `rows-longrun-c` | transcript-compact | 48 | 48 | 48 | 202.49 | 224.08 | **refused** |
| `rows-longrun-c` | lease-reopen | 48 | 48 | **34** | 136.17 | 166.71 | **refused** |
| `rows-longrun-v3` | pointer-stable | 48 | 48 | 47 | 168.27 | 232.83 | **refused** |
| `rows-longrun-v3` | transcript-grow | 48 | 48 | 48 | 200.65 | 230.48 | **refused** |
| `rows-longrun-v4` | pointer-stable | 48 | 48 | **40** | 187.81 | 284.88 | **refused** |
| `rows-longrun-v4` | transcript-grow | 48 | 48 | 48 | 199.79 | 227.23 | **refused** |
| `rows-longrun-v4-tools` | pointer-stable | **68** | 48 | 47 | 201.64 | 307.59 | **refused** |
| `rows-longrun-v5-tools` | pointer-stable | **72** | 48 | 47 | 139.43 | 200.26 | **refused** |
| `rows-longrun-v6-tools` | pointer-stable | **72** | 48 | 48 | 144.81 | 339.46 | **refused** |
| `rows-cell-pointer-stable-…182535Z` | pointer-stable | 27 | 27 | **25** | 141.58 | 562.35 | **refused** |

**Every single cell is refused, by name.** At n = 47:

```
refusing p95 at n=47: the 95% order-statistic span is ranks 42-47 (p89.4-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60
```

At n = 48:

```
refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60
```

The request filter is what the tools-on grids' old `n` came from: **72 rows → 48 turns → 47 after the
truncated-turn drop** on `rows-longrun-v5-tools`, and **68 → 48 → 47** on `rows-longrun-v4-tools`. On the
non-tools longrun grids the two filters agree (one ttft row per turn), which is why the C-grid values do
not move.

## 4. Disjointness, request-n and turn-n side by side

Paired resamples whose two p95 intervals are disjoint (%). `REF` = the frozen estimator refuses that n, so
no admissible fraction exists; the bracketed number is the floor-ignoring diagnostic.

| grid | pop. | n=47 | n=48 | n=60 | n=96 | n=144 |
|---|---|---|---|---|---|---|
| `rows-longrun-c` (C vs A) | request-n | REF [100.0] | REF [100.0] | 100.0 | 100.0 | **100.0** |
| `rows-longrun-c` (C vs A) | **turn-n** | REF [100.0] | REF [100.0] | 100.0 | 100.0 | **100.0** |
| `rows-longrun-v3` (C vs A) | request-n | REF [1.5] | REF [1.1] | 2.5 | 1.2 | **1.5** |
| `rows-longrun-v3` (C vs A) | **turn-n** | REF [1.9] | REF [2.7] | 1.5 | 1.7 | **2.9** |
| `rows-longrun-v4` (C vs A) | request-n | REF [3.9] | REF [4.7] | 5.0 | 4.7 | **9.0** |
| `rows-longrun-v4` (C vs A) | **turn-n** | REF [5.3] | REF [6.6] | 7.9 | 6.2 | **12.3** |

The side-by-side is the finding: on these three grids the denominator change moves the *admissibility
boundary* (nothing below 60 is publishable at all) far more than it moves the *fraction*, because each of
these grids already carried ≈1 ttft row per turn. What the old card called "100 % at n = 48" is a
**diagnostic at an inadmissible n**, not a p95 reading.

## 5. The three questions

### (a) Single cell (n ≈ 48) or only the pooled 3-run (n ≈ 144)?

**Only the pooled 3-run reading is admissible.** At n = 47/48 the estimator refuses a p95 outright
(`48 × 0.05 = 2.4 < 3`), so **no single cell in the grid can carry the H1 comparison**. Pooling 3 runs
reaches 144 = 7.2 tails, admissible, and there the pair separates in **100.0 %** of paired resamples. The
effect is already decisive at 48 — the floor-ignoring diagnostic is **100.0 %** there too — so what
pooling buys is **admissibility, not separation**.

### (b) Does the 315.29 ms C-grid gap survive at turn-n, and do v3/v4 stay non-separating?

**Yes, unchanged.** `rows-longrun-c` at turn-n: **p50 gap 315.29 ms**, **p95 gap 529.99 ms** — identical
to the request-row figures, because that grid has one ttft row per turn (48 rows → 47 usable turn rows for
C, 48 for A). `rows-longrun-v3` reproduces **32.39 ms p50 / −2.35 ms p95**; `rows-longrun-v4`
**11.99 ms / −57.65 ms** — and both stay non-separating: **2.9 %** and **12.3 %** disjoint at n = 144
under turn-n (1.5 % / 9.0 % under request-n). The 12–32 ms gaps are not adjudicable at any n on this
corpus.

### (c) n_eff at turn-n, and does the pooled 144 clear 60 after the discount?

Turn-n lag-1: **0.3921** Fisher-z pooled over 13 sets, **0.4598** median; on the H1 pair specifically
**0.6423** (`pointer-stable`) and **0.1071** (`transcript-grow`).

| raw turns/arm | n_eff @ pooled r = 0.3921 | n_eff @ median r = 0.4598 | n_eff @ C's r = 0.6423 |
|---|---|---|---|
| 48 (1 run) | 20.96 | 17.76 | 10.45 |
| 96 (2 runs) | 41.92 | 35.52 | 20.91 |
| **144 (3 runs)** | **62.89** ✅ (+2.9) | **53.29** ❌ | **31.36** ❌ (−28.6) |
| 192 (4 runs) | 83.85 | 71.05 | 41.82 |
| 288 (6 runs) | 125.77 | 106.57 | **62.73** ✅ |

So the pooled 144 clears 60 **only** under the pooled dependence estimate (62.89, a 4.8 % margin) — it
does **not** clear under the median r (53.29) and is at **half** the floor under the arm whose interval has
to be the tight one (31.36). The floor must be met by the binding arm, so the answer to (c) is **no**.

## 6. Verdict and the price of the design that would not be underpowered

**`grid_underpowered`.**

The 1,016-request grid is 10 cells × 48 turns (`grid_resume.py`, read-only): `pointer-stable r1-r3`,
`transcript-grow r1-r3`, `transcript-compact r1-r2`, `lease-reopen r1-r2`. So the H1 pair gets
**144 raw turns/arm = 3 runs × 48** — the "pooled 3-rep 144" is not an extrapolation beyond the design,
only beyond the rows on disk. Forcing numbers:

- raw admissibility: 144 ≥ 60 ✅ (but no single cell publishes a p95, and `PARM-1:142` already forces reps ≥ 2);
- effective on the binding arm: **31.36 < 60**, a shortfall of 28.64 (52 % of the floor);
- it clears only under the pooled r (62.89), i.e. the verdict flips on an assumption about dependence.

**What would not be:** **276 → 288 raw turns/arm** (6 runs × 48; `PARM-1:137` pins 48 turns/arm, so the
only lever is runs). Price at the ledger factor **1.374532**:

| design | turns | requests | remaining of 3,192 |
|---|---|---|---|
| 288 turns/arm, pair only | 576 | 792 | 2,400 |
| **288 turns/arm pair + 96 turns/arm on B and D (2 runs each, `PARM-1:142`)** | **768** | **1,056** | **2,136** |
| at the rounds-aware rate the 1,016 grid uses (turns + rounds) | 768 | ≈ 1,540 | ≈ 1,652 |

**PARM-1:150-152** (`docs/PREREG-ARM-RUN.md:150-152`) defines the adjudicating grid as **all four arms in
the same grid with identical `fixture_sha256` and identical reasoning policy**. A pair-only 792 therefore
**does not** satisfy it. The smallest conformant shape that both satisfies the four-arm clause and clears
the binding arm's effective floor is the **768-turn / 1,056-request** row above: affordable out of the
3,192 remaining, and no rule has to be relaxed (48 turns/arm is preserved, reps = 6 ≥ 2, thinking off,
one fixture). No 60-turn shape is admissible — the fixture `N = 48` is frozen — which is why the price is
paid in **runs**, not in depth.

## 7. What is not derivable, and what this does not do

- **not_derivable:** whether the launch grid (era B, v8 fixture, tools-on) reproduces the C-grid effect —
  no v8 rows carry `ttft_ms`.
- **not_derivable:** a genuine multi-run block bootstrap from on-disk rows — every longrun file carries
  `rep = 1`, so every arm has **1 block** and the run bootstrap is degenerate. This is stated, not papered over.
- **limit:** per-turn TTFT in tools-on cells is `attribution_disputed` (`definition_fallback` true;
  `mirrored_rows = 3/48` in `rows-longrun-v5-tools` where a turn has follow-ups), so a tools-on H1 read is
  a turn-initial request only where the row model says so.
- **Not touched:** the analyser, the thresholds, `PARM-1*`, the grid card, the ledger, every published
  page. No live cell was run. This is a re-derivation from pinned rows.

## 8. Reproduce

```bash
cd experiments/ptr-engine
python3 -c "import json;d=json.load(open('measure/POWER-UNDER-TURN-N.json'));print(d['verdict'],d['verdict_forcing_numbers'])"
python3 tests/test_power_under_turn_n.py --red-green      # turn selector, not the request filter
```

Machine-readable twin: [`POWER-UNDER-TURN-N.json`](../experiments/ptr-engine/measure/POWER-UNDER-TURN-N.json)
(per-cell series counts, per-arm turn metadata, the full power table, the lag-1 set table, the refusal
strings, the price arithmetic). Seed `20261026`, 1 000 outer × 200 inner resamples, 10 000-resample
interval bootstrap, all rows files sha256-recorded in the artefact.
