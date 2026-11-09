# Unit LEASE-REOPEN-12

**Purpose (one):** measure ONE `lease-reopen` 12-turn cell (rep 1) on the generation-6 tree and decide
whether the lease arm can be certified and the grid launched.

**Bound:** 30 tool calls, one launch invocation, no retries, LIVE cap 24 requests.

**Write paths:** `experiments/ptr-engine/measure/LEASE-REOPEN-12.json`, `docs/LEASE-REOPEN-12.md`,
this card, `orchestration/handoffs/LEASE-REOPEN-12.json`, `journal/2026-10-26.md`.
Nothing else written; no forbidden file touched (`cell.py`, `run_longrun.py`, `run_a_star.py`,
`client.py`, `analyze_stats.py`, `grade_v5.py`, `HARNESS-PIN.json`, `GRID-PARAMS.json`,
`REQUEST-LEDGER.json`, baselines, fixtures, rows, grades).

**Launch:** no launcher edit. `--canary` is the only CLI form with `--turns 12` but ignores `--cell`
(4 arms = 48 requests > cap); used the launcher's own `cell_argv("lease-reopen", 1, "smoke", 12, 900)`
through `run_cell()`, i.e. its exact frozen cell argv, one cell.

**Evidence:** dry run exit 0 / `would_refuse=[]`; live rc 0, 64.1 s, 30 rows, 12/12 turns, 23 billed
rounds, census non-zero on every tool field; shape `shape_unknown` (0 answer_verified); treatment
cannot fire (fixture T23/T40 vs 12 turns). ⇒ `all_four_arms_ok: false`.
