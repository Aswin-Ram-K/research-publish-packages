# PREFLIGHT-SPAWN-DECLARE

**Purpose.** Replace the unsatisfiable PASS rule "`popen_calls == 0` on every refusal"
(V-GATE-REPIN `not_reproduced`) with a rule that keeps the strictness where it belongs,
by classifying every spawn instead of counting them all together.

**Finding.** A refusing `cell.py` makes exactly one Popen call: stage 3/7's
`run_longrun.py --dry-run` self-check, which prices the cell BEFORE any gate is evaluated.
No implementation could satisfy "zero spawns" while keeping the self-check, so the rule
was replaced, not weakened.

**Decision — stayed a classified spawn.** The self-check invokes the runner's own
`--dry-run` path (argv parsing, fixture validation, Planner previews under
`/tmp/longrun-previews/`). Doing it in-process would import that path into the gate
process and change the measured quantity; it is therefore kept and declared
`purpose=preflight_self_check, phase=3/7 budget`.

**Changes.**
- `experiments/ptr-engine/longrun/spawn_record.py` (new): `SpawnRecord` ledger,
  `PURPOSES`, `PHASES`, `as_dict()`, `validate_refusal()`.
- `experiments/ptr-engine/longrun/cell.py`: `_run` classifies its spawn; `stage_run`
  records the one `runner_launch` with the gate manifest; the completed record carries
  `spawns`; a refusal writes `cell-<arm>-<stamp>.refusal.json` with `spawns`, `counts`
  and `validation`, and prints the counts.
- `docs/GATE-CHAIN.md` §11: the one-sentence rule and the reasoning.
- `experiments/ptr-engine/longrun/tests/test_spawn_classification.py`: three tests against
  an independent `subprocess.Popen` oracle.
- `experiments/ptr-engine/measure/PREFLIGHT-SPAWN-DECLARE.json`: measured table.

**Rule.** A refusing invocation must have zero `runner_launch` spawns; any
`preflight_self_check` spawn must be declared in the same record with its phase; an
undeclared spawn (`purpose == other`, or a launch with no gate record) is a failure.

**Measured (exit → runner_launch → declared preflight → oracle Popen):**
2 → 0 → 0 → 0 · 3 → 0 → 1 → 1 · 4 → 0 → 1 → 1 · 8 → 0 → 1 → 1 · 12 → 0 → 1 → 1.
Tests: 3/3 new; neighbours `test_cell_gates` + `test_gate_override` + `test_exit_codes`
40 passed. `cell.py` sha256 before `24627d7b…33253`, after `5a812a98…02cb9`.
