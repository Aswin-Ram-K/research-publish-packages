# R2-VLLM-RERUN — re-run both vLLM cells with the repaired instrument

**Purpose.** Re-run both vLLM cells (OH1 + OH1L on `gx10-occamy-nvfp4`, A1 on prod
`gx10-qwen9b`) with the repaired `pmu16_cell.py`, and produce a run record that can be
verified — replacing the discarded 420-row dry run (blind usage accounting on OH1/OH1L +
collapsed arm identity).

**Hard bound.** 35 tool calls excluding the long-running background job's polling reads.
If the cell cannot be launched after 3 attempts: STOP and report `partial`.

**Declared write paths.**
- `experiments/context-cache/cells/R2-VLLM/rows.jsonl`, `analysis.json`, `logs/**`
  (incl. `discarded-r1/**`, `rerun-console.log`), `logs/cache-occamy/**`
- `experiments/context-cache/.occamy.lock` (acquire/release only)
- `orchestration/units/R2-VLLM-RERUN.md`, `orchestration/handoffs/R2-VLLM-RERUN.json`

**Hard rules.** `gx10-occamy-nvfp4` is never stopped/restarted/removed (read-only:
`docker inspect`, `/health`, `/v1/models`, `/metrics`), health re-checked after every phase.
No prod and variant at once. Respect `TOTAL_REQUEST_CAP` / `ARM_REQUEST_CAP` and record any
truncation. A failed request stops its phase; never "measure through" a failure.

## Sequence and what actually happened

| # | Step | Outcome |
|---|---|---|
| 1 | Reclaim stale lock via the cell's own `acquire_lock` | **Not stale.** First attempt `TimeoutError` (errno 11). A live legitimate holder released at `02:48:57Z` with `note: "R2-VLLM done"`. Reclaimed immediately after (`ACQUIRED`). |
| 2 | Purge dry run to `discarded-r1/` | `rows.jsonl` (420 rows, sha `2737125f…5045c`) + `analysis.json` (sha `8e9e45cf…89515`) moved, both shas preserved. |
| 3 | Replace interrupted A1 attempt | **`r2v-a1` already absent.** Prod had been restored by the prior lock holder (Up, started `02:46:40Z`). No teardown needed; `capture_pre()` was live. |
| 4 | `--all` full cell | Attempt 1 ran OH1 to 54 rows then died: `Runner.send() got an unexpected keyword argument 'extra'`. The console tail read mid-run was misleading; `run.json` on disk was still the 02:35 run. |
| 5 | Analyse new rows | **Not reached** — no battery rows exist. |
| 6 | Prove instrument not blind | **Partially reached** — OH1 grid/baseline/tokens rows *are* blind-usage-free (`usage_has_details=true` on all 54, cached hits 3120–16992 recorded). Battery (arm identity 4/4) has **no rows**. |

## Blocker (found by audit, not by a failed launch)

`ARM_REQUEST_CAP = 200`, but the repaired battery alone spends **128** requests
(`2 passes × 16 turns × 4 arms`), on top of ~54 pre-battery requests for OH1
(`gate 2 + grid 16 + baseline 6 + tokens ~30`). A full OH1 arm is ~183–190 requests, and a
relaunch always replays the ~54 non-battery rows first, so the arm guard trips at the battery
sequentially and **permanently** — observed twice on this cell as
`arm cap reached for OH1: 219/200` and `for A1: 201/200` (02:35 run, before this unit).
Relaunching without raising the cap cannot produce battery rows.

The `extra=` defect is a separate, narrow failure in the same phase: `Runner.send`
(lines 525–534) lacks the `extra` keyword that `phase_battery` passes at line 987, while
`build_row` already accepts and merges `extra` — so the fix is one keyword-forwarding line.

## Verdict

`partial`. Instrument repairs are live-verified on OH1's grid/baseline phases; the battery
(arm identity) and A1 are unmeasured on the new rows. Returning to the REPAIR unit is correct
— these are instrument changes, and this unit's contract forbids measuring through them.
