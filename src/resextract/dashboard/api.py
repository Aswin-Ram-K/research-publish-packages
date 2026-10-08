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
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from resextract import doctor as doctor_mod
from resextract import journal as journal_mod
from resextract.store import TABLES, status_json, utcnow

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
    ) -> None:
        self.store_path = Path(store_path) if store_path is not None else Path("state/state.sqlite")
        self.journal_dir = Path(journal_dir) if journal_dir is not None else Path("state/journal")
        self.dockets_dir = Path(dockets_dir) if dockets_dir is not None else Path("dockets")
        self.graph_path = Path(graph_path) if graph_path is not None else DEFAULT_GRAPH_PATH
        self.max_bytes = int(max_bytes)
        self.doctor_ttl = float(doctor_ttl)
        self._doctor_cache: dict[str, Any] | None = None
        self._doctor_at: float = 0.0
        self._graph_cache: tuple[tuple[str, int, int], dict[str, Any]] | None = None

    # -- plumbing ---------------------------------------------------------- #

    def _connect(self) -> tuple[sqlite3.Connection | None, str | None]:
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
        try:
            con = sqlite3.connect(str(path))
            con.row_factory = sqlite3.Row
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
        try:
            entries = sorted(p for p in directory.rglob("*") if p.is_file())
        except OSError:
            return files
        for path in entries[:500]:
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
        out: list[dict[str, Any]] = []
        for directory in self._iter_docket_dirs():
            try:
                slug = str(directory.relative_to(root)).replace(os.sep, "/")
            except ValueError:  # pragma: no cover
                slug = directory.name
            entry: dict[str, Any] = {
                "slug": slug,
                "route_slug": slug if "/" not in slug else None,
                "dir": str(directory),
                "status": None,
                "type": None,
                "lane": None,
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
                }
            )
            out.append(entry)
        return {
            "generated_at": utcnow(),
            "root": str(root),
            "count": len(out),
            "dockets": out,
            "note": None if out else "dockets directory exists but holds no MANIFEST.json",
        }

    def docket_detail(self, slug: str) -> dict[str, Any]:
        safe = safe_slug(slug)
        if safe is None:
            return _err(f"invalid docket slug: {slug!r}", slug=slug)
        root = Path(self.dockets_dir)
        directory = root / safe
        if not (directory / "MANIFEST.json").is_file():
            return _err(f"docket not found: {safe!r}", slug=safe, root=str(root))
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
            if not path.is_file():
                documents.append({"name": name, "present": False, "headings": [], "bytes": 0})
                continue
            text, truncated, size = _read_text_capped(path, self.max_bytes)
            documents.append(
                {
                    "name": name,
                    "present": True,
                    "bytes": size,
                    "truncated": truncated,
                    "headings": _headings(text),
                }
            )
        verify: dict[str, Any] = {"ok": None, "problems": []}
        if verify_docket is not None:
            try:
                verify = verify_docket(str(directory)).to_dict()
            except Exception as exc:  # noqa: BLE001
                verify = {"ok": False, "problems": [f"verify raised {exc}"]}
        return {
            "slug": safe,
            "dir": str(directory),
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
            report = doctor_mod.run_doctor()
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
        roots: list[Path] = [Path(self.dockets_dir), Path.cwd()]
        seen: set[Path] = set()
        for root in roots:
            if not root.exists():
                continue
            for name in BACKLOG_NAMES:
                candidates = list(root.rglob(name)) if root != Path.cwd() else list(root.glob(name))
                for path in candidates:
                    try:
                        resolved = path.resolve()
                    except OSError:  # pragma: no cover
                        continue
                    if resolved in seen or not path.is_file():
                        continue
                    seen.add(resolved)
                    text, truncated, size = _read_text_capped(path, self.max_bytes)
                    files.append(
                        {
                            "path": str(path),
                            "bytes": size,
                            "truncated": truncated,
                            "headings": _headings(text),
                        }
                    )
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


def default_layer() -> DataLayer:
    global _DEFAULT_LAYER
    if _DEFAULT_LAYER is None:
        store = os.environ.get("RESEXTRACT_STATE_DB", "state/state.sqlite")
        journal = os.environ.get("RESEXTRACT_JOURNAL_DIR", "state/journal")
        _DEFAULT_LAYER = DataLayer(store, journal, "dockets")
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
    "web_research_health",
]
