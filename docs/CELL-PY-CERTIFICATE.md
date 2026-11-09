# Cell.py behaviour certificate

**Certified bytes** `experiments/ptr-engine/longrun/cell.py` = `c29a9fb36e9e8f0e166583d56db00b2184fbc12a97b77b1a72ca9f612c1a9c59`
**Harness pin** `1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285`
**Certificate** `experiments/ptr-engine/measure/CELL-PY-CERTIFICATE.json` · 2026-10-26T19:10:00Z · unit `CELL-PY-BEHAVIOUR-CERTIFY`

## What this certifies — and what it does not

It certifies **behaviour**: the refusals, exit codes, spawn records and dry-run contract below were
observed by running the file. It does **not** certify provenance: `cell.py` is untracked by git, no
baseline copy of the previous bytes (`e24e867b`) exists, and the file was written at 18:54:16Z by no
settled card. How those bytes got there remains unproven and is not recoverable.

## Claim table

| Claim | Status | Evidence (one line) |
|---|---|---|
| `GATES-MESSAGE-CONSISTENCY` | holds | allow/refuse families built from the same numbers and selected by `elif verdict["ok"]` (cell.py:732-788); observed `G2 allow computed=2880 s limit=3600 s` and `G2 REFUSED: computed --max-wall=0 s`; codes unchanged. |
| `GATE-OPERAND-VALIDATION` | holds | `--max-wall 0` → RC 8 end-to-end, `runner_launch=0`; 150+ row hostile-operand matrix passes with zero spawns. The six-bypass *end-to-end* case alone errors inside the test double (`tools/gate_attack.py:544` lacks `purpose=`, cell.py:363) — `not_testable` from that harness. |
| `GATE-CHAIN-FIX` | holds | absent `--hypothesis` → RC 12 `computed hypothesis=none declared`; explicit `none` → 12; `H2` admitted (`claim=H2 comparison_eligible=True`); 12 in `EXIT_TABLE`; both-ways scan green. |
| `PREFLIGHT-SPAWN-DECLARE` + `SPAWN-RECORD-BIND` + `SPAWN-TREE-BIND` | holds | exits 2/8/12 observed with `runner_launch=0 preflight_self_check=1 declared=1 undeclared=0 record=ok`; refusal record carries `cell_sha256=c29a9fb3`, `spawn_record_sha256`, `argv`, `tree_sha=f17663d1`. |
| `HARNESS-REPIN` P2 | holds | `--dry-run` → RC 0 and `1 of 3 gate(s) would refuse`; the branch returns at cell.py:1956-2009, before `stage_run` (cell.py:2057); "0 requests sent". |
| `WIRE-GATES` | holds | table codes `[0..13]`, `EXTERNAL_CODES={13}`, `RUNNER_CODES={2,3,4,5,6,7}`. **Correction:** exit 7 *is* raised by cell.py at 1757, 1766, 1815, 2119 — the "declared but unraised" premise is stale. |
| `EXIT-CODE-TABLE` | holds | exit 1 declared as internal-error and observed live (`cell: EXIT 1 -- internal error`, traceback cell.py:2012 → 363); both-directions scan green. |
| `CELL-ONE-COMMAND` | holds | stages 1/7 → 7/7 in order; manifest at cell.py:2049 precedes `stage_run` at cell.py:2057. `--request-allocation` is a *runner* flag (run_longrun.py:468) not surfaced by cell.py — that element is outside this certificate. |

## Suites (counts, not rates)

| Run | Passed | Failed |
|---|---|---|
| 7 named suites, repo root | 123 | 0 |
| 7 named suites, `experiments/ptr-engine/longrun` | 123 | 0 |
| `test_gate_messages` + `test_exit_codes` | 25 | 0 |
| `test_gate_operand_validation` + `test_gate_messages` + `test_gate_ledger` + `test_cap_gate` | 38 | 1 |

The single failure is the stale test double named above; it is **not** inside `cell.py`'s behaviour and
was not fixed (a new card owns it). `test_verdict_ritual` and the two repo-root reds were not run and
did not appear.

## Verdict

The grid **may** launch against `c29a9fb3` on behaviour: every refusal, code and spawn declaration above
was observed. What remains unproven is only how those 2,213 lines got onto disk — no diff, no author, no
baseline — so any future change to this file must snapshot a baseline first.
