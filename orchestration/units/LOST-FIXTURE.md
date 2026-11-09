# LOST-FIXTURE

**Purpose:** quantify what a missing fixture digest costs the record. Offline, read-only on every existing file.
**Bound:** <=24 tool calls, 0 requests.
**Deliverables:** docs/LOST-FIXTURE.md, experiments/ptr-engine/measure/LOST-FIXTURE.json, state/logs/lost-fixture-baseline.json, experiments/ptr-engine/longrun/tests/test_lost_fixture.py.
**Result:** 261 lines / 259 rows pin 72c3832d95f9c7966b4358eda10fa2882775a416ee8a663d57b1c871ed19c44d across G1 stage1 (192), G2 smoke-rp (40), G3 fix-smoke (27 of 29). No file behind it; recoverable false. 20 manifests name a surviving path (b7e303a6...) with the lost digest. Guard freezes the 259 misses, forward-only.
