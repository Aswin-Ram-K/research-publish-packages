# GUARD-SHAPE-AUDIT — is `orchestration/handoffs/BILL-AUDIT.json` mis-shaped, or mis-classified?

**Conclusion: (b) FALSE POSITIVE.** The file is a COMPLETE unit handoff (7/7 unit-contract keys,
`status:"done"`) that `classify()` wrongly routes to the verifier contract. The defect is in the
rule, not the handoff.

## The rule that decides shape — `tests/test_orchestration_handoffs.py:208-210`

```python
if name.startswith("V") or "verdict" in doc or "overall" in doc:
    return "verifier"
return "unit"
```

Required keys: `CONTRACT` (the 7 unit keys, `:114`) vs the verifier contract
`['unit','overall','checks','blocker','next_unit_hint','write_paths']`, loaded from the pinned
`state/logs/U8.18/verifier_shape_baseline.json` (`:122-123`, `:184-187`, `:215`); asserted at
`:349-358`. Frozen gaps live in `state/logs/U8.15/baseline_gaps.json` (unit, 9 entries, frozen by
U8.15/amended by PAPER-FINAL) and the U8.18 file (verifier, 7 entries).

## Evidence for (b)

1. `BILL-AUDIT.json` top-level keys: `unit, status, artifacts, evidence, verdict, blocker,
   next_unit_hint, write_paths, assumptions` — **all 7 unit keys present**, `status:"done"`,
   artifacts = its own audit scripts + REPORT. The unit shape is a *specification* (`:111-114`), so
   by that spec the file has **no gap**.
2. Its `verdict` is free prose ("The law does NOT survive as an accounting instrument…", line 23),
   not the verifier outcome: `type` is `str`, value ∈ `pass|fail|partial` is **False**. The verifier
   shape's outcome key is `overall` — absent — as is `checks`.
3. The discriminator's own docstring (`:194-196`) names the `V` prefix as the primary discriminator
   (43/43 V* files) and says `verdict`/`overall` exist "so a verdict-shaped handoff that is not
   named V* is still read as a verdict".
4. Census, top-level keys over **823** parseable handoffs (`grep -l '"verdict"'` is misleading: 109
   match, but 818 of those carry it only nested inside `evidence`):
   - top-level `verdict`: **5** files — `BILL-AUDIT`, `U10`, `U-CACHE-INSTRUMENT`, `UVER9`, `V4R`;
   - **4 of 5** also carry `overall` + `checks`, so the `overall` clause already routes them;
     the 5th (`V4R`) is V-prefixed and frozen (`["overall"]`).
   - Files routed to the verifier **because of `verdict` alone: exactly 1 — BILL-AUDIT**, and it is
     unit-complete. The clause catches **zero** genuine verdict shapes.
5. Simulation of dropping `"verdict"` from `:208` (no file edited): new/worse gaps = `{}` unit,
   `{}` verifier → 13/13; all 16 frozen entries stay reachable, none over-declares. Only
   BILL-AUDIT's classification changes.
6. `orchestration/units/BILL-AUDIT.md:1-21` confirms the author role: status done, its own method,
   own write paths ("This unit exists to **falsify** the law"), not a re-check of another handoff.

## Why this must NOT be recorded as a gap

Adding `"BILL-AUDIT.json": ["overall","checks"]` to `state/logs/U8.18/verifier_shape_baseline.json`
would turn the suite green but institutionalise a false accusation against a file that satisfies the
unit contract — and it also requires editing the sha256 pin at `:123`. AGENTS.md's
"recorded gap / invent no values" rule covers units that genuinely chose the other shape
(VLLM-CELL, V-R2VLLM-TRIAGE), not a classifier clause that misroutes a complete unit report.

## ONE recommended action (operator decision)

**Fix the classifier at `tests/test_orchestration_handoffs.py:208`**: replace
`if name.startswith("V") or "verdict" in doc or "overall" in doc:` with
`if name.startswith("V") or "overall" in doc:` — because the measurement shows the bare `verdict`
clause identifies no genuine verdict shape (every non-V* verdict carrier also carries `overall`)
and produces the suite's only live failure on a complete unit handoff. Do **not** add a baseline
entry; do **not** rewrite `BILL-AUDIT.json` (that would invent `overall`/`checks` nobody wrote).

Residual, stated not hidden: a future non-V file carrying only a prose `verdict` and no `overall`
will then be judged as a unit handoff and fail as a *unit* gap — still fail-loud (`:197-203`), and
the RED fixtures `V9.98` (V-prefixed) and `U0.22` (no verdict key) are untouched.

## Evidence lines

`.venv/bin/python -m pytest tests/test_orchestration_handoffs.py -q` → `1 failed, 12 passed in
2.51s`; failure at `:356`: `{'BILL-AUDIT.json': ['overall', 'checks']}`. Note the guard needs
`.venv/bin/python`: plain `python3 -m pytest` dies at conftest import
(`ModuleNotFoundError: No module named 'resextract'`).
