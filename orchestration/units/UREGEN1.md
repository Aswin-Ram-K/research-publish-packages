# UREGEN1 — regeneration measurement (what the substitution actually does)

**Purpose:** produce the numbers a release ruling needs — nothing is released, nothing in the live
trees is modified. **Bound:** 45 tool calls. **Status:** done.

**Write paths:** `scratch/uregen1/**`, `strategy/REGEN_ASSESSMENT.md`, `orchestration/units/UREGEN1.md`,
`orchestration/handoffs/UREGEN1.json`. Live trees read-only throughout (grep/read only).

## Result in one line

`redact.py` runs clean first try (EXIT=0) but applying it leaves the **58-file ship set at 62 hard-fail
lines** (UCURATE1 measured 152 before), moves the scoring-projection digest from `57a29b4e…` to
`b85e4585…`, and changes **no** claim number (`numbers_changed = 0`).

## Measurements

| item | before (shipped) | after (regenerated) |
|---|---|---|
| ship-set hard-fail lines | 152 | **62** |
| whole-tree hard-fail lines | 494 | 360 |
| scoring-projection digest | `57a29b4e…` | `b85e4585d8c7f0beec02620356b8fcb2b53bb27b0c9e5544bf51e8368bec7a26` |
| MANIFEST.json identity contradictions | 6 | 0 |
| routeA.ties | 120 | 120 |
| claim numbers | 9/9 OK | 9/9 OK |

## What is irreducible

The 62 residual lines are option-label strings (`"none -- admit() mints the state"`,
`"the expanded[] ref list"`) and their echoes in the shipped eval results, plus pointers to
`REDACTION_REPORT.md` / `EXCLUDED.md` that the substitution never keyed on. Option labels are
deliberately outside stage C (`redact.py:204-206`). Substituting them is what moved
`routeA.ties` 120 -> 119 in REPORT2's earlier experiment, so 62 is a floor unless labels may move.

## Findings that correct prior units

1. UREDACT3's "98 on the regenerated tree" reproduces **only** as regenerated-tree-minus-9-process-files
   (it is not a whole-tree number). Its "394 present bytes" did not reproduce (whole live tree = 494).
2. UREDACT3's stage-D defect is **contradicted**: stage D writes the *output* digest to `sha256`,
   keeps the source digest in `source_sha256`, and sets `identical_to_source = (source == output)`.
   Zero contradictions in the regenerated MANIFEST; the 6 contradictions are in the **shipped** one.

**Blocker:** none. **Next hint:** see `strategy/REGEN_ASSESSMENT.md` section 7 (release steps).
