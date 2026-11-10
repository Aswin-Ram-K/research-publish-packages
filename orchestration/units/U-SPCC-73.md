# U-SPCC-73 — `--preview-root`: a dry run must not overwrite committed previews

## Defect

Running the longrun suite overwrote six tracked evidence files:

```
experiments/ptr-engine/state/previews/LR-01/pointer-stable/turn-0{1,2,3}.json
experiments/ptr-engine/state/previews/LR-01/transcript-compact/turn-0{1,2,3}.json
```

The diff replaced a populated `INDEX` block with an empty one: the test's dry run has no
index, so it wrote a degraded preview over committed evidence.

Cause: `run_dry(cfg, fixture, cells, root=None)` at
`experiments/ptr-engine/longrun/run_longrun.py:3199` defaults
`root = root or preview_root(fixture["task_id"])` (`:3201`), i.e. the tracked tree. The CLI
dispatch called `run_dry(cfg, fixture, cells)` with **no** `root=`, and there was no
`--preview-root` flag, so any test invoking `R.main(["--dry-run", ...])` wrote into
`experiments/ptr-engine/state/previews/`.

## Fix

1. `experiments/ptr-engine/longrun/run_longrun.py:4321-4324` — new flag:

```python
    ap.add_argument("--preview-root", default=None, dest="preview_root",
                    help="redirect the dry-run preview tree (default: the tracked "
                         "state/previews/<task_id> tree). Tests MUST pass a temp dir so a "
                         "dry run never overwrites committed evidence.")
```

2. `experiments/ptr-engine/longrun/run_longrun.py:4700` — thread it:

```python
        return run_dry(cfg, fixture, cells, root=cfg.preview_root)
```

3. `experiments/ptr-engine/longrun/tests/test_dry_turn_scope.py:92` — `_dry_run` now passes
   `"--preview-root", os.path.join(tmpdir, "previews")`.
4. `experiments/ptr-engine/longrun/tests/test_wall_key.py:160` —
   `test_dry_run_manifest_records_the_per_arm_wall_not_the_top_level_one` now passes
   `"--preview-root", os.path.join(tmp, "previews")`.

No assertion changed in either test.

## Evidence

Full longrun directory (`TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest -q
experiments/ptr-engine/longrun/tests`):

```
2 failed, 929 passed, 1 warning, 36 subtests passed in 41.06s
```

The two reds are the known correctly-red tests: `test_journal_lint.py::test_census_over_the_live_corpus_is_reported`
and `test_request_ledger.py::TestRealCorpus::test_g_real_corpus_total_and_delta_from_466`.

`git --no-optional-locks status --porcelain` after the suite lists only the three edited
files — the six previews are untouched.

Default path still the tracked tree (no `--preview-root`):

```
preview_root(task_id) = /home/zer0null/research extractor/experiments/ptr-engine/state/previews/LR-01
rc = 0
files written under tracked root:
   .../state/previews/LR-01/pointer-stable/turn-01.json
   .../state/previews/LR-01/pointer-stable/turn-02.json
   .../state/previews/LR-01/pointer-stable/turn-03.json
   .../state/previews/LR-01/transcript-compact/turn-01.json
   .../state/previews/LR-01/transcript-compact/turn-02.json
   .../state/previews/LR-01/transcript-compact/turn-03.json
```

Those three modified previews were restored from HEAD afterwards.

## Note

`test_gate_override.py::GateOverride::test_hostile_values_still_refuse_exit_8` failed once
in a full-directory run (`--projected-turn-wall '-1' must be refused by G2 (exit 8), got 0`)
and passes in isolation and in the confirming full run. It drives `cell.py` with a stub
runner and does not import `run_longrun.py`, so it is order-dependent, not caused by this
change.
