#!/usr/bin/env python3
"""E1 distinctness proof — green (post-U13) and red (pre-U13 / U4 defect).

Runs **before any live call**.  Both directions are written as files:

``e1_distinctness_green.json``
    Post-U13 library: the two arms render byte-identical prompts on every
    pre-fork turn (so one request can serve both) and **different** prompts at
    and after the first event.  Records the first differing **byte offset**, the
    differing message indices, the fork-marker and preamble-label offsets, and
    the offline token estimates; ``e1_analyze.py`` later adds the
    server-reported ``prompt_tokens`` at the event turns.

``e1_distinctness_red.json``
    Pre-U13 library: ``FORK`` writes a summary-only root (no marker) and the
    renderer does not label the chain root, so the two arms' prompts are
    byte-identical at *every* turn -- U4's defect.  In that direction
    ``e1_analyze.check_distinctness`` must raise ``UninformativePairs``: zero
    informative pairs, so the analysis refuses to report a break-cost
    comparison.

Exit status is 0 only when green is distinct, red is identical, and the red
rows make the analysis guard raise.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
EXP = REPO / "experiments" / "context-cache"
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cell = _load("e1_cell", HERE / "e1_cell.py")
analyze = _load("e1_analyze", HERE / "e1_analyze.py")
runner = cell.runner

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    canonical_bytes,
    compact,
    default_est_tokens,
    needs_compaction,
    render,
)
from resextract.context.render import concatenated_content  # noqa: E402

GREEN = HERE / "e1_distinctness_green.json"
RED = HERE / "e1_distinctness_red.json"


def _sha(messages) -> str:
    return hashlib.sha256(canonical_bytes(messages)).hexdigest()


def _first_diff(a: bytes, b: bytes) -> int | None:
    return cell.first_diff(a, b)


def _legacy_compact(chain, policy, *, keep_last, summarizer):
    """Pre-U13 compaction: the fork root's text is the summary alone."""

    head = chain[: max(0, len(chain) - keep_last)]
    summary = summarizer("\n\n".join(n.text for n in head)) if head else ""
    new_chain, event = compact(
        chain,
        policy,
        keep_last=keep_last,
        summarizer=summarizer,
        est_tokens=default_est_tokens,
    )
    rebuilt: list[StateNode] = []
    parent = None
    for i, node in enumerate(new_chain):
        text = summary if i == 0 else node.text
        new = StateNode.create(text, node.kind, parent=parent)
        rebuilt.append(new)
        parent = new
    return rebuilt, event


def legacy_plan(session: str, corpus: dict, depth: int) -> dict:
    """Replay the whole session under the pre-U13 (marker-less) library."""

    case = next(s for s in corpus["sessions"] if s["case_id"] == session)
    salt = cell.session_salt(session)
    preamble = case["preamble"]
    chains = {"F": [StateNode.create(preamble, "invariant")],
              "R": [StateNode.create(preamble, "invariant")]}
    turns = []
    for turn_no in range(1, depth + 1):
        text = case["turns"][turn_no - 1]["text"]
        entry = {"turn": turn_no, "arms": {}}
        for arm in ("F", "R"):
            chain = chains[arm] + [
                StateNode.create(text, "delta", parent=chains[arm][-1], turn=turn_no)
            ]
            is_event = False
            if needs_compaction(chain, budget_tokens=cell.BUDGET_TOKENS,
                                est_tokens=default_est_tokens):
                policy = (CompactionPolicy.FORK if arm == "F"
                          else CompactionPolicy.SUMMARISE_IN_PLACE)
                chain, _event = _legacy_compact(
                    chain, policy, keep_last=cell.KEEP_LAST,
                    summarizer=runner._truncating_summarizer,
                )
                is_event = True
            chains[arm] = chain
            messages = render(
                RenderPolicy.POINTER, chain, preamble=preamble, volatile={}, salt=salt
            )
            entry["arms"][arm] = {
                "messages": messages,
                "prompt_sha256": _sha(messages),
                "is_event": is_event,
                "fork_marker_present": any(n.text.startswith("[fork] ") for n in chain),
            }
        entry["same"] = (
            entry["arms"]["F"]["prompt_sha256"] == entry["arms"]["R"]["prompt_sha256"]
        )
        turns.append(entry)
    return {"session": session, "turns": turns}


def main() -> int:
    corpus = json.loads(cell.CORPUS.read_text(encoding="utf-8"))
    plan = cell.build_plan()

    # ----------------------------- GREEN ----------------------------------- #
    green_turns = []
    synthetic_green = []
    for session, sp in plan["sessions"].items():
        for entry in sp["turns"]:
            f, r = entry["arms"]["F"], entry["arms"]["R"]
            fb, rb = canonical_bytes(f["messages"]), canonical_bytes(r["messages"])
            diff = _first_diff(fb, rb)
            fc, rc = concatenated_content(f["messages"]), concatenated_content(r["messages"])
            label = None
            if "\n\n[chain] forked chain: root=" in f["messages"][0]["content"]:
                label = f["messages"][0]["content"].split("\n\n[chain] forked chain:", 1)[0]
                label = "[chain] forked chain:" + f["messages"][0]["content"].split(
                    "\n\n[chain] forked chain:", 1
                )[1]
            record = {
                "session": session,
                "turn": entry["turn"],
                "is_event": f["is_event"],
                "event_index": f["event_index"],
                "identical": diff is None,
                "first_diff_byte_offset": diff,
                "first_diff_message_index": None,
                "bytes_fork": len(fb),
                "bytes_summarise": len(rb),
                "est_tokens_fork": f["est_tokens"],
                "est_tokens_summarise": r["est_tokens"],
                "est_token_delta": f["est_tokens"] - r["est_tokens"],
                "fork_marker_present_fork": f["fork_marker_present"],
                "fork_marker_present_summarise": r["fork_marker_present"],
                "preamble_label_present_fork": f["preamble_label_present"],
                "fork_marker_line": f["fork_marker_line"],
                "preamble_label": label,
                "fork_marker_offset_in_concat": (
                    fc.find("[fork] ") if f["fork_marker_present"] else None
                ),
                "label_offset_in_header": (
                    f["messages"][0]["content"].find("[chain] forked chain:")
                    if f["preamble_label_present"]
                    else None
                ),
                "differing_message_indices": [
                    i
                    for i in range(min(len(f["messages"]), len(r["messages"])))
                    if f["messages"][i]["content"] != r["messages"][i]["content"]
                ],
            }
            if diff is not None:
                fm = [i for i in record["differing_message_indices"]]
                record["first_diff_message_index"] = fm[0] if fm else None
            green_turns.append(record)
            synthetic_green.append(
                {
                    "session": session,
                    "turn": entry["turn"],
                    "arm": "F",
                    "prompt_sha256": f["prompt_sha256"],
                    "is_event": f["is_event"],
                    "fork_marker_present": f["fork_marker_present"],
                }
            )
            synthetic_green.append(
                {
                    "session": session,
                    "turn": entry["turn"],
                    "arm": "R",
                    "prompt_sha256": r["prompt_sha256"],
                    "is_event": r["is_event"],
                    "fork_marker_present": r["fork_marker_present"],
                }
            )

    green_guard = analyze.check_distinctness(synthetic_green)
    event_turns = [t for t in green_turns if t["is_event"]]
    green = {
        "unit": "E1",
        "direction": "green",
        "library": "post-U13",
        "claim": "the two arms render distinct prompts at/after the fork point",
        "corpus_sha256": plan["corpus_sha256"],
        "salt_scope": "per session (make_salt over E1:v1:<seed>:<session>)",
        "arms": plan["arms"],
        "turns": green_turns,
        "guard": green_guard,
        "summary": {
            "pre_fork_turns_identical": all(
                t["identical"]
                for t in green_turns
                if t["turn"] < plan["sessions"][t["session"]]["first_event_turn"]
            ),
            "post_fork_turns_distinct": all(
                not t["identical"]
                for t in green_turns
                if t["turn"] >= plan["sessions"][t["session"]]["first_event_turn"]
            ),
            "event_turns": [t["turn"] for t in event_turns],
            "first_diff_byte_offsets_at_events": [
                t["first_diff_byte_offset"] for t in event_turns
            ],
            "est_token_delta_at_events": [t["est_token_delta"] for t in event_turns],
        },
    }
    GREEN.write_text(json.dumps(green, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ------------------------------ RED ------------------------------------ #
    red_sessions = {}
    synthetic_red = []
    all_identical = True
    marker_seen = False
    for session in cell.SESSIONS:
        lp = legacy_plan(session, corpus, cell.DEPTH)
        red_sessions[session] = [
            {
                "turn": e["turn"],
                "identical": e["same"],
                "first_diff_byte_offset": _first_diff(
                    canonical_bytes(e["arms"]["F"]["messages"]),
                    canonical_bytes(e["arms"]["R"]["messages"]),
                ),
                "is_event": e["arms"]["F"]["is_event"],
                "fork_marker_present_fork": e["arms"]["F"]["fork_marker_present"],
            }
            for e in lp["turns"]
        ]
        for e in lp["turns"]:
            all_identical = all_identical and e["same"]
            marker_seen = marker_seen or e["arms"]["F"]["fork_marker_present"]
            for arm in ("F", "R"):
                synthetic_red.append(
                    {
                        "session": session,
                        "turn": e["turn"],
                        "arm": arm,
                        "prompt_sha256": e["arms"][arm]["prompt_sha256"],
                        "is_event": e["arms"][arm]["is_event"],
                        "fork_marker_present": e["arms"][arm]["fork_marker_present"],
                    }
                )

    red_raised, red_error = False, ""
    try:
        analyze.check_distinctness(synthetic_red)
    except analyze.UninformativePairs as exc:
        red_raised, red_error = True, str(exc)

    red = {
        "unit": "E1",
        "direction": "red",
        "library": "pre-U13 (marker-less fork, unlabelled renderer) -- U4's defect",
        "claim": "with the fork marker removed the two arms become byte-identical "
                 "and the analysis refuses to report pairs",
        "identical_at_every_turn": all_identical,
        "fork_marker_present_anywhere": marker_seen,
        "guard_raised": red_raised,
        "guard_error": red_error,
        "sessions": red_sessions,
        "informative_pairs": 0,
    }
    RED.write_text(json.dumps(red, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "green_pre_fork_identical": green["summary"]["pre_fork_turns_identical"],
            "green_post_fork_distinct": green["summary"]["post_fork_turns_distinct"],
            "green_event_turns": green["summary"]["event_turns"],
            "green_first_diff_offsets": green["summary"]["first_diff_byte_offsets_at_events"],
            "green_est_token_delta": green["summary"]["est_token_delta_at_events"],
            "green_guard_pairs": green_guard["informative_pairs"],
            "red_identical_every_turn": all_identical,
            "red_marker_seen": marker_seen,
            "red_guard_raised": red_raised,
            "red_guard_error": red_error,
        },
        indent=2,
    ))

    ok = (
        green["summary"]["pre_fork_turns_identical"]
        and green["summary"]["post_fork_turns_distinct"]
        and green_guard["informative_pairs"] == plan["preflight"]["pairs_expected"]
        and all_identical
        and not marker_seen
        and red_raised
    )
    print("GREEN+RED CONFIRMED" if ok else "PROOF FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
