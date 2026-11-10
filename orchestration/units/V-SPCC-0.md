# V-SPCC-0 — Independent verification of U-SPCC-0 preservation work

## Checks (outputs pasted verbatim)

1. `git log --oneline -5`:
```
d6b861f U-SPCC-0: card and handoff for preserve-and-merge step
ca9d65e Merge remote-tracking branch 'origin/main' into research/next-candidates-2026-10-24
afe4d78 Merge branch 'research/paper-candidates-2026-11-04'
9fadcc9 wip(ptr-engine): preserve context x serving instrument, fixtures and measurements
0859cfe Merge branch 'wt/20261104-171928' into research/paper-candidates-2026-11-04
```

2. `git status --porcelain | wc -l` → `0`

3. HEAD = `d6b861f1237baf622184dbdbfb83a8292e6a0132`; origin/research/next-candidates-2026-10-24 = `d6b861f1237baf622184dbdbfb83a8292e6a0132` → match.

4. `git rev-list --count HEAD..origin/main` → `0`

5. `merge-base --is-ancestor research/paper-candidates-2026-11-04 HEAD` → `MERGED`

6. Unrelated-histories risk:
- graph shows `ca9d65e` merge with two parents; origin/main side (`5554d82`→`36a82bc`→`78c01e9`) connects down to `f17663d`.
- `rev-list --max-parents=0 HEAD` → two roots: `78c01e9fc38cb97060d87a02e7c704716898ca42` and `b4ea93c457b39a1affa3e9efc63ab90abb234fc7`.
- `78c01e9^` → fatal (no parent) — confirms `78c01e9` is a root; `merge-base 78c01e9 f17663d` → empty. origin/main shares NO common root with this branch.
- `diff --stat HEAD^1 HEAD` → only 2 files (U-SPCC-0 card/handoff), confirming HEAD^1 is the paper-candidates merge.
- DEFECT: origin/main's unrelated tree leaked into HEAD. `HEAD:.api_server.py` exists (vLLM serving checkout, 29939 bytes). origin/main is effectively a different repository; its files now pollute research extractor.

7. Instrument survived:
- `ls measure | wc -l` → `790` (measure dir total; `rows-*.jsonl` count = `92`)
- `cat measure/rows-*.jsonl | wc -l` → `7869`
- vs expected 41 row files / 2591 rows: MISMATCH (92 files, 7869 rows). Finding, not necessarily error — plan's own text cites 7,869 requests of measurements, so 7869 rows is consistent with the plan's stated measurement volume; the "2591" expectation in the assignment appears stale/under-counted. Row-file count 92 vs 41 is a genuine discrepancy worth reconciling.

8. Preservation commit `9fadcc9…` → `2665 files changed, 442636 insertions(+), 1576 deletions(-)` (~2,665 files, matches "2,000+").

## Verdict

Preservation of the instrument itself is intact (2665 files, 7869 rows). However the `--allow-unrelated-histories` merge of origin/main introduced a second, unrelated root and leaked origin/main's serving-checkout files (e.g. `.api_server.py`) into this branch's tree — a defect that must be cleaned before further work.
