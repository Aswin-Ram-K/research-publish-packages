"""``APPEND_NOTE``: the one compaction policy that never rewrites the head (U14).

Every other policy builds a *new* chain out of the retained tail, so the folded
head stops being part of the prompt and the first body after the header changes
at every compaction point:

* ``SLIDING_WINDOW`` drops the head and the invariant root with it;
* ``SUMMARISE_IN_PLACE`` replaces the head (and the invariant root) with one
  bare summary node;
* ``FORK`` does the same but prefixes a ``[fork] ...`` provenance marker.

``APPEND_NOTE`` carries every existing node through untouched -- same object,
same text, same ``node_id``, same parent link -- and records the fold by
*adding* one ``summary`` node at the tail whose text starts with a
content-addressed ``[note] ...`` marker naming the last folded node and the
pre-compaction chain hash.  The property that follows is the one this file
exists to pin: the concatenated text of the invariant head plus every node
emitted before the note is **byte-identical** before and after the compaction.

Both compactions replay the same real corpus event as U13 -- scenario ``C1`` of
``corpora/compaction.json`` at its first compaction point (0-based turn 17),
``keep_last=2``, one canned summary used by both policies -- so the two head
digests below are directly comparable.  Offline only: no network, no requests.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from resextract.context import (
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    make_salt,
    render,
    render_bytes,
)
from resextract.context.budget import is_append_note, note_nodes
from resextract.context.render import concatenated_content, equal_information

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "experiments" / "context-cache" / "corpora" / "compaction.json"
MANIFEST = CORPUS.with_name("MANIFEST.json")
SCENARIO_ID = "C1"
KEEP_LAST = 2
SALT = make_salt(20261020)
RENDER_POLICIES = list(RenderPolicy)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def surface(chain: list[StateNode], limit: int | None = None) -> str:
    """Newline-joined node texts -- the information surface of a chain.

    ``limit`` truncates to a prefix, which is how the pre-note prefix is
    measured on a chain that now ends with a note: the note itself is excluded
    from both sides of the comparison, so the digest is over the same span.
    """

    nodes = list(chain) if limit is None else list(chain)[:limit]
    return "\n".join(node.text for node in nodes)


def render_kwargs(preamble: str) -> dict[str, object]:
    return {"preamble": preamble, "volatile": {}, "salt": SALT}


@pytest.fixture(scope="module")
def event() -> dict:
    """One corpus event, compacted under APPEND_NOTE and SUMMARISE_IN_PLACE."""

    assert CORPUS.exists(), f"missing corpus {CORPUS}"
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pinned = next(e["sha256"] for e in manifest["files"] if e["name"] == CORPUS.name)
    assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == pinned, (
        "corpora/compaction.json does not match its MANIFEST digest; the event "
        "this proof replays is not the pinned corpus"
    )

    scenario = next(s for s in corpus["scenarios"] if s["id"] == SCENARIO_ID)
    turn_index = int(scenario["compaction_points"][0]["at_turn"])
    chain = [StateNode.create(scenario["preamble"], "invariant")]
    for turn_no, turn in enumerate(scenario["turns"][: turn_index + 1], 1):
        chain.append(
            StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)
        )

    summary = scenario["summary_hint"]
    summarizer = lambda _text: summary  # noqa: E731 - canned, deterministic
    appended, append_event = compact(
        chain, CompactionPolicy.APPEND_NOTE, keep_last=KEEP_LAST, summarizer=summarizer
    )
    summarised, summarise_event = compact(
        chain,
        CompactionPolicy.SUMMARISE_IN_PLACE,
        keep_last=KEEP_LAST,
        summarizer=summarizer,
    )
    cut = max(0, len(chain) - KEEP_LAST)
    return {
        "preamble": scenario["preamble"],
        "summary": summary,
        "turn_index": turn_index,
        "chain": chain,
        "cut": cut,
        "folded": chain[:cut],
        "kept": chain[cut:],
        "appended": appended,
        "summarised": summarised,
        "append_event": append_event,
        "summarise_event": summarise_event,
    }


# --------------------------------------------------------------------------- #
# 1. Head stability -- the property no other policy has
# --------------------------------------------------------------------------- #
def test_head_is_byte_identical_after_append_note(event: dict) -> None:
    chain, appended = event["chain"], event["appended"]
    before = surface(chain)
    after = surface(appended, limit=len(chain))
    digest_before, digest_after = sha256_text(before), sha256_text(after)
    print(f"\nAPPEND_NOTE head digest before compaction: {digest_before}")
    print(f"APPEND_NOTE head digest after  compaction: {digest_after}")
    delta = (
        event["append_event"]["tokens_after"] - event["append_event"]["tokens_before"]
    )
    print(f"APPEND_NOTE prompt token delta: +{delta}")

    # The invariant head + every node emitted before the note: byte-identical.
    assert len(appended) == len(chain) + 1, "APPEND_NOTE must add exactly one node"
    assert after == before, "the pre-note prefix was rewritten"
    assert digest_after == digest_before

    # Stronger than bytes: the same nodes, not merely equal copies.
    assert [n.node_id for n in appended[: len(chain)]] == [n.node_id for n in chain]
    assert [n.text for n in appended[: len(chain)]] == [n.text for n in chain]
    assert [n.parent_id for n in appended[: len(chain)]] == [n.parent_id for n in chain]

    # The addition is one note, at the tail, parented on the old last node.
    note = appended[-1]
    assert is_append_note(note) and note.kind == "summary"
    assert note.parent_id == chain[-1].node_id
    assert note_nodes(appended) == [note]
    assert event["append_event"]["edited_node_ids"] == []
    assert event["append_event"]["forked"] is False
    assert event["append_event"]["appended"] is True
    assert event["append_event"]["appended_node_id"] == note.node_id
    assert event["append_event"]["folded_nodes"] == event["cut"]


def test_note_marker_names_what_it_folded(event: dict) -> None:
    chain, note = event["chain"], event["appended"][-1]
    last_folded_id = event["folded"][-1].node_id
    folded_chain_hash = chain[-1].chain_hash
    marker = (
        f"[note] summarises nodes through {last_folded_id}; chain {folded_chain_hash}"
    )

    assert note.text == f"{marker}\n\n{event['summary']}"
    assert note.text.split("\n", 1)[0] == marker
    assert note.meta["summarises_through"] == last_folded_id
    assert note.meta["chain_hash"] == folded_chain_hash
    assert note.meta["appended"] is True
    assert note.meta["folded"] == event["cut"]
    # Content-addressed: the marker is part of the address, so two notes over
    # different folds with the same summariser output cannot collide.
    assert len(note.node_id) == 64 and int(note.node_id, 16) >= 0
    other, _ = compact(
        chain,
        CompactionPolicy.APPEND_NOTE,
        keep_last=1,
        summarizer=lambda _t: event["summary"],
    )
    assert other[-1].node_id != note.node_id
    assert other[-1].meta["summarises_through"] == chain[-2].node_id


@pytest.mark.parametrize("policy", RENDER_POLICIES)
def test_prompt_prefix_survives_the_compaction_under_every_renderer(
    event: dict, policy: RenderPolicy
) -> None:
    """Message 0..N of the pre-compaction prompt is a byte prefix of the post.

    Holds for all four ``RenderPolicy`` values, including ``NAIVE_MUTABLE``:
    the note is a ``summary`` node and both node selectors already emit it, so
    no renderer needs a new branch to carry it.
    """

    kwargs = render_kwargs(event["preamble"])
    before = render(policy, event["chain"], **kwargs)  # type: ignore[arg-type]
    after = render(policy, event["appended"], **kwargs)  # type: ignore[arg-type]

    assert len(after) == len(before) + 1
    assert after[: len(before)] == before, f"{policy.value} rewrote an emitted message"
    assert after[-1]["content"] == event["appended"][-1].text
    assert "[note] summarises nodes through " in after[-1]["content"]

    # The serialised payload relation documented in render.render_bytes: the
    # array's closing ``]`` moves, so the prefix is exact up to that byte.
    before_bytes = render_bytes(policy, event["chain"], **kwargs)  # type: ignore[arg-type]
    after_bytes = render_bytes(policy, event["appended"], **kwargs)  # type: ignore[arg-type]
    assert after_bytes.startswith(before_bytes[:-1] + b",")
    assert sha256_text(concatenated_content(after)) != sha256_text(
        concatenated_content(before)
    )


# --------------------------------------------------------------------------- #
# 2. Contrast -- the same measurement DOES fail for a head-rewriting policy
# --------------------------------------------------------------------------- #
def test_summarise_in_place_produces_a_different_head_digest(event: dict) -> None:
    chain, summarised = event["chain"], event["summarised"]
    before = surface(chain)
    after = surface(summarised, limit=len(chain))
    digest_before, digest_after = sha256_text(before), sha256_text(after)
    print(f"\nSUMMARISE_IN_PLACE head digest before compaction: {digest_before}")
    print(f"SUMMARISE_IN_PLACE head digest after  compaction: {digest_after}")

    assert len(summarised) == 1 + len(event["kept"])
    assert after != before
    assert digest_after != digest_before, (
        "SUMMARISE_IN_PLACE left the head intact -- then test 1 proves nothing"
    )
    # The head rewrite is total: not one folded node survives, nor the root.
    surviving = {n.node_id for n in summarised}
    assert surviving.isdisjoint({n.node_id for n in chain[: event["cut"]]})
    assert summarised[0].kind == "summary"
    assert summarised[0].text == event["summary"]  # bare: no marker, no head
    assert summarised[0].parent_id is None

    # Same at the prompt level: message 1 is the summary, not the first turn.
    kwargs = render_kwargs(event["preamble"])
    rewritten = render(RenderPolicy.NAIVE_APPEND, summarised, **kwargs)
    original = render(RenderPolicy.NAIVE_APPEND, chain, **kwargs)
    assert rewritten[1]["content"] == event["summary"]
    assert original[1]["content"] == chain[1].text
    assert rewritten != original[: len(rewritten)]


# --------------------------------------------------------------------------- #
# 3. Equal information -- within each arm, and exactly what is not equal across
# --------------------------------------------------------------------------- #
def test_equal_information_within_each_arm(event: dict) -> None:
    assert equal_information(event["appended"], event["preamble"], SALT) is True
    assert equal_information(event["summarised"], event["preamble"], SALT) is True

    for arm in ("appended", "summarised"):
        pointer = render(
            RenderPolicy.POINTER, event[arm], **render_kwargs(event["preamble"])  # type: ignore[arg-type]
        )
        naive = render(
            RenderPolicy.NAIVE_APPEND, event[arm], **render_kwargs(event["preamble"])  # type: ignore[arg-type]
        )
        assert pointer == naive
        assert len(naive) == 1 + sum(1 for n in event[arm] if n.kind != "invariant")


def test_append_and_summarise_are_not_equal_information_across_arms(event: dict) -> None:
    """APPEND_NOTE is a strict information *superset* of SUMMARISE_IN_PLACE.

    Equal information cannot hold across the two arms, and the direction is
    fixed by construction: the append form retains every folded body the
    in-place form rewrites away.  What the append form **cannot** carry is a
    token reduction -- it annotates the fold instead of shrinking the prompt,
    so ``tokens_after > tokens_before`` and a budget that was exceeded stays
    exceeded.  That is the honest cost of never rewriting the head, and it is
    asserted here rather than hidden.
    """

    append_text = concatenated_content(
        render(RenderPolicy.NAIVE_APPEND, event["appended"], **render_kwargs(event["preamble"]))  # type: ignore[arg-type]
    )
    summarise_msgs = render(
        RenderPolicy.NAIVE_APPEND, event["summarised"], **render_kwargs(event["preamble"])  # type: ignore[arg-type]
    )
    summarise_text = concatenated_content(summarise_msgs)

    # (a) everything the in-place form carries, the append form also carries:
    # each of its bodies appears verbatim, including the summary (which the
    # note embeds after its marker).
    for message in summarise_msgs[1:]:
        assert message["content"] in append_text
    assert event["summary"] in append_text

    # (b) the converse fails for every folded turn body -- the information the
    # in-place form cannot carry, and the reason the two can never be equal.
    lost = [
        node.text
        for node in event["folded"]
        if node.kind != "invariant" and node.text not in summarise_text
    ]
    print(f"\nAPPEND_NOTE keeps {len(lost)} folded turn bodies that "
          f"SUMMARISE_IN_PLACE drops")
    assert len(lost) == event["cut"] - 1
    assert append_text != summarise_text

    # (c) and the price: the append form cannot satisfy the budget.
    assert event["append_event"]["tokens_after"] > event["append_event"]["tokens_before"]
    assert event["summarise_event"]["tokens_after"] < event["summarise_event"]["tokens_before"]


# --------------------------------------------------------------------------- #
# 4. Red state: make APPEND_NOTE rewrite the head and test 1's property fails
# --------------------------------------------------------------------------- #
def _append_note_that_rewrites_the_head(
    chain: list[StateNode], summary: str, keep_last: int, marker: str
) -> list[StateNode]:
    """What ``APPEND_NOTE`` would be if it rebuilt the prefix like the others.

    Folded head replaced by one summary node, retained tail and the trailing
    note kept -- i.e. the note is still appended, but the head is rewritten.
    This is the mutation test 4 reverts to; it is constructed here so the red
    state is a permanent test and not a one-off transcript.
    """

    cut = max(0, len(chain) - keep_last)
    tail = chain[cut:]
    out = [StateNode.create(f"{marker}\n\n{summary}", "summary", appended=True)]
    for node in tail:
        out.append(
            StateNode.create(node.text, node.kind, parent=out[-1], kept=True)
        )
    out.append(StateNode.create(marker, "summary", parent=out[-1], appended=True))
    return out


def test_a_head_rewriting_append_note_would_fail_head_stability(event: dict) -> None:
    chain, summary = event["chain"], event["summary"]
    marker = event["appended"][-1].text.split("\n", 1)[0]
    mutated = _append_note_that_rewrites_the_head(chain, summary, KEEP_LAST, marker)

    before = surface(chain)
    after = surface(mutated, limit=len(chain))
    assert after != before
    assert sha256_text(after) != sha256_text(before), (
        "the head-rewriting mutation passed test 1 -- test 1 cannot fail"
    )

    # The mutation keeps the same note marker and the same retained tail; the
    # only difference is the prefix, which is exactly what test 1 measures.
    assert mutated[-1].text.startswith(marker)
    assert [n.text for n in mutated[-1 - KEEP_LAST : -1]] == [
        n.text for n in event["appended"][-1 - KEEP_LAST : -1]
    ]
    # Real chain: every folded head node survives, in order.  Mutation: none do.
    assert [n.node_id for n in event["appended"][: event["cut"]]] == [
        n.node_id for n in chain[: event["cut"]]
    ]
    assert {n.node_id for n in mutated}.isdisjoint({n.node_id for n in chain})


def test_subsequent_turns_append_after_the_note(event: dict) -> None:
    """The prompt keeps growing normally: the next turn parents onto the note."""

    appended = event["appended"]
    turn_18 = StateNode.create("turn 18", "delta", parent=appended[-1], turn=18)
    grown = [*appended, turn_18]

    assert grown[-1].parent_id == appended[-1].node_id
    assert grown[:-1] == appended
    assert surface(grown, limit=len(event["chain"])) == surface(event["chain"])
    assert sha256_text(surface(grown, limit=len(event["chain"]))) == sha256_text(
        surface(event["chain"])
    )

    kwargs = render_kwargs(event["preamble"])
    before = render(RenderPolicy.NAIVE_APPEND, appended, **kwargs)  # type: ignore[arg-type]
    after = render(RenderPolicy.NAIVE_APPEND, grown, **kwargs)  # type: ignore[arg-type]
    assert after[: len(before)] == before
    assert after[-1]["content"] == "turn 18"
