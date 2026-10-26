#!/usr/bin/env python3
"""U15 analysis — pure, offline, over ``rows.jsonl``.

One row per live request.  Nothing here touches the network, so a verifier can
re-run this file against the pinned rows and get byte-identical output.

Metric definitions (fixed here so the arm comparison is not re-invented per run):

``total prompt tokens``
    ``sum(prompt_tokens)`` — every token the server was asked to hold, cached
    or not.  This is the window cost.

``total uncached tokens``
    ``sum(prompt_tokens - cached_tokens)`` — tokens actually prefilled.

``hit rate``
    ``sum(cached_tokens) / sum(prompt_tokens)`` (weighted).  The unweighted
    mean of per-turn rates is reported beside it.

``prefix-break event``
    A turn ``t > 1`` where ``cached_t < cached_(t-1)``.  An append-only chain
    can only grow, so the reused prefix shrinking means the cacheable head was
    rewritten (a compaction break) or evicted (an anomaly).  A turn is
    *scheduled* when a compaction was applied to it.

``break cost (gross)``
    ``uncached_t - (prompt_t % 64)`` — tokens re-prefilled beyond the
    unavoidable 64-token-grid residue of an appended turn (U4's definition).

``break cost (net)``
    ``uncached_t - uncached_C(t)`` — the requested metric: the break's cost
    minus Arm C's ambient per-turn residual at the *same* turn.  This is the
    only definition that does not double-count the new turn body, which every
    arm pays.

Usage::

    python3 u15_analyze.py                # reads rows.jsonl beside this file
    python3 u15_analyze.py --rows PATH --json OUT
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
    ("R", "summarise_in_place"),
    ("F", "fork"),
    ("A", "append_note"),
    ("C", "none"),
)
HERE = Path(__file__).resolve().parent
DEFAULT_ROWS = HERE / "rows.jsonl"
DEFAULT_OUT = HERE / "analysis.json"


def dedupe(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the LAST row per ``(arm, turn)``; a resumed run may re-emit one."""

    latest: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["arm"]), int(row["turn"]))
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
                # A crash mid-write can leave one truncated trailing line.
                continue
    return dedupe(rows)


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _median(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize_arm(
    arm: str,
    rows: Sequence[dict[str, Any]],
    control: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    rs = sorted(rows, key=lambda row: int(row["turn"]))
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
    for prev, cur in zip(rs, rs[1:]):
        if int(cur["cached_tokens"]) >= int(prev["cached_tokens"]):
            continue
        turn = int(cur["turn"])
        ctrl = control.get(turn)
        gross = int(cur["uncached"]) - (int(cur["prompt_tokens"]) % GRID)
        net = None if ctrl is None else int(cur["uncached"]) - int(ctrl["uncached"])
        breaks.append(
            {
                "turn": turn,
                "scheduled_compaction": bool(cur.get("scheduled_compaction")),
                "prompt_tokens": int(cur["prompt_tokens"]),
                "cached_tokens": int(cur["cached_tokens"]),
                "prev_cached_tokens": int(prev["cached_tokens"]),
                "cached_drop": int(prev["cached_tokens"]) - int(cur["cached_tokens"]),
                "uncached": int(cur["uncached"]),
                "residual_64": int(cur["prompt_tokens"]) % GRID,
                "break_cost_gross": gross,
                "break_cost_net_vs_C": net,
                "control_uncached": None if ctrl is None else int(ctrl["uncached"]),
                "ttft_ms": float(cur.get("ttft_ms") or 0.0),
            }
        )

    scheduled = [int(r["turn"]) for r in rs if r.get("scheduled_compaction")]
    break_turns = [rec["turn"] for rec in breaks]
    unexpected = [rec for rec in breaks if not rec["scheduled_compaction"]]
    nets = [rec["break_cost_net_vs_C"] for rec in breaks if rec["break_cost_net_vs_C"] is not None]

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
        "turns": [int(rs[0]["turn"]), int(rs[-1]["turn"])],
        "salt": rs[0].get("salt"),
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
        "unexpected_prefix_break_turns": [rec["turn"] for rec in unexpected],
        "breaks": breaks,
        "break_cost_gross_total": sum(rec["break_cost_gross"] for rec in breaks),
        "break_cost_net_total_vs_C": sum(nets) if nets else 0,
        "break_cost_net_fraction_of_uncached": (
            (sum(nets) / total_uncached) if nets and total_uncached else None
        ),
        "uncached_excluding_break_cost_net": total_uncached - (sum(nets) if nets else 0),
        "ambient_uncached_per_turn_mean": _mean([float(v) for v in ambient_uncached]),
        "series": [
            {
                "turn": int(r["turn"]),
                "prompt_tokens": int(r["prompt_tokens"]),
                "cached_tokens": int(r["cached_tokens"]),
                "uncached": int(r["uncached"]),
                "ttft_ms": float(r.get("ttft_ms") or 0.0),
                "scheduled_compaction": bool(r.get("scheduled_compaction")),
                "warm_retry": bool(r.get("warm_retry")),
                "est_chain_tokens": int(r.get("est_chain_tokens") or 0),
            }
            for r in rs
        ],
    }


def decompose(rows: Iterable[dict[str, Any]], arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Where does R's uncached excess over the control actually sit?

    A break event is only two turns out of forty; if the arm-level gap were
    carried by the identical per-turn append residual everywhere else, the
    "cost is head mutability" reading would be wrong.  This splits the gap into
    the scheduled break turns (net of C) and the post-compaction steady state.
    """

    by_arm: dict[str, dict[int, dict[str, Any]]] = {}
    for arm, _policy in ARMS:
        by_arm[arm] = {
            int(r["turn"]): r for r in rows if str(r["arm"]) == arm
        }
    segments: dict[str, dict[str, int]] = {}
    for name, turns in (
        ("1-17 (pre first compaction)", range(1, 18)),
        ("18-34 (post first compaction)", range(18, 35)),
        ("35-40 (post second compaction)", range(35, 41)),
    ):
        segments[name] = {
            arm: sum(
                int(by_arm[arm][t]["uncached"])
                for t in turns
                if t in by_arm.get(arm, {})
            )
            for arm, _policy in ARMS
        }

    r_total = arms["R"].get("total_uncached_tokens")
    c_total = arms["C"].get("total_uncached_tokens")
    a_total = arms["A"].get("total_uncached_tokens")
    gap = (r_total - c_total) if (r_total is not None and c_total is not None) else None
    break_net = arms["R"].get("break_cost_net_total_vs_C")
    steady = (gap - break_net) if (gap is not None and break_net is not None) else None
    counterfactual = (
        (c_total + break_net) if (c_total is not None and break_net is not None) else None
    )

    def mean_turns(arm: str, lo: int, hi: int) -> dict[str, float | None]:
        rs = [by_arm[arm][t] for t in range(lo, hi + 1) if t in by_arm.get(arm, {})]
        if not rs:
            return {"uncached": None, "prompt": None}
        return {
            "uncached": sum(int(r["uncached"]) for r in rs) / len(rs),
            "prompt": sum(int(r["prompt_tokens"]) for r in rs) / len(rs),
        }

    return {
        "note": (
            "R's total-uncached excess over the control splits into (a) the two "
            "scheduled break turns, measured net of C, and (b) the post-compaction "
            "steady state.  If (b) dominates, the arm-level ratio is a window/short-"
            "chain cost, not a break-event cost."
        ),
        "uncached_by_segment": segments,
        "R_minus_C_by_segment": {
            name: values.get("R", 0) - values.get("C", 0) for name, values in segments.items()
        },
        "R_total_uncached": r_total,
        "C_total_uncached": c_total,
        "R_minus_C_total": gap,
        "break_net_total_R": break_net,
        "steady_state_excess_R": steady,
        "steady_state_share_of_gap": (steady / gap) if (steady is not None and gap) else None,
        "counterfactual_R_ambient_plus_break": counterfactual,
        "A_vs_counterfactual_R": (
            (counterfactual / a_total) if (counterfactual and a_total) else None
        ),
        "turns_19_34_means": {arm: mean_turns(arm, 19, 34) for arm, _policy in ARMS},
    }


def analyze(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = dedupe(rows)
    by_arm = {
        arm: [row for row in rows if str(row["arm"]) == arm] for arm, _ in ARMS
    }
    control = {int(r["turn"]): r for r in by_arm["C"]}
    arms = {arm: summarize_arm(arm, by_arm[arm], control) for arm, _ in ARMS}

    a_total = arms["A"].get("total_uncached_tokens")
    r_total = arms["R"].get("total_uncached_tokens")
    f_total = arms["F"].get("total_uncached_tokens")
    c_total = arms["C"].get("total_uncached_tokens")

    ratio_r_over_a = (r_total / a_total) if (a_total and r_total) else None
    ratio_r_over_f = (r_total / f_total) if (f_total and r_total) else None
    ratio_a_over_f = (f_total / a_total) if (a_total and f_total) else None

    decomposition = decompose(rows, arms)
    gap = decomposition["R_minus_C_total"] or 0
    break_net = decomposition["break_net_total_R"] or 0
    steady = decomposition["steady_state_excess_R"] or 0
    share = decomposition["steady_state_share_of_gap"]
    counterfactual = decomposition["counterfactual_R_ambient_plus_break"]
    a_vs_cf = decomposition["A_vs_counterfactual_R"]
    means = decomposition["turns_19_34_means"]
    r_mean = means.get("R", {}).get("uncached") or 0.0
    c_mean = means.get("C", {}).get("uncached") or 0.0
    rf_delta = (
        (r_total - f_total) / r_total if (r_total and f_total is not None) else None
    )

    if ratio_r_over_a is not None and ratio_r_over_a >= 1.5:
        answer = "yes"
        statement = (
            "YES: Arm A beats Arm R by {ratio:.3f}x on total uncached tokens "
            "({r} vs {a}). R and F are within {rf:.1%} of each other, so the "
            "edit-vs-fork contrast is not the driver. Decomposition: only "
            "{bn} tokens of R's {gap}-token excess over the control "
            "({bshare:.1%} of the gap) is net break cost at the two compaction "
            "turns; the other {ss} tokens ({share:.1%}) is the post-compaction "
            "steady state, where R's short window re-prefills "
            "~{ru:.0f} tokens/turn against the control's ~{cu:.0f}. The >=1.5x "
            "test passes, but the cost is window truncation-plus-break, not the "
            "break event alone: with the control's ambient residual and only the "
            "break effect, R would total {cf} and A/R would be {acf:.2f}x."
        ).format(
            ratio=ratio_r_over_a,
            r=r_total,
            a=a_total,
            rf=rf_delta if rf_delta is not None else 0.0,
            bn=break_net,
            gap=gap,
            bshare=(1.0 - share) if share is not None else 0.0,
            share=share if share is not None else 0.0,
            ss=steady,
            ru=r_mean,
            cu=c_mean,
            cf=counterfactual,
            acf=a_vs_cf if a_vs_cf is not None else 0.0,
        )
    else:
        answer = "no"
        ratio_text = "n/a" if ratio_r_over_a is None else f"{ratio_r_over_a:.3f}x"
        statement = (
            "NO: Arm A does NOT beat Arm R by >=1.5x on total uncached tokens "
            "(R/A = {ratio}; R={r}, A={a}). The refutation of the "
            "edit-vs-fork advantage stands unqualified: neither editing the "
            "head nor forking it dominates, because the per-turn append "
            "residual dominates both.".format(ratio=ratio_text, r=r_total, a=a_total)
        )
        if gap:
            statement += (
                " Decomposition: break cost net of C is {bn} of R's {gap}-token "
                "excess over the control; {ss} ({share:.1%}) is the "
                "post-compaction steady state.".format(
                    bn=break_net,
                    gap=gap,
                    ss=steady,
                    share=share if share is not None else 0.0,
                )
            )

    a_growth = arms["A"].get("prompt_tokens", {})
    c_growth = arms["C"].get("prompt_tokens", {})
    window_cost = {
        "arm": "A",
        "first_prompt_tokens": a_growth.get("first"),
        "last_prompt_tokens": a_growth.get("last"),
        "prompt_growth_tokens": a_growth.get("growth_first_to_last"),
        "prompt_growth_factor": a_growth.get("growth_factor"),
        "total_prompt_tokens": arms["A"].get("total_prompt_tokens"),
        "control_total_prompt_tokens": arms["C"].get("total_prompt_tokens"),
        "extra_prompt_tokens_vs_control": (
            (arms["A"].get("total_prompt_tokens") or 0)
            - (arms["C"].get("total_prompt_tokens") or 0)
        ),
        "final_prompt_extra_vs_control": (
            (a_growth.get("last") or 0) - (c_growth.get("last") or 0)
        ),
        "note": (
            "Arm A never shrinks: every compaction appends a [note] node to the "
            "whole existing chain.  `extra_prompt_tokens_vs_control` is the "
            "token mass those notes add over the 40-turn window; "
            "`prompt_growth_tokens` is the window growth from first to last turn."
        ),
    }

    payload: dict[str, Any] = {
        "unit": "U15",
        "cell": "U15",
        "metric_definitions": {
            "total_uncached_tokens": "sum(prompt_tokens - cached_tokens)",
            "hit_rate": "sum(cached_tokens) / sum(prompt_tokens)",
            "prefix_break_event": "turn t>1 with cached_t < cached_(t-1)",
            "break_cost_gross": "uncached_t - (prompt_t % 64)",
            "break_cost_net": "uncached_t - uncached_C(t) at the same turn",
        },
        "arms": arms,
        "comparison": {
            "total_uncached_tokens": {
                arm: arms[arm].get("total_uncached_tokens") for arm, _ in ARMS
            },
            "total_prompt_tokens": {
                arm: arms[arm].get("total_prompt_tokens") for arm, _ in ARMS
            },
            "hit_rate": {arm: arms[arm].get("hit_rate_weighted") for arm, _ in ARMS},
            "ratio_R_over_A": ratio_r_over_a,
            "ratio_R_over_F": ratio_r_over_f,
            "ratio_F_over_A": ratio_a_over_f,
            "delta_A_minus_C_uncached": (
                (a_total - c_total) if (a_total is not None and c_total is not None) else None
            ),
            "delta_R_minus_C_uncached": (
                (r_total - c_total) if (r_total is not None and c_total is not None) else None
            ),
            "delta_F_minus_C_uncached": (
                (f_total - c_total) if (f_total is not None and c_total is not None) else None
            ),
        },
        "claim": {
            "question": "Does Arm A beat Arm R by >=1.5x on total uncached tokens?",
            "answer": answer,
            "ratio_R_over_A": ratio_r_over_a,
            "statement": statement,
            "if_yes": "cost is head mutability, not edit-vs-fork",
            "if_no": "the refutation stands unqualified",
        },
        "window_cost_of_never_compacting": window_cost,
        "decomposition": decomposition,
    }
    payload["digest"] = {
        "rows_sha256": None,  # filled by the caller that knows the path
        "n_rows": len(rows),
        "n_rows_by_arm": {arm: len(by_arm[arm]) for arm, _ in ARMS},
    }
    return payload


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="U15 offline analysis")
    parser.add_argument("--rows", default=str(DEFAULT_ROWS))
    parser.add_argument("--json", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    rows_path = Path(args.rows)
    rows = load_rows(rows_path)
    payload = analyze(rows)
    payload["digest"]["rows_sha256"] = hashlib.sha256(rows_path.read_bytes()).hexdigest()
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
            f"net_break_cost={s['break_cost_net_total_vs_C']}"
        )
    c = payload["claim"]
    print(f"claim: {c['answer']}  R/A={c['ratio_R_over_A']}")
    print(c["statement"])
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
