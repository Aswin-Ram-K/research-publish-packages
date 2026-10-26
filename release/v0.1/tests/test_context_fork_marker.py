"""Fork vs summarise must be genuinely different prompts (U13).

The defect this guards: ``compact(FORK)`` and ``compact(SUMMARISE_IN_PLACE)``
were compared as arms in U4 and U5, but they produced nodes with identical
``text`` -- the fork node carried only the summariser's output.  Since every
renderer emits ``node.text`` and none emits ``node.kind``, the two arms sent
byte-identical prompts (U4 offline replay: 44/44 body digests identical; U5:
fork digest == summarise digest 190/190).  Nothing was being compared.

The fix keeps the two arms information-equivalent *within* each arm
(``equal_information`` -- POINTER vs NAIVE_APPEND over the same chain -- still
holds) while making them different *between* arms for a real reason: the fork
node's text starts with a content-addressed provenance marker naming the folded
head's last node id and the pre-compaction chain hash.  A summary rewrites the
head silently and carries no such pointer.

Every test here is offline and replays one real corpus event: scenario ``C1``
of ``corpora/compaction.json`` at its first compaction point (0-based turn 17),
with the corpus's own ``summary_hint`` as the summariser for *both* policies.
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
    canonical_bytes,
    compact,
    make_salt,
    render,
)
from resextract.context.render import concatenated_content, equal_information

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "experiments" / "context-cache" / "corpora" / "compaction.json"
MANIFEST = CORPUS.with_name("MANIFEST.json")
SCENARIO_ID = "C1"
KEEP_LAST = 2
SALT = make_salt(20261020)


def prompt_digest(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256(canonical_bytes(messages)).hexdigest()


@pytest.fixture(scope="module")
def event() -> dict:
    """One corpus event: the chain at C1's first compaction point."""

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
    forked, fork_event = compact(
        chain, CompactionPolicy.FORK, keep_last=KEEP_LAST, summarizer=summarizer
    )
    summarised, summarise_event = compact(
        chain,
        CompactionPolicy.SUMMARISE_IN_PLACE,
        keep_last=KEEP_LAST,
        summarizer=summarizer,
    )
    return {
        "preamble": scenario["preamble"],
        "summary": summary,
        "turn_index": turn_index,
        "chain": chain,
        "forked": forked,
        "summarised": summarised,
        "fork_event": fork_event,
        "summarise_event": summarise_event,
    }


def prompts(event: dict, policy: RenderPolicy) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    kwargs = {"preamble": event["preamble"], "volatile": {}, "salt": SALT}
    return (
        render(policy, event["forked"], **kwargs),
        render(policy, event["summarised"], **kwargs),
    )


# --------------------------------------------------------------------------- #
# 1. The prompt digests must differ -- the whole point of the fix
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "policy",
    [RenderPolicy.NAIVE_APPEND, RenderPolicy.POINTER, RenderPolicy.POINTER_FORK],
)
def test_corpus_event_fork_and_summarise_prompts_differ(event: dict, policy: RenderPolicy) -> None:
    fork_prompt, summarise_prompt = prompts(event, policy)
    fork_digest = prompt_digest(fork_prompt)
    summarise_digest = prompt_digest(summarise_prompt)
    print(f"\n{policy.value}: sha256(fork)={fork_digest}")
    print(f"{policy.value}: sha256(summarise)={summarise_digest}")

    assert fork_digest != summarise_digest, (
        f"{policy.value}: the fork arm and the summarise arm render the SAME "
        "prompt -- the comparison U4/U5 claimed to run is empty"
    )
    assert len(fork_prompt) == len(summarise_prompt)
    # The difference is confined to the compaction boundary (body 0 / head 0):
    # the retained tail carries the same bytes in both arms.
    assert fork_prompt[2:] == summarise_prompt[2:]
    assert fork_prompt[1]["content"].startswith("[fork] ")
    assert "[fork]" not in summarise_prompt[1]["content"]


# --------------------------------------------------------------------------- #
# 2. Equal information must survive the fix, in both arms
# --------------------------------------------------------------------------- #
def test_equal_information_holds_for_both_arms(event: dict) -> None:
    assert equal_information(event["forked"], event["preamble"], SALT) is True
    assert equal_information(event["summarised"], event["preamble"], SALT) is True

    for arm in ("forked", "summarised"):
        pointer = render(
            RenderPolicy.POINTER, event[arm], preamble=event["preamble"], volatile={}, salt=SALT
        )
        naive = render(
            RenderPolicy.NAIVE_APPEND,
            event[arm],
            preamble=event["preamble"],
            volatile={},
            salt=SALT,
        )
        assert pointer == naive
        assert concatenated_content(pointer) == concatenated_content(naive)
        # Neither arm sends less than the other's own renderer: same node count,
        # header + one body per non-invariant node.
        assert len(naive) == 1 + sum(1 for n in event[arm] if n.kind != "invariant")


# --------------------------------------------------------------------------- #
# 3. compact(FORK) and compact(SUMMARISE) differ in an emitted text
# --------------------------------------------------------------------------- #
def test_compaction_emits_a_fork_marker_that_summarise_lacks(event: dict) -> None:
    chain, forked, summarised = event["chain"], event["forked"], event["summarised"]
    replaced_head_id = chain[-1 - KEEP_LAST].node_id
    forked_from = chain[-1].chain_hash

    assert [n.text for n in forked] != [n.text for n in summarised], (
        "compact produced identical texts for FORK and SUMMARISE_IN_PLACE"
    )
    assert forked[0].text == (
        f"[fork] replaces head through {replaced_head_id}; forked_from {forked_from}"
        f"\n\n{event['summary']}"
    )
    assert summarised[0].text == event["summary"]
    # The pointer is content-addressed, and the fork's own address commits to
    # the prefix it replaced: same summary text, different node ids.
    assert replaced_head_id in forked[0].text
    assert forked_from in forked[0].text
    assert forked[0].meta["forked_from"] == forked_from
    assert forked[0].node_id != summarised[0].node_id
    assert forked[0].kind == "fork" and summarised[0].kind == "summary"
    # Only the boundary text changed; the kept tail is the same content.
    assert [n.text for n in forked[1:]] == [n.text for n in summarised[1:]]
    assert event["fork_event"]["forked"] is True
    assert event["summarise_event"]["forked"] is False


# --------------------------------------------------------------------------- #
# 4. Guard: the marker is the *only* reason the digests differ
# --------------------------------------------------------------------------- #
def test_without_the_marker_the_prompts_collide(event: dict) -> None:
    """Reconstruct the pre-fix fork (summary text only) and show it collides.

    This is the red state of test 1: if ``compact(FORK)`` stops writing the
    marker, this chain is what it produces and the two prompts are identical.
    """

    chain = event["chain"]
    cut = max(0, len(chain) - KEEP_LAST)
    tail = chain[cut:]
    tag = {"forked": True, "forked_from": chain[-1].chain_hash}
    root = StateNode.create(event["summary"], "fork", **tag)
    legacy = [root]
    for node in tail:
        legacy.append(
            StateNode.create(
                node.text,
                "summary" if node.kind == "fork" else node.kind,
                parent=legacy[-1],
                **tag,
            )
        )

    kwargs = {"preamble": event["preamble"], "volatile": {}, "salt": SALT}
    legacy_prompt = render(RenderPolicy.NAIVE_APPEND, legacy, **kwargs)
    summarise_prompt = render(RenderPolicy.NAIVE_APPEND, event["summarised"], **kwargs)
    assert prompt_digest(legacy_prompt) == prompt_digest(summarise_prompt), (
        "the legacy (marker-less) fork should render exactly like the summary -- "
        "if this fails, some other difference is carrying the distinction"
    )

    fixed_prompt = render(RenderPolicy.NAIVE_APPEND, event["forked"], **kwargs)
    assert prompt_digest(fixed_prompt) != prompt_digest(legacy_prompt)
    # Char delta is the marker only: ~1 line, not a rewritten transcript.
    delta = len(fixed_prompt[1]["content"]) - len(legacy_prompt[1]["content"])
    marker_line = event["forked"][0].text.split("\n", 1)[0]
    assert delta == len(marker_line) + 2  # marker + "\n\n"
