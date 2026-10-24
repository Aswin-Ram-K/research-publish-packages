# UFIXPKG9 — tag-grammar second copy + stale MANIFEST + failure triage

**Purpose.** (1) Widen the stale live tag-grammar copy at `tools/package/gate.sh:110` to accept `P`, preserving `N`; determine whether the two copies are independent sources of truth or one emitted from the other. (2) Verify and regenerate `scratch/uneutral10/package/MANIFEST.json` after a prior unit edited `scratch/uneutral10/package/fixture/reflex-decisions.ts`. (3) Triage the pre-existing test failures.

**Hard bound.** 20 tool calls. If a claim cannot be verified inside the bound, STOP and report `partial`.

**Declared write paths.** `tools/package/gate.sh`, `tests/**`, `scratch/uneutral10/package/MANIFEST.json`, `orchestration/units/UFIXPKG9.md`, `orchestration/handoffs/UFIXPKG9.json`, `scratch/ufixpkg9/**`.

**Constraints.** `/home/zer0null/Duval` read-only, never `git` against it. No installs, no fetches, no builds into release destinations. Do not weaken any guard. No new numbers not read from disk or measured. Separate measured / inferred / undetermined.

**Deliverables.** red→green control on live files for the grammar; before/after per touched file with before-string uniqueness asserted; suite result with literal count; three package tools exit 0 with diagnostics and `recompute-claims.py` PASS; manifest entry count + byte total and confirmation no published number in `papers/encoder-crossover-190/` depends on the byte total.
