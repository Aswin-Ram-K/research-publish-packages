# Current repo state

- Branch: `research/next-candidates-2026-10-24`
- HEAD: `17182ff` (`backup: screened serving WIP (unverified)`)
- Pushed as: `origin/backup/screened-dirty-progress-2026-11-10-1348` = `17182ff`
- `origin/main`: `5554d82` — **an ancestor** of this branch (merge-base = `5554d82`)
- Working tree: untracked paths from sibling agents (not part of this unit)

## Branch-only history
These live only on the research branch; `origin/main` has not moved past `5554d82`:
- `9fadcc9` — preservation commit (context x serving instrument, fixtures, measurements)
- `afe4d78` — merge of `research/paper-candidates-2026-11-04`
- `ca9d65e` — merge of `origin/main` with `--allow-unrelated-histories`, leaking 31 files
- `1977d30` — `git revert -m 1 ca9d65e`; repair recorded in `59c1c60`. No history rewritten.

## Reading rule
The work is pushed, but `main` has not moved. Do not read `origin/main` as containing the
research branch's commits (`9fadcc9`, `afe4d78`, `dfba6aa`, `17182ff`), and do not read this
branch as a descendant-by-content of `origin/main`: the remote root is a different project
(encoder-crossover-190 deposit), merged and then reverted.
