#!/usr/bin/env python3
"""U14 probe: is APPEND_NOTE's head really byte-identical after compaction?

Offline only.  Replays one real corpus event -- scenario ``C1`` of
``corpora/compaction.json`` at its first compaction point (``at_turn=17``,
0-based) -- through ``APPEND_NOTE`` and ``SUMMARISE_IN_PLACE`` with the SAME
canned summariser (the corpus ``summary_hint``), then digests:

* ``head``  -- the newline-joined text of the invariant node plus every node
  emitted before the note (for the in-place arm: the same span of the chain it
  produced, i.e. everything it left).  This is the surface test 1 measures.
* ``head_prompt`` -- the message-0..N prefix of the rendered prompt under each
  ``RenderPolicy``.

``APPEND_NOTE`` must leave ``head`` identical; ``SUMMARISE_IN_PLACE`` must not.
Also records the information verdict: equal-information *within* each arm
(POINTER vs NAIVE_APPEND), and the strict superset relation *across* arms --
the append arm keeps every folded body the in-place arm drops, and in exchange
it cannot reduce the token count.

Writes ``u14_append_note.json`` beside this file.  No network, no requests.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
CORPUS = REPO / "experiments" / "context-cache" / "corpora" / "compaction.json"
MANIFEST = CORPUS.with_name("MANIFEST.json")
OUT = HERE / "u14_append_note.json"

sys.path.insert(0, str(SRC))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    make_salt,
    render,
    render_bytes,
)
from resextract.context.budget import is_append_note  # noqa: E402
from resextract.context.render import (  # noqa: E402
    concatenated_content,
    equal_information,
)

SCENARIO_ID = "C1"
KEEP_LAST = 2
SALT = make_salt(20261020)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def surface(nodes: list[StateNode], limit: int | None = None) -> str:
    chosen = nodes if limit is None else nodes[:limit]
    return "\n".join(node.text for node in chosen)


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pinned = next(e["sha256"] for e in manifest["files"] if e["name"] == CORPUS.name)
    corpus_sha = hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    if corpus_sha != pinned:
        raise SystemExit(f"corpus digest {corpus_sha} != MANIFEST {pinned}")

    scenario = next(s for s in corpus["scenarios"] if s["id"] == SCENARIO_ID)
    turn_index = int(scenario["compaction_points"][0]["at_turn"])
    chain = [StateNode.create(scenario["preamble"], "invariant")]
    for turn_no, turn in enumerate(scenario["turns"][: turn_index + 1], 1):
        chain.append(StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no))

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
    note = appended[-1]

    head_before = surface(chain)
    head_append = surface(appended, limit=len(chain))
    head_summarise = surface(summarised, limit=len(chain))

    kwargs = {"preamble": scenario["preamble"], "volatile": {}, "salt": SALT}
    prompts: dict[str, dict[str, object]] = {}
    for policy in RenderPolicy:
        before_msgs = render(policy, chain, **kwargs)
        append_msgs = render(policy, appended, **kwargs)
        summarise_msgs = render(policy, summarised, **kwargs)
        prefix = append_msgs[: len(before_msgs)]
        prompts[policy.value] = {
            "messages_before": len(before_msgs),
            "messages_after_append": len(append_msgs),
            "sha256_head_before": sha256_text(concatenated_content(before_msgs)),
            "sha256_head_after_append": sha256_text(concatenated_content(prefix)),
            "head_prefix_identical": prefix == before_msgs,
            "json_prefix_relation": render_bytes(policy, appended, **kwargs).startswith(
                render_bytes(policy, chain, **kwargs)[:-1] + b","
            ),
            "note_is_last_body": append_msgs[-1]["content"] == note.text,
            "sha256_summarise_prompt": sha256_text(concatenated_content(summarise_msgs)),
        }

    append_text = concatenated_content(render(RenderPolicy.NAIVE_APPEND, appended, **kwargs))
    summarise_text = concatenated_content(
        render(RenderPolicy.NAIVE_APPEND, summarised, **kwargs)
    )
    summarise_bodies = [m["content"] for m in render(RenderPolicy.NAIVE_APPEND, summarised, **kwargs)[1:]]
    carried = [body in append_text for body in summarise_bodies]
    lost = [
        node.text
        for node in chain[:cut]
        if node.kind != "invariant" and node.text not in summarise_text
    ]

    payload = {
        "unit": "U14",
        "policy": CompactionPolicy.APPEND_NOTE.value,
        "corpus": {
            "path": "experiments/context-cache/corpora/compaction.json",
            "sha256": corpus_sha,
            "matches_manifest": True,
            "scenario": SCENARIO_ID,
            "turn_index": turn_index,
            "nodes_before": len(chain),
            "keep_last": KEEP_LAST,
            "folded_nodes": cut,
            "salt": SALT,
        },
        "head_digests": {
            "before_compaction": sha256_text(head_before),
            "append_note_after": sha256_text(head_append),
            "append_note_identical": head_append == head_before,
            "summarise_in_place_after": sha256_text(head_summarise),
            "summarise_in_place_identical": head_summarise == head_before,
        },
        "append_note": {
            "nodes_after": len(appended),
            "nodes_added": len(appended) - len(chain),
            "note_kind": note.kind,
            "is_append_note": is_append_note(note),
            "note_text": note.text,
            "note_node_id": note.node_id,
            "note_parent_id": note.parent_id,
            "parent_is_old_tail": note.parent_id == chain[-1].node_id,
            "prefix_node_ids_unchanged": [n.node_id for n in appended[: len(chain)]]
            == [n.node_id for n in chain],
            "marker_line": note.text.split("\n", 1)[0],
            "summarises_through": note.meta["summarises_through"],
            "chain_hash": note.meta["chain_hash"],
            "event": append_event,
        },
        "summarise_in_place": {
            "nodes_after": len(summarised),
            "root_kind": summarised[0].kind,
            "root_text_is_bare_summary": summarised[0].text == summary,
            "folded_nodes_still_present": sorted(
                {n.node_id for n in summarised} & {n.node_id for n in chain[:cut]}
            ),
            "event": summarise_event,
        },
        "prompts": prompts,
        "information": {
            "equal_information_within_append_arm": equal_information(
                appended, scenario["preamble"], SALT
            ),
            "equal_information_within_summarise_arm": equal_information(
                summarised, scenario["preamble"], SALT
            ),
            "equal_information_across_arms": append_text == summarise_text,
            "summarise_bodies_all_carried_by_append": all(carried),
            "folded_bodies_lost_by_summarise": len(lost),
            "folded_bodies_total": cut - 1,
            "append_tokens_before": append_event["tokens_before"],
            "append_tokens_after": append_event["tokens_after"],
            "append_growth_tokens": append_event["tokens_after"]
            - append_event["tokens_before"],
            "summarise_tokens_before": summarise_event["tokens_before"],
            "summarise_tokens_after": summarise_event["tokens_after"],
            "verdict": (
                "equal information holds WITHIN each arm (POINTER vs NAIVE_APPEND); "
                "it cannot hold ACROSS arms: the append form is a strict superset "
                f"by {len(lost)} folded bodies, and it cannot carry a token "
                "reduction (+{} tokens instead)".format(
                    append_event["tokens_after"] - append_event["tokens_before"]
                )
            ),
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    hd = payload["head_digests"]
    print(f"head digest BEFORE compaction          : {hd['before_compaction']}")
    print(f"head digest AFTER  APPEND_NOTE         : {hd['append_note_after']}")
    print(f"  identical                            : {hd['append_note_identical']}")
    print(f"head digest AFTER  SUMMARISE_IN_PLACE  : {hd['summarise_in_place_after']}")
    print(f"  identical                            : {hd['summarise_in_place_identical']}")
    print(f"note node: {note.node_id}  parent == old tail: {note.parent_id == chain[-1].node_id}")
    print(f"marker  : {payload['append_note']['marker_line']}")
    print(f"token delta: {payload['information']['append_growth_tokens']:+d}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
