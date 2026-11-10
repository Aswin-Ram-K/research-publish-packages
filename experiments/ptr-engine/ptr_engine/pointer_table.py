"""Pointer table: compact masking, deterministic fetch resolution.

This module is pure: no I/O, no network, no model calls.  The same inputs
always produce the same outputs and the same bytes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Tuple

from .errors import PtrDuplicateIdError, PtrStoreMissError
from .outcomes import NOT_FOUND, OK, SCOPE_UNGRANTED, STALE_OR_REVOKED
from .quantise import token_len


OUTCOMES: Tuple[str, ...] = (OK, NOT_FOUND, STALE_OR_REVOKED, SCOPE_UNGRANTED)


class DuplicateRefError(PtrDuplicateIdError, ValueError):
    """Raised by ``build_table`` when two entries share a ``ref``."""


@dataclass(frozen=True)
class PointerEntry:
    ref: str
    logical_id: str
    revision: int
    since_turn: int
    body_tokens: int
    digest: str
    state: str
    task_id: str = ""


@dataclass(frozen=True)
class FetchResult:
    ref: str
    outcome: str
    text: Optional[str]
    body_tokens: int
    truncated: bool


# Body registry populated by ``mask_output`` so ``fetch`` can return the original
# bytes for a live pointer.  Pure lookup; never mutated by ``fetch``.
_BODIES: dict = {}


def reset_bodies(task_id=None) -> None:
    """Clear stored bodies.  ``task_id=None`` clears all; otherwise only that fixture's."""
    global _BODIES
    if task_id is None:
        _BODIES.clear()
        return
    tid = str(task_id)
    for key in [k for k in list(_BODIES) if (k[0] if isinstance(k, tuple) else None) == tid]:
        del _BODIES[key]


def _fallback_tokens(text: str) -> int:
    return len(text.split()) if text else 0


def mask_output(
    text: str,
    *,
    logical_id: str,
    revision: int,
    since_turn: int,
    tokenizer=None,
    task_id=None,
) -> Tuple[str, PointerEntry]:
    body = "" if text is None else str(text)
    try:
        tokens = token_len(body, tokenizer)
    tool_call_id: Optional[str] = None
    tokenizer_reused: bool = False
    tokenizer_cache_hit: bool = False
    reused: bool = False
    tokenizer_reused: bool = False
    tokenizer_cache_hit: bool = False
    reused: bool = False
        tokens = _fallback_tokens(body)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    ref = f"{logical_id}@r{revision}"
    tid = "" if task_id is None else str(task_id)
    entry = PointerEntry(
        ref=ref,
        logical_id=str(logical_id),
        revision=int(revision),
        since_turn=int(since_turn),
        body_tokens=int(tokens),
        digest=digest,
        state="live",
        task_id=tid,
    )
    _BODIES[(tid, ref)] = body
    marker = (
        f"[ptr ref={ref} logical_id={logical_id} revision={revision} "
        f"since_turn={since_turn} digest={digest} body_tokens={tokens}]"
    )
    return marker, entry


def build_table(entries: Iterable[PointerEntry], *, task_id=None) -> dict:
    tid = None if task_id is None else str(task_id)
    result: dict = {}
    for entry in entries:
        if not isinstance(entry, PointerEntry):
            # tolerate dict-like inputs defensively
            ref = getattr(entry, "ref", None)
            if ref is None and isinstance(entry, Mapping):
                ref = entry.get("ref")
            if ref is None:
                raise ValueError("entry missing ref")
            if ref in result:
                raise DuplicateRefError(f"duplicate ref: {ref!r}")
            result[ref] = entry
            continue
        if tid is not None:
            import dataclasses
            entry = dataclasses.replace(entry, task_id=tid)
        if entry.ref in result:
            raise DuplicateRefError(f"duplicate ref: {entry.ref!r}")
        result[entry.ref] = entry
    # deterministic ordering by ref
    return {k: result[k] for k in sorted(result)}


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def fetch(
    table: Mapping[str, PointerEntry],
    ref: str,
    byte_range: Tuple[int, int] = None,
    *,
    budget_tokens: int,
    task_id=None,
) -> FetchResult:
    safe_ref = "" if ref is None else str(ref)
    # normalise table
    if not isinstance(table, Mapping):
        table = {}
    entry = table.get(safe_ref) if hasattr(table, "get") else None
    if entry is None and safe_ref in table:
        try:
            entry = table[safe_ref]
        except (KeyError, TypeError, AttributeError, IndexError):

    if entry is None:
        return FetchResult(ref=safe_ref, outcome=NOT_FOUND, text=None, body_tokens=0, truncated=False)

    state = getattr(entry, "state", None)
    if isinstance(entry, Mapping):
        state = entry.get("state", state)

    if state == "live":
        outcome = OK
    elif state in ("stale", "revoked"):
        outcome = STALE_OR_REVOKED
    elif state == "ungranted":
        outcome = SCOPE_UNGRANTED
    else:
        # unknown state treated as not found-ish; keep deterministic
        outcome = NOT_FOUND

    if outcome != OK:
        return FetchResult(ref=safe_ref, outcome=outcome, text=None, body_tokens=0, truncated=False)

    if task_id is None:
        task_id = getattr(entry, "task_id", None)
        if isinstance(entry, Mapping):
            task_id = entry.get("task_id", task_id)
    tid = "" if task_id is None else str(task_id)
    key = (tid, safe_ref)
    if key in _BODIES:
        body = _BODIES[key]
    else:
        candidates = [v for (t, r), v in _BODIES.items() if r == safe_ref]
        if len(candidates) == 1:
            body = candidates[0]
        elif len(candidates) == 0:
            raise PtrStoreMissError(
                f"no stored body for ref {safe_ref!r} (task_id={tid!r})"
            )
        else:
            raise PtrStoreMissError(
                f"ambiguous stored bodies for ref {safe_ref!r}; task_id required"
            )
    # byte_range handling
    if byte_range is not None:
        if not isinstance(byte_range, (tuple, list)) or len(byte_range) != 2:
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False)
        try:
            start = int(byte_range[0])
            end = int(byte_range[1])
        except (TypeError, ValueError):
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False)
        if start < 0 or end < start or start > len(body) or end > len(body):
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False)
        text = body[start:end]
    else:
        text = body

    # budget truncation
    try:
        budget = int(budget_tokens)
    except (TypeError, ValueError):
        budget = 0
    if budget < 0:
        budget = 0
    truncated = False
    if text is not None and len(text) > budget:
        text = text[:budget]
        truncated = True

    return FetchResult(ref=safe_ref, outcome=OK, text=text, body_tokens=len(text) if text is not None else 0, truncated=truncated)


def verify(table: Mapping[str, PointerEntry], ref: str, body: str) -> bool:
    safe_ref = "" if ref is None else str(ref)
    if not isinstance(table, Mapping):
        table = {}
    entry = table.get(safe_ref) if hasattr(table, "get") else None
    if entry is None:
        try:
            entry = table[safe_ref]
        except (KeyError, TypeError, AttributeError, IndexError):
            entry = None
    if entry is None:
        return False
    digest = getattr(entry, "digest", None)
    if isinstance(entry, Mapping):
        digest = entry.get("digest", digest)
    if digest is None:
        return False
    try:
        return hashlib.sha256(("" if body is None else str(body)).encode("utf-8")).hexdigest() == str(digest)
    except (TypeError, ValueError, AttributeError, UnicodeError):
        return False
