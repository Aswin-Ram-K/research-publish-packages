# C66-C68-GUARD

**Purpose.** Bring C66, C67 and C68 under the value-cell contract in
`tests/test_claims_value_guard.py` — the residue named by `C63-CELL`'s `next_unit_hint` and by
`FIX-CLAIMSTABLE`'s `residual[2]`.

**Bound.** 30 tool calls / 12 bash. **Write paths.** `tests/test_claims_value_guard.py`,
`orchestration/handoffs/C66-C68-GUARD.json`, `orchestration/units/C66-C68-GUARD.md`.
`CLAIMS.md` only if a genuine cell error was found (none was; sha unchanged).

## What was already true (not re-derived)

All three rows carry full Value cells and a `recompute_r2.py` command; `recompute_r2.py all`
already PASSes C66 75/75, C67 85/85, C68 70/70. The gap was only admission to `CONTRACT`.

## What this unit did

1. Admitted `C66 (recompute_r2, "C66")`, `C67 (recompute_r2, "C67")`, `C68 (recompute_r2, "C68")`
   to `CONTRACT`, with the module docstring naming what each guards.
2. Established what C66 actually pins: 75 numeric keys — 15 arm means (1 dp), 15 arm-n/pairs (71),
   9 gcd/off-grid, 3 row counts, 9 paired deltas, 9 CI tuples, 9 excludes-zero flags,
   3 file tuples. Its `EXPECTED` block is a plain flat dict; the earlier "naive scan yielded no
   keys" was a scan artefact, not a structural difference.
3. Measured the misalignment first (legibility with the existing `_legible`): C66 33/75,
   C67 40/85, C68 14/70 keys could not be matched. Every one was a rendering decision (2 dp in the
   cell vs 3 dp in the pin, the 71 paired-turn denominator, a bare-point null), not a wrong
   number: `recompute_r2.py C66/C67/C68` still reproduce every pin exactly.
4. Added `NOT_IN_CELL` entries for every key the cell genuinely cannot carry, each with the
   reason (see the handoff's `waived_by_design`), following C63's 1,088 launch-reading precedent.
5. Added three claim-specific legs mirroring C63's:
   `test_c66_paired_reading_is_directional`, `test_c67_intervals_and_c67a`,
   `test_c68_pairs_are_counted_once`.
6. Added `test_the_guard_bites_when_the_recomputation_moves`: a clone-based probe that sabotages
   one cell's rows and requires the same cell comparator to stop accepting the recomputation.

## Result

| claim | guarded | waived | red→green bite |
|---|---|---|---|
| C66 | 56 | 19 | **yes** (`test_pinned_values_are_legible_in_their_value_cell`, exit 1: `C66:T64_minus_T256_A=-4.507 ... does not appear in C66's Value cell`) |
| C67 | 53 | 32 | **no** — planted `[8.39, 53.48] → [8.39, 58.48]`, exit 0 |
| C68 | 40 | 30 | **no** — planted `277 (O1 vs O3) → 271`, exit 0 |

`CLAIMS.md` sha256 unchanged throughout:
`3fbf199f85b103d2e954eee225084da04c81776f1c1692ad726544798d68178e`.

## Acceptance

- `verify_package.py` — PASS, exit 0
- `recompute.py all` — COVERAGE GUARD PASS 69 claims, exit 0
- `recompute_r2.py all` — 7 PASS lines, exit 0
- `pytest tests/test_claims_value_guard.py` — 7 passed, exit 0 (standalone)
- `pytest tests/` — 4 failed, 1371 passed, 1 skipped, exit 1; three predate this unit (all cite
  `MANUSCRIPT.md` lines 1100-1112, outside this unit's write paths), the fourth is this unit's
  probe under context pollution.

## Status: partial

The admission is complete and green; the red→green proof is not established for C67 and C68,
so this unit does not claim `done`.
