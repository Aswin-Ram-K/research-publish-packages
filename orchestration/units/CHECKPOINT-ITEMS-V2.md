# CHECKPOINT-ITEMS-V2 — unit card (persisted)

**Purpose (one).** Make the 12-item checkpoint grid of `CHECKPOINT-COVERAGE` (f6d1bb5c) fully
decidable *at the fixture level*: every item declares a machine-checkable one-line answer form, every
truth is AST-derived, `cp.10.t36`'s expected-truth record matches the grader's schema, and the new
version carries an explicit `old_id → new_id` map. Do **not** re-freeze H3 — record both denominators
and request an errata.

**Trigger.** `CHECKPOINT-COVERAGE` settled with 8 of 12 gradeable: three `NONE` items aborted with
`SystemExit: fixture_truth_mismatch: <id> has no usable answer_spec` and `cp.10.t36` raised
`KeyError: 'function'`. H3 is stated over 2 of 12 at 16.7 pp, so an 8-item denominator would silently
turn the same two successes into 25 pp.

**Write paths (declared).** `experiments/ptr-engine/longrun/tasks-v6/`,
`experiments/ptr-engine/longrun/tests/test_checkpoint_items_v2.py`,
`experiments/ptr-engine/measure/CHECKPOINT-ITEMS-V2.md`, `orchestration/units/CHECKPOINT-ITEMS-V2.md`,
`orchestration/handoffs/CHECKPOINT-ITEMS-V2.json`, `orchestration/journals/CHECKPOINT-ITEMS-V2.jsonl`.
`grade_v5.py`, historical fixtures, row files, grades, `ANCHOR-PREREG*`, `PARM-1` and every settled
document are **not** written.

**Bound.** ≤30 tool calls, zero inference requests, no network, no `git`. Partial within 4 calls if
blocked. **Automated**: no `ask_user_question`; a missing value becomes a recorded assumption.

**Result.** `partial` — the decidability repair and the new version ship and are proven; requirement 2's
*NUM-or-CALL-only* recast for the three former `NONE` items is refused on measured grounds (§5 of the
measure doc) and those three items are named.

**Evidence.** 9 tests pass; coverage gate `PASS: 12/12 … none colliding`; 24/24 synthetic probes;
red→green on `cp.2.t12`; both historical sha256 digests unchanged; new fixture sha256 `42b4df00…`.

**Next hint.** Prereg owner: one-line errata (`margin = 2 / decidable`), then wire `LR-01.v7.json` into
`run_longrun.py` / PARM-1 through the §7 id map.
