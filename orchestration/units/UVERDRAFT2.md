# UVERDRAFT2 — independent verifier, paper `papers/replay-record-not-decision/`

**Purpose:** Re-derive every number in the drafted paper from raw records; report contradicted / overstated / not_reproduced / unverified. Not the author; will not improve the paper.

**Write paths (only):** `strategy/VERIFICATION_REPORT_DRAFT2.md`, `orchestration/units/UVERDRAFT2.md`, `orchestration/handoffs/UVERDRAFT2.json`, `scratch/uverdraft2/**`

**Hard bound:** 25 tool calls. Read-only on `/home/zer0null/Duval`; no `git` anywhere; no network.

**Raw records:**
- `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/decision-variants.jsonl` (3040 rows)
- `…/l1-head-to-head.jsonl` (380 rows)

**Checks 1–11** per unit card. Report each with literal command + output.
