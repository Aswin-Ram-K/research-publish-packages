#!/usr/bin/env python3
"""U13 probe: does a fork prompt actually differ from an in-place summary?

Offline only.  Replays one real corpus event -- scenario ``C1`` of
``corpora/compaction.json`` at its first compaction point (``at_turn=17``,
0-based) -- through both compaction policies with the SAME summariser and the
SAME renderer, then digests the two prompts.

The ``legacy`` fields reconstruct the pre-U13 fork node (summary text only,
no provenance marker) to record the defect the fix removes: with it, the fork
prompt and the summarise prompt are byte-identical; without it they are not.

Writes ``u13_fork_marker.json`` beside this file.  No network, no requests.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SRC = REPO / "src"
CORPUS = REPO / "experiments" / "context-cache" / "corpora" / "compaction.json"
MANIFEST = CORPUS.with_name("MANIFEST.json")
OUT = HERE / "u13_fork_marker.json"

sys.path.insert(0, str(SRC))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    canonical_bytes,
    compact,
    default_est_tokens,
    make_salt,
    render,
)
from resextract.context.render import equal_information  # noqa: E402


def _sha(messages: list[dict[str, str]]) -> str:
    return hashlib.sha256(canonical_bytes(messages)).hexdigest()


def load_event() -> tuple[dict[str, Any], list[StateNode], int]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    scenario = next(s for s in corpus["scenarios"] if s["id"] == "C1")
    point = scenario["compaction_points"][0]
    turn_index = int(point["at_turn"])
    chain = [StateNode.create(scenario["preamble"], "invariant")]
    for turn_no, turn in enumerate(scenario["turns"][: turn_index + 1], 1):
        chain.append(
            StateNode.create(turn["text"], "delta", parent=chain[-1], turn=turn_no)
        )
    return scenario, chain, turn_index


def legacy_fork(chain: list[StateNode], *, keep_last: int, summary: str) -> list[StateNode]:
    """Pre-U13 fork chain: fork root whose text is only the summary text."""

    cut = max(0, len(chain) - keep_last)
    tail = chain[cut:]
    tag = {"forked": True, "forked_from": chain[-1].chain_hash}
    root = StateNode.create(summary, "fork", **tag)
    out = [root]
    for node in tail:
        out.append(
            StateNode.create(
                node.text, "summary" if node.kind == "fork" else node.kind, parent=out[-1], **tag
            )
        )
    return out


def main() -> int:
    scenario, chain, turn_index = load_event()
    preamble = scenario["preamble"]
    summary = scenario["summary_hint"]
    summarizer = lambda _text: summary  # noqa: E731 - canned, deterministic
    keep_last = 2
    salt = make_salt(20261020)

    forked, fork_event = compact(
        chain, CompactionPolicy.FORK, keep_last=keep_last, summarizer=summarizer
    )
    summarised, sum_event = compact(
        chain, CompactionPolicy.SUMMARISE_IN_PLACE, keep_last=keep_last, summarizer=summarizer
    )
    old = legacy_fork(chain, keep_last=keep_last, summary=summary)

    prompts: dict[str, dict[str, Any]] = {}
    for renderer in (RenderPolicy.NAIVE_APPEND, RenderPolicy.POINTER, RenderPolicy.POINTER_FORK):
        fork_msgs = render(renderer, forked, preamble=preamble, volatile={}, salt=salt)
        sum_msgs = render(renderer, summarised, preamble=preamble, volatile={}, salt=salt)
        old_msgs = render(renderer, old, preamble=preamble, volatile={}, salt=salt)
        prompts[renderer.value] = {
            "sha256_fork": _sha(fork_msgs),
            "sha256_summarise": _sha(sum_msgs),
            "sha256_legacy_fork": _sha(old_msgs),
            "fork_differs_from_summarise": _sha(fork_msgs) != _sha(sum_msgs),
            "legacy_fork_equals_summarise": _sha(old_msgs) == _sha(sum_msgs),
            "prompt_chars_fork": len(json.dumps(fork_msgs)),
            "prompt_chars_summarise": len(json.dumps(sum_msgs)),
            "fork_message_0_chars": len(fork_msgs[0]["content"]),
            "summarise_message_0_chars": len(sum_msgs[0]["content"]),
        }

    marker = forked[0].text.split("\n", 1)[0]
    record = {
        "unit": "U13",
        "corpus": str(CORPUS.relative_to(REPO)),
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "corpus_sha256_in_manifest": next(
            entry["sha256"]
            for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
            if entry["name"] == CORPUS.name
        ),
        "scenario": scenario["id"],
        "compaction_point_0based_turn": turn_index,
        "chain_nodes_before": len(chain),
        "chain_est_tokens_before": sum(default_est_tokens(n.text) for n in chain),
        "keep_last": keep_last,
        "salt": salt,
        "summariser": "corpus summary_hint (identical for both arms)",
        "fork_event": fork_event,
        "summarise_event": sum_event,
        "compact_texts_differ": [n.text for n in forked] != [n.text for n in summarised],
        "fork_root_text": forked[0].text,
        "summarise_root_text": summarised[0].text,
        "fork_marker_first_line": marker,
        "replaced_head_last_node_id": chain[len(chain) - 1 - keep_last].node_id,
        "forked_from_chain_hash": chain[-1].chain_hash,
        "fork_meta": dict(forked[0].meta),
        "fork_node_id": forked[0].node_id,
        "summarise_node_id": summarised[0].node_id,
        "equal_information_fork": equal_information(forked, preamble, salt),
        "equal_information_summarise": equal_information(summarised, preamble, salt),
        "prompts": prompts,
    }
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    naive = prompts["naive_append"]
    print(f"corpus            {record['corpus']}  sha256={record['corpus_sha256'][:16]}…")
    print(f"event             {scenario['id']} @ 0-based turn {turn_index}  "
          f"({len(chain)} nodes, {record['chain_est_tokens_before']} est tokens)")
    print(f"fork marker       {marker[:120]}")
    print(f"sha256(fork)      {naive['sha256_fork']}")
    print(f"sha256(summarise) {naive['sha256_summarise']}")
    print(f"differ (new)      {naive['fork_differs_from_summarise']}   "
          f"(legacy fork == summarise: {naive['legacy_fork_equals_summarise']})")
    print(f"equal_information fork={record['equal_information_fork']} "
          f"summarise={record['equal_information_summarise']}")
    print(f"wrote             {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
