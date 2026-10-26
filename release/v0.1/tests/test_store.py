"""Offline tests for :mod:`resextract.store` (fixtures are local; no conftest).

Covers: idempotent init, WAL, every enumerated CHECK vocabulary, upsert
round-trips (target/run/lane/docket), ``status_json()`` shape, and row
preservation across a second ``init_db``.
"""

from __future__ import annotations

import sqlite3

import pytest

from resextract import store


@pytest.fixture()
def db_path(tmp_path):
    path = tmp_path / "state" / "state.sqlite"
    store.init_db(path)
    return path


@pytest.fixture()
def con(db_path):
    connection = store.connect(db_path)
    yield connection
    connection.close()


def test_init_db_twice_is_idempotent(db_path):
    store.init_db(db_path)
    store.init_db(db_path)
    con = store.connect(db_path)
    try:
        assert store.schema_version(con) == store.SCHEMA_VERSION
        rows = con.execute("SELECT version FROM schema_version ORDER BY version").fetchall()
        assert [r["version"] for r in rows] == [v for v, _ in store.MIGRATIONS]
        names = {
            r["name"]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        assert set(store.TABLES) <= names
    finally:
        con.close()


def test_wal_mode_is_enabled(db_path):
    probe = sqlite3.connect(str(db_path))
    try:
        assert probe.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    finally:
        probe.close()


def test_foreign_keys_enabled_on_connect(con):
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        con.execute(
            "INSERT INTO evidence(claim_id, source_kind) VALUES (99999, 'web')"
        )


# --------------------------------------------------------------------------- #
# Vocabulary CHECK constraints
# --------------------------------------------------------------------------- #

_BAD_VERDICT = (
    "INSERT INTO verdicts(claim_id, verdict, rationale, evidence_ids_json, checked_at) "
    "VALUES (NULL, ?, NULL, NULL, NULL)"
)
_BAD_LANE_TYPE = (
    'INSERT INTO lanes(target, slug, title, thesis, audience, "type", parent_lane_id, maturity, status) '
    "VALUES ('t', ?, 'title', 'thesis', 'aud', ?, NULL, NULL, 'draft')"
)
_BAD_LANE_STATUS = (
    'INSERT INTO lanes(target, slug, title, thesis, audience, "type", parent_lane_id, maturity, status) '
    "VALUES ('t', ?, 'title', 'thesis', 'aud', 'report', NULL, NULL, ?)"
)
_BAD_SOURCE_KIND = (
    "INSERT INTO evidence(claim_id, source_kind, source_ref, sha256, quote, context, retrieved_at, copy_path) "
    "VALUES (NULL, ?, 'ref', NULL, NULL, NULL, NULL, NULL)"
)


@pytest.mark.parametrize("bad", ["MAYBE", "confirms", "SUPPORTED", ""])
def test_verdict_check_rejects_bad_value(con, bad):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: verdict"):
        con.execute(_BAD_VERDICT, (bad,))
    con.rollback()


@pytest.mark.parametrize("good", store.VERDICT_VOCAB)
def test_verdict_check_accepts_vocabulary(con, good):
    con.execute(_BAD_VERDICT, (good,))
    con.rollback()


@pytest.mark.parametrize("bad", ["essay", "PAPER", "paper ", "poster"])
def test_lane_type_check_rejects_bad_value(con, bad):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: type"):
        con.execute(_BAD_LANE_TYPE, (f"slug-{bad!r}", bad))
    con.rollback()


@pytest.mark.parametrize("good", store.LANE_TYPES)
def test_lane_type_check_accepts_vocabulary(con, good):
    con.execute(_BAD_LANE_TYPE, (f"slug-{good}", good))
    con.rollback()


@pytest.mark.parametrize("bad", ["wip", "READY", "done", "stale "])
def test_lane_status_check_rejects_bad_value(con, bad):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: status"):
        con.execute(_BAD_LANE_STATUS, (f"slug-{bad!r}", bad))
    con.rollback()


@pytest.mark.parametrize("good", store.LANE_STATUSES)
def test_lane_status_check_accepts_vocabulary(con, good):
    con.execute(_BAD_LANE_STATUS, (f"slug-{good}", good))
    con.rollback()


@pytest.mark.parametrize("bad", ["ftp", "LOCAL", "web ", "file"])
def test_evidence_source_kind_check_rejects_bad_value(con, bad):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: source_kind"):
        con.execute(_BAD_SOURCE_KIND, (bad,))
    con.rollback()


@pytest.mark.parametrize("good", store.EVIDENCE_SOURCE_KINDS)
def test_evidence_source_kind_check_accepts_vocabulary(con, good):
    con.execute(_BAD_SOURCE_KIND, (good,))
    con.rollback()


# --------------------------------------------------------------------------- #
# Round-trips
# --------------------------------------------------------------------------- #


def test_target_upsert_round_trip(con):
    store.upsert_target(
        con,
        slug="duval",
        path="<workspace>",
        head_sha="abc123",
        exclude_json=[".git/", "node_modules/"],
    )
    target = store.get_target(con, "duval")
    assert target["slug"] == "duval"
    assert target["path"] == "<workspace>"
    assert target["head_sha"] == "abc123"
    assert target["exclude_json"] == [".git/", "node_modules/"]  # JSON decoded on read
    assert target["last_seen_at"].endswith("Z")

    store.upsert_target(con, slug="duval", path="/moved/Duval", head_sha="def456")
    second = store.get_target(con, "duval")
    assert second["path"] == "/moved/Duval"
    assert second["head_sha"] == "def456"
    assert store.count(con, "targets") == 1


def test_run_insert_and_upsert_round_trip(con):
    run_id = store.insert_run(con, target="duval", budget={"tokens": 1000})
    run = store.get_run(con, run_id)
    assert run["target"] == "duval"
    assert run["status"] == "running"
    assert run["tokens_used"] == 0
    assert run["finished_at"] is None

    assert store.upsert_run(con, id=run_id, status="done", tokens_used=42) == run_id
    updated = store.get_run(con, run_id)
    assert updated["status"] == "done"
    assert updated["tokens_used"] == 42
    assert updated["target"] == "duval"  # untouched fields survive the upsert

    assert store.finish_run(con, run_id, status="done", tokens_used=43) is True
    assert store.last_run(con)["tokens_used"] == 43
    assert store.count(con, "runs") == 1


def test_lane_upsert_and_set_lane_status(con):
    lane_id = store.upsert_lane(
        con,
        target="duval",
        slug="consonance",
        title="Consonance metric",
        thesis="A novel interval metric",
        audience="researchers",
        type="paper",
        maturity="draft",
    )
    lane = store.get_lane(con, lane_id)
    assert lane["type"] == "paper"
    assert lane["status"] == "draft"

    assert store.set_lane_status(con, lane_id, "ready") is True
    assert store.get_lane(con, lane_id)["status"] == "ready"
    with pytest.raises(ValueError, match="lane status must be one of"):
        store.set_lane_status(con, lane_id, "wip")

    store.upsert_lane(con, id=lane_id, target="duval", slug="consonance", title="Consonance v2", status="stale")
    updated = store.get_lane(con, lane_id)
    assert updated["title"] == "Consonance v2"
    assert updated["status"] == "stale"
    assert store.get_lane_by_slug(con, "duval", "consonance")["id"] == lane_id
    with pytest.raises(ValueError, match="lane type must be one of"):
        store.upsert_lane(con, target="duval", slug="bad", type="essay")


def test_docket_upsert_round_trip(con):
    lane_id = store.upsert_lane(con, target="duval", slug="lane-a", type="report")
    docket_id = store.upsert_docket(
        con,
        lane_id=lane_id,
        dir="dockets/duval/lane-a",
        manifest_json={"schema": "resextract/docket/1"},
        source_head="abc123",
        freshness="current",
    )
    docket = store.get_docket(con, docket_id)
    assert docket["dir"] == "dockets/duval/lane-a"
    assert docket["manifest_json"] == {"schema": "resextract/docket/1"}
    assert docket["freshness"] == "current"

    store.upsert_docket(
        con, id=docket_id, lane_id=lane_id, dir="dockets/duval/lane-a", freshness="stale",
        manifest_json={"schema": "resextract/docket/1"},
    )
    assert store.get_docket(con, docket_id)["freshness"] == "stale"
    assert store.get_docket_by_dir(con, "dockets/duval/lane-a")["id"] == docket_id
    assert store.count(con, "dockets") == 1


def test_evidence_verdict_search_health_and_rework_round_trip(con):
    run_id = store.insert_run(con, target="duval")
    candidate_id = store.insert_candidate(
        con, run_id=run_id, kind="claim", title="T", graph_nodes_json=["a", "b"],
        provenance_json=[{"ref": "fixture"}],
    )
    claim_id = store.insert_claim(
        con, candidate_id=candidate_id, kind="novelty", text="X beats Y",
        provenance_json=[{"ref": "fixture"}],
    )
    evidence_id = store.insert_evidence(
        con, claim_id=claim_id, source_kind="web", source_ref="https://example.org",
        sha256="ab" * 32, retrieved_at="2026-10-08T10:00:00.000Z",
    )
    verdict_id = store.insert_verdict(
        con, claim_id=claim_id, verdict="CONFIRMS", evidence_ids_json=[evidence_id],
        checked_at="2026-10-08T10:00:01.000Z",
    )
    health_id = store.insert_search_health(con, engine="duckduckgo", query="q", result_count=3, ok=True)
    con.execute("INSERT INTO dockets(id, lane_id, dir, freshness) VALUES (1, NULL, 'd/1', 'current')")
    rework_id = store.open_rework(con, docket_id=1, reason="source moved", required_work="re-measure")
    con.commit()

    assert store.get_candidate(con, candidate_id)["graph_nodes_json"] == ["a", "b"]
    assert store.get_claim(con, claim_id)["text"] == "X beats Y"
    assert store.get_evidence(con, evidence_id)["source_kind"] == "web"
    assert store.get_verdict(con, verdict_id)["evidence_ids_json"] == [evidence_id]
    assert store.get_search_health(con, health_id)["ok"] == 1
    assert store.close_rework(con, rework_id) is True
    assert store.get_rework(con, rework_id)["closed_at"] is not None
    assert store.close_rework(con, rework_id) is False  # already closed

    with pytest.raises(ValueError, match="verdict must be one of"):
        store.insert_verdict(con, verdict="MAYBE")
    with pytest.raises(ValueError, match="source_kind must be one of"):
        store.insert_evidence(con, source_kind="ftp")


def test_status_json_shape(con):
    run_id = store.insert_run(con, target="duval")
    claim_lane = store.upsert_lane(con, target="duval", slug="lane-a", type="paper", status="ready")
    store.upsert_lane(con, target="duval", slug="lane-b", type="memo", status="draft")
    store.upsert_docket(con, lane_id=claim_lane, dir="dockets/duval/lane-a", freshness="current",
                        manifest_json={"schema": "resextract/docket/1"})
    store.upsert_docket(con, lane_id=claim_lane, dir="dockets/duval/lane-b", freshness="stale",
                        manifest_json={"schema": "resextract/docket/1"})

    summary = store.status_json(con)
    assert set(summary) >= {
        "db_path",
        "schema_version",
        "generated_at",
        "tables",
        "lanes",
        "dockets",
        "last_run",
    }
    assert set(summary["tables"]) == set(store.TABLES)
    assert summary["tables"]["runs"] == 1
    assert summary["tables"]["lanes"] == 2
    assert summary["tables"]["dockets"] == 2
    assert summary["lanes"]["total"] == 2
    assert summary["lanes"]["by_status"] == {"draft": 1, "ready": 1}
    assert summary["lanes"]["by_type"] == {"memo": 1, "paper": 1}
    assert summary["dockets"]["by_freshness"] == {"current": 1, "stale": 1}
    assert summary["last_run"]["id"] == run_id
    assert summary["schema_version"] == store.SCHEMA_VERSION
    assert "db:" in store.status_text(con)


def test_reinit_preserves_populated_rows(db_path):
    con = store.connect(db_path)
    store.upsert_target(con, slug="duval", path="<workspace>")
    run_id = store.insert_run(con, target="duval")
    store.upsert_lane(con, target="duval", slug="lane-a", type="report", status="ready")
    con.close()

    store.init_db(db_path)  # second init over populated DB

    con = store.connect(db_path)
    try:
        assert store.count(con, "targets") == 1
        assert store.count(con, "lanes") == 1
        assert store.get_run(con, run_id)["target"] == "duval"
        rows = con.execute("SELECT COUNT(*) AS n FROM schema_version").fetchone()
        assert rows["n"] == len(store.MIGRATIONS)
    finally:
        con.close()
