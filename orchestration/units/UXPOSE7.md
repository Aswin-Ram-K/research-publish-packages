# Unit UXPOSE7 — Exposure column resolution

**Question:** Which flag set does the gated-read paper's own stated definition of exposure require?
Column: corrected threat union across six arms = 20/20/19/0/19/20; headline 0/20 routed.
URELEASE7: column reproduces only from context-carry flags; file-exposure flags give 19 for routed. §2c mis-attributes formula.

**Write paths:** strategy/EXPOSURE_COLUMN_RESOLUTION.md, orchestration/units/UXPOSE7.md,
orchestration/handoffs/UXPOSE7.json, scratch/uxpose7/**
**Bound:** 20 tool calls. Stub report first, append as measured.
**Raw record:** on withhold list — read only, never copy/quote withheld literals.

## Status log
- [t1] card persisted
- [t17] DONE. Verdict: definition requires ctx_has_a/ctx_has_b (context survival) -> column 20/20/19/0/19/20 and 0/20 headline HOLD. expo_a/expo_b = read-level, gives stage_route 19 (URELEASE7 confirmed). REVERIFY:103 field attribution wrong. F1 0.210 is a truncation of 0.210526 -> 0.211. Report: strategy/EXPOSURE_COLUMN_RESOLUTION.md
