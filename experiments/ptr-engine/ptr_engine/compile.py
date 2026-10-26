"""Compile a turn's material into a ``TurnIndex``.

Lifecycle: at turn end the host hands the turn's new material to
:func:`compile_turn`. Every body goes into the warmpool, and the index keeps one
**pointer line per item** -- the item id plus a short hash prefix, never the body.
At turn start the host sends the index and nothing else.

Determinism is a hard requirement, not a nicety: the same
``(material, revision, scope, block_size)`` must produce byte-identical index bytes
in every process. So the index carries no timestamp, no random id and no absolute
path -- sorting is by ``(kind, id)`` and the only bytes in a line are the text form,
the hash prefix and the body length. ``tests/test_determinism.py`` compiles the same
material in two processes under two *different* warmpool roots and compares digests.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence, Union

from .errors import (
    PtrDuplicateIdError,
    PtrMaterialError,
    PtrPointerError,
    PtrProjectionUngrantedError,
)
from .reference import REF_KINDS, Reference, ResourceRef, format as format_ref, parse
from .store import BodyStore, default_root

#: Enumerated views per kind. ``"*"`` is the fallback for kinds without an override.
#: A projection name not in the enumeration is refused (``PTR_PROJECTION_UNENUMERATED``).
DEFAULT_PROJECTIONS: Mapping[str, frozenset[str]] = {
    "*": frozenset({"full", "brief", "raw", "summary"}),
}

INDEX_MAGIC = "ptr-index/1"
HASH_PREFIX_LEN = 8


def projections_for(
    kind: str, projections: Optional[Mapping[str, Iterable[str]]] = None
) -> frozenset[str]:
    """The enumerated views for ``kind`` under this enumeration."""
    table = DEFAULT_PROJECTIONS if projections is None else projections
    if kind in table:
        return frozenset(table[kind])
    return frozenset(table.get("*", ()))


@dataclass(frozen=True)
class Entry:
    """One resolvable item: its position, its content identity, its annotations."""

    kind: str
    id: str
    ref: Reference
    text: str
    scope: str
    role: str
    count: int
    target: ResourceRef
    pointer: Optional[str] = None
    projection: Optional[str] = None
    regions: Mapping[str, ResourceRef] = field(default_factory=dict)

    @property
    def hash8(self) -> str:
        return self.target.digest[:HASH_PREFIX_LEN]

    @property
    def body_len(self) -> int:
        try:
            return self.target.size
        except AttributeError:  # pragma: no cover - size is stamped by compile
            return -1

    @property
    def line(self) -> str:
        return f"- {self.text} {self.hash8} {self.size}"

    # the size a fetch of this entry returns, stamped at compile time
    size: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "id": self.id,
            "text": self.text,
            "scope": self.scope,
            "role": self.role,
            "depth": 0 if self.role == "root" else 1,
            "hash8": self.hash8,
            "body_len": self.size,
            "pointer": self.pointer,
            "projection": self.projection,
        }


@dataclass(frozen=True)
class TurnIndex:
    """The compiled index: pointer lines plus the root entry, and its bytes."""

    scope: str
    revision: int
    block_size: int
    header: str
    lines: tuple[str, ...]
    entries: Mapping[tuple[str, str], Entry]
    targets: Mapping[tuple[str, str, Optional[str]], ResourceRef]
    index_bytes: bytes

    # -- convenience -------------------------------------------------------
    @property
    def index_text(self) -> str:
        return self.index_bytes.decode("utf-8")

    @property
    def index_sha256(self) -> str:
        return hashlib.sha256(self.index_bytes).hexdigest()

    @property
    def index_size(self) -> int:
        return len(self.index_bytes)

    def refs(self) -> tuple[Reference, ...]:
        return tuple(entry.ref for entry in self._sorted())

    def texts(self) -> tuple[str, ...]:
        return tuple(entry.text for entry in self._sorted())

    def root_entry(self) -> dict[str, Any]:
        return {
            "kind": "index",
            "id": self.scope,
            "role": "root",
            "scope": self.scope,
            "revision": self.revision,
            "text": self.header,
            "depth": 0,
            "body_len": len(self.header),
        }

    def entry_dicts(self) -> tuple[dict[str, Any], ...]:
        """Root first, then leaves in index order -- the residency hint carrier."""
        return (self.root_entry(),) + tuple(e.as_dict() for e in self._sorted())

    def entry_for(self, ref_or_text: Union[Reference, str]) -> Entry:
        text = format_ref(ref_or_text) if isinstance(ref_or_text, Reference) else ref_or_text
        key = _key(parse(text))
        if key not in self.entries:
            from .errors import PtrUnknownIdError

            raise PtrUnknownIdError(f"index enumerates no {text}", text=text)
        return self.entries[key]

    def _sorted(self) -> tuple[Entry, ...]:
        return tuple(self.entries[k] for k in sorted(self.entries))


def _key(ref: Reference) -> tuple[str, str]:
    return (ref.kind, ref.id)


def _select_pointer(value: Any, pointer: str) -> Any:
    """RFC 6901 selection over a parsed JSON value. Raises ``PTR_POINTER_INVALID``."""
    if pointer == "":
        return value
    current = value
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            if token == "-":
                raise PtrPointerError(
                    "'-' addresses the position after the last array element and "
                    "cannot be read",
                    pointer=pointer,
                )
            if not token.isdigit():
                raise PtrPointerError(
                    f"array index {token!r} is not a number", pointer=pointer
                )
            index = int(token)
            if index >= len(current):
                raise PtrPointerError(
                    f"array index {index} is out of range (len {len(current)})",
                    pointer=pointer,
                )
            current = current[index]
        elif isinstance(current, dict):
            if token not in current:
                raise PtrPointerError(
                    f"object has no key {token!r}", pointer=pointer, key=token
                )
            current = current[token]
        else:
            raise PtrPointerError(
                f"cannot descend into a {type(current).__name__}", pointer=pointer
            )
    return current


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _as_bytes(body: Any, item: Mapping[str, Any]) -> bytes:
    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    raise PtrMaterialError(
        f"material item body must be str or bytes, got {type(body).__name__}",
        kind=item.get("kind"),
        id=item.get("id"),
    )


def compile_turn(
    material: Sequence[Mapping[str, Any]],
    revision: int,
    scope: str,
    block_size: int = 64,
    *,
    store: Optional[BodyStore] = None,
    projections: Optional[Mapping[str, Iterable[str]]] = None,
) -> TurnIndex:
    """Compile one turn's material into index bytes plus content identities.

    ``material`` items are ``{kind, id, body, pointer?, projection?, ext?}``. The
    body is put into the store; the index keeps a line of the form
    ``- @kind:id[#pointer]@revision[?projection] <hash8> <len>``.
    """
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise PtrMaterialError(f"revision must be a non-negative int, got {revision!r}")
    if not isinstance(scope, str) or not scope:
        raise PtrMaterialError(f"scope must be a non-empty string, got {scope!r}")
    if not isinstance(block_size, int) or isinstance(block_size, bool) or block_size <= 0:
        raise PtrMaterialError(f"block_size must be a positive int, got {block_size!r}")
    if store is None:
        store = BodyStore(default_root())

    items: list[dict[str, Any]] = []
    for position, raw in enumerate(material):
        if not isinstance(raw, Mapping):
            raise PtrMaterialError(
                f"material[{position}] is not a mapping", got=type(raw).__name__
            )
        kind = raw.get("kind")
        ident = raw.get("id")
        if kind not in REF_KINDS:
            raise PtrMaterialError(
                f"material[{position}].kind {kind!r} is not an enumerated kind",
                position=position,
            )
        if not isinstance(ident, str) or not ident:
            raise PtrMaterialError(
                f"material[{position}].id must be a non-empty string", position=position
            )
        if "body" not in raw:
            raise PtrMaterialError(
                f"material[{position}] has no body", position=position, id=ident
            )
        projection = raw.get("projection")
        if projection is not None and projection not in projections_for(kind, projections):
            raise PtrProjectionUngrantedError(
                f"projection {projection!r} is not enumerated for kind {kind!r}; "
                f"enumerated: {sorted(projections_for(kind, projections))}",
                kind=kind,
                projection=projection,
            )
        items.append(
            {
                "kind": kind,
                "id": ident,
                "body": raw["body"],
                "pointer": raw.get("pointer"),
                "projection": projection,
                "ext": raw.get("ext", ".txt"),
            }
        )

    items.sort(key=lambda item: (item["kind"], item["id"]))
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (item["kind"], item["id"])
        if key in seen:
            raise PtrDuplicateIdError(
                f"two items claim {item['kind']}:{item['id']}", kind=key[0], id=key[1]
            )
        seen.add(key)

    entries: dict[tuple[str, str], Entry] = {}
    targets: dict[tuple[str, str, Optional[str]], ResourceRef] = {}
    lines: list[str] = []

    for item in items:
        body = _as_bytes(item["body"], item)
        whole_ref = store.put(body, ext=item["ext"], pin=f"rev:{revision}")
        pointer = item["pointer"]
        target = whole_ref
        regions: dict[str, ResourceRef] = {}
        size = len(body)
        if pointer is not None:
            if not isinstance(pointer, str):
                raise PtrPointerError(
                    f"pointer must be a string, got {type(pointer).__name__}",
                    id=item["id"],
                )
            try:
                parsed = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PtrPointerError(
                    f"body of {item['id']!r} is not JSON, so no pointer can select "
                    f"a region of it ({exc})",
                    id=item["id"],
                ) from exc
            selected = _select_pointer(parsed, pointer)
            region_bytes = _canonical(selected)
            region_ref = store.put(region_bytes, ext=".json", pin=f"rev:{revision}")
            regions[pointer] = region_ref
            target = region_ref
            size = len(region_bytes)

        ref = Reference(
            kind=item["kind"],
            id=item["id"],
            pointer=pointer,
            revision=revision,
            projection=item["projection"],
        )
        text = format_ref(ref)
        entry = Entry(
            kind=item["kind"],
            id=item["id"],
            ref=ref,
            text=text,
            scope=scope,
            role="leaf",
            count=len(entries),
            target=target,
            pointer=pointer,
            projection=item["projection"],
            regions=regions,
            size=size,
        )
        entries[(item["kind"], item["id"])] = entry
        targets[(item["kind"], item["id"], pointer)] = target
        lines.append(entry.line)

    header = (
        f"{INDEX_MAGIC} scope={scope} revision={revision} "
        f"block_size={block_size} entries={len(lines)}"
    )
    index_bytes = ("\n".join([header, *lines]) + "\n").encode("utf-8")
    return TurnIndex(
        scope=scope,
        revision=revision,
        block_size=block_size,
        header=header,
        lines=tuple(lines),
        entries=entries,
        targets=targets,
        index_bytes=index_bytes,
    )


__all__ = [
    "compile_turn",
    "Entry",
    "TurnIndex",
    "DEFAULT_PROJECTIONS",
    "INDEX_MAGIC",
    "projections_for",
]
