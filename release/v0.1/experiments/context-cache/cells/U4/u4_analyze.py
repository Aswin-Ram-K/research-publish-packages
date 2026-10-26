#!/usr/bin/env python3
"""U4 analysis — compaction break cost per policy.

Two independent evidence layers:

**A. Byte-level structural replay (no network).**
  Re-executes the *real* ``runner.run_cell`` loop over the *real* corpus with
  the real ``compact`` + ``render``, but with a ``send`` that only records the
  exact ``canonical_bytes(messages)`` it was handed.  Because ``send`` receives
  the bytes the server would have received, this proves -- rather than assumes
  -- (i) every non-compaction turn is a byte-prefix extension of the previous
  turn (the append-only contract the orchestrator required), and (ii) which
  policies emit byte-identical prompts after a compaction.

**B. Live break cost.**
  ``break_cost(event) = uncached(first turn after compaction) - (prompt_tokens
  mod 64)``.  The ``mod 64`` term is the unavoidable 64-token-grid residual of
  a normal appended turn; subtracting it is what separates a *compaction break*
  from ordinary append tax.

Usage::

    python3 u4_analyze.py                  # uses the files next to this script
    python3 u4_analyze.py --json out.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import u4_cell as D  # noqa: E402  (corpus/cell construction, shared)
from resextract.context import (  # noqa: E402
    CacheRow,
    canonical_bytes,
    default_est_tokens,
    rows_from_jsonl,
)

GRID = 64
PERMUTATIONS = 50_000
PERM_SEED = 987654321


# --------------------------------------------------------------------------- #
# Small deterministic statistics
# --------------------------------------------------------------------------- #
def quantile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile (numpy's default), deterministic."""

    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = q * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * frac)


def describe(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "median": float(statistics.median(values)),
        "mean": float(statistics.fmean(values)),
        "p25": quantile(values, 0.25),
        "p75": quantile(values, 0.75),
        "min": float(min(values)),
        "max": float(max(values)),
        "values": [float(v) for v in values],
    }


class Lcg:
    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        self.s = (seed ^ 0x9E3779B97F4A7C15) & ((1 << 64) - 1)

    def below(self, n: int) -> int:
        self.s = (6364136223846793005 * self.s + 1442695040888963407) % (1 << 64)
        return self.s % n


def permutation_test_median(
    a: Sequence[float], b: Sequence[float], *, perms: int = PERMUTATIONS
) -> dict[str, Any]:
    """Two-sided permutation test on ``median(a) - median(b)``."""

    if not a or not b:
        return {"p_value": None, "observed_delta": None, "perms": 0}
    observed = float(statistics.median(a) - statistics.median(b))
    pool = list(a) + list(b)
    n_a = len(a)
    rng = Lcg(PERM_SEED)
    at_least = 0
    eps = 1e-12
    for _ in range(perms):
        idx = list(range(len(pool)))
        # Fisher-Yates over the whole pool, then split.
        for i in range(len(idx) - 1, 0, -1):
            j = rng.below(i + 1)
            idx[i], idx[j] = idx[j], idx[i]
        sample_a = [pool[i] for i in idx[:n_a]]
        sample_b = [pool[i] for i in idx[n_a:]]
        delta = statistics.median(sample_a) - statistics.median(sample_b)
        if abs(delta) >= abs(observed) - eps:
            at_least += 1
    return {
        "p_value": (at_least + 1) / (perms + 1),
        "observed_delta": observed,
        "perms": perms,
        "note": "two-sided, permutation distribution of the median difference",
    }


def paired_deltas(
    pairs: Iterable[tuple[float, float]]
) -> dict[str, Any]:
    diffs = [a - b for a, b in pairs]
    return {
        "n_pairs": len(diffs),
        "deltas": diffs,
        "max_abs_delta": float(max((abs(d) for d in diffs), default=0.0)),
        "n_zero": sum(1 for d in diffs if abs(d) <= 1e-12),
        "median_delta": float(statistics.median(diffs)) if diffs else None,
    }


# --------------------------------------------------------------------------- #
# A. Structural replay
# --------------------------------------------------------------------------- #
def structural_replay(units: Sequence[dict[str, Any]]) -> dict[str, dict[int, dict[str, Any]]]:
    """Capture the exact message list each cell would send, turn by turn."""

    captured: dict[str, dict[int, dict[str, Any]]] = {}
    for unit in units:
        cell = unit["cell"]
        turn_box: dict[int, dict[str, Any]] = {}
        counter = {"turn": 0}

        def send(messages: list[dict[str, str]], _box=turn_box, _c=counter):
            _c["turn"] += 1
            bodies = list(messages[1:])
            _box[_c["turn"]] = {
                "messages": [dict(m) for m in messages],
                "head_sha256": hashlib.sha256(canonical_bytes(messages[0])).hexdigest(),
                "body_sha256": hashlib.sha256(canonical_bytes(bodies)).hexdigest(),
                "n_messages": len(messages),
                "body_chars": sum(len(m["content"]) for m in bodies),
                "chars": sum(len(m["content"]) for m in messages),
                "roles": [m["role"] for m in messages],
            }
            return (0, 0, 0, 0.0, 0.0, 200, "")

        D.runner.run_cell(
            cell,
            unit["case"],
            send,
            None,
            compaction=unit["compaction"],
            summarizer=D.runner._truncating_summarizer,
            est_tokens=default_est_tokens,
        )
        captured[cell.cell] = turn_box
    return captured


def structural_report(
    units: Sequence[dict[str, Any]],
    captured: dict[str, dict[int, dict[str, Any]]],
    events_by_cell: dict[str, set[int]],
) -> dict[str, Any]:
    append_violations: list[dict[str, Any]] = []
    breaks: list[dict[str, Any]] = []
    head_changes: list[dict[str, Any]] = []
    checked = 0

    for unit in units:
        cell = unit["cell"].cell
        box = captured[cell]
        turns = sorted(box)
        event_turns = events_by_cell.get(cell, set())
        for prev, cur in zip(turns, turns[1:]):
            a = box[prev]["messages"]
            b = box[cur]["messages"]
            if box[cur]["head_sha256"] != box[prev]["head_sha256"]:
                head_changes.append({"cell": cell, "turn": cur})
            if cur in event_turns:
                # A compaction turn must change the prompt; record exactly
                # where in the message list the first rewrite lands.
                limit = min(len(a), len(b))
                i = 0
                while i < limit and a[i] == b[i]:
                    i += 1
                dropped_chars = sum(len(m["content"]) for m in a[i:])
                new_chars = sum(len(m["content"]) for m in b[i:])
                breaks.append(
                    {
                        "cell": cell,
                        "turn": cur,
                        "first_changed_message": i,
                        "messages_kept_verbatim": i,
                        "prev_messages": len(a),
                        "messages": len(b),
                        "dropped_chars": dropped_chars,
                        "rewritten_chars": new_chars,
                        "rewritten_share_of_prompt": (
                            new_chars / box[cur]["chars"] if box[cur]["chars"] else 0.0
                        ),
                        "predicted_break_tokens_est": round(new_chars / 4),
                        "roles": box[cur]["roles"],
                    }
                )
            else:
                checked += 1
                if len(b) != len(a) + 1:
                    append_violations.append(
                        {
                            "cell": cell,
                            "turn": cur,
                            "prev_messages": len(a),
                            "messages": len(b),
                            "note": "message count did not grow by exactly one",
                        }
                    )
                else:
                    for i, old in enumerate(a):
                        if b[i] != old:
                            append_violations.append(
                                {
                                    "cell": cell,
                                    "turn": cur,
                                    "message_index": i,
                                    "prev_chars": len(old["content"]),
                                    "chars": len(b[i]["content"]),
                                    "note": "append-only broken: an emitted message "
                                            "was rewritten by a later turn",
                                }
                            )
                            break

    # Cross-policy comparison of the *bodies* (message 0 carries the per-cell
    # salt, so only the bodies are policy-comparable).  Same session, same
    # turn: are the prompts the model would receive byte-identical?
    by_session_turn: dict[tuple[str, int], dict[str, str]] = defaultdict(dict)
    for unit in units:
        if unit["compaction"] == "none":
            continue
        cell = unit["cell"].cell
        for turn, info in captured[cell].items():
            by_session_turn[(unit["session"], turn)][unit["compaction"]] = info["body_sha256"]

    pairs = [
        ("summarise_in_place", "sliding_window"),
        ("summarise_in_place", "fork"),
        ("sliding_window", "fork"),
    ]
    identity: dict[str, Any] = {}
    for left, right in pairs:
        same = 0
        total = 0
        differing: list[int] = []
        for (_session, turn), shas in by_session_turn.items():
            if left in shas and right in shas:
                total += 1
                if shas[left] == shas[right]:
                    same += 1
                else:
                    differing.append(turn)
        identity[f"{left} vs {right}"] = {
            "turns_compared": total,
            "turns_byte_identical": same,
            "all_identical": total > 0 and same == total,
            "first_differing_turn": min(differing) if differing else None,
        }

    return {
        "append_only_violations": append_violations,
        "append_only_holds": not append_violations,
        "non_compaction_turns_checked": checked,
        "invariant_head_holds": not head_changes,
        "head_changes": head_changes,
        "compaction_breaks": breaks,
        "post_compaction_byte_identity": identity,
        "note": (
            "message 0 is the salted invariant head (per-cell salt), so only "
            "messages[1:] are comparable across cells; the salt is what keeps "
            "cells in separate radix paths."
        ),
    }


# --------------------------------------------------------------------------- #
# B. Live break cost
# --------------------------------------------------------------------------- #
def index_rows(rows: Sequence[CacheRow]) -> dict[str, dict[int, CacheRow]]:
    out: dict[str, dict[int, CacheRow]] = defaultdict(dict)
    for row in rows:
        if row.rep != 1:
            continue
        out[row.cell][row.turn] = row
    return out


def break_costs(
    rows: Sequence[CacheRow], events: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    indexed = index_rows(rows)
    out: list[dict[str, Any]] = []
    for event in events:
        cell = event["cell"]
        turn = int(event["turn"])
        row = indexed.get(cell, {}).get(turn)
        if row is None:
            continue
        residual = row.prompt_tokens % GRID
        out.append(
            {
                "cell": cell,
                "session": event["session"],
                "policy": event["compaction"],
                "event_index": None,  # filled below
                "turn": turn,
                "prompt_tokens": row.prompt_tokens,
                "cached_tokens": row.cached_tokens,
                "uncached": row.uncached,
                "residual_64": residual,
                "break_cost": row.uncached - residual,
                "tokens_before": event["tokens_before"],
                "tokens_after": event["tokens_after"],
                "ttft_ms": row.ttft_ms,
            }
        )
    # Number the events per (cell) in turn order.
    per_cell: dict[str, int] = defaultdict(int)
    for rec in sorted(out, key=lambda r: (r["cell"], r["turn"])):
        per_cell[rec["cell"]] += 1
        rec["event_index"] = per_cell[rec["cell"]]
    return sorted(out, key=lambda r: (r["policy"], r["session"], r["turn"]))


def grid_baseline(rows: Sequence[CacheRow], events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Residual check on turns that are neither cold nor post-compaction."""

    break_turns = {(e["cell"], int(e["turn"])) for e in events}
    residuals: list[int] = []
    anomalies: list[dict[str, Any]] = []
    for row in rows:
        if row.rep != 1 or row.turn < 2:
            continue
        if (row.cell, row.turn) in break_turns:
            continue
        residual = row.uncached - (row.prompt_tokens % GRID)
        residuals.append(residual)
        if abs(residual) > GRID:
            anomalies.append(
                {
                    "cell": row.cell,
                    "turn": row.turn,
                    "prompt_tokens": row.prompt_tokens,
                    "uncached": row.uncached,
                    "residual": residual,
                    "cached_tokens": row.cached_tokens,
                }
            )
    hist: dict[str, int] = defaultdict(int)
    for value in residuals:
        hist[str(value)] += 1
    return {
        "n_turns": len(residuals),
        "residual_histogram": dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        "max_abs_residual": max((abs(v) for v in residuals), default=0),
        "n_abs_residual_gt_64": len(anomalies),
        "anomalies": anomalies,
        "note": (
            "On a warm appended turn uncached == prompt_tokens % 64, so this "
            "residual should be 0. A nonzero value means the 64-grid "
            "assumption behind break_cost does not hold for that row."
        ),
    }


def ttft_report(rows: Sequence[CacheRow], events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    indexed = index_rows(rows)
    out: dict[str, Any] = {}
    per_policy: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"break": [], "append": []}
    )
    break_turns = {(e["cell"], int(e["turn"])) for e in events}
    for event in events:
        cell, turn = event["cell"], int(event["turn"])
        row = indexed.get(cell, {}).get(turn)
        prev = indexed.get(cell, {}).get(turn - 1)
        if row is not None:
            per_policy[event["compaction"]]["break"].append(row.ttft_ms)
        if prev is not None:
            per_policy[event["compaction"]]["append"].append(prev.ttft_ms)
    for row in rows:
        if row.rep != 1 or row.turn < 2:
            continue
        if (row.cell, row.turn) in break_turns:
            continue
        per_policy[row.cell.split("/")[2]]["append"].append(row.ttft_ms)
    for policy, series in per_policy.items():
        out[policy] = {
            "ttft_break_median_ms": float(statistics.median(series["break"]))
            if series["break"]
            else None,
            "ttft_append_median_ms": float(statistics.median(series["append"]))
            if series["append"]
            else None,
        }
    return out


def hit_rate_report(rows: Sequence[CacheRow]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    grouped: dict[str, list[CacheRow]] = defaultdict(list)
    for row in rows:
        grouped[row.cell.split("/")[2]].append(row)
    for policy, group in sorted(grouped.items()):
        prompt = sum(r.prompt_tokens for r in group)
        out[policy] = {
            "cell": policy,
            "rows": len(group),
            "weighted_hit_rate": (sum(r.cached_tokens for r in group) / prompt)
            if prompt
            else 0.0,
            "total_prompt_tokens": prompt,
            "total_uncached": sum(r.uncached for r in group),
        }
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", default=str(HERE / "u4_rows.jsonl"))
    parser.add_argument("--events", default=str(HERE / "u4_events.jsonl"))
    parser.add_argument("--runlog", default=str(HERE / "u4_runlog.json"))
    parser.add_argument("--json", default=str(HERE / "u4_report.json"))
    args = parser.parse_args(argv)

    rows = rows_from_jsonl(args.rows)
    events = [
        json.loads(line)
        for line in Path(args.events).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    runlog = json.loads(Path(args.runlog).read_text(encoding="utf-8"))

    corpus = D.load_corpus()
    units = D.build_units(corpus)
    captured = structural_replay(units)
    events_by_cell: dict[str, set[int]] = defaultdict(set)
    for event in events:
        events_by_cell[event["cell"]].add(int(event["turn"]))
    structure = structural_report(units, captured, events_by_cell)

    per_event = break_costs(rows, events)
    by_policy: dict[str, list[float]] = defaultdict(list)
    for rec in per_event:
        by_policy[rec["policy"]].append(float(rec["break_cost"]))

    # Paired comparisons on the same (session, turn): the strongest form.
    keyed: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for rec in per_event:
        keyed[(rec["session"], rec["turn"])][rec["policy"]] = float(rec["break_cost"])

    def paired(left: str, right: str) -> dict[str, Any]:
        pairs = [
            (d[left], d[right]) for d in keyed.values() if left in d and right in d
        ]
        return paired_deltas(pairs)

    comparisons = {
        "fork - summarise_in_place": paired("fork", "summarise_in_place"),
        "fork - sliding_window": paired("fork", "sliding_window"),
        "summarise_in_place - sliding_window": paired(
            "summarise_in_place", "sliding_window"
        ),
    }
    tests = {
        "fork vs summarise_in_place": permutation_test_median(
            by_policy["fork"], by_policy["summarise_in_place"]
        ),
        "fork vs sliding_window": permutation_test_median(
            by_policy["fork"], by_policy["sliding_window"]
        ),
        "summarise_in_place vs sliding_window": permutation_test_median(
            by_policy["summarise_in_place"], by_policy["sliding_window"]
        ),
    }

    # Kill condition: "break_cost for edits statistically indistinguishable
    # from fork across 4+ events".  Indistinguishable = the permutation test
    # cannot separate them AND the paired difference is within one 64-grid
    # block.  Both edit policies are reported; the verdict is driven by the
    # one that actually characterises an edit (summarise_in_place keeps the
    # folded history; sliding_window does not).
    max_events = max((len(v) for v in by_policy.values()), default=0)
    grid_equiv = GRID
    verdicts: dict[str, Any] = {}
    for edit in ("summarise_in_place", "sliding_window"):
        test = tests[f"fork vs {edit}"]
        pair = comparisons[f"fork - {edit}"]
        indistinguishable = bool(
            test["p_value"] is not None
            and test["p_value"] > 0.05
            and pair["max_abs_delta"] <= grid_equiv
        )
        verdicts[edit] = {
            "permutation_p": test["p_value"],
            "median_delta": test["observed_delta"],
            "max_abs_paired_delta": pair["max_abs_delta"],
            "n_pairs": pair["n_pairs"],
            "indistinguishable_from_fork": indistinguishable,
        }

    kill = {
        "condition": (
            "break_cost for edit policies statistically indistinguishable from "
            "fork across >=4 events"
        ),
        "events_per_policy": {k: len(v) for k, v in by_policy.items()},
        "max_events_in_one_policy": max_events,
        "per_edit_policy": verdicts,
        "all_breaks_above_one_grid_block": {
            policy: {
                "n": len(values),
                "n_gt_64": sum(1 for v in values if v > GRID),
                "fraction_gt_64": (sum(1 for v in values if v > GRID) / len(values))
                if values
                else 0.0,
            }
            for policy, values in by_policy.items()
        },
        "fork_breaks_on_every_event": (
            all(v > GRID for v in by_policy.get("fork", []))
            if by_policy.get("fork")
            else None
        ),
    }

    report = {
        "unit": "U4",
        "renderer": runlog.get("renderer"),
        "design": {
            "renderer_held_constant": runlog.get("renderer"),
            "volatile": runlog.get("volatile"),
            "reps": runlog.get("reps"),
            "reps_rationale": (
                "a second repetition re-sends byte-identical post-compaction "
                "prompts the server already cached, so it would report ~0 and "
                "measure memoisation instead of the break"
            ),
            "budget_tokens": runlog.get("budget_tokens"),
            "keep_last": runlog.get("keep_last"),
            "corpus": "cells/U4/u4_sessions.json (generated by u4_corpus.py; "
                      "corpora/compaction.json does not exist)",
            "corpus_sha256": runlog.get("corpus_sha256"),
            "sessions": sorted({u["session"] for u in units}),
            "cells": [u["cell"].cell for u in units],
        },
        "measurement": {
            "requests": runlog.get("requests"),
            "rows": len(rows),
            "events": len(events),
            "null_cache_coercions": runlog.get("null_coercions"),
            "explicit_prompt_tokens_details": runlog.get("explicit_details"),
            "elapsed_s": runlog.get("elapsed_s"),
            "lock_wait_s": runlog.get("lock_wait_s"),
            "status": runlog.get("status"),
            "stop_reason": runlog.get("stop_reason"),
        },
        "break_cost": {policy: describe(values) for policy, values in by_policy.items()},
        "break_cost_total_per_policy": {
            policy: float(sum(values)) for policy, values in by_policy.items()
        },
        "break_cost_by_event_index": {
            policy: {
                str(i): describe(
                    [
                        float(rec["break_cost"])
                        for rec in per_event
                        if rec["policy"] == policy and rec["event_index"] == i
                    ]
                )
                for i in sorted({r["event_index"] for r in per_event if r["policy"] == policy})
            }
            for policy in by_policy
        },
        "per_event": per_event,
        "paired": comparisons,
        "tests": tests,
        "kill_condition": kill,
        "structural": structure,
        "grid_baseline": grid_baseline(rows, events),
        "ttft": ttft_report(rows, events),
        "hit_rate": hit_rate_report(rows),
    }

    Path(args.json).write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "requests": report["measurement"]["requests"],
        "events": kill["events_per_policy"],
        "break_cost_median": {
            policy: round(values["median"], 1) if values["n"] else None
            for policy, values in report["break_cost"].items()
        },
        "break_cost_p25_p75": {
            policy: (
                [round(values["p25"], 1), round(values["p75"], 1)]
                if values["n"]
                else None
            )
            for policy, values in report["break_cost"].items()
        },
        "break_cost_total": {
            k: round(v, 1) for k, v in report["break_cost_total_per_policy"].items()
        },
        "paired_max_abs_delta": {
            k: round(v["max_abs_delta"], 1) for k, v in comparisons.items()
        },
        "permutation_p": {
            k: (round(v["p_value"], 6) if v["p_value"] is not None else None)
            for k, v in tests.items()
        },
        "indistinguishable_from_fork": {
            k: v["indistinguishable_from_fork"]
            for k, v in kill["per_edit_policy"].items()
        },
        "append_only_holds": structure["append_only_holds"],
        "append_only_violations": len(structure["append_only_violations"]),
        "fork_vs_sliding_byte_identical": structure["post_compaction_byte_identity"][
            "sliding_window vs fork"
        ]["all_identical"],
        "grid_max_abs_residual": report["grid_baseline"]["max_abs_residual"],
        "grid_anomalies": report["grid_baseline"]["n_abs_residual_gt_64"],
        "report": str(args.json),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
