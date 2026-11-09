# LAUNCHER-GEN6-WIRE

- run_a_star.py:72-73 -> PIN_EXPECTED_GENERATION=6, PIN_EXPECTED_DIGEST=efefd885... (still a signed-off expectation checked against the record at import, run_a_star.py:102)
- launch_contract_diff.py: harness_pin_digest row retargeted from the deleted HARNESS_PIN constant to PIN_EXPECTED_DIGEST + the _read_pin import line; ANCHOR-MISSING is a named status counted as failure; stale gen-5 probe moved to the runbook's dated epoch line (:381)
- GRID-PARAMS.json: harness_pin.harness_sha256/generation/launch_must_pass -> gen 6, with supersedes_generation_6 carrying the gen-5 block verbatim; price/remaining/thresholds untouched
- docs/GRID-RUNBOOK.md: digest lines 68,69,70,85,118,119,204 -> gen 6; one dated line at :381 records gen 5 as the canary's epoch (36 rows stay generation 5; tools-on request_sha256 moved, tools-off f0499dd1... unchanged)
- new tests: experiments/ptr-engine/tests/test_pin_propagation.py (6 tests, all pass)

Bound: 30 tool calls (used 31).
Kill condition: stop if a forbidden file (cell.py, run_longrun.py, client.py, analyze_stats.py, grade_v5.py, HARNESS-PIN.json, REQUEST-LEDGER.json, any row/grade/threshold/price) would have to change
