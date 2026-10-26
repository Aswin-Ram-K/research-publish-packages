#!/usr/bin/env python3
"""A worked example, runnable offline in one process.

    python3 experiments/ptr-engine/examples/worked_example.py

It builds a ~30,000-character corpus of 12 items, compiles it into an index at turn
end, prints the index size, the body size and the ratio

    r = bodies / index

then resolves two refs and prints the byte sizes. No network, no model, no server:
the point measured here is the pointer engine's own overhead, which is what a later
measurement of cache behaviour multiplies.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from ptr_engine import (  # noqa: E402
    BodyStore,
    Ledger,
    Scope,
    append_cost,
    build_prompt,
    compile_turn,
    depth,
    parse,
    resolve,
)

TARGET_CHARS = 30_000
BLOCK_SIZE = 64
REVISION = 1
SCOPE = "worked-example"


def corpus() -> list[dict]:
    """Exactly 12 items totalling exactly 30,000 characters, of assorted kinds."""
    kinds = [
        "knowledge",
        "artifact",
        "memory",
        "decision",
        "evidence",
        "task",
        "policy",
        "world",
        "hypothesis",
        "meta",
        "execution",
    ]
    plan_body = json.dumps({"goal": "read only what is asked", "rev": REVISION})
    per_item = (TARGET_CHARS - len(plan_body)) // (len(kinds) + 1)
    items: list[dict] = []
    for position, kind in enumerate(kinds, start=1):
        sentence = (
            f"{kind} item {position}: the pointer engine stores this body once, "
            "addresses it by sha256, and sends only the index line on the turn "
            "where the model does not ask for it. "
        )
        repeats = per_item // len(sentence) + 1
        items.append({"kind": kind, "id": f"i{position:02d}", "body": (sentence * repeats)[:per_item]})
    used = sum(len(item["body"]) for item in items) + len(plan_body)
    items[-1]["body"] += "x" * (TARGET_CHARS - used)  # pad so the corpus is exact
    items.append(
        {
            "kind": "artifact",
            "id": "plan",
            "body": plan_body,
            "pointer": "/goal",
            "ext": ".json",
        }
    )
    assert len(items) == 12
    assert sum(len(item["body"]) for item in items) == TARGET_CHARS
    return items


def main() -> int:
    material = corpus()
    warmpool = Path(tempfile.mkdtemp(prefix="ptr-worked-example-"))
    try:
        store = BodyStore(warmpool)
        ledger = Ledger(warmpool / "ledger.jsonl", block_size=BLOCK_SIZE)

        total_body = sum(len(item["body"].encode("utf-8")) for item in material)
        index = compile_turn(
            material, revision=REVISION, scope=SCOPE, block_size=BLOCK_SIZE, store=store
        )
        scope = Scope(name=SCOPE, index=index, block_size=BLOCK_SIZE)

        ratio = total_body / index.index_size
        print(f"items                 : {len(material)}  (12 items, {TARGET_CHARS} chars)")
        print(f"total body bytes      : {total_body}")
        print(f"index bytes           : {index.index_size}")
        print(f"index lines           : {len(index.lines)}")
        print(f"r = bodies/index      : {ratio:.1f}x")
        print(f"index sha256          : {index.index_sha256}")
        print(f"depth(root)           : {depth(index.root_entry())}  (hot)")
        print(f"depth(leaf)           : {depth(next(iter(index.entries.values())))}  (cold)")
        print()

        print("zero-resolution prompt:")
        bare = build_prompt(index, {}, ledger)
        print(f"  bytes               : {len(bare.encode('utf-8'))}")
        print()

        print("two resolves:")
        for text in ("@knowledge:i01@1", "@artifact:plan#/goal@1"):
            ref = parse(text)
            target = resolve(ref, scope, ledger)
            body = store.get(target)
            print(
                f"  {text:<26} bytes={len(body):>5}  "
                f"hash={target.hash[:19]}…  append_cost={append_cost(ref, BLOCK_SIZE)}"
            )

        resolved = {parse("@knowledge:i01@1"): store.get(
            resolve(parse("@knowledge:i01@1"), scope, ledger)
        )}
        with_one = build_prompt(index, resolved, ledger)
        print()
        print(f"one-body prompt bytes : {len(with_one.encode('utf-8'))}")
        print(f"ledger rows           : {len(ledger)}")
        print(f"ledger file           : {ledger.path}")
        print()
        print("warmpool layout:")
        for path in sorted(p for p in warmpool.rglob("*") if p.is_file())[:4]:
            print(f"  {path.relative_to(warmpool)}  ({path.stat().st_size} B)")
        return 0
    finally:
        shutil.rmtree(warmpool, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
