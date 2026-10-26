# REGRADE-DET — re-grade every on-disk checkpoint answer with the repaired verifier

**PROVISIONAL — subject to V-DET-2.**

## Purpose
Every quality number quoted so far came from `grade_v3.py` (bag-of-anchors) or `grade_v4.py`
(range-scoped tokens), both measured unfit by `GRADE-FIT-CONTROL` (v3 FN 30.8 % / FP 45.5 %;
v4 FN 26.9 % / FP 50.0 %). `DET-VERIFY-FIX` (`e49b6f7a`) repaired
`experiments/ptr-engine/tools/det_verify.py` to derive ground truth from the source AST. This unit
puts that instrument over the answers **already on disk**, so the arm comparison stops resting on a
broken judge. It spends **no request** and decides no arm: it converts existing answer text into
verdicts.

## Hard bound
≤24 tool calls, zero live requests, offline. **Used: 17 calls, 0 requests.** (Handoff persisted as
`status: partial` at call 5, then updated.)

## Method (instrument used as-is, never re-implemented)
1. Enumerated every `(run file, arm, checkpoint)` triple with a recorded assistant answer across the
   graded grids: `rows-longrun-c-2026-10-26`, `rows-longrun-2026-10-26`, `...-fix`, `...-policy`,
   `rows-longrun-v3-2026-10-26`, `rows-longrun-v4-2026-10-26`, `rows-longrun-v4-tools-2026-10-26`,
   `rows-longrun-v5-tools`, `rows-longrun-v6-tools`.
2. Called `det_verify.Truth()` + `det_verify.verify_probe({"checkpoint": id}, answer_text, truth)`
   on each answer. No matching logic re-implemented; nothing edited.
3. Config-C rows carry no `checkpoint` object, so answers were located by the checkpoint turns the old
   graders used (12 / 24 / 46 / 30); expected values taken from fixture `LR-01.json`.
4. Diffed each cell against `grade-v3` and `grade-v4` from the grids' own `arms.<arm>.checks`.

## Result (all numbers from `experiments/ptr-engine/measure/regrade-det.json`)
- **56 triples** with an answer; 92 cells examined; **36 `missing`** (answer absent from the rows —
  never counted as fail); 13 `undecidable`; 38 fail; 5 pass.
- **Config C:** `pointer-stable` 1/3 (v3 0/3, v4 0/3); other three arms 0/3. **C does not stay at 0/3.**
- **v6-tools / pointer-stable:** det **2/3** vs v3 1/3 vs v4 2/3.
- **`flips_vs_v3` = 2, `flips_vs_v4` = 1**, all fail→pass, all **old judge wrong** (both are
  `cp.2.t46` `pointer-stable`: v3/v4 demanded the literal token `raising`, which the checkpoint
  question never asks; the answer names the AST-derived callee + all three keywords).
- No pass→fail flip: the instrument never overturned a legitimate old pass.

## Limits (stated, not approximated)
- `repair.t30` is undecidable (dialogue commitment, no AST fact) → excluded from every denominator, so
  accuracies are over /3 decidable cells.
- `cp.2.t46`'s handler compares callee + keyword names only; the fixture expected string also carries
  the ordering clause "before re-raising", which the instrument does not decide.
- `acc.*` checkpoints have **no answer rows anywhere** → `missing`, never `fail`.
- Some fails carry a spurious asserted value (a numeral from a tool-call argument, e.g. `start_line:
  35`); the verdict is right, the `reason` label is loose. No verdict flips.

## Write paths (exactly these four)
- `experiments/ptr-engine/measure/regrade-det.json`
- `experiments/ptr-engine/measure/REGRADE-DET.md`
- `orchestration/units/REGRADE-DET.md`
- `orchestration/handoffs/REGRADE-DET.json`

## Next
`V-DET-2` verifies the instrument; if its verdict changes a rule, this regrade must be re-run
(one command, no requests). Nothing here may be quoted as settled before that.
