# C63-CELL — give the headline claim a real Value cell and a guard

**Status:** done · **Bound:** 30 tool calls, bash ≤12 · **Writes:** `papers/context-cache/CLAIMS.md`,
`papers/context-cache/recompute_r2.py`, `tests/test_claims_value_guard.py`, this card, and the handoff.

## Purpose

C63 ("the engine, not the model, sets the per-turn uncached bill") was the one claims-table row whose
numbers existed only as prose: no Value cell, no `recompute_r2` EXPECTED pin, and no coverage in
`tests/test_claims_value_guard.py`. It is also the paper's headline claim.

## What was done

1. **Row rebuilt** (`CLAIMS.md:229`). The claim text is now 5 sentences stating the current finding; the
   Value cell carries 1,136 rows = 4 x 284, the four `(model/engine, hit, unc/turn, hot gcd, rows)` cells,
   the three main effects with CIs (549.33 [462.4, 631.9]; -400.02 [-474.2, -326.5];
   interaction -403.63 [-479.7, -328.5]), the four within-contrasts, the ratios
   (engine 2.3058x MoE / 1.1987x dense), the shares of the 1,006.2306 grand mean and the replicate-arm band.
2. **Superseded block relocated**, not deleted: `### Superseded (C63)` at `CLAIMS.md:231-239` keeps the MTP
   correction whole, including every superseded value (engine share 0.9115 -> 0.5459 and the rest).
3. **Year typo fixed:** `MTP CORRECTION (2024-10-24)` -> `(2026-10-24)`. It was a silent year error in a
   published row; the correct batch date is recorded in `orchestration/STATUS.md` §10 and the V2C/V2D handoffs.
4. **New pin** `recompute_r2.py c63()` — 61 values, re-derived from the four cells' own rows without
   importing `recompute.py`, reproducing every published figure to the digit.
5. **Guard extended** — C63 added to `CONTRACT`, with a dedicated headline-figure test in addition to the
   generic legibility check.
6. **A real defect in the shared guard helper was fixed:** the number regex truncated every `Nx` multiplier
   to its integer part, so `1.249x` read as `1` and any cell trivially satisfied it. Fixing it tightened two
   pre-existing legs (C62, C65) which now pass honestly.

## Red -> green

* Pin: `engine_effect 549.33 -> 464.55` → `FAIL 60/61` (exit 1); restored → `PASS 61/61` (exit 0);
  sha256 `b422788a…0d464` identical before and after.
* Guard: cell `549.33 [462.4, 631.9] -> 464.55` → 2 failed / 4 passed; restored → 6 passed;
  sha256 `4bc0047b…e118e` identical before and after.

## Acceptance

`verify_package.py` PASS · `recompute.py all` PASS · `recompute_r2.py all` exit 0 (7/7 claims PASS) ·
pytest trio 37 passed · full suite 1374 passed, 1 skipped.

## Verdict on dates

No other claim row in `CLAIMS.md` carries a bracketed date or a disagreeing year. The only other
date-shaped strings are the pointers and the typo record I wrote (lines 235-236, which quote the old form on
purpose). Line 181/196/197/269 contain bare 4-digit groups (`2096`, `1056`, …) that are block sizes.

## Not closed here

`cell_hot_gcd_qwen3.5-9b_vllm = 1,088` is unverifiable from rows (a launch reading; the gcd is 16) and is
declared, not pinned. The four `cell_rows_*` values are waived, so a `284 -> 288` plant does not go red.
