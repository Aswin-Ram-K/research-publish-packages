"""The four annotations, one test each -- plus the off-grid case they exist for."""

from __future__ import annotations

import re

import pytest

from ptr_engine import append_cost, depth, entry_scope, ledger_id, parse
from ptr_engine.annotate import DEPTH_LEAF, DEPTH_ROOT
from ptr_engine.errors import PtrAnnotationError


def test_depth_is_residency(index):
    root = index.root_entry()
    leaves = [entry.as_dict() for entry in index.entries.values()]
    assert depth(root) == DEPTH_ROOT == 0
    assert all(depth(leaf) == DEPTH_LEAF == 1 for leaf in leaves)
    # the dataclass entry works as well as the dict form
    assert depth(next(iter(index.entries.values()))) == 1


def test_depth_refuses_a_role_it_cannot_place():
    with pytest.raises(PtrAnnotationError) as excinfo:
        depth({"role": "warm"})
    assert excinfo.value.code == "PTR_ANNOTATION_INVALID"
    with pytest.raises(PtrAnnotationError):
        depth({"kind": "knowledge"})
    with pytest.raises(PtrAnnotationError):
        depth(object())


def test_scope_names_the_capability_a_resolve_must_present(index):
    assert entry_scope(index.root_entry()) == "sess-01"
    for entry in index.entries.values():
        assert entry_scope(entry) == "sess-01"
    with pytest.raises(PtrAnnotationError):
        entry_scope({"role": "leaf"})


def test_append_cost_is_length_modulo_block_size():
    text = "@knowledge:k01@3"
    assert len(text.encode()) == 16
    assert append_cost(text, 64) == 16 == len(text.encode()) % 64
    assert append_cost(parse(text), 64) == 16, "a Reference annotates like its text"
    assert append_cost(text, 7) == 16 % 7


def test_off_grid_is_detectable_and_on_grid_is_not():
    off_grid = "@knowledge:k01@3"  # 16 bytes -> 16 % 64 == 16
    on_grid = "@artifact:" + "a" * 54  # exactly 64 bytes
    assert len(on_grid.encode()) == 64
    assert append_cost(off_grid, 64) != 0, "an off-grid append must be visible"
    assert append_cost(on_grid, 64) == 0, "an on-grid append must read as 0"
    assert bool(append_cost(off_grid, 64)) is True
    assert bool(append_cost(on_grid, 64)) is False


@pytest.mark.parametrize("block_size", [0, -64, 1.5, True])
def test_append_cost_refuses_a_nonsense_block_size(block_size):
    with pytest.raises(PtrAnnotationError):
        append_cost("@knowledge:k01@3", block_size)


def test_ledger_id_is_deterministic_and_positional():
    a = ledger_id("sess-01", "@knowledge:k01@3", 7)
    b = ledger_id("sess-01", "@knowledge:k01@3", 7)
    c = ledger_id("sess-01", "@knowledge:k01@3", 8)
    d = ledger_id("sess-02", "@knowledge:k01@3", 7)
    assert a == b
    assert a != c and a != d
    assert re.fullmatch(r"sess-01:0007:[0-9a-f]{12}", a)


def test_ledger_id_refuses_empty_parts():
    with pytest.raises(PtrAnnotationError):
        ledger_id("", "@knowledge:k01@3", 0)
    with pytest.raises(PtrAnnotationError):
        ledger_id("sess-01", "", 0)
    with pytest.raises(PtrAnnotationError):
        ledger_id("sess-01", "@knowledge:k01@3", -1)
