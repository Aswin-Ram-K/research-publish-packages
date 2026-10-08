"""Provenance verification — the honesty mechanism of the miner.

A miner that trusts the model's citations is worthless: the model will happily
invent a node id or a line span that does not exist.  This module is the
independent check.  Every reference a candidate cites is resolved against two
authorities and nothing else:

* ``graph_node``  — the id must be present in the **loaded graph** (``by_id()``).
* ``file_lines``  — ``path#L<start>-L<end>`` must name a file that really lives
  *inside* ``target_root`` (realpath containment) with a span inside the file's
  real line count.
* ``doc_section`` — the file must exist inside ``target_root``; when a heading
  is supplied it must actually occur in the file.

Nothing here ever raises: an unreadable file, a hostile path or a nonsensical
reference all come back as ``Provenance(exists=False, ...)``.  The caller
decides what to do with a failed verification; the miner's policy is that a
candidate with **zero** verified references is thrown away.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from ..kg import Graph

__all__ = [
    "MALFORMED_KIND",
    "PROVENANCE_KINDS",
    "Provenance",
    "ProvenanceVerdict",
    "parse_ref",
    "verify_provenance",
]

# The closed vocabulary of provenance kinds.
PROVENANCE_KINDS: tuple[str, ...] = ("graph_node", "file_lines", "doc_section")

# A reference whose kind cannot even be inferred is reported as this kind so the
# ``kind`` field always stays inside the closed vocabulary.  ``detail`` says
# "malformed" — that is the field callers should look at.
MALFORMED_KIND = "graph_node"

# ``path#L120`` or ``path#L120-L160`` (also tolerating ``#L120-160``).
_SPAN_RE = re.compile(r"^(?P<path>.+?)#L(?P<start>\d+)(?:-L?(?P<end>\d+))?$")

# Explicit kind prefixes let a caller (or a test) be unambiguous.
_PREFIXES: tuple[tuple[str, str], ...] = (
    ("graph:", "graph_node"),
    ("file:", "file_lines"),
    ("doc:", "doc_section"),
)

# ``foo/bar.py``, ``notes.md``, ``/etc/passwd`` — something that reads as a path.
_PATHISH_RE = re.compile(r"(/|\.[A-Za-z0-9]{1,6}$)")

# Node ids emitted by graphify for this extractor look like
# ``src_experiment_experiment`` — word characters only.
_NODEISH_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_:.\-]*$")


@dataclass(frozen=True)
class Provenance:
    """One checked reference.

    ``ref``    the reference exactly as cited (node id, ``path#L1-L2``, ...)
    ``kind``   one of :data:`PROVENANCE_KINDS`
    ``exists`` whether the independent check succeeded
    ``detail`` short human-readable explanation (always set)
    """

    ref: str
    kind: str
    exists: bool
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {"ref": self.ref, "kind": self.kind, "exists": self.exists, "detail": self.detail}


@dataclass(frozen=True)
class ProvenanceVerdict:
    """The result of verifying a whole reference list."""

    all_verified: bool
    verified: int
    failed: int
    items: list[Provenance] = field(default_factory=list)

    @property
    def good(self) -> list[Provenance]:
        return [p for p in self.items if p.exists]

    @property
    def bad(self) -> list[Provenance]:
        return [p for p in self.items if not p.exists]

    def as_dict(self) -> dict[str, object]:
        return {
            "all_verified": self.all_verified,
            "verified": self.verified,
            "failed": self.failed,
            "items": [p.as_dict() for p in self.items],
        }


def parse_ref(ref: str) -> tuple[str | None, str, str | None]:
    """Classify ``ref`` into ``(kind, payload, heading)``.

    ``kind`` is ``None`` when the reference carries no explicit kind and must be
    inferred by :func:`_verify_one` (a bare token is a graph node only when the
    graph really contains it, and a path only when it reads as one).  ``payload``
    is the node id, the ``path#L..`` text or the plain path; ``heading`` is only
    set for a ``path#Heading`` reference.
    """
    for prefix, kind in _PREFIXES:
        if ref.startswith(prefix):
            return kind, ref[len(prefix):], None
    if _SPAN_RE.match(ref):
        return "file_lines", ref, None
    if "#" in ref:
        path, _, heading = ref.partition("#")
        return "doc_section", path, heading or None
    return None, ref, None


def _resolve_inside(path_text: str, target_root: Path) -> Path | None:
    """Return the realpath of ``path_text`` if it is inside ``target_root``.

    Containment is checked on ``os.path.realpath`` so ``..`` and symlinks
    cannot escape the target root.  Anything outside (including ``/etc/passwd``)
    returns ``None``.
    """
    if not path_text:
        return None
    root = Path(os.path.realpath(str(target_root)))
    raw = Path(path_text)
    candidate = raw if raw.is_absolute() else root / raw
    real = Path(os.path.realpath(str(candidate)))
    if real == root or root in real.parents:
        return real
    return None


def _line_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    return len(text.splitlines())


def _check_graph_node(ref: str, graph: Graph | None) -> Provenance:
    if graph is None:
        return Provenance(ref, "graph_node", False, "no graph loaded")
    try:
        known = graph.by_id()
    except Exception as exc:  # noqa: BLE001 - a broken graph is a failed check
        return Provenance(ref, "graph_node", False, f"graph unreadable: {type(exc).__name__}")
    if ref in known:
        node = known[ref]
        where = f"{node.source_file}:{node.source_location}".strip(":")
        return Provenance(ref, "graph_node", True, f"node in graph ({where})" if where else "node in graph")
    return Provenance(ref, "graph_node", False, "node id not found in graph")


def _check_file_lines(ref: str, target_root: Path) -> Provenance:
    match = _SPAN_RE.match(ref)
    if not match:  # pragma: no cover - callers only route spans here
        return Provenance(ref, "file_lines", False, "malformed")
    path_text = match.group("path")
    start = int(match.group("start"))
    end = int(match.group("end") or start)
    real = _resolve_inside(path_text, target_root)
    if real is None:
        return Provenance(ref, "file_lines", False, "path outside target_root or missing")
    if not real.is_file():
        return Provenance(ref, "file_lines", False, f"file not found: {path_text}")
    try:
        total = _line_count(real)
    except OSError as exc:
        return Provenance(ref, "file_lines", False, f"unreadable: {type(exc).__name__}")
    if total == 0:
        return Provenance(ref, "file_lines", False, "empty file")
    if start < 1 or end < start:
        return Provenance(ref, "file_lines", False, f"invalid span {start}-{end}")
    if end > total:
        return Provenance(ref, "file_lines", False, f"span {start}-{end} beyond {total} lines")
    return Provenance(ref, "file_lines", True, f"lines {start}-{end} of {total}")


def _check_doc_section(ref: str, path_text: str, heading: str | None, target_root: Path) -> Provenance:
    real = _resolve_inside(path_text, target_root)
    if real is None:
        return Provenance(ref, "doc_section", False, "path outside target_root or missing")
    if not real.is_file():
        return Provenance(ref, "doc_section", False, f"file not found: {path_text}")
    if not heading:
        return Provenance(ref, "doc_section", True, "heading unverified")
    try:
        text = real.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return Provenance(ref, "doc_section", False, f"unreadable: {type(exc).__name__}")
    wanted = heading.strip().lstrip("#").strip().lower()
    for line in text.splitlines():
        if line.strip().lstrip("#").strip().lower() == wanted:
            return Provenance(ref, "doc_section", True, f"heading matched: {heading.strip()}")
    if wanted and wanted in text.lower():
        return Provenance(ref, "doc_section", True, f"heading text present: {heading.strip()}")
    return Provenance(ref, "doc_section", False, f"heading not found: {heading.strip()}")


def _in_graph(ref: str, graph: Graph | None) -> bool:
    if graph is None:
        return False
    try:
        return ref in graph.by_id()
    except Exception:  # noqa: BLE001 - an unreadable graph verifies nothing
        return False


def _verify_one(ref: object, graph: Graph | None, target_root: Path) -> Provenance:
    """Verify one reference; never raises."""
    try:
        if not isinstance(ref, str) or not ref.strip():
            return Provenance(str(ref), MALFORMED_KIND, False, "malformed")
        text = ref.strip()
        kind, payload, heading = parse_ref(text)
        explicit = kind is not None
        if kind is None:
            # Inferred kind.  A bare token counts as a graph node **only when the
            # graph really holds it**; otherwise a path-like token is checked for
            # file existence and anything else is malformed.
            if _in_graph(payload, graph):
                return _check_graph_node(payload, graph)
            if _PATHISH_RE.search(payload):
                return _check_doc_section(text, payload, None, target_root)
            return Provenance(text, MALFORMED_KIND, False, "malformed")
        if kind == "graph_node":
            if not explicit or not payload:
                return Provenance(text, MALFORMED_KIND, False, "malformed")
            return _check_graph_node(payload, graph)
        if kind == "file_lines":
            return _check_file_lines(payload, target_root)
        return _check_doc_section(text, payload, heading, target_root)
    except Exception as exc:  # noqa: BLE001 - verification must never raise
        return Provenance(str(ref), MALFORMED_KIND, False, f"error: {type(exc).__name__}")


def graph_nodeish(text: str) -> bool:
    """Whether ``text`` reads as a graph node id rather than a path."""
    if not text or _SPAN_RE.match(text) or "#" in text:
        return False
    return bool(_NODEISH_RE.match(text))


def verify_provenance(
    refs: Sequence[object] | Iterable[object],
    *,
    graph: Graph | None,
    target_root: Path | str,
) -> ProvenanceVerdict:
    """Independently check every reference in ``refs``.

    Returns a :class:`ProvenanceVerdict`; ``all_verified`` is ``True`` only when
    at least one reference was given and every one of them checked out.  This
    function never raises — a malformed reference is simply ``exists=False``
    with ``detail='malformed'``.
    """
    root = Path(target_root)
    items: list[Provenance] = []
    try:
        iterable = list(refs)
    except TypeError:
        return ProvenanceVerdict(False, 0, 0, [Provenance(str(refs), MALFORMED_KIND, False, "malformed")])
    for ref in iterable:
        items.append(_verify_one(ref, graph, root))
    verified = sum(1 for p in items if p.exists)
    failed = len(items) - verified
    return ProvenanceVerdict(
        all_verified=bool(items) and failed == 0,
        verified=verified,
        failed=failed,
        items=items,
    )
