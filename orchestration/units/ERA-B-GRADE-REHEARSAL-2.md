# UNIT `ERA-B-GRADE-REHEARSAL-2` — re-run the era-B grading rehearsal against the repaired grader

**Status:** done · **Bound:** 8 tool calls after the first journal row · **Requests:** 0 (offline) · **Date:** 2026-10-26

## Purpose
`ERA-B-GRADE-REHEARSAL` found 50/64 correct era-B answers rejected and set the grid's quality precondition
**false**. `GRADE-V5-T4-DECORATION` then repaired `grade_v5.py` (sha `056eb605…` → `3d70ed1d…`). This unit
asks one question: **do the same 64 correct answers now grade, and do the nine negative controls still
fail?** Same rows, same fixture, same `derive_truth`. Only the grader under test moved.

## Steps
1. Probe: grader sha256, pin's recorded value (stale, expected), old artefact, decoration handoff.
2. Import `grade_v5` (never edit it); `derive_truth(experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json)`
   from the repo root; rebuild the identical 64-row corpus from the derived truth.
3. Grade every row through `parse_answer_contract` → `grade_cell`; keep every verbatim `reason` and every
   `decoration_stripped` fragment.
4. Re-run the nine controls; add six distinction controls and twelve wrong-value mutants (recorded as
   additions, never replacing the nine).
5. Write the new artefact; never overwrite `measure/ERA-B-GRADE-REHEARSAL.json`.

## Result
**50/64 → 64/64.** All three decoration families **now pass** — trailing period on CALL (rule a), trailing
provenance parenthetical on CALL (rule b), `NONE — justification` (rule c). The nine negative controls are
**0/9**; the three previously-green shapes are still 12/12 and `e1`/`g` still 4/4 and 5/5.
**Verdict: `contract_accepts_era_b_correct_answers`** — grid quality precondition 10 is true.

## Proof of distinction
64/64 correct pass; 0/27 wrong answers pass (9 gate controls + 6 added + 12 per-checkpoint mutants). The
repair strips decoration, not value: `call_wrong_value_with_provenance` carries the same `(resolve.py:159)`
the repair strips and still fails `kwarg_value_mismatch:block_size`.

## Not touched
`grade_v5.py`, fixtures, thresholds, `PARM-1*`, grid card, ledger, published pages, `HARNESS-PIN.json`.
The old rehearsal artefact is unmodified (`17e4b6dd…fcc49d1`).

## Write paths
`experiments/ptr-engine/measure/ERA-B-GRADE-REHEARSAL-2.json` · `docs/ERA-B-GRADE-REHEARSAL-2.md` ·
`experiments/ptr-engine/tests/test_era_b_rehearsal_2.py` · `orchestration/units/ERA-B-GRADE-REHEARSAL-2.md` ·
`orchestration/handoffs/ERA-B-GRADE-REHEARSAL-2.json` · `orchestration/journals/ERA-B-GRADE-REHEARSAL-2.jsonl`
