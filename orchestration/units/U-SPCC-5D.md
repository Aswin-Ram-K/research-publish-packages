# U-SPCC-5D — allowance decision chain: signal death and peak-over-cap

Status: COMPLETE

## Target
`experiments/ptr-engine/serving/spcc_supervisor.py`, `experiments/ptr-engine/serving/MEM-WINDOW.schema.md`,
`experiments/ptr-engine/serving/tests/test_spcc_supervisor.py` (tests only). No other path touched.

## Defect closed
`spcc_supervisor.py` stamped `allowance: VERIFIED` when the child died by signal
(`returncode -9`, kernel OOM kill) while the measured cgroup peak was above the 60 GB cap,
because the decision omitted both `returncode < 0` and `cgroup_peak_gb > CAP_GB`.
Reproduced case: peak 62.0 GiB, `returncode -9`, `killed null`, `unaccounted 4.0` → VERIFIED.
Secondary: `_setup_cgroup` fabricated `'0'` into `memory.peak` when the kernel file was absent.

## Changes
1. `_setup_cgroup` no longer creates `memory.peak`; only `memory.current` is created when absent.
2. `_read_peak` returns `None` (unknown) when `memory.peak` is absent AND no source is explicitly
   configured (`SPCC_PEAK_FILE/SOURCE/PATH/OVERRIDE` or a non-callable `peak_source`). An explicitly
   configured source that is missing/unreadable still raises, so the run aborts (existing contract).
3. Run-loop cap check skips comparison when the peak is `None` (unknown cannot be "under cap").
4. Single ordered allowance chain; VERIFIED is the last resort. New `allowance_reason` field:
   `killed-by-supervisor`, `aborted`, `died-by-signal`, `peak-unknown`, `peak-exceeded-cap`,
   `unaccounted-unknown`, `mem-available-rose`, or the measured sum for VERIFIED.
5. `MEM-WINDOW.schema.md:86-105` decision table replaced with the ordered eight-row chain.

## Final ordered chain (as in code, spcc_supervisor.py:560-586)
```
allowance = "UNVERIFIED"
allowance_reason = None
if killed_reason is not None:            allowance_reason = "killed-by-supervisor"
elif aborted is not None:                allowance_reason = "aborted"
elif rc is not None and rc < 0:          allowance_reason = "died-by-signal"
elif cgroup_peak_gb is None:             allowance_reason = "peak-unknown"
elif cgroup_peak_gb > CAP_GB:            allowance_reason = "peak-exceeded-cap"
elif unaccounted_gb is None:             allowance_reason = "unaccounted-unknown"
elif unaccounted_gb < 0:                 allowance_reason = "mem-available-rose"
else:
    allowance = "VERIFIED"
    allowance_reason = f"cgroup_peak_gb {cgroup_peak_gb:.2f} + unaccounted_gb {unaccounted_gb:.2f} <= {CAP_GB} GB"
w2["allowance"] = allowance
w2["allowance_reason"] = allowance_reason
```
`died-by-signal` is ordered **before** `peak-exceeded-cap` so a kernel OOM kill is never
reported as the supervisor's own cap enforcement.

## Tests added
- `test_peak_62_with_sigkill_is_unverified_died_by_signal` — peak 62 GiB, `returncode -9`,
  `killed null` → UNVERIFIED / `died-by-signal`.
- `test_peak_62_with_clean_exit_is_unverified_peak_exceeded` — peak 62 GiB, `returncode 0`
  → UNVERIFIED / `peak-exceeded-cap`.
- `test_absent_memory_peak_is_unknown_not_verified` — no peak source, kernel file absent
  → `cgroup_peak_gb null`, UNVERIFIED / `peak-unknown`.
- `test_within_cap_measured_sum_is_verified` — peak 44 GiB, `returncode 0`, unaccounted 3 GiB
  → VERIFIED with reason naming `44.00 + 3.00 <= 60`.
- `make_env` now supplies `tmp_path/peak` explicitly (honest fixture peak) instead of relying
  on the supervisor's former synthetic zero.

## Verification
`.venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q` → 22 passed.
Red→green for the signal branch: absent branch gave `peak-exceeded-cap`; after adding it, the test passes.
