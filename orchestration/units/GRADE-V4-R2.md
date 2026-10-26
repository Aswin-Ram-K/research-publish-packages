# UNIT GRADE-V4-R2 — implement frozen anchor rule R2 in a new grader, re-grade every grid

- **Objective:** implement R2 (ANCHOR-PREREG.md §1, frozen 2026-10-26T13:29:21Z) in a NEW
  `experiments/ptr-engine/longrun/grade_v4.py`; `required_anchors` derived from occurrence-context
  classification; re-grade every grid on disk to `*.grade-v4.json`; prove the guard red→green in
  `experiments/ptr-engine/longrun/tests/test_grade_v4.py`.
- **Hard bound:** ≤28 tool calls, zero network requests, automated (never ask_user_question).
- **Read-only:** `grade_v3.py`, `grade_v2.py`, `score_longrun.py`, `analyze_longrun.py`, fixtures,
  rows, existing grade files, `ANCHOR-PREREG.md`, `tools/anchor_prereg_check.py`.
- **Write paths:** exactly the five listed by the card (grade_v4.py, tests/test_grade_v4.py,
  measure/*.grade-v4.json, this card, orchestration/handoffs/GRADE-V4-R2.json).
- **Acceptance:** realized flips ≤3 of 39; C-grid `not_applicable` and inert; four test exits recorded;
  one red exit with the classifier stubbed to always-CODE-SYMBOL.
- **Status:** done. `status: done` handoff: `orchestration/handoffs/GRADE-V4-R2.json`.

## Normative reading used
R2 §1 (lines 31-53): required = CODE-SYMBOL + NUMBER; PROSE-CONNECTOR informational. Classification is
by occurrence context in the cited file, computed with `tokenize` STRING/COMMENT line coverage
(the §1.1 amendment: `raising` occurs at `resolve.py:67` only inside a docstring). Reused verbatim from
`tools/anchor_prereg_check.py` (`prose_lines`, `occurrences`, `classify`, `anchors`, `has_anchor`) by
import so there is exactly one implementation of the rule.


## Result — realized flips **1 of 39** (prereg bound ≤3)

| grid | arm | checkpoint | R1 verdict | R2 verdict | flipped? |
|---|---|---|---|---|---|
| c-2026-10-26 | lease-reopen | cp.0.t12 | FAIL (number_wrong:2000) | FAIL (number_wrong:2000) | - |
| c-2026-10-26 | lease-reopen | cp.1.t24 | FAIL (number_wrong:15) | FAIL (number_wrong:15) | - |
| c-2026-10-26 | lease-reopen | cp.2.t46 | FAIL (missing_anchor:ledger) | FAIL (missing_anchor:ledger) | - |
| c-2026-10-26 | pointer-stable | cp.0.t12 | FAIL (number_wrong:39) | FAIL (number_wrong:39) | - |
| c-2026-10-26 | pointer-stable | cp.1.t24 | FAIL (number_wrong:7) | FAIL (number_wrong:7) | - |
| c-2026-10-26 | pointer-stable | cp.2.t46 | FAIL (missing_anchor:raising) | FAIL (missing_anchor:raising) | - |
| c-2026-10-26 | transcript-compact | cp.0.t12 | FAIL (preamble_only) | FAIL (preamble_only) | - |
| c-2026-10-26 | transcript-compact | cp.1.t24 | FAIL (preamble_only) | FAIL (preamble_only) | - |
| c-2026-10-26 | transcript-compact | cp.2.t46 | FAIL (missing_anchor:ledger) | FAIL (missing_anchor:ledger) | - |
| c-2026-10-26 | transcript-grow | cp.0.t12 | FAIL (value_not_in_concluding_position) | FAIL (value_not_in_concluding_position) | - |
| c-2026-10-26 | transcript-grow | cp.1.t24 | FAIL (number_wrong:12) | FAIL (number_wrong:12) | - |
| c-2026-10-26 | transcript-grow | cp.2.t46 | FAIL (missing_anchor:raising) | FAIL (missing_anchor:raising) | - |
| v3-2026-10-26 | pointer-stable | cp.0.t12 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26 | pointer-stable | cp.1.t24 | FAIL (number_wrong:7) | FAIL (number_wrong:7) | - |
| v3-2026-10-26 | pointer-stable | cp.2.t46 | FAIL (refused_while_knowable) | FAIL (refused_while_knowable) | - |
| v3-2026-10-26 | transcript-grow | cp.0.t12 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26 | transcript-grow | cp.1.t24 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26 | transcript-grow | cp.2.t46 | FAIL (refused_while_knowable) | FAIL (refused_while_knowable) | - |
| v3-2026-10-26-final | pointer-stable | cp.0.t12 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26-final | pointer-stable | cp.1.t24 | FAIL (number_wrong:7) | FAIL (number_wrong:7) | - |
| v3-2026-10-26-final | pointer-stable | cp.2.t46 | FAIL (refused_while_knowable) | FAIL (refused_while_knowable) | - |
| v3-2026-10-26-final | transcript-grow | cp.0.t12 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26-final | transcript-grow | cp.1.t24 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v3-2026-10-26-final | transcript-grow | cp.2.t46 | FAIL (refused_while_knowable) | FAIL (refused_while_knowable) | - |
| v4-2026-10-26 | pointer-stable | cp.0.t12 | PASS (ok) | PASS (ok) | - |
| v4-2026-10-26 | pointer-stable | cp.1.t24 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v4-2026-10-26 | pointer-stable | cp.2.t46 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v4-2026-10-26 | transcript-grow | cp.0.t12 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v4-2026-10-26 | transcript-grow | cp.1.t24 | FAIL (marker_without_value) | FAIL (marker_without_value) | - |
| v4-2026-10-26 | transcript-grow | cp.2.t46 | FAIL (missing_anchor:ledger) | FAIL (missing_anchor:ledger) | - |
| v4-tools-2026-10-26 | pointer-stable | cp.0.t12 | PASS (ok) | PASS (ok) | - |
| v4-tools-2026-10-26 | pointer-stable | cp.1.t24 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v4-tools-2026-10-26 | pointer-stable | cp.2.t46 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v5-tools | pointer-stable | cp.0.t12 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v5-tools | pointer-stable | cp.1.t24 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v5-tools | pointer-stable | cp.2.t46 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v6-tools | pointer-stable | cp.0.t12 | PASS (ok) | PASS (ok) | - |
| v6-tools | pointer-stable | cp.1.t24 | FAIL (marker_missing) | FAIL (marker_missing) | - |
| v6-tools | pointer-stable | cp.2.t46 | FAIL (refused_while_knowable) | PASS (ok) | YES |

R2 flipped exactly one arm-check: `v6-tools / pointer-stable / cp.2.t46`
`refused_while_knowable` → `ok` — the prose anchor `raising`. Zero checks went PASS→FAIL and zero
unexpected FAIL→PASS (checked across all 39). The C grid is **inert**: no `answer_marker` is required
there, so all four arms report `r2_status: not_applicable` and their checkpoint accuracy is `0/3`,
byte-identical to grade-v3; its two `missing_anchor:raising` checks stay FAIL, which is why this run
does not reproduce the prereg's "would flip ≤2" count for that grid — that count assumed R2 applied.

## Guard

`tests/test_grade_v4.py` green exit 0 (4/4 assertions); `--stub-code` red exit 1 (assertion 1
fails when the occurrence-context classifier is stubbed to always CODE-SYMBOL = R1).

## R2 rule, as implemented

`required_anchors(expected, source)` = tokens of `grade_v3.anchors(expected)` whose occurrence in the
cited file is outside any STRING/COMMENT token, imported from `tools/anchor_prereg_check.py`. Non-numeric
judging uses that set for `missing` and the concluding-position test; numbers keep `number_in()`.
