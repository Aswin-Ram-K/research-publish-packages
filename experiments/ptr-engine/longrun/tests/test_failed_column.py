#!/usr/bin/env python3
"""test_failed_column.py - red->green on the reclaim classifier's --check gate.

The gate has to catch three things, or the reclaim file is wallpaper:
  1. a card left unclassified,
  2. a `finished_once_and_still_green` card whose command no longer exits 0,
  3. totals that do not add up to the census.

Every test builds a census+reclaim pair in a temp dir; nothing here reads the live
census except the one contract test, and nothing writes outside tempfile.mkdtemp().
"""
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.normpath(os.path.join(HERE, "..", "..", "tools", "failed_column.py"))


def load_tool():
    spec = importlib.util.spec_from_file_location("failed_column", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_pair(tmp, rows, census_rows, counts=None):
    census = {"census": "T", "card_ids": [r["card_id"] for r in census_rows], "rows": census_rows}
    cpath = os.path.join(tmp, "census.json")
    with open(cpath, "w") as fh:
        json.dump(census, fh)
    if counts is None:
        counts = {}
        for r in rows:
            counts[r["class"]] = counts.get(r["class"], 0) + 1
    doc = {"scope": {"census_total": len(rows), "in_scope": len(rows) - counts.get("superseded", 0)},
           "counts": counts, "rows": rows}
    opath = os.path.join(tmp, "reclaim.json")
    with open(opath, "w") as fh:
        json.dump(doc, fh)
    return cpath, opath


def row(card, unit, cls, cmd="/bin/true", exit_today=0):
    return {"card": card, "unit": unit, "execution_id": "e", "class": cls,
            "artifacts_present": ["x.md"], "command": cmd, "exit_today": exit_today,
            "first_failure_line": "", "next_action": "record_a_row", "reason": ""}


def census_row(card, unit):
    return {"card_id": card, "title": unit, "classification": "never_had_a_row"}


def test_green_card_that_is_still_green_passes():
    mod = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        cpath, opath = write_pair(tmp, [row("c1", "U1", "finished_once_and_still_green")],
                                  [census_row("c1", "U1")])
        assert mod.check(opath, cpath) == 0


def test_red_green_is_caught_and_named():
    """RED: a green card whose command now exits 1 must fail the gate, naming the unit."""
    mod = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        cpath, opath = write_pair(tmp, [row("c1", "FABRICATED-GREEN", "finished_once_and_still_green",
                                            cmd="/bin/false", exit_today=0)],
                                  [census_row("c1", "FABRICATED-GREEN")])
        rc = mod.check(opath, cpath)
        assert rc == 1, "a green card whose command exits 1 must fail the check"


def test_unclassified_card_is_caught():
    mod = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        cpath, opath = write_pair(tmp, [row("c1", "U1", "made_up_class")], [census_row("c1", "U1")])
        assert mod.check(opath, cpath) == 1


def test_totals_must_reach_the_census():
    mod = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        cpath, opath = write_pair(tmp, [row("c1", "U1", "no_artifacts", cmd=None, exit_today=None)],
                                  [census_row("c1", "U1")], counts={"no_artifacts": 0})
        assert mod.check(opath, cpath) == 1


def test_missing_card_is_caught():
    mod = load_tool()
    with tempfile.TemporaryDirectory() as tmp:
        cpath, opath = write_pair(tmp, [row("c1", "U1", "no_artifacts", cmd=None, exit_today=None)],
                                  [census_row("c1", "U1"), census_row("c2", "U2")])
        assert mod.check(opath, cpath) == 1


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-q"]))
