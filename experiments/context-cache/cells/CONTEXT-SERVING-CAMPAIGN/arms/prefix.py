"""Byte-prefix identity for rendered arm text."""

from __future__ import annotations

import hashlib
from typing import Any, Optional, Union


def _to_bytes(x) -> bytes:
    if isinstance(x, (bytes, bytearray)):
        return bytes(x)
    if isinstance(x, str):
        return x.encode("utf-8")
    return str(x).encode("utf-8")


def common_prefix_len(a, b) -> int:
    ba, bb = _to_bytes(a), _to_bytes(b)
    n = min(len(ba), len(bb))
    i = 0
    while i < n and ba[i] == bb[i]:
        i += 1
    return i


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class PrefixTracker:
    """Stateful tracker: call .identity(text) per turn in order."""

    def __init__(self):
        self.previous: Optional[bytes] = None
        self.prefix_len: int = 0
        self.prefix_sha256: str = _sha256_bytes(b"")
        self.full_sha256: str = ""

    def identity(self, rendered_text):
        cur = _to_bytes(rendered_text)
        if self.previous is None:
            plen = 0
        else:
            plen = common_prefix_len(self.previous, cur)
        prefix_bytes = cur[:plen]
        self.prefix_len = plen
        self.prefix_sha256 = _sha256_bytes(prefix_bytes)
        self.full_sha256 = _sha256_bytes(cur)
        self.previous = cur
        return {
            "prefix_sha256": self.prefix_sha256,
            "full_sha256": self.full_sha256,
            "prefix_len": self.prefix_len,
            "common_prefix_bytes": self.prefix_len,
        }

    def reset(self):
        self.previous = None
        self.prefix_len = 0
        self.prefix_sha256 = _sha256_bytes(b"")
        self.full_sha256 = ""


# Back-compat name.
PrefixIdentity = PrefixTracker


_DEFAULT_TRACKER = PrefixTracker()


def identity(rendered_text, previous=None, *, tracker=None):
    """Return prefix/full identity.

    - identity(text): stateful, uses a default (or provided) tracker.
    - identity(text, previous): ad-hoc common prefix with `previous`, no state.
    - identity(text, tracker=tracker): use that tracker.
    """
    if tracker is not None:
        return tracker.identity(rendered_text)
    if previous is not None:
        plen = common_prefix_len(previous, rendered_text)
        cur = _to_bytes(rendered_text)
        return {
            "prefix_sha256": _sha256_bytes(cur[:plen]),
            "full_sha256": _sha256_bytes(cur),
            "prefix_len": plen,
            "common_prefix_bytes": plen,
        }
    return _DEFAULT_TRACKER.identity(rendered_text)


def prefix_len_value(rendered_text, previous=None):
    if previous is None:
        return 0
    return common_prefix_len(previous, rendered_text)


# Convenience alias expected by some callers.
def prefix_len(a, b=None):
    if b is None:
        return 0
    return common_prefix_len(a, b)


__all__ = [
    "common_prefix_len",
    "identity",
    "prefix_len",
    "PrefixTracker",
    "PrefixIdentity",
]
