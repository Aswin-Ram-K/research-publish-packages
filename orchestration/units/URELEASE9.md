# URELEASE9 — deposit-artifact consistency after licence fix

**Purpose (one):** make the deposit artifacts internally consistent after the late
`package/COMMERCIAL.md` fix. Rebuild the released tarball, re-emit the Zenodo upload text,
mark the old zip superseded, prove the archive sound.

## Inputs (verified by parent)
- `scratch/uneutral10/package/COMMERCIAL.md` — 3,520 B, sha256 `d8762806bbbb53229345b625db77910f60f7c74b608c7f550797053da89f250c`.
- `scratch/uneutral10/package/MANIFEST.json` — 11,043 B, sha256 `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02`, `counts.bytes_total` 831,775, `manifest_self` `f8337fc2030c938f`.
- Fresh data zip: `scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` — 29 members, 169,869 B, sha256 `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610`.
- STALE, must not ship: `scratch/uauclean1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` (sha256 `2338ed02c1c6770b182a79355dbda36cb6d593e08e65a3d38ae9da369c4b048f`) and `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` (157,272 B, sha256 `a0a210fcdde1eab14e2e2d8d9c90b2ee897b4968ac7028c28c4c7d0187a5e088`).

## Tasks
1. Rebuild `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` from
   CURRENT `scratch/uneutral10/package/` + the same two extras (`CITATION.cff`,
   `README_DEPOSIT.md`; confirm locations first). One top-level dir, same member list as
   before, extract → `diff -r` empty vs inputs. Build twice; prove byte-identity.
2. Re-emit `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`: current licence wording
   (commercial licensing available on request), current data zip path+sha256, no draft
   wording; fields title, creators, type, licence `polyform-noncommercial-1.0.0` (spdx),
   version, description, keywords, paper relation.
3. Write `scratch/uauclean1/zenodo/SUPERSEDED.md` (dated; names old zip path+sha256;
   "do not upload"). Do NOT delete the old zip.
4. Prove archive sound: extract, run package self-check (`tools/package/check_manifest.py`)
   and the three shipped tools; report literal exit codes, checker verdict line,
   `recompute-claims.py` verdict line.
5. Report tarball size, sha256, member count, upload-text path, exact `diff -r` result.

## Hard bound
20 tool calls. If the previous build's exact member list cannot be reconstructed from disk,
STOP and report that blocker rather than guessing.

## Write paths (nothing else)
`papers/encoder-crossover-190/released/**`, `scratch/urelease9/**`,
`scratch/uauclean1/zenodo/SUPERSEDED.md`, `strategy/DEPOSIT_ARCHIVE.md`,
`orchestration/units/URELEASE9.md`, `orchestration/handoffs/URELEASE9.json`

## Do NOT
- Touch `papers/*/submission/**` (LaTeX frozen).
- Modify `scratch/uneutral10/package/**` (read only).
- Network calls. No credentials/ORCID in any file. No writes outside listed paths.
