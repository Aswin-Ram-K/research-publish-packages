# CLAIM-HEALTH — unit card

**Purpose.** Judge, per claim, whether the cell it cites is safe to publish after the cached_tokens audit.
No number changes; a disposition only.

**Mode.** Fully offline. Zero live requests, no GX10, no endpoint, no model lock. Automated task-board
session: no `ask_user_question`.

**Inputs (read-only).** `orchestration/handoffs/CACHED-AUDIT2.json` (ground-truth classes, not re-derived),
`state/logs/cached-dedupe-audit.json` (per-arm fire counts), `papers/context-cache/CLAIMS.md` (values + cells),
`experiments/context-cache/cells/*/rows.jsonl` (read only, to confirm which quantities are prompt_tokens
vs cached_tokens functions).

**Outputs.** `papers/context-cache/CLAIM-HEALTH.md`, `orchestration/handoffs/CLAIM-HEALTH.json`, this card.

**Result.** 20 ids: SAFE 7 / REMEASURED 0 / BLOCKED 13. All 20 are suspect for reason (a), the
flagged cached_tokens pattern. BLOCKED: C17, C18, C19, C20, C21, C22, C23, C24, C44, C46, C47, C50, C51 — each named with the live card that would fix it.

**Bound.** 18 tool calls, self-imposed; used 18. No forbidden write occurred.
