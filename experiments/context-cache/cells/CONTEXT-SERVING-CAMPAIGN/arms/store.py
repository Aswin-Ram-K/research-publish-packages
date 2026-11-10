"""Content-addressed body store for campaign arms.

Layout: <root>/<aa>/<digest> where <aa> is the first two hex chars of the
digest.  A resolve of a missing or digest-mismatched body raises a typed
error; it never returns a placeholder or claimed content.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Union

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
BODY_REF_RE = re.compile(r"#body:([0-9a-f]{64})")


class BodyMissing(Exception):
    """Raised when a digest has no stored body."""


class DigestMismatch(Exception):
    """Raised when a stored body's hash does not match its digest."""


class InvalidDigest(ValueError):
    """Raised when a digest is not a full 64-hex string."""


# Back-compat alias for the historical CCS store.
MissingBody = BodyMissing


def _normalise(digest: str) -> str:
    if not isinstance(digest, str):
        raise InvalidDigest(f"digest must be str, got {type(digest).__name__}")
    d = digest.strip()
    if d.lower().startswith("sha256:"):
        d = d[len("sha256:"):]
    if not DIGEST_RE.fullmatch(d):
        raise InvalidDigest(
            f"digest must be a full 64-hex sha256, got {digest!r} (len={len(d)})"
        )
    return d


def _extract_digest(ref: Any) -> str:
    if isinstance(ref, dict):
        for key in ("digest", "sha256", "body_digest", "body"):
            if key in ref and ref.get(key) is not None:
                val = ref[key]
                if isinstance(val, str):
                    m = BODY_REF_RE.search(val)
                    if m:
                        return m.group(1)
                    try:
                        return _normalise(val)
                    except InvalidDigest:
                        continue
        # maybe ref itself contains a #body token in a value
        for v in ref.values():
            if isinstance(v, str):
                m = BODY_REF_RE.search(v)
                if m:
                    return m.group(1)
        raise BodyMissing(f"no digest found in ref {ref!r}")
    if isinstance(ref, (bytes, bytearray)):
        try:
            ref = ref.decode("utf-8")
        except UnicodeDecodeError:
            raise BodyMissing(f"cannot decode ref {ref!r}")
    if not isinstance(ref, str):
        raise BodyMissing(f"ref must be str/dict, got {type(ref).__name__}")
    m = BODY_REF_RE.search(ref)
    if m:
        return m.group(1)
    try:
        return _normalise(ref)
    except InvalidDigest as e:
        raise BodyMissing(str(e))


class BodyStore:
    def __init__(self, root=None):
        if root is None:
            root = Path(__file__).resolve().parent / "store"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        d = _normalise(digest)
        return self.root / d[:2] / d

    def put(self, body) -> str:
        if isinstance(body, str):
            body = body.encode("utf-8")
        body = bytes(body)
        d = hashlib.sha256(body).hexdigest()
        target = self.root / d[:2] / d
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(body)
        elif target.read_bytes() != body:
            raise ValueError(f"content-address collision at {d}")
        return d

    def get(self, digest: str) -> bytes:
        d = _normalise(digest)
        target = self.root / d[:2] / d
        if not target.is_file():
            raise BodyMissing(f"no body stored for digest {d}")
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != d:
            raise DigestMismatch(
                f"stored body corrupt for digest {d}: "
                f"got {hashlib.sha256(data).hexdigest()}"
            )
        return data

    def resolve(self, ref) -> bytes:
        d = _extract_digest(ref)
        return self.get(d)

    def verify(self, digest: str, expected_bytes) -> bool:
        if isinstance(expected_bytes, str):
            expected_bytes = expected_bytes.encode("utf-8")
        expected_bytes = bytes(expected_bytes)
        try:
            actual = self.get(digest)
        except (BodyMissing, DigestMismatch, InvalidDigest, ValueError):
            return False
        return actual == expected_bytes

    def verify_all(self):
        checked = 0
        failures = []
        if not self.root.exists():
            return {"ok": True, "checked": 0, "failures": []}
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue
            name = p.name
            if not DIGEST_RE.fullmatch(name):
                continue
            checked += 1
            data = p.read_bytes()
            if hashlib.sha256(data).hexdigest() != name:
                failures.append(name)
        return {"ok": len(failures) == 0, "checked": checked, "failures": failures}

    def list_digests(self):
        out = []
        if not self.root.exists():
            return out
        for p in self.root.rglob("*"):
            if p.is_file() and DIGEST_RE.fullmatch(p.name):
                out.append(p.name)
        return sorted(set(out))


__all__ = [
    "BodyStore",
    "BodyMissing",
    "DigestMismatch",
    "InvalidDigest",
    "MissingBody",
]
