# Current repo state

- Branch: `research/next-candidates-2026-10-24`
- HEAD: `dfba6aa` (revert of `ca9d65e` merge + removal of vendored `.api_server.py`)
- Working tree: 9 untracked paths from sibling agents (not part of this unit)

## Branches
- `research/next-candidates-2026-10-24`: active integration branch; preservation commit `9fadcc9`, paper-candidates merge `afe4d78`.
- `research/paper-candidates-2026-11-04`: 4 commits ahead at merge time, now merged.
- `origin/main`: a *different* repository (encoder-crossover-190 deposit: second-labeller, results, fixture). Shares no common ancestor with this branch (two roots: `78c01e9`, `b4ea93c`).

## Merge outcome
- `ca9d65e` merged origin/main with `--allow-unrelated-histories`, leaking 31 unrelated files. Reverted as new commit `1977d30` (`git revert -m 1`). No history rewritten.
- Vendored vLLM `.api_server.py` (tracked since `f17663d`) removed in `dfba6aa`.

## Row files
- `experiments/ptr-engine/measure`: 92 `rows-*.jsonl`, 7,869 rows, 0 exact duplicate lines, 123 distinct run manifests -> growth, not corruption.
