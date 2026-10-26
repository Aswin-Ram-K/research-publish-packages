# QUALITY-POSITIVE-CONTROL

**Purpose.** Decide, for zero inference requests, whether the long-run quality path can return
`verified_success: true` on a real-shaped log, or whether the 0/3 record on every live arm is an
instrument artefact.

**Hard bound.** Max 20 tool calls; no network, no `curl`, no endpoint. `/tmp` only for synthetic logs;
`measure/rows-longrun-c-2026-10-26.jsonl` read-only.

**Write paths.** `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`,
`orchestration/handoffs/QUALITY-POSITIVE-CONTROL.json`, `orchestration/units/QUALITY-POSITIVE-CONTROL.md`,
`/tmp/qpc/**`. Never edit `score_longrun.py`, `grade_v2.py`, `run_longrun.py`, any fixture, plan, or row file.

**Method.** Read `score_longrun.py`, `grade_v2.py`, and `tasks-v3/runtime-v3/LR-01.v3.json`; build
`/tmp/qpc/{pos-full,neg-one,neg-marker,neg-truncated}.jsonl` from the 48 real `pointer-stable` rows
(copy-only, `fixture_sha256` set to the v3 fixture digest), plus `pos-exact-only.jsonl` as a diagnostic;
run both graders on each; record the truth table.

**Kill condition.** If no log satisfying every required check can be constructed from the fixture's own
`expected` values, report `PATH-UNSPECIFIED` with the unsatisfiable fixture key. (Not reached: the values
are satisfiable in prose; the *match mode* is what cannot be satisfied.)

**Deliverable.** Verdict + four-log truth table + both graders' exit codes and output lines. Result:
`PATH-CANNOT-SAY-YES` — `cp.t12` (kind `fact`, turn 12, expected `"64"`) fails on the prose+`ANSWER: 64`
log because `score_longrun.py:814` defaults checkpoints to `exact` and `:174-176` compares whole content.
