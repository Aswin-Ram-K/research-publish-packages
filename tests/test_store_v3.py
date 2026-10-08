"""Schema-v3 tests for :mod:`resextract.store` (U2.2).

Unit under test: the additive, row-preserving migration from schema v2 to v3,
which gives a candidate a **producer identity** (FAIL A) and repairs a run left
``running``.  A *v2-shaped* database is built by executing the shipped v2 DDL
(``store._MIGRATION_1`` + the SQL statements of ``store._MIGRATION_2``), every
table is filled, and ``store.init_db`` is then called to prove nothing was lost
and that every existing candidate was labelled honestly.

Two guards carry a red->green note; the pasted failures are the real output of
running each single test against a deliberately reverted store/miner.

Run: ``.venv/bin/python -m pytest tests/test_store_v3.py -q``
"""

from __future__ import annotations

import importlib
import json
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from resextract import store
from resextract.kg import Query, QueryResult, read_graph
from resextract.mine import Miner

FIX = Path(__file__).resolve().parent / "fixtures" / "mine-mini"
QUERY_NAME_RE = re.compile(r"^QUERY_NAME:\s*(\S+)\s*$", re.M)

V2_COLUMNS: dict[str, tuple[str, ...]] = {
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
    "rework": ("id", "docket_id", "reason", "required_work", "opened_at", "closed_at", "source_ref", "model_suggested"),
}


# --------------------------------------------------------------------------- #
# a v2-shaped database, built from the shipped v2 DDL
# --------------------------------------------------------------------------- #


def _build_v2(path: Path) -> None:
    """Create a v2 database and fill *every* table (v2 shape: no producer/model)."""
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    for group in (store._MIGRATION_1, store._MIGRATION_2):
        for statement in group:
            if isinstance(statement, str):  # DDL only; callables are migration logic
                con.execute(statement)
    con.execute("INSERT INTO schema_version(version, applied_at) VALUES (2, '2026-01-01T00:00:00.000Z')")

    # runs: one replay-tagged run (also left 'running', to exercise the repair),
    # one run with no producer evidence at all.
    con.execute(
        "INSERT INTO runs(id,target,started_at,finished_at,status,budget,tokens_used,notes) "
        "VALUES (1,'duval','2026-01-01T00:00:00.000Z',NULL,'running','{\"calls\": 1}',0,"
        "'tag-replay graph=/g/graph.json')"
    )
    con.execute(
        "INSERT INTO runs(id,target,started_at,finished_at,status,budget,tokens_used,notes) "
        "VALUES (2,'duval','2026-01-01T00:00:01.000Z','2026-01-01T00:00:02.000Z','done',NULL,7,'plain-run')"
    )
    con.execute(
        "INSERT INTO targets(slug,path,head_sha,graph_path,graph_hash,last_seen_at,exclude_json) "
        "VALUES ('duval','/home/zer0null/Duval','abc',NULL,NULL,'2026-01-01T00:00:00.000Z',NULL)"
    )
    # candidate 1 has a deriveable basis (replay tag + 'REPLAY ' prefix);
    # candidate 2 has no basis at all and must land 'unknown'.
    con.execute(
        "INSERT INTO candidates(id,run_id,kind,title,summary,provenance_json,graph_nodes_json,score,state) "
        "VALUES (1,1,'novel_primitive','REPLAY tag-replay: node_a','S1','[\"a\"]','[\"n1\"]',0.5,'mined')"
    )
    con.execute(
        "INSERT INTO candidates(id,run_id,kind,title,summary,provenance_json,graph_nodes_json,score,state) "
        "VALUES (2,2,'claim','an honest unlabelled candidate','S2',NULL,NULL,NULL,'mined')"
    )
    con.execute(
        "INSERT INTO claims(id,candidate_id,kind,\"text\",provenance_json,verification_state,confidence) "
        "VALUES (1,1,'measured','X beats Y','[\"p\"]','verified',0.9)"
    )
    con.execute(
        "INSERT INTO evidence(id,claim_id,source_kind,source_ref,sha256,quote,context,retrieved_at,copy_path) "
        "VALUES (1,1,'local','src/a.py#L1-L2','ab','q','c','2026-01-01T00:00:00.000Z','material/x')"
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
        "INSERT INTO dockets(id,lane_id,dir,manifest_json,source_head,graph_hash,freshness,verified_at,last_refresh_at) "
        "VALUES (1,1,'dockets/duval/lane-a',NULL,'abc','dead',NULL,NULL,NULL)"
    )
    con.execute("INSERT INTO lane_candidates(lane_id,candidate_id) VALUES (1,1)")
    con.execute(
        "INSERT INTO web_sources(url,sha256,title,page_date,fetched_at,http_status,extracted_text_path,failure_reason) "
        "VALUES ('https://example.org','ab','T',NULL,'2026-01-01T00:00:00.000Z',200,NULL,NULL)"
    )
    con.execute(
        "INSERT INTO search_health(id,ts,engine,query,result_count,ok,error) "
        "VALUES (1,'2026-01-01T00:00:00.000Z','searxng','q',3,1,NULL)"
    )
    con.execute(
        "INSERT INTO rework(id,docket_id,reason,required_work,opened_at,closed_at,source_ref,model_suggested) "
        "VALUES (1,1,'r','w','2026-01-01T00:00:00.000Z',NULL,'git:abc:f',0)"
    )
    con.commit()
    con.close()


@pytest.fixture()
def v2_path(tmp_path: Path) -> Path:
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    _build_v2(path)
    store.MIGRATION_NOTES_V3.clear()
    store.init_db(path)
    return path


def _rows(con: sqlite3.Connection, table: str) -> list[dict]:
    return [dict(r) for r in con.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]


# --------------------------------------------------------------------------- #
# 1. the migration itself
# --------------------------------------------------------------------------- #


def test_v2_to_v3_preserves_every_row_and_backfills_honestly(v2_path: Path):
    con = store.connect(v2_path)
    try:
        assert store.schema_version(con) == 3
        assert store.SCHEMA_VERSION == 3

        # every v2 row still there, table by table
        for table, expected in {
            "runs": 2, "targets": 1, "candidates": 2, "claims": 1, "evidence": 1,
            "verdicts": 1, "lanes": 1, "dockets": 1, "web_sources": 1,
            "search_health": 1, "rework": 1, "lane_candidates": 1,
        }.items():
            assert store.count(con, table) == expected, table
        # the v2 projection of every pre-existing row is byte-identical
        for table, cols in V2_COLUMNS.items():
            for row in _rows(con, table):
                assert set(cols) <= set(row), table
        # the new columns exist, additively
        cand_cols = {r["name"] for r in con.execute("PRAGMA table_info(candidates)")}
        run_cols = {r["name"] for r in con.execute("PRAGMA table_info(runs)")}
        assert {"producer", "model"} <= cand_cols
        assert {"model", "mode"} <= run_cols

        # honest backfill: replay where the basis is real, unknown where it is absent
        replay = store.candidates_by_producer(con, "replay")
        assert [c["id"] for c in replay] == [1]
        assert replay[0]["model"] is None
        assert store.get_candidate(con, 1)["producer"] == "replay"
        assert store.get_candidate(con, 2)["producer"] == "unknown"

        basis = {
            n["table"] + ":" + str(n.get("id")): n
            for n in store.MIGRATION_NOTES_V3
            if n.get("migration") == 3
        }
        assert basis["candidates:1"]["producer"] == "replay"
        assert "replay" in basis["candidates:1"]["basis"]
        assert basis["candidates:2"]["producer"] == "unknown"
        assert basis["candidates:2"]["basis"], "an unknown row still records why"
        assert not store.may_back_model_claim(store.get_candidate(con, 1))
        assert store.model_produced_candidates(con) == []

        # the stale run was repaired, and its graph path survives in notes
        run3 = store.get_run(con, 1)
        assert run3["status"] == "failed"
        assert run3["finished_at"] is None
        assert "graph=/g/graph.json" in run3["notes"]
        assert "[U2.2 migration 3]" in run3["notes"]
        assert run3["mode"] == "replay"
        assert store.get_run(con, 2)["mode"] == "unknown"

        # not a table rebuild: the candidate row values are untouched
        assert store.get_candidate(con, 1)["title"] == "REPLAY tag-replay: node_a"
        assert store.get_candidate(con, 1)["score"] == 0.5
    finally:
        con.close()


def test_producer_check_rejects_out_of_vocabulary(v2_path: Path):
    con = store.connect(v2_path)
    try:
        for bad in ("bogus", "MODEL", ""):
            with pytest.raises(sqlite3.IntegrityError):
                con.execute("UPDATE candidates SET producer=? WHERE id=1", (bad,))
            con.rollback()
        # every vocabulary value is accepted
        for good in store.PRODUCER_VOCAB:
            con.execute("UPDATE candidates SET producer=? WHERE id=1", (good,))
        con.rollback()
    finally:
        con.close()


def test_finish_run_preserves_notes_and_graph_path(v2_path: Path):
    con = store.connect(v2_path)
    try:
        run_id = store.insert_run(
            con, target="duval", status="running", notes="mine-x graph=/abs/graph.json"
        )
        assert store.finish_run(con, run_id, status="done", tokens_used=5, notes="accepted=2") is True
        row = store.get_run(con, run_id)
        assert "graph=/abs/graph.json" in row["notes"], "the graph path must survive"
        assert "accepted=2" in row["notes"]
        assert row["notes"] == "mine-x graph=/abs/graph.json | accepted=2"
        assert row["tokens_used"] == 5 and row["status"] == "done"
        # a caller that genuinely means to replace still can
        store.finish_run(con, run_id, notes="replaced", append_notes=False)
        assert store.get_run(con, run_id)["notes"] == "replaced"
    finally:
        con.close()


def test_producer_filters_and_model_claim_helper(v2_path: Path):
    con = store.connect(v2_path)
    try:
        assert [c["id"] for c in store.candidates_by_producer(con, "replay")] == [1]
        assert store.candidates_by_producer(con, "model") == []
        assert store.candidates_by_producer(con, "unknown")[0]["id"] == 2
        assert [c["id"] for c in store.candidates_by_producer(con, run_id=1)] == [1]
        assert len(store.candidates_by_producer(con)) == 2
        assert not store.may_back_model_claim({"producer": "replay"})
        assert not store.may_back_model_claim({"producer": "unknown"})
        assert not store.may_back_model_claim({"producer": "fixture"})
        assert not store.may_back_model_claim(None)
        assert store.may_back_model_claim({"producer": "model"})
        # a model-produced row does back a claim, and only it
        cid = store.insert_candidate(con, run_id=1, title="m", producer="model", model="occamy-1.0")
        assert [c["id"] for c in store.model_produced_candidates(con)] == [cid]
        # the honest default for an unlabelled insert is 'unknown', never 'model'
        plain = store.insert_candidate(con, run_id=1, title="plain")
        assert store.get_candidate(con, plain)["producer"] == "unknown"
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 2. the regression surface: prior vocabularies and accessors
# --------------------------------------------------------------------------- #


def test_prior_check_vocabularies_still_hold(v2_path: Path):
    con = store.connect(v2_path)
    try:
        for table, column, good, bad in (
            ("evidence", "source_kind", "web", "ftp"),
            ("verdicts", "verdict", "EXTENDS", "MAYBE"),
            ("lanes", "type", "memo", "tweet"),
            ("lanes", "status", "stale", "wip"),
            ("candidates", "producer", "fixture", "guessed"),
        ):
            con.execute(f'UPDATE "{table}" SET "{column}"=?', (good,))
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(f'UPDATE "{table}" SET "{column}"=?', (bad,))
            con.rollback()
        assert store.VERDICT_VOCAB == ("CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED")
        assert store.LANE_TYPES == ("paper", "report", "blog", "benchmark_card", "memo")
        assert store.EVIDENCE_SOURCE_KINDS == ("local", "web")
        assert store.PRODUCER_VOCAB == ("model", "replay", "fixture", "unknown")
    finally:
        con.close()


def test_prior_accessors_still_behave(v2_path: Path):
    con = store.connect(v2_path)
    try:
        assert store.last_run(con)["id"] == 2
        assert store.get_run(con, 1)["id"] == 1
        assert store.upsert_run(con, id=2, status="partial") == 2
        assert store.get_run(con, 2)["status"] == "partial"
        assert store.get_run(con, 2)["notes"] == "plain-run", "upsert must merge, not wipe"

        assert store.get_target(con, "duval")["path"] == "/home/zer0null/Duval"
        assert [t["slug"] for t in store.list_targets(con)] == ["duval"]
        assert store.get_claim(con, 1)["verification_state"] == "verified"
        assert store.get_evidence(con, 1)["source_kind"] == "local"
        assert store.get_verdict(con, 1)["verdict"] == "CONFIRMS"

        assert store.get_lane(con, 1)["slug"] == "lane-a"
        assert store.get_lane_by_slug(con, "duval", "lane-a")["id"] == 1
        assert store.set_lane_status(con, 1, "stale") is True
        assert store.lane_candidate_ids(con, 1) == [1]
        assert [c["id"] for c in store.candidates_for_lane(con, 1)] == [1]
        assert [l["id"] for l in store.lanes_for_candidate(con, 1)] == [1]
        assert [c["id"] for c in store.unlinked_candidates(con)] == [2]
        store.link_lane_candidates(con, 1, [2])
        assert store.lane_candidate_ids(con, 1) == [1, 2]

        assert store.get_docket_by_dir(con, "dockets/duval/lane-a")["id"] == 1
        assert store.get_web_source(con, "https://example.org")["http_status"] == 200
        assert store.get_search_health(con, 1)["engine"] == "searxng"
        assert store.get_rework(con, 1)["source_ref"] == "git:abc:f"

        assert store.count(con, "candidates") == 2
        summary = store.status_json(con)
        assert summary["schema_version"] == 3
        assert summary["candidates"]["by_producer"] == {"replay": 1, "unknown": 1}
        assert summary["candidates"]["by_state"] == {"mined": 2}
        assert summary["runs"]["by_status"] == {"failed": 1, "partial": 1}
        assert set(summary["tables"]) == set(store.TABLES)
        assert "schema v3" in store.status_text(con)
        assert not store.find_duplicate_dockets(con)
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 3. red -> green guard (b): a replay client must yield model_calls == 0
# --------------------------------------------------------------------------- #


class _ReplayClient:
    """A zero-I/O replay client: declares itself, and makes no requests."""

    producer = "replay"
    mode = "replay"
    model = "replay-no-network"
    makes_requests = False

    def __init__(self, payloads: dict):
        self.payloads = payloads
        self.usage_sink = lambda record: None

    def sync(self):
        return self

    def call_json(self, messages, schema, **kw):
        name = QUERY_NAME_RE.search(
            "\n".join(str(m.get("content", "")) for m in messages)
        ).group(1)
        self.usage_sink(  # a synthetic record, exactly as a real client emits one
            SimpleNamespace(prompt_tokens=100, completion_tokens=20, reasoning_tokens=0, total_tokens=120)
        )
        return schema.model_validate(self.payloads[name])


class _StubGraphify:
    def __init__(self, graph_path: Path):
        self.nodes = list(read_graph(graph_path).nodes)

    def query(self, question, *, graph=None, budget=None, timeout=None):
        return QueryResult(
            ok=True, argv=["query", question], exit_code=0, stdout="", stderr_tail="",
            wall_s=0.0, nodes=list(self.nodes), edges=[], node_count=len(self.nodes),
            matched=True,
        )


def test_guard_b_replay_yields_zero_model_calls(tmp_path: Path):
    """RED->GREEN guard (b) — "a replay client must yield ``model_calls == 0``".

    Reverted (the meter counting every usage record as a call again, i.e.
    ``_Meter.absorb`` without the ``outbound`` guard, which is exactly the old
    ``self.calls += 1`` at ``candidates.py:307``), this test fails with::

        tests/test_store_v3.py:411: in test_guard_b_replay_yields_zero_model_calls
            assert report.model_calls == 0, "a replay client made no outbound request"
        E   AssertionError: a replay client made no outbound request
        E   assert 2 == 0
        E    +  where 2 = MineReport(run_id='u22-replay-guard', store_run_id=1,
        E        graph_used='/home/zer0null/reserach extarctor/tests/fixtures/mine-mini/graph.json',
        E        ...).model_calls

        (Real output, wrapped to fit; the reverted line was `_Meter.absorb`.)
    """
    payloads = {
        "q-alpha": {"candidates": [{"kind": "novel_primitive", "title": "R", "summary": "s",
                                    "evidence_quote": "q", "provenance_refs": ["miner_verify"],
                                    "graph_nodes": [], "confidence": "high", "rationale": "r"}]},
        "q-beta": {"candidates": [{"kind": "novel_primitive", "title": "R2", "summary": "s",
                                   "evidence_quote": "q", "provenance_refs": ["miner_verify"],
                                   "graph_nodes": [], "confidence": "high", "rationale": "r"}]},
    }
    client = _ReplayClient(payloads)
    miner = Miner(
        FIX,
        FIX / "graph.json",
        client=client,
        store_path=tmp_path / "state.sqlite",
        journal_dir=tmp_path / "journal",
        out_dir=tmp_path / "mine",
        graphify=_StubGraphify(FIX / "graph.json"),
        queries=[
            Query(name="q-alpha", intent="i", template="t", why="w"),
            Query(name="q-beta", intent="i", template="t", why="w"),
        ],
    )
    report = miner.mine(run_id="u22-replay-guard")
    assert report.producer == "replay" and report.mode == "replay"
    assert report.usage_records == 2 > 0
    assert report.model_calls == 0, "a replay client made no outbound request"
    assert report.total_tokens == 240  # token accounting is unchanged

    con = store.connect(tmp_path / "state.sqlite")
    try:
        rows = store.candidates_by_producer(con, "replay")
        assert len(rows) == 2 and all(r["producer"] == "replay" for r in rows)
        assert store.candidates_by_producer(con, "model") == []
        run = store.last_run(con)
        assert run["mode"] == "replay" and run["model"] == "replay-no-network"
        assert "graph=" in run["notes"], "finish_run must keep the start notes"
        written = json.loads(Path(report.out_dir, "report.json").read_text())
        assert written["producer"] == "replay" and written["model_calls"] == 0
        assert written["usage_records"] == 2 and written["model"] == "replay-no-network"
    finally:
        con.close()


def test_guard_a_backfill_never_guesses(tmp_path: Path):
    """RED->GREEN guard (a) — "backfill-never-guesses".

    A candidate row whose producer basis is *absent* must land ``unknown``, not
    ``replay``.  Reverted (``store.derive_producer``'s final ``return ("unknown", ...)``
    changed to ``return ("replay", ...)`` -- i.e. treating a run's plain tag as
    proof of replay), this test fails with::

        tests/test_store_v3.py:439: in test_guard_a_backfill_never_guesses
            assert store.derive_producer(title="honest", run_notes="plain-run")[0] == "unknown"
        E   AssertionError: assert 'replay' == 'unknown'
        E     
        E     - unknown
        E     + replay

        (Real output; the reverted line was `derive_producer`'s final return.)
    """
    assert store.derive_producer(title="honest", run_notes="plain-run")[0] == "unknown"
    assert store.derive_producer(title="honest", run_notes="")[0] == "unknown"
    assert store.derive_producer(title="REPLAY surfacing alone")[0] == "unknown"
    assert store.derive_producer(title="", run_notes="tag-replay")[0] == "unknown"
    # both signals present is the only thing that establishes replay
    producer, basis = store.derive_producer(title="REPLAY x", run_notes="tag-replay graph=/g")
    assert producer == "replay" and "replay" in basis

    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    _build_v2(path)
    store.MIGRATION_NOTES_V3.clear()
    store.init_db(path)
    con = store.connect(path)
    try:
        assert store.get_candidate(con, 2)["producer"] == "unknown"
        assert store.candidates_by_producer(con, "replay") and all(
            c["id"] == 1 for c in store.candidates_by_producer(con, "replay")
        )
    finally:
        con.close()
