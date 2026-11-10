# V-SPCC-5 — verify spcc_supervisor

Independent re-check of `experiments/ptr-engine/serving/spcc_supervisor.py`.

## Author tests
`.venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q` → `7 passed in 4.88s`. Covers declared-peak refusal, MemAvailable refusal, run-no-window, unwritable cgroup, peak (best-effort/no-op), clean run, clean run with sleep. Does NOT exercise real peak kill or window removal on crash.

## Checks performed
1. open-window declared 61 → exit 2 "refusing: declared peak 61.0 GB exceeds cap 60 GB", no MEM-WINDOW.json written.
2. MemAvailable below 68 GB reserve → exit 2, no window.
3. run with no window → exit 3, marker absent.
4. run with unwritable cgroup root → exit 3, marker absent.
5. CAP_BYTES == 64424509440 written to memory.max (lines 133,147); child pid written to cgroup.procs (line 193); no child spawn when setup fails (lines 176-179).
6. try/finally samples cgroup peak and writes window; does not unlink MEM-WINDOW.json.
7. serving dir has no stray MEM-WINDOW.json.
8. unaccounted_gb = (opened_ma - close_ma) - cgroup_peak_gb (line 236); positive → allowance UNVERIFIED (lines 241-244). Correct.

## Defects
- `cmd_run` never removes `MEM-WINDOW.json` (even in finally), so a completed/crashed run leaves the window in place, blocking `launch-sglang-spcc.sh`.
- No injection point exists to drive `memory.peak` above the cap, so the peak-kill/SIGTERM/SIGKILL-escalation path is untested.
- Peak kill path reads `memory.peak` with `int(...)` and catches exceptions as 0, masking unreadable peak files.
