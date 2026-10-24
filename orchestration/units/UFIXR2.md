# UFIXR2 — verify two suspect statements in strategy/PAPER2_REVERIFICATION.md

- Purpose: independently verify (from raw JSONL records, not from UREVER2's or any other unit's word) two statements in `strategy/PAPER2_REVERIFICATION.md`: (S1) that `ms`, `p_chosen` and `conf` "differ on every row" of `l1-head-to-head.jsonl`; (S2) that the per-variant spread is "3.9 % (40.0–47.1 %)".
- Raw records (read-only): `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/l1-head-to-head.jsonl` (380 rows) and `.../decision-variants.jsonl` (3,040 rows).
- Write paths: `strategy/PAPER2_REVERIFICATION.md`, `orchestration/units/UFIXR2.md`, `orchestration/handoffs/UFIXR2.json`, `scratch/ufixr2/**`.
- Hard bound: 10 tool calls. No git commands, no network, no writes to /home/zer0null/Duval, no edits under `papers/replay-record-not-decision/**`.
- Method: compute per-field agreement on l1-head-to-head.jsonl; compute the true percentage-point spread across variants in decision-variants.jsonl; read the exact original lines; assert the before-string occurs exactly once before editing; append dated `[corrected 2026-10-16 by UFIXR2: …]` markers only.
