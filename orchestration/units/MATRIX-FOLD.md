# MATRIX-FOLD — the four-cell model x engine matrix, folded as C63

## Objective
All four cells of the 2x2 are measured (occamy-1.0 MoE x SGLang G3/S0 and x vLLM MOE-VLLM/V3;
qwen3.5-9b dense x SGLang DENSE-SGL/P1 and x vLLM WIN-VLLM/V1). Fold them into one claim,
**C63**, that separates the **engine** effect from the **model** effect and states their
interaction; recompute every number from the four `rows.jsonl` files; carry the claim through
recompute.py, CLAIMS.md, READER-MAP.md, MANUSCRIPT.md (§9b, abstract, §11), PACKAGE.md,
EVIDENCE.md, GAPS.md G4 and RUN.json; add a red->green guard.

## Hard bound
45 tool calls / one pass. Stop and report `partial` if any of the four cells' rows fail the
byte-identity pairing or a cell's 32k battery is incomplete; do not invent a fifth cell.

## Write paths
papers/context-cache/recompute.py
papers/context-cache/CLAIMS.md
papers/context-cache/READER-MAP.md
papers/context-cache/MANUSCRIPT.md
papers/context-cache/PACKAGE.md
papers/context-cache/EVIDENCE.md
papers/context-cache/GAPS.md
papers/context-cache/RUN.json
tests/test_paper_matrix_fold.py
state/gap-ledger.json
state/logs/MATRIX-FOLD-redgreen.txt
orchestration/units/MATRIX-FOLD.md
orchestration/handoffs/MATRIX-FOLD.json

## Deliverable
C63 in the ledger with its 41 pinned values, §9b in the manuscript, the guard test, and a
valid unit handoff. Author-side: the independent verifier for this claim is a separate unit.

## What this pass did (2026-10-24)

- **Cell set and pairing.** 4 cells x (arms R/A/C/H x turns 1..71) = 284 rows each, 1,136 in
  all; prompt prefix digests and lengths equal on all six cell pairs (`prefix_sha256` 284/284,
  `chars` 284/284); the chat template moves
  `prompt_tokens` by -4 on 140 of the 284 rows in each SGLang cell (pair-row counts over all
  six pairs: 0 on 1,144, +4 on 420, -4 on 140), so the pairing is on `(arm, turn_id)`.
  No compaction at 32k, so the arms are replicates and the **turn** is the resampling unit.
- **Factorial.** engine +1,225.18 [1,132.2, 1,313.3] (70/71 turns positive); model +275.83
  [194.3, 357.6] (53/71); interaction +272.23 [190.1, 354.6] (52/71); engine within MoE
  +952.96 [805.7, 1,099.8], within dense +1,497.41 [1,404.4, 1,585.0]; model within vLLM
  +548.06 [384.7, 711.9] (52/71), within SGLang +3.61 [0.0, 10.8] (1/71). Ratios: engine
  2.3058x / 3.0418x (mean 2.6738x), model 1.3257x / 1.0049x (mean 1.1653x); engine 91.15 % of
  the 1,344.1585 grand mean; engine/model 4.4418; model effect 151.82x larger under vLLM.
  Percentile bootstrap over 71 turns, 10,000 resamples, seed 20251023.
- **Mechanism, measured.** SGLang reports the 64 hot grid in both cells; vLLM resolves 2,096
  (MoE) and 1,088 (dense). The claim is a measured 2x2 at one band/seed/GPU, not a law.
- **Verification.** `recompute.py all` -> `60 claims checked, all match` + `GRID GUARD PASS
  7/7 configs` + `COVERAGE GUARD PASS 63 claims documented, 61 runnable here + 2
  script-backed`; `verify_package.py` -> PASS 63/63; new guard 8/8 with a captured
  red->green (`state/logs/MATRIX-FOLD-redgreen.txt`).
