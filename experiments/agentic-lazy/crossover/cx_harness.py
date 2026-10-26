#!/usr/bin/env python3
"""Task texts, renderers and answer checkers for the crossover sweep.

Everything that can be reused from the first arm is imported from
`../harness.py` rather than copied: SYSTEM_CORE, SYSTEM_L1, SYSTEM_C0_PREFIX,
EMULATED_PROTOCOL, parse_emulated, projection, hero_line, FETCH_TOOL.

Two task variants, one per needed-fraction. The task text never names an item id:
it describes the systems, and the model must find the item that carries the fact.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PARENT = ROOT.parent
sys.path.insert(0, str(PARENT))
import harness as h  # noqa: E402  (the first arm's harness, unmodified)

CORPUS = ROOT / "corpus"

# ---------------------------------------------------------------- tasks
TASK_2 = h.TASK  # byte-identical to the first arm: 2 facts, 2 of 12 items

TASK_6 = (
    "We are writing a post-incident note covering six unrelated systems.\n\n"
    "Part 1. The billing service writes logs that must survive the annual\n"
    "reconciliation window. State the exact number of days those logs are retained.\n\n"
    "Part 2. The nightly scheduler is being redesigned. State the exact cap on the\n"
    "number of retry attempts for a nightly scheduled job that exits non-zero.\n\n"
    "Part 3. Compliance wants the audit trail kept for the legal minimum. State the\n"
    "exact number of days the compliance audit trail is retained.\n\n"
    "Part 4. The dispatch worker is being resized. State the exact cap on the number\n"
    "of attempts a dispatch job that exits non-zero is given.\n\n"
    "Part 5. The edge tier is being costed. State the exact number of seconds after\n"
    "which a cached response expires.\n\n"
    "Part 6. The search team is planning a migration. State the exact number of\n"
    "documents the batch reindexer processes in one chunk.\n\n"
    "Answer with exactly six lines and nothing else:\n"
    "  billing_retention_days: <number>\n"
    "  scheduler_max_attempts: <number>\n"
    "  audit_retention_days: <number>\n"
    "  dispatch_max_attempts: <number>\n"
    "  cache_ttl_seconds: <number>\n"
    "  batch_chunk_size: <number>"
)

FIELDS_2 = {
    "billing_retention_days": "400",
    "scheduler_max_attempts": "5",
}
FIELDS_6 = {
    "billing_retention_days": "400",
    "scheduler_max_attempts": "5",
    "audit_retention_days": "2555",
    "dispatch_max_attempts": "3",
    "cache_ttl_seconds": "900",
    "batch_chunk_size": "512",
}

NEEDED_2 = ["K-2", "M-1"]
NEEDED_6 = ["K-2", "M-1", "K-4", "M-4", "S-4", "T-4"]

GRID_SIZES = (3000, 30000)   # the crossover grid: 3k and 30k only


def task_for(n_items: int) -> str:
    return TASK_2 if n_items == 12 else TASK_6


def fields_for(n_items: int) -> dict[str, str]:
    return FIELDS_2 if n_items == 12 else FIELDS_6


def needed_for(n_items: int) -> list[str]:
    return NEEDED_2 if n_items == 12 else NEEDED_6


# ---------------------------------------------------------------- corpus
def cell_dir(n_items: int, total_chars: int) -> pathlib.Path:
    return CORPUS / f"{n_items:02d}_{total_chars:05d}"


def load_items(n_items: int, total_chars: int) -> list[dict]:
    return json.loads((cell_dir(n_items, total_chars) / "items.json")
                      .read_text(encoding="utf-8"))["items"]


# ---------------------------------------------------------------- rendering
def render_c0(items: list[dict], task: str, salt: str | None = None) -> list[dict]:
    """All bodies inlined; `salt` is prepended so the prefix cannot be cache-hit."""
    parts = [h.SYSTEM_C0_PREFIX]
    for kind in ("tool", "skill", "memory", "knowledge"):
        group = [it for it in items if it["kind"] == kind]
        parts.append(f"\n===== {kind.upper()} ITEMS ({len(group)}) =====\n")
        for it in group:
            parts.append(f"\n----- [{it['id']}] {it['title']} -----\n{it['body']}")
    system = "".join(parts)
    if salt:
        system = f"cache-salt: {salt}\n" + system
    return [{"role": "system", "content": system},
            {"role": "user", "content": task}]


def render_l1(items: list[dict], task: str, salt: str | None = None) -> list[dict]:
    """Compact index only; bodies arrive as ordinary messages on FETCH."""
    system = (h.SYSTEM_L1 + "\n" + h.EMULATED_PROTOCOL + "\n"
              + h.projection(items) + "\n")
    if salt:
        system = f"cache-salt: {salt}\n" + system
    return [{"role": "system", "content": system},
            {"role": "user", "content": task}]


FETCH_REPLY = ("ITEM {iid} -- full text follows.\n\n{body}")
FETCH_UNKNOWN = ("ERROR: no item with id {iid!r} in the library. "
                 "Reply with FETCH <item_id> or ANSWER.")
ANSWER_NUDGE = h.EMULATED_ANSWER


def check_answer(text: str | None, n_items: int) -> dict:
    """Every required field must carry its exact value."""
    text = text or ""
    flat = text.replace("*", "").replace("`", "")
    got, ok = {}, {}
    for field, want in fields_for(n_items).items():
        m = re.search(rf"{field}\s*[:=]?\s*([0-9][0-9,]*)", flat, re.I)
        val = m.group(1).replace(",", "") if m else None
        got[field] = val
        ok[field] = val == want
    return {"parsed": got, "per_field": ok,
            "facts_present": sum(1 for v in ok.values() if v),
            "facts_required": len(ok),
            "correct": all(ok.values())}


def item_index(items: list[dict]) -> dict[str, dict]:
    """id -> item, the lookup the FETCH protocol resolves against."""
    return {it["id"]: it for it in items}


def selfcheck() -> int:
    ok = True
    for n in (12, 30):
        for s in GRID_SIZES:
            items = load_items(n, s)
            task, fields = task_for(n), fields_for(n)
            c0 = render_c0(items, task)
            l1 = render_l1(items, task)
            c0_chars = sum(len(m["content"]) for m in c0)
            l1_chars = sum(len(m["content"]) for m in l1)
            bodies = sum(len(i["body"]) for i in items)
            # task must not name an item
            names_item = any(re.search(rf"\b{i['id']}\b", task) for i in items)
            from cx_corpus import FACT_SPECS  # local import: builder module
            fact_ok = all(FACT_SPECS[f][1] in c0[0]["content"]
                          for f in needed_for(n))
            no_leak = all(FACT_SPECS[f][1] not in l1[0]["content"]
                          for f in needed_for(n))
            ids_once = all(l1[0]["content"].count(f"[{i['id']}]") == 1 for i in items)
            print(f"n={n:2d} size={s:6d} items={len(items):2d} bodies={bodies:6d} "
                  f"c0={c0_chars:6d} l1={l1_chars:5d} "
                  f"task_names_item={names_item} facts_in_c0={fact_ok} "
                  f"no_fact_in_l1={no_leak} ids_once={ids_once}")
            ok &= (bodies == s and not names_item and fact_ok and no_leak
                   and ids_once and len(items) == n)
    print("SELFCHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selfcheck())
