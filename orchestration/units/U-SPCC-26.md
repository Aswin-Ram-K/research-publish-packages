# U-SPCC-26 — A dry run no longer deletes committed preview evidence

## 1. The defect

`experiments/ptr-engine/longrun/run_longrun.py` `run_dry` opened with:

```python
root = .../state/previews/<task_id>
if os.path.exists(root):
    shutil.rmtree(root)
```

`experiments/ptr-engine/state/previews/LR-01/**` is **tracked evidence** — the request
bodies each arm would send. Every offline `--dry-run` therefore wiped the whole task
directory and re-created only the arms/files that run happened to render. It destroyed
`LR-01/transcript-compact/turn-0{1,2,3}.json` twice (nine files were restored once by
hand; the three `transcript-compact` files, and the whole directory, were gone again at
this unit's start). A read-only-sounding command was mutating the committed record.

## 2. The rule chosen

**Delete nothing up front.** The dry run overwrites each preview it renders, and prunes
only (a) inside an arm it *just re-rendered* and (b) only a file whose turn lies inside
that run's turn scope (`<= n_turns`) which this run did not write — i.e. an artefact of a
naming the previous config produced at a turn this one no longer produces. Files of arms
the run does not render, and files beyond the run's turn scope, are never touched.

Invariant, stated in the code: **a dry run never leaves the working tree with fewer
tracked files than it found.**

## 3. Code change (`run_longrun.py`)

| Line | Change |
|---|---|
| `:2967` | `preview_root(task_id)` — the one place the committed tree path is computed |
| `:2976` | `prune_stale_previews(arm_root, written, n_turns)` — the narrow prune; returns removed paths |
| `:3004` | `run_dry(cfg, fixture, cells, root=None)` — `root` injectable so a test can aim a dry run at a temp dir |
| `:3010` | `root = root or preview_root(...)`; `os.makedirs(root, exist_ok=True)`; `rmtree` deleted |
| `:3070,3076,3088` | each `preview_write` site records `written.add(os.path.abspath(...))` |
| `:3095` | after an arm's turn loop, `prune_stale_previews` runs for that arm only, printing every removal |

## 4. Red → green (regression test)

New test `experiments/ptr-engine/longrun/tests/test_preview_preservation.py`
(`test_dry_run_keeps_previews_of_arms_it_does_not_render`): a synthetic task directory in
`tempfile.mkdtemp` holding (a) `masking-no-fetch/turn-01.json`, an arm the run never
renders, and (b) `pointer-stable/turn-48.json`, outside a `--max-turns 1` run's scope. It
runs the real `run_dry` against the real fixture `tasks-v4/runtime-v4/LR-01.v4.tools2.json`.

**Red** — with the old `rmtree` temporarily restored:

```
FAILED experiments/ptr-engine/longrun/tests/test_preview_preservation.py::test_dry_run_keeps_previews_of_arms_it_does_not_render
AssertionError: the dry run deleted /tmp/preview-preserve-8sn9o3sg/masking-no-fetch/turn-01.json: an arm it never rendered
1 failed in 0.05s
```

**Green** — after removing it:

```
.                                                                        [100%]
1 passed in 0.05s
```

## 5. Evidence restored

`transcript-compact/turn-0{1,2,3}.json` re-written from `git show HEAD:<path>`; the
directory itself had to be re-created (`mkdir -p`) because the rmtree removed it. All
three `sha256sum` values equal `git show HEAD:<path> | sha256sum`:

| file | sha256 (disk == HEAD) |
|---|---|
| turn-01.json | `934c1533e70a80e37a634fa773fc165cea49dc943e004ecde03393cfa6ea8b70` |
| turn-02.json | `e7f11cdc6c187482791bb5579b508eba3d3a00fa588b850b73f9416f930adad9` |
| turn-03.json | `d841695713b8032594b43e78f2ca6899b446e61d764c9417c5e3706c2785cec5` |

After the restore `git status --porcelain` showed only the intended
`M experiments/ptr-engine/longrun/run_longrun.py`, i.e. the deletions were undone exactly.

## 6. Landing

Commit `990edc3` was produced by peer unit **U-SPCC-27** (`git add -A` in the shared
checkout) and already contains this unit's two files:

```
 experiments/ptr-engine/longrun/run_longrun.py      | 58 ++++++++++++++++--
 .../longrun/tests/test_preview_preservation.py     | 71 ++++++++++++++++++++++
```

The test was re-run **from HEAD** after that commit and passes (`1 passed in 0.03s`), so
the green above is the state of the repository, not just of the working tree. Docs gate:
`python3 tools/doc_check.py` → `OK docs clean`, `exit=0`.
