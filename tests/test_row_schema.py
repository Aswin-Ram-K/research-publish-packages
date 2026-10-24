"""ROW-SCHEMA: one writer that refuses null rows, plus a per-cell audit.

The defect class this guards (``U8.40``/``U8.43`` key gaps, the ``C-curated`` CONFIRMS
row with no producer) has one shape: a row is written with a cell the row's contract
says must be there, and nothing at the write boundary notices.

Three guards here, each with the revert recorded that turns it red.

**Guard 1 -- the writer refuses a required NULL, and writes nothing.**
    Reverted (``_gate`` made a no-op / ``store._insert`` calling ``con.execute``
    directly), ``store.insert_claim(con, kind=..., text=..., provenance_json=None)``
    writes a claim row and the refusal assertion goes red.  The test additionally
    proves the *no partial write* half: a refused row leaves ``COUNT(*)`` unchanged.

**Guard 2 -- the single writer cannot be bypassed.**
    A source scan: no ``con.execute`` in ``src/resextract/**`` may open an INSERT
    without going through ``_insert``/``_arrow_execute``.  Reverted (restore the old
    ``upsert_target`` body), the scan reports the site by ``file:line``.

**Guard 3 -- the audit sees a defect planted behind the writer's back.**
    Reverted (``audit()`` not classifying a tier-1 NULL as ``DEFECT``), the planted
    row is reported ``conformant`` and the exit-1 assertion goes red.

Profiles are also pinned to the schema: every table and column must carry exactly one
tier, and the tier-2 ``identity`` backlog is pinned by name so it can only shrink by an
explicit edit (never grow silently into a place where new gaps hide).
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from resextract import audit_store, row_schema, store

SRC = Path(__file__).resolve().parents[1] / "src" / "resextract"


@pytest.fixture()
def con(tmp_path):
    path = tmp_path / "s.sqlite"
    store.init_db(path)
    c = store.connect(path)
    try:
        yield c
    finally:
        c.close()


# --------------------------------------------------------------------------- #
# Guard 1 -- the writer refuses
# --------------------------------------------------------------------------- #


def _count(con: sqlite3.Connection, table: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_writer_refuses_a_required_null_and_writes_nothing(con):
    """RED when reverted: `_gate` a no-op -> insert_claim writes the row, no exception.

    Recorded revert output (``store._insert`` body replaced with a bare
    ``cur = con.execute(sql, params); con.commit(); return int(cur.lastrowid)``)::

        $ .venv/bin/python -m pytest tests/test_row_schema.py::test_writer_refuses_a_required_null_and_writes_nothing -q
        E       Failed: DID NOT RAISE <class 'resextract.row_schema.NullRowError'>
        E       assert 1 == 0        # the claim row *was* written
        1 failed
    """
    before = _count(con, "claims")
    with pytest.raises(row_schema.NullRowError) as exc:
        store.insert_claim(con, kind="architectural", text="t", provenance_json=None)
    msg = str(exc.value)
    assert "claims" in msg and "provenance_json" in msg, msg
    assert "tier-1" in msg, "the refusal must say which tier the column belongs to"
    assert _count(con, "claims") == before, "a refused row must leave no trace"

    # ... and the same call with the value present still writes.
    cid = store.insert_claim(
        con, kind="architectural", text="t", provenance_json=[{"ref": "x"}]
    )
    assert store.get_claim(con, cid)["provenance_json"] == [{"ref": "x"}]


def test_writer_refuses_every_tier1_column_not_just_the_first(con):
    """All wrong cells are named at once -- a caller fixes one write, not five."""
    with pytest.raises(row_schema.NullRowError) as exc:
        store.insert_evidence(con, source_kind=None, source_ref="x", sha256="h", retrieved_at="t")
    cols = {c for c, _ in exc.value.violations}
    assert cols == {"source_kind"}, cols
    # a second call names the *other* required column -- so the refusal is not hard-wired
    with pytest.raises(row_schema.NullRowError) as exc2:
        store.insert_verdict(con, claim_id=None, verdict="EXTENDS", evidence_ids_json=[])
    assert {c for c, _ in exc2.value.violations} == {"claim_id", "checked_at"}, exc2.value


def test_writer_refuses_unparseable_json(con):
    """``_dump`` re-serialises containers but passes a ``str`` through: that text must parse.

    This is the ``U8.40``-family rule applied one layer down -- validate *parse*, not just
    presence: a JSON column holding ``'{not json'`` is as defective as a NULL one.
    """
    with pytest.raises(row_schema.NullRowError) as exc:
        store.insert_claim(con, kind="k", text="t", provenance_json="{not json")
    assert any("JSON" in why for _, why in exc.value.violations), str(exc.value)


def test_tier2_identity_null_is_written_and_audited_not_refused(con):
    """The dated backlog: a tier-2 NULL passes the writer; the audit prints it."""
    store.insert_candidate(con, kind="k", title="t", provenance_json=[])
    out = audit_store.audit(con)
    backlog = [i for i in out["nonconformant"] if i["verdict"] == audit_store.BACKLOG]
    assert backlog, "a NULL summary/score/state must surface as backlog, not vanish"
    assert {i["column"] for i in backlog} >= {"summary", "score", "state"}
    assert out["totals"][audit_store.DEFECT] == 0


def test_model_id_refusal_still_holds_with_the_gate_in_place(con):
    """The pre-existing provenance rule is not loosened by the new gate."""
    with pytest.raises(ValueError) as exc:
        store.insert_verdict(
            con, claim_id=1, verdict="EXTENDS", evidence_ids_json=[], producer="replay", model="m"
        )
    assert "may only accompany" in str(exc.value)


# --------------------------------------------------------------------------- #
# Guard 2 -- the single writer cannot be bypassed
# --------------------------------------------------------------------------- #

# ``[\s(]*`` spans the newline (and the implicit ``"a" "b"`` continuation) that a
# multi-line call puts between ``con.execute(`` and its SQL literal -- the shape the
# first draft of this scan silently missed by scanning one *line* at a time.
_INSERT_IN_EXECUTE = re.compile(r"(?<![\w.])con\.execute\([\s(]*[fbr]?[\"\']\s*INSERT", re.I)
# A site is admitted only if something on the preceding lines proves its row was
# checked (``_gate(...)`` or ``validate_row(...)``).  Two writers legitimately need
# SQLite's own ``ON CONFLICT`` / ``OR IGNORE`` clause; both call that gate first.
_GATE_BEFORE = re.compile(r"(_gate|validate_row)\s*\(")


def test_no_insert_bypasses_the_single_writer():
    """RED when reverted: an accessor that calls ``con.execute`` with an ungated INSERT.

    Recorded revert (``upsert_lane``'s explicit-id upsert restored to a bare
    ``con.execute``, its ``row_schema.validate_row("lanes", ...)`` call removed)::

        E  AssertionError: bypassing INSERT sites: ['store.py:1584: \'con.execute(\\n            "INSERT INTO dockets(lane_id, dir, manifest_j\'']
        E  assert not ['store.py:1584: ...']
        (second revert: ``upsert_lane``'s ``row_schema.validate_row("lanes", ...)`` stubbed out) ::
        E  AssertionError: expected the two gate-then-execute writer sites, saw [...lane_candidates...]
        1 failed
    """
    offenders: list[str] = []
    gated: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text()
        for m in _INSERT_IN_EXECUTE.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            # walk back to the nearest line that closed a call at column 0 -- the
            # gate call always ends there (``    )``), even when its argument list is
            # twenty lines long
            prev_line_start = text.rfind("\n", 0, text.rfind("\n", 0, m.start()) + 1)
            while prev_line_start > 0:
                cur = text.find("\n", prev_line_start + 1)
                if text[prev_line_start + 1:len(text) if cur < 0 else cur].strip() == ")":
                    break
                prev_line_start = text.rfind("\n", 0, prev_line_start)
            # everything from the previous statement's end to this site: a gate call
            # can be twenty lines long, so "the previous line" is not enough
            window = text[max(0, prev_line_start - 600):m.start()]
            site = f"{path.name}:{line_no}: {text[m.start():m.start() + 70]!r}"
            (gated if _GATE_BEFORE.search(window) else offenders).append(site)
    # Control: the scan must actually match the multi-line shape.  Without this the
    # guard can silently match nothing -- which is exactly how its first draft passed
    # green against a reverted store for 40 minutes of this unit.
    assert _INSERT_IN_EXECUTE.search('cur = con.execute(\n            "INSERT INTO dockets(x) VALUES (1)"'), \
        "the bypass scan does not match a multi-line con.execute(\n \"INSERT ...\")"
    # Control 2: exactly the two known non-``_insert`` writers stay, each explicitly
    # gated.  A refactor that moves a row back behind a bare execute grows ``offenders``.
    assert len(gated) == 2, f"expected the two gate-then-execute writer sites, saw {gated}"
    assert not offenders, f"bypassing INSERT sites: {offenders}"
    assert audit_store  # imported: the audit must be importable from the package


# --------------------------------------------------------------------------- #
# Guard 3 -- the audit sees a defect planted behind the writer's back
# --------------------------------------------------------------------------- #


def test_audit_flags_a_defect_planted_with_raw_sql(con, tmp_path):
    """RED when reverted: ``audit()`` treats a tier-1 NULL as conformant.

    Recorded revert (the ``elif cells and tier == row_schema.REQUIRED`` branch deleted,
    so every NULL falls through to the ``else: conformant`` arm)::

        $ .venv/bin/python -m pytest tests/test_row_schema.py::test_audit_flags_a_defect_planted_with_raw_sql -q
        E       AssertionError: the audit missed a planted tier-1 NULL
        1 failed
    """
    con.execute("INSERT INTO claims(kind, text, provenance_json, verification_state) VALUES ('k','t',NULL,'unverified')")
    con.commit()
    out = audit_store.audit(con)
    assert out["totals"][audit_store.DEFECT] >= 1, "the audit missed a planted tier-1 NULL"
    hit = [i for i in out["nonconformant"] if i["table"] == "claims" and i["column"] == "provenance_json"]
    assert hit and hit[0]["verdict"] == audit_store.DEFECT, out["nonconformant"]

    # and the CLI's --strict exit code reflects it
    db = tmp_path / "s.sqlite"
    con.close()
    copied = sqlite3.connect(db)
    copied.execute("INSERT INTO claims(kind, text, provenance_json, verification_state) VALUES ('k','t',NULL,'unverified')")
    copied.commit()
    copied.close()
    rc = audit_store.main(["--db", str(db), "--strict"])
    assert rc == 1


def test_audit_opens_the_db_read_only(tmp_path, con):
    db = tmp_path / "s.sqlite"
    con.close()
    before = db.stat().st_mtime_ns, db.stat().st_size
    ro = audit_store.open_readonly(db)
    try:
        with pytest.raises(sqlite3.OperationalError):
            ro.execute("INSERT INTO claims(kind, text) VALUES ('k','t')")
    finally:
        ro.close()
    assert (db.stat().st_mtime_ns, db.stat().st_size) == before


def test_profile_coverage_matches_the_live_schema(con):
    assert row_schema.profile_problems(con) == []
    row_schema.assert_profiles_cover_schema(con)


def test_identity_backlog_is_pinned_so_it_can_only_shrink():
    """Tier-2 is a dated list, not a parking space: growing it needs an explicit edit."""
    assert {t: tuple(sorted(c)) for t, c in row_schema.identity_columns().items()} == {
        "runs": ("target",),
        "candidates": ("score", "state", "summary"),
        "claims": ("verification_state",),
        "evidence": ("sha256", "source_ref"),
        "lanes": ("audience", "status", "thesis", "title", "type"),
        "dockets": ("graph_hash", "source_head", "verified_at"),
    }


def test_required_and_identity_tiers_do_not_overlap_and_cover_every_column(con):
    for table, profile in row_schema.PROFILES.items():
        assert profile.required.isdisjoint(profile.identity)
        assert profile.required.isdisjoint(profile.optional)
        if table == "schema_version":
            continue
        actual = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
        assert actual == profile.columns, table


def test_live_store_audit_is_conformant():
    """The shipped store must audit clean: 0 defects, 0 unparseable, 0 undeclared."""
    db = Path(__file__).resolve().parents[1] / "state" / "state.sqlite"
    con = audit_store.open_readonly(db)
    try:
        out = audit_store.audit(con)
    finally:
        con.close()
    assert out["totals"][audit_store.DEFECT] == 0, out["nonconformant"]
    assert out["totals"][audit_store.UNPARSEABLE] == 0
    assert out["totals"][audit_store.UNDECLARED] == 0
    assert out["profiles_cover_schema"] == []
    assert out["cells_audited"] >= 200
    # the four pre-existing NULL families are classified, with their reason
    reasons = {
        (t, c): e["null_means"]
        for t, entry in out["tables"].items()
        for c, e in entry["columns"].items()
        if e["nulls"]
    }
    assert ("lanes", "parent_lane_id") in reasons and "root lane" in reasons[("lanes", "parent_lane_id")]
    assert "finished_at" in {c for (_, c) in reasons}


def test_audit_report_is_valid_json_shape(tmp_path):
    db = tmp_path / "empty.sqlite"
    store.init_db(db)
    con = audit_store.open_readonly(db)
    try:
        out = audit_store.audit(con)
    finally:
        con.close()
    json.dumps(out)  # must be serialisable as-is
    text = audit_store.render_text(out)
    assert "profile coverage: OK" in text
    assert "VERDICT: OK" in text
