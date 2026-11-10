# V-SPCC-5C — independent verification of U-SPCC-5C (allowance decision, null-not-zero, owner liveness)

Verdict: **the claimed fixes are real, and I reproduce them, with one exception.** The decision table
matches the claim line for line, both closing-read failures produce JSON `null` (never `0.0`), the
`(pid, start_time)` owner chain accepts a wrapper-owned window and refuses both an exited owner and a
pid-reuse record, and every refusal names its numbers. **One defect remains:** the decision never tests
the measured peak against the cap and never tests the child's exit signal, so a kernel OOM kill that the
0.5 s poll misses records `allowance: "VERIFIED"` at a measured `cgroup_peak_gb: 62.0` (> 60 GiB) with
`child_signal: 9`. Reproduced 3/3.

Target: `/home/zer0null/research extractor/experiments/ptr-engine/serving/spcc_supervisor.py` (644 lines).
All driving used throwaway `SPCC_BASE_DIR` / `SPCC_CGROUP_ROOT` / `SPCC_MEMINFO_PATH` / `SPCC_PEAK_FILE`
under `/tmp/spccv/work/`; the real `serving/` directory was never written.

## 1. Suite

```
$ .venv/bin/python -m pytest experiments/ptr-engine/serving/tests/test_spcc_supervisor.py -q
..................                                                       [100%]
18 passed in 8.62s
```

## 2. The decision table, read out of `spcc_supervisor.py:540-548`

```python
if killed_reason is not None or aborted is not None:   # :543
    w2["allowance"] = "UNVERIFIED"
elif unaccounted_gb is None or unaccounted_gb < 0:     # :545
    w2["allowance"] = "UNVERIFIED"
else:                                                  # :547
    w2["allowance"] = "VERIFIED"
```

`killed` ∈ {`null`, `"cgroup-peak"`}; `aborted` ∈ {`null`, `"sample-unreadable"`};
`unaccounted_gb` ∈ {`null`, `<0`, `≥0`}. Rows are in code order; "driven" marks my own CLI runs.

| # | killed | aborted | unaccounted_gb | allowance | reached by | driven |
|---|--------|---------|----------------|-----------|------------|--------|
| 1 | `cgroup-peak` | `null` | `null` | UNVERIFIED | kill + peak read fails at close | – |
| 2 | `cgroup-peak` | `null` | `<0` | UNVERIFIED | kill + MemAvailable rose | – |
| 3 | `cgroup-peak` | `null` | `≥0` | UNVERIFIED | kill, both closing reads fine | **B**: peak 64, unacc `4.0` → UNVERIFIED |
| 4 | `cgroup-peak` | `sample-unreadable` | any | UNVERIFIED | kill + sample failure | – (row 3 shows `killed` alone suffices) |
| 5 | `null` | `sample-unreadable` | `null` | UNVERIFIED | both closing reads fail | **C**: `null`/`null` → UNVERIFIED |
| 6 | `null` | `sample-unreadable` | `<0` | UNVERIFIED | abort + rose | – |
| 7 | `null` | `sample-unreadable` | `≥0` | UNVERIFIED | sampling fails mid-run, closing reads fine | **G**: peak 4, unacc `2.0` → UNVERIFIED |
| 8 | `null` | `null` | `null` | UNVERIFIED | close-read-failed with no abort — unreachable from `run` (a failed close read sets `aborted` at `:498`/`:505`/`:513`); reachable only from a hand-written record | – |
| 9 | `null` | `null` | `<0` | UNVERIFIED (`unaccounted_reason: mem-available-rose`) | normal exit, MemAvailable rose | **D**: unacc `-14.0` → UNVERIFIED |
| 10 | `null` | `null` | `≥0` | **VERIFIED** | normal completion, both reads fine | **A**: peak 4, unacc `2.0` → VERIFIED |
| 11 | `null` | `null` | `≥0`, but `cgroup_peak_gb > CAP_GB` and `returncode < 0` | **VERIFIED (DEFECT)** | kernel OOM kill faster than the 0.5 s poll at `:454-465`, remainder still ≥0 | **E**: peak **62.0**, unacc `4.0`, `child_signal: 9` → VERIFIED |

Rows 1–10 are consistent with the invariant "a window that did not complete normally is never counted
inside the cap". Row 11 is not: the record itself carries a measured peak above the cap and a signal
death, and still claims VERIFIED, because `killed` is only ever set by the supervisor's own poll
(`:456-458`) and neither `cgroup_peak_gb > CAP_GB` nor `returncode < 0` participates in the decision.
Measured records below.

**A — normal, measured, non-negative remainder → VERIFIED**

```
{"job": "A", "declared_peak_gb": 20.0, "cap_gb": 60, "reserve_gb": 68, ..., "mem_available_gb": 70.0,
 "cgroup_peak_gb": 4.0, "unaccounted_gb": 2.0, "killed": null, "aborted": null,
 "exit_code": 0, "returncode": 0, "child_returncode": 0, "allowance": "VERIFIED"}
```

**B — cap kill, remainder positive → killed wins, UNVERIFIED**

```
$ run --grace 0.2 -- sh -c "printf 'MemAvailable: ... kB' > meminfo; sleep 20"
killed: cgroup-peak
run rc=1
{"job": "B", ..., "cgroup_peak_gb": 64.0, "unaccounted_gb": 4.0, "killed": "cgroup-peak", "aborted": null,
 "exit_code": -15, "child_signal": 15, "allowance": "UNVERIFIED"}
```

**G — abort with a positive remainder → UNVERIFIED**

```
aborted: sample-unreadable /tmp/spccv/work/G/cg/spcc-G-3994503/memory.current
run rc=1
{"job": "G", ..., "cgroup_peak_gb": 4.0, "unaccounted_gb": 2.0, "killed": null,
 "aborted": "sample-unreadable", "aborted_path": "/tmp/spccv/work/G/cg/spcc-G-3994503/memory.current",
 "exit_code": 0, "returncode": 0, "child_returncode": 0, "allowance": "UNVERIFIED"}
```

No `unaccounted_reason` on this row, as designed: the remainder *was* measured (2.0); only the sampling
thread failed, and `aborted` alone forces UNVERIFIED.

**D — MemAvailable rose → negative kept for diagnosis, UNVERIFIED**

```
{"job": "D", ..., "cgroup_peak_gb": 4.0, "unaccounted_gb": -14.0, "killed": null, "aborted": null,
 "unaccounted_reason": "mem-available-rose", "exit_code": 0, "allowance": "UNVERIFIED"}
```

**E — the defect, driven three times, identical every time**

```
$ SPCC_PEAK_FILE=.../peak (62 GiB)  run --grace 0.2 -- sh -c "printf 'MemAvailable: 4194304 kB\n' > meminfo; kill -9 \$\$"
E1 rc=247   {'cgroup_peak_gb': 62.0, 'unaccounted_gb': 4.0, 'killed': None, 'aborted': None, 'returncode': -9, 'allowance': 'VERIFIED'}
E2 rc=247   {'cgroup_peak_gb': 62.0, 'unaccounted_gb': 4.0, 'killed': None, 'aborted': None, 'returncode': -9, 'allowance': 'VERIFIED'}
first run   {"job": "E", ..., "cgroup_peak_gb": 62.0, "unaccounted_gb": 4.0, "killed": null, "aborted": null,
             "exit_code": -9, "child_returncode": -9, "child_signal": 9, "signal": 9, "allowance": "VERIFIED"}
```

The window whose peak is 62 GiB — above the 60 GiB cap the kernel was supposed to enforce — is the one
record the operator would read as inside the cap. A kernel OOM kill is exactly the case the plan calls
"enforced by the kernel rather than by sampling"; here the kernel did its job and the record denies it.

## 3. No zeros for unmeasured

Both closing reads forced to fail (child deletes the peak file *and* the meminfo file before exiting):

```
aborted: sample-unreadable /tmp/spccv/work/C/peak
run rc=1
{"job": "C", ..., "mem_available_gb": 70.0, "cgroup_peak_gb": null, "unaccounted_gb": null,
 "killed": null, "aborted": "sample-unreadable", "aborted_path": "/tmp/spccv/work/C/peak",
 "unaccounted_reason": "close-read-failed", "exit_code": 0, "returncode": 0,
 "child_returncode": 0, "allowance": "UNVERIFIED"}
```

Both fields are JSON `null`, not `0`/`0.0`. `peak_bytes` and `close_ma` are initialised to `None`
(`:496`, `:503`) before their reads, so a raise cannot leave a stale zero behind.

Secondary (code-read, not driven): `_setup_cgroup` at `:328-331` writes `"0\n"` into `memory.peak` /
`memory.current` when the kernel does not provide them, which would manufacture a measured-looking peak
of 0 on a cgroup without the memory controller — the same `ABSENT ≠ 0` rule, one layer down. On this
host the write fails and `run` refuses, so it is a latent hazard, not an observed one.

## 4. Owner liveness

**(a) window opened from a wrapper shell, `run` from a different process → accepted**

```
opened memory window job=OWN-WRAP declared_peak=20.0GB mem_available=70.00GB
a rc=0
```

`owners` in that record is `[{"pid": 3973557, "start_time": 142022878}, {"pid": 3973548, "start_time": 142022877}]`
— the CLI invocation and its parent wrapper, exactly as claimed (`:107-127`).

**(b) owner exited, window still open → refused, naming pid and start time**

```
opened memory window job=OWN-DEAD declared_peak=20.0GB mem_available=70.00GB
{"job":"OWN-DEAD", ..., "owner_pid":3987838, "owner_start_time":142025303,
 "owners":[{"pid":3987838,"start_time":142025303},{"pid":3987835,"start_time":142025303}], "mem_available_gb":70.0}
refusing to run: window owner pid 3987838 start_time 142025303 no longer alive (pid reuse or owner exited)
b' rc=3
```

(An earlier attempt returned `refusing to run: no memory window open` because the successful `run` in
(a) had already consumed the window — correct lifecycle, not the case under test.)

**(c) pid alive but `owner_start_time` mismatch → refused**

```
live pid=3986305 real_start=142024920 recorded_start=1
refusing to run: window owner pid 3986305 start_time 1 no longer alive (pid reuse or owner exited)
c rc=3
```

`window_owner_alive` (`:129-152`) compares `/proc/<pid>/stat` field 22 parsed from the last `)`
(`:84-105`) — the comm field's spaces are handled, and nothing falls back to bare liveness when a start
time is present.

## 5. Refusal messages name the numbers and the shortfall

```
refusing: declared peak 61.0 GB exceeds cap 60 GB (over by 1.0 GB)                      rc=2
refusing: MemAvailable 60.0 GB < 68.0 GB reserve (short by 8.0 GB)                     rc=2
refusing to run: cgroup root not writable: [Errno 13] Permission denied: '/tmp/spccv/work/REF/ro/spcc-test-write'   rc=3
```

## 6. The cap is untouched

```
$ grep -n "64424509440\|memory.max\|cgroup.procs" experiments/ptr-engine/serving/spcc_supervisor.py
35:CAP_BYTES = 64424509440  # 60 GiB
307:        (test_cg / "memory.max").write_text(str(CAP_BYTES))
308:        (test_cg / "memory.max").unlink(missing_ok=True)
312:            (test_cg / "memory.max").unlink(missing_ok=True)
321:        (cg_path / "memory.max").write_text(str(CAP_BYTES))
385:            (cg_path / "memory.max").read_text()
405:            (cg_path / "cgroup.procs").write_text(str(proc.pid) + "\n")
```

Single constant, written to `memory.max` at `:321`, read back at `:385`, `cgroup.procs` assigned at
`:405`. No second cap value anywhere.

## 7. Hygiene and the schema document

```
$ ls -a experiments/ptr-engine/serving/
.  ..  MEM-WINDOW.schema.md  REMOTE-ROOT.md  __pycache__  launch-sglang-spcc.sh  spcc_supervisor.py  tests
```

No `MEM-WINDOW.json`, no `MEM-WINDOW.jsonl`, no scratch files. `MEM-WINDOW.schema.md` is 113 lines of
schema, not a pasted program:

```
# MEM-WINDOW — memory-window record schema

Written and read by `experiments/ptr-engine/serving/spcc_supervisor.py`. Two
files live in the base dir (`--base-dir` / `SPCC_BASE_DIR`, default: this
directory):

| File | Lifecycle | Contents |
|---|---|---|
| `MEM-WINDOW.json` | exists only while a window is open; deleted by `run` in its `finally`, or by `close-window` | the open record (below) |
| `MEM-WINDOW.jsonl` | append-only; truncated at `open-window` | one 2 s sample per line while running, then the close record as the last line |

## Invariants

1. **A window that did not complete normally is never counted inside the cap.**
   `allowance: "VERIFIED"` requires a run that ended on its own with every
   closing read succeeding and a non-negative remainder. A kill (cap exceeded),
   an abort (`sample-unreadable`), or a negative remainder is always
   `"UNVERIFIED"`, whatever else the record says.
2. **`ABSENT ≠ 0`.** A read that failed is recorded as JSON `null`, never as
   `0.0`. A zero in `cgroup_peak_gb` is a measurement of zero; `null` is the
```

Its decision table at lines 88–92 enumerates exactly rows 1–10 of mine and, like the code, has no row
for "peak above cap / signal death with a non-negative remainder" — the schema and the code are
consistent with each other and both miss row 11. The schema also mis-states the base-dir flag: the CLI
exposes `SPCC_BASE_DIR` only (no `--base-dir` argument in `main()` at `:615-641`).

## 8. No regression in the neighbouring pieces

```
$ .venv/bin/python -m pytest experiments/ptr-engine/serving/tests/ -q
18 passed in 8.54s
```

`launch-sglang-spcc.sh:12-15` is still correct for the default layout:

```bash
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$HERE/MEM-WINDOW.json" ]]; then
  echo "refusing to start: MEM-WINDOW.json present in $HERE (memory window open)" >&2
  exit 1
```

It checks the same directory the supervisor writes to by default (`_base_dir()` = `__file__`'s parent,
`:39-41`), so a window opened in place blocks the launch. Caveat, unchanged by this unit: a window
opened with `SPCC_BASE_DIR` pointing elsewhere is invisible to the launcher, so the guard is only as
strong as the convention that windows are opened in `serving/`.

## Defect

**`spcc_supervisor.py:543-548` — a cap-exceeding window can still be recorded `VERIFIED`.** The decision
consults `killed` and `aborted` only, and `killed` is set solely by the supervisor's own 0.5 s poll
(`:454-465`); when the kernel OOM-kills the child between polls (or any other signal ends it), the
record shows `child_signal: 9` with `killed: null`, and with a non-negative remainder it is stamped
`VERIFIED` at a measured `cgroup_peak_gb: 62.0` — above the 60 GiB cap. Fix: add
`elif cgroup_peak_gb is None or cgroup_peak_gb > CAP_GB: "UNVERIFIED"` and
`elif rc is not None and rc < 0: "UNVERIFIED"` before the VERIFIED branch, and add the corresponding
rows to `MEM-WINDOW.schema.md:88-92`.
