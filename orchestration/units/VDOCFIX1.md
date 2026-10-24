# VDOCFIX1 — independent verifier of UDOCFIX1 (upload-doc labelling)

**Purpose.** Re-derive, without reading the author's report, that four upload-facing docs name
exactly one deposit file. Artifact under check:
`papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` (read-only).

**Bound.** 12 tool calls. **Status.** done (9 investigative + 3 persistence).

**Write paths.** `scratch/vdocfix1/**`, `orchestration/units/VDOCFIX1.md`,
`orchestration/handoffs/VDOCFIX1.json`. Nothing under `papers/**`,
`scratch/uneutral10/package/**`, or the four checked docs was modified.

## Claims and independent measurements

1. **Which archive is the deposit — SUPPORTED.** Tarball has one wrapper dir
   (`encoder-crossover-190-released/`), 37 entries = 1 top dir + 5 subdirs + 31 files, and carries its
   own `README_DEPOSIT.md` + `CITATION.cff`. Both zips
   (`scratch/uauclean1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip`, 169,845 B;
   `scratch/ulicfix1/zenodo/…-v1.zip`, 169,869 B) have 29 entries **at the archive root, no wrapper
   directory**, and neither contains `README_DEPOSIT.md` or `CITATION.cff`. Tarball is the superset.
2. **Tarball identity — SUPPORTED.** bytes `159014`; sha256
   `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`; md5
   `4066c3428c1e4836d200909c6a2db6b0`; 37 tar entries / 31 files. (The *card's* quoted digest
   `…94d3279a…` is a transcription error; the docs carry the measured `…94d32739…`.)
3. **Manifest reconciles — SUPPORTED.** `check_manifest.py --package
   "$PWD/scratch/vdocfix1/tar/encoder-crossover-190-released"` →
   `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`,
   exit 0. `verify/recompute-claims.py` inside the extraction → exit 0, `VERDICT: PASS`,
   `ALL PUBLISHED NUMBERS REPRODUCED: True`.
4. **Labelling unambiguous — SUPPORTED.** All four docs name the tarball and mark the zip as
   do-not-upload (`ZENODO_UPLOAD.txt:87`, `DEPOSIT_METADATA.md:67`); the only `158,956` occurrences are
   in explicitly superseded columns/annotations (`DEPOSIT_ARCHIVE.md:154,183-184` under header
   `| field | value | superseded (dated history) |`).
5. **Corrected `main.tex` figure — SUPPORTED.** `SUBMISSION_RUNBOOK.md:108-109` says 84,695 B /
   `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`; disk
   `papers/encoder-crossover-190/submission/main.tex` measures exactly that.
6. **Red→green, non-vacuous — SUPPORTED.** Reverting `ZENODO_UPLOAD.txt` to the pre-edit backup makes
   the check fire (`zip_as_upload=PRESENTS_ZIP`, red); the live doc is green. Reverting the runbook
   makes `maintex_84695=bad` (red). Both checks can fail.
7. **Containment — SUPPLIED.** Tarball re-measured unchanged (159,014 B, same sha256/md5). Within the
   edit window only UDOCFIX1's four docs + `scratch/udocfix1/backup/**` + its card/handoff changed;
   `strategy/ZENODO_DEPOSIT.md` (23:03) is outside the four and belongs to concurrent UDOCREFRESH2.
   No `papers/**` file touched; no git state-changing command run.

**Verdict: pass** (see `orchestration/handoffs/VDOCFIX1.json`).
