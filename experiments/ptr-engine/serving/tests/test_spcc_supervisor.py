import os
import shlex
import subprocess
import json
import time
import threading
import importlib.util
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "spcc_supervisor.py"
PY = "/home/zer0null/research extractor/.venv/bin/python"

CAP_BYTES = 64424509440


def run_supervisor(env, *args, timeout=30):
    return subprocess.run([PY, str(SCRIPT), *args], env=env, capture_output=True, text=True, timeout=timeout)


def make_env(tmp_path):
    env = os.environ.copy()
    env["SPCC_BASE_DIR"] = str(tmp_path)
    env["SPCC_CGROUP_ROOT"] = str(tmp_path / "cg")
    env["SPCC_MEMINFO_PATH"] = str(tmp_path / "meminfo")
    cg = tmp_path / "cg"
    cg.mkdir(exist_ok=True)
    (cg / "subtree_control").write_text("")
    # 121 GB: the GB10/GX10 pool the 60 GB allowance is written against.
    (tmp_path / "meminfo").write_text("MemTotal: 126877696 kB\n"
                                      "MemAvailable: 104857600 kB\n")
    # A measured peak the fixture supplies itself; the supervisor must never
    # write a synthetic zero into the cgroup.
    peak = tmp_path / "peak"
    peak.write_text("0\n")
    env["SPCC_PEAK_FILE"] = str(peak)
    return env


def final_record(tmp_path):
    sp = tmp_path / "MEM-WINDOW.jsonl"
    lines = [l for l in sp.read_text().splitlines() if l.strip()]
    return json.loads(lines[-1])


def test_declared_peak_61(tmp_path):
    env = make_env(tmp_path)
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "61")
    assert r.returncode == 2, r.stderr + r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists()


def test_memavailable_below_reserve(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / "meminfo").write_text("MemTotal: 126877696 kB\n"
                                      "MemAvailable: 62914560 kB\n")
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    assert r.returncode == 2, r.stderr + r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists()


def test_run_no_window(tmp_path):
    env = make_env(tmp_path)
    r = run_supervisor(env, "run", "--", "echo", "hi")
    assert r.returncode == 3, r.stderr + r.stdout


def test_run_unwritable_cgroup(tmp_path):
    env = make_env(tmp_path)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    ro = tmp_path / "nonexistent_cg_root"
    env2 = dict(env)
    env2["SPCC_CGROUP_ROOT"] = str(ro)
    marker = tmp_path / "marker.txt"
    r = run_supervisor(env2, "run", "--", "sh", "-c", f"touch {marker}")
    assert r.returncode == 3, r.stderr + r.stdout
    assert not marker.exists(), "command must not have started"


def test_clean_run(tmp_path):
    env = make_env(tmp_path)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 0, r.stderr + r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists(), "window should be removed after run"
    sp = tmp_path / "MEM-WINDOW.jsonl"
    assert sp.exists()
    lines = [l for l in sp.read_text().splitlines() if l.strip()]
    assert len(lines) >= 1
    rec = json.loads(lines[-1])
    assert rec.get("aborted") is None
    assert rec.get("killed") is None


def test_clean_run_with_sleep(tmp_path):
    env = make_env(tmp_path)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "sleep", "3")
    assert r.returncode == 0, r.stderr + r.stdout
    samples = tmp_path / "MEM-WINDOW.jsonl"
    assert samples.exists()
    lines = [l for l in samples.read_text().splitlines() if l.strip()]
    assert len(lines) >= 2, f"only {len(lines)} samples"
    assert not (tmp_path / "MEM-WINDOW.json").exists()


def test_exit_code_propagates(tmp_path):
    env = make_env(tmp_path)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", PY, "-c", "import sys; sys.exit(7)")
    assert r.returncode == 7, r.stderr + r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("exit_code") == 7


def test_child_killed_by_signal_removes_window(tmp_path):
    env = make_env(tmp_path)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", PY, "-c", "import os,signal; os.kill(os.getpid(), signal.SIGTERM)")
    # supervisor propagates child signal (negative) or 0/1; window removed either way
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("child_signal") == 15 or rec.get("signal") == 15 or rec.get("child_returncode", 0) < 0


def test_unreadable_peak_aborts(tmp_path):
    env = make_env(tmp_path)
    env["SPCC_PEAK_FILE"] = str(tmp_path / "no-such-peak-file")
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "sleep", "5")
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("aborted") == "sample-unreadable", rec
    assert "aborted: sample-unreadable" in (r.stdout + r.stderr)


def test_unreadable_peak_midrun_aborts(tmp_path):
    env = make_env(tmp_path)
    peak_file = tmp_path / "peak"
    peak_file.write_text("0")
    env["SPCC_PEAK_FILE"] = str(peak_file)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")

    def _remove_peak():
        time.sleep(1.0)
        peak_file.unlink(missing_ok=True)

    t = threading.Thread(target=_remove_peak)
    t.start()
    r = run_supervisor(env, "run", "--", "sleep", "10")
    t.join(timeout=5)
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("aborted") == "sample-unreadable", rec
    assert "aborted: sample-unreadable" in (r.stdout + r.stderr)


def test_peak_above_cap_sigterm(tmp_path):
    env = make_env(tmp_path)
    peak_file = tmp_path / "peak"
    peak_file.write_text(str(70 * 1024 ** 3))
    env["SPCC_PEAK_FILE"] = str(peak_file)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--grace", "0.2", "--", "sleep", "30")
    assert r.returncode != 0
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("killed") == "cgroup-peak", rec
    assert "killed: cgroup-peak" in (r.stdout + r.stderr)


def test_peak_above_cap_sigkill(tmp_path):
    env = make_env(tmp_path)
    peak_file = tmp_path / "peak"
    peak_file.write_text("0")
    env["SPCC_PEAK_FILE"] = str(peak_file)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")

    def _raise_peak():
        time.sleep(1.0)
        tmp = tmp_path / "peak.tmp"
        tmp.write_text(str(70 * 1024 ** 3))
        tmp.replace(peak_file)

    t = threading.Thread(target=_raise_peak)
    t.start()
    # child ignores SIGTERM, so the supervisor must escalate to SIGKILL
    child = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
    r = run_supervisor(env, "run", "--grace", "0.2", "--", PY, "-c", child)
    t.join(timeout=5)
    assert r.returncode != 0
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    rec = final_record(tmp_path)
    assert rec.get("killed") == "cgroup-peak", rec
    assert rec.get("child_returncode") == -9 or rec.get("child_signal") == 9 or rec.get("signal") == 9, rec


# --- Fix 1: a killed window is never VERIFIED -------------------------------

def test_killed_window_never_verified(tmp_path):
    env = make_env(tmp_path)
    peak_file = tmp_path / "peak"
    peak_file.write_text(str(70 * 1024 ** 3))
    env["SPCC_PEAK_FILE"] = str(peak_file)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--grace", "0.2", "--", "sleep", "30")
    assert r.returncode != 0
    rec = final_record(tmp_path)
    assert rec.get("killed") == "cgroup-peak", rec
    assert rec.get("allowance") != "VERIFIED", rec
    assert rec.get("allowance") == "UNVERIFIED", rec


# --- Fix 2: no fabricated zeros when the closing reads fail ------------------

def test_closing_read_failure_records_null_not_zero(tmp_path):
    env = make_env(tmp_path)
    env["SPCC_PEAK_FILE"] = str(tmp_path / "no-such-peak-file")
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "sleep", "5")
    assert r.returncode != 0
    rec = final_record(tmp_path)
    assert rec.get("aborted") == "sample-unreadable", rec
    # ABSENT != 0: the failed read must be null, never a measured-looking 0.0
    assert "cgroup_peak_gb" in rec and rec["cgroup_peak_gb"] is None, rec
    assert "unaccounted_gb" in rec and rec["unaccounted_gb"] is None, rec
    assert rec["cgroup_peak_gb"] != 0
    assert rec["unaccounted_gb"] != 0
    assert rec.get("unaccounted_reason") == "close-read-failed", rec
    assert rec.get("allowance") == "UNVERIFIED", rec


# --- Fix 3: negative unaccounted is still unmeasured ------------------------

def test_memavailable_rose_stays_unverified(tmp_path):
    env = make_env(tmp_path)
    # 100 GB available at open time, recorded into the window
    (tmp_path / "meminfo").write_text("MemTotal: 126877696 kB\n"
                                      "MemAvailable: 104857600 kB\n")
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    assert r.returncode == 0, r.stdout + r.stderr
    win = json.loads((tmp_path / "MEM-WINDOW.json").read_text())
    assert win["mem_available_gb"] == 100.0, win
    # MemAvailable climbs to 120 GB before the run closes the window
    (tmp_path / "meminfo").write_text("MemAvailable: 125829120 kB\n")
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = final_record(tmp_path)
    assert rec.get("unaccounted_gb") is not None and rec["unaccounted_gb"] < 0, rec
    assert rec.get("unaccounted_reason") == "mem-available-rose", rec
    assert rec.get("allowance") == "UNVERIFIED", rec


# --- Fix 4: window ownership survives a short-lived wrapper -----------------

def test_owner_wrapper_bash_c_accepted(tmp_path):
    env = make_env(tmp_path)
    py, script = shlex.quote(PY), shlex.quote(str(SCRIPT))
    win_path = tmp_path / "MEM-WINDOW.json"
    inner = (f"{py} {script} open-window --job j --declared-peak-gb 10"
             f" && cat {shlex.quote(str(win_path))}"
             f" && {py} {script} run -- true")
    r = subprocess.run(["bash", "-c", inner], env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    # The opener itself is gone by the time `run` starts; only the wrapper
    # shell remains, so acceptance proves the parent link is used.
    win, _ = json.JSONDecoder().raw_decode(r.stdout[r.stdout.index("{"):])
    assert win["owners"][0]["pid"] != os.getpid()
    assert all(owner["pid"] != os.getpid() for owner in win["owners"]), win["owners"]
    assert (tmp_path / "MEM-WINDOW.jsonl").exists()
    rec = final_record(tmp_path)
    assert rec.get("allowance") == "VERIFIED", rec
    assert not (tmp_path / "MEM-WINDOW.json").exists()


def test_owner_refused_after_owner_exits_and_pid_reuse_defeated(tmp_path):
    env = make_env(tmp_path)
    # The whole opener chain (open-window process and its wrapper shell) is
    # short-lived and detached from this test process.
    # A bash `-c` script execs its last command, which would leave the caller as
    # the recorded parent; the trailing no-op forces a real wrapper process
    # that exits with the opener, so the whole recorded chain is short-lived.
    opener = (f"{shlex.quote(PY)} {shlex.quote(str(SCRIPT))} open-window "
              f"--job j --declared-peak-gb 10; :")
    r = subprocess.run(["bash", "-c", opener], env=env, capture_output=True,
                       text=True, timeout=60, start_new_session=True)
    assert r.returncode == 0, r.stdout + r.stderr
    win = json.loads((tmp_path / "MEM-WINDOW.json").read_text())
    assert win["owner_pid"] != os.getpid()
    assert all(owner["pid"] != os.getpid() for owner in win["owners"]), win["owners"]
    for owner in win["owners"]:
        assert owner["start_time"] is not None
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 3, r.stdout + r.stderr
    assert "no longer alive" in (r.stdout + r.stderr)
    # pid reuse: a live pid with a different start time must not revive it.
    win["owners"] = [{"pid": os.getpid(), "start_time": 1}]
    win["owner_pid"] = os.getpid()
    win["owner_start_time"] = 1
    (tmp_path / "MEM-WINDOW.json").write_text(json.dumps(win) + "\n")
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 3, r.stdout + r.stderr


# --- Refusal names the blocking number and the shortfall -------------------

def test_refusal_names_shortfall(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / "meminfo").write_text("MemTotal: 126877696 kB\n"
                                      "MemAvailable: 62914560 kB\n")  # 60.0 GB
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "MemAvailable 60.0 GB < 68.0 GB reserve (short by 8.0 GB)" in r.stdout, r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists()


# --- U-SPCC-5D: the allowance chain may only end at VERIFIED as a last resort

def test_peak_62_with_sigkill_is_unverified_died_by_signal(tmp_path):
    env = make_env(tmp_path)
    peak = tmp_path / "peak"
    peak.write_text(str(62 * 1024 ** 3))
    env["SPCC_PEAK_FILE"] = str(peak)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    child = "import os,signal; os.kill(os.getpid(), signal.SIGKILL)"
    r = run_supervisor(env, "run", "--", PY, "-c", child)
    rec = final_record(tmp_path)
    assert rec.get("killed") is None, rec
    assert rec.get("aborted") is None, rec
    assert rec.get("returncode") == -9, rec
    assert rec.get("child_signal") == 9, rec
    assert rec["cgroup_peak_gb"] > 60, rec
    assert rec.get("allowance") == "UNVERIFIED", rec
    assert rec.get("allowance_reason") == "died-by-signal", rec


def test_peak_62_with_clean_exit_is_unverified_peak_exceeded(tmp_path):
    env = make_env(tmp_path)
    peak = tmp_path / "peak"
    peak.write_text(str(62 * 1024 ** 3))
    env["SPCC_PEAK_FILE"] = str(peak)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = final_record(tmp_path)
    assert rec.get("killed") is None, rec
    assert rec.get("aborted") is None, rec
    assert rec.get("returncode") == 0, rec
    assert rec["cgroup_peak_gb"] > 60, rec
    assert rec.get("allowance") == "UNVERIFIED", rec
    assert rec.get("allowance_reason") == "peak-exceeded-cap", rec


def test_absent_memory_peak_is_unknown_not_verified(tmp_path):
    env = make_env(tmp_path)
    # No explicit peak source at all: the cgroup's own memory.peak is the only
    # source, and the kernel-facing fixture does not provide one.
    env.pop("SPCC_PEAK_FILE", None)
    run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    r = run_supervisor(env, "run", "--", "true")
    rec = final_record(tmp_path)
    assert rec.get("aborted") is None, rec
    assert "cgroup_peak_gb" in rec and rec["cgroup_peak_gb"] is None, rec
    assert rec.get("unaccounted_gb") is None, rec
    assert rec.get("allowance") == "UNVERIFIED", rec
    assert rec.get("allowance_reason") == "peak-unknown", rec


def test_within_cap_measured_sum_is_verified(tmp_path):
    env = make_env(tmp_path)
    peak = tmp_path / "peak"
    peak.write_text(str(44 * 1024 ** 3))
    env["SPCC_PEAK_FILE"] = str(peak)
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "50")
    assert r.returncode == 0, r.stdout + r.stderr
    # 100 GB available when the window opened, 53 GB when it closed.
    (tmp_path / "meminfo").write_text("MemTotal: 126877696 kB\n"
                                      "MemAvailable: 55574528 kB\n")
    r = run_supervisor(env, "run", "--", "true")
    assert r.returncode == 0, r.stdout + r.stderr
    rec = final_record(tmp_path)
    assert rec.get("killed") is None and rec.get("aborted") is None, rec
    assert rec.get("returncode") == 0, rec
    assert abs(rec["cgroup_peak_gb"] - 44.0) < 1e-6, rec
    assert abs(rec["unaccounted_gb"] - 3.0) < 1e-6, rec
    assert rec.get("allowance") == "VERIFIED", rec
    reason = rec.get("allowance_reason") or ""
    assert "44.00" in reason and "3.00" in reason and "60" in reason, rec


# --- U-SPCC-13: the supervisor must bound the host the workload runs on ------
#
# The measured host is the GX10 (121 GB unified pool); this box reports 29 GB.
# The old supervisor sampled this box unconditionally, so 60 + 8 = 68 GB was
# unsatisfiable and the allowance could never describe the accelerator. The
# remote cases use injected readers: no ssh/network is exercised here.

REMOTE_121 = "MemTotal: 126877696 kB\nMemAvailable: 104857600 kB\n"


def _load_module():
    spec = importlib.util.spec_from_file_location("spcc_supervisor_u13", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_wrong_host_memtotal_29_refused_before_child(tmp_path):
    env = make_env(tmp_path)
    (tmp_path / "meminfo").write_text("MemTotal: 30408704 kB\n"   # 29 GB
                                      "MemAvailable: 10485760 kB\n")  # 10 GB
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    assert r.returncode == 4, r.stdout + r.stderr
    assert "MemTotal 29.0 GB" in r.stdout, r.stdout
    assert "100 GB minimum" in r.stdout, r.stdout
    assert "wrong machine" in r.stdout, r.stdout
    assert not (tmp_path / "MEM-WINDOW.json").exists()
    # No child may ever be spawned for a wrong-host window: `run` refuses for
    # want of a window, and no sample record exists to carry a child argv.
    marker = tmp_path / "child-ran"
    r = run_supervisor(env, "run", "--", PY, "-c", f"open({str(marker)!r}, 'w')")
    assert r.returncode == 3, r.stdout + r.stderr
    assert not marker.exists(), "the child command must never have run"
    assert not (tmp_path / "MEM-WINDOW.jsonl").exists()


def test_local_memtotal_121_proceeds_with_cgroup(tmp_path):
    env = make_env(tmp_path)
    r = run_supervisor(env, "open-window", "--job", "j", "--declared-peak-gb", "10")
    assert r.returncode == 0, r.stdout + r.stderr
    win = json.loads((tmp_path / "MEM-WINDOW.json").read_text())
    assert win["mem_source"] == "local", win
    assert win["enforcement"] == "cgroup", win
    assert abs(win["mem_total_gb"] - 121.0) < 1e-6, win


def test_remote_source_declared_only_never_verified(tmp_path):
    mod = _load_module()
    args = types.SimpleNamespace(job="j", declared_peak_gb=10.0, target_host="gx10")
    opener = mod.RemoteMeminfo("gx10", runner=lambda host: REMOTE_121)
    assert mod.cmd_open_window(args, mem_source=opener, base_dir=tmp_path) == 0
    win = json.loads((tmp_path / "MEM-WINDOW.json").read_text())
    assert win["mem_source"] == "ssh:gx10", win
    assert win["enforcement"] == "declared-only", win
    assert win["mem_available_gb"] == 100.0, win

    closing = "MemTotal: 126877696 kB\nMemAvailable: 104333312 kB\n"  # 99.5 GB
    runner = mod.RemoteMeminfo("gx10", runner=lambda host: closing)
    sup = mod.SpccSupervisor(base_dir=tmp_path, mem_source=runner,
                             cgroup_root=tmp_path / "cg",
                             grace_seconds=0.2, sample_interval=0.01)
    assert sup.run(["true"]) == 0
    rec = final_record(tmp_path)
    assert rec["mem_source"] == "ssh:gx10", rec
    assert rec["enforcement"] == "declared-only", rec
    assert rec["cgroup_peak_gb"] is None, rec
    assert rec["unaccounted_gb"] is None, rec
    assert rec.get("unaccounted_reason") == "remote-host-declared-only", rec
    assert rec["allowance"] == "UNVERIFIED", rec
    assert rec["allowance_reason"] == "remote-host-declared-only", rec
    # No cgroup was fabricated on the local hierarchy for a remote window.
    assert not (tmp_path / "cg").exists()


def test_remote_reader_raises_refused_not_zero(tmp_path, capsys):
    mod = _load_module()

    def boom(host):
        raise RuntimeError("ssh: connect to host gx10 port 22: Connection timed out")

    args = types.SimpleNamespace(job="j", declared_peak_gb=10.0, target_host="gx10")
    src = mod.RemoteMeminfo("gx10", runner=boom)
    rc = mod.cmd_open_window(args, mem_source=src, base_dir=tmp_path)
    out = capsys.readouterr().out
    assert rc == mod.EXIT_WRONG_HOST == 4, out
    assert "unreadable" in out and "ssh:gx10" in out, out
    assert not (tmp_path / "MEM-WINDOW.json").exists(), "no record may hold zeros"
    assert not (tmp_path / "MEM-WINDOW.jsonl").exists()


def test_remote_empty_meminfo_raises(tmp_path):
    mod = _load_module()
    src = mod.RemoteMeminfo("gx10", runner=lambda host: "")
    try:
        src.mem_total_gb()
    except RuntimeError as e:
        assert "no meminfo" in str(e), e
    else:
        raise AssertionError("empty remote meminfo must raise, never return zeros")

