#!/usr/bin/env python3
"""U4 baseline-grid probe (small, decisive, ~7 requests).

The unit card assumes a baseline law for a warm append::

    cached == 64 * floor(prompt_tokens / 64)   ->   uncached == prompt_tokens % 64

The 3-request smoke for this unit did NOT show that on a growing prompt: the
prompt went 935 -> 1804 -> 2643 tokens and ``cached_tokens`` went
0 -> 896 -> 896, i.e. it reused only the first request's aligned blocks and
never accumulated the appended ones.  If that is real, ``break_cost =
uncached - (prompt % 64)`` is wrong by construction, because an ordinary
appended turn would look like a break.

This probe decides between three hypotheses on one isolated salt:

H1 grid      every warm turn reuses ``64*floor(len/64)``            (brief)
H2 plateau   a warm append reuses only the first request's prefix    (smoke)
H3 tree      the tree holds every prompt; an append just matches the
             longest stored prefix, so a *repeat* of an intermediate
             prompt must hit it fully

Sequence (one chain, turn numbers chosen to separate the hypotheses)::

    1, 2, 3, 3(repeat), 4, 2(repeat), 6(skip 5)

* if a repeat of turn 3 hits ``64*floor(len3/64)`` -> the tree holds it (not H2
  for repeats), so the append path is what fails to match, not the insert;
* if the repeat also returns 896 -> the branch was never extended (H2).

Usage: ``python3 u4_grid_probe.py``
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import u4_cell as D  # noqa: E402
from resextract.context import StateNode, render  # noqa: E402

SEQUENCES = {
    # separates "tree holds every prompt" from "only the first request's
    # blocks are ever reused": repeats of stored prompts must hit fully.
    "mixed": [1, 2, 3, 3, 4, 2, 6],
    # pure append, no repeats: the exact access pattern of a live cell.
    "append": [1, 2, 3, 4, 5, 6],
}
OUT = HERE / "u4_grid_probe.json"
SALT_TAG = "gridprobe-v1"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(SEQUENCES), default="mixed")
    args = parser.parse_args(argv)
    SEQUENCE = SEQUENCES[args.mode]
    salt_tag = f"{SALT_TAG}-{args.mode}"
    out_path = HERE / f"u4_grid_probe_{args.mode}.json"

    corpus = D.load_corpus()
    session = corpus["sessions"][0]
    salt = D.cell_salt("append", salt_tag, session["case_id"])
    preamble = session["preamble"]
    turns = [t["text"] for t in session["turns"]]

    D.install_usage_probe()
    client = D.client_mod.ChatClient()
    started = time.monotonic()
    send = D.make_send(client, started)

    fd = D.acquire_lock(D.LOCK_PATH, D.LOCK_TIMEOUT_S)
    if fd is None:
        print(json.dumps({"status": "blocked", "reason": "lock timeout"}))
        return 3

    chain: list[StateNode] = [StateNode.create(preamble, "invariant")]
    rendered: dict[int, list[dict[str, str]]] = {}
    rows: list[dict] = []
    try:
        for target in SEQUENCE:
            while len(chain) - 1 < target:
                n = len(chain)
                chain = chain + [
                    StateNode.create(turns[n - 1], "delta", parent=chain[-1], turn=n)
                ]
            if target not in rendered:
                rendered[target] = render(
                    "naive_append",
                    chain[: target + 1],
                    preamble=preamble,
                    volatile={},
                    salt=salt,
                )
            messages = rendered[target]
            D.CURRENT.update({"cell": "U4/gridprobe", "policy": "none", "turn": target})
            prompt, cached, _completion, ttft, _wall, status, _text = send(messages)
            rows.append(
                {
                    "turn": target,
                    "prompt_tokens": prompt,
                    "cached_tokens": cached,
                    "uncached": max(0, prompt - cached),
                    "grid_residual": max(0, prompt - cached) - (prompt % 64),
                    "grid_expected_cached": 64 * (prompt // 64),
                    "ttft_ms": round(ttft, 1),
                    "status": status,
                }
            )
            print(json.dumps(rows[-1], sort_keys=True), flush=True)
    finally:
        D.release_lock(fd)

    # Summarise against the three hypotheses.
    by_turn: dict[int, list[dict]] = {}
    for row in rows:
        by_turn.setdefault(row["turn"], []).append(row)
    repeats = {
        turn: {
            "hits": [(r["prompt_tokens"], r["cached_tokens"]) for r in group[1:]],
            "full_grid_would_be": 64 * (group[0]["prompt_tokens"] // 64),
        }
        for turn, group in by_turn.items()
        if len(group) > 1
    }
    appends = [
        {
            "turn": row["turn"],
            "prompt_tokens": row["prompt_tokens"],
            "cached_tokens": row["cached_tokens"],
            "uncached": row["uncached"],
        }
        for row in rows
    ]
    verdict = {
        "observed": appends,
        "repeats": repeats,
        "requests": D.COUNTS["requests"],
        "null_coercions": D.COUNTS["null_coercions"],
        "note": (
            "H1 (grid on append) is supported only if every append row has "
            "cached == 64*floor(prompt/64).  Otherwise the break_cost baseline "
            "must be measured per turn, not assumed."
        ),
    }
    out_path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out_path), **verdict}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
