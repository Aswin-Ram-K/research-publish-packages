#!/usr/bin/env python3
"""Harness for the lazy-instruction-loading measurement.

Two arms over the same corpus and the same task:

  c0  -- every item body inlined into the system prefix.
  l1  -- a compact projection per item (kind, id, one-line description, byte size)
         plus ONE fetch tool that returns an item body on demand.

The projection is derived mechanically from each body (kind + id + the hero line of
the body + byte size), so it cannot leak a fact the body does not contain.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"

SYSTEM_CORE = (
    "You are an engineering assistant working from a library of reference items.\n"
    "The library contains four kinds of item: tools, skills, memory notes and "
    "knowledge notes.\n"
)

SYSTEM_L1 = SYSTEM_CORE + (
    "Each item's full text is NOT included in this prompt. The index below gives, for\n"
    "every item, its kind, its id, a one-line description and its size in bytes.\n"
    "When you need the content of an item, call the tool get_library_item with that\n"
    "item's item_id. You may call it as many times as you need, and you must not\n"
    "answer from the description alone.\n"
    "When you have enough information, stop calling tools and give your final answer.\n"
)

SYSTEM_C0_PREFIX = SYSTEM_CORE + (
    "Every item's full text is included below, grouped by kind.\n"
)

TASK = (
    "We are writing a post-incident note for two unrelated systems.\n\n"
    "Part 1. The billing service writes logs that must survive the annual\n"
    "reconciliation window. State the exact number of days those logs are retained.\n\n"
    "Part 2. The nightly scheduler is being redesigned. State the exact cap on the\n"
    "number of retry attempts for a nightly scheduled job that exits non-zero.\n\n"
    "Answer with exactly two lines and nothing else:\n"
    "  billing_retention_days: <number>\n"
    "  scheduler_max_attempts: <number>"
)

# Ground truth: the two facts the answer must contain.
GROUND_TRUTH = {
    "fact_billing_retention_days": "400",
    "fact_scheduler_max_attempts": "5",
}
REQUIRED_ITEMS = ["K-2", "M-1"]

FETCH_TOOL = {
    "type": "function",
    "function": {
        "name": "get_library_item",
        "description": "Return the full body of one library item by its item id.",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "The item id exactly as shown in the index, e.g. M-1.",
                }
            },
            "required": ["item_id"],
        },
    },
}


# Text-emulated fetch protocol, used ONLY where the server has no tool parser.
# The model answers a request with exactly one line "FETCH <ID>" (or "ANSWER" when
# it is ready); the harness replies with a user message carrying the body. This
# keeps the L1 arms comparable across servers: in both, a fetched body reaches the
# model as an ordinary message, never as a system-prefix token.
EMULATED_PROTOCOL = (
    "Fetch protocol for this environment (no native tool calling is available):\n"
    "  * To read an item, reply with exactly one line: FETCH <item_id>\n"
    "  * To give your final answer, reply with exactly one line: ANSWER\n"
    "Every FETCH reply is answered with that item's full text as the next message.\n"
)

EMULATED_ANSWER = (
    "You have answered ANSWER. Produce the final answer now, in exactly the format "
    "the task specifies, and nothing else."
)


def parse_emulated(text: str | None) -> tuple[str, str | None]:
    """Read a text-emulated reply. Returns ('fetch', id) / ('answer', None) / ('other', None).

    A model with no tool parser still emits its chat template's native tool-call
    syntax when it sees a function described in the prompt. That syntax is honoured
    only for "<parameter=item_id>" in the text-emulated arm: it is a fetch request,
    and treating it as a final answer would score the arm wrong for a formatting
    reason rather than for the arm under test.
    """
    text = text or ""
    native = re.search(r"<function=get_library_item>.*?<parameter=item_id>\s*([^<\s]+)",
                       text, re.S)
    if native:
        return "fetch", native.group(1).strip()
    for line in text.splitlines():
        bare = line.strip().strip("*`> ").strip()
        # trailing emphasis/quoting is common ("FETCH K-2*"); strip it before matching
        bare = bare.strip("*`\"'").strip()
        upper = bare.upper()
        # bare "ANSWER" may be followed by the answer on the same line; a line that
        # simply starts with the word is not a control signal
        if upper == "ANSWER":
            return "answer", None
        if upper.startswith("FETCH"):
            token = bare[5:].strip().strip(":[]<>\"'.,")
            if token:
                return "fetch", token
    return "other", None


def load_items() -> list[dict]:
    return json.loads((CORPUS / "items.json").read_text(encoding="utf-8"))["items"]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hero_line(body: str) -> str:
    """First line of the body -- an honest one-line description.

    Derived from the body itself, never hand-written, so the index cannot carry a
    fact the body lacks.
    """
    for line in body.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def projection(items: list[dict]) -> str:
    """The compact per-item projection used by the lazy arm."""
    by_kind: dict[str, list[str]] = {}
    for it in items:
        nbytes = len(it["body"].encode("utf-8"))
        by_kind.setdefault(it["kind"], []).append(
            f"  [{it['id']}] ({nbytes} B) {hero_line(it['body'])}"
        )
    out = ["LIBRARY INDEX"]
    for kind in ("tool", "skill", "memory", "knowledge"):
        if kind in by_kind:
            out.append(f"{kind.upper()} ({len(by_kind[kind])} items)")
            out.extend(by_kind[kind])
    return "\n".join(out)


def render_c0(items: list[dict]) -> list[dict]:
    """All bodies inlined into the system prefix."""
    parts = [SYSTEM_C0_PREFIX]
    for kind in ("tool", "skill", "memory", "knowledge"):
        group = [it for it in items if it["kind"] == kind]
        parts.append(f"\n===== {kind.upper()} ITEMS ({len(group)}) =====\n")
        for it in group:
            parts.append(f"\n----- [{it['id']}] {it['title']} -----\n{it['body']}")
    return [
        {"role": "system", "content": "".join(parts)},
        {"role": "user", "content": TASK},
    ]


def render_l1(items: list[dict], emulated: bool = False) -> list[dict]:
    """Compact projection only; bodies arrive on demand through the fetch tool."""
    system = SYSTEM_L1 + ("\n" + EMULATED_PROTOCOL if emulated else "") + "\n" + projection(items) + "\n"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": TASK},
    ]


def item_index(items: list[dict]) -> dict[str, dict]:
    return {it["id"]: it for it in items}


def check_answer(text: str | None) -> dict:
    """Check a completion against the ground truth."""
    text = text or ""
    # Strip emphasis marks only. Underscores are PART of the field names the
    # patterns below match, so removing them makes every answer parse as None.
    flat = text.replace("*", "").replace("`", "")
    days = re.search(r"billing_retention_days\s*[:=]?\s*([0-9][0-9,]*)", flat, re.I)
    tries = re.search(r"scheduler_max_attempts\s*[:=]?\s*([0-9][0-9,]*)", flat, re.I)
    got_days = days.group(1).replace(",", "") if days else None
    got_tries = tries.group(1).replace(",", "") if tries else None
    ok_days = got_days == GROUND_TRUTH["fact_billing_retention_days"]
    ok_tries = got_tries == GROUND_TRUTH["fact_scheduler_max_attempts"]
    return {
        "parsed_billing_retention_days": got_days,
        "parsed_scheduler_max_attempts": got_tries,
        "fact_billing_retention_days": ok_days,
        "fact_scheduler_max_attempts": ok_tries,
        "correct": ok_days and ok_tries,
    }


def selfcheck() -> None:
    """Pre-flight proof that the two arms differ as intended."""
    items = load_items()
    c0, l1 = render_c0(items), render_l1(items)
    c0_chars = sum(len(m["content"] or "") for m in c0)
    l1_chars = sum(len(m["content"] or "") for m in l1)
    print(f"items                  : {len(items)}")
    print(f"corpus total chars     : {sum(len(it['body']) for it in items)}")
    print(f"c0 prefix+task chars   : {c0_chars}")
    print(f"l1 prefix+task chars   : {l1_chars}")
    print(f"all 12 bodies in c0    : "
          f"{all(it['body'].strip() in c0[0]['content'] for it in items)}")
    print(f"bodies absent from l1  : "
          f"{not any(it['body'].strip()[:80] in l1[0]['content'] for it in items)}")
    print(f"required items in c0   : {REQUIRED_ITEMS}")
    idx = item_index(items)
    print(f"required ids resolvable: {all(i in idx for i in REQUIRED_ITEMS)}")
    # the index must carry every id exactly once
    proj_line = l1[0]["content"]
    for i in idx:
        assert proj_line.count(f"[{i}]") == 1, f"id {i} not exactly once in index"
    print("index ids exactly once : True")
    print("ground truth           :", json.dumps(GROUND_TRUTH))
    print("l1 projection sample   :")
    for line in projection(items).splitlines()[:4]:
        print("   ", line)


if __name__ == "__main__":
    selfcheck()
