# U-SPCC-17 — ptr-engine longrun scratch residue

STATUS: DONE.

## Decision
`experiments/ptr-engine/longrun/state/scratch/` is an **output root**, not an input root.
The only producer is `experiments/ptr-engine/longrun/tests/test_fixture_schema.py:14`
(`SCRATCH = os.path.join(LONGRUN, "state", "scratch", "u11")`) and `:19`
(`d = tempfile.mkdtemp(dir=SCRATCH)`), whose `_write()` dumps `fx.json` for negative-schema
tests and never cleans up. Nothing in `experiments/ptr-engine` reads those files back
(`grep -rn "state/scratch"` over py/md/json/sh: zero hits).

Therefore: deleted the 60 untracked `tmp*/fx.json` dumps and added a narrow ignore rule.

## Evidence
- Before: 60 untracked dirs (60 `fx.json`), 260 `fx.json` on disk (200 already tracked), `du -sh u11` = 8.2M.
- After: 0 untracked, 200 tracked `fx.json` remain on disk, `du -sh u11` = 6.3M.
- `git check-ignore -v --no-index .../u11/tmp1/fx.json`: before = no output, exit 1 (not ignored);
  after = `.gitignore:45:experiments/ptr-engine/longrun/state/scratch/` exit 0.
- 204 tracked files under `.../longrun/state` unchanged (older `u11/tmp*/fx.json` and `scratch/probe/*.json`
  were already committed history; the ignore rule cannot and did not untrack them).
- `git status --porcelain | wc -l` = 1 (` M .gitignore`); zero `state/scratch` entries.

## .gitignore added
```
# ptr-engine longrun fixture-run residue: run residue, not inputs (written by
# tempfile.mkdtemp(dir=SCRATCH) in experiments/ptr-engine/longrun/tests/test_fixture_schema.py).
experiments/ptr-engine/longrun/state/scratch/
```

Note: 60 dirs is the real count, not the 60/60-per-file 60-file figure assumed in the ticket.
