# Unit DESIGN-V3 — wall-clock projection and a grid that fits a 6-hour block

**Card:** measurement-analysis and design. Zero inference requests. Automated session (no answerer).

## Objective

Turn "the long-run programme is tens of hours" into arithmetic from the row files that already exist, and
propose three grids plus one recommendation that does not relax `LONGRUN-PREREG.md` §4.

## Bound and kill

Max 20 tool calls. Stub handoff (`status=partial`, blocker `in progress`) written first so a sweep cannot
mistake silence for completion. If the rows had not carried `latency_s`, the answer would have been
`NOT PROJECTABLE` and stopped.

## Inputs read (all read-only)

- `experiments/ptr-engine/measure/rows-longrun-2026-10-26.jsonl` (192 Stage-1 rows; timing only, content invalid)
- `experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.jsonl` (22 rows; two `max_tokens` groups: 4096 n=9, 16384 n=13)
- `experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl` (17 rows, all `max_tokens=16384`)
- `experiments/ptr-engine/LONGRUN-PREREG.md` + `orchestration/handoffs/LONGRUN-PREREG.json` (the frozen rule, N=60, 2 reps, 500 requests)
- `experiments/ptr-engine/longrun/{METRICS.md,analyze_longrun.py}` and `longrun/runtime/LR-0*.json` (N = 48/64/56/40/72/60, `wall_tokens=65536`)

## Write paths (only these)

`experiments/ptr-engine/longrun/project_wallclock.py`,
`experiments/ptr-engine/longrun/DESIGN-V3.md`,
`experiments/ptr-engine/longrun/policy_reasoning_cap.json`,
`orchestration/handoffs/DESIGN-V3.json`, `orchestration/units/DESIGN-V3.md`.

Not touched: `run_longrun.py`, `score_longrun.py`, `longrun/fixtures/`, `longrun/runtime/`, `papers/`,
`state/`, `tests/`, `dockets/`.

## Method

1. Read every row file, group by `max_tokens`, never pool across groups (the script refuses to price a grid
   unless `--price-max-tokens` names one group).
2. Per arm: n, usable latency, mean/p50/p95/max latency, mean completion tokens, and hours for N turns at 1 rep.
3. Census of rows above 120 s, truncations, and `completion==16384`.
4. Correlate latency with completion length and with turn index to test "does latency grow with depth".
5. Price the pre-registered grid, the approved 1,360-request grid, and three candidates.

## Result

- Stage-1 timings are unusable for cost (empty 128-token parses); pricing on them understates ~20×.
- r(completion_tokens, latency) = **+0.997**, 27.6–38.0 tokens/s: latency is completion length, not depth.
- 16,384 triggers runaway turns: 9 rows ≥12k tokens average 450.9 s; 6 truncations across the two 16k groups.
- Approved 1,360-request grid = **27.18 h median / 136.89 h p95** at 16k. Recommendation:
  204 requests at cap 4,096, N=48, four arms, one rep = **3.44 h median / 5.84 h p95** — fits one 6-hour block.

## Kill condition met?

No. Projection was defensible; the three files are committed and the script re-runs clean (exit 0) and
refuses correctly (exit 2).
