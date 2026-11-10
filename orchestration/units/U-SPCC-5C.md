# U-SPCC-5C — supervisor accounting honesty + window ownership

Closes the four defects named by `V-SPCC-5B` in
`experiments/ptr-engine/serving/spcc_supervisor.py`.

## Fixes

1. **A killed window is never `VERIFIED`.** `allowance` is now decided as:
   `killed is not None` or `aborted is not None` → `UNVERIFIED`;
   `unaccounted_gb is None or < 0` → `UNVERIFIED`; otherwise `VERIFIED`. The
   invariant is in the module docstring: *a window that did not complete
   normally is never counted inside the cap.* Driving `killed='cgroup-peak'`
   now yields `UNVERIFIED` (previously `VERIFIED`, because the peak read
   succeeded and the remainder was 0).
2. **No fabricated zeros.** `peak_bytes`/`close_ma` are initialised to `None`;
   `cgroup_peak_gb` and `unaccounted_gb` are written as JSON `null` when their
   read failed, with `unaccounted_reason: "close-read-failed"`. `cmd_close_window`
   prints `null` instead of formatting a missing value (it would have raised).
3. **Negative unaccounted is unmeasured.** `unaccounted_gb < 0` is recorded
   as-is for diagnosis and forces `allowance: "UNVERIFIED"` with
   `unaccounted_reason: "mem-available-rose"`.
4. **Window ownership pid.** `cmd_open_window` records `owner_pid`,
   `owner_start_time` (`/proc/<pid>/stat` field 22) and an `owners` chain of
   the opener plus its immediate parent. `run` accepts the window iff some
   recorded (pid, start_time) pair still matches a live process, so a wrapper
   shell keeps the window usable and pid reuse cannot revive it. Documented in
   `MEM-WINDOW.schema.md`.

Bonus in scope (same refusal surface): refusals now name the blocking number
and the shortfall —
`refusing: MemAvailable 14.0 GB < 68.0 GB reserve (short by 54.0 GB)` and
`declared peak 61.0 GB exceeds cap 60 GB (over by 1.0 GB)`.

## Notes

- `MEM-WINDOW.schema.md` was a stale full copy of the supervisor source
  (314 lines of Python, `import argparse` at line 7). It is now the actual
  record schema: files, invariants, open/close field tables, ownership rule,
  allowance decision table, refusal message forms.
- `_base_dir()` makes `owner_chain` the only /proc dependency; on a host
  without `/proc` every start time is `null` and liveness falls back to
  `kill(pid, 0)` (legacy path, documented).
- A single-command `bash -c` execs its last command, so the recorded parent
  can be the caller; only a genuine multi-command wrapper contributes a
  short-lived parent. The refusal test forces this with a trailing `; :`.

## Verification

`.venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q`
→ **18 passed in 8.60s** (13 pre-existing + 5 new).

New tests: `test_killed_window_never_verified`,
`test_closing_read_failure_records_null_not_zero`,
`test_memavailable_rose_stays_unverified`,
`test_owner_wrapper_bash_c_accepted`,
`test_owner_refused_after_owner_exits_and_pid_reuse_defeated`,
`test_refusal_names_shortfall`.

No GPU job, no container, no real `MEM-WINDOW.json` in `serving/` (tests use
`SPCC_BASE_DIR` under `tmp_path`; `ls serving/` shows none).
