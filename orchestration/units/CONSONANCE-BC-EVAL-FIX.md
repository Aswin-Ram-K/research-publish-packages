# CONSONANCE-BC-EVAL-FIX — surgical corrections to the protocol

**Status:** done (no experiment, no model call, no live request, no spend).
**Date:** 2026-11-03. **Bound:** 25 tool calls; used well inside it.
**Trigger:** `orchestration/handoffs/V-CONSONANCE-BC-EVAL.json` — one material arithmetic defect and four
minor template defects. This unit applies exactly those edits; it does not rewrite the protocol, the
report, the sources, or any frozen record.

**Declared write paths (only these):**
- `research/next-candidates/consonance-bounded-context-evaluation.md` (surgical `edit` calls only)
- `orchestration/units/CONSONANCE-BC-EVAL-FIX.md`
- `orchestration/handoffs/CONSONANCE-BC-EVAL-FIX.json`

**Read:** `orchestration/handoffs/V-CONSONANCE-BC-EVAL.json`; the protocol at
`research/next-candidates/consonance-bounded-context-evaluation.md`; `handoff from consonance/EXPERIMENTS.md`
lines 21/30–31 (control thresholds).

## Corrections applied

1. **§6.3 request total (material).** `5,040` covers arms A, B, C, E at one request per turn; arm D at
   2 req/turn adds `2 × 420 × 3 = 2,520`, so the total is **7,560** and the ratio is
   **7,560 / 1,729 = 4.3725 ≈ 4.37×**, not 6,300 / 3.64×. The block now reads
   `turns 420 → four one-request arms 1,680/rep → 3 reps 5,040 → D adds 2,520 → total 7,560 → ≥7,560 with
   digests/checkpoints`. The following prose (`~3.6×` → `~4.4× (4.37×)`) and the owner-decision sentence
   (`≥6,300` → `≥7,560`) were corrected with it. **`UNFUNDED` is unchanged and stronger**: the "even if D
   were free" figure stays 5,040 / 1,729 = 2.92×.
2. **§5 draft `run.json` option (b) caps.** `150 per arm` → per-arm object `{"A":147,"B":150,"C":153}`,
   because a 150 cap cannot finance arm C (40 turns + 2 checkpoints + 9 checkpoint/verify per rep = 51,
   ×3 = 153) and a mid-cell cap trips §3.6 (`INVALID-INSTRUMENT`). The note under the block shows the
   per-rep derivation (A 49 / B 50 / C 51) and the 450 total. Option (a)'s 123 is untouched.
3. **§4 E1 control thresholds.** Restated from `handoff from consonance/EXPERIMENTS.md`: identical
   hit **≥ 0.9 of `P`**; append reuse **≥ `P − k`**; never-sent **0**; mismatched-tokenizer **no reuse (0)**;
   plus the rule that **a control without an explicit threshold is not green**. The mismatched-tokenizer
   control is declared in the E1 draft `run.json` `notes` (the contract's `controls` object keeps exactly
   four keys).
4. **§5/§6 falsifier cells.** Arm A (both tables) now reads `none (baseline; cannot falsify itself)`; arm E
   reads `none (upper-bound diagnostic; not deployable)` and its negative control now carries the
   parametric-recall rule: an E that answers without an injection is `INVALID-INSTRUMENT`.
5. **§5 arm C, t40.** The definition cell now states that t40 is the last turn of a 40-turn fixture, so
   that checkpoint is recorded and reported but has **zero** post-checkpoint repayment turns and is
   excluded from the repayment window. The falsifier text is unchanged.

## Verification (offline, recorded in the handoff)

- `grep -n '6,300\|3\.64\|3\.6×'` → no matches.
- `grep -n '7,560\|4\.37'` → §6.3 total line, digest line, ratio line, prose, owner sentence.
- `python3`: `2*420*3 = 2520`, `5040+2520 = 7560`, `7560/1729 = 4.3725`, `3*(49+50+51) = 450`.
- Invariants intact: `UNFUNDED` ×3, E1/E2 falsifier texts unchanged, null rule (`:8012` null = 0 /
  `:8014` unknown) present, missing fixture classes still `UNAVAILABLE`/`NOT_OBSERVED`, worked abstention
  hypothetical `HYP-ABSENT-01` present.
- Fence count 10 (even) — the inserted option-(b) note did not break the JSON block.

## Residual, recorded not fixed

`orchestration/units/CONSONANCE-BC-EVAL.md` finding 4 still quotes the pre-fix `6,300 (3.64×)` as the
original unit's record. It is outside this unit's write paths and was left untouched; the corrected figure
in the protocol and in this card supersedes it.
