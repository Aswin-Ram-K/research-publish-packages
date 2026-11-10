# U-SPCC-25 — repo-state page names the real HEAD and stops contradicting itself

## Target
`docs/CURRENT-REPO-STATE.md` only. No other doc, no code.

## Change
1. Stale HEAD/push pair replaced with the verified pair: `HEAD: 7e96632 (spcc: the TX-03 cliff
   is presence, not position; row fields stop lying about masking)` and `Pushed as:
   origin/research/next-candidates-2026-10-24 = 7e96632`. The backup ref
   `origin/backup/screened-dirty-progress-2026-11-10-1348 = 17182ff` is retained only as an
   explicitly labelled older backup, never as the current HEAD.
2. `## Reading rule` rewritten: `origin/main` at `5554d82` IS an ancestor and reading it is
   correct; the unrelated-root merge (`ca9d65e`) was reverted by `1977d30` with the repair in
   `59c1c60`, so the branch must not be read as containing the research commits.
3. `dfba6aa` removed from the reading-rule commit list (not in the branch-only history list,
   not on this branch's verified first-parent chain).
4. Branch-only history list (`9fadcc9`, `afe4d78`, `ca9d65e`, `1977d30`/`59c1c60`) left intact.

## Evidence
- `git log --oneline -1` → `7e96632 spcc: the TX-03 cliff is presence, not position; row fields
  stop lying about masking`
- `grep -n "17182ff\|dfba6aa" docs/CURRENT-REPO-STATE.md` → single line, line 6, the labelled
  backup ref; no `dfba6aa` anywhere.
- `python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Status
complete
