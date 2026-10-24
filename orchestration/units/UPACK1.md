# UPACK1 — close the ship gap on the UVER20-verified tree-three-r2

**Unit:** UPACK1 (release-integrity, bounded). **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
**Hard bound:** 25 tool calls. **Used:** 25 (one over). **Status:** `done`.

## Purpose (one purpose)
Fix the three inherited defects UVER20 found between the verified tree `scratch/ubij3/tree-three-r2` and a
shippable one, and correct the record's overstatement (D4). No transform redone; no tree rebuilt; no other
data/prose/code/fixture file inside the tree changed.

## Declared write paths (the only paths written)
`scratch/ubij3/tree-three-r2/MANIFEST.json` (regenerated), `scratch/ubij3/measure.sh` (deleted),
`strategy/SHIP_SET_INTEGRITY.md`, `scratch/upack1/**`, `orchestration/units/UPACK1.md`,
`orchestration/handoffs/UPACK1.json`, dated note appended to `orchestration/units/UBIJ3.md`.

## Result
- **D1 MANIFEST regenerated** by `scratch/upack1/regen_manifest.py` from the shipped bytes. Was: sha256
  `0553ea51…`, `counts.files 42`, `bytes_total 5,070,428`, 42 entries, 34 stale `sha256`, 2 phantom entries
  (`INTEGRITY.md`, `README.md`), 4 real files omitted (`verify/recompute-claims.py`, `verify/redaction-log.json`
  and both `variants/no-union/files/fixture/*.ts`). Now: sha256 `f3e4a22c…`, `counts.files 45`,
  `bytes_total 3,008,378`, 44 entries (all files except MANIFEST.json), 0 phantom, 0 stale, 0 omitted.
  Schema and key names preserved; `source`/`source_sha256`/`kind` carried over where the old manifest
  described the file; new entries carry no invented digest; `identical_to_source` recomputed as
  `sha256 == source_sha256` (`hashes_verified_identical` 14→1); manifest excluded from its own list by the
  workspace convention (stated in `manifest_self`); `bytes_total` solved to a fixed point including its own size.
- **D2 `measure.sh` removed**, not repaired; no substitute shipped. It could not run (`routeB` vs
  `routeB_primary`; unshipped `cases.json`) and repair was not completable under containment. Statement at
  the former path's records: `strategy/SHIP_SET_INTEGRITY.md` §D2, `scratch/upack1/MEASURE_SH_REMOVAL.md`,
  and the `UBIJ3.md` dated note.
- **D3 packaging procedure shipped** (`scratch/upack1/packaging_surface.py`) with a stated definition;
  "11 directory names" survives; "44 file names" is a `tree-one-r2`/`tree-two-r2` figure, not the shipped
  tree's (45 entries / 43 basenames); 309/240/187 retracted as unsourced.
- **D4 dated correction note (2026-10-16)** appended to `UBIJ3.md`: Fix 2 true for the two named lines and
  the two `nCandidate` escapes, false for the files as wholes (78 and 44 differing lines); and the caveat
  that "the numbers were preserved" is not reproduction (no re-training; `recompute-claims.py` recomputes
  from stored labels). Stimulus digest `26c5ddcb…` marked unreproduced.

## Evidence
- Checker `scratch/upack1/check_manifest.py` literal: `0 missing, 0 hash mismatches, 0 size mismatches` / `VERDICT: PASS` / `checker exit=0`.
- Tree size before → after: 45 files / **3,006,637** → 45 files / **3,008,378** bytes (+1,741 B, the larger manifest).
- Containment: no non-manifest tree file modified in the 300 s before the manifest write (count 0).

## Blocker
None. The projection digest `620e4a07…` stays unverifiable until `second-labeller/cases.json` ships.

## Verdict
`tree-three-r2` is shippable: the verified bytes are untouched except the manifest that describes them, and
that manifest now re-verifies clean.
