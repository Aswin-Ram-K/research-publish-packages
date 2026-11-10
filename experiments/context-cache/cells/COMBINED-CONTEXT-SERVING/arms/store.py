"""Content-addressed body store: full 64-hex digests, never truncated."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Union

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class MissingBody(Exception):
    """Raised by get() when a digest has no stored body."""


class InvalidDigest(ValueError):
    """Raised when a digest is not a full 64-hex string."""


def _normalise(digest: str) -> str:
    if not isinstance(digest, str):
        raise InvalidDigest(f"digest must be str, got {type(digest).__name__}")
    d = digest.strip()
    if d.lower().startswith("sha256:"):
        d = d[len("sha256:"):]
    if not DIGEST_RE.fullmatch(d):
        raise InvalidDigest(
            f"digest must be a full 64-hex sha256, got {digest!r} "
            f"(len={len(d)})"
        )
    return d


class BodyStore:
    def __init__(self, root: Union[str, Path, None] = None):
        if root is None:
            root = Path(__file__).resolve().parent / "store"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, digest: str) -> Path:
        d = _normalise(digest)
        return self.root / d[:2] / d

    def put(self, body: Union[bytes, str, bytearray]) -> str:
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
            raise MissingBody(f"no body stored for digest {d}")
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != d:
            raise MissingBody(f"stored body corrupt for digest {d}")
        return data

    def verify(self, digest: str, expected_bytes: Union[bytes, str, bytearray]) -> bool:
        if isinstance(expected_bytes, str):
            expected_bytes = expected_bytes.encode("utf-8")
        expected_bytes = bytes(expected_bytes)
        try:
            actual = self.get(digest)
        except (MissingBody, InvalidDigest, ValueError):
            return False
        return actual == expected_bytes


__all__ = ["BodyStore", "MissingBody", "InvalidDigest"]
