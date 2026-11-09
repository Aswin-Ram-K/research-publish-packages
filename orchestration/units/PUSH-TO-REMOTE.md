# UNIT PUSH-TO-REMOTE

**Purpose:** one push of all local work on a work branch. No merge, no PR, no force, main untouched.

**Bound:** <=22 tool calls. Handoff written as `partial` within first 5 calls.

**Write paths:** `orchestration/units/PUSH-TO-REMOTE.md`, `orchestration/handoffs/PUSH-TO-REMOTE.json`.

**Steps:** recon -> secret/large-file sweep + exclusion -> `git add -A` -> one ordinary commit -> `git push -u origin <branch>` -> verify remote-tracking ref.

**Kill condition:** no remote / push rejected / any single untracked file >50 MB -> stop and report, do not force.

## Outcome (2026-10-26)

- Remote `origin https://github.com/Aswin-Ram-K/research-publish-packages.git`, branch `research/next-candidates-2026-10-24` (work branch; local `main` does not exist, `master` 41ad35b untouched).
- One commit `86c3edb71fc504d2bcc569547a8be5cf874c2c0d` — 3324 files, +1915776/-161.
- Excluded (`.git/info/exclude`): `scratch/` (2.7 GB scratch), `.scratch/`, `.verify-scratch/`, `.dsh-progress/`, byte-code/dep caches, embedded clone `.ucurate1/pre/research-publish-packages/`.
- **Push BLOCKED** by GitHub push protection GH013: 10 scraped HTML files under `jobs/*` contain secret-looking strings. No force, no amend, no rewrite. Stored local, reported.
