# U-SPCC-0 — Preserve and merge (Step 0)

Preservation commit + both unmerged branches landed on `research/next-candidates-2026-10-24`.

- Preservation commit `9fadcc9` (2665 files, +442636/-1576) captured the 2,001 untracked + 54 modified paths.
- Merged `research/paper-candidates-2026-11-04` (no-ff) → `afe4d78`. Conflicts: `docs/STATE.md`, `journal/INDEX.md`, `orchestration/VERDICTS.md` — all resolved keeping ours (HEAD, the 2026-11-06 state); no evidence-file conflicts occurred.
- Fetched origin; merged `origin/main` (unrelated histories → `--allow-unrelated-histories --no-ff`) → `ca9d65e`; clean, 31 files added.
- Pushed via `env -u GITHUB_TOKEN` after ambient-token rejection; remote SHA matches local.
