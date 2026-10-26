"""The host-facing seam. Two functions, and no third.

``build_prompt`` assembles the turn prompt from the index plus the bodies the model
actually asked for. ``fetch_tool_spec`` is the one tool the model may call.

The rule this module exists to enforce: **no prefetch**. ``build_prompt`` is handed
already-resolved bodies and nothing else. It cannot reach the store -- it has no
store parameter and never imports one for writing -- so a body that was not
explicitly resolved cannot appear in a prompt. Two hard checks make that structural
rather than aspirational:

* every ref handed to it must be enumerated in the index, and (when a ledger is
  given) must carry a successful resolve row -- otherwise ``PTR_UNRESOLVED_REF``;
* every body's sha256 must be the body that ref resolved to -- otherwise
  ``PTR_BODY_MISMATCH``, so "resolved" cannot be faked by passing the wrong bytes.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Optional, Union

from .compile import TurnIndex
from .errors import (
    PtrBodyMismatchError,
    PtrPointerError,
    PtrUnresolvedRefError,
)
from .ledger import Ledger
from .reference import Reference, format as format_ref, parse

INDEX_OPEN = "<ptr-index>"
INDEX_CLOSE = "</ptr-index>"
BODIES_OPEN = "<ptr-bodies>"
BODIES_CLOSE = "</ptr-bodies>"

#: The body wrapper is byte-counted, not line-counted: a body may contain anything.
BODY_TEMPLATE = '<ptr-body ref="{ref}" bytes="{size}">\n{body}\n</ptr-body>'

FETCH_TOOL: dict[str, Any] = {
    "name": "fetch",
    "description": (
        "Resolve one pointer reference listed in the index and return its body. "
        "The index line already tells you the size and the leading hash bits, so "
        "fetch only what you actually need to read."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ref": {
                "type": "string",
                "description": (
                    "A serialized reference copied from an index line, e.g. "
                    "'@knowledge:k03' or '@artifact:plan#/goal@2?brief'."
                ),
            }
        },
        "required": ["ref"],
        "additionalProperties": False,
    },
}


def _as_bytes(value: Union[bytes, bytearray, str]) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    raise PtrUnresolvedRefError(
        f"a resolved body must be bytes or str, got {type(value).__name__}"
    )


def build_prompt(
    index: TurnIndex,
    resolved_bodies: Mapping[Union[Reference, str], Union[bytes, str]],
    ledger: Optional[Ledger] = None,
) -> str:
    """Assemble the prompt: the index, then only the bodies explicitly resolved.

    With ``resolved_bodies`` empty the prompt is the index block alone -- the
    zero-resolution turn, which is the whole point of the engine.
    """
    if not isinstance(index, TurnIndex):
        raise PtrUnresolvedRefError(
            f"build_prompt takes a TurnIndex, got {type(index).__name__}"
        )

    prepared: list[tuple[str, bytes]] = []
    for key, value in resolved_bodies.items():
        ref = key if isinstance(key, Reference) else parse(key)
        entry = index.entries.get((ref.kind, ref.id))
        if entry is None:
            raise PtrUnresolvedRefError(
                f"{format_ref(ref)} is not enumerated in this index, so it was never "
                "resolved",
                ref=format_ref(ref),
            )
        if ref.pointer is not None and ref.pointer not in entry.regions:
            raise PtrPointerError(
                f"{format_ref(ref)} names no region of {ref.kind}:{ref.id}",
                ref=format_ref(ref),
                pointer=ref.pointer,
            )
        expected = entry.regions.get(ref.pointer, entry.target)
        if ledger is not None and not ledger.was_resolved(
            format_ref(ref), entry.text
        ):
            raise PtrUnresolvedRefError(
                f"{format_ref(ref)} has no successful resolve in the ledger; "
                "build_prompt will not materialise a body that was not resolved",
                ref=format_ref(ref),
            )
        body = _as_bytes(value)
        actual = "sha256:" + hashlib.sha256(body).hexdigest()
        if actual != expected.hash:
            raise PtrBodyMismatchError(
                f"bytes handed for {format_ref(ref)} hash to {actual}, that ref "
                f"resolves to {expected.hash}",
                ref=format_ref(ref),
                actual=actual,
                expected=expected.hash,
            )
        prepared.append((format_ref(ref), body))

    prepared.sort(key=lambda pair: pair[0])

    parts = [INDEX_OPEN, index.index_text.rstrip("\n"), INDEX_CLOSE]
    if prepared:
        parts.append(BODIES_OPEN)
        for ref_text, body in prepared:
            parts.append(
                BODY_TEMPLATE.format(
                    ref=ref_text,
                    size=len(body),
                    body=body.decode("utf-8", errors="replace"),
                )
            )
        parts.append(BODIES_CLOSE)
    return "\n".join(parts) + "\n"


def fetch_tool_spec() -> dict[str, Any]:
    """The single tool the model may call: ``fetch(ref)``.

    A copy, so a host that mutates the spec cannot change what the engine documents.
    """
    import copy

    return copy.deepcopy(FETCH_TOOL)


__all__ = ["build_prompt", "fetch_tool_spec", "FETCH_TOOL"]
