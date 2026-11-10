# Current repo state

- Branch: `research/next-candidates-2026-10-24`
- HEAD: `7e96632` (`spcc: the TX-03 cliff is presence, not position; row fields stop lying about masking`)
- Pushed as: `origin/research/next-candidates-2026-10-24` = `7e96632`
- Older backup ref still on the remote: `origin/backup/screened-dirty-progress-2026-11-10-1348` = `17182ff` (a backup, not the current HEAD)
- `origin/main`: `5554d82` — **an ancestor** of this branch (merge-base = `5554d82`)
- Working tree: untracked paths from sibling agents (not part of this unit)

## Branch-only history
These live only on the research branch; `origin/main` has not moved past `5554d82`:
- `9fadcc9` — preservation commit (context x serving instrument, fixtures, measurements)
- `afe4d78` — merge of `research/paper-candidates-2026-11-04`
- `ca9d65e` — merge of `origin/main` with `--allow-unrelated-histories`, leaking 31 files
- `1977d30` — `git revert -m 1 ca9d65e`; repair recorded in `59c1c60`. No history rewritten.

## Reading rule
The work is pushed, but `main` has not moved past `5554d82`. `origin/main` at `5554d82` **is**
an ancestor of this branch, so reading `origin/main` normally is correct. What you must not do
is read this branch as if it contained the research commits above: they exist only on
`research/next-candidates-2026-10-24`.

An earlier merge pulled an unrelated root (`ca9d65e`, `--allow-unrelated-histories`); that was
reverted by `1977d30`, with the repair recorded in `59c1c60`. The unrelated root is therefore
not part of the current branch content.
