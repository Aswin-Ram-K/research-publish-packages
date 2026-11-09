# UNIT `FETCH-BUDGET-48` — does the per-arm fetch budget survive a 48-turn tools-on cell?

**Status:** done · **Cost:** 0 requests, 0 network, 0 live cells · **Bound:** 24 tool calls (used 17).

## One purpose
Decide, from rows already on disk, whether `TOOL_FETCH_ROUNDS_PER_ARM = 24`
(`run_longrun.py:226`) survives a 48-turn tools-on cell, and what happens to the turns after it
closes.

## Conclusion
**`budget_sufficient`.** The V6 cell (per-turn cap 3 + serve-from-prompt) billed **20 of 24**
rounds, all by **T16**, and **0** in T17–T48; **0** `fetch_budget_exhausted` refusals in 371 tool
calls. No turn ran with the channel shut, so the cell is measurement to T48. The only closure on
disk is the pre-V6 configuration (v5, 24 rounds inside T3), which confounded **45** turns, still
carried a read invitation on **43 of them**, and produced **1** cap-length completion (T29, 4096).

## Evidence (counts, not rates)
- v6: 20 rounds, closes never, last billed T16, histogram `{0:39, 1:3, 2:1, 3:5}`, p50 0 / p90 3 / max 3.
- v4: 20 rounds, closes never, last billed T30 — but its rounds billed on `path_not_found`, so not a
  modern demand measurement.
- v5: 24 rounds by T3 (21 bought at T3 alone), then 45 turns with 226 refusals, 41 with tool calls.
- Fixture census re-derived: **46/48** path-ref turns in v7 and v8 (non-inviting: T30, T48).

## Recommendation (a separate card, not applied)
`TOOL_FETCH_ROUNDS_PER_ARM` → **48**, price `480 + 480 + 4 = 964` against 3,219 remaining
(+240 over the frozen 724). Also raise per-cell `--budget` from 67 to at least `turns + B`, because
`48 + 24 = 72` already exceeds 67 (`run_longrun.py:961`).

## Bound on residual
Earliest closure is T8 (24/3 per turn) → a **5-turn canary cannot see it**. `RUN-A-STAR-2` rule 8 is
**not on disk**; the mechanism it names is `run_longrun.py:2560`, exit 6 on the second cap-length
completion — after ≥2 turns are already wasted.

## Write paths
`docs/FETCH-BUDGET-48.md` · `experiments/ptr-engine/measure/FETCH-BUDGET-48.json` ·
`orchestration/units/FETCH-BUDGET-48.md` · `orchestration/handoffs/FETCH-BUDGET-48.json` ·
`orchestration/journals/FETCH-BUDGET-48.jsonl`

## Not touched
`run_longrun.py`, `cell.py`, the fixture, `GRID-SHAPE.json`, the graders, the analyser, any row
file, any published number.
