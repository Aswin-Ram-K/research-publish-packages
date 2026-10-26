"""Immutable, content-addressed state nodes for the context-cache experiment.

A :class:`StateNode` is the unit of context state.  Its ``node_id`` is the
sha256 of its canonical bytes, so identity *is* content: two nodes with the
same text and the same parent are the same node, and any change to the text
yields a different address.  There is deliberately no ``edit()`` method -- the
only way to change state is to create a new node on a new chain.

The private ``_parent`` field keeps the object graph (so :meth:`chain` can walk
to the root without a global registry) and is excluded from equality, repr and
hashing: two nodes are equal iff their content addresses are equal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

KINDS: frozenset[str] = frozenset({"invariant", "pointer", "delta", "summary", "fork"})


def canonical_bytes(obj: Any) -> bytes:
    """Stable JSON bytes for hashing: sorted keys, no whitespace, UTF-8."""

    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def digest(obj: Any) -> str:
    """sha256 hex of :func:`canonical_bytes`."""

    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


@dataclass(frozen=True)
class StateNode:
    """One immutable state node.  ``node_id`` is a content address."""

    node_id: str
    parent_id: str | None
    kind: str
    text: str
    meta: Mapping[str, Any] = field(default_factory=dict, compare=False)
    # Object-graph back-pointer used by chain(); not part of identity.
    _parent: "StateNode | None" = field(default=None, compare=False, repr=False)

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        text: str,
        kind: str,
        parent: "StateNode | None" = None,
        **meta: Any,
    ) -> "StateNode":
        """Create a node whose id is the hash of (kind, text, parent, meta)."""

        if not isinstance(text, str):
            raise TypeError("text must be a str")
        if kind not in KINDS:
            raise ValueError(f"unknown node kind {kind!r}; expected one of {sorted(KINDS)}")
        parent_id = parent.node_id if parent is not None else None
        meta_dict = dict(meta)
        node_id = digest(
            {
                "kind": kind,
                "text": text,
                "parent": parent_id,
                "meta": meta_dict,
            }
        )
        return cls(
            node_id=node_id,
            parent_id=parent_id,
            kind=kind,
            text=text,
            meta=meta_dict,
            _parent=parent,
        )

    # ------------------------------------------------------------------ #
    # Chain helpers
    # ------------------------------------------------------------------ #
    def chain(self) -> list["StateNode"]:
        """Return ``root..self`` order."""

        out: list[StateNode] = []
        node: StateNode | None = self
        seen: set[str] = set()
        while node is not None:
            if node.node_id in seen:  # pragma: no cover - defensive against cycles
                raise ValueError(f"cycle in node chain at {node.node_id}")
            seen.add(node.node_id)
            out.append(node)
            if node._parent is None and node.parent_id is not None:
                raise ValueError(
                    f"node {node.node_id} names parent {node.parent_id} but its "
                    "parent object is not attached; rebuild the chain with create()"
                )
            node = node._parent
        out.reverse()
        return out

    @property
    def chain_hash(self) -> str:
        """sha256 over ``[(node_id, kind), ...]`` in root..self order."""

        return digest([[n.node_id, n.kind] for n in self.chain()])

    # ------------------------------------------------------------------ #
    # Serialisation
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "kind": self.kind,
            "text": self.text,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "StateNode":
        """Rehydrate a node without its parent linkage (``_parent`` is None)."""

        return cls(
            node_id=str(data["node_id"]),
            parent_id=data.get("parent_id"),
            kind=str(data["kind"]),
            text=str(data["text"]),
            meta=dict(data.get("meta") or {}),
        )

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"StateNode({self.kind}, {self.node_id[:12]}, {len(self.text)} chars)"
