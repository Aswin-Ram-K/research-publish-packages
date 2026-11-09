# UNIT `SEAM-TEST-RED` — one owner for the `decidable` count

- **Date:** 2026-10-26 · **Offline:** zero inference requests · **Status:** done (suite carries one external red, named below)
- **Bound:** 22 calls · **Actual:** overran (this unit is over its call bound — see Handoff `tool_calls`)
- **Write paths:** `experiments/ptr-engine/longrun/grade_v5.py` · `experiments/ptr-engine/longrun/analyze_stats.py` ·
  `experiments/ptr-engine/longrun/tests/test_decidability_seam.py` · this card · its handoff · its journal.
  (The card named `tools/analyze_stats.py`; that path does not exist — the analyser is
  `longrun/analyze_stats.py`, and that is the file edited.)

## 1. The decision, restated from the settled handoff (not re-litigated)

`orchestration/handoffs/DECIDABILITY-SEAM.json` + `docs/DECIDABILITY-SEAM.md:23` decided:

> the grader is "**the authoritative numerator/denominator**"; the analyser "**was wrong**, on two
> counts: (a) it keyed on a row column the runner never populates … and (b) its denominator was the
> row count including follow-up duplicates, not the graded checkpoint count".

`handoffs/DECIDABILITY-SEAM.json` `assumptions[2]`: "Fix placed in `analyze_stats.py`, **not**
`grade_v5.py`: the analyser was the wrong side". Handoff rule text: "decidable = every cell the
grader emitted a verdict for; `pass: null` cells are undecidable".

**It is silent on which *function* owns the number.** Ownership proposed and adopted:

> `grade_v5.decidable_population(cells)` — the grader emits the verdicts, so the grader owns the
> count; every consumer *calls* it. Two agreeing copies are the drift bug, and the copies had
> already drifted (below).

## 2. What had actually drifted

| # | fact | evidence |
|---|---|---|
| T3 | A later unit (`ATTACK-GRADE-V5-2`) **repaired the grader**: `decidable` went from `len(arm_cells)` to `pass + fail`, non-answers (`prose_only`, `unparseable`, …) became `undecidable`, and `turn_missing` was **contracted as a decidable fail** | `grade_v5.py:NON_ANSWER_ERRORS` + `grade_cell`; `experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py:132-140,160-166`; `measure/ATTACK-GRADE-V5-2.json` |
| drift | `analyze_stats.accuracy_from_grade` kept its **own copy** of the rule and that copy **excluded `turn_missing` from `failed`** | old `analyze_stats.py:524-534` |
| effect | on any arm with unanswered checkpoints the analyser's denominator was smaller than the grade document's for the *same cells* | matrix arms: grader `decidable=19` vs analyser `pass + fail−missing = 8` |

So on the v6 fixture (0 missing) both said `decidable = 1`; the copies only disagreed where missing
cells exist. The two red tests were the *other* drift: they hardcoded the **pre-T3** numbers
(`grader decidable=3`, `accuracy = 1/3`) that T3 had superseded.

## 3. The fix

- `grade_v5.decidable_population(cells)` — the single owner. `pass + fail` (fail **includes**
  `turn_missing`), `text` and `undecidable` outside, a cell with **no verdict** (`pass: null`)
  counted as undecidable, `missing` a subset of `fail`. `DECIDABLE_SOURCE = "grade_v5.decidable_population"`.
- `grade_v5.grade_rows` and `analyze_stats.accuracy_from_grade` both call it; the analyser's private
  counting is deleted and it returns `decidable_source` for provenance. `analyze_stats` imports
  `grade_v5` **hard** (no try/except) for the same reason its `row_provenance` import is hard.
- **grade_v5 output is numerically unchanged** (the helper reproduces `pass + len(fail)` exactly);
  one new key, `decidable_source`, is added to each arm.
- **No threshold, no guard and no rows/measure/doc file was touched.**

## 4. Tests (`experiments/ptr-engine/longrun/tests/test_decidability_seam.py`, 5 tests)

- **(a)** unchanged: pre-fix row population decides 0 on the real 72 rows.
- **(b)** fixture with **pass, fail, undecidable AND a `pass: null` cell**: `graded_n = 5`,
  `accuracy = 1/3 (pass 1, fail 2, undecidable 2, missing 1)`, JSON tuple
  `("grade_v5", 5, 72, 1, 2, 3, 1, 2)`.
- **(c)** exit 9 on the contradiction + exit 0 with `--allow-inconsistent`; the quoted grader number
  is **computed from the grader** (`grade_v5.grade_rows` on fixture+rows), not hardcoded.
- **(d)** consistent cell exits 0 and the recorded accuracy line **equals the grader's arms block**.
- **(e)** `analyze_stats.grade_v5.decidable_population is grade_v5.decidable_population`; the mixed
  5-cell fixture yields `decidable=3 ≠ cells=5`, `missing=1` inside fail, `undecidable=2`; a
  `pass: null`-only cell yields `decidable=0` on both sides.

**Red→green (measured):**

```
RED   (analyser's private copy restored)
      test_b: 'accuracy = 1/3 …' not found — got 'accuracy = 1/2 (pass 1, fail 1, undecidable 2, missing 1)'
      test_e: AssertionError 2 != 3                       → FAILED (failures=2)
GREEN (shared helper restored)   5/5 OK
```

## 5. Suite

| | tests | failures |
|---|---|---|
| before | 125 | 2 — `test_decidability_seam.test_c…`, `test_decidability_seam.test_d…` |
| after | 126 | 1 — `test_cap_gate.CapGateTest.test_c_followup_counts_as_a_second_unit` (`experiments/ptr-engine/longrun/tests/test_cap_gate.py:205`) |

The remaining red is **external to this unit**: `test_cap_gate` imports neither `analyze_stats` nor
`grade_v5`, and `cell.py`'s mtime moved **11:33:19 → 11:33:43** (and `run_longrun.py` 11:32:30)
*during* this unit — a concurrent card is editing the cap-gate path. Not in this unit's write paths;
not touched, not masked.

## 6. Blast radius

- **grade_v5 figures: none move** (identical arithmetic, verified by the unchanged `tests/test_grade_v5*`).
- **analyser figures:** the denominator grows by the number of `turn_missing` cells wherever
  `missing > 0`. Published artefacts that embed the analyser block: `measure/cell-*.analysis.json`,
  `measure/cell-*.json` (`populations`), `measure/cell-*.md` (transcripts). Measured: **0** hits for a
  `decidable` field in `measure/LATENCY-REPORT.json`, `measure/MATRIX-*.json`,
  `measure/TVS.json`, `docs/OPERATOR-BRIEF.md` — those four named files carry no such figure.
  Nothing was rewritten; recomputation is a follow-up (`next_unit_hint`).
