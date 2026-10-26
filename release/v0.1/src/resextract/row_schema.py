"""One declared row profile per table, and the single gate every store write passes.

**Why this module exists.** The null-field defect class has one shape: a row reaches the
database with a value missing that the row's own contract says must be there, and nothing
at the write boundary notices.  It has appeared three times here in three disguises -- a
handoff validated with ``json.load`` only (``U8.40``/``U8.43``), a claim standing
``CONFIRMS`` with no producer key (the ``C-curated`` row), and a manifest where ``None``
meant both "never recorded" and "cleared".  Each was found by a human reading the artefact
afterwards, because nothing enumerated the cells.

The fix is structural: **one writer** (``store._insert`` -> :func:`validate_row`) and
**one declared profile per table** (below).  The writer cannot pick a weaker rule than
its table's profile, and a schema column with no profile tier is itself a caught error
(:func:`profile_problems`).

**Three tiers, and the middle one is not a loophole.**

``REQUIRED`` (tier 1)
    A NULL means the row cannot say what it is about.  Refused before any INSERT is
    issued.

``IDENTITY`` (tier 2)
    A NULL passes the writer but is **counted and printed by name on every audit run**.
    It is not refused because a live writer omits it today -- measured on this tree,
    ``insert_candidate``/``insert_lane`` also take legacy call shapes -- and refusing it
    would turn 22 pre-existing test call sites red *without* touching the rows the
    pipeline actually writes, since the production callers already pass these values.
    The tier is a **dated, visible backlog**, not a place to park a new gap: the audit
    prints every non-conformant cell, and ``tests/test_row_schema.py`` pins the list so
    it can only shrink by explicit edit.

``OPTIONAL`` (tier 3)
    NULL is a recorded state with a meaning the row's own words give it: a root lane has
    no parent, a replay candidate has no model id, a run that never reached ``finish_run``
    has no ``finished_at``.  Permitted, and counted by the audit as conformant.

Every column of every table must appear in exactly one tier; :func:`assert_profiles_cover_schema`
checks that against ``PRAGMA table_info``, so a schema migration cannot silently widen the
unwatchable surface.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

JSON_SUFFIX = "_json"

REQUIRED = "required"  # tier 1: NULL refused at the writer
IDENTITY = "identity"  # tier 2: NULL written but audited by name (dated backlog)
OPTIONAL = "optional"  # tier 3: NULL is a recorded state

TIERS = (REQUIRED, IDENTITY, OPTIONAL)

#: The router tier: a row whose NULLs are decided by the ``upsert_*`` (router) writer that
#: owns the table's boundary, not by the shared writer.  Used only where a caller
#: legitimately needs "no row at all": a failed fetch has no bytes, so it has no hash
#: and no ``http_status``.  A router writer must call :func:`router_insert`, which applies
#: ``router_required`` and is the *only* path allowed to store ``router_methods`` columns
#: as NULL; every other writer is refused those NULLs by :func:`validate_row`.
ROUTER = "router"

#: Columns stored as JSON text.  A value that is not NULL must parse.
JSON_COLUMNS: tuple[tuple[str, str], ...] = (
    ("runs", "budget"),
    ("targets", "exclude_json"),
    ("candidates", "provenance_json"),
    ("candidates", "graph_nodes_json"),
    ("claims", "provenance_json"),
    ("verdicts", "evidence_ids_json"),
    ("dockets", "manifest_json"),
)

#: Params spellings of the quoted SQL identifiers ``"text"``/``"type"``/``"list"``, which
#: cannot be Python keyword arguments.  Mapped to the column they stand for.
ALIASES: dict[str, str] = {"_text": "text", "_type": "list"}


@dataclass(frozen=True)
class RowProfile:
    """The contract for one table's rows: three disjoint tiers covering every column."""

    table: str
    required: frozenset[str]
    identity: frozenset[str]
    optional: frozenset[str]
    json_columns: frozenset[str] = field(default_factory=frozenset)
    #: ``None`` = the table is not router-tier.  Otherwise the columns the router
    #: caller must supply, and the ones the router writer accepts as NULL but that
    #: are refused for every non-router INSERT (a NULL there is meaningful only on a
    #: router-owned row, e.g. a failed fetch's hash).
    router_required: frozenset[str] | None = None
    #: ``{writer method: columns}`` that only that router writer may store as NULL.
    router_methods: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def router_refuses(self) -> frozenset[str]:
        return frozenset(c for cols in self.router_methods.values() for c in cols)
    #: Why each column that may legitimately be NULL may be NULL -- carried so the audit
    #: prints a reason per NULL cell instead of a bare count.
    null_means: Mapping[str, str] = field(default_factory=dict)

    @property
    def columns(self) -> frozenset[str]:
        cols = self.required | self.identity | self.optional
        if self.router_required is not None:
            cols = cols | self.router_required | self.router_refuses
        return cols

    def kind_of(self, column: str) -> str | None:
        if column in self.required:
            return REQUIRED
        if column in self.identity:
            return IDENTITY
        if column in self.optional:
            return OPTIONAL
        if self.router_required is not None and column in (self.router_required | self.router_refuses):
            return ROUTER
        return None


def _profile(
    table: str,
    required: Iterable[str] = (),
    identity: Iterable[str] = (),
    optional: Iterable[str] = (),
    null_means: Mapping[str, str] | None = None,
    router_required: Iterable[str] | None = None,
    router_methods: Mapping[str, Iterable[str]] | None = None,
) -> RowProfile:
    req, ident, opt = frozenset(required), frozenset(identity), frozenset(optional)
    rreq = None if router_required is None else frozenset(router_required)
    rmethods = {k: tuple(v) for k, v in (router_methods or {}).items()}
    rref = frozenset(c for cols in rmethods.values() for c in cols)
    if rreq is not None and not rreq:
        raise AssertionError(f"{table}: router tier declared with no required columns")
    router_cols = (rreq or frozenset()) | rref
    if router_cols & (req | ident | opt):
        raise AssertionError(f"{table}: router columns overlap other tiers: {sorted(router_cols & (req | ident | opt))}")
    pairs = ((req, ident, "required/identity"), (req, opt, "required/optional"), (ident, opt, "identity/optional"))
    for a, b, names in pairs:
        if a & b:
            raise AssertionError(f"{table}: columns in two tiers ({names}): {sorted(a & b)}")
    json_cols = frozenset(c for (t, c) in JSON_COLUMNS if t == table)
    missing_json = json_cols - (req | ident | opt | router_cols)
    if missing_json:
        raise AssertionError(f"{table}: json columns not declared: {sorted(missing_json)}")
    return RowProfile(
        table=table,
        required=req,
        identity=ident,
        optional=opt,
        json_columns=json_cols,
        router_required=rreq,
        router_methods=rmethods,
        null_means=dict(null_means or {}),
    )


#: One profile per table in ``store.TABLES`` (+ ``schema_version``).  See the module
#: docstring for what each tier costs.
PROFILES: dict[str, RowProfile] = {
    # A run must say when it started.  ``finished_at`` is NULL exactly when the run never
    # reached ``finish_run`` (migration 3 repairs such a run to ``failed`` and leaves the
    # unknowable time NULL); ``model`` is NULL for every non-model run.
    "runs": _profile(
        "runs",
        required=("started_at",),
        identity=("target",),
        optional=("id", "finished_at", "status", "budget", "tokens_used", "notes", "model", "mode"),
        null_means={
            "finished_at": "the run never reached finish_run; the completion time is unknowable",
            "model": "no model id to record (non-model producer)",
            "status": "a freshly inserted run is 'running' by convention, not stored",
        },
    ),
    # A target row is its identity: a slug and the path it points at.
    "targets": _profile(
        "targets",
        required=("slug", "path"),
        optional=("head_sha", "graph_path", "graph_hash", "last_seen_at", "exclude_json"),
        null_means={"head_sha": "never resolved (no git)", "graph_hash": "no graph built yet"},
    ),
    # A candidate with no text or no provenance cannot be traced to anything.
    "candidates": _profile(
        "candidates",
        required=("kind", "title", "provenance_json"),
        identity=("summary", "score", "state"),
        optional=("id", "run_id", "graph_nodes_json", "producer", "model"),
        null_means={
            "model": "no model id to record (replay/fixture/unknown producer)",
            "graph_nodes_json": "the candidate names no graph node",
        },
    ),
    # A claim IS its text; provenance is the plan's no-orphan rule (§1.4).
    "claims": _profile(
        "claims",
        required=("kind", "text", "provenance_json"),
        identity=("verification_state",),
        optional=("id", "candidate_id", "confidence"),
        null_means={"confidence": "never assessed (recorded only when a model scored it)"},
    ),
    # Evidence without a source kind cannot be re-verified; the rest is tier 2 because a
    # live writer (``assess.verdicts``) passes a record whose hash the record may leave empty.
    "evidence": _profile(
        "evidence",
        required=("source_kind", "retrieved_at", "producer"),
        identity=("source_ref", "sha256"),
        optional=("id", "claim_id", "quote", "context", "copy_path"),
        null_means={"quote": "the evidence is a whole-file copy, quoted by excerpt elsewhere"},
    ),
    # A verdict IS its verdict word; it must name its claim and its evidence list.
    "verdicts": _profile(
        "verdicts",
        required=("claim_id", "verdict", "evidence_ids_json", "checked_at", "producer"),
        optional=("id", "rationale", "model"),
        null_means={
            "model": "no model id to record (non-model producer)",
            "rationale": "a deterministic guard may rule without prose",
        },
    ),
    # A lane must be addressable: target + slug.
    "lanes": _profile(
        "lanes",
        required=("target", "slug"),
        identity=("title", "thesis", "audience", "type", "status"),
        optional=("id", "parent_lane_id", "maturity"),
        null_means={"parent_lane_id": "a root lane has no parent", "maturity": "unrecorded maturity"},
    ),
    "lane_candidates": _profile(
        "lane_candidates",
        required=("lane_id", "candidate_id"),
    ),
    # A docket row is its directory plus the manifest it materialised.
    "dockets": _profile(
        "dockets",
        required=("dir", "manifest_json", "freshness"),
        identity=("source_head", "graph_hash", "verified_at"),
        optional=("id", "lane_id", "last_refresh_at"),
        null_means={
            "lane_id": "assembled from a replay manifest, no lane row on disk",
            "last_refresh_at": "never refreshed",
        },
    ),
    # A web source is its URL and the moment it was fetched (a router-tier table: a
    # *failed* fetch has no bytes and no status, and "no row at all" would erase the
    # failure the plan (§7) requires to be recorded).  ``method`` names the one writer
    # allowed to store such a row.
    "web_sources": _profile(
        "web_sources",
        optional=("title", "page_date", "extracted_text_path", "failure_reason"),
        router_required=("url", "fetched_at"),
        router_methods={"upsert_web_source": ("sha256", "http_status")},
        null_means={
            "page_date": "the page states no date",
            "sha256": "the fetch failed, so there are no bytes to hash",
            "http_status": "the fetch failed before a status was obtained",
        },
    ),
    # A search attempt's outcome must be recorded even when it failed (ok=0 + error).
    "search_health": _profile(
        "search_health",
        required=("ts", "engine", "query", "ok"),
        optional=("id", "result_count", "error"),
        null_means={"result_count": "the engine returned an error, not a count"},
    ),
    "rework": _profile(
        "rework",
        required=("docket_id", "reason", "required_work", "opened_at", "model_suggested"),
        optional=("id", "closed_at", "source_ref"),
        null_means={
            "closed_at": "the rework item is still open",
            "source_ref": "the caller had no real provenance ref to record (never fabricated)",
        },
    ),
    "schema_version": _profile(
        "schema_version",
        required=("version", "applied_at"),
    ),
}


def identity_columns() -> dict[str, frozenset[str]]:
    """The tier-2 backlog as ``{table: columns}`` -- what the audit must print by name."""

    return {t: p.identity for t, p in PROFILES.items() if p.identity}


def routers() -> dict[str, dict[str, tuple[str, ...]]]:
    """``{table: {writer: null-allowed columns}}`` -- the router writers that own a boundary."""

    return {t: dict(p.router_methods) for t, p in PROFILES.items() if p.router_methods}


class NullRowError(ValueError):
    """A row was refused because a required cell was NULL (or its JSON did not parse).

    The message names the table, each offending column, its tier, and why the profile
    demands a value -- enough for a caller to fix the write, and enough for a journal
    reader to see *what* was refused rather than a bare NOT NULL failure.
    """

    def __init__(self, table: str, violations: Iterable[tuple[str, str]]) -> None:
        self.table = table
        self.violations: list[tuple[str, str]] = list(violations)
        detail = "; ".join(f"{col} ({why})" for col, why in self.violations)
        super().__init__(f"refusing row for table {table!r}: {detail}")


_INSERT_RE = None


def _insert_re():
    global _INSERT_RE

    if _INSERT_RE is None:
        import re as _re

        _INSERT_RE = _re.compile(
            r"^\s*INSERT\s+(?:OR\s+\w+\s+)?INTO\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", _re.I
        )
    return _INSERT_RE


def table_of_insert(sql: str) -> str | None:
    """Return the table an INSERT statement targets, or ``None`` if it is not an INSERT.

    ``store`` words its statements in identifier form (``INSERT INTO claims(candidate_id,
    ...)``).  The pattern is deliberately strict: a statement this gate cannot attribute
    fails at the call site (``validate_row`` reports an undeclared table) rather than
    slipping past the profile.
    """

    m = _insert_re().match(sql or "")
    return m.group(1).lower() if m else None


def _json_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return True  # a caller that passed an object is rewritten by store._dump
    try:
        json.loads(value)
    except (ValueError, TypeError):
        return False
    return True


def check_row(
    table: str,
    values: Mapping[str, Any],
    *,
    strict_columns: bool = True,
) -> list[tuple[str, str]]:
    """Return every violation in ``values`` for ``table``; empty means the row may be written.

    Violations are ``(column, why)`` pairs, never raised here, so the audit path can
    classify a stored row with the same rule the writer uses, and so a caller sees *all*
    wrong cells at once instead of fixing one and hitting the next.
    """

    profile = PROFILES.get(table)
    if profile is None:
        return [("<table>", f"no row profile declared for table {table!r}")]
    out: list[tuple[str, str]] = []
    if strict_columns:
        unknown = sorted(set(values) - profile.columns - set(ALIASES))
        for col in unknown:
            out.append((col, "column is not declared in this table's row profile"))
    for col in sorted(values):
        name = ALIASES.get(col, col)
        if name not in profile.columns:
            continue
        value = values[col]
        if name in profile.required and value is None:
            out.append((col, f"tier-1 required column for {table!r} is NULL"))
            continue
        if name in profile.json_columns and value is not None and not _json_ok(value):
            out.append((col, "JSON column does not parse"))
    return out


def router_insert(con, sql: str, params: Mapping[str, Any], *, method: str) -> None:
    """The only way a router-tier row reaches SQLite (``INSERT ... ON CONFLICT``).

    ``method`` is the writer function's name; it must be the one declared for this table
    in ``router_methods``.  Refuses (before executing anything) when the row is short of a
    router-required column, and records the row as written by that method.
    """

    table = table_of_insert(sql)
    if table is None:
        raise ValueError("router_insert only accepts an INSERT statement")
    profile = PROFILES.get(table)
    if profile is None or method not in profile.router_methods:
        raise ValueError(f"{method!r} is not a declared router writer for table {table!r}")
    validate_row(table, {ALIASES.get(k, k): v for k, v in params.items()})
    con.execute(sql, params)


def validate_row(table: str, values: Mapping[str, Any]) -> None:
    """Raise :class:`NullRowError` unless ``values`` may be written to ``table``."""

    violations = check_row(table, values)
    if violations:
        raise NullRowError(table, violations)


def profile_problems(con: sqlite3.Connection) -> list[str]:
    """Report tables/columns the profiles do not cover, and declared columns that are gone."""

    problems: list[str] = []
    tables = [
        r[0]
        for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    ]
    for table in tables:
        if table.startswith("sqlite_"):
            continue
        actual = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
        profile = PROFILES.get(table)
        if profile is None:
            problems.append(f"table {table!r} has no row profile")
            continue
        undeclared = sorted(actual - profile.columns)
        if undeclared:
            problems.append(f"table {table!r} columns with no profile tier: {undeclared}")
        phantom = sorted(profile.columns - actual)
        if phantom:
            problems.append(f"table {table!r} profile names columns that do not exist: {phantom}")
    for table in PROFILES:
        if table in tables:
            continue
        problems.append(f"profile for {table!r} but no such table")
    return problems


def assert_profiles_cover_schema(con: sqlite3.Connection) -> None:
    problems = profile_problems(con)
    if problems:
        raise AssertionError("row profiles disagree with the schema: " + " | ".join(problems))
