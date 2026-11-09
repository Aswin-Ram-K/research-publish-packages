# GATE-CHAIN-FIX — repair the four defects V-GATE-CHAIN found

**Bound:** 30 tool calls. **Status:** done.

## Objective
1. D1 — a non-positive `--max-wall` must refuse (exit 8), not switch G2 off.
2. D2 — an absent `--hypothesis` must be `none` and refused by G3; never default to H2.
3. D3 — G3 gets its own exit code `12`, in `EXIT_TABLE` and the scan test.
4. D4 — the stated test command must be green from the repo root.

## What changed
- `cell.py`: `ok = (max_wall > 0 and projected <= max_wall)` plus an explicit non-positive
  refusal naming `--max-wall=<v>` and stating there is no unlimited mode; `_declared_hypothesis`
  returns `NONE`/`absent:--hypothesis` when the flag is absent; `_enforce(eval_gate_prereg(...),
  "3c/7 G3 prereg gate", 12)`; help text for `--hypothesis`/`--max-wall` states both rules.
- `exit_codes.py`: `EXIT_PREREG = 12` + table entry ("prereg"); `EXIT_PREFLIGHT` no longer
  claims a G3 refusal.
- `experiments/ptr-engine/longrun/tests/test_cell_gates.py`: max-wall 0/-1, silence, explicit none, unknown, H1 n=144, repo-root
  import; `RED_GREEN` now supports multi-step mutants and covers every repaired defect.
- `experiments/ptr-engine/longrun/tests/test_exit_codes.py`: the injected-extra-code red uses 13 (12 is now declared).
- `docs/GATE-CHAIN.md`, `docs/EXIT-CODES.md`: 12 documented, G2 non-positive ceiling documented,
  G3 no-default documented.
- Seam (other cards' files, disclosed): `experiments/ptr-engine/longrun/tests/test_guards.py`, `experiments/ptr-engine/longrun/tests/test_projection_calibration.py`,
  `experiments/ptr-engine/longrun/tests/test_projection_modes.py` — all three drove live paths without `--hypothesis`; each now
  declares `H2` (n>=1, honest for their n=10..60 cells). `test_guards.py`'s `--max-wall 0`
  "disabled" red became a source mutation because a non-positive ceiling is now a refusal.

## Evidence
- `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cell_gates.py'`
  from the repo root: `Ran 15 tests … OK`.
- Four red→green runs recorded in the handoff (a,b,c,d); cell.py restored byte-identically
  (sha256 60cdf98b… before and after).
