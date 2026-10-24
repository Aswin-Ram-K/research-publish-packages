"""U2.6 boundary / hint / single-predicate / ``verdicts.model`` tests.

Covers the three items U2.5 owed that U2.6 closed:

* **ITEM 1** -- the v3/v4 schema boundary: a v3 database handed to a *write* path
  raises the typed ``store.SchemaTooOldError`` (naming the required migration),
  **never** the raw ``sqlite3.OperationalError: table verdicts has no column named
  producer``; ``store.migrate_copy`` migrates a run-scoped copy idempotently and
  never writes its source; and the assessment stage against a **migrated copy**
  reaches ``claims_assessed > 0`` with ``producer`` populated.
* **ITEM 2** -- ``producer_hint`` may never *upgrade* standing: the client's own
  declaration is authoritative.
* **ITEM 3** -- exactly one vocabulary and one model-standing predicate, shared
  by object identity.

Stale-bytecode discipline (U2.6): every revert/restore in this unit was measured
after ``PYTHONDONTWRITEBYTECODE=1`` plus a **FULL** ``__pycache__`` purge.  A
*narrow* purge was observed to produce 5 spurious failures -- only a full purge
is trustworthy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from resextract import store
from resextract.assess import value as value_mod
from resextract.assess import verdicts as verdicts_mod
from resextract.assess.verdicts import assess_claim, assess_claims

from test_assess_verdicts import claim_dict, gathering_search_and_fetcher  # noqa: E402

CLAIM_TEXT = "The bridge protocol uses a single round trip."


# --------------------------------------------------------------------------- #
# fixtures / stubs
# --------------------------------------------------------------------------- #


def _make_v3(tmp_path: Path, name: str = "v3.sqlite") -> Path:
    """A minimal, self-contained **schema v3** store (no v4 producer columns)."""
    p = tmp_path / name
    con = sqlite3.connect(str(p))
    try:
        con.executescript(
            """
            CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            INSERT INTO schema_version(version, applied_at) VALUES (1,'x'),(2,'x'),(3,'x');
            CREATE TABLE claims (
                id INTEGER PRIMARY KEY, candidate_id INTEGER, kind TEXT, "text" TEXT,
                provenance_json TEXT, verification_state TEXT, confidence REAL
            );
            CREATE TABLE evidence (
                id INTEGER PRIMARY KEY, claim_id INTEGER, source_kind TEXT, source_ref TEXT,
                sha256 TEXT, quote TEXT, context TEXT, retrieved_at TEXT, copy_path TEXT
            );
            CREATE TABLE verdicts (
                id INTEGER PRIMARY KEY, claim_id INTEGER, verdict TEXT, rationale TEXT,
                evidence_ids_json TEXT, checked_at TEXT
            );
            INSERT INTO claims(id, kind, "text") VALUES (1, 'architectural', 'bridge');
            """
        )
        con.commit()
    finally:
        con.close()
    return p


class _DeclaringClient:
    """A client that declares its producer exactly as the real one does."""

    def __init__(self, declared: str, model: str = "test-model-1") -> None:
        self.producer = declared
        self.model = model
        self.calls = 0

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001, ANN003
        self.calls += 1
        return schema(verdict="CONFIRMS", rationale="evidence supports it", evidence_ids=[1])


class _ReplayClient(_DeclaringClient):
    """Declares ``replay``; replays a recorded CONFIRMS that must be capped."""

    def __init__(self) -> None:
        super().__init__("replay")


# --------------------------------------------------------------------------- #
# ITEM 3 -- one vocabulary, one predicate, shared by identity
# --------------------------------------------------------------------------- #


def test_single_vocabulary_and_predicate_by_object_identity() -> None:
    assert verdicts_mod.may_back_model_claim is store.producer_is_model
    assert verdicts_mod.may_back_model_claim.__module__ == "resextract.store"
    assert verdicts_mod.PRODUCER_VOCAB is store.PRODUCER_VOCAB
    assert value_mod.PRODUCER_VOCAB is store.PRODUCER_VOCAB
    assert verdicts_mod.MODEL_PRODUCER is store.MODEL_PRODUCER
    assert value_mod.MODEL_PRODUCER is store.MODEL_PRODUCER
    # the row-level predicate keeps its public name and its own signature
    assert store.may_back_model_claim is not store.producer_is_model
    assert store.may_back_model_claim({"producer": "model"}) is True


# --------------------------------------------------------------------------- #
# ITEM 2 -- the client's own declaration is authoritative; a hint cannot upgrade
# --------------------------------------------------------------------------- #


def test_producer_hint_never_upgrades_standing() -> None:
    # over a declaring-replay client => capped
    assert verdicts_mod._client_producer(_ReplayClient(), "model") == "replay"
    # over an undeclared client => capped
    class _Undeclared:
        pass

    assert verdicts_mod._client_producer(_Undeclared(), "model") == "unknown"
    # over a genuine model client => unchanged
    real = _DeclaringClient("model")
    assert verdicts_mod._client_producer(real, "model") == "model"
    # a hint may still DENY/downgrade, never upgrade
    assert verdicts_mod._client_producer(real, "replay") == "replay"
    # out-of-vocabulary hint => still the typed error
    with pytest.raises(verdicts_mod.ProducerDeclarationError):
        verdicts_mod._client_producer(real, "MODEL")
    # the same rule holds on the value half (delegates, does not mirror)
    assert value_mod._client_producer(_ReplayClient(), "model") == "replay"
    assert value_mod._client_producer(real, "model") == "model"


def test_hint_cases_at_the_publish_gate() -> None:
    gate = verdicts_mod.may_back_model_claim
    assert gate(verdicts_mod._client_producer(_ReplayClient(), "model")) is False
    assert gate(verdicts_mod._client_producer(_DeclaringClient("model"), "model")) is True


def test_genuine_model_client_with_hint_still_confirms_replay_hint_is_capped() -> None:
    search, fetcher = gathering_search_and_fetcher()
    claim = claim_dict(1, CLAIM_TEXT)
    from resextract.assess.evidence import gather_evidence

    gather = gather_evidence(claim, search=search, fetcher=fetcher, max_queries=1)
    assert gather.records

    model_client = _DeclaringClient("model")
    v = assess_claim(claim, gather, client=model_client, evidence_ids=[1], producer_hint="model")
    assert v.verdict == "CONFIRMS"
    assert v.client_producer == "model"
    assert model_client.calls == 1

    replay_client = _ReplayClient()
    capped = assess_claim(
        claim, gather, client=replay_client, evidence_ids=[1], producer_hint="model"
    )
    # the hint did not upgrade the declaring-replay client: its CONFIRMS is capped
    assert capped.verdict == "EXTENDS"
    assert capped.client_producer == "replay"
    assert capped.model_calls == 0 and capped.replay_calls == 1


# --------------------------------------------------------------------------- #
# ITEM 1 -- the v3/v4 boundary
# --------------------------------------------------------------------------- #


def test_v3_write_raises_typed_error_not_operationalerror(tmp_path: Path) -> None:
    p = _make_v3(tmp_path)
    con = store.connect(p)
    try:
        with pytest.raises(store.SchemaTooOldError) as ei:
            store.insert_verdict(
                con, claim_id=1, verdict="CONFIRMS", rationale="r",
                evidence_ids_json=[], checked_at="2026-10-08T10:00:01.000Z",
            )
    finally:
        con.close()
    err = ei.value
    assert err.found == 3 and err.required == 4
    assert not isinstance(err, sqlite3.OperationalError)
    assert "no column named producer" not in str(err)
    assert "migrate_copy" in str(err) and "schema v3" in str(err)


def test_migrate_copy_is_idempotent_and_never_writes_its_source(tmp_path: Path) -> None:
    src = _make_v3(tmp_path)
    src_sha = store._sha256_file(src)
    first = store.migrate_copy(src, tmp_path / "mig.sqlite", backup_dir=tmp_path / "bak")
    assert first["version_before"] == 3 and first["version_after"] == 4
    assert first["rows_lost"] == 0 and first["migrated"] is True
    assert Path(first["backup"]).exists() and first["sha256_backup"]
    assert store._sha256_file(src) == src_sha  # source untouched
    assert store._version_of(src) == 3

    second = store.migrate_copy(src, tmp_path / "mig.sqlite", backup_dir=tmp_path / "bak")
    assert second["version_after"] == 4 and second["rows_lost"] == 0

    con = store.connect(tmp_path / "mig.sqlite")
    try:
        store.insert_verdict(
            con, claim_id=1, verdict="CONFIRMS", rationale="r", producer="replay",
            evidence_ids_json=[], checked_at="2026-10-08T10:00:01.000Z",
        )
        con.commit()
        rows = store.verdicts_by_producer(con)
        assert rows and rows[-1]["producer"] == "replay"
    finally:
        con.close()


def test_assess_refuses_v3_then_succeeds_on_a_migrated_copy(tmp_path: Path) -> None:
    src = _make_v3(tmp_path)
    claims = [{"claim_id": 1, "text": CLAIM_TEXT}]

    # a v3 store is refused loudly before any write ...
    with pytest.raises(store.SchemaTooOldError):
        assess_claims(claims, store_path=src, out_dir=tmp_path / "out-v3")

    # ... and the pipeline can migrate its OWN run-scoped copy
    search, fetcher = gathering_search_and_fetcher()
    report = assess_claims(
        claims,
        search=search,
        fetcher=fetcher,
        store_path=src,
        out_dir=tmp_path / "out-v4",
        migrate_store=True,
    )
    assert report.claims_assessed > 0
    assert report.migration is not None and report.migration["version_after"] == 4
    assert store._version_of(src) == 3  # the caller's database was never written
    con = store.connect(report.migration["dst"])
    try:
        rows = store.verdicts_by_producer(con)
        assert len(rows) == report.claims_assessed
        assert all(r["producer"] for r in rows), "producer must be populated, not blank"
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# verdicts.model -- wired, and only for a model producer
# --------------------------------------------------------------------------- #


def test_model_id_recorded_only_for_a_model_producer(tmp_path: Path) -> None:
    p = store.init_db(tmp_path / "s.sqlite")
    con = store.connect(p)
    try:
        cid = store.insert_claim(
            con, kind="architectural", text="bridge protocol", provenance_json=[{"ref": "fixture"}]
        )
        store.insert_verdict(
            con, claim_id=cid, verdict="CONFIRMS", rationale="r", producer="model", model="occamy-1",
            evidence_ids_json=[], checked_at="2026-10-08T10:00:01.000Z",
        )
        store.insert_verdict(
            con, claim_id=cid, verdict="UNVERIFIED", rationale="r", producer="replay",
            evidence_ids_json=[], checked_at="2026-10-08T10:00:01.000Z",
        )
        with pytest.raises(ValueError, match="may only accompany producer"):
            store.insert_verdict(
                con, claim_id=cid, verdict="CONFIRMS", rationale="r", producer="replay",
                model="occamy-1", evidence_ids_json=[], checked_at="2026-10-08T10:00:01.000Z",
            )
        con.commit()
        by_producer = {r["producer"]: r for r in store.verdicts_by_producer(con)}
        assert by_producer["model"]["model"] == "occamy-1"
        assert by_producer["replay"]["model"] is None
        assert store.model_produced_verdicts(con)[0]["model"] == "occamy-1"
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# REPAIR 2 -- the migration-4 note's basis is the truth, not the old claim
# --------------------------------------------------------------------------- #


def test_migration4_note_basis_is_join_nothing_not_no_evidence(tmp_path: Path) -> None:
    _make_v3(tmp_path)  # has one pre-existing... no rows for evidence/verdicts
    con = sqlite3.connect(str(tmp_path / "v3.sqlite"))
    con.execute("INSERT INTO verdicts(claim_id, verdict, rationale) VALUES (1,'CONFIRMS','old')")
    con.commit()
    con.close()
    src = tmp_path / "v3.sqlite"
    store.migrate_copy(src, tmp_path / "mig.sqlite", backup_dir=tmp_path / "bak")
    notes = [n for n in store.MIGRATION_NOTES_V4 if n.get("table") == "verdicts"]
    assert notes, "the v3 verdict row must have been noted"
    for note in notes:
        assert note["producer"] == "unknown"  # fail-closed behaviour unchanged
        assert "joins nothing" in note["basis"]
        assert "no producer evidence exists" not in note["basis"]
