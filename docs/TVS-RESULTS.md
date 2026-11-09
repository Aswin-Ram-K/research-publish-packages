# TVS results — tokens to verified success

**Definition and denominator:** [`docs/TVS.md`](TVS.md) — frozen, not amended by this unit. **Machine-readable:** `experiments/ptr-engine/measure/TVS.json`. **Instrument of record:** `grade_v5` (`experiments/ptr-engine/longrun/grade_v5.py`, sha256 `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`). **Zero inference requests, zero network, no grader/fixture/definition change.** Every number below is a re-read of existing rows plus 8 offline `grade_v5` runs.

## Verdict in one sentence

**TVS is now decided on all 23 declared run/arm pairs and produced on 3 of them** — `rows-longrun-v4-2026-10-26`/`pointer-stable` (**48,347**), `rows-longrun-v4-tools-2026-10-26`/`pointer-stable` (**50,847**) and `rows-longrun-v6-tools`/`pointer-stable` (**111,994**), each a first `grade_v5` pass at `cp.0.t12`, turn 12 — and the remaining 20 pairs are `null / no_verified_success` under a real `grade_v5` verdict, **not** `not_produced`.

Directly behind that headline: the produced fraction is **3/23 = 13%**, and all 3 certified passes are the *same* checkpoint (`cp.0.t12`, turn 12) on the *same* arm (`pointer-stable`). That is why the metric is still too sparse to carry a headline — see [§Sparsity](#sparsity-what-decides-usability).

## Denominator

| quantity | count |
|---|---|
| declared run/arm pairs (`rows-longrun-*.jsonl` in `experiments/ptr-engine/measure/`) | **23** |
| pairs with a `grade_v5` output (instrument of record) | **23** |
| pairs with a verified success → TVS produced | **3** |
| pairs `null / no_verified_success` | **20** |
| pairs `not_produced` (no `grade_v5` output exists) | **0** |
| `repair.t30` | dropped from TVS's declared space: `grade_v5` emits no verdict for it, so it can neither certify a success nor sit in the denominator |

`not_produced` ≠ `null` ≠ `0`. Nothing is pooled across grids; no whole-run total stands in for a TVS value.

> Stale-string note: `TVS.json → denominator.pairs_not_produced_why` still carries the tool's fixed explanatory string ("no grade_v5 output exists…"). Its *count* field is `0`, which is the fact; the string is a template, not a claim about this run. The tool was not edited.

## The new graded set (this unit's only new instrument outputs)

`grade_v5` run offline, one file per rows file, all with fixture `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json` — the same fixture the pre-existing v6 `grade_v5` output used, so all 23 pairs share one declared space (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`). The 12-checkpoint `LR-01.v6.json` fixture was **not** used: swapping it would change the declared space mid-metric and re-open the coverage gap as a scoring question. That stays a separate coverage card.

| rows file | grade_v5 output (new) | arms | cells pass/fail/undec |
|---|---|---|---|
| `rows-longrun-2026-10-26.jsonl` | `measure/cell-longrun-base-20261026T1556Z.grade-v5.json` | 4 | 0 / 0 / 12 |
| `rows-longrun-2026-10-26-fix.jsonl` | `measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` | 4 | 0 / 11 / 1 |
| `rows-longrun-2026-10-26-policy.jsonl` | `measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` | 4 | 0 / 10 / 2 |
| `rows-longrun-c-2026-10-26.jsonl` | `measure/cell-longrun-c-20261026T1556Z.grade-v5.json` | 4 | 0 / 0 / 12 |
| `rows-longrun-v3-2026-10-26.jsonl` | `measure/cell-longrun-v3-20261026T1556Z.grade-v5.json` | 2 | 0 / 1 / 5 |
| `rows-longrun-v4-2026-10-26.jsonl` | `measure/cell-longrun-v4-20261026T1556Z.grade-v5.json` | 2 | **1** / 0 / 5 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `measure/cell-longrun-v4-tools-20261026T1556Z.grade-v5.json` | 1 | **1** / 0 / 2 |
| `rows-longrun-v5-tools.jsonl` | `measure/cell-longrun-v5-tools-20261026T1556Z.grade-v5.json` | 1 | 0 / 0 / 3 |

No older grade file was edited; no rows file was edited; judge, fixture and [`docs/TVS.md`](TVS.md) are untouched. Filename note: `grade_v5` emits **one file per rows file (all arms)**, so the `<arm>` slot of the contracted name `cell-<arm>-<stamp>.grade-v5.json` carries the grid tag — a single-arm filename would have been false for the 7 multi-arm grids.

## Produced values — the primary instrument (`grade_v5`)

| grid | arm | first pass | turn | **tokens** | prompt | completion | cached share | requests counted | dup records skipped |
|---|---|---|---|---|---|---|---|---|---|
| `rows-longrun-v4-2026-10-26` | `pointer-stable` | `cp.0.t12` (num_equal) | **12** | **48,347** | 47,556 | 791 | 85.73% | 12 | 0 |
| `rows-longrun-v4-tools-2026-10-26` | `pointer-stable` | `cp.0.t12` (num_equal) | **12** | **50,847** | 49,850 | 997 | 88.07% | 12 | 17 |
| `rows-longrun-v6-tools` | `pointer-stable` | `cp.0.t12` (num_equal) | **12** | **111,994** | 109,780 | 2,214 | 85.23% | 20 | 11 |

- **Smallest:** 48,347 — `rows-longrun-v4-2026-10-26` / `pointer-stable`. **Largest:** 111,994 — `rows-longrun-v6-tools` / `pointer-stable`. Spread **2.32×**, and it is a spread across *grids*, not arms; no pooling.
- Tokens are `prompt_tokens + completion_tokens` over every distinct request from the run's first request through turn 12 inclusive; the cached share is a diagnostic beside the number, never a substitute for it.
- `tools` vs no-tools on the V4 row family is nearly a wash at this checkpoint (50,847 vs 48,347, +5.2%), because the extra fetch follow-ups at turns ≤12 are few. The V6 difference is a code-state difference, not a tools effect.
- **Carried beside the numbers, not inside them:** V6 ran turns 1-6 before a correction and turns 7-48 after, so the turn-1–12 window spans two code states (`TVS.json → cells[].code_state.mid_cell_code_change = true` for `rows-longrun-v6-tools` only). V4 and V4-tools are homogeneous (`false`).
- Whole-run total for V6 (never used as TVS): **307,380 tokens** after de-duplication — TVS is 36% of it, which is the point of the window rule.

## `null / no_verified_success` — 20 pairs, with the reason

Every one of these has a `grade_v5` verdict now; none has a passing checkpoint. Two distinct mechanisms, and they must not be read as one:

| grid | arms | what `grade_v5` said |
|---|---|---|
| `rows-longrun-2026-10-26` | all 4 (`transcript-grow`, `transcript-compact`, `pointer-stable`, `lease-reopen`) | 12/12 cells **undecidable** — `prose_only` / `no_answer_line`: these rows predate the answer contract, so no cell can be decided (no pass, no fail) |
| `rows-longrun-c-2026-10-26` | all 4 | 12/12 cells **undecidable** — same, pre-contract rows |
| `rows-longrun-v5-tools` | `pointer-stable` | 3/3 **undecidable** (`prose_only` / `no_answer_line`) |
| `rows-longrun-v3-2026-10-26` | `pointer-stable`, `transcript-grow` | `pointer-stable` 1 **fail** (`answer_not_contract:multiple_answer_lines`) + 2 undecidable; `transcript-grow` 3/3 undecidable |
| `rows-longrun-v4-2026-10-26` | `transcript-grow` | 3/3 undecidable, while `pointer-stable` on the same rows passes `cp.0.t12` |
| `rows-longrun-2026-10-26-fix` | all 4 | 11 **fail** `turn_missing` (+3 missing cells), 1 undecidable — the run ended before the graded turns |
| `rows-longrun-2026-10-26-policy` | all 4 | 10 **fail** `turn_missing` (+ missing cells), 2 undecidable — same truncation |

Read this correctly: `undecidable` is an *absence of a verdict-bearing answer*, not a failure of the work; `fail` here is mostly `turn_missing` (the run stopped short). Neither may be turned into a `0`, and neither may be turned into a pass by loosening a rule. Per-pair `reason` is `no_verified_success`, carried in `TVS.json`.

## Secondary instruments — reported, **not certified**

`grade-v3`/`grade-v4` passes are context only. They disagree with `grade_v5` on the same rows (`cp.2.t46`: pass under `grade-v4`, `fail/answer_not_contract` under `grade_v5`), which is exactly why one instrument certifies.

| grid | arm | instrument | pass cells | first-pass turn | tokens |
|---|---|---|---|---|---|
| `rows-longrun-v4-2026-10-26` | `pointer-stable` | `grade-v4` | `cp.0.t12` | 12 | 48,347 |
| `rows-longrun-v4-tools-2026-10-26` | `pointer-stable` | `grade-v4` | `cp.0.t12` | 12 | 50,847 |
| `rows-longrun-v6-tools` | `pointer-stable` | `grade-v4` | `cp.0.t12`, `cp.2.t46` | 12 | 111,994 |

The secondary and certified values coincide for all three produced pairs because the *first* pass is the same cell; the instrument disagreement moves accuracy, not the first-pass turn.

## Duplicate rows — these numbers are already de-duplicated

`measure/DUPLICATE-ROWS.md` measures the defect on all 14 rows files. In one line: **30 byte-identical repeat rows** in the three tool-era grids (v6 11, v4-tools 17, v5-tools 2), counted once here; the five legacy-schema files carry none that the rule can establish. Their effect on these TVS values, measured rather than assumed: the V6 window is **155,955 raw → 111,994 de-duplicated = 1.39×**, not the ~1.8× the prior unit estimated; V4-tools is 17 duplicate rows lighter; V4 is unaffected (0 duplicates).

## Out of scope (never counted)

- `rows-baseline-2026-10-26.jsonl` — not a declared long-run grid (declared space = `rows-longrun-*.jsonl` carrying the LR-01 fixture task_id)
- `rows-cell-pointer-stable-20261026T145758Z.jsonl` — not a declared long-run grid
- `rows-equalinfo-2026-10-26.jsonl` — not a declared long-run grid
- `rows-live-2026-10-26.jsonl` — not a declared long-run grid
- `rows-pilot-thinking-2026-10-26.jsonl` — not a declared long-run grid
- `cell-transcript-grow-20261026T144452Z.grade-v5.json` and `cell-transcript-grow-20261026T144540Z.grade-v5.json` — their `rows_file` values are `/tmp/cell-demo-rows.jsonl` and `.cell-demo/rows.jsonl`: demo cells (3/3 passes), not declared long-run grids.

## Tests

`experiments/ptr-engine/longrun/tests/test_tokens_to_verified.py` — **7 passed** (unchanged by this unit; no code was edited): T6 cutoff covers turns 1-6 and a later row does not change it · T12 in a 48-turn run covers turns 1-12, not 48 · no pass → `null` + `no_verified_success` · null `completion_tokens` excluded and counted · fetch follow-up at the pass turn included (both requests asserted) · duplicate record counted once · in-test red→green.

## Sparsity: what decides usability

Is `tokens_to_verified_success` now a usable second headline? **Not yet.** The deciding number is **3/23 pairs produced, from one arm, all at one checkpoint (turn 12)**, against a 20-pair `null` set dominated by `undecidable` rows written before the answer contract rather than by measured failure. A headline drawn from three turn-12 passes on `pointer-stable` would describe the arm, not the system — and a 2.32× grid spread with no second checkpoint ever reached makes it a single-arm observation. The *instrument* is now sound and every pair is decided; the *coverage* is not. What would move it: reach `cp.1.t24`/`cp.2.t46` with a passing arm in at least one grid (which means grading the coverage fixture `LR-01.v6.json` as a declared-space change), so that a first success is not always the first checkpoint.
