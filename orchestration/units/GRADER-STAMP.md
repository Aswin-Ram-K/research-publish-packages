# Unit GRADER-STAMP

**Status:** done · **Bound:** 22 calls declared (overrun recorded in the handoff) · **Offline:** zero inference.

## Why
`orchestration/handoffs/QUALITY-ERA-TABLE.json` `.evidence.real_output.census`: of **20** `grade_v5`
documents, **9** record a grader sha — all nine are regrade outputs — and the **11 genuinely stored**
grade files record none. Every historical accuracy figure was therefore datable only by re-running the
grader against the rows, which is why `REGRADE-ONE-COMMAND` had to exist before any grid could be trusted.

## What was built (recording only — no grading rule changed)
1. **Stamp on write** — `experiments/ptr-engine/longrun/grade_v5.py`: `GRADER_VERSION = "5.1"`,
   `StampError`, `stamp_document(doc, rows_path, grader_path=None)` writes `grader_sha256` (the grader
   file's own sha256 at write time), `grader_version`, and `rows_sha256`. `main()` stamps **before**
   opening `--out`; on `StampError` it returns **3** and no file is created.
2. **One resolver, no second copy** — `experiments/ptr-engine/tools/grader_identity.py`:
   `grader_identity(document, regrade_result=None) -> {"sha256", "source": "stamp"|"derived", "stamped", …}`.
   `source="stamp"` only when all three fields are present; a historical document reports
   `source="derived"`, `stamped=False`, `sha256=None`, `requires="regrade_result"` until the caller
   supplies the re-derived sha. There is **no lookup table of historical shas**; `file_sha256()` in this
   module is the single sha256 implementation and `grade_v5` imports it (no second copy).
3. **Tests** — `experiments/ptr-engine/longrun/tests/test_grader_stamp.py` (6 tests): fresh document
   carries all three fields and `grader_sha256 == sha256sum(grade_v5.py)`; removal of the stamp is reported
   `derived`/unstamped (and two-of-three is not a stamp); the writer refuses with exit 3 and no file when
   the stamp cannot be computed; **red→green** by running an `/tmp` copy of the writer with the stamp call
   deleted, which emits an undated document and grades the same cells identically. No stored grade file is
   read-modified-written anywhere.

## Evidence
- GREEN: `python3 -m pytest experiments/ptr-engine/longrun/tests/test_grader_stamp.py -q` → `6 passed`.
- RED: `GRADE_V5_MODULE=/tmp/grader-stamp/grade_v5_nostamp.py python3 -m pytest … -q` → `2 failed, 4 passed`
  (`test_fresh_document_carries_all_three_stamp_fields`, `test_writer_refuses_when_stamp_uncomputable`).
- Regression: `test_grade_v5.py` + `test_grade_v5_repair.py` + `test_grader_stamp.py` → `24 passed`.
- Demo document: `grader_sha256=056eb605…f26772` (= `sha256sum grade_v5.py`), `grader_version=5.1`,
  `rows_sha256=797e028e…6260a6` (= `sha256sum` of the rows file); refusal probe → `exit = 3 | file written: False`.
- Resolver: stamped → `stamp True`; stamp removed → `derived stamped=False sha=None requires=regrade_result
  missing=['grader_sha256','grader_version','rows_sha256']`; with a regrade sha → `derived` + that sha.

## Containment
Wrote exactly: `experiments/ptr-engine/longrun/grade_v5.py`,
`experiments/ptr-engine/tools/grader_identity.py`,
`experiments/ptr-engine/longrun/tests/test_grader_stamp.py`, this card, its handoff, its journal, `/tmp/grader-stamp/**`.
No stored `*.grade-v5.json`, no rows file, no `measure/QUALITY-ERAS.json`, no `docs/QUALITY-ERAS.md`,
no `docs/OPERATOR-BRIEF.md`, `cell.py`, `client.py`, `run_longrun.py`, `analyze_stats.py` was touched
(stored grade-v5 files: 11, newest mtime 2026-10-26T10:56:19; all untouched).

## The sentence a later reader can rely on
> stamping is forward-only from this card's sha; the 11 unstamped files remain datable only by re-derivation, as `docs/QUALITY-ERAS.md` already records.

**This card's sha:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3` (HEAD when the stamp was written).
