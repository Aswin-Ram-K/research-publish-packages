#!/usr/bin/env python3
"""Aggregate the crossover rows into the two tables that decide the question.

Definitions, stated rather than hidden
--------------------------------------
prompt_tokens        Summed over every request in a run. C0 is always 1 request;
                     L1 is 1 + one request per fetch round, so L1 pays for its
                     tool turns instead of having them for free.
fetched_body_tokens  fetched_body_chars x the chars-per-token ratio the SAME model
                     realises on the C0 request of the SAME corpus cell. A
                     character-based estimate, applied symmetrically; the ratio is
                     printed so the estimate can be checked.
realised_saving      (C0_prompt - L1_prompt - fetched_body_tokens) / C0_prompt
                     Positive = L1 cheaper. Credits L1 for not shipping the bodies
                     it never fetched.
billed_saving        (C0_uncached - L1_uncached) / C0_uncached, where
                     uncached = prompt_tokens - cached_tokens. This is the number
                     that decides whether the technique is worth anything: a cached
                     prefix token is not billed, so shipping 30k chars of prefix to
                     a warm cache is nearly free and L1's extra round trips are not.
                     Where the server reports no cache statistics at all
                     (prompt_tokens_details: null), cached tokens are recorded as
                     unknown and the column is labelled "cache-blind" -- it then
                     assumes 0 cached, which is the client's only defensible
                     assumption and an upper bound on L1's disadvantage.
"""
from __future__ import annotations

import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parent


def load():
    """Prefer per-model tagged files (one process per model) over the canonical pair."""
    tagged_rows = sorted(ROOT.glob("rows_*.jsonl"))
    if tagged_rows:
        rows, runs = [], []
        for f in tagged_rows:
            rows += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        for f in sorted(ROOT.glob("runs_*.json")):
            runs += json.loads(f.read_text())
        return rows, runs
    rows = [json.loads(l) for l in (ROOT / "rows.jsonl").read_text().splitlines() if l.strip()]
    runs = json.loads((ROOT / "runs.json").read_text())
    return rows, runs


def cell_of(r: dict) -> tuple:
    return (r["model"], r["n_items"], r["size"], r["cache_state"])


def aggregate(runs: list[dict], rows: list[dict]) -> dict:
    """One aggregate per (model, n_items, size, cache_state)."""
    # chars/token measured on each cell's own C0 request
    c0_ratio = {}
    for r in rows:
        if r["arm"] != "c0" or r.get("error") or not r["prompt_tokens"]:
            continue
        k = (r["model"], r["n_items"], r["size"])
        c0_ratio.setdefault(k, []).append(r["sent_chars"] / r["prompt_tokens"])

    cells: dict[tuple, dict] = {}
    for r in runs:
        k = cell_of(r)
        c = cells.setdefault(k, {"model": r["model"], "n_items": r["n_items"],
                                 "size": r["size"], "cache_state": r["cache_state"],
                                 "needed_fraction": r["needed_fraction"],
                                 "arms": {}, "reps": set()})
        c["arms"].setdefault(r["arm"], []).append(r)
        c["reps"].add(r["rep"])

    out = {}
    for k, c in cells.items():
        c0r = c["arms"].get("c0") or []
        l1r = c["arms"].get("l1") or []
        if not c0r or not l1r:
            continue
        ratio = statistics.mean(c0_ratio.get((c["model"], c["n_items"], c["size"]), [4.0]))

        def mean(xs):
            return statistics.mean(xs) if xs else None

        c0_prompt = mean([r["prompt_tokens"] for r in c0r if not r.get("error")])
        l1_prompt = mean([r["prompt_tokens"] for r in l1r if not r.get("error")])
        c0_cached = mean([r["cached_tokens"] or 0 for r in c0r])
        l1_cached = mean([r["cached_tokens"] or 0 for r in l1r])
        fetched_tok = mean([r["fetched_body_chars"] * ratio for r in l1r])
        reporting = any(r.get("cache_reporting") for r in c0r + l1r)

        c0_unc = (c0_prompt or 0) - c0_cached
        l1_unc = (l1_prompt or 0) - l1_cached
        realised = ((c0_prompt - l1_prompt - fetched_tok) / c0_prompt
                    if c0_prompt else None)
        billed = ((c0_unc - l1_unc) / c0_unc) if c0_unc else None

        out[k] = {
            "model": c["model"], "n_items": c["n_items"], "size": c["size"],
            "cache_state": c["cache_state"],
            "needed_fraction": c["needed_fraction"],
            "chars_per_token": round(ratio, 3),
            "c0_prompt": round(c0_prompt, 1) if c0_prompt else None,
            "l1_prompt": round(l1_prompt, 1) if l1_prompt else None,
            "c0_cached": round(c0_cached, 1),
            "l1_cached": round(l1_cached, 1),
            "c0_uncached": round(c0_unc, 1),
            "l1_uncached": round(l1_unc, 1),
            "fetched_body_tokens": round(fetched_tok, 1),
            "realised_saving": round(realised, 4) if realised is not None else None,
            "billed_saving": round(billed, 4) if billed is not None else None,
            "cache_reporting": reporting,
            "c0_rounds": mean([r["rounds"] for r in c0r]),
            "l1_rounds": mean([r["rounds"] for r in l1r]),
            "fetch_count": mean([r["fetch_count"] for r in l1r]),
            "fetch_ids": sorted({i for r in l1r for i in r["fetch_ids"]}),
            "correct_c0": sum(1 for r in c0r if r["correct"]),
            "correct_l1": sum(1 for r in l1r if r["correct"]),
            "reps": len(c["reps"]),
            "errors": sum(1 for r in c0r + l1r if r.get("error")),
            "l1_facts": mean([r["facts_present"] for r in l1r]),
            "l1_all_needed_fetched": sum(1 for r in l1r if r.get("all_needed_fetched")),
        }
    return out


def pct(x):
    return "n/a" if x is None else f"{x*100:+.1f}%"


def table(cells: dict, metric: str, title: str, note: str, out: list) -> None:
    out.append(f"\n### {title}\n")
    out.append(note + "\n")
    models = sorted({c["model"] for c in cells.values()})
    header = "| items | corpus chars | needed | " + " | ".join(
        f"{m} cold | {m} warm" for m in models) + " |"
    out.append(header)
    out.append("|" + "---|" * (3 + 2 * len(models)))
    for n in sorted({c["n_items"] for c in cells.values()}):
        for s in sorted({c["size"] for c in cells.values()}):
            row = [f"{n}", f"{s:,}"]
            any_cell = next((c for c in cells.values()
                             if c["n_items"] == n and c["size"] == s), None)
            row.append(f"{any_cell['needed_fraction']*100:.0f}%" if any_cell else "?")
            for m in models:
                for cs in ("cold", "warm"):
                    c = cells.get((m, n, s, cs))
                    row.append(pct(c[metric]) if c else "missing")
            out.append("| " + " | ".join(row) + " |")


def main() -> None:
    rows, runs = load()
    cells = aggregate(runs, rows)
    (ROOT / "analysis.json").write_text(
        json.dumps({"cells": [v for _, v in sorted(cells.items(), key=lambda kv: str(kv[0]))],
                    "rows": len(rows), "runs": len(runs)},
                   indent=2) + "\n", encoding="utf-8")

    out: list[str] = []
    w = out.append
    w("# RESULTS — lazy instruction loading: cold/warm crossover sweep\n")
    w(f"Requests recorded: **{len(rows)}** rows across **{len(runs)}** runs. "
      "One JSONL row per request; a C0 run is exactly 1 request, an L1 run is "
      "1 + one request per fetch round, so L1's extra round trips are counted, "
      "not hidden.\n")

    models = sorted({c["model"] for c in cells.values()})
    blind = [m for m in models
             if not any(c["cache_reporting"] for c in cells.values() if c["model"] == m)]
    prot = sorted({r.get("fetch_protocol") for r in runs if r.get("fetch_protocol")})
    w(f"Fetch protocol on the L1 arm, both models: `{'/'.join(prot) or 'text_emulated'}` "
      "— the native-tool-call vs text-emulation confound of the first arm is removed. "
      "C0 rows carry no fetch protocol by construction (nothing to fetch).\n")
    if blind:
        w(f"\n**Cache instrument is blind on: {', '.join(blind)}.** That server returns "
          "`prompt_tokens_details: null` on every call, so `cached_tokens` is unknown "
          "there, not zero. Its rows are recorded with `cache_reporting: false` and the "
          "billed column for it assumes 0 cached — the only defensible client assumption, "
          "and an upper bound on L1's disadvantage. Its *realised* column is unaffected: "
          "`prompt_tokens` is real either way.\n")

    table(cells, "realised_saving",
          "Table 1 — realised saving",
          "`(C0_prompt − L1_prompt − fetched_body_tokens) / C0_prompt`. Positive = L1 "
          "cheaper. Credits L1 for the bodies it never fetched. Fetched body tokens are "
          "estimated as `fetched_body_chars × chars_per_token`, where the ratio is measured "
          "on that same model's C0 request for that same corpus.", out)
    table(cells, "billed_saving",
          "Table 2 — billed saving (the one that decides)",
          "`(C0_uncached − L1_uncached) / C0_uncached`, `uncached = prompt_tokens − "
          "cached_tokens`. A cached prefix token is not billed, so a warm C0 ships 30k "
          "chars for almost nothing while L1 still pays a round trip per fetch.", out)

    table(cells, "c0_uncached",
          "Table 2b - absolute uncached prompt tokens (the base under Table 2's percentages)",
          "A percentage over a ~20-token base is not a cost decision on its own, so the "
          "absolute tokens are shown: this is what a warm C0 and a warm L1 each still bill "
          "after the prefix is cached.", out)
    out.append("")
    out.append("| items | corpus chars | model | cache | C0 uncached | L1 uncached | "
               "delta (L1 - C0) |")
    out.append("|---|---|---|---|---|---|---|")
    for k in sorted(cells, key=lambda k: (cells[k]["n_items"], cells[k]["size"],
                                          cells[k]["model"], cells[k]["cache_state"])):
        c = cells[k]
        out.append(f"| {c['n_items']} | {c['size']:,} | {c['model']} | {c['cache_state']} | "
                   f"{c['c0_uncached']:.0f} | {c['l1_uncached']:.0f} | "
                   f"{c['l1_uncached']-c['c0_uncached']:+.0f} |")

    # ---- correctness + fetches
    w("\n### Table 3 — correctness (reps correct / reps) and fetch counts\n")
    w("| items | corpus chars | model | cache | C0 correct | L1 correct | L1 mean fetches "
      "| L1 fetched ids | L1 facts found |")
    w("|---|---|---|---|---|---|---|---|---|")
    for k in sorted(cells, key=lambda k: (cells[k]["n_items"], cells[k]["size"],
                                          cells[k]["model"], cells[k]["cache_state"])):
        c = cells[k]
        w(f"| {c['n_items']} | {c['size']:,} | {c['model']} | {c['cache_state']} | "
          f"{c['correct_c0']}/{c['reps']} | {c['correct_l1']}/{c['reps']} | "
          f"{c['fetch_count']:.1f} | {', '.join(c['fetch_ids']) or '—'} | "
          f"{c['l1_facts']:.1f} |")

    # ---- regime proof
    w("\n### Table 4 — the regime, proved per cell rather than assumed\n")
    w("| model | cache state | mean cached / prompt (C0) | mean cached / prompt (L1) | "
      "cache reported |")
    w("|---|---|---|---|---|")
    for m in models:
        for cs in ("cold", "warm"):
            sel = [c for c in cells.values() if c["model"] == m and c["cache_state"] == cs]
            if not sel:
                continue
            c0r = statistics.mean([(c["c0_cached"] / c["c0_prompt"]) for c in sel
                                   if c["c0_prompt"]])
            l1r = statistics.mean([(c["l1_cached"] / c["l1_prompt"]) for c in sel
                                   if c["l1_prompt"]])
            w(f"| {m} | {cs} | {c0r*100:.1f}% | {l1r*100:.1f}% | "
              f"{'yes' if sel[0]['cache_reporting'] else 'NO — null'} |")

    # ---- crossover point
    w("\n### Crossover point\n")
    for m in models:
        for cs in ("cold", "warm"):
            wins = [c for c in cells.values()
                    if c["model"] == m and c["cache_state"] == cs
                    and (c["billed_saving"] or 0) > 0]
            losses = [c for c in cells.values()
                      if c["model"] == m and c["cache_state"] == cs
                      and (c["billed_saving"] or 0) <= 0]
            if wins:
                best = min(wins, key=lambda c: (c["size"], c["n_items"]))
                w(f"- **{m}, {cs}**: billed saving is positive from "
                  f"{best['size']:,} chars / {best['n_items']} items "
                  f"({best['needed_fraction']*100:.0f}% needed) — "
                  f"{pct(best['billed_saving'])} there.")
            else:
                w(f"- **{m}, {cs}**: NO crossover in the swept range — L1 loses on billed "
                  f"tokens in all {len(losses)} cells.")
        # worst cell for this model
        warm = [c for c in cells.values() if c["model"] == m and c["cache_state"] == "warm"]
        if warm:
            worst = min(warm, key=lambda c: c["billed_saving"] or 0)
            w(f"- {m}, warm, worst cell: {worst['size']:,} chars / {worst['n_items']} items "
              f"→ billed {pct(worst['billed_saving'])}, realised "
              f"{pct(worst['realised_saving'])}.")

    (ROOT / "TABLES.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
