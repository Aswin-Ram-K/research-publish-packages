"""The four annotations, each a small pure function.

An annotation is a *hint carried beside the index*, not a body. A host reads it to
decide residency (``depth``), grant (``scope``), payload size (``append_cost``) and
bookkeeping (``ledger_id``). Pure functions: same input, same output, in every
process, forever.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Union

from .errors import PtrAnnotationError
from .reference import Reference, format as format_ref

#: An index entry: 0 means "this line is the index itself" (hot, must be resident).
DEPTH_ROOT = 0
#: A body behind a pointer: 1 means "cold, resolve to bring it in".
DEPTH_LEAF = 1

_ROLE_DEPTH = {
    "root": DEPTH_ROOT,
    "index": DEPTH_ROOT,
    "leaf": DEPTH_LEAF,
    "body": DEPTH_LEAF,
}


def _field(entry: Any, name: str) -> Any:
    """Read a field from a dict or a dataclass-like entry, or raise."""
    if isinstance(entry, Mapping):
        if name not in entry:
            raise PtrAnnotationError(
                f"entry has no {name!r} field", entry_keys=sorted(map(str, entry.keys()))
            )
        return entry[name]
    if not hasattr(entry, name):
        raise PtrAnnotationError(
            f"entry has no {name!r} attribute", entry_type=type(entry).__name__
        )
    return getattr(entry, name)


def depth(entry: Any) -> int:
    """0 for a root index entry, 1 for a leaf body.

    A host uses this for residency: depth 0 is sent hot on every turn (it is a few
    bytes per item and it is what makes the rest addressable), depth 1 stays cold
    until a ``fetch`` asks for it.
    """
    role = _field(entry, "role")
    if role not in _ROLE_DEPTH:
        raise PtrAnnotationError(
            f"role {role!r} is not one of {sorted(_ROLE_DEPTH)}", role=role
        )
    return _ROLE_DEPTH[role]


def scope(entry: Any) -> str:
    """The capability scope that must be presented to resolve this entry."""
    value = _field(entry, "scope")
    if not isinstance(value, str) or not value:
        raise PtrAnnotationError(f"scope must be a non-empty string, got {value!r}")
    return value


def append_cost(
    serialized_ref: Union[str, Reference], block_size: int
) -> int:
    """``len(serialized_ref.encode()) % block_size``.

    Why this and not the length: a cache prefix advances in whole blocks. An append
    of L bytes lands on the grid only when ``L % block_size == 0``; otherwise the
    partial trailing block is rewritten on the next append, which is exactly the
    cache tail a pointer engine must not invalidate. The annotation is the offset
    from the grid, so a host picks payload sizes by making it 0.
    """
    if isinstance(serialized_ref, Reference):
        serialized_ref = format_ref(serialized_ref)
    if not isinstance(serialized_ref, str):
        raise PtrAnnotationError(
            "append_cost takes a serialized ref string or a Reference, got "
            f"{type(serialized_ref).__name__}"
        )
    if not isinstance(block_size, int) or isinstance(block_size, bool) or block_size <= 0:
        raise PtrAnnotationError(
            f"block_size must be a positive int, got {block_size!r}"
        )
    return len(serialized_ref.encode("utf-8")) % block_size


def ledger_id(scope_name: str, serialized_ref: str, seq: int) -> str:
    """The id under which a resolve is recorded. Deterministic, no clock, no uuid.

    Shape ``<scope>:<seq zero-padded to 4>:<12 hex chars>``. The suffix hashes the
    serialized ref so that two rows can be matched back to a ref by eye from a log,
    and so a test can assert the same resolve twice yields the same id.
    """
    if not isinstance(scope_name, str) or not scope_name:
        raise PtrAnnotationError("ledger_id needs a non-empty scope name")
    if not isinstance(serialized_ref, str) or not serialized_ref:
        raise PtrAnnotationError("ledger_id needs a non-empty serialized ref")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise PtrAnnotationError(f"seq must be a non-negative int, got {seq!r}")
    digest = hashlib.sha256(serialized_ref.encode("utf-8")).hexdigest()[:12]
    return f"{scope_name}:{seq:04d}:{digest}"


__all__ = [
    "DEPTH_ROOT",
    "DEPTH_LEAF",
    "depth",
    "scope",
    "append_cost",
    "ledger_id",
]
