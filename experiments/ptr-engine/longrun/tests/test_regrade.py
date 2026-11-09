#!/usr/bin/env python3
"""Tests for tools/regrade.py - one command that re-derives a published grade.

Offline, stdlib + pytest. Every test drives the CLI, because the contract is the
exit codes and the printed check status, not an internal helper.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
TOOL = os.path.join(ENGINE, "tools", "regrade.py")
GRADER = os.path.join(ENGINE, "longrun", "grade_v5.py")
FIXTURE = os.path.join(ENGINE, "longrun", "tasks-v5", "runtime-v5",
                       "LR-01.v5.json")
PY = sys.executable
AS_OF = "2026-01-01T00:00:00+00:00"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def run(*args):
    return subprocess.run([PY, TOOL] + list(args), capture_output=True,
                          text=True, cwd=ENGINE)


@pytest.fixture()
def rows(tmp_path):
    p = tmp_path / "rows-test.jsonl"
    recs = [
        {"arm": "pointer-stable", "turn": 12, "content": "ANSWER: NUM 64"},
        {"arm": "pointer-stable", "turn": 24, "content": "ANSWER: NUM 31"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    return str(p)


def regrade_once(rows, out_dir, *extra):
    return run("--rows", rows, "--out-dir", str(out_dir),
               "--as-of", AS_OF, *extra)


def test_a_grade_records_grader_sha256(rows, tmp_path):
    out = tmp_path / "out"
    r = regrade_once(rows, out)
    assert r.returncode == 0, r.stdout + r.stderr
    grade = out / "rows-test.grade-v5.json"
    doc = json.loads(grade.read_text(encoding="utf-8"))
    assert doc["grader_sha256"] == sha256(GRADER)
    assert doc["grader_path"] == GRADER
    assert doc["generated_at"] == AS_OF
    assert sha256(GRADER) in r.stdout
    assert doc["grader"] == "grade_v5"


def test_b_check_in_sync_prints_identical_and_exits_0(rows, tmp_path):
    out = tmp_path / "out"
    assert regrade_once(rows, out).returncode == 0
    grade = out / "rows-test.grade-v5.json"
    r = run("--rows", rows, "--check", "--grade", str(grade))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "IDENTICAL" in r.stdout


def test_c_check_one_mutated_field_exits_1_and_names_path(rows, tmp_path):
    out = tmp_path / "out"
    assert regrade_once(rows, out).returncode == 0
    src = out / "rows-test.grade-v5.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["arms"]["pointer-stable"]["checkpoint_accuracy_pct"] = 99.9
    bad = tmp_path / "mutated.grade-v5.json"
    bad.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    r = run("--rows", rows, "--check", "--grade", str(bad))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "DIFFERS" in r.stdout
    assert "arms.pointer-stable.checkpoint_accuracy_pct" in r.stdout


def test_d_as_of_makes_two_runs_byte_identical(rows, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert regrade_once(rows, a).returncode == 0
    assert regrade_once(rows, b).returncode == 0
    fa = (a / "rows-test.grade-v5.json").read_bytes()
    fb = (b / "rows-test.grade-v5.json").read_bytes()
    assert fa == fb
    # and without --as-of the two differ only in generated_at
    c, d = tmp_path / "c", tmp_path / "d"
    assert run("--rows", rows, "--out-dir", str(c)).returncode == 0
    assert run("--rows", rows, "--out-dir", str(d)).returncode == 0
    dc = json.loads((c / "rows-test.grade-v5.json").read_text())
    dd = json.loads((d / "rows-test.grade-v5.json").read_text())
    dc.pop("generated_at")
    dd.pop("generated_at")
    assert dc == dd


def test_e_refused_overwrite_exits_4(rows, tmp_path):
    out = tmp_path / "out"
    assert regrade_once(rows, out).returncode == 0
    r = regrade_once(rows, out)
    assert r.returncode == 4, r.stdout + r.stderr
    assert "refusing overwrite" in r.stdout


def test_f_red_green_recorded_grader_sha(rows, tmp_path):
    """Mutate the recorded grader sha: the check must fail, naming the path.
    Restore it: the same check must pass again."""
    out = tmp_path / "out"
    assert regrade_once(rows, out).returncode == 0
    good = out / "rows-test.grade-v5.json"
    doc = json.loads(good.read_text(encoding="utf-8"))
    doc["grader_sha256"] = "0" * 64
    bad = tmp_path / "bad.grade-v5.json"
    bad.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    r = run("--rows", rows, "--check", "--grade", str(bad))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "grader_sha256" in r.stdout
    print("RED:", [ln for ln in r.stdout.splitlines()
                   if "grader_sha256" in ln][0])
    shutil.copyfile(good, bad)
    r = run("--rows", rows, "--check", "--grade", str(bad))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "IDENTICAL" in r.stdout
    print("GREEN:", [ln for ln in r.stdout.splitlines()
                     if "IDENTICAL" in ln][0])


def test_g_check_rules_out_a_wrong_grader_sha(tmp_path):
    r = run("--rows", str(tmp_path / "missing.jsonl"), "--check",
            "--sha256", "0" * 64)
    assert r.returncode == 3
    assert "sha256 mismatch" in r.stdout


def test_h_unreadable_rows_exits_2(tmp_path):
    r = run("--rows", str(tmp_path / "nope.jsonl"), "--out-dir", str(tmp_path))
    assert r.returncode == 2
    assert "not found" in r.stdout
