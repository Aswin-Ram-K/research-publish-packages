#!/usr/bin/env python3
"""CX-V2: offline reconstruction of U4's fork and summarise prompts.

Replays the same chains U4 sent (same corpus, same per-cell salts, same
budget/keep_last/summariser) through runner.run_cell with a fake `send` that
digests the message list -- no network, no score of the unit's tables.

Question: at the same event, were the fork and summarise arms' prompts the
same bytes?  The rows only carry `prefix_sha256`, which for NAIVE_APPEND is
sha256(messages[:1]) (runner.prefix_sha256 keep=1) -- a head-only digest, so it
cannot answer it.  This script computes the full-prompt digest and the
body-only digest as well.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent / "U4"
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "src"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


from resextract.context import (  # noqa: E402
    CacheMeter,
    CompactionPolicy,
    StateNode,
    canonical_bytes,
    default_est_tokens,
)

runner = _load("cx_runner", REPO / "experiments/context-cache/runner.py")
u4 = _load("cx_u4cell", CELL / "u4_cell.py")

corpus = json.loads((CELL / "u4_sessions.json").read_text(encoding="utf-8"))
units = {u["cell"].cell: u for u in u4.build_units(corpus)}

CAPTURE: list[dict] = []


def make_send():
    def send(messages):
        body = messages[1:]
        CAPTURE.append(
            {
                "messages": len(messages),
                "full": hashlib.sha256(canonical_bytes(messages)).hexdigest(),
                "head": hashlib.sha256(canonical_bytes(messages[:1])).hexdigest(),
                "body": hashlib.sha256(canonical_bytes(body)).hexdigest() if body else "-",
                "body_bytes": len(canonical_bytes(body)) if body else 0,
                "chars": sum(len(m["content"]) for m in messages),
            }
        )
        # prompt_tokens is not known offline; report a length proxy so the
        # call cannot silently look like the live row file.
        return (len(messages), 0, 1, 0.0, 0.0, 200, "")

    return send


def run(compaction: str, session: str):
    key = f"U4/append/{compaction}/{session}"
    unit = units[key]
    CAPTURE.clear()
    runner.run_cell(
        unit["cell"],
        unit["case"],
        make_send(),
        CacheMeter(),
        compaction=unit["compaction"],
        summarizer=runner._truncating_summarizer,
        est_tokens=default_est_tokens,
    )
    return list(CAPTURE)


print(f"units rebuilt: {len(units)}")
print(f"corpus sessions: {[s['case_id'] for s in corpus['sessions']]}")

live_rows = [json.loads(l) for l in (CELL / "u4_rows.jsonl").read_text().splitlines() if l.strip()]
live = {}
for r in live_rows:
    live.setdefault(r["cell"], {})[r["turn"]] = r

for session in ("u4-s1", "u4-s2", "u4-s3"):
    sm = run("summarise_in_place", session)
    fk = run("fork", session)
    print(f"\n--- {session}: {len(sm)} vs {len(fk)} turns captured")
    # faithfulness: reconstructed head digest == the live row's prefix_sha256
    ok_s = sum(1 for i, cap in enumerate(sm, 1)
               if live[f"U4/append/summarise_in_place/{session}"][i]["prefix_sha256"] == cap["head"])
    ok_f = sum(1 for i, cap in enumerate(fk, 1)
               if live[f"U4/append/fork/{session}"][i]["prefix_sha256"] == cap["head"])
    print(f"reconstruction check (head digest == live row prefix_sha256): "
          f"summarise {ok_s}/{len(sm)}, fork {ok_f}/{len(fk)}")
    same_full = sum(1 for a, b in zip(sm, fk) if a["full"] == b["full"])
    same_body = sum(1 for a, b in zip(sm, fk) if a["body"] == b["body"])
    same_head = sum(1 for a, b in zip(sm, fk) if a["head"] == b["head"])
    same_bytes = sum(1 for a, b in zip(sm, fk) if a["body_bytes"] == b["body_bytes"])
    print(f"turn-by-turn: full-prompt digest equal {same_full}/{len(sm)}; "
          f"head equal {same_head}; body digest equal {same_body}; body bytes equal {same_bytes}")
    d = [(i, a["full"][:8], b["full"][:8], a["body_bytes"], b["body_bytes"])
         for i, (a, b) in enumerate(zip(sm, fk), 1) if a["full"] != b["full"]]
    print(f"   full-prompt differences: {len(d)} turns; first 3 {d[:3]}")
    print(f"   body bytes at turn 1/12/13/44: "
          f"{[(i, sm[i-1]['body_bytes'], fk[i-1]['body_bytes']) for i in (1,12,13,44)]}")
    print(f"   live prompt_tokens turn 1: summarise {live[f'U4/append/summarise_in_place/{session}'][1]['prompt_tokens']} "
          f"fork {live[f'U4/append/fork/{session}'][1]['prompt_tokens']}; "
          f"identical full prompt would force identical prompt_tokens")

# Where does each arm's distinguishing information live?
print("\n--- static: what budget.compact() puts in the prompt")
for pol in (CompactionPolicy.SUMMARISE_IN_PLACE, CompactionPolicy.FORK):
    chain = [StateNode.create("PREAMBLE", "invariant")]
    for t in range(1, 15):
        chain.append(StateNode.create(f"body {t}", "delta", parent=chain[-1], turn=t))
    new_chain, event = u4.budget_compact(chain, pol) if hasattr(u4, "budget_compact") else (None, None)
from resextract.context import compact  # noqa: E402

for pol in (CompactionPolicy.SUMMARISE_IN_PLACE, CompactionPolicy.FORK):
    chain = [StateNode.create("PREAMBLE", "invariant")]
    for t in range(1, 15):
        chain.append(StateNode.create(f"body {t}", "delta", parent=chain[-1], turn=t))
    new_chain, event = compact(chain, pol, keep_last=2,
                               summarizer=runner._truncating_summarizer)
    print(f"  {pol.value:>18}: kinds={[n.kind for n in new_chain]} "
          f"texts={[n.text[:14] for n in new_chain]} forked={event['forked']}")

print("\n--- U4 renderer check")
print("  u4_cell.RENDER =", u4.RENDER.value)
print("  documented fork usage: read u4_cell.py RENDER constant; POINTER_FORK never imported:",
      "POINTER_FORK" not in (CELL / "u4_cell.py").read_text())
