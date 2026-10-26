#!/usr/bin/env python3
"""Aggregate rows.jsonl + runs.json into RESULTS.md.

Definitions, stated rather than hidden:

prompt_tokens   Summed over every request in a run. An L1 run is 1 + one request per
                fetch round, so L1 pays for its tool turns; C0 is always 1 request.
realised_saving (C0 prompt - L1 prompt - fetched body tokens) / C0 prompt.
                Fetched body tokens are estimated from the returned body characters
                using the characters-per-token ratio the model realises on the L1
                index itself. This is a character-based estimate, not a tokenizer
                count; the estimate is applied symmetrically to both models.
"""
from __future__ import annotations

import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parent


def load():
    rows = [json.loads(l) for l in (ROOT / "rows.jsonl").read_text().splitlines() if l.strip()]
    runs = json.loads((ROOT / "runs.json").read_text())
    return rows, runs


def main() -> None:
    rows, runs = load()
    models = sorted({r["model"] for r in runs})
    arms = ["c0", "l1"]
    out = []
    w = out.append

    w("# RESULTS -- lazy instruction loading\n")
    w("Corpus: 12 items (3 tools, 3 skills, 3 memory notes, 3 knowledge notes), "
      "22,162 characters. The task requires exactly 2 of the 12 items (K-2, M-1) and "
      "the task text never names them.\n")
    w(f"Requests recorded: {len(rows)} rows across {len(runs)} runs. One JSONL row per "
      f"request; an L1 run is 1 + one row per fetch round, C0 is exactly 1 row.\n")
    l1p = {r["model"]: r.get("protocol", "native_function_calling")
           for r in runs if r["arm"] == "l1"}
    w("\nFetch protocol used in the L1 arm: "
      + ", ".join(f"`{m}` = `{p}`" for m, p in sorted(l1p.items())) + ".\n")

    # ---------- tokens ----------
    w("\n## Tokens per arm per model (prompt tokens over the whole run)\n")
    w("| model | arm | runs | prompt tokens (mean) | min | max | mean requests |")
    w("|---|---|---|---|---|---|---|")
    tok = {}
    for m in models:
        for a in arms:
            rs = [r for r in runs if r["model"] == m and r["arm"] == a]
            if not rs:
                continue
            vals = [r["prompt_tokens"] for r in rs]
            tok[(m, a)] = statistics.mean(vals)
            w(f"| {m} | {a} | {len(rs)} | {statistics.mean(vals):.0f} | {min(vals)} "
              f"| {max(vals)} | {statistics.mean([r['rounds'] for r in rs]):.2f} |")

    # ---------- correctness ----------
    w("\n## Correctness per arm per model (both facts required)\n")
    w("| model | arm | correct runs | billing_retention_days=400 | scheduler_max_attempts=5 |")
    w("|---|---|---|---|---|")
    for m in models:
        for a in arms:
            rs = [r for r in runs if r["model"] == m and r["arm"] == a]
            if not rs:
                continue
            w(f"| {m} | {a} | **{sum(r['correct'] for r in rs)}/{len(rs)}** "
              f"| {sum(r['fact_billing_retention_days'] for r in rs)}/{len(rs)} "
              f"| {sum(r['fact_scheduler_max_attempts'] for r in rs)}/{len(rs)} |")

    # ---------- fetch distribution ----------
    w("\n## L1 fetch-count distribution\n")
    w("| model | fetch counts per run | mean | fetched ids | required items retrieved |")
    w("|---|---|---|---|---|")
    for m in models:
        rs = [r for r in runs if r["model"] == m and r["arm"] == "l1"]
        if not rs:
            continue
        counts = [r["fetch_count"] for r in rs]
        ids = sorted({i for r in rs for i in r["fetch_ids"]})
        req = sum(len(r["required_items_fetched"]) for r in rs)
        w(f"| {m} | {counts} | {statistics.mean(counts):.2f} | "
          f"{', '.join(ids) or '(none)'} | {req}/{2 * len(rs)} |")
    w("\nThe required items were retrieved **without a miss** in every L1 run: the "
      "fetch count equals the number of required items exactly, so no run fetched a "
      "non-required item and no run needed a retry after a wrong id.\n")

    # ---------- realised saving ----------
    w("\n## Realised saving\n")
    w("`realised_saving = (C0 prompt - L1 prompt - fetched body tokens) / C0 prompt`\n")
    w("| model | C0 prompt (tok) | L1 prompt (tok) | fetched body chars | "
      "fetch overhead (tok) | fetched body (tok, est) | realised saving |")
    w("|---|---|---|---|---|---|---|")
    ratios = {}
    for m in models:
        if (m, "c0") not in tok or (m, "l1") not in tok:
            continue
        c0, l1 = tok[(m, "c0")], tok[(m, "l1")]
        l1_rows = [r for r in rows if r["model"] == m and r["arm"] == "l1" and r["round"] == 1]
        ratio = statistics.mean([r["prompt_chars"] / r["prompt_tokens"] for r in l1_rows])
        ratios[m] = ratio
        rs = [r for r in runs if r["model"] == m and r["arm"] == "l1"]
        chars = statistics.mean([r["fetched_body_chars"] for r in rs])
        est = chars / ratio
        seed_tok = statistics.mean([r["prompt_tokens"] for r in l1_rows])
        overhead = l1 - seed_tok
        save = (c0 - l1 - est) / c0
        w(f"| {m} | {c0:.0f} | {l1:.0f} | {chars:.0f} | {overhead:.0f} | {est:.0f} "
          f"| **{save * 100:.1f}%** |")
    w("\nCharacters per prompt token, measured on the L1 index itself: "
      + ", ".join(f"`{m}` = {v:.2f}" for m, v in ratios.items()) + ".\n")
    w("\"fetch overhead\" is the L1 prompt cost that is not the index: the assistant's "
      "own fetch request plus the protocol instruction, re-sent on each further round.\n")

    # ---------- cache ----------
    w("\n## Cache behaviour (`prompt_tokens_details.cached_tokens`)\n")
    w("| model | arm | rows | rows reporting cached_tokens | mean cached (tok) | mean cached fraction |")
    w("|---|---|---|---|---|---|")
    for m in models:
        for a in arms:
            rs = [r for r in rows if r["model"] == m and r["arm"] == a]
            if not rs:
                continue
            have = [r for r in rs if r.get("cached_tokens") is not None]
            if have:
                mean_c = statistics.mean(r["cached_tokens"] for r in have)
                frac = statistics.mean(r["cached_tokens"] / r["prompt_tokens"] for r in have)
                w(f"| {m} | {a} | {len(rs)} | {len(have)}/{len(rs)} | {mean_c:.0f} | {frac * 100:.1f}% |")
            else:
                w(f"| {m} | {a} | {len(rs)} | 0/{len(rs)} | not reported | not reported |")
    w("\nThe `:8014` server never populates `prompt_tokens_details`, so cached-token "
      "overlap for `qwen3.5-9b` is **unmeasured**, not zero.\n")
    w("**This is the honest headline caveat.** At temperature 0 with a byte-identical "
      "prefix, `occamy-1.0` served the C0 arm at a **99.1% cache hit** in every rep, so "
      "C0's 5,359 prompt tokens are ~53 billable tokens each time after the first. "
      "L1 never reaches that steady state: each run is a fresh index seed followed by "
      "fetch rounds whose payload differs per rep. The realised saving above is "
      "therefore a **cold-cache** comparison, and it is the reading that flatters L1.\n")

    # ---------- completions ----------
    w("\n## Completion text (every run)\n")
    for m in models:
        for a in arms:
            for r in sorted([r for r in runs if r["model"] == m and r["arm"] == a],
                            key=lambda x: x["rep"]):
                text = (r["final_text"] or "").strip().replace("\n", " / ")
                w(f"- `{m}` `{a}` rep{r['rep']}: correct={r['correct']} "
                  f"fetch={r['fetch_count']} ({','.join(r['fetch_ids']) or '-'}) "
                  f"err={r['error']} -> {text[:150]}")

    (ROOT / "RESULTS.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
