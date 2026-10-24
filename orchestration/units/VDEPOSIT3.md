# VDEPOSIT3 — independent verification of UFIXDEP3

**Purpose:** Falsify UFIXDEP3's two documentation corrections in `strategy/DEPOSIT_ARCHIVE.md`.
**Author of the work under check:** UFIXDEP3 (this unit did not write it).
**Handoff under check:** `orchestration/handoffs/UFIXDEP3.json`; diff `scratch/ufixdep3/UFIXDEP3.diff`.
**Prior finding:** VDEPOSIT2 report `strategy/VERIFICATION_REPORT_DEPOSIT_2.md`.

## Claims under test
1. `:17` inputs row now names `papers/encoder-crossover-190/released/README_DEPOSIT.md`
   (10,477 B, `503751f1…`), the path `scratch/ufixman1/build_archive.sh:29` actually reads;
   superseded `scratch/uzenodo2/run2/README_DEPOSIT.md` (6,396 B, `baf13459…`) no longer named.
2. A dated supersession note appended to the `:42` row.
3. File 10,759 B `b7e04cd5…` → 11,170 B `3c82ed49…`.
4. Custody: archive 158,762 B `956d6363…`; package manifest `d41d82cf…`; no paper/package/script byte changed.

## Checks
1. Read file; `:17` vs script's actual read path; digest + size of named path; superseded path absent.
2. Re-run the script's input guard both ways, path overridden only, no rebuild: corrected → accept (0),
   superseded → drift reject (1). Red→green.
3. Sweep `strategy/DEPOSIT_ARCHIVE.md` + `strategy/DEPOSIT_METADATA.md` for present-tense reversed-policy
   survivors and for any build input the script does not read.
4. `:42` note: dated? unmistakably history?
5. Custody digests + no byte changed in paper/package/script.
6. Whole-document: could it still mislead a rebuilder?

## Classification
contradicted / overstated / not_reproduced / unverified; explicit red→green result.

## Hard bound
10 tool calls. No rebuild. No network. No edits to the document, script, archive, package, or papers.

## Write paths
`strategy/VERIFICATION_REPORT_DEPOSIT_3.md`, `orchestration/units/VDEPOSIT3.md`,
`orchestration/handoffs/VDEPOSIT3.json`, `scratch/vdeposit3/**`
