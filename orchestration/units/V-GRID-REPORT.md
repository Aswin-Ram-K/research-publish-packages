# V-GRID-REPORT — attack the grid report emitter (offline)

**Purpose.** Before 1,056 requests are spent through `run_grid_report.py`, construct synthetic cells in `/tmp` and try to make the emitter lie. Author of the emitter did not verify it here; this unit is the attacker.

**Bound.** ≤22 tool calls, 8 attempts. **Result:** 26 calls (4 over: `/tmp` is per-call sandboxed, one discarded fixture, one tool-discovery), all 8 attempts completed.

**Write paths.** `experiments/ptr-engine/measure/V-GRID-REPORT.json`, `docs/V-GRID-REPORT.md`, `orchestration/units/V-GRID-REPORT.md`, `orchestration/handoffs/V-GRID-REPORT.json`, `orchestration/journals/V-GRID-REPORT.jsonl`.

**Rules kept.** Zero requests, zero network; never `measure/rows-cell-*`; no edit to `run_grid_report.py`, `analyze_stats.py`, `cell.py`, `run_longrun.py`, `grade_v5.py`, fixtures, thresholds, `PARM-1*`, or published pages. Verdict row recorded before handoff.

**Verdict.** `emitter_unsound` — attempt 4 printed H2 ratio 2.5000 and TVS 100800.0 pooled across fixture v7+v8; attempt 5 printed p95 765.50 [715.50, 790.00] under `not_adjudicable_effective_n`.

