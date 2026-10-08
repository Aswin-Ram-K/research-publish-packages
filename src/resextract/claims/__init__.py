"""Claim decomposition -- candidate -> atomic, falsifiable, verified claims.

Public surface: :func:`decompose_candidates`, :class:`Claim`,
:class:`ClaimReport`, and the two vocabularies this stage defines because the
store declares neither (see :mod:`resextract.claims.decompose`).
"""

from __future__ import annotations

from .decompose import (
    CLAIM_KINDS,
    INITIAL_VERIFICATION_STATE,
    Claim,
    ClaimReport,
    decompose_candidates,
    normalise_text,
)

__all__ = [
    "CLAIM_KINDS",
    "INITIAL_VERIFICATION_STATE",
    "Claim",
    "ClaimReport",
    "decompose_candidates",
    "normalise_text",
]
