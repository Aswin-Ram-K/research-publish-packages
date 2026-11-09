# UNIT `QUALITY-CARRY-FORWARD`

**Status:** done. **Bound:** 24 tool calls (used 18, including journal and handoff). **Offline:** zero requests, no sockets.

## Purpose

Put era A's quality verdict on the record in one additive place, recomputed from its own artefacts, and name the pages that must cite it. `orchestration/handoffs/MODAL-ANSWER-ACCURACY.json` measured what era A's answers were and its hint required the carry-forward numbers be appended to the QUALITY record from a unit whose write paths include it; MODAL-ANSWER-ACCURACY was barred from every QUALITY/TVS/PARM-1 path.

## Write paths (exactly, all additive)

- `experiments/ptr-engine/tools/quality_carry_forward.py`
- `experiments/ptr-engine/tests/test_quality_carry_forward.py`
- `experiments/ptr-engine/measure/QUALITY-CARRY-FORWARD.json`
- `docs/QUALITY-CARRY-FORWARD.md`
- `orchestration/units/QUALITY-CARRY-FORWARD.md`
- `orchestration/handoffs/QUALITY-CARRY-FORWARD.json`
- `orchestration/journals/QUALITY-CARRY-FORWARD.jsonl`

No existing artefact, page, threshold, `PARM-1*`, grader, fixture or rows file was edited.

## Method

Every figure is re-derived at recompute time by `quality_carry_forward.py`, from the file in its `source_path` column, with that file's sha256 stored beside it:

- counterfactual grades: summed over `MODAL-ANSWER.json` `grids[*].arms[*].counterfactual_grades`, never read from `counterfactual_totals` (a mismatch is recorded as drift);
- observed passes: recomputed from `observed[*].verdict` and compared to `tables.observed_passes`;
- distinct answers: `rows-longrun-c-2026-10-26.jsonl`, turn rows only, `content` stripped / whitespace-collapsed / casefolded (the MODAL-ANSWER normalisation);
- invitation: `longrun/tasks-v6/LR-01.v8.json`, `.py`-path regex on each question, cross-checked against `GRID-SHAPE.json` `fixture.*`;
- QUALITY: `QUALITY-ERAS.json` `pairs[*].current_grader`, checked against its `headline.current_grader`.

## Recomputed figures (all reproduced; no figure failed)

| figure | value | denominator | source |
|---|---|---|---|
| counterfactual modal passes, worst arm | 0 | 12 | `measure/MODAL-ANSWER.json` |
| counterfactual modal passes, all groups | 0 | 348 | `measure/MODAL-ANSWER.json` |
| NONE-kinded ids, counterfactual | 0 | 3 | `measure/MODAL-ANSWER.json` |
| observed passes | 3 | 29 groups | `measure/MODAL-ANSWER.json` |
| observed passes that are modal | 0 | 3 | `measure/MODAL-ANSWER.json` |
| NONE-kinded ids, observed | 1 | 3 | `measure/MODAL-ANSWER.json` |
| distinct answers | 48 / 46 / 33 / 9 | 48 turns | `measure/rows-longrun-c-2026-10-26.jsonl` |
| turns inviting a read | 46 | 48 | `longrun/tasks-v6/LR-01.v8.json` |
| turns naming `@knowledge:` / `read_file` | 0 / 0 | 48 | `longrun/tasks-v6/LR-01.v8.json` |
| era-A grade_v5 grid | 3 | 25 | `measure/QUALITY-ERAS.json` |

**One reading distinction, recorded rather than smoothed:** the hint's *"NONE 0 of 3"* reproduces as the **counterfactual** figure. The **observed** NONE count is 1 of 3 (`cp.7.t20`, `none_confirmed_absent_in_source`). Both are in the record as separate ids so a reader cannot mistake one for the other.

## Guard

`--check` exits 1 on any figure whose `value`, `denominator`, `source_path` or `source_sha256` differs from a fresh recomputation, on moved citation lines, on a statements block missing either sentence, and on an attribution digest that no longer matches its source. Green: shipped record, exit 0. Red: `/tmp` copy with `distinct_answers.transcript-grow` 33 → 34, exit 1, `DRIFT distinct_answers.transcript-grow.value: recorded 34 != recomputed 33`.

## Assumptions (automated session, no answerer)

- The card names `docs/OPERATOR-BRIEF-4.md` and `docs/OPERATOR-BRIEF-5` as citation targets; neither file exists in this tree. The operator contract lives at `docs/OPERATOR-BRIEF.md:18` and `:85`, which are in `needs_citation`; the absent pages are listed under `missing_pages` rather than invented.
- `tests/test_quality_carry_forward.py` is written under `experiments/ptr-engine/tests/`, where the ptr-engine suite lives (there is no top-level `tests/` in this tree).

## Result

QUALITY record now carries, in one place with digests and a drift gate: era A's checkpoint answers are **0/12 under the modal-answer reading**, 3 observed passes across 29 groups, all one-arm and none modal; 46/48 turns invited a read the arm could not perform.
