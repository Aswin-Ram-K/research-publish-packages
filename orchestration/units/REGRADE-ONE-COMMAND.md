# REGRADE-ONE-COMMAND — one command that re-derives every published grade

**Status:** done · **Bound:** 30 tool calls · **Live requests:** 0 (OFFLINE) · **Deliverables:** tool,
tests, docs, report table, handoff.

## Purpose

`docs/HARNESS-MAP-V2.md` item 13 ("cross-run regrade is prose, not a command") was open. `TVS-REGRADE`
graded 8 files by hand; `LATENCY-REPORT-2`/`OPERATOR-BRIEF-2` trusted whatever grade sat beside a rows
file. This unit makes the loop executable and provenance-carrying.

## Built

- `experiments/ptr-engine/tools/regrade.py` — rows → fresh grade at
  `measure/regrade/<rows-stem>.grade-v5.json`; never overwrites (exit 4). Records `grader_sha256` +
  `grader_path` in the output and on stdout; `--sha256` pin (exit 3); `--check` dict-wise compare
  ignoring only `generated_at` (exit 1 + differing paths); `--report` table + `measure/REGRADE.json`;
  `--as-of` pins `generated_at` for byte-identical reruns; exit 2 for unreadable input / no grade.
- `experiments/ptr-engine/longrun/tests/test_regrade.py` — 8 tests (a)-(f) plus sha-pin and unreadable-input.
- `docs/REGRADE.md` — example command per figure class, `--check` idiom, named limitation
  (reproduces the grader; not a validator), archaeology.
- `experiments/ptr-engine/measure/REGRADE.json` — report table + provenance + published-grid re-derivation
  + determinism + archaeology.

## Results

- 9 declared long-run grids regraded; **8 existing grade-v5 files `identical`**, 1 (`v6-tools`) `differs`
  in 22 paths because it predates `GRADE-V5-REPAIR` T3 (`arms.pointer-stable.checkpoint_accuracy`
  grade `1/3` → regrade `1/1`; `cp.0.t12` still passes, so tvs 111 994 is unaffected).
- Determinism: two independent pinned runs + production are byte-identical on all 9 grids.
- TVS re-derived from regraded grades: **48 347 / 50 847 / 111 994**, 20 pairs `null/no_verified_success`.
- Quality from grade_v5 checkpoint cells: **3/25 decidable**. Published **5/43** is the `det_verify`
  grid, not grade_v5 — not reproducible by this command.
- Archaeology: **6** rows files have no grade file; **19** grade files are not the current grader sha
  (18 v2/v3/v4 + the pre-T3 v6 v5 grade), 2 more unverifiable (rows gone).
- Red→green: mutating the recorded `grader_sha256` made `--check` exit 1 naming `grader_sha256`;
  restoring it printed `IDENTICAL`.
