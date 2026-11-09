# V12 Verify

1. _BODIES keyed by (task_id, ref): `_BODIES[(tid, ref)] = body` (pointer_table.py:111); fetch lookup `_BODIES[key]` with key=(tid,safe_ref) (pointer_table.py:204). PASS.
2. reset_bodies caller on real path: longrun/run_longrun.py:317/321-322 imports and calls reset_bodies(doc.get("task_id")). PASS.
3. `except Exception`: empty in both files. PASS.
4. `/tmp` in run_longrun.py: empty. Preview path `state/previews/<task_id>`, cleared via shutil.rmtree per run (run_longrun.py:2601-2606). PASS.
5. Collision probe: same ref different bodies -> each fetch returns own body; unstored ref raises PtrStoreMissError. PASS.
6. pytest 5 files: 30 passed. PASS.

overall: PASS (6/6).
blockers: (a) resolved, (b) resolved.
