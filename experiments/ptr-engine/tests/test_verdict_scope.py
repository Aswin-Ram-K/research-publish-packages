#!/usr/bin/env python3
"""test_verdict_scope.py -- a row must say which bytes it judged, and be re-judgeable.

THE THREE HISTORICAL INSTANCES, REPLAYED HERE AS CASES:

  (a) a command that touches nothing named                -> `clean`, exit 0
  (b) a command that edits a named path mid-run            -> `tree-moved`, exit 13
                                                              (`SEAM-TEST-RED`'s foreign
                                                              edit, made reproducible)
  (c) a named path deleted after the row was written       -> `check` exits 1,
                                                              `path_missing`
                                                              (`GRID-PARAMS-DIGEST-SUPERSEDE`:
                                                              grade_v5.py moved after a
                                                              green run)
  (d) a row that carries no `scope` block                  -> `undatable`, exit 0
                                                              (older rows are younger
                                                              rows, not defects)
  (e) a named path that is untracked                       -> `head_is_meaningful: false`
                                                              (cell.py/tree_freeze.py are
                                                              untracked; `sha f17663d1` then
                                                              names a commit that does not
                                                              contain the bytes)
  (f) `check` on a row whose tree is unchanged             -> `same`, exit 0

The tool reuses `tools/tree_freeze.py` for freezing and classification; these tests drive
it through the CLI so the EXIT CODES are the ones a caller sees, not a return value.

Offline: no request, no network, no live cell.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
TOOL = os.path.join(TOOLS, "verdict_scope.py")


def _repo_root(start):
    """The nearest ancestor carrying `.git`, so the suite also runs from a copied tree."""
    current = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise RuntimeError("no repository above %r" % (start,))
        current = parent


REPO = _repo_root(TOOLS)

#: A wrapper that edits its input 0.05 s into the run: the race, made reproducible.
MOVER = (
    "import sys, time\n"
    "time.sleep(0.05)\n"
    "with open(sys.argv[1], 'a', encoding='utf-8') as fh:\n"
    "    fh.write('# moved mid-run\\n')\n"
)


def _run(*args, cwd=REPO):
    return subprocess.run([sys.executable, TOOL] + list(args), capture_output=True,
                          text=True, cwd=cwd)


def _payload(done):
    """The paste-ready payload line: last JSON line on stdout."""
    for line in reversed(done.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError("no payload line on stdout:\n%s\n--- stderr ---\n%s"
                         % (done.stdout, done.stderr))


@pytest.fixture
def named(tmp_path):
    path = tmp_path / "load_bearing.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")
    return str(path)


def test_clean_command_names_its_bytes_and_exits_zero(named):
    """(a) A command that touches nothing named: moved [], exit 0, scope `clean`."""
    done = _run("run", "--paths", named, "--", sys.executable, "-c", "print('ok')")
    payload = _payload(done)
    assert done.returncode == 0
    assert payload["exitCode"] == 0
    assert payload["scope"]["moved"] == []
    assert payload["scope"]["verdict"] == "clean"
    assert payload["scope"]["exit"] == 0
    assert [row["moved"] for row in payload["scope"]["paths"]] == [False]


def test_command_editing_a_named_path_mid_run_is_tree_moved_not_failed(named):
    """(b) SEAM-TEST-RED: another writer moved the bytes; exit 13, both shas quoted."""
    before = subprocess.run([sys.executable, "-c", "import hashlib,sys;"
                             "print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())",
                             named], capture_output=True, text=True).stdout.strip()
    done = _run("run", "--paths", named, "--", sys.executable, "-c", MOVER, named)
    payload = _payload(done)
    assert done.returncode == 13, done.stderr
    assert payload["scope"]["moved"] == [named]
    assert payload["scope"]["verdict"] == "tree-moved"
    row = payload["scope"]["paths"][0]
    assert row["path"] == named and row["moved"] is True
    assert row["sha_before"] == before
    assert row["sha_after"] != row["sha_before"]
    assert len(row["sha_after"]) == 64 and len(row["sha_before"]) == 64
    # the command itself succeeded; the tree is what moved. Never `FAIL exit-1`.
    assert payload["exitCode"] == 0


def test_a_named_path_deleted_after_the_row_makes_check_exit_one(tmp_path):
    """(c) GRID-PARAMS-DIGEST-SUPERSEDE: the file the row judged is gone -> exit 1."""
    path = tmp_path / "graded.py"
    path.write_text("VALUE = 1\n", encoding="utf-8")
    done = _run("run", "--paths", str(path), "--", sys.executable, "-c", "print('green')")
    payload = _payload(done)
    assert done.returncode == 0
    path.unlink()
    checked = _run("check", "--row", json.dumps(payload))
    report = json.loads(checked.stdout.strip().splitlines()[-1])
    assert checked.returncode == 1, checked.stderr
    assert report["verdict"] == "path_missing"
    assert report["paths"][0]["state"] == "path_missing"
    assert report["paths"][0]["path"] == str(path)


def test_a_row_without_a_scope_block_is_undatable_not_a_defect():
    """(d) Every row written before this tool exists: `undatable`, exit 0."""
    row = {"command": "python3 -m pytest -q experiments/ptr-engine/tests/test_old.py",
           "exitCode": 0,
           "sha": "f17663d1fed0162a7dc3c5a0a58d372c710974c3"}
    done = _run("check", "--row", json.dumps(row))
    report = json.loads(done.stdout.strip().splitlines()[-1])
    assert done.returncode == 0, done.stderr
    assert report["verdict"] == "undatable"
    assert report["paths"] == []


def test_an_untracked_named_path_makes_head_unmeaningful(named):
    """(e) The row's sha must not be read as a statement about untracked bytes."""
    done = _run("run", "--paths", named, "--", sys.executable, "-c", "print('ok')")
    payload = _payload(done)
    assert done.returncode == 0
    assert payload["head_is_meaningful"] is False
    assert "untracked at HEAD" in payload["head_is_meaningful_because"]
    assert named in payload["head_is_meaningful_because"]
    # `sha` is still the measured HEAD (never invented), it is just not a claim about
    # these bytes.
    assert len(payload["sha"]) == 40


def test_a_tracked_named_path_leaves_head_meaningful():
    """(e, positive control) A tracked path IS in the commit the row names."""
    done = _run("run", "--paths", "AGENTS.md", "--", sys.executable, "-c", "print('ok')")
    payload = _payload(done)
    assert done.returncode == 0
    assert payload["head_is_meaningful"] is True
    assert payload["sha"] == subprocess.run(
        ["git", "--no-optional-locks", "-C", REPO, "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()


def test_check_on_an_unchanged_tree_says_same(named):
    """(f) The row is re-judgeable against present bytes."""
    done = _run("run", "--paths", named, "--", sys.executable, "-c", "print('ok')")
    payload = _payload(done)
    checked = _run("check", "--row", json.dumps(payload))
    report = json.loads(checked.stdout.strip().splitlines()[-1])
    assert checked.returncode == 0, checked.stderr
    assert report["verdict"] == "same"
    assert report["paths"][0]["state"] == "same"


def test_check_reports_drift_since_the_row_without_failing(named):
    """A file that moved AFTER the row is `moved_since`, exit 0 -- the row already said
    which bytes it judged, so drift is information, not a verdict."""
    done = _run("run", "--paths", named, "--", sys.executable, "-c", "print('ok')")
    payload = _payload(done)
    with open(named, "a", encoding="utf-8") as fh:
        fh.write("VALUE = 2\n")
    checked = _run("check", "--row", json.dumps(payload))
    report = json.loads(checked.stdout.strip().splitlines()[-1])
    assert checked.returncode == 0, checked.stderr
    assert report["verdict"] == "moved_since"
    assert report["paths"][0]["state"] == "moved_since"


def test_the_payload_is_paste_ready_and_never_an_invented_exit(named):
    """`command` re-quotes the exact argv and `exitCode` is the measured exit, not 13."""
    argv = [sys.executable, "-c", "import sys; sys.exit(7)"]
    done = _run("run", "--paths", named, "--", *argv)
    payload = _payload(done)
    assert done.returncode == 7
    assert payload["exitCode"] == 7
    assert payload["argv"] == argv
    assert shlex.split(payload["command"]) == argv
    assert payload["scope"]["exit"] == 7
    assert payload["scope"]["verdict"] == "clean"


def test_an_empty_path_set_is_refused_before_the_command_runs(tmp_path):
    """A row that names no bytes is the defect this tool exists for: exit 2, no row."""
    marker = tmp_path / "ran"
    done = _run("run", "--paths", "--", sys.executable, "-c",
                "open(%r, 'w').close()" % (str(marker),))
    assert done.returncode == 2
    assert "no bytes" in done.stderr
    assert not marker.exists()
    assert "{" not in done.stdout


def test_a_refused_phantom_path_exits_two_and_writes_no_row(tmp_path):
    """A path that does not exist cannot be frozen; the command is never started."""
    missing = tmp_path / "never_existed.py"
    marker = tmp_path / "ran"
    done = _run("run", "--paths", str(missing), "--", sys.executable, "-c",
                "open(%r, 'w').close()" % (str(marker),))
    assert done.returncode == 2
    assert "does not exist" in done.stderr
    assert not marker.exists()
    assert "{" not in done.stdout
