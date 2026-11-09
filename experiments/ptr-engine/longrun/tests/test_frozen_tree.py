#!/usr/bin/env python3
"""Red->green tests for tools/frozen_tree.py (unit FROZEN-TREE).

Offline, stdlib only, no network, no ``git`` invocation anywhere.

(a) three-file snapshot reproduces the source sha256s and a canonical snapshot_sha256
(b) a command that edits its own input mid-run -> inputs_unchanged false, exit 2, relpath named
(c) a failing command (exit 1) with stable inputs -> inputs_unchanged true, exit 1, changed []
(d) a missing input path -> exit 3-class refusal naming the path, no dest left behind
(e) a symlink pointing outside the workspace root -> refused, named
(f) snapshot_sha256 stable across two snapshots of the same bytes at different times,
    changes when one byte changes
(g) --json stdout parses as the result object with no extra output
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
TOOLS = HERE.parents[2] / "tools"
REPO = HERE.parents[4]
TOOL = TOOLS / "frozen_tree.py"

sys.path.insert(0, str(TOOLS))
import frozen_tree  # noqa: E402
from frozen_tree import snapshot, verify, verdict_exit_code, snapshot_sha256  # noqa: E402


# ---------------------------------------------------------------- helpers

def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=300,
    )


@pytest.fixture()
def tree(tmp_path):
    """A tiny workspace root with three files, used by most tests."""
    root = tmp_path / "ws"
    root.mkdir()
    (root / "a.txt").write_text("alpha\n", encoding="utf-8")
    (root / "b.txt").write_text("bravo\n", encoding="utf-8")
    sub = root / "pkg"
    sub.mkdir()
    (sub / "c.txt").write_text("charlie\n", encoding="utf-8")
    return root


# ---------------------------------------------------------------- (a)

def test_a_snapshot_reproduces_digests(tree, tmp_path):
    dest = tmp_path / "snap"
    manifest = snapshot(["a.txt", "b.txt", "pkg/c.txt"], dest, root=tree)

    assert dest.is_dir()
    snap_json = json.loads((dest / "SNAPSHOT.json").read_text(encoding="utf-8"))
    by_rel = {f["relpath"]: f for f in snap_json["files"]}
    assert sorted(by_rel) == ["a.txt", "b.txt", "pkg/c.txt"]

    for rel in ("a.txt", "b.txt", "pkg/c.txt"):
        assert by_rel[rel]["sha256"] == sha(tree / rel), rel
        assert by_rel[rel]["bytes"] == (tree / rel).stat().st_size
        assert isinstance(by_rel[rel]["mtime_ns"], int)
        # the copy is byte-identical and content-preserving at the same rel path
        assert sha(dest / rel) == sha(tree / rel)
        assert (dest / rel).read_text(encoding="utf-8") == (tree / rel).read_text(encoding="utf-8")

    assert manifest["snapshot_sha256"] == snap_json["snapshot_sha256"]
    # canonical: sha256 over sorted [{"relpath","sha256"}] with fixed separators
    canonical = json.dumps(
        [{"relpath": r, "sha256": by_rel[r]["sha256"]} for r in sorted(by_rel)],
        sort_keys=True,
        separators=(",", ":"),
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert manifest["snapshot_sha256"] == expected
    assert snapshot_sha256(snap_json["files"]) == expected


# ---------------------------------------------------------------- (b)

def test_b_mutated_input_is_fatal(tree, tmp_path):
    dest = tmp_path / "snap"
    snapshot(["a.txt", "b.txt"], dest, root=tree)

    res = verify(
        dest,
        [sys.executable, "-c", "open('a.txt','a').write('MUTATED')"],
    )
    assert res["inputs_unchanged"] is False
    assert res["changed"] == ["a.txt"]
    assert res["exit_code"] == 0  # the command itself succeeded; the snapshot did not hold
    assert verdict_exit_code(res) == 2
    assert res["snapshot_sha256"]

    # CLI agrees, and --json still emits exactly one object
    proc = cli("verify", "--json", "--snapshot", str(dest), "--",
               sys.executable, "-c", "open('a.txt','a').write('MUTATED')")
    assert proc.returncode == 2, proc.stdout + proc.stderr
    obj = json.loads(proc.stdout)
    assert obj["inputs_unchanged"] is False and obj["changed"] == ["a.txt"]


# ---------------------------------------------------------------- (c)

def test_c_failing_command_with_stable_inputs(tree, tmp_path):
    dest = tmp_path / "snap"
    snapshot(["a.txt", "b.txt"], dest, root=tree)

    res = verify(dest, [sys.executable, "-c", "import sys; sys.exit(1)"])
    assert res["inputs_unchanged"] is True
    assert res["changed"] == []
    assert res["exit_code"] == 1
    assert verdict_exit_code(res) == 1

    proc = cli("verify", "--json", "--snapshot", str(dest), "--",
               sys.executable, "-c", "import sys; sys.exit(1)")
    assert proc.returncode == 1, proc.stdout + proc.stderr


# ---------------------------------------------------------------- (d)

def test_d_missing_input_refused_and_no_partial_dest(tree, tmp_path):
    dest = tmp_path / "never"
    with pytest.raises(frozen_tree.SnapshotRefused) as ei:
        snapshot(["a.txt", "nope/missing.txt"], dest, root=tree)
    assert "nope/missing.txt" in str(ei.value)
    assert not dest.exists(), "a refused snapshot must not leave a dest behind"

    proc = cli("snapshot", "--dest", str(dest), str(tree / "a.txt"), "nope/missing.txt", cwd=tree)
    # relative paths are resolved against the workspace root (cwd), so nope/missing.txt is absent
    assert proc.returncode in (3,), proc.stdout + proc.stderr
    assert "nope/missing.txt" in (proc.stdout + proc.stderr)
    assert not dest.exists()


# ---------------------------------------------------------------- (e)

def test_e_symlink_escaping_root_refused(tree, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("outside the workspace\n", encoding="utf-8")
    link = tree / "leak.txt"
    os.symlink(outside, link)

    dest = tmp_path / "snap"
    with pytest.raises(frozen_tree.SnapshotRefused) as ei:
        snapshot(["a.txt", "leak.txt"], dest, root=tree)
    msg = str(ei.value)
    assert "leak.txt" in msg
    assert "outside" in msg or "escape" in msg.lower()
    assert not dest.exists()

    proc = cli("snapshot", "--dest", str(dest), "a.txt", "leak.txt", cwd=tree)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "leak.txt" in (proc.stdout + proc.stderr)
    assert not dest.exists()


# ---------------------------------------------------------------- (f)

def test_f_snapshot_sha256_is_stable_and_content_sensitive(tree, tmp_path):
    s1 = snapshot(["a.txt", "b.txt"], tmp_path / "s1", root=tree)["snapshot_sha256"]
    time.sleep(0.02)
    # rewrite the same bytes (new mtime) -> identity must not move
    for rel in ("a.txt", "b.txt"):
        (tree / rel).write_text((tree / rel).read_text(encoding="utf-8"), encoding="utf-8")
    time.sleep(0.02)
    s2 = snapshot(["a.txt", "b.txt"], tmp_path / "s2", root=tree)["snapshot_sha256"]
    assert s1 == s2

    (tree / "b.txt").write_text("bravo!\n", encoding="utf-8")  # one byte added
    s3 = snapshot(["a.txt", "b.txt"], tmp_path / "s3", root=tree)["snapshot_sha256"]
    assert s3 != s1


# ---------------------------------------------------------------- (g)

def test_g_json_stdout_is_only_the_result_object(tree, tmp_path):
    dest = tmp_path / "snap"
    snapshot(["a.txt"], dest, root=tree)

    proc = cli("verify", "--json", "--snapshot", str(dest), "--",
               sys.executable, "-c", "print('hello from the command')")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    obj = json.loads(proc.stdout)  # parses whole stdout: no banner, no human prose
    assert set(obj) == {
        "command", "exit_code", "duration_ms", "inputs_unchanged",
        "changed", "snapshot_sha256", "stdout_tail", "stderr_tail",
    }
    assert obj["exit_code"] == 0
    assert obj["inputs_unchanged"] is True
    assert obj["changed"] == []
    assert "hello from the command" in obj["stdout_tail"]
    assert proc.stdout.strip().startswith("{") and proc.stdout.strip().endswith("}")
