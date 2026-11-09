# Z1-BODIES — key pointer bodies by (task_id, ref); narrow handlers; move preview path

**Unit.** `Z1-BODIES` · offline.
**Objective.** Namespace `_BODIES` by `(task_id, ref)`; call `reset_bodies()` per fixture load; narrow broad exception handlers; move preview dir into workspace.
**Write paths.** `experiments/ptr-engine/ptr_engine/pointer_table.py`, `experiments/ptr-engine/longrun/run_longrun.py`, `experiments/ptr-engine/tests/test_body_namespacing.py`, `orchestration/units/Z1-BODIES.md`, `orchestration/handoffs/Z1-BODIES.json`.

## Procedure

1. `PointerEntry` gained `task_id`; `mask_output` accepts `task_id` and stores `_BODIES[(tid, ref)]`.
2. `build_table`/`fetch` accept `task_id`; fetch raises `PtrStoreMissError` when a live ref has no stored body.
3. `reset_bodies(task_id=None)` clears all or one fixture's bodies; called in `load_fixture`.
4. Narrowed all `except Exception` in `run_longrun.py` (6 sites) and `pointer_table.py`.
5. Preview path moved to `experiments/ptr-engine/state/previews/<task_id>`, recreated fresh per run.

## Verification

- `grep -n '_BODIES' ptr_engine/pointer_table.py` shows tuple keying.
- `grep -rn 'reset_bodies' --include=*.py ptr-engine` shows real caller (`longrun/run_longrun.py:322`).
- `grep -n 'except Exception' longrun/run_longrun.py ptr_engine/pointer_table.py` empty.
- `grep -rn '/tmp' longrun/run_longrun.py` empty.
- Red: reverting to bare ref gives `AssertionError: assert 'BETA body' == 'ALPHA body'`.
- Green: 24 passed.