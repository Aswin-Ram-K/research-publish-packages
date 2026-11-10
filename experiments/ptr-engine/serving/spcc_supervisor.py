#!/usr/bin/env python3
"""SPCC memory-window supervisor.

Enforces the 60 GB (of 121 GB unified) allowance as a measured, kernel-backed
limit rather than a sampled guess. See experiments/ptr-engine/serving/MEM-WINDOW.schema.md.

Invariant: a window that did not complete normally is never counted inside the
cap. ``allowance`` is ``VERIFIED`` only when the run ended on its own, every
closing read succeeded, and the measured unaccounted remainder is not negative.
A killed, aborted or unreadable window is ``UNVERIFIED`` by construction, and a
failed read is recorded as JSON ``null`` — never as a fabricated ``0.0``
(``ABSENT != 0``).

Window ownership: ``open-window`` records ``owner_pid`` / ``owner_start_time``
(``/proc/<pid>/stat`` field 22) for itself and its immediate parent, so a window
opened from a short-lived wrapper shell stays usable by a later ``run``. A
window is live only while one of those recorded (pid, start-time) pairs still
matches a running process, which defeats pid reuse.

Grace period for SIGTERM->SIGKILL escalation defaults to 10 seconds; pass 0.2 in
tests (see --grace).
"""
import argparse
import json
import os
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

CAP_GB = 60
RESERVE_GB = 8
CAP_BYTES = 64424509440  # 60 GiB
SAMPLE_INTERVAL = 2.0

# The allowance bounds a 121 GB unified pool (GB10 / GX10). A host whose
# MemTotal is smaller cannot hold the workload the cap is about, so refusing is
# the only honest answer: enforcing 68 GB of headroom there would bound the
# wrong machine.
MIN_TOTAL_GB = 100

# Distinct exit codes: callers must be able to tell "allowance refused" from
# "this supervisor is pointed at the wrong host".
EXIT_ALLOWANCE = 2
EXIT_RUN_REFUSED = 3
EXIT_WRONG_HOST = 4


def _base_dir():
    return Path(os.environ.get("SPCC_BASE_DIR", str(Path(__file__).resolve().parent)))


def _cgroup_root():
    return Path(os.environ.get("SPCC_CGROUP_ROOT", "/sys/fs/cgroup"))


def _meminfo_path():
    return Path(os.environ.get("SPCC_MEMINFO_PATH", "/proc/meminfo"))


def parse_meminfo(text):
    """Parse ``/proc/meminfo`` text into ``{field: kB}``."""
    fields = {}
    for line in text.splitlines():
        key, sep, rest = line.partition(":")
        if not sep:
            continue
        parts = rest.split()
        if not parts:
            continue
        try:
            fields[key.strip()] = int(parts[0])
        except ValueError:
            continue
    return fields


class MemSource:
    """The memory facts of the host the *workload* runs on.

    The supervisor must read this host's ``MemTotal`` / ``MemAvailable``, not
    the machine the CLI happens to execute on. A source that cannot be read
    raises; it never reports zeros.
    """

    label = "local"

    def meminfo(self):
        raise NotImplementedError

    def mem_total_gb(self):
        mem = self.meminfo()
        if "MemTotal" not in mem:
            raise RuntimeError("MemTotal not found in meminfo")
        return mem["MemTotal"] / (1024 * 1024)

    def mem_available_gb(self):
        mem = self.meminfo()
        if "MemAvailable" not in mem:
            raise RuntimeError("MemAvailable not found in meminfo")
        return mem["MemAvailable"] / (1024 * 1024)


class LocalMeminfo(MemSource):
    """``/proc/meminfo`` on the machine the supervisor runs on.

    Only this source can be cgroup-enforced: the cgroup the supervisor writes
    is the one that governs the child it spawns here.
    """

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else _meminfo_path()

    @property
    def label(self):
        return "local"

    def meminfo(self):
        return parse_meminfo(self.path.read_text())


class RemoteMeminfo(MemSource):
    """``/proc/meminfo`` of another host, read over read-only ``ssh cat``.

    Every failure (non-zero exit, empty or unparseable output, timeout) raises.
    A remote host whose memory cannot be read must never be recorded as zero,
    and this supervisor can never write that host's cgroup.
    """

    def __init__(self, host, runner=None, timeout=15):
        self.host = host
        self.runner = runner
        self.timeout = float(timeout)

    @property
    def label(self):
        return f"ssh:{self.host}"

    def _run(self):
        if self.runner is not None:
            return self.runner(self.host)
        proc = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={int(self.timeout)}",
             self.host, "cat /proc/meminfo"],
            capture_output=True, text=True, timeout=self.timeout,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"ssh {self.host} exited {proc.returncode}: {detail}")
        return proc.stdout

    def meminfo(self):
        text = self._run()
        if not text or not text.strip():
            raise RuntimeError(f"ssh {self.host} returned no meminfo")
        fields = parse_meminfo(text)
        if "MemTotal" not in fields or "MemAvailable" not in fields:
            raise RuntimeError(f"ssh {self.host} returned unparseable meminfo")
        return fields


def make_mem_source(target_host=None, meminfo_path=None, remote_runner=None):
    """Build the memory source for ``--target-host`` (default: local)."""
    host = target_host
    if host is None:
        host = os.environ.get("SPCC_TARGET_HOST") or "local"
    host = str(host).strip()
    if host in ("", "local", "localhost", "127.0.0.1", "::1"):
        return LocalMeminfo(meminfo_path)
    return RemoteMeminfo(host, runner=remote_runner)


def mem_available_gb(path=None):
    p = Path(path) if path is not None else _meminfo_path()
    with p.open() as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                kb = int(line.split()[1])
                return kb / (1024 * 1024)
    raise RuntimeError("MemAvailable not found in meminfo")


def window_path():
    return _base_dir() / "MEM-WINDOW.json"


def samples_path():
    return _base_dir() / "MEM-WINDOW.jsonl"


def read_window():
    p = window_path()
    if not p.exists():
        return None
    return json.loads(p.read_text())


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def proc_start_time(pid):
    """Return ``/proc/<pid>/stat`` field 22 (starttime, clock ticks since boot).

    ``None`` means the process does not exist or the value is unreadable. The
    comm field is parenthesised and may contain spaces, so parse from the last
    ``)``; field 3 (state) is the first token after it, making field 22 index 19.
    """
    try:
        data = Path(f"/proc/{int(pid)}/stat").read_text(errors="replace")
    except (OSError, ValueError, TypeError):
        return None
    rparen = data.rfind(")")
    if rparen < 0:
        return None
    fields = data[rparen + 1:].split()
    if len(fields) < 20:
        return None
    try:
        return int(fields[19])
    except ValueError:
        return None


def owner_chain(max_depth=1):
    """Record the window opener and its parent, with /proc start times.

    The opener's own process is often a short-lived CLI invocation; its parent
    is the wrapper shell that goes on to call ``run``. Deeper ancestors (the
    test runner, systemd, pid 1) are deliberately excluded so an unrelated
    long-lived process cannot keep a stale window alive.
    """
    chain = []
    pid = os.getpid()
    for _ in range(max_depth + 1):
        if pid is None or int(pid) <= 1:
            break
        chain.append({"pid": int(pid), "start_time": proc_start_time(pid)})
        try:
            pid = int(Path(f"/proc/{int(pid)}/stat").read_text(errors="replace")
                      .rpartition(")")[2].split()[1])  # field 4 = ppid
        except (OSError, ValueError, IndexError, TypeError):
            break
    return chain


def window_owner_alive(window):
    """True iff a process with a recorded (pid, start_time) pair still exists."""
    if window is None:
        return False
    owners = window.get("owners")
    if not owners:
        owners = [{"pid": window.get("owner_pid", window.get("pid")),
                   "start_time": window.get("owner_start_time")}]
    for owner in owners:
        pid = owner.get("pid")
        if pid is None:
            continue
        current = proc_start_time(pid)
        if current is None:
            continue
        recorded = owner.get("start_time")
        if recorded is None:
            # Legacy record without a start time: fall back to plain liveness.
            if pid_alive(pid):
                return True
            continue
        if current == recorded:
            return True
    return False


def _peak_path(cg_path, peak_source=None):
    if peak_source is not None and not callable(peak_source):
        return Path(peak_source)
    env_src = (os.environ.get("SPCC_PEAK_FILE")
               or os.environ.get("SPCC_PEAK_SOURCE")
               or os.environ.get("SPCC_PEAK_PATH")
               or os.environ.get("SPCC_PEAK_OVERRIDE"))
    if env_src:
        return Path(env_src)
    return Path(cg_path) / "memory.peak"


def _read_peak(cg_path, peak_source=None):
    """Measured peak in bytes, or ``None`` when the kernel has no peak counter.

    An absent ``memory.peak`` with no source explicitly configured means the
    kernel does not expose a peak at all, so the peak is UNKNOWN — never a
    synthetic 0. An explicitly configured source that cannot be read, or a
    source that disappears mid-run, is still an error and must propagate so
    the caller aborts instead of believing a missing number.
    """
    if callable(peak_source):
        return int(peak_source())
    explicit = bool(
        (peak_source is not None and not callable(peak_source))
        or os.environ.get("SPCC_PEAK_FILE")
        or os.environ.get("SPCC_PEAK_SOURCE")
        or os.environ.get("SPCC_PEAK_PATH")
        or os.environ.get("SPCC_PEAK_OVERRIDE")
    )
    p = _peak_path(cg_path, peak_source)
    if not explicit and not p.exists():
        return None
    return int(p.read_text().strip())


def _signal_child(proc, sig):
    """Signal the child's whole process group (child is started in a new session)."""
    try:
        os.killpg(os.getpgid(proc.pid), sig)
        return
    except Exception:
        pass
    try:
        if sig == signal.SIGTERM:
            proc.terminate()
        else:
            proc.kill()
    except Exception:
        pass


def cmd_open_window(args, mem_source=None, base_dir=None, remote_runner=None):
    declared = float(args.declared_peak_gb)
    if declared > CAP_GB:
        print(f"refusing: declared peak {declared:.1f} GB exceeds cap {CAP_GB} GB "
              f"(over by {declared - CAP_GB:.1f} GB)", flush=True)
        return EXIT_ALLOWANCE
    src = mem_source if mem_source is not None else make_mem_source(
        getattr(args, "target_host", None), remote_runner=remote_runner)
    # The cap is about a 121 GB pool. Reading MemTotal from the *chosen* host
    # before anything else stops the supervisor silently bounding a laptop.
    try:
        total = src.mem_total_gb()
    except Exception as e:
        print(f"refusing: mem_source {src.label} MemTotal unreadable: {e}", flush=True)
        return EXIT_WRONG_HOST
    if total < MIN_TOTAL_GB:
        print(f"refusing: mem_source {src.label} reports MemTotal {total:.1f} GB "
              f"< {MIN_TOTAL_GB} GB minimum; the allowance governs a 121 GB pool "
              f"and this supervisor would bound the wrong machine", flush=True)
        return EXIT_WRONG_HOST
    reserve = CAP_GB + RESERVE_GB
    try:
        ma = src.mem_available_gb()
    except Exception as e:
        print(f"refusing: mem_source {src.label} MemAvailable unreadable: {e}", flush=True)
        return EXIT_WRONG_HOST
    if ma < reserve:
        print(f"refusing: MemAvailable {ma:.1f} GB < {reserve:.1f} GB reserve "
              f"(short by {reserve - ma:.1f} GB)", flush=True)
        return EXIT_ALLOWANCE
    base = Path(base_dir) if base_dir is not None else _base_dir()
    wp = base / "MEM-WINDOW.json"
    w = json.loads(wp.read_text()) if wp.exists() else None
    if window_owner_alive(w):
        owner = (w.get("owners") or [{}])[0]
        print(f"refusing: memory window already open "
              f"(owner pid {owner.get('pid')} start {owner.get('start_time')} alive)", flush=True)
        return EXIT_ALLOWANCE
    owners = owner_chain()
    record = {
        "job": args.job,
        "declared_peak_gb": declared,
        "cap_gb": CAP_GB,
        "reserve_gb": reserve,
        "opened_at": datetime.now(timezone.utc).isoformat(),
        "owner_pid": owners[0]["pid"],
        "owner_start_time": owners[0]["start_time"],
        "owners": owners,
        "mem_source": src.label,
        "mem_total_gb": total,
        "enforcement": "cgroup" if src.label == "local" else "declared-only",
        "mem_available_gb": ma,
    }
    wp.write_text(json.dumps(record, indent=2) + "\n")
    sp = base / "MEM-WINDOW.jsonl"
    if sp.exists():
        sp.unlink()
    print(f"opened memory window job={args.job} declared_peak={declared}GB "
          f"mem_source={src.label} mem_total={total:.1f}GB mem_available={ma:.2f}GB")
    return 0


class Sampler(threading.Thread):
    def __init__(self, stop_event, cg_path, out_path, meminfo, peak_source=None,
                 interval=None, source=None):
        super().__init__(daemon=True)
        self.stop_event = stop_event
        # cg_path is None for declared-only (remote) windows: there is no local
        # cgroup and no kernel peak to sample, only the host's MemAvailable.
        self.cg_path = Path(cg_path) if cg_path is not None else None
        self.out_path = Path(out_path)
        self.meminfo = Path(meminfo) if meminfo is not None and not isinstance(meminfo, Path) else meminfo
        self.source = source
        self.peak_source = peak_source
        self.interval = SAMPLE_INTERVAL if interval is None else float(interval)
        self.error = None
        self.error_path = None
        self.samples_written = 0

    def _mem_available(self):
        if self.source is not None:
            return self.source.mem_available_gb()
        return mem_available_gb(self.meminfo)

    def _one_sample(self):
        rec = {"ts": time.time()}
        if self.cg_path is not None:
            try:
                peak = _read_peak(self.cg_path, self.peak_source)
            except Exception as e:
                self.error = e
                self.error_path = str(_peak_path(self.cg_path, self.peak_source))
                self.stop_event.set()
                return False
            try:
                cur = int((self.cg_path / "memory.current").read_text().strip())
            except Exception as e:
                self.error = e
                self.error_path = str(self.cg_path / "memory.current")
                self.stop_event.set()
                return False
            rec["memory_peak_bytes"] = peak
            rec["memory_current_bytes"] = cur
        try:
            ma = self._mem_available()
        except Exception as e:
            self.error = e
            self.error_path = str(self.source.label if self.source is not None else self.meminfo)
            self.stop_event.set()
            return False
        rec["mem_available_gb"] = ma
        try:
            with self.out_path.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception as e:
            self.error = e
            self.error_path = str(self.out_path)
            self.stop_event.set()
            return False
        self.samples_written += 1
        return True

    def run(self):
        # Always take an opening sample, then poll, then a closing sample so a
        # run of any duration produces at least two samples. Any failure is
        # surfaced to the supervisor, never coerced into a fabricated zero.
        try:
            if not self._one_sample():
                return
            while not self.stop_event.is_set():
                self.stop_event.wait(self.interval)
                if self.stop_event.is_set():
                    break
                if not self._one_sample():
                    return
            self._one_sample()
        except Exception as e:  # defensive: never die silently
            self.error = e
            if self.error_path is None:
                self.error_path = "sampling-thread"
            self.stop_event.set()


def _setup_cgroup(job, cgroup_root=None):
    root = Path(cgroup_root) if cgroup_root is not None else _cgroup_root()
    sc = root / "subtree_control"
    try:
        if sc.exists():
            sc.write_text("+memory\n")
    except Exception:
        pass
    test_cg = root / "spcc-test-write"
    try:
        test_cg.mkdir(exist_ok=True)
        (test_cg / "memory.max").write_text(str(CAP_BYTES))
        (test_cg / "memory.max").unlink(missing_ok=True)
        test_cg.rmdir()
    except Exception as e:
        try:
            (test_cg / "memory.max").unlink(missing_ok=True)
            test_cg.rmdir()
        except Exception:
            pass
        return None, f"cgroup root not writable: {e}"
    cg_name = f"spcc-{job}-{os.getpid()}"
    cg_path = root / cg_name
    try:
        cg_path.mkdir(exist_ok=True)
        (cg_path / "memory.max").write_text(str(CAP_BYTES))
        swap = cg_path / "memory.swap.max"
        if swap.exists():
            try:
                swap.write_text("0")
            except Exception:
                pass
        # Never fabricate memory.peak: it is kernel-provided. If the kernel
        # does not expose it, the field stays absent and every read treats it
        # as unknown (null), so the window can never be VERIFIED.
        cur = cg_path / "memory.current"
        if not cur.exists():
            cur.write_text("0\n")
    except Exception as e:
        return None, f"failed to configure cgroup: {e}"
    return cg_path, None


class SpccSupervisor:
    """In-process supervisor with injectable cgroup root and peak source."""

    def __init__(self, cgroup_root=None, peak_source=None, meminfo_path=None, base_dir=None,
                 grace_seconds=10.0, sample_interval=None, mem_source=None, remote_runner=None):
        self.cgroup_root = Path(cgroup_root) if cgroup_root is not None else _cgroup_root()
        self.peak_source = peak_source
        self.meminfo_path = Path(meminfo_path) if meminfo_path is not None else _meminfo_path()
        self.base_dir = Path(base_dir) if base_dir is not None else _base_dir()
        self.grace_seconds = float(grace_seconds)
        self.sample_interval = SAMPLE_INTERVAL if sample_interval is None else float(sample_interval)
        # An injected source wins; otherwise the open window's mem_source is
        # reconstructed (legacy windows without one are local).
        self.mem_source = mem_source
        self.remote_runner = remote_runner

    def _source_for_window(self, w):
        label = str(w.get("mem_source") or "local")
        if label.startswith("ssh:"):
            return RemoteMeminfo(label[4:], runner=self.remote_runner)
        return LocalMeminfo(self.meminfo_path)

    def _window_path(self):
        return self.base_dir / "MEM-WINDOW.json"

    def _samples_path(self):
        return self.base_dir / "MEM-WINDOW.jsonl"

    def _read_window(self):
        p = self._window_path()
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def run(self, cmd, grace_seconds=None):
        """Run ``cmd`` under the window.

        ``grace_seconds`` is the SIGTERM->SIGKILL escalation delay; it defaults
        to 10 seconds and tests pass 0.2.
        """
        grace = self.grace_seconds if grace_seconds is None else float(grace_seconds)
        w = self._read_window()
        if w is None:
            print("refusing to run: no memory window open", flush=True)
            return 3
        if not window_owner_alive(w):
            owner = (w.get("owners") or [{}])[0]
            print(f"refusing to run: window owner pid {owner.get('pid')} "
                  f"start_time {owner.get('start_time')} no longer alive "
                  f"(pid reuse or owner exited)", flush=True)
            return 3
        if not cmd:
            print("refusing to run: empty command", flush=True)
            return 3
        src = self.mem_source if self.mem_source is not None else self._source_for_window(w)
        # A cgroup written here governs the child spawned here — it can only be
        # claimed when the memory facts come from this same machine. A remote
        # host's memory cannot be bounded by a local cgroup.
        # The mode follows the source actually read on this run: only a local
        # source can be cgroup-enforced, whatever an earlier window recorded.
        enforcement = "cgroup" if src.label == "local" else "declared-only"
        cg_path = None
        if enforcement == "cgroup":
            cg_path, err = _setup_cgroup(w["job"], cgroup_root=self.cgroup_root)
            if err is not None:
                print(f"refusing to run: {err}", flush=True)
                return 3
            try:
                (cg_path / "memory.max").read_text()
            except Exception as e:
                print(f"refusing to run: cgroup not writable: {e}", flush=True)
                try:
                    cg_path.rmdir()
                except Exception:
                    pass
                return 3
        else:
            print(f"declared-only: mem_source {src.label}; no cgroup can govern "
                  f"the remote host (peak is declared, not measured)", flush=True)
        try:
            opened_ma = float(w["mem_available_gb"]) if "mem_available_gb" in w else src.mem_available_gb()
        except Exception as e:
            print(f"refusing to run: memavailable unreadable for {src.label}: {e}", flush=True)
            if cg_path is not None:
                try:
                    cg_path.rmdir()
                except Exception:
                    pass
            return 3

        proc = subprocess.Popen(cmd, start_new_session=True)
        if cg_path is not None:
            try:
                (cg_path / "cgroup.procs").write_text(str(proc.pid) + "\n")
            except Exception as e:
                _signal_child(proc, signal.SIGKILL)
                print(f"refusing to run: cannot assign process to cgroup: {e}", flush=True)
                try:
                    cg_path.rmdir()
                except Exception:
                    pass
                return 3

        stop_event = threading.Event()
        sampler = Sampler(stop_event, cg_path, self._samples_path(), self.meminfo_path,
                          peak_source=self.peak_source, interval=self.sample_interval,
                          source=src)
        sampler.start()
        # Give the child a moment to install its own signal handlers before the
        # first cap evaluation can signal it (bounded by the kill grace).
        if grace > 0:
            time.sleep(min(0.2, grace))

        killed_reason = None
        aborted = None
        aborted_path = None
        stop_requested = {"v": False}

        def _handler(signum, frame):
            stop_requested["v"] = True
            try:
                if proc.poll() is None:
                    _signal_child(proc, signal.SIGTERM)
            except Exception:
                pass

        prev_int = None
        prev_term = None
        try:
            prev_int = signal.signal(signal.SIGINT, _handler)
            prev_term = signal.signal(signal.SIGTERM, _handler)
        except Exception:
            pass

        try:
            while proc.poll() is None and not stop_requested["v"]:
                if not sampler.is_alive() and getattr(sampler, "error", None) is not None:
                    aborted = "sample-unreadable"
                    aborted_path = sampler.error_path
                    break
                if cg_path is not None:
                    try:
                        peak = _read_peak(cg_path, self.peak_source)
                    except Exception as e:
                        aborted = "sample-unreadable"
                        aborted_path = str(_peak_path(cg_path, self.peak_source))
                        break
                    # peak is None when the kernel exposes no counter, so the
                    # peak is unknown: it cannot be compared and the window can
                    # never be VERIFIED (decided after the run closes).
                    if peak is not None and peak > CAP_BYTES:
                        killed_reason = "cgroup-peak"
                        _signal_child(proc, signal.SIGTERM)
                        try:
                            proc.wait(timeout=grace)
                        except subprocess.TimeoutExpired:
                            _signal_child(proc, signal.SIGKILL)
                            proc.wait()
                        break
                time.sleep(0.5)
            if aborted:
                try:
                    _signal_child(proc, signal.SIGTERM)
                    proc.wait(timeout=grace)
                except Exception:
                    try:
                        _signal_child(proc, signal.SIGKILL)
                        proc.wait()
                    except Exception:
                        pass
            if stop_requested["v"] and proc.poll() is None:
                try:
                    proc.wait(timeout=grace)
                except subprocess.TimeoutExpired:
                    _signal_child(proc, signal.SIGKILL)
                    proc.wait()
            if proc.poll() is None:
                proc.wait()
        finally:
            if prev_int is not None:
                try:
                    signal.signal(signal.SIGINT, prev_int)
                except Exception:
                    pass
            if prev_term is not None:
                try:
                    signal.signal(signal.SIGTERM, prev_term)
                except Exception:
                    pass
            stop_event.set()
            sampler.join(timeout=5)
            if sampler.error is not None and aborted is None:
                aborted = "sample-unreadable"
                aborted_path = sampler.error_path
            peak_bytes = None
            if cg_path is not None:
                try:
                    peak_bytes = _read_peak(cg_path, self.peak_source)
                except Exception:
                    if aborted is None:
                        aborted = "sample-unreadable"
                        aborted_path = str(_peak_path(cg_path, self.peak_source))
            cgroup_peak_gb = (peak_bytes / (1024 ** 3)) if peak_bytes is not None else None
            close_ma = None
            try:
                close_ma = src.mem_available_gb()
            except Exception:
                if aborted is None:
                    aborted = "sample-unreadable"
                    aborted_path = src.label
            unaccounted_gb = None
            unaccounted_reason = None
            if enforcement == "declared-only":
                # No measured peak exists off-box, so the remainder cannot be
                # accounted. Recording it as 0 would fabricate a measurement.
                unaccounted_reason = "remote-host-declared-only"
            elif cgroup_peak_gb is None or close_ma is None:
                unaccounted_reason = "close-read-failed"
            else:
                unaccounted_gb = (opened_ma - close_ma) - cgroup_peak_gb
                if unaccounted_gb < 0:
                    unaccounted_reason = "mem-available-rose"
            w2 = self._read_window() or w
            w2["mem_source"] = src.label
            w2["enforcement"] = enforcement
            w2["cgroup_peak_gb"] = cgroup_peak_gb
            w2["unaccounted_gb"] = unaccounted_gb
            w2["killed"] = killed_reason
            w2["aborted"] = aborted
            if aborted_path is not None:
                w2["aborted_path"] = aborted_path
            if unaccounted_reason is not None:
                w2["unaccounted_reason"] = unaccounted_reason
            rc = proc.returncode
            w2["exit_code"] = rc
            w2["returncode"] = rc
            w2["child_returncode"] = rc
            if rc is not None and rc < 0:
                w2["child_signal"] = -rc
                w2["signal"] = -rc
            # Ordered allowance chain: every UNVERIFIED branch is tested first
            # and VERIFIED is the LAST RESORT. VERIFIED is reachable only when
            # the child completed normally, was neither killed nor aborted by
            # the supervisor, the measured peak exists and is inside the cap,
            # and the measured unaccounted remainder is present and >= 0.
            allowance = "UNVERIFIED"
            allowance_reason = None
            if killed_reason is not None:
                allowance_reason = "killed-by-supervisor"
            elif aborted is not None:
                allowance_reason = "aborted"
            elif rc is not None and rc < 0:
                allowance_reason = "died-by-signal"
            elif enforcement == "cgroup" and cgroup_peak_gb is None:
                allowance_reason = "peak-unknown"
            elif cgroup_peak_gb is not None and cgroup_peak_gb > CAP_GB:
                allowance_reason = "peak-exceeded-cap"
            elif enforcement == "cgroup" and unaccounted_gb is None:
                allowance_reason = "unaccounted-unknown"
            elif unaccounted_gb is not None and unaccounted_gb < 0:
                allowance_reason = "mem-available-rose"
            elif enforcement == "declared-only":
                # The peak was declared, never measured, and the cgroup that
                # would prove it lives on another host. Never claim VERIFIED.
                allowance_reason = "remote-host-declared-only"
            else:
                allowance = "VERIFIED"
                allowance_reason = (
                    f"cgroup_peak_gb {cgroup_peak_gb:.2f} + "
                    f"unaccounted_gb {unaccounted_gb:.2f} <= {CAP_GB} GB"
                )
            w2["allowance"] = allowance
            w2["allowance_reason"] = allowance_reason
            try:
                with self._samples_path().open("a") as f:
                    f.write(json.dumps(w2) + "\n")
            except Exception:
                pass
            try:
                self._window_path().unlink(missing_ok=True)
            except Exception:
                pass
            if cg_path is not None:
                try:
                    cg_path.rmdir()
                except Exception:
                    pass

        if killed_reason == "cgroup-peak":
            print("killed: cgroup-peak", flush=True)
        if aborted == "sample-unreadable":
            print(f"aborted: sample-unreadable {aborted_path}", flush=True)
        if aborted is not None or killed_reason is not None:
            return 1
        return proc.returncode if proc.returncode is not None else 0


# Back-compat aliases for injectable entry points
Supervisor = SpccSupervisor
SpccRunSupervisor = SpccSupervisor
MemorySupervisor = SpccSupervisor
RunSupervisor = SpccSupervisor


def cmd_run(args, cgroup_root=None, peak_source=None, meminfo_path=None, base_dir=None,
            grace_seconds=None, mem_source=None, remote_runner=None):
    # Constructor defaults read SPCC_CGROUP_ROOT / SPCC_MEMINFO_PATH / SPCC_BASE_DIR.
    grace = grace_seconds if grace_seconds is not None else getattr(args, "grace", 10.0)
    if mem_source is None and getattr(args, "target_host", None):
        # An explicit --target-host on `run` overrides the window's mem_source;
        # otherwise the window's own record decides which host was bounded.
        mem_source = make_mem_source(args.target_host, remote_runner=remote_runner)
    sup = SpccSupervisor(
        cgroup_root=cgroup_root,
        peak_source=peak_source,
        meminfo_path=meminfo_path,
        base_dir=base_dir,
        grace_seconds=grace,
        mem_source=mem_source,
        remote_runner=remote_runner,
    )
    return sup.run(getattr(args, "cmd", None), grace_seconds=grace)


def cmd_close_window(args):
    w = read_window()
    if w is None:
        print("no window open", flush=True)
        return 1
    peak = w.get("cgroup_peak_gb")
    unacc = w.get("unaccounted_gb")
    verdict = w.get("allowance", "UNVERIFIED")
    killed = w.get("killed")
    try:
        window_path().unlink()
    except FileNotFoundError:
        pass
    extra = f" killed={killed}" if killed else ""
    peak_s = "null" if peak is None else f"{float(peak):.3f}GB"
    unacc_s = "null" if unacc is None else f"{float(unacc):.3f}GB"
    reason = w.get("unaccounted_reason")
    if reason:
        extra += f" unaccounted_reason={reason}"
    print(f"job={w.get('job')} cgroup_peak={peak_s} unaccounted={unacc_s} verdict={verdict}{extra}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="sub", required=True)
    ow = sub.add_parser("open-window")
    ow.add_argument("--job", required=True)
    ow.add_argument("--declared-peak-gb", type=float, required=True)
    ow.add_argument("--target-host", default=None,
                    help="host the workload runs on; default local (env SPCC_TARGET_HOST)")
    ow.set_defaults(func=cmd_open_window)

    rn = sub.add_parser("run")
    rn.add_argument("cmd", nargs=argparse.REMAINDER)
    _default_grace = 10.0
    try:
        _default_grace = float(os.environ.get("SPCC_KILL_GRACE", "10"))
    except (TypeError, ValueError):
        _default_grace = 10.0
    rn.add_argument("--grace", "--kill-grace", "--grace-seconds", "--kill-grace-seconds", "--grace-period",
                    dest="grace", type=float, default=_default_grace)
    rn.add_argument("--target-host", default=None,
                    help="override the memory source recorded by open-window")
    rn.set_defaults(func=cmd_run)

    cw = sub.add_parser("close-window")
    cw.set_defaults(func=cmd_close_window)

    args = ap.parse_args()
    if getattr(args, "cmd", None) and args.cmd and args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
