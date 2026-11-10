# V-SPCC-1 — Verify FINDINGS-LEDGER.md

## Verdict

Masking conflict settled: `RESULTS-TX02-CELL1.md` line 20 (table row masking rep 1) reads `12/48` total (d=2 12/12, d=8/20/32 0/12 each); line 82 boundary statement confirms. `RESULTS-STACK-8014.md` line 24: TX-03 masking r1 8/48. The programme summary's "0/48 on both stacks" is unsupported; the per-bucket 8/48 is a per-stack total on :8014 only. Correct phrasing: masking scores 12/48 on :8012 and 8/48 on :8014, both entirely from the d=2 bucket.

## Settling sentence

`RESULTS-TX02-CELL1.md` line 20: `| masking-no-fetch | 1 | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 | 12/48 |`

## Row table

| row | claimed | source says | verdict |
|---|---|---|---|
| Masking past eviction | 0/48 on both stacks; 8/48 total from d=2 | :8012 12/48 (TX-02 line 20); :8014 8/48 (STACK-8014 line 24) | corrected |
| Bounded fetch single-fact recall | 41/48 (:8012), 42/48 (:8014) | STACK-8014 lines 38, 61 | VERIFIED |
| Bounded fetch aggregation | 4/48 (:8012), 0/48 w/ 243 calls (:8014) | STACK-8014 lines 26, 41 | VERIFIED |
| Bounded fetch two-fact chain | 9/48 both stacks | STACK-8014 lines 29, 62 | VERIFIED |
| Payload cut vs billed cut | −24.2% payload, −2.4% billed | MEASURED_FACTS F1 line 12; DO_NOT_REDO line 7 | VERIFIED |
| Append-only cache hit climb | 0 → 0.489 | MEASURED_FACTS F2 line 13 | VERIFIED |
| Rewrite cost 48/72-byte handle | D-086 repayment step cost | MEASURED_FACTS F3 line 14 (was cited as DO_NOT_REDO — wrong file) | VERIFIED (source corrected) |

## Rules / open questions

Four rules present (lines 6-9). Open questions section: 5 one-line entries — within bound.