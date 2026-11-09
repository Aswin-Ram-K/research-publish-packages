#!/usr/bin/env python3
"""Tests for experiments/ptr-engine/tools/fixture_coverage.py - the checkpoint gate.

The gate exists because 3 decidable checkpoints cannot rank arms: b+c <= 3 puts the
exact McNemar minimum two-sided p at 0.25. `LR-01.v6.json` carries 12. These tests
hold that fixture green, and hold each failure mode RED on a mutated copy:

  (a) a truth value outside the pinned range it is asked from   (the resolve.py L39
      defect that already cost this project three rounds)
  (b) a truth that collides with another occurrence in the pinned range
  (c) a TEXT item, which grade_v5 refuses

A gate nobody has seen fail is not a gate: each mutant's observed output is asserted
here, not asserted in prose.

    python3 -m pytest -q experiments/ptr-engine/longrun/tests/test_fixture_coverage.py
"""
import json
import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOLS = os.path.join(REPO, "experiments", "ptr-engine", "tools")
RUNTIME = os.path.join(REPO, "experiments", "ptr-engine", "longrun",
                       "tasks-v5", "runtime-v5")
V5 = os.path.join(RUNTIME, "LR-01.v5.json")
V6 = os.path.join(RUNTIME, "LR-01.v6.json")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import fixture_coverage as fc  # noqa: E402


def _load(path):
    with open(path) as fh:
        return json.load(fh)


def _mutant(tmp_path, mutate):
    doc = _load(V6)
    mutate(doc)
    out = tmp_path / "mutant.json"
    out.write_text(json.dumps(doc, indent=1))
    return str(out)


def _cp(doc, cid):
    for cp in doc["checkpoints"]:
        if cp["id"] == cid:
            return cp
    raise AssertionError("checkpoint %s missing" % cid)


# --------------------------------------------------------------------- coverage
def test_v6_is_green():
    """12 decidable checkpoints, none colliding, all expected answers <= 40 tokens."""
    rows, failures = fc.check_fixture(V6, quiet=True)
    assert failures == [], failures
    assert len(rows) == 12, len(rows)
    assert all(r["answerable"] for r in rows)
    assert not any(r["collision"] for r in rows)
    assert all(r["tokens"] <= fc.MAX_EXPECTED_TOKENS for r in rows)
    kinds = {r["kind"] for r in rows}
    assert kinds == {"NUM", "CALL", "NONE"}
    assert sum(1 for r in rows if r["kind"] == "NUM") >= 4
    assert sum(1 for r in rows if r["kind"] == "CALL") >= 4
    assert sum(1 for r in rows if r["kind"] == "NONE") >= 2
    # one checkpoint per checkpoint turn, and the turn list matches
    assert sorted(r["turn"] for r in rows) == sorted(_load(V6)["checkpoint_turns"])
    assert len(set(r["turn"] for r in rows)) == 12


def test_v6_turns_are_checkpoint_turns():
    """Every checkpoint sits on a turn the fixture declares, and that turn is a checkpoint."""
    doc = _load(V6)
    turns = {t["turn"]: t for t in doc["turns"]}
    for cp in doc["checkpoints"]:
        assert cp["turn"] in doc["checkpoint_turns"]
        assert turns[cp["turn"]]["kind"] == "checkpoint", cp["id"]


def test_v5_is_untouched():
    """LR-01.v5.json is a live cell's contract: still 3 checkpoints at T12/T24/T46."""
    doc = _load(V5)
    assert len(doc["checkpoints"]) == 3
    assert doc["checkpoint_turns"] == [12, 24, 46]


# ---------------------------------------------------------- (a) unanswerable
def test_truth_outside_pinned_range_is_red(tmp_path, capsys):
    """RED (a): scope.block() sits at L163; a pin ending at L110 cannot answer it."""
    path = _mutant(tmp_path, lambda d: _cp(d, "cp.4.t08").update(source=(
        "experiments/ptr-engine/ptr_engine/resolve.py#L36-L110")))
    rows, failures = fc.check_fixture(path, quiet=True)
    row = [r for r in rows if r["id"] == "cp.4.t08"][0]
    assert row["answerable"] is False
    assert failures and "falls outside the declared pinned range" in row["reason"], row["reason"]
    fc.check_fixture(path)
    out = capsys.readouterr().out
    assert "FAIL" in out and "cp.4.t08" in out


def test_truth_with_no_pinned_source_is_red(tmp_path):
    """RED (a2): a source path that is not in the fixture's pinned items at all."""
    path = _mutant(tmp_path, lambda d: _cp(d, "cp.0.t12").update(source=(
        "experiments/ptr-engine/ptr_engine/ledger.py#L39")))
    rows, failures = fc.check_fixture(path, quiet=True)
    row = [r for r in rows if r["id"] == "cp.0.t12"][0]
    assert row["answerable"] is False
    assert failures


# ------------------------------------------------------------- (b) collision
def test_colliding_truth_is_red(tmp_path, capsys):
    """RED (b): a second checkpoint deciding the same fact (31 Ptr* classes)."""
    def mutate(doc):
        _cp(doc, "cp.6.t18")["answer_spec"]["derive"]["pattern"] = r"^Ptr\w*$"
        _cp(doc, "cp.6.t18")["expected"] = "31"
    path = _mutant(tmp_path, mutate)
    rows, failures = fc.check_fixture(path, quiet=True)
    row = [r for r in rows if r["id"] == "cp.6.t18"][0]
    assert row["collision"] is True
    assert any("duplicate truth of cp.1.t24" in why for _, why in failures), failures
    fc.check_fixture(path)
    out = capsys.readouterr().out
    assert "FAIL" in out


def test_absence_that_does_not_hold_is_red(tmp_path):
    """RED (b2): a NONE item whose attribute IS called inside the pinned range."""
    path = _mutant(tmp_path, lambda d: _cp(d, "cp.11.t42").update(
        source="experiments/ptr-engine/ptr_engine/resolve.py#L66-L71",
        answer_spec={"kind": "NONE", "derive": {
            "rule": "no_attr_call_inside_function",
            "file": "experiments/ptr-engine/ptr_engine/resolve.py",
            "function": "_refuse", "attr": "record_refusal"}}))
    rows, failures = fc.check_fixture(path, quiet=True)
    row = [r for r in rows if r["id"] == "cp.11.t42"][0]
    # _refuse DOES call record_refusal, so the declared absence is a fixture defect
    assert row["collision"] is True or row["answerable"] is False
    assert failures


# ------------------------------------------------------------------ (c) TEXT
def test_text_item_is_red(tmp_path, capsys):
    """RED (c): grade_v5 refuses TEXT, so the gate must refuse it too."""
    def mutate(doc):
        cp = _cp(doc, "cp.9.t32")
        cp["answer_spec"] = {"kind": "TEXT", "derive": {"rule": "constant_value",
                                                       "symbol": "DEFAULT_MAX_REFS"}}
        cp["expected"] = "sixty-four"
    path = _mutant(tmp_path, mutate)
    rows, failures = fc.check_fixture(path, quiet=True)
    row = [r for r in rows if r["id"] == "cp.9.t32"][0]
    assert "TEXT" in row["reason"]
    assert failures
    fc.check_fixture(path)
    out = capsys.readouterr().out
    assert "FAIL" in out
