# UENCFIX1 — fix internal orchestration unit ids leaked into published CITATION.cff

**Workspace:** `/home/zer0null/reserach extarctor`
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Bound:** 25 tool calls; 3 attempts per sub-problem then report unverified.

## Write paths (declared)
- `papers/encoder-crossover-190/**`
- `scratch/uneutral10/**`
- `scratch/ufixman1/**`
- `scratch/uencfix1/**`
- `orchestration/units/UENCFIX1.md`
- `orchestration/handoffs/UENCFIX1.json`

## JOB list
1. Find source of truth CFF used by the build; digest every copy; quote offending lines.
2. Fix at source (replace unit ids with reader-actionable prose; no invented version/date/DOI); case-insensitive sweep of whole package for `\bU[A-Z]{2,}[0-9][A-Z0-9]*\b` plus `scratch/`, `tools/package/`, absolute host paths.
3. Regenerate MANIFEST.json via `tools/package/regen_manifest.py`; rebuild archive twice, prove byte identity; clean-extraction checks (`check_manifest.py`, `verify/recompute-claims.py`); own leak sweep; red->green on recompute.
4. Report previous shipped archive size (measured, not trusted), new size/sha256/md5/member count, and prove no published number moved (claims, fixture digest `c7696edc…`, 29-file payload).
5. Report-only: other published containers built from this package (e.g. zip under `scratch/ulicfix1/zenodo/`).

## Rules
- Never hand-edit MANIFEST.json.
- No published number / measured value / paper prose change.
- No invented paths, numbers, versions, DOIs.
- No `git` command against any target repo. Write nothing outside declared paths.

## Status
- [ ] JOB 1 source of truth
- [ ] JOB 2 fix + sweep
- [ ] JOB 3 rebuild + prove
- [ ] JOB 4 report new version
- [ ] JOB 5 report-only other containers

## Result (2026-10-19)

### JOB 1 — source of truth
`scratch/ufixman1/build_archive.sh` reads `CIT=scratch/uzenodo2/run2/CITATION.cff` (sha256
`32bee18f…`, 2152 B) plus the 29-file package `scratch/uneutral10/package` (which contains **no**
`CITATION.cff`) plus `papers/encoder-crossover-190/released/README_DEPOSIT.md`. The package CFF does
not exist; the deposit CFF is the canonical build input. Same leaked bytes also sit in
`scratch/uconcept1/v2x/…`; the pre-DOI `56300d7c…` copies (v1x, udoiback1, urepo1) are stale.

Offending lines, verbatim (`CITATION.cff:30-31`):
```
# DOI installed 2026-10-18 (UDOIBACK1) after the author published the deposit on Zenodo.
# CONCEPT DOI installed 2026-10-18 (UCONCEPT1) so this citation survives version bumps:
```

### JOB 2 — fix
Corrected copy `scratch/uencfix1/CITATION.cff` (`91a64a20…`, 2147 B): the two parenthetical unit ids
removed, every fact kept (date 2026-10-18, DOI-then-concept-DOI intent, superseded wording untouched).
No version, date or DOI invented. Post-fix case-insensitive sweep of the clean extraction: unitid 0,
`scratch/` 0, `tools/package/` 0, absolute host paths 0, `/tmp/` 0.

### JOB 3 — rebuild and prove
Control first: the unmodified `build_archive.sh` reproduces the shipped archive byte-for-byte
(159185 B, `196f5311…`). Then `scratch/uencfix1/build_candidate.sh` (same recipe, corrected CFF) built
twice into independent work dirs → `cmp` rc=0, 159182 B, `dbbf7b1a…`. Clean extraction:
`check_manifest.py` five counters 0 / VERDICT PASS / rc=0; `recompute-claims.py` rc=0 /
ALL PUBLISHED NUMBERS REPRODUCED: True / VERDICT PASS / fixture digest `c7696edc…`. Red→green:
flipping one per-case `"correct"` → rc=1 with `0.3474 modernbert-base sealed-190 accuracy …
MISMATCH`; restore → rc=0 PASS. (Flipping the redundant top-level `"accuracy"` field does not fail —
the script recomputes from `perCase`; recorded, not a defect.) Installed archive == installed tree.

### JOB 4 — new version
previous 159185 B / `196f5311…` / `b3b30f66…` → new **159182 B** / `dbbf7b1a…` / `b4dac172…`,
37 tar members / 31 files (unchanged). MANIFEST diff is 4 lines: `counts.bytes_total` 845023→845018,
CITATION sha256+bytes 2152→2147, `manifest_self`; `generated_utc` unchanged. All 28 non-manifest
package files byte-identical; no claim value moved.

### JOB 5 — other containers (report only)
`scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip`: 29 members, **no**
`CITATION.cff`, 0 unit ids — predates the DOI lines, superseded. Other archives clean; the only
regex matches anywhere are the false positive `utf8` in `\usepackage[utf8]{inputenc}` (main.tex:4).
`submission/BUILD_NOTES.md:350` is now stale (records the old 159185 B / `196f5311…`).

### Residual (why status = partial)
`scratch/uzenodo2/run2/CITATION.cff` is outside this unit's declared write paths, so the documented
pipeline still rebuilds the leaked archive; only `scratch/uencfix1/build_candidate.sh` produces the
delivered one. Handoff `next_unit_hint` carries the 3-step follow-up.
