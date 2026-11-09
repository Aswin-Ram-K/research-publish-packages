# UNIT `LIVE-CANARY-4ARM-2` — run the pinned four-arm canary once, then decide on the 16-cell grid

**Card** `e07e2764-ff52-41bb-a663-272335d45154` · **Execution** `f4578fcf-e8ca-482b-b553-9d78e9e5e2e4`
**Permission** workspace-write · **Mode** automated (never ask the user) · **Bound** one live canary
invocation, hard cap **52** requests, no retries; stop at the first precondition that fails.

## Objective (as carded)

Verify seven preconditions on disk, then invoke the pinned four-arm canary **once**
(4 arms × 12 turns = 48 requests), classify each arm with the settled rules
(`shape_ok` requires `answer_verified ≥ 1` **and** `stop_signal_source=finish_reason`), and decide
in writing whether the **1,056-request / 16-cell** grid may launch.

## Bound and stop condition

- One live invocation of the canary path. A second attempt needs its own card.
- Every precondition is a hard gate: **any failure ⇒ STOP without spending.**
- The launcher (`experiments/ptr-engine/tools/run_a_star.py`) is the only permitted argv builder;
  hand-assembling a `cell.py` argv is forbidden. If the launcher cannot run a canary, that is a
  defect to report, not a prompt to improvise.

## Result — `blocked_before_spend`, decision `GRID HELD`

Preconditions 1, 2, 3, 4 and 7 **pass** (quoted in `docs/CANARY-ERA-B-2.md` and in
`experiments/ptr-engine/measure/CANARY-ERA-B-2.json`). Preconditions **5 and 6 fail**:

- **5** `python3 experiments/ptr-engine/tools/launch_contract_diff.py --check` → exit 1,
  `KeyError: 'components'` at `experiments/ptr-engine/tools/launch_contract_diff.py:653`
  (`params["price"]["components"]["tranche"]`) — `measure/GRID-PARAMS.json` was rewritten at
  `2026-10-26T20:20:00Z` by `GRID-PARAMS-16CELL` as schema `consonance.grid-params/3`, which no
  longer carries `price.components`.
- **6** `python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --dry-run`
  → exit 1, `HARNESS-PIN record disagrees with the launcher: record generation=5 digest='35ff41b7…',
  launcher gen 4 digest='fa6fd8cc…'`. `run_a_star.py:51` still pins generation 4 and `:64` refuses
  any other generation; `HARNESS-PIN.json` names the owner as `HARNESS-PIN-WIRING successor`
  (`wiring.status = "PENDING ADVANCE"`).

Because the launcher cannot build the argv, step 8 is unreachable. No arm was measured; every arm
is therefore `shape_unknown` and is not rounded to `shape_ok`. **The grid stays HELD.**

**Spend: `spent_before 1128 / spent_after 1128 / delta 0`** (from `measure/REQUEST-LEDGER.json`,
`generated_at 2026-10-26T18:56:31Z`), i.e. the 48-request canary remains unspent and the 52 cap was
never approached.

## What this unit did NOT do

- Did not run the canary (unreachable), so there is no per-arm table and no era-B shape census.
- Did not edit, re-pin or work around `run_a_star.py`, `cell.py`, `run_longrun.py`,
  `launch_contract_diff.py`, `HARNESS-PIN.json`, `GRID-PARAMS.json`, any fixture, threshold or
  published page. A canary that can move the pin it is measured against is the defect this batch
  already paid for twice.
- Did not re-pin. The tree moved under this card (GRID-PARAMS.json at 20:20:00Z); a canary may not
  run on an unrecorded tree.

## Write paths (exactly)

`orchestration/units/LIVE-CANARY-4ARM-2.md` · `orchestration/handoffs/LIVE-CANARY-4ARM-2.json` ·
`orchestration/journals/LIVE-CANARY-4ARM-2.jsonl` ·
`experiments/ptr-engine/measure/CANARY-ERA-B-2.json` · `docs/CANARY-ERA-B-2.md`

## Next

Advance `run_a_star.py`'s `HARNESS_PIN` (and its `:64` generation check) to generation 5, and
repair `launch_contract_diff.py` for the `grid-params/3` record. Then re-run **this card's step 8
unchanged** — the canary argv, price and cap are still correct.
