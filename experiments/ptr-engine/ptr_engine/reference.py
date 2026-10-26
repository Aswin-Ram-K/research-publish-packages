"""The two identities, and the text form that serializes one of them.

``ResourceRef`` is *content identity*: which bytes, verified. ``Reference`` is
*position*: which region of which namespace, at which revision, in which view.
They are not interchangeable, and the bridge between them has exactly one
direction -- see ``resolve.resolve``.

The text form ``@kind:id[#pointer][@revision][?projection]`` is a SERIALIZATION,
not the primitive. Prompts and logs carry the text; everything downstream carries
the object, so the syntax can change without rewriting the resolver.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .errors import PtrPointerError, PtrSyntaxError, PtrUnknownKindError

#: Enumerated kinds, taken from Duval ``src/reference.ts`` ``REF_KINDS`` (D-024).
REF_KINDS: tuple[str, ...] = (
    # D-024 kernel namespaces
    "task",
    "evidence",
    "execution",
    "capability",
    "policy",
    "decision",
    # D-024 module namespaces
    "artifact",
    "memory",
    "knowledge",
    "meta",
    "world",
    "hypothesis",
    # layer-model L3 compositions -- what a caller names, not namespaces
    "lease",
    "agent",
    "run",
    # the L1 primitive
    "state",
)

_ID_RE = re.compile(r"^[A-Za-z0-9_.\-/]+$")
_PROJECTION_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")
_POINTER_ESCAPE_RE = re.compile(r"~(?![01])")


@dataclass(frozen=True)
class ResourceRef:
    """Content identity: which bytes, verified.

    ``hash`` is ``sha256:<64 hex>``; ``locator`` is store-relative, so the warmpool
    can be moved without invalidating an index. ``pin`` is the caller's retention
    handle (a revision string here); it is metadata, never part of the key.
    """

    scheme: str
    locator: str
    hash: str
    pin: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.scheme, str) or not self.scheme:
            raise PtrSyntaxError("ResourceRef.scheme must be a non-empty string")
        if not isinstance(self.locator, str) or not self.locator:
            raise PtrSyntaxError("ResourceRef.locator must be a non-empty string")
        if not isinstance(self.hash, str) or not self.hash.startswith("sha256:"):
            raise PtrSyntaxError("ResourceRef.hash must be 'sha256:<hex>'")

    @property
    def digest(self) -> str:
        """The bare hex digest, without the algorithm prefix."""
        return self.hash.split(":", 1)[1]

    def as_dict(self) -> dict[str, str]:
        return {
            "scheme": self.scheme,
            "locator": self.locator,
            "hash": self.hash,
            "pin": self.pin,
        }


@dataclass(frozen=True)
class Reference:
    """Position: which region of which namespace, at which revision, in which view.

    ``revision`` absent means head; ``projection`` absent means the kind's default
    view; ``pointer`` absent means the whole body.
    """

    kind: str
    id: str
    pointer: Optional[str] = None
    revision: Optional[int] = None
    projection: Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind not in REF_KINDS:
            raise PtrUnknownKindError(f"unknown kind {self.kind!r}", kind=self.kind)
        if not isinstance(self.id, str) or not self.id:
            raise PtrSyntaxError("Reference.id must be a non-empty string")
        if self.revision is not None and (
            not isinstance(self.revision, int) or isinstance(self.revision, bool)
        ):
            raise PtrSyntaxError("Reference.revision must be an int")
        if self.pointer is not None:
            _validate_pointer(self.pointer)

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "id": self.id,
            "pointer": self.pointer,
            "revision": self.revision,
            "projection": self.projection,
        }


def _validate_pointer(pointer: str) -> None:
    """Validate RFC 6901 syntax. Selection is checked against a body at compile."""
    if pointer == "":
        return
    if not isinstance(pointer, str):
        raise PtrPointerError("pointer must be a string", pointer=repr(pointer))
    if not pointer.startswith("/"):
        raise PtrPointerError(
            "a JSON pointer must start with '/' (or be empty)", pointer=pointer
        )
    if _POINTER_ESCAPE_RE.search(pointer):
        raise PtrPointerError(
            "RFC 6901 escapes are '~0' and '~1'; any other '~' is invalid",
            pointer=pointer,
        )


def format(ref: Reference) -> str:  # noqa: A001 - the contract names it `format`
    """Serialize a ``Reference`` to the text form. Inverse of :func:`parse`."""
    if not isinstance(ref, Reference):
        raise PtrSyntaxError("format() takes a Reference, not a ResourceRef")
    out = f"@{ref.kind}:{ref.id}"
    if ref.pointer is not None:
        out += f"#{ref.pointer}"
    if ref.revision is not None:
        out += f"@{ref.revision}"
    if ref.projection is not None:
        out += f"?{ref.projection}"
    return out


def parse(text: str) -> Reference:
    """Parse the text form into a ``Reference``. Strict; raises named errors.

    The parse order is fixed by the grammar's own ambiguity: ``?`` first (nothing
    after it may be read as anything else), then the trailing ``@revision``
    (rightmost ``@``, because a pointer may legitimately contain ``@``), then
    ``#`` (first ``#``: a pointer may contain ``#`` in a key, a projection may not),
    then ``:`` (first ``:``: the id may contain ``:``, the kind may not).
    """
    if not isinstance(text, str):
        raise PtrSyntaxError("reference must be a string", got=type(text).__name__)
    if not text:
        raise PtrSyntaxError("reference is empty")
    if not text.startswith("@"):
        raise PtrSyntaxError(
            "the text form starts with '@', e.g. '@knowledge:k03'", input=text
        )
    rest = text[1:]
    if not rest:
        raise PtrSyntaxError("bare '@' is not a reference", input=text)

    projection: Optional[str] = None
    if "?" in rest:
        rest, projection = rest.split("?", 1)
        if not projection:
            raise PtrSyntaxError("empty projection after '?'", input=text)
        if not _PROJECTION_RE.match(projection):
            raise PtrSyntaxError(
                f"projection {projection!r} is not a plain view name", input=text
            )

    revision: Optional[int] = None
    if "@" in rest:
        rest, rev_text = rest.rsplit("@", 1)
        if not rev_text:
            raise PtrSyntaxError("empty revision after '@'", input=text)
        if not rev_text.isdigit():
            raise PtrSyntaxError(
                f"revision {rev_text!r} is not a non-negative integer", input=text
            )
        revision = int(rev_text)

    pointer: Optional[str] = None
    if "#" in rest:
        rest, pointer = rest.split("#", 1)
        _validate_pointer(pointer)

    if ":" not in rest:
        raise PtrSyntaxError(
            "missing ':' between kind and id, e.g. '@knowledge:k03'", input=text
        )
    kind, ident = rest.split(":", 1)
    if not kind:
        raise PtrSyntaxError("empty kind", input=text)
    if kind not in REF_KINDS:
        raise PtrUnknownKindError(
            f"unknown kind {kind!r}; known kinds: {', '.join(REF_KINDS)}",
            kind=kind,
            input=text,
        )
    if not ident:
        raise PtrSyntaxError("empty id", input=text)
    if not _ID_RE.match(ident):
        raise PtrSyntaxError(
            f"id {ident!r} contains characters outside [A-Za-z0-9_.-/]", input=text
        )
    return Reference(
        kind=kind, id=ident, pointer=pointer, revision=revision, projection=projection
    )


#: Spelled-out aliases, for callers that dislike shadowing the builtin.
format_reference = format
parse_reference = parse

__all__ = [
    "REF_KINDS",
    "Reference",
    "ResourceRef",
    "format",
    "parse",
    "format_reference",
    "parse_reference",
]
