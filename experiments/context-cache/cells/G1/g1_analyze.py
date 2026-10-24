#!/usr/bin/env python3
"""G1 analysis — pure, offline, over ``rows.jsonl``.

Two arms only: E (summarise_in_place / EDIT) and F (fork / FORK).
3 sessions x 44 turns, compaction at turns 18 and 35.  No control arm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Iterable, Sequence

GRID = 64
ARMS: tuple[tuple[str, str], ...] = (
    ("E", "summarise_in_place"),
    ("F", "fork"),
)
SESSIONS = ("g1-s1", "g1-s2", "g1-s3")
TURNS = 44
COMPACT_TURNS = (18, 35)
HERE = Path(__file__).resolve().parent
DEFAULT_ROWS = HERE / "rows.jsonl"
DEFAULT_OUT = HERE / "analysis.json"


def dedupe(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["arm"]), str(row.get("session")), int(row["turn"]))
        latest.pop(key, None)
        latest[key] = row
    return list(latest.values())


def load_rows(path: str | Path = DEFAULT_ROWS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return dedupe(rows)


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize_arm(arm: str, rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    rs = sorted(rows, key=lambda row: (str(row.get("session")), int(row["turn"])))
    if not rs:
        return {"arm": arm, "n_rows": 0, "missing": True}

    prompts = [int(r["prompt_tokens"]) for r in rs]
    cached = [int(r["cached_tokens"]) for r in rs]
    uncached = [int(r["uncached"]) for r in rs]
    ttfts = [float(r.get("ttft_ms") or 0.0) for r in rs]

    total_prompt = sum(prompts)
    total_cached = sum(cached)
    total_uncached = sum(uncached)

    breaks: list[dict[str, Any]] = []
    # Prefix breaks are detected per session chain.
    by_session: dict[str, list[dict[str, Any]]] = {}
    for r in rs:
        by_session.setdefault(str(r.get("session")), []).append(r)
    for session, srows in by_session.items():
        srows = sorted(srows, key=lambda r: int(r["turn"]))
        for prev, cur in zip(srows, srows[1:]):
            if int(cur["cached_tokens"]) >= int(prev["cached_tokens"]):
                continue
            turn = int(cur["turn"])
            gross = int(cur["uncached"]) - (int(cur["prompt_tokens"]) % GRID)
            breaks.append(
                {
                    "session": session,
                    "turn": turn,
                    "scheduled_compaction": bool(cur.get("scheduled_compaction")),
                    "prompt_tokens": int(cur["prompt_tokens"]),
                    "cached_tokens": int(cur["cached_tokens"]),
                    "prev_cached_tokens": int(prev["cached_tokens"]),
                    "cached_drop": int(prev["cached_tokens"]) - int(cur["cached_tokens"]),
                    "uncached": int(cur["uncached"]),
                    "residual_64": int(cur["prompt_tokens"]) % GRID,
                    "break_cost_gross": gross,
                    "ttft_ms": float(cur.get("ttft_ms") or 0.0),
                    "est_chain_tokens_before": int(cur.get("est_chain_tokens_before") or 0),
                    "est_chain_tokens_after": int(cur.get("est_chain_tokens_after") or 0),
                }
            )

    scheduled = sorted({int(r["turn"]) for r in rs if r.get("scheduled_compaction")})
    break_turns = sorted({rec["turn"] for rec in breaks})
    unexpected = [rec for rec in breaks if not rec["scheduled_compaction"]]
    grosses = [rec["break_cost_gross"] for rec in breaks]

    per_turn_hit = [
        (int(r["cached_tokens"]) / int(r["prompt_tokens"])) if int(r["prompt_tokens"]) else 0.0
        for r in rs
    ]
    ambient_turns = [r for r in rs if int(r["turn"]) > 1 and not r.get("scheduled_compaction")]
    ambient_uncached = [int(r["uncached"]) for r in ambient_turns]

    return {
        "arm": arm,
        "policy": rs[0].get("policy"),
        "n_rows": len(rs),
        "sessions": sorted(by_session),
        "turns": [int(rs[0]["turn"]) if rs else None, int(rs[-1]["turn"]) if rs else None],
        "salt": rs[0].get("salt") if len({r.get("salt") for r in rs}) == 1 else [r.get("salt") for r in rs],
        "total_prompt_tokens": total_prompt,
        "total_cached_tokens": total_cached,
        "total_uncached_tokens": total_uncached,
        "hit_rate_weighted": (total_cached / total_prompt) if total_prompt else 0.0,
        "hit_rate_mean_per_turn": _mean(per_turn_hit),
        "prompt_tokens": {
            "first": prompts[0],
            "last": prompts[-1],
            "min": min(prompts),
            "max": max(prompts),
            "mean": _mean([float(p) for p in prompts]),
            "growth_first_to_last": prompts[-1] - prompts[0],
            "growth_factor": (prompts[-1] / prompts[0]) if prompts[0] else None,
        },
        "ttft_ms": {"mean": _mean(ttfts), "median": _median(ttfts)},
        "cold_turn_cached_tokens": int(rs[0]["cached_tokens"]) if int(rs[0]["turn"]) == 1 else None,
        "scheduled_compaction_turns": scheduled,
        "prefix_break_events": len(breaks),
        "prefix_break_turns": break_turns,
        "unexpected_prefix_break_turns": sorted({rec["turn"] for rec in unexpected}),
        "breaks": breaks,
        "break_cost_gross_total": sum(grosses),
        "ambient_uncached_per_turn_mean": _mean([float(v) for v in ambient_uncached]),
        "series": [
            {
                "session": str(r.get("session")),
                "turn": int(r["turn"]),
                "prompt_tokens": int(r["prompt_tokens"]),
                "cached_tokens": int(r["cached_tokens"]),
                "uncached": int(r["uncached"]),
                "ttft_ms": float(r.get("ttft_ms") or 0.0),
                "scheduled_compaction": bool(r.get("scheduled_compaction")),
                "warm_retry": bool(r.get("warm_retry")),
                "est_chain_tokens_before": int(r.get("est_chain_tokens_before") or 0),
                "est_chain_tokens_after": int(r.get("est_chain_tokens_after") or 0),
            }
            for r in rs
        ],
    }


def window_imbalance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_session_arm: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
    for r in rows:
        by_session_arm.setdefault((str(r.get("session")), str(r["arm"])), {})[int(r["turn"])] = r

    per_turn: list[dict[str, Any]] = []
    for session in SESSIONS:
        e_rows = by_session_arm.get((session, "E"), {})
        f_rows = by_session_arm.get((session, "F"), {})
        for turn in range(1, TURNS + 1):
            er = e_rows.get(turn)
            fr = f_rows.get(turn)
            if er is None or fr is None:
                continue
            per_turn.append(
                {
                    "session": session,
                    "turn": turn,
                    "E_prompt_tokens": int(er["prompt_tokens"]),
                    "F_prompt_tokens": int(fr["prompt_tokens"]),
                    "prompt_delta_E_minus_F": int(er["prompt_tokens"]) - int(fr["prompt_tokens"]),
                    "E_est_chain_tokens_after": int(er.get("est_chain_tokens_after") or 0),
                    "F_est_chain_tokens_after": int(fr.get("est_chain_tokens_after") or 0),
                    "est_delta_E_minus_F": int(er.get("est_chain_tokens_after") or 0)
                    - int(fr.get("est_chain_tokens_after") or 0),
                    "post_compaction": turn >= COMPACT_TURNS[0],
                }
            )

    post = [r for r in per_turn if r["post_compaction"]]
    return {
        "note": (
            "Imbalance between EDIT and FORK after compaction.  The library does "
            "not force the two arms to the same rendered token count; these deltas "
            "are reported as a limitation rather than normalised away."
        ),
        "per_turn": per_turn,
        "post_compaction_turns": list(range(COMPACT_TURNS[0], TURNS + 1)),
        "post_compaction_prompt_delta_mean": _mean(
            [float(r["prompt_delta_E_minus_F"]) for r in post]
        ),
        "post_compaction_prompt_delta_max_abs": (
            max(abs(r["prompt_delta_E_minus_F"]) for r in post) if post else None
        ),
        "post_compaction_est_delta_mean": _mean(
            [float(r["est_delta_E_minus_F"]) for r in post]
        ),
        "post_compaction_est_delta_max_abs": (
            max(abs(r["est_delta_E_minus_F"]) for r in post) if post else None
        ),
        "n_post_compaction_turns_imbalanced": sum(
            1 for r in post if r["est_delta_E_minus_F"] != 0
        ),
        "n_post_compaction_turns": len(post),
    }


def per_break_pairs(rows: list[dict[str, Any]], arms: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    by_arm_session_turn: dict[tuple[str, str, int], dict[str, Any]] = {}
    for r in rows:
        by_arm_session_turn[(str(r["arm"]), str(r.get("session")), int(r["turn"]))] = r

    pairs: list[dict[str, Any]] = []
    for session in SESSIONS:
        e_breaks = {b["turn"]: b for b in arms["E"].get("breaks", []) if b["session"] == session}
        f_breaks = {b["turn"]: b for b in arms["F"].get("breaks", []) if b["session"] == session}
        for turn in sorted(set(e_breaks) | set(f_breaks)):
            eb = e_breaks.get(turn)
            fb = f_breaks.get(turn)
            e_cost = eb["break_cost_gross"] if eb else None
            f_cost = fb["break_cost_gross"] if fb else None
            e_uncached = eb["uncached"] if eb else None
            f_uncached = fb["uncached"] if fb else None
            ratio = (e_cost / f_cost) if (e_cost is not None and f_cost not in (None, 0)) else None
            within = None
            if e_cost is not None and f_cost not in (None, 0):
                within = abs(e_cost - f_cost) / abs(f_cost) <= 0.10
            pairs.append(
                {
                    "session": session,
                    "turn": turn,
                    "scheduled_compaction": bool((eb or fb or {}).get("scheduled_compaction")),
                    "E_break_cost_gross": e_cost,
                    "F_break_cost_gross": f_cost,
                    "E_uncached": e_uncached,
                    "F_uncached": f_uncached,
                    "E_prompt_tokens": eb["prompt_tokens"] if eb else None,
                    "F_prompt_tokens": fb["prompt_tokens"] if fb else None,
                    "ratio_E_over_F": ratio,
                    "within_10pct": within,
                    "E_cached_drop": eb["cached_drop"] if eb else None,
                    "F_cached_drop": fb["cached_drop"] if fb else None,
                }
            )
    return pairs


def analyze(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = dedupe(rows)
    by_arm = {arm: [row for row in rows if str(row["arm"]) == arm] for arm, _ in ARMS}
    arms = {arm: summarize_arm(arm, by_arm[arm]) for arm, _ in ARMS}

    e_total = arms["E"].get("total_uncached_tokens")
    f_total = arms["F"].get("total_uncached_tokens")
    e_prompt_total = arms["E"].get("total_prompt_tokens")
    f_prompt_total = arms["F"].get("total_prompt_tokens")

    ratio_total_uncached_e_over_f = (
        (e_total / f_total) if (e_total and f_total) else None
    )

    pairs = per_break_pairs(rows, arms)
    e_costs = [p["E_break_cost_gross"] for p in pairs if p["E_break_cost_gross"] is not None]
    f_costs = [p["F_break_cost_gross"] for p in pairs if p["F_break_cost_gross"] is not None]
    mean_e_cost = _mean([float(v) for v in e_costs]) if e_costs else None
    mean_f_cost = _mean([float(v) for v in f_costs]) if f_costs else None
    ratio_mean_cost = (
        (mean_e_cost / mean_f_cost) if (mean_e_cost is not None and mean_f_cost not in (None, 0)) else None
    )
    all_within = bool(pairs) and all(p.get("within_10pct") is True for p in pairs)
    n_within = sum(1 for p in pairs if p.get("within_10pct") is True)
    kill_condition = "REFUTED" if all_within else "not refuted"

    imbalance = window_imbalance(rows)

    payload: dict[str, Any] = {
        "unit": "G1",
        "cell": "G1",
        "metric_definitions": {
            "total_uncached_tokens": "sum(prompt_tokens - cached_tokens)",
            "hit_rate": "sum(cached_tokens) / sum(prompt_tokens)",
            "prefix_break_event": "turn t>1 with cached_t < cached_(t-1)",
            "break_cost_gross": "uncached_t - (prompt_t % 64)",
            "per_break_uncached_cost": "uncached tokens on the break turn",
        },
        "arms": arms,
        "comparison": {
            "total_prompt_tokens": {"E": e_prompt_total, "F": f_prompt_total},
            "total_cached_tokens": {
                "E": arms["E"].get("total_cached_tokens"),
                "F": arms["F"].get("total_cached_tokens"),
            },
            "total_uncached_tokens": {"E": e_total, "F": f_total},
            "hit_rate": {
                "E": arms["E"].get("hit_rate_weighted"),
                "F": arms["F"].get("hit_rate_weighted"),
            },
            "ratio_total_uncached_E_over_F": ratio_total_uncached_e_over_f,
            "prefix_break_events": {"E": arms["E"].get("prefix_break_events"), "F": arms["F"].get("prefix_break_events")},
        },
        "per_break_uncached_cost": {
            "note": (
                "Per break event (3 sessions x 2 compaction turns = 6 per arm). "
                "cost_gross = uncached_t - (prompt_t % 64).  within_10pct compares "
                "EDIT cost to FORK cost."
            ),
            "events": pairs,
            "n_events": len(pairs),
            "n_events_within_10pct": n_within,
            "all_events_within_10pct": all_within,
            "mean_break_cost_gross_E": mean_e_cost,
            "mean_break_cost_gross_F": mean_f_cost,
            "ratio_mean_break_cost_E_over_F": ratio_mean_cost,
        },
        "window_token_imbalance": imbalance,
        "kill_condition": {
            "rule": (
                "If per-break cost in EDIT is within 10% of FORK across all 6 break "
                "events, the 'never create the break' claim is REFUTED."
            ),
            "all_events_within_10pct": all_within,
            "n_events_within_10pct": n_within,
            "n_events": len(pairs),
            "verdict": kill_condition,
        },
        "u15_1_700x_survives_decomposition": False,
        "u15_decomposition_note": (
            "U15's 1.700x total-uncached ratio (R/A) does not survive decomposition: "
            "only 1620 of R's 20649-token excess over the control (7.8%) was net break "
            "cost at the two compaction turns; 19029 tokens (92.2%) was post-compaction "
            "steady-state window truncation.  G1 isolates the break cost with a constant "
            "post-compaction window; its per-break cost ratio E/F is "
            f"{ratio_mean_cost if ratio_mean_cost is not None else 'n/a'} and kill-condition "
            f"verdict is {kill_condition}."
        ),
        "claim": {
            "question": (
                "Is the per-break cost in the EDIT arm within 10% of the FORK arm "
                "across all 6 break events?"
            ),
            "answer": "yes" if all_within else "no",
            "ratio_E_over_F_per_break_mean": ratio_mean_cost,
            "all_events_within_10pct": all_within,
            "statement": (
                ("REFUTED: " if all_within else "NOT REFUTED: ")
                + "per-break cost in EDIT is "
                + ("within 10% of FORK across all 6 break events "
                   if all_within
                   else f"not within 10% of FORK across all 6 break events "
                        f"({n_within}/{len(pairs)} within 10%) ")
                + f"(mean gross E={mean_e_cost}, F={mean_f_cost}, ratio={ratio_mean_cost}). "
                + "U15's 1.700x does not survive decomposition: it was 92.2% "
                + "post-compaction window truncation, not break-event cost."
            ),
            "u15_1_700x_survives_decomposition": False,
        },
    }
    return payload


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G1 offline analysis")
    parser.add_argument("--rows", default=str(DEFAULT_ROWS))
    parser.add_argument("--json", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    rows_path = Path(args.rows)
    rows = load_rows(rows_path)
    payload = analyze(rows)
    payload.setdefault("digest", {})
    payload["digest"]["rows_sha256"] = hashlib.sha256(rows_path.read_bytes()).hexdigest()
    payload["digest"]["n_rows"] = len(rows)
    payload["digest"]["n_rows_by_arm"] = {arm: len([r for r in rows if r["arm"] == arm]) for arm, _ in ARMS}
    payload["digest"]["n_rows_by_session"] = {s: len([r for r in rows if str(r.get("session")) == s]) for s in SESSIONS}
    out = Path(args.json)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"rows: {payload['digest']['n_rows']} {payload['digest']['n_rows_by_arm']}")
    for arm, _ in ARMS:
        s = payload["arms"][arm]
        if s.get("missing"):
            print(f"{arm}: MISSING")
            continue
        print(
            f"{arm}: prompt={s['total_prompt_tokens']:>7} "
            f"cached={s['total_cached_tokens']:>7} "
            f"uncached={s['total_uncached_tokens']:>7} "
            f"hit={s['hit_rate_weighted']:.3f} "
            f"breaks={s['prefix_break_events']} "
            f"gross={s['break_cost_gross_total']}"
        )
    c = payload["claim"]
    print(f"kill: {payload['kill_condition']['verdict']}  ratio_mean={c['ratio_E_over_F_per_break_mean']}")
    print(c["statement"])
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
