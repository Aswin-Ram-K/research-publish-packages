"""Audit every cell of the live store against the declared row profiles.

``python -m resextract.audit_store [--db state/state.sqlite] [--json PATH] [--txt PATH] [--strict]``

What it prints, per table and per column: rows, NULL count, and -- for every JSON column
-- how many stored texts fail to parse; and, for each non-conformant cell, which table,
which column, which tier it violates, which row id, and what the row *does* say (the
few non-NULL values of that column).  Verdicts per cell:

``conformant``
    The cell is populated, or NULL in a column whose profile says NULL is a recorded state.

``defect``
    The cell is NULL in a **tier-1 required** column: a row that cannot say what it is
    about.  Exit 1 under ``--strict``.

``backlog``
    The cell is NULL in a **tier-2 identity** column: written by a live legacy call shape,
    counted and printed by name (``row_schema`` documents why it is not refused).

``unparseable``
    A JSON column whose stored text does not parse.

``undeclared``
    A table or column the profiles do not name -- the schema outgrew the contract.

Read-only by construction: the DB is opened with ``file:...?mode=ro`` and the audit
never writes to it.  Its own report paths are the only writes.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from resextract import row_schema, store

CONFORMANT = "conformant"
DEFECT = "defect"
BACKLOG = "backlog"
UNPARSEABLE = "unparseable"
UNDECLARED = "undeclared"


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def open_readonly(path: str | Path) -> sqlite3.Connection:
    """Open ``path`` for reading only; a missing DB is an error, never an empty store."""

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"no store at {p}")
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _parse_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        json.loads(value)
    except (ValueError, TypeError):
        return False
    return True


def _row_key(row: sqlite3.Row) -> dict[str, Any]:
    """The cell's address: the row's ``id`` plus the first identifying column it has."""

    out: dict[str, Any] = {}
    if "id" in row.keys():
        out["id"] = row["id"]
    for col in ("slug", "url", "dir", "version"):
        if col in row.keys() and row[col] is not None:
            out[col] = row[col]
            break
    return out


def _examples(table: str, con: sqlite3.Connection, column: str, limit: int = 3) -> list[Any]:
    """What the populated rows of this column actually say (so a backlog cell is readable)."""

    try:
        rows = con.execute(
            f'SELECT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL LIMIT ?',
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [r[1] for r in rows]


def audit(con: sqlite3.Connection) -> dict[str, Any]:
    """Walk every cell; return the structured report (JSON-serialisable)."""

    started = _utcnow()
    report: dict[str, Any] = {
        "audit": "row-schema/1",
        "generated_at": started,
        "db": None,
        "schema_version": store.schema_version(con),
        "profiles_cover_schema": row_schema.profile_problems(con),
        "tables": {},
        "totals": {CONFORMANT: 0, DEFECT: 0, BACKLOG: 0, UNPARSEABLE: 0, UNDECLARED: 0},
        "cells_audited": 0,
        "nonconformant": [],
    }
    tables = [
        r[0]
        for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        if not r[0].startswith("sqlite_")
    ]
    for table in tables:
        profile = row_schema.PROFILES.get(table)
        columns = [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
        rows = con.execute(f'SELECT * FROM "{table}"').fetchall()
        n_rows = len(rows)
        table_entry: dict[str, Any] = {"rows": n_rows, "tier": "declared" if profile else UNDECLARED, "columns": {}}
        if profile is None:
            report["totals"][UNDECLARED] += 1
            report["nonconformant"].append(
                {"table": table, "column": "<all>", "verdict": UNDECLARED, "rows": n_rows,
                 "why": "table has no row profile"}
            )
            report["tables"][table] = table_entry
            continue
        for column in columns:
            tier = profile.kind_of(column)
            entry: dict[str, Any] = {"tier": tier, "nulls": 0, "null_means": profile.null_means.get(column, "")}
            cells = [r for r in rows if r[column] is None]
            entry["nulls"] = len(cells)
            report["cells_audited"] += n_rows
            if tier is None:
                entry["verdict"] = UNDECLARED
                report["totals"][UNDECLARED] += 1
                report["nonconformant"].append(
                    {"table": table, "column": column, "verdict": UNDECLARED, "rows": n_rows,
                     "why": "column has no profile tier"}
                )
            elif cells and tier == row_schema.REQUIRED:
                entry["verdict"] = DEFECT
                report["totals"][DEFECT] += len(cells)
                report["nonconformant"].append(
                    {"table": table, "column": column, "verdict": DEFECT, "tier": tier,
                     "cells": len(cells), "rows": [_row_key(c) for c in cells[:10]],
                     "why": profile.null_means.get(column) or "tier-1 required column is NULL"}
                )
            elif cells and tier == row_schema.IDENTITY:
                entry["verdict"] = BACKLOG
                report["totals"][BACKLOG] += len(cells)
                report["nonconformant"].append(
                    {"table": table, "column": column, "verdict": BACKLOG, "tier": tier,
                     "cells": len(cells), "rows": [_row_key(c) for c in cells[:10]],
                     "examples": _examples(table, con, column),
                     "why": "tier-2 identity column is NULL (legacy call shape; see row_schema)"}
                )
            else:
                entry["verdict"] = CONFORMANT
                report["totals"][CONFORMANT] += n_rows
            if column in profile.json_columns:
                bad = [r for r in rows if r[column] is not None and not _parse_ok(r[column])]
                entry["json_unparseable"] = len(bad)
                if bad:
                    entry["verdict"] = UNPARSEABLE
                    report["totals"][UNPARSEABLE] += len(bad)
                    report["nonconformant"].append(
                        {"table": table, "column": column, "verdict": UNPARSEABLE, "cells": len(bad),
                         "rows": [_row_key(b) for b in bad[:10]], "why": "JSON column does not parse"}
                    )
            table_entry["columns"][column] = entry
        report["tables"][table] = table_entry
    report["finished_at"] = _utcnow()
    report["ok"] = not (report["totals"][DEFECT] or report["totals"][UNPARSEABLE] or report["totals"][UNDECLARED]) and not report["profiles_cover_schema"]
    return report


def render_text(report: dict[str, Any]) -> str:
    """The human-readable form: one line per non-conformant cell, then the per-table table."""

    lines: list[str] = []
    lines.append(f"row-schema audit @ {report['generated_at']}  (schema v{report['schema_version']})")
    lines.append(f"db: {report.get('db')}")
    t = report["totals"]
    lines.append(
        f"cells audited {report['cells_audited']} :: conformant {t[CONFORMANT]} | backlog {t[BACKLOG]} | "
        f"DEFECT {t[DEFECT]} | unparseable {t[UNPARSEABLE]} | undeclared {t[UNDECLARED]}"
    )
    if report["profiles_cover_schema"]:
        lines.append("PROFILE COVERAGE PROBLEMS:")
        for p in report["profiles_cover_schema"]:
            lines.append(f"  ! {p}")
    else:
        lines.append("profile coverage: OK (every table and column has exactly one tier)")
    lines.append("")
    for item in report["nonconformant"]:
        lines.append(
            f"[{item['verdict'].upper():12s}] {item['table']}.{item['column']}: {item.get('why', '')}"
        )
        if "cells" in item:
            lines.append(f"               cells={item['cells']} rows={item['rows']}")
        if item.get("examples"):
            lines.append(f"               populated rows say: {item['examples']}")
    if not report["nonconformant"]:
        lines.append("no non-conformant cells")
    lines.append("")
    lines.append(f"{'table':16s} {'rows':>5s}  tier-1 req / tier-2 id / tier-3 opt (NULL counts)")
    for table, entry in report["tables"].items():
        cols = entry["columns"]
        parts = []
        for tier, label in (
            (row_schema.REQUIRED, "req"),
            (row_schema.IDENTITY, "id"),
            (row_schema.OPTIONAL, "opt"),
        ):
            names = [(c, e) for c, e in cols.items() if e["tier"] == tier]
            nulls = sum(e["nulls"] for _, e in names)
            parts.append(f"{label} {len(names)}/{nulls} null")
        lines.append(f"{table:16s} {entry['rows']:>5d}  " + " · ".join(parts))
    lines.append("")
    lines.append("VERDICT: " + ("OK" if report["ok"] else "NON-CONFORMANT (see cells above)"))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m resextract.audit_store", description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(store.DEFAULT_DB_PATH), help="store to audit (opened read-only)")
    ap.add_argument("--json", dest="json_path", default=None, help="write the structured report here")
    ap.add_argument("--txt", dest="txt_path", default=None, help="write the text report here")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any defect/unparseable/undeclared cell")
    ns = ap.parse_args(argv)

    try:
        con = open_readonly(ns.db)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        report = audit(con)
    finally:
        con.close()
    report["db"] = str(Path(ns.db).resolve())
    text = render_text(report)
    sys.stdout.write(text)
    if ns.json_path:
        Path(ns.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.json_path).write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    if ns.txt_path:
        Path(ns.txt_path).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.txt_path).write_text(text)
    if ns.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
