"""Per-cell salts: the first tokens of a cell's invariant prefix.

Two cells must never share a radix-cache prefix, otherwise one cell's warm
cache silently serves another cell's prompt.  A deterministic, fixed-length
salt derived from the cell seed and placed at the very front of the invariant
preamble makes the first block differ per cell by construction.  Determinism
matters for reproducibility: the same seed always yields the same salt, so a
re-run lands on the same cache key.
"""

from __future__ import annotations

import hashlib

SALT_LEN = 16
SALT_PREFIX = "cell-"


def make_salt(seed: int) -> str:
    """Deterministic 16-hex-char salt for ``seed``.

    >>> make_salt(7) == make_salt(7)
    True
    >>> len(make_salt(7))
    16
    """

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an int")
    raw = hashlib.sha256(f"resextract-cell-salt:v1:{seed}".encode("utf-8")).hexdigest()
    return raw[:SALT_LEN]


def salted(salt: str, preamble: str) -> str:
    """The invariant preamble message: salt first, then the preamble."""

    if not salt:
        raise ValueError("salt must be non-empty")
    return f"[{SALT_PREFIX}{salt}]\n{preamble}"
