"""Offline fail-closed proof suite for the campaign instrument."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CAMPAIGN = Path("/home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN")
WATCHER = CAMPAIGN / "tools" / "watcher.py"
ANALYSER = CAMPAIGN / "run" / "analyse.py"
LEDGER = CAMPAIGN / "ledger" / "ledger.py"
REAL_LEDGER_DIR = CAMPAIGN / "ledger"
PY = sys.executable


def _make_env(tmp_path, rows_path=None, first_deadline=30.0, intent_tol=1, ledger_tol=1, ledger_dir=None):
    d = tmp_path / "env"
    d.mkdir(exist_ok=True)
    env = {
        "rows_path": str(rows_path) if rows_path is not None else str(tmp_path / "rows.jsonl"),
        "intents_path": str(tmp_path / "intents.jsonl"),
        "first_row_deadline_s": first_deadline,
        "row_gap_deadline_s": 30.0,
        "intent_row_tolerance": intent_tol,
        "ledger_tolerance": ledger_tol,
    }
    if ledger_dir is not None:
        env["ledger_dir"] = str(ledger_dir)
    (tmp_path / "envelope.json").write_text(json.dumps(env))
    return tmp_path / "envelope.json"


def _run_watcher(envelope, driver_pid, out_path, interval=0.1, timeout=5):
    cmd = [PY, str(WATCHER), "--envelope", str(envelope), "--phase", "context",
           "--driver-pid", str(driver_pid), "--out", str(out_path), "--interval", str(interval)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _make_rows(tmp_path, name, n_rows=6, null_one=False, fail_arm_task=None):
    rows = []
    tasks = ["D1", "D2"]
    arms = ["A", "B"]
    turn = 0
    for tid in tasks:
        for arm in arms:
            for t in range(1, 4):
                turn += 1
                ok = True
                if fail_arm_task and arm == fail_arm_task[0] and tid == fail_arm_task[1]:
                    ok = False
                cached = 50
                if null_one and arm == "B" and tid == "D1" and t == 2:
                    cached = None
                row = {
                    "schema": "cs.row/1",
                    "attempt_id": f"att-{turn}",
                    "run_id": "synth",
                    "phase": "context",
                    "task_id": tid,
                    "arm": arm,
                    "seed": 1,
                    "rep": 1,
                    "turn": t,
                    "prompt_sha256": "abc",
                    "prompt_tokens": 100,
                    "cached_tokens": cached,
                    "completion_tokens": 20,
                    "reasoning_tokens": 0,
                    "ttft_ms": 100.0 + (5 if arm == "B" else 0),
                    "wall_ms": 200.0,
                    "finish_reason": "stop",
                    "output": f"key={turn}",
                    "grade": {"ok": ok, "checks": [], "silent": False},
                    "engine": {"endpoint": "x", "model": "m", "fingerprint": "fp"},
                    "envelope_path": "env",
                    "envelope_sha256": "h",
                }
                rows.append(row)
    path = tmp_path / name
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_1_missing_rows_file(tmp_path):
    rows_path = tmp_path / "nope.jsonl"  # missing
    env = _make_env(tmp_path, rows_path=rows_path, ledger_dir=tmp_path)
    # alive driver
    driver = subprocess.Popen(["sleep", "30"])
    out = tmp_path / "watch.jsonl"
    try:
        res = _run_watcher(env, driver.pid, out, interval=0.1, timeout=5)
    finally:
        driver.terminate()
        driver.wait()
    assert res.returncode != 0, res.stdout + res.stderr
    assert out.exists()
    last = [l for l in out.read_text().splitlines() if l.strip()][-1]
    ev = json.loads(last)
    assert "rows_missing" in ev["alerts"]
    # driver gate refuses
    sys.path.insert(0, str(CAMPAIGN / "tools"))
    import watcher as w  # type: ignore
    vf = w.verdict_from(out)
    assert vf["alerts"], vf


def test_2_prerow_stall(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text("")  # empty but exists
    env = _make_env(tmp_path, rows_path=rows_path, first_deadline=0.1, ledger_dir=tmp_path)
    driver = subprocess.Popen(["sleep", "30"])
    out = tmp_path / "watch.jsonl"
    try:
        res = _run_watcher(env, driver.pid, out, interval=0.1, timeout=5)
    finally:
        driver.terminate()
        driver.wait()
    assert res.returncode != 0, res.stdout + res.stderr
    evs = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert any("no_first_row" in e["alerts"] for e in evs)


def test_3_watcher_killed_driver_sees_dead(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text("")
    env = _make_env(tmp_path, rows_path=rows_path, ledger_dir=tmp_path)
    driver = subprocess.Popen(["sleep", "30"])
    out = tmp_path / "watch.jsonl"
    watcher = subprocess.Popen([PY, str(WATCHER), "--envelope", str(env), "--phase", "context",
                               "--driver-pid", str(driver.pid), "--out", str(out), "--interval", "0.1"])
    time.sleep(0.5)
    watcher.terminate()
    watcher.wait(timeout=5)
    # make pid file stale
    pid_path = Path(str(out) + ".pid")
    assert pid_path.exists()
    old = time.time() - 100
    os.utime(pid_path, (old, old))
    sys.path.insert(0, str(CAMPAIGN / "tools"))
    import watcher as w  # type: ignore
    vf = w.verdict_from(out)
    assert vf["alive"] is False
    driver.terminate()
    driver.wait()


def test_4_cap_exhaustion(tmp_path):
    # copy ledger dir with small cap
    d = tmp_path / "led"
    d.mkdir()
    cj = d / "campaign.json"
    cj.write_text(json.dumps({
        "total_cap": 2,
        "phase_caps": {"context": 2, "preflight": 1, "prompt_format": 1, "serving": 1, "holdout": 1, "contingency": 1},
        "lock_basename": "campaign.lock",
        "journal_basename": "journal.jsonl",
    }))
    (d / "campaign.lock").write_text("")
    # real ledger hash
    real_journal = REAL_LEDGER_DIR / "journal.jsonl"
    before = real_journal.read_bytes() if real_journal.exists() else None

    def run(*args):
        return subprocess.run([PY, str(LEDGER), "--campaign-json", str(cj), "--ledger-dir", str(d), *args],
                            capture_output=True, text=True)

    aids = []
    for i in range(2):
        r = run("reserve", "--phase", "context", "--label", f"x{i}")
        assert r.returncode == 0, r.stderr
        aids.append(r.stdout.strip())
    # 3rd (1501st analog) rejected
    r = run("reserve", "--phase", "context", "--label", "overflow")
    assert r.returncode != 0
    # real ledger unchanged
    after = real_journal.read_bytes() if real_journal.exists() else None
    assert before == after


def test_5_injected_alert_blocks(tmp_path):
    out = tmp_path / "watch.jsonl"
    ev = {"utc": "2026-01-01T00:00:00Z", "check": 1, "driver_alive": True,
          "rows_count": 1, "intents_count": 1, "last_row_age_s": 0.0,
          "ledger_spent": 1, "verdict": "alert", "alerts": ["injected"]}
    out.write_text(json.dumps(ev) + "\n")
    sys.path.insert(0, str(CAMPAIGN / "tools"))
    import watcher as w  # type: ignore
    vf = w.verdict_from(out)
    assert "injected" in vf["alerts"]
    # driver gate refuses
    assert vf["alerts"]


def test_6_healthy_synthetic_run(tmp_path):
    rows_path = _make_rows(tmp_path, "rows.jsonl")
    env = _make_env(tmp_path, rows_path=rows_path, ledger_dir=tmp_path)
    # run analyser
    res = subprocess.run([PY, str(ANALYSER), "--envelope", str(env), "--phase", "context"],
                        capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "A" in res.stdout and "B" in res.stdout
    assert "WINNER" in res.stdout
    # rows valid
    for line in rows_path.read_text().splitlines():
        obj = json.loads(line)
        assert obj["schema"] == "cs.row/1"


def test_7_uncertainty_range(tmp_path):
    rows_path = _make_rows(tmp_path, "rows.jsonl", null_one=True)
    env = _make_env(tmp_path, rows_path=rows_path, ledger_dir=tmp_path)
    res = subprocess.run([PY, str(ANALYSER), "--envelope", str(env), "--phase", "context"],
                        capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    assert ".." in res.stdout, res.stdout


def test_8_quality_refusal(tmp_path):
    rows_path = _make_rows(tmp_path, "rows.jsonl", fail_arm_task=("B", "D1"))
    env = _make_env(tmp_path, rows_path=rows_path, ledger_dir=tmp_path)
    res = subprocess.run([PY, str(ANALYSER), "--envelope", str(env), "--phase", "context"],
                        capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "WINNER: A" in res.stdout, res.stdout
