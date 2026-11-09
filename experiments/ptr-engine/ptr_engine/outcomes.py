"""Retrieval-outcome vocabulary.

A single source of truth: every retrieval branch in the engine and every test
must reference one of these constants rather than a bare string literal.
"""

from __future__ import annotations

from typing import Final, Tuple

OK: Final[str] = "OK"
NOT_FOUND: Final[str] = "NOT_FOUND"
STALE_OR_REVOKED: Final[str] = "STALE_OR_REVOKED"
SCOPE_UNGRANTED: Final[str] = "SCOPE_UNGRANTED"

RETRIEVAL_OUTCOMES: Final[Tuple[str, ...]] = (
    OK,
    NOT_FOUND,
    STALE_OR_REVOKED,
    SCOPE_UNGRANTED,
)

__all__ = [
    "OK",
    "NOT_FOUND",
    "STALE_OR_REVOKED",
    "SCOPE_UNGRANTED",
    "RETRIEVAL_OUTCOMES",
]
