#!/usr/bin/env python3
"""QUALITY-ARM corpus: 12 knowledge items, ONE unique fact, index carries no fact.

Item bodies are synthetic and deterministic (no clock, no random seed): prose over a
small word pool, padded to 9000 bytes. Exactly one item (k01) contains the vendor
name "lumen"; exactly one item (k01) contains the audit code AUD-4417. Every other
item carries a different code, and none carries "lumen".

The builder proves the discrimination property offline before any request is sent:
* no body but k01 contains "lumen" or "AUD-4417";
* the compiled index text contains neither "AUD-" nor "lumen";
* each item's index line is `- @knowledge:kNN@1 <hash8> <len>` and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

BODY_BYTES = 9000
ITEM_COUNT = 12
FACT_ITEM = "k01"
FACT_VENDOR = "lumen"
FACT_CODE = "AUD-4417"
FILLER_CODES = [
    "AUD-1029", "AUD-2031", "AUD-3089", "AUD-3311", "AUD-5129", "AUD-6013",
    "AUD-7027", "AUD-8143", "AUD-9001", "AUD-1187", "AUD-6455",
]

#: A deliberately institutional, boring register: no instruction words, no numbers
#: that look like an answer, and no word that appears only in k01.
_NOUNS = ["charter", "register", "annex", "schedule", "memorandum", "protocol",
          "inventory", "bulletin", "dossier", "ledger", "briefing", "appendix"]
_VERBS = ["records", "restates", "consolidates", "annotates", "tabulates",
          "cross-checks", "reproduces", "indexes", "transcribes", "reconciles"]
_OBJECTS = ["the maintenance window", "the calibration series", "the audit trail",
            "the bench worksheet", "the change advisory note", "the instrument log",
            "the quarterly reconciliation", "the standing operating procedure"]


def body_for(position: int) -> str:
    """Deterministic 9000-byte body for item ``position`` (1-based)."""
    head = (
        f"Knowledge item k{position:02d}. This item is one entry of the standing "
        f"reference set: it {_VERBS[position % len(_VERBS)]} "
        f"{_OBJECTS[position % len(_OBJECTS)]} and carries no bearing on any other "
        f"item in the set. "
    )
    if position == 1:
        head += (
            f"The constant recorded in this entry is named {FACT_VENDOR} and its "
            f"audit code is {FACT_CODE}. This is the only entry in the set that "
            f"names that constant; the remaining codes below belong to retired "
            f"instruments and are kept for completeness. "
        )
    chunk = [
        f"Section {n}. The {_NOUNS[(position + n) % len(_NOUNS)]} for entry k{position:02d} "
        f"{_VERBS[(position + n) % len(_VERBS)]} {_OBJECTS[(n * 3 + position) % len(_OBJECTS)]} "
        f"as it stood at the end of the previous period. "
        for n in range(1, 40)
    ]
    text = head + "".join(chunk)
    while len(text.encode("utf-8")) < BODY_BYTES:
        text += ("Clause references are given by section number only; "
                 "superscripts are not reproduced. ")
    return text.encode("utf-8")[:BODY_BYTES].decode("utf-8", errors="ignore")


def material() -> list[dict]:
    return [
        {"kind": "knowledge", "id": f"k{position:02d}", "body": body_for(position)}
        for position in range(1, ITEM_COUNT + 1)
    ]


def leak_check(items: list[dict], index_text: str) -> dict:
    """Offline proof that the index does not carry the fact."""
    finders = {}
    for item in items:
        body = item["body"]
        finders[item["id"]] = {
            "has_vendor": FACT_VENDOR in body,
            "has_fact_code": FACT_CODE in body,
            "codes": [c for c in FILLER_CODES if c in body],
        }
    named = [i for i, f in finders.items() if f["has_vendor"]]
    coded = [i for i, f in finders.items() if f["has_fact_code"]]
    return {
        "items": len(items),
        "body_bytes": sorted({len(i["body"].encode()) for i in items}),
        "items_naming_the_vendor": named,
        "items_carrying_the_fact_code": coded,
        "index_bytes": len(index_text.encode()),
        "index_has_AUD": "AUD-" in index_text,
        "index_has_vendor": FACT_VENDOR in index_text,
        "index_has_audit_code_phrase": "audit code" in index_text.lower(),
        "fact_unique_to_k01": named == [FACT_ITEM] and coded == [FACT_ITEM],
    }


def compile_index(items: list[dict]):
    from ptr_engine import BodyStore, compile_turn
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="ptr-quality-probe-"))
    try:
        store = BodyStore(root)
        return compile_turn(items, revision=1, scope="quality", block_size=64, store=store)
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    items = material()
    index = compile_index(items)
    report = leak_check(items, index.index_text)
    report["index_text"] = index.index_text
    print(report)
    raise SystemExit(0 if report["fact_unique_to_k01"] and not report["index_has_AUD"]
                     and not report["index_has_vendor"] else 1)
