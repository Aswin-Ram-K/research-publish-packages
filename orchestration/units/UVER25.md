# UVER25 — independent verification of UWIRE2 (build source-tree wiring)

**Verdict: `pass-with-corrections`.** Bound: 25 tool calls (used 13).
Write paths used: `strategy/VERIFICATION_REPORT_25.md`, `orchestration/units/UVER25.md`,
`orchestration/handoffs/UVER25.json`, `scratch/uver25/**`. Full evidence in the report.

## What was verified (all reproduced unless noted)

1. **Identity** — sha256 `45fe28e435f7d1d7ddd11bbf327d741a1bef2028b6edf11b9e27d8d732867ad3`,
   1066 lines, `bash -n` rc=0; pre-edit `scratch/uwire2/UBUILD1.build.sh.orig` =
   `df471955…0ab5`, 1036 lines. Claimed `45fe28e4…7ad3` reproduced.
2. **Anchors** — re-derived: `:135-140` default ✓, `:147` warning ✓, `:180` `SHIP_STAGED=(` ✓,
   `:309-315` FATAL ✓, `:339` `NEVER_SHIP=(` ✓, `:622` `LIC_SRC=` ✓, `:631` licence sha guard
   (`3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`) ✓, gate `:1051-1066`
   with `exit "$GATE_RC"` ✓. **Correction:** the staged-copy block is `:257-263`, not `:256-262`.
3. **Runs** (`scratch/uver25/{a,b,c,d}.log`, explicit `DEST` under `scratch/uver25/**`):
   default → `scratch/ubij3/tree-three-r2`, `promoted_default=yes` (29,936 OOV, 8 dropped);
   `SAN_SRC_FROZEN_OVERRIDE=1` → `repro/encoder-crossover-190-SANITISED`, `no`, + WARNING
   lines (95,606 OOV, 14 dropped); `SAN_SRC_OVERRIDE=…/tree-three-b` → that exact tree;
   both overrides set → override wins (highest precedence).
4. **Ordering** — wiring line is log line 1; the first write/destructive op in the script is
   `rm -rf "$DEST"` at `:169`. Warning precedes everything destructive.
5. **Hunks** — diffed current vs both baselines (`scratch/uwire1/…orig` 1019L,
   `scratch/uwire2/…orig` 1036L): 2 hunks each, all comments plus the SAN_SRC wiring block.
   No hunk touches `SHIP_STAGED`, the missing-file `FATAL`, `NEVER_SHIP`, licence plumbing,
   the `LIC_SHA` guard, or the gate. **Wiring-only.**
6. **Emitted set** — 64 paths on all three paths, byte-for-byte identical path lists
   (`diff a b`, `diff a c`). Kept 52 on both; drops 8 (promoted) vs 14 (frozen).
7. **Tests** — green `8 passed in 0.04s`; red 1 (default reverted to frozen literal on a
   copy) `3 failed`; red 2 (frozen branch neutralised on a copy) `1 failed`
   (`test_frozen_override_still_selects_the_frozen_tree` in both). Red→green reproduced.
   **Correction:** claimed counts 4/2 are each one high — the author's harness also failed
   `test_build_wiring_doc_names_both_overrides`, which reads `strategy/BUILD_WIRING.md`
   (current doc passes; it fails only against a stale pre-UWIRE2 doc copy).
8. **Containment** — real `/home/zer0null/research-publish-packages` empty (0 entries, mtime
   18:07), untouched; no command of mine wrote `/home/zer0null/Duval` and no git verb was run
   against it (a `find -newermt` sweep shows concurrent-unit `.git` mtimes, not mine).

## Open corrections for the next unit

- Fix the printed ratio: `:151-153` says "~12.4x more residual project identifiers: 44,056 vs
  3,317" → `44056/3317 = 13.3` (or 12.3 as a difference ratio). Comment-only, but it is echoed
  at build time.
- If exact red counts matter, pin the doc copy the red harness reads.
- Caveat: a concurrent unit may supersede the promoted *path* (`scratch/ubij3/tree-three-r2`);
  the mechanism verified here does not depend on which path wins.
