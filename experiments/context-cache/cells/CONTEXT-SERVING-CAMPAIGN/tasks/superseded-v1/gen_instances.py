#!/usr/bin/env python3
"""Deterministic generator for cs.task/1 instances (D1-D4 discovery, H1-H4 heldout)."""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTANCES = HERE / "instances"
TURNS = 12


def _turn(n, event, question, contract, expect):
    return {
        "n": n,
        "event": event,
        "question": question,
        "answer_contract": list(contract),
        "expect": dict(expect),
    }


def _instance(task_id, split, seed, family, turns):
    return {
        "schema": "cs.task/1",
        "task_id": task_id,
        "split": split,
        "seed": seed,
        "family": family,
        "fixture": {"turns": TURNS, "values": [t["event"] for t in turns]},
        "turns": turns,
        "grader": "cs.grade/1",
    }


def gen_d1(seed):
    rng = random.Random(seed)
    vals = [rng.randint(-9, 9) for _ in range(TURNS)]
    turns = []
    total = 0
    for i, v in enumerate(vals, 1):
        total += v
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "value": v},
            f"Observation {i}: value={v}. What is the cumulative total of all observed values so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"total={total}"],
            {"total": total},
        ))
    return turns


def gen_d2(seed):
    rng = random.Random(seed)
    pool = ["alpha", "beta", "gamma", "delta", "epsilon"]
    vals = [rng.choice(pool) for _ in range(TURNS)]
    turns = []
    seen = set()
    for i, v in enumerate(vals, 1):
        seen.add(v)
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "token": v},
            f"Observation {i}: token={v}. How many distinct tokens have been observed so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"distinct={len(seen)}"],
            {"distinct": len(seen)},
        ))
    return turns


def gen_d3(seed):
    rng = random.Random(seed)
    vals = [rng.randint(-20, 20) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        sub = vals[:i]
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "temperature": v},
            f"Observation {i}: temperature={v}. What are the minimum and maximum temperatures observed so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"min={min(sub)}", f"max={max(sub)}"],
            {"min": min(sub), "max": max(sub)},
        ))
    return turns


def gen_d4(seed):
    rng = random.Random(seed)
    vals = [rng.randint(1, 99) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "value": v},
            f"Observation {i}: value={v}. What is the most recently observed value? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"last={v}"],
            {"last": v},
        ))
    return turns


def gen_h1(seed):
    rng = random.Random(seed)
    vals = [round(rng.uniform(-5.0, 5.0), 3) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        sub = vals[:i]
        mean = sum(sub) / len(sub)
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "value": v},
            f"Observation {i}: value={v}. What is the arithmetic mean of all observed values so far, rounded to 2 decimals? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"mean={mean:.2f}"],
            {"mean": f"{mean:.2f}"},
        ))
    return turns


def gen_h2(seed):
    rng = random.Random(seed)
    pool = ["red", "green", "blue", "amber"]
    vals = [rng.choice(pool) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        sub = vals[:i]
        counts = {}
        for x in sub:
            counts[x] = counts.get(x, 0) + 1
        maxc = max(counts.values())
        candidates = sorted(k for k, c in counts.items() if c == maxc)
        mode = candidates[0]
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "color": v},
            f"Observation {i}: color={v}. What is the most frequent color observed so far (ties broken alphabetically)? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"mode={mode}"],
            {"mode": mode},
        ))
    return turns


def gen_h3(seed):
    rng = random.Random(seed)
    vals = [rng.randint(2, 9) for _ in range(TURNS)]
    turns = []
    prod = 1
    for i, v in enumerate(vals, 1):
        prod = (prod * v) % 1000
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "factor": v},
            f"Observation {i}: factor={v}. What is the product of all observed factors so far, modulo 1000? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"product_mod={prod}"],
            {"product_mod": prod},
        ))
    return turns


def gen_h4(seed):
    rng = random.Random(seed)
    vals = [rng.randint(1, 50) for _ in range(TURNS)]
    turns = []
    for i, v in enumerate(vals, 1):
        sub = sorted(vals[:i])
        n = len(sub)
        if n % 2 == 1:
            med = sub[n // 2]
        else:
            med = (sub[n // 2 - 1] + sub[n // 2]) / 2
        if isinstance(med, float) and med.is_integer():
            med_str = str(int(med))
        else:
            med_str = str(med)
        turns.append(_turn(
            i,
            {"type": "observation", "seq": i, "value": v},
            f"Observation {i}: value={v}. What is the median of all observed values so far? "
            "Reply with exactly one line per contracted key, no extra text.",
            [f"median={med_str}"],
            {"median": med_str},
        ))
    return turns


GENERATORS = {
    "D1": (gen_d1, "discovery", 2026110501, "running_total"),
    "D2": (gen_d2, "discovery", 2026110502, "distinct_count"),
    "D3": (gen_d3, "discovery", 2026110503, "min_max"),
    "D4": (gen_d4, "discovery", 2026110504, "last_value"),
    "H1": (gen_h1, "heldout", 2026110505, "mean_rounded"),
    "H2": (gen_h2, "heldout", 2026110506, "mode"),
    "H3": (gen_h3, "heldout", 2026110507, "product_mod"),
    "H4": (gen_h4, "heldout", 2026110508, "median"),
}


def generate_all():
    out = {}
    for tid, (fn, split, seed, family) in GENERATORS.items():
        turns = fn(seed)
        assert len(turns) == TURNS
        out[tid] = _instance(tid, split, seed, family, turns)
    return out


def main():
    INSTANCES.mkdir(parents=True, exist_ok=True)
    for tid, inst in generate_all().items():
        path = INSTANCES / f"{tid}.json"
        path.write_text(json.dumps(inst, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
