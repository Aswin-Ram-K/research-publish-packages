# QUALITY carry-forward: era A's answers, recomputed

**Unit** `QUALITY-CARRY-FORWARD`. **Additive**: this page and `measure/QUALITY-CARRY-FORWARD.json` are new; no existing artefact, page, threshold, grader, fixture or rows file was edited.

`orchestration/handoffs/MODAL-ANSWER-ACCURACY.json` measured what era A's answers actually were, and its hint named the gap: the numbers had to be appended to the QUALITY record from a unit whose write paths include it. This is that place. Every figure below was re-derived at recompute time from the artefact in its `source` column; none was copied from a prior report.

Recomputed at `2026-10-26T19:34:03+00:00`. Era: *era A = tools off (no read_file serviced), per MODAL-ANSWER.json population.era_a_definition*. Rows population: 11 rows files, 889 turn rows; era-B (tools-on) rows files excluded with reasons recorded in the JSON.

## Figures

| figure | value | denominator | source | sha256 |
|---|---|---|---|---|
| `counterfactual_modal_pass_per_arm` | **0** | 12 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `counterfactual_modal_pass_total` | **0** | 348 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `none_id_counterfactual_pass` | **0** | 3 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `observed_pass_total` | **3** | 29 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `observed_passes_that_are_modal` | **0** | 3 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `none_id_observed_pass` | **1** | 3 | `experiments/ptr-engine/measure/MODAL-ANSWER.json` | `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb` |
| `distinct_answers.pointer-stable` | **48** | 48 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `distinct_answers.lease-reopen` | **46** | 48 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `distinct_answers.transcript-grow` | **33** | 48 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `distinct_answers.transcript-compact` | **9** | 48 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `distinct_answers` | **48/46/33/9** | 48 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `turns_with_path_read_invitation` | **46** | 48 | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` |
| `turns_with_at_knowledge` | **0** | 48 | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` |
| `turns_with_literal_read_file` | **0** | 48 | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` |
| `era_a_grade_v5_pass` | **3** | 25 | `experiments/ptr-engine/measure/QUALITY-ERAS.json` | `6d75159e21e3c8233cc842e59277fd67b39dd19accc2654c59db2265fe5046d8` |

Reading the four that matter:

- **The modal-answer reading is 0/12 in every arm.** Every one of the 29 era-A grid/arm groups has 12 counterfactual checkpoint grades and none passes: 0 of 348. The `NONE`-kinded ids (`cp.5.t14`, `cp.7.t20`, `cp.11.t42`) are 0 of 3 under the same reading. The hint's *"NONE 0 of 3"* reproduces as a **counterfactual** figure; the **observed** NONE count is 1 of 3 (`cp.7.t20`, reason `none_confirmed_absent_in_source`) and is recorded separately as `none_id_observed_pass` so the two readings cannot be confused.
- **The observed passes are three, all in `pointer-stable`, and none is modal.** 3 of 29 groups; `observed_passes_that_are_modal` is 0 of 3. Two are `cp.0.t12` `num_equal` in different rows files; one is the single observed `NONE` pass.
- **Distinct answers per arm in one grid**: 48/48, 46/48, 33/48, 9/48 for pointer-stable / lease-reopen / transcript-grow / transcript-compact. High distinctness is not correctness — the arm that emitted 48 different answers scored 3 observed passes.
- **46 of 48 turns invite a read** (questions name a `.py` path; turns 30 and 48 do not), `@knowledge:` appears in 0 of 48 questions, literal `read_file` in 0 of 48. The instrument asked the arm for a read it could not perform; the answer is then measured as an answer.

The QUALITY record this is appended to is the era-A `grade_v5` grid: **3/25 = 12.0 %** (pointer-stable 3/10; its stored 3/27 = 11.1 % form is withdrawn, source `docs/QUALITY-ERAS.md`). That numerator is three passes, all in pointer-stable — the same arm and the same count as the three observed passes recorded here, though this unit did not assert cell-by-cell identity between the two instruments.

## Statements carried verbatim (attributed)

> era A's checkpoint answers are answer-production measurements under an instruction to read sources the arm could not read (46 of 48 turns in v5/v6/v7/v8 invite a read; `@knowledge:` 0/48, literal `read_file` 0/48)

Attribution: unit **MODAL-ANSWER-ACCURACY**, `experiments/ptr-engine/measure/MODAL-ANSWER.json`, sha256 `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb`, figures `turns_with_path_read_invitation`, `turns_with_at_knowledge`, `turns_with_literal_read_file`. quoted verbatim from the MODAL-ANSWER-ACCURACY handoff hint; figures re-derived here from the fixture.

> under the modal-answer reading every arm scores 0/12; the three observed passes are one-off, one-arm, and none is the arm's most frequent answer.

Attribution: unit **MODAL-ANSWER-ACCURACY**, `experiments/ptr-engine/measure/MODAL-ANSWER.json`, sha256 `b8cb6e790fdb57f1f6c2c06a08d46e2026e8080eed2855d308c1c1fb8cb795bb`, figures `counterfactual_modal_pass_per_arm`, `observed_pass_total`, `observed_passes_that_are_modal`. quoted verbatim from the MODAL-ANSWER-ACCURACY handoff hint; 0/12 and the three one-off passes re-derived from MODAL-ANSWER.json.

## What this does NOT say

- It does not say era A's arms are equally good. It says the instrument could not separate them on this measure.
- It does not license differencing era B against era A.

Concretely: era A's arms are **not** shown to be equally good. The instrument could not separate them on this measure, because the measure asks for answers to questions whose source was unreachable for every arm. Nothing here licenses subtracting era A from era B (tools-on) — era B answers a question era A could not, so the difference is instrument, not treatment.

## Pages that must now cite this (named, not edited)

| page | current wording | figures it must carry |
|---|---|---|
| `docs/OPERATOR-BRIEF.md:18` | \| **H3** quality \| lose no more than 2 of 12 checkpoints (**16.7** pp), veto at b+c ≥ 6, either arm < 8 of 12 decidable → no verdict (`docs/PREREG-ARM-RUN.... | `counterfactual_modal_pass_per_arm`, `none_id_counterfactual_pass` |
| `docs/OPERATOR-BRIEF.md:85` | 3. Pointer-stable ≥ 8 of 12 decidable and losing > 2 checkpoints → H3 veto kills the latency win | `counterfactual_modal_pass_per_arm` |
| `orchestration/STATUS.md:392` | - **H3 quality — not evaluable at this n.** `OPERATOR-BRIEF.json` `hypotheses.H3_quality.min_decidable_to_verdict` is *"8 of 12"*; `docs/PARM-1-ERRATA.md:223... | `counterfactual_modal_pass_per_arm`, `distinct_answers` |
| `orchestration/STATUS.md:394` | **The missing measurement:** one four-arm grid with ≥ 60 usable timings per arm. **Do not** read the batch aggregate (134 rows: PASS / FAIL / partial / autho... | `era_a_grade_v5_pass` |
| `docs/QUALITY-ERAS.md:19` | that grid reads **3/27 = 11.1 %** as recorded and **3/25 = 12.0 %** when every pair is put through the current | `era_a_grade_v5_pass` |
| `docs/QUALITY-ERAS.md:63` | \| as recorded on disk \| **3/27** \| 11.1 % \| 3/12 \| 0/3 \| 0/6 \| 0/6 \| | `era_a_grade_v5_pass` |
| `docs/QUALITY-ERAS.md:64` | \| all pairs under the current grader \| **3/25** \| 12.0 % \| 3/10 \| 0/3 \| 0/6 \| 0/6 \| | `era_a_grade_v5_pass` |
| `docs/QUALITY-ERAS.md:73` | `grade_v5.py`. The `grade_v5.py` grid, if quoted at all, is **3/25 = 12.0 %** (pointer-stable 3/10) and its | `era_a_grade_v5_pass`, `counterfactual_modal_pass_per_arm` |
| `docs/GRID-SHAPE.md:61` | **Counts.** 46/48 turns invite a read. **All 12 checkpoint turns invite a read** | `turns_with_path_read_invitation`, `turns_with_at_knowledge` |
| `docs/GRID-SHAPE.md:64` | on a tool-inviting turn**; 0/12 sit on a turn that does not. | `counterfactual_modal_pass_per_arm` |

Absent contract pages the card named: `docs/OPERATOR-BRIEF-4.md` (absent) — no such file in this tree at recompute time; the operator contract lives at docs/OPERATOR-BRIEF.md:18 and :85, which are listed in needs_citation; `docs/OPERATOR-BRIEF-5.md` (absent) — no such file in this tree at recompute time; same substitute as OPERATOR-BRIEF-4.md.

## Guard

`experiments/ptr-engine/tools/quality_carry_forward.py --check` exits **1** if any figure stops matching a fresh recomputation (drifted source sha, changed count, moved citation line, lost statement or attribution) and **0** when it matches. Proven both directions: the shipped record returns 0; a `/tmp` copy with `distinct_answers.transcript-grow` mutated 33 → 34 returns 1 with `DRIFT distinct_answers.transcript-grow.value: recorded 34 != recomputed 33`. `experiments/ptr-engine/tests/test_quality_carry_forward.py` holds six tests over the statements block and the gate.
