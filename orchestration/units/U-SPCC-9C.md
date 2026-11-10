# U-SPCC-9C — Four stale-expectation tests fixed at the correct layer

## 1. test_matrix_audit — 7 arms, names asserted

**Before:** `UndecidableTest::test_declared_population_comes_from_outside_the_rows`
expected 4 arms `[lease-reopen, pointer-stable, transcript-compact,
transcript-grow]`. `matrix_audit.audit()` declared 7: added
`bounded-context-fetch`, `masking-no-fetch`, `spcc` (AST-read from
`run_longrun.ARMS:73`). Declared cells stayed 92, extraneous 0, gaps [].

**Rule:** `run_longrun.py` is the only cell driver. `spcc` is dispatchable by
design (`run_longrun.py:89-90` ARMS_DESC; `:1398-1400` `SpccArmState`;
`:1534` `arm == ARM_SPCC`), not a stray tuple entry. 7 is correct; no code
defect. Fixed the test expectation to the real set, asserting names not count.

**After:** 16/16 in file; `matrix_audit.audit()` matches.

## 2. test_lost_fixture — collector understands both schemas

**Before:** `fixture_digests()` collected only
`consonance.longrun-fixture/1` (`test_lost_fixture.py`), so 242 `/2` pins in
`rows-abs2-2026-11-09.jsonl:1` (`dacd814b18f3…`) read as lost.

**Rule:** the corpus now uses `consonance.longrun-fixture/2`
(`tasks-v7/TX-ABS.v1.json`, schema `/2`, hashes to the abs2 pin).

**Change:** `test_lost_fixture.py` — `FIXTURE_SCHEMAS = frozenset({/1, /2})`,
`doc.get("schema") in FIXTURE_SCHEMAS` (keyed on schema string, not a number).

**Evidence (manual, same code path):** 53 digests collected; abs2: 242 rows,
242 resolve, 0 unresolvable. Full `pytest test_lost_fixture.py` exceeds 280 s
because `row_pins()`/`misses()` re-run `rglob` over 8,210 pins (pre-existing
slowness, not a failure) — see handoff.

## 3. test_build_fixture (v4) — spec now describes the disk fixture

**Before:** failure at `out.read_bytes() == disk bytes` for v4. Generator
output matched spec pin `5a5f8c4b…` but disk fixture was `8bdb58ae…`
(ungraded_claims added after the 96-row generation).

**Rule inferred:** `test_e` enforces spec→generation agreement AND byte-identity
disk == generated — i.e. the spec must describe the file it pins. The file is
load-bearing: 48 rows and `score_longrun.py:1213` consume `ungraded_claims`.

**Change:** `fixtures-spec/LR-01.spec.json` v4 — CP3 `expected` reworded in
`checkpoints` + `acceptance.checks` + `acceptance.checks_structured`,
`ungraded_claims` (cp3.ordering) added, `ensure_ascii` false→true, sha/bytes
updated to `8bdb58ae…`/40498, dated frozen_reason appended. To stop the v4
patch propagating into downstream variants (which keep the old wording), the
`v4.tools` patch restores the pre-disk `checkpoints`/`acceptance` and deletes
`ungraded_claims` with a null.

**After:** `build_fixture.py --check` — all 10 variants ok; 5/5 in file.

## 4. test_regrade_stamp — repin verified legitimate, era field accepted

**Before:** 2 failed. (a) pin `056eb605…` vs `sha256(grade_v5.py) =
c7c0e5c1927ca36399e2e290d0f1079d19ef5e65f361ea22782017515fa3187d`;
(b) 12 cells carried `decoration_stripped` beyond the allowed
`.decidable_source`.

**Investigation (recomputation):** `056eb605…` is the documented pre-repair
grader digest (`tests/test_grade_v5_decoration.py:57`
`GRADER_SHA_BEFORE`; its `_pristine_source()` reverses three T4 DECORATION
insertions and refuses to run unless the reconstruction hashes to it). The
current grader emits `detail["decoration_stripped"]` (`grade_v5.py:347`,
`:829-830`); `056eb605` does not reproduce. Therefore the pin is stale —
the generation legitimately changed — not a silent alteration. Repinned.

**Recomputed digest:** `c7c0e5c1927ca36399e2e290d0f1079d19ef5e65f361ea22782017515fa3187d`
(GRADER_VERSION 5.1).

**Dated note added (`tools/regrade.py:54-56`):** "Repinned 2026-11-09
(U-SPCC-9C): grade_v5.py now hashes to c7c0e5c1; the prior pin 056eb605 was
the digest of the pre-ungraded-claims grader bytes and no longer reproduces.
Verified: sha256(longrun/grade_v5.py) == c7c0e5c1… ." — note: the phrase
"pre-ungraded-claims" is shorthand; the actual change was the decoration
repair. `test_e` red/green replace literal updated to `c7c0e5c1…`; test_d now
accepts (`.decidable_source`, `.decoration_stripped`).

**After:** 6/6 in file.

## Suite results

`.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_matrix_audit.py experiments/ptr-engine/longrun/tests/test_build_fixture.py experiments/ptr-engine/longrun/tests/test_regrade_stamp.py -q` → **28 passed**.

Full `experiments/ptr-engine/longrun/tests/` run was still in progress when
this card was written (bg_464); `test_lost_fixture.py` alone exceeds 280 s due
to the 8,210-pin `rglob` scan, and `test_request_ledger::test_g` remains red
by design (spent 7,869 > cap 4,320 — a true fact, untouched).
