"""Invariant 1 + 4: content-addressed immutability and fork compaction."""

from __future__ import annotations

import dataclasses

import pytest

from resextract.context import CompactionPolicy, StateNode, compact, make_salt


def make_chain(texts: list[str]) -> list[StateNode]:
    chain = [StateNode.create("INVARIANT PREAMBLE", "invariant")]
    for text in texts:
        chain.append(StateNode.create(text, "delta", parent=chain[-1]))
    return chain


def test_same_text_same_id_and_different_text_different_id() -> None:
    a = StateNode.create("hello world", "delta")
    b = StateNode.create("hello world", "delta")
    c = StateNode.create("hello worlds", "delta")

    assert a.node_id == b.node_id
    assert a == b
    assert a.node_id != c.node_id
    assert a.chain_hash == b.chain_hash


def test_nodes_are_frozen_and_have_no_edit() -> None:
    node = StateNode.create("x", "delta")
    with pytest.raises(dataclasses.FrozenInstanceError):
        node.text = "y"  # type: ignore[misc]
    assert not hasattr(StateNode, "edit")
    assert not hasattr(node, "edit")


def test_chain_hash_changes_when_a_parent_changes() -> None:
    left = StateNode.create("root-A", "invariant")
    right = StateNode.create("root-B", "invariant")
    child_a = StateNode.create("same child text", "delta", parent=left)
    child_b = StateNode.create("same child text", "delta", parent=right)

    assert child_a.node_id != child_b.node_id
    assert child_a.chain_hash != child_b.chain_hash


def test_chain_is_root_to_self() -> None:
    chain = make_chain(["one", "two", "three"])
    walked = chain[-1].chain()
    assert [n.node_id for n in walked] == [n.node_id for n in chain]
    assert walked[0].parent_id is None
    # A node rehydrated from its own dict keeps the same content address.
    assert StateNode.from_dict(chain[-1].to_dict()).node_id == chain[-1].node_id


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValueError):
        StateNode.create("x", "not-a-kind")


def test_salt_is_deterministic_fixed_length_and_seed_sensitive() -> None:
    assert make_salt(7) == make_salt(7)
    assert make_salt(7) != make_salt(8)
    assert len(make_salt(7)) == 16
    assert all(ch in "0123456789abcdef" for ch in make_salt(7))
    with pytest.raises(TypeError):
        make_salt("7")  # type: ignore[arg-type]


def test_fork_creates_all_new_addresses_without_old_parents() -> None:
    old = make_chain(["t1", "t2", "t3", "t4"])
    old_ids = {node.node_id for node in old}
    old_hash = old[-1].chain_hash

    new, event = compact(
        old,
        CompactionPolicy.FORK,
        keep_last=2,
        summarizer=lambda text: f"SUMMARY[{len(text)}]",
    )

    new_ids = {node.node_id for node in new}
    assert new_ids.isdisjoint(old_ids), "fork reused an old content address"
    assert all(node.parent_id is None or node.parent_id in new_ids for node in new)
    assert new[-1].chain_hash != old_hash
    assert new[0].kind == "fork"
    assert event["forked"] is True
    assert event["policy"] == "fork"
    assert event["edited_node_ids"] == [n.node_id for n in old]
    assert set(event) == {
        "policy",
        "at_turn",
        "tokens_before",
        "tokens_after",
        "edited_node_ids",
        "forked",
    }


def test_summarise_in_place_keeps_kept_suffix_and_drops_folded_nodes() -> None:
    old = make_chain(["t1", "t2", "t3"])
    new, event = compact(
        old,
        CompactionPolicy.SUMMARISE_IN_PLACE,
        keep_last=1,
        summarizer=lambda text: "condensed",
    )
    assert new[0].kind == "summary"
    assert new[0].text == "condensed"
    assert event["forked"] is False
    assert len(new) == 2
    assert new[-1].text == "t3"
