#!/usr/bin/env python3
"""Tests for tools/unstamped_audit.py --check.

Three cases, exactly the contract:
  1. the real census exits 0;
  2. a copy with a designed `verified_fail` on a refusal exit exits 1, naming the card;
  3. a copy with a card id removed (while the board still reports it failed) exits 1, naming it.

No network, no board writes, no test/cell/pipeline command is run.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
TOOL = os.path.join(ENGINE, "tools", "unstamped_audit.py")
CENSUS = os.path.join(ENGINE, "measure", "UNSTAMPED-CENSUS.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(CENSUS), reason="census not built in this tree"
)


def run(*args):
    return subprocess.run(
        [sys.executable, TOOL, "--check", *args],
        capture_output=True, text=True, timeout=120,
    )


def load():
    with open(CENSUS, encoding="utf-8") as fh:
        return json.load(fh)


def board_snapshot(tmpdir, card_ids):
    path = os.path.join(tmpdir, "board.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"card_ids": card_ids}, fh)
    return path


def write_census(tmpdir, census):
    path = os.path.join(tmpdir, "census.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(census, fh)
    return path


def test_real_census_exits_zero():
    proc = run()
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "CENSUS OK" in proc.stdout


def test_fabricated_verified_fail_on_refusal_exit_exits_one():
    census = load()
    victim = census["rows"][0]
    victim["classification"] = "verified_fail"
    victim["command"] = "python3 -c 'pass'"
    victim["exit_code"] = 3            # budget: a refusal, never a measurement
    tmpdir = tempfile.mkdtemp(prefix="unstamped-audit-")
    try:
        path = write_census(tmpdir, census)
        board = board_snapshot(tmpdir, census["card_ids"])
        proc = run("--census", path, "--board", board)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert victim["card_id"] in proc.stdout
        assert "non-measuring" in proc.stdout
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_missing_card_id_exits_one():
    census = load()
    dropped = census["rows"].pop(0)["card_id"]
    census["card_ids"] = [c for c in census["card_ids"] if c != dropped]
    tmpdir = tempfile.mkdtemp(prefix="unstamped-audit-")
    try:
        path = write_census(tmpdir, census)
        # the board still reports the dropped card failed
        board = board_snapshot(tmpdir, load()["card_ids"])
        proc = run("--census", path, "--board", board)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert dropped in proc.stdout
        assert "missing from the census" in proc.stdout
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
