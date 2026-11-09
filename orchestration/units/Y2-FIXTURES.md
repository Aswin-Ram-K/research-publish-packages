# Y2-FIXTURES — X1.3/X1.4/X1.8/X1.10/X1.11 fixture + checker + test repairs

**Unit type:** BUILD (no live calls).
**Status:** done.

## Write paths
- experiments/ptr-engine/longrun/tasks-v6/PT-0{1,2,3}.v9.json
- experiments/ptr-engine/longrun/check_pointer_fixtures.py
- experiments/ptr-engine/tests/test_fetch_tool.py
- experiments/ptr-engine/longrun/tests/test_fixture_schema.py
- experiments/ptr-engine/longrun/PIN-UPDATES.md
- orchestration/units/Y2-FIXTURES.md
- orchestration/handoffs/Y2-FIXTURES.json

## Deliverables
- PT walls derived: PT-01 6629, PT-02 6888, PT-03 6369 (transcript-grow slope 64.979, P1 5134, target turn floor(N/2)).
- fetch_budget_tokens=1024 + provenance in each PT fixture.
- checker hard-fails: nonexistent checkpoint doc, unresolvable fetch ref (non-NOT_FOUND), no tool_outputs, non-null wall under UNMEASURED.
- fetch_tool: malformed args marked invalid; budget test uses non-1:1 tokenizer.
- test_fixture_schema: mutation count assertion.
- PIN-UPDATES.md: three new digests.
