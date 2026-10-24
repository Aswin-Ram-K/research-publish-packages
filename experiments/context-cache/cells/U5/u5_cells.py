#!/usr/bin/env python3
"""U5 quality arm -- deterministic prompt cells.

Scope (unit card + orchestrator corrigendum at 18:0x):

* Corpus: ``experiments/second-labeller-190/cases.json`` (read-only, 190 cases).
* Deep history: the compaction corpus already on disk,
  ``experiments/context-cache/cells/U4/u4_sessions.json`` (a sibling unit's
  pinned artifact -- read-only here, snapshotted into ``u5_pin.json`` with its
  sha256 so the run cites a pinned copy, not a live path).
* Volume: ``volatile={}`` everywhere; volatile values are baked into node text
  at creation.  The append-only renderer therefore never rewrites an emitted
  message, so the only thing that can change the prefix is compaction itself.

Rendering arms (all append-only, ``render(NAIVE_APPEND, ...)``):

``baseline``   full history, no compaction (~10-11k prompt tokens)
``summarise``  ``compact(SUMMARISE_IN_PLACE, keep_last=2)``
``fork``       ``compact(FORK, keep_last=2)``

Shallow: the case alone, nothing to compact, so both compaction policies
render the same chain and are asserted byte-identical.

``render.py`` was rewritten by a sibling unit while this unit was starting: in
the current version ``POINTER`` and ``NAIVE_APPEND`` are byte-identical for the
same chain (salted invariant head + every body verbatim, fork bodies included).
The original renderer-vs-renderer question is therefore answered by *assertion*
rather than by spending requests: :func:`pointer_equivalence` proves a 0-token
delta over all 190 cases at both depths.  The live requests go to the
compaction question instead.

Determinism: no wall clock, no ``os.urandom``, no ``random`` module, no
dict-order dependence.  Entropy is sha256 over fixed strings plus the pinned
U4 corpus.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resextract.context import (  # noqa: E402
    CompactionPolicy,
    RenderPolicy,
    StateNode,
    compact,
    render,
)
from resextract.context.budget import default_est_tokens  # noqa: E402
from resextract.context.salt import make_salt  # noqa: E402

HERE = Path(__file__).resolve().parent
CASES_PATH = ROOT / "experiments" / "second-labeller-190" / "cases.json"
U4_PATH = ROOT / "experiments" / "context-cache" / "cells" / "U4" / "u4_sessions.json"
PIN_PATH = HERE / "u5_pin.json"

#: History turns taken from the pinned compaction corpus, per case.
#: 12 x 2800 chars ~ 8,400 estimated tokens -> 10.8k measured prompt tokens
#: (inside the 8k-12k depth band; the 14-turn probe measured 12,465).
HISTORY_TURNS = 12
#: Budget handed to ``needs_compaction`` -- 14 turns exceed it, so compaction
#: is forced.
BUDGET_TOKENS = 6000
#: Nodes retained verbatim by ``compact(keep_last=...)``.
KEEP_LAST = 3
#: Index of the history turn that carries the per-case gold line.
GOLD_TURN = 3

PREAMBLE = (
    "You are a careful analyst answering a multiple-choice question.\n"
    "Reply with the option letter only: one capital letter, nothing else."
)

LETTERS = "ABCDE"


# ---------------------------------------------------------------------- #
# Deterministic text helpers
# ---------------------------------------------------------------------- #
def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cell_salt(case_id: str, depth: str) -> str:
    """Deterministic per-(case, depth) salt: distinct cache key per cell."""

    return make_salt(int(sha(f"u5:{case_id}:{depth}")[:12], 16))


def gold_line(case_id: str) -> str:
    """Unique, answer-free marker line planted mid-history (turn ``GOLD_TURN``).

    Structural probe for silent content loss: a compaction that drops it drops
    arbitrary early-turn content, which is a correctness failure regardless of
    how much cache it saves.
    """

    token = sha(f"u5-gold:{case_id}")[:16]
    return f"- pinned evidence {token} :: case {case_id} finding recorded verbatim"


def lead_summariser(text: str) -> str:
    """Deterministic extractive summariser: first line of each folded turn.

    ``compact`` calls the summariser at most once on the folded head text
    joined by ``\\n\\n``.  Keeping only each paragraph's lead line is the
    realistic cheap summary: later lines -- including the gold line, which
    sits mid-turn -- are discarded.
    """

    out: list[str] = []
    for para in text.split("\n\n"):
        if not para.strip():
            continue
        first = para.split("\n", 1)[0].strip()
        out.append(first[:180])
    return "\n".join(out)


# ---------------------------------------------------------------------- #
# Corpus loading / pinning
# ---------------------------------------------------------------------- #
def load_cases() -> list[dict[str, Any]]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 190:
        raise ValueError(f"expected 190 cases, got {type(cases)}/{len(cases)}")
    return cases


def pin_sessions() -> dict[str, Any]:
    """Snapshot the U4 compaction corpus with a digest (pinned copy)."""

    raw = U4_PATH.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    pinned = {
        "source": str(U4_PATH.relative_to(ROOT)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "u4_seed": payload["seed"],
        "u4_budget_tokens": payload["budget_tokens"],
        "u4_keep_last": payload["keep_last"],
        "turn_chars": payload["turn_chars"],
        "sessions": [
            {
                "case_id": s["case_id"],
                "preamble": s["preamble"],
                "turns": [t["text"] for t in s["turns"]],
            }
            for s in payload["sessions"]
        ],
    }
    PIN_PATH.write_text(json.dumps(pinned, indent=1) + "\n", encoding="utf-8")
    return pinned


def load_pinned() -> dict[str, Any]:
    if PIN_PATH.exists():
        return json.loads(PIN_PATH.read_text(encoding="utf-8"))
    return pin_sessions()


# ---------------------------------------------------------------------- #
# Cell construction
# ---------------------------------------------------------------------- #
def question_block(case: dict[str, Any]) -> str:
    opts = "\n".join(
        f"{LETTERS[i]}) {opt}" for i, opt in enumerate(case["options"])
    )
    return f"QUESTION\n{case['question']}\n\nOPTIONS\n{opts}"


def history_turns(case: dict[str, Any], case_index: int, pinned: dict[str, Any]) -> list[str]:
    sessions = pinned["sessions"]
    sess = sessions[case_index % len(sessions)]
    turns = list(sess["turns"][:HISTORY_TURNS])
    g = gold_line(case["id"])

    # Plant the gold line mid-turn (not the lead line) of GOLD_TURN.
    planted = turns[GOLD_TURN]
    lines = planted.split("\n")
    at = max(1, len(lines) // 2)
    lines.insert(at, g)
    turns[GOLD_TURN] = "\n".join(lines)
    return turns


def _chain(texts: Iterable[tuple[str, str]]) -> list[StateNode]:
    out: list[StateNode] = []
    for text, kind in texts:
        out.append(StateNode.create(text, kind, parent=out[-1] if out else None))
    return out


def build_chain(
    case: dict[str, Any],
    case_index: int,
    depth: str,
    condition: str,
    pinned: dict[str, Any],
) -> dict[str, Any]:
    """Return ``{"chain", "event", "history_turns"}`` for one cell."""

    qblock = question_block(case)

    if depth == "shallow":
        chain = _chain([(PREAMBLE, "invariant"), (qblock, "delta")])
        return {"chain": chain, "event": None, "history_turns": 0}

    turns = history_turns(case, case_index, pinned)
    hist = _chain([(t, "delta") for t in turns])
    total = sum(default_est_tokens(n.text) for n in hist)
    if total <= BUDGET_TOKENS:  # pragma: no cover - construction invariant
        raise AssertionError(f"history {total} est tokens does not force compaction")

    event = None
    if condition == "baseline":
        kept = hist
    else:
        policy = (
            CompactionPolicy.SUMMARISE_IN_PLACE
            if condition == "summarise"
            else CompactionPolicy.FORK
        )
        kept, event = compact(
            hist,
            policy,
            keep_last=KEEP_LAST,
            summarizer=lead_summariser,
            est_tokens=default_est_tokens,
        )

    chain = [StateNode.create(PREAMBLE, "invariant")] + list(kept)
    chain.append(StateNode.create(qblock, "delta", parent=chain[-1]))
    return {"chain": chain, "event": event, "history_turns": len(turns)}


def build_cell(
    case: dict[str, Any],
    case_index: int,
    depth: str,
    condition: str,
    pinned: dict[str, Any],
    *,
    policy: RenderPolicy | str = RenderPolicy.NAIVE_APPEND,
) -> dict[str, Any]:
    built = build_chain(case, case_index, depth, condition, pinned)
    messages = render(
        policy,
        built["chain"],
        preamble=PREAMBLE,
        volatile={},
        salt=cell_salt(case["id"], depth),
    )
    if messages[-1]["role"] != "user":
        raise AssertionError(
            f"last message must be a user turn, got {messages[-1]['role']!r} "
            f"({len(messages)} messages)"
        )
    return {
        "case_id": case["id"],
        "kind": case["kind"],
        "depth": depth,
        "condition": condition,
        "policy": RenderPolicy(policy).value,
        "messages": messages,
        "history_turns": built["history_turns"],
        "compacted": bool(built["event"]),
        "compaction_event": built["event"],
    }


def concat(messages: list[dict[str, str]]) -> str:
    return "\n".join(m["content"] for m in messages)


def canonical(messages: list[dict[str, str]]) -> str:
    return json.dumps(messages, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def retention(cell: dict[str, Any], case: dict[str, Any]) -> dict[str, bool]:
    text = concat(cell["messages"])
    return {
        "gold": gold_line(case["id"]) in text,
        "question": case["question"] in text,
        "options": all(opt in text for opt in case["options"]),
    }


# ---------------------------------------------------------------------- #
# Equal-information assertions
# ---------------------------------------------------------------------- #
def shallow_identity(cases: list[dict[str, Any]], pinned: dict[str, Any]) -> dict[str, Any]:
    """Both compaction arms at shallow depth render the same chain."""

    bad: list[str] = []
    for i, case in enumerate(cases):
        a = build_cell(case, i, "shallow", "summarise", pinned)
        b = build_cell(case, i, "shallow", "fork", pinned)
        if canonical(a["messages"]) != canonical(b["messages"]):
            bad.append(case["id"])
    return {"cases": len(cases), "mismatches": bad, "identical": not bad}


def pointer_equivalence(cases: list[dict[str, Any]], pinned: dict[str, Any]) -> dict[str, Any]:
    """POINTER vs NAIVE_APPEND: byte-identical for the same chain (all depths)."""

    rows = []
    for depth, conditions in (
        ("shallow", ["baseline"]),
        ("deep", ["baseline", "summarise", "fork"]),
    ):
        for cond in conditions:
            diff = 0
            for i, case in enumerate(cases):
                a = build_cell(case, i, depth, cond, pinned, policy=RenderPolicy.POINTER)
                b = build_cell(case, i, depth, cond, pinned, policy=RenderPolicy.NAIVE_APPEND)
                if canonical(a["messages"]) != canonical(b["messages"]):
                    diff += 1
            rows.append(
                {"depth": depth, "condition": cond, "cells": len(cases), "byte_diff_cells": diff}
            )
    return {
        "rows": rows,
        "identical": all(r["byte_diff_cells"] == 0 for r in rows),
        "cells_checked": sum(r["cells"] for r in rows),
    }


def deep_identity(cases: list[dict[str, Any]], pinned: dict[str, Any]) -> dict[str, Any]:
    """Measure summarise-vs-fork and compacted-vs-baseline renderings."""

    rows = []
    for i, case in enumerate(cases):
        s = build_cell(case, i, "deep", "summarise", pinned)
        f = build_cell(case, i, "deep", "fork", pinned)
        b = build_cell(case, i, "deep", "baseline", pinned)
        s_text, f_text, b_text = concat(s["messages"]), concat(f["messages"]), concat(b["messages"])
        r_s, r_f, r_b = retention(s, case), retention(f, case), retention(b, case)
        rows.append(
            {
                "case_id": case["id"],
                "summarise_chars": len(s_text),
                "fork_chars": len(f_text),
                "baseline_chars": len(b_text),
                "identical_summarise_vs_fork": s_text == f_text,
                "summarise_est_tokens": sum(default_est_tokens(m["content"]) for m in s["messages"]),
                "fork_est_tokens": sum(default_est_tokens(m["content"]) for m in f["messages"]),
                "baseline_est_tokens": sum(default_est_tokens(m["content"]) for m in b["messages"]),
                "chars_dropped_by_compaction": len(b_text) - len(s_text),
                "gold": {"baseline": r_b["gold"], "summarise": r_s["gold"], "fork": r_f["gold"]},
                "question": {
                    "baseline": r_b["question"],
                    "summarise": r_s["question"],
                    "fork": r_f["question"],
                },
                "options": {
                    "baseline": r_b["options"],
                    "summarise": r_s["options"],
                    "fork": r_f["options"],
                },
            }
        )
    arms = ("baseline", "summarise", "fork")
    return {
        "cases": len(rows),
        "identical_cases": sum(1 for r in rows if r["identical_summarise_vs_fork"]),
        "gold_retained": {arm: sum(1 for r in rows if r["gold"][arm]) for arm in arms},
        "question_retained": {arm: sum(1 for r in rows if r["question"][arm]) for arm in arms},
        "options_retained": {arm: sum(1 for r in rows if r["options"][arm]) for arm in arms},
        "rows": rows,
    }


if __name__ == "__main__":  # pragma: no cover - manual inspection
    cases = load_cases()
    pinned = pin_sessions()
    print("pin sha256", pinned["sha256"], "bytes", pinned["bytes"])
    sh = shallow_identity(cases, pinned)
    print("shallow summarise==fork:", sh["identical"], "mismatches", sh["mismatches"][:5])
    pe = pointer_equivalence(cases, pinned)
    print("pointer==append:", pe["identical"], pe["rows"])
    dp = deep_identity(cases, pinned)
    print("deep identical summarise vs fork:", dp["identical_cases"], "/", dp["cases"])
    print(
        "gold retained:", dp["gold_retained"],
        "question:", dp["question_retained"],
        "options:", dp["options_retained"],
    )
    r0 = dp["rows"][0]
    print(json.dumps({k: r0[k] for k in r0 if k != "case_id"}, indent=1))
    b = build_cell(cases[0], 0, "deep", "baseline", pinned)
    print("baseline est tokens:", sum(default_est_tokens(m["content"]) for m in b["messages"]))
