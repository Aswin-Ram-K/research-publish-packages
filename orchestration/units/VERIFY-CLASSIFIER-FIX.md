# VERIFY-CLASSIFIER-FIX — does dropping the bare `verdict` clause keep the guard alive?

**Verdict: PASS — keep the edit. Not reverted.** Clause at `tests/test_orchestration_handoffs.py:208-210`:
```python
if name.startswith("V") or "overall" in doc:
    return "verifier"
return "unit"
```
## Proof 1 — GREEN
`.venv/bin/python -m pytest tests/test_orchestration_handoffs.py -q` → `EXIT=0`, tail `13 passed in 2.48s`.
Pre-fix baseline: `1 failed, 12 passed`, failure at `:356` `{'BILL-AUDIT.json': ['overall', 'checks']}`.
## Proof 2 — THE GUARD STILL BITES
`/tmp`-only `SYNTH-NOT-V.json` = `{"unit":"SYNTH-NOT-V","overall":"pass","blocker":"",…}` (no `checks`); the real module imported, `classify()` + `required_keys()` + `_regressions()` replayed:
```
SYNTH shape=verifier missing=['checks']
BITE FAILED-AS-REQUIRED: new_v={'SYNTH-NOT-V.json': {'shape':'verifier','missing':['checks']}}
EXIT_SIMULATED=1 msg=NEW verifier-shape gaps: {'SYNTH-NOT-V.json': {… 'missing': ['checks']}}
```
Caught by name → guard intact.
## Proof 3 — NO FROZEN ENTRY OVER-DECLARES (16/16)
Old vs new rule over `state/logs/U8.15/baseline_gaps.json` (9 unit) and `state/logs/U8.18/verifier_shape_baseline.json` (7 verifier):

| entries | old | new | movement |
|---|---|---|---|
| R2-A2, R2-A3, R2-B2, R2-C, R2-SGL-CAP, U0.22, U3.2, U6.16, U6.17 | unit | unit | none (9) |
| V-R2VLLM-TRIAGE, V2T, V4R, V5F, V6E, V6F, VLLM-CELL | verifier | verifier | none (7) |

`MOVES: []`, `TOTAL_ENTRIES=16`. The one permitted move is outside both baselines (BILL-AUDIT is not a recorded gap), verified explicitly:
```
BILL-AUDIT old: shape=verifier missing=['overall','checks'] -> FAILS
BILL-AUDIT new: shape=unit     missing=[]                   -> passes
```
## Proof 4 — WIDER SUITE
`.venv/bin/python -m pytest tests/ -q -k handoff` → `EXIT=0`, tail `14 passed, 1364 deselected in 2.88s` (not empty).
## Residual / notes
- My own stub was flagged `['overall','checks']` mid-run because its name starts with `V` — the `V` clause working as designed; the final handoff legitimately carries `overall` + `checks`.
- A future non-`V` file with only prose `verdict` and no `overall` is still judged a unit handoff and fails as a *unit* gap → fail-loud, never silent.
- Card named `state/logs/U8.15/unit_shape_baseline.json`; the pinned file is `baseline_gaps.json` — used the real path. `/tmp` is per-call ephemeral, so outputs came from in-call stdout.
- Wrote only this card, the handoff, `/tmp`. No baseline, `BILL-AUDIT.json`, or other test touched. Revert **not** applied — proofs 2 and 3 passed.
