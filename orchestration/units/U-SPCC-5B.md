# U-SPCC-5B — repair spcc_supervisor defects

Fix the three V-SPCC-5 defects in `experiments/ptr-engine/serving/spcc_supervisor.py`
and `experiments/ptr-engine/serving/tests/test_spcc_supervisor.py`.

## Defect 1 — window record leak

`SpccSupervisor.run` now removes `MEM-WINDOW.json` in `finally` on every exit path:
normal completion, child crash, SIGINT/SIGTERM delivered to the supervisor (handlers
signal the child group and set a stop flag), and an exception raised in the sampling
thread. The finalised window record is appended to `MEM-WINDOW.jsonl` **before** the
live file is unlinked, so the measurement is not lost.

## Defect 2 — untested kill path

The cgroup root, peak source and kill grace are injectable:
`SpccSupervisor(cgroup_root=..., peak_source=..., meminfo_path=..., base_dir=..., grace_seconds=...)`
(with aliases `Supervisor`, `SpccRunSupervisor`, `MemorySupervisor`, `RunSupervisor`),
plus env overrides `SPCC_CGROUP_ROOT`, `SPCC_PEAK_FILE` / `SPCC_PEAK_SOURCE` /
`SPCC_PEAK_PATH` / `SPCC_PEAK_OVERRIDE`, and
`--grace/--kill-grace/--grace-seconds/--kill-grace-seconds`. The grace period defaults
to 10 s and tests pass 0.2 s; the module docstring states this. `cmd_run` also accepts
the injection kwargs. The child is started in its own session and signalled as a
process group, so a SIGTERM-ignoring shell cannot leave descendants holding the
supervisor's pipes.

Tests drive `memory.peak` above 60 GiB and assert SIGTERM->SIGKILL with the injected
grace and `killed: "cgroup-peak"` in the finalised record.

## Defect 3 — unreadable reads coerced to zero

`_read_peak` raises instead of returning 0; `Sampler._one_sample` surfaces the first
unreadable `memory.peak`, `memory.current` or `MemAvailable` as `self.error` and stops
the sampler; the main loop and the finaliser both terminate the child and record
`aborted: "sample-unreadable"` with `aborted_path`. No code path continues on a
fabricated zero.

## Tests

`12 passed` in the acceptance command. Added behaviours: exit-code propagation, child
killed by signal with the window removed and the child's signal recorded, unreadable
peak abort, cap kill with SIGTERM only, cap kill escalating to SIGKILL, and the
existing marker-file proof that no child starts when cgroup setup fails.

## Files changed

- `experiments/ptr-engine/serving/spcc_supervisor.py`
- `experiments/ptr-engine/serving/tests/test_spcc_supervisor.py`

Untouched: `launch-sglang-spcc.sh`, `MEM-WINDOW.schema.md`, anything outside
`experiments/ptr-engine/serving/`.
