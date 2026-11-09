"""LEDGER-RECONCILE-DELTA — the launcher's ledger check is a DELTA, not equality.

The defect this file guards is structural, not arithmetic. `measure/REQUEST-LEDGER.json`
is REBUILT from `measure/rows-*.jsonl`, so it moves with every billed cell, while
`measure/LEDGER-GRID-BASELINE-N.json` is frozen at one instant. Comparing the two
numbers for equality therefore refuses EVERY launch after the first post-freeze cell:
CANARY-ERA-B-4 was refused at gate 2 with zero requests spent (baseline-2 3,192 vs
live 3,144 — 48 rows billed 20:20–20:43Z, four complete 12-turn cells).

The check is now `live == baseline + attributed_delta`, the delta counted from the rows
files stamped after the baseline's `as_of`. Re-cutting the number alone would leave the
trap armed for the next cell, which is why the tests below cover BOTH halves:

  * the delta is measured and printed (tests 1-4),
  * a gap that NO rows file explains is still a hard refusal, naming the gap
    (test 5), and the guard is proven load-bearing by reverting it (test 8).

Offline by construction: every launcher run here is `--dry-run`, and test 9 records
every child argv and fails on a socket. No request is spent and no cell runs live.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(ENG))
TOOLS = os.path.join(ENG, "tools")
MEAS = os.path.join(ENG, "measure")
# RUN_A_STAR_PATH lets a REVERTED launcher be loaded without touching the tree.
LAUNCHER = os.environ.get("RUN_A_STAR_PATH") or os.path.join(TOOLS, "run_a_star.py")
BASELINE_V2 = os.path.join(MEAS, "LEDGER-GRID-BASELINE-2.json")
BASELINE_V3 = os.path.join(MEAS, "LEDGER-GRID-BASELINE-3.json")
LIVE = os.path.join(MEAS, "REQUEST-LEDGER.json")
ROWS_GLOB = os.path.join(MEAS, "rows-*.jsonl")
PY = os.path.abspath(sys.executable)

FOUR_FILES = (
    "rows-cell-pointer-stable-20261026T202040Z.jsonl",
    "rows-cell-transcript-grow-20261026T202444Z.jsonl",
    "rows-cell-transcript-compact-20261026T203733Z.jsonl",
    "rows-cell-pointer-stable-20261026T204258Z.jsonl",
)
CANARY = ["--tools", "read_file", "--canary", "--budget", "108",
          "--hypothesis", "smoke", "--max-wall", "900", "--dry-run"]
RECONCILE_RE = re.compile(r"RECONCILE baseline=(\d+) attributed_delta=(\d+) live=(\d+) "
                          r"explained=(\d+) gap=(-?\d+)")


# --------------------------------------------------------------------------- helpers

def load_launcher(**env):
    """Import the launcher by path with its ledger hooks set BEFORE import."""
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update({k: v for k, v in env.items() if v is not None})
    try:
        spec = importlib.util.spec_from_file_location("run_a_star_ledger", LAUNCHER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def copies(tmp_path, *, baseline=BASELINE_V3, bump_requests=0):
    """A /tmp baseline + live ledger pair, optionally inflated by N unattributed rows."""
    base = json.load(open(baseline, encoding="utf-8"))
    live = json.load(open(LIVE, encoding="utf-8"))
    b = tmp_path / ("baseline-%s" % os.path.basename(baseline))
    l = tmp_path / "live.json"
    if bump_requests:
        for key in ("requests", "requests_raw"):
            if key in live:
                live[key] += bump_requests
        live["budget"]["spent"] += bump_requests
        live["budget"]["spent_raw"] = live["budget"].get("spent_raw", 0) + bump_requests
        live["remaining"] -= bump_requests
        live["budget"]["remaining"] -= bump_requests
        live["budget"]["remaining_raw"] = live["budget"].get("remaining_raw", 0) - bump_requests
        for key in ("requests_raw", "requests"):
            if key in live.get("counting", {}):
                live["counting"][key] += bump_requests
        for key in ("remaining_raw", "remaining"):
            if key in live.get("counting", {}):
                live["counting"][key] -= bump_requests
    b.write_text(json.dumps(base), encoding="utf-8")
    l.write_text(json.dumps(live), encoding="utf-8")
    return str(b), str(l)


def run(args, env=None):
    e = dict(os.environ)
    e.pop("RUN_A_STAR_LEDGER_BASELINE", None)
    e.pop("RUN_A_STAR_LEDGER_LIVE", None)
    e.pop("RUN_A_STAR_LEDGER_ROWS", None)
    e.update(env or {})
    return subprocess.run([PY, LAUNCHER] + args, cwd=ROOT, env=e,
                          capture_output=True, text=True, timeout=300)


# ------------------------------------------------------- 1. the delta is a measurement

def test_attributed_delta_counts_the_four_files_since_v2():
    """The 48 are read off the row files, not asserted: 4 x 12 rows, shas from the ledger."""
    ra = load_launcher(RUN_A_STAR_LEDGER_ROWS=ROWS_GLOB)
    v2 = json.load(open(BASELINE_V2, encoding="utf-8"))
    delta, files = ra.attributed_delta(ra._epoch(v2["frozen_at"]))
    assert delta == 48, delta
    assert sorted(f["file"] for f in files) == sorted(FOUR_FILES), files
    assert all(f["rows"] == 12 for f in files), files
    live = json.load(open(LIVE, encoding="utf-8"))
    by = {e["file"]: e["sha256"] for e in live["per_file"]}
    for f in files:
        assert f["sha256"] == by[f["file"]], f


def test_v3_baseline_attributes_the_48_and_leaves_v2_untouched():
    v3 = json.load(open(BASELINE_V3, encoding="utf-8"))
    assert (v3["requests"], v3["remaining"], v3["cap"]) == (1176, 3144, 4320), v3
    assert v3["attribution"]["total_requests"] == 48, v3["attribution"]
    assert sorted(e["file"] for e in v3["attribution"]["files"]) == sorted(FOUR_FILES)
    assert all(e["rows"] == 12 for e in v3["attribution"]["files"])
    assert v3["supersedes"]["requests"] == 1128
    assert v3["supersedes"]["remaining"] == 3192
    assert v3["supersedes"]["frozen_at"] == "2026-10-26T19:04:18Z"
    v2 = json.load(open(BASELINE_V2, encoding="utf-8"))
    assert (v2["requests"], v2["remaining"]) == (1128, 3192), "v2 was mutated"


# ------------------------------------------------------------ 2. the launcher accepts

def test_canary_dry_run_exits_zero_with_the_three_numbers():
    proc = run(CANARY)
    out = proc.stdout
    assert proc.returncode == 0, out[-2000:] + proc.stderr[-2000:]
    m = RECONCILE_RE.search(out)
    assert m, out[-2000:]
    base, delta, live, explained, gap = (int(g) for g in m.groups())
    assert (base, delta, live) == (1176, 0, 1176), m.group(0)
    assert explained == live and gap == 0, m.group(0)
    assert "canary_arms=4" in out and "canary_requests=48" in out, out[-800:]
    assert "refused=0" in out, out[-800:]


def test_legacy_v2_baseline_is_accepted_through_the_delta(tmp_path):
    """The old frozen record plus the 48 rows that landed after it closes exactly."""
    proc = run(CANARY, env={"RUN_A_STAR_LEDGER_BASELINE": BASELINE_V2})
    out = proc.stdout
    assert proc.returncode == 0, out[-2000:] + proc.stderr[-2000:]
    m = RECONCILE_RE.search(out)
    assert m, out[-2000:]
    base, delta, live = (int(g) for g in m.groups()[:3])
    assert (base, delta, live) == (1128, 48, 1176), m.group(0)
    for name in FOUR_FILES:
        assert name in m.string, "the delta's files are not named on the line"


# --------------------------------------------- 3. an unexplained gap is still a refusal

def test_seven_unattributed_requests_refuse_and_name_the_seven(tmp_path):
    base, live = copies(tmp_path, baseline=BASELINE_V2, bump_requests=7)
    proc = run(CANARY, env={"RUN_A_STAR_LEDGER_BASELINE": base,
                            "RUN_A_STAR_LEDGER_LIVE": live})
    out, err = proc.stdout, proc.stderr
    assert proc.returncode != 0, "an unexplained gap of 7 was allowed:\n" + out[-2000:]
    blob = out + err
    assert "REFUSED" in blob, blob[-2000:]
    assert "unexplained=7" in blob, blob[-2000:]
    assert "7 request(s) of ledger gap cannot be attributed" in blob, blob[-2000:]
    assert "DRY END" not in out, "a refused launch still previewed cells"
    m = RECONCILE_RE.search(out)
    assert m and int(m.group(5)) == 7, out[-2000:]  # live exceeds explained


def test_equal_baseline_plus_delta_is_allowed(tmp_path):
    base, live = copies(tmp_path, baseline=BASELINE_V2)
    proc = run(CANARY, env={"RUN_A_STAR_LEDGER_BASELINE": base,
                            "RUN_A_STAR_LEDGER_LIVE": live})
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert "REFUSED" not in (proc.stdout + proc.stderr)
    assert "refused=0" in proc.stdout, proc.stdout[-800:]


def test_missing_baseline_refuses_by_name(tmp_path):
    missing = str(tmp_path / "no-such-baseline.json")
    proc = run(CANARY, env={"RUN_A_STAR_LEDGER_BASELINE": missing})
    blob = proc.stdout + proc.stderr
    assert proc.returncode != 0, blob[-2000:]
    assert "REFUSED: ledger baseline" in blob, blob[-2000:]
    assert missing in blob, "the missing record is not named: " + blob[-2000:]
    assert "DRY END" not in proc.stdout


def test_reverted_delta_check_lets_the_seven_through(tmp_path):
    """red->green: the two refusal branches are the guard, and removing them is visible."""
    src = open(LAUNCHER, encoding="utf-8").read()
    gap_guard = "    if explained != live_requests:"
    rem_guard = "    if base_remaining - delta != live_remaining:"
    for marker in (gap_guard, rem_guard):
        assert src.count(marker) == 1, "the guard is not where this test expects: %r" % marker
    reverted = tmp_path / "run_a_star_no_delta_guard.py"
    reverted.write_text(src.replace(gap_guard, "    if False and explained != live_requests:")
                           .replace(rem_guard, "    if False and base_remaining - delta "
                                               "!= live_remaining:"), encoding="utf-8")
    base, live = copies(tmp_path, baseline=BASELINE_V2, bump_requests=7)
    env = {"RUN_A_STAR_LEDGER_BASELINE": base, "RUN_A_STAR_LEDGER_LIVE": live}
    green = run(CANARY, env=env)
    red = subprocess.run([PY, str(reverted)] + CANARY, cwd=ROOT,
                         env={**os.environ, **env}, capture_output=True, text=True,
                         timeout=300)
    assert green.returncode != 0, "GREEN: the guard did not fire:\n" + green.stdout[-1500:]
    assert red.returncode == 0, (
        "RED: with the guard removed the 7 are still refused, so this test proves "
        "nothing:\n" + red.stdout[-1500:] + red.stderr[-800:])


# ------------------------------------------------------------------- 4. zero network

def test_dry_run_opens_no_socket_and_launches_no_live_cell(monkeypatch):
    ra = load_launcher(RUN_A_STAR_LEDGER_ROWS=ROWS_GLOB)
    spawned, sockets = [], []
    real_run = subprocess.run

    def record(argv, **kw):
        spawned.append(list(argv))
        return real_run(argv[:1] + ["-c", "print('dry-run G1 allow; dry-run G2 allow; "
                                    "dry-run G3 allow')"], **kw)

    monkeypatch.setattr(ra.subprocess, "run", record)
    monkeypatch.setattr(socket, "socket",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a socket"))
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a connection"))
    monkeypatch.setattr(sys, "argv", [LAUNCHER] + CANARY)
    assert ra.main() == 0
    assert sockets == [], sockets
    assert spawned, "the recorder saw no child — the test proved nothing"
    assert len(spawned) == 4, "the canary previews one cell per arm: %r" % (spawned,)
    for argv in spawned:
        assert "--dry-run" in argv, "a LIVE cell.py was launched: %r" % (argv,)
