# URESID3 — Residual token triage (Part A/B/C)

**Purpose (one):** Diagnose the 1,133 flagged out-of-vocabulary tokens in the emitted tree, the
removability of internal-process identifiers, and the two reported discrepancies (CLAIMS A/B row
`0.3526` vs `0.3684…`; three sha256s for "the fixture"). **Diagnosis only — no fixes.**

**Hard bound:** 25 tool calls.

**Declared write paths (exactly these):**
- `strategy/RESIDUAL_TRIAGE_3.md`
- `orchestration/units/URESID3.md`
- `orchestration/handoffs/URESID3.json`
- `scratch/uresid3/**`

**Read-only:** `/home/zer0null/Duval` (no git, no writes). Payload/paper/tools not edited.

**Method:** exact token accounting on the emitted tree (not a keyword guess); copy under
`scratch/uresid3/` for Part B; digest identification and exit-code code-reading for Part C.

**Status:** done (2026-10-16). Report: strategy/RESIDUAL_TRIAGE_3.md. Handoff: orchestration/handoffs/URESID3.json.
