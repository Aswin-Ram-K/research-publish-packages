"""Offline tests for commit-pinned source resolution (``docket.git_source``).

Everything here runs against ``tmp_path`` git repositories — no network, no
LLM, no touching the real acceptance target.
"""

from __future__ import annotations

import builtins
import os
import stat
import subprocess
from pathlib import Path

import pytest

from resextract.docket.git_source import (
    CommitNotFound,
    GitObjectSource,
    PathIsDirectoryAtCommit,
    PathIsSymlinkAtCommit,
    PathNotFoundAtCommit,
    PinnedIntegrityError,
    SourcePathRefused,
    WorkingTreeSource,
    commit_exists,
    normalise_repo_relative,
    resolve_head,
    verify_pinned,
)


# --------------------------------------------------------------------------- #
# rig
# --------------------------------------------------------------------------- #


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git_hash_blob(repo: Path, data: bytes) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--stdin"],
        input=data,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.decode().strip()


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A", ".")
    git(repo, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "unit@example.invalid")
    git(r, "config", "user.name", "Unit Test")
    git(r, "config", "commit.gpgsign", "false")
    (r / "README.md").write_bytes(b"committed\n")
    commit_all(r, "c1")
    return r


# --------------------------------------------------------------------------- #
# the central test
# --------------------------------------------------------------------------- #


def test_pinned_bytes_beat_a_dirty_working_tree(repo: Path) -> None:
    """Pinned = the committed bytes; working tree = whatever is on disk now."""
    (repo / "README.md").write_bytes(b"dirty local edit\n")
    head = resolve_head(repo)

    pinned = GitObjectSource(repo, head).resolve("README.md")
    assert pinned.bytes_ == b"committed\n"
    assert pinned.resolved_from == "git_object"
    assert pinned.commit_sha == head

    working = WorkingTreeSource(repo).resolve("README.md")
    assert working is not None
    assert working.bytes_ == b"dirty local edit\n"
    assert working.resolved_from == "working_tree"

    # The two sources disagree precisely because the working tree is dirty.
    assert pinned.sha256 != working.sha256


def test_pinned_sha256_matches_git_blob_identity(repo: Path) -> None:
    head = resolve_head(repo)
    pinned = GitObjectSource(repo, head).resolve("README.md")

    blob = git(repo, "rev-parse", f"{head}:README.md")
    assert pinned.blob_sha == blob
    # git's blob id is sha1("blob <len>\\0" + bytes) — the same bytes, two hashes.
    assert git_hash_blob(repo, pinned.bytes_) == blob

    (repo / "README.md").write_bytes(b"changed after the commit\n")
    working = WorkingTreeSource(repo).resolve("README.md")
    assert working is not None
    assert working.sha256 != pinned.sha256


def test_two_commits_of_the_same_path_differ(repo: Path) -> None:
    first = resolve_head(repo)
    (repo / "README.md").write_bytes(b"second revision\n")
    commit_all(repo, "c2")
    second = resolve_head(repo)
    assert first != second

    p1 = GitObjectSource(repo, first).resolve("README.md")
    p2 = GitObjectSource(repo, second).resolve("README.md")
    assert p1.bytes_ == b"committed\n"
    assert p2.bytes_ == b"second revision\n"
    assert p1.sha256 != p2.sha256
    assert p1.blob_sha != p2.blob_sha


# --------------------------------------------------------------------------- #
# RED->GREEN guard 1
# --------------------------------------------------------------------------- #


def test_missing_at_commit_is_typed_error_and_never_falls_back(repo: Path) -> None:
    """RED->GREEN guard: "the pinned source never falls back to the working tree".

    The file exists on disk but not at HEAD.  A resolver that falls back (reads
    the working tree when ``git ls-tree`` lists nothing) returns a ``PinnedFile``
    here and this test fails.  With the guard in place it raises
    :class:`PathNotFoundAtCommit`, and it raises **exactly the same** error after
    the disk file is deleted — so the error cannot have come from the disk.

    Reverted-guard failure (``ls-tree`` empty -> read the working tree):

        E       Failed: DID NOT RAISE PathNotFoundAtCommit
        FAILED tests/test_git_source.py::test_missing_at_commit_is_typed_error_and_never_falls_back
        FAILED tests/test_git_source.py::test_directory_at_commit_is_typed_error
        2 failed, 19 passed in 0.23s
    """
    head = resolve_head(repo)
    src = GitObjectSource(repo, head)
    later = repo / "later.txt"
    later.write_bytes(b"added after the commit\n")
    assert later.exists()  # it is right there on disk ...

    with pytest.raises(PathNotFoundAtCommit):
        src.resolve("later.txt")

    later.unlink()  # ... and deleting it changes nothing about the error
    with pytest.raises(PathNotFoundAtCommit) as after_delete:
        src.resolve("later.txt")
    assert after_delete.type is PathNotFoundAtCommit


def test_git_object_source_never_opens_the_working_tree(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A spy on ``open`` proves the working tree is never read for content."""
    opened: list[str] = []
    real_open = builtins.open

    def spy(file, *args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            opened.append(os.fspath(file))
        except TypeError:  # pragma: no cover - non-path file objects
            pass
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    head = resolve_head(repo)
    (repo / "README.md").write_bytes(b"dirty and irrelevant\n")

    pinned = GitObjectSource(repo, head).resolve("README.md")
    assert pinned.bytes_ == b"committed\n"
    assert not [p for p in opened if str(p).startswith(str(repo))]


# --------------------------------------------------------------------------- #
# refusal: containment, .worktrees, directories, symlinks
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad",
    [
        "../etc/passwd",
        "/etc/passwd",
        "C:/Windows/win.ini",
        "docs/../../outside.txt",
        ".worktrees/run-1/tools/selfbuild/loop.ts",
        "nested/.worktrees/run-2/x.txt",
        "",
    ],
)
def test_containment_and_worktree_refusals(repo: Path, bad: str) -> None:
    head = resolve_head(repo)
    with pytest.raises(SourcePathRefused):
        GitObjectSource(repo, head).resolve(bad)
    with pytest.raises(SourcePathRefused):
        WorkingTreeSource(repo).resolve(bad)


def test_normalise_repo_relative_accepts_plain_paths() -> None:
    assert normalise_repo_relative("src/resextract/cli.py") == "src/resextract/cli.py"
    assert normalise_repo_relative("./README.md") == "README.md"
    assert normalise_repo_relative("src\\resextract\\cli.py") == "src/resextract/cli.py"


def test_directory_at_commit_is_typed_error(repo: Path) -> None:
    before = resolve_head(repo)
    (repo / "pkg").mkdir()
    (repo / "pkg" / "mod.py").write_bytes(b"X = 1\n")
    commit_all(repo, "add package dir")
    after = resolve_head(repo)

    # present at `after`, absent at `before`: two different typed errors.
    with pytest.raises(PathIsDirectoryAtCommit):
        GitObjectSource(repo, after).resolve("pkg")
    with pytest.raises(PathNotFoundAtCommit):
        GitObjectSource(repo, before).resolve("pkg")
    # ... and it resolves fine once a file is named, not the tree.
    assert GitObjectSource(repo, after).resolve("pkg/mod.py").bytes_ == b"X = 1\n"


def test_symlink_at_commit_is_typed_error(repo: Path) -> None:
    os.symlink("README.md", repo / "link.md")
    commit_all(repo, "add symlink")
    head = resolve_head(repo)
    with pytest.raises(PathIsSymlinkAtCommit):
        GitObjectSource(repo, head).resolve("link.md")


def test_unknown_commit_is_typed_error(repo: Path) -> None:
    with pytest.raises(CommitNotFound):
        GitObjectSource(repo, "0" * 40)
    assert commit_exists(repo, resolve_head(repo)) is True
    assert commit_exists(repo, "0" * 40) is False
    assert commit_exists(repo, "") is False


# --------------------------------------------------------------------------- #
# bytes, atomicity, mode, verification
# --------------------------------------------------------------------------- #


def test_binary_file_round_trips_byte_exactly(repo: Path, tmp_path: Path) -> None:
    payload = bytes(range(256)) * 8 + b"\x00\xff\x00tail"
    (repo / "assets").mkdir()
    (repo / "assets" / "logo.bin").write_bytes(payload)
    commit_all(repo, "add binary")
    head = resolve_head(repo)

    pinned = GitObjectSource(repo, head).resolve("assets/logo.bin")
    assert pinned.bytes_ == payload
    assert b"\x00" in pinned.bytes_

    dest = tmp_path / "out" / "logo.bin"
    pinned.write_to(dest)
    assert dest.read_bytes() == payload
    assert verify_pinned(pinned, dest) == pinned.sha256


def test_write_to_is_atomic_and_strips_setuid(repo: Path, tmp_path: Path) -> None:
    script = repo / "script.sh"
    script.write_bytes(b"#!/bin/sh\necho hi\n")
    os.chmod(script, 0o4755)  # setuid + executable

    working = WorkingTreeSource(repo).resolve("script.sh")
    assert working is not None
    out_dir = tmp_path / "out"
    dest = Path(working.write_to(out_dir / "script.sh"))

    mode = stat.S_IMODE(dest.stat().st_mode)
    assert mode == 0o755
    assert mode & (stat.S_ISUID | stat.S_ISGID | stat.S_ISVTX) == 0
    assert dest.read_bytes() == script.read_bytes()
    # atomic: the temp file was replaced, nothing else was left behind
    assert [p.name for p in out_dir.iterdir()] == ["script.sh"]


def test_git_object_source_preserves_exec_bit(repo: Path) -> None:
    tool = repo / "tool.sh"
    tool.write_bytes(b"#!/bin/sh\nexit 0\n")
    os.chmod(tool, 0o755)
    commit_all(repo, "executable")
    head = resolve_head(repo)
    pinned = GitObjectSource(repo, head).resolve("tool.sh")
    assert pinned.git_mode == 0o100755
    assert pinned.executable is True
    assert stat.S_IMODE(pinned.mode) == 0o755


def test_verify_pinned_detects_a_tampered_destination(repo: Path, tmp_path: Path) -> None:
    head = resolve_head(repo)
    pinned = GitObjectSource(repo, head).resolve("README.md")
    dest = tmp_path / "material" / "README.md"
    pinned.write_to(dest)
    assert verify_pinned(pinned, dest) == pinned.sha256

    dest.write_bytes(b"tampered\n")
    with pytest.raises(PinnedIntegrityError) as excinfo:
        verify_pinned(pinned, dest)
    assert excinfo.value.expected == pinned.sha256
    assert excinfo.value.actual != pinned.sha256

    with pytest.raises(PinnedIntegrityError):
        verify_pinned(pinned, tmp_path / "material" / "absent.md")


def test_pinned_file_dict_carries_both_identities(repo: Path) -> None:
    head = resolve_head(repo)
    pinned = GitObjectSource(repo, head).resolve("README.md")
    d = pinned.to_dict()
    assert d["resolved_from"] == "git_object"
    assert d["blob_sha"] == git(repo, "rev-parse", f"{head}:README.md")
    assert d["sha8"] == pinned.sha256[:8]
    assert d["bytes"] == len(b"committed\n")
