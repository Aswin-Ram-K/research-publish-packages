# TREE-FREEZE — a verdict must name the bytes it judged

**The rule, in one paragraph.** A claim about code is a claim about particular bytes, so
before an audit reads a file it must freeze what it is about to judge (path, sha256, size,
mtime_ns, and one `tree_sha256` for the set) and afterwards re-hash it; if the bytes moved,
the result is *unstamped*, not a FAIL, and the remedy is a re-run against the settled tree,
never a re-interpretation of the old result. Concurrent cards editing the same tree is the
design of this batch — `cell.py` moved twice inside one audit (`0136052e` 12:16:20,
`24627d7b` 12:23:43), a rewrite had to be bracketed to keep an adjudication meaningful,
and a red in `experiments/ptr-engine/longrun/tests/test_cap_gate.py:205` from *another* card was settled as the
claimant's `FAIL exit-1`. The defect was never that files move; it was that a claim was
recorded against unnamed bytes and that a settle-time failure was reported as the
claimant's fault. `tools/tree_freeze.py` exists so those two facts can never again be
substituted for one another.

## Tool

`experiments/ptr-engine/tools/tree_freeze.py` (stdlib, offline, records only — it never
repairs and never rewrites a file):

```
# freeze what you are about to judge (refuses a path that does not exist)
python3 experiments/ptr-engine/tools/tree_freeze.py freeze --out F.json PATH [PATH...]

# re-hash later: prints `path, recorded_sha, current_sha, verdict`
# exit 0 = every file `same`; exit 13 = at least one `moved` / `deleted`
python3 experiments/ptr-engine/tools/tree_freeze.py verify F.json

# freeze -> run -> re-verify -> one JSON record
python3 experiments/ptr-engine/tools/tree_freeze.py --wrap REC.json PATHS... -- CMD [ARGS...]
```

`moved` means **the bytes changed** (sha256 differs); `deleted` means gone. A bare `touch`
changes `mtime_ns` and is reported as `(touched)` while staying `same`, because a result
judged against identical bytes is not invalidated by a timestamp.

## The four verdicts

| verdict | command | tree | process exit | what it means |
|---|---|---|---|---|
| `pass` | 0 | unmoved | 0 | the work passed and the bytes it judged still exist |
| `moved_during_run` | 0 | moved | 13 | the work passed, but **unstamped**: re-run against the settled tree |
| `failed` | ≠0 | unmoved | 1 | the work failed on a still tree — a real FAIL |
| `failed_and_moved` | ≠0 | moved | 1 | both facts kept: the failure may be foreign, so re-run before believing it |

`13` is `exit_codes.EXIT_TREE_MOVED` (`name: tree-moved`), declared in the project's one
exit-code table and owned there via `EXTERNAL_CODES = {13: "tools/tree_freeze.py"}` because
`cell.py` never raises it. **A movement is never code 1**: "the tree moved" and "the work
failed" must not share a number, or a foreign red is settled as the claimant's verdict.

## Measured (2026-10-26 12:40, offline)

* The card's own pin was already stale when this unit re-checked it: `cell.py` was
  `24627d7b…` at the card's measurement (12:26:38) and `5a812a98…` here — it moved again.
  `run_longrun.py 9e8c30df…` and `grade_v5.py 056eb605…` still matched.
* Red→green on the classifier: a `/tmp` copy appended one byte 0.2 s into a wrapped run →
  `moved`, `moved_during_run`, exit **13**; a clean run → `pass`, exit **0**.
* `failed` (exit 3, nothing moved) and `failed_and_moved` (exit 3, one file moved) are
  distinguishable in the record alone.
* Evidence artefact: [`measure/TREE-FREEZE.json`](../experiments/ptr-engine/measure/TREE-FREEZE.json);
  tests: `experiments/ptr-engine/longrun/tests/test_tree_freeze.py` (14) and the new
  `ExternalCodeTests` in `experiments/ptr-engine/longrun/tests/test_exit_codes.py` (20 total).

## How to use it on a card

1. `freeze` the files your verdict will cite, before you read them.
2. Do the work; keep the freeze path in the handoff (`freeze_before`).
3. `--wrap` your evidence command, and settle from its `verdict`, never from the exit
   status alone: a `moved_during_run` card is re-run, not failed.

**Never** rewrite a recorded sha to make a record match, and never "repair" a freeze: the
tool records what it saw. If the tree moved, say so with the two digests.

## D1 fix: the baseline is the BEFORE freeze (TREE-FREEZE-D1-FIX)

What `V-TREE-FREEZE` measured, verbatim from its `defects` array:

> "D1 (high): a file DELETED by the wrapped command is not classified at all -- after=freeze(paths)
> refuses the missing path, --wrap exits 2 (usage) and writes NO record (reproduced twice).
> moved_during_run/failed_and_moved only ever describe changed bytes, never deletions."

The old `--wrap` took a second freeze AFTER the command and used it as the baseline, so the one
path the command deleted was exactly the path that second freeze refused. The fix is one line of
authority: after the command, `classify(before)` -- the freeze taken BEFORE the command ran -- is
the baseline, and the after-document is a snapshot written from those rows, never a fresh freeze.

### The four states (classification row shape)

| state | meaning | row digests |
|---|---|---|
| `same` | bytes identical to the before freeze (a bare `touch` is `same (touched)`) | `before` sha, `after` sha |
| `moved` | bytes differ | `before` sha, `after` sha |
| `deleted` | present before, absent after | `before` sha, `after: null` |
| `created` | absent before, present after, inside a declared root, not declared | `before: null`, `after` sha |

Every row also keeps `recorded_sha` / `current_sha` / `verdict`, so consumers written against the
old shape keep reading it; `state` is the authoritative key.

### Declared vs witnessed: what a creation can be

A path that does not exist cannot be DECLARED: `freeze` refuses it (exit 2) before the wrapped
command is ever started -- a baseline of nothing cannot be classified against, and a phantom
digest is indistinguishable from a mid-run deletion. So "the command created a declared file" is
not expressible, by design. Creation is instead WITNESSED: `--wrap` scans the declared roots (the
parent directory of each declared path, recursively, skipping `.git`/`__pycache__`/cache dirs)
before and after the run. A new file there is a `created` row, the record lists it under
`created`, and the output says **the declared set did not cover it**. A tree that grew is not a
`pass`.

### Verdict mapping (one function, `classify_verdict`, tested)

| command exit | any `moved` / `deleted` / `created` among declared paths | verdict | CLI exit |
|---|---|---|---|
| 0 | no | `pass` | 0 |
| 0 | yes | `moved_during_run` | 13 |
| nonzero | no | `failed` | 1 |
| nonzero | yes | `failed_and_moved` | 1 (the record keeps the command's own `exit_code`) |

No fifth outcome. `moved_during_run` is **unstamped, never FAIL**: a settle-time consumer must not
turn exit 13 into a failure verdict -- the remedy is a re-run against the settled tree.

`verify` also refuses a structurally invalid freeze document with exit 2 (D2: it used to raise
`KeyError('files')` and exit 1, the same code as "the command failed").

### Evidence

* `python3 -m pytest experiments/ptr-engine/longrun/tests/test_tree_freeze.py experiments/ptr-engine/longrun/tests/test_exit_codes.py -q`
  -> `42 passed, 14 subtests passed`. New induced cases: delete/exit 0 -> `deleted` row,
  `moved_during_run`, rc 13; create/exit 0 -> `created` row, `moved_during_run`, rc 13;
  edit/exit 1 -> `failed_and_moved`, rc 1; untouched/exit 1 -> `failed`, rc 1; declared path
  missing before the run -> refusal, rc 2, command never started.
* Bytes-named proof: freeze `/tmp/tfd1/one/input.py`
  `0a775022744f64c352863f165f2e125898419999bc57c83204772036d0ef6b2e`, append one byte, `verify` ->
  `829500d2d37c8a3a9c253cebf30c7144be0a872bfb462c99f2905357e26559bb`, verdict `moved`, rc 13.
* Red: the old after-freeze step on the same now-absent path raises `Refused` (CLI 2) and writes
  no document; the new wrapper writes a record with `deleted: [...]`, `after: null`, rc 13.
