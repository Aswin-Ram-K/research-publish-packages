# ACCURACY-RECOMPUTED — every analyser-derived accuracy block under the shared denominator rule

Unit `ACCURACY-DENOMINATOR-RECOMPUTE`, 2026-10-26. **Zero inference requests; nothing historical was
edited.** Every number below names the file it came from; machine-readable record:
[ACCURACY-RECOMPUTED.json](ACCURACY-RECOMPUTED.json) (which also carries the generator that produced it,
and its sha256).

## The rule being applied (owner, not a copy)

`decidable = pass + fail` over the grader's **checkpoint cells**; `fail` **includes**
`reason == "turn_missing"`; `text` and `undecidable` are outside; a cell with no verdict (`pass: null`)
is undecidable.

- Owner: `grade_v5.decidable_population(cells)` — [grade_v5.py:752-789](../../ptr-engine/longrun/grade_v5.py)
- Consumer: `accuracy_from_grade` — [analyze_stats.py:714-757](../../ptr-engine/longrun/analyze_stats.py).
  It is now a **caller**; the private copy that dropped `turn_missing` out of `failed` is gone.

## How a record was classified

| class | test | verdict |
|---|---|---|
| `private_rule` | reported denominator `== pass + fail - missing`, with `missing > 0` | affected |
| `row_population` | denominator is the run's **row** count and no `missing` field exists | the private-rule hint cannot be applied (different population) — reported as `unclassifiable_by_private_rule_discriminator`, still superseded by the cell population |
| `shared_rule` | denominator `== pass + fail`, `missing` printed beside it | already correct |
| `no_missing` | `missing == 0`, both rules agree | unaffected |

## Records examined

| id | source | class | pairs/blocks |
|---|---|---|---|
| REC-01 | [regrade-det.json](regrade-det.json) `per_run_arm` | `private_rule` | 23 pairs, **10 affected** |
| REC-02 | [cell-transcript-grow-20261026T144452Z.analysis.json](cell-transcript-grow-20261026T144452Z.analysis.json) (+ [.md](cell-transcript-grow-20261026T144452Z.md), [.json](cell-transcript-grow-20261026T144452Z.json)) | `unclassifiable_by_private_rule_discriminator` (row population) | 1 arm |
| REC-03 | [cell-transcript-grow-20261026T144540Z.analysis.json](cell-transcript-grow-20261026T144540Z.analysis.json) (+ [.md](cell-transcript-grow-20261026T144540Z.md), [.json](cell-transcript-grow-20261026T144540Z.json)) | same | 1 arm |
| REC-04 | [cell-pointer-stable-20261026T145722Z.analysis.json](cell-pointer-stable-20261026T145722Z.analysis.json) (+ [.md](cell-pointer-stable-20261026T145722Z.md), [.json](cell-pointer-stable-20261026T145722Z.json)) | same | 1 arm |
| — | 25 `cell-*.grade-v5.json` arms blocks | `shared_rule` | 24 confirmed; 1 **counter-field gap** |
| — | [MATRIX-HONESTY.json](MATRIX-HONESTY.json), [MATRIX-COVERAGE.json](MATRIX-COVERAGE.json), [OPERATOR-BRIEF.json](OPERATOR-BRIEF.json), [QUALITY-ERAS.json](QUALITY-ERAS.json), [REGRADE.json](REGRADE.json) | `shared_rule` | denominators unchanged |

`source_sha256` for every record read is in the JSON (`records[].source_sha256`,
`grade_v5_documents_checked`, `aggregate_records_checked`).

## The delta table — REC-01, the only private-rule record on disk

`regrade-det.json` (`det_verify.py` sha256 `12ccc74ea3…`) publishes `passed/len(decidable)` and lists
`missing` cells in their own column — so its denominators are short by exactly `len(missing)`.

| run | arm | before | after | missing | reverses? |
|---|---|---|---|---|---|
| `rows-longrun-2026-10-26` | pointer-stable | 0/1 | **0/4** | 3 | yes — "0/1" became "0/4" |
| `rows-longrun-2026-10-26` | transcript-grow | 0/0 | **0/4** | 4 | yes — read as *no decidable outcome*, now a decided 0 |
| `rows-longrun-2026-10-26-fix` | lease-reopen | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-fix` | pointer-stable | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-fix` | transcript-compact | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-fix` | transcript-grow | 0/1 | **0/4** | 3 | yes |
| `rows-longrun-2026-10-26-policy` | lease-reopen | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-policy` | pointer-stable | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-policy` | transcript-compact | 0/0 | **0/4** | 4 | yes |
| `rows-longrun-2026-10-26-policy` | transcript-grow | 0/2 | **0/4** | 2 | yes |

Aggregate over all 23 pairs: denominator **43 → 79**, accuracy **5/43 → 5/79** (6.98 %), 36 turn-missing
checkpoints charged. This 5/79 is the sum of 23 per-run-arm denominators; it is **not** the 92-cell
declared grid's 5/43 (see below).

## The delta table — REC-02..04 (row population → checkpoint population)

| record | arm | before | after | notes |
|---|---|---|---|---|
| [cell-transcript-grow…144452Z](cell-transcript-grow-20261026T144452Z.analysis.json) | transcript-grow | 55/64 (85.9 %) | **3/3 (100 %)** | denominator 64 rows → 3 checkpoint cells |
| [cell-transcript-grow…144540Z](cell-transcript-grow-20261026T144540Z.analysis.json) | transcript-grow | 55/64 (85.9 %) | **3/3 (100 %)** | same |
| [cell-pointer-stable…145722Z](cell-pointer-stable-20261026T145722Z.analysis.json) | pointer-stable | 0/0 "UNDECIDABLE (n=0 decidable turns; 72 rows)" | **1/3 (33.3 %)** | denominator 72 rows → 3 checkpoint cells |

`turns_missing` is 0 in all three grade documents (the cells carry verdicts); the row analyser never
counted cells, so the failure is the **population**, not a dropped `turn_missing`.

## Unclassifiable, stated as a result

- **REC-02..04** — `unclassifiable_by_private_rule_discriminator`: no `missing` field and a row-count
  denominator, so the hint "denominator == pass + fail − missing" cannot fire. They are still superseded
  by the checkpoint population, and are recorded as such rather than silently re-labelled.
- **The 5/8 figure** the seam cites (analyser `5/8` vs grader `5/19`) **was never persisted** to a measure
  artefact. Nothing on disk can be recomputed to it; the matrix records that *are* on disk
  ([MATRIX-HONESTY.json](MATRIX-HONESTY.json)) already read `pointer-stable 5/19`, i.e. they were
  re-issued after the repair.
- **1 grade-v5 arms block is a counter-field gap, not a rule violation**:
  [cell-pointer-stable-20261026T145722Z.grade-v5.json](cell-pointer-stable-20261026T145722Z.grade-v5.json)
  omits `failed`/`missing`, but its three cells are 1 pass + 2 fail, so `decidable = 3` obeys the rule.

## Published sentences that need correcting (list only — not rewritten here)

**14 lines**, handed to `OPERATOR-BRIEF-3` (page owner) and `QUALITY-ERA-TABLE` (era table owner):

| # | file:line | printed | defensible |
|---|---|---|---|
| 1 | [cell-transcript-grow-20261026T144452Z.md:36](cell-transcript-grow-20261026T144452Z.md#L36) | `accuracy 55/64 … 0.8594` | 3/3 |
| 2 | [cell-transcript-grow-20261026T144540Z.md:36](cell-transcript-grow-20261026T144540Z.md#L36) | `accuracy 55/64 … 0.8594` | 3/3 |
| 3 | [cell-pointer-stable-20261026T145722Z.md:36](cell-pointer-stable-20261026T145722Z.md#L36) | `UNDECIDABLE (n=0 … 72 rows)` | 1/3 |
| 4 | [cell-pointer-stable-20261026T145722Z.md:41](cell-pointer-stable-20261026T145722Z.md#L41) | `no decidable turns (n=0)` | 1/3 |
| 5–14 | [REGRADE-DET.md:76](REGRADE-DET.md#L76), [78](REGRADE-DET.md#L78), [79](REGRADE-DET.md#L79), [80](REGRADE-DET.md#L80), [81](REGRADE-DET.md#L81), [82](REGRADE-DET.md#L82), [83](REGRADE-DET.md#L83), [84](REGRADE-DET.md#L84), [85](REGRADE-DET.md#L85), [86](REGRADE-DET.md#L86) | `0/0`, `0/1`, `0/2` per-pass denominators | `0/4` (REC-01) |

Already correct, **do not touch**: [OPERATOR-BRIEF.md:148](../../../docs/OPERATOR-BRIEF.md#L148) states
"`55/64` is a row proportion, not a checkpoint accuracy"; [DECIDABILITY-SEAM.md:105](../../../docs/DECIDABILITY-SEAM.md#L105)
is a labelled audit quote and [:114](../../../docs/DECIDABILITY-SEAM.md#L114) forbids quoting `55/64`.
The pinned table header at [REGRADE-DET.md:66-67](REGRADE-DET.md#L66) also carries the private-rule
sentence ("missing cells are *not* counted as failures") and belongs to the same correction as items 5–14.

## The headline that survives

- **`5/43` does not move.** It is the `det_verify` declared grid: 92 declared cells = 5 pass + 38 fail +
  36 missing + 13 undecidable; 38 fail **already includes** the 36 missing, so 43 is the shared-rule
  denominator. Nothing to recompute.
- **`3/25` does not move.** Every grade_v5 arms block on disk already has `decidable == passed + failed`
  with `turn_missing` inside `failed` — e.g. `cell-longrun-fix` lease-reopen `0/3` (missing 3) and
  `cell-longrun-policy` transcript-grow `0/1` (missing 1). Missing is already charged; `3/27` stays
  withdrawn.
- **What does move** is everything that quoted the analyser's own denominators: the `regrade-det`
  per-run table, whose affected arms read `0/0`–`0/2` and now read `0/4`, and the three cell reports whose
  row denominators (`55/64`, `0/0 over 72 rows`) become `3/3`, `3/3`, `1/3`.

## Reproduction

```
python3 -c "import json;d=json.load(open('experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json'));open('/tmp/gen.py','w').write(d['generator'])"
python3 /tmp/gen.py --outdir /tmp/regen
diff /tmp/regen/ACCURACY-RECOMPUTED.json experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json
```

Empty diff = the consolidated record regenerates byte-identically from the historical sources.
