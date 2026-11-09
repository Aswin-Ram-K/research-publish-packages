# V10 Verification

Verdict: FAIL (one stale test; code-level defects closed).

Surviving defect: experiments/ptr-engine/longrun/tests/test_fixture_schema.py:73 uses stale ref "doc-secret@1" but fixture refs are now "doc-secret@r1", so the mutation never matches and no FixtureError is raised.

Test summary lines:
- tests/test_pointer_table.py: 10 passed in 0.01s
- tests/test_fetch_tool.py: 6 passed in 0.01s
- longrun/tests/test_fixture_schema.py: 1 failed, 5 passed in 0.04s
- longrun/tests/test_arm_cd_wiring.py: 6 passed in 0.53s
