"""Dashboard tests (U6.1) — offline, ``fastapi.testclient.TestClient``.

Coverage: every read route's documented shape, explicit error payloads (never a
500) for a missing/empty store, the three docket cases (valid / corrupt
MANIFEST / none at all), ordered journal events with no invented reasoning
text, a live SSE stream, directory-traversal 404s, loopback-bind enforcement
and the control-route token gate.

Red→green guards
----------------
``test_safe_slug_guard_blocks_traversal`` (with
``test_dockets_traversal_is_404[.../../ok-docket]``) and
``test_non_loopback_host_is_refused`` are both written so the suite goes red the
moment the guard is reverted.  The exact failures observed with each guard
reverted are pasted in those tests' docstrings.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from resextract import doctor as doctor_mod
from resextract.dashboard import api
from resextract.dashboard import app as app_mod

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "dashboard-store"
STORE = FIXTURES / "state.sqlite"
JOURNALS = FIXTURES / "journal"
DOCKETS = FIXTURES / "dockets"
EMPTY_DOCKETS = FIXTURES / "dockets-empty"
GRAPH = FIXTURES / "graph-mini.json"

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
    def fake_doctor():
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

    def boom():
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
    with pytest.raises(ValueError):
        app_mod.create_app(host="0.0.0.0")
    with pytest.raises(ValueError):
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
