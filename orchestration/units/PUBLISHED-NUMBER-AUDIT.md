# PUBLISHED-NUMBER-AUDIT — unit card

**Status:** done · **Bound:** ≤26 tool calls, 0 inference requests · **Used:** 13 calls, 0 requests
**Tag:** `[automated]` — no human; `ask_user_question` never called.

## Objective

Find every **published accuracy that is not an accuracy**: a proportion over the wrong denominator,
published (in the worst case) with a confidence interval attached, so a reader cannot tell. Third
species of wrong number in this project, after the missing marker and the starved pin.

## What was done

1. Pattern sweep of 112 documents (`experiments/ptr-engine/measure/*.md` 16, `*.json` 46,
   `docs/*.md` 26, `papers/context-cache` 16, `orchestration/STATUS.md` 1, `cell-*.md` 3, plus 7
   swept outside the minimum list) for `accuracy`, `wilson`, `wilson95`, `[0.` intervals, `%`,
   `cp.`/`decidable`, `n=`, and literal ratio strings.
2. Classified each hit by denominator: `checkpoint` (defensible) · `row` · `turn` · `unknown`.
3. Recorded 37 claims: file, line, number as printed, the denominator it actually uses, the
   defensible number from the same run's grade JSON (cited by path), status.
4. Wrote the additive registry — `measure/PUBLISHED-NUMBERS.json` + `docs/PUBLISHED-NUMBERS.md` —
   with the no-rewrite rule stated explicitly.
5. Counted the family, named the worst claim and its replacement sentence, and recommended one guard
   (producer stamps `denominator=` + `n=`; `tests/test_published_numbers.py` rejects the rest).

## Result

| measure | count |
|---|---|
| documents scanned | 112 |
| claims registered | 37 |
| `wrong_denominator` | 6 |
| `undetermined` | 1 |
| `checked` | 30 |
| distinct documents publishing a wrong-denominator accuracy | 5 (3 `.md` + 2 `.json`) |
| `wilson95` intervals on a wrong number | 4 published lines, 2 distinct intervals (n=64) |
| runs affected | 3 |

Offenders: `cell-transcript-grow-20261026T144452Z.{md:36,json:36}` and
`…T144540Z.{md:36,json:36}` print `accuracy 55/64 wilson95 n=64 0.8594 [0.7538, 0.9242]` while both
runs grade **3/3** (decidable 3); `cell-pointer-stable-20261026T145722Z.md:36,:41` print
`UNDECIDABLE (n=0 decidable turns)` over the 72-row population while that run grades **1/3**
(decidable 3, `cp.1.t24`/`cp.2.t46` = `answer_not_contract`). Undetermined:
`orchestration/units/HOST-SCOUT-1.md:41` (`accuracy 0.8974/0.90/0.85/1.0/0.925/0.8378`, no n).

**Worst:** `cell-transcript-grow-20261026T144452Z.md:36` — prominence (first live cell of a flagship
arm) × wrongness (0.8594 published against a true 3/3), with three separate signals of measurement
(ratio, Wilson interval, `undecidable: 0`) all belonging to a row population.

**Replacement sentence:** `accuracy 3/3 (denominator=checkpoint, n=3 decidable, decidable=3; interval
withheld — n=3 is below the reported-precision floor), source
cell-transcript-grow-20261026T144452Z.grade-v5.json:arms.transcript-grow.checkpoint_accuracy; the
55/64 row-level ratio in the analyser's raw output is not accuracy.`

## Constraints honoured

Read-only on every historical artefact (0 historical files edited; this unit wrote only its two
register files, this card, its handoff and its journal). No network, no `git`, 0 inference requests.
No row file, grade file, fixture or analysis script was touched. Every defensible number is copied
from a cited grade JSON — none computed here.

## Guard (recommended, not implemented)

Producer: `experiments/ptr-engine/longrun/analyze_stats.py` (`accuracy_from_grade` `:431-463`,
`graded_n` `:457`) — the only emitter of these lines. Linter: new `tests/test_published_numbers.py`,
failing any published `accuracy` line lacking `denominator=<kind>` and `n=<int>`, with
`denominator=row`/`turn` treated as an error.
