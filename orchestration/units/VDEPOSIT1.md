# VDEPOSIT1 — independent verification of the rebuilt deposit archive

**Role:** independent verifier (NOT the author; UFIXMAN1 rebuilt the archive).
**Bound:** 18 tool calls.

## Claims to falsify
- `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` = 158,762 B,
  sha256 `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a`, 37 members
  (1 top-level dir + 5 subdirs + 31 files), byte-identical on two builds.
- Manifest describes the archive's own tree: 30 listed, `counts.files` 31, `bytes_total` 844,089.
  Superseded: 157,650 B / `7389bd87…`.
- `check_manifest.py` at extracted archive root → all-zero mismatches, `VERDICT PASS`, exit 0.
- Same tool on `scratch/uneutral10/package` also passes.
- With the package's 28-file manifest restored in the stage, checker must report `unlisted=2`,
  `VERDICT FAIL`, non-zero exit (red→green).
- `verify/recompute-claims.py` in extraction → exit 0, `ALL PUBLISHED NUMBERS REPRODUCED: True`.
- Package manifest byte-unchanged: sha256 `d41d82cf…`, 28 listed / `counts.files` 29 / 831,775.
- `diff -r` package vs archive payload (excl. MANIFEST.json, CITATION.cff, README_DEPOSIT.md) empty.

## Write paths (only these)
`scratch/vdeposit1/**`, `strategy/VERIFICATION_REPORT_DEPOSIT.md`,
`orchestration/units/VDEPOSIT1.md`, `orchestration/handoffs/VDEPOSIT1.json`

## Method
Re-derive every number from disk with my own build, not by trusting the author's stdout.
