# Unit `ERA-B-ANALYSIS-CONTRACT` — one command from finished cell files to the fixed-terms report

**Card:** `2511822e-e600-4809-973b-d2d81217f468` · execution `a00e6c49` · 2026-10-26 · OFFLINE, 0 requests, 0 live cells.

## Purpose
`RUN-A-STAR-2` requires a report in terms decided **in advance**: H1 pooled R-all via
`quantile_ci` with effective n beside every interval, H2 both limbs with sign, H3 `x/12` +
`x/9` + `answered_ratio` + `contract_adherence` + exact McNemar, TVS or `UNDEFINED`,
verbosity before cost, spend delta. No emitter existed, so a nine-hour live run would have
ended in a hand-written summary. This unit adds the **consumer**: one command, refusals
tested before any real data exists.

## Bound
≤60 tool calls, offline, additive only. No edit of `cell.py`, `run_longrun.py`,
`run_a_star.py`, `analyze_stats.py`, `grade_v5.py`, `launch_contract_diff.py`, any fixture,
the pin, the params, any threshold or any published page. No synthetic cell may be written
into `measure/rows-cell-*`.

## Write paths (declared)
- `experiments/ptr-engine/tools/run_grid_report.py`
- `experiments/ptr-engine/tests/test_run_grid_report.py`
- `experiments/ptr-engine/measure/GRID-REPORT-2.json`
- `docs/GRID-REPORT-2.md`
- `orchestration/units/ERA-B-ANALYSIS-CONTRACT.md`
- `orchestration/handoffs/ERA-B-ANALYSIS-CONTRACT.json`
- `orchestration/journals/ERA-B-ANALYSIS-CONTRACT.jsonl`

## The command
```
python3 experiments/ptr-engine/tools/run_grid_report.py --write
# exit 0 emitted (may contain refusals) · 2 no cell files · 3 baseline missing
```
Reads `measure/rows-cell-*.jsonl` + manifests + `GRID_CELL_SANITY` stamps + `GRID-SHAPE.json`
+ `LEDGER-GRID-BASELINE-2.json` + `REQUEST-LEDGER.json` (+ `--grade` for H3/TVS).

## Imported, never re-implemented
| need | owner |
|---|---|
| one row per turn | `analyze_stats.turn_latency_rows` (`analyze_stats.py:805`) |
| p50/p95 + refusal text | `analyze_stats.quantile_ci` (`:350`) |
| p95 floor | `analyze_stats.min_n_for(0.95)` (`:330`) → 60 |
| cap-length exclusion | `analyze_stats.split_truncated` (`:937`) |
| `usable_for` record | `analyze_stats.select_usable_cells` (`:737`) |
| arm provenance | `analyze_stats.provenance_cells` (`:1246`) |
| comparability gate | `row_provenance.same_provenance` (`row_provenance.py:78`) |
| H1 floor/compare, H2 limbs, H3, TVS | `verify_tranche1.h1_estimate/h2_tokens/h2_compare/h3/tvs_for_arm` (`verify_tranche1.py:105,152,180,223,285`) |
| lag-1 autocorrelation | `p95_power_probe.lag1` (`p95_power_probe.py:55`) |

**Finding, not a reimplementation:** `analyze_stats` has **no** `minimum` function. The only
floors it owns are `MIN_N = 20` (`analyze_stats.py:112`) and `min_n_for(0.95) == 60`
(`:330`). No second copy was written.

## The keys it emits (JSON, in this order)
`schema · unit · offline · terms · inputs · cells[] · h1{grids[],floor} · h2{per_arm[],comparison} ·
h3{x_12,x_9,none_flagged,answered_ratio,contract_adherence,mcnemar{b,c,p},verdict} ·
tvs | "UNDEFINED" + tvs_reason · verbosity{per_arm[]} · spend{baseline,spent_now,delta,price_expectation} ·
price_artefact · epochs_never_pooled[] · missing_arms[] · refusals[] · verdicts`

`verbosity` is emitted **before** `spend` in both the document and the page (`test_j`).
Every interval carries its own `n` and its `source_paths`; a refused interval is
`{"refused": <verbatim analyser text>}` and never a number.

## The three refusal modes, with their synthetic proofs
| mode | synthetic cell | proof |
|---|---|---|
| `not_adjudicable_floor` | 40 turns, one arm | `test_red_raw_floor_guard` — refuses at the raw floor, quoting `quantile_ci`'s text |
| `not_adjudicable_effective_n` | 120 turns, `r≈0.99` | `test_b` — names `pointer-stable`, prints `n_used=120` and `n_eff<60` |
| `not_adjudicable_quality` | no grade document | `test_h` — H3 `not_adjudicable`, `tvs == "UNDEFINED"`, never `0` |

Plus two structural refusals: `usable_for` **absent** (`test_d`, the `analyze_stats.py:749`
include-on-absence trap — the analyser keeps it, this consumer refuses it) and a missing
ledger baseline (`test_g`, exit 3, `delta` never assumed from 0).

## Red → green (three guards neutered, quoted)
1. `effective_n_verdict` → `assert 'adjudicable' == 'not_adjudicable_effective_n'`
2. `raw_floor_verdict` → `assert 'not_adjudicable_effective_n' == 'not_adjudicable_floor'`
3. `cell_inclusion` → `assert True is False`

Each is restored in the same test (`monkeypatch.undo()` + a green re-assertion).

## Tests
`experiments/ptr-engine/tests/test_run_grid_report.py` — **13 passed** (cases a–j + three
red→green). Synthetic cells live in pytest's tmp dir only; the two real rows files are
byte-identical before and after (sha256 re-checked against
`measure/LEDGER-GRID-BASELINE-2.json::rows_inventory`).

## Result on the disk as it stands
Both `rows-cell-*` files are stamped `usable_for: []` in `measure/GRID-CELL-SANITY.json`
(the 27-row era-A abandoned cell and the 6-row pre-RUN-A cell). `GRID-REPORT-2.json`
therefore emits **no grid**, five recorded refusals, `tvs: "UNDEFINED"`, `spend.delta: 0`
against baseline 1,128 — the honest pre-data state, produced by the same command that will
be run after the ninth hour.

## Findings for the card after this one
1. **`price_expectation: 1056` has no artefact.** `measure/GRID-PARAMS.json:price.total`
   prices the grid at **1,016** (964 tranche + 48 canary + 4 warm-ups). The report emits the
   card's 1,056 as *declared* and the artefact's 1,016 beside it with
   `matches_price_expectation: false` — reconciled, not rounded.
2. **The effective-n floor is a raw-n floor.** Inverting `n(1−r)/(1+r) ≥ 60` gives
   `n ≥ 60(1+r)/(1−r)`: r=0.05 → 66.3, r=0.10 → 73.3, r=0.20 → 90.0, r=0.30 → 111.4,
   r=0.40 → 140.0. A single 48- or 60-turn cell cannot clear it; a 3-rep arm (144) clears
   up to r≈0.41. Measured on synthetic case (a): 60 turns at r=0.052 gives `n_eff=54.04`.
3. **`contract_adherence` has no column in `grade_v5`.** The report carries the frozen
   placeholder string and says so; nobody should read it as a measurement.
4. `analyze_stats` — the function the card names as `minimum` does not exist (see above).

## The sentence
**What can no longer be decided after the data is seen:** whether an arm is adjudicable at
all — the p95 floor, the effective-n floor, the era boundary, the `usable_for` refusal and
the verbosity-before-cost order are all fixed in code now, so a reader cannot pick an
interval, pool era A into era B, or quote a cost before a verbosity figure after the fact.
