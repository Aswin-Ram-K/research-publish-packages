# UREPOMAN1 — Repository MANIFEST self-consistency

**Purpose (one):** Reproduce, decide, and fix the `MANIFEST.json` / `README.md` mismatch in the public
repo `https://github.com/Aswin-Ram-K/research-publish-packages`, then verify from the remote.

**Bound:** 20 tool calls. Report `partial` naming the remainder if exhausted.

**Write paths (declared):**
- `orchestration/units/UREPOMAN1.md` (this card)
- `orchestration/handoffs/UREPOMAN1.json`
- `scratch/urepoman1/**`
- the cloned repository's own files (clone under `scratch/urepoman1/clone/`)

**Non-goals / forbidden:** no writes under `papers/**`; nothing in `/home/zer0null/Duval`; no git at
workspace root; no global git config; no repo settings/visibility changes; no token printing.

**Steps:**
1. Fresh clone to `scratch/urepoman1/clone/`; reproduce mismatch literally.
2. Decide (regenerate repo-owned manifest vs remove it), justify, state cost.
3. Implement with project tooling (`tools/package/regen_manifest.py`,
   `tools/package/check_manifest.py`) — zero mismatches if regenerating.
4. Add ≤1 sentence to `README.md`; read the DOI from the file, do not retype from card.
5. Commit+push to `main`, repo-local git identity only.
6. Fresh-clone the pushed repo to a second scratch dir; run the check there; report SHA, HTTP statuses.

**Doc:** none required beyond the above; follow AGENTS.md unit contract.
