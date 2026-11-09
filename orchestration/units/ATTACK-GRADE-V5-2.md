# UNIT `ATTACK-GRADE-V5-2` — second, disjoint attack on the repaired `grade_v5`

**Card** `751d5f3e-a234-436f-95c6-44d3f53ed9bc` · execution `8b763d0b-69ea-49cf-8c17-6eac62e05240`
**Gate** `GRADE-V5-REPAIR` `c470ff85-7953-47e6-a6b4-2ee02a3016ac` — verified settled (`done`,
execution `31c83a58` result `succeeded`, endedAt 1793029316644) before any probing.
**Mode** automated, offline: 0 inference requests, 0 network calls, hand-written strings only.
**Role** attacker — read the grader, do not edit it.

## Objective
A repair tested only against the probes that found the bug is a fit to those probes. Build a corpus
that reuses none of the first 41 probes and check whether the three repairs hold on adversaries a
repair typically breaks on; re-run the 41 and build a regression table; report FN and FP separately
with denominators; attack the row-trust repair directly; re-derive the three old defects; state a
verdict.

## Bound
≤30 tool calls, zero requests, handoff `partial` within 5 calls if needed, journal first.

## Write paths (exactly)
`experiments/ptr-engine/tools/attack_grade_v5_2.py`,
`experiments/ptr-engine/measure/ATTACK-GRADE-V5-2.json`,
`docs/ATTACK-GRADE-V5-2.md`,
`orchestration/units/ATTACK-GRADE-V5-2.md`,
`orchestration/handoffs/ATTACK-GRADE-V5-2.json`,
`orchestration/journals/ATTACK-GRADE-V5-2.jsonl`.

## Forbidden (honoured)
No edit to `grade_v5.py`, `attack_grade_v5.py`, any fixture/row/grade file, `cell.py`,
`run_longrun.py`, `client.py`, `analyze_stats.py`, `matrix_audit.py`, `det_verify.py`,
`handoff_lint.py`. Only imports and reads. No git, no network.

## Method
Own temp fixture (`RETRY_CEILING = 64`, `_decline()` with the real `record_refusal` call, `_quiet()`
naming it in a docstring only), absolute `sources` paths, truth via `grade_v5.derive_truth`. Probes
graded through `parse_answer_contract` + `grade_cell`; row probes through the real `grade_rows`.
Old corpus re-run from `attack_grade_v5`'s fixture and diffed against `measure/attack-grade-v5.json`.

## Result
45 new probes + 10 row probes, 0 exact string reuse. Own FN **0/16**, FP **0/27**, omissions
rejected 8/8; combined FN **0/24**, FP **0/48 corrected**; 41 old probes: **0 changes**; T1 fixed,
T2 fixed, T3 **partially fixed** (`multiple_answer_lines` still lands in `decidable`, `N42`).
Verdict `pass` on the card's bar, one open residual defect named.

Full report: `docs/ATTACK-GRADE-V5-2.md`. Measurement: `measure/ATTACK-GRADE-V5-2.json`.
