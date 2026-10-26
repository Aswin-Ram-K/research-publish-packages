"""Resolve a ``Reference`` to a ``ResourceRef`` -- the one-way bridge.

Resolution ends at a content hash. A resolved ``Reference`` yields a
``ResourceRef``; a ``ResourceRef`` cannot yield a ``Reference``, because content does
not know which namespace it was reached through, at which revision, or in which
view. There is deliberately **no** function anywhere in this package that goes the
other way, and ``tests/test_oneway.py`` asserts it by calling every public function
with a ``ResourceRef`` and checking that none returns a ``Reference``.

``resolve`` never returns a body. It returns the identity of the body, and the
caller asks the store. Selecting bytes inside the pointer type is what puts
selection inside a string parser; identity keeps the grant check at the boundary
where it belongs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Union

from .compile import TurnIndex, projections_for
from .errors import (
    PtrBudgetExceededError,
    PtrError,
    PtrNotAReferenceError,
    PtrPointerError,
    PtrProjectionUngrantedError,
    PtrRevisionError,
    PtrScopeUngrantedError,
    PtrUnknownIdError,
    PtrUnknownKindError,
)
from .ledger import Ledger
from .reference import REF_KINDS, Reference, ResourceRef, format as format_ref

#: Default per-turn resolve budget. Overridable per scope: the point of a budget is
#: that a host can make it small, and a runaway loop then fails by name instead of
#: quietly costing a context window.
DEFAULT_MAX_REFS = 64


@dataclass(frozen=True)
class Scope:
    """The capability scope a session presents on every resolve.

    It carries the index (which is what the session is allowed to name), the
    enumerated projections, the resolve budget and the block size. A scope is
    neither a user nor a token: it is the grant, and ``scope.name`` must equal the
    name the index was compiled under.
    """

    name: str
    index: TurnIndex
    projections: Optional[Mapping[str, Iterable[str]]] = None
    max_refs: int = DEFAULT_MAX_REFS
    block_size: Optional[int] = field(default=None)

    def block(self) -> int:
        """The cache block granularity this scope resolves against."""
        return self.block_size if self.block_size is not None else self.index.block_size

    def enumerated(self, kind: str) -> frozenset[str]:
        return projections_for(kind, self.projections)


def _refuse(ledger: Optional[Ledger], scope_name: str, text: str, error: PtrError) -> None:
    """Record the refusal before re-raising. A refusal is a measurement too."""
    if ledger is not None:
        ledger.record_refusal(
            scope=scope_name, serialized_ref=text, code=error.code
        )


def resolve(
    ref: Reference,
    scope: Scope,
    ledger: Optional[Ledger] = None,
) -> ResourceRef:
    """Resolve ``ref`` within ``scope``, recording exactly one ledger row.

    Raises a named error for every refusal; the refusal is recorded in the ledger
    first, with ``refs_refused=1``.
    """
    if not isinstance(ref, Reference):
        raise PtrNotAReferenceError(
            "resolve() takes a Reference; a ResourceRef is content identity and "
            f"cannot be resolved, got {type(ref).__name__}",
            got=type(ref).__name__,
        )
    if not isinstance(scope, Scope):
        raise PtrScopeUngrantedError(
            "resolve() takes a Scope; no capability was presented",
            got=type(scope).__name__,
        )

    presented = format_ref(ref)
    try:
        if scope.index.scope != scope.name:
            raise PtrScopeUngrantedError(
                f"this index was compiled under scope {scope.index.scope!r}, "
                f"the session presents {scope.name!r}",
                index_scope=scope.index.scope,
                presented=scope.name,
            )
        if ref.kind not in REF_KINDS:
            raise PtrUnknownKindError(f"unknown kind {ref.kind!r}", kind=ref.kind)

        entry = scope.index.entries.get((ref.kind, ref.id))
        if entry is None:
            raise PtrUnknownIdError(
                f"the index enumerates no {ref.kind}:{ref.id}",
                kind=ref.kind,
                id=ref.id,
                enumerated=sorted(f"{k}:{i}" for k, i in scope.index.entries),
            )

        if ref.revision is not None and ref.revision != scope.index.revision:
            raise PtrRevisionError(
                f"{presented} pins revision {ref.revision}; this index is "
                f"revision {scope.index.revision}",
                pinned=ref.revision,
                index_revision=scope.index.revision,
            )

        if ref.projection is not None and ref.projection not in scope.enumerated(ref.kind):
            raise PtrProjectionUngrantedError(
                f"projection {ref.projection!r} is not enumerated for kind "
                f"{ref.kind!r}; enumerated: {sorted(scope.enumerated(ref.kind))}",
                kind=ref.kind,
                projection=ref.projection,
            )

        if ref.pointer is not None and ref.pointer not in entry.regions:
            raise PtrPointerError(
                f"{ref.kind}:{ref.id} exposes no region at {ref.pointer!r}",
                kind=ref.kind,
                id=ref.id,
                pointer=ref.pointer,
            )

        if ledger is not None and ledger.resolved_count() >= scope.max_refs:
            raise PtrBudgetExceededError(
                f"resolve budget spent: {ledger.resolved_count()} of "
                f"{scope.max_refs} refs this turn",
                max_refs=scope.max_refs,
                resolved=ledger.resolved_count(),
            )

        target: ResourceRef = (
            entry.regions.get(ref.pointer, entry.target)
            if ref.pointer is not None
            else entry.target
        )
    except PtrError as error:
        _refuse(ledger, scope.name, presented, error)
        raise

    if ledger is not None:
        ledger.record_resolution(
            scope=scope.name,
            serialized_ref=presented,
            bytes_appended=len(presented.encode("utf-8")),
            block_size=scope.block(),
            entry_text=entry.text,
        )
    return target


__all__ = ["Scope", "resolve", "DEFAULT_MAX_REFS"]
