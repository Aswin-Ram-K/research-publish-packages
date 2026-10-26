#!/usr/bin/env python3
"""Aggregate run2/rows.jsonl into the crossover table.

Two numbers per (size, needed fraction, model, cache state) cell:

  saving_billed = (C0_uncached - L1_uncached) / C0_uncached,  uncached = prompt - cached
      THE DECISION NUMBER. A cached prefix token is not billed, so a warm C0 that
      ships the whole corpus can still be cheaper than a small, uncached L1 prompt.

  saving_prompt = (C0_prompt - L1_prompt - fetched_body_tokens) / C0_prompt
      the naive prompt-size saving, shown for contrast only. Fetched body tokens are
      estimated at a fixed 4 chars/token and the estimate is printed per cell.

Honesty rules baked in:
  * `cached_tokens: null` means the server reported no cache statistics at all
    (`prompt_tokens_details: null`). That is a BLIND instrument, not a cache miss.
    Blind cells are reported as blind and their uncached figure is labelled an upper
    bound; they are never silently mixed with measured cache hits.
  * 1 rep per cell: this locates a crossover, it does not test significance.
  * No cell is dropped because it looks bad. A failing cell carries its failure.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent          # run2/
ROWS = ROOT / "rows.jsonl"
OUT = ROOT.parent / "cells.json"

CHARS_PER_TOKEN = 4  # for the fetch-body contrast estimate only


def load() -> list[dict]:
    """Aggregate rows per run, and treat a cell as stolen if two runs share a key."""
    runs: dict[tuple, dict] = {}
    with ROWS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r["model"], r["n_items"], r["size"], r["arm"], r["cache_state"])
            a = runs.setdefault(key, {"prompt": 0, "cached": 0, "blind": 0,
                                      "requests": 0, "chats": set(), "ids": [],
                                      "protocol": r.get("protocol")})
            a["prompt"] += r.get("prompt_tokens") or 0
            a["requests"] += 1
            if r.get("cached_tokens") is None:
                a["blind"] += 1
            else:
                a["cached"] += r["cached_tokens"]
            # Two concurrent writers can append to the same key. Each run has one or
            # more requests; a duplicate "round 1" means a collision, so group by the
            # set of rounds rather than by row count.
            a["chats"].add(r.get("round"))
            if r.get("fetched_item"):
                a["ids"].append(r["fetched_item"])
    return [{"key": k, **v} for k, v in runs.items()]


def main() -> int:
    agg = {(x["key"]): x for x in load()}
    sums = json.loads((ROOT / "runs.json").read_text(encoding="utf-8"))
    meta = {(r["model"], r["n_items"], r["size"], r["arm"], r["cache_state"]): r
            for r in sums}

    keys = sorted({(m, n, s, cs) for (m, n, s, a, cs) in agg})
    cells = []
    for (m, n, s, cs) in keys:
        kc = (m, n, s, "c0", cs)
        kl = (m, n, s, "l1", cs)
        if kc not in agg or kl not in agg:
            cells.append({"model": m, "n_items": n, "size": s, "cache_state": cs,
                          "complete": False})
            continue
        c0, l1 = agg[kc], agg[kl]
        mc0, ml1 = meta.get(kc, {}), meta.get(kl, {})
        c0_unc = c0["prompt"] - c0["cached"]
        l1_unc = l1["prompt"] - l1["cached"]
        fb = ml1.get("fetched_body_chars") or 0
        ftok = round(fb / CHARS_PER_TOKEN)
        cells.append({
            "complete": True, "model": m, "n_items": n, "size": s,
            "needed_fraction": round((2 if n == 12 else 6) / n, 4),
            "cache_state": cs,
            "c0_prompt": c0["prompt"], "c0_cached": c0["cached"], "c0_uncached": c0_unc,
            "c0_requests": c0["requests"], "c0_blind": c0["blind"] == c0["requests"],
            "l1_prompt": l1["prompt"], "l1_cached": l1["cached"], "l1_uncached": l1_unc,
            "l1_requests": l1["requests"], "l1_blind": l1["blind"] == l1["requests"],
            "c0_hit": round(c0["cached"] / c0["prompt"], 4) if c0["prompt"] else None,
            "l1_hit": round(l1["cached"] / l1["prompt"], 4) if l1["prompt"] else None,
            "fetched_body_chars": fb, "fetched_body_tokens_est": ftok,
            "saving_billed": round((c0_unc - l1_unc) / c0_unc, 4) if c0_unc else None,
            "saving_prompt": (round((c0["prompt"] - l1["prompt"] - ftok) / c0["prompt"], 4)
                              if c0["prompt"] else None),
            "c0_correct": mc0.get("correct"), "l1_correct": ml1.get("correct"),
            "c0_facts": f"{mc0.get('facts_present')}/{mc0.get('facts_required')}",
            "l1_facts": f"{ml1.get('facts_present')}/{ml1.get('facts_required')}",
            "l1_fetch_count": ml1.get("fetch_count"),
            "l1_rounds": ml1.get("rounds"),
            "l1_fetch_ids": ml1.get("fetch_ids"),
            "error": ml1.get("error") or mc0.get("error"),
        })

    cells.sort(key=lambda r: (r["model"], r["n_items"], r["size"], r["cache_state"]))
    OUT.write_text(json.dumps(cells, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hdr = (f"{'model':11s} {'items':>5s} {'size':>6s} {'cache':>4s} | "
           f"{'C0 prompt':>9s} {'cached':>7s} {'uncached':>8s} | "
           f"{'L1 prompt':>9s} {'cached':>7s} {'uncached':>8s} | "
           f"{'req':>5s} {'fch':>3s} {'fetchB':>6s} | {'bill':>7s} {'prompt':>7s} | "
           f"{'C0':>5s} {'L1':>5s}")
    print(hdr)
    print("-" * len(hdr))
    for r in cells:
        if not r.get("complete"):
            print(f"INCOMPLETE {r}")
            continue
        bl = "B" if (r["c0_blind"] or r["l1_blind"]) else " "
        print(f"{r['model']:11s} {r['n_items']:5d} {r['size']:6d} {r['cache_state']:>4s} | "
              f"{r['c0_prompt']:9d} {r['c0_cached']:7d} {r['c0_uncached']:8d} | "
              f"{r['l1_prompt']:9d} {r['l1_cached']:7d} {r['l1_uncached']:8d} | "
              f"{r['c0_requests']}/{r['l1_requests']:<3d} {r['l1_fetch_count'] or 0:3d} "
              f"{r['fetched_body_chars']:6d} | "
              f"{r['saving_billed']*100:+6.1f}% {r['saving_prompt']*100:+6.1f}% | "
              f"{r['c0_facts']:>5s} {r['l1_facts']:>5s}{bl}")

    print("\nwarm-prefix decision (saving_billed, positive = L1 cheaper):")
    for r in cells:
        if r.get("complete") and r["cache_state"] == "warm":
            print(f"  {r['model']:11s} n={r['n_items']:2d} size={r['size']:6d}: "
                  f"{r['saving_billed']*100:+6.1f}%  "
                  f"({'L1 WINS' if r['saving_billed'] > 0 else 'C0 WINS'})")
    print("\ncold-prefix decision (saving_billed):")
    for r in cells:
        if r.get("complete") and r["cache_state"] == "cold":
            print(f"  {r['model']:11s} n={r['n_items']:2d} size={r['size']:6d}: "
                  f"{r['saving_billed']*100:+6.1f}%  "
                  f"({'L1 WINS' if r['saving_billed'] > 0 else 'C0 WINS'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
