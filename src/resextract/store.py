"""SQLite store for resextract: schema, ordered migrations and typed accessors.

Design notes (U0.3):
  * One connection = one ``sqlite3.Connection`` with ``row_factory=Row`` and
    ``PRAGMA foreign_keys=ON`` (per-connection, so ``connect()`` always sets it).
  * ``init_db()`` is idempotent: ``CREATE TABLE IF NOT EXISTS`` plus a
    ``schema_version`` table whose rows record each applied migration.
  * Accessors take/return plain ``dict`` objects.  Columns ending in ``_json``
    accept Python objects on write and come back decoded on read.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = 2
DEFAULT_DB_PATH = Path("state/state.sqlite")

TABLES: tuple[str, ...] = (
    "runs",
    "targets",
    "candidates",
    "claims",
    "evidence",
    "verdicts",
    "lanes",
    "dockets",
    "web_sources",
    "search_health",
    "rework",
    "lane_candidates",  # added in migration 2
)

# Enumerated vocabularies (enforced by CHECK constraints in migration 1).
VERDICT_VOCAB: tuple[str, ...] = ("CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED")
LANE_TYPES: tuple[str, ...] = ("paper", "report", "blog", "benchmark_card", "memo")
LANE_STATUSES: tuple[str, ...] = ("draft", "ready", "stale", "needs_rework", "superseded")
EVIDENCE_SOURCE_KINDS: tuple[str, ...] = ("local", "web")

_JSON_SUFFIX = "_json"


def utcnow() -> str:
    """ISO-8601 UTC timestamp with a trailing ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def default_db_path() -> Path:
    """``state/state.sqlite`` unless ``RESEXTRACT_STATE_DB`` overrides it."""
    env = os.environ.get("RESEXTRACT_STATE_DB")
    return Path(env) if env else DEFAULT_DB_PATH


# --------------------------------------------------------------------------- #
# Migrations
# --------------------------------------------------------------------------- #

_MIGRATION_1: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS runs (
        id          INTEGER PRIMARY KEY,
        target      TEXT,
        started_at  TEXT NOT NULL,
        finished_at TEXT,
        status      TEXT,
        budget      TEXT,
        tokens_used INTEGER DEFAULT 0,
        notes       TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS targets (
        slug         TEXT PRIMARY KEY,
        path         TEXT NOT NULL,
        head_sha     TEXT,
        graph_path   TEXT,
        graph_hash   TEXT,
        last_seen_at TEXT,
        exclude_json TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS candidates (
        id               INTEGER PRIMARY KEY,
        run_id           INTEGER REFERENCES runs(id),
        kind             TEXT,
        title            TEXT,
        summary          TEXT,
        provenance_json  TEXT,
        graph_nodes_json TEXT,
        score            REAL,
        state            TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS claims (
        id                 INTEGER PRIMARY KEY,
        candidate_id       INTEGER REFERENCES candidates(id),
        kind               TEXT,
        "text"             TEXT,
        provenance_json    TEXT,
        verification_state TEXT,
        confidence         REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence (
        id          INTEGER PRIMARY KEY,
        claim_id    INTEGER REFERENCES claims(id),
        source_kind TEXT CHECK (source_kind IN ('local', 'web')),
        source_ref  TEXT,
        sha256      TEXT,
        quote       TEXT,
        context     TEXT,
        retrieved_at TEXT,
        copy_path   TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS verdicts (
        id                INTEGER PRIMARY KEY,
        claim_id          INTEGER REFERENCES claims(id),
        verdict           TEXT CHECK (verdict IN ('CONFIRMS', 'EXTENDS', 'CONTRADICTS', 'UNVERIFIED')),
        rationale         TEXT,
        evidence_ids_json TEXT,
        checked_at        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS lanes (
        id             INTEGER PRIMARY KEY,
        target         TEXT,
        slug           TEXT,
        title          TEXT,
        thesis         TEXT,
        audience       TEXT,
        "type"         TEXT CHECK ("type" IN ('paper', 'report', 'blog', 'benchmark_card', 'memo')),
        parent_lane_id INTEGER REFERENCES lanes(id),
        maturity       TEXT,
        status         TEXT CHECK (status IN ('draft', 'ready', 'stale', 'needs_rework', 'superseded'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dockets (
        id              INTEGER PRIMARY KEY,
        lane_id         INTEGER REFERENCES lanes(id),
        dir             TEXT,
        manifest_json   TEXT,
        source_head     TEXT,
        graph_hash      TEXT,
        freshness       TEXT,
        verified_at     TEXT,
        last_refresh_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS web_sources (
        url                   TEXT PRIMARY KEY,
        sha256                TEXT,
        title                 TEXT,
        page_date             TEXT,
        fetched_at            TEXT,
        http_status           INTEGER,
        extracted_text_path   TEXT,
        failure_reason        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS search_health (
        id           INTEGER PRIMARY KEY,
        ts           TEXT,
        engine       TEXT,
        query        TEXT,
        result_count INTEGER,
        ok           INTEGER,
        error        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rework (
        id            INTEGER PRIMARY KEY,
        docket_id     INTEGER REFERENCES dockets(id),
        reason        TEXT,
        required_work TEXT,
        opened_at     TEXT,
        closed_at     TEXT
    )
    """,
    # Indices: run_id, candidate_id, claim_id, target, status, ts (+ useful extras).
    "CREATE INDEX IF NOT EXISTS idx_candidates_run_id ON candidates(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_candidates_state ON candidates(state)",
    "CREATE INDEX IF NOT EXISTS idx_claims_candidate_id ON claims(candidate_id)",
    "CREATE INDEX IF NOT EXISTS idx_evidence_claim_id ON evidence(claim_id)",
    "CREATE INDEX IF NOT EXISTS idx_verdicts_claim_id ON verdicts(claim_id)",
    "CREATE INDEX IF NOT EXISTS idx_lanes_target ON lanes(target)",
    "CREATE INDEX IF NOT EXISTS idx_lanes_status ON lanes(status)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_lanes_target_slug ON lanes(target, slug)",
    "CREATE INDEX IF NOT EXISTS idx_dockets_lane_id ON dockets(lane_id)",
    "CREATE INDEX IF NOT EXISTS idx_dockets_freshness ON dockets(freshness)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_dockets_dir ON dockets(dir)",
    "CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)",
    "CREATE INDEX IF NOT EXISTS idx_runs_target ON runs(target)",
    "CREATE INDEX IF NOT EXISTS idx_search_health_ts ON search_health(ts)",
    "CREATE INDEX IF NOT EXISTS idx_rework_docket_id ON rework(docket_id)",
]

def find_duplicate_dockets(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return ``dockets.dir`` values that currently have more than one row.

    Used by migration 2 to *report* duplicates before uniqueness is enforced.
    Nothing is deleted here; resolution is a separate, deliberate step.
    """
    rows = con.execute(
        "SELECT dir, COUNT(*) AS n, GROUP_CONCAT(id) AS ids FROM dockets "
        "WHERE dir IS NOT NULL GROUP BY dir HAVING n > 1 ORDER BY dir"
    ).fetchall()
    return [
        {
            "dir": r["dir"],
            "count": int(r["n"]),
            "ids": [int(x) for x in str(r["ids"]).split(",")],
        }
        for r in rows
    ]


def resolve_docket_dir_duplicates(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """Deterministically de-duplicate ``dockets.dir``, then report what merged.

    Keeper = newest ``verified_at`` (NULL newest-last), tie-broken by highest
    ``id``.  ``rework.docket_id`` rows pointing at a loser are re-pointed at the
    keeper first, so no rework row is orphaned or lost.  Losers are deleted.
    Called by migration 2 *before* ``dockets_dir_unique`` is created.
    """
    merged: list[dict[str, Any]] = []
    for dup in find_duplicate_dockets(con):
        rows = con.execute(
            "SELECT id, verified_at FROM dockets WHERE dir=? ORDER BY "
            "(verified_at IS NULL), verified_at DESC, id DESC",
            (dup["dir"],),
        ).fetchall()
        keeper = int(rows[0]["id"])
        losers = [int(r["id"]) for r in rows[1:]]
        for loser in losers:
            con.execute("UPDATE rework SET docket_id=? WHERE docket_id=?", (keeper, loser))
            con.execute("DELETE FROM dockets WHERE id=?", (loser,))
        merged.append({"dir": dup["dir"], "keeper": keeper, "merged_ids": losers})
    return merged


def _resolve_docket_dir_duplicates(con: sqlite3.Connection) -> list[dict[str, Any]]:
    """Migration step: report and resolve pre-existing duplicate docket dirs."""
    found = resolve_docket_dir_duplicates(con)
    MIGRATION_NOTES.extend(found)
    return found


# Ordered migrations.  Statement lists may contain plain SQL strings or a
# callable ``(con) -> Any`` for steps that need Python (e.g. reporting and
# deterministically merging pre-existing duplicate rows before adding a
# UNIQUE index, which SQLite cannot do in SQL alone).
_MIGRATION_2: list[Any] = [
    # 1. Report + deterministically resolve any pre-existing dockets.dir dupes.
    _resolve_docket_dir_duplicates,
    # 2. rework: persist where a suggestion came from, and whether a model
    #    (rather than a measurement) suggested it.
    "ALTER TABLE rework ADD COLUMN source_ref TEXT",
    "ALTER TABLE rework ADD COLUMN model_suggested INTEGER NOT NULL DEFAULT 0 "
    "CHECK (model_suggested IN (0, 1))",
    # 3. Lane <-> candidate membership join (defect 2: --lane pulled every lane).
    """
    CREATE TABLE IF NOT EXISTS lane_candidates (
        lane_id      INTEGER NOT NULL REFERENCES lanes(id) ON DELETE CASCADE,
        candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
        PRIMARY KEY (lane_id, candidate_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_lane_candidates_candidate_id "
    "ON lane_candidates(candidate_id)",
    "CREATE INDEX IF NOT EXISTS idx_lane_candidates_lane_id ON lane_candidates(lane_id)",
    # 4. dockets.dir uniqueness (defect 3).  SQLite cannot add a table-level
    #    UNIQUE constraint in place, so this is a unique index.
    "CREATE UNIQUE INDEX IF NOT EXISTS dockets_dir_unique ON dockets(dir)",
]

MIGRATIONS: list[tuple[int, list[Any]]] = [(1, _MIGRATION_1), (2, _MIGRATION_2)]

# Populated by migration 2 when it detects/resolves duplicate docket dirs, so a
# caller can report exactly what merged during an in-place upgrade.
MIGRATION_NOTES: list[dict[str, Any]] = []


# --------------------------------------------------------------------------- #
# Connection / schema
# --------------------------------------------------------------------------- #


def connect(path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    """Open a connection with the row factory and foreign keys enabled."""
    p = Path(path) if path is not None else default_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(path: str | os.PathLike[str] | None = None) -> Path:
    """Create/upgrade the schema in WAL mode.  Idempotent; returns the path."""
    p = Path(path) if path is not None else default_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = connect(p)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        row = con.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()
        current = int(row[0])
        for version, statements in MIGRATIONS:
            if version <= current:
                continue
            for statement in statements:
                if callable(statement):
                    statement(con)
                    continue
                try:
                    con.execute(statement)
                except sqlite3.OperationalError as exc:
                    # A migration that died between ADD COLUMNs leaves the
                    # column behind; re-running must still reach the end.
                    if "duplicate column name" not in str(exc).lower():
                        raise
            con.execute(
                "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                (version, utcnow()),
            )
        con.commit()
    finally:
        con.close()
    return p


def schema_version(con: sqlite3.Connection) -> int:
    row = con.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()
    return int(row[0])


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _dump(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def _load(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value


def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    out: dict[str, Any] = {}
    for key in row.keys():
        value = row[key]
        out[key] = _load(value) if key.endswith(_JSON_SUFFIX) else value
    return out


def _rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [r for r in (_row(row) for row in rows) if r is not None]


def _insert(con: sqlite3.Connection, sql: str, params: Mapping[str, Any]) -> int:
    cur = con.execute(sql, params)
    con.commit()
    return int(cur.lastrowid)


def _get(con: sqlite3.Connection, table: str, key: str, value: Any) -> dict[str, Any] | None:
    return _row(con.execute(f"SELECT * FROM {table} WHERE {key} = ?", (value,)).fetchone())


# --------------------------------------------------------------------------- #
# runs
# --------------------------------------------------------------------------- #


def insert_run(
    con: sqlite3.Connection,
    *,
    target: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    status: str | None = "running",
    budget: Any = None,
    tokens_used: int = 0,
    notes: str | None = None,
) -> int:
    return _insert(
        con,
        "INSERT INTO runs(target, started_at, finished_at, status, budget, tokens_used, notes) "
        "VALUES (:target, :started_at, :finished_at, :status, :budget, :tokens_used, :notes)",
        {
            "target": target,
            "started_at": started_at or utcnow(),
            "finished_at": finished_at,
            "status": status,
            "budget": _dump(budget),
            "tokens_used": tokens_used,
            "notes": notes,
        },
    )


def upsert_run(con: sqlite3.Connection, *, id: int | None = None, **fields: Any) -> int:
    """Insert a run, or update it in place when ``id`` is supplied."""
    if id is None:
        return insert_run(con, **fields)
    existing = get_run(con, id)
    if existing is None:
        return _insert(
            con,
            "INSERT INTO runs(id, target, started_at, finished_at, status, budget, tokens_used, notes) "
            "VALUES (:id, :target, :started_at, :finished_at, :status, :budget, :tokens_used, :notes)",
            {
                "id": id,
                "target": fields.get("target"),
                "started_at": fields.get("started_at") or utcnow(),
                "finished_at": fields.get("finished_at"),
                "status": fields.get("status", "running"),
                "budget": _dump(fields.get("budget")),
                "tokens_used": fields.get("tokens_used", 0),
                "notes": fields.get("notes"),
            },
        )
    merged = dict(existing)
    merged.update(fields)
    merged["id"] = id
    merged["budget"] = _dump(merged.get("budget"))
    con.execute(
        "UPDATE runs SET target=:target, started_at=:started_at, finished_at=:finished_at, "
        "status=:status, budget=:budget, tokens_used=:tokens_used, notes=:notes WHERE id=:id",
        {k: merged.get(k) for k in ("id", "target", "started_at", "finished_at", "status", "budget", "tokens_used", "notes")},
    )
    con.commit()
    return id


def get_run(con: sqlite3.Connection, run_id: int) -> dict[str, Any] | None:
    return _get(con, "runs", "id", run_id)


def finish_run(con: sqlite3.Connection, run_id: int, *, status: str = "done", tokens_used: int | None = None, notes: str | None = None) -> bool:
    sets = ["finished_at=?", "status=?"]
    params: list[Any] = [utcnow(), status]
    if tokens_used is not None:
        sets.append("tokens_used=?")
        params.append(tokens_used)
    if notes is not None:
        sets.append("notes=?")
        params.append(notes)
    params.append(run_id)
    cur = con.execute(f"UPDATE runs SET {', '.join(sets)} WHERE id=?", params)
    con.commit()
    return cur.rowcount == 1


def last_run(con: sqlite3.Connection) -> dict[str, Any] | None:
    return _row(con.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone())


# --------------------------------------------------------------------------- #
# targets
# --------------------------------------------------------------------------- #


def upsert_target(
    con: sqlite3.Connection,
    *,
    slug: str,
    path: str,
    head_sha: str | None = None,
    graph_path: str | None = None,
    graph_hash: str | None = None,
    last_seen_at: str | None = None,
    exclude_json: Any = None,
) -> str:
    con.execute(
        "INSERT INTO targets(slug, path, head_sha, graph_path, graph_hash, last_seen_at, exclude_json) "
        "VALUES (:slug, :path, :head_sha, :graph_path, :graph_hash, :last_seen_at, :exclude_json) "
        "ON CONFLICT(slug) DO UPDATE SET path=excluded.path, head_sha=excluded.head_sha, "
        "graph_path=excluded.graph_path, graph_hash=excluded.graph_hash, "
        "last_seen_at=excluded.last_seen_at, exclude_json=excluded.exclude_json",
        {
            "slug": slug,
            "path": path,
            "head_sha": head_sha,
            "graph_path": graph_path,
            "graph_hash": graph_hash,
            "last_seen_at": last_seen_at or utcnow(),
            "exclude_json": _dump(exclude_json),
        },
    )
    con.commit()
    return slug


def get_target(con: sqlite3.Connection, slug: str) -> dict[str, Any] | None:
    return _get(con, "targets", "slug", slug)


def list_targets(con: sqlite3.Connection) -> list[dict[str, Any]]:
    return _rows(con.execute("SELECT * FROM targets ORDER BY slug").fetchall())


# --------------------------------------------------------------------------- #
# candidates / claims / evidence / verdicts
# --------------------------------------------------------------------------- #


def insert_candidate(
    con: sqlite3.Connection,
    *,
    run_id: int | None = None,
    kind: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    provenance_json: Any = None,
    graph_nodes_json: Any = None,
    score: float | None = None,
    state: str | None = None,
) -> int:
    return _insert(
        con,
        "INSERT INTO candidates(run_id, kind, title, summary, provenance_json, graph_nodes_json, score, state) "
        "VALUES (:run_id, :kind, :title, :summary, :provenance_json, :graph_nodes_json, :score, :state)",
        {
            "run_id": run_id,
            "kind": kind,
            "title": title,
            "summary": summary,
            "provenance_json": _dump(provenance_json),
            "graph_nodes_json": _dump(graph_nodes_json),
            "score": score,
            "state": state,
        },
    )


def upsert_candidate(con: sqlite3.Connection, *, id: int | None = None, **fields: Any) -> int:
    if id is None:
        return insert_candidate(con, **fields)
    con.execute(
        "INSERT INTO candidates(id, run_id, kind, title, summary, provenance_json, graph_nodes_json, score, state) "
        "VALUES (:id, :run_id, :kind, :title, :summary, :provenance_json, :graph_nodes_json, :score, :state) "
        "ON CONFLICT(id) DO UPDATE SET run_id=excluded.run_id, kind=excluded.kind, title=excluded.title, "
        "summary=excluded.summary, provenance_json=excluded.provenance_json, "
        "graph_nodes_json=excluded.graph_nodes_json, score=excluded.score, state=excluded.state",
        {
            "id": id,
            "run_id": fields.get("run_id"),
            "kind": fields.get("kind"),
            "title": fields.get("title"),
            "summary": fields.get("summary"),
            "provenance_json": _dump(fields.get("provenance_json")),
            "graph_nodes_json": _dump(fields.get("graph_nodes_json")),
            "score": fields.get("score"),
            "state": fields.get("state"),
        },
    )
    con.commit()
    return id


def get_candidate(con: sqlite3.Connection, candidate_id: int) -> dict[str, Any] | None:
    return _get(con, "candidates", "id", candidate_id)


def insert_claim(
    con: sqlite3.Connection,
    *,
    candidate_id: int | None = None,
    kind: str | None = None,
    text: str | None = None,
    provenance_json: Any = None,
    verification_state: str | None = None,
    confidence: float | None = None,
) -> int:
    return _insert(
        con,
        'INSERT INTO claims(candidate_id, kind, "text", provenance_json, verification_state, confidence) '
        "VALUES (:candidate_id, :kind, :text, :provenance_json, :verification_state, :confidence)",
        {
            "candidate_id": candidate_id,
            "kind": kind,
            "text": text,
            "provenance_json": _dump(provenance_json),
            "verification_state": verification_state,
            "confidence": confidence,
        },
    )


def get_claim(con: sqlite3.Connection, claim_id: int) -> dict[str, Any] | None:
    return _get(con, "claims", "id", claim_id)


def insert_evidence(
    con: sqlite3.Connection,
    *,
    claim_id: int | None = None,
    source_kind: str | None = None,
    source_ref: str | None = None,
    sha256: str | None = None,
    quote: str | None = None,
    context: str | None = None,
    retrieved_at: str | None = None,
    copy_path: str | None = None,
) -> int:
    if source_kind is not None and source_kind not in EVIDENCE_SOURCE_KINDS:
        raise ValueError(f"source_kind must be one of {EVIDENCE_SOURCE_KINDS}, got {source_kind!r}")
    return _insert(
        con,
        "INSERT INTO evidence(claim_id, source_kind, source_ref, sha256, quote, context, retrieved_at, copy_path) "
        "VALUES (:claim_id, :source_kind, :source_ref, :sha256, :quote, :context, :retrieved_at, :copy_path)",
        {
            "claim_id": claim_id,
            "source_kind": source_kind,
            "source_ref": source_ref,
            "sha256": sha256,
            "quote": quote,
            "context": context,
            "retrieved_at": retrieved_at or utcnow(),
            "copy_path": copy_path,
        },
    )


def get_evidence(con: sqlite3.Connection, evidence_id: int) -> dict[str, Any] | None:
    return _get(con, "evidence", "id", evidence_id)


def insert_verdict(
    con: sqlite3.Connection,
    *,
    claim_id: int | None = None,
    verdict: str | None = None,
    rationale: str | None = None,
    evidence_ids_json: Any = None,
    checked_at: str | None = None,
) -> int:
    if verdict is not None and verdict not in VERDICT_VOCAB:
        raise ValueError(f"verdict must be one of {VERDICT_VOCAB}, got {verdict!r}")
    return _insert(
        con,
        "INSERT INTO verdicts(claim_id, verdict, rationale, evidence_ids_json, checked_at) "
        "VALUES (:claim_id, :verdict, :rationale, :evidence_ids_json, :checked_at)",
        {
            "claim_id": claim_id,
            "verdict": verdict,
            "rationale": rationale,
            "evidence_ids_json": _dump(evidence_ids_json),
            "checked_at": checked_at or utcnow(),
        },
    )


def get_verdict(con: sqlite3.Connection, verdict_id: int) -> dict[str, Any] | None:
    return _get(con, "verdicts", "id", verdict_id)


# --------------------------------------------------------------------------- #
# lanes
# --------------------------------------------------------------------------- #


def upsert_lane(
    con: sqlite3.Connection,
    *,
    id: int | None = None,
    target: str | None = None,
    slug: str | None = None,
    title: str | None = None,
    thesis: str | None = None,
    audience: str | None = None,
    type: str | None = None,  # noqa: A002 - matches the schema vocabulary
    parent_lane_id: int | None = None,
    maturity: str | None = None,
    status: str | None = "draft",
) -> int:
    if type is not None and type not in LANE_TYPES:
        raise ValueError(f"lane type must be one of {LANE_TYPES}, got {type!r}")
    if status is not None and status not in LANE_STATUSES:
        raise ValueError(f"lane status must be one of {LANE_STATUSES}, got {status!r}")
    if id is None:
        return _insert(
            con,
            'INSERT INTO lanes(target, slug, title, thesis, audience, "type", parent_lane_id, maturity, status) '
            "VALUES (:target, :slug, :title, :thesis, :audience, :type, :parent_lane_id, :maturity, :status)",
            {
                "target": target,
                "slug": slug,
                "title": title,
                "thesis": thesis,
                "audience": audience,
                "type": type,
                "parent_lane_id": parent_lane_id,
                "maturity": maturity,
                "status": status,
            },
        )
    con.execute(
        'INSERT INTO lanes(id, target, slug, title, thesis, audience, "type", parent_lane_id, maturity, status) '
        "VALUES (:id, :target, :slug, :title, :thesis, :audience, :type, :parent_lane_id, :maturity, :status) "
        'ON CONFLICT(id) DO UPDATE SET target=excluded.target, slug=excluded.slug, title=excluded.title, '
        'thesis=excluded.thesis, audience=excluded.audience, "type"=excluded."type", '
        "parent_lane_id=excluded.parent_lane_id, maturity=excluded.maturity, status=excluded.status",
        {
            "id": id,
            "target": target,
            "slug": slug,
            "title": title,
            "thesis": thesis,
            "audience": audience,
            "type": type,
            "parent_lane_id": parent_lane_id,
            "maturity": maturity,
            "status": status,
        },
    )
    con.commit()
    return id


def get_lane(con: sqlite3.Connection, lane_id: int) -> dict[str, Any] | None:
    return _get(con, "lanes", "id", lane_id)


def get_lane_by_slug(con: sqlite3.Connection, target: str, slug: str) -> dict[str, Any] | None:
    return _row(
        con.execute("SELECT * FROM lanes WHERE target=? AND slug=?", (target, slug)).fetchone()
    )


def set_lane_status(con: sqlite3.Connection, lane_id: int, status: str) -> bool:
    if status not in LANE_STATUSES:
        raise ValueError(f"lane status must be one of {LANE_STATUSES}, got {status!r}")
    cur = con.execute("UPDATE lanes SET status=? WHERE id=?", (status, lane_id))
    con.commit()
    return cur.rowcount == 1


# --------------------------------------------------------------------------- #
# lane <-> candidate membership (migration 2)
# --------------------------------------------------------------------------- #


def link_lane_candidates(
    con: sqlite3.Connection, lane_id: int, candidate_ids: Iterable[int]
) -> int:
    """Idempotently link ``candidate_ids`` to ``lane_id``; returns new links.

    Linking the same pair twice is a no-op.  This is the join the materialize
    stage needs so ``--lane A`` cannot pull lane B's members (defect 2).
    """
    ids = sorted({int(c) for c in candidate_ids})
    before = con.total_changes
    for candidate_id in ids:
        con.execute(
            "INSERT OR IGNORE INTO lane_candidates(lane_id, candidate_id) VALUES (?, ?)",
            (lane_id, candidate_id),
        )
    con.commit()
    return int(con.total_changes - before)


def lane_candidate_ids(con: sqlite3.Connection, lane_id: int) -> list[int]:
    """Candidate ids linked to a lane, ascending."""
    rows = con.execute(
        "SELECT candidate_id FROM lane_candidates WHERE lane_id=? ORDER BY candidate_id",
        (lane_id,),
    ).fetchall()
    return [int(r["candidate_id"]) for r in rows]


def candidates_for_lane(con: sqlite3.Connection, lane_id: int) -> list[dict[str, Any]]:
    """Candidate rows linked to a lane (joined), ordered by candidate id."""
    rows = con.execute(
        "SELECT c.* FROM candidates c JOIN lane_candidates lc ON lc.candidate_id = c.id "
        "WHERE lc.lane_id=? ORDER BY c.id",
        (lane_id,),
    ).fetchall()
    return _rows(rows)


def lanes_for_candidate(con: sqlite3.Connection, candidate_id: int) -> list[dict[str, Any]]:
    """Inverse of :func:`candidates_for_lane`: lane rows for one candidate."""
    rows = con.execute(
        "SELECT l.* FROM lanes l JOIN lane_candidates lc ON lc.lane_id = l.id "
        "WHERE lc.candidate_id=? ORDER BY l.id",
        (candidate_id,),
    ).fetchall()
    return _rows(rows)


def unlinked_candidates(con: sqlite3.Connection, state: str | None = None) -> list[dict[str, Any]]:
    """Candidates with no lane link -- the honest answer when backfill is partial."""
    sql = (
        "SELECT c.* FROM candidates c LEFT JOIN lane_candidates lc ON lc.candidate_id = c.id "
        "WHERE lc.candidate_id IS NULL"
    )
    params: list[Any] = []
    if state is not None:
        sql += " AND c.state = ?"
        params.append(state)
    sql += " ORDER BY c.id"
    return _rows(con.execute(sql, params).fetchall())


# --------------------------------------------------------------------------- #
# dockets
# --------------------------------------------------------------------------- #


def upsert_docket_by_dir(
    con: sqlite3.Connection,
    *,
    lane_id: int | None = None,
    dir: str,  # noqa: A002 - matches the schema column name
    manifest_json: Any = None,
    source_head: str | None = None,
    graph_hash: str | None = None,
    freshness: str | None = None,
    verified_at: str | None = None,
    last_refresh_at: str | None = None,
) -> tuple[int, bool]:
    """Insert-or-update a docket keyed on ``dir``; never duplicates.

    Returns ``(row_id, inserted)``.  This is the *documented* docket write path
    (defect 3: ``dockets.dir`` had no uniqueness, so the same directory could be
    recorded repeatedly).

    On update, provided (non-NULL) fields win and omitted fields keep their
    stored value, so a partial refresh cannot blank out the manifest.  Use the
    ``id=`` path of :func:`upsert_docket` when a full-row overwrite is intended.
    """
    if dir is None:
        raise ValueError("upsert_docket_by_dir requires a non-NULL dir")
    params: dict[str, Any] = {
        "lane_id": lane_id,
        "dir": dir,
        "manifest_json": _dump(manifest_json),
        "source_head": source_head,
        "graph_hash": graph_hash,
        "freshness": freshness,
        "verified_at": verified_at,
        "last_refresh_at": last_refresh_at,
    }
    existing = _row(con.execute("SELECT * FROM dockets WHERE dir=?", (dir,)).fetchone())
    if existing is None:
        cur = con.execute(
            "INSERT INTO dockets(lane_id, dir, manifest_json, source_head, graph_hash, "
            "freshness, verified_at, last_refresh_at) "
            "VALUES (:lane_id, :dir, :manifest_json, :source_head, :graph_hash, "
            ":freshness, :verified_at, :last_refresh_at)",
            params,
        )
        con.commit()
        return int(cur.lastrowid), True
    con.execute(
        "UPDATE dockets SET lane_id=COALESCE(:lane_id, lane_id), "
        "manifest_json=COALESCE(:manifest_json, manifest_json), "
        "source_head=COALESCE(:source_head, source_head), "
        "graph_hash=COALESCE(:graph_hash, graph_hash), "
        "freshness=COALESCE(:freshness, freshness), "
        "verified_at=COALESCE(:verified_at, verified_at), "
        "last_refresh_at=COALESCE(:last_refresh_at, last_refresh_at) WHERE id=:id",
        {**params, "id": int(existing["id"])},
    )
    con.commit()
    return int(existing["id"]), False


def upsert_docket(
    con: sqlite3.Connection,
    *,
    id: int | None = None,
    lane_id: int | None = None,
    dir: str | None = None,
    manifest_json: Any = None,
    source_head: str | None = None,
    graph_hash: str | None = None,
    freshness: str | None = None,
    verified_at: str | None = None,
    last_refresh_at: str | None = None,
) -> int:
    """Upsert a docket, returning its row id (kept ``int`` for existing callers).

    * ``id=None`` **and** a ``dir`` -> insert-or-update keyed on ``dir``
      (never duplicates; see :func:`upsert_docket_by_dir`).
    * ``id`` given -> full-row update by id (unchanged legacy behaviour).
    * ``id=None`` and no ``dir`` -> plain insert (nothing to key on).
    """
    params = {
        "id": id,
        "lane_id": lane_id,
        "dir": dir,
        "manifest_json": _dump(manifest_json),
        "source_head": source_head,
        "graph_hash": graph_hash,
        "freshness": freshness,
        "verified_at": verified_at,
        "last_refresh_at": last_refresh_at,
    }
    if id is None:
        if dir is not None:
            return upsert_docket_by_dir(
                con,
                lane_id=lane_id,
                dir=dir,
                manifest_json=manifest_json,
                source_head=source_head,
                graph_hash=graph_hash,
                freshness=freshness,
                verified_at=verified_at,
                last_refresh_at=last_refresh_at,
            )[0]
        return _insert(
            con,
            "INSERT INTO dockets(lane_id, dir, manifest_json, source_head, graph_hash, freshness, verified_at, last_refresh_at) "
            "VALUES (:lane_id, :dir, :manifest_json, :source_head, :graph_hash, :freshness, :verified_at, :last_refresh_at)",
            params,
        )
    con.execute(
        "INSERT INTO dockets(id, lane_id, dir, manifest_json, source_head, graph_hash, freshness, verified_at, last_refresh_at) "
        "VALUES (:id, :lane_id, :dir, :manifest_json, :source_head, :graph_hash, :freshness, :verified_at, :last_refresh_at) "
        "ON CONFLICT(id) DO UPDATE SET lane_id=excluded.lane_id, dir=excluded.dir, "
        "manifest_json=excluded.manifest_json, source_head=excluded.source_head, graph_hash=excluded.graph_hash, "
        "freshness=excluded.freshness, verified_at=excluded.verified_at, last_refresh_at=excluded.last_refresh_at",
        params,
    )
    con.commit()
    return id


def get_docket(con: sqlite3.Connection, docket_id: int) -> dict[str, Any] | None:
    return _get(con, "dockets", "id", docket_id)


def get_docket_by_dir(con: sqlite3.Connection, dir: str) -> dict[str, Any] | None:  # noqa: A002
    return _get(con, "dockets", "dir", dir)


# --------------------------------------------------------------------------- #
# web_sources / search_health / rework
# --------------------------------------------------------------------------- #


def upsert_web_source(
    con: sqlite3.Connection,
    *,
    url: str,
    sha256: str | None = None,
    title: str | None = None,
    page_date: str | None = None,
    fetched_at: str | None = None,
    http_status: int | None = None,
    extracted_text_path: str | None = None,
    failure_reason: str | None = None,
) -> str:
    con.execute(
        "INSERT INTO web_sources(url, sha256, title, page_date, fetched_at, http_status, extracted_text_path, failure_reason) "
        "VALUES (:url, :sha256, :title, :page_date, :fetched_at, :http_status, :extracted_text_path, :failure_reason) "
        "ON CONFLICT(url) DO UPDATE SET sha256=excluded.sha256, title=excluded.title, page_date=excluded.page_date, "
        "fetched_at=excluded.fetched_at, http_status=excluded.http_status, "
        "extracted_text_path=excluded.extracted_text_path, failure_reason=excluded.failure_reason",
        {
            "url": url,
            "sha256": sha256,
            "title": title,
            "page_date": page_date,
            "fetched_at": fetched_at or utcnow(),
            "http_status": http_status,
            "extracted_text_path": extracted_text_path,
            "failure_reason": failure_reason,
        },
    )
    con.commit()
    return url


def get_web_source(con: sqlite3.Connection, url: str) -> dict[str, Any] | None:
    return _get(con, "web_sources", "url", url)


def insert_search_health(
    con: sqlite3.Connection,
    *,
    ts: str | None = None,
    engine: str | None = None,
    query: str | None = None,
    result_count: int | None = None,
    ok: bool | int | None = None,
    error: str | None = None,
) -> int:
    ok_value = None if ok is None else int(bool(ok))
    return _insert(
        con,
        "INSERT INTO search_health(ts, engine, query, result_count, ok, error) "
        "VALUES (:ts, :engine, :query, :result_count, :ok, :error)",
        {
            "ts": ts or utcnow(),
            "engine": engine,
            "query": query,
            "result_count": result_count,
            "ok": ok_value,
            "error": error,
        },
    )


def get_search_health(con: sqlite3.Connection, health_id: int) -> dict[str, Any] | None:
    return _get(con, "search_health", "id", health_id)


def add_rework(
    con: sqlite3.Connection,
    *,
    docket_id: int | None = None,
    reason: str | None = None,
    required_work: str | None = None,
    source_ref: str | None = None,
    model_suggested: bool | int = 0,
    opened_at: str | None = None,
) -> tuple[int, bool]:
    """Idempotently open a rework item; returns ``(row_id, inserted)``.

    Deduplicates on ``(docket_id, reason, source_ref)`` (defect 1: refresh output
    was never persisted, and re-recording duplicated rows).  An identical entry
    that already exists -- open *or* closed -- is returned as-is and NOT
    reopened or duplicated; call :func:`close_rework` to close one.

    ``source_ref`` is never fabricated: pass the real provenance ref (e.g.
    ``git:<sha>:<path>``) or leave it ``None``.
    """
    model_value = int(model_suggested)
    if model_value not in (0, 1):
        raise ValueError("model_suggested must be 0 or 1")
    existing = con.execute(
        "SELECT id FROM rework WHERE docket_id IS ? AND reason IS ? AND source_ref IS ?",
        (docket_id, reason, source_ref),
    ).fetchone()
    if existing is not None:
        return int(existing["id"]), False
    cur = con.execute(
        "INSERT INTO rework(docket_id, reason, required_work, source_ref, model_suggested, "
        "opened_at, closed_at) VALUES (:docket_id, :reason, :required_work, :source_ref, "
        ":model_suggested, :opened_at, NULL)",
        {
            "docket_id": docket_id,
            "reason": reason,
            "required_work": required_work,
            "source_ref": source_ref,
            "model_suggested": model_value,
            "opened_at": opened_at or utcnow(),
        },
    )
    con.commit()
    return int(cur.lastrowid), True


def list_rework(
    con: sqlite3.Connection,
    docket_id: int | None = None,
    open_only: bool = False,
) -> list[dict[str, Any]]:
    """List rework rows (optionally for one docket / only still-open items)."""
    where: list[str] = []
    params: list[Any] = []
    if docket_id is not None:
        where.append("docket_id = ?")
        params.append(docket_id)
    if open_only:
        where.append("closed_at IS NULL")
    sql = "SELECT * FROM rework"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id"
    return _rows(con.execute(sql, params).fetchall())


def open_rework(
    con: sqlite3.Connection,
    *,
    docket_id: int | None = None,
    reason: str | None = None,
    required_work: str | None = None,
    source_ref: str | None = None,
    model_suggested: bool | int = 0,
    opened_at: str | None = None,
) -> int:
    """Legacy int-returning opener; delegates to :func:`add_rework`."""
    return add_rework(
        con,
        docket_id=docket_id,
        reason=reason,
        required_work=required_work,
        source_ref=source_ref,
        model_suggested=model_suggested,
        opened_at=opened_at,
    )[0]


def close_rework(con: sqlite3.Connection, rework_id: int, *, closed_at: str | None = None) -> bool:
    cur = con.execute(
        "UPDATE rework SET closed_at=? WHERE id=? AND closed_at IS NULL",
        (closed_at or utcnow(), rework_id),
    )
    con.commit()
    return cur.rowcount == 1


def get_rework(con: sqlite3.Connection, rework_id: int) -> dict[str, Any] | None:
    return _get(con, "rework", "id", rework_id)


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #


def count(con: sqlite3.Connection, table: str) -> int:
    if table not in TABLES:
        raise ValueError(f"unknown table {table!r}")
    return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _group(con: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    rows = con.execute(
        f"SELECT COALESCE(CAST({column} AS TEXT), '<null>') AS k, COUNT(*) AS n "
        f"FROM {table} GROUP BY k ORDER BY k"
    ).fetchall()
    return {str(r["k"]): int(r["n"]) for r in rows}


def status_json(con: sqlite3.Connection) -> dict[str, Any]:
    """Bounded summary: counts per table, lanes by status/type, dockets by freshness, last run."""
    db_path: str | None = None
    try:
        for row in con.execute("PRAGMA database_list").fetchall():
            if row["name"] == "main":
                db_path = row["file"]
    except sqlite3.Error:
        db_path = None
    return {
        "db_path": db_path,
        "schema_version": schema_version(con),
        "generated_at": utcnow(),
        "tables": {table: count(con, table) for table in TABLES},
        "lanes": {
            "total": count(con, "lanes"),
            "by_status": _group(con, "lanes", "status"),
            "by_type": _group(con, "lanes", "type"),
        },
        "dockets": {
            "total": count(con, "dockets"),
            "by_freshness": _group(con, "dockets", "freshness"),
        },
        "candidates": {
            "total": count(con, "candidates"),
            "by_state": _group(con, "candidates", "state"),
        },
        "lane_candidates": {
            "total": count(con, "lane_candidates"),
            "candidates_linked": int(
                con.execute(
                    "SELECT COUNT(DISTINCT candidate_id) FROM lane_candidates"
                ).fetchone()[0]
            ),
            "rework_open": int(
                con.execute("SELECT COUNT(*) FROM rework WHERE closed_at IS NULL").fetchone()[0]
            ),
        },
        "runs": {"total": count(con, "runs"), "by_status": _group(con, "runs", "status")},
        "last_run": last_run(con),
    }


def status_text(con: sqlite3.Connection) -> str:
    """Human-readable rendering of :func:`status_json`."""
    data = status_json(con)
    lines = [
        f"db: {data['db_path']} (schema v{data['schema_version']})",
        "tables: " + " ".join(f"{k}={v}" for k, v in data["tables"].items()),
        "lanes: total={total} by_status={by_status} by_type={by_type}".format(**data["lanes"]),
        "dockets: total={total} by_freshness={by_freshness}".format(**data["dockets"]),
        "runs: total={total} by_status={by_status}".format(**data["runs"]),
    ]
    run = data["last_run"]
    if run is None:
        lines.append("last run: none")
    else:
        lines.append(
            f"last run: id={run['id']} target={run['target']} status={run['status']} "
            f"started_at={run['started_at']} finished_at={run['finished_at']} tokens_used={run['tokens_used']}"
        )
    return "\n".join(lines)
