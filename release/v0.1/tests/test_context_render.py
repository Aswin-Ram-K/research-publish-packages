"""Render semantics: stability, fairness, and equal information (U8).

What is asserted, precisely:

* ``test_append_only_prefix_stability``: for ``POINTER`` and ``NAIVE_APPEND``,
  turn N's ``messages`` list is a prefix of turn N+1's
  (``new[:len(old)] == old``), and the newline-joined concatenation of message
  contents of turn N is a prefix of turn N+1's.  The canonical-JSON blob from
  ``render_bytes`` is NOT literally a byte prefix, because serialising an array
  writes its closing ``]`` only at the end; the exact JSON relation asserted is
  ``bytes_new.startswith(bytes_old[:-1] + b",")``.
* ``test_naive_append_never_rewrites_an_emitted_message`` is the red->green
  guard for the fairness bug.  On the old renderer the current ``[volatile]``
  block was attached to the newest body, so appending turn 3 rewrote the turn-2
  message (it lost that block).  ``new[:len(old)] == old`` failed at index 2.
* ``test_pointer_and_naive_append_are_equal_information``: the two arms send the
  same concatenated content for the same chain (DEFECT 2), so a cost difference
  cannot be explained by sending less.

The NAIVE_MUTABLE assertions remain: that policy is the deliberate sensitivity
bound, not a bug, and must still rewrite message 0.
"""

from __future__ import annotations

import json

import pytest

from resextract.context import (
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    first_message_bytes,
    make_salt,
    render,
    render_bytes,
)
from resextract.context.render import concatenated_content, equal_information

PREAMBLE = "You are a careful analyst. Follow the pointer table."
SALT = make_salt(11)


def build(turn_count: int) -> list[StateNode]:
    chain = [StateNode.create(PREAMBLE, "invariant")]
    for turn in range(1, turn_count + 1):
        chain.append(
            StateNode.create(f"turn {turn}: inspect item {turn}", "delta", parent=chain[-1])
        )
    return chain


def volatile(turn: int) -> dict[str, str]:
    return {"step": str(turn), "focus": f"item-{turn}"}


def render_turn(policy: RenderPolicy, turn_count: int) -> list[dict[str, str]]:
    return render(
        policy,
        build(turn_count),
        preamble=PREAMBLE,
        volatile=volatile(turn_count),
        salt=SALT,
    )


def test_naive_append_never_rewrites_an_emitted_message() -> None:
    """Red->green for the fairness bug: message N-1 must not change."""

    old = render_turn(RenderPolicy.NAIVE_APPEND, 2)
    new = render_turn(RenderPolicy.NAIVE_APPEND, 3)

    assert old[-1]["content"] == "turn 2: inspect item 2", (
        "the turn-2 message must be the node's own text, not text plus the "
        "turn-2 volatile block -- otherwise the next append rewrites it"
    )
    assert new[: len(old)] == old, (
        "appending turn 3 rewrote an already-emitted message: turn N's messages "
        "are no longer a prefix of turn N+1's (the old renderer failed here at "
        "index 2, where the [volatile] block was dropped)"
    )
    assert new[2] == old[-1]
    assert all("[volatile]" not in message["content"] for message in new), (
        "append-only rendering must not attach volatile values to a body"
    )
    assert all("focus=item-3" not in message["content"] for message in new)


@pytest.mark.parametrize("policy", [RenderPolicy.POINTER, RenderPolicy.NAIVE_APPEND])
def test_append_only_prefix_stability(policy: RenderPolicy) -> None:
    """Turn N is a prefix of turn N+1 at message, content and JSON level."""

    for turn_count in (1, 2, 3, 4):
        old = render_turn(policy, turn_count)
        new = render_turn(policy, turn_count + 1)

        assert new[: len(old)] == old, f"{policy.value}: message list changed at turn {turn_count}"
        old_text = concatenated_content(old)
        new_text = concatenated_content(new)
        assert new_text.startswith(old_text)
        assert len(new_text) > len(old_text)

        old_bytes = render_bytes(
            policy,
            build(turn_count),
            preamble=PREAMBLE,
            volatile=volatile(turn_count),
            salt=SALT,
        )
        new_bytes = render_bytes(
            policy,
            build(turn_count + 1),
            preamble=PREAMBLE,
            volatile=volatile(turn_count + 1),
            salt=SALT,
        )
        assert json.loads(old_bytes) == old
        assert new_bytes.startswith(old_bytes[:-1] + b","), (
            "canonical JSON: everything except the array's closing ']' must be "
            "preserved when one message is appended"
        )


def test_pointer_header_only_changes_with_the_chain() -> None:
    """Changing the volatile values must not touch an append-only rendering."""

    turn_two = render(
        RenderPolicy.POINTER, build(3), preamble=PREAMBLE, volatile=volatile(2), salt=SALT
    )
    turn_three = render(
        RenderPolicy.POINTER, build(3), preamble=PREAMBLE, volatile=volatile(3), salt=SALT
    )
    assert turn_two == turn_three
    assert turn_two[0]["content"].startswith(f"[cell-{SALT}]")
    assert first_message_bytes(turn_two) == first_message_bytes(turn_three)


def test_pointer_emits_every_body_in_order_and_no_volatile() -> None:
    chain = build(4)
    messages = render(
        RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=volatile(4), salt=SALT
    )

    assert messages[0]["content"].startswith(f"[cell-{SALT}]")
    assert [message["content"] for message in messages[1:]] == [node.text for node in chain[1:]]
    assert all("[volatile]" not in message["content"] for message in messages)


def test_pointer_and_naive_append_are_equal_information() -> None:
    """DEFECT 2: the pointer arm must not send less than the baseline."""

    for chain in (build(1), build(4), build(6)):
        assert equal_information(chain, PREAMBLE, SALT) is True

        pointer = render(
            RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=volatile(6), salt=SALT
        )
        naive = render(
            RenderPolicy.NAIVE_APPEND, chain, preamble=PREAMBLE, volatile=volatile(6), salt=SALT
        )
        assert pointer == naive
        assert len(concatenated_content(pointer)) == len(concatenated_content(naive))
        assert len(pointer) == len(chain)  # header + one body per non-invariant node


def test_pointer_and_naive_append_agree_on_a_forked_chain() -> None:
    forked, _event = compact(
        build(3), CompactionPolicy.FORK, keep_last=1, summarizer=lambda text: "folded"
    )
    assert equal_information(forked, PREAMBLE, SALT) is True
    assert [node.text for node in forked][1:] == ["turn 3: inspect item 3"]


def test_naive_mutable_rewrites_the_preamble() -> None:
    """The sensitivity bound: message 0 changes, history is appended verbatim."""

    old = render_turn(RenderPolicy.NAIVE_MUTABLE, 2)
    new = render_turn(RenderPolicy.NAIVE_MUTABLE, 3)

    assert old[0]["content"] != new[0]["content"], (
        "NAIVE_MUTABLE must interpolate volatile values into message 0; "
        "if this fails the policy was silently made identical to POINTER"
    )
    assert "focus=item-3" in new[0]["content"]
    assert "focus=item-2" not in new[0]["content"]
    assert new[1] == old[1]
    assert new[: len(old)] != old, "the mutable preamble is meant to break the prefix"


def test_pointer_fork_labels_the_forked_chain() -> None:
    forked, _event = compact(
        build(3), CompactionPolicy.FORK, keep_last=1, summarizer=lambda text: "folded"
    )
    messages = render(
        RenderPolicy.POINTER_FORK, forked, preamble=PREAMBLE, volatile=volatile(3), salt=SALT
    )

    assert messages[0]["content"].startswith(f"[cell-{SALT}]")
    assert "forked chain" in messages[0]["content"]
    assert forked[0].node_id in messages[0]["content"]
    assert [message["content"] for message in messages[1:]] == [node.text for node in forked]


def test_pointer_fork_without_a_fork_equals_pointer() -> None:
    chain = build(3)
    forked_policy = render(
        RenderPolicy.POINTER_FORK, chain, preamble=PREAMBLE, volatile=volatile(3), salt=SALT
    )
    pointer = render(
        RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=volatile(3), salt=SALT
    )
    assert forked_policy == pointer


def test_render_bytes_is_canonical_json_of_render() -> None:
    chain = build(3)
    vol = volatile(3)
    blob = render_bytes(
        RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=vol, salt=SALT
    )
    assert json.loads(blob) == render(
        RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=vol, salt=SALT
    )
    assert blob == render_bytes(
        RenderPolicy.POINTER, chain, preamble=PREAMBLE, volatile=vol, salt=SALT
    )


def test_empty_chain_is_rejected() -> None:
    with pytest.raises(ValueError):
        render(RenderPolicy.POINTER, [], preamble=PREAMBLE, volatile={}, salt=SALT)
