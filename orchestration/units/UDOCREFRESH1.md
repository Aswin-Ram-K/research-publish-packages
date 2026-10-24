# UDOCREFRESH1 — refresh stale archive digests in the upload-facing documents

**Date:** 2026-10-18. **Bound:** 15 tool calls. **Used:** 15.

## Purpose

The upload artifact `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` was
rebuilt (UREADMEFIX1) to fix dead paths in its front-page `README_DEPOSIT.md`, so its size, sha256 and
archive-manifest digests moved. Documents a human reads *while uploading* still quoted the previous
values. Re-measure the archive, sweep the workspace for stale occurrences, classify each hit, and
correct class (a) in place — new value live, old value retained verbatim as dated history.

## Write paths

`strategy/DEPOSIT_ARCHIVE.md`, `strategy/ZENODO_UPLOAD.txt` (does not exist — see below),
`strategy/DEPOSIT_METADATA.md`, `scratch/udocrefresh1/**`, this card,
`orchestration/handoffs/UDOCREFRESH1.json`. Not touched: `papers/**`,
`scratch/uneutral10/package/**`, `/home/zer0null/Duval`.

## Measured facts (literal commands, literal output)

```
$ stat -c '%s bytes' papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz
159014 bytes
$ sha256sum .../encoder-crossover-190-released.tar.gz
478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7
$ md5sum .../encoder-crossover-190-released.tar.gz
4066c3428c1e4836d200909c6a2db6b0
$ tar -tzf .../encoder-crossover-190-released.tar.gz | wc -l
37
```
Extracted archive manifest: `files[]` 30, `counts` `{"files": 31, "bytes_total": 844708,
"staged_from_source_tree": 20}`, archive `MANIFEST.json` = 11,761 B /
`9898e384601e84e53b8a71cf9cc7777a7fbc15454aaa1f32d678f74752d9e38c`,
`manifest_self` = `a4d6767c9fbe85d85c63376cb724a392ba438f9bebca30a3690e42b6b71830e3`;
`README_DEPOSIT.md` = 10,585 B /
`71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d`. **Every number in the unit card is
confirmed** except the claimed write-path `strategy/ZENODO_UPLOAD.txt`, which does not exist.

```
$ python3 tools/package/check_manifest.py --package <ABS>/scratch/udocrefresh1/x/encoder-crossover-190-released
missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0
manifest_self_recomputes=True (blank generated_utc; drop manifest_self; sort_keys indent=2)
VERDICT PASS        (exit 0)
$ (cd <extraction> && python3 verify/recompute-claims.py)
ALL PUBLISHED NUMBERS REPRODUCED: True
VERDICT: PASS
fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55   (exit 0)
```

## Two stale digests the unit card's pattern list missed

The rebuild changed `MANIFEST.json` **content**, so besides `844,600 → 844,708` and
`503751f1…/10,477 → 71f76e60…/10,585`, these two live values also moved:
`23b7fa94… → 9898e384…` (archive `MANIFEST.json` sha256) and `6381551c… → a4d6767c…`
(`manifest_self`). Both were live in `strategy/DEPOSIT_ARCHIVE.md` and are corrected there.

## Classification of the 240 sweep hits

Class (a) corrected: `strategy/DEPOSIT_ARCHIVE.md:15,16,18,20,51` (+ header + appended dated block);
`strategy/DEPOSIT_METADATA.md:31,133,134,342,347` (+ §0 provenance sentence).
Class (b) dated/frozen, left verbatim: `strategy/DEPOSIT_ARCHIVE.md:88,127,153,154,168`;
`strategy/DEPOSIT_METADATA.md:35-37,366-367`; `strategy/VERIFICATION_REPORT_DEPOSIT_{2,3,4}.md`;
all `orchestration/units/*.md` and `orchestration/handoffs/*.json`; `scratch/**` build/custody trees
(`ufixdep*`, `vdeposit*`, `uneutral10` siblings) and `papers/.../encoder-crossover-190-released/`
(the superseded unpacked tree's own manifest).
Class (c) unrelated lookalikes: `.venv/**` (scipy/numpy test data), tectonic-cache/hyphenation tables,
`state/**/sf.pdf`, `scratch/urender2/*.xml` coordinates.

## Remainder — class (a) sites outside the declared write paths (UNFIXED)

1. `strategy/SUBMISSION_RUNBOOK.md:20-22` and `:47-48` — live pre-flight/upload instructions:
   "confirm the digest is still `bcdbf75e…` (158,956 B)" and "the sha256 must read `bcdbf75e…fbb6a2`".
   FALSE now; this is the document read *during* the upload.
2. `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt:77-79` — the real `ZENODO_UPLOAD.txt`
   (`strategy/ZENODO_UPLOAD.txt` does not exist). Per `DEPOSIT_METADATA.md:17` this file is
   authoritative for the archive digest record; its live "Companion paper-side archive" section still
   records `bcdbf75e…/158956`. Its `:53-63` block is dated UFIXDEP4 history (class b).
3. `strategy/ZENODO_DEPOSIT.md:398,433-434` — "**Live values (measured):** bytes **158,956**, sha256
   `bcdbf75e…`" and the `10,477 B` README line. Live claims, now false.

Observed but out of scope (not an archive-digest value): `strategy/SUBMISSION_RUNBOOK.md:28-30` gives
the PDF as 184,933 B while `strategy/DEPOSIT_METADATA.md:210` gives 188,364 B.

## Artifact integrity

The tarball was never written. Re-measured after the edits: 159,014 B, sha256
`478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`, md5
`4066c3428c1e4836d200909c6a2db6b0`, 37 members — identical to the pre-edit measurement.
