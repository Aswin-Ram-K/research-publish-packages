# UENCFIX2 — install corrected CFF source, re-pin build, prove reproduction, refresh stale record

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Bound:** 12 tool calls. If a step cannot be established in 3 attempts → STOP, report unverified.
**Write paths:** `scratch/uzenodo2/**`, `scratch/uconcept1/**`, `scratch/ufixman1/**`,
`papers/encoder-crossover-190/**`, `scratch/uencfix2/**`, `orchestration/units/UENCFIX2.md`,
`orchestration/handoffs/UENCFIX2.json`.

## Premise (from UENCFIX1)
Corrected deposit: 159,182 B, sha256 `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877`,
md5 `b4dac172003233d7d6c8c78c909b5594`, 37 tar members / 31 files. Corrected CFF:
`scratch/uencfix1/CITATION.cff` 2,147 B sha256 `91a64a20…`, unit ids removed.
Defect: `CITATION.cff:30-31` leaked `UDOIBACK1`, `UCONCEPT1` into a published archive.

## Jobs
1. Verify premise on disk (shipped archive, corrected CFF, leaked run2 CFF, build script `CIT=`).
2. Install corrected CFF over `scratch/uzenodo2/run2/CITATION.cff` (+ `scratch/uconcept1/v2x/` if it
   holds the same leaked bytes); preserve mode; report before/after digest each.
3. Re-pin `want_cit` to `91a64a20…` in `scratch/ufixman1/build_archive.sh`; remove/narrow only the
   byte-equality assertion against the superseded shipped file; input guards stay.
4. Fresh build into scratch dir must produce 159,182 B / `dbbf7b1a…`.
5. `papers/encoder-crossover-190/submission/BUILD_NOTES.md:350` — dated note with current figures,
   old value kept as dated history, nothing else changed.
6. Report upload candidate: path, size, sha256, md5, member count; 0 occurrences of either unit id;
   28 non-manifest payload files byte-identical to previous version.

## Status
DONE (2026-10-19)

## Result — 2026-10-19 (all six jobs done)
- JOB 1 premise TRUE: shipped 159,182 B / `dbbf7b1a…` / md5 `b4dac172…` / 37 members / 0 id hits;
  `scratch/uencfix1/CITATION.cff` 2,147 B / `91a64a2081…` / 0 hits; `scratch/uzenodo2/run2/CITATION.cff`
  leaked 2 hits at 2,152 B / `32bee18f…`; `build_archive.sh:31` pointed `CIT=` there.
  `scratch/uconcept1/v2x/CITATION.cff` does not exist (nothing to fix).
- JOB 2 installed: run2 CITATION.cff 32bee18f… (2,152 B) -> 91a64a2081… (2,147 B), mode 664 unchanged.
- JOB 3 patch: want_cit -> 91a64a20…; byte-equality gate against the shipped file narrowed to advisory
  (`cmp -s` + report, no exit 1); input guards (package 29 files, front-matter pin) untouched.
- JOB 4 fresh build from corrected source, BUILD_WORK=scratch/uencfix2/w, GENUTC=2026-10-19T04:14:50Z
  (read from the shipped MANIFEST): 159,182 B / dbbf7b1a… / md5 b4dac172… / 37 members; cmp IDENTICAL.
- JOB 5 BUILD_NOTES.md:350 got one dated UENCFIX2 note; 159,185 B / 196f5311… kept as dated history.
- JOB 6: upload candidate = papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz,
  version 3 of concept DOI 10.5281/zenodo.23463944; 0 occurrences of either unit id (case-insensitive);
  28 non-manifest payload files byte-identical to the previous version's members.
