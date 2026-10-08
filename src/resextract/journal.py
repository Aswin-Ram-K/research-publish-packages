"""Append-only, hash-chained JSONL journal.

Layout: ``state/journal/<run_id>.jsonl`` (one file per run).  Each line is a
JSON object::

    {"seq": 1, "ts": "...Z", "kind": "run.start", ...fields,
     "prev": "<previous hash or ''>", "hash": "<sha256>"}

``hash`` is the sha256 of the canonical JSON of the entry *without* the
``hash`` key (sorted keys, compact separators).  ``verify()`` recomputes the
whole chain, so any edit, deletion or reordering of a line is detected and
reported with the first bad ``seq``.

Redaction runs before hashing: secret-named keys and secret-shaped values are
replaced with ``"<redacted>"`` and never reach disk.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DEFAULT_ROOT = Path("state/journal")
REDACTED = "<redacted>"

RESERVED_KEYS = frozenset({"seq", "ts", "kind", "prev", "hash"})

def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #

# Key names from the spec.  Boundaries avoid collateral damage on words such as
# "tokens_used" / "tokenizer" while still catching "api_key", "access_token",
# "client_secret", "Authorization", "db_password".
_SECRET_KEY_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:api[_-]?key|authorization|token|secret|password)(?![A-Za-z0-9])",
    re.IGNORECASE,
)

# Value shapes: provider-prefixed keys, and long base64-ish blobs.
# Pure lowercase hex of >=40 chars is *excluded* on purpose: sha256/sha1 digests
# are legitimate journal content and are not secrets.
_SECRET_VALUE_RE = re.compile(
    r"(?<![A-Za-z0-9_\-])sk-[A-Za-z0-9_\-]{8,}"
    r"|(?<![A-Za-z0-9_\-])okr_[A-Za-z0-9_\-]{8,}"
    r"|(?<![A-Za-z0-9+/=_\-])(?![0-9a-f]{40,}(?![A-Za-z0-9+/=_\-]))[A-Za-z0-9+/=_\-]{40,}"
    r"(?![A-Za-z0-9+/=_\-])"
)

_RUN_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def redact_text(text: str) -> str:
    """Replace secret-shaped substrings inside ``text``."""
    return _SECRET_VALUE_RE.sub(REDACTED, text)


def redact_value(key: str, value: Any) -> Any:
    """Redact ``value`` if its key names a secret, else redact secret-shaped text."""
    if _SECRET_KEY_RE.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {k: redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(key, item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact(fields: dict[str, Any]) -> dict[str, Any]:
    return {str(k): redact_value(str(k), v) for k, v in fields.items()}


# --------------------------------------------------------------------------- #
# Paths / canonical form
# --------------------------------------------------------------------------- #


def journal_root(root: str | os.PathLike[str] | None = None) -> Path:
    if root is not None:
        return Path(root)
    env = os.environ.get("RESEXTRACT_JOURNAL_DIR")
    return Path(env) if env else DEFAULT_ROOT


def safe_run_id(run_id: Any) -> str:
    cleaned = _RUN_ID_RE.sub("_", str(run_id)).strip("._")
    if not cleaned:
        raise ValueError("run_id must contain at least one safe character")
    return cleaned


def path_for(run_id: Any, root: str | os.PathLike[str] | None = None) -> Path:
    return journal_root(root) / f"{safe_run_id(run_id)}.jsonl"


def canonical(entry: dict[str, Any]) -> str:
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def entry_hash(entry_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(entry_without_hash).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Journal
# --------------------------------------------------------------------------- #


class Journal:
    """Append-only journal for a single run."""

    def __init__(self, run_id: Any, root: str | os.PathLike[str] | None = None) -> None:
        self.run_id = safe_run_id(run_id)
        self.root = journal_root(root)

    @property
    def path(self) -> Path:
        return self.root / f"{self.run_id}.jsonl"

    # -- write ------------------------------------------------------------- #

    def append(self, kind: str, **fields: Any) -> dict[str, Any]:
        """Append one entry; returns the entry as written (redacted + hashed)."""
        bad = RESERVED_KEYS.intersection(fields)
        if bad:
            raise ValueError(f"journal fields may not shadow reserved keys: {sorted(bad)}")
        entry: dict[str, Any] = {"seq": self._next_seq(), "ts": utcnow(), "kind": kind}
        entry.update(redact(fields))
        entry["prev"] = self._last_hash()
        entry["hash"] = entry_hash(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = canonical(entry) + "\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        return entry

    def _entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def _next_seq(self) -> int:
        entries = self._entries()
        return int(entries[-1]["seq"]) + 1 if entries else 1

    def _last_hash(self) -> str:
        entries = self._entries()
        return str(entries[-1]["hash"]) if entries else ""

    # -- read -------------------------------------------------------------- #

    def read(self, since_seq: int = 0) -> Iterator[dict[str, Any]]:
        """Stream entries with ``seq > since_seq`` in file order."""
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if int(entry.get("seq", 0)) > since_seq:
                    yield entry

    def verify(self) -> tuple[bool, int | None]:
        """Return ``(ok, first_bad_seq)``; ``first_bad_seq`` is None when ok."""
        if not self.path.exists():
            return False, None
        prev = ""
        expected = 1
        for entry in self.read():
            seq = entry.get("seq")
            body = {k: v for k, v in entry.items() if k != "hash"}
            if seq != expected:
                return False, seq if isinstance(seq, int) else expected
            if entry.get("prev") != prev:
                return False, seq
            if entry_hash(body) != entry.get("hash"):
                return False, seq
            prev = str(entry.get("hash"))
            expected += 1
        return True, None


# --------------------------------------------------------------------------- #
# Module-level convenience API
# --------------------------------------------------------------------------- #


def append(run_id: Any, kind: str, *, root: str | os.PathLike[str] | None = None, **fields: Any) -> dict[str, Any]:
    return Journal(run_id, root).append(kind, **fields)


def read(run_id: Any, since_seq: int = 0, *, root: str | os.PathLike[str] | None = None) -> Iterator[dict[str, Any]]:
    return Journal(run_id, root).read(since_seq)


def verify(run_id: Any, *, root: str | os.PathLike[str] | None = None) -> tuple[bool, int | None]:
    return Journal(run_id, root).verify()
