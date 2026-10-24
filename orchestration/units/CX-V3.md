# CX-V3 — independent verification of the U7 synthesis package

**Purpose (one):** Rule on the `## CX-V3 — pending` entry in `orchestration/VERDICTS.md` by independently
re-running its ten checks against `papers/context-cache/` (U7 synthesis). CX-V3 is not U7.

**Hard bound:** ≤40 work tool calls, one attempt. STOP and write the handoff with exact observed output if
`recompute.py all` is not `41 claims checked, all match`, a command errors unrecoverably, or the bound is hit.
No retry loops, no repairs.

**HARD RULE — verify only, never extend an authoring unit.** No edits under `papers/context-cache/`; no request
to U7 or anyone to continue authoring. A failed check is the result: record it and rule. If `recompute.py all`
is wrong, the package is FAIL — say so, don't fix it.

**Declared write paths (only these):**
- `orchestration/units/CX-V3.md`
- `orchestration/handoffs/CX-V3.json`
- `orchestration/VERDICTS.md` (replace the CX-V3 PENDING marker + fill its drafted table row only)

**Concurrency:** `M1-M` owns `experiments/context-cache/cells/M1-M/**` + its handoff. All of
`experiments/context-cache/cells/` is read-only here. No bare `git status` on `/home/zer0null/Duval`; never
touch that target.

**Status:** done — verdict **PASS** (all ten checks); handoff at `orchestration/handoffs/CX-V3.json`; 31/40 tool calls.
