"""The baseline guard must bite: a tampered copy makes `verify` exit 1.

Red test: a scratch tree is copied out of the workspace, snapshotted with
``--root`` pointing at the copy, and then ONE file in the copy is appended to.
``verify`` must exit 1, name the changed file, and print both shas.  The green
control in the same test proves the guard is not simply always-red.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOL = os.path.join(REPO_ROOT, "experiments", "ptr-engine", "tools", "harness_baseline.py")
sys.path.insert(0, os.path.dirname(TOOL))

import harness_baseline  # noqa: E402


def _scratch_tree(dst):
    """Copy every harness file into ``dst`` keeping repo-relative paths."""
    for rel in harness_baseline.SNAPSHOT_PATHS:
        src = os.path.join(REPO_ROOT, rel)
        assert os.path.isfile(src), "harness file missing from the workspace: %s" % rel
        out = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(src, out)
    return dst


def _run(*args):
    return subprocess.run(
        [sys.executable, TOOL, *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def test_snapshot_verify_green_then_red(tmp_path):
    work = _scratch_tree(str(tmp_path / "repo"))
    bases = str(tmp_path / "bases")

    snap = _run("snapshot", "--root", work, "--out", bases, "--label", "T0")
    assert snap.returncode == 0, snap.stderr
    bdir = os.path.join(bases, "T0")
    manifest = json.load(open(os.path.join(bdir, "MANIFEST.json"), encoding="utf-8"))
    assert len(manifest["files"]) == len(harness_baseline.SNAPSHOT_PATHS)
    assert len(manifest["harness_sha256_of_HARNESS_FILES"]) == 64

    green = _run("verify", bdir, "--root", work)
    assert green.returncode == 0, green.stdout + green.stderr
    assert "0 differing file(s)" in green.stdout

    victim = "experiments/ptr-engine/longrun/cell.py"
    target = os.path.join(work, victim)
    before = harness_baseline.sha256_file(target)
    with open(target, "ab") as fh:
        fh.write(b"\n# tampered by the red test\n")
    after = harness_baseline.sha256_file(target)
    assert after != before

    red = _run("verify", bdir, "--root", work)
    assert red.returncode == 1, red.stdout
    assert "moved" in red.stdout
    assert victim in red.stdout
    assert before in red.stdout and after in red.stdout
    assert "1 differing file(s)" in red.stdout

    # The deleted branch must also bite.
    os.remove(target)
    gone = _run("verify", bdir, "--root", work)
    assert gone.returncode == 1
    assert "deleted" in gone.stdout and victim in gone.stdout
