# REGRADE-DET — every on-disk checkpoint answer, re-graded with the repaired verifier

**PROVISIONAL — subject to V-DET-2.** Every number below comes from a zero-request re-read of files
already on disk. `V-DET-2` is verifying `det_verify.py` concurrently; nothing here is final and no
verdict here may be quoted as settled until that verification lands.

Unit: `REGRADE-DET`. Live model requests: **0**. Nothing graded was regenerated; no fixture, row,
grader or instrument file was modified (all paths read-only except the four declared write paths).

## 1. Instrument

| | |
|---|---|
| path | `experiments/ptr-engine/tools/det_verify.py` |
| sha256 | `12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439` |
| CLI | `python3 experiments/ptr-engine/tools/det_verify.py [--out ...]` |
| API used here | `det_verify.Truth() + det_verify.verify_probe({checkpoint: id}, answer_text, truth)` |
| coverage | 8/13 machine-decidable of 13 matrix entries |

The instrument was **imported and called** (`det_verify.Truth()`, `det_verify.verify_probe(...)`);
no matching logic was re-implemented in this unit. Its ground truth is the AST of the cited source:

- `DEFAULT_MAX_REFS` = **64** at `experiments/ptr-engine/ptr_engine/resolve.py:39` (sha256 `71a14c2c…`, fixture digest match: True)
- `^Ptr\w*$` classes = **31** in `experiments/ptr-engine/ptr_engine/errors.py` (sha256 `402dc958…`, match: True)
- `_refuse` calls `ledger.record_refusal` with kwargs `scope, serialized_ref, code` (`experiments/ptr-engine/ptr_engine/resolve.py:69`)

Decidable: `cp.0.t12`, `cp.1.t24`, `cp.2.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`, `acc.4`. **Undecidable (named, excluded from every accuracy below):** `repair.t30`, `acc.2`,
`acc.3`, `acc.n2b`, `acc.n3b..acc.n3e` — reasons in `regrade-det.json` under `instrument.undecidable_why`.

## 2. Inputs actually used

| rows file | sha256 (first 16) |
|---|---|
| `rows-longrun-c-2026-10-26.jsonl` | `aa7d6cfe9adedf9e` |
| `rows-longrun-2026-10-26.jsonl` | `bc61d38192d4e431` |
| `rows-longrun-2026-10-26-fix.jsonl` | `9d4ad90ce34cb781` |
| `rows-longrun-2026-10-26-policy.jsonl` | `9b1097234bf8d246` |
| `rows-longrun-v3-2026-10-26.jsonl` | `80d85fe0e977af16` |
| `rows-longrun-v4-2026-10-26.jsonl` | `999f298dac8b8356` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `f11391aa2989949f` |
| `rows-longrun-v5-tools.jsonl` | `586b66f27939bd05` |
| `rows-longrun-v6-tools.jsonl` | `1e78d75f259afbe0` |

Grade grids read for the v3 / v4 columns (each self-describes `rows_file` + `grader`):

`rows-longrun-2026-10-26-fix.grade-v4.json`, `rows-longrun-2026-10-26-policy.grade-v4.json`, `rows-longrun-2026-10-26.grade-v4.json`, `rows-longrun-c-2026-10-26.grade-v3.json`, `rows-longrun-c-2026-10-26.grade-v4.json`, `rows-longrun-v3-2026-10-26.grade-v3.json`, `rows-longrun-v3-2026-10-26.grade-v4.json`, `rows-longrun-v4-2026-10-26.grade-v3.json`, `rows-longrun-v4-2026-10-26.grade-v4.json`, `rows-longrun-v4-tools-2026-10-26.grade-v3.json`, `rows-longrun-v4-tools-2026-10-26.grade-v4.json`, `rows-longrun-v5-tools.grade-v3.json`, `rows-longrun-v5-tools.grade-v4.json`, `rows-longrun-v6-tools.grade-v3.json`, `rows-longrun-v6-tools.grade-v4.json`

Fixture: `LR-01.json` (sha256 `2c07e4610abf0a88`).

Not used (no checkpoint answers and/or not a graded grid): `rows-baseline-2026-10-26.jsonl`, `rows-equalinfo-2026-10-26.jsonl`, `rows-live-2026-10-26.jsonl`, `rows-pilot-thinking-2026-10-26.jsonl`, `rows.jsonl`.

**Tools-off control:** No separate tools-off control rows file exists; the non-`-tools` grids (rows-longrun-v4-2026-10-26.jsonl vs rows-longrun-v4-tools-2026-10-26.jsonl) are the control pair.

## 3. Enumeration

- **(run file, arm, checkpoint) triples with a recorded assistant answer: 56.**
- cells examined: 92 (4 checkpoint slots x 23 run/arm pairs); 36 are `missing` (no answer text in the rows at that turn), 13 `undecidable`.
- checkpoint ids that have answers somewhere on disk: `cp.0.t12`, `cp.1.t24`, `cp.2.t46`, `repair.t30`.
- **answerless acceptance ids** (`acc.1`, `acc.2`, `acc.3`, `acc.4`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.n2b`, `acc.n3b`, `acc.n3c`, `acc.n3d`, `acc.n3e`): no rows file carries an answer for any of them, so they are `missing`, never `fail`.
- `repair.t30` has answers but no source-derivable truth: `undecidable` for the instrument, excluded everywhere.
- `v6-tools` carries 5 checkpoint rows for 3 checkpoints (turns 12 and 46 appear twice as `kind=turn` and
  `kind=tool-followup`); the texts are byte-identical, deduped by text (`distinct_texts=1`).

## 4. Per arm, per run — accuracy over the decidable checkpoints only

`passed/decidable`; the decidable ids are listed, and `repair.t30` is named as excluded. `missing` cells
are *not* counted as failures and not counted in the denominator.

| run | arm | **det_verify** | passed | undecidable (excluded) | missing (not fail) | grade-v3 | grade-v4 |
|---|---|---|---|---|---|---|---|
| `longrun-c-2026-10-26` | lease-reopen | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-c-2026-10-26` | pointer-stable | **1/3** | cp.2.t46 | repair.t30 | — | 0/3 | 0/3 |
| `longrun-c-2026-10-26` | transcript-compact | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-c-2026-10-26` | transcript-grow | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-2026-10-26` | lease-reopen | **0/3** | — | repair.t30 | — | no v3 grid | 0/3 |
| `longrun-2026-10-26` | pointer-stable | **0/1** | — | — | cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26` | transcript-compact | **0/3** | — | repair.t30 | — | no v3 grid | 0/3 |
| `longrun-2026-10-26` | transcript-grow | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-fix` | lease-reopen | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-fix` | pointer-stable | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-fix` | transcript-compact | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-fix` | transcript-grow | **0/1** | — | — | cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-policy` | lease-reopen | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-policy` | pointer-stable | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-policy` | transcript-compact | **0/0** | — | — | cp.0.t12, cp.1.t24, cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-2026-10-26-policy` | transcript-grow | **0/2** | — | — | cp.2.t46, repair.t30 | no v3 grid | 0/3 |
| `longrun-v3-2026-10-26` | pointer-stable | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-v3-2026-10-26` | transcript-grow | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-v4-2026-10-26` | pointer-stable | **1/3** | cp.0.t12 | repair.t30 | — | 1/3 | 1/3 |
| `longrun-v4-2026-10-26` | transcript-grow | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-v4-tools-2026-10-26` | pointer-stable | **1/3** | cp.0.t12 | repair.t30 | — | 1/3 | 1/3 |
| `longrun-v5-tools` | pointer-stable | **0/3** | — | repair.t30 | — | 0/3 | 0/3 |
| `longrun-v6-tools` | pointer-stable | **2/3** | cp.0.t12, cp.2.t46 | repair.t30 | — | 1/3 | 2/3 |

The decidable denominator is always the 3 fact checkpoints `cp.0.t12`, `cp.1.t24`, `cp.2.t46`; a row
showing `/1`, `/2` or `/0` means the other checkpoints' answers are absent from that run file.

## 5. Cell-by-cell diff against v3 and v4

- `flips_vs_v3` = **2**, `flips_vs_v4` = **1** (cells where the deterministic verdict is `pass` and the old judge `fail`, or the reverse).
- Every flip is **fail -> pass**: no cell that v3/v4 passed is failed by the instrument, and **every flip is a case of the old judge being wrong**, not the new one (justification per row below).

| run | arm | cp | grade-v3 | grade-v4 | det_verify | answer chars |
|---|---|---|---|---|---|---|
| `longrun-c-2026-10-26` | pointer-stable | `cp.2.t46` | fail (`missing_anchor:raising`) | fail (`missing_anchor:raising`) | **pass** | 77 |
| `longrun-v6-tools` | pointer-stable | `cp.2.t46` | fail (`refused_while_knowable`) | pass (already `ok`) | **pass** | 225 |

Both flips are the same failure mode in two runs (the v6 row is a v3-only flip; v4 already accepted it):

- **`cp.2.t46`, `pointer-stable`, config C** — the recorded answer is exactly
  `ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)` (77 chars). v3/v4 failed it
  with `missing_anchor:raising` because the grader required the literal token `raising`. The checkpoint
  question is *"What does _refuse call, and what does it pass?"* — the answer names the AST-derived callee
  and all three keyword names, so the deterministic verdict (`call_shape_matches`) is right and the anchor
  demand was an artifact of bag-of-anchors grading. **Old judge wrong.**
- **`cp.2.t46`, `pointer-stable`, v6-tools** — 225 chars, the call is described in prose *and* restated after
  `ANSWER:` with all three keywords. v3 failed it with `refused_while_knowable` (`marker dropped anchors;
  missing raising`): v3 read only the text after `ANSWER:`, which necessarily drops the prose sentence, then
  asked that dropped segment for the `raising` anchor. That is the `grade_v3` marker rule failing, not the
  answer. **Old judge wrong.** (v4 already accepted this cell, `ok`.)
- Reverse direction: none. No cell where the instrument passes what v3/v4 failed *legitimately* and no cell
  where it fails what they passed.

## 6. The one number that matters

### Config C (`rows-longrun-c-2026-10-26.jsonl`, 4 arms x 48 turns)

| arm | det_verify | grade-v3 | grade-v4 |
|---|---|---|---|
| lease-reopen | **0/3** | 0/3 | 0/3 |
| pointer-stable | **1/3** | 0/3 | 0/3 |
| transcript-compact | **0/3** | 0/3 | 0/3 |
| transcript-grow | **0/3** | 0/3 | 0/3 |

**Config C does not stay at 0/3.** `pointer-stable` becomes **1/3**: exactly one cell flipped —
`cp.2.t46`, from v3 `missing_anchor:raising` and v4 `missing_anchor:raising` to `pass`
(`call_shape_matches`, callee `ledger.record_refusal` + keywords `scope, serialized_ref, code` all from
the AST; see §5). The other three arms stay at 0/3 for substantive reasons: `lease-reopen` asserts 2000 at
turn 12 and 15 at turn 24; `transcript-compact` returns tool calls only (no asserted value at either
turn); `transcript-grow` asserts 1 at both turns (its transcript dump is preamble, not a claim).

### v6-tools / `pointer-stable` (`rows-longrun-v6-tools.jsonl`)

| instrument | accuracy | cells |
|---|---|---|
| **det_verify** | **2/3** | `cp.0.t12` pass, `cp.1.t24` fail, `cp.2.t46` pass |
| grade-v3 | 1/3 | `cp.0.t12` pass; `cp.1.t24`, `cp.2.t46` fail |
| grade-v4 | 2/3 | `cp.0.t12`, `cp.2.t46` pass; `cp.1.t24` fail |

All three instruments agree `cp.1.t24` fails: the recorded answer is a tool call (turn 24 never returns
the count), and the instrument reports `no_asserted_value`/`asserted_value_mismatch` rather than a
token-miss. v3 understates by one cell (`cp.2.t46`); v4 agrees with the instrument on both passes.

## 7. Limits — what this instrument does not decide

- repair.t30 is undecidable (dialogue commitment, no source AST fact); excluded from every checkpoint_accuracy, so accuracies are over /3 decidable cells, never /3 assumed and never /4.
- cp.2.t46's handler compares callee + keyword names only; the fixture expected string also carries an ordering clause ('before re-raising') that the instrument does not decide. Both cp.2.t46 passes assert call shape, not ordering.
- config C rows carry no checkpoint object (expected=null); answers were located by the checkpoint turns the old graders used (12/24/46/30) and expected values taken from the fixture LR-01.json.
- v6-tools has 5 checkpoint rows for 3 checkpoints (turn 12 and 46 each appear twice, kind=turn and kind=tool-followup) with byte-identical content; deduped by text, distinct_texts=1 each.

Further honesty notes from the fail audit: several `fail` cells are failed with a *spurious* asserted
value because the answer's numerals come from a tool call, not a claim — e.g. `rows-longrun-v5-tools.jsonl`
`pointer-stable` `cp.0.t12` asserts `35` (a `start_line: 35` argument) and `rows-longrun-v6-tools.jsonl`
`cp.1.t24` asserts `1` (a `start_line: 1` argument). The verdicts are right (no count/budget is claimed)
but the `reason` mislabels them; no verdict flips. No fail was found where the answer states the correct
value and the instrument rejects it.

## 8. Reproduction

```
python3 experiments/ptr-engine/tools/det_verify.py            # instrument self-gate (FN=0/FP=0)
# regrade: import det_verify, D.Truth(), D.verify_probe({checkpoint: id}, answer_text, truth)
```

Machine-readable detail (all 92 cells, per-cell asserted/expected, old-judge reason, answer sha256):
`experiments/ptr-engine/measure/regrade-det.json`.
