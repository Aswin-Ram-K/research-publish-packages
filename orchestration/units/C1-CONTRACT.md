# C1-CONTRACT

**Purpose.** Make gate 0.1's control gradeable: a correct transcript scores
`verified_success=True`, a wrong one does not.

**Changes.**
- `score_longrun.answer_of` now parses the v5 answer contract: `ANSWER: NUM 64`
  -> `"64"`, `ANSWER: CALL ...` -> canonical sorted call string. Exact comparison
  applies to the parsed value, not the raw line.
- `tasks-v4/LR-01.v4.json` (and runtime mirror): cp1/cp2 `expected` are bare
  values (`"64"`, `"31"`); cp3 `expected` is the canonical call form naming the
  three facts (`code`, `scope`, `serialized_ref`).
- Ordering claim ("before re-raising") is NOT folded into the string. The run log
  records no refusal/raise event sequence, so it is recorded as an `ungraded_claim`
  with reason. Route chosen: explicit ungraded claim, because faking order into
  text would make the check vacuous and there is no event data to grade from.
- Negative controls retained: truncated working set ->
  `verified_success=False, failed_required=[acc.2,acc.3,acc.4]`; verify turn
  omitting `exit 0` -> `False, [acc.2]`.

**Evidence.** `test_gate01_control.py`: 5 passed (pytest). Synthetic scorer control
on synthetic input, not measured evidence.

**Write paths.** as listed in handoff.
