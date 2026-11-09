"""Red/green tests for experiments/ptr-engine/tools/harness_map_check.py.

The guard's job: a citation in `docs/HARNESS-MAP.md` must resolve to the line it claims.
Each test copies the real map and appends one deliberately wrong citation, so the guard is
proven on the document it guards, not on a toy fixture. `run_longrun.py:1 make_row` is
wrong because line 137 (`load_fixture`) is not inside `make_row` (1781-1970 at HEAD); a blank/comment line is
wrong because it holds no code.
"""
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GUARD = os.path.join(REPO, "experiments", "ptr-engine", "tools", "harness_map_check.py")
MAP = os.path.join(REPO, "docs", "HARNESS-MAP.md")
RUNNER = os.path.join(REPO, "experiments", "ptr-engine", "longrun", "run_longrun.py")


def run(*args):
    return subprocess.run([sys.executable, GUARD, *args], capture_output=True, text=True)


def with_citation(tmp_path, citation):
    """Copy the shipped map and append one citation line, returning the copy's path."""
    dst = tmp_path / "HARNESS-MAP.md"
    dst.write_text(open(MAP, encoding="utf-8").read() + f"\nSee `{citation}`.\n", encoding="utf-8")
    return str(dst)


def test_corrected_map_passes():
    """The shipped map exits 0: every non-baselined citation resolves."""
    res = run("--check")
    assert res.returncode == 0, res.stderr
    assert "harness_map_check: OK" in res.stderr


def test_moved_symbol_fails(tmp_path):
    """A real line that is no longer inside the named symbol fails."""
    res = run("--check", "--map", with_citation(tmp_path, "run_longrun.py:137 make_row"))
    assert res.returncode == 1, res.stderr
    assert "symbol_moved" in res.stderr or "anchor_mismatch" in res.stderr


def test_blank_line_fails(tmp_path):
    """A cited line that is blank fails even when the file and line number exist."""
    src = open(RUNNER, encoding="utf-8").read().splitlines()
    blank = next(i for i, line in enumerate(src, 1) if not line.strip())
    res = run("--check", "--map", with_citation(tmp_path, f"run_longrun.py:{blank} make_row"))
    assert res.returncode == 1, res.stderr
    assert "blank_line" in res.stderr


def test_comment_line_fails(tmp_path):
    """A comment-only line is not code, so a citation to it fails."""
    src = open(RUNNER, encoding="utf-8").read().splitlines()
    comment = next(i for i, line in enumerate(src, 1) if line.strip().startswith("#"))
    res = run("--check", "--map", with_citation(tmp_path, f"run_longrun.py:{comment} make_row"))
    assert res.returncode == 1, res.stderr
    assert "comment_only" in res.stderr


def test_baseline_keeps_history_green(tmp_path):
    """A stale citation frozen in the forward-only baseline does not fail today."""
    res = run("--check", "--map", with_citation(tmp_path, "run_longrun.py:1191 make_row"))
    assert res.returncode == 0, res.stderr
