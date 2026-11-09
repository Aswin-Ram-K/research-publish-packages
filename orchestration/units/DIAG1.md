# DIAG1 — compliance diagnosis (occamy-1.0)

**Unit.** `DIAG1` · offline diagnosis, 3 completions.
**Objective.** Determine why occamy-1.0 answers `ANSWER: NOT-AN-ANSWER` on 45/48 turns.
**Write paths.** `experiments/ptr-engine/measure/rows-compliance-diag-2026-11-08.jsonl`, `orchestration/notes/joint-plan/DIAG1-compliance.md`, `orchestration/units/DIAG1.md`, `orchestration/handoffs/DIAG1.json`.

## Procedure

1. Read one posctrl row: model `occamy-1.0`, max_tokens 4096, thinking off; instruction text = system_prompt answer line.
2. Built R1 (control), R2 (explicit example), R3 (minimal) with identical working set for R1/R2.
3. Sent each once; appended row; read back before next request.
4. Parsed each with `score_longrun.answer_of` and `grade_v5.parse_answer_contract`.
5. Verdict: instruction-wording defect (refusal token not a contract kind).

## Verification

- 3 rows on disk in `rows-compliance-diag-2026-11-08.jsonl`.
- R1 parsed NUM 64; R2 parsed NUM 64; R3 prose_only.
- Cap accounting: 2639 → 2642 (cap 12094).
