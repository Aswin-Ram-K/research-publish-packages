# Unit card — CANARY-ERA-B-3

**Purpose.** Run ONE live 4-arm × 12-turn era-B canary, classify each arm from the rows, and decide whether the grid may launch.

**Hard bound.** 30 tool calls; one invocation, no retries; 52-request cap. (Used 18 tool calls; 1 invocation; 36 requests.)

**Write paths (declared).**
- `experiments/ptr-engine/measure/CANARY-ERA-B-3.json`
- `docs/CANARY-ERA-B-3.md`
- `orchestration/units/CANARY-ERA-B-3.md` (this card)
- `orchestration/handoffs/CANARY-ERA-B-3.json`
- `orchestration/journals/CANARY-ERA-B-3.jsonl`

**Forbidden.** `cell.py`, `run_longrun.py`, `run_a_star.py`, `analyze_stats.py`, `grade_v5.py`, `measure/HARNESS-PIN.json`,
`measure/GRID-PARAMS.json`, `measure/REQUEST-LEDGER.json`, any fixture, any row, any grade file, any published page.

**Stop rule.** If any precondition failed, send zero requests and report. If the launcher is broken, stop and report — do not repair it on this card.

**Result.** `status: done`. All four preconditions PASS. The canary ran once: 3 of 4 cells, 36 requests, delta 36 ≤ 52.
Classification from rows: `pointer-stable` degenerate (t4), `transcript-grow` degenerate (t1,2,4,5,11),
`transcript-compact` ok, `lease-reopen` unknown (never ran — launcher precondition 10). Decision **HOLD**,
`grid_may_launch: false`.

A hold here is a successful result: the card's job was to measure and classify, and it did both.
