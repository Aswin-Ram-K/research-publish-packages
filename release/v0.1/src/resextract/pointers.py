"""External-workspace pointer protocol (R2-OPT-SIM card, `## POINTER PROTOCOL`).

A pointer is a **path plus the manifest that declares it**. Resolution is
per-workspace through named roots, so one manifest yields a different absolute
path on another host and nothing is ever copied between workspaces.

The three roles, and the only thing that differs between them:

=============  ==========================================  ==============================
role           lives where                                 may be written by
=============  ==========================================  ==============================
``external``   outside this workspace (another checkout)    nobody here -- read-only
``cursor``     this workspace                              this workspace (boundary artefact)
``cell-source``  this workspace                            nobody (evidence)
=============  ==========================================  ==============================

Safety rules, each enforced rather than documented:

1. **Absence degrades, it never raises.**  A missing root or file is the status
   ``MISSING``, reported in :meth:`PointerReport.degraded`.
2. **Digest, not path.**  A pointer that declares a ``sha256`` and does not match
   is ``DIGEST_MISMATCH`` -- a changed source cannot be silently re-read.
3. **An external root is present only if the host holds it.**  ``root_for`` does
   not create, and never falls back to a default path: a root the host does not
   have is simply absent.
4. **One writer per pointer.**  :func:`write_cursor` refuses any role but
   ``cursor``; nothing in this module can write an ``external`` or
   ``cell-source`` pointer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MANIFEST_SECTION = "## POINTER PROTOCOL"
ROLES = ("external", "cursor", "cell-source")
WRITABLE_ROLES = ("cursor",)


@dataclass
class Pointer:
    source_id: str
    path: str
    role: str
    manifest: str
    sha256: str | None = None
    bytes_expected: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"{self.source_id}: role {self.role!r} is not one of {ROLES}")

    def resolve(self, roots: dict[str, Path | str]) -> Path | None:
        """Resolve through the roots. An ``external`` pointer is tried under ``external`` only."""

        if self.role == "external":
            root = roots.get("external")
            if root is None or str(root) == "":
                return None
            candidate = Path(root) / self.path
        else:
            root = roots.get("own")
            if root is None:
                return None
            candidate = Path(root) / self.path
        return candidate if candidate.exists() else None

    def check(self, roots: dict[str, Path | str]) -> dict[str, Any]:
        target = self.resolve(roots)
        out: dict[str, Any] = {
            "source_id": self.source_id, "role": self.role, "manifest": self.manifest,
            "declared_path": self.path, "status": "MISSING", "served_from": None,
            "path_has_sha256": self.sha256 is not None,
        }
        if target is None:
            return out
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        out["served_from"] = str(target)
        out["sha256"] = digest
        out["bytes"] = target.stat().st_size
        if self.sha256 is not None and digest != self.sha256:
            out["status"] = "DIGEST_MISMATCH"
        elif self.bytes_expected is not None and target.stat().st_size != self.bytes_expected:
            out["status"] = "SIZE_MISMATCH"
        else:
            out["status"] = "OK"
        return out

    def to_json(self) -> dict[str, Any]:
        return {"source_id": self.source_id, "path": self.path, "role": self.role,
                "manifest": self.manifest, "sha256": self.sha256,
                "bytes_expected": self.bytes_expected, "note": self.note}


@dataclass
class PointerReport:
    roots: dict[str, str]
    pointers: list[dict[str, Any]] = field(default_factory=list)

    def all_ok(self) -> bool:
        return all(p["status"] == "OK" for p in self.pointers)

    def degraded(self) -> list[str]:
        return [p["source_id"] for p in self.pointers if p["status"] != "OK"]


def load_manifest(manifest: Path) -> dict[str, Any]:
    """Read the json pointer block out of a unit-card manifest."""

    text = Path(manifest).read_text(encoding="utf-8")
    start = text.find(MANIFEST_SECTION)
    if start < 0:
        raise ValueError(f"{manifest}: no {MANIFEST_SECTION!r} section")
    block = text.find("```json", start)
    if block < 0:
        raise ValueError(f"{manifest}: pointer section has no ```json block")
    end = text.find("```", block + len("```json"))
    if end < 0:
        raise ValueError(f"{manifest}: unterminated ```json block")
    return json.loads(text[block + len("```json"):end])


def pointers_from_manifest(manifest: Path) -> tuple[list[Pointer], dict[str, Any]]:
    body = load_manifest(manifest)
    defined = body.get("roles") or []
    if defined and set(defined) != set(ROLES):
        raise ValueError(f"{manifest}: declared roles {defined} != {ROLES}")
    return [Pointer(**p) for p in body["pointers"]], body


def declared_roots(manifest: Path, body: dict[str, Any] | None = None) -> dict[str, Path]:
    """The roots the host actually holds.

    ``own`` is the manifest's own workspace root (the repository the card lives
    in).  ``external`` is present only when the declaration carries a path AND
    that path exists on this host -- a declared-but-absent external root yields
    no key at all, so every external pointer degrades to ``MISSING``.
    """

    manifest = Path(manifest)
    body = body if body is not None else load_manifest(manifest)
    roots: dict[str, Path] = {"own": manifest.parents[2] if len(manifest.parents) > 2 else manifest.parent}
    ext = (body.get("roots") or {}).get("external") or {}
    path = str(ext.get("path") or "")
    if ext.get("declared") and path:
        candidate = Path(path).expanduser()
        if candidate.exists():
            roots["external"] = candidate
    return roots


def resolve_manifest(manifest: Path, roots: dict[str, Path | str] | None = None) -> PointerReport:
    """Check every pointer in a manifest; never raises on absence."""

    pointers, body = pointers_from_manifest(Path(manifest))
    roots = {k: str(v) for k, v in (roots or declared_roots(manifest, body)).items()}
    return PointerReport(roots=roots, pointers=[p.check(roots) for p in pointers])


def write_cursor(pointer: Pointer, payload: dict[str, Any], roots: dict[str, Path | str]) -> Path:
    """Write the one role this workspace may write, and refuse every other role."""

    if pointer.role not in WRITABLE_ROLES:
        raise PermissionError(f"{pointer.source_id}: role {pointer.role!r} may not be written from here")
    root = Path(roots["own"])
    target = root / pointer.path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


__all__ = ["ROLES", "WRITABLE_ROLES", "Pointer", "PointerReport", "declared_roots",
           "load_manifest", "pointers_from_manifest", "resolve_manifest", "write_cursor"]
