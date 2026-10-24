# FIX-PKG2 — stop PACKAGE.md claiming a gate it lacks; fix C06's retracted floor reading

**Trigger:** task board card, tag `automated` (no human answerer). Handoff stub written before the
first read, per the tag prefix.

**Bound:** 1 pass over the named files, ≤3 red→green cycles. Reached: 1 cycle, 5 plantings.

## Declared write paths

- `papers/context-cache/PACKAGE.md`
- `papers/context-cache/CLAIMS.md`
- `papers/context-cache/verify_package.py`
- `papers/context-cache/recompute.py`
- `scratch/fixpkg2/**` (pre-edit backups)
- `orchestration/units/FIX-PKG2.md`, `orchestration/handoffs/FIX-PKG2.json`

No overlap with any concurrent unit at launch (the tree's newest neighbours, FIX-MAN2, FIX-MANU,
FIX-COVERAGE, FIX-G3BANDS, were all settled by the time this unit started).

## What was found

1. **`PACKAGE.md` claimed a gate it does not have.** `:11` said "Integrity gate: `verify_package.py`
   (exit 0 required)" with no scope. That gate maps ids and resolves cells; it recomputes **no
   value**. §7 step 1 (`recompute.py all`) is the value check, and §9 never said so.
2. **The documented cascade-hole was real and still open.** `V-FINAL2` (checks 3–5, RED E) planted
   `| Not a claim at all, planted | … |` in `CLAIMS.md` and both guards returned exit 0. Re-run here:
   reproduced exactly — the row was invisible to both `CLAIM_RE` and `coverage_ids`.
3. **`CLAIMS.md:76` (C06) still asserted a floor.** Its prose column read "The measured ratio is a
   floor; … 5.3922", while `CLAIMS.md:74` (C05) named no supersession for 3.3133, and
   `MANUSCRIPT.md:139-150` says both halves of that framing are wrong. Anyone citing C06 for a bound
   got the retracted reading. `PACKAGE.md:191` ("The gate fails if any row carries an UNVERIFIED
   mark") was also untrue of unmatchable rows.
4. **Four `CLAIMS.md` corrections-table citations did not resolve:** `` `handoffs/U4.json` ``,
   `U4b`, `CX-V2`, `U15` — there is no `papers/context-cache/handoffs/`; the files live in
   `orchestration/handoffs/`.

## What was changed

- `verify_package.py`: new `table_rows()` + `surface_errors()`; every markdown table row is admitted
  only as a `C\d\d` claim row, a header/separator, a row of the section `Source rows and digests`
  (5 cells), or a row of the numbered corrections table (4 cells, numeric first cell). Anything else
  is an error naming the `CLAIMS.md` line. Wired as check (0) before the census.
- `recompute.py`: new `surface_defects()` with the same admission rule (a bold lead-in line counts as
  a section opener, so the source-key table can be declared without an ATX heading); `coverage_guard()`
  fails the run and lists each invisible row.
- `CLAIMS.md`: the "Source rows and digests" lead-in became a real `###` heading so the table is a
  *declared* section rather than a table under no heading at all; C06 rewritten (not a floor; 5.3922
  is above the measured value and below G5's 6.744; retraction explicit); C05's 3.3133 marked
  superseded as an effect size by C53; four correction citations repointed to
  `orchestration/handoffs/`.
- `PACKAGE.md`: `:11` names the gate's actual scope; §9 states the structural-vs-value split and the
  new row-refusal with its red→green; the `V-CLAIMAUD2` hole note now names the refusal.

## Evidence (commands as run)

| Check | Result |
|---|---|
| `verify_package.py` (after) | `PASS — 62 claims in CLAIMS.md, 62 mapped 1:1, … UNVERIFIED: none`, exit 0 |
| `recompute.py all` (after) | `59 claims checked, all match`, `GRID GUARD PASS 7/7`, `COVERAGE GUARD PASS 62 claims documented, 60 runnable here + 2 script-backed`, exit 0 |
| `recompute.py C06` | `PASS 6/6 values match` |
| RED E: plant `\| Not a claim at all, planted \| … \|` | `verify_package: FAIL - CLAIMS.md:202: unrecognised row, invisible to the claim census`, exit 1; `COVERAGE GUARD FAIL 1 CLAIMS.md row(s) invisible to the census`, exit 1 |
| RED F: plant unbacked `C63` row | `- missing claim ids in READER-MAP: C63`, exit 1; `COVERAGE GUARD FAIL no runner for 1 claim(s): C63`, exit 1 |
| RED G2: source row with an extra cell | `CLAIMS.md:35: unrecognised row, invisible to the claim census (under 'Source rows and digests')`, exit 1 |
| RED H: revert the `###` heading to bold prose | `verify_package: FAIL … CLAIMS.md:33`, exit 1; restored → `cmp` byte-identical, both guards exit 0 |
| tests | 81 passed (`test_paper_attribution_guard`, `test_claims_decompose`, `test_paper_boundary_attribution`, `test_paper_g3_bands`, `test_orchestration_handoffs`, `test_repo_hygiene`) |

## Traps hit (worth carrying forward)

- `papers/context-cache/recompute.py` exports `floor = np.floor`. A new module-level `from
  recompute import *` (or any star-import of it) rebinds `floor` and silently breaks
  `math.floor`. Neither new function calls `floor`.
- `.strip("#")` on a heading turns "# the two claims …" into " the two claims …" and leaves the
  heading text looking like prose — use `re.sub(r"^#{1,6}\s+", "", …)`.

## Not done (recorded, not silently dropped)

- `RUN.json` `verification.synthesis_recompute` still records the 59-vs-62 split without a value
  hash for the *current* `recompute.py`; left untouched, as it is not a claim about a gate.
- `PACKAGE.md:191`'s UNVERIFIED sentence is now literally true (the gate does refuse unmatchable
  rows), but the sentence still reads as a value guarantee. The §9 scope bullet is the correction;
  rewriting the sentence itself is a prose unit's job.
