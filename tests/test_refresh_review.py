"""Red→green guards for :mod:`resextract.refresh.review`.

RED→GREEN GUARD B — a no-op run writes nothing.

Revert: in ``_apply_docket`` make the HISTORY append unconditional (``if True:``
in place of the ledger-guarded ``if event_new:``).  Measured failure:

            assert first.dockets[0].state == "needs_rework"
            before = snapshot(ddir, tmp_path / "state")
        
            second = refresh_target(r["path"], **args)
    >       assert second.noop is True
    E       AssertionError: assert False is True
    E        +  where False = RefreshReport(target='/tmp/pytest-of-zer0null/pytest-1/test_noop_second_pass_writes_n0/repo', slug='duval', observed=T...fy-out/graph.json: graph refresh skipped'], noop=False, dry_run=False, wall_s=0.005, run_id='20261008T000000Z-58c08ff').noop
    
    tests/test_refresh_review.py:391: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_refresh_review.py::test_noop_second_pass_writes_nothing - A...
    1 failed in 0.06s

The test that must fail is :func:`test_noop_second_pass_writes_nothing`: it
snapshots mtime/size/bytes for every file under the docket *and* the state root,
re-runs with nothing new, and requires ``noop is True`` and byte-identical files.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from resextract.refresh.backlog import ReworkEntry, append_backlog
from resextract.refresh.review import refresh_target
from resextract.web.fetch import FetchMeta, FetchResult

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "refresh-repo" / "seed"
NOW = "2026-10-08T00:00:00Z"
TARGET_URL = "https://example.com/cited"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


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


def make_repo(tmp_path: Path) -> dict:
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
    return {"path": dst, "first": first, "second": second}


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_docket(
    ddir: Path,
    *,
    repo_path: Path,
    slug: str,
    head_sha: str,
    claims: list[dict],
    material: list[tuple[str, tuple[int, int], str]] = (),
    web_sources: list[str] = (),
    prior_art: str = "2026-10-01T00:00:00Z",
) -> Path:
    ddir.mkdir(parents=True, exist_ok=True)
    items = []
    for dest, span, reason in material:
        src = Path(repo_path) / dest
        out = ddir / "material" / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        items.append(
            {
                "src": str(src),
                "dest": dest,
                "sha256": sha256_file(src),
                "bytes": src.stat().st_size,
                "excerpt": list(span),
                "excerpt_reason": reason,
                "linked": False,
                "note": None,
            }
        )
    manifest = {
        "schema": "resextract/docket/1",
        "lane": {"slug": slug, "type": "report", "thesis": "fixture", "audience": "tests"},
        "target": {"slug": "duval", "head_sha": head_sha, "graph_hash": "deadbeefdeadbeef"},
        "status": "draft",
        "freshness": {
            "verified_at": prior_art,
            "prior_art_checked_at": prior_art,
            "age_days": 0.0,
            "state": "current",
        },
        "claims": claims,
        "material": items,
        "web_sources": [{"url": u} for u in web_sources],
        "open_questions": [],
        "rework_open": [],
        "generated_by": {"app": "resextract", "version": "0.1.0", "model": "fixture-u7.1"},
        "generated_at": prior_art,
    }
    (ddir / "MANIFEST.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    (ddir / "HISTORY.md").write_text(
        "# HISTORY — append-only\n\n## 2026-10-08T00:00:00Z — assembly\n\n"
        f"- lane `{slug}` · claims: {len(claims)}\n"
    )
    return ddir


def claim_citing(dest: str, span: tuple[int, int], cid: str = "C1") -> dict:
    return {
        "id": cid,
        "kind": "finding",
        "text": f"fixture claim citing {dest}",
        "provenance": [f"file:{dest}#L{span[0]}-L{span[1]}"],
        "evidence": [f"material/{dest}#L{span[0]}-L{span[1]}"],
        "verdict": "CONFIRMS",
    }


def kw(tmp_path: Path, ddir: Path, **over) -> dict:
    base = dict(
        docket_dirs=[ddir],
        check_links=False,
        now=NOW,
        state_root=tmp_path / "state",
        kg_root=tmp_path / "state" / "kg",
        slug="duval",
    )
    base.update(over)
    return base


def snapshot(*roots: Path) -> dict:
    out = {}
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                st = path.stat()
                out[str(path)] = (st.st_mtime_ns, st.st_size, path.read_bytes())
    return out


class StubFetcher:
    """Offline ``Fetcher.refresh`` stand-in; records the URLs it was asked for."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.calls: list[str] = []

    def refresh(self, url: str) -> FetchResult:
        self.calls.append(url)
        return self.plan[url]


def _meta(url: str, sha: str, status: int = 200) -> FetchMeta:
    return FetchMeta(url=url, title="t", text="body text", sha256=sha, http_status=status)


def unchanged_result(url: str, sha: str = "a" * 64) -> FetchResult:
    return FetchResult(
        ok=True,
        meta=_meta(url, sha),
        changed=False,
        detail={"old_sha256": sha, "new_sha256": sha},
        note="unchanged",
        usable_chars=900,
    )


def changed_result(url: str, old: str, new: str) -> FetchResult:
    return FetchResult(
        ok=True,
        meta=_meta(url, new),
        changed=True,
        detail={"old_sha256": old, "new_sha256": new},
        note="content_changed",
        usable_chars=900,
    )


def gone_result(url: str) -> FetchResult:
    return FetchResult(
        ok=False,
        error="HTTP 404",
        changed=True,
        detail={"old_sha256": "a" * 64, "new_sha256": None},
        note="refresh_failed",
        usable_chars=0,
    )


def suspect_result(url: str) -> FetchResult:
    return FetchResult(
        ok=True,
        meta=_meta(url, "c" * 64, status=404),
        changed=False,
        detail={"old_sha256": "a" * 64, "new_sha256": "c" * 64},
        note="unchanged",
        suspect=True,
        suspicion="25 chars: looks like a GitHub 404 stub",
        usable_chars=25,
    )


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #


def test_head_moved_cited_file_needs_rework(tmp_path: Path) -> None:
    """Guard A end-to-end: cited file changed ⇒ needs_rework + manifest + backlog."""
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="live-docket",
        head_sha=r["first"],
        claims=[claim_citing("docs/FINDINGS.md", (1, 3))],
        material=[("docs/FINDINGS.md", (1, 3), "headline")],
    )
    before_history = (ddir / "HISTORY.md").read_text()

    rep = refresh_target(r["path"], **kw(tmp_path, ddir))

    assert rep.change.kind == "head_moved" and rep.change.commits_between == 1
    assert rep.noop is False
    docket = rep.dockets[0]
    assert docket.state == "needs_rework"
    assert any(
        "docs/FINDINGS.md" in reason and r["second"][:7] in reason for reason in docket.reasons
    )
    manifest = json.loads((ddir / "MANIFEST.json").read_text())
    assert manifest["freshness"]["state"] == "needs_rework"
    assert manifest["target"]["head_sha"] == r["first"], "content head must not be silently bumped"
    history = (ddir / "HISTORY.md").read_text()
    assert history.startswith(before_history), "HISTORY.md is append-only"
    assert "— refresh" in history and "kind `head_moved`" in history
    backlog = (ddir / "UPDATE_BACKLOG.md").read_text()
    assert "docs/FINDINGS.md" in backlog and r["second"][:7] in backlog
    entry_lines = [ln for ln in backlog.splitlines() if ln.startswith("- ")]
    assert entry_lines and all("[measured]" in ln for ln in entry_lines)
    assert all("[model-suggested]" not in ln for ln in entry_lines)
    assert docket.backlog and all(e.model_suggested is False for e in docket.backlog)
    assert docket.backlog[0].source_ref.startswith("git:" + r["second"])
    assert (ddir / ".refresh_ledger.json").is_file()


def test_unchanged_docket_stays_current_without_backlog(tmp_path: Path) -> None:
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="quiet-docket",
        head_sha=r["first"],
        claims=[claim_citing("keep.txt", (1, 1))],
        material=[("keep.txt", (1, 1), "untouched")],
    )
    rep = refresh_target(r["path"], **kw(tmp_path, ddir))
    docket = rep.dockets[0]
    assert docket.state == "current"
    assert docket.reasons == ()
    assert docket.backlog == ()
    assert not (ddir / "UPDATE_BACKLOG.md").exists()
    assert json.loads((ddir / "MANIFEST.json").read_text())["freshness"]["state"] == "current"


def test_changed_link_carries_both_digests(tmp_path: Path) -> None:
    r = make_repo(tmp_path)
    old, new = "1" * 64, "2" * 64
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="link-docket",
        head_sha=r["first"],
        claims=[claim_citing("keep.txt", (1, 1))],
        material=[("keep.txt", (1, 1), "untouched")],
        web_sources=[TARGET_URL],
    )
    fetcher = StubFetcher({TARGET_URL: changed_result(TARGET_URL, old, new)})
    rep = refresh_target(
        r["path"], **kw(tmp_path, ddir, check_links=True, fetcher=fetcher, max_link_checks=5)
    )
    assert rep.checked_links == 1 and rep.changed_links == 1
    assert rep.links[0].status == "changed"
    assert rep.dockets[0].state == "stale"
    backlog = (ddir / "UPDATE_BACKLOG.md").read_text()
    assert old[:8] in backlog and new[:8] in backlog
    assert any(e.source_ref == f"web:{TARGET_URL}" for e in rep.dockets[0].backlog)
    assert all(e.model_suggested is False for e in rep.dockets[0].backlog)


def test_suspect_fetch_is_suspect_not_unchanged(tmp_path: Path) -> None:
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="stub-docket",
        head_sha=r["first"],
        claims=[claim_citing("keep.txt", (1, 1))],
        material=[("keep.txt", (1, 1), "untouched")],
        web_sources=[TARGET_URL],
    )
    fetcher = StubFetcher({TARGET_URL: suspect_result(TARGET_URL)})
    rep = refresh_target(
        r["path"], **kw(tmp_path, ddir, check_links=True, fetcher=fetcher, max_link_checks=5)
    )
    assert rep.links[0].status == "suspect"
    assert rep.links[0].status != "unchanged", "a stub is not evidence"
    assert rep.suspect_links == 1 and rep.changed_links == 0 and rep.gone_links == 0
    assert rep.dockets[0].state == "stale"
    assert "stub" in rep.dockets[0].reasons[0]
    assert "suspect" in (ddir / "UPDATE_BACKLOG.md").read_text()


def test_gone_link_is_gone_and_makes_docket_stale(tmp_path: Path) -> None:
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="gone-docket",
        head_sha=r["first"],
        claims=[claim_citing("keep.txt", (1, 1))],
        material=[("keep.txt", (1, 1), "untouched")],
        web_sources=[TARGET_URL],
    )
    fetcher = StubFetcher({TARGET_URL: gone_result(TARGET_URL)})
    rep = refresh_target(
        r["path"], **kw(tmp_path, ddir, check_links=True, fetcher=fetcher, max_link_checks=5)
    )
    assert rep.links[0].status == "gone" and rep.gone_links == 1
    assert rep.dockets[0].state == "stale"
    assert any(TARGET_URL in reason and "unreachable" in reason for reason in rep.dockets[0].reasons)


def test_noop_second_pass_writes_nothing(tmp_path: Path) -> None:
    """Guard B: nothing new ⇒ ``noop=True`` and byte-identical files."""
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="noop-docket",
        head_sha=r["first"],
        claims=[claim_citing("docs/FINDINGS.md", (1, 3))],
        material=[("docs/FINDINGS.md", (1, 3), "headline")],
        web_sources=[TARGET_URL],
    )
    fetcher = StubFetcher({TARGET_URL: unchanged_result(TARGET_URL)})
    args = kw(tmp_path, ddir, check_links=True, fetcher=fetcher, max_link_checks=5)

    first = refresh_target(r["path"], **args)
    assert first.noop is False and first.written
    assert first.dockets[0].state == "needs_rework"
    before = snapshot(ddir, tmp_path / "state")

    second = refresh_target(r["path"], **args)
    assert second.noop is True
    assert second.written == [] and second.planned == []
    assert snapshot(ddir, tmp_path / "state") == before


def test_dry_run_writes_nothing_but_reports(tmp_path: Path) -> None:
    r = make_repo(tmp_path)
    ddir = make_docket(
        tmp_path / "docket",
        repo_path=r["path"],
        slug="dry-docket",
        head_sha=r["first"],
        claims=[claim_citing("docs/FINDINGS.md", (1, 3))],
        material=[("docs/FINDINGS.md", (1, 3), "headline")],
    )
    before = snapshot(ddir)
    rep = refresh_target(r["path"], **kw(tmp_path, ddir, dry_run=True))
    assert rep.dry_run is True
    assert rep.dockets[0].state == "needs_rework"
    assert rep.dockets[0].reasons
    assert rep.written == [] and rep.planned, "dry run reports the work without doing it"
    assert snapshot(ddir) == before
    assert not (tmp_path / "state").exists()


def test_append_backlog_dedupes_same_entry(tmp_path: Path) -> None:
    ddir = tmp_path / "docket"
    ddir.mkdir()
    entry = ReworkEntry(
        docket_slug="s",
        reason="`a.md` changed in `x..y` (commit y)",
        required_work="re-verify claim C1",
        opened_at=NOW,
        source_ref="git:y:a.md",
    )
    assert append_backlog(ddir, [entry]) == [entry]
    assert append_backlog(ddir, [entry]) == []
    lines = [
        line
        for line in (ddir / "UPDATE_BACKLOG.md").read_text().splitlines()
        if line.startswith("- ")
    ]
    assert len(lines) == 1
    assert entry.key in lines[0]


# --------------------------------------------------------------------------- #
# RED->GREEN guard B (defect U7.2-2): the staged copy's provenance must not lie
# --------------------------------------------------------------------------- #


def _graph_harness(tmp_path: Path, r: dict, monkeypatch: pytest.MonkeyPatch):
    """Drive ``_graph_refresh`` offline: the update child is a stub, never spawned."""
    from resextract.refresh.review import _graph_refresh
    from resextract.refresh.staleness import detect_change, read_target_state

    target = r["path"]
    orig = tmp_path / "state" / "kg" / "duval" / "graphify-out" / "graph.json"
    orig.parent.mkdir(parents=True, exist_ok=True)
    orig.write_text('{"nodes": [], "edges": []}\n')
    calls: list[str] = []

    def stub(copy_dir, *, timeout):
        calls.append(str(copy_dir))
        out = Path(copy_dir) / "graphify-out" / "graph.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"nodes": [], "edges": [], "rev": len(calls)}) + "\n")
        return True, 0, "graphify update ok"

    monkeypatch.setattr("resextract.refresh.review._run_graphify_update", stub)
    notes: list[str] = []

    def run(run_update: bool = True):
        observed = read_target_state(target)
        change = detect_change(None, observed.head_sha, target)
        gr, _obj = _graph_refresh(
            target,
            "duval",
            observed,
            change,
            state_root=tmp_path / "state",
            kg_root=tmp_path / "state" / "kg",
            original_graph=orig,
            run_update=run_update,
            timeout=5.0,
            notes=notes,
        )
        return gr

    run.notes = notes
    return run, calls, orig


def test_graph_copy_restaged_when_head_advances(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """RED->GREEN guard B: a copy staged at head A must be RE-STAGED at head B.

    Revert: disable the head-mismatch branch (``elif False:`` in place of
    ``elif prior_label != current_head:``).  Measured failure — the stale copy is
    reused and the update skipped, so the graph is built from files that no
    longer match the head it claims:

        >       assert g2.restaged is True
        E       AssertionError: assert False is True
        FAILED tests/test_refresh_review.py::test_graph_copy_restaged_when_head_advances
        1 failed
    """
    r = make_repo(tmp_path)
    run, calls, _orig = _graph_harness(tmp_path, r, monkeypatch)
    g1 = run()
    assert g1.staged_from_head == r["second"]
    assert g1.restaged is False  # first ever stage, not a re-stage
    assert (Path(g1.copy_dir) / "src" / "new.py").is_file()

    (r["path"] / "docs" / "ADDED_AT_C.md").write_text("# added at C\n")
    git(r["path"], "add", "-A")
    git(r["path"], "commit", "-qm", "c3")
    third = git(r["path"], "rev-parse", "HEAD")

    g2 = run()
    assert g2.restaged is True, "a head move must re-stage, not reuse the stale copy"
    assert g2.staged_from_head == third
    assert (Path(g2.copy_dir) / "docs" / "ADDED_AT_C.md").is_file(), "the new file must exist"
    assert len(calls) == 2


def test_graph_copy_reused_at_unchanged_head_is_a_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A re-run at an unchanged head reuses the copy and writes nothing."""
    r = make_repo(tmp_path)
    run, calls, _orig = _graph_harness(tmp_path, r, monkeypatch)
    g1 = run()
    state = tmp_path / "state" / "kg-refresh" / "duval" / "graph_state.json"
    before = (state.read_bytes(), state.stat().st_mtime_ns)

    g2 = run()
    assert g2.restaged is False
    assert g2.staged_from_head == g1.staged_from_head == r["second"]
    assert "update skipped" in (g2.note or "")
    assert len(calls) == 1, "the reuse guard must skip the update on the second pass"
    assert (state.read_bytes(), state.stat().st_mtime_ns) == before, "zero writes"


def test_forged_graph_state_label_is_invalidated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A label that disagrees with the copy's real content is never trusted."""
    r = make_repo(tmp_path)
    run, _calls, _orig = _graph_harness(tmp_path, r, monkeypatch)
    run()
    state = tmp_path / "state" / "kg-refresh" / "duval" / "graph_state.json"

    (r["path"] / "docs" / "ADDED_AT_C.md").write_text("# added at C\n")
    git(r["path"], "add", "-A")
    git(r["path"], "commit", "-qm", "c3")
    third = git(r["path"], "rev-parse", "HEAD")

    payload = json.loads(state.read_text())
    assert payload["staged_from_head"] == r["second"]
    payload["staged_from_head"] = third  # the lie: content is still at `second`
    payload["observed_head"] = third
    state.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")

    g2 = run()
    assert g2.restaged is True, "a label the copy contradicts must trigger a re-stage"
    assert g2.staged_from_head == third
    assert (Path(g2.copy_dir) / "docs" / "ADDED_AT_C.md").is_file()


def test_legacy_graph_state_without_staged_label_is_invalidated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A schema-1 state file (only ``observed_head``) is migrated by re-staging."""
    r = make_repo(tmp_path)
    run, _calls, _orig = _graph_harness(tmp_path, r, monkeypatch)
    run()
    state = tmp_path / "state" / "kg-refresh" / "duval" / "graph_state.json"
    payload = json.loads(state.read_text())
    payload.pop("staged_from_head", None)
    payload.pop("copy_head", None)
    state.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")

    g2 = run()
    assert g2.restaged is True
    assert g2.staged_from_head == r["second"]
    assert any("staged_from_head" in n for n in run.notes), "the migration must be recorded"
