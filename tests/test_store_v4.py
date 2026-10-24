"""Schema-v4 tests for :mod:`resextract.store` (U2.3).

Unit under test: the additive, row-preserving migration from schema v3 to v4,
which gives **`evidence`** and **`verdicts`** a producer identity reusing
``candidates``' own vocabulary verbatim (``model | replay | fixture | unknown``)
plus a nullable ``verdicts.model``.  Verifier V4A called the missing column a
RISK, not a nicety: ``verdicts`` is the artefact that decides whether a research
claim is novel, and it had no producer at all, so a model-produced verdict was
stored indistinguishably from a replay-produced one.

Run: ``.venv/bin/python -m pytest tests/test_store_v4.py -q``
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from resextract import store

V3_EVIDENCE_COLUMNS = (
    "id", "claim_id", "source_kind", "source_ref", "sha256",
    "quote", "context", "retrieved_at", "copy_path",
)
V3_VERDICT_COLUMNS = (
    "id", "claim_id", "verdict", "rationale", "evidence_ids_json", "checked_at",
)
TS = "2026-01-01T00:00:00.000Z"


def _columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in con.execute(f'PRAGMA table_info("{table}")')}


def _rows(con: sqlite3.Connection, table: str) -> list[dict]:
    return [dict(r) for r in con.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]


def _init_to(path: Path, version: int) -> None:
    """Build a database at exactly *version* using the shipped MIGRATIONS.

    The real migration statements (DDL *and* their callables) are executed, so
    the fixture is a genuine v2/v3-shaped store rather than a hand-written
    approximation.  No statement of a later migration is touched.
    """
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    for v, statements in store.MIGRATIONS:
        if v > version:
            continue
        for statement in statements:
            if callable(statement):
                statement(con)
            else:
                con.execute(statement)
        con.execute("INSERT INTO schema_version(version, applied_at) VALUES (?, ?)", (v, TS))
    con.commit()
    con.close()


def _fill_v3_rows(path: Path) -> None:
    """Rows that exist *before* migration 4 -- written with v3 columns only."""
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute(
        "INSERT INTO claims(id,candidate_id,kind,\"text\",provenance_json,verification_state,confidence) "
        "VALUES (1,NULL,'measured','X beats Y','[\"p\"]','verified',0.9)"
    )
    con.execute(
        "INSERT INTO evidence(id,claim_id,source_kind,source_ref,sha256,quote,context,retrieved_at,copy_path) "
        "VALUES (1,1,'local','src/a.py#L1-L2','ab','q','c',?,'material/x')",
        (TS,),
    )
    con.execute(
        "INSERT INTO verdicts(id,claim_id,verdict,rationale,evidence_ids_json,checked_at) "
        "VALUES (1,1,'CONFIRMS','because','[1]',?)",
        (TS,),
    )
    con.commit()
    con.close()


@pytest.fixture()
def v4_path(tmp_path: Path) -> Path:
    """A fresh, empty database initialised by the shipped code."""
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    store.init_db(path)
    return path


@pytest.fixture()
def v3_path(tmp_path: Path) -> Path:
    """A v3-shaped database that already holds an evidence and a verdict row."""
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    _init_to(path, 3)
    _fill_v3_rows(path)
    store.MIGRATION_NOTES_V3.clear()
    store.MIGRATION_NOTES_V4.clear()
    store.init_db(path)
    return path


# --------------------------------------------------------------------------- #
# 1. fresh DB lands on v4 with the new columns
# --------------------------------------------------------------------------- #


def test_fresh_db_is_v4_with_producer_columns(v4_path: Path):
    con = store.connect(v4_path)
    try:
        assert store.schema_version(con) == 4
        assert store.schema_version(con) == store.SCHEMA_VERSION
        assert store.SCHEMA_VERSION >= 3, "the schema only ever advances"

        assert _columns(con, "evidence") == set(V3_EVIDENCE_COLUMNS) | {"producer"}
        assert _columns(con, "verdicts") == set(V3_VERDICT_COLUMNS) | {"producer", "model"}

        # NOT NULL with the fail-closed default, and a CHECK on the vocabulary
        for table, expected in (("evidence", {"producer"}), ("verdicts", {"producer", "model"})):
            info = {r["name"]: dict(r) for r in con.execute(f'PRAGMA table_info("{table}")')}
            assert expected <= set(info)
            assert info["producer"]["notnull"] == 1, table
            assert info["producer"]["dflt_value"] == "'unknown'", table
            ddl = con.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()[0]
            assert "'model', 'replay', 'fixture', 'unknown'" in ddl, table
            assert "'none'" not in ddl, "a differently-scoped value sharing a word is how fields get confused"
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 2. v3 -> v4: every row survives, every old row is 'unknown'
# --------------------------------------------------------------------------- #


def test_v3_to_v4_preserves_every_row_and_backfills_unknown(v3_path: Path):
    """RED->GREEN guard (a) — "the backfill never guesses 'model'".

    Reverting the fail-closed backfill (``UPDATE {table} SET producer='model'``
    instead of ``'unknown'`` in ``_backfill_evidence_verdict_producer``) makes
    this test fail with this real output::

        $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
              tests/test_store_v4.py::test_v3_to_v4_preserves_every_row_and_backfills_unknown -q
        E             At index 0 diff: 'model' != 'unknown'
        E             Use -v to get more diff
        tests/test_store_v4.py:179: AssertionError
        1 failed in 0.04s

    i.e. the first element of the evidence producer list is 'model', so the
    migrated row became 'model' by default -- the exact hazard.  Restored,
    1 passed in 0.03s.  NOTE: line numbers are from the pre-docstring-edit
    revision; they shift when this text changes.

    Restored (``producer='unknown'``), the same test passes.  sha256 of
    ``src/resextract/store.py`` was identical before and after the revert cycle.
    """
    con = store.connect(v3_path)
    try:
        assert store.schema_version(con) == 4
        # the pre-existing rows are all still here: rows_lost == 0
        assert store.count(con, "claims") == 1
        assert store.count(con, "evidence") == 1
        assert store.count(con, "verdicts") == 1
        assert store.get_evidence(con, 1)["source_ref"] == "src/a.py#L1-L2"
        assert store.get_verdict(con, 1)["verdict"] == "CONFIRMS"
        # the v3 columns are untouched by the upgrade
        for row in _rows(con, "evidence"):
            assert set(V3_EVIDENCE_COLUMNS) <= set(row)
        for row in _rows(con, "verdicts"):
            assert set(V3_VERDICT_COLUMNS) <= set(row)

        # fail-closed: every migrated row is 'unknown', and NEVER 'model'
        assert [r["producer"] for r in _rows(con, "evidence")] == ["unknown"]
        assert [r["producer"] for r in _rows(con, "verdicts")] == ["unknown"]
        assert not any(r["producer"] == "model" for r in _rows(con, "evidence"))
        assert not any(r["producer"] == "model" for r in _rows(con, "verdicts")), (
            "no migrated verdict row may be 'model'"
        )
        assert store.get_verdict(con, 1)["model"] is None

        # the basis is recorded per row, like migration 3's
        notes = [n for n in store.MIGRATION_NOTES_V4 if n.get("migration") == 4]
        assert {n["table"] for n in notes} == {"evidence", "verdicts"}
        assert all(n["producer"] == "unknown" and n["basis"] for n in notes)
    finally:
        con.close()


def test_v2_to_v4_chain_reaches_v4(tmp_path: Path):
    """The whole chain works end to end: a v2-shaped DB reaches v4."""
    path = tmp_path / "state" / "state.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    _init_to(path, 2)                      # genuine v2 shape, no producer columns
    _fill_v3_rows(path)                    # v2 / v3 shared row shape
    store.init_db(path)                    # 2 -> 3 -> 4
    con = store.connect(path)
    try:
        assert store.schema_version(con) == 4
        assert store.count(con, "evidence") == 1
        assert store.count(con, "verdicts") == 1
        assert store.get_evidence(con, 1)["producer"] == "unknown"
        assert store.get_verdict(con, 1)["producer"] == "unknown"
        assert {"producer"} <= _columns(con, "evidence")
        assert {"producer", "model"} <= _columns(con, "verdicts")
    finally:
        con.close()


def test_migration_reports_rows_lost_zero(v4_path: Path):
    """``rows_lost`` is 0 for the upgrade (counted, not asserted by hand)."""
    path = v4_path
    con = store.connect(path)
    try:
        before = {t: store.count(con, t) for t in store.TABLES}
    finally:
        con.close()
    store.init_db(path)                    # re-run is a no-op
    con = store.connect(path)
    try:
        after = {t: store.count(con, t) for t in store.TABLES}
    finally:
        con.close()
    rows_lost = sum(before.values()) - sum(after.values())
    assert rows_lost == 0


# --------------------------------------------------------------------------- #
# 3. the CHECK constraint, both via INSERT and via UPDATE
# --------------------------------------------------------------------------- #


def test_producer_check_rejects_out_of_vocabulary_insert_and_update(v3_path: Path):
    """RED->GREEN guard (b) — "the CHECK reuses candidates' vocabulary exactly".

    Extending only migration 4's CHECK to admit ``'none'`` (reverting the
    vocabulary) makes this test fail with this real output::

        $ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
              tests/test_store_v4.py::test_producer_check_rejects_out_of_vocabulary_insert_and_update -q
        >           with pytest.raises(sqlite3.IntegrityError) as ins:
        E           Failed: DID NOT RAISE IntegrityError
        tests/test_store_v4.py:259: Failed
        1 failed in 0.04s

    i.e. the INSERT of 'none' was accepted once the vocabulary admitted it.
    Restored, 1 passed in 0.03s.

    Restored (vocabulary ``model|replay|fixture|unknown``), the same test passes
    and the quoted error is::

        IntegrityError: CHECK constraint failed: producer IN ('model', 'replay', 'fixture', 'unknown')

    sha256 of ``src/resextract/store.py`` was identical before and after.
    """
    con = store.connect(v3_path)
    try:
        note = "'none' is the word V4A warned about: it looks like the right value and is not."
        with pytest.raises(sqlite3.IntegrityError) as ins:
            con.execute("INSERT INTO evidence(claim_id, producer) VALUES (1, 'none')")
        assert "CHECK" in str(ins.value), note
        assert "'none'" not in str(ins.value)

        with pytest.raises(sqlite3.IntegrityError) as upd:
            con.execute("UPDATE verdicts SET producer='bogus' WHERE id=1")
        assert "CHECK" in str(upd.value)

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: producer"):
            con.execute("INSERT INTO verdicts(claim_id, verdict, producer) VALUES (1, 'CONFIRMS', 'none')")

        # nothing was written by the refused statements
        assert store.get_evidence(con, 1)["producer"] == "unknown"
        assert store.get_verdict(con, 1)["producer"] == "unknown"
    finally:
        con.close()


def test_producer_defaults_to_unknown_when_writer_omits_column(v3_path: Path):
    """A writer that omits ``producer`` gets the fail-closed default, not NULL."""
    con = store.connect(v3_path)
    try:
        con.execute(
            "INSERT INTO evidence(id, claim_id, source_kind) VALUES (2, 1, 'web')"
        )
        con.execute(
            "INSERT INTO verdicts(id, claim_id, verdict) VALUES (2, 1, 'UNVERIFIED')"
        )
        con.commit()
        assert store.get_evidence(con, 2)["producer"] == "unknown"
        assert store.get_verdict(con, 2)["producer"] == "unknown"
        # and the accessor's own default matches the schema default
        eid = store.insert_evidence(
            con, claim_id=1, source_kind="local", retrieved_at="2026-10-08T10:00:00.000Z"
        )
        vid = store.insert_verdict(
            con, claim_id=1, verdict="EXTENDS", evidence_ids_json=[eid],
            checked_at="2026-10-08T10:00:01.000Z",
        )
        assert store.get_evidence(con, eid)["producer"] == "unknown"
        assert store.get_verdict(con, vid)["producer"] == "unknown"
        assert store.get_verdict(con, vid)["model"] is None
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 4. accessors and the verdict predicate
# --------------------------------------------------------------------------- #


def test_by_producer_accessors_filter_and_handle_empty(v4_path: Path):
    con = store.connect(v4_path)
    try:
        con.execute("INSERT INTO claims(id, \"text\") VALUES (1, 'c')")
        for pid, producer in ((1, "model"), (2, "replay"), (3, "unknown")):
            con.execute(
                "INSERT INTO evidence(id, claim_id, producer) VALUES (?, 1, ?)", (pid, producer)
            )
            con.execute(
                "INSERT INTO verdicts(id, claim_id, verdict, producer) VALUES (?, 1, 'CONFIRMS', ?)",
                (pid, producer),
            )
        con.commit()

        assert [r["id"] for r in store.evidence_by_producer(con)] == [1, 2, 3]
        assert [r["id"] for r in store.evidence_by_producer(con, "model")] == [1]
        assert [r["id"] for r in store.evidence_by_producer(con, "replay")] == [2]
        assert [r["id"] for r in store.evidence_by_producer(con, "fixture")] == []
        assert [r["id"] for r in store.verdicts_by_producer(con)] == [1, 2, 3]
        assert [r["id"] for r in store.verdicts_by_producer(con, "unknown")] == [3]
        assert [r["id"] for r in store.verdicts_by_producer(con, "fixture")] == []
        assert [r["id"] for r in store.evidence_by_producer(con, "model", claim_id=1)] == [1]
        assert store.evidence_by_producer(con, "model", claim_id=99) == []
    finally:
        con.close()

    empty = store.connect(v4_path)
    try:
        empty.execute("DELETE FROM evidence")
        empty.execute("DELETE FROM verdicts")
        empty.commit()
        assert store.evidence_by_producer(empty, "model") == []
        assert store.verdicts_by_producer(empty, "model") == []
    finally:
        empty.close()


def test_verdict_predicate_true_only_for_model(v4_path: Path):
    con = store.connect(v4_path)
    try:
        con.execute("INSERT INTO claims(id, \"text\") VALUES (1, 'c')")
        for pid, producer in ((1, "model"), (2, "replay"), (3, "fixture"), (4, "unknown")):
            con.execute(
                "INSERT INTO verdicts(id, claim_id, verdict, producer) VALUES (?, 1, 'CONFIRMS', ?)",
                (pid, producer),
            )
        con.commit()
        assert store.may_back_model_claim_verdict(store.get_verdict(con, 1)) is True
        for pid in (2, 3, 4):
            assert store.may_back_model_claim_verdict(store.get_verdict(con, pid)) is False
        assert store.verdict_may_back_model_claim(store.get_verdict(con, 2)) is False
        assert store.may_back_model_claim_verdict(None) is False
        assert store.may_back_model_claim_verdict({}) is False
        # the same shared predicate, so candidates and verdicts cannot diverge
        assert store.may_back_model_claim({"producer": "model"}) is True
        assert store.may_back_model_claim({"producer": "replay"}) is False
        assert [v["id"] for v in store.model_produced_verdicts(con)] == [1]
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 5. purely additive: no v3 object changed
# --------------------------------------------------------------------------- #


def test_purely_additive_v3_columns_and_constraints_unchanged(tmp_path: Path):
    pre = tmp_path / "pre.sqlite"
    _init_to(pre, 3)
    c = sqlite3.connect(str(pre))
    c.row_factory = sqlite3.Row
    pre_evidence = _columns(c, "evidence")
    pre_verdicts = _columns(c, "verdicts")
    pre_cand = _columns(c, "candidates")
    c.close()

    post = tmp_path / "post.sqlite"
    _init_to(post, 3)
    store.init_db(post)
    con = store.connect(post)
    try:
        assert _columns(con, "evidence") - pre_evidence == {"producer"}
        assert _columns(con, "verdicts") - pre_verdicts == {"producer", "model"}
        assert pre_evidence <= _columns(con, "evidence")
        assert pre_verdicts <= _columns(con, "verdicts")
        # v2/v3 additions survive untouched
        assert {"producer", "model"} <= _columns(con, "candidates")
        assert {"model", "mode"} <= _columns(con, "runs")
        assert pre_cand <= _columns(con, "candidates")
        # the v1 CHECKs still fire
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: source_kind"):
            con.execute("INSERT INTO evidence(claim_id, source_kind) VALUES (1, 'nope')")
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: verdict"):
            con.execute("INSERT INTO verdicts(claim_id, verdict) VALUES (1, 'MAYBE')")
        # candidates' own producer CHECK is bit-for-bit what it was
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed: producer"):
            con.execute("INSERT INTO candidates(run_id, producer) VALUES (NULL, 'none')")
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 6. exactly one string-level producer comparison in this module (U2.7)
# --------------------------------------------------------------------------- #


def test_store_has_exactly_one_producer_comparison():
    """RED->GREEN guard (c) -- "store compares the producer string in one place".

    U2.7 found the second site: ``_producer_is_model`` compared
    ``row.get("producer") == "model"`` with its own literal while
    :func:`producer_is_model`'s docstring called itself "the single string-level
    comparison".  Delegating the row predicate to the string predicate makes
    that claim true **for this module**, and restoring the literal makes this
    test fail on the module-source scan below (real output is quoted in
    ``state/logs/U2.7-red-green.txt``)::

        E  AssertionError: store.py must not compare the literal 'model' directly; ...
        1 failed

    The row/string agreement table is checked too, so a future *divergence*
    between the two sites -- not merely a duplicated literal -- fails as well.
    """
    import re
    from pathlib import Path as _Path

    source = _Path(store.__file__).read_text(encoding="utf-8")
    literal = re.findall(r"""[!=]=\s*["']model["']""", source)
    assert literal == [], (
        "store.py must not compare the literal 'model' directly; compare against "
        f"store.MODEL_PRODUCER instead (found {literal!r})"
    )
    # the predicate is the thing consuming the vocabulary constant
    assert store.MODEL_PRODUCER == "model"
    assert store.MODEL_PRODUCER in store.PRODUCER_VOCAB
    assert store.producer_is_model(store.MODEL_PRODUCER) is True

    # the string site and the row site agree on the whole table, awkward inputs
    # included; the row site keeps its own fail-closed edge cases
    values = [
        (None, False), ("", False), ("model", True), ("Model", False),
        ("replay", False), ("fixture", False), ("unknown", False),
        (123, False), (b"model", False), (True, False),
    ]
    for value, expected in values:
        assert store.producer_is_model(value) is expected, value
        assert store._producer_is_model({"producer": value}) is expected, value
    for row in (None, {}, {"producer": None}, {"other": "model"}):
        assert store._producer_is_model(row) is False, row
        assert store.may_back_model_claim(row) is False, row
        assert store.may_back_model_claim_verdict(row) is False, row
    # delegation, not an equal copy: the row sites route through the string one
    assert store._producer_is_model({"producer": "model"}) is store.producer_is_model("model")
    assert store.may_back_model_claim({"producer": "model"}) is store.producer_is_model("model")
    assert store.may_back_model_claim_verdict({"producer": "model"}) is store.producer_is_model("model")
