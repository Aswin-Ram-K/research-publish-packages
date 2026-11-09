# TURN-CENSUS — how many completed turns does this corpus actually hold?

**Unit:** `TURN-CENSUS-60` · **Cost:** 0 inference requests, 0 network calls. Counts, never rates.
**Machine-readable twin:** [`TURN-CENSUS.json`](../experiments/ptr-engine/measure/TURN-CENSUS.json).

**Definition used (the current one, no local re-implementation).** Every row was passed through
`analyze_stats.turn_latency_rows` — the turn's own initial request (`kind="turn-initial"` when
present, the legacy `kind="turn"` row as a marked fallback); `kind="tool-followup"` rows dropped.
`usable` = that turn's rows minus `stop_reason="length"`. TTFT statement: `ttft_ms is not None`.

**Floor.** `min_n_for(0.95) = 60` (imported from the analyser, not copied).

## Per file · per arm

| file | arm | turns | usable | ttft_present | excluded (length) | usable_for |
|---|---|---|---|---|---|---|
| rows-baseline-2026-10-26.jsonl | C | 12 | 12 | 0 | 0 | — |
| rows-baseline-2026-10-26.jsonl | C0 | 12 | 12 | 0 | 0 | — |
| rows-baseline-2026-10-26.jsonl | R | 12 | 12 | 0 | 0 | — |
| rows-cell-pointer-stable-20261026T145758Z.jsonl | pointer-stable | 6 | 6 | 6 | 0 | **[]** |
| rows-cell-pointer-stable-20261026T182535Z.jsonl | pointer-stable | 27 | 26 | 27 | 1 | **[]** |
| rows-equalinfo-2026-10-26.jsonl | C0F | 12 | 12 | 0 | 0 | — |
| rows-equalinfo-2026-10-26.jsonl | C0FT | 12 | 12 | 0 | 0 | — |
| rows-equalinfo-2026-10-26.jsonl | R | 12 | 12 | 0 | 0 | — |
| rows-live-2026-10-26.jsonl | (none) | 27 | 27 | 0 | 0 | — |
| rows-longrun-2026-10-26-fix.jsonl | lease-reopen | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-fix.jsonl | pointer-stable | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-fix.jsonl | transcript-compact | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-fix.jsonl | transcript-grow | 12 | 12 | 12 | 0 | — |
| rows-longrun-2026-10-26-policy.jsonl | lease-reopen | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-policy.jsonl | pointer-stable | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-policy.jsonl | transcript-compact | 3 | 3 | 3 | 0 | — |
| rows-longrun-2026-10-26-policy.jsonl | transcript-grow | 28 | 28 | 28 | 0 | — |
| rows-longrun-2026-10-26.jsonl | lease-reopen | 48 | 48 | **0** | 0 | — |
| rows-longrun-2026-10-26.jsonl | pointer-stable | 48 | 48 | **0** | 0 | — |
| rows-longrun-2026-10-26.jsonl | transcript-compact | 48 | 48 | **0** | 0 | — |
| rows-longrun-2026-10-26.jsonl | transcript-grow | 48 | 48 | **0** | 0 | — |
| rows-longrun-c-2026-10-26.jsonl | lease-reopen | 48 | 48 | 48 | 0 | — |
| rows-longrun-c-2026-10-26.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-longrun-c-2026-10-26.jsonl | transcript-compact | 48 | 48 | 48 | 0 | — |
| rows-longrun-c-2026-10-26.jsonl | transcript-grow | 48 | 48 | 48 | 0 | — |
| rows-longrun-v3-2026-10-26.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-longrun-v3-2026-10-26.jsonl | transcript-grow | 48 | 48 | 48 | 0 | — |
| rows-longrun-v4-2026-10-26.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-longrun-v4-2026-10-26.jsonl | transcript-grow | 48 | 48 | 48 | 0 | — |
| rows-longrun-v4-tools-2026-10-26.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-longrun-v5-tools.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-longrun-v6-tools.jsonl | pointer-stable | 48 | 48 | 48 | 0 | — |
| rows-pilot-thinking-2026-10-26.jsonl | transcript-grow | 5 | 5 | 5 | 0 | — |

Raw rows on disk **1,128** → turns selected by the current definition **915**: 213 rows are not
turns (follow-ups, foreign kinds, non-rows). Every file reports `definition_fallback: true` — no
file on disk carries `kind="turn-initial"`; the legacy `kind="turn"` row is the selector everywhere.

## Q1 — does any cell/arm reach ≥60 usable turns?

**No. None. 0 of 15 files, 0 of 15 arms-by-file rows.** The largest usable count anywhere is 48.

## Q2 — maximum usable turns per cell per arm anywhere

**48** (`rows-longrun-v6-tools.jsonl` / `pointer-stable`, tied with every other 48-turn cell).
Of those 48, only the cells whose `ttft_present` is 48 carry a latency sample at all:
`rows-longrun-c` (all four arms), `longrun-v3`, `-v4`, `-v4-tools`, `-v5-tools`, `-v6-tools`.
`rows-longrun-2026-10-26.jsonl` has 48 turns per arm but **0** non-null `ttft_ms`: turns without
timings cannot produce a percentile.

## Q3 — what a single cell would need, and whether it is reachable

A cell needs **n ≥ 60 usable turns** to publish a p95 without pooling (`min_n_for(0.95) = 60`,
i.e. `n·(1−q) = 60 × 0.05 = 3 ≥ TAIL_MIN`). At the pre-registered 48 turns/arm it is **not
reachable** — 48 leaves 2.4 tail observations, below `TAIL_MIN = 3`, which is exactly why the
analyser refuses. It becomes reachable only at ≥60 turns per arm, i.e. only by **pooling across
reps** (3 × 48 = 144) or by lengthening the cell beyond 48 turns. No `rows-*.jsonl` on disk
contains more than one rep; there is no file where reps are already pooled.

## Consequence for PARM-1's H1

The adjudicating grid is **10 cells × 48 turns × 3 reps per arm**, so R-all pools to **144 turns
per arm** and the p95 is therefore admissible at the pooled level while inadmissible at every
single cell. `docs/H1-CONDITIONING.md:76` states it as a table row:

> | **R-all** | PARM-1 frozen, primary | `select_r_all(rows, fire_turn=None)` | every completed turn | 48 | **144 all four arms** | **yes** |

and `docs/H1-CONDITIONING.md:42-43` gives the arithmetic that makes the pooling load-bearing:

> n=48 : 48 × 0.05 = 2.4 < TAIL_MIN = 3 → per-rep p95 is INADMISSIBLE (that is why PARM-1 pools)
> n=144 : 144 × 0.05 = 7.2 → the top ~7 observations set p95 (rank span 132–142)

**Verdict on the withdrawn p95s: keep them withdrawn; they cannot be restored per cell.** No
re-count, re-derivation or dedup fix reaches 60 turns in any cell, because the cells were *built*
at 48 turns. The only p95 this grid can produce is the pooled R-all figure at n=144, and it can
produce one only once three reps per arm of actual `ttft_ms` rows exist on disk — the single-rep
48-turn files in this corpus, with the two `usable_for: []` cells excluded, cannot supply it.

## Census stamp situation

`measure/GRID-CELL-SANITY.json` stamps **both** cell files `usable_for: []`
(`cells[0]` = 27 rows, `cells[1]` = 6 rows). Published figures still citing a stamped cell:

- `docs/RUNAWAY-POLICY.md:34` — `ttft_ms_p50 141.58`, taken over the 27 `kind=turn` rows of
  `rows-cell-pointer-stable-20261026T182535Z.jsonl`, which the census excludes.
- `docs/ANALYSIS-PATH.md:33` — the same computation quoted as a reproduction
  (`ttft_p50 n=27 141.58ms [131.35, 166.38]`).
- `docs/ANALYSIS-CONSUMER.md:100` — counts (`27 → 25`) over the same cell.

All three are census/audit citations, not grid claims: `docs/LATENCY-REPORT.md:259` records the
cell as excluded by name and reports p95-bearing cells as **0**. No *published p95* cites a
`usable_for: []` cell; two *census* readings do.

## One sentence

This corpus can produce **zero** publishable p95 values today — every cell holds at most 48 usable
turns against a floor of 60, and the two certified-second-opinion cells are stamped `usable_for: []`
— and for the grid to produce one there must be **3 usable reps × 48 turns × ≥1 arm of non-null
`ttft_ms` rows pooled to n=144 per arm**, since no single 48-turn cell can ever clear `min_n_for(0.95)=60`.
