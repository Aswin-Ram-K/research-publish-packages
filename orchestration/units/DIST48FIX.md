# DIST48FIX

**Purpose.** Redesign TX-02 fixture so 48 checkpoints sit on 48 unique turns (one question per turn), keeping 12 fact-to-query distances {2,8,20,32} x 12 facts; close two checker gaps; add three red-then-green tests.

**Target.** `experiments/ptr-engine/longrun/tasks-v7/TX-02.v1.json`, `experiments/ptr-engine/longrun/check_pointer_fixtures.py`, `experiments/ptr-engine/longrun/tests/test_tx02_distance.py`.

**Changes.**
1. Redesigned TX-02: 12 fact introduction turns [1,2,5,6,15,16,41,42,51,52,55,56]; 48 distinct checkpoint turns (max 88); N=88; four distance buckets of 12; 48 distinct expected values.
2. Checker: reject answer kind vs expected value type mismatch; reject duplicate checkpoint turns; reject checkpoint whose question is not the one the runner would inject.
3. Tests: added duplicate-checkpoint-turn, kind/type mismatch, injected-question identity tests.

**Suite.** `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_tx02_distance.py -q` -> 13 passed. TX-01 contrast tests pass (7).

**Tool calls.** ~40 (bound 60).