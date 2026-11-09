# Unit FROZEN-TREE — verify a snapshot, not a moving tree

Card: `6e601e58-8084-4cbf-a449-aa3a56c69063` · execution `b39916e8-5989-471f-ab53-8ed57f482a9f`
Tag: `[automated]` — OFFLINE, zero inference requests, no network, no `git`.

## Purpose

Give a verifier a jurisdiction that is not the live tree: copy the files a batch verification
reads at recorded sha256s, run the command inside that copy, and refuse a verdict if any declared
input moved. This releases the authors whose write paths touch `run_longrun.py`, `client.py`,
`fixture_coverage.py`, `tasks-v5/runtime-v5/LR-01.v6.json`, `matrix_audit.py`, `handoff_lint.py`
from being serialised behind `VERIFY-BATCH-1`.

## Bound

≤26 tool calls, zero requests. Handoff `partial` within 4 calls; journal first. **Used 21 calls,
0 requests.**

## Write paths

* `experiments/ptr-engine/tools/frozen_tree.py`
* `experiments/ptr-engine/longrun/tests/test_frozen_tree.py`
* `docs/FROZEN-TREE.md`
* `orchestration/units/FROZEN-TREE.md`
* `orchestration/handoffs/FROZEN-TREE.json`
* `orchestration/journals/FROZEN-TREE.jsonl`

## Delivered

1. `snapshot(paths, dest, include_imports=False, root=None)` — copies files/recursive dirs,
   preserves relative paths, writes `dest/SNAPSHOT.json` (`relpath`, `sha256`, `bytes`,
   `mtime_ns`) and `snapshot_sha256`. Refuses (named path, exit 3, no `dest`) on a missing path,
   a path outside the root, or a symlink escaping the root. `.git` is never entered.
2. `verify(snapshot_dir, command, cwd=None, timeout=None)` — digests before, runs with `cwd`
   inside the snapshot, digests after; returns exactly `{command, exit_code, duration_ms,
   inputs_unchanged, changed, snapshot_sha256, stdout_tail, stderr_tail}`.
3. `inputs_unchanged: false` → exit **2** and a result that names the mutated relpaths.
4. CLI `snapshot --dest DIR PATH...` / `verify --snapshot DIR -- CMD...`; exit codes 0/1/2/3;
   `--json` prints the result object on stdout and nothing else.
5. Atomicity by **temp dir + `os.rename`**; temp removed on any failure, so a refused snapshot
   never leaves a partial `dest`.
6. `snapshot_sha256` = sha256 of canonical JSON of `[{"relpath","sha256"}]` (sorted,
   `sort_keys`, separators `(",", ":")`) — stable across copy times, changes on one byte.

## Red outputs (pasted)

Red 1 — tool absent, tests collected first:

```
$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_frozen_tree.py -q
ERROR collecting experiments/ptr-engine/longrun/tests/test_frozen_tree.py
...
E   ModuleNotFoundError: No module named 'frozen_tree'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection not found !!!!!!!!!!!!!!!!!!!!
1 error in 0.05s
```

Red 2 — result object carried one key too many (`timed_out`), caught by the strict shape test:

```
____________________ test_g_json_stdout_is_only_the_result_object _____________________
E       AssertionError: assert {'changed', '..._sha256', ...} == {'changed', '..._sha256', ...}
E         Extra items in the left set:
E         'timed_out'
experiments/ptr-engine/longrun/tests/test_frozen_tree.py:203: AssertionError
FAILED experiments/ptr-engine/longrun/tests/test_frozen_tree.py::test_g_json_stdout_is_only_the_result_object
1 failed, 6 passed in 0.25s
```

Fix: the timeout is reported through `exit_code: 124` + `stderr_tail`, not an extra key, so the
result object is exactly the contracted eight keys.

## Green output (pasted)

```
$ python3 -m pytest experiments/ptr-engine/longrun/tests/test_frozen_tree.py -v
test_a_snapshot_reproduces_digests PASSED                 [ 14%]
test_b_mutated_input_is_fatal PASSED                      [ 28%]
test_c_failing_command_with_stable_inputs PASSED           [ 42%]
test_d_missing_input_refused_and_no_partial_dest PASSED    [ 57%]
test_e_symlink_escaping_root_refused PASSED                [ 71%]
test_f_snapshot_sha256_is_stable_and_content_sensitive PASSED [ 85%]
test_g_json_stdout_is_only_the_result_object PASSED        [100%]
7 passed in 0.24s
```

## Demonstration — the real use

Snapshot of the six files `VERIFY-BATCH-1` reads (plus the test module to run), dest `/tmp/ft-demo`
(a disposable temp dir — nothing was written into the live tree):

```
$ python3 experiments/ptr-engine/tools/frozen_tree.py snapshot --dest /tmp/ft-demo \
    experiments/ptr-engine/longrun/run_longrun.py \
    experiments/ptr-engine/longrun/client.py \
    experiments/ptr-engine/tools/fixture_coverage.py \
    experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json \
    experiments/ptr-engine/tools/matrix_audit.py \
    experiments/ptr-engine/tools/handoff_lint.py \
    experiments/ptr-engine/longrun/tests/test_handoff_lint.py
snapshot /tmp/ft-demo
  snapshot_sha256 3776faed510c72501fb2abbaa20bb0e2b7951280b974f8ad11c0639da8e7db53
  files 7
SNAPSHOT EXIT=0

$ python3 experiments/ptr-engine/tools/frozen_tree.py verify --json --snapshot /tmp/ft-demo -- \
    python3 -m pytest experiments/ptr-engine/longrun/tests/test_handoff_lint.py -q -p no:cacheprovider
{"changed": [], ..., "exit_code": 0, "inputs_unchanged": true,
 "snapshot_sha256": "3776faed510c72501fb2abbaa20bb0e2b7951280b974f8ad11c0639da8e7db53",
 "stdout_tail": ".............  [100%]\n13 passed in 0.02s\n"}
VERIFY EXIT=0
```

**snapshot_sha256 `3776faed510c72501fb2abbaa20bb0e2b7951280b974f8ad11c0639da8e7db53`, exit 0.**
No file outside the snapshot was needed: the preserved relative layout keeps the test module's
`HERE/../../tools` and `HERE/../../../..` arithmetic pointing inside the snapshot.

Mutation on a real snapshot is fatal:

```
$ python3 experiments/ptr-engine/tools/frozen_tree.py verify --json --snapshot /tmp/ft-mut -- \
    python3 -c "open('experiments/ptr-engine/tools/handoff_lint.py','a').write('# mutated during run\n')"
{"changed": ["experiments/ptr-engine/tools/handoff_lint.py"], "exit_code": 0,
 "inputs_unchanged": false, "snapshot_sha256": "9cb635badadf46e882a844bd49e204e83d48abd231480514c3e1976dd9bfa25d", ...}
VERIFY EXIT=2
```

The command succeeded (exit 0) and still the verdict is exit **2**: a verification whose inputs
moved is not a verdict.

## Constraints honoured

* Zero inference requests; no network; **no `git` invocation** (tool, tests, demo commands all
  copy/read the filesystem directly; `.git` is pruned unread).
* None of the six demonstrated files was modified — they were only read and copied; the demo
  wrote exclusively into `/tmp`.
* No edits to `cell.py`, `run_longrun.py`, `client.py`, `grade_v5.py`, `analyze_stats.py`,
  `fixture_coverage.py`, `matrix_audit.py`, `handoff_lint.py`, fixtures, historical rows/grades,
  or `orchestration/handoffs/` (except this unit's own handoff file).
* Partial `dest` never survives a refusal (test d, test e).

## Answer

**Can a verifier now judge a card without reading the live tree?** Yes — `verify` judges the
snapshot named by `snapshot_sha256`, refuses to report if those inputs move, and therefore holds
no author's live write path for the duration of its run.

## Next hint

`VERIFY-BATCH-1` should snapshot its six inputs at the start of its run (`--include-imports` if it
imports siblings), record that `snapshot_sha256` in its verdict handoff, and run its commands with
`verify --snapshot ... --`; a `changed` relpath at settle time means re-snapshot and re-verdict,
never a PASS.
