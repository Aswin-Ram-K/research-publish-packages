"""LAUNCHER-GEN5-WIRE — one number, one owner: the record, not the launcher.

The launcher held three literals while a record under ``measure/`` held the truth:
``HARNESS_PIN`` (generation 4, digest ``fa6fd8cc``) against a generation-5 record, a
10-cell ``CELLS`` tuple against a 16-cell promotion, and ``3219`` in four arithmetic
sites against a ledger that says 3,192 (cap 4,320). Every test here is a guard that
the launcher OBEYS the record — including the opposite defect, a launcher that
silently follows any record.

Offline by construction: every launch below is ``--dry-run``, which cell.py answers
by printing its WOULD-REFUSE lines and returning before the runner exists
(cell.py:1956-2009). The zero-network test proves that on the launcher's own path.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import socket
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(ENG))
TOOLS = os.path.join(ENG, "tools")
# RUN_A_STAR_PATH lets a REVERTED launcher be loaded without touching the tree, so the
# red half of every red->green below is the same test against the same defects.
LAUNCHER = os.environ.get("RUN_A_STAR_PATH") or os.path.join(TOOLS, "run_a_star.py")
PIN_RECORD = os.path.join(ENG, "measure", "HARNESS-PIN.json")
GRID_RECORD = os.path.join(ENG, "measure", "GRID-PARAMS.json")
PY = os.path.abspath(sys.executable)

PRICE_RE = re.compile(r"PRICE source=(\S+) price_total=(\d+) .*?remaining=(\d+) "
                      r"remaining_basis=(\S+)")
END_RE = re.compile(r"DRY END cells=(\d+) refused=(\d+)")


# --------------------------------------------------------------------------- helpers

def load_launcher(**env):
    """Import the launcher by path, with the record hooks set BEFORE import.

    Both hooks (``RUN_A_STAR_PIN``, ``RUN_A_STAR_GRID``) are read at import time, so
    a refusal happened already by the time the module object exists.
    """
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update({k: v for k, v in env.items() if v is not None})
    try:
        spec = importlib.util.spec_from_file_location(
            "run_a_star_%d" % len(os.listdir(os.path.dirname(__file__))), LAUNCHER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run(argv, launcher=LAUNCHER, env=None):
    e = os.environ.copy()
    e.pop("CELL_RUNNER_PATH", None)
    e.pop("RUN_A_STAR_PIN", None)
    e.pop("RUN_A_STAR_GRID", None)
    e.update(env or {})
    return subprocess.run([PY, launcher] + argv, cwd=ROOT, env=e,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def tmp_pin(tmp_path, **over):
    rec = json.load(open(PIN_RECORD, encoding="utf-8"))
    rec.update(over)
    p = tmp_path / "HARNESS-PIN.json"
    p.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return str(p)


def tmp_grid(tmp_path, mutate):
    rec = json.load(open(GRID_RECORD, encoding="utf-8"))
    mutate(rec)
    p = tmp_path / "GRID-PARAMS.json"
    p.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return str(p)


# ------------------------------------------------------------------------ 1. the pin

def test_real_pin_lets_the_launcher_proceed():
    """Current record ⇒ the launcher proceeds and the digest it carries IS the record's."""
    ra = load_launcher()
    rec = json.load(open(PIN_RECORD, encoding="utf-8"))
    assert ra.PIN_ABORT is None, ra.PIN_ABORT
    assert ra.HARNESS_PIN == rec["harness_sha256"]
    assert ra.PIN_GENERATION == rec["generation"]
    assert ra.pinned_digest() == rec["harness_sha256"]
    assert rec["harness_sha256"] in ra.cell_argv("pointer-stable", 1)


def test_wrong_digest_in_a_tmp_record_aborts_naming_both(tmp_path):
    """A record whose digest moved is a refusal, and both digests are on the line."""
    rec = json.load(open(PIN_RECORD, encoding="utf-8"))
    wrong = "0" * 64
    p = tmp_pin(tmp_path, harness_sha256=wrong)
    proc = run(["--dry-run", "--cell", "1"], env={"RUN_A_STAR_PIN": p})
    out = proc.stdout
    assert proc.returncode != 0, out[-2000:]
    assert "HARNESS-PIN record disagrees with the launcher" in out, out[-2000:]
    assert wrong in out, "the record's (wrong) digest is not named: %s" % out[-2000:]
    assert rec["harness_sha256"] in out, (
        "the launcher's signed-off digest is not named: %s" % out[-2000:])
    assert "DRY END" not in out, "a refused pin must reach no cell at all"


def test_pin_refusal_launches_no_cell_and_opens_no_socket(tmp_path, monkeypatch):
    """The pin gate fires BEFORE the first subprocess: nothing is spawned, no socket."""
    wrong = tmp_pin(tmp_path, harness_sha256="f" * 64)
    ra = load_launcher(RUN_A_STAR_PIN=wrong)
    popped, sockets = [], []
    real_run = subprocess.run
    monkeypatch.setattr(ra.subprocess, "run",
                        lambda argv, **kw: popped.append(argv) or real_run(
                            [PY, "-c", "print('would_send_total=48')"], **kw))
    monkeypatch.setattr(socket, "socket",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a socket"))
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a connection"))
    monkeypatch.setattr(sys, "argv", [LAUNCHER, "--dry-run", "--cell", "1"])
    with pytest.raises(SystemExit) as exc:
        ra.main()
    assert "HARNESS-PIN record disagrees" in str(exc.value), exc.value
    assert popped == [], "a refused pin launched %d subprocess(es): %r" % (len(popped), popped)
    assert sockets == []


# ---------------------------------------------------------------------- 2. the cells

def test_cell_plan_is_the_promotion_not_a_literal():
    """16 cells, 6/6/2/2, derived from the record's shape.arms."""
    ra = load_launcher()
    assert len(ra.CELLS) == 16, ra.CELLS
    assert ra.CELLS == ra.plan_cells(ra.grid_record())
    counts = {}
    for arm, _rep in ra.CELLS:
        counts[arm] = counts.get(arm, 0) + 1
    assert counts == {"pointer-stable": 6, "transcript-grow": 6,
                      "transcript-compact": 2, "lease-reopen": 2}, counts
    assert [r for _a, r in ra.CELLS if _a == "pointer-stable"] == [1, 2, 3, 4, 5, 6]
    rec = json.load(open(GRID_RECORD, encoding="utf-8"))
    assert rec["shape"]["arms"] == counts


def test_dry_run_prints_sixteen_cells(tmp_path):
    proc = run(["--dry-run", "--cell", "1"])
    m = END_RE.search(proc.stdout)
    assert m, proc.stdout[-2000:]
    assert proc.returncode == 0, proc.stdout[-2000:]
    # --cell 1 previews one cell; the PLAN is what must read 16.
    plan = run(["--dry-run", "--cell", "99"])
    assert plan.returncode != 0 and "1..16" in plan.stdout, plan.stdout[-800:]


def test_cells_regression_to_ten_is_refused(tmp_path):
    """red→green: the old 3/3/2/2 data edit cannot silently launch 10 cells."""
    src = open(LAUNCHER, encoding="utf-8").read()
    good = ('SHAPE_EXPECTATION = (("pointer-stable", 6), ("transcript-grow", 6),\n'
            '                     ("transcript-compact", 2), ("lease-reopen", 2))')
    reverted = ('SHAPE_EXPECTATION = (("pointer-stable", 3), ("transcript-grow", 3),\n'
                '                     ("transcript-compact", 2), ("lease-reopen", 2))')
    assert src.count(good) == 1, "the signed-off promotion is not where this test expects"
    copy = tmp_path / "run_a_star_10cells.py"
    copy.write_text(src.replace(good, reverted), encoding="utf-8")
    # RED: ten cells would have launched. GREEN: the record disagrees and it refuses.
    proc = run(["--dry-run", "--cell", "1"], launcher=str(copy))
    assert proc.returncode != 0, (
        "a 10-cell launcher ran against a 16-cell record:\n%s" % proc.stdout[-2000:])
    assert "shape disagrees with the launcher's signed-off promotion" in proc.stdout, (
        proc.stdout[-2000:])
    assert "DRY END" not in proc.stdout


# ---------------------------------------------------------------------- 3. the price

def test_dry_run_prints_the_records_price(tmp_path):
    proc = run(["--dry-run", "--cell", "1"])
    lines = [ln for ln in proc.stdout.splitlines() if " PRICE " in ln]
    assert lines, proc.stdout[-2000:]
    m = PRICE_RE.search(lines[-1])
    assert m, "unparseable price line: %r" % lines[-1]
    rec = json.load(open(GRID_RECORD, encoding="utf-8"))
    assert int(m.group(2)) == rec["price"]["total"] == 1056, lines[-1]
    assert os.path.basename(m.group(1)) == "GRID-PARAMS.json", lines[-1]
    # it is printed BESIDE the remaining figure, and names its basis
    assert int(m.group(3)) == rec["price"]["remaining_before"] == 3192, lines[-1]
    assert m.group(4).startswith("ledger"), lines[-1]
    assert "price_approved=false" in lines[-1], lines[-1]


def test_missing_price_field_refuses_by_name(tmp_path):
    """A record without price.total is a NAMED refusal, never a blank line."""
    def drop(rec):
        del rec["price"]["total"]
    p = tmp_grid(tmp_path, drop)
    proc = run(["--dry-run", "--cell", "1"], env={"RUN_A_STAR_GRID": p})
    assert proc.returncode != 0, proc.stdout[-2000:]
    assert "GRID-PARAMS price.total MISSING" in proc.stdout, proc.stdout[-2000:]
    assert "DRY END" not in proc.stdout
    assert "PRICE " not in proc.stdout, "a blank price line was printed anyway"


# ------------------------------------------------------------------ 4. the remaining

def test_remaining_comes_from_the_ledger_not_3219():
    """3,219 was the pre-rebuild total; the records say 3,192 (cap 4,320)."""
    ra = load_launcher()
    rem, basis, cap = ra.remaining_basis()
    assert rem == 3192, rem
    assert basis.startswith("ledger"), basis
    assert cap == 4320, cap
    src = open(LAUNCHER, encoding="utf-8").read()
    assert "3219" not in src, "the pre-rebuild total is still baked into the launcher"
    for site in ('remaining = base_remaining - (spend() - spent0)',
                 'rec["remaining_after"] = base_remaining - (spend() - spent0)'):
        assert src.count(site) == 1, "arithmetic site missing: %r" % site


def test_disagreeing_ledger_records_are_a_refusal(tmp_path, monkeypatch):
    """Two records that disagree are refused, not averaged or picked."""
    ra = load_launcher()
    bad = tmp_path / "baseline.json"
    bad.write_text(json.dumps({"remaining": 3219, "cap": 4320}), encoding="utf-8")
    monkeypatch.setattr(ra, "LEDGER_FROZEN", str(bad))
    with pytest.raises(SystemExit) as exc:
        ra.remaining_basis()
    assert "disagree on `remaining`" in str(exc.value), exc.value
    assert "3219" in str(exc.value) and "3192" in str(exc.value), exc.value


# ------------------------------------------------------------------- 5. zero network

def test_dry_run_opens_no_socket_and_launches_no_live_cell(monkeypatch):
    """The dry run's own path: no socket, and every child carries --dry-run.

    A live cell.py (no --dry-run) is the only thing here that could reach the
    endpoint, so "no live child" is the launcher-side half of the offline proof.
    """
    ra = load_launcher()
    spawned, sockets = [], []
    real_run = subprocess.run

    def record(argv, **kw):
        spawned.append(list(argv))
        return real_run(argv[:1] + ["-c", "print('dry-run G1 allow; "
                                    "dry-run G2 allow; dry-run G3 allow')"], **kw)

    monkeypatch.setattr(ra.subprocess, "run", record)
    monkeypatch.setattr(socket, "socket",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a socket"))
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: sockets.append(a) or pytest.fail(
                            "the launcher opened a connection"))
    monkeypatch.setattr(sys, "argv", [LAUNCHER, "--dry-run", "--cell", "1"])
    rc = ra.main()
    assert rc == 0, "dry run exited %r" % rc
    assert sockets == [], "sockets opened: %r" % (sockets,)
    assert spawned, "the recorder saw no child at all — the test proved nothing"
    for argv in spawned:
        assert "--dry-run" in argv, "a LIVE cell.py was launched: %r" % (argv,)
    assert not any("cell.py" in a and "--dry-run" not in argv
                   for argv in spawned for a in argv)


def test_warmup_is_never_called_by_a_dry_run(monkeypatch):
    """The one function that could reach the endpoint directly."""
    ra = load_launcher()
    hit = []
    monkeypatch.setattr(ra, "warmup", lambda arm: hit.append(arm))
    monkeypatch.setattr(ra.subprocess, "run",
                        lambda argv, **kw: subprocess.CompletedProcess(
                            argv, 0, stdout="dry-run G1 allow\n", stderr=""))
    monkeypatch.setattr(sys, "argv", [LAUNCHER, "--dry-run", "--cell", "1"])
    assert ra.main() == 0
    assert hit == [], "a dry run warmed up the endpoint: %r" % (hit,)
