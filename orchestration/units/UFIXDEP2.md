# UFIXDEP2 — deposit archive: reversed-policy doc fixes + self-contained rebuild

**Status:** done — 12 tool calls used of 15.
**Bound:** 15 tool calls (this card = 1)

## Purpose
Two jobs on the deposit archive, both arising from `strategy/VERIFICATION_REPORT_DEPOSIT.md` (VDEPOSIT1):
the artifact passed, but (1) docs still state the old, now-reversed `unlisted=2 / exit 1` policy as current,
and (2) `scratch/ufixman1/build_archive.sh` declares `PKG` at `:22` but never reads it — the build inherits
its stage tree from a previous tarball and is therefore not self-contained.

## Job 1 — reversed-policy sentences
Verify each flagged claim against disk, then correct only those that read as current; explicitly label the
superseded wording as dated history (the fact that `unlisted=2` was once believed by design is worth keeping).
Sweep `strategy/DEPOSIT_METADATA.md` for the same class.

## Job 2 — self-contained rebuild
Stage the 29 payload files from `scratch/uneutral10/package`, add `CITATION.cff` + `README_DEPOSIT.md`,
regenerate the manifest inside the stage, produce the tarball with **no prior-artifact dependence**.
Prove byte-identity against the shipped archive (158,762 B, sha256 `956d6363…7910a`, 37 members); build twice.
Shipped artifact is the authority — never adjust it to match the script.

## Write paths
`strategy/DEPOSIT_ARCHIVE.md`, `strategy/DEPOSIT_METADATA.md`, `scratch/ufixman1/build_archive.sh`,
`scratch/ufixdep2/**`, `orchestration/units/UFIXDEP2.md`, `orchestration/handoffs/UFIXDEP2.json`

## Result
- Job 1 done: `strategy/DEPOSIT_ARCHIVE.md` 10,127 B → 10,759 B (`91f1843a…` → `b7e04cd5…`); three
  present-tense assertions of the reversed `unlisted=2`/"by design" policy (`:56`, `:80`, `:94-95`) now
  read as dated 2026-10-17 history with the 2026-10-18 reversal stated. `strategy/DEPOSIT_METADATA.md`
  needed nothing (29,867 B / `953cbc28…` unchanged; no sentence of that class survived UFIXDEP1).
- Job 2 done: superseded `scratch/ufixman1/build_archive.sh` in place (same path, so no future unit
  reaches for the non-self-contained recipe). It stages the 29 package files, adds `CITATION.cff`
  (`scratch/uzenodo2/run2/`) + `README_DEPOSIT.md` (`papers/.../released/`), regenerates the manifest
  in-stage, packs, and asserts identity; it never reads `prev-*.tar.gz` and never writes the shipped file.
- Proof: 158,762 B, sha256 `956d6363…7910a`, 37 members; two runs identical; `cmp` vs shipped exit 0.
- `check_manifest.py --package <abs>` at extracted root → `unlisted=0`, `VERDICT PASS`, exit 0;
  `recompute-claims.py` → `ALL PUBLISHED NUMBERS REPRODUCED: True`, exit 0.
