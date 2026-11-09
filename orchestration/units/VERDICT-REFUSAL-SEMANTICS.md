# Unit VERDICT-REFUSAL-SEMANTICS

**Objective.** Stop the verdict table calling a budget refusal a failure, using this batch's own
closures. (a) Triage the recent FAIL closures; (b) write `docs/VERDICT-SEMANTICS.md` with the
exit-code partition; (c) make it mechanical in
`experiments/ptr-engine/tools/verdict_semantics.py` + `longrun/experiments/ptr-engine/longrun/tests/test_verdict_semantics.py`;
(d) record a row that measures this unit's own work and state, without recording rows for them, which
triaged card should be re-opened and with which command.

**Hard bound.** 26 tool calls; stub handoff within the first 5 calls; partial acceptable if tasks 2
and 3 are complete.

**Write paths (only these).** `docs/VERDICT-SEMANTICS.md`,
`experiments/ptr-engine/tools/verdict_semantics.py`,
`experiments/ptr-engine/longrun/tests/test_verdict_semantics.py`,
`orchestration/units/VERDICT-REFUSAL-SEMANTICS.md`,
`orchestration/handoffs/VERDICT-REFUSAL-SEMANTICS.json`,
`orchestration/journals/VERDICT-REFUSAL-SEMANTICS.log`, `/tmp/vrs/**`.

**Offline.** Zero inference requests; the two triage re-runs are local test commands only.

**Deliverable shape.** Doc table (code / name / measures-or-refuses / verdict) parsed by the test and
compared to `exit_codes.EXIT_TABLE`; `classify()`/`is_refusal()`; a red proof on a `/tmp` copy with a
fake code 14; one recorded verdict row; a handoff naming the re-open candidate.
