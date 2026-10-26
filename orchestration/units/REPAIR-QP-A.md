# REPAIR-QP-A — correct refuted prose in the quality-arm results

**Status:** done. **Bound:** 10 tool calls (used 10). **Zero live requests.**

## Purpose
`experiments/ptr-engine/quality/RESULTS.md` carried three sentences that its independent verifier refuted
(`orchestration/handoffs/V-QUALITY-ARM.json`, overall PARTIAL). Correct the prose to match the measured
rows; change no measured number; add no new figure; leave the discrimination result untouched.

## Write paths (declared, nothing else touched)
- `experiments/ptr-engine/quality/RESULTS.md`
- `orchestration/handoffs/REPAIR-QP-A.json`
- `orchestration/units/REPAIR-QP-A.md`

## What was corrected
1. `:150` "the avalanche column is empty / 48 requests, 0 avalanches" → states what the rows say: C rep2 T4
   `per_turn` = `avalanche: true`, `residue: 1`, `uncached: 34,190`, and the request-row residue column is
   `templated_prompt_tokens % 64` (≠ measured `prompt_tokens % 64` in 48/48 request rows).
2. `:174` telescoping identity "holds exactly" → refuted with the measured residuals A +151/+110/+106,
   B +117/+150/+127, C +159/+111/+17,193, D +100×3.
3. `:175-176` "completion of T1+T2+T3 carrying into the prefix" → 6 completion tokens vs a 17,193 gap; C
   rep2 raw prefix is 32,401 (the prose's 34,201 was a transcription error, annotated as such).
   `:147` C/T4 avalanche cell now shows `no` (request row) / `true` (rep row) — a flag, not a number.
4. Limitation stated once in plain words: `cached_tokens` read at `runner.py:585-596`, never persisted to
   `rows.jsonl`; `billed_tokens_measured` recomputed at `runner.py:688`; reconciliation needs a live re-run
   that persists the field (parked operator decision).
5. Corrections note appended at EOF naming the verifier path and the code-level defect.

## Evidence
- `rows.jsonl`: 115 rows; 48 request / 48 prediction / 12 rep / 4 corpus / 3 compaction. Request-row residue
  mismatches measured `prompt_tokens % 64` in **48/48**. C rep2 per-turn T4: `avalanche: true`, `residue: 1`,
  `uncached: 34,190`; rep `billed_tokens_measured` 49,594.
- `runner.py:585-596` reads `usage.prompt_tokens_details.cached_tokens`; `runner.py:688` is
  `"billed_tokens_measured": sum(t["prompt_tokens"] for t in turns)`.
- Discrimination untouched: A 3/3, B 0/3, C 3/3, D 0/3; D 0 of 5 withheld bodies per rep; `756741be`;
  index 458 B with its hash over the in-row `index_text`.

## Not done (deliberately)
No re-run, no rows edited, no `runner.py` change, no touch of `VERDICTS.md` or `QUALITY-ARM.json`.
