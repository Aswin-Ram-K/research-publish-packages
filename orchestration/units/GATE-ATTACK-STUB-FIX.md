# GATE-ATTACK-STUB-FIX

## Defect
`tests/test_gate_operand_validation.py::OperandMatrix::test_the_six_named_bypasses_now_refuse_with_zero_live_spawns`
failed:
`AssertionError: 8 != 1 : F1: expected exit 8, got 1 ()` (test line 129). Root cause: the double
`counted()` at `experiments/ptr-engine/tools/gate_attack.py:544` had signature
`counted(argv, capture=True, label="")` while the real `cell._run` at
`experiments/ptr-engine/longrun/cell.py:200` is
`_run(argv, capture=True, label="", purpose="other", phase="")`, and `cell.py:363` calls it with
`purpose="preflight_self_check", phase="3/7 budget", label="budget-dry-run"`.

## Fix (test/tooling only; no harness edit)
`gate_attack.py:552` now `counted(argv, capture=True, label="", purpose="other", phase="")`.
Arguments enumerated from all four `_run` call sites: `cell.py:363` (purpose/phase/label),
`:1629` (grade_v5), `:1655` (analyse). `purpose` and `phase` are DELIBERATELY IGNORED and the
comment says so: this double counts dry vs live spawns only; it does not reproduce SPAWNS
classification.

## Evidence
- Six bypasses execute end-to-end: F1 B2_max_wall_1e308_allows exit 8, F2 G_tiny_override_allows
  exit 8, F3 H_artefact_zero_allows exit 8, F4 D_turns0_H3_runs_full exit 4, F5 D2_turns_neg_runs_full
  exit 4, F8 I2b_cap_zero_passed_to_runner exit 8; live_spawns=0, dry_run_probes=1 each; refusal
  lines quoted e.g. "G2 projection REFUSED: computed --max-wall=1e+308".
- Red: F1 neutered to `--max-wall 3600` -> `AssertionError: 8 != 1 : F1`, 1 failed / 8 passed.
- Green after restore to `1e308`: 9 passed.
- Neighbours: test_gate_messages + test_gate_ledger + test_cap_gate + test_cell_gates -> 45 passed,
  7 subtests passed. Combined with operand suite -> 39 passed.

## Answer
No: before this fix the six named bypasses were NOT exercised at all -- `counted()` raised TypeError
on `purpose=`, so F1 died at rc 1 with an empty refusal and the other five never reached their
expectation; the suite's green therefore meant only "the double never ran", not "the gates refuse".
