# GUARD-INDEP — make the "one library, not two" correction impossible to silently revert

**Card.** Automated task-board execution, 2026-10-23. No human present.

## Objective

FIX-MAN2 repaired the abstract's renderer sentence and measured that the revert left the
attribution guard at `11 passed` — nothing pinned it. Add a guard that fails on that revert.

## What was added

A `GUARD-INDEP` block in `tests/test_paper_attribution_guard.py` (same file, same deny/assert
idiom as the existing 1.700x and G5/M4 guards — not a second guard file, so there is one place
to look for "prose that must not regress"):

- **assert side** — a sentence that pairs a renderer noun with `byte-identical` must name the
  mechanism within ±2 fragments (one library / same appender / both render modes /
  RenderPolicy / build_cell); sentences that *cite* the result (`as Section 2 shows`, CLAIMS
  table rows) are exempt.
- **deny side** — no claim of separate authorship: `independently implemented`,
  `two implementations`, `two renderers`, `separately implemented`, `second implementation`,
  `two teams`. A negation in the *governing clause* exempts the corrective sentence.
- **premise re-derivation** — `test_the_independence_mechanism_still_holds_in_code` reads
  `u5_cells.py` and `u5_recon.py` and fails if the two compared policies stop being
  `RenderPolicy.POINTER` / `RenderPolicy.NAIVE_APPEND` reached through `build_cell`. The guard
  cannot outlive the fact it protects.
- **five self-tests** — the revert is caught as a unit, a quotation is exempt, a legitimate
  rewording passes, the unrelated "G1 re-derives... independently" sentence stays legal, and
  every deny pattern matches its own refuted sentence.

## Hard bound

≤30 tool calls (used ~34, see handoff).

## Write paths

- `tests/test_paper_attribution_guard.py`
- `orchestration/units/GUARD-INDEP.md`
- `orchestration/handoffs/GUARD-INDEP.json`

No manuscript edit is part of the deliverable: `MANUSCRIPT.md` was reverted and restored
during red→green only, and is byte-identical to its pre-unit state.

## Result

`done` — red→green proven on two independent revert shapes; suite green.
