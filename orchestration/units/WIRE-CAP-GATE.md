# WIRE-CAP-GATE — the budget cap stops a request BEFORE it is sent

**Parent card:** 9d182ed2-34ec-491c-be23-ff6d24b0650b. Runs only after `REQUEST-LEDGER`
(a2c4508e) settled `done`.

## Why
`REQUEST-LEDGER` shipped a cap gate and wrote its own limit into its handoff
(`orchestration/handoffs/REQUEST-LEDGER.json`, field `known_limit`): *"the gate reads rows on
disk, so it sees a request only after the writer recorded it; hard pre-send prevention needs
record->gate->send ordering or an in-memory counted allocation. As shipped it buys detection,
not prevention."* Measured on `LIVE-SMOKE-CELL` (dbed0e9d): the planned cell was 130 requests
and the ledger would have learned about the overspend only after the money was gone.

## What was built (prevention, not detection)
`experiments/ptr-engine/longrun/run_longrun.py`:

* `load_request_ledger()` imports `experiments/ptr-engine/tools/request_ledger.py` (the
  counting rule is never re-implemented; `REQUEST_LEDGER_TOOL` may point the import at a copy).
* `RequestCapGate` reads rows **once at run start** (`spent_at_start`), then keeps an
  **in-memory authoritative count**: `acquire(turn, kind)` reserves the slot BEFORE the send
  and raises `CapRefusal` when the run would exceed either the declared allocation
  (`--request-allocation N|projection`, default `projection`) or the global
  `--budget-cap`/`--budget-reserve` headroom.
* Call sites: the digest request, the turn request (immediately BEFORE `client.chat()`), and
  every tool **follow-up** inside `fetch_rounds` — follow-ups bill separately.
* Exit `4` propagates unmodified (`run_cell` -> `main` -> `sys.exit`); `3` (usage) and `5`
  (unreadable rows) likewise. Refusal arithmetic keeps the ledger's fields and adds
  `allocation= used_in_run= turn= kind= projected= over_by=`.
* Exit reconciliation: re-scan, require `spent_after - spent_at_start == used_in_run`.
  `delta > 0` -> exit `9` + delta printed (a bug); `delta < 0` (a request stranded mid-turn by
  a refusal) -> loud `CAP GATE UNRECORDED` line, never silent.
* Manifest: additive `cap_gate` block written at start (allocation, spent_at_start) and at
  exit (running + final count, reconciliation); `frozen_sha256` keeps `--resume` verification
  working after the addendum. No existing key changes meaning; `measure/REQUEST-LEDGER.json`
  needed no new field.
* Untouched gates: exit 8 (projection), `--turn-wall-cap`, `--runaway-turns`, the `sent >=
  budget` aborts, and `cell.py`'s preflight (WIRE-GATES owns that chain).

## Tests (offline: zero inference requests, no network, no git; every transport a fake)
`experiments/ptr-engine/longrun/tests/test_cap_gate.py` — 9 cases: zero rows on refusal
(transport never called), mid-run refusal at the right turn, follow-up counting, allows +
manifest count, red->green (neutered pre-send call writes rows; restored writes none),
reconcile divergence, and exit 4/3/5 through the process.

## Bound / write paths
<= 32 tool calls; write paths exactly: `run_longrun.py`, `experiments/ptr-engine/longrun/tests/test_cap_gate.py`,
`docs/REQUEST-LEDGER.md` (additive), `orchestration/units/WIRE-CAP-GATE.md`,
`orchestration/handoffs/WIRE-CAP-GATE.json`, `orchestration/journals/WIRE-CAP-GATE.jsonl`.
