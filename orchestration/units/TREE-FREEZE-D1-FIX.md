# TREE-FREEZE-D1-FIX

**Defect.** `experiments/ptr-engine/tools/tree_freeze.py` `--wrap` took a SECOND freeze after
the wrapped command and used it as the baseline. The one path the command deleted is exactly
the path that second freeze refuses, so a mid-run deletion produced exit 2, a usage message and
NO record. Quoted from `orchestration/handoffs/V-TREE-FREEZE.json` `defects[0]`:

> "D1 (high): a file DELETED by the wrapped command is not classified at all -- after=freeze(paths)
> refuses the missing path, --wrap exits 2 (usage) and writes NO record (reproduced twice).
> moved_during_run/failed_and_moved only ever describe changed bytes, never deletions."

Its `scope_gaps` add: new files are invisible (a grown tree can still read `pass`), files outside
the declared set are never observed, directories are refused, symlinks are followed.

**Fix (one authority line).** After the command, `classify(before, root=before["root"])` -- the
freeze taken BEFORE the command -- is the baseline. The after-document is a snapshot written from
those rows, never a fresh freeze (so it can record `absent`). Rows carry `state`
(`same|moved|deleted|created`), `before` sha, `after` sha-or-null, plus the legacy
`recorded_sha`/`current_sha`/`verdict` keys.

**Contract decision (stated once, used by doc and tests).** A path that does not exist cannot be
declared: `freeze` refuses it (exit 2) BEFORE the command runs -- a baseline of nothing cannot be
classified against. Creation is therefore WITNESSED rather than declared: the wrapper scans the
declared roots (parent dirs of the declared paths) before and after, emits a `created` row, and
says in its output that the declared set did not cover it. A grown tree is not a `pass`.

**Verdict mapping.** One function, `classify_verdict(exit_code, changed)`: 0+none `pass` (0),
0+any `moved_during_run` (13), nonzero+none `failed` (1), nonzero+any `failed_and_moved` (1,
record keeps the command's own `exit_code`). No fifth outcome. `moved_during_run` is UNSTAMPED,
never FAIL.

**D2 (also fixed).** `verify()` on a structurally invalid freeze document raises `Refused`
(exit 2) instead of a `KeyError('files')` traceback with exit 1 -- 1 is the command-failed code.

**Tests.** `experiments/ptr-engine/longrun/tests/test_tree_freeze.py` gains
`BaselineIsTheBeforeFreezeTests` (delete/0 -> `deleted` row + rc 13; create/0 -> `created` row +
rc 13; edit/1 -> `failed_and_moved` rc 1; untouched/1 -> `failed` rc 1; missing declared path ->
refusal with the command never started), `VerdictMappingTests` (the four-case table), and
`InvalidDocumentTests` (D2). Every pre-existing test is unchanged and green: no old assertion had
to be rewritten, because the legacy row keys were kept.

**Evidence.** `orchestration/journals/TREE-FREEZE-D1-FIX.log` (proof run),
`orchestration/handoffs/TREE-FREEZE-D1-FIX.json`. Tests: 42 passed, 14 subtests in
`test_tree_freeze.py` + `test_exit_codes.py`.

**Wrapper ownership.** `verdict_with_freeze.py` does not exist in this tree and no
`WIRE-TREE-FREEZE-INTO-VERDICTS` card is running, so `tree_freeze.py --wrap` is the wrapper path;
nothing else was edited. Follow-up (not this card): a settle-time consumer that reads `verdict`
and treats exit 13 as `pass`-equivalent, never as FAIL.
