# UNEUTRAL5 — Price the stimulus neutralisation (option B)

**Hard bound:** 25 tool calls. Status: IN PROGRESS (skeleton written before work).

## Purpose
Price two neutralisation variants for the ten mechanism-bearing tokens in the released
stimulus, then apply only the variant that moves no published claim number.

- V1 maximal: neutralise all ten everywhere (injective NEUTRAL-TAG/v1 map, never persisted).
- V2 stimulus-only: neutralise only inside-stimulus sites (values of `question`, `options`, `situation`).

## Write paths (nothing else)
strategy/STIMULUS_NEUTRALISATION.md, orchestration/units/UNEUTRAL5.md,
orchestration/handoffs/UNEUTRAL5.json, scratch/uneutral5/**

## Plan
1. Recon + skeleton (this card).
2. Copy scratch/uoutside1/tree-seven -> scratch/uneutral5/tree-v1 and tree-v2.
3. Census: per-token, per-class counts (a inside-stimulus, b schema/vocab, c prose/source).
4. Route A diagnostics before/after per variant; verify/recompute-claims.py; second-labeller tools.
5. Decide (rule: most occurrences removed with zero published claim movement); apply to tree-eight.
6. Regenerate MANIFEST.json from disk, independent checker, sha256, bytes_total, idempotence x2.

## Results
(filled as work proceeds)
