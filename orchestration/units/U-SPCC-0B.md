# U-SPCC-0B — Repair unrelated origin/main merge

## Result
- Reverted merge commit `ca9d65e` via `git revert -m 1` (new commit `1977d30`); no history rewritten.
- Removed vendored `.api_server.py` (`dfba6aa`).
- `origin/main` confirmed to be a different project (encoder-crossover-190 deposit); two roots `78c01e9`, `b4ea93c`.
- Row files: 92 files / 7,869 rows, 0 exact duplicate lines, 123 distinct run manifests -> growth, not corruption.

## Evidence
- `git rev-list --max-parents=0 HEAD` -> `78c01e9...`, `b4ea93c...`
- `git diff --name-only ca9d65e^1 ca9d65e | wc -l` -> 31
- `ls rows-*.jsonl | wc -l` -> 92; `cat rows-*.jsonl | wc -l` -> 7869
- generation tallies: `gen-7` 5003, `7` 272, (none) 2594
- exact duplicate full-row lines: 0

## Acceptance
- `git status --porcelain | wc -l` -> 9 (sibling-agent untracked paths only; no tracked changes)
- leaked file `.api_server.py` no longer exists
