"""Schema-v2 tests for :mod:`resextract.store` (U0.10).

Unit under test: the additive, row-preserving migration from schema v1 to v2.
v1 is the DDL shipped in ``store._MIGRATION_1``; the tests build a *v1-shaped*
database by executing exactly that DDL, fill **every** table, then call
``store.init_db`` and prove nothing was lost, retyped or dropped.

The two guards below carry a red->green note.  The pasted failures are the real
output of running that single test against a deliberately reverted store.

Run: ``.venv/bin/python -m pytest tests/test_store_v2.py -q``
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from resextract import store

V1_TABLES = tuple(t for t in store.TABLES if t != "lane_candidates")

# The exact v1 column list per table.  Preservation is compared on this
# projection, because migration 2 *adds* columns to `rework` (additively, as
# required) -- a full-row compare would report the new columns as a "loss".
V1_COLUMNS: dict[str, tuple[str, ...]] = {
    "runs": ("id", "target", "started_at", "finished_at", "status", "budget", "tokens_used", "notes"),
    "targets": ("slug", "path", "head_sha", "graph_path", "graph_hash", "last_seen_at", "exclude_json"),
    "candidates": ("id", "run_id", "kind", "title", "summary", "provenance_json", "graph_nodes_json", "score", "state"),
    "claims": ("id", "candidate_id", "kind", "text", "provenance_json", "verification_state", "confidence"),
    "evidence": ("id", "claim_id", "source_kind", "source_ref", "sha256", "quote", "context", "retrieved_at", "copy_path"),
    "verdicts": ("id", "claim_id", "verdict", "rationale", "evidence_ids_json", "checked_at"),
    "lanes": ("id", "target", "slug", "title", "thesis", "audience", "type", "parent_lane_id", "maturity", "status"),
    "dockets": ("id", "lane_id", "dir", "manifest_json", "source_head", "graph_hash", "freshness", "verified_at", "last_refresh_at"),
    "web_sources": ("url", "sha256", "title", "page_date", "fetched_at", "http_status", "extracted_text_path", "failure_reason"),
    "search_health": ("id", "ts", "engine", "query", "result_count", "ok", "error"),
    "rework": ("id", "docket_id", "reason", "required_work", "opened_at", "closed_at"),
}


# --------------------------------------------------------------------------- #
# v1-shaped database built from the shipped v1 DDL
# --------------------------------------------------------------------------- #


def _build_v1(path: Path, *, duplicate_docket_dir: bool = False) -> sqlite3.Connection:
    """Create a v1 database by executing the real v1 DDL, then fill every table."""
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    for statement in store._MIGRATION_1:  # verbatim v1 DDL
        con.execute(statement)
    if duplicate_docket_dir:
        # A DB created before defect 3's index existed: force the old shape so
        # the migration's duplicate detection/resolution path is exercised.
        con.execute("DROP INDEX IF EXISTS uq_dockets_dir")
    con.execute(
        "INSERT INTO schema_version(version, applied_at) VALUES (1, '2026-01-01T00:00:00.000Z')"
    )
    # every table, with NULLs and non-ASCII to make loss obvious
    con.execute(
        "INSERT INTO runs(id,target,started_at,finished_at,status,budget,tokens_used,notes) "
        "VALUES (1,'duval','2026-01-01T00:00:00.000Z',NULL,'done','{\"usd\": 1}',42,'naïve — ünïcode')"
    )
    con.execute(
        "INSERT INTO targets(slug,path,head_sha,graph_path,graph_hash,last_seen_at,exclude_json) "
        "VALUES ('duval','/home/zer0null/Duval','abc123','state/kg/duval/graph.json','deadbeef',"
        "'2026-01-01T00:00:00.000Z','[\"docs/**\"]')"
    )
    con.execute(
        "INSERT INTO candidates(id,run_id,kind,title,summary,provenance_json,graph_nodes_json,score,state) "
        "VALUES (1,1,'novel_primitive','T1','S1','[\"a\"]','[\"n1\"]',0.5,'mined')"
    )
    con.execute(
        "INSERT INTO candidates(id,run_id,kind,title,summary,provenance_json,graph_nodes_json,score,state) "
        "VALUES (2,1,'claim','T2',NULL,NULL,'[\"n2\"]',NULL,'mined')"
    )
    con.execute(
        "INSERT INTO claims(id,candidate_id,kind,\"text\",provenance_json,verification_state,confidence) "
        "VALUES (1,1,'measured','X beats Y','[\"p\"]','verified',0.9)"
    )
    con.execute(
        "INSERT INTO evidence(id,claim_id,source_kind,source_ref,sha256,quote,context,retrieved_at,copy_path) "
        "VALUES (1,1,'web','https://example.org','ab','q','c','2026-01-01T00:00:00.000Z','material/x')"
    )
    con.execute(
        "INSERT INTO verdicts(id,claim_id,verdict,rationale,evidence_ids_json,checked_at) "
        "VALUES (1,1,'CONFIRMS','because','[1]','2026-01-01T00:00:00.000Z')"
    )
    con.execute(
        "INSERT INTO lanes(id,target,slug,title,thesis,audience,\"type\",parent_lane_id,maturity,status) "
        "VALUES (1,'duval','lane-a','A','thesis A','practitioners','report',NULL,'medium','ready')"
    )
    con.execute(
        "INSERT INTO lanes(id,target,slug,title,thesis,audience,\"type\",parent_lane_id,maturity,status) "
        "VALUES (2,'duval','lane-b','B','thesis B','practitioners','memo',1,NULL,'draft')"
    )
    con.execute(
        "INSERT INTO dockets(id,lane_id,dir,manifest_json,source_head,graph_hash,freshness,verified_at,last_refresh_at) "
        "VALUES (1,1,'dockets/duval/lane-a','{\"schema\": \"resextract/docket/1\"}','abc123','deadbeef',"
        "'current','2026-01-01T00:00:00.000Z','2026-01-02T00:00:00.000Z')"
    )
    second = "dockets/duval/lane-a" if duplicate_docket_dir else "dockets/duval/lane-b"
    con.execute(
        "INSERT INTO dockets(id,lane_id,dir,manifest_json,source_head,graph_hash,freshness,verified_at,last_refresh_at) "
        f"VALUES (2,2,'{second}',NULL,'def456','cafe','stale','2026-03-01T00:00:00.000Z',NULL)"
    )
    con.execute(
        "INSERT INTO web_sources(url,sha256,title,page_date,fetched_at,http_status,extracted_text_path,failure_reason) "
        "VALUES ('https://example.org','ab','Ex','2026-01-01','2026-01-02',200,'state/webcache/x.txt',NULL)"
    )
    con.execute(
        "INSERT INTO search_health(id,ts,engine,query,result_count,ok,error) "
        "VALUES (1,'2026-01-01T00:00:00.000Z','duckduckgo','q',3,1,NULL)"
    )
    con.execute(
        "INSERT INTO rework(id,docket_id,reason,required_work,opened_at,closed_at) "
        "VALUES (1,1,'source moved','re-measure','2026-01-01T00:00:00.000Z',NULL)"
    )
    con.commit()
    return con


def _snapshot(con: sqlite3.Connection) -> dict[str, list[tuple]]:
    """Raw v1-column row images, so preservation is compared literally."""
    out: dict[str, list[tuple]] = {}
    for table in V1_TABLES:
        cols = ", ".join(f'"{c}"' for c in V1_COLUMNS[table])
        out[table] = [
            tuple(r) for r in con.execute(f"SELECT {cols} FROM {table} ORDER BY rowid").fetchall()
        ]
    return out


@pytest.fixture()
def v1_path(tmp_path: Path) -> Path:
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    con = _build_v1(path)
    con.close()
    return path


@pytest.fixture()
def con(tmp_path: Path):
    path = tmp_path / "state" / "state.sqlite"
    store.init_db(path)
    connection = store.connect(path)
    yield connection
    connection.close()


# --------------------------------------------------------------------------- #
# migrations
# --------------------------------------------------------------------------- #


def test_fresh_db_is_v2_with_all_tables_columns_and_indices(tmp_path: Path):
    path = tmp_path / "state" / "state.sqlite"
    store.init_db(path)
    con = store.connect(path)
    try:
        # Relaxed version pins.  The schema advances; these pin the migration's
        # contract, not the current number.  A fresh DB must reach AT LEAST v2
        # (the level this file's data model requires) and must sit exactly at the
        # module's declared current version.  Do NOT re-tighten to `== 2`: the
        # mandated v3 bump is exactly what broke that pin.
        assert store.schema_version(con) >= 2
        assert store.SCHEMA_VERSION >= 2
        assert store.schema_version(con) == store.SCHEMA_VERSION
        tables = {
            r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert set(store.TABLES) <= tables

        rework_cols = {r["name"] for r in con.execute("PRAGMA table_info(rework)")}
        assert {"source_ref", "model_suggested"} <= rework_cols
        assert {r["name"] for r in con.execute("PRAGMA table_info(lane_candidates)")} == {
            "lane_id",
            "candidate_id",
        }
        assert {r["name"] for r in con.execute("PRAGMA table_info(dockets)")} >= {
            "id",
            "lane_id",
            "dir",
            "manifest_json",
            "source_head",
            "graph_hash",
            "freshness",
            "verified_at",
            "last_refresh_at",
        }

        indices = {
            r["name"]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert {"dockets_dir_unique", "idx_lane_candidates_candidate_id"} <= indices
        assert store.count(con, "lane_candidates") == 0
    finally:
        con.close()


def test_init_db_twice_is_a_noop(v1_path: Path):
    store.init_db(v1_path)
    con = store.connect(v1_path)
    after_first = _snapshot(con)
    versions_first = [
        tuple(r) for r in con.execute("SELECT * FROM schema_version ORDER BY version")
    ]
    con.close()

    store.init_db(v1_path)  # must be a no-op, not a re-run
    con = store.connect(v1_path)
    try:
        assert _snapshot(con) == after_first
        assert [
            tuple(r) for r in con.execute("SELECT * FROM schema_version ORDER BY version")
        ] == versions_first
        # Relaxed version pin: assert membership/ordering, not equality against a
        # fixed list that a future v4 breaks again.  v1 and v2 must both occur
        # along the way, in ascending order with no duplicates -- "the schema
        # advances; this pins the migration's contract, not the current number."
        # Do NOT re-tighten to `== [1, 2]`.
        versions = [
            r["version"] for r in con.execute("SELECT version FROM schema_version ORDER BY version")
        ]
        assert versions == sorted(set(versions)), f"version chain not ascending/unique: {versions}"
        assert {1, 2} <= set(versions), f"v1/v2 migration steps missing from chain: {versions}"
        assert store.schema_version(con) >= 2
    finally:
        con.close()


def test_v1_to_v2_preserves_every_row(v1_path: Path):
    """RED->GREEN guard 1 — "v1->v2 preserves every row".

    Reverted (``MIGRATIONS`` without migration 2, ``SCHEMA_VERSION = 1``), this
    test fails with this real output::

        $ .venv/bin/python -m pytest tests/test_store_v2.py::test_v1_to_v2_preserves_every_row -q
        E           AssertionError: schema_version must be 2 after the upgrade
        E           assert 1 == 2
        E            +  where 1 = <function schema_version at 0x...>(<sqlite3.Connection object at 0x...>)
        E            +    where <function schema_version at 0x...> = store.schema_version
        1 failed in 0.02s

    i.e. the DB stays v1, ``rework.source_ref``/``model_suggested`` and
    ``lane_candidates`` never appear, and every v2 assertion below is red.
    Restored, the same test passes (13 passed).

    NOTE (U0.12): the ``== 2`` pin below was later relaxed to ``>= 2`` because
    the schema advanced to v3.  The transcript above is the real pre-relaxation
    output; re-running the same reverted store now fails identically but reports
    ``assert 1 >= 2``.  It still fails -- the migration contract is intact.
    """
    con = store.connect(v1_path)
    before = _snapshot(con)
    before_counts = {t: len(rows) for t, rows in before.items()}
    con.close()

    store.init_db(v1_path)

    con = store.connect(v1_path)
    try:
        # Relaxed version pin: this pins the migration's contract (a v1 DB must
        # reach at least v2 after the upgrade), not the current global number.
        # Do NOT re-tighten to `== 2`: the schema advances; this is a range.
        assert store.schema_version(con) >= 2, "v1 db must reach at least v2 after the upgrade"
        after = _snapshot(con)
        after_counts = {t: len(rows) for t, rows in after.items()}
        assert after_counts == before_counts, (before_counts, after_counts)
        for table in V1_TABLES:
            assert after[table] == before[table], f"rows changed in {table}"
        # the new column was added with a real default, not NULL
        assert all(r["model_suggested"] == 0 for r in con.execute("SELECT * FROM rework"))
        assert store.count(con, "lane_candidates") == 0
    finally:
        con.close()


def test_migration_reports_and_resolves_duplicate_docket_dirs(tmp_path: Path):
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    con = _build_v1(path, duplicate_docket_dir=True)
    assert len(store.find_duplicate_dockets(con)) == 1  # 2 rows share the dir
    con.close()

    store.init_db(path)

    con = store.connect(path)
    try:
        assert store.find_duplicate_dockets(con) == []
        docket = store.get_docket_by_dir(con, "dockets/duval/lane-a")
        assert docket is not None and docket["id"] == 2, "keeper must be newest verified_at"
        assert store.count(con, "dockets") == 1
        # the rework row pointing at the loser was re-pointed, not orphaned
        assert store.get_rework(con, 1)["docket_id"] == 2
        assert store.MIGRATION_NOTES[-1]["merged_ids"] == [1]
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# rework
# --------------------------------------------------------------------------- #


def test_add_rework_dedupes_and_lists(con: sqlite3.Connection):
    docket_id, _ = store.upsert_docket_by_dir(
        con, dir="dockets/duval/lane-a", freshness="current",
        manifest_json={"schema": "resextract/docket/1"},
    )

    rid, inserted = store.add_rework(
        con,
        docket_id=docket_id,
        reason="file moved",
        required_work="re-read README.md",
        source_ref="git:b2bade3:README.md",
        model_suggested=1,
    )
    assert inserted is True

    rid2, inserted2 = store.add_rework(
        con,
        docket_id=docket_id,
        reason="file moved",
        required_work="re-read README.md",
        source_ref="git:b2bade3:README.md",
        model_suggested=1,
    )
    assert (rid2, inserted2) == (rid, False)
    assert store.count(con, "rework") == 1

    # same reason, different source_ref -> a distinct item
    rid3, inserted3 = store.add_rework(
        con, docket_id=docket_id, reason="file moved", required_work="re-read", source_ref="git:cafe:README.md"
    )
    assert inserted3 is True and rid3 != rid
    assert store.count(con, "rework") == 2

    row = store.get_rework(con, rid)
    assert row["model_suggested"] == 1
    assert row["source_ref"] == "git:b2bade3:README.md"
    assert row["required_work"] == "re-read README.md"
    assert row["closed_at"] is None

    assert len(store.list_rework(con)) == 2
    assert [r["id"] for r in store.list_rework(con, docket_id=docket_id)] == [rid, rid3]
    assert store.list_rework(con, docket_id=999) == []

    assert store.close_rework(con, rid) is True
    assert store.close_rework(con, rid) is False  # already closed
    assert [r["id"] for r in store.list_rework(con, open_only=True)] == [rid3]
    assert len(store.list_rework(con, open_only=False)) == 2
    # a closed duplicate is still a duplicate: no reopen, no second row
    assert store.add_rework(
        con, docket_id=docket_id, reason="file moved", required_work="x", source_ref="git:b2bade3:README.md"
    ) == (rid, False)
    assert store.count(con, "rework") == 2


def test_model_suggested_check_rejects_two(con: sqlite3.Connection):
    # row_schema tier 1: a rework item without a docket cannot be acted on, so the row
    # the CHECK is being tested on now names its docket (docket_id=1 is seeded by
    # ``test_open_rework_legacy_path_still_returns_int``'s sibling; here we make one).
    store.upsert_docket_by_dir(con, dir="dockets/duval/check", freshness="current",
                               manifest_json={"schema": "resextract/docket/1"})
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: model_suggested"):
        con.execute(
            "INSERT INTO rework(docket_id, reason, required_work, model_suggested) "
            "VALUES (1, 'r', 'w', 2)"
        )
    with pytest.raises(ValueError, match="model_suggested must be 0 or 1"):
        store.add_rework(con, reason="r", required_work="w", model_suggested=7)
    # 0/1 both round-trip
    _, i0 = store.add_rework(con, docket_id=1, reason="a", required_work="w", model_suggested=0)
    _, i1 = store.add_rework(con, docket_id=1, reason="b", required_work="w", model_suggested=True)
    assert (i0, i1) == (True, True)
    assert [r["model_suggested"] for r in store.list_rework(con)] == [0, 1]


def test_open_rework_legacy_path_still_returns_int(con: sqlite3.Connection):
    store.upsert_docket_by_dir(con, dir="dockets/duval/lane-a", freshness="current",
                               manifest_json={"schema": "resextract/docket/1"})
    rid = store.open_rework(con, docket_id=1, reason="source moved", required_work="re-measure")
    assert isinstance(rid, int)
    assert store.get_rework(con, rid)["model_suggested"] == 0
    assert store.open_rework(con, docket_id=1, reason="source moved", required_work="re-measure") == rid


# --------------------------------------------------------------------------- #
# dockets
# --------------------------------------------------------------------------- #


def test_upsert_docket_by_dir_never_duplicates(con: sqlite3.Connection):
    """RED->GREEN guard 2 — "upsert_docket by dir never duplicates".

    Reverted (``upsert_docket`` ignores ``dir`` when ``id=None`` and takes the v1
    plain-``INSERT`` path), this test fails with this real output::

        $ .venv/bin/python -m pytest tests/test_store_v2.py::test_upsert_docket_by_dir_never_duplicates -q
        E       sqlite3.IntegrityError: UNIQUE constraint failed: dockets.dir
        1 failed in 0.03s

    Defect 3 confirmed: one directory races to a second row.  On a DB that
    already has a unique dir index that surfaces as the error above; on one that
    predates the index it duplicates *silently* — which is exactly the shape
    ``test_migration_reports_and_resolves_duplicate_docket_dirs`` reconstructs by
    dropping ``uq_dockets_dir`` before inserting two rows for one dir.
    Restored, the same test passes (13 passed).
    """
    first_id, inserted = store.upsert_docket_by_dir(
        con, lane_id=None, dir="dockets/duval/lane-a", freshness="current",
        manifest_json={"schema": "resextract/docket/1"},
    )
    assert (inserted, first_id) == (True, 1)

    second_id, inserted2 = store.upsert_docket_by_dir(
        con, dir="dockets/duval/lane-a", freshness="stale"
    )
    assert second_id == first_id, "a second upsert of the same dir must update"
    assert inserted2 is False
    assert store.count(con, "dockets") == 1

    # legacy int-returning path is by-dir too, and idempotent
    same = store.upsert_docket(con, dir="dockets/duval/lane-a", freshness="current")
    assert same == first_id and store.count(con, "dockets") == 1

    # a partial update must not blank the stored manifest / lane
    lane = store.upsert_lane(con, target="duval", slug="lane-a", type="report")
    store.upsert_docket_by_dir(
        con, lane_id=lane, dir="dockets/duval/lane-a", manifest_json={"schema": "x"}
    )
    row = store.get_docket(con, first_id)
    assert row["manifest_json"] == {"schema": "x"}
    assert row["lane_id"] == lane
    assert row["freshness"] == "current"  # omitted field kept its value

    # two different dirs -> two rows
    other, inserted3 = store.upsert_docket_by_dir(
        con, dir="dockets/duval/lane-b", freshness="current",
        manifest_json={"schema": "resextract/docket/1"},
    )
    assert inserted3 is True and other != first_id
    assert store.count(con, "dockets") == 2


def test_dockets_dir_unique_index_rejects_direct_duplicate(con: sqlite3.Connection):
    con.execute("INSERT INTO dockets(lane_id, dir) VALUES (NULL, 'dockets/x')")
    con.commit()
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed: dockets.dir"):
        con.execute("INSERT INTO dockets(lane_id, dir) VALUES (NULL, 'dockets/x')")
    con.rollback()
    assert store.count(con, "dockets") == 1


# --------------------------------------------------------------------------- #
# lane <-> candidate join
# --------------------------------------------------------------------------- #


def _seed(con: sqlite3.Connection) -> tuple[int, int, int, int]:
    run = store.insert_run(con, target="duval")
    c1 = store.insert_candidate(con, run_id=run, kind="claim", title="c1", state="mined", provenance_json=[])
    c2 = store.insert_candidate(con, run_id=run, kind="claim", title="c2", state="mined", provenance_json=[])
    c3 = store.insert_candidate(con, run_id=run, kind="claim", title="c3", state="mined", provenance_json=[])
    lane = store.upsert_lane(con, target="duval", slug="lane-a", type="report")
    return run, c1, c2, c3, lane  # type: ignore[return-value]


def test_link_lane_candidates_is_idempotent_and_queryable(con: sqlite3.Connection):
    _, c1, c2, c3, lane = _seed(con)
    assert store.link_lane_candidates(con, lane, [c1, c2]) == 2
    assert store.link_lane_candidates(con, lane, [c2, c1, c1]) == 0  # no duplicates
    assert store.count(con, "lane_candidates") == 2
    assert store.lane_candidate_ids(con, lane) == [c1, c2]

    rows = store.candidates_for_lane(con, lane)
    assert [r["id"] for r in rows] == [c1, c2]
    assert [r["title"] for r in rows] == ["c1", "c2"]

    lanes = store.lanes_for_candidate(con, c2)
    assert [r["id"] for r in lanes] == [lane]
    assert store.lanes_for_candidate(con, c3) == []
    assert [r["id"] for r in store.unlinked_candidates(con)] == [c3]
    assert [r["id"] for r in store.unlinked_candidates(con, state="mined")] == [c3]


def test_deleting_a_lane_cascades_its_links(con: sqlite3.Connection):
    assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    _, c1, c2, _, lane = _seed(con)
    store.link_lane_candidates(con, lane, [c1, c2])
    other = store.insert_candidate(con, kind="claim", title="c4", provenance_json=[])

    con.execute("DELETE FROM lanes WHERE id=?", (lane,))
    con.commit()
    assert store.count(con, "lane_candidates") == 0
    # the candidate rows themselves are untouched by the lane cascade
    assert store.count(con, "candidates") == 4
    assert store.get_candidate(con, other) is not None

    # deleting a candidate cascades from the other side too
    lane2 = store.upsert_lane(con, target="duval", slug="lane-b", type="report")
    store.link_lane_candidates(con, lane2, [other])
    con.execute("DELETE FROM candidates WHERE id=?", (other,))
    con.commit()
    assert store.count(con, "lane_candidates") == 0


# --------------------------------------------------------------------------- #
# vocabularies still enforced after migration
# --------------------------------------------------------------------------- #


def test_all_four_check_vocabularies_reject_bad_values(con: sqlite3.Connection):
    run = store.insert_run(con, target="duval")
    candidate = store.insert_candidate(con, run_id=run, title="c", kind="claim", provenance_json=[])
    claim = store.insert_claim(con, candidate_id=candidate, text="x", kind="claim", provenance_json=[])

    with pytest.raises(ValueError, match="verdict must be one of"):
        store.insert_verdict(con, claim_id=claim, verdict="MAYBE")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: verdict"):
        con.execute("INSERT INTO verdicts(claim_id, verdict) VALUES (?, 'MAYBE')", (claim,))
    con.rollback()

    with pytest.raises(ValueError, match="source_kind must be one of"):
        store.insert_evidence(con, claim_id=claim, source_kind="ftp")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: source_kind"):
        con.execute("INSERT INTO evidence(claim_id, source_kind) VALUES (?, 'ftp')", (claim,))
    con.rollback()

    with pytest.raises(ValueError, match="lane type must be one of"):
        store.upsert_lane(con, target="duval", slug="bad-type", type="essay")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: type"):
        con.execute("INSERT INTO lanes(target, slug, \"type\") VALUES ('duval','bt','essay')")
    con.rollback()

    with pytest.raises(ValueError, match="lane status must be one of"):
        store.set_lane_status(con, 1, "wip")
    lane_row = store.upsert_lane(con, target="duval", slug="ok-lane", type="report", status="draft")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: status"):
        con.execute("UPDATE lanes SET status='wip' WHERE id=?", (lane_row,))
    con.rollback()


# --------------------------------------------------------------------------- #
# status_json
# --------------------------------------------------------------------------- #


def test_status_json_counts_new_table_and_stays_sane(con: sqlite3.Connection):
    _, c1, c2, _, lane = _seed(con)
    store.link_lane_candidates(con, lane, [c1, c2])
    store.upsert_docket_by_dir(con, dir="dockets/duval/lane-a", freshness="current",
                               manifest_json={"schema": "resextract/docket/1"})
    store.add_rework(con, docket_id=1, reason="r", required_work="w", source_ref="git:abc:f")

    summary = store.status_json(con)
    assert set(summary["tables"]) == set(store.TABLES)
    assert summary["tables"]["lane_candidates"] == 2
    assert summary["lane_candidates"]["total"] == 2
    assert summary["lane_candidates"]["candidates_linked"] == 2
    assert summary["lane_candidates"]["rework_open"] == 1
    assert summary["dockets"]["total"] == 1
    # Relaxed version pin: status_json must surface the DB's live version, which
    # must be at least the v2 this test's data model relies on -- a range, not the
    # current number.  Do NOT re-tighten to `== 2`.
    assert summary["schema_version"] >= 2
    assert summary["schema_version"] == store.schema_version(con)
    assert summary["last_run"]["target"] == "duval"
    assert "lane_candidates=2" in store.status_text(con)
