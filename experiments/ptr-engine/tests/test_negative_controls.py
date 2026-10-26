"""Seven negative controls, seven DIFFERENT named errors, never a generic exception.

This is the file that decides whether the engine is debuggable: a host that gets one
generic ``ValueError`` for all seven cannot tell "you lack the capability" from "you
typoed the id", and will retry the wrong thing forever.
"""

from __future__ import annotations

import pytest

from ptr_engine import Scope, parse, resolve
from ptr_engine.errors import (
    PtrBudgetExceededError,
    PtrError,
    PtrPointerError,
    PtrProjectionUngrantedError,
    PtrScopeUngrantedError,
    PtrSyntaxError,
    PtrUnknownIdError,
    PtrUnknownKindError,
)


def _code(excinfo) -> str:
    error = excinfo.value
    assert isinstance(error, PtrError), f"{type(error).__name__} is not a named error"
    assert error.code.startswith("PTR_")
    assert str(error).startswith(error.code)
    return error.code


def test_one_malformed_token(index):
    with pytest.raises(PtrSyntaxError) as excinfo:
        parse("knowledge:k01")  # no leading '@'
    assert _code(excinfo) == "PTR_SYNTAX"


def test_two_unknown_kind(index):
    with pytest.raises(PtrUnknownKindError) as excinfo:
        parse("@widget:k01")
    assert _code(excinfo) == "PTR_UNKNOWN_KIND"


def test_three_unknown_id(index, ledger):
    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrUnknownIdError) as excinfo:
        resolve(parse("@knowledge:nope@3"), scope, ledger)
    assert _code(excinfo) == "PTR_UNKNOWN_ID"


def test_four_ungranted_scope(index, ledger):
    with pytest.raises(PtrScopeUngrantedError) as excinfo:
        resolve(parse("@knowledge:k01@3"), Scope(name="sess-99", index=index), ledger)
    assert _code(excinfo) == "PTR_SCOPE_UNGRANTED"


def test_five_unenumerated_projection(index, ledger):
    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrProjectionUngrantedError) as excinfo:
        resolve(parse("@knowledge:k01@3?secret-view"), scope, ledger)
    assert _code(excinfo) == "PTR_PROJECTION_UNENUMERATED"


def test_six_bad_pointer(index, ledger):
    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrPointerError) as excinfo:
        resolve(parse("@artifact:plan#/nope@3"), scope, ledger)
    assert _code(excinfo) == "PTR_POINTER_INVALID"


def test_seven_over_budget(index, ledger):
    scope = Scope(name="sess-01", index=index, max_refs=1)
    resolve(parse("@knowledge:k01@3"), scope, ledger)
    with pytest.raises(PtrBudgetExceededError) as excinfo:
        resolve(parse("@knowledge:k02@3"), scope, ledger)
    assert _code(excinfo) == "PTR_BUDGET_EXCEEDED"


def test_all_seven_codes_are_distinct(index, ledger):
    codes: list[str] = []
    cases = [
        (lambda: parse("knowledge:k01"), None),
        (lambda: parse("@widget:k01"), None),
        (lambda: resolve(parse("@knowledge:nope@3"), Scope("sess-01", index), ledger), None),
        (lambda: resolve(parse("@knowledge:k01@3"), Scope("sess-99", index), ledger), None),
        (
            lambda: resolve(parse("@knowledge:k01@3?secret-view"), Scope("sess-01", index), ledger),
            None,
        ),
        (lambda: resolve(parse("@artifact:plan#/nope@3"), Scope("sess-01", index), ledger), None),
    ]
    for case, _ in cases:
        with pytest.raises(PtrError) as excinfo:
            case()
        codes.append(excinfo.value.code)

    tight = Scope("sess-01", index, max_refs=1)
    resolve(parse("@knowledge:k01@3"), tight, ledger)
    with pytest.raises(PtrError) as excinfo:
        resolve(parse("@knowledge:k02@3"), tight, ledger)
    codes.append(excinfo.value.code)

    assert len(codes) == 7
    assert len(set(codes)) == 7, f"two controls collapsed onto one code: {codes}"
    assert codes == [
        "PTR_SYNTAX",
        "PTR_UNKNOWN_KIND",
        "PTR_UNKNOWN_ID",
        "PTR_SCOPE_UNGRANTED",
        "PTR_PROJECTION_UNENUMERATED",
        "PTR_POINTER_INVALID",
        "PTR_BUDGET_EXCEEDED",
    ]


def test_ledger_codes_extend_the_enumeration_without_colliding():
    """The seven controls are fixed; the ledger's five codes are additive."""
    from ptr_engine import LEDGER_CODES, PtrError
    from ptr_engine.ledger import LEDGER_CODES as DECLARED

    controls = {
        "PTR_SYNTAX",
        "PTR_UNKNOWN_KIND",
        "PTR_UNKNOWN_ID",
        "PTR_SCOPE_UNGRANTED",
        "PTR_PROJECTION_UNENUMERATED",
        "PTR_POINTER_INVALID",
        "PTR_BUDGET_EXCEEDED",
    }
    assert tuple(LEDGER_CODES) == DECLARED
    assert len(DECLARED) == 5
    assert len(set(LEDGER_CODES)) == 5
    assert controls.isdisjoint(LEDGER_CODES)
    assert len(controls | set(LEDGER_CODES)) == 12
    assert issubclass(PtrError, Exception)
