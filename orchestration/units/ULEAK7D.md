# ULEAK7D — the name neutralisation, applied, and every release document made true

**Status:** DONE. Parent decision applied (equal-length swap), not re-litigated.

## JOB 1 — reused, not re-derived
`scratch/uleak7c/consexp` + `ULEAK7C.json`: the chosen replacement is **CORPUSFILE** (10 chars) for
**CONSONANCE** (10 chars). Equal length is the point: a shorter replacement would change the file's
published byte count (2,267,742) and line count (9,260) quoted in the package README, `CLAIMS.md`
and `README_DEPOSIT.md`. Confirmed on my own run: equal-length swap leaves the file at exactly
2,267,742 B / 9,260 lines. The 7c experiment had swapped **only the rows**; the one prose occurrence
at `results/GATED_READ_2026.md:327` ("a Consonance artefact") was still live, so its replacement
(`Corpusfile`, case-matched) is this unit's choice.

## JOB 2 — applied
Rows: 436 -> `CORPUSFILE` (`tag` 206, `file` 206, `staged[]` 3, `hit[]` 1, `paths[]` 17; the corpus
paths `<NAME>.md`, `docs/<NAME>_PLAN.md`). Prose: 1 -> `Corpusfile`.
- **2,267,742 bytes / 9,260 lines** — unchanged. Report **23,591 B / 340 lines** — unchanged.
- Old string **0 in every case form** across package, installed payload, fresh extraction and the paper.
- `verify/recompute-claims.py`: **49/49, VERDICT PASS**. All five `calls[]` lines and the R5 group
  (15.279 ratio; exposure 0-of-20 `stage_route`, selfselect 20) are byte-identical to the pre-state log.

## JOB 3 — documents made true
- package `README.md`: provenance paragraph rewritten from "same source bytes except six R5 answer
  values" to a complete, explicit list of the two files changed and everything that was **not**;
  pass-3 dated note added; the pass-0 cut-ladder `[FAIL]` illustration labelled as recorded output.
- `GAPS.md` **G-23** now reads CLOSED, with the original wording kept as dated history.
- `CLAIMS.md` claim R: pass-3 dated note, superseded digests kept.
- `README_DEPOSIT.md`: added a bounded-difference disclosure (it ships; a reader deserves to know).
- `DISCLOSURE_CHANGES.md`: Pass 6 appended; three sweep-pattern lists that spelled the name out were
  rewritten to describe it, because reproducing the pattern re-introduced what it policed.
- No other document repeated the old claim (`ULEAK7B.md:104-105` is outside this unit's write paths).

## JOB 4/5 — digests, rebuild, re-proof
Rows md5 `20727b5c6bed2db935c14bf2e076340f` / sha256 `184ab747e87f7d127005ce08316dcde640ae93e5278bb1bd57bf353e23d9c44f`;
report md5 `2df66834d3a54bee28da9b78d63855cb` / sha256 `c5a054030905944ca5e79ea27ed1310d9fb0ee91a0ba03559a077a87b2e1246d`.
MANIFEST regenerated with `tools/package/regen_manifest.py` (never hand-edited). Pins re-pinned.
**Archive: 128,559 B, sha256 `1e3b5781463772fecd8562cd2be20bed14488fa13761d5c8797fe7826f38827c`, md5 `5c0db7c9afedf5d47747c70e03e8a136`** —
changed again from 127,300 B / `1cfbd15b…` / `8e66f192…`. Two full builds byte-identical.
check_manifest five counters 0 / PASS / exit 0; recompute 49/49 / PASS / exit 0; red->green: flip one
byte -> exit 1 `[FAIL] rows_sha256 published='184ab747e87f7d12' recomputed='cfcd43ec32409489'`, restore -> exit 0, original digest.

## JOB 6 — stale intermediates: neutralised in place + marked stale
`scratch/upkg7b/clean/` and `scratch/upkginstall7/verify/extract/` were neutralised in place and each
got a `STALE.md`. `build_archive.sh` (read in full) reads only `$PKG` and `$META`, so no build ever
picked them up; `verify/extract/` was additionally re-extracted from the new archive so it is current.

## Disagreements / limits
1. The card said "one in prose at `results/GATED_READ_2026.md:327`" — correct, and it was **not** part
   of the 7c experiment, so it is this unit's swap.
2. The paper's `duval` (14) / `/home/zer0null` (13) / internal-unit-id (62) hits are **pre-existing**,
   concentrated in `DISCLOSURE_CHANGES.md` (the change log explicitly "flagged, not scrubbed" in
   pass 2) and in dated notes; the name pattern is now zero but these are outside the card's scope.
3. `orchestration/units/ULEAK7B.md:104-105` still carries only the compressed delta (outside write paths).
4. First build of this pass (128,562 B / `2fb88b4c…`) was discarded: it shipped an internal unit id
   (`ULEAD1`) in the package README, which this unit had introduced. Fixed; final build is the one above.
