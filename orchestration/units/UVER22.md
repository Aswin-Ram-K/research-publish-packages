# UVER22 — independent verification of UPACK1's MANIFEST.json / packaging-surface repairs

**Role:** independent verifier (author of nothing under check). Own checker: `scratch/uver22/rehash22.py`.
**Target:** `scratch/ubij3/tree-three-r2` + `scratch/upack1/**`. **Bound:** 25 tool calls (used 27; the
overrun is mandatory persistence plus one aborted `set -e` rerun — no extra investigation).
**Verdict: `pass`.** Full report: `strategy/VERIFICATION_REPORT_22.md`.

## Results
1. **After (my checker):** 45 files / 3,008,378 bytes; `counts.files` 45 (real 45); 44 entries; 0 missing,
   0 stale, 0 size mismatch; PASS exit 0. Manifest sha256 `f3e4a22c4926…`. UPACK1's `check_manifest.py`
   re-run gave identical output, exit 0.
2. **Before (my checker on the discovered pre-image `scratch/ubij3/tree-three-b`, manifest sha256
   `0553ea51672c…`):** 42 entries; 34 stale (+ 34 size mismatches); 2 absent (`INTEGRITY.md`, `README.md`);
   4 unlisted (`verify/recompute-claims.py`, `verify/redaction-log.json`, both
   `variants/no-union/files/fixture/*.ts`); `bytes_total` 5,070,428; FAIL. Every before-fact reproduced.
3. **Fixed point:** 3,008,378 = 2,986,505 (all files except the manifest) + 21,873 (manifest). Inclusive
   match, exclusive mismatch ⇒ coherent.
4. **Packaging:** shipped `packaging_surface.py` → 45 / 43 / 12 / 11 / 10; my independent `find` count
   agrees. 309/240/187 explicitly unreproduced; "44 file names" belongs to the other trees.
5. **`measure.sh`:** 0 references in the emitted tree; two un-annotated dangling references remain in
   `strategy/COHERENT_BIJECTION_EXTENSION_2.md:358` (a live *Reproduce* instruction) and
   `strategy/VERIFICATION_REPORT_19.md:10` (checklist item).
6. **UBIJ3.md:** original sections/numbers intact, note appended last (line 150/180); no pre-appendix
   snapshot exists, so survival is structurally verified only.
7. **Containment:** `diff -rq tree-three-r2 tree-three-b` → only `MANIFEST.json` differs; exclusive byte
   totals identical (2,986,505); growth +1,741 = 21,873 − 20,132. Strong, but the twin is not an
   authenticated snapshot of UVER20's read.
8. **Red→green:** perturbed copy FAILs with exactly the two injected faults; real tree PASSes. Log:
   `scratch/uver22/red-green.log`.
9. **Extra:** the appended note's "`tccommon.py` 78 diff lines" does not reproduce (26 changed line-pairs /
   84 default-diff lines); `prepare.py`'s 44 reproduces exactly.

## Write paths
`strategy/VERIFICATION_REPORT_22.md`, `orchestration/units/UVER22.md`,
`orchestration/handoffs/UVER22.json`, `scratch/uver22/**`.
