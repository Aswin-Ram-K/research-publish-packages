# U-SPCC-59 — E2 readiness: the compaction interval is a parameter and a cell dimension

## Why

`PREREG-SPCC.md` §E2 varies `COMPACT_EVERY ∈ {12, 24, 48}` on one fixture and one
arm. Before this unit the interval was a module constant (`ptr_engine/layers.py:30`)
read directly at the fold (`ptr_engine/layers.py:230`), so no cell could vary it, and
G3's `n = turns × arms × reps` (`longrun/cell.py:1259`) refused a 100-turn
single-interval cell at `n=100 < 200`. E2 as preregistered was unrunnable.

## What changed

- `ptr_engine/layers.py`: `CompactionState` gains `compact_every: int = COMPACT_EVERY`;
  `compile_prompt(..., compact_every=None)` resolves the interval (explicit argument
  wins and is recorded on the state; otherwise the state's own value, default 24).
  The module constant stays and stays 24.
- `longrun/arm_cd.py`: `SpccArmState(..., compact_every=COMPACT_EVERY)` passes it to
  `CompactionState` and to `compile_prompt`.
- `longrun/run_longrun.py`: `--compact-every` (comma list), `compact_intervals(cfg)`,
  `expand_cells(arms, reps, intervals)`; cells are `(arm, rep, interval)`; the gate's
  arm term is `declared arms × interval variants`; `Planner`/`run_cell`/`run_dry` carry
  the interval. A single interval reproduces the pre-change cell list exactly.

`longrun/cell.py` was NOT changed: its arithmetic stays `turns × arms × reps`, and the
interval enters as an arm-variant count at the runner's call site.

## Evidence

- Red (new test against HEAD's `layers.py`/`arm_cd.py`/`run_longrun.py`):
  `TypeError: SpccArmState.__init__() got an unexpected keyword argument 'compact_every'`,
  `AttributeError: module 'run_longrun' has no attribute 'compact_intervals'`.
- Green: `8 passed` for `test_compact_every_param.py`; `26 passed` for the required
  five-file suite; `25 passed` for the adjacent gate/preview/claim suite.
- Default byte-identity: 30 prompt sha256 values captured from
  `git show HEAD:experiments/ptr-engine/ptr_engine/layers.py` match the current
  no-flag run exactly.
- Compaction turns: 12 → 13, 24 → 25, 48 → 49.
- Gate: `12,24,48` × 100 turns × 1 rep → `n=300`, admitted; single interval → `n=100`,
  refused.
- `python3 tools/doc_check.py` → exit 0.
