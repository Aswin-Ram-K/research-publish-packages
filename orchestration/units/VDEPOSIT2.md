# VDEPOSIT2 — independent verification of UFIXDEP2

Verifier unit. Did not author any code under check. Job: try to falsify UFIXDEP2's claims.

## Claims under check (UFIXDEP2)
1. `strategy/DEPOSIT_ARCHIVE.md` corrected at ~:56, :80, :94-95 (reversed policy mended); went
   10,127 B `91f1843ac42fbd42a3766a8377a0d55f5c00cb08789c979484055796e5194de2` →
   10,759 B `b7e04cd5acf93f76be5e2fb8eaea8b31136a333ae72f52a7b9d55944d8f12a57`.
   `strategy/DEPOSIT_METADATA.md` unchanged at `953cbc28bc07fb4ce15b2e90432946d9429ee6db813c7e141549b302be7c1afb`.
2. `scratch/ufixman1/build_archive.sh` superseded in place: self-contained rebuild (stages from
   `scratch/uneutral10/package`, adds `CITATION.cff` + `README_DEPOSIT.md`, regenerates manifest in
   stage, never reads `prev-*.tar.gz`), reproduces shipped archive byte-for-byte.

## Required checks
1. Doc correction + sweep both docs for surviving "check_manifest.py fails / unlisted=2 / exit 1 by design".
2. Self-containment: build in `scratch/vdeposit2/` with all `prev-*.tar.gz` renamed away; then prove
   input-digest guards go red (red→green).
3. Byte-identity: 158,762 B, sha256 `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a`,
   37 members (6 dirs + 31 files). Build twice, cmp both + shipped.
4. Shipped checks on extraction: `tools/package/check_manifest.py` (absolute path) + `verify/recompute-claims.py`;
   5 zero counts, VERDICT PASS, exit 0, ALL PUBLISHED NUMBERS REPRODUCED: True, fixture digest
   `c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.
5. Custody: archive digest before/after; package `MANIFEST.json` still
   `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02`.
6. Open item: `strategy/DEPOSIT_ARCHIVE.md:42` retired unpacked path — live or marked superseded?
   Report only, do not edit.

## Classification required
`contradicted` / `overstated` / `not_reproduced` / `unverified`, plus one red→green guard result.

## Hard bound
18 tool calls. Say so rather than guess if a check is impossible.

## Write paths (nothing else)
`strategy/VERIFICATION_REPORT_DEPOSIT_2.md`, `orchestration/units/VDEPOSIT2.md`,
`orchestration/handoffs/VDEPOSIT2.json`, `scratch/vdeposit2/**`

## Do NOT
Edit any doc/script/archive/package/paper. No network. Do not overwrite shipped archive or `prev-*.tar.gz`.
