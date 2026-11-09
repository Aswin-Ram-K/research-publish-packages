# Unit: VERDICT-BACKFILL-FIXTURE-GENERATIONS

**Purpose (one):** clear the `test_verdict_ritual` red caused by `FIXTURE-GENERATIONS` settling `done`
with no verdict row — by recovering its own recorded acceptance command, re-running it today, and
recording a row only if it exits 0.

**Card:** `96ec0bcc-9d40-444a-a0f8-c82c7e27f9ec` · **Execution:** `efa8039f-751e-4ceb-b3e5-eaef3df6f8b5`
· **HEAD observed:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`.

**Hard bound:** ≤14 tool calls, 0 network requests, offline. Stop at step 2 with `no_recorded_command` if
no command was recorded; stop with no row if the command exits non-zero.

**Write paths (exactly):**
- `experiments/ptr-engine/measure/VERDICT-BACKFILL-FIXTURE-GENERATIONS.json`
- `docs/VERDICT-BACKFILL-FIXTURE-GENERATIONS.md`
- `orchestration/units/VERDICT-BACKFILL-FIXTURE-GENERATIONS.md`
- `orchestration/handoffs/VERDICT-BACKFILL-FIXTURE-GENERATIONS.json`
- `orchestration/journals/VERDICT-BACKFILL-FIXTURE-GENERATIONS.jsonl`

**Forbidden:** editing `FIXTURE-GENERATIONS`' deliverables or its handoff; editing
`test_verdict_ritual.py` to silence the red; recording a row for a command that does not exit 0 today.

**Result:** command recovered verbatim (4 entries), re-run exit 0 twice (10/10 `ok` digests and 5 passed),
row recorded `PASS` at `f17663d1`; `test_verdict_ritual` now green (10 tests OK); suite still exit 1 with
179 tests and 1 failure in `test_gate_operand_validation` (`F1: expected exit 8, got 1`), outside this
card's write paths.
