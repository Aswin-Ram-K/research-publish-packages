# DIST48

**Purpose.** Create a 48-checkpoint fixture measuring fact-to-query distance as a dose-response: 12 distinct transient facts, each introduced once, queried at distances {2,8,20,32}. Zero live requests.

**Bound.** Fixture + checker (additive) + test; no subagents, no git mutations.

**Deliverables.**
- `experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json`: schema `consonance.longrun-fixture/2`, gen-7, N=72, 48 checkpoints, 12 fact docs, fetch_scenarios for all four outcomes.
- `experiments/ptr-engine/longrun/check_pointer_fixtures.py`: added `validate()` with duplicate-expected, reachability (fact value only in its tool output), distance-match, gradability checks; `check()` accepts path or in-memory dict.
- `experiments/ptr-engine/longrun/tests/test_tx02_distance.py`: 10 tests, all pass.

**Evidence.**
- checker: TX-02.v1.json OK, 48 checkpoints, N=72, counts {2:12,8:12,20:12,32:12}.
- expected values: 48/48 unique.
- distances: all 48 match measured turn gap.
- pytest test_tx02_distance.py: 10 passed; test_tx01_contrast.py: 7 passed.
