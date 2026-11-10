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

## Which host is measured

`mem_source` records *where the supervisor read its memory facts*, because the
60 GB allowance is about the host that holds the workload — the 121 GB GB10 /
GX10 unified pool — not necessarily the machine the CLI runs on. Two sources
exist: `"local"` (`LocalMeminfo`, reading `/proc/meminfo` here, `SPCC_MEMINFO_PATH`
overrides the path in tests) and `"ssh:<host>"` (`RemoteMeminfo`, running
`ssh -o BatchMode=yes <host> cat /proc/meminfo`, read-only). A remote read that
fails raises and is refused; it never becomes zero. `--target-host` (or
`SPCC_TARGET_HOST`) selects the source at `open-window`; `run` reuses the source
recorded in the window unless it is given its own `--target-host`.

`enforcement` states what the window can actually prove. `"cgroup"` is claimed
**only** when `mem_source` is `"local"`: the cgroup written by `run`
(`spcc-<job>-<pid>`, `memory.max = 60 GiB`) governs the child this supervisor
spawned, so `memory.peak` is a real measurement of that child. A remote host
can only ever yield **`"declared-only"`**: the supervisor cannot write a cgroup
on another machine, so there is no measured peak and no kernel-enforced cap —
only the declared peak admitted at open time plus the sampled `MemAvailable`.
Do not fake a cgroup for a remote window; the mode is recorded precisely so a
reader can tell the two apart.

`MIN_TOTAL_GB = 100` exists to stop the supervisor silently bounding a laptop.
`open-window` reads `MemTotal` from the chosen source before anything else and
refuses with exit code **4** (distinct from the allowance refusal, exit 2) when
it is below 100 GB, naming both numbers and the 121 GB pool the allowance
governs. On this box `MemTotal` is 29 GB, so a local window is now refused by
construction instead of pretending that a 68 GB reserve on a 29 GB laptop
bounds the accelerator.

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
| `mem_source` | `"local"` \| `"ssh:<host>"` | where `MemTotal`/`MemAvailable` were read; default `"local"` |
| `mem_total_gb` | float | `MemTotal` of that source; refused below `MIN_TOTAL_GB = 100` |
| `enforcement` | `"cgroup"` \| `"declared-only"` | `cgroup` only for a local source; remote is always declared-only |
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
| `cgroup_peak_gb` | float or `null` | `memory.peak` / 2^30; `null` if the closing read failed **or** `enforcement` is `declared-only` (there is no cgroup to measure) |
| `unaccounted_gb` | float or `null` | `(opened MemAvailable − closing MemAvailable) − cgroup_peak_gb`; `null` unless both reads succeeded. May be negative when `MemAvailable` rose mid-run — that means the remainder was **not measured**, so it is never treated as a zero. Always `null` for a declared-only window |
| `unaccounted_reason` | string, absent when accounted | `"mem-available-rose"` for a negative remainder; `"close-read-failed"` when `cgroup_peak_gb` or the closing `MemAvailable` is `null`; `"remote-host-declared-only"` for any declared-only window |
| `mem_source` / `enforcement` | string | carried over from the open record; the close record never upgrades a mode |
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
| `enforcement` is `declared-only` | `UNVERIFIED` (`allowance_reason: "remote-host-declared-only"`) — the peak was declared, not measured, and the cgroup that would prove it is on another host |
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
refusing: mem_source local reports MemTotal 29.0 GB < 100 GB minimum; the allowance governs a 121 GB pool and this supervisor would bound the wrong machine
refusing: mem_source ssh:gx10 MemTotal unreadable: ssh: connect to host gx10 port 22: Connection timed out
refusing to run: window owner pid 1234 start_time 8877665544 no longer alive (pid reuse or owner exited)
```

Exit codes are distinct so callers can tell the refusals apart: **2** for an
allowance refusal (declared peak, reserve, or an already-open window), **3**
for a `run` precondition, and **4** for a wrong/unreadable memory host. Exit 4
means the supervisor could not establish that the chosen host is the 121 GB
pool the allowance is about, so it refuses before any child is spawned rather
than enforcing a cap on the wrong machine.

The admission reserve is `cap + 8 GB = 68 GB` of `MemAvailable` immediately
before launch, so the host keeps working headroom even when the cap is fully
used. On a box whose `MemAvailable` is below 68 GB every window is legitimately
refused; the message states which number blocked it and by how much. The
reserve applies to the chosen `mem_source`, not necessarily this machine: on the
29 GB box that runs the CLI the `MIN_TOTAL_GB` gate refuses first (exit 4),
which is correct — a 68 GB reserve there would bound the laptop, not the 121 GB
pool the allowance describes.
