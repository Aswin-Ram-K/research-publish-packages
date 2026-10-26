"""Offline tests for concurrent-writer detection (``refresh.writer``).

``tmp_path`` git repositories only; the observation window is either tiny or
faked so the whole file stays fast, and nothing here touches a live target.
"""

from __future__ import annotations

import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from resextract.refresh import writer as writer_mod
from resextract.refresh.writer import (
    WORKER_VERDICTS,
    TargetBusyError,
    WriterSignal,
    assert_quiescent,
    detect_concurrent_writer,
    tracked_mtime_snapshot,
)


# --------------------------------------------------------------------------- #
# rig
# --------------------------------------------------------------------------- #


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    assert proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr.strip()}"
    return proc.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "unit@example.invalid")
    git(r, "config", "user.name", "Unit Test")
    git(r, "config", "commit.gpgsign", "false")
    (r / "a.txt").write_bytes(b"a\n")
    (r / "b.txt").write_bytes(b"b\n")
    git(r, "add", "-A", ".")
    git(r, "commit", "-q", "-m", "c1")
    return r


def commit(repo: Path, name: str, text: str, message: str) -> None:
    (repo / name).write_bytes(text.encode())
    git(repo, "add", "-A", ".")
    git(repo, "commit", "-q", "-m", message)


def freezegun_style_sleep(monkeypatch: pytest.MonkeyPatch, action, *, limit: float) -> None:
    """Replace ``writer.time`` so the window's sleep runs ``action`` instead.

    Deterministic: the "concurrent" write happens exactly between the two reads.
    Also asserts the module never asks to sleep longer than ``limit``.
    """

    def fake_sleep(seconds: float) -> None:
        assert seconds <= limit + 1e-9, f"sleep {seconds}s exceeds window {limit}s"
        action()

    monkeypatch.setattr(writer_mod, "time", SimpleNamespace(sleep=fake_sleep))


# --------------------------------------------------------------------------- #
# verdicts
# --------------------------------------------------------------------------- #


def test_quiet_repo_is_quiescent(repo: Path) -> None:
    before = tracked_mtime_snapshot(repo)
    signal = detect_concurrent_writer(repo, window_s=0.05)

    assert signal.verdict == "quiescent"
    assert signal.quiescent is True
    assert signal.files_touched_in_window == 0
    assert signal.head_before == signal.head_after
    assert signal.new_untracked == ()
    assert signal.newest_mtime_utc is not None
    assert signal.newest_mtime_utc.endswith("Z")
    assert signal.note
    assert signal.worktree_dirs_present == 0
    assert before.count == 2
    assert signal.as_dict()["verdict"] == "quiescent"


def test_commit_between_reads_is_head_moved(repo: Path) -> None:
    """A real concurrent commit, via a thread that writes inside the window."""
    head_before = git(repo, "rev-parse", "HEAD")

    def writer() -> None:
        time.sleep(0.3)
        commit(repo, "a.txt", "moved\n", "c2")

    thread = threading.Thread(target=writer)
    thread.start()
    try:
        signal = detect_concurrent_writer(repo, window_s=1.0)
    finally:
        thread.join()

    assert signal.verdict == "head_moved"
    assert signal.head_before == head_before
    assert signal.head_after != head_before
    assert signal.head_moved is True
    assert signal.files_touched_in_window >= 1  # the commit rewrote a.txt
    assert signal.newest_mtime_utc is not None


def test_dirty_file_between_reads_is_active_writer(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = repo / "a.txt"
    before_ns = target.stat().st_mtime_ns

    def touch() -> None:
        time.sleep(0.005)  # real time module: guarantee a different mtime_ns
        target.write_bytes(b"touched, never committed\n")

    freezegun_style_sleep(monkeypatch, touch, limit=0.2)
    head_before = git(repo, "rev-parse", "HEAD")
    signal = detect_concurrent_writer(repo, window_s=0.2)

    assert signal.verdict == "active_writer"
    assert signal.head_before == signal.head_after == head_before
    assert signal.files_touched_in_window >= 1
    assert target.stat().st_mtime_ns > before_ns
    # the reported newest mtime is *this* file's new mtime, at second precision
    expected = datetime.fromtimestamp(
        target.stat().st_mtime_ns / 1_000_000_000, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert signal.newest_mtime_utc == expected
    assert signal.newest_mtime_utc >= datetime.fromtimestamp(
        before_ns / 1_000_000_000, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert "a.txt" in signal.note


def test_new_untracked_entry_is_active_writer(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def appear() -> None:
        (repo / "brand-new.txt").write_bytes(b"untracked\n")

    freezegun_style_sleep(monkeypatch, appear, limit=0.2)
    signal = detect_concurrent_writer(repo, window_s=0.2)

    assert signal.verdict == "active_writer"
    assert signal.files_touched_in_window == 0  # nothing *tracked* changed ...
    assert signal.new_untracked  # ... but the untracked set grew
    assert "brand-new.txt" in signal.new_untracked


# --------------------------------------------------------------------------- #
# RED->GREEN guard 2
# --------------------------------------------------------------------------- #


def test_assert_quiescent_refuses_a_busy_target(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RED->GREEN guard: "assert_quiescent refuses a busy target".

    With the guard removed (``assert_quiescent`` returns the signal
    unconditionally), ``pytest.raises(TargetBusyError)`` sees no exception and
    the test fails:

        E       Failed: DID NOT RAISE TargetBusyError
        FAILED tests/test_writer_detection.py::test_assert_quiescent_refuses_a_busy_target
        FAILED tests/test_writer_detection.py::test_assert_quiescent_refuses_a_moved_head
        2 failed, 10 passed in 1.41s

    The error must say what moved and when, so the message is asserted too.
    """

    def touch() -> None:
        time.sleep(0.005)
        (repo / "a.txt").write_bytes(b"busy\n")

    freezegun_style_sleep(monkeypatch, touch, limit=0.2)

    with pytest.raises(TargetBusyError) as excinfo:
        assert_quiescent(repo, window_s=0.2)

    error = excinfo.value
    assert error.signal.verdict == "active_writer"
    message = str(error)
    assert "not quiescent" in message
    assert "a.txt" in message or "tracked file" in message
    assert "newest tracked-file mtime" in message
    assert "allow_active=True" in message

    # the opt-in is explicit and does not raise
    signal = assert_quiescent(repo, window_s=0.2, allow_active=True)
    assert signal.verdict == "active_writer"


def test_assert_quiescent_passes_on_a_quiet_repo(repo: Path) -> None:
    signal = assert_quiescent(repo, window_s=0.05)
    assert signal.verdict == "quiescent"
    assert signal.as_dict()["path"] == str(repo)


def test_assert_quiescent_refuses_a_moved_head(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    freezegun_style_sleep(
        monkeypatch, lambda: commit(repo, "a.txt", "c2\n", "c2"), limit=0.2
    )
    with pytest.raises(TargetBusyError) as excinfo:
        assert_quiescent(repo, window_s=0.2)
    assert excinfo.value.signal.verdict == "head_moved"
    assert "HEAD moved" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# bounded walk / never descends
# --------------------------------------------------------------------------- #


def test_walk_never_descends_into_worktrees(repo: Path) -> None:
    worktrees = repo / ".worktrees"
    sentinel_dir = worktrees / "run-1"
    sentinel_dir.mkdir(parents=True)
    for i in range(400):
        (sentinel_dir / f"churn-{i}.txt").write_bytes(b"live sibling worktree\n")
    sentinel = sentinel_dir / "SENTINEL_NEVER_COUNTED"
    sentinel.write_bytes(b"if this is counted, the walk descended\n")
    (worktrees / "run-2").mkdir()
    (worktrees / "not-a-run-dir").mkdir()

    snapshot = tracked_mtime_snapshot(repo)
    # exactly the tracked files — the 400+ files under .worktrees/ cost nothing
    assert set(snapshot.stats) == {"a.txt", "b.txt"}
    assert snapshot.count == 2
    assert snapshot.total_tracked == 2
    assert not any(".worktrees" in rel for rel in snapshot.stats)
    assert "SENTINEL_NEVER_COUNTED" not in "".join(snapshot.stats)

    signal = detect_concurrent_writer(repo, window_s=0.05)
    assert signal.verdict == "quiescent"
    assert signal.files_touched_in_window == 0
    assert signal.worktree_dirs_present == 2  # observation: run-1, run-2


def test_snapshot_honours_max_files_bound(repo: Path) -> None:
    snapshot = tracked_mtime_snapshot(repo, max_files=1)
    assert snapshot.count == 1
    assert snapshot.truncated is True
    assert snapshot.total_tracked == 2
    assert any("bounded at 1" in w for w in snapshot.warnings)


# --------------------------------------------------------------------------- #
# never raises
# --------------------------------------------------------------------------- #


def test_git_failure_is_recorded_in_note_not_raised(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every git call fails: the verdict degrades, the failure lands in ``note``."""
    from resextract.refresh import staleness

    def boom(target, *args, **kwargs):  # type: ignore[no-untyped-def]
        return 128, "", f"fatal: simulated git failure in {target}"

    monkeypatch.setattr(staleness, "_git", boom)
    monkeypatch.setattr(writer_mod, "_git", boom)

    signal = detect_concurrent_writer(repo, window_s=0.05)

    assert signal.verdict in WORKER_VERDICTS
    assert signal.verdict == "quiescent"  # only what was observable
    assert signal.head_before is None and signal.head_after is None
    assert signal.files_touched_in_window == 0
    assert "simulated git failure" in signal.note
    assert "git rev-parse HEAD failed" in signal.note
    assert "no tracked files" in signal.note


def test_missing_directory_is_recorded_not_raised(tmp_path: Path) -> None:
    signal = detect_concurrent_writer(tmp_path / "does-not-exist", window_s=0.0)
    assert signal.verdict in WORKER_VERDICTS
    assert signal.note


def test_signal_rejects_unknown_verdict() -> None:
    with pytest.raises(ValueError, match="verdict must be one of"):
        WriterSignal(
            verdict="maybe",
            head_before=None,
            head_after=None,
            dirty_before=(),
            dirty_after=(),
            files_touched_in_window=0,
            newest_mtime_utc=None,
            worktree_dirs_present=0,
            note="",
        )


# --------------------------------------------------------------------------- #
# RED->GREEN guard A (defect U7.2-1)
# --------------------------------------------------------------------------- #


def _policy_for(repo: Path, **over):
    from resextract.kg.policy import TargetPolicy

    kw = dict(slug="fixture", path=str(repo), include=[], exclude=[], assert_present=[])
    kw.update(over)
    return TargetPolicy(**kw)


def test_existing_untracked_admitted_file_change_is_active_writer(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RED->GREEN guard A: a write INSIDE an existing untracked admitted dir.

    Revert: drop ``changed_untracked`` from the verdict expression in
    ``_detect`` (``elif files_touched or new_untracked:``).  Measured failure —
    the old behaviour read a same-size content rewrite quiescent:

        >       assert signal.verdict == "active_writer"
        E       AssertionError: assert 'quiescent' == 'active_writer'
        FAILED tests/test_writer_detection.py::test_existing_untracked_admitted_file_change_is_active_writer
        1 failed

    The directory pre-exists and no new entry appears, which is exactly the
    blind spot: git reports ``?? .lane-j-scratch/`` identically before and after.
    """
    scratch = repo / ".lane-j-scratch"
    scratch.mkdir()
    mono = scratch / "monograph.txt"
    mono.write_bytes(b"x" * 4096)
    (scratch / "consonance.txt").write_bytes(b"y" * 16)
    policy = _policy_for(
        repo,
        include=[".lane-j-scratch/**"],
        assert_present=[".lane-j-scratch/monograph.txt"],
    )
    assert policy.admit(".lane-j-scratch/monograph.txt").admitted is True

    def mutate() -> None:
        time.sleep(0.005)
        mono.write_bytes(b"z" * 4096)  # SAME size: only the identity can reveal it

    freezegun_style_sleep(monkeypatch, mutate, limit=0.2)
    signal = detect_concurrent_writer(repo, window_s=0.2, policy=policy)

    assert signal.verdict == "active_writer"
    assert signal.files_touched_in_window == 0, "nothing tracked changed"
    assert signal.new_untracked == (), "no new untracked entry appeared"
    assert ".lane-j-scratch/monograph.txt" in signal.untracked_changed
    assert signal.untracked_watched >= 2
    assert signal.untracked_hashed >= 1
    assert ".lane-j-scratch/monograph.txt" in signal.note


def test_untracked_dir_the_policy_rejects_is_not_watched(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Policy basis: an untracked dir the policy does not admit is not signal.

    ``config_exclude`` narrows admission (``TargetPolicy.admit``), so a churn
    inside it is deliberately not depended-upon and must not be watched.
    """
    other = repo / "scratch-unadmitted"
    other.mkdir()
    f = other / "churn.txt"
    f.write_bytes(b"1")
    policy = _policy_for(repo, exclude=["scratch-unadmitted/**"])
    adm = policy.admit("scratch-unadmitted/churn.txt")
    assert adm.admitted is False and adm.source == "config_exclude"

    freezegun_style_sleep(monkeypatch, lambda: f.write_bytes(b"2"), limit=0.2)
    signal = detect_concurrent_writer(repo, window_s=0.2, policy=policy)

    assert signal.untracked_watched == 0
    assert "scratch-unadmitted/churn.txt" not in signal.untracked_changed
    assert signal.verdict == "quiescent"


def test_new_untracked_entry_still_active_with_policy(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: the old new-entry signal must not be lost."""
    policy = _policy_for(repo)
    freezegun_style_sleep(
        monkeypatch, lambda: (repo / "brand-new.txt").write_bytes(b"n\n"), limit=0.2
    )
    signal = detect_concurrent_writer(repo, window_s=0.2, policy=policy)
    assert signal.verdict == "active_writer"
    assert "brand-new.txt" in signal.new_untracked


def test_tracked_change_still_active_with_policy(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a tracked-file change keeps its verdict."""
    policy = _policy_for(repo)
    freezegun_style_sleep(
        monkeypatch, lambda: (repo / "a.txt").write_bytes(b"dirty\n"), limit=0.2
    )
    signal = detect_concurrent_writer(repo, window_s=0.2, policy=policy)
    assert signal.verdict == "active_writer"
    assert signal.files_touched_in_window >= 1


def test_untracked_bounds_record_caps_hit(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The caps bind and are recorded; bytes read stay bounded."""
    scratch = repo / ".lane-j-scratch"
    scratch.mkdir()
    for i in range(5):
        (scratch / f"f{i}.txt").write_bytes(b"m" * 1024)
    policy = _policy_for(repo)
    freezegun_style_sleep(
        monkeypatch, lambda: (scratch / "f0.txt").write_bytes(b"M" * 1024), limit=0.5
    )
    signal = detect_concurrent_writer(
        repo,
        window_s=0.5,
        policy=policy,
        max_untracked_paths=2,
        max_untracked_bytes=1024,
        hash_size_cap=1 << 20,
    )
    assert "max_untracked_paths" in signal.caps_hit
    assert "max_untracked_bytes" in signal.caps_hit
    assert signal.untracked_watched <= 2
    assert signal.untracked_hashed <= 1, "the byte budget must bound hashing"
    assert "caps hit" in signal.note


def test_policy_path_never_descends_worktrees(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Even with a policy, the untracked watcher never enters ``.worktrees/``."""
    wt = repo / ".worktrees" / "run-1"
    wt.mkdir(parents=True)
    for i in range(50):
        (wt / f"churn-{i}.txt").write_bytes(b"live sibling worktree\n")
    (wt / "SENTINEL_NEVER_COUNTED").write_bytes(b"if counted, we descended\n")
    policy = _policy_for(repo)

    freezegun_style_sleep(
        monkeypatch, lambda: (wt / "churn-0.txt").write_bytes(b"CHURN\n"), limit=0.2
    )
    signal = detect_concurrent_writer(repo, window_s=0.2, policy=policy)

    assert signal.untracked_watched == 0
    assert "SENTINEL_NEVER_COUNTED" not in signal.note
    assert signal.worktree_dirs_present == 1
    assert signal.verdict == "quiescent"


def test_assert_pinned_quiescent_checks_pinned_paths(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sealed window: the caller pins the exact untracked paths it depends on."""
    from resextract.refresh.writer import assert_pinned_quiescent

    scratch = repo / "scratch"
    scratch.mkdir()
    f = scratch / "m.txt"
    f.write_bytes(b"a" * 8)

    def mutate() -> None:
        time.sleep(0.005)
        f.write_bytes(b"b" * 8)

    freezegun_style_sleep(monkeypatch, mutate, limit=0.2)
    with pytest.raises(TargetBusyError) as excinfo:
        assert_pinned_quiescent(repo, ["scratch/m.txt"], window_s=0.2)
    assert excinfo.value.signal.verdict == "active_writer"
    assert "scratch/m.txt" in excinfo.value.signal.untracked_changed

    signal = assert_pinned_quiescent(repo, ["scratch/m.txt"], window_s=0.0, allow_active=True)
    assert signal.head_after, "the caller re-verifies HEAD after the window"
