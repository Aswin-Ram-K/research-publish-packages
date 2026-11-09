# UNIT ANSWER-DEGENERACY-ERA-A — answer repetition per arm and per cell

**Card:** d45914e7-4178-4d92-b41d-15aa62b0cd65 · **Execution:** b0a8c727-be26-4888-9ae2-d0c03455483f
**Date:** 2026-10-26 · **Live requests:** 0 (offline, zero sockets) · **Tool calls used:** 13 of 22 · **Journal-first:** yes

## Objective
Measure repetition of answers per arm and per cell across every rows file, define the measure before computing it,
answer what repetition does to H3's denominator, and record it additively without touching any published number.

## Write paths (exactly, as declared)
- `experiments/ptr-engine/measure/ANSWER-DEGENERACY.json`
- `docs/ANSWER-DEGENERACY.md`
- `orchestration/units/ANSWER-DEGENERACY-ERA-A.md`
- `orchestration/handoffs/ANSWER-DEGENERACY-ERA-A.json`
- `orchestration/journals/ANSWER-DEGENERACY-ERA-A.jsonl`

## Measure (frozen before computation, reproduced in both artifacts)
Turn row = `kind` absent or `"turn"` (`tool-followup` excluded). Non-empty = normalised text non-empty.
Normalisation = strip, collapse whitespace runs to one space, case-fold. NOT normalised: numerals, punctuation,
code fences, tags, `ANSWER:` prefix. Distinct = |set of normalised non-empty answers|. Largest group = biggest
set of turns sharing one identical normalised answer. Grid = one rows file; cell = `(task_id, rep)`.

## Headline counts
- `rows-longrun-c-2026-10-26.jsonl`: 192 turn rows, 48/arm; distinct = `pointer-stable` 48, `lease-reopen` 46,
  `transcript-grow` 33, `transcript-compact` 9 (largest group 16) — reproduces TURN-DEDUP-RECONCILE exactly.
- `rows-longrun-2026-10-26.jsonl`: distinct 39 / 12 / 13 / 1 with 48 turns/arm.
- Checkpoint turns `{6,8,12,14,18,20,24,26,32,36,42,46}`: in `rows-longrun` and `rows-longrun-c`, **0 of 12**
  ANSWER lines in every arm (H3 denominator 0, absence not repetition). In `rows-longrun-v3`/`-v4`,
  `transcript-grow` has 12/12 ANSWER lines reducing to **1 distinct string** (same answer 12 times);
  `pointer-stable` 9/12 and 8/12 with 4 distinct strings and 7/6 repeated.
- 16 rows files, 1177 raw rows / 1109 turn rows, 0 unparseable; 2 files have no assistant-content field.

## What grade_v5 can / cannot distinguish
Can: absent (`undecidable`, reason `no_answer_line` / `prose_only`) vs wrong (`fail`, reason `num_mismatch`,
`callee_mismatch`, `kwarg_set_mismatch`, `kwarg_value_mismatch:%s`, `kind_mismatch:%s_expected`,
`answer_not_contract:<err>`) vs missing (`turn_missing`). Cannot: repetition — no reason token names a value,
a modal answer, or a previous turn.

## Deliberately not done
No re-grade, no grade file read, no rows file touched, no TVS/latency page touched. Contradictions would have been
listed as `file:line` and left unedited; none were found (the `MATRIX-COVERAGE` 4-id vs `PREREG` 12-id split is
pre-existing and already recorded in `docs/PARM-1-ERRATA.md`).
