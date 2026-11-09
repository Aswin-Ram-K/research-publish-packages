#!/usr/bin/env python3
"""PATH-REFS — the guard must bite on a wrong path, and must stay quiet on a correct one.

The point of this suite is not coverage of the scanner; it is the three red shapes that cost
this batch four corrections, and the three green shapes that would otherwise make the guard
unusable:

  RED    docs/BUDGET-SCHEDULE.md cited while the artefact lives at
         experiments/ptr-engine/measure/BUDGET-SCHEDULE.md            -> wrong_dir, --check 1
  RED    docs/does-not-exist.md, a fabricated path                    -> missing,   --check 1
  RED    tests/test_cap_gate.py cited while it lives under
         experiments/ptr-engine/longrun/tests/                       -> wrong_dir, --check 1
  GREEN  the same citation written correctly                          -> ok,        --check 0
  GREEN  "`docs/GATE-SIMPLIFY.md` does not exist" (a line naming a
         phantom as a phantom)                                       -> ignored,   --check 0
  GREEN  a finding frozen in the baseline                             -> --check 0,
         and a NEW finding appended past the baseline                -> --check 1

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_path_refs.py -q
"""

import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOL = os.environ.get(
    "PATH_REFS_TOOL", os.path.join(REPO, "experiments", "ptr-engine", "tools", "path_refs.py")
)


def load_tool():
    spec = importlib.util.spec_from_file_location("path_refs", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pr = load_tool()


def make_ws(tmp_path, docs=(), measure=(), units=(), handoffs=()):
    """Build a minimal repo-shaped tree with the scan globs present."""
    root = tmp_path
    for d in ("docs", "experiments/ptr-engine/measure", "orchestration/units",
              "orchestration/handoffs", "state/logs"):
        (root / d).mkdir(parents=True, exist_ok=True)
    for name in docs:
        (root / "docs" / name).write_text("real\n", encoding="utf-8")
    for name in measure:
        (root / "experiments" / "ptr-engine" / "measure" / name).write_text("real\n",
                                                                            encoding="utf-8")
    for name in units:
        (root / "orchestration" / "units" / name).write_text("real\n", encoding="utf-8")
    for name in handoffs:
        (root / "orchestration" / "handoffs" / name).write_text("{}\n", encoding="utf-8")
    return root


def run(root, *args):
    return subprocess.run([sys.executable, TOOL, "--root", str(root)] + list(args),
                          capture_output=True, text=True)


def findings(root, cited):
    return [f for f in pr.scan(str(root)) if f["path"] == cited]


# ------------------------------------------------------------------ RED

def test_red_wrong_dir_legal_alternate(tmp_path):
    """The BUDGET-SCHEDULE case: cited at docs/, artefact at measure/."""
    root = make_ws(tmp_path, measure=["BUDGET-SCHEDULE.md"])
    (root / "docs" / "PRICE-REPLICATION.md").write_text(
        "2. **`docs/BUDGET-SCHEDULE.md` §7** goes stale\n", encoding="utf-8")
    got = findings(root, "docs/BUDGET-SCHEDULE.md")
    assert len(got) == 1, got
    assert got[0]["classification"] == "wrong_dir", got[0]
    assert got[0]["resolved"] == "experiments/ptr-engine/measure/BUDGET-SCHEDULE.md", got[0]
    assert got[0]["line"] == 1
    r = run(root, "--check")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "NEW docs/PRICE-REPLICATION.md:1 wrong_dir docs/BUDGET-SCHEDULE.md" in r.stdout


def test_red_missing_fabricated_path(tmp_path):
    root = make_ws(tmp_path, docs=["REAL.md"])
    (root / "docs" / "PRICE-REPLICATION.md").write_text(
        "see `docs/does-not-exist.md` for the table\n", encoding="utf-8")
    got = findings(root, "docs/does-not-exist.md")
    assert len(got) == 1, got
    assert got[0]["classification"] == "missing", got[0]
    assert got[0]["resolved"] == "", got[0]
    r = run(root, "--check")
    assert r.returncode == 1
    assert "missing docs/does-not-exist.md" in r.stdout


def test_red_wrong_dir_elsewhere_in_tree(tmp_path):
    """A shorthand that is not one of the two legal alternates is still a wrong citation."""
    root = make_ws(tmp_path)
    p = root / "experiments/ptr-engine/longrun/tests"
    p.mkdir(parents=True)
    (p / "test_cap_gate.py").write_text("x\n", encoding="utf-8")
    (root / "docs" / "CAPGATE.md").write_text(
        "guard: `tests/test_cap_gate.py`\n", encoding="utf-8")
    got = findings(root, "tests/test_cap_gate.py")
    assert got and got[0]["classification"] == "wrong_dir", got
    assert got[0]["resolved"] == "experiments/ptr-engine/longrun/tests/test_cap_gate.py"
    assert run(root, "--check").returncode == 1


# ---------------------------------------------------------------- GREEN

def test_green_correct_citation(tmp_path):
    root = make_ws(tmp_path, measure=["BUDGET-SCHEDULE.md"])
    (root / "docs" / "PRICE-REPLICATION.md").write_text(
        "| factor | 1.374532 | [`BUDGET-SCHEDULE.md`](../experiments/ptr-engine/measure/"
        "BUDGET-SCHEDULE.md) §1 |\n", encoding="utf-8")
    got = findings(root, "experiments/ptr-engine/measure/BUDGET-SCHEDULE.md")
    assert len(got) == 1, got
    assert got[0]["classification"] == "ok", got[0]
    assert run(root, "--check").returncode == 0


def test_green_named_phantom_is_ignored(tmp_path):
    """A record is allowed to discuss a phantom it has named as a phantom."""
    root = make_ws(tmp_path)
    (root / "docs" / "COLD-START-PROBE.md").write_text(
        "**`docs/GATE-SIMPLIFY.md` does not exist**; the artefact is elsewhere.\n",
        encoding="utf-8")
    got = findings(root, "docs/GATE-SIMPLIFY.md")
    assert len(got) == 1, got
    assert got[0]["classification"] == "ignored", got[0]
    assert got[0]["reason"] == "says-it-does-not-exist", got[0]
    r = run(root, "--check")
    assert r.returncode == 0, r.stdout
    assert "ok=0 wrong_dir=0 missing=0 ignored=1" in r.stdout


def test_green_baseline_freezes_old_but_not_new(tmp_path):
    root = make_ws(tmp_path)
    doc = root / "docs" / "OLD.md"
    doc.write_text("`docs/gone.md`\n", encoding="utf-8")
    assert run(root, "--write-baseline").returncode == 0
    baseline = root / "state/logs/path-refs-baseline.json"
    assert json.loads(baseline.read_text(encoding="utf-8"))["anchors"]
    r = run(root, "--check")
    assert r.returncode == 0, r.stdout
    assert "0 new" in r.stdout, r.stdout

    # Forward-only: a reference added after the freeze is NEW and fails.
    doc.write_text("`docs/gone.md`\n`docs/also-new-and-absent.md`\n", encoding="utf-8")
    r = run(root, "--check")
    assert r.returncode == 1, r.stdout
    assert "NEW docs/OLD.md:2 missing docs/also-new-and-absent.md" in r.stdout
    assert "NEW docs/OLD.md:1 missing docs/gone.md" not in r.stdout, "baselined key re-failed"
