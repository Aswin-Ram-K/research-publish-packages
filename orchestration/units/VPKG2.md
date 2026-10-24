# VPKG2 — Independent verification of UPKGINSTALL2 (paper #2 release package)

**Role:** independent verifier (not the author). **Bound:** 20 tool calls; a claim uncheckable in 3
attempts is recorded `unverified`.
**Write paths:** `scratch/vpkg2/**`, `orchestration/units/VPKG2.md`, `orchestration/handoffs/VPKG2.json`,
`strategy/VERIFICATION_REPORT_PKG2.md`.
**Frozen artifact (never modified):**
`papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz`

## Jobs
1. Re-derive all headline numbers from files (size, sha256, md5, 13 members, payload counts, checks).
2. Archive-vs-payload tree diff apart from regenerated MANIFEST.json — name each differing file.
3. Manifest internal consistency (both directions).
4. Licence files vs `strategy/licence-templates/RELEASED-PIECE/`; PolyForm 4,563 B body digest.
5. Leak scan (unit ids, `scratch/`, `tools/package/`, parent project name).
6. Reproducibility of `scratch/upkginstall2/build_archive.sh` (copy only).
7. Paper §7 vs archive contents (stimulus fixture deliberately absent).
8. Containment incident: one bare `git -C /home/zer0null/Duval status` (upstream self-report) — record only.

## Status log
- (init) card + handoff persisted before any work.

## Final status (complete, 19/20 tool calls)
- **Verdict: `partial`.** All 11 headline claims re-derived and ✅; internal consistency, determinism,
  red→green and §7 agreement all pass.
- **Not claimed by the author, checked because the brief demanded it — both defective:**
  - **Leaks: 28 hits.** `MANIFEST.json` lines 3,5,9,23,32,41,50,86 and `README.md` lines
    6,10,39,49,50,54,81,91,93-98,102,103,114,117,118,120 carry internal unit ids (`UPKG2B`/`UPKG2C`),
    `scratch/` + `tools/package/` paths, and the absolute target path `/home/zer0null/Duval/...`
    (README.md:91). Full list: `scratch/vpkg2/leaks.txt`. Parent-project name `reserach extarctor`: 0 hits.
  - **Licence drift.** `COMMERCIAL.md` identical to `strategy/licence-templates/RELEASED-PIECE/`;
    `CONTRIBUTING.md` and `LICENSE` differ (released variants). The 4,563 B PolyForm body
    `ffcca388…cc8` appears **verbatim once at offset 115** of `LICENSE` (unmodified ✅), but the added
    Scope section `LICENSE:152-163` names `harness/`, `results/`, `fixture/`, `second-labeller/` —
    none of which exist in paper #2's package.
- **Nuance:** the red run emits 4 FAIL lines / `CHECKS 26/30`, not the 3 the claim named; and the
  brief's "payload `counts.files=10`" is the 10-file unpacked archive tree, not `scratch/upkg2c/package`
  (whose own manifest reports 8).
- **Repro:** `build_archive.sh` rebuilt the shipped archive byte-for-byte in an isolated mirror
  (`scratch/vpkg2/repro/`), from inputs alone; frozen `released/` tree untouched.
- **Containment (record-only):** reported bare `git -C /home/zer0null/Duval status`; observed
  `.git/index` mtime `2026-10-18 10:32:19 -0500`, 89,570 B, ≈14.7 h before the run — consistent with no
  write; no write is *observable*, no other file proven untouched. This unit ran no `git` command.
- Report: `strategy/VERIFICATION_REPORT_PKG2.md`.
