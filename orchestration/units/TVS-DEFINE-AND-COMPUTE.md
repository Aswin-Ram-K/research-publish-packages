# UNIT `TVS-DEFINE-AND-COMPUTE`

**Card:** `12af69cc-76fe-404c-a5c7-ec9d2b08b3e8` · execution `49d7b210-f43f-4718-aa65-bbfd7624fc43`
**Mode:** automated, offline. Zero inference requests, no network, no `git`. Row/grade files read-only.
**Gated on:** `ATTACK-GRADE-V5-2` (751d5f3e) and `LATENCY-REPORT` (9bf0d318), both settled.

## Purpose
Define the operator's second headline metric, tokens-to-verified-success (TVS), settle its denominator, and
compute it — after resolving the contradiction between `LATENCY-REPORT.json` ("n_verified_success = 0 in every
grid") and the grade files / `V6-RESULT.md` (`cp.0.t12` PASS).

## Outcome
- Contradiction resolved: **the "0" side was wrong for this metric**. `docs/LATENCY-REPORT.md:363-368` required
  "a decidable verdict at **all four** declared checkpoints", and `repair.t30` is judge-undecidable in 13/13 pairs,
  so the rule had a structurally zero denominator. The grade files' `verified_success` field
  (`grade_v5.py:814`) is that same arm-level conjunction and is `false` in every arm. A **checkpoint-level** pass
  (`cp.0.t12`, turn 12) exists and is a verified success.
- `repair.t30` **dropped** from TVS's declared space (no `grade_v5` verdict exists for it; making it decidable
  would be a loosening). Denominator 4 → 3 ids per arm; H3 margin restored to the frozen 2/12 = 16.7 pp
  (2/13 = 15.4 pp with it counted).
- Definition written in `docs/TVS.md` before any number; computed by
  `experiments/ptr-engine/tools/tokens_to_verified.py` into `experiments/ptr-engine/measure/TVS.json`
  (`--all` mode) and rendered in `docs/TVS-RESULTS.md`.

## Numbers
| item | value |
|---|---|
| declared run/arm pairs | 23 |
| pairs with a `grade_v5` output | 1 |
| pairs with a verified success | **1** |
| pairs `null / no_verified_success` | 0 |
| pairs `not_produced` | 22 (no `grade_v5` output; re-grading forbidden) |
| **TVS of record** | `rows-longrun-v6-tools` / `pointer-stable`: **111,994 tokens** at **turn 12** (prompt 109,780 + completion 2,214), cached share **85.23%** |
| whole-run total, never used | 307,380 |
| duplicate records skipped (v6) | 11 |

## Tests
`experiments/ptr-engine/longrun/tests/test_tokens_to_verified.py` — 7 passed (T6 cutoff, T12-in-48, no-pass null,
null completion excluded, fetch follow-up included, duplicate counted once, in-test red→green).
Live red→green: whole-run cutoff → `3 failed, 4 passed` (T12 total 5280 vs 1320); restored → `7 passed`.

## Bound
≤32 tool calls (used 24), zero requests. Handoff written `partial` at call 5, then final.

## Write paths (exactly)
`docs/TVS.md`, `docs/TVS-RESULTS.md`, `experiments/ptr-engine/tools/tokens_to_verified.py`,
`experiments/ptr-engine/longrun/tests/test_tokens_to_verified.py`, `experiments/ptr-engine/measure/TVS.json`,
`orchestration/units/TVS-DEFINE-AND-COMPUTE.md`, `orchestration/handoffs/TVS-DEFINE-AND-COMPUTE.json`,
`orchestration/journals/TVS-DEFINE-AND-COMPUTE.jsonl`

## Next
Run `grade_v5` offline over the 8 long-run rows files with no `grade_v5` output (0 requests) to convert 22
`not_produced` pairs into decided ones. Repairing the fixture to carry the 12 declared checkpoint ids is a
separate card and is what H3 actually needs.
