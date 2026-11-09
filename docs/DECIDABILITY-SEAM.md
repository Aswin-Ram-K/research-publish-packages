# DECIDABILITY-SEAM — the grader and the analyser disagreed about the same rows

Unit `DECIDABILITY-SEAM` · 2026-10-26 · offline (zero inference requests).

## 1. The contradiction, as observed

One conductor run over `experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl`
(fixture `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json`):

- `grade_v5` — `acc=1/3 decidable=3` (pass `cp.0.t12`, fail `cp.1.t24`, fail `cp.2.t46`).
- `analyze_stats` — `accuracy UNDECIDABLE (n=0 decidable turns; 72 rows carry no decidable outcome)`,
  with p50 158.19 ms and p95 435.27 ms at n=72.

Same rows, two populations, one record: exactly the "green summary over cells that were never
graded" defect class.

## 2. Where the seam is — both sides

| side | path:line | what it counts |
|---|---|---|
| grader | `experiments/ptr-engine/longrun/grade_v5.py:608-622` (`_parsed_from_row`) | parses the answer out of the row **`content`** when `answer_kind` is null, then grades one cell per truth checkpoint |
| grader | `experiments/ptr-engine/longrun/grade_v5.py:630` (`by_turn`) | collapses rows to **one row per turn**, so duplicated follow-up rows cannot inflate the denominator |
| grader | `experiments/ptr-engine/longrun/grade_v5.py:653` (`"decidable": len(arm_cells)`) | **the authoritative numerator/denominator: 3** |
| analyser (pre-fix) | `experiments/ptr-engine/longrun/analyze_stats.py:415` (`if row.get("answer_kind") != "NUM": return None`) | required a row-level `answer_kind == "NUM"`; every v6 row has `answer_kind: null` |
| analyser (pre-fix) | `experiments/ptr-engine/longrun/analyze_stats.py:547-549` | printed `accuracy UNDECIDABLE (n=0 ...)` from a 72-row denominator that also included 24 `tool-followup` rows |

Row evidence (`rows-longrun-v6-tools.jsonl`, 72 rows, never modified):

```
answer_kind   None  ×72          ← why the analyser saw nothing
answer_value  None  ×72
answer_source content ×72        ← the runner itself says answers are in `content`
kind          turn ×48, tool-followup ×24   ← 72 rows are NOT 72 turns
is_checkpoint True ×5 (3 distinct turns 12/24/46), False ×67
```

`grade_v5.py` is right that those three checkpoints are decidable: `cp.0.t12`'s content ends
`ANSWER: 64` and `cp.2.t46`'s ends `ANSWER: ledger.record_refusal(scope=..., ...)`, both typed
answers. The **analyser was wrong**, on two counts: (a) it keyed on a row column the runner never
populates for this format instead of on the grader's verdicts, and (b) its denominator was the row
count including follow-up duplicates, not the graded checkpoint count.

## 3. Fix — the population is now named and shared

`analyze_stats.py`:

- new `--grade <grade_v5.json>`: accuracy is read from the grader's checkpoint **cells**
  (`accuracy_from_grade`, `analyze_stats.py:431`; `graded_n` set at `:457`), never re-derived from rows;
- every arm prints the two populations on their own lines (`:602-621`):

```
  timing_n = 72  (rows with a usable ttft_ms)
  graded_n = 3  (checkpoint cells graded by grade_v5)
  accuracy = 1/3 (pass 1, fail 2, undecidable 0, missing 0)
  accuracy wilson95 n=3  0.3333 [0.0615, 0.7923]
```

`UNDECIDABLE` is now reachable only when `graded_n == 0` **and** nothing is decided, and it always
carries the four named counts — a bare `UNDECIDABLE (n=0)` beside a graded `1/3` is impossible.
Without `--grade` the old row-derived fallback is kept for row-only callers, but it is labelled
`graded_n = 0` and `source: rows`, so it cannot claim a graded population.

## 4. Conductor consistency gate — exit 9

`cell.py` now passes the grade document to the analyser (`stage_analyse(..., grade_path=...)`,
`cell.py:652`) and runs a consistency gate after analysis (`stage_consistency`, `cell.py:459`,
emitted as `cell.py:664`). If the grader reports `decidable > 0` while the analyser reports
`graded_n == 0`, or vice versa:

```
cell: 7 consistency REFUSED(9) authoritative facts disagree — grader decidable=3 (grade_v5.py:653) vs analyser graded_n=0 (analyze_stats.py:457)
```

Exit codes 2–8 are untouched; **9** is new. `--allow-inconsistent` (`cell.py:587`) overrides and
records the override in the cell record under `consistency`
(`{grader_decidable, analyser_graded_n, line, contradictory, override}`). A consistent cell emits
`6b/7 consistency ok grader decidable=3 (grade_v5.py:653) vs analyser graded_n=3 (analyze_stats.py:457)`.

## 5. Regression test — red before, green after

`experiments/ptr-engine/longrun/tests/test_decidability_seam.py` (4 tests, copies the row file to a
temp dir; the original is never edited; every cell run is `--offline`):

- (a) pre-fix population reproducible: all 72 rows have null `answer_kind`/`answer_value`, 24 are
  `tool-followup`, `row_outcome()` decides **0** — while the grader grades **3**;
- (b) with `--grade`: `timing_n = 72`, `graded_n = 3`,
  `accuracy = 1/3 (pass 1, fail 2, undecidable 0, missing 0)`, no `UNDECIDABLE` on that line;
- (c) contradiction → cell **exit 9** with both numbers and both source lines; same cell with
  `--allow-inconsistent` → **exit 0** and `consistency.override == true` in the record;
- (d) real grader + real analyser → **exit 0** with `6b/7 consistency ok`.

Red→green (measured, not asserted):

```
RED   (gate call removed)  AssertionError: 0 != 9          → FAILED (failures=1)
GREEN (gate in place)      4/4 OK · test_cell.py 7/7 OK · test_analyze_stats.py 8/8 OK
```

## 6. Audit — has this project already published an accuracy over the wrong population?

**Yes, two records.** `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.md:36`
and `…T144540Z.md:36` publish

```
  accuracy  55/64  wilson95 n=64  0.8594 [0.7538, 0.9242]  (undecidable: 0)
```

while `grade_v5` on the same runs graded **3/3** over 3 checkpoints
(`cell-transcript-grow-20261026T144452Z.grade-v5.json` → `arms.transcript-grow.checkpoint_accuracy
= 3/3, decidable = 3`). The 55/64 denominator is the row population, not the checkpoint
population — the wrong population under the grade_v5 contract. Those two cells predate this fix and
their analysis JSON is unchanged (historical records are not rewritten). They are **withheld as
accuracy evidence**: use the grade document's `checkpoint_accuracy` (`3/3`, n=3) with the
`experiments/ptr-engine/measure/GRADER-FITNESS.md` caveat, and never `55/64`.

The v6 live cell did not publish a wrong number — the analyser refused (`UNDECIDABLE`) — but the
record still carried `decidable=3` from the grader beside it, which is the contradiction this unit
gates.

## 7. Reproduce

```
python3 experiments/ptr-engine/longrun/analyze_stats.py \
  --rows experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl \
  --grade experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.grade-v5.json
python3 experiments/ptr-engine/longrun/tests/test_decidability_seam.py
```

## Constraints honoured

Zero requests (every run `--offline`, no call to 192.168.2.168); no historical row, grade or cell
record edited; `client.py`, `run_longrun.py`, `det_verify.py`, `fixture_coverage.py`,
`matrix_audit.py`, `LR-01.v5.json`, `LR-01.v6.json` untouched; `grade_v5.py` not edited (the fix
belongs in the analyser, which was the wrong side).
