# U-SPCC-8 — make `longrun/tests/` green: diagnosis first, then repair

## 1. `test_verdict_semantics.py` — exit-code partition drift on 14

**Diagnosis (code read first).** The message comes from `tools/verdict_semantics.py:87`
`check_partition()`, called at import (`:128`), not from the test. The table DOES carry 14:

- `longrun/exit_codes.py:42` `EXIT_CAPGATE_UNRECORDED = 14`
- `longrun/exit_codes.py:61` `RUNNER_MAPPED_TO_CELL = {9: EXIT_CAPGATE_UNRECORDED}`
- producer: `longrun/cell.py:1750` `return Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, "4/7 run", ...)`
  reached by `stage_run()` when the runner's exit reconciliation refuses (runner rc 9 = `EXIT_CAP_DIVERGENCE`,
  "CAP GATE UNRECORDED"/"RECONCILE DIVERGENCE"); `cell.py:1858` reads the same code.
- `exit_codes.py:229-238`: name `capgate-unrecorded`, meaning "the cap gate refused because requests
  reached the wire whose rows were not written, so the ledger understates the spend".

So 14 is a **refusal**: the spend accounting is untrustworthy; no evidence about the artefact exists.
`verdict_semantics.REFUSING` was simply never taught the code (the CAPGATE-CELL-LABEL fix landed the
table entry and `docs/EXIT-CODES.md`/`docs/GATE-CHAIN.md`, not the partition). **Verdict: stale
partition, not a code returning 14 wrongly.** Fix at the partition layer, not in the test.

Edits: `tools/verdict_semantics.py` `REFUSING = frozenset({2,3,4,7,8,12,13,14})` + docstring;
`docs/VERDICT-SEMANTICS.md` row 14 + prose; test's "unknown code" probe moved from 14 to 99 (99 is in
no table) and a positive assertion added: `classify(14) == UNSTAMPED_REFUSAL`.
Red->green (fix reverted by hand): collection `RuntimeError: exit-code partition drift: unclassified
in exit_codes.EXIT_TABLE=[14]` -> `9 passed`.

Note: `tools/verdict_semantics.py` is not in the card's three-file list but is the module that owns the
partition the test guards; `exit_codes.py`/`cell.py` were read and are correct, so no edit there.

## 2. `test_arm_cd_wiring` D cases — `run_cell` exit 4

**Diagnosis.** `run_longrun.py:743` `cap = getattr(cfg, "budget_cap", None)` → `ledger.DEFAULT_CAP`
(4320); `RequestCapGate.__init__` scans `DEFAULT_CAP_PATTERN`
(`run_longrun.py:549`, `measure/rows-*.jsonl`, 92 files) → `spent_at_start=7869`; `acquire()`
(`run_longrun.py:625-647`) refuses before any send:
`CAP REFUSED at T1 (turn) — over the global cap: spent=7869 ... cap=4320 ... over_by=3550 — nothing sent`.
The refusal is correct and the gate is correct; the test asserted wiring while depending on the
machine's global ledger. Fix in the test: `budget_cap=64`, `budget_glob=<tmp>/rows-*.jsonl`.
Arm reached afterwards (pasted from a live probe of the fixed helper):
`{"arm": "bounded-context-fetch", "rep": 1, "run_id": "offline-armcd-bounded-context-fetch-r1",
"turn": 1, "kind": "turn", "fetch_rows": 1, "retrieval_outcomes": ["NOT_FOUND"]}` — plus new
assertions `{r["arm"]} == {arm_cd.ARM_D}` and `fetched["retrieval_outcomes"]`. 3 failed -> 6 passed.

## 3. `test_arm_treatments` (3) + `test_treatments_fire` (2) — repeat identity

**Diagnosis.** `run_longrun.py:2475-2493` `assert_repeat_identity` requires `str(rep) in run_id`.
Production always builds an id that carries the repeat: `run_longrun.py:4014`
`rid = f"{run_base}-{arm}-r{rep}"` (dry run `:3972` `f"dryrun-{task_id}-{arm}-r{rep}"`). The two tests
(and `tools/arm_treatments_probe.py:202`) hand-wrote `arm-treatments-forced` /
`fixture-treatments-forced` with `rep=1` — an id production can never produce, i.e. the **builder
dropped the rep field**, not the guard being strict. Guard kept untouched (it exists because a cell
once ran twice under one stamp). Added `arm_treatments_probe.run_id_for(rep, tag)` (documented against
`run_longrun.py:4014`) and used it at both sites. 5 failed -> 16 passed.

## 4. Same defect classes elsewhere in the directory (found while proving the above)

The three named areas were not the only carriers of those two classes; the directory had 86 failures.
Fixed at the same layers, no assertion weakened:
- repeat-identity: `test_cap_gate` (`capgate-run-r1`), `test_claim_rows` (`rid-claimrows-r1`,
  `rid-red-r1`), `test_record_stop_reason` (`run-stop-reason-r1`), `test_row_provenance`
  (`run-provenance-r1`), `test_stop_reason_producers` (`run-stop-holes-r1`),
  `test_request_identity` (`run-r1`).
- TEMPZERO: `run_longrun.py:3895-3898` deliberately refuses `cfg.temperature is None`
  ("--temperature must be stated explicitly ... refusing run", exit 2). Tests asserting other
  contracts now state `--temperature 0`: `test_dry_turn_scope`, `test_cap_gate`, `test_claim_rows`,
  `test_runaway_policy`, `test_stop_reason_producers`, `test_guards`, `test_wall_key`.
- cap gate: `test_row_attribution` (both helpers) declares `budget_cap`/`budget_glob`; the CLI
  builders in `test_runaway_policy`/`test_stop_reason_producers`/`test_guards` pass
  `--budget-cap 1000 --budget-glob <tmp>/*.jsonl`.
Effect: `86 failed, 723 passed` -> `23 failed, 786 passed`.

## 5. Remaining 23 — not repairable by editing tests, left red

(a) Live-corpus / orchestration-state guards that are correctly red about facts on this box, which a
test edit could only satisfy by fabricating a measurement: `test_request_ledger::test_g` (spent 7869 >
cap 4320, a true over-budget fact), `test_lost_fixture` (`rows-abs2-2026-11-09.jsonl:1` pins a
fixture_sha256 with no file), `test_verbosity` (3: report lists rows files absent from the corpus),
`test_stop_reason::OnDiskArtefact` (STOP-REASON.json stale), `test_regrade_stamp` (2: sha/era drift),
`test_verdict_ritual` (6 done handoffs with no verdict row), `test_journal_lint`,
`test_handoff_lint` (2: lint emits `W_NO_COMMAND`, test/docs say `W_NO_COMMANDS` — tool/doc drift),
`test_matrix_audit`, `test_false_pass` (E_STATUS_WORD_CONTRADICTION x19), `test_build_fixture` (v4
spec), `test_withdrawn_screen` (2: `docs/RUNAWAY-POLICY.md`, another unit's new file, trips WI-014).
(b) Cross-test interference, full-directory only: `test_guards::test_guards_all` (`_NoSocket: a socket
was opened`) and `test_projection_calibration` (5). Each **passes in isolation** (verified: 17 passed
across `test_runaway_policy`+`test_stop_reason_producers`+`test_row_attribution`+`test_guards`;
`test_projection_calibration::test_thinking_off_keeps_60s_per_turn` 1 passed alone). Global
`socket.socket` monkeypatching left in place by tests outside this card's file set reddens later
blocks; fixing it means owning `test_wire_client`/`test_client_ttft`/`test_cell_gates` isolation.

## Acceptance runs

- `test_verdict_semantics.py -q` -> `9 passed`
- `test_arm_cd_wiring.py -q` -> `6 passed`
- `test_arm_treatments.py + test_treatments_fire.py -q` -> `16 passed`
- full directory: `23 failed, 786 passed, 1 warning, 31 subtests passed in 383.68s` (was
  `86 failed, 723 passed, 31 subtests passed in 361.00s`)
