"""Named, typed errors. Every failure mode carries a stable code string.

A bare ``Exception`` is a bug in this package: a host that cannot tell
``PTR_UNKNOWN_ID`` from ``PTR_SCOPE_UNGRANTED`` cannot decide whether to ask for a
capability or to fix a typo in a pointer. Each class below is a distinct failure
mode, and the seven negative controls in ``tests/test_negative_controls.py`` each
raise a different one.
"""

from __future__ import annotations

from typing import Any


class PtrError(Exception):
    """Base of every engine error. ``code`` is stable; treat it as API."""

    code = "PTR_ERROR"

    def __init__(self, detail: str = "", **context: Any) -> None:
        self.detail = detail
        self.context = dict(context)
        msg = f"{self.code}: {detail}" if detail else self.code
        super().__init__(msg)

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "detail": self.detail, "context": self.context}


class PtrSyntaxError(PtrError):
    """The token is not of the form ``@kind:id[#pointer][@revision][?projection]``."""

    code = "PTR_SYNTAX"


class PtrUnknownKindError(PtrError):
    """``kind`` is not one of the enumerated kinds (Duval D-024 / ``REF_KINDS``)."""

    code = "PTR_UNKNOWN_KIND"


class PtrUnknownIdError(PtrError):
    """The id is well formed but this index enumerates no such item."""

    code = "PTR_UNKNOWN_ID"


class PtrScopeUngrantedError(PtrError):
    """The presented capability scope did not compile this index."""

    code = "PTR_SCOPE_UNGRANTED"


class PtrProjectionUngrantedError(PtrError):
    """The requested projection is not enumerated for that kind."""

    code = "PTR_PROJECTION_UNENUMERATED"


class PtrPointerError(PtrError):
    """The JSON pointer is malformed, or selects no region in the item body."""

    code = "PTR_POINTER_INVALID"


class PtrBudgetExceededError(PtrError):
    """The per-turn resolve budget (``Scope.max_refs``) is spent."""

    code = "PTR_BUDGET_EXCEEDED"


class PtrRevisionError(PtrError):
    """The reference pins a revision the index was not compiled at."""

    code = "PTR_REVISION_MISMATCH"


class PtrHashMismatchError(PtrError):
    """Bytes read back are not the bytes the content identity names."""

    code = "PTR_HASH_MISMATCH"


class PtrStoreMissError(PtrError):
    """The content identity names a body that is not in the store."""

    code = "PTR_STORE_MISS"


class PtrWarmpoolViolationError(PtrError):
    """The store root resolves inside the repository working tree."""

    code = "PTR_WARMPOOL_INSIDE_REPO"


class PtrExtensionError(PtrError):
    """A body extension is not a plain dotted suffix."""

    code = "PTR_EXTENSION_INVALID"


class PtrDuplicateIdError(PtrError):
    """Two items in one turn claim the same ``(kind, id)``."""

    code = "PTR_DUPLICATE_ID"


class PtrMaterialError(PtrError):
    """A material item is missing a required field or has the wrong type."""

    code = "PTR_MATERIAL_INVALID"


class PtrNotAReferenceError(PtrError):
    """A resolver was handed something that is not a ``Reference``."""

    code = "PTR_NOT_A_REFERENCE"


class PtrUnresolvedRefError(PtrError):
    """The adapter was handed a ref that was not explicitly resolved."""

    code = "PTR_UNRESOLVED_REF"


class PtrBodyMismatchError(PtrError):
    """Body bytes handed to the adapter are not the bytes that ref resolved to."""

    code = "PTR_BODY_MISMATCH"


class PtrTokenSourceRequiredError(PtrError):
    """Token counts were supplied without naming where they came from.

    A count with no provenance is indistinguishable from a measurement, and this
    project has already paid for a zero that meant "unknown".
    """

    code = "PTR_TOKEN_SOURCE_REQUIRED"


class PtrAnnotationError(PtrError):
    """An annotation was asked for something it cannot annotate."""

    code = "PTR_ANNOTATION_INVALID"


__all__ = [
    "PtrError",
    "PtrSyntaxError",
    "PtrUnknownKindError",
    "PtrUnknownIdError",
    "PtrScopeUngrantedError",
    "PtrProjectionUngrantedError",
    "PtrPointerError",
    "PtrBudgetExceededError",
    "PtrRevisionError",
    "PtrHashMismatchError",
    "PtrStoreMissError",
    "PtrWarmpoolViolationError",
    "PtrExtensionError",
    "PtrDuplicateIdError",
    "PtrMaterialError",
    "PtrNotAReferenceError",
    "PtrUnresolvedRefError",
    "PtrBodyMismatchError",
    "PtrTokenSourceRequiredError",
    "PtrAnnotationError",
    "PtrLawError",
    "PtrLawUnknownServerError",
    "PtrLawBoundInvalidError",
    "PtrLawSeriesLengthError",
    "PtrLawObservedInvalidError",
]

class PtrLedgerError(PtrError, ValueError):
    """A ledger row or counter was supplied in a shape the row contract refuses.

    Also a ``ValueError`` so callers written before the code existed (and
    ``tests/test_ledger.py``'s refusal test) keep catching it -- the code is the
    improvement, the exception family is not a break.
    """

    code = "PTR_LEDGER_ERROR"


class PtrLedgerCountError(PtrLedgerError):
    """A counter (``refs_resolved``, ``bytes_appended``, ...) is not a non-negative int."""

    code = "PTR_LEDGER_COUNT"


class PtrLedgerBlockSizeError(PtrLedgerError):
    """``block_size`` is not a positive int."""

    code = "PTR_LEDGER_BLOCK_SIZE"


class PtrLedgerIdError(PtrLedgerError):
    """``ledger_id`` is not a non-empty string."""

    code = "PTR_LEDGER_ID"


class PtrLedgerScopeError(PtrLedgerError):
    """``scope`` is not a non-empty string."""

    code = "PTR_LEDGER_SCOPE"


class PtrLedgerRefusalCodeError(PtrLedgerError):
    """A refusal row's ``code`` is not a named ``PTR_*`` code."""

    code = "PTR_LEDGER_REFUSAL_CODE"


class PtrLawError(PtrLedgerError):
    """A hit-ledger (billing law) call was handed something the law cannot read.

    Same exception family as the ledger errors -- a ``PtrError`` that is also a
    ``ValueError`` -- so a caller written before the codes existed still catches it.
    The codes live in ``LEDGER_LAW_CODES``, not in ``LEDGER_CODES``: the five ledger
    codes are the row contract's, and these four are the law's.
    """

    code = "PTR_LAW_ERROR"


class PtrLawUnknownServerError(PtrLawError):
    """The named server has no measured cache profile, so no prediction is possible."""

    code = "PTR_LAW_UNKNOWN_SERVER"


class PtrLawBoundInvalidError(PtrLawError):
    """``P1``/``L``/an observed count is not a non-negative int (or ``None`` where allowed)."""

    code = "PTR_LAW_BOUND_INVALID"


class PtrLawSeriesLengthError(PtrLawError):
    """The supplied observed series does not line up one-to-one with the recorded turns."""

    code = "PTR_LAW_SERIES_LENGTH"


class PtrLawObservedInvalidError(PtrLawError):
    """An observed series entry is malformed, or contradicts the turn it is applied to."""

    code = "PTR_LAW_OBSERVED_INVALID"
