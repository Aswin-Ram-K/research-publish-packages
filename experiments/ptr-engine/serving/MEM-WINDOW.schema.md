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
   absence of a measurement, and nothing downstream may treat them alike.
3. **`DERIVED ≠ MEASURED`.** `cgroup_peak_gb` is read from cgroup v2
   `memory.peak`; `unaccounted_gb` is derived from `MemAvailable` deltas minus
   that peak and is only meaningful when both are measured.
4. Samples are taken every `SAMPLE_INTERVAL` (2 s). The peak is the kernel's
   `memory.peak` maximum, not the largest sampled value.

## Open record (`MEM-WINDOW.json`)

| Field | Type | Meaning |
|---|---|---|
| `job` | string | job name; also prefixes the cgroup `spcc-<job>-<pid>` |
| `declared_peak_gb` | float | the job's declared peak; refused if `> 60` |
| `cap_gb` | number | `60` |
| `reserve_gb` | number | `68` = cap 60 + 8 GB host headroom |
| `opened_at` | ISO-8601 UTC string | open time |
| `owner_pid` | int | pid of the `open-window` process (first owner) |
| `owner_start_time` | int | `/proc/<owner_pid>/stat` field 22 at open time |
| `owners` | array of `{pid, start_time}` | opener and its immediate parent, in that order |
| `mem_available_gb` | float | `MemAvailable` at open time; the baseline for `unaccounted_gb` |

## Window ownership rule

`open-window` is usually a short-lived CLI and is often launched from a
short-lived wrapper (`bash -c '… open-window … && … run …'`). Recording only
`os.getppid()` made a window unusable as soon as the wrapper exited, so the
record carries a small **owner chain**: the `open-window` process itself plus
its immediate parent. Deeper ancestors (test runner, systemd, pid 1) are
deliberately excluded — an unrelated long-lived process must not keep a stale
window alive.

A window is **live** if and only if at least one recorded pair still matches a
running process:

- `/proc/<pid>/stat` must exist, and
- its field 22 (`starttime`, clock ticks since boot) must equal the recorded
  `start_time`.

`starttime` matching defeats pid reuse: a recycled pid with a different start
time does not revive the window. `start_time: null` occurs only in legacy
records and falls back to plain pid liveness (`kill(pid, 0)`).

`run` refuses with exit code 3 when no owner is live; `open-window` refuses
(exit 2) when a live window is already open. A dead window is cleared with
`close-window`, which prints `null` for any accounting field that was never
measured.

## Close record (last line of `MEM-WINDOW.jsonl`)

All open-record fields, plus:

| Field | Type | Meaning |
|---|---|---|
| `cgroup_peak_gb` | float or `null` | `memory.peak` / 2^30; `null` if the closing read failed |
| `unaccounted_gb` | float or `null` | `(opened MemAvailable − closing MemAvailable) − cgroup_peak_gb`; `null` unless both reads succeeded. May be negative when `MemAvailable` rose mid-run — that means the remainder was **not measured**, so it is never treated as a zero |
| `unaccounted_reason` | string, absent when accounted | `"mem-available-rose"` for a negative remainder; `"close-read-failed"` when `cgroup_peak_gb` or the closing `MemAvailable` is `null` |
| `killed` | string or `null` | `"cgroup-peak"` when `memory.peak` exceeded the cap (SIGTERM, then SIGKILL after `--grace`) |
| `aborted` | string or `null` | `"sample-unreadable"` when any sample or closing read failed |
| `aborted_path` | string, when aborted | the path that could not be read |
| `exit_code` / `returncode` / `child_returncode` | int or `null` | the child's status; all three carry the same value |
| `child_signal` / `signal` | int, when the child died by signal | `-returncode` |
| `allowance` | `"VERIFIED"` \| `"UNVERIFIED"` | see the decision table |

## Allowance decision table

| Condition (evaluated in this order) | `allowance` |
|---|---|
| `killed` is not `null` | `UNVERIFIED` (`allowance_reason: "killed-by-supervisor"`) |
| `aborted` is not `null` | `UNVERIFIED` (`allowance_reason: "aborted"`) |
| `returncode < 0` (child died by a signal: kernel OOM kill, external `SIGKILL`) | `UNVERIFIED` (`allowance_reason: "died-by-signal"`) |
| `cgroup_peak_gb` is `null` (kernel exposes no `memory.peak`) | `UNVERIFIED` (`allowance_reason: "peak-unknown"`) |
| `cgroup_peak_gb > 60` | `UNVERIFIED` (`allowance_reason: "peak-exceeded-cap"`) |
| `unaccounted_gb` is `null` | `UNVERIFIED` (`allowance_reason: "unaccounted-unknown"`) |
| `unaccounted_gb < 0` | `UNVERIFIED` (`allowance_reason: "mem-available-rose"`) |
| none of the above | `VERIFIED` (`allowance_reason` names `cgroup_peak_gb + unaccounted_gb <= 60 GB`) |

Only the last row is a claim that the workload stayed inside the 60 GB
allowance; it is the last resort and is reachable only when every earlier row
is false. A signal death is never attributed to the supervisor's own kill path:
if the supervisor did not kill the child, a negative `returncode` means the
kernel or an external signal ended it, and the cap was not enforced by us.
`memory.peak` is never fabricated by the supervisor: when the kernel does not
expose it the peak is `null`, never `0`, and the window cannot be `VERIFIED`.
Admission remains `cgroup_peak_gb + unaccounted_gb ≤ 60` for a workload whose
unaccounted remainder has been measured for its shape.

## Refusal messages

Every refusal names the blocking number and the shortfall, so a refusal is
diagnosable without further inspection:

```
refusing: MemAvailable 14.0 GB < 68.0 GB reserve (short by 54.0 GB)
refusing: declared peak 61.0 GB exceeds cap 60 GB (over by 1.0 GB)
refusing: memory window already open (owner pid 1234 start 8877665544 alive)
refusing to run: window owner pid 1234 start_time 8877665544 no longer alive (pid reuse or owner exited)
```

The admission reserve is `cap + 8 GB = 68 GB` of `MemAvailable` immediately
before launch, so the host keeps working headroom even when the cap is fully
used. On a box whose `MemAvailable` is below 68 GB every window is legitimately
refused; the message states which number blocked it and by how much.
