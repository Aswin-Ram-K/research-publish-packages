# UNIT `ERA-B-GRADE-REHEARSAL` — prove the grader accepts a correct era-B answer, and still rejects wrong ones

**Status:** done · **Bound:** 20 tool calls (used 14) · **Requests:** 0 (offline, zero sockets, no live endpoint) · **Date:** 2026-10-26

## Purpose
`MODAL-ANSWER-ACCURACY` (PASS `f17663d1`) showed era A's quality record is 0/12 for every arm under the
modal reading: the arms never emitted a contract `ANSWER:` line. Era B (tools serviced at checkpoint
turns) fixes the **channel**. This unit checks the **other half**: that `grade_v5` accepts an answer that
is correct **and** shaped the way era B will emit it — tool-narration-then-answer, two-line, reordered
kwargs, trailing period, trailing provenance citation — and still rejects wrong answers. If it does not,
the 1,016-request grid manufactures a fifth zero.

## Method
1. **Truth:** `grade_v5.derive_truth(experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json)` — no typed
   table. Run from the repo root (the `call_at_line` spec's `file` is repo-relative).
2. **Corpus:** one correct answer per checkpoint id in eight shapes (`a` canonical, `b` + period, `c`
   two-line, `d` tool narration, `e1` reordered CALL, `e2` reordered + provenance appended, `f` NONE +
   em-dash justification, `g` NUM + citation) — 64 rows, every one asserting the derived truth.
3. **Grading:** `grade_v5.parse_answer_contract` → `grade_v5.grade_cell`. Nothing re-implemented;
   `grade_v5.py` not edited.
4. **Controls:** 9 wrong answers (wrong number, wrong callee, wrong kwarg value, truncated CALL, truncated
   NUM, prose-only wrong value, three NONE-by-naming-a-call).

## Results
- Grader loaded: `experiments/ptr-engine/longrun/grade_v5.py`, sha256 `056eb605…f26772` (matches the
  card), `GRADER_VERSION 5.1`.
- 12 ids: **NUM 5** (`cp.2.t12` 64, `cp.4.t18` 6, `cp.6.t24` 31, `cp.7.t26` 5, `cp.8.t32` 2) ·
  **CALL 4** (`cp.0.t06`, `cp.1.t08`, `cp.9.t36`, `cp.11.t46`) · **NONE 3** (`cp.3.t14`, `cp.5.t20`,
  `cp.10.t42`).
- **50 / 64 correct rows pass.** `a` 12/12, `c` 12/12, `d` 12/12, `e1` 4/4, `g` 5/5. The era-B turn
  shape (narration line, then `ANSWER:`) is accepted at **all 12** checkpoints.
- **14 correct rows do not pass:** `e2` 0/4 (`kwarg_value_mismatch:block_size`, `…:code`,
  `answer_not_contract:call_arg_not_kwarg:) (resolve.py:163`), `b`-on-CALL 4 fail
  (`answer_not_contract:call_not_parsable`), `b`-on-NONE 3 `undecidable` (`unparseable`), `f` 3 fail
  (`answer_not_contract:trailing_after_none`).
- **0 of 9 negative controls passes.** Two are `undecidable` by design (`empty_num`, `prose_only`, the
  repair-T3 rule) — not passes.

## Verdict
`contract_rejects_correct_era_b_answer` — **the grid's quality precondition fails.** `e2` and `b` are
grader-rule problems (the fixture allows a citation after the value and NUM already strips one; CALL/NONE
do not), `f` is a fixture-wording problem. Named fixes, not applied: citation/period stripping in
`experiments/ptr-engine/longrun/grade_v5.py`; the NONE allowance in the v8 fixture `system_prompt`.

## Write paths
`orchestration/units/ERA-B-GRADE-REHEARSAL.md` · `orchestration/handoffs/ERA-B-GRADE-REHEARSAL.json` ·
`orchestration/journals/ERA-B-GRADE-REHEARSAL.jsonl` · `measure/ERA-B-GRADE-REHEARSAL.json` ·
`docs/ERA-B-GRADE-REHEARSAL.md` · `tests/test_era_b_grade_rehearsal.py`

## Not touched
`grade_v5.py`, `analyze_stats.py`, `cell.py`, `run_longrun.py`, any fixture, any threshold, `PARM-1*`,
any published page. No repair attempted; that is `GRADE-V5-REPAIR`.
