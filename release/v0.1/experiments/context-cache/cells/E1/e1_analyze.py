#!/usr/bin/env python3
"""E1 analysis — paired break cost of FORK vs SUMMARISE_IN_PLACE at the event.

Break cost of a compaction event, per arm, per event:

    bc(E) = uncached(E) - median(uncached(E-1), uncached(E+1))

i.e. the extra uncached prompt at the turn the head is rewritten, against the
two neighbouring turns of the *same* arm and session.  The two arms are paired
by event index within a session (U4's matched-pair design); a pair is only
counted when both arms compact on the same turn.

`check_distinctness` is the guard the whole experiment rests on: if the two
arms render byte-identical prompts at/after the event (U4's defect), the pairs
carry no information and this module refuses to analyse them.

Writes `e1_analysis.json`; `--rows` also refreshes `e1_distinctness_green.json`
with the server-reported prompt_tokens the offline proof cannot know.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
ROWS = HERE / "e1_rows.jsonl"
PLAN = HERE / "e1_plan.json"
GREEN = HERE / "e1_distinctness_green.json"
OUT = HERE / "e1_analysis.json"

BOOTSTRAP_RESAMPLES = 20000
BOOTSTRAP_SEED = 20261020


class UninformativePairs(RuntimeError):
    """The arms are not byte-distinct: any delta would be instrument noise."""


# --------------------------------------------------------------------------- #
# The guard
# --------------------------------------------------------------------------- #
def check_distinctness(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Fail unless every event and every post-event turn renders two prompts.

    Contract, checked on the rows themselves (not on the offline plan):
      * before the first event, the two arms must be byte-identical -- they are
        literally the same conversation, which is why one request can serve
        both before the fork point;
      * at and after the first event, the two arms must differ at every turn;
      * every compaction event must have both arms present with a *different*
        prompt digest, or the pair is not informative.
    """

    by = {(r["session"], int(r["turn"]), r["arm"]): r for r in rows}
    sessions = sorted({r["session"] for r in rows})
    problems: list[str] = []
    informative: list[dict[str, Any]] = []

    for session in sessions:
        turns = sorted({int(r["turn"]) for r in rows if r["session"] == session})
        event_turns = {
            arm: sorted(
                int(r["turn"])
                for r in rows
                if r["session"] == session and r["arm"] == arm and r["is_event"]
            )
            for arm in ("F", "R")
        }
        if not event_turns["F"] or not event_turns["R"]:
            problems.append(f"{session}: an arm recorded no compaction event")
            continue
        first_event = min(event_turns["F"][0], event_turns["R"][0])
        for turn in turns:
            f, r = by.get((session, turn, "F")), by.get((session, turn, "R"))
            if f is None or r is None:
                problems.append(f"{session} turn {turn}: one arm missing")
                continue
            same = f["prompt_sha256"] == r["prompt_sha256"]
            if turn < first_event:
                if not same:
                    problems.append(
                        f"{session} turn {turn}: arms differ BEFORE the first event"
                    )
            else:
                if same:
                    problems.append(
                        f"{session} turn {turn}: arms render byte-identical prompts "
                        "at/after the event -- the U4 defect"
                    )
                if not f["fork_marker_present"]:
                    problems.append(f"{session} turn {turn}: fork arm carries no marker")
        for i, turn in enumerate(event_turns["F"]):
            if turn not in event_turns["R"]:
                problems.append(f"{session}: fork event turn {turn} unpaired")
                continue
            f, r = by[(session, turn, "F")], by[(session, turn, "R")]
            if f["prompt_sha256"] != r["prompt_sha256"]:
                informative.append(
                    {"session": session, "event_index": i + 1, "turn": turn}
                )

    if problems:
        raise UninformativePairs(
            f"{len(problems)} distinctness failure(s); first: {problems[0]}"
        )
    if not informative:
        raise UninformativePairs("zero informative pairs")
    return {
        "informative_pairs": len(informative),
        "pairs": informative,
        "pre_fork_turns_identical": True,
        "post_fork_turns_distinct": True,
    }


# --------------------------------------------------------------------------- #
# Break cost
# --------------------------------------------------------------------------- #
def _median(values: Sequence[float]) -> float:
    return float(statistics.median(values))


def _bootstrap_ci(deltas: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(deltas)
    meds = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        meds.append(statistics.median(sample))
    meds.sort()
    lo = meds[int(0.025 * (len(meds) - 1))]
    hi = meds[int(0.975 * (len(meds) - 1))]
    return float(lo), float(hi)


def _sign_test(deltas: Sequence[float]) -> dict[str, Any]:
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    zero = sum(1 for d in deltas if d == 0)
    n = pos + neg
    if n == 0:
        return {"positive": pos, "negative": neg, "zero": zero, "p_two_sided": 1.0}
    # exact two-sided binomial with p=0.5
    from math import comb

    tail = sum(comb(n, k) for k in range(0, min(pos, neg) + 1)) / (2**n)
    return {
        "positive": pos,
        "negative": neg,
        "zero": zero,
        "p_two_sided": round(min(1.0, 2 * tail), 6),
    }


def analyse(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    guard = check_distinctness(rows)
    by = {(r["session"], int(r["turn"]), r["arm"]): r for r in rows}
    sessions = sorted({r["session"] for r in rows})

    per_event: list[dict[str, Any]] = []
    for session in sessions:
        for arm in ("F", "R"):
            eturns = sorted(
                int(r["turn"])
                for r in rows
                if r["session"] == session and r["arm"] == arm and r["is_event"]
            )
            for i, turn in enumerate(eturns):
                prev_row = by.get((session, turn - 1, arm))
                next_row = by.get((session, turn + 1, arm))
                if prev_row is None or next_row is None:
                    continue
                base = _median([prev_row["uncached"], next_row["uncached"]])
                per_event.append(
                    {
                        "session": session,
                        "arm": arm,
                        "event_index": i + 1,
                        "turn": turn,
                        "uncached": by[(session, turn, arm)]["uncached"],
                        "base_uncached": base,
                        "break_cost": by[(session, turn, arm)]["uncached"] - base,
                        "prompt_tokens": by[(session, turn, arm)]["prompt_tokens"],
                        "cached_tokens": by[(session, turn, arm)]["cached_tokens"],
                        "prompt_mod64": by[(session, turn, arm)]["prompt_mod64"],
                        "diff_offset_vs_other_arm": by[(session, turn, arm)][
                            "diff_offset_vs_other_arm"
                        ],
                    }
                )

    # pair by (session, event_index); only same-turn pairs count
    pairs: list[dict[str, Any]] = []
    for session in sessions:
        f_events = [e for e in per_event if e["session"] == session and e["arm"] == "F"]
        r_events = [e for e in per_event if e["session"] == session and e["arm"] == "R"]
        for fe, re_ in zip(f_events, r_events):
            if fe["turn"] != re_["turn"]:
                continue
            pairs.append(
                {
                    "session": session,
                    "event_index": fe["event_index"],
                    "turn": fe["turn"],
                    "break_cost_fork": fe["break_cost"],
                    "break_cost_summarise": re_["break_cost"],
                    "delta_fork_minus_summarise": fe["break_cost"] - re_["break_cost"],
                    "prompt_tokens_fork": fe["prompt_tokens"],
                    "prompt_tokens_summarise": re_["prompt_tokens"],
                    "cached_tokens_fork": fe["cached_tokens"],
                    "cached_tokens_summarise": re_["cached_tokens"],
                }
            )

    deltas = [p["delta_fork_minus_summarise"] for p in pairs]
    bc_f = [p["break_cost_fork"] for p in pairs]
    bc_r = [p["break_cost_summarise"] for p in pairs]
    ci = _bootstrap_ci(deltas) if deltas else (0.0, 0.0)

    warm = [
        r
        for r in rows
        if not r["is_event"] and int(r["turn"]) > 1 and r["cached_tokens"] > 0
    ]
    residual = {
        arm: sorted(r["uncached"] - r["prompt_mod64"] for r in warm if r["arm"] == arm)
        for arm in ("F", "R")
    }
    grid = {
        arm: {
            "n_warm": len(vals),
            "median_residual": _median(vals) if vals else None,
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "on_grid": sum(1 for v in vals if v == 0),
        }
        for arm, vals in residual.items()
    }

    stratified = {"by_event_index": {}}
    for k in sorted({p["event_index"] for p in pairs}):
        sel = [p for p in pairs if p["event_index"] == k]
        ds = [p["delta_fork_minus_summarise"] for p in sel]
        stratified["by_event_index"][str(k)] = {
            "n": len(ds),
            "deltas": ds,
            "median_delta": statistics.median(ds) if ds else None,
            "positive": sum(1 for d in ds if d > 0),
            "negative": sum(1 for d in ds if d < 0),
            "median_break_cost_fork": statistics.median([p["break_cost_fork"] for p in sel]),
            "median_break_cost_summarise": statistics.median([p["break_cost_summarise"] for p in sel]),
            "median_cached_at_event_fork": statistics.median([p["cached_tokens_fork"] for p in sel]),
            "median_cached_at_event_summarise": statistics.median([p["cached_tokens_summarise"] for p in sel]),
        }
    ex = [p["delta_fork_minus_summarise"] for p in pairs if p["event_index"] != 2]
    stratified["excluding_event_index_2"] = {
        "why": "at event 2 both arms recorded cached_tokens=0 (an across-the-board full miss, not a policy effect); reported, not dropped silently",
        "n": len(ex),
        "deltas": ex,
        "median": statistics.median(ex) if ex else None,
        "min": min(ex) if ex else None,
        "max": max(ex) if ex else None,
        "positive": sum(1 for d in ex if d > 0),
        "negative": sum(1 for d in ex if d < 0),
        "bootstrap_95ci": list(_bootstrap_ci(ex)) if len(ex) > 2 else None,
        "sign_test": _sign_test(ex),
    }
    result = {
        "unit": "E1",
        "guard": guard,
        "n_pairs": len(pairs),
        "pairs": pairs,
        "per_event": per_event,
        "summary": {
            "median_break_cost_fork": _median(bc_f) if bc_f else None,
            "median_break_cost_summarise": _median(bc_r) if bc_r else None,
            "median_paired_delta": _median(deltas) if deltas else None,
            "mean_paired_delta": statistics.fmean(deltas) if deltas else None,
            "delta_min": min(deltas) if deltas else None,
            "delta_max": max(deltas) if deltas else None,
            "delta_bootstrap_95ci": list(ci),
            "sign_test": _sign_test(deltas),
        },
        "grid_64": grid,
        "requests": max(r["request_index"] for r in rows) if rows else 0,
        "rows": len(rows),
        "rows_sha256": hashlib.sha256(ROWS.read_bytes()).hexdigest()
        if ROWS.exists()
        else None,
    }
    result["stratified"] = stratified
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=Path, default=ROWS)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)

    rows = [json.loads(line) for line in args.rows.read_text().splitlines() if line.strip()]
    result = analyse(rows)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    # Enrich the offline distinctness proof with the server-reported token
    # counts only the live rows can supply.
    if GREEN.exists():
        green = json.loads(GREEN.read_text())
        by = {(r["session"], int(r["turn"]), r["arm"]): r for r in rows}
        for row in green.get("turns", []):
            f = by.get((row["session"], int(row["turn"]), "F"))
            r = by.get((row["session"], int(row["turn"]), "R"))
            if f and r:
                row["server_prompt_tokens_fork"] = f["prompt_tokens"]
                row["server_prompt_tokens_summarise"] = r["prompt_tokens"]
                row["server_prompt_token_delta"] = f["prompt_tokens"] - r["prompt_tokens"]
                row["server_cached_tokens_fork"] = f["cached_tokens"]
                row["server_cached_tokens_summarise"] = r["cached_tokens"]
        green["server_token_counts_added"] = True
        real = [row for row in green["turns"] if row["is_event"]]
        if real:
            ds = [row["server_prompt_token_delta"] for row in real]
            green["server_prompt_token_delta_at_events"] = {
                "values": ds,
                "median": statistics.median(ds),
            }
        GREEN.write_text(json.dumps(green, indent=2, sort_keys=True) + "\n")

    s = result["summary"]
    print(f"pairs                 {result['n_pairs']}")
    print(f"median bc fork        {s['median_break_cost_fork']}")
    print(f"median bc summarise   {s['median_break_cost_summarise']}")
    print(f"median paired delta   {s['median_paired_delta']}")
    print(f"delta range           [{s['delta_min']}, {s['delta_max']}]")
    print(f"bootstrap 95% CI      {s['delta_bootstrap_95ci']}")
    print(f"sign test             {s['sign_test']}")
    print(f"requests / rows       {result['requests']} / {result['rows']}")
    print(f"rows sha256           {result['rows_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
