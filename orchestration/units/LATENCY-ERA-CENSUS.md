# LATENCY-ERA-CENSUS — the latency side's era census

**Status:** done · **Card:** `9d172796-49ab-4043-8157-eb928ea73fe3` · **Execution:** `1511a317-8862-4e41-916e-335d97e8cc45`
**Bound:** 24 tool calls · **Used:** ~20 · **Live requests: 0 · Network: none · Inference: 0**

## Why this unit exists

The quality side already had an era census (`QUALITY-ERA-TABLE`: 50 grade files → 17 current / 1 pre-T3 / 28 pre-grade_v5 / 4 undatable). The **latency** side — H1's and the operator's headline metric — had none. This unit answers, from the rows already on disk: **which TTFT measurement era produced each rows file, and which of the 12 published p50 values (plus the 2 surviving p95s) sit on rows the fixed client would have timed differently.**

## Write paths (exactly these, nothing else)

- `docs/LATENCY-ERA-CENSUS.md`
- `experiments/ptr-engine/measure/LATENCY-ERA-CENSUS.json`
- `orchestration/units/LATENCY-ERA-CENSUS.md` (this file)
- `orchestration/handoffs/LATENCY-ERA-CENSUS.json`
- `orchestration/journals/LATENCY-ERA-CENSUS.jsonl`

**Never edited:** any rows file, any grade file, `docs/LATENCY-REPORT.md`, `measure/LATENCY-REPORT.json`, `client.py`, `run_longrun.py`. Proven, not asserted: all 14 computed rows-file sha256 values equal the digests `LATENCY-REPORT.md` §8.1 publishes.

## Deliverables

| # | deliverable | where |
|---|---|---|
| 1 | **Era classifier** — stated as a rule, applied per rows file: `post-client` / `pre-client` / `mixed` / `undatable`, with field-presence counts and sha256 per file, and the one file named as unclassifiable | census doc §1–§2 |
| 2 | **The exposed share** — rows the old latch could have mistimed, at row level (`tool_calls` non-empty) and at the card's run level (`tool-followup` present in the run) | census doc §3 |
| 3 | **Era label for every published figure** — 12 p50 cells + 2 surviving p95s + the withdrawn G7 p95 | census doc §4 |
| 4 | **The quotable sentence** | census doc §0, JSON `headline.quotable_sentence` |
| 5 | **The empirical cross-check** — `ttft ≈ wall` counted both ways per era | census doc §5, JSON `cross_check` |
| 6 | **Reproducible generator** — the fenced `python3` block *is* the computation; regenerating rewrites the JSON byte-identically | census doc §10 |

## Findings, short form

1. **Era:** 14 declared files / 1,101 rows → **1 post-client** file (6 rows) · **10 pre-client** files (863 rows) · **3 undatable-no-TTFT** files (232 rows) · **0 mixed** · **0 unclassifiable-but-declared**. `measure/rows.jsonl` (49 rows, calibration corpus, not declared) is the file named as unclassifiable.
2. **Exposure:** **186 of 1,101 rows (16.89 %)** carry `tool_calls`; the card's run-level rule makes it **212 (19.26 %)**. **All of them sit in the three tools-ON pre-client files**; the other 11 declared files carry no `tool_calls` and no follow-up row, so the latch is structurally unreachable there.
3. **Published numbers:** **0 of 12** p50 cells is `era-clean`; **12 of 12** are wholly pre-client; **9 of 12** are provably defect-inert (0 exposed rows); **3** (G7, G8, G9) are exposed on every row. G8/G9's p95s are published, G7's is withdrawn — **all three pre-client**, so era does not decide the withdrawal.
4. **Cross-check:** the `ttft ≈ wall` signature is **absent** — **0 of 186** tool-call rows are null and **0 of 186** are within 1 % of wall (ttft/wall: min 0.00122 · p50 0.08291 · p95 0.22169 · max 0.39053); **0 of 1,101** declared rows timed as wall. The **post-client column is empty**: the only post-client file has 0 tool-call rows, so the fixed latch's tool-call path has never written a row any published cell used.
5. **Correction to the brief:** the old latch did **not** fall back to `wall_ms` — it left `ttft_s` **`None`** (`HEAD`'s `run_longrun.py:1077`; snapshots `manifests/v6-run-longrun-pre-edit.py:874`, `manifests/v4tools2-baseline-pre.py:762`). Its failure mode is **silent deletion from every quantile**, not a wall-inflated tail. Neither occurred on disk.

## Boundaries respected

- No quantile recomputed; every p50/p95 is copied from `measure/LATENCY-REPORT.json`. The floor policy stays with `LATENCY-UNDER-DISPUTE`; the power question stays with `P95-POWER-FROM-ROWS`.
- No file of a different era pooled into a figure without a label.
- `run_longrun.py` changed twice under this unit (live ownership `TURN-ROW-ATTRIBUTION`); all three observed sha256 values are recorded in the census §8 and in the JSON as a static sequence, and the era boundary rests on the **immutable committed** `:1077`, not on working-tree bytes.
