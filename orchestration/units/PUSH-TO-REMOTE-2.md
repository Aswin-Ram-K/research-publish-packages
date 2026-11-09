# UNIT PUSH-TO-REMOTE-2 — complete the operator's one push without GitHub-flagged crawler caches

**Status:** done · **Bound:** ≤20 tool calls (used 9) · **Routes:** (b) crawler-cache exclusion, amends only of a never-pushed commit.

## Objective
Operator intent (m00403): "one push to remote, all the local work as is, no merge to main".
PUSH-TO-REMOTE left commit `86c3edb` (3324 files) unpushed because `git push` was rejected
GH013 "Push cannot contain secrets". This unit excludes exactly the flagged crawler caches,
amends the unpushed commit, and pushes.

## Preconditions checked
- `origin` = https://github.com/Aswin-Ram-K/research-publish-packages.git, branch `research/next-candidates-2026-10-24`.
- Before: `git rev-list --left-right --count origin/<branch>...HEAD` = `0  1`; HEAD = `86c3edb71fc504d2bcc569547a8be5cf874c2c0d`. Never pushed — amend permitted.
- All flagged paths matched `jobs/<job>/(raw|scratch|\.cache)/` (crawler captures). None were project work.
- Token nature: `pk.` Mapbox **public** access tokens embedded in scraped Drupal page JSON — third-party
  page source, not this project's credential. No genuine project credential found.

## Flagged paths (12 total, by round)
Round 1 (10): jobs/evals-safety-foundations/raw/caissi_careers.html, jobs/us-national-labs/scratch/nist.html,
jobs/us-nonprofit-research/.cache/nist_aisi.html, jobs/us-nonprofit-research/.cache/nist_caisi.html,
jobs/us-nonprofit-research/.cache/nist_caissi.html, jobs/us-national-labs/scratch/jpl.html,
jobs/us-national-labs/scratch/jpl_ai.html, jobs/us-national-labs/scratch/mitre.html,
jobs/us-national-labs/scratch/mitre_ai.html, jobs/us-nonprofit-research/.cache/mitre_careers.html.
Round 2 (2): jobs/evals-safety-foundations/raw/nist_caissi.html, jobs/us-nonprofit-research/.cache/nist_careers.html.

## Procedure actually run
1. Verified unpushed (`0  1`, `86c3edb`).
2. `git push` retry → captured GH013 findings verbatim; parsed paths (no truncation).
3. `git rm --cached -- <path>` per path + one line each in `.git/info/exclude` (blocks re-add by `git add -A`).
4. `git commit --amend -F` with original message plus:
   `excluded from this snapshot: N crawler HTML caches flagged by GitHub push protection (GH013), paths listed in orchestration/handoffs/PUSH-TO-REMOTE-2.json`
5. Retried push; round 2 surfaced 2 further caches → same exclude/amend/push sequence → accepted.

## Result
- Final commit `f17663d1fed0162a7dc3c5a0a58d372c710974c3` (parent `0eeaa5a`), 3312 files changed, +1,883,679 / −161.
- Push: `0eeaa5a..f17663d  research/next-candidates-2026-10-24 -> research/next-candidates-2026-10-24`; branch set to track origin.
- After: `git rev-list --left-right --count origin/<branch>...HEAD` = `0  0`.

## Constraints honoured
No `--force`/`--force-with-lease`/`-f`; `master` (41ad35b) and all other refs untouched; no PR, no merge,
no push to any other branch; no GitHub web unblock; secret scanning untouched. Excluded files remain on
disk untracked (excluded via `.git/info/exclude`), so nothing was deleted.

## Trap worth remembering
Sandbox `/tmp` does not persist between `bash` calls (each call gets a fresh temp namespace) — the first
`git rm` loop read an empty list and only the amend took effect. Keep scratch files under `.git/push2/`
inside the workspace instead.
