# FROZEN-TREE — verify a snapshot, not a moving tree

`experiments/ptr-engine/tools/frozen_tree.py` + `experiments/ptr-engine/longrun/tests/test_frozen_tree.py`
Unit `FROZEN-TREE`. Offline, stdlib only, no network, **no `git` invocation anywhere**.

## The cost this removes

`VERIFY-BATCH-1` reads `run_longrun.py`, `client.py`, `fixture_coverage.py`,
`tasks-v5/runtime-v5/LR-01.v6.json`, `matrix_audit.py` and `handoff_lint.py`. Because it reads
them **live**, every author whose write path touches one of those files is held: six cards
(`PROJECTION-CALIBRATION`, `LINT-RECOVERED-STATUS`, `RECORD-STOP-REASON`, `FIXTURE-GENERATIONS`,
`GRADE-V5-REPAIR`, and the batch itself) sat in `todo` for that reason alone. One verifier
serialised the batch — not because it verified too much, but because its jurisdiction was the
live tree.

The fix is a frozen copy with a recorded identity. The verifier runs against files copied at
recorded sha256 values and **refuses to report a verdict if any snapshot input changed under it**.
Authors may then write freely, because the verifier's jurisdiction is the snapshot, not the tree.

## Interface

```python
snapshot(paths, dest, include_imports=False, root=None) -> manifest
verify(snapshot_dir, command, cwd=None, timeout=None) -> result
verdict_exit_code(result) -> int
snapshot_sha256(files) -> str          # sha256 of the canonical per-file digests
SnapshotRefused                         # always names the offending path
```

```bash
python3 experiments/ptr-engine/tools/frozen_tree.py snapshot --dest DIR PATH...
python3 experiments/ptr-engine/tools/frozen_tree.py verify --snapshot DIR -- CMD...
#   --json prints ONLY the result object on stdout
#   --root, --include-imports on snapshot; --cwd, --timeout on verify
```

`snapshot` copies named files (and directories recursively, `.git` never entered) preserving
relative paths, and writes `dest/SNAPSHOT.json` with per file `relpath`, `sha256`, `bytes`,
`mtime_ns`. `verify` re-digests every listed file **before** the run, runs the command with
`cwd` inside the snapshot, then re-digests **after**.

Result object (exactly these keys):

```json
{"command": [...], "exit_code": 0, "duration_ms": 12,
 "inputs_unchanged": true, "changed": [],
 "snapshot_sha256": "…", "stdout_tail": "…", "stderr_tail": "…"}
```

## Exit codes

| code | meaning |
|---|---|
| 0 | ok — inputs held, command exited 0 |
| 1 | command failed (inputs held) |
| 2 | **snapshot mutated or invalid** — fatal, beats the command's own exit code |
| 3 | usage error, or a refused snapshot (missing path, escaping symlink) |

`inputs_unchanged: false` is fatal by design: a verification whose inputs moved is not a verdict.
A snapshot that was already mutated *before* the run, or whose `SNAPSHOT.json` disagrees with its
own digests, is `invalid` → exit 2 with `exit_code: null` and the changed relpaths named.

## What `snapshot_sha256` is, and is not

It is the sha256 of the canonical JSON of the per-file digests —
`[{"relpath": …, "sha256": …}, …]`, sorted by relpath, `sort_keys=True`, separators `(",", ":")`.
It is **not** a function of copy time, `mtime_ns` or `bytes`, so:

* the same bytes snapshotted at two different times keep **one** identity (test f);
* one changed byte changes it (test f);
* a verdict can name exactly what it judged, and a re-run against different bytes cannot
  impersonate the earlier verdict.

## Containment: a refused snapshot leaves no `dest`

The tree is built in a sibling temp directory (`tempfile.mkdtemp` next to `dest`), fully
digested and verified byte-identical against the source, then published with one `os.rename`.
On any exception the temp directory is removed; `dest` never exists in a partial state. Chosen
over "copy then clean up" because a kill mid-cleanup can leave a dest that *looks* valid.

**Atomic temp-dir + rename is what this unit used** (test d asserts `not dest.exists()` after a
missing input, test e after an escaping symlink).

## Demonstrated use

Snapshot of the six `VERIFY-BATCH-1` inputs (plus the test module to run):

```
snapshot /tmp/ft-demo  →  snapshot_sha256 3776faed510c72501fb2abbaa20bb0e2b7951280b974f8ad11c0639da8e7db53
  files 7: client.py, run_longrun.py, tasks-v5/runtime-v5/LR-01.v6.json,
           experiments/ptr-engine/longrun/tests/test_handoff_lint.py, fixture_coverage.py, handoff_lint.py, matrix_audit.py

verify --snapshot /tmp/ft-demo -- python3 -m pytest experiments/ptr-engine/longrun/tests/test_handoff_lint.py -q -p no:cacheprovider
  exit 0 · inputs_unchanged true · changed [] · "13 passed in 0.02s"
```

No file outside the snapshot was needed: the preserved relative layout keeps the test's
`HERE/../../tools` and `HERE/../../../..` path arithmetic pointing inside the snapshot.

Mutation is fatal on a real snapshot too:

```
verify --snapshot /tmp/ft-mut -- python3 -c "open('experiments/ptr-engine/tools/handoff_lint.py','a').write('# mutated during run\n')"
  exit 2 · inputs_unchanged false · changed ["experiments/ptr-engine/tools/handoff_lint.py"]
```

## Limits — read before trusting a verdict

* **Only the listed files are digested.** A command that creates new files (e.g. `__pycache__`,
  a fresh log) does not make `inputs_unchanged` false; the unit detects *movement of declared
  inputs*, not a hermetic sandbox. Declare every input that matters.
* **Writes elsewhere are not prevented.** The command runs with the caller's permissions; the
  tool reports, it does not jail. It is a jurisdiction boundary, not a security boundary.
* `include_imports` follows only top-level absolute Python imports resolvable under the
  workspace root or next to the importing file; stdlib and unfindable modules are ignored.
* `snapshot` refuses an existing `dest`; take a fresh directory per verification.
* Snapshot and verify in **one** command when `dest` lives in the platform temp area: this
  host's temp tree is not persistent between separate shell invocations (`/tmp/ft-demo` was gone
  on the next call), which is a property of the environment, not of the tool. A `dest` inside the
  workspace survives; a temp `dest` must be created and consumed in the same invocation.
* Relative CLI paths resolve against the workspace root (`cwd` unless `--root`); absolute paths
  outside the root are refused as escaping the workspace.

## Red→green record

Tests: `experiments/ptr-engine/longrun/tests/test_frozen_tree.py` (7 tests, offline, no git).
Red 1 (tool absent): `ModuleNotFoundError: No module named 'frozen_tree'` — collection error.
Red 2 (result object carried an extra `timed_out` key): `test_g_json_stdout_is_only_the_result_object`
`AssertionError: Extra items in the left set: 'timed_out'`.
Green: `7 passed in 0.23s`. See `orchestration/units/FROZEN-TREE.md` for the per-test lines.
