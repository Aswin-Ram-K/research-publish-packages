"""Read-only data layer for the dashboard.

Every function here is a *pure reader*: it opens the SQLite store read-only,
streams the hash-chained journal, walks the docket tree and reports exactly what
is on disk.  Nothing is written, nothing is inferred, and no function raises:
an absent table, an unreadable docket or a missing graph produces an explicit
``{"error": "..."}`` payload (which the HTTP layer renders as 200 + JSON, never
a 500).

The one accepted side effect is *reading* the doctor's probe layer
(:func:`resextract.doctor.run_doctor`), which is how the Occamy leg is shown
honestly as down.  No model call is ever made: the Occamy probe is a
connection probe and is expected to fail.

Field honesty (U6.1 evidence): today's journals carry ``seq/ts/kind/prev/hash``
plus miner fields (``query``, ``title``, ``refs``, ``reason``, ``confidence``,
``model_calls``, ``reasoning_tokens``, ...).  They do **not** carry the model's
``reasoning_content`` text — the Occamy client captures it, the miner does not
journal it yet.  :meth:`DataLayer.reasoning_trace` says so in the payload
(``reasoning_text_available: false``) instead of paraphrasing anything.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from resextract import doctor as doctor_mod
from resextract import journal as journal_mod
from resextract.store import DEFAULT_DB_PATH, TABLES, status_json, utcnow

try:  # docket package is read-only for this unit
    from resextract.docket import read_manifest, verify_docket
except Exception:  # pragma: no cover - import guard, never fatal
    read_manifest = None  # type: ignore[assignment]
    verify_docket = None  # type: ignore[assignment]

try:
    from resextract.kg.graphify import graph_stats
except Exception:  # pragma: no cover
    graph_stats = None  # type: ignore[assignment]

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_MAX_BYTES = 2 * 1024 * 1024  # hard per-request read cap
DEFAULT_EVENT_LIMIT = 200
HEADING_FILES: tuple[str, ...] = ("README.md", "CLAIMS.md", "EVIDENCE.md", "UPDATE_BACKLOG.md")
BACKLOG_NAMES: tuple[str, ...] = ("UPDATE_BACKLOG.md", "WORK_SUGGESTIONS.md")
RESERVED_JOURNAL_KEYS = frozenset({"seq", "ts", "kind", "prev", "hash"})
REJECTED_STATES = frozenset({"rejected", "dropped", "invalid", "discarded", "refused"})
DEFAULT_GRAPH_PATH = Path("state/kg/duval/graphify-out/graph.json")

REASONING_GAP_NOTE = (
    "the client captures reasoning_content but the miner does not journal it yet"
)

_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"error": message}
    out.update(extra)
    return out


def utc_now() -> str:
    return utcnow()


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _age_days(value: Any) -> float | None:
    dt = _parse_ts(value)
    if dt is None:
        return None
    return round((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 3)


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"
    except OSError:
        return None


def safe_slug(slug: Any) -> str | None:
    """Return a filesystem-safe single-segment docket slug, or ``None``.

    Rejects anything containing a path separator, ``..``, a NUL byte, a
    leading dot or an unexpected character.  This is the directory-traversal
    guard: without it ``..%2fok-docket`` would walk out of the dockets root.
    """
    if not isinstance(slug, str):
        return None
    candidate = slug.strip()
    if not candidate or len(candidate) > 200:
        return None
    if candidate.startswith(".") or "\x00" in candidate:
        return None
    if "/" in candidate or "\\" in candidate or ".." in candidate:
        return None
    if not _SLUG_RE.match(candidate):
        return None
    return candidate


def safe_docket_slug(slug: Any, dockets_dir: Any = None) -> str | None:
    """Return a validated relative docket slug (one or more segments) or ``None``.

    Dockets may live in a nested directory (``duval/duval-u55-pinned``), so the
    detail route accepts multi-segment slugs.  Every segment is validated
    **individually** through :func:`safe_slug`, so the whole single-segment
    guard still applies per segment and none of its redundancy is dropped: a
    ``.`` or ``..`` segment, an empty segment, a backslash, a NUL byte, a
    leading dot, a ``..`` substring or any unexpected character refuses the
    slug.  Refusing is preferred to normalising — a client-supplied traversal
    path is never resolved into a legitimate one.

    When ``dockets_dir`` is given the joined path is *also* resolved with
    :func:`os.path.realpath` and must stay inside the realpath of that root.
    Containment is therefore enforced on the resolved filesystem path, not on
    string matching alone: a symlinked docket that escapes the root is refused.
    """
    if not isinstance(slug, str):
        return None
    candidate = slug.strip()
    if not candidate or len(candidate) > 200:
        return None
    if "\\" in candidate or "\x00" in candidate:
        return None
    segments = candidate.split("/")
    if any(segment != safe_slug(segment) for segment in segments):
        return None
    if dockets_dir is not None:
        try:
            root = Path(os.path.realpath(str(dockets_dir)))
            target = Path(os.path.realpath(str(root.joinpath(*segments))))
        except (OSError, ValueError, TypeError):
            return None
        if target != root and root not in target.parents:
            return None
    return candidate


def _store_dir_slug_candidates(directory: Any) -> list[str]:
    """U6.20: slug candidates for a store ``dockets.dir`` value, best first.

    The store records the directory the way the pipeline wrote it
    (``dockets/duval/duval-replay-material``), while a layer may be pointed at
    an absolute root.  The board only ever supports depth 1-2 (``*`` and
    ``*/*``), so the trailing segments carry the slug; the single-segment name
    is kept as a last-resort alias.  **Every** candidate is later validated by
    :func:`safe_docket_slug` (segment check + realpath containment) and
    required to be an existing directory under the root, so an ambiguous
    candidate can never widen the read.
    """
    if not directory:
        return []
    parts = [
        part
        for part in Path(str(directory).replace("\\", "/")).parts
        if part not in ("", ".", "/", os.sep)
    ]
    if not parts:
        return []
    anchors = [index for index, part in enumerate(parts) if part == "dockets"]
    tail = parts[anchors[-1] + 1 :] if anchors else parts
    candidates: list[str] = []
    if tail:
        candidates.append("/".join(tail[-2:]) if len(tail) > 2 else "/".join(tail))
    if len(parts) >= 2:
        candidates.append("/".join(parts[-2:]))
    candidates.append(parts[-1])
    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    return ordered


def _contained_realpath(path: Path, root: Path) -> Path | None:
    """Return the ``realpath`` of *path* only when it stays inside *root*.

    This is the per-file analogue of the ``realpath`` containment already done
    in :func:`safe_docket_slug` for the docket *directory*.  Containing the
    directory is not enough: a **file symlink inside an accepted docket** still
    follows its target on read (``_read_text_capped``) and on listing
    (``_docket_files``), which crosses the containment boundary one layer down.

    ``None`` means "refuse": the path resolves outside ``root`` (an escape), or
    resolution raised ``OSError``/``ValueError``/``TypeError``.  Containment is
    realpath-based, so an **in-root** symlink alias is allowed — it is not an
    escape — while a symlinked directory that leaves the root is refused too.
    """
    try:
        root_real = Path(os.path.realpath(str(root)))
        real = Path(os.path.realpath(str(path)))
    except (OSError, ValueError, TypeError):
        return None
    if real == root_real or root_real not in real.parents:
        return None
    return real


def _read_text_capped(path: Path, max_bytes: int) -> tuple[str, bool, int]:
    """Read at most ``max_bytes``; returns ``(text, truncated, total_bytes)``."""
    try:
        total = path.stat().st_size
        with path.open("rb") as fh:
            raw = fh.read(max_bytes)
    except OSError:
        return "", False, 0
    truncated = len(raw) < total
    return raw.decode("utf-8", errors="replace"), truncated, total


def _open_readonly(path: Path) -> int:
    """The single ``open`` seam, so a test can retarget a path inside the window."""
    return os.open(str(path), os.O_RDONLY)


def _fd_realpath(fd: int) -> Path | None:
    """Identity of the object the *kernel* has open for ``fd`` (Linux procfs)."""
    try:
        return Path(os.readlink(f"/proc/self/fd/{fd}"))
    except OSError:
        return None


def _read_text_capped_checked(
    path: Path, expected_real: Path, max_bytes: int
) -> tuple[str, bool, int, str | None]:
    """Read *path*, but only if the **opened file descriptor** is ``expected_real``.

    What this closes, stated honestly: the older shape was
    ``real = _contained_realpath(path, root)`` and then ``_read_text_capped(real)``
    — **two steps** — so a local writer could retarget a symlink between the
    containment *check* and the ``open`` (a TOCTOU window) and the read followed
    the new target.  Here the containment decision is still taken from the path
    (``expected_real``, produced by :func:`_contained_realpath`), and then the
    read is performed **from the descriptor** whose identity is resolved *after*
    the open (:func:`_fd_realpath` → ``/proc/self/fd/{fd}``).  A swap between
    check and use cannot matter: the object that will be read is exactly the
    object whose identity is compared.  Either it still resolves to the
    validated ``expected_real`` (safe) or it does not and the read is refused
    with an explicit reason — never a silent read and never a 500.

    Residual, disclosed and **not** closed here: **hard links**.  A hard link
    placed inside the root to an outside inode has an in-root path *and* an
    in-root descriptor identity, so path-based containment cannot tell it apart
    from a legitimate file.  Creating one requires write access to the outside
    file's filesystem — the same precondition the loopback-only threat model
    already names.
    """
    try:
        fd = _open_readonly(path)
    except OSError as exc:
        return "", False, 0, f"refused: unreadable ({type(exc).__name__}: {exc})"
    try:
        try:
            st = os.fstat(fd)
        except OSError as exc:
            return "", False, 0, f"refused: fstat failed ({type(exc).__name__})"
        if not stat.S_ISREG(st.st_mode):
            return "", False, 0, "refused: not a regular file"
        actual = _fd_realpath(fd)  # GUARD-B: identity taken AFTER the open
        if actual is None:
            return (
                "",
                False,
                0,
                "refused: cannot resolve the opened file descriptor "
                "(/proc/self/fd unavailable on this platform)",
            )
        if actual != expected_real:
            return (
                "",
                False,
                0,
                f"refused: the opened file descriptor is {str(actual)!r}, not the "
                f"validated path {str(expected_real)!r} (swapped between check and use)",
            )
        try:
            with os.fdopen(fd, "rb") as fh:
                fd = -1  # fdopen owns the descriptor now
                raw = fh.read(max_bytes)
        except OSError as exc:
            return "", False, 0, f"refused: read failed ({type(exc).__name__})"
    finally:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:  # pragma: no cover
                pass
    total = st.st_size
    truncated = len(raw) < total
    return raw.decode("utf-8", errors="replace"), truncated, total, None


def _headings(text: str, limit: int = 120) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            out.append({"level": len(match.group(1)), "text": match.group(2).strip()})
            if len(out) >= limit:
                break
    return out


def _sha256_stream(path: Path, chunk: int = 1 << 20) -> str | None:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while True:
                block = fh.read(chunk)
                if not block:
                    break
                digest.update(block)
    except OSError:
        return None
    return digest.hexdigest()


def _journal_files(root: Path) -> list[Path]:
    try:
        return sorted(root.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return []


def _match_journal(run: dict[str, Any], files: list[Path]) -> Path | None:
    notes = str(run.get("notes") or "")
    for path in files:
        stem = path.stem
        if stem == str(run.get("id")):
            return path
    for path in files:
        if path.stem and path.stem in notes:
            return path
    return None


# --------------------------------------------------------------------------- #
# Store resolution -- the ONE boundary (U6.16)
# --------------------------------------------------------------------------- #
# Before U6.16 there were two resolutions and they disagreed: `default_layer()`
# honoured ``RESEXTRACT_STATE_DB`` / ``RESEXTRACT_JOURNAL_DIR`` while
# ``DataLayer.__init__`` ignored them and fell back to the literal
# ``"state/state.sqlite"``.  A caller that set the env var to isolate the store
# redirected only the routes that used ``default_layer()``; a ``create_app()``
# server (which builds its own ``DataLayer``) read the *real* store while
# believing it was contained.  Two verifier units paid for that.
#
# Every layer construction now goes through the functions below, so the class of
# bug cannot recur -- enforce at the boundary, not at instances.
#
# Precedence (matches ``store.default_db_path()``, the reference behaviour):
#   explicit argument (``--store`` / ``create_app(store_path=...)``)
#     > ``RESEXTRACT_STATE_DB`` (process-level)
#     > the cwd-relative default (``state/state.sqlite``).

STORE_SOURCE_EXPLICIT = "explicit"
STORE_SOURCE_ENV = "env"
STORE_SOURCE_DEFAULT = "default"

JOURNAL_SOURCE_EXPLICIT = "explicit"
JOURNAL_SOURCE_ENV = "env"
JOURNAL_SOURCE_DEFAULT = "default"


def resolve_store(explicit: str | os.PathLike[str] | None = None) -> tuple[Path, str]:
    """Resolve the store path **and report which rule decided it**.

    The single source of truth for every ``DataLayer`` store path.  Returns the
    resolved :class:`Path` plus one of ``"explicit"``, ``"env"`` or ``"default"``,
    so a caller can *see* which store it is using instead of inferring it.
    """
    if explicit is not None:
        return Path(explicit), STORE_SOURCE_EXPLICIT
    env = os.environ.get("RESEXTRACT_STATE_DB")
    if env:
        return Path(env), STORE_SOURCE_ENV
    return Path(DEFAULT_DB_PATH), STORE_SOURCE_DEFAULT


def resolve_store_path(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Path-only form of :func:`resolve_store`."""
    return resolve_store(explicit)[0]


def resolve_journal_dir(explicit: str | os.PathLike[str] | None = None) -> tuple[Path, str]:
    """Resolve the journal directory and its source (same precedence rule)."""
    if explicit is not None:
        return Path(explicit), JOURNAL_SOURCE_EXPLICIT
    env = os.environ.get("RESEXTRACT_JOURNAL_DIR")
    if env:
        return Path(env), JOURNAL_SOURCE_ENV
    return Path("state/journal"), JOURNAL_SOURCE_DEFAULT


# --------------------------------------------------------------------------- #
# Data layer
# --------------------------------------------------------------------------- #


class DataLayer:
    """Read-only aggregation over store + journal + dockets + graph + doctor."""

    def __init__(
        self,
        store_path: str | os.PathLike[str] | None = None,
        journal_dir: str | os.PathLike[str] | None = None,
        dockets_dir: str | os.PathLike[str] | None = None,
        graph_path: str | os.PathLike[str] | None = None,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        doctor_ttl: float = 20.0,
        backlog_dirs: Iterable[str | os.PathLike[str]] | None = None,
    ) -> None:
        # U6.16: the ONE resolution boundary -- explicit > env var > default.
        self.store_path, self.store_source = resolve_store(store_path)
        self.journal_dir, self.journal_source = resolve_journal_dir(journal_dir)
        self.dockets_dir = Path(dockets_dir) if dockets_dir is not None else Path("dockets")
        self.graph_path = Path(graph_path) if graph_path is not None else DEFAULT_GRAPH_PATH
        self.max_bytes = int(max_bytes)
        self.doctor_ttl = float(doctor_ttl)
        # Explicit, opt-in extra backlog roots.  There is deliberately NO
        # ``cwd`` root any more (U6.8): see :meth:`refresh_backlog`.
        self.backlog_dirs = tuple(Path(d) for d in (backlog_dirs or ()))
        self._doctor_cache: dict[str, Any] | None = None
        self._doctor_at: float = 0.0
        self._graph_cache: tuple[tuple[str, int, int], dict[str, Any]] | None = None

    # -- plumbing ---------------------------------------------------------- #

    def resolution(self) -> dict[str, str]:
        """Report *which* store/journal this layer resolved to, and by which rule.

        U6.16: an isolation mechanism that half-works produces false containment
        claims, so the resolved path is observable here, on the instance, rather
        than inferred from behaviour.
        """
        return {
            "store_path": str(self.store_path),
            "store_source": self.store_source,
            "journal_dir": str(self.journal_dir),
            "journal_source": self.journal_source,
        }

    def _connect(self) -> tuple[sqlite3.Connection | None, str | None]:
        """Open the store read-only.  U6.18 boundary note (decision, with evidence).

        Why ``mode=ro`` and *not* ``immutable=1``/``nolock=1``: the store is a
        **WAL** database (header bytes 18/19 = ``2/2``, established from the
        header of a copy) and the pipeline writes it through
        ``store.connect()`` while a dashboard can be up, so readers and writers
        are concurrent **by design**.  Measured on throwaway copies
        (``tests/test_cli.py::test_readonly_open_*`` / ``::test_immutable_uri_*``,
        U6.18):

        * ``mode=ro`` creates ``<store>-wal``/``<store>-shm`` beside the store.
          That is a WAL reader's shared-memory bookkeeping, not a write to the
          database: the store's own bytes, sha256 and mtime are unchanged.  It
          cannot be suppressed safely while the store is WAL and concurrently
          written, so U6.18 records it as a **documented non-fix** (option d)
          rather than trading it for a torn read.
        * ``immutable=1`` *does* suppress the sidecars, but it asserts the file
          can never change: it does not consult the ``-wal`` at all.  With
          committed pages still in the WAL it answered ``no such table`` where
          ``mode=ro`` returned the rows -- silent data loss -- and it disables
          the change detection that would notice a checkpoint rewriting the
          file under the reader.  REJECTED as unsafe here.
        * ``nolock=1`` cannot open this database at all (``unable to open
          database file``).  Unusable, not merely risky.

        The real remedy belongs to the *writer* (``journal_mode=DELETE`` needs
        no reader sidecars, at the cost of the WAL's concurrent read/write
        capability); it is handed up, not applied, because ``state/state.sqlite``
        is read-only to this unit.
        """
        path = self.store_path
        if not path.is_file():
            return None, f"store not found: {path}"
        quoted = str(path).replace("?", "%3f").replace("#", "%23")
        try:
            con = sqlite3.connect(f"file:{quoted}?mode=ro", uri=True)
            con.row_factory = sqlite3.Row
            con.execute("SELECT 1 FROM sqlite_master LIMIT 1")
            return con, None
        except sqlite3.Error:
            pass
        # U6.18: this fallback used to be a plain read-WRITE open.  A layer whose
        # whole contract is read-only must not silently regain write access when
        # the URI form fails, so the fallback is made read-only at the SQL level
        # too -- the boundary's "read-only" claim now holds on every path.
        try:
            con = sqlite3.connect(str(path))
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA query_only=ON")
            con.execute("SELECT 1 FROM sqlite_master LIMIT 1")
            return con, None
        except sqlite3.Error as exc:  # pragma: no cover - defensive
            return None, f"cannot open store: {exc}"

    def _select(
        self, con: sqlite3.Connection, table: str, order: str = "id"
    ) -> tuple[list[dict[str, Any]], str | None]:
        try:
            rows = con.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
        except sqlite3.Error as exc:
            return [], f"table {table!r} unavailable: {exc}"
        out = []
        for row in rows:
            item = {}
            for key in row.keys():
                value = row[key]
                if key.endswith("_json") and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        pass
                item[key] = value
            out.append(item)
        return out, None

    def _bounded_sections(self) -> dict[str, Any]:
        con, err = self._connect()
        if con is None:
            return _err(err or "store unavailable", tables={})
        try:
            tables: dict[str, int] = {}
            problems: list[str] = []
            for table in TABLES:
                try:
                    tables[table] = int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                except sqlite3.Error as exc:
                    problems.append(f"table {table!r} unavailable: {exc}")
            return {"tables": tables, "table_errors": problems}
        finally:
            con.close()

    # -- runs -------------------------------------------------------------- #

    def runs_summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "generated_at": utcnow(),
            "runs": [],
            "count": 0,
            "journals": [],
            "degradations": [],
            "resume_point": None,
            "errors": [],
        }
        con, err = self._connect()
        runs: list[dict[str, Any]] = []
        if con is None:
            out["errors"].append(err or "store unavailable")
            out["error"] = err or "store unavailable"
        else:
            try:
                runs, sel_err = self._select(con, "runs", "id")
                if sel_err:
                    out["errors"].append(sel_err)
                    out["error"] = sel_err
            finally:
                con.close()

        files = _journal_files(self.journal_dir)
        journals: list[dict[str, Any]] = []
        for path in files:
            info: dict[str, Any] = {
                "run_id": path.stem,
                "path": str(path),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "mtime": _mtime_iso(path),
                "events": 0,
                "verify": {"ok": None, "first_bad_seq": None},
            }
            try:
                count = 0
                for _entry in journal_mod.read(path.stem, root=self.journal_dir):
                    count += 1
                    if count > 100000:  # bound absurd journals
                        break
                info["events"] = count
            except Exception as exc:  # noqa: BLE001 - unreadable journal is data
                info["read_error"] = f"{type(exc).__name__}: {exc}"
            try:
                ok, bad = journal_mod.verify(path.stem, root=self.journal_dir)
                info["verify"] = {"ok": bool(ok), "first_bad_seq": bad}
            except Exception as exc:  # noqa: BLE001
                info["verify"] = {"ok": False, "first_bad_seq": None, "error": str(exc)}
            journals.append(info)
        out["journals"] = journals

        for run in runs:
            match = _match_journal(run, files)
            entry = dict(run)
            entry["journal_file"] = str(match) if match else None
            entry["journal_present"] = bool(match)
            if match is not None:
                jinfo = next((j for j in journals if j["path"] == str(match)), None)
                if jinfo:
                    entry["journal_events"] = jinfo["events"]
                    entry["journal_verify"] = jinfo["verify"]
            out["runs"].append(entry)
        out["count"] = len(out["runs"])
        if not runs and not out["errors"]:
            out["note"] = "no runs recorded in the store"
        if out["errors"] and not runs:
            out["note"] = "store unreadable; runs cannot be listed"

        # degradations: honest signals, not guesses
        degradations: list[dict[str, Any]] = []
        for run in out["runs"]:
            status = str(run.get("status") or "")
            if status not in ("done", ""):
                degradations.append(
                    {
                        "kind": "run_not_done",
                        "run_id": run.get("id"),
                        "detail": f"status={status!r}, finished_at={run.get('finished_at')!r}",
                    }
                )
            if int(run.get("tokens_used") or 0) == 0:
                degradations.append(
                    {
                        "kind": "zero_tokens_recorded",
                        "run_id": run.get("id"),
                        "detail": "tokens_used=0 (replay/mock path or unrecorded accounting)",
                    }
                )
        for journal in journals:
            ok = journal["verify"].get("ok")
            if ok is False:
                degradations.append(
                    {
                        "kind": "journal_chain_broken",
                        "run_id": journal["run_id"],
                        "detail": f"verify={journal['verify']}",
                    }
                )
        for table, count_value in (
            ("search_health_failures", self._search_failures()),
        ):
            if count_value:
                degradations.append(
                    {"kind": table, "detail": f"{count_value} failed search row(s) in store"}
                )

        resume = None
        if journals:
            latest = journals[-1]
            try:
                last: dict[str, Any] | None = None
                end: dict[str, Any] | None = None
                for entry in journal_mod.read(latest["run_id"], root=self.journal_dir):
                    last = entry
                    if entry.get("kind") in ("run_end", "run.end"):
                        end = entry
                resume = {
                    "run_id": latest["run_id"],
                    "last_seq": (last or {}).get("seq"),
                    "last_kind": (last or {}).get("kind"),
                    "last_ts": (last or {}).get("ts"),
                    "run_end": end is not None,
                    "status": (end or {}).get("status"),
                    "resumed": (end or {}).get("resumed"),
                    "partial": (end or {}).get("partial"),
                    "note": (
                        "journal has run_end"
                        if end is not None
                        else "journal has no run_end: a resume point, not a finished run"
                    ),
                }
            except Exception as exc:  # noqa: BLE001
                resume = {"run_id": latest["run_id"], "error": f"{type(exc).__name__}: {exc}"}
        out["resume_point"] = resume
        out["degradations"] = degradations
        return out

    def _search_failures(self) -> int:
        con, err = self._connect()
        if con is None:
            return 0
        try:
            row = con.execute(
                "SELECT COUNT(*) FROM search_health WHERE ok = 0 OR error IS NOT NULL"
            ).fetchone()
            return int(row[0]) if row else 0
        except sqlite3.Error:
            return 0
        finally:
            con.close()

    # -- reasoning --------------------------------------------------------- #

    def _journal_path(self, run_id: str) -> Path:
        return Path(self.journal_dir) / f"{run_id}.jsonl"

    def reasoning_trace(self, run_id: str | None = None, limit: int = DEFAULT_EVENT_LIMIT) -> dict[str, Any]:
        files = _journal_files(Path(self.journal_dir))
        target: Path | None = None
        if run_id:
            wanted = journal_mod.safe_run_id(run_id)
            candidate = self._journal_path(wanted)
            target = candidate if candidate.is_file() else None
        elif files:
            target = files[-1]
        if target is None:
            return _err(
                f"no journal found for run_id={run_id!r}" if run_id else "no journal files on disk",
                journal_dir=str(self.journal_dir),
                journals=[p.stem for p in files],
                events=[],
                count=0,
                reasoning_text_available=False,
                note=REASONING_GAP_NOTE,
            )

        events: list[dict[str, Any]] = []
        fields: Counter[str] = Counter()
        total = 0
        truncated = False
        used_bytes = 0
        try:
            for entry in journal_mod.read(target.stem, root=self.journal_dir):
                total += 1
                used_bytes += len(json.dumps(entry))
                payload = {k: v for k, v in entry.items() if k not in RESERVED_JOURNAL_KEYS}
                fields.update(payload.keys())
                events.append(
                    {
                        "seq": entry.get("seq"),
                        "ts": entry.get("ts"),
                        "kind": entry.get("kind"),
                        "prev": entry.get("prev"),
                        "hash": entry.get("hash"),
                        "payload": payload,
                    }
                )
                if used_bytes > self.max_bytes:
                    truncated = True
                    break
        except Exception as exc:  # noqa: BLE001
            if not events:
                return _err(
                    f"cannot read journal {target.name}: {type(exc).__name__}: {exc}",
                    journal_path=str(target),
                    events=[],
                    count=0,
                    reasoning_text_available=False,
                    note=REASONING_GAP_NOTE,
                )

        events.sort(key=lambda e: (e["seq"] is None, e["seq"]))
        if limit is not None and limit > 0 and len(events) > limit:
            events = events[-limit:]
            truncated = True

        fields_present = sorted(fields)
        reasoning_text = "reasoning_content" in fields
        try:
            ok, bad = journal_mod.verify(target.stem, root=self.journal_dir)
            verify: dict[str, Any] = {"ok": bool(ok), "first_bad_seq": bad}
        except Exception as exc:  # noqa: BLE001
            verify = {"ok": False, "first_bad_seq": None, "error": str(exc)}

        reasoning_tokens = [
            e["payload"].get("reasoning_tokens")
            for e in events
            if "reasoning_tokens" in e["payload"]
        ]
        return {
            "run_id": target.stem,
            "journal_path": str(target),
            "journal_present": True,
            "events": events,
            "count": len(events),
            "total_events": total,
            "truncated": truncated,
            "limit": limit,
            "bytes_cap": self.max_bytes,
            "verify": verify,
            "fields_present": fields_present,
            "reasoning_text_available": reasoning_text,
            "reasoning_text_field": "reasoning_content" if reasoning_text else None,
            "reasoning_tokens_recorded": "reasoning_tokens" in fields,
            "reasoning_tokens_seen": reasoning_tokens,
            "note": (
                "reasoning_content text is present in the journal"
                if reasoning_text
                else REASONING_GAP_NOTE
            ),
        }

    # -- findings ---------------------------------------------------------- #

    def _journal_rejections(self) -> tuple[list[dict[str, Any]], str | None]:
        rejected: list[dict[str, Any]] = []
        try:
            for path in _journal_files(Path(self.journal_dir)):
                used = 0
                for entry in journal_mod.read(path.stem, root=self.journal_dir):
                    used += 1
                    if used > 20000:
                        break
                    if entry.get("kind") in ("candidate_rejected", "candidate.rejected"):
                        payload = {
                            k: v for k, v in entry.items() if k not in RESERVED_JOURNAL_KEYS
                        }
                        rejected.append(
                            {
                                "run_id": path.stem,
                                "seq": entry.get("seq"),
                                "ts": entry.get("ts"),
                                "reason": payload.get("reason"),
                                "title": payload.get("title"),
                                "query": payload.get("query"),
                                "refs": payload.get("refs"),
                                "failed": payload.get("failed"),
                            }
                        )
        except Exception as exc:  # noqa: BLE001
            return rejected, f"journal rejection scan failed: {type(exc).__name__}: {exc}"
        return rejected, None

    def findings(self) -> dict[str, Any]:
        con, err = self._connect()
        if con is None:
            return _err(err or "store unavailable", counts={"candidates": 0, "claims": 0})
        try:
            candidates, c_err = self._select(con, "candidates", "id")
            claims, cl_err = self._select(con, "claims", "id")
            evidence, e_err = self._select(con, "evidence", "id")
            verdicts, v_err = self._select(con, "verdicts", "id")
        finally:
            con.close()
        for problem in (c_err, cl_err, e_err, v_err):
            if problem:
                return _err(problem, counts={"candidates": len(candidates), "claims": len(claims)})

        by_claim: dict[Any, list[dict[str, Any]]] = {}
        for item in evidence:
            by_claim.setdefault(item.get("claim_id"), []).append(item)
        verdict_by_claim: dict[Any, dict[str, Any]] = {}
        for item in verdicts:
            verdict_by_claim.setdefault(item.get("claim_id"), item)
        claims_by_candidate: dict[Any, list[dict[str, Any]]] = {}
        for claim in claims:
            enriched = dict(claim)
            enriched["evidence"] = by_claim.get(claim.get("id"), [])
            enriched["verdict"] = verdict_by_claim.get(claim.get("id"))
            claims_by_candidate.setdefault(claim.get("candidate_id"), []).append(enriched)

        accepted: list[dict[str, Any]] = []
        rejected_store: list[dict[str, Any]] = []
        for candidate in candidates:
            enriched = dict(candidate)
            enriched["claims"] = claims_by_candidate.get(candidate.get("id"), [])
            state = str(candidate.get("state") or "").lower()
            if state in REJECTED_STATES:
                enriched["rejection_reason"] = (
                    candidate.get("summary") or "state marked rejected in store; no reason recorded"
                )
                rejected_store.append(enriched)
            else:
                accepted.append(enriched)

        journal_rejected, j_err = self._journal_rejections()
        reasons = Counter(
            str(item.get("reason") or "<no reason recorded>")
            for item in rejected_store + journal_rejected
        )
        counts = {
            "candidates": len(candidates),
            "candidates_accepted": len(accepted),
            "candidates_rejected": len(rejected_store) + len(journal_rejected),
            "candidates_rejected_in_store": len(rejected_store),
            "candidates_rejected_in_journal": len(journal_rejected),
            "claims": len(claims),
            "evidence": len(evidence),
            "verdicts": len(verdicts),
        }
        out: dict[str, Any] = {
            "generated_at": utcnow(),
            "counts": counts,
            "candidates": accepted,
            "rejected": rejected_store + journal_rejected,
            "rejected_reasons": dict(sorted(reasons.items())),
            "verdict_vocabulary": ["CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED"],
        }
        if j_err:
            out["errors"] = [j_err]
        if not candidates:
            out["note"] = "no candidates recorded in the store"
        return out

    # -- dockets ----------------------------------------------------------- #

    def _iter_docket_dirs(self) -> list[Path]:
        root = Path(self.dockets_dir)
        if not root.is_dir():
            return []
        found: list[Path] = []
        for depth in ("*", "*/*"):
            try:
                found.extend(sorted(p.parent for p in root.glob(f"{depth}/MANIFEST.json")))
            except OSError:  # pragma: no cover
                continue
        return found

    def _docket_files(self, directory: Path) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        root = Path(self.dockets_dir)
        try:
            entries = sorted(p for p in directory.rglob("*") if p.is_file())
        except OSError:
            return files
        for path in entries[:500]:
            # Per-file realpath containment (GUARD-B): the docket *directory*
            # was contained, but a file symlink inside an accepted docket still
            # follows its target here.  An entry that resolves outside the
            # dockets root — directly, or through a symlinked directory — is
            # excluded from the listing rather than disclosed.
            if _contained_realpath(path, root) is None:
                continue
            try:
                files.append(
                    {
                        "path": str(path.relative_to(directory)),
                        "bytes": path.stat().st_size,
                    }
                )
            except (OSError, ValueError):
                continue
        return files

    def _store_docket_snapshots(self) -> list[tuple[list[str], dict[str, Any]]]:
        """U6.20: the ``dockets.manifest_json`` rows, parsed, as (slug keys, snapshot).

        Why this is a *fallback* and never the source of truth: ``manifest_json``
        is a snapshot taken when the row was inserted or refreshed.  A re-render
        that repairs the artifact -- a descriptive ``lane.title``, the evidence
        lists, ``generated_by.producer`` -- leaves the row exactly as it was, so
        a surface that reads the row reports the damaged, pre-re-render metadata
        (the slug standing in for the title, no evidence) for a docket whose
        on-disk manifest is correct.  The artifact is what the pipeline
        produced, what ``verify_docket`` validates and what an operator can
        read; the row is a cache.

        Read through the layer's usual ``mode=ro`` connection (never
        ``immutable=1``: this is a WAL store and ``immutable=1`` does not
        consult the ``-wal`` -- see :meth:`_connect`).  A row whose snapshot
        will not parse is dropped rather than guessed at.  Nothing is written.
        """
        con, _err_text = self._connect()
        if con is None:
            return []
        try:
            rows, _sel_err = self._select(con, "dockets", "id")
        except sqlite3.Error:  # pragma: no cover - defensive
            return []
        finally:
            con.close()
        out: list[tuple[list[str], dict[str, Any]]] = []
        for row in rows:
            snapshot = row.get("manifest_json")
            if not isinstance(snapshot, dict):
                continue
            candidates = _store_dir_slug_candidates(row.get("dir"))
            if candidates:
                out.append((candidates, snapshot))
        return out

    @staticmethod
    def _snapshot_metadata(snapshot: dict[str, Any]) -> dict[str, Any]:
        """Flatten a store snapshot to the fields the board publishes."""
        lane = snapshot.get("lane") if isinstance(snapshot.get("lane"), dict) else {}
        claims = snapshot.get("claims") if isinstance(snapshot.get("claims"), list) else []
        evidence = 0
        for claim in claims:
            if isinstance(claim, dict) and isinstance(claim.get("evidence"), list):
                evidence += len(claim["evidence"])
        freshness = (
            snapshot.get("freshness") if isinstance(snapshot.get("freshness"), dict) else {}
        )
        return {
            "lane_title": lane.get("title"),
            "lane_slug": lane.get("slug"),
            "claims": len(claims),
            "evidence": evidence,
            "generated_by": snapshot.get("generated_by"),
            "verified_at": freshness.get("verified_at"),
            "store_status": snapshot.get("status"),
        }

    @staticmethod
    def _snapshot_for(
        snapshots: list[tuple[list[str], dict[str, Any]]], slug: str
    ) -> dict[str, Any] | None:
        for candidates, snapshot in snapshots:
            if slug in candidates:
                return snapshot
        return None

    def dockets(self) -> dict[str, Any]:
        root = Path(self.dockets_dir)
        if not root.is_dir():
            return {
                "generated_at": utcnow(),
                "root": str(root),
                "count": 0,
                "dockets": [],
                "note": "no dockets directory on disk",
            }
        # U6.20: the store rows are read once per board read and used ONLY as
        # a fallback (a directory whose MANIFEST.json is absent/unreadable).
        snapshots = self._store_docket_snapshots()
        out: list[dict[str, Any]] = []
        for directory in self._iter_docket_dirs():
            try:
                slug = str(directory.relative_to(root)).replace(os.sep, "/")
            except ValueError:  # pragma: no cover
                slug = directory.name
            route_slug = safe_docket_slug(slug, root)
            if route_slug is None:
                # a docket directory that resolves outside the dockets root (a
                # symlinked docket) is excluded from the board entirely: nothing
                # about an escaped directory is listed or served.
                continue
            entry: dict[str, Any] = {
                "slug": slug,
                "route_slug": route_slug,
                "dir": str(directory),
                "status": None,
                "type": None,
                "lane": None,
                "lane_title": None,
                "title": None,
                "evidence": 0,
                "source": None,
                "target": None,
                "freshness": {"state": None, "age_days": None, "verified_at": None},
                "claims": 0,
                "material": 0,
                "material_bytes": 0,
                "web_sources": 0,
                "open_questions": [],
                "rework_open": [],
                "files": self._docket_files(directory),
                "verify": {"ok": None, "problems": []},
                "error": None,
            }
            if verify_docket is not None:
                try:
                    result = verify_docket(str(directory))
                    entry["verify"] = result.to_dict()
                except Exception as exc:  # noqa: BLE001
                    entry["verify"] = {
                        "ok": False,
                        "problems": [f"verify raised {type(exc).__name__}: {exc}"],
                        "claims": 0,
                        "material": 0,
                    }
            try:
                manifest = read_manifest(directory)  # type: ignore[misc]
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"MANIFEST.json unreadable: {type(exc).__name__}: {exc}"
                entry["status"] = "unreadable"
                # U6.20: the artifact cannot be read, so the store snapshot is
                # the only metadata left.  It IS served -- and ``source`` says
                # so.  ``status``/``error`` still report the unreadable
                # artifact, so a stale row can never pass itself off as fresh.
                snapshot = self._snapshot_for(snapshots, slug)
                if snapshot is not None:
                    metadata = self._snapshot_metadata(snapshot)
                    entry.update(
                        {
                            "lane_title": metadata["lane_title"],
                            "evidence": metadata["evidence"],
                            "claims": metadata["claims"],
                            "generated_by": metadata["generated_by"],
                            "store_status": metadata["store_status"],
                            "source": "store",
                        }
                    )
                    entry["title"] = metadata["lane_title"] or entry["lane"] or slug
                out.append(entry)
                continue

            material = list(manifest.material)
            freshness = manifest.freshness
            age = freshness.age_days
            if age is None:
                age = _age_days(freshness.verified_at)
            entry.update(
                {
                    "status": manifest.status,
                    "type": manifest.lane.type,
                    "lane": manifest.lane.slug,
                    "thesis": manifest.lane.thesis,
                    "target": manifest.target.slug,
                    "freshness": {
                        "state": freshness.state,
                        "age_days": age,
                        "age_days_recorded": freshness.age_days,
                        "verified_at": freshness.verified_at,
                        "prior_art_checked_at": freshness.prior_art_checked_at,
                    },
                    "claims": len(manifest.claims),
                    "material": len(material),
                    "material_bytes": sum(int(item.bytes or 0) for item in material),
                    "web_sources": len(manifest.web_sources),
                    "open_questions": list(manifest.open_questions),
                    "rework_open": list(manifest.rework_open),
                    "generated_by": manifest.generated_by.model_dump(mode="json"),
                    "generated_at": manifest.generated_at,
                    "claim_verdicts": dict(
                        Counter(str(claim.verdict) for claim in manifest.claims)
                    ),
                    # U6.20: ``lane`` carries the manifest's ``lane.slug`` (normally
                    # the directory slug, but not always: ``dockets/_smoke``
                    # records ``duval-trace-integrity``).  ``lane_title``/``title``
                    # add the artifact's real title so no slug stands in for it,
                    # and ``evidence`` counts the artifact's evidence entries.
                    "lane_title": getattr(manifest.lane, "title", None),
                    "evidence": sum(
                        len(getattr(claim, "evidence", None) or [])
                        for claim in manifest.claims
                    ),
                    "source": "manifest",
                }
            )
            entry["title"] = entry["lane_title"] or entry["lane"]
            out.append(entry)
        # U6.20 (b): a store row whose docket directory exists but whose
        # MANIFEST.json is *absent* (so the glob above never saw it) is still
        # listed -- from the snapshot, with ``source="store"`` and an explicit
        # error naming the missing artifact.  The slug is validated and
        # contained through ``safe_docket_slug`` and must resolve to an
        # existing directory under the root, so no store row can name a path
        # outside the dockets root or resurrect a docket that is gone.
        seen = {str(item.get("slug")) for item in out}
        for candidates, snapshot in snapshots:
            resolved: str | None = None
            for candidate in candidates:
                safe_candidate = safe_docket_slug(candidate, root)
                if safe_candidate is None:
                    continue
                if safe_candidate in seen or root.joinpath(
                    *safe_candidate.split("/")
                ).is_dir():
                    resolved = safe_candidate
                    break
            if resolved is None or resolved in seen:
                continue
            metadata = self._snapshot_metadata(snapshot)
            directory = root.joinpath(*resolved.split("/"))
            out.append(
                {
                    "slug": resolved,
                    "route_slug": resolved,
                    "dir": str(directory),
                    "status": "unreadable",
                    "type": None,
                    "lane": metadata["lane_slug"] or resolved.split("/")[-1],
                    "lane_title": metadata["lane_title"],
                    "title": metadata["lane_title"] or resolved.split("/")[-1],
                    "target": None,
                    "claims": metadata["claims"],
                    "evidence": metadata["evidence"],
                    "generated_by": metadata["generated_by"],
                    "freshness": {
                        "state": None,
                        "age_days": None,
                        "verified_at": metadata["verified_at"],
                    },
                    "store_status": metadata["store_status"],
                    "material": 0,
                    "material_bytes": 0,
                    "web_sources": 0,
                    "open_questions": [],
                    "rework_open": [],
                    "files": self._docket_files(directory),
                    # U6.23: two distinct states, never one.  ``verify.ok`` is
                    # ``None`` here because *no verification was run*: there is
                    # no MANIFEST.json to verify and this store-only listing
                    # path never calls ``verify_docket``.  That is NOT the same
                    # as the corrupt-but-present artifact handled above, where
                    # ``verify_docket`` *did* run and failed, so ``verify.ok`` is
                    # ``False``.  So: a store-sourced entry with no artifact
                    # reports ``None`` (did not run); a corrupt-but-present
                    # manifest reports ``False`` (ran and failed).
                    "verify": {
                        "ok": None,
                        "problems": ["no MANIFEST.json on disk: not verified"],
                    },
                    "error": (
                        "MANIFEST.json absent on disk: metadata served from the "
                        "store snapshot (source=store, possibly stale)"
                    ),
                    "source": "store",
                }
            )
            seen.add(resolved)
        return {
            "generated_at": utcnow(),
            "root": str(root),
            "count": len(out),
            "dockets": out,
            "note": None if out else "dockets directory exists but holds no MANIFEST.json",
        }

    def docket_detail(self, slug: str) -> dict[str, Any]:
        safe = safe_docket_slug(slug, self.dockets_dir)
        if safe is None:
            return _err(f"invalid docket slug: {slug!r}", slug=slug)
        root = Path(self.dockets_dir)
        directory = root.joinpath(*safe.split("/"))
        manifest_path = directory / "MANIFEST.json"
        if not manifest_path.is_file():
            return _err(f"docket not found: {safe!r}", slug=safe, root=str(root))
        # The directory guard proved the docket *directory* did not escape; the
        # manifest is contained again per file, because it may itself be a
        # symlink out of the root (MANIFEST.json is the one file always read).
        if _contained_realpath(manifest_path, root) is None:
            return _err(
                f"MANIFEST.json resolves outside the dockets root: {safe!r}",
                slug=safe,
                dir=str(directory),
            )
        try:
            manifest = read_manifest(directory)  # type: ignore[misc]
            manifest_json: Any = manifest.model_dump(mode="json", by_alias=True)
        except Exception as exc:  # noqa: BLE001
            return _err(
                f"MANIFEST.json unreadable: {type(exc).__name__}: {exc}",
                slug=safe,
                dir=str(directory),
            )
        documents: list[dict[str, Any]] = []
        for name in HEADING_FILES:
            path = directory / name
            real = _contained_realpath(path, root)  # GUARD-A: per-file containment
            entry: dict[str, Any] = {
                "name": name,
                "present": False,
                "headings": [],
                "bytes": 0,
            }
            if real is None:
                # explicit refusal: never a 500, never a silent serve
                entry["error"] = f"refused: {name!r} resolves outside the dockets root"
                documents.append(entry)
                continue
            if not real.is_file():
                # broken symlink, or a symlink to a directory where a file is
                # expected: an explicit error, never a crash and never a serve
                if path.is_symlink():
                    entry["error"] = (
                        f"refused: {name!r} is a symlink that does not resolve "
                        "to a regular file"
                    )
                documents.append(entry)
                continue
            text, truncated, size, read_refusal = _read_text_capped_checked(
                real, real, self.max_bytes  # GUARD-B: fd identity after open
            )
            if read_refusal is not None:
                entry["error"] = read_refusal
                documents.append(entry)
                continue
            entry.update(
                {
                    "present": True,
                    "bytes": size,
                    "truncated": truncated,
                    "headings": _headings(text),
                }
            )
            documents.append(entry)
        verify: dict[str, Any] = {"ok": None, "problems": []}
        if verify_docket is not None:
            try:
                verify = verify_docket(str(directory)).to_dict()
            except Exception as exc:  # noqa: BLE001
                verify = {"ok": False, "problems": [f"verify raised {exc}"]}
        return {
            "slug": safe,
            "dir": str(directory),
            # U6.20: every field below is read from the artifact.
            "source": "manifest",
            "manifest": manifest_json,
            "documents": documents,
            "files": self._docket_files(directory),
            "verify": verify,
            "error": None,
        }

    # -- web health -------------------------------------------------------- #

    def web_research_health(self) -> dict[str, Any]:
        con, err = self._connect()
        if con is None:
            return _err(err or "store unavailable", search_health={}, web_sources={})
        try:
            health, h_err = self._select(con, "search_health", "id")
            sources, s_err = self._select(con, "web_sources", "url")
        finally:
            con.close()
        for problem in (h_err, s_err):
            if problem:
                return _err(problem)

        by_engine: Counter[str] = Counter()
        engines_ok: Counter[str] = Counter()
        engines_failed: Counter[str] = Counter()
        by_day: Counter[str] = Counter()
        day_failed: Counter[str] = Counter()
        for row in health:
            engine = str(row.get("engine") or "<none>")
            by_engine[engine] += 1
            ok = row.get("ok")
            failed = ok in (0, False) or bool(row.get("error"))
            (engines_failed if failed else engines_ok)[engine] += 1
            day = str(row.get("ts") or "")[:10] or "<undated>"
            by_day[day] += 1
            if failed:
                day_failed[day] += 1

        def _classify(source: dict[str, Any]) -> str:
            status = source.get("http_status")
            if source.get("failure_reason") or status is None or int(status) >= 400:
                return "gone"
            if 300 <= int(status) < 400:
                return "suspect"
            if not source.get("sha256"):
                return "suspect"
            return "current"

        states: Counter[str] = Counter()
        source_rows: list[dict[str, Any]] = []
        for source in sources:
            state = _classify(source)
            states[state] += 1
            row = dict(source)
            row["change_state"] = state
            source_rows.append(row)

        failed_rows = [
            {
                "ts": row.get("ts"),
                "engine": row.get("engine"),
                "query": row.get("query"),
                "error": row.get("error"),
                "result_count": row.get("result_count"),
            }
            for row in health
            if row.get("ok") in (0, False) or bool(row.get("error"))
        ]
        degraded = bool(failed_rows)
        if not health:
            note = (
                "no search-health rows recorded yet — the SearXNG degradation is not "
                "observable from the store; the live signal is the doctor's SearXNG leg "
                "(GET /api/doctor)"
            )
        elif degraded:
            note = f"{len(failed_rows)} failed search row(s) — SearXNG degraded for those engines"
        else:
            note = "all recorded searches returned without error"
        return {
            "generated_at": utcnow(),
            "search_health": {
                "total": len(health),
                "ok": len(health) - len(failed_rows),
                "failed": len(failed_rows),
                "by_engine": dict(sorted(by_engine.items())),
                "by_engine_ok": dict(sorted(engines_ok.items())),
                "by_engine_failed": dict(sorted(engines_failed.items())),
                "by_day": dict(sorted(by_day.items())),
                "by_day_failed": dict(sorted(day_failed.items())),
                "failures": failed_rows[:200],
                "rows": health[-200:],
            },
            "web_sources": {
                "total": len(sources),
                "changed": states.get("changed", 0),
                "gone": states.get("gone", 0),
                "suspect": states.get("suspect", 0),
                "current": states.get("current", 0),
                "rows": source_rows[-200:],
                "classification": {
                    "gone": "failure_reason set, http_status missing, or HTTP >= 400",
                    "suspect": "3xx, or a 2xx row with no sha256 to compare",
                    "changed": "reserved: sha256 differs from the freshly fetched copy (needs a re-fetch)",
                    "current": "2xx with a sha256 on record",
                },
            },
            "degraded": degraded,
            "note": note,
        }

    # -- graph ------------------------------------------------------------- #

    def graph_summary(self) -> dict[str, Any]:
        path = Path(self.graph_path)
        if not path.is_file():
            return _err(f"graph file not found: {path}", path=str(path))
        if graph_stats is None:  # pragma: no cover
            return _err("resextract.kg.graphify.graph_stats unavailable")
        try:
            stat = path.stat()
        except OSError as exc:
            return _err(f"cannot stat graph: {exc}", path=str(path))
        key = (str(path), int(stat.st_mtime_ns), int(stat.st_size))
        if self._graph_cache is not None and self._graph_cache[0] == key:
            return self._graph_cache[1]
        try:
            stats = graph_stats(path)
        except Exception as exc:  # noqa: BLE001
            return _err(
                f"graph_stats failed: {type(exc).__name__}: {exc}",
                path=str(path),
                bytes=stat.st_size,
            )
        payload = stats.as_dict() if hasattr(stats, "as_dict") else dict(stats)  # type: ignore[arg-type]
        payload.update(
            {
                "generated_at": utcnow(),
                "sha256": _sha256_stream(path),
                "mtime": _mtime_iso(path),
                "bytes": stat.st_size,
                "error": None,
            }
        )
        self._graph_cache = (key, payload)
        return payload

    # -- doctor ------------------------------------------------------------ #

    def doctor_status(self, *, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        if (
            not force
            and self._doctor_cache is not None
            and now - self._doctor_at < self.doctor_ttl
        ):
            return dict(self._doctor_cache)
        try:
            report = doctor_mod.run_doctor(force=force)
        except Exception as exc:  # noqa: BLE001 - never 500 on a probe
            report = {
                "ok": False,
                "exit_code": 2,
                "checked_at": utcnow(),
                "legs": [],
                "core_down": [],
                "optional_down": [],
                "error": f"run_doctor raised {type(exc).__name__}: {exc}",
            }
        legs = list(report.get("legs") or [])
        report = dict(report)
        report["legs"] = legs
        report["cached_at"] = utcnow()
        report["by_leg"] = {str(leg.get("leg")): leg for leg in legs}
        report["occamy"] = next(
            (leg for leg in legs if str(leg.get("leg", "")).lower() == "occamy"), None
        )
        self._doctor_cache = report
        self._doctor_at = now
        return dict(report)

    def doctor_snapshot(self) -> dict[str, Any] | None:
        """Non-probing view of the doctor for the SSE stream (may be ``None``)."""
        if self._doctor_cache is None:
            return None
        return {
            "checked_at": self._doctor_cache.get("checked_at"),
            "ok": self._doctor_cache.get("ok"),
            "core_down": self._doctor_cache.get("core_down"),
            "optional_down": self._doctor_cache.get("optional_down"),
        }

    # -- refresh backlog --------------------------------------------------- #

    def refresh_backlog(self) -> dict[str, Any]:
        con, err = self._connect()
        rework: list[dict[str, Any]] = []
        errors: list[str] = []
        if con is None:
            errors.append(err or "store unavailable")
        else:
            try:
                rework, sel_err = self._select(con, "rework", "id")
                if sel_err:
                    errors.append(sel_err)
            finally:
                con.close()

        docket_index: dict[int, str] = {}
        con2, _ = self._connect()
        if con2 is not None:
            try:
                rows, _e = self._select(con2, "dockets", "id")
                docket_index = {row.get("id"): row.get("dir") for row in rows}
            finally:
                con2.close()
        for row in rework:
            row["docket_dir"] = docket_index.get(row.get("docket_id"))

        files: list[dict[str, Any]] = []
        # Roots are EXPLICIT.  ``Path.cwd()`` used to be a second root here and
        # is DROPPED (U6.8): resolving BACKLOG_NAMES against the process working
        # directory made this the weakest read in the dashboard — a local writer
        # could drop a file *named* ``UPDATE_BACKLOG.md`` anywhere under the cwd
        # and have an arbitrary path read back through ``/api/refresh``, with no
        # relation to any docket, no slug validation and (before this unit) no
        # containment.  Every genuine backlog file in this repo lives *inside* a
        # dockets tree, which the recursive walk below already finds, so dropping
        # cwd breaks no legitimate read; a deployment that really keeps a backlog
        # outside the tree must now pass it explicitly via ``backlog_dirs``, and
        # each such root is contained exactly like the dockets root.
        roots: list[tuple[Path, bool]] = [(Path(self.dockets_dir), True)]
        roots += [(Path(d), False) for d in self.backlog_dirs]
        seen: set[Path] = set()
        for root, recursive in roots:
            if not root.exists():
                continue
            for name in BACKLOG_NAMES:
                candidates = list(root.rglob(name) if recursive else root.glob(name))
                for path in candidates:
                    if not path.is_file():
                        # a broken symlink, a symlink to a directory, a symlink
                        # loop, or a directory with the backlog name: disclose an
                        # explicit refusal, never a silent skip that reads as
                        # "no backlog file here"
                        files.append(
                            {
                                "path": str(path),
                                "present": False,
                                "bytes": 0,
                                "truncated": False,
                                "headings": [],
                                "error": (
                                    f"refused: {name!r} is not a regular file "
                                    "(broken symlink, directory, or unresolvable)"
                                ),
                            }
                        )
                        continue
                    real = _contained_realpath(path, root)  # GUARD-A: per-file containment
                    if real is None:
                        # explicit refusal payload naming the reason: the escape
                        # is disclosed as a refusal, never served and never dropped
                        # silently (a silent drop would read as "no data")
                        files.append(
                            {
                                "path": str(path),
                                "present": False,
                                "bytes": 0,
                                "truncated": False,
                                "headings": [],
                                "error": (
                                    f"refused: {name!r} resolves outside the docket "
                                    f"root {str(root)!r}"
                                ),
                            }
                        )
                        continue
                    if real in seen:
                        continue
                    seen.add(real)
                    text, truncated, size, refusal = _read_text_capped_checked(
                        path, real, self.max_bytes  # GUARD-B: fd identity after open
                    )
                    entry: dict[str, Any] = {
                        "path": str(path),
                        "present": refusal is None,
                        "bytes": size,
                        "truncated": truncated,
                        "headings": _headings(text),
                    }
                    if refusal is not None:
                        entry["error"] = refusal
                    files.append(entry)
        open_rows = [row for row in rework if not row.get("closed_at")]
        closed_rows = [row for row in rework if row.get("closed_at")]
        if not rework and not files:
            note = "none recorded yet: no rework rows in the store and no UPDATE_BACKLOG.md / WORK_SUGGESTIONS.md on disk"
        else:
            note = None
        return {
            "generated_at": utcnow(),
            "rework": rework,
            "open": open_rows,
            "closed": closed_rows,
            "count": len(rework),
            "open_count": len(open_rows),
            "files": files,
            "note": note,
            "errors": errors,
        }

    # -- status ------------------------------------------------------------ #

    def status(self) -> dict[str, Any]:
        con, err = self._connect()
        if con is None:
            return _err(err or "store unavailable", tables={})
        try:
            payload = status_json(con)
        except Exception as exc:  # noqa: BLE001
            return _err(f"status_json failed: {type(exc).__name__}: {exc}")
        finally:
            con.close()
        payload["generated_at"] = utcnow()
        payload["journals"] = [p.stem for p in _journal_files(Path(self.journal_dir))]
        payload["dockets_dir"] = str(self.dockets_dir)
        payload["error"] = None
        return payload


# --------------------------------------------------------------------------- #
# Module-level convenience API (default paths, matching the spec names)
# --------------------------------------------------------------------------- #

_DEFAULT_LAYER: DataLayer | None = None
# U6.16: the cache key is the *resolved* paths, so a changed
# RESEXTRACT_STATE_DB rebuilds the layer instead of silently reusing the old one.
_DEFAULT_LAYER_KEY: tuple[str, str] | None = None


def default_layer() -> DataLayer:
    """The process-wide layer, re-resolved when the env var changes."""
    global _DEFAULT_LAYER, _DEFAULT_LAYER_KEY
    key = (str(resolve_store_path()), str(resolve_journal_dir()[0]))
    if _DEFAULT_LAYER is None or _DEFAULT_LAYER_KEY != key:
        # No explicit store/journal: resolution must stay truthful ("env"/"default").
        _DEFAULT_LAYER = DataLayer(dockets_dir="dockets")
        _DEFAULT_LAYER_KEY = key
    return _DEFAULT_LAYER


def runs_summary() -> dict[str, Any]:
    return default_layer().runs_summary()


def reasoning_trace(run_id: str | None = None, limit: int = DEFAULT_EVENT_LIMIT) -> dict[str, Any]:
    return default_layer().reasoning_trace(run_id, limit)


def findings() -> dict[str, Any]:
    return default_layer().findings()


def dockets() -> dict[str, Any]:
    return default_layer().dockets()


def docket_detail(slug: str) -> dict[str, Any]:
    return default_layer().docket_detail(slug)


def web_research_health() -> dict[str, Any]:
    return default_layer().web_research_health()


def graph_summary() -> dict[str, Any]:
    return default_layer().graph_summary()


def doctor_status(*, force: bool = False) -> dict[str, Any]:
    return default_layer().doctor_status(force=force)


def refresh_backlog() -> dict[str, Any]:
    return default_layer().refresh_backlog()


__all__ = [
    "DataLayer",
    "DEFAULT_MAX_BYTES",
    "HEADING_FILES",
    "REASONING_GAP_NOTE",
    "default_layer",
    "docket_detail",
    "dockets",
    "doctor_status",
    "findings",
    "graph_summary",
    "reasoning_trace",
    "refresh_backlog",
    "runs_summary",
    "safe_slug",
    "safe_docket_slug",
    "web_research_health",
]
