# Unit CAPGATE-FOREIGN-RED

**Purpose:** settle `experiments/ptr-engine/longrun/tests/test_cap_gate.py::test_c_followup_counts_as_a_second_unit`, which had
been charging other cards' acceptance commands with a FAIL (`SEAM-TEST-RED`, `CLAIM-ROW-STAMP`,
`WIRE-CAP-GATE`).

**Bound:** <=14 tool calls, 0 inference requests, offline.
**Write paths:** `experiments/ptr-engine/longrun/tests/test_cap_gate.py`,
`experiments/ptr-engine/measure/CAPGATE-FOREIGN-RED.json`, `docs/CAPGATE-FOREIGN-RED.md`,
`orchestration/units/CAPGATE-FOREIGN-RED.md`, `orchestration/handoffs/CAPGATE-FOREIGN-RED.json`,
`orchestration/journals/CAPGATE-FOREIGN-RED.jsonl`.

**Finding:** the test was stale. `run_longrun.py:2462-2520` implements one-row-per-send
(`TURN-ROW-ATTRIBUTION`): k=1 writes `['turn-initial','turn']`, and the turn row measures the
follow-up. The invariant test `experiments/ptr-engine/longrun/tests/test_row_attribution.py:222-231` is the contract.

**Action:** replaced only that assertion with the per-send invariant (distinct `request_sha256`,
`send_index`, `row_measurement_source`, `fetch_followup`), and stamped a per-send
`request_sha256` in the scenario's fake transport so the invariant is measurable.

**Result:** cap gate 9/9 OK; row attribution 5 passed; longrun full 176 tests with one unrelated
pre-existing red (`test_verdict_ritual`); repo-root pytest 2 failed / 1375 passed / 1 skipped,
both failures outside this unit's write paths.
