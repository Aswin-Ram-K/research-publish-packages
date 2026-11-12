#!/usr/bin/env python3
"""test_cell.py - offline tests for the ONE-COMMAND-PER-CELL conductor.

Every test is OFFLINE: no request is sent, no row is written by the runner, and
the network is never touched. Each guard is checked twice: once against the real
`cell.py` (green) and once against a mutant of the real file with exactly that
guard removed (red). The mutation is a string edit of `cell.py`, so the red run
exercises the same code path with one refusal turned off - not a hand-written
stub that proves nothing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
CELL = os.path.join(LONGRUN, "cell.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"  # a real arm of run_longrun.py (preflight validates it)

sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(os.path.dirname(LONGRUN), "tools"))

PY = sys.executable


# --------------------------------------------------------------- run helpers
def _run_cell(cell_path, argv, env=None, cwd=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    proc = subprocess.run([PY, cell_path] + argv, capture_output=True, text=True,
                          env=e, cwd=cwd or LONGRUN)
    return proc.returncode, proc.stdout + proc.stderr


def _records(tmp):
    if not os.path.isdir(tmp):
        return []
    return sorted(n for n in os.listdir(tmp)
                  if n.startswith("cell-") and ".grade-v5." not in n
                  and ".analysis." not in n
                  and (n.endswith(".json") or n.endswith(".md")))


def _fixture_variant(tmp, name, mutate):
    with open(FIXTURE, encoding="utf-8") as fh:
        doc = json.load(fh)
    mutate(doc)
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return path


def _truth():
    import grade_v5
    with open(FIXTURE, encoding="utf-8") as fh:
        return grade_v5.derive_truth(json.load(fh))


def _contract_line(tr):
    kind, exp = tr["kind"], tr["expected"]
    if kind == "NUM":
        return "ANSWER: NUM %d" % int(exp)
    if kind == "CALL":
        kw = ", ".join("%s=%s" % (k, v) for k, v in sorted(exp["kwargs"].items()))
        return "ANSWER: CALL %s(%s)" % (exp["callee"], kw)
    if kind == "NONE":
        return "ANSWER: NONE"
    return "ANSWER: TEXT %s" % (exp,)


def _rows(path, n_turns=64, checkpoints=True):
    """A synthetic row file: real checkpoint contract lines + n timed turns.

    Shaped exactly like the runner's rows (arm/turn/ttft_ms/ttft_source/content)
    so the conductor, the grader and the analyzer all parse it unchanged.
    """
    by_turn = {}
    if checkpoints:
        for tr in _truth():
            by_turn[tr["turn"]] = {
                "arm": ARM, "turn": tr["turn"], "ttft_ms": 120.0,
                "ttft_source": "stream", "content": _contract_line(tr)}
    rows = []
    for t in range(1, n_turns + 1):
        row = by_turn.get(t) or {"arm": ARM, "turn": t,
                                 "ttft_ms": 100.0 + 13.7 * t,
                                 "ttft_source": "stream", "content": ""}
        row = dict(row)
        row["passed"] = (t % 7 != 0)
        if row.get("content", "").startswith("ANSWER:"):
            row["passed"] = True
        rows.append(row)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return path


def _base_argv(rows, out, fixture=None):
    return ["--arm", ARM, "--fixture", fixture or FIXTURE, "--offline", rows,
            "--out-dir", out, "--no-cell-handoff"]


# ------------------------------------------------------------------- checks
def check_offline_records(cell_path, tmp):
    """(a) --offline produces JSON + markdown, exit 0, interval and n present."""
    out = os.path.join(tmp, "a")
    rows = _rows(os.path.join(tmp, "a.jsonl"))
    rc, log = _run_cell(cell_path, _base_argv(rows, out))
    assert rc == 0, "expected exit 0, got %d\n%s" % (rc, log)
    names = _records(out)
    assert any(n.endswith(".json") for n in names), "no JSON record: %s" % names
    md = [n for n in names if n.endswith(".md")]
    assert md, "no markdown record: %s" % names
    with open(os.path.join(out, md[0]), encoding="utf-8") as fh:
        text = fh.read()
    assert "ttft_p95 n=" in text, "markdown has no p95 with n:\n%s" % text[-2000:]
    assert "[" in text and "]" in text, "markdown has no interval"
    assert "wilson95 n=" in text, "markdown has no Wilson interval for accuracy"
    with open(os.path.join(out, [n for n in names if n.endswith(".json")][0])) as fh:
        doc = json.load(fh)
    assert doc["offline"] is True and doc["requests_used"] == 0
    # The record must carry one digest per MEASUREMENT INPUT: every entry of cell.py's
    # HARNESS_FILES plus the fixture.  Pinned by name, not by count, so an accidental
    # removal still fails while a deliberate addition (generation 9 added arm_cd.py and
    # ptr_engine/layers.py) does not have to be retyped here.
    import cell as _cell
    expected = {name for _path, name in _cell.HARNESS_FILES} | {"fixture"}
    assert set(doc["harness"]["files"]) == expected, (
        "harness record names %r, cell.HARNESS_FILES+fixture is %r"
        % (sorted(doc["harness"]["files"]), sorted(expected)))
    assert {"arm_cd.py", "ptr_engine/layers.py"} <= set(doc["harness"]["files"])
    assert doc["harness"]["harness_sha256"]


def check_missing_system_prompt(cell_path, tmp):
    """(b) a fixture without system_prompt refuses (2) and names the key."""
    fx = _fixture_variant(tmp, "no-sp.json", lambda d: d.pop("system_prompt"))
    rows = _rows(os.path.join(tmp, "b.jsonl"), n_turns=3, checkpoints=False)
    rc, log = _run_cell(cell_path, _base_argv(rows, os.path.join(tmp, "b"), fixture=fx))
    assert rc == 2, "expected exit 2, got %d\n%s" % (rc, log)
    assert "system_prompt" in log, "refusal does not name 'system_prompt':\n%s" % log
    assert "preflight" in log


def check_underivable_truth(cell_path, tmp):
    """(c) a checkpoint whose truth is not derivable refuses (2), naming it."""
    def mutate(doc):
        # a rule grade_v5 cannot derive from the source tree
        doc["checkpoints"][1]["answer_spec"]["derive"]["rule"] = "no_such_rule_zzz"
    fx = _fixture_variant(tmp, "bad-derive.json", mutate)
    rows = _rows(os.path.join(tmp, "c.jsonl"), n_turns=3, checkpoints=False)
    rc, log = _run_cell(cell_path, _base_argv(rows, os.path.join(tmp, "c"), fixture=fx))
    assert rc == 2, "expected exit 2, got %d\n%s" % (rc, log)
    assert "cp.1.t24" in log, "refusal does not name the checkpoint:\n%s" % log
    assert "derivable" in log


def check_budget_refusal(cell_path, tmp):
    """(d) a budget under would_send_total refuses (3) BEFORE any request."""
    out = os.path.join(tmp, "d")
    os.makedirs(out, exist_ok=True)
    marker = os.path.join(tmp, "d-runner-invoked.marker")
    fake = os.path.join(tmp, "fake_runner.py")
    with open(fake, "w", encoding="utf-8") as fh:
        fh.write("import sys, os\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('  would_send_total=500')\n"
                 "    sys.exit(0)\n"
                 "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
                 "sys.exit(0)\n")
    rc, log = _run_cell(cell_path,
                        ["--arm", ARM, "--fixture", FIXTURE, "--turns", "48",
                         "--reps", "1", "--budget", "100", "--out-dir", out,
                         "--no-cell-handoff"],
                        env={"CELL_RUNNER_PATH": fake, "CELL_MARKER": marker})
    assert rc == 3, "expected exit 3, got %d\n%s" % (rc, log)
    # TWO refusals can fire here and they are both correct: `--budget` (the cell's own
    # ceiling) or the PROJECT headroom, whichever is tighter. As the project spends down,
    # headroom becomes the binding one and the `--budget` message never appears — so the
    # assertion pins the invariant (a refusal that names the number) and not one branch's
    # wording. Measured 2026-11-11: headroom 307 made this a headroom refusal.
    assert "500" in log, "the dry-run's price is not named in the refusal:\n%s" % log
    assert ("exceeds --budget 100" in log) or ("exceeds headroom" in log), \
        "the refusal does not name which ceiling was exceeded:\n%s" % log
    assert not os.path.exists(marker), "the runner was invoked past --dry-run"
    assert not [n for n in os.listdir(out) if n.startswith("rows-cell-")], \
        "a row file was created before the budget check"


def check_wrong_harness(cell_path, tmp):
    """(e) a wrong --expect-harness refuses (2)."""
    rows = _rows(os.path.join(tmp, "e.jsonl"), n_turns=3, checkpoints=False)
    rc, log = _run_cell(cell_path, _base_argv(rows, os.path.join(tmp, "e"))
                        + ["--expect-harness", "0" * 64])
    assert rc == 2, "expected exit 2, got %d\n%s" % (rc, log)
    assert "harness changed mid-cell" in log
    assert "2/7 harness" in log


def check_analysis_refusal(cell_path, tmp):
    """(f) an analysis that must refuse prints the refusal; the cell still exits 0."""
    out = os.path.join(tmp, "f")
    rows = _rows(os.path.join(tmp, "f.jsonl"), n_turns=6)
    rc, log = _run_cell(cell_path, _base_argv(rows, out))
    assert rc == 0, "expected exit 0 (a refusal is a result), got %d\n%s" % (rc, log)
    names = _records(out)
    with open(os.path.join(out, [n for n in names if n.endswith(".json")][0])) as fh:
        doc = json.load(fh)
    refusals = doc["analysis"]["refusals"]
    assert any("refusing p95" in r for r in refusals), \
        "p95 refusal not recorded: %r" % (refusals,)
    assert not any(c.get("p95") for c in doc["analysis"]["checks"]), \
        "a p95 number was published despite the refusal"
    with open(os.path.join(out, [n for n in names if n.endswith(".md")][0]),
              encoding="utf-8") as fh:
        md = fh.read()
    assert "REFUSED at n=" in md and "ttft_p95" in md
    assert "ttft_p95 n=" not in md, "markdown printed a bare p95"


CHECKS = [
    ("a", check_offline_records,
     ('fh.write("\\n".join(lines) + "\\n")', 'pass  # SABOTAGE(a)')),
    ("b", check_missing_system_prompt,
     ('if not isinstance(sp, str) or not sp.strip():',
      'if False and not isinstance(sp, str):')),
    ("c", check_underivable_truth,
     ('derived = grade_v5.derive_truth(one)', 'derived = [{"x": 1}]  # SABOTAGE(c)')),
    ("d", check_budget_refusal,
     ('if required > args.budget:', 'if False:  # SABOTAGE(d)')),
    ("e", check_wrong_harness,
     ('if args.expect_harness and args.expect_harness != digest:',
      'if False:  # SABOTAGE(e)')),
    ("f", check_analysis_refusal,
     ('refusals.append("arm %s %s: %s" % (arm, key, est["refused"]))',
      'checks.append({"arm": arm, key: None})  # SABOTAGE(f)')),
]


class CellCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="cell-one-command-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _case(self, name):
        path = os.path.join(self.tmp, "case-" + name)
        os.makedirs(path, exist_ok=True)
        return path

    # (a)-(f) against the REAL conductor
    def test_a_offline_records(self):
        check_offline_records(CELL, self._case("a"))

    def test_b_missing_system_prompt(self):
        check_missing_system_prompt(CELL, self._case("b"))

    def test_c_underivable_truth(self):
        check_underivable_truth(CELL, self._case("c"))

    def test_d_budget_refusal(self):
        check_budget_refusal(CELL, self._case("d"))

    def test_e_wrong_harness(self):
        check_wrong_harness(CELL, self._case("e"))

    def test_f_analysis_refusal(self):
        check_analysis_refusal(CELL, self._case("f"))

    # red->green: the SAME check must fail when its guard is deleted from cell.py
    def test_red_green_every_guard(self):
        with open(CELL, encoding="utf-8") as fh:
            source = fh.read()
        for name, check, (old, new) in CHECKS:
            with self.subTest(guard=name):
                self.assertIn(old, source, "mutation anchor drifted for %s" % name)
                mutant = os.path.join(self.tmp, "cell-sabotage-%s.py" % name)
                with open(mutant, "w", encoding="utf-8") as fh:
                    fh.write(source.replace(old, new, 1))
                case = self._case("red-" + name)
                with self.assertRaises(AssertionError,
                                       msg="guard %s is not load-bearing: the check "
                                           "passed against a sabotaged conductor" % name):
                    check(mutant, case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
