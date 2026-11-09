# UNIT CONTRACT-DIFF-TREE-SCOPE

**Card:** `b51f4988-2983-49e1-b5e2-cd88f312abad` · execution `f5b2339c-86a0-4a27-a747-d392a04e75b5`
**Class:** automated / offline (zero requests, no network, no live cell, never `ask_user_question`)
**Base:** `f17663d1fed0162a7dc3c5a0a58d372c710974c3`

## Objective

Make `launch_contract_diff.py --check` judge a **named tree** instead of "whatever is on disk
now", so a concurrent edit to a pinned input reports `moved` (unstamped) and never a false `FAIL`.

## Why (the case)

`GRID-PARAMS-DIGEST-SUPERSEDE` (`a3fdaab5`) settled **FAIL exit-1**. Its `--check` passed at
19:27 against pin generation 4 (`fa6fd8cc…`); three minutes later `GRADE-V5-T4-DECORATION`
repaired `grade_v5.py` (`056eb605… → 3d70ed1d…`) and the same check exited 1 naming a digest row
that is *supposed* to be stale until the next pin generation. Nothing about that card's work was
wrong; the check had no notion of which tree it judged.

## Contract

1. Reproduce and quote today's `--check` exit and the row it names, plus the exit on a `/tmp`
   tree restored to generation 4.
2. Add `--pin-generation N` and `--tree-sha <harness_sha256>`. The scope resolves through
   `measure/HARNESS-PIN.json`'s supersedes chain; a differing tree is `MOVED` (a distinct class
   from `DISAGREES`), naming every mover with both digests; exit **13**
   (`exit_codes.EXIT_TREE_MOVED`, the project's established tree-moved code — not invented).
   The report carries `judged_tree: {generation, harness_sha256, pinned_at}`.
3. The default (no scope) behaviour is **unchanged**: exit 1 on a real disagreement.
4. Prove three cases: (a) scoped gen 4 on today's tree → `moved` 13; (b) scoped gen 4 on a tree
   whose record matches its bytes → 0; (c) default on a tree with help `108 → 67` → 1 naming both
   `file:line`. (c) is the guard that the scope did not become a bypass.
5. `--write` the artefact only if the new fields require it; never re-derive a launch number.
6. Record the operational rule (below) in the artefact and the page.

**Operational rule installed:** *a check whose acceptance depends on files other cards may edit
must be run with an explicit scope; a check that cannot name its tree cannot distinguish a defect
from a neighbour.*

## Hard bound

One pass over the tool + one test file; no attempt to restore the lost generation-4 bytes beyond
what is honestly available; no edit to `cell.py`, `run_longrun.py`, `analyze_stats.py`,
`grade_v5.py`, `run_a_star.py`, `HARNESS-PIN.json`, `GRID-PARAMS.json`, any fixture, threshold or
published measurement page.

## Write paths (exactly)

- `experiments/ptr-engine/tools/launch_contract_diff.py`
- `experiments/ptr-engine/tests/test_launch_contract_diff.py`
- `experiments/ptr-engine/measure/LAUNCH-CONTRACT-DIFF.json`
- `docs/LAUNCH-CONTRACT.md`
- `orchestration/units/CONTRACT-DIFF-TREE-SCOPE.md`
- `orchestration/handoffs/CONTRACT-DIFF-TREE-SCOPE.json`
- `orchestration/journals/CONTRACT-DIFF-TREE-SCOPE.jsonl`

## Result

`done`. Default check unchanged (exit 1, `harness_pin_digest`); scoped gen 4 on today's tree
`MOVED` exit 13 naming `grade_v5.py` (`056eb605… → 3d70ed1d…`) and — because a second neighbour
edited it mid-card — `run_longrun.py` (`b2003038… → 30dfa9e9…`); a `/tmp` tree whose record
matches its bytes exits 0 scoped; a tree with help `108 → 67` exits 1 naming
`run_a_star.py:241` and `run_a_star.py:367`, and still exits 1 *with* a scope. Artefact re-written
under generation 4 with `judged_tree` + the rule; suite 7 passed; full engine suite 266 passed.
