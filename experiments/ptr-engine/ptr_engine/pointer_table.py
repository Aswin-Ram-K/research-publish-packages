"""Pointer table: compact masking, deterministic fetch resolution.

This module is pure: no I/O, no network, no model calls.  The same inputs
always produce the same outputs and the same bytes.
"""
from __future__ import annotations
from .outcomes import NOT_FOUND, OK, SCOPE_UNGRANTED, STALE_OR_REVOKED
import hashlib
from .errors import PtrDuplicateIdError, PtrStoreMissError
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Tuple
from .quantise import token_len

class TokenizerUnavailable(RuntimeError):
    """Raised when no tokenizer can be resolved to count tokens."""
    pass


def make_ref(doc_id, revision) -> str:
    """Canonical pointer ref builder: ``{doc_id}@r{revision}``."""
    return f"{doc_id}@r{revision}"

def tokenizer_calls() -> int:
    """Total tokenizer invocations performed by this module's fetch path."""
    return _TOKENIZER_CALL_COUNT


def _reset_tokenizer_calls() -> None:  # test hook
    global _TOKENIZER_CALL_COUNT
    _TOKENIZER_CALL_COUNT = 0


def _clear_truncation_cache() -> None:  # test hook
    _TRUNCATION_CACHE.clear()

def reset_bodies(task_id=None) -> None:  # test hook / per-fixture reset
    """Clear stored bodies.  ``task_id=None`` clears all; otherwise only that fixture's."""
    if task_id is None:
        _BODIES.clear()
        return
    tid = str(task_id)
    for key in [k for k in list(_BODIES) if isinstance(k, tuple) and k[0] == tid]:
        del _BODIES[key]

# Body registry populated by ``mask_output`` so ``fetch`` can return the original
# bytes for a live pointer.  Pure lookup; never mutated by ``fetch``.
_BODIES: dict = {}
# Module-level accounting for tokenizer invocations performed by fetch truncation.
_TOKENIZER_CALL_COUNT: int = 0
_TRUNCATION_CACHE: dict = {}
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
    body_tokens_basis: str = "estimate:none"
    body: Optional[str] = None
    task_id: Optional[str] = None

@dataclass(frozen=True)
class FetchResult:
    ref: str
    outcome: str
    text: Optional[str]
    body_tokens: int
    truncated: bool
    tool_call_id: Optional[str] = None
    tokenizer_reused: bool = False
    tokenizer_cache_hit: bool = False
    reused: bool = False



def mask_output(
    text: str,
    *,
    logical_id: str,
    revision: int,
    since_turn: int,
    tokenizer,
    task_id=None,
) -> Tuple[str, PointerEntry]:
    body = "" if text is None else str(text)
    if tokenizer is None:
        raise TokenizerUnavailable("no tokenizer resolvable for body token count")
    tokens = int(token_len(body, tokenizer))
    basis = f"tokenizer:{type(tokenizer).__name__}"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    ref = make_ref(logical_id, revision)
    tid = None if task_id is None else str(task_id)
    entry = PointerEntry(
        ref=ref,
        logical_id=str(logical_id),
        revision=int(revision),
        since_turn=int(since_turn),
        body_tokens=int(tokens),
        digest=digest,
        state="live",
        body_tokens_basis=basis,
        body=body,
        task_id=tid,
    )
    _BODIES[(tid, ref)] = body
    marker = f"[MASKED {ref}]"
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
    tokenizer,
    tool_call_id=None,
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
        except (KeyError, TypeError):
            entry = None

    if entry is None:
        return FetchResult(ref=safe_ref, outcome=NOT_FOUND, text=None, body_tokens=0, truncated=False, tool_call_id=tool_call_id)

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
        return FetchResult(ref=safe_ref, outcome=outcome, text=None, body_tokens=0, truncated=False, tool_call_id=tool_call_id)

    body = None
    entry_body = getattr(entry, "body", None)
    if entry_body is None and isinstance(entry, Mapping):
        entry_body = entry.get("body", None)
    if entry_body is not None:
        body = entry_body
    else:
        _task_id_specified = task_id is not None
        if task_id is None:
            task_id = getattr(entry, "task_id", None)
            if isinstance(entry, Mapping):
                task_id = entry.get("task_id", task_id)
        tid = "" if task_id is None else str(task_id)
        key = (tid, safe_ref)
        if key in _BODIES:
            body = _BODIES[key]
        elif not _task_id_specified:
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
        else:
            raise PtrStoreMissError(
                f"no stored body for ref {safe_ref!r} (task_id={tid!r})"
            )
    if body is None:
        # no stored body: nothing to slice
        raise PtrStoreMissError(f"no stored body for ref {safe_ref!r}")
    # byte_range handling
    if byte_range is not None:
        if not isinstance(byte_range, (tuple, list)) or len(byte_range) != 2:
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False, tool_call_id=tool_call_id)
        try:
            start = int(byte_range[0])
            end = int(byte_range[1])
        except (TypeError, ValueError):
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False, tool_call_id=tool_call_id)
        if start < 0 or end < start or start > len(body) or end > len(body):
            return FetchResult(ref=safe_ref, outcome=SCOPE_UNGRANTED, text=None, body_tokens=0, truncated=False, tool_call_id=tool_call_id)
        text = body[start:end]
    else:
        text = body

    # budget truncation by tokens
    try:
        budget = int(budget_tokens)
    except (TypeError, ValueError):
        budget = 0
    if budget < 0:
        budget = 0
    truncated = False
    _reused = False
    if text is not None:
        if tokenizer is None:
            raise TokenizerUnavailable("no tokenizer resolvable for fetch")
        # Memoised truncation: at most one tokenizer call per distinct (body, budget).
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache_key = (digest, budget)
        cached = _TRUNCATION_CACHE.get(cache_key)
        _reused = cached is not None
        if cached is not None:
            text, truncated, _cached_tokens = cached
        else:
            global _TOKENIZER_CALL_COUNT
            _TOKENIZER_CALL_COUNT += 1
            total = int(token_len(text, tokenizer))
            if total <= budget or budget <= 0:
                if total <= budget:
                    new_text = text
                    new_truncated = False
                    new_tokens = total
                else:
                    new_text = ""
                    new_truncated = (text != "")
                    new_tokens = 0
            else:
                # Deterministic prefix selection (codepoint-safe slicing): one count
                # of the whole body, then a proportional prefix. No further counts.
                n = int(len(text) * budget / total)
                if n < 1:
                    n = 1
                if n >= len(text):
                    n = len(text) - 1
                    if n < 1:
                        n = 0
                new_text = text[:n]
                new_truncated = True
                # Upper bound on returned token count; exact count not re-measured.
                new_tokens = min(budget, total)
            _TRUNCATION_CACHE[cache_key] = (new_text, new_truncated, new_tokens)
            text, truncated, _cached_tokens = _TRUNCATION_CACHE[cache_key]
        # body_tokens from cached upper bound
        if text is None:
            result_tokens = 0
        elif not truncated:
            # non-truncated: count was measured (cached); reuse
            result_tokens = _TRUNCATION_CACHE[cache_key][2]
        else:
            result_tokens = _TRUNCATION_CACHE[cache_key][2]
    else:
        result_tokens = 0
    return FetchResult(ref=safe_ref, outcome=OK, text=text, body_tokens=result_tokens, truncated=truncated, tool_call_id=tool_call_id, tokenizer_reused=_reused, tokenizer_cache_hit=_reused, reused=_reused)


def verify(table: Mapping[str, PointerEntry], ref: str, body: str) -> bool:
    safe_ref = "" if ref is None else str(ref)
    if not isinstance(table, Mapping):
        table = {}
    entry = table.get(safe_ref) if hasattr(table, "get") else None
    if entry is None:
        try:
            entry = table[safe_ref]
        except (KeyError, TypeError):
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
    except (TypeError, ValueError):
        return False
