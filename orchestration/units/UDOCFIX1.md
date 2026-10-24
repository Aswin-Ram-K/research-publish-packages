# UDOCFIX1 — make the Zenodo upload path unambiguous; fix two stale-value contradictions

**Status:** done. **Bound:** 12 tool calls; used 8 (bash×2, read×4, patch×1, verify×1). No git run. No artifact
written. `/home/zer0null/Duval` untouched.

## Purpose
The author is publishing a Zenodo deposit now. Three contradictions remained in human-facing upload docs;
one was dangerous: the docs disagreed on which file IS the deposit.

## Verdict by evidence (not by which doc is louder): the TARBALL is the deposit

Both archives extracted read-only to `scratch/udocfix1/{tar,zip}` and compared.

| property | tarball `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | zip `scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` |
|---|---|---|
| bytes / sha256 / md5 | 159,014 / `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7` / `4066c3428c1e4836d200909c6a2db6b0` | 169,869 / `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610` |
| members | 37 = 1 top-level dir `encoder-crossover-190-released/` + 6 dirs + 31 files | 29 files at archive ROOT, no wrapper dir |
| `README_DEPOSIT.md` / `CITATION.cff` | PRESENT (in wrapper) | ABSENT (both) |
| own manifest reconciles | `check_manifest.py` → `missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0`, `VERDICT PASS`, exit 0; `recompute-claims.py` → `ALL PUBLISHED NUMBERS REPRODUCED: True`, `VERDICT: PASS`, exit 0 | 11,043 B manifest, 29 root files, no deposit extras |

Evidence for the tarball: extractable without exploding into the author's cwd, a superset (adds
`CITATION.cff` + `README_DEPOSIT.md`), and its own manifest reconciles + its verifier passes. The zip was
recorded only as a digest record and labelled NOT-THE-DEPOSIT everywhere.

## Corrections applied (new value primary, old kept verbatim as dated history)
1. `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` — the dangerous inversion: tarball was called
   *"Companion paper-side archive - NOT the deposit file"* while the superseded zip headed
   *"ARCHIVE TO UPLOAD"*. Retitled tarball **DEPOSIT FILE - UPLOAD THIS ONE, AND ONLY THIS ONE** with size +
   sha256 + md5; zip section retitled **NOT THE DEPOSIT**. Also fixed the UFIXDEP4 digest block, where the
   current 159,014/`478941c0…` value was wrongly labelled as superseded BY the older 158,956/`bcdbf75e…`;
   fixed `:91` ("29-file" → 37-member tarball) and the closing NOTE (`:221-223`), both kept as dated history.
2. `strategy/DEPOSIT_ARCHIVE.md:153` (now `:154`) — classified **dated history**: it is the UFIXDEP4 build's
   own measured archive row, so the value 158,956 B / `bcdbf75e…` was NOT overwritten (that would falsify the
   dated table). Instead an inline pointer marks the CURRENT upload value 159,014 B / `478941c0…` / md5
   `4066c342…`. Also added the deposit md5 row (`:17`) and retitled the "Current: data package" table
   (`:29`) to "NOT the deposit — superseded candidate … do not upload".
3. `strategy/SUBMISSION_RUNBOOK.md:105-106` — `main.tex` measured on disk = **84,695 B /
   `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`** (md5
   `1f1ae487ae7420783d5c1dada2a252f7`), matching `BUILD_NOTES.md:292`; the runbook's 84,223 B /
   `8374fd28…` was stale and is kept verbatim as superseded (2026-10-17 UDEPOSITDOC2). Also added the
   deposit md5 to Step 0 and Step 1.2 and relabelled the zip in Step 0 as not a deposit candidate.
4. `strategy/DEPOSIT_METADATA.md` — row A and the recommendation already named the tarball correctly; added
   the deposit md5, and removed the "(If the author uploads the 29-file zip instead: …)" alternative-deposit
   sentence, replacing it with a plain NOT-the-upload label.

## Bounds honoured
`papers/**` and `scratch/uneutral10/package/**` not modified (mtime sweep since 23:04 lists only the four
granted docs). No git command run. Tarball re-measured after edits: 159,014 B /
`478941c0…` / `4066c342…`, mtime unchanged 2026-10-18 22:54:16.

## Note on a card claim
Card said BUILD_NOTES may be the stale one and asked to correct "whichever is stale". Here BUILD_NOTES is
CORRECT and the runbook was stale, so no `papers/**` write was needed — the `papers/**` prohibition was
never in conflict.
