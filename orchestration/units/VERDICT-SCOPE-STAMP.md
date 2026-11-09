# VERDICT-SCOPE-STAMP — make a verdict row say which files the command it judged read

**Status:** done · **Batch:** verdict-integrity · **Automated, offline (zero requests).**

## Why

A row `{command, exit, sha}` says *what* and never *over what*. Three instances lost FAILs to
bytes nobody named: `SEAM-TEST-RED` (`FAIL exit-1` from another card's edit of `cell.py`;
its own seam tests 5/5), `GRID-PARAMS-DIGEST-SUPERSEDE` (`launch_contract_diff --check` green at
19:27, `grade_v5.py` moved 14:44, same command exits 1), and `tests/test_cap_gate.py:205` (a stale
assertion manufacturing three FAILs). A later reader cannot re-judge any of them without
re-running against a tree that no longer exists.

## Deliverable

`experiments/ptr-engine/tools/verdict_scope.py` — two verbs over the EXISTING machinery:

* `run --paths P… -- CMD…` → freeze before, run, freeze/classify after, print one paste-ready
  `orchestration_verdict` payload + a `scope` block `{paths:[{path,sha_before,sha_after,moved}],
  moved, exit, command, verdict}`. `moved` non-empty → `scope.verdict: tree-moved`, exit **13**.
* `check --row <json|FILE>` → re-freeze the row's named paths now: `same` / `moved_since` /
  `path_missing` (exit 1) / `undatable` (no scope, exit 0).

`tools/tree_freeze.py` is **imported**, not forked: it already owns the freezer, the classifier,
creations, the four verdicts and exit 13 (`exit_codes.EXTERNAL_CODES`). Finding recorded rather than
forked: the wrap record carries `moved_detail` only for moved paths, so an unmoved path's
`sha_after` is its own `sha_before` — exact, since "absent from moved_detail" means "classified
`same` by the same read".

`head_is_meaningful: false` whenever a named path is untracked — in this workspace `cell.py`,
`tree_freeze.py` and this tool are untracked, so `sha f17663d1` must not be read as a statement
about them.

## Tests

`experiments/ptr-engine/tests/test_verdict_scope.py` — 11 passed. The three historical instances
are cases: (a) clean, (b) edit mid-run → 13 with both shas, (c) deleted after the row → `check` 1
`path_missing`, (d) no scope → `undatable`, (e) untracked → `head_is_meaningful false`, (f)
unchanged → `same`. Red proven by neutering each guard in a `/tmp` copy, then restored.

## Write paths (exactly)

`experiments/ptr-engine/tools/verdict_scope.py` · `experiments/ptr-engine/tests/test_verdict_scope.py` ·
`orchestration/VERDICT-RITUAL.md` (append only) · `docs/VERDICT-SCOPE.md` ·
`orchestration/units/VERDICT-SCOPE-STAMP.md` · `orchestration/handoffs/VERDICT-SCOPE-STAMP.json` ·
`orchestration/journals/VERDICT-SCOPE-STAMP.jsonl`

## Hard rules honoured

No `ask_user_question`, zero requests, no network, no live cell. Not edited: `cell.py`,
`run_longrun.py`, `run_a_star.py`, `analyze_stats.py`, `grade_v5.py`, `launch_contract_diff.py`,
`tree_freeze.py`, any fixture, the pin, the params, any threshold, any published measurement page.

## Acceptance

`python3 -m pytest -q experiments/ptr-engine/tests/test_verdict_scope.py` → 11 passed, exit 0,
run through `verdict_scope run` itself so the row is its first user.
