# UNIT `QUALITY-ERA-TABLE`

**Purpose (one).** Publish the quality record **once, with its grader era named**, so no published accuracy
figure can be re-read as if it came from the current judge. Offline: zero inference requests, no new live data.

**Bound.** 26 tool calls; wrote the deliverables by call 18 and the handoff inside the bound.

**Write paths (exactly).** `docs/QUALITY-ERAS.md` · `experiments/ptr-engine/measure/QUALITY-ERAS.json` ·
`orchestration/units/QUALITY-ERA-TABLE.md` · `orchestration/handoffs/QUALITY-ERA-TABLE.json` ·
`orchestration/journals/QUALITY-ERA-TABLE.jsonl`. Nothing else was written; no rows file, `*.grade-v5.json`,
`docs/OPERATOR-BRIEF.md`, `measure/OPERATOR-BRIEF.json`, `measure/PUBLISHED-NUMBERS.json`, `TVS` file,
`analyze_stats.py`, `grade_v5.py` or another card's handoff was touched.

**Inputs read.** `measure/REGRADE.json`, `measure/regrade/*.grade-v5.json` (9), the 11 stored
`measure/cell-*.grade-v5.json`, `measure/MATRIX-HONESTY.json`, `tools/regrade.py`, `tools/matrix_audit.py`,
`tools/det_verify.py`, `docs/GRADE-V5-REPAIR.md`, `docs/REGRADE.md`, `orchestration/handoffs/REGRADE-ONE-COMMAND.json`.

## What was measured

| reading | grade_v5.py grid (23 pairs) | per-arm |
|---|---|---|
| as recorded on disk | **3/27 = 11.1 %** | pointer-stable 3/12, transcript-grow 0/3, lease-reopen 0/6, transcript-compact 0/6 |
| all pairs under current grader (sha 6893d5…) | **3/25 = 12.0 %** | pointer-stable 3/10, others unchanged |

The brief's **5/43 = 11.6 %** was checked separately: it is `det_verify.py` sha256 `12ccc74e…` via
`matrix_audit.py`, and re-deriving it in memory reproduces `states`, `accuracy`, `per_arm` and
`declared_cells` identically. It is **current**, not era-mixed; only the `grade_v5` grid carries the drift.

## Why the drift exists

`docs/GRADE-V5-REPAIR.md:54-63` (T3): a non-answer is `undecidable`, not `fail`. Two cells move in
`rows-longrun-v6-tools` / `pointer-stable`: `cp.1.t24` (`answer_not_contract` → `prose_only`) and `cp.2.t46`
(`answer_not_contract` → `unparseable`). The numerator never changes — only the denominator.

## Known gap this unit did not close

No stored `*.grade-v5.json` records a grader sha256 (0 of 11). Era is therefore decided only by
re-derivation. 4 of 50 grade files are undatable here (2 `cell-transcript-grow` grade-v5 whose rows live in
`/tmp` and `.cell-demo`, 2 `grade-v2` with no grader field), and 2 further files are named `grade-v4` but were
written by `grade_v3`. A separate card should make `grade_v5.py` write `grader_sha256` at write time.

## Assumptions (automated session, no answerer)

1. The "headline recomputed both ways" is reported **twice** — once for the `grade_v5` grid, which
   `regrade.py` can re-derive, and once as the cross-check on the brief's `5/43`, which it cannot. The card's
   premise that 5/43 is era-mixed did not survive the check; the measured finding is recorded instead of the
   premise.
2. `byte-identity` is read as `regrade.py`'s dict-wise identity ignoring `generated_at`, which is what the tool
   actually computes and what `docs/REGRADE.md` documents.
