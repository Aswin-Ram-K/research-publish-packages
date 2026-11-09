#!/usr/bin/env python3
"""test_cell_gates.py - offline tests for the G1/G2/G3 preflight gate chain.

WHY THIS EXISTS: three offline cards built the conditions under which a live cell may
spend a request (the ledger's cap, the calibrated projection, the frozen PARM-1
prereg). Each proved itself alone; nothing joined them. These tests prove the JOIN:
every gate's ALLOW and REFUSE path, the one refusal format, the pinned exit codes, and
that `--dry-run` prints the decision without touching a socket.

Every test is OFFLINE. No request is sent, no endpoint is contacted, and the live
runner is replaced by a stub that only records that it was invoked.
"""
import contextlib
import glob
import importlib.util
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PTR_ENGINE = os.path.dirname(LONGRUN)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))
CELL = os.path.join(LONGRUN, "cell.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
REAL_LEDGER = os.path.join(PTR_ENGINE, "measure", "REQUEST-LEDGER.json")
REAL_PROJECTION = os.path.join(PTR_ENGINE, "measure", "PROJECTION.json")
REAL_PREREG = os.path.join(PTR_ENGINE, "measure", "PREREG-ARM-RUN.json")
ARM = "transcript-grow"          # a real arm of run_longrun.py (preflight validates it)
PY = sys.executable


# ------------------------------------------------------------------- fixtures
def _write_json(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    return path


def _copy_real(src, tmp, name):
    dst = os.path.join(tmp, name)
    shutil.copyfile(src, dst)
    return dst


def _fake_runner(tmp):
    """A runner stub: honours --dry-run, otherwise records that it was invoked."""
    marker = os.path.join(tmp, "runner-invoked.marker")
    path = os.path.join(tmp, "fake_runner.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "import os, sys\n"
            "if '--dry-run' in sys.argv:\n"
            "    print('  would_send_total=48')\n"
            "    sys.exit(0)\n"
            "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
            "sys.exit(0)\n")
    return path, marker


def _fake_ledger(tmp, cap, spent, reserve=0, name="ledger.json"):
    """An artefact shaped exactly like REQUEST-LEDGER.json, plus the rows it counts."""
    rows = os.path.join(tmp, "rows-fake-ledger.jsonl")
    with open(rows, "w", encoding="utf-8") as fh:
        for i in range(spent):
            fh.write(json.dumps({"kind": "turn", "turn": i + 1,
                                 "prompt_tokens": 100}) + "\n")
    doc = {
        "unit": "REQUEST-LEDGER", "rule": "test fixture",
        "counting": {}, "total": {"files": 1, "rows": spent, "requests": spent,
                                  "assumed_billed": 0},
        "budget": {"cap": cap, "reserve": reserve, "headroom": cap - reserve,
                   "spent": spent, "would_spend": 0, "projected": spent,
                   "remaining": cap - reserve - spent, "within_budget": True},
        "files": [{"file": rows, "sha256": "0" * 64, "rows": spent, "requests": spent,
                   "assumed_billed": 0, "first_ts": None, "last_ts": None}],
        "suppressed": [],
    }
    return _write_json(os.path.join(tmp, name), doc), rows


def _env(tmp, ledger, runner, marker, projection=None, prereg=None):
    e = dict(os.environ)
    e.update({
        "CELL_LEDGER_ARTEFACT": ledger,
        "CELL_PROJECTION_ARTEFACT": projection or REAL_PROJECTION,
        "CELL_PREREG_ARTEFACT": prereg or REAL_PREREG,
        "CELL_RUNNER_PATH": runner,
        "CELL_MARKER": marker,
    })
    return e


def _run(argv, env, cell=CELL, cwd=None, timeout=180):
    proc = subprocess.run([PY, cell] + list(argv), capture_output=True, text=True,
                          env=env, cwd=cwd or LONGRUN, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def _live_argv(tmp, extra):
    out = os.path.join(tmp, "out")
    os.makedirs(out, exist_ok=True)
    return (["--arm", ARM, "--fixture", FIXTURE, "--turns", "48", "--reps", "1",
             "--budget", "1000", "--out-dir", out, "--no-cell-handoff"] + list(extra))


# --------------------------------------------------------------------- checks
def check_g1_refuses(tmp, cell=CELL):
    """G1 refuses (exit 4) a cell that does not fit the ledger's remaining quota.

    The ledger's cap is 120 with 100 already spent; a 48-turn cell needs 48 requests
    plus its fetch follow-up allowance, so it does not fit and must not send.
    """
    ledger, _rows = _fake_ledger(tmp, cap=120, spent=100)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, []), _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 4, "expected exit 4 (the ledger's cap refusal), got %d\n%s" % (rc, log)
    assert "G1 ledger-cap REFUSED" in log, log[-3000:]
    assert "shortfall" in log, "the refusal does not name the shortfall:\n%s" % log[-3000:]
    assert "--fetch-followup-allowance" in log, "no actionable flag in the refusal"
    assert os.path.basename(ledger) in log, "the refusal does not name the artefact"
    assert not os.path.exists(marker), "the runner was invoked past a G1 refusal"


def check_g1_allows(tmp, cell=CELL):
    """G1 allows a cell with headroom and the chain proceeds to the runner."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=100)
    runner, marker = _fake_runner(tmp)
    # G3 has no default claim: a live path must name one. H2 at n=48 is admissible.
    rc, log = _run(_live_argv(tmp, ["--hypothesis", "H2"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert os.path.exists(marker), ("G1 refused a cell that fits the quota; the runner "
                                    "was never invoked\n%s" % log[-3000:])
    assert rc != 4, "rc=%d is the ledger's refusal code on a cell with headroom" % rc


def check_g2_refuses(tmp, cell=CELL):
    """G2 refuses (exit 8) a projection past --max-wall, quoting both second counts."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, ["--projected-turn-wall", "180"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 8, "expected exit 8 (projection refusal), got %d\n%s" % (rc, log)
    assert "8640" in log and "3600" in log, (
        "the refusal does not quote projected and allowed seconds:\n%s" % log[-3000:])
    assert "G2 projection REFUSED" in log, log[-3000:]
    assert not os.path.exists(marker), "the runner was invoked past a G2 refusal"


def check_g2_allows(tmp, cell=CELL):
    """G2 allows a cell inside --max-wall."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, ["--hypothesis", "H2"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc != 8, "48 turns x 60 s = 2880 s must be admitted, got exit 8\n%s" % log[-3000:]
    assert os.path.exists(marker), "the runner was never invoked after an admission"


def check_g3_refuses_h1_at_48(tmp, cell=CELL):
    """G3 refuses (exit 12) an H1 claim at n=48, naming PARM-1's 60."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, ["--hypothesis", "H1"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 12, "expected exit 12 (prereg refusal), got %d\n%s" % (rc, log)
    assert "G3 prereg REFUSED" in log, log[-3000:]
    assert "n >= 60" in log, "the refusal does not name the 60-turn minimum:\n%s" % log[-3000:]
    assert "--hypothesis" in log, "no actionable flag in the refusal"
    assert not os.path.exists(marker), "the runner was invoked past a G3 refusal"


def check_g3_allows_h1_at_60(tmp, cell=CELL):
    """G3 allows an H1 claim at exactly n=60 (the estimator's own minimum)."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    argv = _live_argv(tmp, ["--hypothesis", "H1", "--turns", "60"])
    _rc, log = _run(argv, _env(tmp, ledger, runner, marker), cell=cell)
    assert os.path.exists(marker), ("an H1 claim at n=60 is admissible but the runner "
                                    "was never invoked\n%s" % log[-3000:])
    assert "G3 prereg REFUSED" not in log, "G3 refused an admissible H1 cell"


def check_g3_refuses_no_hypothesis(tmp, cell=CELL):
    """An explicit `--hypothesis none` is refused by G3 with its own code 12."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, ["--hypothesis", "none"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 12, "expected exit 12 (explicit none), got %d\n%s" % (rc, log)
    assert "G3 prereg REFUSED" in log, log[-3000:]
    assert "silence is not a claim" in log, log[-3000:]
    assert not os.path.exists(marker), "the runner was invoked with no claim declared"


def check_g3_refuses_silence(tmp, cell=CELL):
    """ABSENT --hypothesis is refused (exit 12): silence is not a claim.

    GATE-CHAIN-FIX D2: the old `_declared_hypothesis` fell back to PARM-1's primary (H2),
    so this path ALLOWED the run and the no-hypothesis branch was unreachable.
    """
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, []), _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 12, ("expected exit 12 (no hypothesis declared), got %d\n%s"
                      % (rc, log))
    assert "G3 prereg REFUSED" in log, log[-3000:]
    assert "hypothesis=none declared" in log, log[-3000:]
    assert "silence is not a claim" in log, log[-3000:]
    assert not os.path.exists(marker), "the runner was invoked with no claim declared"


def check_g3_refuses_unknown_hypothesis(tmp, cell=CELL):
    """An unknown --hypothesis is refused by G3 with exit 12, naming the unknown name."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, ["--hypothesis", "H9"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 12, "expected exit 12 (unknown hypothesis), got %d\n%s" % (rc, log)
    assert "G3 prereg REFUSED" in log, log[-3000:]
    assert "does not define hypothesis" in log, log[-3000:]
    assert not os.path.exists(marker), "the runner was invoked with an unknown hypothesis"


def check_g3_allows_h1_at_144(tmp, cell=CELL):
    """An H1 claim at n=144 is well past the 60 minimum, so G3 allows and the run starts."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    argv = _live_argv(tmp, ["--hypothesis", "H1", "--turns", "144"])
    _rc, log = _run(argv, _env(tmp, ledger, runner, marker), cell=cell)
    assert os.path.exists(marker), ("an H1 claim at n=144 is admissible but the runner "
                                    "was never invoked\n%s" % log[-3000:])
    assert "G3 prereg REFUSED" not in log, "G3 refused an admissible H1 cell"


def check_g2_refuses_nonpositive_max_wall(tmp, value, cell=CELL):
    """A ceiling of zero or less is a REFUSAL (exit 8), not a way to switch G2 off.

    GATE-CHAIN-FIX D1: the old verdict `not (max_wall > 0 and projected > max_wall)`
    allowed `--max-wall 0` and `--max-wall -1`, so a 2880 s projection started a live run.
    Neither the help text nor docs/GATE-CHAIN.md declares an "unlimited" mode.
    """
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    # H2 is declared so the ONLY thing that can refuse this cell is the ceiling itself.
    rc, log = _run(_live_argv(tmp, ["--max-wall", str(value), "--hypothesis", "H2"]),
                   _env(tmp, ledger, runner, marker), cell=cell)
    assert rc == 8, ("expected exit 8 for --max-wall %s (a ceiling of zero or less is not "
                     "'unlimited'), got %d\n%s" % (value, rc, log))
    assert "G2 projection REFUSED" in log, log[-3000:]
    assert "--max-wall" in log and str(value) in log, (
        "the refusal does not name the value it was given:\n%s" % log[-3000:])
    assert "unlimited" in log, (
        "the refusal must say that zero/negative is not an 'unlimited' mode:\n%s"
        % log[-3000:])
    assert not os.path.exists(marker), "the runner was invoked with --max-wall %s" % value


def check_repo_root_import(tmp, cell=CELL):
    """cell.py must import with cwd = the repo root and no PYTHONPATH help.

    GATE-CHAIN-FIX D4: a top-level `import exit_codes` made the documented command
    `python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p
    'test_cell_gates.py'` (run from the repo root) die with ModuleNotFoundError. A test
    green only under an undocumented invocation is red, so this runs the module from the
    root with PYTHONPATH scrubbed.
    """
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    proc = subprocess.run([PY, cell, "--help"], capture_output=True, text=True,
                          env=env, cwd=ROOT, timeout=180)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, ("cell.py does not run from the repo root (a sibling "
                                  "import depends on cwd/PYTHONPATH)\n%s" % out[-3000:])
    assert "ModuleNotFoundError" not in out, out[-3000:]


def check_dry_run_touches_no_network(tmp):
    """--dry-run prints all three verdicts and exits 0 with no socket and no runner.

    The module is imported in-process so the transport can be replaced by a tripwire:
    any socket, HTTP connection or subprocess raises instead of running.
    """
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp)
    os.environ.update(_env(tmp, ledger, runner, marker))

    spec = importlib.util.spec_from_file_location("cell_gates_under_test", CELL)
    cell = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cell)

    import http.client
    import urllib.request

    def boom(*a, **k):
        raise AssertionError("--dry-run attempted network/subprocess I/O: %r" % (a,))

    saved = (socket.socket, socket.create_connection, http.client.HTTPConnection,
             urllib.request.urlopen, subprocess.run, subprocess.Popen)
    buf = io.StringIO()
    try:
        socket.socket = socket.create_connection = boom
        http.client.HTTPConnection = boom
        urllib.request.urlopen = boom
        subprocess.run = subprocess.Popen = boom
        with contextlib.redirect_stdout(buf):
            rc = cell.main(["--arm", ARM, "--fixture", FIXTURE, "--turns", "60",
                            "--reps", "1", "--dry-run", "--no-cell-handoff",
                            "--out-dir", os.path.join(tmp, "dry")])
    finally:
        (socket.socket, socket.create_connection, http.client.HTTPConnection,
         urllib.request.urlopen, subprocess.run, subprocess.Popen) = saved

    log = buf.getvalue()
    assert rc == 0, "dry run must exit 0, got %r\n%s" % (rc, log)
    for gate in ("G1", "G2", "G3"):
        assert gate in log, "dry run did not print %s's verdict:\n%s" % (gate, log)
    assert "requests" in log and " s of " in log, (
        "the three verdict lines do not carry their numbers:\n%s" % log)
    assert "nothing was sent" in log, log
    assert not os.path.exists(marker), "a dry run invoked the runner"
    assert not glob.glob(os.path.join(tmp, "dry", "rows-cell-*.jsonl")), \
        "a dry run wrote a row file"


# ------------------------------------------------------------- red -> green
def check_g2_zero_max_wall(tmp, cell=CELL):
    return check_g2_refuses_nonpositive_max_wall(tmp, 0, cell=cell)


def check_g2_negative_max_wall(tmp, cell=CELL):
    return check_g2_refuses_nonpositive_max_wall(tmp, -1, cell=cell)


RED_GREEN = [
    # (label, check, [(old source fragment, sabotaged replacement), ...])
    ("G1", check_g1_refuses,
     [('"gate": GATE_LEDGER, "what": "ledger-cap", "ok": bool(b["within_budget"]),',
       '"gate": GATE_LEDGER, "what": "ledger-cap", "ok": True,  # SABOTAGE(G1)')]),
    ("G2", check_g2_refuses,
     [('"ok": (max_wall > 0 and projected <= max_wall),',
       '"ok": True,  # SABOTAGE(G2)')]),
    ("G2-max-wall", check_g2_zero_max_wall,
     [('"ok": (max_wall > 0 and projected <= max_wall),',
       '"ok": not (max_wall > 0 and projected > max_wall),  # SABOTAGE(G2-np)'),
      ("    if not (max_wall > 0):", "    if False:  # SABOTAGE(G2-np-branch)")]),
    ("G2-max-wall-negative", check_g2_negative_max_wall,
     [('"ok": (max_wall > 0 and projected <= max_wall),',
       '"ok": not (max_wall > 0 and projected > max_wall),  # SABOTAGE(G2-np)'),
      ("    if not (max_wall > 0):", "    if False:  # SABOTAGE(G2-np-branch)")]),
    ("G3", check_g3_refuses_h1_at_48,
     [("        ok = n >= min_n\n        verdict[\"thresholds\"] = {\n            \"estimator\":",
       "        ok = True  # SABOTAGE(G3)\n        verdict[\"thresholds\"] = {\n"
       "            \"estimator\":")]),
    # CLAIM-ROW-STAMP: G3-silence now points at the NEW resolver. The old anchor
    # restored `_declared_hypothesis` -> "H2" and drifted when that function was
    # deleted; this one restores the old DEFAULT SHAPE inside `_resolved_claim`:
    # a refusal is turned into a comparable H2 record, i.e. silence declares a claim.
    ("G3-silence", check_g3_refuses_silence,
     [("            _CLAIM_CACHE[key] = exc",
       '            _CLAIM_CACHE[key] = mod.ClaimRecord("hypothesis", "H2", True)  '
       '# SABOTAGE(G3-default restored)')]),
    ("G3-code", check_g3_refuses_h1_at_48,
     [('"3c/7 G3 prereg gate", 12)', '"3c/7 G3 prereg gate", 2)  # SABOTAGE(G3-code)')]),
]


class CellGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="cell-gates-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _case(self, name):
        path = os.path.join(self.tmp, "case-" + name)
        os.makedirs(path, exist_ok=True)
        return path

    # ---- G1 -----------------------------------------------------------------
    def test_g1_refuses(self):
        check_g1_refuses(self._case("g1-refuse"))

    def test_g1_allows(self):
        check_g1_allows(self._case("g1-allow"))

    # ---- G2 -----------------------------------------------------------------
    def test_g2_refuses(self):
        check_g2_refuses(self._case("g2-refuse"))

    def test_g2_allows(self):
        check_g2_allows(self._case("g2-allow"))

    # ---- G3 -----------------------------------------------------------------
    def test_g3_refuses_h1_at_48(self):
        check_g3_refuses_h1_at_48(self._case("g3-h1-48"))

    def test_g3_allows_h1_at_60(self):
        check_g3_allows_h1_at_60(self._case("g3-h1-60"))

    def test_g3_refuses_no_hypothesis(self):
        check_g3_refuses_no_hypothesis(self._case("g3-none"))

    def test_g3_refuses_silence(self):
        check_g3_refuses_silence(self._case("g3-silence"))

    def test_g3_refuses_unknown_hypothesis(self):
        check_g3_refuses_unknown_hypothesis(self._case("g3-unknown"))

    def test_g3_allows_h1_at_144(self):
        check_g3_allows_h1_at_144(self._case("g3-h1-144"))

    # ---- G2's ceiling must be positive (D1) ---------------------------------
    def test_g2_refuses_zero_max_wall(self):
        check_g2_refuses_nonpositive_max_wall(self._case("g2-zero"), 0)

    def test_g2_refuses_negative_max_wall(self):
        check_g2_refuses_nonpositive_max_wall(self._case("g2-negative"), -1)

    # ---- the stated command must work from the repo root (D4) ----------------
    def test_repo_root_import(self):
        check_repo_root_import(self._case("repo-root"))

    # ---- dry run ------------------------------------------------------------
    def test_dry_run_touches_no_network(self):
        check_dry_run_touches_no_network(self._case("dry-run"))

    # ---- red -> green -------------------------------------------------------
    def test_red_green_every_gate(self):
        """Neuter one gate in cell.py, show the same check goes red, then restore.

        The mutant is the conductor itself with ONE gate's decision forced to allow, so
        the red run exercises the real code path (not a stub), and the green run that
        follows restores the exact original bytes.
        """
        with open(CELL, encoding="utf-8") as fh:
            source = fh.read()
        try:
            for label, check, pairs in RED_GREEN:
                with self.subTest(gate=label):
                    mutant = source
                    for old, new in pairs:
                        self.assertIn(old, mutant, "mutation anchor drifted for %s" % label)
                        mutant = mutant.replace(old, new, 1)
                    with open(CELL, "w", encoding="utf-8") as fh:
                        fh.write(mutant)
                    try:
                        check(self._case("red-" + label), CELL)
                    except AssertionError as exc:
                        # A red for the WRONG reason (e.g. a broken harness path) proves
                        # nothing: the failure must be the gate's own exit assertion.
                        self.assertIn("expected exit", str(exc),
                                      "gate %s went red for the wrong reason: %s"
                                      % (label, str(exc)[:400]))
                    else:
                        self.fail("gate %s is not load-bearing: the check passed against "
                                  "a sabotaged conductor" % label)
                    finally:
                        with open(CELL, "w", encoding="utf-8") as fh:
                            fh.write(source)
        finally:
            with open(CELL, "w", encoding="utf-8") as fh:
                fh.write(source)
        with open(CELL, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), source,
                             "cell.py was not restored after the red run")


if __name__ == "__main__":
    unittest.main(verbosity=2)
