#!/usr/bin/env python3
"""U5 analysis: accuracy, agreement, per-kind, confusion, kill condition.

Reads ``u5_raw.jsonl`` (written by ``u5_gate.py``) and re-derives every metric.
The raw model text is stored in each row, so this can be re-run -- and its
parser changed -- without spending a single live request.

Literal command::

    python3 experiments/context-cache/cells/U5/u5_analyze.py

Writes ``u5_report.json`` next to itself and prints the tables.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "src"))

import u5_cells as cellsmod  # noqa: E402

DEEP = ("baseline", "summarise", "fork")
KILL_DELTA_POINTS = 5.0
AGREEMENT_FLOOR = 0.90


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def acc(correct: int, n: int) -> float:
    return round(correct / n, 6) if n else 0.0


def arm_rows(rows: list[dict[str, Any]], depth: str) -> dict[str, list[dict[str, Any]]]:
    """Group rows into arms.  Shallow has one shared reading for both arms."""

    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["depth"] != depth:
            continue
        if row.get("status") != 200:
            continue
        cond = row["condition"]
        if depth == "shallow":
            by["summarise"].append(row)
            by["fork"].append(row)  # same reading, byte-identical prompt
        else:
            by[cond].append(row)
    return dict(by)


def accuracy_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for depth in ("shallow", "deep"):
        arms = arm_rows(rows, depth)
        out[depth] = {}
        for arm, rs in arms.items():
            n = len(rs)
            c = sum(1 for r in rs if r.get("correct"))
            strict = sum(1 for r in rs if r.get("strict_letter") == r["correct_letter"])
            out[depth][arm] = {
                "n": n,
                "correct": c,
                "accuracy": acc(c, n),
                "strict_correct": strict,
                "strict_accuracy": acc(strict, n),
                "shared_reading": depth == "shallow",
            }
    return out


def agreement(
    rows: list[dict[str, Any]], depth: str, a: str, b: str
) -> dict[str, Any]:
    arms = arm_rows(rows, depth)
    if a not in arms or b not in arms:
        return {"n": 0, "rate": None, "note": "arm missing"}
    if depth == "shallow":
        return {
            "n": len(arms[a]),
            "agreed": len(arms[a]),
            "rate": 1.0,
            "basis": "shallow arms are byte-identical renderings; single reading "
            "used for both (asserted, not measured twice)",
        }
    ra = {r["case_id"]: r for r in arms[a]}
    rb = {r["case_id"]: r for r in arms[b]}
    ids = sorted(set(ra) & set(rb))
    agree = sum(1 for i in ids if ra[i].get("parsed_letter") == rb[i].get("parsed_letter"))
    return {
        "n": len(ids),
        "agreed": agree,
        "rate": round(agree / len(ids), 6) if ids else None,
        "basis": "same cases, same depth, independent requests",
    }


def confusion(rows: list[dict[str, Any]], depth: str, a: str, b: str) -> dict[str, Any]:
    arms = arm_rows(rows, depth)
    ra = {r["case_id"]: r for r in arms.get(a, [])}
    rb = {r["case_id"]: r for r in arms.get(b, [])}
    ids = sorted(set(ra) & set(rb))
    cells = {"a_right_b_right": 0, "a_right_b_wrong": 0, "a_wrong_b_right": 0, "a_wrong_b_wrong": 0}
    discordant = []
    for i in ids:
        x, y = bool(ra[i].get("correct")), bool(rb[i].get("correct"))
        key = f"a_{'right' if x else 'wrong'}_b_{'right' if y else 'wrong'}"
        cells[key] += 1
        if x != y:
            discordant.append(
                {
                    "case_id": i,
                    "kind": ra[i]["kind"],
                    "a_parsed": ra[i].get("parsed_letter"),
                    "b_parsed": rb[i].get("parsed_letter"),
                    "correct_letter": ra[i]["correct_letter"],
                    "a_raw": ra[i].get("raw"),
                    "b_raw": rb[i].get("raw"),
                }
            )
    b = cells["a_right_b_wrong"]
    c = cells["a_wrong_b_right"]
    return {
        "n": len(ids),
        "cells": cells,
        "discordant": len(discordant),
        "mcnemar_exact_p": mcnemar_exact_p(b, c),
        "discordant_cases": discordant,
    }


def mcnemar_exact_p(b: int, c: int) -> float | None:
    """Two-sided exact McNemar (binomial) p-value for b vs c discordant pairs."""

    n = b + c
    if n == 0:
        return None
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n)
    return round(min(1.0, 2.0 * tail), 6)


def per_kind(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for depth in ("shallow", "deep"):
        arms = arm_rows(rows, depth)
        out[depth] = {}
        for arm, rs in arms.items():
            agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            for r in rs:
                agg[r["kind"]][1] += 1
                if r.get("correct"):
                    agg[r["kind"]][0] += 1
            out[depth][arm] = {
                k: {"correct": v[0], "n": v[1], "accuracy": acc(v[0], v[1])}
                for k, v in sorted(agg.items())
            }
    return out


def kill_check(accs: dict[str, Any], agrees: dict[str, Any]) -> dict[str, Any]:
    details = []
    for depth in ("shallow", "deep"):
        arms = list(accs.get(depth, {}))
        for i in range(len(arms)):
            for j in range(i + 1, len(arms)):
                a, b = arms[i], arms[j]
                delta = abs(accs[depth][a]["accuracy"] - accs[depth][b]["accuracy"]) * 100.0
                details.append(
                    {
                        "depth": depth,
                        "a": a,
                        "b": b,
                        "delta_points": round(delta, 3),
                        "exceeds_5pts": delta > KILL_DELTA_POINTS,
                    }
                )
    max_delta = max((d["delta_points"] for d in details), default=0.0)
    low_agreement = [
        {"pair": k, **v}
        for k, v in agrees.items()
        if v.get("rate") is not None and v["rate"] < AGREEMENT_FLOOR
    ]
    return {
        "triggered": bool(max_delta > KILL_DELTA_POINTS),
        "max_abs_delta_points": max_delta,
        "threshold_points": KILL_DELTA_POINTS,
        "details": details,
        "agreement_below_90": low_agreement,
        "negative_result": bool(max_delta > KILL_DELTA_POINTS),
    }


def verify_prompts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute every prompt from the deterministic builder and compare sha256."""

    cases = {c["id"]: (i, c) for i, c in enumerate(cellsmod.load_cases())}
    pinned = cellsmod.load_pinned()
    mismatch = []
    checked = 0
    for row in rows:
        if row.get("status") != 200:
            continue
        index, case = cases[row["case_id"]]
        cond = row["condition"]
        if row["depth"] == "shallow":
            cell = cellsmod.build_cell(case, index, "shallow", "summarise", pinned)
        else:
            cell = cellsmod.build_cell(case, index, "deep", cond, pinned)
        text = cellsmod.concat(cell["messages"])
        checked += 1
        if cellsmod.sha(text) != row["prompt_sha256"]:
            mismatch.append(row["case_id"] + "/" + cond)
    return {"checked": checked, "mismatches": mismatch, "reproducible": not mismatch}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(HERE / "u5_raw.jsonl"))
    ap.add_argument("--out", default=str(HERE / "u5_report.json"))
    ap.add_argument("--summary", default=str(HERE / "u5_summary.json"))
    args = ap.parse_args()

    rows = load_rows(Path(args.rows))
    summary = {}
    sp = Path(args.summary)
    if sp.exists():
        try:
            summary = json.loads(sp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            summary = {}

    accs = accuracy_block(rows)
    agrees = {
        "deep/summarise_vs_fork": agreement(rows, "deep", "summarise", "fork"),
        "deep/baseline_vs_summarise": agreement(rows, "deep", "baseline", "summarise"),
        "deep/fork_vs_baseline": agreement(rows, "deep", "fork", "baseline"),
        "shallow/summarise_vs_fork": agreement(rows, "shallow", "summarise", "fork"),
    }
    conf = {
        "deep/baseline_vs_summarise": confusion(rows, "deep", "baseline", "summarise"),
        "deep/baseline_vs_fork": confusion(rows, "deep", "baseline", "fork"),
        "deep/summarise_vs_fork": confusion(rows, "deep", "summarise", "fork"),
    }
    # Depth effect: the same cases, shallow reading vs deep baseline.
    shallow_by_id = {
        r["case_id"]: r for r in rows if r["depth"] == "shallow" and r["condition"] == "shared"
    }
    depth_effect = {}
    for other in ("baseline", "summarise", "fork"):
        deep_by_id = {r["case_id"]: r for r in rows if r["depth"] == "deep" and r["condition"] == other}
        ids = sorted(set(shallow_by_id) & set(deep_by_id))
        b = sum(1 for i in ids if shallow_by_id[i].get("correct") and not deep_by_id[i].get("correct"))
        c = sum(1 for i in ids if deep_by_id[i].get("correct") and not shallow_by_id[i].get("correct"))
        depth_effect[f"shallow_vs_deep_{other}"] = {
            "n": len(ids),
            "shallow_right_deep_wrong": b,
            "deep_right_shallow_wrong": c,
            "mcnemar_exact_p": mcnemar_exact_p(b, c),
        }

    parse_methods = Counter(r.get("parse_method", "missing") for r in rows)
    parse_none = sum(1 for r in rows if r.get("parsed_letter") is None)
    failed = sum(1 for r in rows if r.get("status") != 200)

    retention = {}
    for depth, cond in (("shallow", "shared"), ("deep", "baseline"), ("deep", "summarise"), ("deep", "fork")):
        subset = [r for r in rows if r["depth"] == depth and r["condition"] == cond]
        if not subset:
            continue
        retention[f"{depth}/{cond}"] = {
            "n": len(subset),
            "gold": sum(1 for r in subset if r["retained"]["gold"]),
            "question": sum(1 for r in subset if r["retained"]["question"]),
            "options": sum(1 for r in subset if r["retained"]["options"]),
        }

    report = {
        "rows": len(rows),
        "failed_rows": failed,
        "requests_reported_by_summary": summary.get("requests"),
        "status": summary.get("status"),
        "cases_used": summary.get("cases_used"),
        "subset_rule": summary.get("subset_rule"),
        "probe": summary.get("probe"),
        "parse": {"methods": dict(parse_methods), "unparsed": parse_none},
        "accuracy": accs,
        "agreement": agrees,
        "confusion": conf,
        "per_kind": per_kind(rows),
        "depth_effect": depth_effect,
        "kill": kill_check(accs, agrees),
        "retention": retention,
        "assertions": summary.get("assertions"),
        "prompt_reproduction": verify_prompts(rows),
        "wall_s": summary.get("wall_s"),
    }
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    # ---- print -------------------------------------------------------
    print(f"rows={len(rows)} failed={failed} requests={summary.get('requests')} "
          f"status={summary.get('status')} cases={summary.get('cases_used')}")
    print(f"parse methods: {dict(parse_methods)} unparsed={parse_none}")
    print("\nACCURACY (primary parse / strict)")
    for depth in ("shallow", "deep"):
        for arm, a in accs.get(depth, {}).items():
            print(f"  {depth:8s} {arm:10s} {a['correct']:3d}/{a['n']:3d} = {a['accuracy']*100:5.1f}%"
                  f"  strict {a['strict_accuracy']*100:5.1f}%"
                  + ("  (shared reading)" if a.get("shared_reading") else ""))
    print("\nAGREEMENT")
    for k, v in agrees.items():
        print(f"  {k:32s} {v.get('agreed')}/{v.get('n')} = "
              f"{(v.get('rate') or 0)*100:5.1f}%")
    print("\nCONFUSION")
    for k, v in conf.items():
        print(f"  {k:32s} discordant={v['discordant']:3d}/{v['n']:3d} {v['cells']}")
    print("\nRETENTION (gold / question / options)")
    for k, v in retention.items():
        print(f"  {k:20s} gold {v['gold']:3d}/{v['n']:3d} question {v['question']:3d} options {v['options']:3d}")
    k = report["kill"]
    print(f"\nKILL: triggered={k['triggered']} max_delta={k['max_abs_delta_points']}pts "
          f"(threshold {k['threshold_points']}) agreement<90={bool(k['agreement_below_90'])}")
    print(f"prompt reproduction: {report['prompt_reproduction']['reproducible']} "
          f"({report['prompt_reproduction']['checked']} checked)")
    print(f"report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
