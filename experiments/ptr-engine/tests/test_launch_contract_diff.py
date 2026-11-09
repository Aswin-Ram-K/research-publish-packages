"""Scoped judging for launch_contract_diff -- a check must be able to name its tree.

The defect this guards: the default `--check` judges "whatever is on disk now", so a
neighbour card editing a pinned input between a card's write and its re-check turns a
correct row into a false FAIL (`GRID-PARAMS-DIGEST-SUPERSEDE`, a3fdaab5: its row was
correct at 19:27, `grade_v5.py` was repaired at 19:30, and the digest row went red
naming a value that is *supposed* to be stale until the next pin generation).

Every fixture tree here is built in `tmp_path` from the real repository's files, so the
tests never write inside the workspace and never depend on which generation is current:
the scope is re-recorded in the copy, and the tests assert the RELATIONSHIP between tree
and record, not a literal digest.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
REPO = ENGINE.parents[1]
TOOL = ENGINE / "tools" / "launch_contract_diff.py"

if str(ENGINE / "tools") not in sys.path:
    sys.path.insert(0, str(ENGINE / "tools"))

import launch_contract_diff as lcd  # noqa: E402


# ------------------------------------------------------------------ fixtures
def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest_over(root: Path, files, live: bool) -> str:
    rows = []
    for f in files:
        sha = _sha(root / f["path"]) if live else f["sha256"]
        rows.append((f["name"], sha))
    rows.sort()
    return hashlib.sha256("".join("%s:%s\n" % (n, s) for n, s in rows).encode()).hexdigest()


def _needed(root: Path):
    """Every file the tool reads: probe paths, their marker files, the pinned inputs."""
    paths = set()
    for chk in lcd.checks(str(root)):
        for p in chk["probes"]:
            rel = p.get("path") or ""
            if rel and not rel.startswith("<computed"):
                paths.add(rel)
            if p.get("marker_in"):
                paths.add(p["marker_in"])
    paths |= {lcd.PIN, lcd.PARAMS, lcd.SHAPE, lcd.LEDGER, lcd.BASELINE, lcd.STATS,
              lcd.CELL, lcd.RUN_A_STAR, "experiments/ptr-engine/longrun/client.py"}
    for f in json.loads((root / lcd.PIN).read_text())["files"]:
        paths.add(f["path"])
    return sorted(paths)


def _clone(dst: Path) -> Path:
    for rel in _needed(REPO):
        to = dst / rel
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_bytes((REPO / rel).read_bytes())
    return dst


def _bump(dst: Path, generation: int = 5) -> str:
    """Record a NEW pin generation over the copy's bytes, keeping the old one in the chain.

    This is what a pin bump does: the tree is named, the previous generation is preserved
    verbatim under `supersedes_pin_generation_<n-1>`.
    """
    pin = json.loads((dst / lcd.PIN).read_text())
    old = pin["harness_sha256"]
    files = [dict(f) for f in pin["files"]]
    for f in files:
        f["sha256"] = _sha(dst / f["path"])
    rec = {"schema": "harness-pin/1", "generation": generation,
           "unit": "test_launch_contract_diff (fixture)",
           "recorded_at": pin["recorded_at"], "frozen_at": pin["frozen_at"],
           "harness_sha256": _digest_over(dst, files, False),
           "superseded_harness_sha256": old, "files": files,
           "purpose": pin.get("purpose", ""), "wiring": pin.get("wiring", {}),
           "supersedes_pin_generation_%d" % (generation - 1): pin}
    (dst / lcd.PIN).write_text(json.dumps(rec, indent=1))
    for rel in (lcd.RUN_A_STAR, lcd.DOC_RUNBOOK):
        p = dst / rel
        p.write_text(p.read_text().replace(old, rec["harness_sha256"]))
    return rec["harness_sha256"]


def _run(root: Path, *args):
    """Run the tool's CLI out-of-process; return (exit code, stdout, stderr, document)."""
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root), *args, "--json"],
        capture_output=True, text=True, cwd=str(REPO))
    doc = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else None
    return proc.returncode, proc.stdout, proc.stderr, doc


def _row(doc, cid):
    return [n for n in doc["numbers"] if n["id"] == cid][0]


@pytest.fixture()
def consistent(tmp_path: Path) -> Path:
    """A tree whose recorded generation matches its bytes."""
    root = _clone(tmp_path / "tree")
    _bump(root)
    return root


def _break_help(root: Path) -> None:
    p = root / lcd.RUN_A_STAR
    text = p.read_text()
    assert "handed to cell.py (default 108)" in text
    p.write_text(text.replace("handed to cell.py (default 108)",
                              "handed to cell.py (default 67)"))


# ------------------------------------------------------------------ the cases
def test_scope_names_the_judged_tree_and_passes_on_it(consistent: Path):
    """(b) the tree the scope names is the tree on disk -> 0, and the report says which."""
    code, _out, _err, doc = _run(consistent, "--check", "--pin-generation", "5")
    assert doc["judged_tree"]["generation"] == 5
    row = _row(doc, "harness_pin_digest")
    assert row["status"] == "AGREES", row["reason"]
    assert doc["judged_tree"]["harness_sha256"] == _digest_over(
        consistent, json.loads((consistent / lcd.PIN).read_text())["files"], True)
    assert doc["judged_tree"]["pinned_at"] is None or doc["judged_tree"]["pinned_at"]
    row = _row(doc, "harness_pin_digest")
    assert row["status"] == "AGREES", row["reason"]
    assert row["judged_tree"] == doc["judged_tree"]


def test_a_moved_tree_is_moved_not_disagrees(tmp_path: Path):
    """(a) a neighbour rewrites a pinned input -> MOVED, naming the mover and BOTH digests."""
    root = _clone(tmp_path / "tree")
    gen4 = json.loads((root / lcd.PIN).read_text())
    victim = root / "experiments/ptr-engine/longrun/grade_v5.py"
    recorded = [f["sha256"] for f in gen4["files"] if f["name"] == "grade_v5.py"][0]
    victim.write_bytes(victim.read_bytes() + b"\n# a neighbour card moved this file\n")

    code, out, err, doc = _run(root, "--check", "--pin-generation", str(gen4["generation"]))
    assert code == lcd.EXIT_TREE_MOVED == 13, (code, out, err)
    row = _row(doc, "harness_pin_digest")
    assert row["status"] == "MOVED", row["reason"]
    assert row["status"] != "DISAGREES"          # the whole point of the card
    movers = {m["name"]: m for m in row["moved_inputs"]}
    assert "grade_v5.py" in movers
    assert movers["grade_v5.py"]["recorded_sha256"] == recorded
    assert movers["grade_v5.py"]["current_sha256"] == _sha(victim)
    assert row["live_harness_sha256"] != row["judged_tree"]["harness_sha256"]
    assert "grade_v5.py" in row["reason"]
    assert recorded in row["reason"] and row["live_harness_sha256"] in row["reason"]


def test_the_default_check_is_unchanged_and_still_strict(consistent: Path):
    """(c) no scope: a genuine 108 -> 67 disagreement is exit 1, naming both file:line."""
    _break_help(consistent)
    code, _out, _err, doc = _run(consistent, "--check")
    assert code == 1
    row = _row(doc, "per_cell_budget")
    assert row["status"] == "DISAGREES"
    assert "run_a_star.py" in row["reason"]
    assert "108" in row["reason"] and "67" in row["reason"]
    assert "judged_tree" not in doc                 # the default report shape is unchanged


def test_an_explicit_scope_is_not_a_bypass(consistent: Path):
    """(c') naming a tree must not launder a real disagreement somewhere else."""
    _break_help(consistent)
    code, _out, _err, doc = _run(consistent, "--check", "--pin-generation", "5")
    assert code == 1                                # not 0, not 13
    assert _row(doc, "per_cell_budget")["status"] == "DISAGREES"
    assert _row(doc, "harness_pin_digest")["status"] == "AGREES"


def test_an_unrecorded_tree_is_refused_not_laundered(tmp_path: Path):
    """A --tree-sha the pin never recorded names no recorded values: refuse (2), never 0."""
    root = _clone(tmp_path / "tree")
    code, _out, err, _doc = _run(root, "--check", "--tree-sha", "0" * 64)
    assert code == lcd.EXIT_USAGE == 2
    assert "REFUSED" in err and "not a generation recorded" in err


def test_an_unknown_generation_is_a_usage_error(tmp_path: Path):
    root = _clone(tmp_path / "tree")
    code, _out, err, _doc = _run(root, "--check", "--pin-generation", "999")
    assert code == 2
    assert "no pin generation 999" in err


def test_write_lands_in_the_measure_directory(consistent: Path):
    """--write must write measure/LAUNCH-CONTRACT-DIFF.json, not <root>/measure/."""
    code, _out, _err, _doc = _run(consistent, "--write", "--pin-generation", "5")
    assert code == 0
    artefact = consistent / lcd.MEAS / "LAUNCH-CONTRACT-DIFF.json"
    assert artefact.is_file()
    assert not (consistent / "measure").exists()
    doc = json.loads(artefact.read_text())
    assert doc["judged_tree"]["generation"] == 5
    assert "explicit scope" in doc["operational_rule"]
