# LAUNCH-CONTRACT-ABSENT (card 962c8fcb-4252-480c-a53a-aeda15537192)

**Purpose.** Make `launch_contract_diff.py` report a missing field as `ABSENT <dotted.path>`
(non-zero exit, never a traceback) instead of raising `KeyError: 'components'` while building
the row table; and restore the price arithmetic in the *report* (never by editing the params).

**Bound.** 24 tool calls. **Status: done.**

**Write paths (declared).**
- `experiments/ptr-engine/tools/launch_contract_diff.py`
- `experiments/ptr-engine/tests/test_launch_contract_diff_absent.py` (new)
- `docs/CONTRACT-DIFF-ABSENCE.md` (new)
- `orchestration/units/LAUNCH-CONTRACT-ABSENT.md`, `orchestration/handoffs/LAUNCH-CONTRACT-ABSENT.json`,
  `orchestration/JOURNAL.md`

**Change.** One accessor `resolve_field(obj, keys) -> (present, value, path)`; every JSON row goes
through it. `ABSENT` is a first-class status, named with the dotted path and the file, exiting
non-zero. `DISAGREES` is evaluated before `ABSENT` so absence cannot mask a disagreement. `CA()`
lets a computed row be absent without a KeyError. `price_derivation()` prints turns × factor and
the factor's provenance beside the bare total and flags `price_unjustified`.

**Not touched (forbidden).** `measure/GRID-PARAMS.json`, `measure/HARNESS-PIN.json`, `cell.py`,
`run_longrun.py`, `run_a_star.py`, `analyze_stats.py`, `grade_v5.py`, fixtures, rows, grades.

**Evidence.** See `orchestration/handoffs/LAUNCH-CONTRACT-ABSENT.json`.
