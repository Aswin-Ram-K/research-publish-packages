# UWIRE3 — rewire the release build to the data+verification package

**Purpose.** Scope changed: the release is **data + verification tools only, the harness withheld**.
`orchestration/units/UBUILD1.build.sh` still ships 18 `code/harness/*` entries and promotes a 45-file
tree (`scratch/ubij3/tree-three-r2`). Re-point it at the proven package `scratch/urecut1/package/`
(29 files, 874,473 bytes) and fix a test that is green over the wrong tree.

**Hard bound:** 25 tool calls. Stop and report if the build cannot be red→greened in 3 attempts.

**Write paths (nothing else):**
`orchestration/units/UBUILD1.build.sh`, `strategy/BUILD_WIRING.md`, `tests/test_build_wiring.py`,
`orchestration/units/UWIRE3.md`, `orchestration/handoffs/UWIRE3.json`, `scratch/uwire3/**`.

**Read-only:** `/home/zer0null/Duval` (never bare `git status`). `/home/zer0null/research-publish-packages`
never written. Build only into `scratch/uwire3/**`.

## Skeleton plan (written first, per instruction)

1. Recon: list `scratch/urecut1/package` (29 files), read `UBUILD1.build.sh` ship list / scope clause /
   staging / inventory, read `tests/test_build_wiring.py`, read `strategy/BUILD_WIRING.md`.
2. Re-derive `SHIP_STAGED` from the package's real files (29); remove the 18 `code/harness/*`.
3. Stage the package verbatim (`cp -r "$SAN_SRC/." "$PKG/"`); drop the `paper/ code/ eval/` staging,
   the `LAB_SRC` dedup block, the authored `$PKG/README.md`, `$PKG/code/README.md`, `$PKG/paper/LICENSE`.
4. Re-pin `PROMOTED_SAN_SRC` to `scratch/urecut1/package` — ONE named constant, one line.
   (`PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`; follow-up re-pins this exact line after UNEUTRAL6.)
5. Update the scope clause, inventory, commit message, and `strategy/BUILD_WIRING.md` pins.
6. Rewrite `tests/test_build_wiring.py` to DERIVE the promoted path from the script's constant and assert
   properties (path exists; warning names it; frozen override still selects the frozen tree; ship list ==
   files actually present in the promoted tree).
7. Preserve all fail-closed guards: DEST `exit 2` before `rm -rf`, ship-list-missing `FATAL`, `NEVER_SHIP`
   absence check, licence sha guard, `exit "$GATE_RC"`.
8. `bash -n`; run the build into `scratch/uwire3/dest/research-publish-packages`; report staged/kept/dropped,
   emitted file count, gate out-of-vocabulary token count.
9. Red→green: green, then point the constant at a wrong tree, show RED, restore.
10. Finish the handoff and re-parse it as JSON.

**Notes.** The package's `MANIFEST.json` and `second-labeller/OWED_CORRECTIONS.md` are real package files,
so they must be removed from `NEVER_SHIP` (which asserts absence) and added to the ship list. UNEUTRAL6 is
neutralising ten identifiers inside the package in place, so no digest of the package is pinned anywhere;
only the path is pinned, in the single constant.

## Result

See `orchestration/handoffs/UWIRE3.json`.
