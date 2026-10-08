"""Offline tests for commit-pinned material and the sealed window (U5.5).

A **real** temporary git repository is the fixture: files are committed, then the
working tree is *dirtied*, so "the bytes at the commit" and "the bytes on disk"
are different and the difference is observable.  No network, no model calls.

What is pinned here
===================

* the central guard — in ``commit`` mode the docket holds the **committed** bytes
  and the manifest names the **blob sha**, even though the working tree differs;
* untracked material is copied but marked ``unpinned=true`` with a reason, listed
  in ``unpinned_material``, and warned about on stderr — never silently accepted;
* a path absent at the recorded commit never claims ``git_object``;
* **refusal parity** — a secret-shaped path, a secret-shaped body, a
  containment escape and a ``.worktrees/`` ref are refused identically in both
  source modes, and nothing lands on disk in either;
* pinned bytes cannot smuggle a secret the working tree hides;
* the sealed window: HEAD moving mid-run ⇒ ``window_sealed=false`` and
  ``freshness.state="needs_rework"``, with the docket still produced;
* idempotency survives all of it.

Red → green (two guards, both pasted verbatim)
=============================================

Guard 1 — the **"a pinned byte never comes from the working tree when the path is
tracked at that commit"** guard
(``test_commit_mode_holds_the_committed_bytes_not_the_dirty_working_tree``).
Revert = make the silent fallback: in ``materialize_lane``, replace the
``_open_pinned_source(...)`` call with ``pinned_source, pin_failure_reason = None,
"not_a_git_repo"`` so every entry is read from the working tree while still
recording the commit as ``head_sha``.  Running
``.venv/bin/python -m pytest tests/test_docket_materialize_pinned.py -k central``::

            docket = Path(result.docket_dir)
            dest = docket / "material" / "docs" / "TRACKED.md"

            pinned_sha = sha256_bytes(TRACKED_COMMITTED.encode())
            working_sha = sha256_bytes(TRACKED_WORKING.encode())
            assert pinned_sha != working_sha  # the fixture really is dirty

            assert dest.is_file()
    >       assert sha256_bytes(dest.read_bytes()) == pinned_sha
    E       AssertionError: assert '05947c193fd4...537bb8319b7ea' == 'c9d4925a4528...56579f8824eea'
    E         
    E         - c9d4925a45280428df494257b282cde91cd7fb5f114c9432ab056579f8824eea
    E         + 05947c193fd49e5b0b5948ffbead6858bd84707dee5dbb02227537bb8319b7ea

    tests/test_docket_materialize_pinned.py:188: AssertionError
    ----------------------------- Captured stderr call -----------------------------
    WARNING: unpinned material docs/TRACKED.md (working tree /tmp/pytest-of-zer0null/pytest-0/test_commit_mode_holds_the_com0/repo/docs/TRACKED.md): not_a_git_repo; sha256=05947c19; mtime=2026-10-08T11:24:33Z
    =========================== short test summary info ============================
    FAILED tests/test_docket_materialize_pinned.py::test_commit_mode_holds_the_committed_bytes_not_the_dirty_working_tree
    1 failed, 10 deselected in 0.13s

Guard 2 — the **"``window_sealed=False`` ⇒ ``needs_rework``"** guard
(``test_window_sealed_false_marks_needs_rework_and_still_produces_the_docket``).
Revert = delete the ``needs_rework`` marking: replace ``needs_rework = not
window_sealed`` with ``needs_rework = False`` in ``materialize_lane``.  Running
``.venv/bin/python -m pytest tests/test_docket_materialize_pinned.py -k needs_rework``::

        def test_window_sealed_false_marks_needs_rework_and_still_produces_the_docket(
            repo, tmp_path, db
        ):
            start = _git(repo, "rev-parse", "HEAD")
            result = run(
                lane("sealed-moved", ["docs/TRACKED.md"]),
                repo,
                tmp_path,
                db,
                head_probe=lambda root: MOVED_SHA,
            )
            docket = Path(result.docket_dir)

            assert result.window_sealed is False
    >       assert result.needs_rework is True
    E       AssertionError: assert False is True
    E        +  where False = MaterializedDocket(docket_dir='/tmp/pytest-of-zer0null/pytest-0/test_window_sealed_false_marks0/dockets/fixture/sealed...26-10-08T11:24:17Z', path='/tmp/pytest-of-zer0null/pytest-0/test_window_sealed_false_marks0/repo'), needs_rework=False).needs_rework

    tests/test_docket_materialize_pinned.py:398: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_docket_materialize_pinned.py::test_window_sealed_false_marks_needs_rework_and_still_produces_the_docket
    1 failed, 10 deselected in 0.08s

(Full logs: ``state/logs/U5.5_red1.txt`` and ``state/logs/U5.5_red2.txt``.)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from resextract import store
from resextract.docket import materialize as mat

# --------------------------------------------------------------------------- #
# fixture material
# --------------------------------------------------------------------------- #

TRACKED_COMMITTED = "committed line 1\ncommitted line 2\ncommitted line 3\n"
TRACKED_WORKING = "DIRTY working-tree line 1\nDIRTY working-tree line 2\n"
KEYS_COMMITTED = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n"
KEYS_CLEAN = "nothing secret here anymore\n"
SCRATCH = "scratch notes that no commit contains\n"
EXTRA = "extra untracked file\n"
NEW_AFTER_COMMIT = "created after the commit\n"
ENV_BODY = "API_KEY=not-a-real-key\n"
BEARER = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345\n"
LEAK = "TOP SECRET — this file lives outside the repo root\n"
MOVED_SHA = "b" * 40


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A real git repo whose working tree is dirty *after* the commit."""
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "notes").mkdir()
    (root / "docs" / "TRACKED.md").write_text(TRACKED_COMMITTED, encoding="utf-8")
    (root / "docs" / "keys.md").write_text(KEYS_COMMITTED, encoding="utf-8")
    (root / "src" / "clean.ts").write_text("export const clean = 1;\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "u55@example.invalid")
    _git(root, "config", "user.name", "U5.5")
    _git(root, "add", "-A")
    _git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture")

    # -- after the commit: the working tree no longer matches the object store --
    (root / "docs" / "TRACKED.md").write_text(TRACKED_WORKING, encoding="utf-8")
    # the committed bytes are secret-shaped; the working-tree bytes are not
    (root / "docs" / "keys.md").write_text(KEYS_CLEAN, encoding="utf-8")
    # untracked, admitted material that no commit contains
    (root / "notes" / "SCRATCH.md").write_text(SCRATCH, encoding="utf-8")
    (root / "EXTRA.txt").write_text(EXTRA, encoding="utf-8")
    (root / "docs" / "NEW.md").write_text(NEW_AFTER_COMMIT, encoding="utf-8")
    (root / ".env").write_text(ENV_BODY, encoding="utf-8")
    (root / "docs" / "bearer.md").write_text(BEARER, encoding="utf-8")
    # a live sibling worktree: never walked, never copied
    (root / ".worktrees" / "run-1").mkdir(parents=True)
    (root / ".worktrees" / "run-1" / "leak.md").write_text(LEAK, encoding="utf-8")
    return root


@pytest.fixture
def db(tmp_path: Path) -> Path:
    path = tmp_path / "state.sqlite"
    store.init_db(path)
    return path


def lane(slug: str, refs: list[str]) -> mat.LaneSpec:
    return mat.LaneSpec(
        slug=slug,
        title="Pinned fixture lane",
        thesis="Commit-pinned material must be the committed bytes.",
        audience="test suite",
        type="report",
        members=[mat.MemberSpec("M1", provenance_refs=refs)],
        target_slug="fixture",
        head_sha=None,
    )


def run(spec: mat.LaneSpec, repo: Path, tmp_path: Path, db: Path, **kw):
    """Materialize with a 0 s quiescence window (the fixture is a real repo)."""
    kw.setdefault("window_s", 0.0)
    return mat.materialize_lane(
        spec,
        target_root=str(repo),
        docket_root=str(tmp_path / "dockets"),
        db_path=db,
        **kw,
    )


def material_texts(docket: Path) -> str:
    out = []
    for path in sorted((docket / "material").rglob("*")):
        if path.is_file():
            out.append(path.read_bytes().decode("utf-8", errors="replace"))
    return "\n".join(out)


def manifest_of(result) -> dict:
    return json.loads(
        (Path(result.docket_dir) / "MANIFEST.json").read_text(encoding="utf-8")
    )


def material_rows(result) -> dict[str, dict]:
    return {row["dest"]: row for row in manifest_of(result)["material"]}


# --------------------------------------------------------------------------- #
# the central guard: pinned bytes, not working-tree bytes
# --------------------------------------------------------------------------- #


def test_commit_mode_holds_the_committed_bytes_not_the_dirty_working_tree(
    repo, tmp_path, db
):
    """The docket must hold the bytes the commit contains, not the dirty file."""
    result = run(lane("central", ["docs/TRACKED.md"]), repo, tmp_path, db)
    docket = Path(result.docket_dir)
    dest = docket / "material" / "docs" / "TRACKED.md"

    pinned_sha = sha256_bytes(TRACKED_COMMITTED.encode())
    working_sha = sha256_bytes(TRACKED_WORKING.encode())
    assert pinned_sha != working_sha  # the fixture really is dirty

    assert dest.is_file()
    assert sha256_bytes(dest.read_bytes()) == pinned_sha
    assert sha256_bytes(dest.read_bytes()) != working_sha
    # the working tree still holds the dirty bytes: we did not read from it
    assert (repo / "docs" / "TRACKED.md").read_text(encoding="utf-8") == TRACKED_WORKING

    row = material_rows(result)["docs/TRACKED.md"]
    assert row["resolved_from"] == "git_object"
    assert row["unpinned"] is False
    assert row["blob_sha"] == _git(repo, "rev-parse", "HEAD:docs/TRACKED.md")
    assert row["sha256"] == pinned_sha

    prov = result.provenance["docs/TRACKED.md"]
    assert prov["resolved_from"] == "git_object"
    assert prov["blob_sha"] == row["blob_sha"]
    assert prov["sha256"] == pinned_sha
    assert result.unpinned_material == []
    assert result.pinned is True
    assert result.counts()["pinned_entries"] == 1


def test_pinned_bytes_cannot_smuggle_a_secret_the_working_tree_hides(
    repo, tmp_path, db
):
    """A body that is secret-shaped *at the commit* is refused, though clean on disk."""
    result = run(
        lane("pinned-secret", ["docs/TRACKED.md", "docs/keys.md"]), repo, tmp_path, db
    )
    docket = Path(result.docket_dir)

    assert result.copy_report.copied_count == 1
    assert result.copy_report.refused_count == 1
    assert result.refusals == ["docs/keys.md: secret_content"]
    assert not (docket / "material" / "docs" / "keys.md").exists()
    assert "PRIVATE KEY" not in material_texts(docket)
    # the working-tree plan alone would have copied it: this refusal is the
    # mirror plan's, i.e. it came from the *pinned* bytes.
    assert (repo / "docs" / "keys.md").read_text(encoding="utf-8") == KEYS_CLEAN


# --------------------------------------------------------------------------- #
# untracked / absent-at-commit material is copied but never silently
# --------------------------------------------------------------------------- #


def test_untracked_file_is_copied_unpinned_and_warned(repo, tmp_path, db, capsys):
    result = run(
        lane("untracked", ["docs/TRACKED.md", "notes/SCRATCH.md"]), repo, tmp_path, db
    )
    docket = Path(result.docket_dir)

    copied = docket / "material" / "docs" / "SCRATCH.md"
    assert copied.is_file()
    assert copied.read_bytes() == SCRATCH.encode()

    entry = {e["dest"]: e for e in result.unpinned_material}["docs/SCRATCH.md"]
    assert entry["resolved_from"] == "working_tree"
    assert entry["unpinned"] is True
    assert entry["reason"] == "untracked_at_commit"
    assert entry["mtime"], "an unpinned entry must carry the file mtime"

    row = material_rows(result)["docs/SCRATCH.md"]
    assert row["unpinned"] is True
    assert row["resolved_from"] == "working_tree"
    assert row["blob_sha"] is None
    assert "untracked_at_commit" in (row["note"] or "")

    err = capsys.readouterr().err
    assert "WARNING: unpinned material docs/SCRATCH.md" in err
    assert "untracked_at_commit" in err
    assert any("unpinned material docs/SCRATCH.md" in n for n in result.notes)
    # the run is still commit-pinned for the tracked file
    assert result.pinned is True
    assert result.counts() == {
        **result.counts(),
        "pinned_entries": 1,
        "unpinned_entries": 1,
    }


def test_file_absent_at_the_commit_never_claims_git_object(repo, tmp_path, db):
    result = run(lane("absent", ["docs/NEW.md"]), repo, tmp_path, db)
    docket = Path(result.docket_dir)

    assert (docket / "material" / "docs" / "NEW.md").read_bytes() == NEW_AFTER_COMMIT.encode()
    row = material_rows(result)["docs/NEW.md"]
    assert row["resolved_from"] == "working_tree"
    assert row["unpinned"] is True
    assert row["blob_sha"] is None
    assert result.provenance["docs/NEW.md"]["reason"] == "untracked_at_commit"
    assert result.unresolved_refs == []  # reported as unpinned, not dropped


# --------------------------------------------------------------------------- #
# refusal parity
# --------------------------------------------------------------------------- #


def test_refusal_parity_secret_path_and_secret_content_in_both_modes(
    repo, tmp_path, db
):
    refs = ["docs/TRACKED.md", ".env", "docs/bearer.md"]
    results = {
        mode: run(lane(f"parity-{mode}", refs), repo, tmp_path, db, source_mode=mode)
        for mode in ("commit", "working-tree")
    }

    for mode, result in results.items():
        assert result.copy_report.refused_count == 2, mode
        assert sorted(result.refusals) == [
            "data/.env: secret_path",
            "docs/bearer.md: secret_content",
        ], mode
        docket = Path(result.docket_dir)
        assert not (docket / "material" / "data" / ".env").exists(), mode
        assert not (docket / "material" / "docs" / "bearer.md").exists(), mode
        assert ENV_BODY.strip() not in material_texts(docket), mode
        assert "Bearer" not in material_texts(docket), mode

    assert sorted(results["commit"].refusals) == sorted(results["working-tree"].refusals)


def test_containment_parity_in_both_modes(repo, tmp_path, db):
    outside = tmp_path / "outside" / "leak.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text(LEAK, encoding="utf-8")
    ref = "../outside/leak.md"

    plan = mat.refs_to_copy_requests([ref, "docs/TRACKED.md"], target_root=str(repo))
    assert {u.ref: u.reason for u in plan.unresolved} == {ref: "outside_target_root"}

    for mode in ("commit", "working-tree"):
        result = run(
            lane(f"contain-{mode}", [ref, "docs/TRACKED.md"]),
            repo,
            tmp_path,
            db,
            source_mode=mode,
        )
        reasons = {u.ref: u.reason for u in result.unresolved_refs}
        assert reasons[ref] == "outside_target_root", mode
        assert LEAK.strip() not in material_texts(Path(result.docket_dir)), mode


def test_worktrees_refs_are_refused_in_both_modes(repo, tmp_path, db):
    ref = ".worktrees/run-1/leak.md"
    plan = mat.refs_to_copy_requests([ref, "docs/TRACKED.md"], target_root=str(repo))
    assert {u.ref: u.reason for u in plan.unresolved} == {ref: "unsafe_path"}
    assert ".worktrees" in plan.unresolved[0].detail

    for mode in ("commit", "working-tree"):
        result = run(
            lane(f"worktrees-{mode}", [ref, "docs/TRACKED.md"]),
            repo,
            tmp_path,
            db,
            source_mode=mode,
        )
        reasons = {u.ref: u.reason for u in result.unresolved_refs}
        assert reasons[ref] == "unsafe_path", mode
        assert LEAK.strip() not in material_texts(Path(result.docket_dir)), mode


# --------------------------------------------------------------------------- #
# working-tree mode declares itself
# --------------------------------------------------------------------------- #


def test_working_tree_mode_records_itself_as_unpinned(repo, tmp_path, db):
    result = run(
        lane("wt-mode", ["docs/TRACKED.md"]), repo, tmp_path, db, source_mode="working-tree"
    )
    docket = Path(result.docket_dir)

    assert result.source_mode == "working-tree"
    assert result.pinned is False
    # deliberately the dirty bytes — and said so
    assert (
        sha256_bytes((docket / "material" / "docs" / "TRACKED.md").read_bytes())
        == sha256_bytes(TRACKED_WORKING.encode())
    )
    row = material_rows(result)["docs/TRACKED.md"]
    assert row["resolved_from"] == "working_tree"
    assert row["unpinned"] is True
    assert row["blob_sha"] is None
    assert result.unpinned_material
    assert all(
        e["reason"] == "source_mode_working_tree" for e in result.unpinned_material
    )
    assert any("NOT commit-pinned" in note for note in result.notes)


# --------------------------------------------------------------------------- #
# the sealed window
# --------------------------------------------------------------------------- #


def test_window_sealed_false_marks_needs_rework_and_still_produces_the_docket(
    repo, tmp_path, db
):
    start = _git(repo, "rev-parse", "HEAD")
    result = run(
        lane("sealed-moved", ["docs/TRACKED.md"]),
        repo,
        tmp_path,
        db,
        head_probe=lambda root: MOVED_SHA,
    )
    docket = Path(result.docket_dir)

    assert result.window_sealed is False
    assert result.needs_rework is True
    assert result.head_sha == start
    assert result.head_sha_end == MOVED_SHA

    manifest = manifest_of(result)
    assert manifest["window_sealed"] is False
    assert manifest["freshness"]["state"] == "needs_rework"
    assert any(
        start[:8] in reason and MOVED_SHA[:8] in reason
        for reason in manifest["rework_open"]
    )

    history = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert "target head moved during materialization" in history
    assert start[:8] in history and MOVED_SHA[:8] in history

    # the docket is honest about being mid-move, not discarded
    assert (docket / "MANIFEST.json").is_file()
    assert result.ok and result.verification.ok, result.verification.problems

    con = store.connect(db)
    try:
        assert con.execute("SELECT freshness FROM dockets").fetchone()[0] == "needs_rework"
    finally:
        con.close()


def test_window_sealed_true_on_a_quiet_target(repo, tmp_path, db):
    result = run(lane("sealed-quiet", ["docs/TRACKED.md"]), repo, tmp_path, db)

    assert result.window_sealed is True
    assert result.needs_rework is False
    assert result.window_reason == ""
    manifest = manifest_of(result)
    assert manifest["window_sealed"] is True
    assert manifest["freshness"]["state"] != "needs_rework"
    assert result.writer_signal is not None
    assert result.writer_signal.verdict in ("quiescent", "active_writer", "head_moved")


# --------------------------------------------------------------------------- #
# idempotency
# --------------------------------------------------------------------------- #


def test_rerun_is_idempotent_and_keeps_one_row(repo, tmp_path, db):
    spec = lane("idem-pinned", ["docs/TRACKED.md", "notes/SCRATCH.md"])
    first = run(spec, repo, tmp_path, db)
    docket = Path(first.docket_dir)
    history_one = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert first.copy_report.copied_count == 2

    second = run(spec, repo, tmp_path, db)
    assert second.ok
    assert second.copy_report.copied_count == 0
    assert second.copy_report.unchanged_count == 2
    assert second.window_sealed is True

    assert (docket / "ITEM.md.r1").is_file()
    history_two = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert history_one.rstrip("\n") in history_two

    con = store.connect(db)
    try:
        count = con.execute("SELECT COUNT(*) FROM dockets").fetchone()[0]
        row_id = con.execute("SELECT id FROM dockets").fetchone()[0]
    finally:
        con.close()
    assert count == 1
    assert second.dockets_row_id == first.dockets_row_id == row_id


# --------------------------------------------------------------------------- #
# U5.6 — tree-first resolution: a deleted-but-committed file is still material
# --------------------------------------------------------------------------- #
#
# The defect (verifier V5): ``_resolve_one`` demanded on-disk existence before
# pinning, so a file tracked at the commit but DELETED from the working tree
# reported ``not_a_file_in_target`` and its blob — still in the object store —
# was never read.  Pinning exists to carry the bytes at the commit, and deletion
# is the extreme case of drift.  The commit is now asked first.
import shutil  # noqa: E402  (U5.6 section-local import)


def _blob_bytes(root: Path, spec: str) -> bytes:
    """The exact blob bytes, without any stripping (``git cat-file blob``)."""
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", spec],
        capture_output=True,
        check=True,
    )
    return proc.stdout


def test_deleted_but_committed_file_is_resolved_tree_first(repo, tmp_path, db):
    """A file tracked at the commit but DELETED from the working tree is copied.

    RED -> GREEN guard A — the tree-first resolution guard (verbatim):

        PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
          tests/test_docket_materialize_pinned.py::test_deleted_but_committed_file_is_resolved_tree_first

    * fix REVERTED -> FAILS: the deleted path is reported
      ``not_a_file_in_target`` and nothing is copied (the pinned blob is never
      read);
    * fix PRESENT -> PASSES.
    """
    committed = _blob_bytes(repo, "HEAD:docs/TRACKED.md")
    (repo / "docs" / "TRACKED.md").unlink()
    assert not (repo / "docs" / "TRACKED.md").exists()

    result = run(lane("tree-first-deleted", ["docs/TRACKED.md"]), repo, tmp_path, db)
    docket = Path(result.docket_dir)
    dest = docket / "material" / "docs" / "TRACKED.md"

    assert dest.is_file(), "the pinned blob must still be material"
    assert dest.read_bytes() == committed
    assert sha256_bytes(dest.read_bytes()) == sha256_bytes(TRACKED_COMMITTED.encode())

    row = material_rows(result)["docs/TRACKED.md"]
    assert row["resolved_from"] == "git_object"
    assert row["unpinned"] is False
    assert row["blob_sha"] == _git(repo, "rev-parse", "HEAD:docs/TRACKED.md")
    assert row["blob_sha"] == _git(repo, "rev-parse", "HEAD:docs/TRACKED.md")
    assert result.provenance["docs/TRACKED.md"]["resolved_from"] == "git_object"
    assert result.unpinned_material == []
    assert result.unresolved_refs == []
    assert result.counts()["pinned_entries"] == 1
    assert result.ok and result.verification.ok, result.verification.problems


def test_absent_from_both_commit_and_working_tree_is_still_not_a_file(repo, tmp_path, db):
    """``not_a_file_in_target`` survives only for a path absent from BOTH."""
    ref = "docs/GONE.md"
    head = _git(repo, "rev-parse", "HEAD")
    source = mat.GitObjectSource(str(repo), head)

    # tree-first, with the commit consulted: still absent from both
    plan = mat.refs_to_copy_requests(
        [ref, "docs/TRACKED.md"], target_root=str(repo), pinned_source=source
    )
    assert {u.ref: u.reason for u in plan.unresolved} == {ref: "not_a_file_in_target"}
    # ... and the same through a full run
    result = run(lane("absent-both", [ref, "docs/TRACKED.md"]), repo, tmp_path, db)
    reasons = {u.ref: u.reason for u in result.unresolved_refs}
    assert reasons[ref] == "not_a_file_in_target"
    assert not (Path(result.docket_dir) / "material" / "docs" / "GONE.md").exists()
    assert result.copy_report.copied_count == 1


def test_tree_only_committed_secret_is_refused_with_nothing_on_disk(repo, tmp_path, db):
    """The intended asymmetry: committed-only secret content is REFUSED.

    The working tree holds clean bytes, the commit holds secret-shaped ones.
    Deleting the file makes it tree-only, so only the pinned-bytes pass can see
    it — and that pass must still refuse, writing nothing.  This asymmetry is the
    safety win, not a parity bug.
    """
    assert (repo / "docs" / "keys.md").read_text(encoding="utf-8") == KEYS_CLEAN
    (repo / "docs" / "keys.md").unlink()

    result = run(
        lane("tree-only-secret", ["docs/TRACKED.md", "docs/keys.md"]), repo, tmp_path, db
    )
    docket = Path(result.docket_dir)

    assert result.refusals == ["docs/keys.md: secret_content"]
    assert not (docket / "material" / "docs" / "keys.md").exists()
    assert result.copy_report.refused_count == 1
    assert result.copy_report.copied_count == 1
    # and the deleted path is never downgraded to an unpinned working-tree read
    assert all(
        p["resolved_from"] == "git_object" for p in result.provenance.values()
    )


def test_dirty_working_tree_still_yields_pinned_bytes(repo, tmp_path, db):
    """Regression: a present-but-dirty file still yields the PINNED bytes.

    RED -> GREEN guard B — the pinned-bytes-not-working-bytes guard (verbatim):

        PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
          tests/test_docket_materialize_pinned.py::test_dirty_working_tree_still_yields_pinned_bytes

    * pinned resolution MUTATED to let the working tree win -> FAILS (the docket
      would hold the dirty bytes and record no blob sha);
    * fix PRESENT -> PASSES.
    """
    assert (repo / "docs" / "TRACKED.md").read_text(encoding="utf-8") == TRACKED_WORKING
    result = run(lane("tree-first-dirty", ["docs/TRACKED.md"]), repo, tmp_path, db)
    dest = Path(result.docket_dir) / "material" / "docs" / "TRACKED.md"

    assert sha256_bytes(dest.read_bytes()) == sha256_bytes(TRACKED_COMMITTED.encode())
    assert sha256_bytes(dest.read_bytes()) != sha256_bytes(TRACKED_WORKING.encode())
    row = material_rows(result)["docs/TRACKED.md"]
    assert row["resolved_from"] == "git_object"
    assert row["blob_sha"] == _git(repo, "rev-parse", "HEAD:docs/TRACKED.md")


def test_tree_only_directory_and_unsafe_paths_are_still_unresolved(repo, tmp_path, db):
    """A tree-only DIRECTORY at the commit, ``..``/absolute/``.worktrees/``: as before."""
    (repo / "pkg").mkdir()
    (repo / "pkg" / "inner.md").write_text(SCRATCH, encoding="utf-8")
    _git(repo, "add", "pkg")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "add pkg dir")
    shutil.rmtree(repo / "pkg")
    assert not (repo / "pkg").exists()

    weird = ".worktrees/run-1/leak.md"
    result = run(
        lane(
            "tree-only-safety",
            ["pkg", "../outside/leak.md", "/etc/passwd", weird, "docs/TRACKED.md"],
        ),
        repo,
        tmp_path,
        db,
    )
    reasons = {u.ref: u.reason for u in result.unresolved_refs}
    assert reasons["pkg"] == "not_a_file_in_target"
    assert reasons["../outside/leak.md"] == "outside_target_root"
    assert reasons["/etc/passwd"] == "outside_target_root"
    assert reasons[weird] == "unsafe_path"  # unresolved, never a refusal
    assert not (Path(result.docket_dir) / "material" / "data" / "pkg").exists()
    assert LEAK.strip() not in material_texts(Path(result.docket_dir))
    assert result.copy_report.copied_count == 1


def test_tree_only_rerun_is_idempotent(repo, tmp_path, db):
    """A second run of a tree-only file reports ``unchanged`` and does not rewrite."""
    (repo / "docs" / "TRACKED.md").unlink()
    spec = lane("tree-only-idem", ["docs/TRACKED.md"])

    first = run(spec, repo, tmp_path, db)
    dest = Path(first.docket_dir) / "material" / "docs" / "TRACKED.md"
    before = dest.read_bytes()
    mtime_before = dest.stat().st_mtime_ns
    assert first.copy_report.copied_count == 1

    second = run(spec, repo, tmp_path, db)
    assert second.ok
    assert second.copy_report.copied_count == 0
    assert second.copy_report.unchanged_count == 1
    assert dest.read_bytes() == before
    assert dest.stat().st_mtime_ns == mtime_before, "unchanged must not rewrite"
    assert material_rows(second)["docs/TRACKED.md"]["blob_sha"] == _git(
        repo, "rev-parse", "HEAD:docs/TRACKED.md"
    )
