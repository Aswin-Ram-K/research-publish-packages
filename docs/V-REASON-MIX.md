# V-REASON-MIX — independent recomputation of the reason-mix table

**Verdict: `partial`.** Offline, zero requests. Nothing existing was edited; this verdict reads the graders' own `reason` strings and re-derives the buckets with a classifier written without consulting `reason_mix.py`'s bucket table (then, separately, read that table to test it).

## 1. Do their five totals reproduce? Yes — exactly

I walked all 11 `*.grade-v5.json` documents `QUALITY-REASON-MIX.json` names, keyed every cell by `(rows_file, arm, checkpoint_id)`, and compared key sets: 75 cells on both sides, no omission, no double count.

| bucket | theirs | mine (my rule) |
|---|---|---|
| `never_answered` | 63 | **64** |
| `answered_wrong_value` | 0 | **1** |
| `answered_right_but_rejected_by_contract` | 3 | **1** |
| `undecidable` | 0 | 0 |
| `unclassifiable` | 0 | 0 |
| sum (= non-passes) | 66 | 66 |

Their sum, their 66 non-passes, their 9 passes (3 on real grids), their 3 real-grid passes at `cp.0.t12` with `ANSWER: 64`, and their `0/42` arithmetic all reproduce. The disagreement is not arithmetic — it is **two named cells in bucket 3**.

Verbatim reason census, all 75 cells: `prose_only` 28 (undecidable), `turn_missing` 21 (fail), `unparseable` 9 (undecidable), `num_equal` 7 (pass), `no_answer_line` 5 (undecidable), `answer_not_contract` 2 (fail), `call_equal` 2 (pass), `answer_not_contract:multiple_answer_lines` 1 (fail).

## 2. The mapping: right for bucket 1, wrong for two bucket-3 cells

For each distinct reason I applied my own rule:

| reason (verbatim) | bucket | agrees with theirs? |
|---|---|---|
| `prose_only` (28) | never_answered — no ANSWER line; 0 of 28 contains `64` | yes |
| `turn_missing` (21) | never_answered — no row at that turn | yes |
| `unparseable` (9) | never_answered — `answer_raw` is the runner sentinel `ANSWER: NOT-AN-ANSWER` | yes |
| `no_answer_line` (5) | never_answered — empty turn | yes |
| `answer_not_contract:multiple_answer_lines` (1) | **answered_wrong_value** | **no** |
| `answer_not_contract`, `answer_raw` null (1) | **never_answered** | **no** |
| `answer_not_contract`, `answer_raw` = the ledger CALL (1) | answered_right_but_rejected_by_contract | yes |

**F2 — a wrong value is hiding in bucket 3.** `rows-longrun-v3` / `pointer-stable` / `cp.1.t24`, from `cell-longrun-v3-20261026T1556Z.grade-v5.json`: `verdict "fail"`, `reason "answer_not_contract:multiple_answer_lines"`, `answer_raw "ANSWER: 7"`, `expected 31`, `asserted null`. The claim files it under *answered_right* but rejected by contract. `7 != 31`. That reply answered, in contract shape, and answered wrongly; the grader stopped at "two ANSWER lines" and never compared the numeral.

**F3 — a non-answer is counted as a contract rejection.** `rows-longrun-v6-tools` / `pointer-stable` / `cp.1.t24` has `reason "answer_not_contract"` and `answer_raw null`. There is no answer line to be right about. Re-derived with the current grader (`measure/regrade/rows-longrun-v6-tools.grade-v5.json`) the same cell is `undecidable` / `prose_only`.

**F4 — one bucket-3 cell is genuine.** `cp.2.t46` answers `ANSWER: ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)`: exact callee, exact kwarg set, exact values, keyword order only. `grade_v5.py` grades callee + name set + value text and says order is "a formatting rule, not a truth rule". Right answer, rejected for form — bucket 3 is correct here.

## 3. Is `answered_wrong_value` structurally empty? No — empirically empty only

Built three throwaway rows in memory (no file written) and passed them to `grade_v5.grade_rows` against the same fixture:

- `ANSWER: NUM 65` (truth 64) → `fail` / **`num_mismatch`** / `asserted 65`
- `ANSWER: NUM 999` (truth 31) → `fail` / **`num_mismatch`** / `asserted 999`
- `ANSWER: CALL ledger.record_refusal(code=WRONG.code, ...)` → `fail` / **`kwarg_value_mismatch:code`**

So a correct-format wrong value *is* gradable and does grade `fail`. The contract does not blur wrong into absent.

**But the mapping cannot receive one.** `reason_mix.py` `REASON_BUCKET` keys `answered_wrong_value` on `number_wrong`, `missing_anchor`, `keyword_missing`, `callee_mismatch`, `keyword_mismatch` — all `grade_v4` vocabulary. The reasons `grade_v5.py` actually emits for a wrong value are `num_mismatch`, `kwarg_value_mismatch:<name>`, `kind_mismatch:<K>_expected`, `num_not_integer:<n>`, `none_but_call_exists`, `none_contradicted_by_source` — **none of them is in the table**. Calling the author's own classifier:

```
classify('fail','num_mismatch')               -> ('unclassifiable', "reason 'num_mismatch' not in REASON_BUCKET")
classify('fail','kwarg_value_mismatch:code')  -> ('unclassifiable', ...)
classify('fail','kind_mismatch:NUM_expected') -> ('unclassifiable', ...)
```

`answered_wrong_value: 0` is therefore unmeasured on this grader family, not measured — a wrong-value cell would have landed in `unclassifiable`, and `unclassifiable: 0` does not detect that because no cell exercised the path.

## 4. The 0 % arithmetic

Denominator reproduces: 66 non-passes − 24 pointer-stable non-passes = 42 (lease-reopen 12 + transcript-compact 12 + transcript-grow 18). Numerator 0. `0/42 = 0.0 % < 60 %`, so **`threshold_met false` is the correct verdict under the card's own rule**.

What is honest to say next: the test is **inapplicable, not failed**. All 42 non-pointer non-passes are non-answers, so the denominator holds nothing whose contract compliance could be measured. The card's reading — H3 measures whether an arm answers at all — is the correct one. The threshold line over-reads it into a compliance result, and the published headline repeats that over-read.

## 5. The three passes and their eras

| grid | source | generated_at | era |
|---|---|---|---|
| `rows-longrun-v4` | `cell-longrun-v4-…1556Z` | 15:56:19 | current — "byte-identical re-derivation" |
| `rows-longrun-v4-tools` | `cell-longrun-v4-tools-…1556Z` | 15:56:19 | current — "byte-identical re-derivation" |
| `rows-longrun-v6-tools` | `cell-pointer-stable-…145722Z` | **14:57:22** | **pre-T3** — "re-derivation DIFFERS: arms.pointer-stable.cells" |

All three declare `grader: grade_v5` with an identical `rule` (`ANSWER-CONTRACT v1`) and the same fixture `LR-01.v5.json` — the same family, **not** the same repair era, and no grader sha is recorded in any of them. The third pass nevertheless survives the era change: the current-grader re-derivation `measure/regrade/rows-longrun-v6-tools.grade-v5.json` still grades `cp.0.t12` pass / `num_equal` / `ANSWER: 64`. Bucket 3 is the part that does *not* survive: recomputing the same 69-cell population with the current grader gives `65 / 0 / 1 / 0 / 0`, because that pre-T3 document's two `answer_not_contract` cells become `prose_only` and `unparseable`.

## 6. One sentence

The quality pillar as graded measures answer **presence in contract form**, not answer correctness: 5 of 69 real-grid cells emitted an ANSWER line (3 right, 1 verifiably wrong, 1 right-but-out-of-form), so the number that separates the two readings is the attempted-answer rate **5/69 = 7.2 %** against correctness-among-attempts **3/5 = 60 %** — while "zero wrong-value answers in 66 non-passes" is an artefact of a bucket keyed to reasons the current grader never emits, plus one wrong value (`ANSWER: 7` vs 31) parked in the contract bucket.

## Note on containment

Files read only. New files written: this document, `experiments/ptr-engine/measure/V-REASON-MIX.json`, `orchestration/units/V-REASON-MIX.md`, `orchestration/handoffs/V-REASON-MIX.json`, `orchestration/journals/V-REASON-MIX.jsonl`. The synthetic wrong-value rows existed only in memory. `grade_v5.py`, the fixture, the claim JSON, and every grade document were not modified.
