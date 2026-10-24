# VDEPOSIT4 — independent verification of UFIXDEP4's deposit repair + cascade

**Purpose.** Falsify UFIXDEP4 before the deposit is uploaded to Zenodo for a permanent DOI.
Independent verifier; did not write what is checked. **Fix nothing.** No network. No edits to the
five documents, the package, the archive, the build script, or any paper. No rebuild/overwrite of
the shipped archive.

**Hard bound:** 15 tool calls.

**Write paths (only these):** `strategy/VERIFICATION_REPORT_DEPOSIT_4.md`,
`orchestration/units/VDEPOSIT4.md`, `orchestration/handoffs/VDEPOSIT4.json`, `scratch/vdeposit4/**`.

**Claims under test**
1. Repair: `scratch/uneutral10/package/CONTRIBUTING.md:3` DRAFT banner + dead `../PLACEMENT.md`
   link gone; replacement names PolyForm Noncommercial, paid-commercial, ideas-not-code, issue
   tracker; no invented email; 3,547 B `3b5e59622b3e4b7d4b9326101b615bcef484ddd80b31b78306ba416698a87996`; ASCII.
2. Cascade: package `MANIFEST.json` 11,043 B `fecdc1fbf67820be…`; archive 158,956 B
   `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`, 37 members, installed over
   `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`; superseded 158,762 B `956d6363…`; two builds byte-identical; extraction checks pass.
3. Shipped checks on an extraction: `check_manifest.py` (five counters zero, VERDICT PASS) and
   `verify/recompute-claims.py` (`ALL PUBLISHED NUMBERS REPRODUCED: True`, fixture digest
   `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`).
4. Five docs carry the new digest; workspace-wide sweep for `956d6363…` and `7389bd87…` without
   `bcdbf75e…`, classified live defect / dated history / frozen record.
5. `strategy/DEPOSIT_ARCHIVE.md:18` wording true: archive MANIFEST legitimately differs; other package files byte-identical.
6. Custody: no paper / `submission/**` / `tools/package/**` byte changed.
7. The whole question: would a reader deposit the right file?

**Classification required:** contradicted / overstated / not_reproduced / unverified; ≥1 red→green guard.
