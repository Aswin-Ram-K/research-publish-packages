# UNIT PUSH-TO-REMOTE

**Purpose:** one push of all local work on a work branch. No merge, no PR, no force, main untouched.

**Bound:** <=22 tool calls. Handoff written as `partial` within first 5 calls.

**Write paths:** `orchestration/units/PUSH-TO-REMOTE.md`, `orchestration/handoffs/PUSH-TO-REMOTE.json`.

**Steps:** recon -> secret/large-file sweep + exclusion -> `git add -A` -> one ordinary commit -> `git push -u origin <branch>` -> verify remote-tracking ref.

**Kill condition:** no remote / push rejected / any single untracked file >50 MB -> stop and report, do not force.
