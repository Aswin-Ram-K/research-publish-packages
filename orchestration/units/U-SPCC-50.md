# U-SPCC-50 — fetch-round accounting on the fetch arm

## Defects

1. `fetch_rounds_used` was initialised at `experiments/ptr-engine/longrun/run_longrun.py:3359`
   and never incremented on the `bounded-context-fetch` path — the only arm that fetches.
   The E1 cell stamped `0` on 52 rows and `null` on 66 while spending 18 of its 48-round
   pool, and `manifest['tools']['fetch_rounds_used']` stayed `0`.
2. The manifest's `tools` block was frozen at launch and never updated at finalisation, so
   a finished cell reported launch POLICY rather than what happened.

## Change

- `run_longrun.py` — the D arm's inline follow-up is a billed round, so
  `fetch_rounds_used += 1` now happens where the round is actually spent (right after the
  follow-up's `sent += 1`). The generic `fetch_rounds` path already incremented; its
  follow-up rows now carry the cumulative value too.
- Every row of a tools-on run carries `fetch_rounds_used`: the turn's rows inherit the
  turn-start value from `extras`, and the follow-up rows and the turn row override it with
  their own cumulative value, so row order is monotonically non-decreasing. A tools-off
  run never stamps it — `null`, not `0`.
- `_observed_tools(rows_path, available)` reads the cell's own rows at finalisation and
  `_gate_finish` rewrites `doc["tools"]` with `fetch_rounds_used` (the durable
  `fetch_rounds_spent` ledger), `fetch_rounds_available` (the frozen pool) and
  `tools_schema_sent` (the wire fact).
- No fetch budget, per-turn cap or arm behaviour changed.

## Evidence

Red (pre-fix `run_longrun.py`, new test):
`AssertionError: None unexpectedly found in [None, 0, None, 0, 0]` — the counter stuck at
0 while 2 rounds were spent; `AssertionError: 0 != 1` — the finalised manifest reported
the launch default.

Green: `3 passed`; the counter ends at `2` for 2 spent rounds, tools-off stamps `null`,
and the finalised manifest reports `fetch_rounds_used=1` for a 1-round cell.

Acceptance suite: `test_fetch_rounds_accounting.py`, `test_fetch_arm_row_persistence.py`,
`test_arm_cd_wiring.py` → 14 passed. `tools/doc_check.py` → exit 0.
