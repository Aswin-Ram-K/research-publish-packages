# P1Gate01

**Purpose.** Determine why gate 0.1 composite `verified_success` is false despite seven target checks passing; fix.

**Provenance.** `controls/pos-full.jsonl` is a hand-assembled control derived from `measure/rows-longrun-c-2026-10-26.jsonl` (commit f17663d); not a raw recording. Turn 48 is a genuine model abstention caused by a deliberately incomplete working set.

**Truncation (by design).** Fixture `tasks-v2/runtime-v2/LR-01.v2.json` pins `items[].body_bytes` = 1680 (resolve.py) and 331 (errors.py); errors.py holds only 3 classes. No size cap bug in a builder; the fixture intentionally provides an incomplete working set to test abstention.

**Change.** Reclassified control as `synthetic-abstention` (header `control_kind`), reverted turn 48 to original abstention, dropped `synthetic_turns`. Retained metadata. Extended `self_test()` with two negative controls: (a) verify turn missing "exit 0" -> acc.2 false; (b) original truncated working set -> acc.2/3/4 false. Removed the premature composite assertion.

**Evidence.** Truncated control: verified_success=False, failed_required=[acc.2,acc.3,acc.4]. Insufficient-verify: verified_success=False, failed_required=[acc.2]. test_grade_v6_derive.py 14 passed.

**Gate 0.1 status.** Cannot pass today: no recorded run has a complete working set (v4 fixture has errors.py 6353 bytes but no control log). Gate 0.1 proves a truncated working set must not verify; it does not yet prove a positive case.

**Write paths.** `longrun/score_longrun.py`, `longrun/controls/pos-full.jsonl`, `orchestration/units/P1Gate01.md`, `orchestration/handoffs/P1Gate01.json`.
