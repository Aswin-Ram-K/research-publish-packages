"""Capability scope: the grant, not the user, decides what resolves."""

from __future__ import annotations

import pytest

from ptr_engine import Scope, parse, resolve
from ptr_engine.errors import (
    PtrBudgetExceededError,
    PtrRevisionError,
    PtrScopeUngrantedError,
    PtrUnknownIdError,
)


def test_the_wrong_scope_is_ungranted(index, ledger):
    other = Scope(name="sess-02", index=index)
    with pytest.raises(PtrScopeUngrantedError) as excinfo:
        resolve(parse("@knowledge:k01@3"), other, ledger)
    assert excinfo.value.code == "PTR_SCOPE_UNGRANTED"
    assert ledger.rows[-1]["refs_refused"] == 1
    assert ledger.resolved_count() == 0


def test_the_right_scope_resolves(index, ledger):
    scope = Scope(name="sess-01", index=index)
    target = resolve(parse("@knowledge:k01@3"), scope, ledger)
    assert target.hash.startswith("sha256:")
    assert ledger.resolved_count() == 1


def test_a_scope_must_be_presented_not_implied(index):
    with pytest.raises(PtrScopeUngrantedError):
        resolve(parse("@knowledge:k01@3"), "sess-01", None)  # type: ignore[arg-type]


def test_an_unknown_id_is_refused_by_name(index, ledger):
    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrUnknownIdError) as excinfo:
        resolve(parse("@knowledge:k99@3"), scope, ledger)
    assert excinfo.value.code == "PTR_UNKNOWN_ID"
    assert "knowledge:k01" in excinfo.value.context["enumerated"]


def test_a_ref_pinned_to_another_revision_is_refused(index, ledger):
    scope = Scope(name="sess-01", index=index)
    with pytest.raises(PtrRevisionError) as excinfo:
        resolve(parse("@knowledge:k01@9"), scope, ledger)
    assert excinfo.value.code == "PTR_REVISION_MISMATCH"
    assert excinfo.value.context["pinned"] == 9
    assert excinfo.value.context["index_revision"] == 3


def test_a_ref_with_no_revision_resolves_at_head(index, ledger):
    scope = Scope(name="sess-01", index=index)
    assert resolve(parse("@knowledge:k01"), scope, ledger).digest
    assert ledger.resolved_count() == 1


def test_the_budget_is_per_turn_and_configurable(index, ledger):
    scope = Scope(name="sess-01", index=index, max_refs=2)
    resolve(parse("@knowledge:k01@3"), scope, ledger)
    resolve(parse("@knowledge:k02@3"), scope, ledger)
    with pytest.raises(PtrBudgetExceededError) as excinfo:
        resolve(parse("@knowledge:k03@3"), scope, ledger)
    assert excinfo.value.code == "PTR_BUDGET_EXCEEDED"
    assert excinfo.value.context["max_refs"] == 2
    assert len(ledger) == 3
    assert ledger.resolved_count() == 2
    assert ledger.refused_count() == 1


def test_a_bigger_budget_admits_more(index, ledger):
    scope = Scope(name="sess-01", index=index, max_refs=5)
    for text in index.texts()[:5]:
        resolve(parse(text), scope, ledger)
    assert ledger.resolved_count() == 5


def test_scope_defaults_to_the_index_block_size(index):
    scope = Scope(name="sess-01", index=index)
    assert scope.block() == index.block_size == 64
    assert Scope(name="sess-01", index=index, block_size=128).block() == 128
