"""Render policies: how a state chain becomes OpenAI ``messages``.

Two rules keep the comparison honest, and both are asserted in
``tests/test_context_render.py``:

1. **A message, once emitted, is never rewritten by a later turn.**  Every
   history node renders from its own ``node.text``, verbatim, in chain order.
   Appending turn N+1 therefore appends one message and leaves the first N
   history messages byte-identical: turn N's message list is a prefix of turn
   N+1's, and the newline-joined concatenation of message contents is likewise
   a prefix.  (The canonical-JSON blob is not literally a byte prefix, because
   serialising an array writes its closing ``]`` only at the end; the tests
   state the exact JSON relation they assert.)
2. **Equal information.**  ``POINTER`` and ``NAIVE_APPEND`` send the same chain
   content for the same chain -- every body, in order, byte for byte.
   :func:`equal_information` asserts it.  What distinguishes the pointer arm is
   how the chain was *built* -- content-addressed nodes, fork-instead-of-edit,
   one node shared across several chains -- not the omission of earlier turn
   bodies.  Comparing the arms therefore measures caching, not a smaller
   prompt.

``POINTER``
    Salted invariant preamble (salt first), then every body in chain order,
    verbatim.  Appending a turn appends one message; nothing earlier changes.

``NAIVE_APPEND``
    The same salted preamble and the same bodies in the same order, built by
    plain append: for the same chain it is byte-identical to ``POINTER``.  The
    salt is per cell, not per arm -- without it one cell could be served
    another cell's radix-cache prefix, which would corrupt both arms.

``NAIVE_MUTABLE``
    Volatile values are interpolated *into the preamble message*, so changing
    one value rewrites message 0 on every turn and invalidates the prefix.
    This is the sensitivity bound under test -- not a bug to "fix", and
    deliberately not equal-information with the other two.

``POINTER_FORK``
    ``POINTER`` over a chain whose root is a fork, with the fork labelled in
    the invariant preamble (root address): the label is how a
    compaction-caused prefix break is identified.  If the root is not a fork
    the label is omitted and the rendering equals ``POINTER``.  The fork node's
    own body also starts with the content-addressed provenance marker that
    :func:`resextract.context.budget.compact` writes (replaced-head pointer +
    forked-from chain hash), so the distinction survives any renderer -- a
    summary node carries no marker in either rendering.

Volatile values are never re-attached to an already-emitted body.  A body is
its node's text; the only policy that adds the current volatile block to the
prompt is ``NAIVE_MUTABLE``, which puts it in the invariant header.  The two
append-only policies send no volatile block at all rather than rewrite history
to carry it -- an honest baseline may carry less volatile metadata, but it may
not manufacture a cache miss by rewriting an emitted message.

``APPEND_NOTE`` chains need no renderer of their own, and no new branch here:
the note is a ``summary`` node appended at the tail, and both node selectors --
:func:`_body_nodes` for the append-only policies and :func:`_history` for
``NAIVE_MUTABLE`` -- already include every non-invariant ``summary`` node.  So
the note's own ``[note] ...`` marker reaches the transcript verbatim under all
four policies, and the distinction from ``SUMMARISE_IN_PLACE`` lives in
``node.text`` rather than in a renderer flag -- the same lesson as the fork
marker.  What rule 1 above says for appended *turns* therefore extends across
the compaction boundary for this policy alone: because no earlier node's text
changes, a turn's message list remains a byte-identical prefix of the next
turn's even when a fold happens in between.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from .nodes import StateNode, canonical_bytes

# Kinds that NAIVE_MUTABLE has always rendered as append-only history.  The
# append-only arms render every non-invariant node (see _body_nodes) so a
# compaction summary/fork root is never dropped from the transcript.
_HISTORY_KINDS = frozenset({"delta", "summary", "pointer"})


class RenderPolicy(str, Enum):
    POINTER = "pointer"
    NAIVE_APPEND = "naive_append"
    NAIVE_MUTABLE = "naive_mutable"
    POINTER_FORK = "pointer_fork"


def _volatile_block(volatile: Mapping[str, str]) -> str:
    if not volatile:
        return ""
    return "\n".join(f"{key}={volatile[key]}" for key in sorted(volatile))


def _history(chain: Sequence[StateNode]) -> list[StateNode]:
    """Turn-bearing nodes (deltas/summaries), root invariant excluded."""

    return [n for n in chain if n.kind in _HISTORY_KINDS]


def _body_nodes(chain: Sequence[StateNode]) -> list[StateNode]:
    """Every node that carries conversation content: all but the invariant."""

    return [n for n in chain if n.kind != "invariant"]


def _role(index: int) -> str:
    return "user" if index % 2 == 0 else "assistant"


def _invariant_content(
    preamble: str,
    salt: str,
    chain: Sequence[StateNode],
    *,
    label_fork: bool,
) -> str:
    from .salt import salted

    head = salted(salt, preamble)
    if label_fork and chain and chain[0].kind == "fork":
        head = f"{head}\n\n[chain] forked chain: root={chain[0].node_id}"
    return head


def _bodies(chain: Sequence[StateNode]) -> list[dict[str, str]]:
    return [
        {"role": _role(i), "content": node.text}
        for i, node in enumerate(_body_nodes(chain))
    ]


def _linear_messages(
    chain: Sequence[StateNode],
    *,
    preamble: str,
    salt: str,
    label_fork: bool,
) -> list[dict[str, str]]:
    """Salted invariant head, then every body verbatim and in order."""

    head = _invariant_content(preamble, salt, chain, label_fork=label_fork)
    return [{"role": "system", "content": head}, *_bodies(chain)]


def render(
    policy: RenderPolicy | str,
    chain: Iterable[StateNode],
    *,
    preamble: str,
    volatile: Mapping[str, str],
    salt: str,
) -> list[dict[str, str]]:
    """Render a chain to OpenAI ``messages`` under ``policy``."""

    policy = RenderPolicy(policy)
    nodes = list(chain)
    if not nodes:
        raise ValueError("cannot render an empty chain")
    volatile = dict(volatile)

    if policy in (RenderPolicy.POINTER, RenderPolicy.NAIVE_APPEND):
        return _linear_messages(nodes, preamble=preamble, salt=salt, label_fork=False)

    if policy is RenderPolicy.POINTER_FORK:
        return _linear_messages(nodes, preamble=preamble, salt=salt, label_fork=True)

    if policy is RenderPolicy.NAIVE_MUTABLE:
        from .salt import salted

        block = _volatile_block(volatile)
        head = salted(salt, preamble)
        if block:
            head = f"{head}\n\n[volatile]\n{block}"
        messages = [{"role": "system", "content": head}]
        for i, node in enumerate(_history(nodes)):
            messages.append({"role": _role(i), "content": node.text})
        return messages

    raise AssertionError(f"unhandled policy {policy!r}")  # pragma: no cover


def concatenated_content(messages: Sequence[Mapping[str, Any]]) -> str:
    """Newline-joined contents of ``messages`` -- the information surface."""

    return "\n".join(str(message["content"]) for message in messages)


def equal_information(
    chain: Iterable[StateNode],
    preamble: str,
    salt: str,
) -> bool:
    """Assert POINTER and NAIVE_APPEND carry the same information.

    The two renderings must have the same message count and the same
    concatenated content for the same chain (a non-empty probe volatile is
    passed, so an implementation that re-attaches volatile to one arm but not
    the other is caught too).  Returns ``True`` on equality; raises
    ``AssertionError`` naming both lengths otherwise.
    """

    nodes = list(chain)
    probe = {"step": "1", "focus": "probe"}
    pointer = render(
        RenderPolicy.POINTER, nodes, preamble=preamble, volatile=probe, salt=salt
    )
    naive = render(
        RenderPolicy.NAIVE_APPEND, nodes, preamble=preamble, volatile=probe, salt=salt
    )
    pointer_text = concatenated_content(pointer)
    naive_text = concatenated_content(naive)
    if len(pointer) != len(naive) or pointer_text != naive_text:
        raise AssertionError(
            "POINTER and NAIVE_APPEND are not equal-information: "
            f"{len(pointer)} vs {len(naive)} messages, "
            f"{len(pointer_text)} vs {len(naive_text)} chars"
        )
    return True


def render_bytes(
    policy: RenderPolicy | str,
    chain: Iterable[StateNode],
    *,
    preamble: str,
    volatile: Mapping[str, str],
    salt: str,
) -> bytes:
    """Canonical JSON bytes of :func:`render`.

    This is the serialised experiment payload, *not* a prefix surface on its
    own: appending a message moves the array's closing ``]``, so a turn's
    bytes are a prefix of the next turn's only up to its final byte.  Prefix
    stability is asserted over the message list / concatenated contents; the
    exact JSON relation is ``new.startswith(old[:-1] + b",")``.
    """

    messages = render(
        policy,
        chain,
        preamble=preamble,
        volatile=volatile,
        salt=salt,
    )
    return canonical_bytes(messages)


def first_message_bytes(messages: list[dict[str, Any]]) -> bytes:
    """Canonical bytes of ``messages[0]`` (the invariant header)."""

    if not messages:
        raise ValueError("messages is empty")
    return canonical_bytes(messages[0])
