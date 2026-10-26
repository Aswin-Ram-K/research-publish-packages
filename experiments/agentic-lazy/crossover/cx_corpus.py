#!/usr/bin/env python3
"""Build the parametric crossover corpora: 3,000 / 10,000 / 30,000 characters,
with either 12 items (2 of which are needed) or 30 items (6 needed).

Reuse, not rewrite
------------------
The first arm's `build_corpus.py` is imported and its ITEMS list is the seed
material for every filler body here: fillers are recombined from that corpus's own
sentences, so vocabulary and register stay identical to the arm already measured.
The output format is also the first arm's format (items.json + one .txt per item +
MANIFEST.json with per-item sha256), so the same runner/analyzer shapes apply.

What is new: the six fact-bearing sentences (compact restatements of facts that
already exist in the first arm's corpus, plus four new facts for the 30-item
corpora), and the exact-size fitting that makes the sweep reproducible.

Reproducibility
---------------
SEED is fixed and recorded in MANIFEST.json. Re-running this script regenerates
byte-identical files. Every corpus's total body characters is EXACTLY the target;
the last filler item absorbs the rounding padding.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PARENT = ROOT.parent
OUT = ROOT / "corpus"

sys.path.insert(0, str(PARENT))
import build_corpus as base  # noqa: E402  (the first arm's builder, unmodified)

SEED = 20261024
SIZES = (3000, 30000)
COUNTS = (12, 30)

MIN_FACT_CHARS = 175      # hero line + fact sentence + a little prose
MIN_FILLER_CHARS = 60     # below this an item is a bare title; kept as a floor

BASE_IDS_12 = ["T-1", "T-2", "T-3", "S-1", "S-2", "S-3",
               "M-1", "M-2", "M-3", "K-1", "K-2", "K-3"]
EXTRA_FACT_IDS = ["K-4", "M-4", "S-4", "T-4"]
EXTRA_FILLER_IDS = ["T-5", "T-6", "T-7", "T-8", "S-5", "S-6", "S-7", "S-8",
                    "M-5", "M-6", "M-7", "M-8", "K-5", "K-6"]

# id -> (kind, fact sentence, exact value the answer must contain)
FACT_SPECS = {
    "K-2": ("knowledge",
            "Retention for the billing service's logs is 400 days; the annual "
            "reconciliation window runs against this tier.", "400"),
    "M-1": ("memory",
            "A nightly scheduled job that exits non-zero is retried a maximum of "
            "5 attempts, then marked dead.", "5"),
    "K-4": ("knowledge",
            "The compliance audit trail is retained for 2555 days before it is "
            "purged by the retention worker.", "2555"),
    "M-4": ("memory",
            "A dispatch job that exits non-zero is given a maximum of 3 attempts "
            "before it is abandoned.", "3"),
    "S-4": ("skill",
            "A cached response expires after 900 seconds, after which the next "
            "request rebuilds it.", "900"),
    "T-4": ("tool",
            "The batch reindexer processes documents in chunks of 512.", "512"),
}

NEW_HERO = {
    "K-4": "KNOWLEDGE K-4 -- Compliance audit trail retention",
    "M-4": "MEMORY M-4 -- Dispatch retry limits",
    "S-4": "SKILL S-4 -- Response cache warming",
    "T-4": "TOOL T-4 -- Batch reindexer",
}

KIND_OF_ID = {"T": "tool", "S": "skill", "M": "memory", "K": "knowledge"}


def hero_line(body: str) -> str:
    """Same rule as the first arm's harness: first non-empty line."""
    for line in body.splitlines():
        if line.strip():
            return line.strip()
    return ""


def sentence_pool(items: list[dict]) -> list[str]:
    """Recombine-able sentences taken from the first arm's own corpus."""
    pool: list[str] = []
    for it in items:
        body = "\n".join(it["body"].splitlines()[1:])       # drop the hero line
        for para in re.split(r"\n\s*\n", body):
            flat = " ".join(para.split())
            for sent in re.split(r"(?<=[.!?])\s+", flat):
                s = sent.strip()
                if 45 <= len(s) <= 400 and not re.search(r"\d{3,}", s):
                    pool.append(s)
    if not pool:
        raise SystemExit("empty sentence pool")
    return pool


def take(pool: list[str], rng: random.Random, budget: int) -> str:
    """Concatenate pool sentences (seeded order) up to `budget` characters."""
    out, used = [], 0
    while used < budget:
        s = pool[rng.randrange(len(pool))]
        if used + len(s) + 1 > budget:
            # try to close the gap with a shorter sentence before giving up
            short = [p for p in pool if len(p) <= budget - used - 1]
            if not short:
                break
            s = short[rng.randrange(len(short))]
        out.append(s)
        used += len(s) + 1
    return " ".join(out)


def fit(body: str, budget: int) -> str:
    """Cut to <= budget at a word boundary, then pad with prose to exactly budget."""
    if len(body) <= budget:
        return body
    cut = body[:budget]
    sp = cut.rfind(" ")
    return cut[:sp] if sp > budget - 40 else cut


def exact_body(text: str, target: int, pool: list[str]) -> str:
    """Return a body of EXACTLY `target` characters, terminated by one newline.

    The trailing newline is part of the count, so every caller works in whole
    bodies and the cell total is exact by construction rather than by luck.
    """
    out = text.rstrip()
    if len(out) + 1 > target:
        out = fit(out, target - 1).rstrip()
    i = 0
    while len(out) + 1 < target:
        need = target - 1 - len(out)
        out += (" " + pool[(i * 7 + 3) % len(pool)])[:need]
        i += 1
        if i > 400:
            raise SystemExit(f"cannot pad to {target} chars")
    return out + "\n"


def hero_for(iid: str, by_id: dict[str, dict]) -> str:
    """A neutral hero line for any id.

    Ids that exist in the seed corpus keep their own hero. Generated filler ids
    take the hero of a same-kind seed item with the id substituted, so no title is
    hand-written and no hero can carry a fact.
    """
    if iid in by_id:
        return hero_line(by_id[iid]["body"])
    if iid in NEW_HERO:
        return NEW_HERO[iid]
    kind = KIND_OF_ID[iid[0]]
    seeds = [f"{iid[0]}-{n}" for n in (1, 2, 3)]
    src = seeds[int(iid.split("-")[1]) % len(seeds)]
    base_hero = hero_line(by_id[src]["body"])
    return base_hero.replace(f"{kind.upper()} {src}", f"{kind.upper()} {iid}", 1)


def build_cell(n_items: int, total_chars: int) -> dict:
    """One (item count, total chars) cell. Returns {"items": [...], "meta": {...}}."""
    rng = random.Random(SEED + n_items * 100000 + total_chars)
    pool = sentence_pool(base.ITEMS)
    by_id = {it["id"]: it for it in base.ITEMS}

    if n_items == 12:
        fact_ids = ["K-2", "M-1"]
        ids = list(BASE_IDS_12)
    else:
        fact_ids = ["K-2", "M-1", "K-4", "M-4", "S-4", "T-4"]
        ids = list(BASE_IDS_12) + EXTRA_FACT_IDS + EXTRA_FILLER_IDS
    assert len(ids) == n_items, (len(ids), n_items)
    filler_ids = [i for i in ids if i not in fact_ids]

    baseline = total_chars // n_items
    fact_budget = max(baseline, MIN_FACT_CHARS)
    # keep fillers above the floor even when the cell is very tight
    fact_budget = min(fact_budget,
                      max(MIN_FACT_CHARS,
                          (total_chars - MIN_FILLER_CHARS * len(filler_ids))
                          // len(fact_ids)))
    filler_budget = (total_chars - fact_budget * len(fact_ids)) // len(filler_ids)
    if filler_budget < MIN_FILLER_CHARS:
        raise SystemExit(f"infeasible cell n={n_items} total={total_chars}")

    items: list[dict] = []
    for iid in ids:
        kind = KIND_OF_ID[iid[0]]
        if iid in fact_ids:
            fact = FACT_SPECS[iid][1]
            hero = hero_for(iid, by_id)
            head = f"{hero}\n\n{fact}\n\n"
            body = head + take(pool, rng, max(0, fact_budget - len(head)))
            body = fit(body, fact_budget)
            # the fact must survive the fit, always
            assert fact in body, f"fact lost for {iid} at budget {fact_budget}"
            title = hero.split("--", 1)[-1].strip()
        else:
            hero = hero_for(iid, by_id)
            body = f"{hero}\n\n" + take(pool, rng, max(0, filler_budget - len(hero) - 2))
            body = fit(body, filler_budget)
            title = hero.split("--", 1)[-1].strip()
        items.append({"id": iid, "kind": kind, "title": title,
                      "body": body.rstrip() + "\n"})

    # exact total: the last filler absorbs the remainder
    total = sum(len(it["body"]) for it in items)
    last = next(it for it in reversed(items) if it["id"] in filler_ids)
    last["body"] = exact_body(last["body"], len(last["body"]) + (total_chars - total),
                              pool)

    # byte-count accident repair: a fact value must not appear in the projection
    for _ in range(60):
        proj = projection(items)
        bad = [f for f in fact_ids
               if len(FACT_SPECS[f][2]) > 1 and FACT_SPECS[f][2] in proj]
        if not bad:
            break
        victim = next(it for it in items if it["id"] == bad[0])
        victim["body"] = exact_body(victim["body"], len(victim["body"]) + 7, pool)
        donor = next(it for it in reversed(items) if it["id"] in filler_ids)
        donor["body"] = exact_body(donor["body"], len(donor["body"]) - 7, pool)
    else:
        raise SystemExit("could not clear a fact value from the projection")

    total = sum(len(it["body"]) for it in items)
    assert total == total_chars, (total, total_chars)
    return {"items": items, "meta": {
        "n_items": n_items, "total_chars": total, "seed": SEED,
        "fact_ids": fact_ids,
        "needed_fraction": round(len(fact_ids) / n_items, 4),
        "fact_budget": fact_budget, "filler_budget": filler_budget,
    }}


def projection(items: list[dict]) -> str:
    """The lazy arm's index, same format as the first arm's harness."""
    by_kind: dict[str, list[str]] = {}
    for it in items:
        nbytes = len(it["body"].encode("utf-8"))
        by_kind.setdefault(it["kind"], []).append(
            f"  [{it['id']}] ({nbytes} B) {hero_line(it['body'])}")
    out = ["LIBRARY INDEX"]
    for kind in ("tool", "skill", "memory", "knowledge"):
        if kind in by_kind:
            out.append(f"{kind.upper()} ({len(by_kind[kind])} items)")
            out.extend(by_kind[kind])
    return "\n".join(out)


def write_cell(n_items: int, total_chars: int) -> dict:
    cell = build_cell(n_items, total_chars)
    name = f"{n_items:02d}_{total_chars:05d}"
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    items = cell["items"]
    (d / "items.json").write_text(
        json.dumps({"items": items}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = []
    for it in items:
        raw = it["body"].encode("utf-8")
        (d / f"{it['id']}.txt").write_bytes(raw)
        manifest.append({"id": it["id"], "kind": it["kind"],
                         "chars": len(it["body"]), "bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest(),
                         "is_fact": it["id"] in cell["meta"]["fact_ids"],
                         "hero": hero_line(it["body"])})
    proj = projection(items)
    man = dict(cell["meta"])
    man.update({
        "dir": name,
        "items": manifest,
        "counts_by_kind": {k: sum(1 for m in manifest if m["kind"] == k)
                           for k in ("tool", "skill", "memory", "knowledge")},
        "projection_chars": len(proj),
        "projection_ratio_of_corpus": round(len(proj) / cell["meta"]["total_chars"], 4),
        "bodies_sha256": hashlib.sha256(
            "".join(m["sha256"] for m in manifest).encode()).hexdigest(),
        "fact_values_absent_from_projection": all(
            FACT_SPECS[f][2] not in proj for f in cell["meta"]["fact_ids"]
            if len(FACT_SPECS[f][2]) > 1),
        "fact_sentences_absent_from_projection": all(
            FACT_SPECS[f][1] not in proj for f in cell["meta"]["fact_ids"]),
    })
    (d / "MANIFEST.json").write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return man


def main() -> int:
    assert len(base.ITEMS) == 12, len(base.ITEMS)
    seed_total = sum(len(i["body"]) for i in base.ITEMS)
    print(f"seed material: build_corpus.ITEMS = {len(base.ITEMS)} items, "
          f"{seed_total} chars")

    mans = []
    for n in COUNTS:
        for s in SIZES:
            m = write_cell(n, s)
            mans.append(m)
            print(f"  {m['dir']}  items={m['n_items']:2d} chars={m['total_chars']:6d} "
                  f"proj={m['projection_chars']:5d} "
                  f"({m['projection_ratio_of_corpus']*100:5.1f}% of corpus) "
                  f"needed={len(m['fact_ids'])}/{m['n_items']} "
                  f"leak_free={m['fact_values_absent_from_projection']}")

    (OUT / "MANIFEST.json").write_text(json.dumps(
        {"seed": SEED, "sizes": list(SIZES), "counts": list(COUNTS),
         "seed_material": {"source": "../build_corpus.py ITEMS",
                           "items": len(base.ITEMS), "chars": seed_total},
         "cells": mans}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(mans)} cells to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
