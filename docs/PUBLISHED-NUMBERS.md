# PUBLISHED-NUMBERS — every published accuracy whose denominator is not an accuracy denominator

**Status:** additive register · **Unit:** `PUBLISHED-NUMBER-AUDIT` · **Generated:** 2026-10-26T10:42:19-05:00
**Machine-readable twin:** [`experiments/ptr-engine/measure/PUBLISHED-NUMBERS.json`](../experiments/ptr-engine/measure/PUBLISHED-NUMBERS.json)

## The rule this document is written under

> **History is not rewritten.** Every document cited here keeps exactly the bytes it was published
> with. No banner is pasted into it, no number is struck through, no retraction is inserted at the
> top. Where a published number is wrong, this register says so **here**, and the original keeps
> saying what it said. A reader who finds a wrong number in an old cell transcript and then finds
> this register has been given the correction; a reader who finds only the old transcript is in the
> same position as anyone reading a pre-registered record before the correction pass existed.
>
> Two consequences, both deliberate: (1) the offenders below are still live on disk and can still be
> quoted, which is why §"Worst" names one explicitly; (2) this file is the only place a correction
> to a published accuracy may be written, so if a second register of this kind ever appears, one of
> the two is wrong.

This is the third species of wrong number in this project, and the most dangerous. The first was a
**missing marker** (a number published where an `UNDECIDABLE` belonged). The second was a **starved
pin** (a comparison run against rows that could not pin). This one needs no defect in the machinery
at all: it is a **proportion over the wrong denominator, published with a confidence interval
attached**. The arithmetic is correct. The interval is correctly computed. Only the population is
wrong, and nothing on the line says which population it is.

Three denominator kinds exist in this project, and only one of them is an accuracy denominator:

| kind | population | is it an accuracy denominator? |
|---|---|---|
| `checkpoint` | `grade_v5` checkpoint cells, `decidable = pass + fail` (n = 3 in the current fixture) | **yes** — this is the only one the grade contract defines |
| `row` | rows of the run transcript (64, 72, … turns) | **no** — a row is a turn, not a graded checkpoint |
| `turn` | turns in a schedule | **no** — the grader does not grade per turn |
| `unknown` | none stated | **no** — a defect of the same class, because the reader cannot tell |

## The family, counted

| measure | count |
|---|---|
| documents swept | **112** (`measure/*.md` 16, `measure/*.json` 46, `docs/*.md` 26, `papers/context-cache` 16, `orchestration/STATUS.md` 1, `cell-*.md` 3, plus 7 swept outside the minimum list) |
| claims registered | **37** |
| `wrong_denominator` | **6** |
| `undetermined` (no denominator anywhere) | **1** |
| `checked` (defensible denominator, or correctly withheld) | **30** |
| **distinct documents** publishing an accuracy over the wrong denominator | **5** (3 markdown + 2 JSON) |
| `wilson95` intervals attached to a wrong-denominator number | **4 published lines · 2 distinct intervals** (the same `[0.7538, 0.9242]` at n=64 on both runs, each printed in the `.md` and again inside the `.json`'s captured output) |
| runs affected | **3** (two transcript-grow runs, one pointer-stable run) |

The interval count is the one that matters for trust: an accuracy printed bare is a claim, but an
accuracy printed with `[0.7538, 0.9242]` is a *measurement*, and a reader discounts it accordingly.
Four published lines in this repository buy that credibility for a ratio that is not accuracy.

## The offenders — `wrong_denominator`

| # | file:line | as published | actual denominator | defensible number | source of the defensible number |
|---|---|---|---|---|---|
| 1 | [`cell-transcript-grow-20261026T144452Z.md:36`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.md#L36) | `accuracy 55/64 wilson95 n=64 0.8594 [0.7538, 0.9242] (undecidable: 0)` | row, n=64 | **3/3** (decidable 3) | [`…144452Z.grade-v5.json`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.grade-v5.json) → `arms["transcript-grow"].checkpoint_accuracy` |
| 2 | [`cell-transcript-grow-20261026T144540Z.md:36`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.md#L36) | same | row, n=64 | **3/3** (decidable 3) | [`…144540Z.grade-v5.json`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.grade-v5.json) → `arms["transcript-grow"].checkpoint_accuracy` |
| 3 | [`cell-transcript-grow-20261026T144452Z.json:36`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.json#L36) | `"accuracy": "55/64"` | row, n=64 | **3/3** | same grade file as #1 |
| 4 | [`cell-transcript-grow-20261026T144540Z.json:36`](../experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.json#L36) | `"accuracy": "55/64"` | row, n=64 | **3/3** | same grade file as #2 |
| 5 | [`cell-pointer-stable-20261026T145722Z.md:36`](../experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.md#L36) | `accuracy UNDECIDABLE (n=0 decidable turns; 72 rows carry no decidable outcome)` | row, n=72 | **1/3** (decidable 3; `cp.1.t24`, `cp.2.t46` = `answer_not_contract`) | [`…145722Z.grade-v5.json`](../experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.grade-v5.json) → `arms["pointer-stable"].checkpoint_accuracy` |
| 6 | [`cell-pointer-stable-20261026T145722Z.md:41`](../experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.md#L41) | `- arm pointer-stable accuracy: no decidable turns (n=0)` | row, n=72 | **1/3** | same grade file as #5 |

Rows 3–4 exist separately from rows 1–2 because the JSON is the half a script reads: nothing in
`{"accuracy": "55/64"}` says the 64 is a row count, and the same string is re-embedded in the
captured analyser output at `:48` of each file. Rows 5–6 publish **no ratio at all**, so they
understate instead of inflating — but the population each reasons from is the 72 rows, and both
tell a reader that nothing was measured on a run whose grade document measures 3 checkpoints and
passes 1. Row 6 makes it worse by filing the refusal under the heading *"refusals (numbers withheld
on purpose)"*: the numbers were not withheld, they were declined.

## The offender with no denominator — `undetermined`

| # | file:line | as published | why it cannot be classified |
|---|---|---|---|
| 7 | [`orchestration/units/HOST-SCOUT-1.md:41`](../orchestration/units/HOST-SCOUT-1.md#L41) | `accuracy 0.8974/0.90/0.85/1.0/0.925/0.8378` | six accuracy-shaped decimals in a row, **no n on the line and none on its neighbours**; the cited dashboard row counts (`4,090` lines, `3,690` rows) sit three lines below and are not the per-round denominator. Neither the line nor its context says checkpoint, row or turn, and no grade document covers that run in this workspace. Registered as a defect of the same class rather than omitted. |

## What is *not* in the family (registered as `checked`, and why)

The sweep found 30 defensible or correctly-handled claims. The distinctions that matter:

- **`papers/context-cache` MCQ accuracies are not this defect.** `126/190` (`CLAIMS.md:94`), the
  `2.632`-point deltas, `strategy/BOUNDARY_ANALYSIS.md:85-86`'s per-K Wilson intervals, the
  `71/73` locator audits in `papers/gated-read-batching` — in each of these a row **is** one graded
  MCQ case or one register row, so the row population is the population of interest. They are
  registered (`PN-019`…`PN-031`) so the sweep is auditable, and the project already states their
  instrument limits (`COMPILATION.md:51-53`, `GAPS.md:350`).
- **A wrong number published as an anti-pattern is not a defect.**
  [`papers/replay-record-not-decision/AVAILABILITY.md:77`](../papers/replay-record-not-decision/AVAILABILITY.md#L77)
  prints the impossible `202/190` accuracy *in order to warn replicators*, with the correct rule on
  the same line. That is the model this register follows.
- **A defective line reprinted inside an audit is not a claim.**
  [`docs/DECIDABILITY-SEAM.md:105`](../docs/DECIDABILITY-SEAM.md#L105) quotes `55/64` verbatim and
  then states at `:110-114` that the denominator is the row population and the figure is withheld as
  accuracy evidence. That is the correct handling of history, and it is why only two of the three
  documents containing the string `55/64` are offenders.
- **The JSON corpus of the grader itself is clean.** All 46 `measure/*.json` files that carry an
  accuracy field carry `checkpoint_accuracy` with its `/3` (`PN-010`…`PN-012`); the wrong-denominator
  fields live only in the analyser's per-cell output files, not in any `grade-v5` document.

## The worst one

**`experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.md:36`** —
`accuracy 55/64 wilson95 n=64 0.8594 [0.7538, 0.9242] (undecidable: 0)`.

Chosen by prominence × wrongness. It is the first-published live cell of a flagship arm, and it
carries **three separate signals of measurement** — a numerator/denominator pair, a Wilson interval,
and an explicit `undecidable: 0` accounting column — every one of which belongs to a population of
64 rows while the reader will read it as a population of graded checkpoints. The true checkpoint
accuracy for that run is **1.0000** (3/3). A wrong number that reads low invites re-checking; a
wrong number that reads *0.86 with a tight interval* reads like a mediocre-but-real measurement and
gets quoted.

**The sentence that should have been written:**

> `accuracy 3/3 (denominator=checkpoint, n=3 decidable, decidable=3; interval withheld — n=3 is below the reported-precision floor), source cell-transcript-grow-20261026T144452Z.grade-v5.json:arms.transcript-grow.checkpoint_accuracy; the 55/64 row-level ratio in the analyser's raw output is not accuracy.`

## The guard — one change, recommended not implemented

**Make the producer print the denominator kind and the n on every accuracy line, and make a linter
reject any published accuracy line that lacks them.** The producer is
`experiments/ptr-engine/longrun/analyze_stats.py` (`accuracy_from_grade`, `:431-463`; `graded_n` set
at `:457`): it is the only code that emits these lines — both the `.md` and the `.json` carry its
captured output verbatim, so a single emit-side change (`accuracy 3/3 denominator=checkpoint n=3
decidable=3`, with `denominator=row` printed when no grade document is supplied, never a bare ratio)
covers every future artefact and every future consumer. The linter belongs in a new
`tests/test_published_numbers.py`, alongside the repo's existing artefact guards: it scans
`experiments/ptr-engine/measure/*.md`, `measure/*.json`, `docs/*.md` and `papers/**/*.md`, and fails
on any line matching `accuracy` followed by a ratio/pct/interval that does not also carry
`denominator=<kind>` and `n=<int>`; a `denominator=row` or `denominator=turn` accuracy is an error,
not a warning, because there is no reading of the grade contract under which a row is a checkpoint.
The same linter answers the `undetermined` class for free: `HOST-SCOUT-1.md:41` and
`COMPILATION.md:50` are exactly the shapes it rejects. This is a recommendation; nothing here is
implemented, and no test, script or fixture was edited by this unit.

## Method, so the sweep can be repeated

Offline, zero inference requests, no network, no `git`. Pattern search for `accuracy`, `wilson`,
`wilson95`, `[0.` intervals, `%`, `cp.`/`decidable`, `n=`, and the literal ratio strings (`55/64`,
`202/190`, `71/73`, `0.8594`) across the paths in the table above, plus a propagation check for
`55/64` (7 occurrences: 2 offenders, 2 JSON twins/embeds, 1 audit quote, and the `DECIDABILITY-SEAM`
unit card and handoff that reported it). Every defensible number above was **copied from a cited
grade JSON**, never recomputed or invented; every registered claim carries a real line number.
