# UNIT POOL-REPS-TOOL

**Purpose.** Build and prove the pooling step that turns three per-rep cells into the n=144/arm
reading H1 requires, without fabricating a measured cell.

**Frozen context.** `H1-CONDITIONING` (PASS `f17663d1`) freezes R-all = every completed turn,
n=144/arm. `TURN-CENSUS-60` found no rows file holding more than one rep and no cell reaching
n>=60; with 48 turns/rep, 48*0.05 = 2.4 < TAIL_MIN = 3, so a per-rep p95 is inadmissible by
arithmetic. The pooling operation did not exist.

**Writes (exactly).** `experiments/ptr-engine/tools/pool_reps.py`;
`experiments/ptr-engine/measure/pooled/**`; `tests/test_pool_reps.py`;
`experiments/ptr-engine/longrun/analyze_stats.py` (loading path only);
`orchestration/units/POOL-REPS-TOOL.md`; `orchestration/handoffs/POOL-REPS-TOOL.json`;
`orchestration/journals/POOL-REPS-TOOL.jsonl`.

**Bound.** 28 tool calls. Zero requests. Never writes `rows-cell-*`, `grade-*.json`, another
card's manifests, `cell.py`, `PARM-1`, or `analyze_stats.py` thresholds/quantiles.

**Refusals (named, tested).** `insufficient_reps`, `incomparable_provenance`, `era_a_excluded`,
`source_unusable`, `source_unreadable`, `rows_sha_mismatch`.

**Honesty rule.** The pooled file is derived (`derived: true`, `purpose: "H1 pooled R-all"`),
lives in `measure/pooled/`, is named `pooled-*` (never `rows-*`), and `analyze_stats` refuses to
read it unless `--pooled` is passed.
