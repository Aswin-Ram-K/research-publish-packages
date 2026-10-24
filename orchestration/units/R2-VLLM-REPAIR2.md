# R2-VLLM-REPAIR2 — make the live send path and the request cap provable offline

**Status:** done (offline). **Bound:** max 22 tool calls. **Locks:** none taken.
`experiments/context-cache/.occamy.lock` was never read for writing nor modified.

## Why this unit exists
`R2-VLLM-REPAIR` (14/14 offline) left two defects that no check could see, because no check
ever drove `phase_battery` through `Runner.send`. The live rerun died at its **first** battery
request (`PHASE FAILED OH1: Runner.send() got an unexpected keyword argument 'extra'`,
`logs/rerun-console.log`) and, once patched, twice on the cap
(`arm cap reached for OH1: 219/200`, `logs/run.json`).

## Findings that changed the work
1. **The card's premise was stale.** `Runner.send` already carried
   `extra: dict | None = None` when this unit started — but it **never forwarded it** to
   `build_row`. So the live crash was already patched (an unlogged editor touched the cell at
   22:06:59Z), yet every battery row would have been written **silently without**
   `arm_compaction` / `arm_render` / `prompt_nodes` — a worse, quieter defect. Fixed by
   forwarding `extra=extra`; `build_row` stays the only owner of the merge.
2. **`ARM_REQUEST_CAP` was 500**, not 200 — again from an unlogged editor. 500 breaks the
   documented 1000-total bound (4 configs x 500); set to **260** (measured worst case 219 + 41).
3. **`test_plan_is_within_cap` encodes a 2-config assumption** (`2*per_config <= TOTAL_REQUEST_CAP`)
   while the run drives three configs. The assertion is not mine to rewrite (it is accepted
   proof); noted in `logs/repair-offline.json` under `_edit_note` and here.
4. **A live rerun was already in flight** (~22:10Z) appending `rows.jsonl` (54 -> 236). This unit
   never wrote it.

## Changes
**`pmu16_cell.py`**
- `Runner.send` forwards `extra` to `build_row` (one merge owner).
- `BatteryBudgetExceeded`, `battery_request_cost()`, `BATTERY_COST_EXPR`, `battery_budget_preflight()`.
- `phase_battery` calls the pre-flight **before the first request**.
- `ARM_REQUEST_CAP = 260`; `TOTAL_REQUEST_CAP` stays the global bound (1000).

**`selftest_offline.py`** (additive only)
- `prove_R8_real_battery_send_path` — drives the **real** `phase_battery` x 4 arms x 2 passes on a
  temp `ROWS_PATH` with an in-memory client; asserts 128 rows, extras on every row, 4 distinct
  `prefix_sha256` per turn, 16 distinct pass-1 salts, pass 2 == pass 1 bytes.
- `prove_R9_battery_budget_preflight` — 54 seeded rows fit and complete; `ARM_REQUEST_CAP=100`
  raises the named error with **0 rows and 0 requests** written.
- `httpx.Client` now **raises** and counts attempts (the old "raises on Client()" claim was not
  actually enforced).
- Two new red→green reverts: `extra_dropped_from_Runner_send`, `arm_cap_restored_to_200`.

## Result
`pass=15 fail=1` over 16 checks; all **14 original assertions untouched** (13 measured-identical to
the 21:42Z record). The single failure, `test_R7_analysis_guard`, is **environmental**:
its last assertion reads the real `analysis.json`, which does not exist on disk mid-rerun, so
there is no stale analysis to refuse. It passed at 21:42Z for the same reason it fails now.
Red→green: **4/4**.

## Not done (out of scope, named)
No live battery, no container, no lock, no `rows.jsonl` write. `next_unit_hint` carries the
relaunch recipe.
