# UNIT `ERA-B-GRADE-REHEARSAL-2` — the same 64 correct era-B answers, against the repaired grader

**Status:** done · **Bound:** 8 calls after journal (used 5) · **Requests:** 0 (offline, zero sockets) ·
**Date:** 2026-10-26 · **Verdict:** **`contract_accepts_era_b_correct_answers`**

## Why this unit exists
`ERA-B-GRADE-REHEARSAL` ran the same 64 correct answers through `grade_v5` and got **50/64**. It named
three families that rejected correct answers and left the grid's quality precondition **false**. Then
`GRADE-V5-T4-DECORATION` repaired the grader, and its own corpus reported 64/64 — but that corpus is the
repairer's own, not the original rehearsal's. The question here is narrow: **do *the same* 64 correct
answers now grade?** A rehearsal that changes the answer set instead of the grader under test is not a
rehearsal.

## 1. The grader under test
| | |
|---|---|
| path | `experiments/ptr-engine/longrun/grade_v5.py` |
| sha256 **now** | `3d70ed1d43d2ab098eeeba4b50fa574273c71e9ff24af5adaa9e519d10c77940` |
| sha256 **before** (old run) | `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` |
| `HARNESS-PIN.json` records | `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` — **stale** |

The pin is stale and that is **expected**: `HARNESS-PIN-GEN5` regenerates it once
`BUDGET-STAGE-MAX-TURNS` has also landed (one regeneration, not two). This unit does not touch the pin.

## 2. What the old run recorded (`measure/ERA-B-GRADE-REHEARSAL.json`, sha256 `17e4b6dd…fcc49d1`)
64 correct rows → **pass 50**, **not passing 14** (11 card-required). Per shape:

| shape | rows | pass | fail | undecidable |
|---|---|---|---|---|
| `a_canonical` | 12 | 12 | 0 | 0 |
| `b_trailing_period` | 12 | 5 | 4 | 3 |
| `c_two_line` | 12 | 12 | 0 | 0 |
| `d_tool_narration` | 12 | 12 | 0 | 0 |
| `e1_kwargs_reordered` | 4 | 4 | 0 | 0 |
| `e2_reordered_plus_provenance` | 4 | 0 | 4 | 0 |
| `g_num_with_citation` | 5 | 5 | 0 | 0 |
| `f_none_with_justification` | 3 | 0 | 3 | 0 |

Nine negative controls: **0/9 passed** (`num_mismatch`, `callee_mismatch`,
`kwarg_value_mismatch:block_size`, `call_not_parsable`, `empty_num` *undecidable*, `prose_only`
*undecidable*, `kind_mismatch:NONE_expected` ×3). Verdict then: `contract_rejects_correct_era_b_answer`.

## 3. What `GRADE-V5-T4-DECORATION` now strips
One pass, `grade_v5._strip_decoration`, called **once** from `parse_answer_contract` before the head split /
kind branches:

- **(a)** one trailing sentence-final `.` (not `..`), **every** kind;
- **(b)** a balanced trailing `(...)` — whitespace-separated, so the call's own `)` is never decoration — or
  a trailing citation from the **imported** `dv.citation_spans`, on a non-NONE kind, and only while the
  remainder is still a complete answer of the **same** kind (`_complete_prefix`);
- **(c)** a `NONE` justification after `—`/`-`/`;`/`(` stays a denial **unless** its payload carries a value
  (numeral, dotted name, callable `(`, snake_case token; citations removed first).

Every removed fragment is recorded in `cell["decoration_stripped"]` (`grade_v5.py:323`).

## 4. The re-run (`experiments/ptr-engine/measure/ERA-B-GRADE-REHEARSAL-2.json`)
Same 12 checkpoints, same 8 shapes, same 64 rows, same fixture
(`tasks-v6/LR-01.v8.json`, sha `0804b515…`), same `grade_v5.derive_truth`, same nine controls.
Only the grader moved.

| shape | old | now |
|---|---|---|
| `a_canonical` | 12/12 | **12/12** |
| `b_trailing_period` | 5/12 | **12/12** |
| `c_two_line` | 12/12 | **12/12** |
| `d_tool_narration` | 12/12 | **12/12** |
| `e1_kwargs_reordered` | 4/4 | **4/4** |
| `e2_reordered_plus_provenance` | 0/4 | **4/4** |
| `g_num_with_citation` | 5/5 | **5/5** |
| `f_none_with_justification` | 0/3 | **3/3** |
| **total** | **50/64** | **64/64** |

### 5. Movement per family, with the rule that accepted it
| family | old | now | status | accepting rule | `decoration_stripped` |
|---|---|---|---|---|---|
| trailing period on CALL | 0/4 | 4/4 | **now pass** | rule (a) | `"."` |
| trailing provenance parenthetical | 0/4 | 4/4 | **now pass** | rule (b) | `(resolve.py:69)`, `(resolve.py:141)`, `(resolve.py:159)`, `(resolve.py:163)` |
| `NONE — justification` | 0/3 | 3/3 | **now pass** | rule (c) | `— the source defines no such call` |

No family still fails; no reason string remains on any of the 11 previously-rejected rows.

### 6. The gate: the nine negative controls
**0 of 9 pass.** Exactly the same nine, exactly the same verdicts and reason strings as before the repair —
`num_mismatch`, `callee_mismatch`, `kwarg_value_mismatch:block_size`, `answer_not_contract:call_not_parsable`,
`empty_num` (undecidable), `prose_only` (undecidable), `kind_mismatch:NONE_expected` ×3. The repair bought
no control.

### 7. Nothing already green regressed
`a` 12/12 · `c` 12/12 · `d` 12/12 · `e1` 4/4 · `g` 5/5 — all still 12/12 (or 4/4, 5/5). All 12 checkpoints
have at least one accepted shape; `e1` 4/4 and `g` 5/5 unchanged.

### 8. Verdict
**`contract_accepts_era_b_correct_answers`** — grid quality precondition **10 is now true**. Forced by
`correct_rows_passing = 64/64` with `negative_controls_passed = 0/9`.

### 9. Quality ceiling and the distinction
- A **perfect** era-B arm scores **12/12** declared checkpoints: every checkpoint has an accepted shape.
- A **partially correct** arm scores strictly less. Proof beyond the nine: **6 added** negative controls and
  **12 wrong-value mutants** (one per checkpoint) — **0/6** and **0/12** pass.
  The decisive pair: `call_wrong_value_with_provenance` wears the same `(resolve.py:159)` citation the
  repair strips and still fails `kwarg_value_mismatch:block_size` — the strip removes the *decoration*, the
  **value** is still graded.
- **Does the repaired grader tell a correct answer from a confident wrong one? Yes.** It accepts the shape
  and still grades the value: 64/64 correct, 0/27 wrong (9 gate + 6 added + 12 mutants).

## Not touched
`grade_v5.py`, any fixture, any threshold, `PARM-1*`, the grid card, the ledger, any published page,
`HARNESS-PIN.json`. `measure/ERA-B-GRADE-REHEARSAL.json` was read only, never rewritten (sha unchanged
`17e4b6dd…fcc49d1`).

## Write paths
`experiments/ptr-engine/measure/ERA-B-GRADE-REHEARSAL-2.json` · `docs/ERA-B-GRADE-REHEARSAL-2.md` ·
`experiments/ptr-engine/tests/test_era_b_rehearsal_2.py` · `orchestration/units/ERA-B-GRADE-REHEARSAL-2.md` ·
`orchestration/handoffs/ERA-B-GRADE-REHEARSAL-2.json` · `orchestration/journals/ERA-B-GRADE-REHEARSAL-2.jsonl`
