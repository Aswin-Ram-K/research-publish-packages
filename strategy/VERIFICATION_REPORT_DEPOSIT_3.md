# VERIFICATION REPORT — DEPOSIT_ARCHIVE.md (VDEPOSIT3)

Verifier: **VDEPOSIT3** — independent; did not author the work under check.
Subject: **UFIXDEP3** (card `orchestration/units/UFIXDEP3.md`, handoff `orchestration/handoffs/UFIXDEP3.json`, diff `scratch/ufixdep3/UFIXDEP3.diff`), following the contradiction found by **VDEPOSIT2** (`strategy/VERIFICATION_REPORT_DEPOSIT_2.md`).
Method: independent re-read of the document and of the build script's own declarations, plus a literal re-run of the script's extracted input-guard with only the input path overridden. **No rebuild, no network, no edits** to the document, script, archive, package or papers. Bound respected (10 tool calls).

## Verdict: PASS

Every checkable UFIXDEP3 claim survived. No claim was contradicted. One pre-existing wording elsewhere in the document is flagged as *overstated* (see Classification); it is not one of UFIXDEP3's two corrections and is outside its write scope.

## Red -> green (explicit)

Guard extracted verbatim from `scratch/ufixman1/build_archive.sh:36-44`; only `$FRONT` overridden; no build.

GREEN — corrected path `papers/encoder-crossover-190/released/README_DEPOSIT.md`:
  literal output: `GUARD ACCEPTED (no MISSING INPUT, no drift)`
  exit code: **0** -> ACCEPTED

RED — superseded path `scratch/uzenodo2/run2/README_DEPOSIT.md`:
  literal output: `README_DEPOSIT.md drifted: baf134595ecb65bb94fcd42d7587acce7655e1a3ad7cb4eaab92b6cece8673f4`
  exit code: **1** -> REJECTED with drift message

This is the required red→green: the same guard that accepts the documented input rejects the superseded one, so the correction is load-bearing, not cosmetic.

## Check 1 — `:17` names the path the script reads

`strategy/DEPOSIT_ARCHIVE.md:17` now reads:
`| inputs | `scratch/uneutral10/package/` (29 files) + `scratch/uzenodo2/run2/CITATION.cff` + `papers/encoder-crossover-190/released/README_DEPOSIT.md` |`

The script's own declarations (read, not taken from the handoff):
- `scratch/ufixman1/build_archive.sh:27` `PKG="$ROOT/scratch/uneutral10/package"`
- `scratch/ufixman1/build_archive.sh:28` `CIT="$ROOT/scratch/uzenodo2/run2/CITATION.cff"`
- `scratch/ufixman1/build_archive.sh:29` `FRONT="$ROOT/papers/encoder-crossover-190/released/README_DEPOSIT.md"`

All three documented inputs are exactly the script's three input declarations. Named path exists: 10,477 B, sha256 `503751f19ad71f6efa4d42217449948178b164521d4acc37ca9ddc4834970085` — matches the claim and the guard's `want_front` (`build_archive.sh:38`). The superseded path `scratch/uzenodo2/run2/README_DEPOSIT.md` is named **nowhere** in `strategy/DEPOSIT_ARCHIVE.md` or `strategy/DEPOSIT_METADATA.md` (grep clean); its live digest remains `baf134595ecb65bb94fcd42d7587acce7655e1a3ad7cb4eaab92b6cece8673f4`, 6,396 B.

## Check 2 — guard both ways
See Red -> green above. Runs were on the extracted body only; no `rm -rf`, no `tar`, no manifest regeneration was executed.

## Check 3 — survivor sweep
`strategy/DEPOSIT_ARCHIVE.md` + `strategy/DEPOSIT_METADATA.md` searched for a **present-tense** assertion of the reversed policy (`unlisted=2` / "by design" / exit 1 at the archive root):
- `strategy/DEPOSIT_ARCHIVE.md:56-57` — explicit history: "that date *believed* to be by design ... That belief was **reversed on 2026-10-18**".
- `strategy/DEPOSIT_ARCHIVE.md:81-83` — explicit history: "`unlisted=2` / exit 1 **was, on 2026-10-17, held to be** by design ... *Superseded 2026-10-18 (UFIXDEP1):* that policy was reversed".
- `strategy/DEPOSIT_ARCHIVE.md:100-102` — explicit history: "the then-current design, **reversed on 2026-10-18**".
- `strategy/DEPOSIT_METADATA.md` — **zero** occurrences of `check_manifest`, `unlisted`, `by design`, or `VERDICT FAIL`.
Every survivor is date-stamped and past-tense. No present-tense reversed-policy assertion remains. No path is named as a build input that the script does not read (the only other inputs row, `:96`, is the dated 2026-10-17 UDEPOSIT2 history).

## Check 4 — `:42` marked unmistakably
The appended note is dated (**Superseded 2026-10-17 (UDEPOSIT2)**), names the mover (`scratch/udeposit2/superseded-unpacked-tree/`) and the dated marker (`papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md`, 2026-10-17), and closes "the present-tense figures above are the row's retained historical record, not a live claim." The row now reads as history; it cannot be mistaken for a live directory listing.

## Check 5 — custody
- Document: 11,170 B, sha256 `3c82ed49ba08681766fb210f15b85b376476b73ee814d057601eb2c22e5f3dda` — matches the claim (was 10,759 B `b7e04cd5…`).
- Archive: `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` = 158,762 B, sha256 `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` — matches.
- Package manifest: `scratch/uneutral10/package/MANIFEST.json` = sha256 `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` — matches.
- Build script: `scratch/ufixman1/build_archive.sh` sha256 `afca433786dd7428717760ac62197d0a7b0a003f98306863ce03bd168a867abf` — matches the handoff's read-only digest.
- No paper/package byte changed: `papers/encoder-crossover-190` = 36 files, combined sha256 `09fb2d0896664795e62f46cfc85764fc902fe7287b735ccbd829673f4ef856d1`; `scratch/uneutral10/package` = 29 files, combined sha256 `2b342acbbec9ac25b0797d5d0ccc66e3b12c3c240957b384849c4a273ec312aa` — both match UFIXDEP3's pre/post values. Mtime sweep finds nothing under `papers/`, `scratch/uneutral10/`, or the script newer than `orchestration/units/UFIXDEP3.md`; only `strategy/DEPOSIT_ARCHIVE.md` (and UFIXDEP3's own artifacts) changed.
- Archive interior unchanged: extracted `README_DEPOSIT.md` inside the tarball digests to `503751f1…` / 10,477 B — the archive already carries the corrected README, so the document now agrees with the shipped bytes.

## Check 6 — can the document still mislead a rebuilder?
Two residuals, neither introduced by UFIXDEP3 and neither touching `:17`/`:42`:
1. **Overstated (`:18`, pre-existing):** "`diff -r` against the inputs is empty (exit 0)". The archive's `MANIFEST.json` is regenerated at build time (`build_archive.sh:56-63`) and differs from the package's `MANIFEST.json` (11,761 B `e9e5e5e0…` vs 11,043 B `d41d82cf…`), so a naive `diff -r` of the extracted archive against the input set cannot be empty. The exact original invocation is not recorded, so this is flagged for a future unit, not reproduced.
2. The archive `MANIFEST.json` facts quoted at `:16`/`:123` (self-exempting 30-of-31 listing, `counts.files` 31, `counts.bytes_total` 844,089, `manifest_self` `8daf32ea…`) were spot-read from the extracted manifest: {"manifest_self": "8daf32ea280059b26b3b43edb0709a3c0c389025fc426e901170925f836a8839", "counts": {"files": 31, "bytes_total": 844089, "staged_from_source_tree": 20}, "listed": 30, "readme_listed": true, "citation_listed": true, "keys": ["subset", "purpose", "policy", "generated_by", "generated_utc", "target", "harness_revision", "amended_by", "manifest_scope_note", "counts", "files", "manifest_self"]}.

Otherwise no residual: the recipe (`:22-25`) matches the script, all three inputs are the script's three reads, and every superseded artifact is date-stamped.

## Classification
- **contradicted:** none
- **overstated:** `strategy/DEPOSIT_ARCHIVE.md:18` "diff -r against the inputs is empty" (pre-existing, not UFIXDEP3's; see Check 6)
- **not_reproduced:** the original `diff -r` invocation (ambiguous, not run)
- **unverified:** none material

## Residual-mislead assessment
None that bears on UFIXDEP3's correction. The `:18` wording predates this unit and should be tightened by a later release unit.
