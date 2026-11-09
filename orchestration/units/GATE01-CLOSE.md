# GATE01-CLOSE — close gate 0.1 offline

## Outcome
Gate 0.1 closable offline against its plan-of-record definition. Five discriminating
outcomes produced by `experiments/ptr-engine/longrun/tests/test_gate01_control.py`
(zero model requests, zero service changes).

## Five-row table
| control | observed result | discriminating evidence |
|---|---|---|
| known-good | verified_success=True | failed_required=[] ; exit 0 ; checkpoint_accuracy 3/3 |
| wrong-value | verified_success=False | cp.t12 in failed_required ; parsed "65" != "64" ; exit 1 ; tampered=False |
| missing-fact | verified_success=False | cp.t46 in failed_required (missing serialized_ref) ; exit 1 |
| same-log-twice | identical full scorecard | deep-equal JSON across two runs ; exit codes equal |
| tampered | tampered=True | fixture.digest in failed_required ; exit 2 ; distinguished from wrong-value (exit 1) |

## Additional controls (pre-existing, unchanged)
- truncated working set: verified_success=False, failed_required=[acc.2, acc.3, acc.4]
- verify turn missing "exit 0": verified_success=False, failed_required=[acc.2]

## acc.2–acc.4 conflict
Documented in `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`. A live
read-only agent cannot satisfy acc.2–acc.4 because `run_longrun.py:811-812` parses
`read_file` only and `:977-984` performs one bounded read; evidenced by
`measure/rows-posctrl-2026-11-08.jsonl` (48 turns, zero `exit 0`/`def test_`/
`PtrNotAReferenceError`/`PTR_NOT_A_REFERENCE`). acc.2–acc.4 unchanged.

## Verification
`/home/zer0null/research extractor/.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_gate01_control.py -q`
=> 7 passed in 0.03s.
Full longrun suite has one pre-existing collection error in
`test_verdict_semantics.py` (exit-code 14 unclassified) unrelated to this change.
