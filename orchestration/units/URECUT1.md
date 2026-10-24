# URECUT1 — build the reduced public package (data + verification tools only)

## Purpose
Author-fixed scope: **data + verification tools only — the harness is withheld.** UTRIMM1 proved the
minimal verification closure exists by experiment; URECUT1 builds the package for real in scratch with
the one blocker (`harness/data/fixture-190.json`) removed.

## Declared write paths
`strategy/PUBLIC_PACKAGE_CUT.md`, `orchestration/units/URECUT1.md`, `orchestration/handoffs/URECUT1.json`,
`scratch/urecut1/**`. Read anything; modify no other unit's tree.

## Hard bound
25 tool calls. Work in small increments. Never `cat` a large file.

## Steps
1. Remove blocker: relocate `harness/data/fixture-190.json` to `fixture/fixture-190.json`; patch the ONE
   reading site in `verify/recompute-claims.py`; find every other reference; delete `harness/` from the
   copy and re-run.
2. Decide `variants/` (2 files) and process docs by test.
3. Build `scratch/urecut1/package/` and prove it (literal exit codes + every number; independent manifest
   checker; idempotence diff).
4. Measure new surface (file count, bytes, censuses, token counts, MANIFEST source fields).
5. Report-only: what else must change (UBUILD1.build.sh / BUILD_WIRING.md / test_build_wiring.py pins;
   repro/encoder-crossover-190/ harness leftovers; MANUSCRIPT.md falsified sentences).

## Status
DONE. Built and proved `scratch/urecut1/package/` (29 files, 874,473 bytes): recompute exit 0 with all claim
numbers preserved, parse_fixture exit 0, compare exit 0, independent manifest checker 0/0/0/0/0 exit 0,
idempotent except `generated_utc`. Blocker (`harness/data/fixture-190.json`) relocated to `fixture/` and the
single reading site `verify/recompute-claims.py:59` patched; `harness/` deleted from the copy with numbers
unchanged. `variants/` + process docs tested droppable. Step-5 report-only findings in
`strategy/PUBLIC_PACKAGE_CUT.md`. BOUND OVERRUN: 31 tool calls against the 25 cap, because the census
helpers needed usage discovery and step 5 needed extra evidence reads; work stopped at report time.
