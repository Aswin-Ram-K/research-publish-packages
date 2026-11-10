# U-SPCC-13 — host-aware memory window

Status: **done**

## Defect

`spcc_supervisor.py` enforced a 60 GB allowance by sampling `/proc/meminfo` of
the machine it ran on. That box is 29 GB; the workload's host (GX10) has a
121 GB unified pool. `60 + 8 = 68 > 29`, so admission could never pass, and
passing it would have bounded the laptop instead of the accelerator.

## Change

- `MemSource` + `LocalMeminfo` (reads `/proc/meminfo`, `SPCC_MEMINFO_PATH`
  aware) and `RemoteMeminfo(host, runner=None)` (`ssh -o BatchMode=yes <host>
  cat /proc/meminfo`; any failure raises, never zeros).
- `MIN_TOTAL_GB = 100`; `open-window` reads `MemTotal` from the chosen source
  first and refuses below it with exit code **4** (allowance refusals stay **2**,
  run preconditions **3**), naming both numbers and the 121 GB pool.
- `--target-host` on `open-window` / `run` (`SPCC_TARGET_HOST` fallback).
- Window JSON: `mem_source` (`local` | `ssh:<host>`), `mem_total_gb`,
  `enforcement` (`cgroup` | `declared-only`). `cgroup` only for a local source;
  a remote source skips cgroup creation and can only yield `declared-only`.
- Declared-only windows keep the declared-peak admission and `MemAvailable`
  sampling, record `cgroup_peak_gb: null`, `unaccounted_gb: null`,
  `unaccounted_reason: "remote-host-declared-only"`, and the decision chain
  gains `remote-host-declared-only` as the last row before `VERIFIED`. The
  existing local rows keep their order and semantics.

## Evidence

Real box, real source:

```
refusing: mem_source local reports MemTotal 29.9 GB < 100 GB minimum; the allowance governs a 121 GB pool and this supervisor would bound the wrong machine
exit=4
```

Tests (injected readers; **ssh was not exercised** — no network in this unit):

```
$ .venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q
...........................                                              [100%]
27 passed in 9.85s
```

Red→green for `test_wrong_host_memtotal_29_refused_before_child` against the
pre-fix copy (`/tmp/spcc_supervisor_prefix.py`):

```
>       assert r.returncode == 4, r.stdout + r.stderr
E       AssertionError: refusing: MemAvailable 10.0 GB < 68.0 GB reserve (short by 58.0 GB)
E       assert 2 == 4
1 failed in 0.06s
```

Green:

```
$ .venv/bin/python -m pytest ".../test_spcc_supervisor.py::test_wrong_host_memtotal_29_refused_before_child" -q
1 passed in 0.07s
```

## Schema

`serving/MEM-WINDOW.schema.md` gained `## Which host is measured` (mem_source /
enforcement / MIN_TOTAL_GB rationale), the new open+close fields, the new
decision-table row, the exit-code split, and a note that the reserve follows
`mem_source` rather than this laptop.

## Files

- `experiments/ptr-engine/serving/spcc_supervisor.py`
- `experiments/ptr-engine/serving/tests/test_spcc_supervisor.py`
- `experiments/ptr-engine/serving/MEM-WINDOW.schema.md`
