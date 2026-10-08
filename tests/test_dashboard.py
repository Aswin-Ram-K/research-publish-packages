"""Dashboard tests (U6.1) — offline, ``fastapi.testclient.TestClient``.

Coverage: every read route's documented shape, explicit error payloads (never a
500) for a missing/empty store, the three docket cases (valid / corrupt
MANIFEST / none at all), ordered journal events with no invented reasoning
text, a live SSE stream, directory-traversal 404s, loopback-bind enforcement
and the control-route token gate.

Fixture
-------
The dashboard fixture tree (store + journals + dockets + decoy + graph) is
**built on demand** into a pytest ``tmp_path`` by the session-scoped
``_dashboard_fixture`` below, via ``build(dest_dir)`` in
``tests/fixtures/dashboard-store/build.py``.  The suite therefore does not read
a pre-generated ``state.sqlite``, and — because ``.gitignore`` matches
``dockets/`` at any depth — it does not depend on the gitignored ``dockets/``
subtree being checked out either.  Nothing is written into the repo.

Red→green guards
----------------
``test_safe_slug_guard_blocks_traversal`` (with
``test_dockets_traversal_is_404[.../../ok-docket]``) and
``test_non_loopback_host_is_refused`` are both written so the suite goes red the
moment the guard is reverted.  The exact failures observed with each guard
reverted are pasted in those tests' docstrings.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from resextract import doctor as doctor_mod
from resextract.dashboard import api
from resextract.dashboard import app as app_mod

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "dashboard-store"
BUILD_SCRIPT = FIXTURES / "build.py"

# These point at the checked-in fixture tree only as a *default*; the
# session-scoped ``_dashboard_fixture`` below rebinds them to a tree built on
# demand in ``tmp_path``.  Tests that deliberately reference a missing path
# (``FIXTURES / "nope.json"`` etc.) keep using FIXTURES, which is intentional.
STORE = FIXTURES / "state.sqlite"
JOURNALS = FIXTURES / "journal"
DOCKETS = FIXTURES / "dockets"
EMPTY_DOCKETS = FIXTURES / "dockets-empty"
GRAPH = FIXTURES / "graph-mini.json"


def _load_builder():
    """Import ``tests/fixtures/dashboard-store/build.py`` as a module."""
    spec = importlib.util.spec_from_file_location("dashboard_store_build", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session", autouse=True)
def _dashboard_fixture(tmp_path_factory):
    """Build the dashboard fixture tree on demand into a pytest ``tmp_path``.

    Red→green guard (a *fixture-build* guard, not an assertion guard): with the
    pre-generated ``state.sqlite`` and the gitignored ``dockets/`` subtree
    removed, building here makes the whole suite pass; reverting this fixture
    (so the module again reads ``FIXTURES`` directly) makes that same clean
    state fail.  Both transcripts are pasted in the docstring of
    ``tests/fixtures/dashboard-store/build.py``.

    U6.23: no test-side normalisation is applied here.  ``build.py`` itself
    declares the fixture's ``C1`` claim and ``generated_by`` with
    ``producer="model"``, so ``ok-docket`` is valid by construction and a
    *direct* ``build.py`` run is sufficient.  The former test-side normalisation
    helper was deleted with this change (U6.23).
    """
    global STORE, JOURNALS, DOCKETS, EMPTY_DOCKETS, GRAPH
    root = _load_builder().build(tmp_path_factory.mktemp("dashboard-store"))
    STORE = root / "state.sqlite"
    JOURNALS = root / "journal"
    DOCKETS = root / "dockets"
    EMPTY_DOCKETS = root / "dockets-empty"
    GRAPH = root / "graph-mini.json"
    return root

READ_ROUTES = [
    "/api/status",
    "/api/runs",
    "/api/reasoning",
    "/api/findings",
    "/api/dockets",
    "/api/web-health",
    "/api/graph",
    "/api/doctor",
    "/api/refresh",
]


def make_app(**overrides):
    kwargs = {
        "store_path": str(STORE),
        "journal_dir": str(JOURNALS),
        "dockets_dir": str(DOCKETS),
        "graph_path": str(GRAPH),
    }
    kwargs.update(overrides)
    return app_mod.create_app(**kwargs)


@pytest.fixture()
def client():
    with TestClient(make_app()) as test_client:
        yield test_client


# --------------------------------------------------------------------------- #
# 1. read routes: 200 + documented shape
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("route", READ_ROUTES)
def test_read_routes_return_200_with_json_shape(client, route):
    response = client.get(route)
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    assert "error" not in body or body.get("error") is None


def test_ui_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "resextract" in response.text


def test_status_reports_fixture_counts(client):
    body = client.get("/api/status").json()
    assert body["tables"]["runs"] == 2
    assert body["tables"]["candidates"] == 2
    assert body["tables"]["claims"] == 2
    assert body["tables"]["verdicts"] == 1
    assert body["schema_version"] >= 1


def test_runs_summary_has_status_tokens_and_resume_point(client):
    body = client.get("/api/runs").json()
    assert body["count"] == 2
    run_ids = {run["id"] for run in body["runs"]}
    assert run_ids == {1, 2}
    tokens = {run["id"]: run["tokens_used"] for run in body["runs"]}
    assert tokens[1] == 1200 and tokens[2] == 0
    assert body["degradations"], "the zero-token / running run must be flagged"
    assert any(d["kind"] == "zero_tokens_recorded" for d in body["degradations"])
    assert body["resume_point"]["run_end"] in (True, False)
    journal_ids = {journal["run_id"] for journal in body["journals"]}
    assert {"fixture-run", "sparse-run"} <= journal_ids
    verified = {journal["run_id"]: journal["verify"]["ok"] for journal in body["journals"]}
    assert verified["fixture-run"] is True


def test_findings_join_claims_to_verdicts_with_provenance(client):
    body = client.get("/api/findings").json()
    counts = body["counts"]
    assert counts["candidates"] == 2
    assert counts["claims"] == 2
    assert counts["verdicts"] == 1
    accepted = body["candidates"]
    assert len(accepted) == 1
    candidate = accepted[0]
    assert candidate["provenance_json"]
    claim = candidate["claims"][0]
    assert claim["verdict"]["verdict"] == "CONFIRMS"
    assert claim["evidence"][0]["source_ref"] == "src/a.ts#L1-L2"


def test_findings_expose_rejected_candidates_and_reasons(client):
    body = client.get("/api/findings").json()
    assert body["counts"]["candidates_rejected"] == 2  # 1 store row + 1 journal row
    assert body["counts"]["candidates_rejected_in_journal"] == 1
    reasons = body["rejected_reasons"]
    assert reasons.get("all-refs-invalid") == 1


def test_web_health_shows_degradation(client):
    body = client.get("/api/web-health").json()
    assert body["search_health"]["total"] == 2
    assert body["search_health"]["failed"] == 1
    assert body["search_health"]["by_engine_failed"] == {"google": 1}
    assert body["web_sources"]["total"] == 2
    assert body["web_sources"]["gone"] == 1
    assert body["degraded"] is True


def test_graph_summary_counts_hash_and_mtime(client):
    body = client.get("/api/graph").json()
    assert body["nodes"] == 3
    assert body["edges"] == 2
    assert body["communities"] == 2
    assert body["top_dirs"]["src"] == 2
    assert len(body["sha256"]) == 64
    assert body["mtime"] and body["bytes"] > 0


def test_graph_missing_is_error_payload():
    with TestClient(make_app(graph_path=str(FIXTURES / "nope.json"))) as test_client:
        response = test_client.get("/api/graph")
        assert response.status_code == 200
        assert "graph file not found" in response.json()["error"]


def test_refresh_backlog_none_recorded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(
        make_app(store_path=str(FIXTURES / "nope.sqlite"), dockets_dir=str(EMPTY_DOCKETS))
    ) as test_client:
        body = test_client.get("/api/refresh").json()
    assert body["count"] == 0
    assert body["open"] == [] and body["closed"] == []
    assert "none recorded yet" in body["note"]


def test_refresh_backlog_reports_rework_rows_and_backlog_file(client):
    body = client.get("/api/refresh").json()
    assert body["count"] == 1
    assert body["open_count"] == 1
    assert body["open"][0]["reason"] == "source moved"
    paths = [item["path"] for item in body["files"]]
    assert any(path.endswith("UPDATE_BACKLOG.md") for path in paths)


# --------------------------------------------------------------------------- #
# 2. missing / empty store: explicit error payload, never a 500
# --------------------------------------------------------------------------- #


def test_missing_store_returns_error_payload_not_500():
    missing = FIXTURES / "does-not-exist.sqlite"
    with TestClient(make_app(store_path=str(missing))) as test_client:
        for route in ["/api/status", "/api/runs", "/api/findings", "/api/web-health"]:
            response = test_client.get(route)
            assert response.status_code == 200, route
            body = response.json()
            assert "error" in body and body["error"], route
            assert "store not found" in body["error"], route


def test_empty_store_without_tables_returns_error_payload(tmp_path):
    empty = tmp_path / "empty.sqlite"
    sqlite3.connect(str(empty)).close()
    with TestClient(make_app(store_path=str(empty))) as test_client:
        runs = test_client.get("/api/runs").json()
        assert "error" in runs and "unavailable" in runs["error"]
        findings = test_client.get("/api/findings").json()
        assert "error" in findings
        assert findings["counts"]["candidates"] == 0


# --------------------------------------------------------------------------- #
# 3. dockets: valid, corrupt manifest, none at all
# --------------------------------------------------------------------------- #


def test_dockets_board_lists_valid_and_corrupt(client):
    body = client.get("/api/dockets").json()
    assert body["count"] == 2
    by_slug = {d["slug"]: d for d in body["dockets"]}
    valid = by_slug["ok-docket"]
    assert valid["status"] == "ready"
    assert valid["type"] == "report"
    assert valid["freshness"]["state"] == "stale"
    assert valid["freshness"]["age_days"] == 1.5
    assert valid["claims"] == 2
    assert valid["material"] == 1
    assert valid["open_questions"] == ["does the fixture cover every claim it makes?"]
    assert valid["rework_open"]
    assert valid["verify"]["ok"] is True
    assert any(f["path"] == "material/note.txt" for f in valid["files"])

    broken = by_slug["broken-docket"]
    assert broken["status"] == "unreadable"
    assert broken["verify"]["ok"] is False
    assert "unreadable" in broken["error"]


def test_dockets_none_at_all_is_explicit():
    with TestClient(make_app(dockets_dir=str(EMPTY_DOCKETS))) as test_client:
        body = test_client.get("/api/dockets").json()
    assert body["count"] == 0
    assert "no MANIFEST.json" in body["note"]
    with TestClient(make_app(dockets_dir=str(FIXTURES / "no-dockets-here"))) as test_client:
        body = test_client.get("/api/dockets").json()
    assert body["count"] == 0
    assert "no dockets directory" in body["note"]


def test_docket_detail_renders_headings(client):
    body = client.get("/api/dockets/ok-docket").json()
    assert body["slug"] == "ok-docket"
    assert body["manifest"]["lane"]["slug"] == "fixture-lane"
    docs = {doc["name"]: doc for doc in body["documents"]}
    assert docs["README.md"]["present"] is True
    assert {"level": 1, "text": "Fixture docket"} in docs["README.md"]["headings"]
    assert docs["CLAIMS.md"]["headings"][0]["text"] == "Claims"
    assert docs["UPDATE_BACKLOG.md"]["present"] is True
    assert body["verify"]["ok"] is True


def test_docket_detail_unknown_slug_is_404(client):
    assert client.get("/api/dockets/no-such-docket").status_code == 404
    assert client.get("/api/dockets/broken-docket").status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        "/api/dockets/..%2f..%2fetc%2fpasswd",
        "/api/dockets/..%2fok-docket",
        "/api/dockets/%2e%2e%2f%2e%2e%2fok-docket",
        "/api/dockets/....%2fok-docket",
    ],
)
def test_dockets_traversal_is_404(client, path):
    response = client.get(path)
    assert response.status_code == 404, f"{path} leaked: {response.status_code}"


def test_safe_slug_guard_blocks_traversal():
    """Red→green guard: reverting ``safe_slug`` fails this test.

    With every check in :func:`api.safe_slug` removed (``return candidate``),
    the observed run was::

        $ .venv/bin/python -m pytest tests/test_dashboard.py -k "traversal or safe_slug" -q
        >           assert api.safe_slug(candidate) is None, candidate
        E           AssertionError: ../../etc/passwd
        E           assert '../../etc/passwd' is None
        E            +  where <function safe_slug at 0x...> = api.safe_slug
        FAILED tests/test_dashboard.py::test_dockets_traversal_is_404[/api/dockets/..%2fok-docket]
        FAILED tests/test_dashboard.py::test_safe_slug_guard_blocks_traversal - Asser...
        2 failed, 4 passed, 42 deselected
    """
    for candidate in ["../../etc/passwd", "../ok-docket", "a/b", "..", ".", "x\x00y", ""]:
        assert api.safe_slug(candidate) is None, candidate
    assert api.safe_slug("ok-docket") == "ok-docket"
    assert api.safe_slug("_smoke") == "_smoke"


# --------------------------------------------------------------------------- #
# 3b. nested dockets (real dockets live under ``dockets/duval/<slug>``) and the
#     *path-specific* guard the single-segment test above cannot pin
# --------------------------------------------------------------------------- #


def _nested_dockets_root(tmp_path: Path) -> Path:
    """Dockets root holding a nested docket (``duval/duval-u55-pinned``)."""
    import shutil

    root = tmp_path / "dockets"
    dest = root / "duval" / "duval-u55-pinned"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(DOCKETS / "ok-docket", dest)
    shutil.copytree(DOCKETS / "ok-docket", root / "ok-docket")
    return root


def test_nested_docket_detail_returns_manifest(tmp_path):
    """A multi-segment slug resolves — the old 404 on ``duval/duval-u55-pinned``."""
    root = _nested_dockets_root(tmp_path)
    with TestClient(make_app(dockets_dir=str(root))) as nested:
        response = nested.get("/api/dockets/duval/duval-u55-pinned")
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["error"] is None
        assert payload["slug"] == "duval/duval-u55-pinned"
        assert payload["manifest"]["status"] == "ready"
        assert payload["manifest"]["lane"]["slug"] == "fixture-lane"
        docs = {doc["name"]: doc for doc in payload["documents"]}
        assert docs["README.md"]["present"] is True
        assert {"level": 1, "text": "Fixture docket"} in docs["README.md"]["headings"]
        assert any(f["path"] == "material/note.txt" for f in payload["files"])
        assert payload["verify"]["ok"] is True
        # the board no longer self-discloses route_slug: null for a nested docket
        board = nested.get("/api/dockets").json()
        entry = {d["slug"]: d for d in board["dockets"]}["duval/duval-u55-pinned"]
        assert entry["route_slug"] == "duval/duval-u55-pinned"
        # single-segment slugs keep working exactly as before
        assert nested.get("/api/dockets/ok-docket").status_code == 200


def test_nested_traversal_encodings_are_404(tmp_path):
    """Nested/path-specific refusals; with the four above these are all 6 encodings."""
    root = _nested_dockets_root(tmp_path)
    refused = [
        "/api/dockets/duval/..%2f..%2fetc%2fpasswd",  # nested traversal
        "/api/dockets/duval/%2e%2e%2f_smoke",  # nested ``..`` segment
        "/api/dockets/..%5c..%5cetc%5cpasswd",  # backslash encoding
        "/api/dockets/%252e%252e%252fok-docket",  # double encoding
        "/api/dockets/%2fetc%2fpasswd",  # encoded leading slash (empty segment)
        "/api/dockets/duval/%2e/_smoke",  # ``.`` segment
        "/api/dockets/escape",  # realpath escape: symlink out of the root
        "/api/dockets/duval/up",  # nested realpath escape
    ]
    outside = tmp_path / "outside" / "sneaky"
    outside.mkdir(parents=True)
    (outside / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (root / "escape").symlink_to(outside)
    (root / "duval" / "up").symlink_to(outside)
    with TestClient(make_app(dockets_dir=str(root))) as escaping:
        for path in refused:
            response = escaping.get(path)
            assert response.status_code == 404, f"{path} leaked: {response.status_code}"
        # the refusal is the guard's explicit payload, not a bare routing 404
        for path in [
            "/api/dockets/duval/%2e%2e%2f_smoke",
            "/api/dockets/escape",
            "/api/dockets/duval/up",
        ]:
            assert escaping.get(path).json().get("error"), path
        # an existing directory with no MANIFEST.json is an explicit 404, not a 500
        missing = escaping.get("/api/dockets/duval")
        assert missing.status_code == 404
        assert missing.json()["error"] == "docket not found: 'duval'"


def test_dot_segment_is_refused_not_normalised(tmp_path):
    """Decision: ``duval/../_smoke`` is REFUSED, never normalised to ``_smoke``.

    Normalising would mean silently accepting a client-supplied traversal path;
    ``_smoke`` is reachable directly under its own slug, so nothing is lost.
    The *reason* is pinned, not merely the status code.
    """
    root = _nested_dockets_root(tmp_path)
    with TestClient(make_app(dockets_dir=str(root))) as nested:
        response = nested.get("/api/dockets/duval/..%2f_smoke")
        assert response.status_code == 404, response.text
        body = response.json()
        assert body["slug"] == "duval/../_smoke"
        assert body["error"] == "invalid docket slug: 'duval/../_smoke'"
        # the same docket is reachable directly, under its own slug
        assert nested.get("/api/dockets/duval/duval-u55-pinned").status_code == 200


def test_safe_docket_slug_pins_path_validation(tmp_path):
    """Red→green for the *path-specific* guard the old test could not pin.

    ``escape`` and ``duval`` are **accepted** by ``safe_slug`` — they are plain
    ``[A-Za-z0-9._-]+`` segments — so reverting ``safe_docket_slug`` to the old
    ``safe_slug``-only behaviour leaves ``_SLUG_RE`` and the leading-dot check
    intact and still fails here, naming the offending input.  Reverting only the
    ``"/" or "\\\\" or ".."`` line of ``safe_slug`` leaves this green too: for
    every single-segment input that line is masked.  What this test pins is the
    multi-segment path handling and the ``realpath`` containment.
    """
    root = tmp_path / "dockets"
    (root / "duval").mkdir(parents=True)
    outside = tmp_path / "outside"
    (outside / "sneaky").mkdir(parents=True)
    (outside / "sneaky" / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (root / "escape").symlink_to(outside / "sneaky")
    (root / "duval" / "up").symlink_to(outside / "sneaky")
    (root / "duval" / "real").mkdir()

    # the masking checks genuinely accept these two
    assert api.safe_slug("escape") == "escape"
    assert api.safe_slug("duval") == "duval"
    assert api.safe_docket_slug("escape", str(root)) is None, (
        "escape (realpath leaves the dockets root)"
    )
    assert api.safe_docket_slug("duval/up", str(root)) is None, (
        "duval/up (nested realpath escape)"
    )

    for candidate in [
        "duval/../_smoke",
        "duval/../../etc/passwd",
        "duval/./real",
        "duval//real",
        "duval/",
        "/etc/passwd",
        "..",
    ]:
        assert api.safe_docket_slug(candidate, str(root)) is None, candidate

    assert api.safe_docket_slug("duval/real", str(root)) == "duval/real"
    assert api.safe_docket_slug("_smoke", str(root)) == "_smoke"


# --------------------------------------------------------------------------- #
# 4. reasoning: ordered events, no invented reasoning text
# --------------------------------------------------------------------------- #


def test_reasoning_trace_is_ordered_and_does_not_invent_reasoning(client):
    body = client.get("/api/reasoning", params={"run_id": "fixture-run"}).json()
    assert body["reasoning_text_available"] is False
    assert body["reasoning_text_field"] is None
    assert "does not journal it yet" in body["note"]
    assert body["verify"]["ok"] is True
    seqs = [event["seq"] for event in body["events"]]
    assert seqs == sorted(seqs)
    assert seqs == [1, 2, 3, 4, 5, 6]
    kinds = [event["kind"] for event in body["events"]]
    assert kinds[0] == "run_start" and kinds[-1] == "run_end"
    for event in body["events"]:
        assert "reasoning_content" not in event["payload"]
        assert json.dumps(event["payload"])  # plain JSON-serialisable payload
    assert "reasoning_tokens" in body["fields_present"]
    assert "reasoning_content" not in body["fields_present"]
    # the rejection reason is carried in the payload, not summarised away
    rejected = next(e for e in body["events"] if e["kind"] == "candidate_rejected")
    assert rejected["payload"]["reason"] == "all-refs-invalid"


def test_reasoning_trace_honours_limit(client):
    body = client.get("/api/reasoning", params={"run_id": "fixture-run", "limit": 2}).json()
    assert body["count"] == 2
    assert [e["seq"] for e in body["events"]] == [5, 6]
    assert body["truncated"] is True


def test_reasoning_trace_unknown_run_is_error_payload(client):
    response = client.get("/api/reasoning", params={"run_id": "no-such-run"})
    assert response.status_code == 200
    body = response.json()
    assert "no journal found" in body["error"]
    assert body["events"] == []
    assert body["reasoning_text_available"] is False


# --------------------------------------------------------------------------- #
# 5. SSE
# --------------------------------------------------------------------------- #


def test_sse_events_stream_yields_heartbeat_and_event(client):
    with client.stream("GET", "/api/events", params={"ticks": 1}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        lines = [line for line in response.iter_lines() if line][:8]
    text = "\n".join(lines)
    assert "event: heartbeat" in text
    data_lines = [line[6:] for line in lines if line.startswith("data: ")]
    assert data_lines, f"no data lines in stream: {lines!r}"
    payload = json.loads(data_lines[0])
    assert "at" in payload and "journals" in payload


def test_sse_stream_is_not_a_one_shot_stub(client):
    with client.stream("GET", "/api/events", params={"ticks": 2}) as response:
        lines = [line for line in response.iter_lines() if line]
    heartbeats = [line for line in lines if line == "event: heartbeat"]
    assert len(heartbeats) >= 2, lines


# --------------------------------------------------------------------------- #
# 6. doctor
# --------------------------------------------------------------------------- #


def test_doctor_route_reports_legs_and_occamy(client, monkeypatch):
    def fake_doctor(**_kwargs):
        return {
            "ok": False,
            "exit_code": 2,
            "checked_at": "2026-10-08T12:00:00.000Z",
            "legs": [
                {"leg": "Occamy", "class": "core", "ok": False, "detail": "ConnectError: refused"},
                {"leg": "SearXNG", "class": "core", "ok": True, "detail": "HTTP 200"},
            ],
            "core_down": ["Occamy"],
            "optional_down": [],
        }

    monkeypatch.setattr(doctor_mod, "run_doctor", fake_doctor)
    body = client.get("/api/doctor").json()
    assert body["by_leg"]["Occamy"]["ok"] is False
    assert body["occamy"]["detail"] == "ConnectError: refused"
    assert body["core_down"] == ["Occamy"]


def test_doctor_status_never_raises(monkeypatch):
    layer = api.DataLayer(str(STORE), str(JOURNALS), str(DOCKETS), str(GRAPH))

    def boom(**_kwargs):
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(doctor_mod, "run_doctor", boom)
    report = layer.doctor_status(force=True)
    assert report["ok"] is False
    assert "probe exploded" in report["error"]


# --------------------------------------------------------------------------- #
# 7. loopback enforcement (red→green guard)
# --------------------------------------------------------------------------- #


def test_non_loopback_host_is_refused():
    """Red→green guard: reverting ``check_bind_host`` fails this test.

    With the refusal removed (``check_bind_host`` returning the host
    unconditionally), the observed run was::

        $ .venv/bin/python -m pytest tests/test_dashboard.py -k non_loopback -q
        >       with pytest.raises(ValueError):
        E       Failed: DID NOT RAISE ValueError
        FAILED tests/test_dashboard.py::test_non_loopback_host_is_refused - Failed: D...
        1 failed, 5 passed, 42 deselected
    """
    with pytest.raises(ValueError, match="refusing to bind non-loopback host '0.0.0.0'"):
        app_mod.create_app(host="0.0.0.0")
    with pytest.raises(ValueError, match="refusing to bind non-loopback host '192.168.2.168'"):
        app_mod.create_app(store_path=str(STORE), host="192.168.2.168")
    remote = app_mod.create_app(store_path=str(STORE), host="0.0.0.0", allow_remote=True)
    assert remote.state.dashboard["host"] == "0.0.0.0"
    assert remote.state.dashboard["allow_remote"] is True


@pytest.mark.parametrize(
    "host,expected",
    [
        ("127.0.0.1", True),
        ("::1", True),
        ("localhost", True),
        ("0.0.0.0", False),
        ("192.168.2.168", False),
        ("example.invalid", False),
        (None, False),
    ],
)
def test_is_loopback(host, expected):
    assert app_mod.is_loopback(host) is expected


# --------------------------------------------------------------------------- #
# 8. token gate: control routes only
# --------------------------------------------------------------------------- #


def test_token_gate_applies_to_control_not_read_routes():
    with TestClient(make_app(token="s3cret")) as test_client:
        for route in READ_ROUTES:
            assert test_client.get(route).status_code == 200, route
        assert test_client.post("/api/control/rescan").status_code == 401
        assert test_client.post("/api/control/rescan", headers={"X-Dashboard-Token": "wrong"}).status_code == 401
        ok = test_client.post("/api/control/rescan", headers={"X-Dashboard-Token": "s3cret"})
        assert ok.status_code == 200
        assert ok.json()["ok"] is True
        bearer = test_client.post("/api/control/doctor", headers={"Authorization": "Bearer s3cret"})
        assert bearer.status_code == 200


def test_control_routes_open_when_no_token_configured():
    with TestClient(make_app()) as test_client:
        assert test_client.post("/api/control/rescan").status_code == 200


# --------------------------------------------------------------------------- #
# 9. byte cap
# --------------------------------------------------------------------------- #


def test_byte_cap_truncates_journal_reasoning_trace():
    with TestClient(make_app(max_bytes=64)) as test_client:
        body = test_client.get("/api/reasoning", params={"run_id": "fixture-run"}).json()
    assert body["truncated"] is True
    assert body["count"] < 6
    assert body["bytes_cap"] == 64


# --------------------------------------------------------------------------- #
# 3c. U6.6 — per-file containment inside an ACCEPTED docket
#
# The directory-level guard (``safe_docket_slug``: every segment through
# ``safe_slug`` plus ``realpath`` containment of the joined directory) is
# load-bearing and stays *exactly* as it was.  V6B found the layer below it: an
# accepted docket could still serve a file from OUTSIDE the dockets root through
# a **file symlink** inside it, because ``_read_text_capped`` and
# ``_docket_files`` both followed symlinks.  These tests plant that escape.
# --------------------------------------------------------------------------- #

OUTSIDE_MARKER = "MARKER-U6.6-LEAKED-OUTSIDE-HEADING"


def _symlink_escape_root(tmp_path: Path):
    """Scratch dockets root with an accepted docket holding symlink escapes."""
    import os
    import shutil

    root = tmp_path / "dockets"
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)
    (outside / "secret.md").write_text(
        f"# {OUTSIDE_MARKER}\n\nharmless local body, not a real secret\n", encoding="utf-8"
    )
    docket = root / "_smoke"
    shutil.copytree(DOCKETS / "ok-docket", docket)
    readme = docket / "README.md"
    readme.unlink()
    readme.symlink_to(os.path.relpath(outside / "secret.md", docket))
    # the same escape through a different door: a directory symlink pointing out
    (docket / "linked-dir").symlink_to(outside, target_is_directory=True)
    return root, outside


def test_docket_file_symlink_outside_is_refused_not_served(tmp_path):
    """Red->green guard (a): per-file ``realpath`` containment on every read.

    V6B's recipe.  Before the fix the direct path was already 404 by realpath,
    but requesting the accepted docket returned 200 and served the OUTSIDE
    file's heading text and size::

        DIRECT /api/dockets/_smoke/README.md -> 404
        DOCKET /api/dockets/_smoke           -> 200
        "documents": [{"name": "README.md", "present": true, "bytes": 77,
          "headings": [{"level": 1, "text": "MARKER-U6.6-LEAKED-OUTSIDE-HEADING"}]}]

    With only the ``docket_detail`` containment reverted (``real = path``) the
    observed failure was::

        >           assert OUTSIDE_MARKER not in response.text
        E           AssertionError: assert 'MARKER-U6.6-LEAKED-OUTSIDE-HEADING' not in '...'
        FAILED tests/test_dashboard.py::test_docket_file_symlink_outside_is_refused_not_served
    """
    root, outside = _symlink_escape_root(tmp_path)
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        direct = test_client.get("/api/dockets/_smoke/README.md")
        assert direct.status_code == 404  # refused: that path's realpath escapes
        assert OUTSIDE_MARKER not in direct.text
        response = test_client.get("/api/dockets/_smoke")
        assert response.status_code == 200, response.text
        # the outside file's heading text is ABSENT from the 200 body
        assert OUTSIDE_MARKER not in response.text
        assert str(outside) not in response.text
        documents = {doc["name"]: doc for doc in response.json()["documents"]}
        readme = documents["README.md"]
        assert readme["present"] is False
        assert readme["headings"] == []
        assert readme["bytes"] == 0
        assert readme["error"], "an explicit refusal payload, never a silent serve"
        assert "outside the dockets root" in readme["error"]
        # the same docket's in-root documents are untouched (no over-blocking)
        claims = documents["CLAIMS.md"]
        assert claims["present"] is True
        assert claims["headings"][0]["text"] == "Claims"


def test_symlink_escape_is_excluded_from_the_file_listing(tmp_path):
    """Red->green guard (b): the ``_docket_files`` listing realpath containment.

    ``_docket_files`` followed the symlink too, disclosing the OUTSIDE file's
    existence and size at 200 (``{"path": "README.md", "bytes": 77}``, 77 being
    the outside file's size).  With only that containment reverted
    (``if False: continue``) the observed failure was::

        >           assert "README.md" not in paths
        E           AssertionError: ['CLAIMS.md', ..., 'README.md', ...]
        FAILED tests/test_dashboard.py::test_symlink_escape_is_excluded_from_the_file_listing
    """
    root, outside = _symlink_escape_root(tmp_path)
    outside_size = (outside / "secret.md").stat().st_size
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        body = test_client.get("/api/dockets/_smoke").json()
        paths = [entry["path"] for entry in body["files"]]
        assert "README.md" not in paths, paths  # resolves outside -> excluded
        # a directory symlink is not traversed into; nothing under it is listed
        assert not any(path.startswith("linked-dir") for path in paths), paths
        assert "material/note.txt" in paths  # in-root files still listed
        assert all(entry["bytes"] != outside_size for entry in body["files"]), body["files"]
        # the predicate contains the directory door as well as the file door
        assert api._contained_realpath(root / "_smoke" / "README.md", root) is None
        assert api._contained_realpath(root / "_smoke" / "linked-dir" / "secret.md", root) is None
        note = root / "_smoke" / "material" / "note.txt"
        assert api._contained_realpath(note, root) is not None


def test_symlink_edge_cases_are_explicit_and_never_a_500(tmp_path):
    """Broken symlink, dir-where-a-file-is-expected, and the in-root decision.

    Decision — an **in-root symlink is ALLOWED**: ``alias.md -> material/note.txt``
    still resolves inside ``realpath(dockets_dir)``, so it is not an escape.
    The boundary is realpath containment, not "symlinks are banned"; banning
    them would break legitimate in-docket aliases for no security gain.  An
    escape is refused per file whether or not its target exists, and the
    refusal is an explicit payload — never a 500, never a silent omission.
    """
    import shutil

    root = tmp_path / "dockets"
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)
    (outside / "secret.md").write_text("# LEAK-MARKER-EDGE\n", encoding="utf-8")
    docket = root / "_smoke"
    shutil.copytree(DOCKETS / "ok-docket", docket)
    (docket / "README.md").unlink()
    (docket / "README.md").symlink_to(outside / "missing.md")  # broken, outside
    (docket / "CLAIMS.md").unlink()
    (docket / "CLAIMS.md").symlink_to(outside, target_is_directory=True)  # dir as a file
    (docket / "UPDATE_BACKLOG.md").unlink()
    (docket / "UPDATE_BACKLOG.md").symlink_to("material/nope.md")  # broken, in-root
    (docket / "alias.md").symlink_to("material/note.txt")  # in-root alias: allowed
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        response = test_client.get("/api/dockets/_smoke")
        assert response.status_code == 200, response.text  # explicit, never a 500
        documents = {doc["name"]: doc for doc in response.json()["documents"]}
        for name in ("README.md", "CLAIMS.md", "UPDATE_BACKLOG.md"):
            assert documents[name]["present"] is False, name
            assert documents[name]["error"], name
        assert "LEAK-MARKER-EDGE" not in response.text
        paths = {entry["path"]: entry for entry in response.json()["files"]}
        assert "alias.md" in paths  # in-root alias allowed...
        assert paths["alias.md"]["bytes"] == (docket / "material" / "note.txt").stat().st_size
        assert "README.md" not in paths  # ...outside escapes excluded


def test_ver_dotdot2_is_refused_and_the_dotdot_line_is_not_dead_code(tmp_path):
    """The ``"/" or "\\\\" or ".."`` line of ``safe_slug`` (``api.py:122``) is load-bearing.

    V6B measured that a docket whose *name* contains an internal ``..``
    (``ver..2``) is refused **with** the line and 200-routable **without** it: it
    has no separator, no NUL byte, no leading dot and matches ``_SLUG_RE``, so
    no other check in ``safe_slug`` masks it, and the directory is inside the
    root so ``safe_docket_slug``'s realpath containment is satisfied.  The
    masking count for every *other* traversal pin, measured by deleting only
    that line::

        $ pytest tests/test_dashboard.py -k "traversal or safe_slug" -q
        6 passed, N deselected

    All 6 remaining pins stay green and only this test goes red — which is why
    the check can never be deleted as redundant.
    """
    import shutil

    root = tmp_path / "dockets"
    root.mkdir(parents=True)
    shutil.copytree(DOCKETS / "ok-docket", root / "ver..2")
    assert (root / "ver..2" / "MANIFEST.json").is_file(), "the docket really exists on disk"
    assert api.safe_slug("ver..2") is None
    assert api.safe_docket_slug("ver..2", str(root)) is None
    assert api._SLUG_RE.match("ver..2"), "no other check in safe_slug refuses it"
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        response = test_client.get("/api/dockets/ver..2")
        assert response.status_code == 404, response.text
        assert response.json()["error"] == "invalid docket slug: 'ver..2'"


def test_existing_containment_layers_stay_intact(tmp_path):
    """The two pre-existing layers this fix must not weaken, plus the 6 encodings.

    * ``safe_slug``'s per-segment validation refuses an in-root
      ``duval/../_smoke`` — **refused, not normalised** to ``_smoke``;
    * ``safe_docket_slug``'s ``realpath`` containment refuses the symlinked
      docket ``escape`` even though ``safe_slug("escape") == "escape"`` — i.e.
      the realpath layer, not ``_SLUG_RE``, is what refuses it.
    """
    root = _nested_dockets_root(tmp_path)
    outside = tmp_path / "outside" / "sneaky"
    outside.mkdir(parents=True)
    (outside / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (root / "escape").symlink_to(outside)
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        for path in [
            "/api/dockets/duval/..%2f..%2fetc%2fpasswd",
            "/api/dockets/duval/%2e%2e%2f_smoke",
            "/api/dockets/..%5c..%5cetc%5cpasswd",
            "/api/dockets/%252e%252e%252fok-docket",
            "/api/dockets/%2fetc%2fpasswd",
            "/api/dockets/duval/%2e/_smoke",
        ]:
            assert test_client.get(path).status_code == 404, path  # all 6 encodings
        escaped = test_client.get("/api/dockets/escape")
        assert escaped.status_code == 404  # refused by realpath, not by _SLUG_RE
        assert escaped.json()["error"]
        assert api.safe_slug("escape") == "escape"
        assert test_client.get("/api/dockets/duval/..%2f_smoke").status_code == 404
        # an escaped docket directory is not advertised on the board either
        board = test_client.get("/api/dockets").json()
        assert "escape" not in {entry["slug"] for entry in board["dockets"]}
        assert all(entry["route_slug"] for entry in board["dockets"])


# --------------------------------------------------------------------------- #
# 3. refresh_backlog: the residual uncontained read (U6.8)
#
# The preceding unit contained ``_docket_files``, every ``HEADING_FILES`` read,
# ``MANIFEST.json`` and ``dockets()`` — but one ``_read_text_capped`` call site
# was left uncontained: ``DataLayer.refresh_backlog``, which reads every
# ``UPDATE_BACKLOG.md`` / ``WORK_SUGGESTIONS.md`` it finds under **two** roots
# (``dockets_dir`` and the process ``cwd``) and is served by ``GET /api/refresh``.
# These tests pin the fix and the fd-based TOCTOU close.
# --------------------------------------------------------------------------- #

RESIDUAL_MARKER = "MARKER-U6.8-BACKLOG-LEAK-3f9a"


def _backlog_escape_root(tmp_path: Path):
    """Scratch dockets root with an escaping ``UPDATE_BACKLOG.md`` symlink."""
    root = tmp_path / "dockets"
    root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)
    (outside / "leaked.md").write_text(
        f"# {RESIDUAL_MARKER}\n\noutside body, harmless local marker\n", encoding="utf-8"
    )
    docket = root / "_smoke"
    docket.mkdir()
    (docket / "WORK_SUGGESTIONS.md").write_text("# Real suggestions\n", encoding="utf-8")
    (docket / "UPDATE_BACKLOG.md").symlink_to(outside / "leaked.md")
    return root, outside


def test_refresh_backlog_symlink_escape_is_refused_not_served(tmp_path):
    """Red->green guard (a): per-file containment on the ``refresh_backlog`` read.

    Before this fix ``refresh_backlog`` called ``_read_text_capped(path)``
    directly on every candidate, with **no containment at all**, so one symlink
    named ``UPDATE_BACKLOG.md`` anywhere under the dockets tree made
    ``GET /api/refresh`` serve the OUTSIDE file.  Observed at function level on
    the scratch root under ``state/U6.8`` before the fix::

        {"path": "state/U6.8/scratch/dockets/escape-docket/UPDATE_BACKLOG.md",
         "bytes": 45, "truncated": false,
         "headings": [{"level": 1, "text": "LEAKED-U68-MARKER-3f9a"}]}

    With only GUARD-A reverted (``real = path``) the failure returns::

        >   assert RESIDUAL_MARKER not in response.text
        E   AssertionError: assert 'MARKER-U6.8-BACKLOG-LEAK-3f9a' not in '...'
    """
    root, outside = _backlog_escape_root(tmp_path)
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        response = test_client.get("/api/refresh")
        assert response.status_code == 200, response.text
        # the outside file's bytes, size, path and headings are ABSENT
        assert RESIDUAL_MARKER not in response.text
        assert str(outside) not in response.text
        entries = {entry["path"]: entry for entry in response.json()["files"]}
        escaped = [e for p, e in entries.items() if p.endswith("UPDATE_BACKLOG.md")]
        assert escaped, "the escaping candidate is disclosed, not silently dropped"
        assert escaped[0]["present"] is False
        assert escaped[0]["bytes"] == 0
        assert escaped[0]["headings"] == []
        assert "resolves outside the docket root" in escaped[0]["error"]
        # legitimate in-root backlog content is still served (no over-blocking)
        legit = [e for p, e in entries.items() if p.endswith("WORK_SUGGESTIONS.md")]
        assert legit and legit[0]["present"] is True
        assert legit[0]["headings"][0]["text"] == "Real suggestions"


def test_refresh_backlog_does_not_resolve_against_cwd(tmp_path, monkeypatch):
    """The ``cwd`` root is DROPPED: a cwd-relative symlink is no longer consulted.

    ``cwd`` made the escape *easier*: no docket, no slug and no dockets-tree
    membership was needed — a single file named ``UPDATE_BACKLOG.md`` in the
    process's working directory was enough for an arbitrary-path read through
    ``GET /api/refresh``.  Reverting that decision (putting ``Path.cwd()`` back
    into ``roots``) makes this test fail with the outside marker served at 200.
    """
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leaked.md").write_text(f"# {RESIDUAL_MARKER}\n", encoding="utf-8")
    (work / "UPDATE_BACKLOG.md").symlink_to(outside / "leaked.md")
    root = tmp_path / "dockets"
    root.mkdir()
    with TestClient(
        make_app(dockets_dir=str(root), store_path=str(FIXTURES / "nope.sqlite"))
    ) as test_client:
        body = test_client.get("/api/refresh").json()
    assert json.dumps(body).find(RESIDUAL_MARKER) == -1
    assert body["files"] == [], "a cwd-relative backlog file is not a root any more"


def test_refresh_backlog_fd_identity_survives_a_swap_in_the_window(tmp_path, monkeypatch):
    """Red->green guard (b): containment is decided on the path, PROVEN on the fd.

    The two-step window is exactly ``real = _contained_realpath(path, root)``
    (check) and then ``open(path)`` (use).  This test lands a write *inside* that
    window: ``_open_readonly`` is wrapped so the symlink is retargeted outside the
    root immediately before the real ``os.open``.  The path-level check already
    passed (the link pointed in-root), so a path-trusting reader would read the
    outside file; the descriptor identity check refuses::

        refused: the opened file descriptor is '.../outside/leaked.md', not the
        validated path '.../dockets/_smoke/insider.md' (swapped between check and use)

    With GUARD-B reverted (trust ``expected_real`` and read without comparing the
    fd's identity) this test fails with ``RESIDUAL_MARKER in text``.
    """
    root, outside = _backlog_escape_root(tmp_path)
    docket = root / "_smoke"
    link = docket / "UPDATE_BACKLOG.md"
    link.unlink()
    insider = docket / "insider.md"
    insider.write_text("# INSIDER-legit\n", encoding="utf-8")
    link.symlink_to(insider)  # in-root: GUARD-A passes
    real = api._contained_realpath(link, root)
    assert real is not None and real == insider.resolve()

    original = api._open_readonly

    def swapping(target):
        # the attacker's write, landing precisely between check and use
        link.unlink()
        link.symlink_to(outside / "leaked.md")
        return original(target)

    monkeypatch.setattr(api, "_open_readonly", swapping)
    try:
        text, _truncated, size, refusal = api._read_text_capped_checked(link, real, 4096)
    finally:
        monkeypatch.undo()
    assert text == "" and size == 0
    assert refusal and "swapped between check and use" in refusal
    assert RESIDUAL_MARKER not in text
    # and the same reader still serves a genuine in-root file
    good, _t, good_size, no_refusal = api._read_text_capped_checked(
        insider, insider.resolve(), 4096
    )
    assert no_refusal is None and good == "# INSIDER-legit\n" and good_size > 0


def test_refresh_backlog_edge_cases_are_explicit_and_never_a_500(tmp_path):
    """Broken symlink and directory-where-file-expected: explicit, never a 500.

    Both used to be *silently skipped* by the ``path.is_file()`` filter, which
    reads as "no backlog file here" in the payload.  They are now disclosed with
    a reason, and the route is still 200 (never a 500).
    """
    root = tmp_path / "dockets"
    docket = root / "_smoke"
    docket.mkdir(parents=True)
    (docket / "UPDATE_BACKLOG.md").symlink_to("material/nope.md")  # broken
    (docket / "WORK_SUGGESTIONS.md").symlink_to(docket, target_is_directory=True)
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        response = test_client.get("/api/refresh")
    assert response.status_code == 200, response.text
    by_name = {Path(entry["path"]).name: entry for entry in response.json()["files"]}
    for name in ("UPDATE_BACKLOG.md", "WORK_SUGGESTIONS.md"):
        entry = by_name[name]
        assert entry["present"] is False
        assert entry["error"], "explicit reason, never a silent empty read"
        assert "not a regular file" in entry["error"]


def test_refresh_backlog_legit_and_in_root_symlink_still_served(tmp_path):
    """The fix does not over-block: real files and *in-root* symlinks are served."""
    root = tmp_path / "dockets"
    docket = root / "ok-docket"
    docket.mkdir(parents=True)
    target = docket / "real-backlog.md"
    target.write_text("# In-root alias target\n", encoding="utf-8")
    # an in-root symlink alias is allowed: realpath containment is the boundary,
    # not a symlink ban
    (docket / "UPDATE_BACKLOG.md").symlink_to(target)
    (docket / "WORK_SUGGESTIONS.md").write_text("# Direct file\n", encoding="utf-8")
    with TestClient(make_app(dockets_dir=str(root))) as test_client:
        body = test_client.get("/api/refresh").json()
    by_name = {Path(entry["path"]).name: entry for entry in body["files"]}
    assert by_name["UPDATE_BACKLOG.md"]["present"] is True
    assert by_name["UPDATE_BACKLOG.md"]["headings"][0]["text"] == "In-root alias target"
    assert "error" not in by_name["UPDATE_BACKLOG.md"]
    assert by_name["WORK_SUGGESTIONS.md"]["present"] is True
    assert by_name["WORK_SUGGESTIONS.md"]["headings"][0]["text"] == "Direct file"


def test_refresh_backlog_explicit_backlog_dirs_are_contained(tmp_path):
    """The replacement for ``cwd`` is explicit and contained exactly like the root.

    ``backlog_dirs`` is a ``DataLayer``-level opt-in: no ``cwd`` magic, and the
    HTTP layer exposes no knob for it, so ``GET /api/refresh`` only ever reads
    ``dockets_dir``.  Exercised at the layer level here.
    """
    root = tmp_path / "dockets"
    root.mkdir()
    extra = tmp_path / "extra"
    extra.mkdir()
    (extra / "UPDATE_BACKLOG.md").write_text("# Explicit root file\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leaked.md").write_text(f"# {RESIDUAL_MARKER}\n", encoding="utf-8")
    (extra / "WORK_SUGGESTIONS.md").symlink_to(outside / "leaked.md")
    body = api.DataLayer(
        str(STORE), str(JOURNALS), str(root), str(GRAPH), backlog_dirs=(str(extra),)
    ).refresh_backlog()
    assert RESIDUAL_MARKER not in json.dumps(body)
    by_name = {Path(entry["path"]).name: entry for entry in body["files"]}
    assert by_name["UPDATE_BACKLOG.md"]["present"] is True
    assert by_name["UPDATE_BACKLOG.md"]["headings"][0]["text"] == "Explicit root file"
    assert by_name["WORK_SUGGESTIONS.md"]["present"] is False
    assert "resolves outside the docket root" in by_name["WORK_SUGGESTIONS.md"]["error"]


# --------------------------------------------------------------------------- #
# 12. the doctor force flag must reach the doctor (U6.11)
# --------------------------------------------------------------------------- #

_DOWN_REPORT = {
    "ok": False,
    "exit_code": 2,
    "checked_at": "1970-01-01T00:00:00Z",
    "legs": [{"leg": "Occamy", "class": "core", "ok": False, "detail": "refused"}],
    "core_down": ["Occamy"],
    "optional_down": [],
}


def _memory_aware_probe(key, attempts):
    """A probe written to the documented protocol (the shape of ``probe_occamy``).

    It consults ``reuse_down(key, force=force)`` first and only pays a network
    attempt (here: bump ``attempts``) on a miss, remembering the DOWN verdict
    with ``finish``.  Without a probe that implements the memory protocol a
    forwarding test could not tell a forwarded flag from an ignored one.
    """

    def probe(*, force: bool = False):
        cached = doctor_mod.reuse_down(key, force=force)
        if cached is not None:
            return cached
        attempts["n"] += 1
        return doctor_mod.finish(
            key,
            doctor_mod.leg("Occamy", doctor_mod.CORE, False, f"refused #{attempts['n']}"),
        )

    return probe


def test_doctor_status_forwards_force_to_run_doctor(monkeypatch):
    """RED→GREEN guard (a): ``force`` is forwarded to ``run_doctor``, and only then.

    Red (guard reverted — ``api.py`` calls ``doctor_mod.run_doctor()``):

        assert [{}] == [{'force': True}]
        E   AssertionError: assert {} == {'force': True}

    Green: ``recorded == [{'force': True}]``, and the second (non-forced) layer
    records ``{'force': False}`` so the fix cannot over-apply into always-forcing.
    """
    recorded = []

    def fake(*args, **kwargs):
        recorded.append(kwargs)
        return dict(_DOWN_REPORT)

    monkeypatch.setattr(doctor_mod, "run_doctor", fake)

    forced = api.DataLayer(str(STORE), str(JOURNALS), str(DOCKETS), str(GRAPH))
    forced.doctor_status(force=True)
    assert recorded == [{"force": True}]

    # The other direction: an ordinary call must NOT force.
    plain = api.DataLayer(str(STORE), str(JOURNALS), str(DOCKETS), str(GRAPH))
    plain.doctor_status(force=False)
    assert recorded[-1] == {"force": False}


def test_forced_doctor_status_actually_probes_while_non_forced_caches(monkeypatch):
    """RED→GREEN guard (b): the forwarded flag must change what really happens.

    An argument-forwarding assertion alone would not catch a doctor that ignores
    the argument, so this drives the real ``run_doctor`` with a memory-aware
    probe and counts genuine attempts.

    Red (guard reverted): the forced call is served from the doctor's negative
    memory, so no attempt is made:

        assert 1 == 2
        E   AssertionError

    Green: non-forced calls inside the dashboard TTL are served by the dashboard
    cache (attempts stay 1), while the forced call probes afresh (attempts 2).

    With the call site reverted to *always* forcing (``force=force`` ->
    ``force=True``) the non-forced assertion is the one that fails, ``assert
    2 == 1``; with ``force`` dropped entirely the forced assertion fails, ``assert
    1 == 2``.  The two guards pin the flag from both sides.
    """
    key = "u6-11-test-occamy"
    doctor_mod._NEGATIVE_CACHE.pop(key, None)
    attempts = {"n": 0}
    probe = _memory_aware_probe(key, attempts)
    real = doctor_mod.run_doctor

    def with_probe(*args, **kwargs):
        kwargs["probes"] = [("Occamy", probe)]
        return real(*args, **kwargs)

    monkeypatch.setattr(doctor_mod, "run_doctor", with_probe)
    layer = api.DataLayer(str(STORE), str(JOURNALS), str(DOCKETS), str(GRAPH))
    try:
        layer.doctor_status(force=False)
        assert attempts["n"] == 1, "first call must probe (cold memory)"
        layer.doctor_status(force=False)
        assert attempts["n"] == 1, "a call inside the dashboard TTL must not probe"
        # With the dashboard's own TTL cache disabled, a NON-forced call must be
        # served by the doctor's negative memory: still no new attempt.  This is
        # the leg that fails if the call site is made to *always* force.
        layer.doctor_ttl = 0.0
        layer.doctor_status(force=False)
        assert attempts["n"] == 1, "a non-forced call must reuse the doctor's memory"
        layer.doctor_status(force=True)
        assert attempts["n"] == 2, "an explicit force must actually probe afresh"
    finally:
        doctor_mod._NEGATIVE_CACHE.pop(key, None)


def test_doctor_read_route_does_not_force(client, monkeypatch):
    """The deliberate omission is preserved: a page load must not force a probe.

    ``GET /api/doctor`` is a read route; ``app.py`` omits ``force`` on purpose.
    If a future "fix" made every read force, each page load would pay a full
    probe — this pins that down.
    """
    recorded = []

    def fake(*args, **kwargs):
        recorded.append(kwargs)
        return dict(_DOWN_REPORT)

    monkeypatch.setattr(doctor_mod, "run_doctor", fake)
    response = client.get("/api/doctor")
    assert response.status_code == 200, response.text
    assert recorded, "the read route must still consult the doctor"
    assert all(kwargs.get("force") is not True for kwargs in recorded)
# --------------------------------------------------------------------------- #
# U6.16 -- store resolution is ONE boundary, and the resolved path is observable
# --------------------------------------------------------------------------- #
def test_env_var_redirects_the_app_layer_path(tmp_path, monkeypatch):
    """Guard (U6.16): RESEXTRACT_STATE_DB must redirect a DataLayer.

    Before U6.16 ``DataLayer.__init__`` ignored the env var and fell back to the
    literal ``state/state.sqlite`` (the *real* store) while ``default_layer()``
    honoured it, so a ``create_app()`` server read the real store during a run
    that believed it was isolated.  Red->green: reverting ``resolve_store`` to
    ``Path(store_path) if store_path is not None else Path("state/state.sqlite")``
    makes this fail (layer.store_path is the real store, not the copy); restoring
    makes it pass.
    """
    copy = tmp_path / "copy.sqlite"
    copy.write_bytes(STORE.read_bytes())
    monkeypatch.setenv("RESEXTRACT_STATE_DB", str(copy))
    layer = api.DataLayer()
    assert layer.store_path == copy, "env var must redirect a DataLayer-constructed path"
    assert layer.store_path != Path("state/state.sqlite")
    assert layer.store_source == "env"


def test_precedence_explicit_store_beats_env(tmp_path, monkeypatch):
    env_copy = tmp_path / "env.sqlite"
    env_copy.write_bytes(STORE.read_bytes())
    explicit = tmp_path / "explicit.sqlite"
    explicit.write_bytes(STORE.read_bytes())
    monkeypatch.setenv("RESEXTRACT_STATE_DB", str(env_copy))
    layer = api.DataLayer(str(explicit))
    assert layer.store_path == explicit and layer.store_source == "explicit"
    app = app_mod.create_app(store_path=str(explicit), host="127.0.0.1")
    assert app.state.dashboard["store_path"] == str(explicit)
    assert app.state.dashboard["store_source"] == "explicit"


def test_precedence_env_beats_default(tmp_path, monkeypatch):
    env_copy = tmp_path / "env.sqlite"
    env_copy.write_bytes(STORE.read_bytes())
    monkeypatch.setenv("RESEXTRACT_STATE_DB", str(env_copy))
    path, source = api.resolve_store()
    assert path == env_copy and source == "env"


def test_no_env_var_keeps_the_cwd_default(monkeypatch):
    monkeypatch.delenv("RESEXTRACT_STATE_DB", raising=False)
    path, source = api.resolve_store()
    assert path == Path("state/state.sqlite") and source == "default"
    assert api.resolve_store_path() == Path("state/state.sqlite")


def test_default_layer_is_observable_and_follows_the_env(tmp_path, monkeypatch):
    copy = tmp_path / "copy.sqlite"
    copy.write_bytes(STORE.read_bytes())
    monkeypatch.setenv("RESEXTRACT_STATE_DB", str(copy))
    monkeypatch.setattr(api, "_DEFAULT_LAYER", None)
    monkeypatch.setattr(api, "_DEFAULT_LAYER_KEY", None)
    layer = api.default_layer()
    assert layer.store_path == copy and layer.store_source == "env"
    assert layer.resolution()["store_path"] == str(copy)


# --------------------------------------------------------------------------- #
# 7. U6.20 -- docket metadata: the ARTIFACT is the source of truth, the store
#    row (``dockets.manifest_json``) is an insert-time snapshot and only ever a
#    fallback.  Read-path only: the store is never written by this unit.
# --------------------------------------------------------------------------- #


def _u620_manifest_payload(lane_title: str, evidence: list[list[str]]) -> tuple[str, int]:
    """A valid ``resextract/docket/1`` manifest derived from the fixture docket.

    The module reads ``dockets/ok-docket`` (so every required key stays exactly
    as the model wrote it) and then mutates it: the fixture lane carries **no**
    title and one evidence entry per claim, which is precisely the pre-re-render
    shape the real ``duval-replay-material`` row still holds.  Returns the
    JSON text plus the evidence total it encodes.
    """
    import json

    data = json.loads((DOCKETS / "ok-docket" / "MANIFEST.json").read_text())
    data["lane"]["title"] = lane_title
    total = 0
    for index, claim in enumerate(data["claims"]):
        items = evidence[index] if index < len(evidence) else []
        claim["evidence"] = items
        claim["provenance"] = [f"file:{item.split('#')[0]}" for item in items]
        total += len(items)
    return json.dumps(data), total


def _u620_stale_snapshot(title, evidence_count) -> dict:
    """A pre-re-render store snapshot: no title, evidence dropped, no producer."""
    return {
        "schema": "resextract/docket/1",
        "status": "draft",
        "lane": {"slug": "stale-lane", "type": "report", "title": title},
        "claims": [{"id": "C0", "evidence": ["stale"] * int(evidence_count)}],
        "generated_by": {"app": "resextract", "version": "0.1.0", "model": ""},
        "freshness": {"state": "stale", "verified_at": "2020-01-01T00:00:00.000Z"},
    }


def _u620_tree(tmp_path, *, store_rows):
    """A dockets root (fresh / manifest-less / corrupt) + a copied store.

    ``store_rows`` maps a store ``dir`` value to the stale snapshot to record
    against it.  The session fixture's store is *copied*, never written.
    """
    import json
    import shutil
    import sqlite3

    root = tmp_path / "dockets"
    fresh = root / "fresh-docket"
    fresh.mkdir(parents=True)
    payload, evidence_total = _u620_manifest_payload(
        "Fresh artifact title",
        [["material/note.txt#L1-L2", "material/note.txt#L2-L3"], ["material/extra.txt"]],
    )
    (fresh / "MANIFEST.json").write_text(payload)
    (fresh / "README.md").write_text("# Fresh docket\n\n## Verdict\n\nok\n")

    # a docket directory that exists while its MANIFEST.json is ABSENT entirely
    (root / "store-only-docket").mkdir()
    (root / "store-only-docket" / "README.md").write_text("# Store only\n")

    corrupt = root / "corrupt-docket"
    corrupt.mkdir()
    (corrupt / "MANIFEST.json").write_text("{ not json at all ")

    store = tmp_path / "state.sqlite"
    shutil.copyfile(STORE, store)
    con = sqlite3.connect(store)
    try:
        for index, (directory, snapshot) in enumerate(store_rows.items(), start=101):
            con.execute(
                "INSERT INTO dockets(id,lane_id,dir,manifest_json,source_head,graph_hash,"
                "freshness,verified_at,last_refresh_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (index, None, directory, json.dumps(snapshot), "", "", "stale",
                 "2020-01-01T00:00:00.000Z", None),
            )
        con.commit()
    finally:
        con.close()
    return root, store, evidence_total


def test_u620_board_prefers_the_manifest_over_a_stale_store_row(tmp_path):
    """U6.20 regression: stale store row + fresh artifact => the API serves the artifact.

    The store row for ``fresh-docket`` is the damaged pre-re-render shape
    (``lane.title`` null, zero evidence, no ``producer``); the artifact on disk
    is repaired.  Before this unit the board published ``lane`` = the slug and
    no title/evidence at all, so the slug stood in for the title.

    Red->green guard -- revert the three artifact lines added to
    ``DataLayer.dockets`` (``lane_title`` / ``evidence`` / ``source``), run this
    test, restore, rerun.  Transcript pasted below:

    RED->GREEN (the three artifact-branch lines removed from
    ``DataLayer.dockets``; FULL ``__pycache__`` purge around both runs):

        E       AssertionError: assert None == 'manifest'

    Restored: ``api.py`` sha256 bit-identical before and after the revert
    (``d5df9b08...`` -> fixed -> ``d5df9b08...`` -> fixed); the test passes
    again.  Both runs recorded in ``state/logs/U6.20-red.txt`` / ``-green.txt``.
    """
    root, store, evidence_total = _u620_tree(
        tmp_path, store_rows={"dockets/fresh-docket": _u620_stale_snapshot(None, 0)}
    )
    with TestClient(make_app(dockets_dir=str(root), store_path=str(store))) as client_:
        body = client_.get("/api/dockets").json()
    entry = {d["slug"]: d for d in body["dockets"]}["fresh-docket"]
    assert entry["source"] == "manifest"
    assert entry["lane_title"] == "Fresh artifact title"
    assert entry["title"] == "Fresh artifact title"  # the slug no longer stands in
    assert entry["title"] != entry["lane"]
    assert entry["lane"] == "fixture-lane"  # the manifest's lane.slug, unchanged
    assert evidence_total == 3
    assert entry["evidence"] == 3  # the stale row said 0
    assert entry["generated_by"]["model"] == "fixture-claims-u6.1"  # artifact, not row
    assert entry["status"] == "ready"


def test_u620_board_falls_back_to_the_store_row_when_the_artifact_is_gone(tmp_path):
    """Missing/unreadable MANIFEST.json => the store row serves, and ``source`` says so."""
    root, store, _ = _u620_tree(
        tmp_path,
        store_rows={
            "dockets/store-only-docket": _u620_stale_snapshot("Store snapshot title", 2),
            "dockets/corrupt-docket": _u620_stale_snapshot("Snapshot title (corrupt)", 4),
        },
    )
    with TestClient(make_app(dockets_dir=str(root), store_path=str(store))) as client_:
        body = client_.get("/api/dockets").json()
    by_slug = {d["slug"]: d for d in body["dockets"]}

    only = by_slug["store-only-docket"]
    assert only["source"] == "store"
    assert only["lane_title"] == "Store snapshot title"
    assert only["title"] == "Store snapshot title"
    assert only["evidence"] == 2
    assert "absent" in only["error"]
    assert only["verify"]["ok"] is None  # never claims a verification it did not run
    assert any(f["path"] == "README.md" for f in only["files"])

    corrupt = by_slug["corrupt-docket"]
    assert corrupt["status"] == "unreadable"  # the artifact's state is not laundered
    assert "unreadable" in corrupt["error"]
    assert corrupt["source"] == "store"
    assert corrupt["lane_title"] == "Snapshot title (corrupt)"
    assert corrupt["evidence"] == 4


def test_u620_board_never_resurrects_a_docket_outside_the_root(tmp_path):
    """A store row cannot name a path outside the dockets root, nor a gone docket."""
    root, store, _ = _u620_tree(
        tmp_path,
        store_rows={
            "dockets/ghost-docket": _u620_stale_snapshot("Gone", 1),
            "dockets/../escape-docket": _u620_stale_snapshot("Escape", 1),
            "../../etc/passwd": _u620_stale_snapshot("Escape2", 1),
        },
    )
    (tmp_path / "escape-docket").mkdir()  # exists, but OUTSIDE the dockets root
    with TestClient(make_app(dockets_dir=str(root), store_path=str(store))) as client_:
        body = client_.get("/api/dockets").json()
    slugs = {d["slug"] for d in body["dockets"]}
    assert "ghost-docket" not in slugs
    assert not any("escape" in slug or ".." in slug for slug in slugs)
    assert "fresh-docket" in slugs  # the artifact-backed docket is unaffected


def test_u620_smoke_manifest_without_newer_keys_still_works(tmp_path):
    """``dockets/_smoke`` validates but has no ``lane.title``/``producer``: no raise.

    Also proves the board is unaffected by an absent store: ``store_path`` here
    points at a file that does not exist.
    """
    import shutil

    repo = Path(__file__).resolve().parents[1]
    root = tmp_path / "dockets"
    root.mkdir()
    shutil.copytree(repo / "dockets" / "_smoke", root / "_smoke")
    missing_store = tmp_path / "absent.sqlite"
    with TestClient(
        make_app(dockets_dir=str(root), store_path=str(missing_store))
    ) as client_:
        body = client_.get("/api/dockets").json()
        detail = client_.get("/api/dockets/_smoke")
    entry = {d["slug"]: d for d in body["dockets"]}["_smoke"]
    assert entry["source"] == "manifest"
    assert entry["lane_title"] is None  # the key is absent in a pre-U5.14 manifest
    # the artifact is authoritative: lane.slug is NOT the directory name here
    assert entry["lane"] == "duval-trace-integrity"
    assert entry["title"] == "duval-trace-integrity"  # degrades to lane.slug, no raise
    assert entry["evidence"] == 3
    assert entry["status"] == "draft"
    assert detail.status_code == 200
    assert detail.json()["source"] == "manifest"
    assert detail.json()["manifest"]["lane"]["slug"] == "duval-trace-integrity"
