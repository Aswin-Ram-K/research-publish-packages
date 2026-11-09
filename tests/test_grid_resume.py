"""Tests for experiments/ptr-engine/tools/grid_resume.py (read-only resumption report).

Every test builds its own rows corpus under tmp_path and passes --measure-dir /
--root, so nothing here can write into the real measure/ directory.  The state
machine is exercised on real 48/47/27-turn shapes, not on prose.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "experiments/ptr-engine/tools/grid_resume.py")
ERA_B_FIXTURE = "0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641"


def load_tool():
    spec = importlib.util.spec_from_file_location("grid_resume", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


grid_resume = load_tool()


def write_rows(measure, name, n, rep=1, arm="pointer-stable", tools_mode="read_file",
               runaway_at=None, ttft=True, stop="stop", start=1):
    path = os.path.join(str(measure), name)
    with open(path, "w", encoding="utf-8") as fh:
        for turn in range(start, start + n):
            row = {"kind": "turn", "turn": turn, "rep": rep, "arm": arm,
                   "prompt_tokens": 3000 + turn, "stop_reason":
                   ("runaway_turn" if turn == runaway_at else stop),
                   "fixture_sha256": ERA_B_FIXTURE}
            if ttft:
                row["ttft_ms"] = 100.0 + turn
            if tools_mode is not None:
                row["tools_mode"] = tools_mode
            fh.write(json.dumps(row) + "\n")
    return path


def corpus(tmp_path):
    measure = tmp_path / "measure"
    measure.mkdir()
    return measure


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_done_needs_exactly_48_turns(tmp_path):
    measure = corpus(tmp_path)
    write_rows(measure, "rows-cell-pointer-stable-20261026T200000Z.jsonl", 48)
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    cell = rep["cells"][0]
    assert cell["state"] == "done"
    f = cell["files"][0]
    assert f["state"] == "done"
    assert f["turns"] == 48
    assert f["ttft_present"] == 48
    assert f["ttft_all"] is True
    assert f["tokens_spent"] == sum(3000 + t for t in range(1, 49))


def test_one_turn_missing_is_partial_not_done(tmp_path):
    measure = corpus(tmp_path)
    write_rows(measure, "rows-cell-pointer-stable-20261026T200000Z.jsonl", 47)
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    cell = rep["cells"][0]
    assert cell["state"] == "partial"
    assert cell["files"][0]["state"] == "partial"
    assert cell["files"][0]["turns"] == 47
    assert cell["files"][0]["turns"] < cell["files"][0]["declared_turns"]


def test_runaway_turn_is_abandoned(tmp_path):
    measure = corpus(tmp_path)
    write_rows(measure, "rows-cell-transcript-grow-20261026T200000Z.jsonl", 20,
               rep=1, arm="transcript-grow", runaway_at=19)
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    cell = [c for c in rep["cells"] if c["arm"] == "transcript-grow"][0]
    assert cell["state"] == "abandoned"
    f = cell["files"][0]
    assert f["state"] == "abandoned"
    assert any("runaway_turn" in e for e in f["evidence"])
    assert f["runaway"] == [(19, "runaway_turn")]


def test_era_a_excluded_by_tools_mode_not_filename(tmp_path):
    measure = corpus(tmp_path)
    # Same fixture sha as era B, same filename shape: only the stamp decides.
    write_rows(measure, "rows-cell-pointer-stable-20261026T182535Z.jsonl", 27,
               tools_mode="off")
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    f = rep["cells"][0]["files"][0]
    assert f["state"] == "era_a_excluded"
    assert rep["cells"][0]["state"] == "era_a_excluded"
    assert f["fixture_sha256"] == [ERA_B_FIXTURE]
    assert any("tools_mode=off" in e for e in f["evidence"])


def test_usable_for_empty_stamp_excludes_a_48_turn_file(tmp_path):
    measure = corpus(tmp_path)
    write_rows(measure, "rows-cell-lease-reopen-20261026T200000Z.jsonl", 48,
               rep=1, arm="lease-reopen")
    (tmp_path / "measure" / "GRID-CELL-SANITY.json").write_text(json.dumps({
        "cells": [{"path": "experiments/ptr-engine/measure/rows-cell-lease-reopen-20261026T200000Z.jsonl",
                   "usable_for": []}]}), encoding="utf-8")
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    cell = [c for c in rep["cells"] if c["arm"] == "lease-reopen"][0]
    assert cell["state"] == "era_a_excluded"
    assert any("usable_for=[]" in e for e in cell["files"][0]["evidence"])


def test_next_cell_is_first_not_done_in_declared_order(tmp_path):
    measure = corpus(tmp_path)
    write_rows(measure, "rows-cell-pointer-stable-20261026T200000Z.jsonl", 48)
    rep = grid_resume.build_report(str(measure), str(tmp_path))
    assert rep["cells"][0]["state"] == "done"
    assert rep["next_cell"] == "pointer-stable r2"
    assert rep["canary_next"] == "pointer-stable"
    # and with pointer-stable r1 absent, the next cell is r1
    empty = tmp_path / "empty"
    empty.mkdir()
    rep2 = grid_resume.build_report(str(empty), str(tmp_path))
    assert rep2["next_cell"] == "pointer-stable r1"
    assert rep2["cells"][0]["state"] == "absent"


def test_cli_is_read_only_on_rows_files(tmp_path):
    measure = corpus(tmp_path)
    path = write_rows(measure, "rows-cell-pointer-stable-20261026T200000Z.jsonl", 48)
    before = sha(path)
    proc = subprocess.run([sys.executable, TOOL, "--measure-dir", str(measure),
                           "--root", str(tmp_path), "--no-ledger"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "state=done" in proc.stdout
    assert sha(path) == before
