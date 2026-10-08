"""Red→green guards for :mod:`resextract.refresh.staleness`.

RED→GREEN GUARD A — `needs_rework` when a cited file changed.

Revert: in ``freshness_for`` replace ``hit = _matches_changed(resolved, changed)``
with ``hit = None`` (i.e. never match a claim's provenance file against the
change).  Measured failure:

            assert rep.change.kind == "head_moved" and rep.change.commits_between == 1
            assert rep.noop is False
            docket = rep.dockets[0]
    >       assert docket.state == "needs_rework"
    E       AssertionError: assert 'current' == 'needs_rework'
    E         
    E         - needs_rework
    E         + current
    
    tests/test_refresh_review.py:263: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_refresh_staleness.py::test_freshness_precedence_and_reasons
    FAILED tests/test_refresh_review.py::test_head_moved_cited_file_needs_rework
    2 failed in 0.07s

That test guards the whole point of the engine: a repo move must invalidate the
items whose cited bytes moved, and the reason must name the file *and* commit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from resextract.refresh.staleness import (
    ChangeReport,
    detect_change,
    freshness_for,
    read_target_state,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "refresh-repo" / "seed"
NOW = "2026-10-08T00:00:00Z"


def git(repo: Path, *args: str) -> str:
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="U7.1",
        GIT_AUTHOR_EMAIL="u71@example.invalid",
        GIT_COMMITTER_NAME="U7.1",
        GIT_COMMITTER_EMAIL="u71@example.invalid",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
    )
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, timeout=30
    )
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> dict:
    dst = tmp_path / "repo"
    shutil.copytree(FIXTURE, dst)
    git(dst, "init", "-q", "-b", "main")
    git(dst, "add", "-A")
    git(dst, "commit", "-qm", "c1: seed")
    first = git(dst, "rev-parse", "HEAD")

    (dst / "docs/FINDINGS.md").write_text("# FINDINGS\n\nline two CHANGED.\nline three.\n")
    (dst / "README.md").write_text("# refresh fixture\n\nseed file one, edited.\n")
    git(dst, "mv", "src/a.py", "src/b.py")
    git(dst, "rm", "-q", "gone.txt")
    (dst / "src/new.py").write_text("def beta():\n    return 2\n")
    git(dst, "add", "-A")
    git(dst, "commit", "-qm", "c2: modify, rename, delete, add")
    second = git(dst, "rev-parse", "HEAD")
    return {"path": dst, "first": first, "second": second, "tmp": tmp_path}


def test_detect_change_head_moved_reports_sets(repo: dict) -> None:
    rep = detect_change(repo["first"], repo["second"], repo["path"])
    assert rep.kind == "head_moved"
    assert rep.commits_between == 1
    assert "docs/FINDINGS.md" in rep.changed_files
    assert "README.md" in rep.changed_files
    assert "src/b.py" in rep.changed_files and "src/a.py" in rep.changed_files
    assert "gone.txt" in rep.deleted
    assert "src/new.py" in rep.added
    assert ("src/a.py", "src/b.py") in rep.renamed
    assert rep.truncated is False
    assert rep.errors == ()


def test_detect_change_none_and_working_tree(repo: dict) -> None:
    rep = detect_change(repo["second"], repo["second"], repo["path"])
    assert rep.kind == "none" and rep.changed_files == ()
    dirty = detect_change(repo["second"], repo["second"], repo["path"], dirty_paths=["src/b.py"])
    assert dirty.kind == "working_tree_changed"
    assert "src/b.py" in dirty.changed_files
    both = detect_change(repo["first"], repo["second"], repo["path"], dirty_paths=["untracked.py"])
    assert both.kind == "both"
    assert "untracked.py" in both.changed_files


def test_detect_change_no_previous_state(repo: dict) -> None:
    rep = detect_change(None, repo["second"], repo["path"])
    assert rep.kind == "head_moved"
    assert rep.note == "no_previous_state"
    assert rep.commits_between is None
    assert rep.changed_files == ()


def test_detect_change_history_rewritten(repo: dict) -> None:
    git(repo["path"], "checkout", "-q", "-b", "side", repo["first"])
    (repo["path"] / "side.txt").write_text("side branch\n")
    git(repo["path"], "add", "-A")
    git(repo["path"], "commit", "-qm", "side commit")
    side = git(repo["path"], "rev-parse", "HEAD")
    git(repo["path"], "checkout", "-q", "main")

    rep = detect_change(side, repo["second"], repo["path"])
    assert rep.kind == "head_moved"
    assert rep.note == "history_rewritten"
    assert rep.commits_between is None
    assert "README.md" in rep.changed_files  # the diff is still measurable
    assert any("not an ancestor" in w for w in rep.warnings)


def test_read_target_state_ignores_worktrees_and_node_modules(repo: dict) -> None:
    st = read_target_state(repo["path"], now=NOW)
    assert st.head_sha == repo["second"]
    assert st.branch == "main"
    assert st.dirty_paths == ()
    digest = st.mtime_digest
    assert digest == read_target_state(repo["path"]).mtime_digest

    (repo["path"] / "node_modules").mkdir()
    (repo["path"] / "node_modules/junk.js").write_text("junk\n")
    (repo["path"] / ".worktrees").mkdir()
    (repo["path"] / ".worktrees/junk.txt").write_text("junk\n")
    st2 = read_target_state(repo["path"])
    assert st2.dirty_paths == ()
    assert st2.mtime_digest == digest, "untracked node_modules/.worktrees must not enter the digest"

    (repo["path"] / "keep.txt").write_text("keep me, edited\n")
    st3 = read_target_state(repo["path"])
    assert "keep.txt" in st3.dirty_paths
    assert st3.mtime_digest != digest


def test_freshness_precedence_and_reasons(repo: dict) -> None:
    change = detect_change(repo["first"], repo["second"], repo["path"])
    head7 = repo["second"][:7]
    gone_url = "https://gone.example/doc"

    stale_base = {
        "prior_art_checked_at": "2020-01-01T00:00:00Z",
    }

    # needs_rework beats stale (expired TTL + gone link are also present).
    hit = {
        "claims": [{"id": "C3", "provenance": ["file:docs/FINDINGS.md#L1-L3"]}],
        "freshness": dict(stale_base, state="current"),
        "web_sources": [{"url": gone_url}],
    }
    f = freshness_for(
        hit, change, now=NOW, prior_art_ttl_days=30, link_status={gone_url: "gone"}
    )
    assert f.state == "needs_rework"
    assert any("docs/FINDINGS.md" in r and head7 in r for r in f.reasons)
    assert any("TTL" in r for r in f.reasons), "the stale reason must still be reported"
    assert any(gone_url in r for r in f.reasons)
    assert f.age_days is not None and f.age_days > 1000

    # stale on TTL alone
    ttl = {
        "claims": [{"id": "C9", "provenance": ["file:CITATION.cff#L1-L2"]}],
        "freshness": dict(stale_base, state="current"),
        "web_sources": [],
    }
    ft = freshness_for(ttl, change, now=NOW, prior_art_ttl_days=30)
    assert ft.state == "stale"
    assert "TTL" in ft.reasons[0]

    # stale on an unreachable cited source
    d3 = {
        "claims": [{"id": "C9", "provenance": ["file:CITATION.cff#L1-L2"]}],
        "freshness": {"state": "current", "prior_art_checked_at": "2026-10-01T00:00:00Z"},
        "web_sources": [{"url": gone_url}],
    }
    f3 = freshness_for(d3, change, now=NOW, link_status={gone_url: "gone"})
    assert f3.state == "stale"
    assert any(gone_url in r and "unreachable" in r for r in f3.reasons)

    # untouched docket stays current
    ok = {
        "claims": [{"id": "C9", "provenance": ["file:CITATION.cff#L1-L2"]}],
        "freshness": {"state": "current", "prior_art_checked_at": "2026-10-01T00:00:00Z"},
        "web_sources": [],
    }
    assert freshness_for(ok, change, now=NOW).state == "current"

    # superseded is only ever preserved, never promoted
    sup = dict(ok, freshness={"state": "superseded"})
    fsup = freshness_for(sup, change, now=NOW)
    assert fsup.state == "superseded"
    # ... even when a cited file moved
    sup_hit = dict(hit, freshness={"state": "superseded"})
    assert freshness_for(sup_hit, change, now=NOW).state == "superseded"


def test_freshness_resolves_graph_node_source_file(repo: dict) -> None:
    from resextract.kg import read_graph

    change = detect_change(repo["first"], repo["second"], repo["path"])
    graph_path = repo["tmp"] / "graph.json"
    graph_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "n1", "label": "Findings", "source_file": "docs/FINDINGS.md"},
                    {"id": "n2", "label": "Keep", "source_file": "keep.txt"},
                ],
                "links": [],
            }
        )
    )
    graph = read_graph(graph_path)
    docket = {
        "claims": [{"id": "C4", "provenance": ["graph:n1", "graph:n2"]}],
        "freshness": {"state": "current", "prior_art_checked_at": "2026-10-01T00:00:00Z"},
        "web_sources": [],
    }
    f = freshness_for(docket, change, now=NOW, graph=graph)
    assert f.state == "needs_rework"
    assert "docs/FINDINGS.md" in f.reasons[0]
    assert "graph node n1" in f.reasons[0]
    assert all("keep.txt" not in r for r in f.reasons)
