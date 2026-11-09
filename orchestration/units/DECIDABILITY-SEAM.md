# UNIT `DECIDABILITY-SEAM`

**Status:** done · 2026-10-26 · automated, offline (zero inference requests).

## Purpose

One conductor run graded `decidable = 3` while `analyze_stats` printed
`accuracy UNDECIDABLE (n=0 decidable turns)` for the same rows. Locate the seam, make the decided
population explicit and shared, add a conductor gate, and a regression test that would have caught
it.

## Bound

≤30 tool calls, zero requests; handoff `partial` within 5 calls if the seam could not be located.
Observed: 27 tool calls, 0 requests, handoff `done`.

## Deliverables

| # | task | artifact |
|---|---|---|
| 1 | locate the seam with `path:line` on both sides | `docs/DECIDABILITY-SEAM.md` §2 |
| 2 | accuracy population from graded checkpoint verdicts; `timing_n` / `graded_n` printed | `experiments/ptr-engine/longrun/analyze_stats.py` |
| 3 | stage-7 consistency gate, exit **9**, `--allow-inconsistent` recorded | `experiments/ptr-engine/longrun/cell.py` |
| 4 | regression test, red→green | `experiments/ptr-engine/longrun/tests/test_decidability_seam.py` |

## Write paths used

- `experiments/ptr-engine/longrun/analyze_stats.py`
- `experiments/ptr-engine/longrun/cell.py`
- `experiments/ptr-engine/longrun/tests/test_decidability_seam.py`
- `docs/DECIDABILITY-SEAM.md`
- `orchestration/units/DECIDABILITY-SEAM.md`
- `orchestration/handoffs/DECIDABILITY-SEAM.json`

`grade_v5.py` was NOT edited: the analyser was the wrong side (row-level `answer_kind`, which is
null on every v6 row; the grader parses `content` and collapses rows by turn).

## Evidence

- Seam: `grade_v5.py:608-622` (content fallback), `:630` (one row per turn), `:653`
  (`decidable`) vs pre-fix `analyze_stats.py:415` (`answer_kind != "NUM" → None`) and `:547-549`.
- Rows: 72 rows, `answer_kind` null ×72, `kind=tool-followup` ×24, 3 distinct checkpoint turns.
- New output: `timing_n = 72`, `graded_n = 3`,
  `accuracy = 1/3 (pass 1, fail 2, undecidable 0, missing 0)`.
- Gate: exit 9, `grader decidable=3 (grade_v5.py:653) vs analyser graded_n=0 (analyze_stats.py:457)`;
  `--allow-inconsistent` → exit 0 with `consistency.override = true`.
- Tests: seam 4/4 OK; `test_cell.py` 7/7 OK; `test_analyze_stats.py` 8/8 OK. Red probe (gate call
  removed) → `AssertionError: 0 != 9`.

## Findings handed back

- The analyser was wrong on two counts (empty population column; row count including follow-ups).
- Two published cells carry an accuracy over the wrong population:
  `measure/cell-transcript-grow-20261026T144452Z.md:36` and `…T144540Z.md:36` print `55/64` while
  `grade_v5` graded `3/3` on 3 checkpoints. Withheld as accuracy evidence; historical files left
  untouched.
- `grade_v5.py` was modified by another session at 10:32 during this unit; `cell.py`'s
  `GRADE_DECIDABLE_SRC` points at `grade_v5.py:653` as measured after that change — re-check it if
  `grade_v5.py` moves again.

## Assumptions (no answerer in this session)

- Fixture for the regression cell is `tasks-v5/runtime-v5/LR-01.v5.json`, the fixture the live
  cell recorded (the v6 fixture has a checkpoint with no `answer_spec` and is refused at
  preflight).
- The v6 fixture's `cp.5.t14` underivability is pre-existing and out of scope; recorded, not fixed.
