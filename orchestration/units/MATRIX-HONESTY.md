# MATRIX-HONESTY — an absent cell must never look like a failed one

**Unit:** MATRIX-HONESTY · **Requests:** 0 (offline) · **Bound:** ≤32 tool calls.
**Why:** REGRADE-DET graded the whole on-disk record as 5 pass / 38 fail / 36 missing /
13 undecidable over 92 cells; HARNESS-MAP recorded the same gap as inefficiency #3
("answerless acceptance: 36/92 missing"). A missing cell and a failed cell differ by nothing a
reader can see, and every headline rate silently changes its denominator depending on which it is.

## What was built

1. **Declared-cell inventory, derived independently.** A cell is
   `(rows_file, arm, checkpoint_id, rep)`: `rows_file` = every `rows-longrun-*.jsonl` whose rows
   carry fixture `task_id` = LR-01; `arm` = arms actually present in that file's rows;
   `checkpoint_id` = the fixture's 3 checkpoints (turns 12/24/46) plus `repair.at_turn` = 30;
   `rep` = 1. **92 = 23 run/arm pairs × 4 checkpoint ids × 1 rep.** Sub-grid probe files
   (`rows-cell-*`, `rows-pilot-*`) are excluded; including them would add 8 cells, all
   `missing_turn_absent`, changing no pass, no fail and no denominator.
2. **`experiments/ptr-engine/tools/matrix_audit.py`** — one state per declared cell with a
   machine-readable reason, using `det_verify` (imported, not re-implemented) as the only judge.
   States: `pass`, `fail`, `missing_row_absent`, `missing_turn_absent`,
   `missing_answer_empty`, `missing_checkpoint_absent`, `undecidable`. Writes
   `measure/MATRIX-COVERAGE.json` (92 cell entries, per-state and per-arm counts) and prints an
   `arm × state` table with totals.
3. **Denominator rule.** Every printed accuracy is
   `label passed/decidable (pass P, fail F, missing M, undecidable U)` with
   `decidable = pass + fail`, and a trailing `– PARTIAL GRID` marker whenever `M + U > 0`.
   `--strict` exits 1 when any cell is `missing_*`.
4. **`docs/MATRIX-COVERAGE.md`** — the declared-cell derivation, per-arm state counts, and the
   old-vs-corrected restatement of RUN-C-V2 "all four arms 0/3", V6 "1/3" and REGRADE-DET
   "5 pass / 92".
5. **`longrun/experiments/ptr-engine/longrun/tests/test_matrix_audit.py`** — 11 tests: green run over the real grid (exit 0
   without `--strict`); crafted grid with one cell removed → that cell is
   `missing_turn_absent`, counts shift by exactly one, line gains `– PARTIAL GRID`; `--strict`
   non-zero on the incomplete grid and zero on the complete one; a graded `undecidable` cell is
   never counted as pass or fail.

## Measured result

| arm | pass | fail | row-absent | turn-absent | answer-empty | cp-absent | undecidable | total |
|---|---|---|---|---|---|---|---|---|
| lease-reopen | 0 | 6 | 0 | 8 | 0 | 0 | 2 | 16 |
| pointer-stable | 5 | 14 | 0 | 8 | 3 | 0 | 6 | 36 |
| transcript-compact | 0 | 6 | 0 | 8 | 0 | 0 | 2 | 16 |
| transcript-grow | 0 | 12 | 0 | 5 | 4 | 0 | 3 | 24 |
| **TOTAL** | **5** | **38** | **0** | **29** | **7** | **0** | **13** | **92** |

`overall 5/43 (pass 5, fail 38, missing 36, undecidable 13) – PARTIAL GRID`.

Newly visible: the 36 "missing" cells split into 29 `missing_turn_absent` (batch stopped before
the turn) and **7 `missing_answer_empty`** (row exists, `content` empty) — the second cause was
invisible in the old single "missing" bucket.

## Red → green

Reverting the audit's classification to fold `missing_*` into `fail` and dropping the partial-grid
marker makes **7 of 11** tests fail, with the regressed line printed as
`overall 5/79 (pass 5, fail 74, missing 0, undecidable 13)` and
`test_states_partition_the_grid: 74 != 38`. Restored: **11 passed**.

## Containment

Read-only on every existing matrix, grade and row file (`git status` shows no modified tracked
file under `measure/`). Only the four declared new artifacts were written. No request was made.
