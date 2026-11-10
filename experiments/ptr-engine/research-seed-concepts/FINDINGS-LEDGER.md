# Findings Ledger — Serving × Context Programme

One row per finding so the two programmes (Consonance and the context×serving experiment) stop telling two stories. Priced in **billed** tokens from the server's own cache report, never in payload size.

Rules:
- A row may not cite a live path for a value that changes — pin the digest instead.
- ABSENT ≠ 0
- DERIVED ≠ MEASURED
- No cross-build comparison.

| Finding | Number | Units | Source | Generation | Replicates on :8012 / :8014 | Status |
|---|---|---|---|---|---|---|
| Masking past eviction | 12/48 on :8012 (TX-02, all 12 at d=2); 8/48 on :8014 (TX-03, all 8 at d=2) (corrected from "0/48 on both stacks" — see RESULTS-TX02-CELL1.md line 20 and RESULTS-STACK-8014.md line 24) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md` (line 20: masking rep 1 12/48, d=2 12/12, d=8/20/32 0/12 each; line 82 boundary statement); `RESULTS-STACK-8014.md` (line 24: TX-03 masking r1 8/48) | TX-02 cell 1; TX-03 stack check | :8012 masking 12/48 (TX-02, line 20); :8014 masking 8/48 (TX-03, line 24) | VERIFIED (masking scores 12/48 on :8012 and 8/48 on :8014, both entirely from the d=2 bucket; "0/48 on both stacks" was unsupported) |
| Bounded fetch, single-fact recall | 41/48 (`:8012`), 42/48 (`:8014`) | score out of 48 checkpoints | `RESULTS-TX02-CELL1.md`, `RESULTS-STACK-8014.md` (line 38) | TX-03 | :8012 41/48; :8014 42/48 | VERIFIED (`RESULTS-STACK-8014.md:38` and `:61`) |
| Bounded fetch, aggregation | 4/48 (`:8012`), 0/48 with 243 fetch calls (`:8014`) | score out of 48 checkpoints; fetch calls | `RESULTS-KINDS-2-agg-abs.md` (line 35: 0/48 and 4/48; line 112 activation gate) | TX-AGG | :8012 4/48; :8014 0/48 (243 calls, line 26 of STACK-8014) | VERIFIED (`RESULTS-KINDS-2-agg-abs.md:35`; `RESULTS-STACK-8014.md:26`) |
| Bounded fetch, two-fact chain | 9/48 both stacks | score out of 48 checkpoints | `RESULTS-KINDS-2-agg-abs.md`, `RESULTS-STACK-8014.md` (line 62) | TX-HOP | :8012 9/48; :8014 9/48 | VERIFIED (`RESULTS-STACK-8014.md:57,62`) |
| Payload cut vs billed cut | −24.2% payload, −2.4% billed | % of tokens | Consonance `EXP#43` — `handoff from consonance/MEASURED_FACTS.md` (F1, line 12); `handoff from consonance/DO_NOT_REDO.md` (line 7) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:12`; `DO_NOT_REDO.md:7`) |
| Append-only cache hit climb | 0 → 0.489 | cached fraction | `handoff from consonance/MEASURED_FACTS.md` (F2, line 13) | EXP#43 | n/a (Consonance single build) | VERIFIED (`MEASURED_FACTS.md:13`) |
| Rewrite cost per 48/72-byte handle | D-086 repayment step cost (48 of 72 prefix bytes moved) | prefix bytes moved | `handoff from consonance/MEASURED_FACTS.md` (F3, line 14); `handoff from consonance/DO_NOT_REDO.md` (D-086) | D-086 | n/a | VERIFIED (`MEASURED_FACTS.md:14` — "48 of 72 prefix bytes"; DO_NOT_REDO.md cites D-086) |

## Open questions this ledger does not answer

- Is the distance cliff a matter of presence or position (E3)?
- Whether bounded fetch's aggregation ceiling can be lifted above 4/48.
- Whether a fork of SGLang is justified (per-range eviction, non-prefix reuse, per-range attribution).
- Whether Nemotron Nano can hold the answer contract at or above occamy.
- Whether HiCache pays for itself in billed tokens (E5).
