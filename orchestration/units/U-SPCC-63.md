# U-SPCC-63 — the masking window is a parameter (E3 readiness)

**Status:** DONE. Offline only: 0 endpoint requests, 0 model calls.

## Why

`PREREG-SPCC.md` §E3 asks whether the distance cliff is **position** or **eviction**, with
the body retained and no masking. `f4de200` made `COMPACT_EVERY` a parameter
(`--compact-every`), so the spcc arm can be told not to compact. The masking arm could not
be told not to mask: `WINDOW_TURNS = 4` was a module constant read directly at the cutoff
(`arm_cd.py:39`, `arm_cd.py:173`), so every arm-C run masked at `intro+4` and the two
explanations were indistinguishable.

## What changed

| file | change |
|---|---|
| `experiments/ptr-engine/longrun/arm_cd.py` | `WINDOW_TURNS` stays 4; `ArmCDState.__init__` takes `window_turns: int = WINDOW_TURNS` (validated `>= 1`), stored as `self.window_turns`; the cutoff reads `int(t) - int(self.window_turns)` |
| `experiments/ptr-engine/longrun/run_longrun.py` | `Planner.__init__(..., window_turns=arm_cd.WINDOW_TURNS)` passes it to `ArmCDState`; `run_cell(..., window_turns=...)`; `window_turns_setting(cfg)` resolves the flag; `--window-turns N` CLI flag; the dry-run preview reads the same setting; a non-default window is stamped into the run id as `-w<N>` |
| `experiments/ptr-engine/longrun/tests/test_window_turns_param.py` | new: the four properties below |

Unchanged: the masking semantics, the `[MASKED <ref>]` marker format, and the
`evicted == masked_rows` stamping (`run_longrun.py:1794`).

## Evidence

- Default is 4 and a no-flag run is **byte-identical**: 30 `prompt_sha256` values captured
  from `git show HEAD:experiments/ptr-engine/longrun/arm_cd.py` driven by the same 30-turn
  stub match the post-change run exactly.
- Window 200 over a 100-turn stub: `masked_rows == 0` on all 100 rows, no `[MASKED` in any
  prompt, and the T1 body `VAL_A = 3001` is still present in the T100 prompt.
- Window 4: T1's tool output is masked at t=5 (`cutoff = t-4`), T4's at t=8, and the marker
  persists on every later turn.
- `evicted == masked_rows` on every row at both windows.
- Red: `4 failed, 1 passed` — `TypeError: Planner.__init__() got an unexpected keyword
  argument 'window_turns'` and `AttributeError: 'ArmCDState' object has no attribute
  'window_turns'`.
- Green: `5 passed`; the four-file suite `31 passed`; `tools/doc_check.py` exit 0.

## How E3 uses it

`--window-turns 200` (any value above the fixture's turn count) on the C arm retains every
body: the arm then measures position with no eviction. `--window-turns 4` (or omitting the
flag) reproduces today's masking arm exactly.
