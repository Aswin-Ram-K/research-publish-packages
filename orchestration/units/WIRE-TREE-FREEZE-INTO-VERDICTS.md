# WIRE-TREE-FREEZE-INTO-VERDICTS

**Purpose.** Make the verdict ritual bind evidence to BYTES by default: a PASS must name the tree
it judged, not only a commit sha.

**Gap.** `orchestration_verdict {command, exitCode, sha}` records a commit and nothing else; since
`f17663d1` the tree moved repeatedly (`cell.py` alone: `0136052e` -> `24627d7b` -> `5a812a98` ...),
so a row recorded today can be re-run tomorrow against different bytes and still read PASS.

**Delivered.** `experiments/ptr-engine/tools/tree_freeze.py` gains `--verdict-row` (usable as
`--wrap OUT --path P... --verdict-row -- CMD`, or as the one-command form
`--path P... --verdict-row -- CMD`). It prints

1. one payload line `{"command","exitCode","sha"}` — command verbatim, `exitCode` the COMMAND's
   real exit (never 13), `sha` = `git rev-parse HEAD` sampled at wrap start;
2. a human line `verdict=<pass|moved_during_run|failed|failed_and_moved>` with per-path
   `before -> after` (or `deleted` / `created`).

`UNSTAMPED: ` prefixes the payload line whenever a declared path moved / was deleted / was created;
empty `--paths` is refused (exit 2); a dirty tree warns on stderr
(`WARNING: dirty tree at HEAD <sha>; the row names a commit that does not contain these bytes`).
`orchestration/VERDICT-RITUAL.md` gains an appended section §7 "Bind the row to bytes"; every
existing sentence is kept.

**Bound.** <=22 tool calls, 0 requests. **Writes:** `tools/tree_freeze.py`,
`longrun/experiments/ptr-engine/longrun/tests/test_tree_freeze.py`, `orchestration/VERDICT-RITUAL.md`, this card, its journal, its
handoff. `cell.py` untouched; no existing exit code changed.

**Acceptance.** `python3 -m pytest -q experiments/ptr-engine/longrun/tests/test_tree_freeze.py`
(35 passed) and the row recorded through `orchestration_verdict`.
