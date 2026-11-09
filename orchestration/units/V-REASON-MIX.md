# UNIT V-REASON-MIX — verifier of QUALITY-REASON-MIX

**Status: complete, verdict `partial`.** Bound ≤24 tool calls / 0 requests — used 18 calls, 0 requests.
Persisted card (this file), write paths honoured exactly.

## Purpose

Independently recompute the reason-mix table published by `QUALITY-REASON-MIX` (card `6f5baffe`) into
`experiments/ptr-engine/measure/QUALITY-REASON-MIX.json`, from the grade documents rather than from its
JSON, with a classification written from the grader's verbatim `reason` strings.

## Attacks carried out

1. **Re-derive denominators** from the 11 named `*.grade-v5.json` docs. 75 cells both sides, key-set equal,
   no omission, no duplication. Their `63 / 0 / 3 / 0 / 0 = 66` reproduces exactly.
2. **Attack the mapping.** Every one of 8 distinct reason strings enumerated verbatim; my rule agrees on 5
   families (63 cells) and disagrees on 2 cells inside bucket 3.
3. **Is `answered_wrong_value` structurally empty?** No. Synthetic in-memory rows grade `fail` with
   `num_mismatch` (65 vs 64, 999 vs 31) and `kwarg_value_mismatch:code`. The bucket is empty empirically —
   and unreachable by construction anyway, because `reason_mix.REASON_BUCKET` keys bucket 2 on `grade_v4`
   reasons (`number_wrong`, …) that `grade_v5` never emits.
4. **0 % arithmetic.** `0/42` and `threshold_met false` are arithmetically correct; the test is inapplicable,
   not failed, because all 42 are non-answers.
5. **Three passes.** Two current-era, one pre-T3 (`cell-pointer-stable`, QUALITY-ERAS: "re-derivation
   DIFFERS"); that third pass nonetheless re-derives to pass under the current grader.
6. **Nothing relaxed.** No existing file edited; no grade document, grader, fixture or claim JSON touched.
   Synthetic rows existed only in memory.

## Verdict basis

`partial` — totals reproduce, but bucket 3 misclassifies two named cells (a wrong value `ANSWER: 7` vs 31,
and a null answer), and the bucket-2 vocabulary is from the wrong grader generation.

## Write paths

`experiments/ptr-engine/measure/V-REASON-MIX.json`, `docs/V-REASON-MIX.md`,
`orchestration/units/V-REASON-MIX.md`, `orchestration/handoffs/V-REASON-MIX.json`,
`orchestration/journals/V-REASON-MIX.jsonl`.
