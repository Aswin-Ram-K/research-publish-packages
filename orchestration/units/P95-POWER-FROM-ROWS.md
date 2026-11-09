# UNIT `P95-POWER-FROM-ROWS`

**One purpose:** answer, from rows already on disk, *how many turns a cell needs before its p95 is
stable enough to compare two arms* — so the 792-request A\* grid is justified or refused on evidence.
**Offline:** 0 inference requests. **Read-only** on every rows file. **Bound:** 28 tool calls.

Card tag: `automated` / `verdict` — no `ask_user_question`, no network, no inference.

## Question

`BUDGET-SCHEDULE` priced A\* at 4 arms × 48 turns × 3 reps = 792 requests, asserting `n_raw = 144`
usable timings per arm for H1. `PARM-1` fixes the H1 gate at disjoint 95 % intervals with n ≥ 60 per
arm — a floor, not a power calculation. What is a p95 interval width at 144, and is 144 enough for the
315 ms p50 gap to become a p95 gap?

## Method (as executed)

1. Census every `rows-*.jsonl` under `experiments/ptr-engine/measure/`: sha256 before and after,
   usable = `kind=="turn"` ∧ `ttft_ms > 0` ∧ `timing_usable is not False`. Every (file, arm) is its
   own set; no pooling across arms or grids; tools-grid distributions marked `attribution_disputed`.
2. Percentile bootstrap of the p95 (10 000 resamples) at n ∈ {24, 48, 60, 96, 144, 384}, reporting the
   interval width and the interval-of-intervals; `n > observed` flagged as ECDF extrapolation.
3. Paired resampling of the two H1 arms (pointer-stable vs transcript-grow, same grid only), 1000
   outer × 200 inner, counting disjoint 95 % intervals at n = 48, 60, 144 (plus 96/192/288/384 scan).
4. Lag-1 correlation of `ttft_ms` along turn order per run, Fisher-z pooled, implied effective n.
5. Verdict from the measured numbers, computed in code (not hand-written).

## Deliverables

| path | content |
|---|---|
| `docs/P95-POWER.md` | the answer, tables, verdict |
| `experiments/ptr-engine/measure/P95-POWER.json` | every number, generated deterministically (seed 20261026) |
| `experiments/ptr-engine/measure/p95_power_gen.py` | the generator (own artefact) |
| `experiments/ptr-engine/measure/p95-power-verify.sh` | the evidence command: regenerate → diff against committed JSON |
| `orchestration/units/P95-POWER-FROM-ROWS.md` | this card |
| `orchestration/handoffs/P95-POWER-FROM-ROWS.json` | handoff |
| `orchestration/journals/P95-POWER-FROM-ROWS.jsonl` | journal |

## Result

`A* sufficient` — on the grid A\* replicates (`rows-longrun-c`): intervals disjoint in 100 % of paired
resamples at n = 48, 60 and 144. Scope: 2 of 3 grids holding the same two arms do **not** separate
them at n = 144 (v3 1.6 %, v4 12.9 %; v4 reaches only 19.1 % at n = 384). No cell on disk holds more
than 48 usable timings, so 144 is everywhere an extrapolation; lag-1 ≈ 0.42 makes effective n at raw
144 only ≈ 66.

## Refusals honoured

No rows, grade, measurement, `analyze_stats.py`, `grade_v5.py`, `cell.py` or `docs/OPERATOR-BRIEF.md`
file was written. `quantile_ci` was not imported; `analyze_stats.py` sha256 recorded at run time anyway.
No bare p95 anywhere: every one carries its n and resample count.
