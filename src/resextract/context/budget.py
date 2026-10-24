"""Token-budget checks and compaction.

``StateNode`` is immutable, so "editing" a chain always means constructing a
new one.  That is what makes a fork distinguishable from an edit: compaction
under ``FORK`` produces nodes with fresh content addresses whose ``parent_id``
links point only at other *new* nodes -- never back into the chain being
replaced.  The summariser is injected so the whole module is testable offline.

A fork is also distinguishable *inside the transcript*, not only in node
metadata: every renderer emits ``node.text`` and none emits ``node.kind``, so
a fork node whose text was just the summary would render byte-for-byte like an
in-place summary (U13's finding -- U4/U5 compared two arms that were literally
the same prompt).  The fork node's text therefore begins with a
content-addressed provenance marker naming the folded head's last node id and
the chain hash being forked from; ``SUMMARISE_IN_PLACE`` rewrites the head
silently and carries no such pointer.

``APPEND_NOTE`` is the fourth policy and the only one that never rewrites the
head.  ``SLIDING_WINDOW``, ``SUMMARISE_IN_PLACE`` and ``FORK`` all construct a
new chain out of the retained tail, so the folded head -- and, for the first
two, the invariant preamble with it -- simply stops being part of the prompt;
the first message after the header therefore changes at every compaction
point.  ``APPEND_NOTE`` instead carries every existing node through untouched,
as the *same object* (same text, same ``node_id``, same parent link), and adds
one summary node at the tail whose text begins with a marker naming the last
folded node and the pre-compaction chain hash.  Nothing is edited and nothing
is removed, so the pre-note prefix of the chain -- and of every renderer's
message list -- stays byte-identical across the compaction.  That is the
property no other policy has, and it is what makes cache reuse across a
compaction point measurable; the price is that the prompt grows instead of
shrinking, because this policy *annotates* the fold rather than enforcing the
budget.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Iterable, Sequence

from .nodes import StateNode

Summarizer = Callable[[str], str]


class CompactionPolicy(str, Enum):
    SUMMARISE_IN_PLACE = "summarise_in_place"
    SLIDING_WINDOW = "sliding_window"
    FORK = "fork"
    APPEND_NOTE = "append_note"


def default_est_tokens(text: str) -> int:
    """Cheap offline token estimate: ~4 characters per token, minimum 1."""

    return max(1, (len(text) + 3) // 4)


def _total(chain: Sequence[StateNode], est_tokens: Callable[[str], int]) -> int:
    return sum(est_tokens(node.text) for node in chain)


def needs_compaction(
    chain: Iterable[StateNode],
    *,
    budget_tokens: int,
    est_tokens: Callable[[str], int],
) -> bool:
    """True when the chain's estimated token count exceeds ``budget_tokens``."""

    if budget_tokens < 0:
        raise ValueError("budget_tokens must be >= 0")
    return _total(list(chain), est_tokens) > budget_tokens


def _rebuild(
    texts: Sequence[tuple[str, str, dict[str, Any]]],
) -> list[StateNode]:
    """Create ``(text, kind, meta)`` nodes in order, linking each to the prior."""

    out: list[StateNode] = []
    parent: StateNode | None = None
    for text, kind, meta in texts:
        node = StateNode.create(text, kind, parent=parent, **meta)
        out.append(node)
        parent = node
    return out


def compact(
    chain: Iterable[StateNode],
    policy: CompactionPolicy | str,
    *,
    keep_last: int,
    summarizer: Summarizer,
    est_tokens: Callable[[str], int] = default_est_tokens,
) -> tuple[list[StateNode], dict[str, Any]]:
    """Compact ``chain`` and return ``(new_chain, event)``.

    ``summarizer`` is called at most once, on the concatenated text of the
    nodes that are folded/dropped, so a stub suffices in tests.
    """

    policy = CompactionPolicy(policy)
    chain = list(chain)
    if not chain:
        raise ValueError("cannot compact an empty chain")
    if keep_last < 0:
        raise ValueError("keep_last must be >= 0")

    tokens_before = _total(chain, est_tokens)
    cut = max(0, len(chain) - keep_last)
    head, tail = chain[:cut], chain[cut:]
    summary_text = summarizer("\n\n".join(node.text for node in head)) if head else ""

    if policy is CompactionPolicy.SLIDING_WINDOW:
        new_chain = _rebuild([(node.text, "delta", {"dropped": cut}) for node in tail])
        edited = [node.node_id for node in head]
        forked = False
    elif policy is CompactionPolicy.SUMMARISE_IN_PLACE:
        specs: list[tuple[str, str, dict[str, Any]]] = [
            (summary_text, "summary", {"compacted": True, "kept": len(tail)})
        ]
        specs += [
            (node.text, "delta" if node.kind == "summary" else node.kind, {"kept": True})
            for node in tail
        ]
        new_chain = _rebuild(specs)
        edited = [node.node_id for node in head]
        forked = False
    elif policy is CompactionPolicy.FORK:
        # The marker is the fork's identity, so it must be content-addressed:
        # the replaced head's last node id pins the prefix that is folded away,
        # and the pre-compaction chain hash pins the chain being forked from.
        # Both are already hashes, so the fork node's own address commits to
        # exactly what it replaced.  ``SUMMARISE_IN_PLACE`` emits no marker --
        # which is why the two policies used to render identical prompts.
        replaced_head_id = head[-1].node_id if head else "none"
        fork_tag = {"forked": True, "forked_from": chain[-1].chain_hash}
        marker = (
            f"[fork] replaces head through {replaced_head_id}; "
            f"forked_from {chain[-1].chain_hash}"
        )
        specs = [
            (
                f"{marker}\n\n{summary_text}" if summary_text else marker,
                "fork",
                dict(fork_tag),
            )
        ]
        specs += [
            (node.text, "summary" if node.kind == "fork" else node.kind, dict(fork_tag))
            for node in tail
        ]
        new_chain = _rebuild(specs)
        edited = [node.node_id for node in chain]
        forked = True
    elif policy is CompactionPolicy.APPEND_NOTE:
        # The head is never rewritten: every existing node is carried through
        # as the *same object* -- same text, same node_id, same parent link --
        # and the fold is recorded by *adding* one summary node at the tail.
        # Contrast SUMMARISE_IN_PLACE just above, which drops the folded head
        # (and the invariant root with it) and starts the new chain at a
        # summary, so its first body changes at every compaction.
        #
        # ``KINDS`` in nodes.py is a closed frozenset and nodes.py is outside
        # this unit's write paths, so the note is a ``summary`` node made
        # distinguishable by its ``[note] ...`` marker text and its
        # ``appended`` meta -- and both of those are inputs to its content
        # address, so the note's node_id commits to exactly what it folded.
        summarises_through = head[-1].node_id if head else "none"
        folded_chain_hash = chain[-1].chain_hash
        marker = (
            f"[note] summarises nodes through {summarises_through}; "
            f"chain {folded_chain_hash}"
        )
        note_text = f"{marker}\n\n{summary_text}" if summary_text else marker
        note = StateNode.create(
            note_text,
            "summary",
            parent=chain[-1],
            appended=True,
            summarises_through=summarises_through,
            chain_hash=folded_chain_hash,
            folded=cut,
        )
        new_chain = [*chain, note]
        # Nothing was rewritten -- that is the policy's whole point, so the
        # event must not claim an edited node id.
        edited = []
        forked = False
    else:  # pragma: no cover - enum is exhaustive
        raise AssertionError(f"unhandled policy {policy!r}")

    tokens_after = _total(new_chain, est_tokens)
    event: dict[str, Any] = {
        "policy": policy.value,
        "at_turn": len(chain) - 1,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "edited_node_ids": edited,
        "forked": forked,
    }
    if policy is CompactionPolicy.APPEND_NOTE:
        # Extra keys only for this policy, so the three pre-existing event
        # shapes stay exactly as ``tests/test_context_nodes.py`` pins them.
        event["appended"] = True
        event["appended_node_id"] = new_chain[-1].node_id
        event["folded_nodes"] = cut
    return new_chain, event


def is_fork_chain(chain: Sequence[StateNode]) -> bool:
    """True when the chain's root is a fork node."""

    return bool(chain) and chain[0].kind == "fork"


def is_append_note(node: StateNode) -> bool:
    """True when ``node`` is an ``APPEND_NOTE`` note node.

    The note is a ``summary`` node -- ``KINDS`` is a closed set owned by
    ``nodes.py`` -- carrying ``appended=True`` in its meta.  Both the flag and
    the ``[note] ...`` marker line are inputs to its content address, so a
    node that claims to be a note-but-rewrote-the-head cannot exist: it would
    need the marker, and the marker names what was folded.
    """

    return node.kind == "summary" and bool(node.meta.get("appended"))


def note_nodes(chain: Sequence[StateNode]) -> list[StateNode]:
    """The ``APPEND_NOTE`` notes in ``chain``, in chain order."""

    return [node for node in chain if is_append_note(node)]
