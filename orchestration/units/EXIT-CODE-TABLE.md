# UNIT `EXIT-CODE-TABLE`

**One purpose:** make the conductor's exit codes tell the truth in both directions — every
declared code is raisable, every raisable code is declared — from a single table, with a scan
test that fails on drift.

- **Depends on:** `HARNESS-MAP-V2` (`2f004247`, settled `done`) — the measurement that opened
  the card: raised set `{0,1,2,3,4,5,6,7,8,9,11}` vs a table that declared `7` with no raise
  site and left `1` undeclared.
- **Hard bound:** ≤26 tool calls, zero inference requests, no network, no `git`.
- **Offline:** all live paths exercised through fakes; no request sent.

## Write paths (exactly)

- `experiments/ptr-engine/longrun/cell.py`
- `experiments/ptr-engine/longrun/exit_codes.py` (new — the single table)
- `experiments/ptr-engine/longrun/tests/test_exit_codes.py` (new)
- `docs/EXIT-CODES.md` (new)
- `orchestration/units/EXIT-CODE-TABLE.md`, `orchestration/handoffs/EXIT-CODE-TABLE.json`,
  `orchestration/journals/EXIT-CODE-TABLE.jsonl`

## What was done

1. **Enumerated from source** (`sys.exit(`, `raise SystemExit(`, `Abort(`, `_enforce(..., code)`)
   across `cell.py`, `run_longrun.py`, `grade_v5.py`, `analyze_stats.py` and the other stage
   modules. Conductor codes: 0,1,2,3,4,5,6,7,8,9,10,11 — all eleven now reachable and declared.
2. **`7` kept and made real** (not deleted): `stage_record()` wraps out-dir creation, the JSON
   write and the markdown write; `main()`'s final record write wraps too. A failing record now
   aborts with `7` naming the artefact. Before this, that `OSError` escaped as an undeclared `1`.
3. **`1` declared** as `internal-error`: `main()` catches `Exception`, prints the full
   traceback, prints an identifying line (`arm/fixture/out_dir`) and returns `1` deliberately.
4. **`11` declared** in the machine-readable table (it was only in prose): `analyze_stats.py`
   exiting non-zero, action = re-run the analyser.
5. **One source of truth:** `exit_codes.EXIT_TABLE` (+ derived `EXIT_CODES`/`EXIT_NAMES`).
   `cell.py` appends `exit_codes.render_table()` to its own `__doc__` at import; the `--dry-run`
   printout lists the declared set from the table; the second runner-code dict is gone.
6. **`docs/EXIT-CODES.md`:** code, name, condition, raise site (function + line), and the action
   a reader should take next.
7. **`experiments/ptr-engine/longrun/tests/test_exit_codes.py`:** AST source scan with set equality (both directions), `7`
   reachability injections, per-row condition/action/raise-site checks, derived-view check,
   docstring/dry-run-read-the-table check, and a red→green mutant (`sys.exit(12)` in a `/tmp`
   copy).

## Evidence

- Table printed from the module: `python3 exit_codes.py` → 11 codes, each with an action.
- `python3 -m pytest experiments/ptr-engine/longrun/tests/test_exit_codes.py -q` → **10 passed, 12 subtests passed**.
- Red: `CELL_EXIT_SCAN_PATH=/tmp/red-cell.py` (copy of `cell.py` with `sys.exit(12)` appended) →
  `1 failed, 9 passed` with `RAISED BUT NEVER DECLARED: [12]`.
  Green: without the mutant → `10 passed`.
- Exit-code-asserting files re-run: `test_cell.py`, `test_cell_gates.py`,
  `test_decidability_seam.py`, `test_guards.py`, `test_exit_codes.py` → **28 passed, 3 failed**;
  the failures are the pre-existing `decidable=3`-vs-`1` text drift in
  `test_decidability_seam.py` (its own `returncode == 9` / `== 0` assertions pass) and one
  transient `test_guards.py` G1 run that hit the ledger counter mid-write while another card was
  writing `experiments/ptr-engine/measure/` (it passes standalone).
- Full `tests/` suite: **21 failed, 188 passed, 21 subtests passed**; the failures cluster in
  `test_grade_v6_derive.py` (`FileNotFoundError`), `test_parm1_errata.py`,
  `test_projection_calibration.py`, `test_grade_v5_repair.py`, `test_guards.py`
  (`test_wire_client._NoSocket` ordering leak) and the `decidable=3` drift — none of them is an
  exit-code assertion of this unit and none is caused by it (`grade_v5.py` mtime 10:38 predates
  this session; the conductor's exit assertions in them still pass).

## Conflicts

None to renumber. `WIRE-GATES` (`2/3/4/5/6/7/8`), `WIRE-CAP-GATE` (`4`) and
`DECIDABILITY-SEAM` (`9`) keep their numbers; `7` gained a record-stage raise site inside the
meaning it already had. Recorded, not hidden: argparse also exits `2`, which shares the
preflight row.
