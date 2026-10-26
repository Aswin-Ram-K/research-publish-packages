# DEPOSIT_ARCHIVE.md — release-archive provenance

Spec of record for what may be uploaded. Maintained by release units; digest table refreshed by **UARTIFACT2** on 2026-10-18 (post-DOI rebuild), previously **UDOCREFRESH1** on 2026-10-18 (archive rebuilt by **UREADMEFIX1**; see the UDOCREFRESH1 block at the end); last written by
**UFIXDEP4** on 2026-10-18, which fixed the package `CONTRIBUTING.md` draft banner (a dead
link to a non-shipped `PLACEMENT.md`) and rebuilt the archive; previously **UFIXDEP1** on
2026-10-18, which re-measured the archive after its manifest was rebuilt to describe the archive
itself (previously **URELEASE9** on 2026-10-17, after the late
`package/COMMERCIAL.md` licence fix).

## Current: shippable archive

| field | value |
|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
| bytes | **159,185** (superseded: 159,085 — v1, pre-concept-DOI; 159,014, 2026-10-18 UDOCREFRESH1; 158,956, 2026-10-18 UFIXDEP4; 158,762, 2026-10-18 UFIXDEP1; 157,650, 2026-10-17 UDEPOSIT2) |
| sha256 | `196f5311a9b5446af44bafdd688f00035e11f5ec2912f20233e5fa8feedc9a34` (superseded: `add182e7…` (159,085 B, v1); `478941c0…` (159,014 B); `bcdbf75e…`; `956d6363…`; `7389bd87…`) |
| md5 | `b3b30f66d231924e02706de0eb3fbc15` (UCONCEPT1 2026-10-18 concept-DOI rebuild; superseded: `479f352569bcf406d9e8e86386afc932` (v1); `4066c3428c1e4836d200909c6a2db6b0`, added by UDOCFIX1 2026-10-18) |
| members | 37 = 1 top-level dir (`encoder-crossover-190-released/`) + 5 subdirs + 31 files |
| archive manifest | `MANIFEST.json` describes the archive: 30 of the 31 archive files listed (all but `MANIFEST.json` itself; `CITATION.cff` and `README_DEPOSIT.md` **are** enumerated); 11,761 B, `210dc61343cf4274fdf6215f1836201000da230e7dcd2490541a07c6104078b6`, `counts.files` 31, `counts.bytes_total` 845,023, `manifest_self` `48344e50…` (UCONCEPT1 2026-10-18 concept-DOI rebuild; superseded: 11,761 B / 844,877 / `5afab382…`, UARTIFACT2 2026-10-18; 844,708 / `a4d6767c…`) |
| inputs | `scratch/uneutral10/package/` (29 files) + `scratch/uzenodo2/run2/CITATION.cff` (concept-DOI `32bee18f…`, UCONCEPT1 2026-10-18; superseded post-v1-DOI `56300d7c…`, UARTIFACT2 2026-10-18) + `papers/encoder-crossover-190/released/README_DEPOSIT.md` |
| proof | builds byte-identically twice (`cmp` clean internally and across two runs); member list identical to the previous archive; `diff -r` against the package inputs is **not** empty — exactly one file differs, `MANIFEST.json`, which is regenerated for the archive (11,761 B, `210dc613…`) and so cannot equal the package's (11,043 B, `fecdc1fb…`); the other 28 package files are byte-identical |

Build recipe (deterministic — epoch mtimes, numeric owner 0/0, name-sorted, `gzip -n`):

```sh
tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 \
    -C <stage> -cf - encoder-crossover-190-released | gzip -n -9 > out.tgz
```

## NOT the deposit — superseded candidate data package (29 files, no wrapper dir; do not upload)

| field | value |
|---|---|
| path | `scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` |
| bytes | 169,869 |
| sha256 | `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610` |
| manifest check | `check_manifest.py` → `VERDICT PASS` (exit 0) |
| upload text | `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` |

## Superseded — retained, never upload

| path | bytes | sha256 | why |
|---|---|---|---|
| `scratch/uauclean1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` | 169,845 | `2338ed02c1c6770b182a79355dbda36cb6d593e08e65a3d38ae9da369c4b048f` | embeds the pre-fix `COMMERCIAL.md` (3,512 B, `ca86a625…`) and old `MANIFEST.json` (`manifest_self` `e44caf89…`). See `scratch/uauclean1/zenodo/SUPERSEDED.md` |
| `papers/encoder-crossover-190/released/encoder-crossover-190-released/` (unpacked dir) | — | — | a third, distinct packaging variant with a **31-file** manifest (covers `CITATION.cff` + `README_DEPOSIT.md`); its `COMMERCIAL.md` is still the pre-fix 3,512-byte file (`ca86a625…`), its `README_DEPOSIT.md` is `b10762…`, `manifest_self` `89ef3836…`, `counts.files` 31. Un-git-tracked. **Left unmodified by URELEASE9** — its manifest policy is undecided, so refreshing it is a separate decision | *Superseded 2026-10-17 (UDEPOSIT2):* this unpacked tree no longer exists at that path — UDEPOSIT2 **moved, not deleted** it to `scratch/udeposit2/superseded-unpacked-tree/`, and the dated marker `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md` (2026-10-17) now stands in its place; the present-tense figures above are the row's retained historical record, not a live claim. *Re-checked 2026-10-18 (UARTIFACT2):* two stray unpacked trees had reappeared under `papers/encoder-crossover-190/released/` (this path plus `encoder-crossover-190-released (2)/`, 31 files each); both were **moved, not deleted**, to `scratch/_superseded-unpacked/` — see its `README.md`.
| `scratch/urelease9/build/old-release-a0a210fc.tar.gz` | 157,272 | `a0a210fcdde1eab14e2e2d8d9c90b2ee897b4968ac7028c28c4c7d0187a5e088` | historical bytes of the superseded tarball, kept inside the URELEASE9 build dir for audit |

## Invariants

1. The shippable archive carries one top-level directory. Its own `MANIFEST.json` describes the
   **archive**: it lists 30 of the 31 archive files (all but `MANIFEST.json` itself, so both deposit
   extras are enumerated) with `counts.files` 31 and `counts.bytes_total` 844,708.
   `check_manifest.py --package <extracted archive root>` -> `unlisted=0`, `VERDICT PASS`, exit **0**
   (UFIXDEP1, 2026-10-18; re-run and re-measured by UFIXDEP4, 2026-10-18). The 29-file payload keeps its own manifest
   (`scratch/uneutral10/package/MANIFEST.json`: 28 listed + itself, `counts.files` 29,
   `counts.bytes_total` 832,286, `manifest_self` `e5b51719…`), which also reports `VERDICT PASS`, exit **0**.
   *Superseded 2026-10-17 (retained as history):* the two deposit extras were *not* enumerated by
   the payload `MANIFEST.json` (which covered only the 29 payload files); `check_manifest.py` then
   reported `unlisted=2` at the tarball root, which that date *believed* to be by design, and only
   the 29-file payload passed. That belief was **reversed on 2026-10-18** — see UFIXDEP1 below.
2. Any change to a file under `scratch/uneutral10/package/` invalidates every row above
   and requires a rebuild plus a new `ZENODO_UPLOAD.txt`.

## UDEPOSIT2 — 2026-10-17 (append only; nothing published, nothing uploaded)

Hazard removal in the released-artifact area, then a re-freeze because one shipping file changed.

1. The stale unpacked tree `papers/encoder-crossover-190/released/encoder-crossover-190-released/`
   (31 files; pre-fix `COMMERCIAL.md` `ca86a625288ac6fd9e3ae0ca9ee2a94acf3001891e5d30f347a686a975b5b9d6`,
   `README_DEPOSIT.md` `b10762bdb746fe8c90cf92f3aa8b548b3e51c9a4390bccfdc3eba0590b7b737f`,
   `manifest_self` `89ef383627e2e774b01bcbb8f1afdb96ccbe260e8a4fec99e746467b7a6f14be`,
   `counts.files` 31) was **moved, not deleted**, to `scratch/udeposit2/superseded-unpacked-tree/`
   (per-file digests: `scratch/udeposit2/superseded-unpacked-tree.sha256`, 31 lines). A dated marker
   now stands at `papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md`. The name-stem
   clash with the tarball is gone.
2. The "30 of the 31 files" claim was measured. It does **not** appear in the shipping
   `README_DEPOSIT.md`; that wording exists only in the superseded tree's README (`b10762…`), whose own
   manifest did enumerate 30 of 31. The shipping README claimed "28 of the 29 files" — true of the
   payload manifest (`counts.files` 29, 28 enumerated, `manifest_self` `f8337fc2…`) but ambiguous about
   the archive, which ships 31 files.
3. `README_DEPOSIT.md` — a deposit-only extra, **not** one of the 29 package files — was clarified to
   state: package = 29 files; `MANIFEST.json` enumerates 28 of them plus its own `manifest_self`; the
   archive adds exactly 2 deposit-only files (`CITATION.cff`, `README_DEPOSIT.md`) for 31 files total;
   and `check_manifest.py` at the archive root reporting `unlisted=2` / exit 1 **was, on 2026-10-17,
   held to be** by design, with the correct invocation being `--package scratch/uneutral10/package`.
   No package file was touched. *Superseded 2026-10-18 (UFIXDEP1):* that policy was reversed — the
   archive's manifest now describes the archive, so the same check at the extracted root reports
   `unlisted=0` / `VERDICT PASS` / exit **0**, and the README was rewritten to match
   (`503751f19ad71f6efa4d42217449948178b164521d4acc37ca9ddc4834970085`).
4. **Rebuilt** (recipe unchanged, built twice, `cmp` exit 0, identical sha256):

   | field | value |
   |---|---|
   | path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
   | bytes | 157,650 (was 157,305) |
   | sha256 | `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` |
   | members | 37 (unchanged: 1 top dir + 5 subdirs + 31 files) |
   | shipping `README_DEPOSIT.md` | `358ce44601ffaca52840c1b56588c1e8f95e089ca0b17787d28ec85e7a152007` (was `baf134595ecb65bb94fcd42d7587acce7655e1a3ad7cb4eaab92b6cece8673f4`) |
   | inputs | `scratch/uneutral10/package/` (29 files, byte-unchanged) + `scratch/uzenodo2/run2/CITATION.cff` (`1c1d25ba…`, unchanged) + the corrected `README_DEPOSIT.md`, staged at `scratch/udeposit2/build/` |

5. Checks, literal exit codes, **as measured on 2026-10-17**: `check_manifest.py --package
   scratch/uneutral10/package` → `VERDICT PASS`, exit **0**; the same tool at the extracted archive
   root → `unlisted=2` (`CITATION.cff`, `README_DEPOSIT.md`), `VERDICT FAIL`, exit **1** — the
   then-current design, **reversed on 2026-10-18** (UFIXDEP1 below re-measures that same root at
   `unlisted=0`, `VERDICT PASS`, exit **0**);
   `verify/recompute-claims.py` exit **0** (`ALL PUBLISHED NUMBERS REPRODUCED: True`, fixture digest
   `c7696edc…`); `second-labeller/parse_fixture.py` exit **0** (190/190, 721 options, no failures);
   `second-labeller/compare.py` exit **0** (routeB kappa 0.9013584840356494, closed subset
   `0.8837023738280471`/106, roster subset `0.9139973672663448`/84 — matching the README);
   `diff -r` inputs vs extraction exit **0** (empty).

The previous archive bytes (`778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb`,
157,305 B) are **superseded** by this rebuild and must not be uploaded.

## UFIXDEP1 — 2026-10-18 (append only; nothing published, nothing uploaded)

The archive was rebuilt so its integrity manifest describes the archive it actually ships inside,
rather than the 29-file package it was assembled from. Re-measured from disk by this unit:

| field | value | superseded (dated history) |
|---|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | same path |
| bytes | **158,762** | 157,650 (2026-10-17, UDEPOSIT2 below); 157,305 (2026-10-17, URELEASE9) |
| sha256 | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` | `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` (157,650 B); `778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb` (157,305 B) |
| members | 37 = 1 top-level dir + 5 subdirs + 31 files | 37 (unchanged) |
| archive `MANIFEST.json` | 30 listed = the 31 archive files minus `MANIFEST.json` itself, so `CITATION.cff` and `README_DEPOSIT.md` **are** enumerated; `counts.files` 31; `counts.bytes_total` 844,089; `manifest_self` `8daf32ea280059b26b3b43edb0709a3c0c389025fc426e901170925f836a8839` | the superseded archive is not on disk here, so its old manifest shape is **UNKNOWN** and not re-asserted |

**Other archive figures re-measured 2026-10-18.** shipping `README_DEPOSIT.md` sha256 `503751f19ad71f6efa4d42217449948178b164521d4acc37ca9ddc4834970085` (10,477 B) - the `358ce44601ffaca52840c1b56588c1e8f95e089ca0b17787d28ec85e7a152007` digest recorded for the 2026-10-17 (UDEPOSIT2) build is superseded; `CITATION.cff` sha256 `1c1d25ba9d1bd9c92742d8d8a53705cc06937c0b8c8ab1b6a9e749da924536c8` (1,837 B, unchanged, matches the UDEPOSIT2 record). Package `MANIFEST.json` still `manifest_self` `f8337fc2030c938f17dbe8d396362107a69070ae83761edb6929721fad2249d5`.

**Package vs archive, plainly.** The **package** is 29 files: 28 listed in
`scratch/uneutral10/package/MANIFEST.json` plus that manifest file itself. The **archive** is 31
files: the 29 package files plus `CITATION.cff` and `README_DEPOSIT.md`, which are deposit metadata,
not package content. The archive's manifest describes the archive; the 29-file package keeps its own
byte-unchanged manifest.

Checks, literal, UFIXDEP1 2026-10-18: `check_manifest.py --package <extracted archive root>` ->
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit **0**;
`check_manifest.py --package scratch/uneutral10/package` -> the same counters, `VERDICT PASS`, exit **0**.


## UFIXDEP4 — 2026-10-18 (append only; nothing published, nothing uploaded)

The 29-file package changed: `CONTRIBUTING.md:3` carried a self-labelled **DRAFT** banner that
linked to `../PLACEMENT.md`, a strategy file that does not ship — a dead link in a public
deposit. It was replaced with a short released-artefact contributing statement (released research
artefact, not open source; PolyForm Noncommercial 1.0.0; commercial use requires a paid licence;
ideas and corrections welcome, code not merged, integrated by re-implementation; the repository
issue tracker as the contact channel). No contact email was invented.

| field | value | superseded (dated history) |
|---|---|---|
| package `CONTRIBUTING.md` | 3,547 B, `3b5e59622b3e4b7d4b9326101b615bcef484ddd80b31b78306ba416698a87996` | 3,036 B, `dd8b8ee416c2bc79b6f4da5502aa6dce258ae8e128f2c901d4fbe5b103fab45b` |
| package `MANIFEST.json` | 11,043 B, `fecdc1fbf67820be2b9988008453282d9f0e4663d9a90551684e1a0f57d9494a` (`manifest_self` `e5b5171902709910…`, `counts.bytes_total` 832,286) | `d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02` (`manifest_self` `f8337fc2030c938f…`, `counts.bytes_total` 831,775) |
| archive | 158,956 B, `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`, 37 members — **this row is the UFIXDEP4 build's dated value; the CURRENT upload value is 159,085 B / `add182e778fcb418fc630ba76e06261575650fa85a289e0d842dfa51ecce1240` / md5 `479f352569bcf406d9e8e86386afc932` (post-DOI rebuild; re-measured by UARTIFACT2 2026-10-18; see the Current table above; superseded 159,014 B / `478941c0…` / md5 `4066c342…`)** | 158,762 B, `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` (UFIXDEP1); 157,650 B, `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` (UDEPOSIT2) |
| archive `MANIFEST.json` | 11,761 B, `23b7fa947fd2ee8c2b58963280dce104e031605b9e91c46e217428c118178856`, `manifest_self` `6381551cf9e31deb1999bda20f1e55929da848ca1abb2d74aa3a66449dbd8616`, `counts.files` 31, `counts.bytes_total` 844,600, 30 of 31 listed | 11,761 B, `e9e5e5e0…` (pre-fix) |

**Proof (literal, re-measured 2026-10-18).** Built with `scratch/ufixman1/build_archive.sh`,
which stages the 29 package files, adds `CITATION.cff` and `README_DEPOSIT.md`, and regenerates
the archive manifest (`GENUTC=2026-10-18T08:05:47Z`). Two runs are `cmp`-clean (exit **0**) and
byte-identical; `check_manifest.py` at the extracted archive root gives
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit
**0**; the same tool on `scratch/uneutral10/package` gives the same counters, `VERDICT PASS`,
exit **0**; `verify/recompute-claims.py` in the extraction exits **0** with
`ALL PUBLISHED NUMBERS REPRODUCED: True` and fixture digest `c7696edc…`.

**`:18` correction (earlier wording was overstated).** The prior claim that `diff -r` against the
inputs is empty was wrong: the archive's `MANIFEST.json` is regenerated and cannot equal the
package's. Measured: exactly one of the 29 package files differs (the manifest); the archive
manifest is 11,761 B / `23b7fa94…` versus the package's 11,043 B / `fecdc1fb…`; the other 28
package files are byte-identical, and the two deposit extras are added.

## UDOCREFRESH1 — 2026-10-18 (digest refresh; append only; nothing published, nothing uploaded)

The shippable archive was rebuilt by **UREADMEFIX1** on 2026-10-18 to fix dead paths in its
front-page `README_DEPOSIT.md` (10,477 B / `503751f1…` -> 10,585 B / `71f76e60…`); nothing else in the
archive changed except that file's `MANIFEST.json` entry, so the archive bytes and both of the
archive manifest's digests moved. Every value below was re-measured from the file on disk by
UDOCREFRESH1 on 2026-10-18.

| field | value | superseded (dated history) |
|---|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | same path |
| bytes | **159,014** | 158,956 (UFIXDEP4, 2026-10-18); 158,762 (UFIXDEP1, 2026-10-18); 157,650 (UDEPOSIT2, 2026-10-17) |
| sha256 | `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7` | `bcdbf75e…` (158,956 B); `956d6363…`; `7389bd87…` |
| md5 | `4066c3428c1e4836d200909c6a2db6b0` | not previously recorded in this file |
| members | 37 = 1 top-level dir + 5 subdirs + 31 files (unchanged) | 37 |
| archive `MANIFEST.json` | 11,761 B, `9898e384601e84e53b8a71cf9cc7777a7fbc15454aaa1f32d678f74752d9e38c`, `manifest_self` `a4d6767c…`, `counts.files` 31, `counts.bytes_total` 844,708, 30 of 31 listed (all but itself) | 11,761 B, `23b7fa94…`, `manifest_self` `6381551c…`, `counts.bytes_total` 844,600 |
| shipping `README_DEPOSIT.md` | 10,585 B, `71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d` | 10,477 B, `503751f1…` |

Literal checks (UDOCREFRESH1, 2026-10-18), archive extracted to `scratch/udocrefresh1/x/`:
`python3 tools/package/check_manifest.py --package /home/zer0null/reserach extarctor/scratch/udocrefresh1/x/encoder-crossover-190-released` ->
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit **0**;
`verify/recompute-claims.py` inside the extraction -> `ALL PUBLISHED NUMBERS REPRODUCED: True`, fixture
digest `c7696edc…`, exit **0**. The tarball itself was not written by this unit; its sha256 was
re-measured after these edits and is unchanged at `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`.

## UARTIFACT2 — 2026-10-18 (post-DOI digest refresh + rebuild-chain repair; append only; nothing published, nothing uploaded)

The published Zenodo DOI `10.5281/zenodo.23463945` was installed into `CITATION.cff` (now 2,006 B,
`56300d7c…`) and the shippable archive was rebuilt. Every value below was re-measured from disk by
UARTIFACT2 on 2026-10-18.

| field | value | superseded (dated history) |
|---|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | same path |
| bytes | **159,085** | 159,014 (UDOCREFRESH1, 2026-10-18); 158,956 (UFIXDEP4); 158,762 (UFIXDEP1); 157,650 (UDEPOSIT2) |
| sha256 | `add182e778fcb418fc630ba76e06261575650fa85a289e0d842dfa51ecce1240` | `478941c0…` (159,014 B); `bcdbf75e…`; `956d6363…`; `7389bd87…` |
| md5 | `479f352569bcf406d9e8e86386afc932` | `4066c3428c1e4836d200909c6a2db6b0` (UDOCFIX1, 2026-10-18) |
| members | 37 = 1 top-level dir + 5 subdirs + 31 files (unchanged) | 37 |
| archive `MANIFEST.json` | 11,761 B, `14c1901515ec14f72a8259984bd14c4e98b17cf8d259b53344d029ef344f4156`, `manifest_self` `5afab382…`, `counts.files` 31, `counts.bytes_total` 844,877, 30 of 31 listed (all but itself) | 11,761 B, `9898e384…`, `manifest_self` `a4d6767c…`, `counts.bytes_total` 844,708 |
| `CITATION.cff` | 2,006 B, `56300d7c43a4cc9d65912130922a5505f07403adebaa73e13da28d4ac792b2a3` (`doi: "10.5281/zenodo.23463945"` version DOI; concept DOI `10.5281/zenodo.23463944`) | 1,837 B, `1c1d25ba9d1bd9c92742d8d8a53705cc06937c0b8c8ab1b6a9e749da924536c8` (pre-DOI) |
| shipping `README_DEPOSIT.md` | 10,585 B, `71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d` (unchanged by UARTIFACT2) | 10,477 B, `503751f1…` |

**Rebuild-chain repair (task 1).** `scratch/ufixman1/build_archive.sh` still pinned the pre-DOI values and
its CITATION source `scratch/uzenodo2/run2/CITATION.cff` was still the pre-DOI copy. Literal failure,
reproduced *before* any repair:

```
$ sh scratch/ufixman1/build_archive.sh
README_DEPOSIT.md drifted: 71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d
[exit 1]
```

Three further divergences surfaced while repairing and are now fixed: the shipped `MANIFEST.json`
carries `"generated_utc": "2026-10-19T04:14:50Z"` (the script pinned `2026-10-18T08:05:47Z`); the
shipped `README_DEPOSIT.md` member mode is `0600`, not the script's forced `0664`; and the CITATION
source itself. Repairs: (a) refreshed `scratch/uzenodo2/run2/CITATION.cff` to the post-DOI bytes
`56300d7c…`; (b) `want_cit` -> `56300d7c…`, `want_front` -> `71f76e60…`; (c) default `GENUTC` ->
`2026-10-19T04:14:50Z`; (d) dropped the README stage `chmod 0664` so the source mode (`0600`) is
preserved; (e) added a `BUILD_WORK` override so a unit can build into its own scratch area. Literal
proof *after* repair (built to `scratch/uartifact2/build-work/`, never the shipped path):

```
--- self-contained build ---
bytes=159085  path=/home/zer0null/reserach extarctor/scratch/uartifact2/build-work/build/encoder-crossover-190-released.tar.gz
add182e778fcb418fc630ba76e06261575650fa85a289e0d842dfa51ecce1240  .../scratch/uartifact2/build-work/build/encoder-crossover-190-released.tar.gz
members=37
--- shipped archive (authority) ---
bytes=159085  path=/home/zer0null/reserach extarctor/papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz
add182e778fcb418fc630ba76e06261575650fa85a289e0d842dfa51ecce1240  .../papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz
BYTE-IDENTICAL: self-contained build == shipped archive (cmp exit 0)
[exit 0]
```

The shipped tarball was not written by this unit: its sha256 is `add182e7…` and md5
`479f3525…` both before and after.

**Archive checks (literal, task-required).** On the shipped extraction
`scratch/uartifact2/extracted/encoder-crossover-190-released`:
`python3 tools/package/check_manifest.py --package <abs extracted root>` ->
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit **0**;
`python3 verify/recompute-claims.py` (run from inside the extraction) ->
`ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, fixture digest `c7696edc…`, exit **0**.

**HTML derivative (task 3).** `papers/encoder-crossover-190/rendered/encoder-crossover-190.html` was
stale (85,507 B, mtime 2026-10-16): it still read `DOI: AUTHOR TO CONFIRM` at `:988-991`. `MANUSCRIPT.md`
already carried the DOI, so the documented derivative route
`papers/encoder-crossover-190/rendered/convert.py` was re-run rather than hand-edited:

```
$ python3 convert.py
paper: encoder-crossover-190
wrote .../encoder-crossover-190.html 86041 bytes
byline: Aswin Ram Kalugasala Moorthy\ Independent researcher\ 	exttt{aswinram.k.1603@gmail.com}
AUTHOR SLOT occurrences in HTML: 0
[exit 0]
```

The regenerated HTML (:989-992) now reads `Persistent identifier: DOI 10.5281/zenodo.23463945` /
concept DOI `10.5281/zenodo.23463944`. The pre-refresh HTML is retained at
`papers/encoder-crossover-190/rendered/_superseded/encoder-crossover-190-html-pre-DOI-refresh-2026-10-16.html`.

**Stray unpacked trees (task 4).** `papers/encoder-crossover-190/released/` held two unpacked trees,
`encoder-crossover-190-released/` (31 files; pre-DOI `CITATION.cff` `1c1d25ba…`) and
`encoder-crossover-190-released (2)/` (31 files; post-DOI `CITATION.cff` `56300d7c…`). Both were
**moved, not deleted**, into `scratch/_superseded-unpacked/`, with a `README.md` mapping each to its
original path, file count and why, and per-tree `.sha256` manifests (31 lines each). `released/` now
contains exactly the tarball, `README_DEPOSIT.md`, and `SUPERSEDED-UNPACKED-TREE.md`.

**Live-value sweep of this file (classification of every hit).**

1. Current table (`:15-21`) — **stale-live** -> refreshed (old values retained parenthetically).
2. `:20` inputs row — **stale-live** (CITATION source was pre-DOI) -> annotated.
3. `:45` "this unpacked tree no longer exists at that path" — **had become false** -> annotated.
4. `:154` inline "the CURRENT upload value is 159,014 B / `478941c0…` / md5 `4066c342…`" — **stale-live** -> refreshed.
5. `:21` proof mention of archive manifest `9898e384…` — **stale-live** -> refreshed to `14c19015…`.
6. `:95-99`, `:112-113` (UDEPOSIT2), `:123-128` (UFIXDEP1), `:152-155` (UFIXDEP4), `:172-195` (UDOCREFRESH1) — **dated history**: no longer current, but correctly framed as superseded/dated -> retained verbatim, not rewritten.
7. `:19` `counts.bytes_total` 844,708 / `manifest_self` `a4d6767c…` — **stale-live** -> refreshed to 844,877 / `5afab382…`.

**Not touched.** The shipped tarball (never written). No upload, publication, or external service; no TMLR
variant; no `/home/zer0null/Duval` access; no git command.


---

## 2026-10-18 (UCONCEPT1) — the deposit citation switched from the v1 version DOI to the concept DOI

**Why.** Zenodo mints a new **version DOI** for every version, so `10.5281/zenodo.23463945` pins **v1 only**.
The author is publishing a v2; a v2 archive whose own citation file names the v1 version DOI would ship a
self-defeating citation. The **concept DOI** `10.5281/zenodo.23463944` always resolves to the latest version,
so every citation of the deposit now uses it.

**What moved (only the identifier).** Live sources edited: `papers/encoder-crossover-190/MANUSCRIPT.md`
(3 occurrences, `:743` / `:794` / `:858`), `papers/encoder-crossover-190/submission/METADATA.md:26`
(1 occurrence), and the archive's own `CITATION.cff` source at `scratch/uzenodo2/run2/CITATION.cff:25`.
The pre-existing concept-DOI mention in the *Persistent identifier* paragraph
(`MANUSCRIPT.md:860`) is the **survivor**; the substitution produced 4 concept-DOI mentions in the
manuscript, not a fifth.

`CITATION.cff` source: 2,006 B / sha256 `56300d7c…` -> **`32bee18f…`**
(`doi: "10.5281/zenodo.23463944"`); `build_archive.sh`'s `want_cit` guard re-pinned to it by UCONCEPT1.
`want_front` (`README_DEPOSIT.md` `71f76e60…`) unchanged.

**Derived, regenerated (never hand-edited).** `submission/main.tex` via
`python3 tools/package/md2tex.py --package encoder-crossover-190` (run twice, `cmp` clean);
payload tarball via `tar --mtime=@0 --sort=name -cf - -C submission main.tex | gzip -n -9` (built twice,
`cmp` clean, member byte-identical to `main.tex`); PDF via
`scratch/utex1/bin/tectonic -r 1 --keep-logs` with `HOME`/`TMPDIR`/`TECTONIC_CACHE_DIR` inside the
workspace and **no** `-Z continue-on-errors` (exit 0, 0 `Undefined control sequence`, 0 `!` lines);
HTML via `rendered/convert.py`; archive via `BUILD_WORK=scratch/uconcept1/archN sh scratch/ufixman1/build_archive.sh`
(built twice in two independent work dirs, byte-identical; the new build was then installed at the shipped
path and a second run reported `BYTE-IDENTICAL … cmp exit 0`, exit 0).

**New shippable archive.** 159,185 B / sha256
`196f5311a9b5446af44bafdd688f00035e11f5ec2912f20233e5fa8feedc9a34` / md5
`b3b30f66d231924e02706de0eb3fbc15`, 37 members. Extracted at its own root,
`python3 tools/package/check_manifest.py --package <ABSOLUTE extracted root>` ->
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0 / VERDICT PASS`, exit 0; and
`python3 verify/recompute-claims.py` inside the extraction -> `ALL PUBLISHED NUMBERS REPRODUCED: True /
VERDICT: PASS / fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`,
exit 0. `diff -rq` against the v1 extraction differs in exactly two files: `CITATION.cff` (the intended
change) and `MANIFEST.json` (re-derived from it: `counts.bytes_total` 844,877 -> 845,023,
`manifest_self` `5afab382…` -> `48344e50…`).

The v1 archive (159,085 B / `add182e7…` / md5 `479f3525…`) is preserved at
`scratch/uconcept1/superseded-v1-archive.tar.gz`; the stray unpacked trees under
`scratch/_superseded-unpacked/` were **not** touched (the build consumes `scratch/uzenodo2/run2/CITATION.cff`,
`scratch/uneutral10/package/` and `released/README_DEPOSIT.md` — never those).

**Unchanged:** numeric-literal multisets of `MANUSCRIPT.md`, `main.tex` and the PDF text — token deltas
exactly `23463945: -3, 23463944: +3` per file, totals unchanged (1195 / 1322 / 1354); `\cite` 23 over
13 distinct keys, `\bibitem` 13, uncited 0, unresolved 0.
