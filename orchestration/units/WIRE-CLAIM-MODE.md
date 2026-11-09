# UNIT WIRE-CLAIM-MODE — wire the settled claim-mode module into the conductor

**Bound:** ≤24 tool calls, **0 requests**. **Precondition:** `GATE-OPERAND-VALIDATION`
settled (`status=done`, cell.py sha `6b0ca83a…8b4e` matched its recorded sha at start).

**Job.** One entry point for the claim decision (`cell.py` -> `claim_mode.resolve_claim`),
`smoke|plumbing` allowed by G3 with `claim="none"` and `comparison_eligible=false`,
absent/empty/`none`/unknown still exit 12 with the module's message verbatim, the
analyser refuses a `claim="none"` cell by name (`incomparable_claim`) instead of
filtering it, and a red→green proves the wiring is load-bearing.

**Before (deleted inline parse, cell.py):**
```python
    name = str(getattr(args, "hypothesis", None) or "").strip().upper()
    if name:
        return name, "flag:--hypothesis"
    return "NONE", "absent:--hypothesis"
```
**After (one call, memoised so the dry run and the live chain share one answer):**
```python
    mod = _claim_module()
    text = getattr(args, "hypothesis", None)
    key = "" if text is None else str(text).strip()
    if key not in _CLAIM_CACHE:
        try:
            _CLAIM_CACHE[key] = mod.resolve_claim(text)
        except mod.ClaimRefusal as exc:
            _CLAIM_CACHE[key] = exc
    return _CLAIM_CACHE[key]
```

**Write paths:** cell.py, claim_mode.py (unchanged), analyze_stats.py (the
`incomparable_claim` refusal), experiments/ptr-engine/longrun/tests/test_claim_wiring.py, experiments/ptr-engine/longrun/tests/test_claim_mode.py
(unchanged), docs/GATE-CHAIN.md, this card, the handoff, the journal.
