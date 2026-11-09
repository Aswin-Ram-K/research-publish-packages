# QUALITY ERAS — every published accuracy figure with the grader that produced it

**Unit** `QUALITY-ERA-TABLE` · **as of** the regrade run `2026-10-26T16:00:00+00:00` · **offline**: no model request, no new measurement.

**Grader of record** `experiments/ptr-engine/longrun/grade_v5.py`, sha256 `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`.

Sources: `experiments/ptr-engine/measure/REGRADE.json` (regrade report), `experiments/ptr-engine/measure/regrade/`
(current-grader outputs), the stored `*.grade-v5.json` files on disk, `experiments/ptr-engine/measure/MATRIX-HONESTY.json`,
`experiments/ptr-engine/tools/regrade.py`, `experiments/ptr-engine/tools/matrix_audit.py`, `experiments/ptr-engine/tools/det_verify.py`.
Machine-readable twin: `experiments/ptr-engine/measure/QUALITY-ERAS.json`.

## 0. The finding in one paragraph

The brief's headline **5/43 = 11.6 %** is **not** era-mixed. It is produced by `det_verify.py`
(sha256 `12ccc74e…`) through `matrix_audit.py`, and re-deriving it today reproduces all 92 declared
cells, every per-arm count and the whole `states` block exactly (`cross_check_det_verify.reproduced = true`).
The era drift is real but lives in the **other** instrument: the `grade_v5.py` checkpoint grid. There one
stored grade file (`cell-pointer-stable-20261026T145722Z.grade-v5.json`) was written by a **pre-T3** grader, so
that grid reads **3/27 = 11.1 %** as recorded and **3/25 = 12.0 %** when every pair is put through the current
grader. The numerator is unchanged in both cases; only the denominator moves, because T3 moved two
non-answers out of `fail` and into `undecidable`.

## 1. Per run/arm pair, both readings side by side

`stored` is the grade file on disk; `current` is `regrade.py`'s output over the same rows file. `Δ` is
`current − stored` in passed/decidable. `decidable = pass + fail`; `missing` and `undecidable` never enter
the denominator. Era is decided by re-derivation, since no stored grade file records a grader sha (§3).

| grid | arm | stored pass/decidable | regraded pass/decidable | Δ | era | grade file |
|---|---|---|---|---|---|---|
| `rows-longrun-2026-10-26-fix` | lease-reopen | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-fix` | pointer-stable | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-fix` | transcript-compact | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-fix` | transcript-grow | 0/2 | 0/2 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-policy` | lease-reopen | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-policy` | pointer-stable | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-policy` | transcript-compact | 0/3 | 0/3 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26-policy` | transcript-grow | 0/1 | 0/1 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26` | lease-reopen | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-base-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26` | pointer-stable | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-base-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26` | transcript-compact | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-base-20261026T1556Z.grade-v5.json` |
| `rows-longrun-2026-10-26` | transcript-grow | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-base-20261026T1556Z.grade-v5.json` |
| `rows-longrun-c-2026-10-26` | lease-reopen | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-c-20261026T1556Z.grade-v5.json` |
| `rows-longrun-c-2026-10-26` | pointer-stable | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-c-20261026T1556Z.grade-v5.json` |
| `rows-longrun-c-2026-10-26` | transcript-compact | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-c-20261026T1556Z.grade-v5.json` |
| `rows-longrun-c-2026-10-26` | transcript-grow | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-c-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v3-2026-10-26` | pointer-stable | 0/1 | 0/1 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v3-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v3-2026-10-26` | transcript-grow | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v3-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v4-2026-10-26` | pointer-stable | 1/1 | 1/1 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v4-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v4-2026-10-26` | transcript-grow | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v4-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v4-tools-2026-10-26` | pointer-stable | 1/1 | 1/1 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v4-tools-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v5-tools` | pointer-stable | 0/0 | 0/0 | +0/+0 | current | `experiments/ptr-engine/measure/cell-longrun-v5-tools-20261026T1556Z.grade-v5.json` |
| `rows-longrun-v6-tools` | pointer-stable | 1/3 | 1/1 | +0/-2 | pre-T3 | `experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` |

Only one pair moves: `rows-longrun-v6-tools` / `pointer-stable`, decidable **3 → 1**, passed **1 → 1**.

## 2. The headline, recomputed both ways

This is `grade_v5.py`'s own grid over the **23** run/arm pairs present in `measure/rows-longrun-*.jsonl`.

| reading | passed/decidable | pct | pointer-stable | transcript-grow | lease-reopen | transcript-compact |
|---|---|---|---|---|---|---|
| as recorded on disk | **3/27** | 11.1 % | 3/12 | 0/3 | 0/6 | 0/6 |
| all pairs under the current grader | **3/25** | 12.0 % | 3/10 | 0/3 | 0/6 | 0/6 |

Delta when every stored pair is regraded: passed **+0**, decidable **-2**. The rate rises only because the
denominator falls; no pair becomes a pass that was not one.

**Which number the operator brief should quote.** `docs/OPERATOR-BRIEF.md:45` quotes **5/43 = 11.6 %** and
`measure/OPERATOR-BRIEF.json` `.quality.defensible_overall` carries the same figure with the per-arm split
`pointer 5/19, grow 0/12, lease 0/6, compact 0/6`. That figure is **current** — it survives re-derivation
unchanged — so it stays, but it must be **named**: 5/43 is `det_verify.py` sha256 `12ccc74e…`, not
`grade_v5.py`. The `grade_v5.py` grid, if quoted at all, is **3/25 = 12.0 %** (pointer-stable 3/10) and its
stored **3/27 = 11.1 %** form is withdrawn.

## 3. Grader-era census

**50** grade files under `experiments/ptr-engine/`:

| era | files | meaning |
|---|---|---|
| `current` | 17 | 9 regrade outputs that record grader_sha256 `6893d5…`, plus 8 stored files byte-identical to a re-derivation |
| `pre-T3` | 1 | re-derivation differs — `cell-pointer-stable-20261026T145722Z.grade-v5.json`, first difference `arms.pointer-stable.cells` |
| `pre-grade_v5` | 28 | produced by grade_v2/v3/v4 — a different grader family, not datable against the current judge by construction |
| `undatable` | 4 | grade_v5 files whose rows file is absent (2 `cell-transcript-grow-*`), and 2 `grade-v2` files that record no grader name at all |

**Provenance gap.** 9 of the 20 `grade_v5` files record a grader sha256 — and all 9 are `regrade.py`'s own outputs.
**No stored `*.grade-v5.json` records one.** So no declared pair can be dated from its own provenance:
all **23 / 23** pairs are dated only by `regrade.py`'s byte-identity check, and **0** pairs remain undatable.
Two single-cell `grade-v5` files (`cell-transcript-grow-20261026T144452Z`, `…T144540Z`) cannot be dated at all: their rows live in `/tmp` and `.cell-demo` and are absent here.

Also recorded: **6** files named `*.grade-v4.json` under `longrun/controls/v4/` were actually produced by `grade_v3` —
a filename/grader mismatch that would misdate them to anyone reading the name.

| grade file | grader | era | why |
|---|---|---|---|
| `experiments/ptr-engine/longrun/controls/neg-codeonly.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/neg-marker.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/neg-one.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/neg-truncated.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/pos-exact-only.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/pos-full.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/neg-codeonly.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/neg-marker.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/neg-one.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/neg-truncated.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/pos-exact-only.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/longrun/controls/v4/pos-full.grade-v4.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/cell-longrun-base-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-c-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-fix-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-policy-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-v3-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-v4-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-v4-tools-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-longrun-v5-tools-20261026T1556Z.grade-v5.json` | grade_v5 | current | byte-identical re-derivation against the current grader |
| `experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` | grade_v5 | pre-T3 | re-derivation DIFFERS: arms.pointer-stable.cells |
| `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144452Z.grade-v5.json` | grade_v5 | undatable | grade_v5 file whose rows file is absent, so no re-derivation is possible |
| `experiments/ptr-engine/measure/cell-transcript-grow-20261026T144540Z.grade-v5.json` | grade_v5 | undatable | grade_v5 file whose rows file is absent, so no re-derivation is possible |
| `experiments/ptr-engine/measure/regrade/rows-longrun-2026-10-26-fix.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-2026-10-26-policy.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-2026-10-26.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-c-2026-10-26.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-v3-2026-10-26.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-v4-2026-10-26.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-v4-tools-2026-10-26.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-v5-tools.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/regrade/rows-longrun-v6-tools.grade-v5.json` | grade_v5 | current | records grader_sha256 = 6893d5… |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-2026-10-26.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.grade-v2.json` | None | undatable | no grader name and no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v2.json` | None | undatable | no grader name and no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v3-final.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v5-tools.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json` | grade_v3 | pre-grade_v5 | produced by grade_v3, a grader family before grade_v5; no grader sha recorded |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v4.json` | grade_v4 | pre-grade_v5 | produced by grade_v4, a grader family before grade_v5; no grader sha recorded |

## 4. What the drift was

The T3 repair in `docs/GRADE-V5-REPAIR.md:54-63` reads:

> ## T3 - non-answers are undecidable

> | empty turn (no `ANSWER:` line, no text) | `no_answer_line` | undecidable |

> | prose with no `ANSWER:` line | `prose_only` | undecidable |

> | `ANSWER:` with nothing / whitespace after it | `empty_answer` | undecidable |

> | `ANSWER: TEXT` with an empty body | `empty_text` | undecidable |

> | `ANSWER: NUM` with an empty body | `empty_num` | undecidable |

> | `ANSWER: <body in no contract form>` | `unparseable` | undecidable |


and `docs/GRADE-V5-REPAIR.md:13`: "…expresses no contracted value is `undecidable`, not `fail` — so it
cannot enter the [decidable denominator]". `docs/REGRADE.md:174` records the same rule. A non-answer used to
be a `fail` inside `decidable`; after T3 it is `undecidable` outside it.

Exactly two cells move, both in `rows-longrun-v6-tools` / `pointer-stable`:

| checkpoint | as recorded | current grader | what changed |
|---|---|---|---|
| `cp.1.t24` | `fail` / `answer_not_contract` | `undecidable` / `prose_only` | non-answer reclassified out of `fail` |
| `cp.2.t46` | `fail` / `answer_not_contract` | `undecidable` / `unparseable` | non-answer reclassified out of `fail` |

The third cell of that arm, `cp.0.t12`, is a pass under both graders (stored `num_equal`, current `num_equal`),
so the arm reads `1/3` as recorded and `1/1` now. The 22 differing paths `regrade.py` counted are this pair
plus the schema keys the pre-T3 writer did not emit (`cells`, `missing`, `undecidable`, `undecidable_reasons`,
`decidable_note`, `failed`, `failing_reasons`, `grader_path`, `grader_sha256`) and the absolute-vs-relative
`fixture_file` / `rows_file` spellings.

## 5. The correction line, ready to paste

```text
QUALITY, with its era named: **5/43 = 11.6 %** (pointer-stable 5/19, transcript-grow 0/12, lease-reopen 0/6, transcript-compact 0/6) measured by `det_verify.py` sha256 `12ccc74e…`, reproduced unchanged 2026-10-26. The separate grade_v5 checkpoint grid is **3/25 = 12.0 %** (pointer-stable 3/10), and its older stored form **3/27 = 11.1 %** came from a pre-T3 grader and is withdrawn.
```

No rows file, no `*.grade-v5.json`, no `docs/OPERATOR-BRIEF.md`, no `measure/OPERATOR-BRIEF.json`, no
`measure/PUBLISHED-NUMBERS.json`, no `TVS` file, `analyze_stats.py`, `grade_v5.py` or other card's handoff was
edited by this unit.
