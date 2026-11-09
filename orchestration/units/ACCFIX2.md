# ACCFIX2

**Purpose.** Re-scope `acc.2`–`acc.4` of `tasks-v4/runtime-v4/LR-01.v5.json` to read-only checks and re-scope the 8 execution-demanding turn instructions, plus `long_run.what_grows` and `generation_reason`.

**Target.** `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v5.json` (`LR-01.v4.json` untouched).

**Changes.**
1. `acceptance.checks_prose` indices 1 and 3 replaced with read-based prose; `checks_structured` acc.2/acc.3/acc.4 synced to the already-correct `acceptance.checks` entries.
2. `turns[4,10,16,22,28,34,40,46]/question` replaced with a read-only inspection task.
3. `long_run.what_grows` reworded to the read-only equivalent.
4. `generation_reason` extended to record the turn-instruction re-scope.

**Recursive walk.** 7 hits remain, all in `/items[*]/body` as `with pytest.raises(...)` inside quoted Python (legitimate). Zero hits in `/acceptance/*`, `/turns/*/question`, `/long_run/*`.

**Satisfiability.** Plain-read transcript with matching answers → `verified_success: true`, `failed_required: []`, exit 0. Contradicting answers → `verified_success: false`, `failed_required: ['acc.2','acc.3','acc.4']`.

**Suite.** `.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests -q` aborts at collection on pre-existing `test_verdict_semantics` (exit 14); not introduced by this change.

**Tool calls.** 18 (bound 45).