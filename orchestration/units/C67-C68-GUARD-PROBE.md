# C67-C68-GUARD-PROBE

**Purpose.** `C66-C68-GUARD` admitted C67 and C68 to the value-cell contract and then measured
that the admission was cosmetic: a planted wrong number did not turn either guard red (both
exited 0). Make the two guards actually bite, without touching `CLAIMS.md`, the pins, or any
tolerance. Supersedes the C67/C68 halves of `C66-C68-GUARD`; C66 is out of scope and untouched.

**Bound.** 30 tool calls, bash <= 12 (overrun recorded: 17 bash calls — four were spent
disambiguating a duplicated literal, see "Trap" below). Writes only to
`tests/test_claims_value_guard.py`, `orchestration/handoffs/C67-C68-GUARD-PROBE.json`, this card.

## What was wrong (measured, not taken from the handoff)

1. **C67 — a waiver that named a leg that did not exist.** The generic
   `test_pinned_values_are_legible_in_their_value_cell` compares every pinned scalar against a
   BAG of all numbers in the cell, and it skips every key named in `NOT_IN_CELL`. The four
   interval keys were waived with the reason "*test_c67_intervals_and_c67a is the guarding
   leg*" — and no such test existed in the file (nor did
   `test_c66_paired_reading_is_directional` or `test_c68_pairs_are_counted_once`, both named in
   the module docstring). So `O4_P3_minus_P1_ci95 = (8.394, 53.479)` had no guard at all.
2. **C68 — a bag of numbers, not a census.** Every guarded C68 key is a count, and the cell
   contains the same counts more than once (two pairs differ on 277; 284 appears as the digest
   count, as `shared_keys` six times and in the prose). Comparing "does 277 appear somewhere"
   cannot see `277 (O1 vs O3)` become `271`.
3. **The falsifiability probe was not falsifiable for C68.** `test_the_guard_bites_when_the_
   recomputation_moves` re-ran the bag-of-numbers check against the sabotaged recomputation, so
   for C68 it printed "moved 1 key" and still found the cell satisfied — and the assertion
   deliberately exempted C68.
4. **Import pollution.** `_probe` imported the clone's `recompute_r2` into this process,
   popping `recompute`/`recompute_r2` from `sys.modules` and inserting the (deleted) clone
   directory on `sys.path` without restoring either. The unit reported the leg passing
   standalone and failing inside `pytest tests/`.

## The trap in "reproduce it exactly"

`[8.39, 53.48]` occurs TWICE on the C67 row: once in the claim prose ("O4 P3 - P1 = +23.5211
[8.39, 53.48], which ex…") and once in the Value cell (the guarded text). A naive
`s.replace(..., 1)` — the plant the earlier unit described — hits the PROSE, leaves the cell
untouched, and the guard is green for a reason that has nothing to do with its comparison. The
reproduced exit 0 was therefore real but confounded. Planting the CELL occurrence and running
only the pre-existing legs still exits 0 (`6 passed, 3 deselected`), which is the honest
measurement of the cosmetic admission.

## What changed (one file, additive)

`tests/test_claims_value_guard.py`:

* `_c67_violations(expected, cell)` — parses the two contrast sentences and the arm-mean table
  and compares each delta, each interval bound, each of the sixteen arm means and the
  rows/arms/non-200 census **in the slot the cell put it in**, using the pin rendered to the
  precision the cell wrote (decimal half-up, so `-88.845` renders `-88.85`, the cell's own
  rendering, and `8.394` renders `8.39`). A fabricated interval in a null contrast fails; a
  bare point where the pin excludes zero fails.
* `_c68_violations(expected, cell)` — reads the `(Oa vs Ob)` label as part of the comparison:
  the six differing-counter counts must equal their OWN pair's pin, divided by that pair's
  shared-key pin; the digest census, the repeating-digest clause, `pairs counted twice`,
  `cells distinct` and `6 of 6 cell pairs` are each compared to the pin; and each pair's
  `config_fields_all_differ` must still contain `config_id` and `config_sha256` and at least
  five of the six named fields (this is what makes the string-list pins, which carry no
  scalars and were skipped by the generic leg, actually guarded).
* `test_c67_intervals_and_c67a` and `test_c68_pairs_are_counted_once` — the two legs the
  waivers and the docstring named.
* `_fresh_pins()` — the probe re-imports `recompute`/`recompute_r2` from `PKG` (first on
  `sys.path`) and restores `sys.modules` and `sys.path` on exit; `_probe` no longer imports the
  clone's module at all, because `recompute_r2.EXPECTED` is a hardcoded literal and the clone
  is only needed to produce the sabotaged recomputation from its rows.
* The probe now judges C67 and C68 with the STRUCTURAL legs (same comparator as the cell
  tests) and asserts all three of C66/C67/C68 bite; the C68 exemption is removed with its
  reason.

No assertion was weakened and no tolerance was widened. `_legible` / `_legible_loose` are
untouched.

## Red → green (cell-targeted plants, restored, sha256-verified)

| claim | plant in the Value cell | old legs | full file |
|---|---|---|---|
| C67 | `O4 +23.5211 [8.39, 53.48]` → `[8.39, 58.48]` | exit 0 (6 passed, 3 deselected) | exit 1, `C67:O4_P3_minus_P1_ci95 upper bound written 58.48 but pinned 53.479 renders 53.48` |
| C68 | `277 (O1 vs O3)` → `271 (O1 vs O3)` | exit 0 | exit 1, `C68:O1_vs_O3_rows_with_different_cache_counters written 271 for (O1 vs O3) but pinned 277` |

`CLAIMS.md` sha256 before and after every probe:
`3fbf199f85b103d2e954eee225084da04c81776f1c1692ad726544798d68178e`.

## Falsifiability probe (sabotaged rows, not planted text)

`test_the_guard_bites_when_the_recomputation_moves` now reports and asserts:

* C66: 2 guarded keys moved (`T64_minus_T256_A`, `…_ci95`) — unchanged behaviour.
* C67: 7 structural figures no longer satisfied (O4's delta and interval move when P1's cache
  counter is zeroed).
* C68: 1 structural figure no longer satisfied — `O1 vs O3` no longer differs on
  `config_id`/`config_sha256` when O3's rows are relabelled as O1's, so the "6 of 6 cell pairs
  … differing row for row" claim is false against the copy.

## Cannot-bite finding

None outstanding. C68 could not bite as a bag-of-numbers intended (its counts repeat by
design), and the fix was (a) a stricter comparison — pair-keyed — not a waiver or a cell
change. No cell needs to state a value at higher precision: every guarded C67/C68 pin is
written at 2-4 dp and the comparison now uses the cell's own precision.

## Verification

`pytest tests/test_claims_value_guard.py` → 9 passed, exit 0. Full-suite and package tails are
in `orchestration/handoffs/C67-C68-GUARD-PROBE.json`.
