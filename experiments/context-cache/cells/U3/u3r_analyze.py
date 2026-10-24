"""U3-R analysis: per-arm prefix-retention curves + the pre-registered kill test.

Reads ``rows.jsonl`` (one row per live request) and emits ``analysis.json``.

Definitions (fixed before the data was read — see ``orchestration/units/U3-R.md``)
-------------------------------------------------------------------------------
``cached_max(arm, scenario)``
    The largest ``cached_tokens`` that arm ever reaches on that scenario.  It is
    the arm's own asymptote, so retention is scale-free: 1.0 means "this arm
    kept everything it is capable of keeping", 0.0 means "it kept nothing the
    previous turn had cached".

``retention(arm, scenario, turn) = cached_tokens / cached_max(arm, scenario)``
    Turn 1 is cold for every arm and is reported but excluded from the kill test.

Kill test (pre-registered, NOT redefinable here)
------------------------------------------------
``naive_mutable`` retains more than 50% of its cached tokens after turn 2 ->
the volatility claim has no support and is reported REFUTED.

"After turn 2" is read as ``turn >= 3`` (turns 3..N), and the statistic is the
**median across all turn>=3 cells** (arm x scenario x turn).  The median is the
pre-registered statistic; the mean and the per-scenario medians are reported
alongside so the reader can see the distribution, not just the verdict.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ARMS = ("pointer", "naive_append", "naive_mutable")
KILL_THRESHOLD = 0.50
KILL_ARM = "naive_mutable"
KILL_FROM_TURN = 3


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def cached_max_by(rows: list[dict]) -> dict[tuple[str, str], int]:
    out: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        key = (r["arm"], r["scenario"])
        out[key] = max(out[key], int(r["cached_tokens"]))
    return dict(out)


def analyse(rows: list[dict]) -> dict:
    cmax = cached_max_by(rows)
    # ---------------------------------------------------------------- curves
    curves: dict[str, dict[str, list[dict]]] = {a: {} for a in ARMS}
    for r in rows:
        arm, sc, turn = r["arm"], r["scenario"], int(r["turn"])
        top = cmax[(arm, sc)]
        cached = int(r["cached_tokens"])
        prompt = int(r["prompt_tokens"])
        curves.setdefault(arm, {}).setdefault(sc, []).append(
            {
                "turn": turn,
                "prompt_tokens": prompt,
                "cached_tokens": cached,
                "uncached": int(r["uncached"]),
                "cached_max": top,
                "retention": round(cached / top, 6) if top else None,
                "hit_rate": round(cached / prompt, 6) if prompt else None,
                "prefix_sha256": r.get("prefix_sha256", "")[:16],
            }
        )
    for arm in curves:
        for sc in curves[arm]:
            curves[arm][sc].sort(key=lambda x: x["turn"])

    # ------------------------------------------------------- kill statistic
    def keep_cells(arm: str, pred) -> list[float]:
        vals = []
        for sc, series in curves.get(arm, {}).items():
            for p in series:
                if pred(p["turn"]) and p["retention"] is not None:
                    vals.append(p["retention"])
        return vals

    mut_after2 = keep_cells(KILL_ARM, lambda t: t >= KILL_FROM_TURN)
    mut_after2_incl2 = keep_cells(KILL_ARM, lambda t: t >= 2)
    mut_late = keep_cells(KILL_ARM, lambda t: t >= 8)

    def stat(vals: list[float]) -> dict:
        if not vals:
            return {"n": 0}
        vals_sorted = sorted(vals)
        return {
            "n": len(vals),
            "median": round(statistics.median(vals), 6),
            "mean": round(statistics.fmean(vals), 6),
            "min": round(vals_sorted[0], 6),
            "max": round(vals_sorted[-1], 6),
            "frac_cells_above_50pct": round(
                sum(1 for v in vals if v > KILL_THRESHOLD) / len(vals), 6
            ),
        }

    per_scenario_medians = {}
    for sc in curves.get(KILL_ARM, {}):
        vals = [
            p["retention"]
            for p in curves[KILL_ARM][sc]
            if p["turn"] >= KILL_FROM_TURN and p["retention"] is not None
        ]
        per_scenario_medians[sc] = stat(vals)

    mut_after2_stat = stat(mut_after2)
    median_after2 = mut_after2_stat.get("median")
    refuted = median_after2 is not None and median_after2 > KILL_THRESHOLD

    # ------------------------------------------------------------ per-arm
    per_arm = {}
    for arm in ARMS:
        after2 = keep_cells(arm, lambda t: t >= KILL_FROM_TURN)
        late = keep_cells(arm, lambda t: t >= 8)
        all_vals = keep_cells(arm, lambda t: True)
        per_arm[arm] = {
            "cached_max_by_scenario": {
                sc: cmax.get((arm, sc), 0) for sc in curves.get(arm, {})
            },
            "retention_turn1_cold": stat(keep_cells(arm, lambda t: t == 1)),
            "retention_turn2": stat(keep_cells(arm, lambda t: t == 2)),
            "retention_after_turn2": stat(after2),
            "retention_turn_ge_8": stat(late),
            "retention_all_turns": stat(all_vals),
            "mean_hit_rate": round(
                statistics.fmean(
                    [
                        p["hit_rate"]
                        for sc in curves.get(arm, {})
                        for p in curves[arm][sc]
                        if p["hit_rate"] is not None
                    ]
                ),
                6,
            )
            if curves.get(arm)
            else None,
        }

    # -------------------------------------------- control equivalence check
    # pointer vs naive_append that share a scenario must be byte-identical.
    control = []
    for sc in curves.get("pointer", {}):
        a = [p["prefix_sha256"] for p in curves["pointer"][sc]]
        b = [p["prefix_sha256"] for p in curves.get("naive_append", {}).get(sc, [])]
        if a and b and len(a) == len(b):
            control.append(
                {
                    "scenario": sc,
                    "turns_compared": len(a),
                    "identical_prompts": a == b,
                    "pointer_cached_max": cmax.get(("pointer", sc), 0),
                    "naive_append_cached_max": cmax.get(("naive_append", sc), 0),
                }
            )

    # ----------------------------------------------------- pairwise deltas
    pairwise = {}
    for sc in curves.get("pointer", {}):
        pa = {p["turn"]: p for p in curves["pointer"][sc]}
        diffs = []
        for other in ("naive_mutable",):
            oa = {p["turn"]: p for p in curves.get(other, {}).get(sc, [])}
            for t in sorted(set(pa) & set(oa)):
                diffs.append(
                    {
                        "turn": t,
                        "pointer_cached": pa[t]["cached_tokens"],
                        other + "_cached": oa[t]["cached_tokens"],
                        "delta_cached": pa[t]["cached_tokens"] - oa[t]["cached_tokens"],
                    }
                )
            pairwise[sc] = {"vs": other, "turns": diffs}

    retention_gap = None
    if per_arm["pointer"]["retention_after_turn2"].get("n") and per_arm[KILL_ARM][
        "retention_after_turn2"
    ].get("n"):
        retention_gap = round(
            per_arm["pointer"]["retention_after_turn2"]["median"]
            - per_arm[KILL_ARM]["retention_after_turn2"]["median"],
            6,
        )

    # ------------------------------------------------- absolute retention
    # The self-normalised retention above can DECEIVE a naive reader: an arm
    # that keeps only a small constant floor (naive_mutable keeps ~800 tokens,
    # the 768/832-token 64-token-grid floor of the system header) has that floor
    # as its own ``cached_max`` and therefore scores retention == 1.0 forever.
    # So the same turn windows are also reported in ABSOLUTE terms: mean hit
    # rate, mean cached tokens, and the share of the turn-16 prompt that is
    # served from cache.  Both statistics are reported; neither is hidden.
    windows = [(1, 1), (2, 2), (3, 4), (5, 8), (9, 12), (13, 16)]
    absolute: dict[str, dict[str, dict]] = {a: {} for a in ARMS}
    for arm in ARMS:
        series = [p for sc in curves.get(arm, {}) for p in curves[arm][sc]]
        for lo, hi in windows:
            sel = [p for p in series if lo <= p["turn"] <= hi]
            if not sel:
                continue
            key = f"turns_{lo}_{hi}"
            absolute[arm][key] = {
                "n": len(sel),
                "mean_hit_rate": round(
                    statistics.fmean(p["hit_rate"] for p in sel if p["hit_rate"] is not None),
                    6,
                ),
                "mean_cached_tokens": round(
                    statistics.fmean(p["cached_tokens"] for p in sel), 1
                ),
                "mean_prompt_tokens": round(
                    statistics.fmean(p["prompt_tokens"] for p in sel), 1
                ),
            }

    def share_of_last_prompt(arm: str) -> dict:
        """Fraction of the FINAL prompt that comes from cache, per scenario."""

        out = {}
        for sc, series in curves.get(arm, {}).items():
            if not series:
                continue
            last = max(series, key=lambda p: p["turn"])
            out[sc] = {
                "turn": last["turn"],
                "prompt_tokens": last["prompt_tokens"],
                "cached_tokens": last["cached_tokens"],
                "share_cached": last["hit_rate"],
            }
        return out

    absolute_share_last = {a: share_of_last_prompt(a) for a in ARMS}

    verdict = "REFUTED" if refuted else "SUPPORTED"

    return {
        "unit": "U3-R",
        "corpus": "volatility.json",
        "arms": list(ARMS),
        "statistic": {
            "retention": "cached_tokens / cached_max(arm, scenario)",
            "kill_stat": f"median retention of {KILL_ARM} over turns >= {KILL_FROM_TURN}",
            "kill_threshold": KILL_THRESHOLD,
        },
        "requests": {
            "rows": len(rows),
            "by_arm": {
                a: sum(1 for r in rows if r["arm"] == a) for a in ARMS
            },
            "scenarios": sorted({r["scenario"] for r in rows}),
            "max_turn": max((int(r["turn"]) for r in rows), default=0),
        },
        "kill_test": {
            "arm": KILL_ARM,
            "from_turn": KILL_FROM_TURN,
            "threshold": KILL_THRESHOLD,
            "median_retention_after_turn2": median_after2,
            "refuted": refuted,
            "verdict": verdict,
            "after_turn2": mut_after2_stat,
            "after_turn1_incl_turn2": stat(mut_after2_incl2),
            "turns_ge_8": stat(mut_late),
            "per_scenario_medians": per_scenario_medians,
        },
        "per_arm": per_arm,
        "absolute_retention_by_window": absolute,
        "absolute_share_of_last_prompt": absolute_share_last,
        "metric_caveat": (
            "Self-normalised retention (cached/cached_max) is the pre-registered kill "
            "statistic, but an arm whose cached tokens are a small CONSTANT floor scores "
            "retention=1.0 forever. Read it against absolute_retention_by_window and "
            "absolute_share_of_last_prompt, which are on the same scale for all arms."
        ),
        "retention_gap_pointer_minus_mutable_after_turn2": retention_gap,
        "control_equivalence_pointer_vs_naive_append": control,
        "pairwise_by_scenario": pairwise,
        "curves": curves,
    }


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(here / "rows.jsonl"))
    ap.add_argument("--out", default=str(here / "analysis.json"))
    args = ap.parse_args(argv)
    rows = load_rows(Path(args.rows))
    if not rows:
        print("no rows", file=sys.stderr)
        return 2
    result = analyse(rows)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    kt = result["kill_test"]
    print(
        f"rows={result['requests']['rows']} "
        f"mutable_median_after_turn2={kt['median_retention_after_turn2']} "
        f"verdict={kt['verdict']}"
    )
    for arm in ARMS:
        s = result["per_arm"][arm]["retention_after_turn2"]
        print(f"  {arm:15s} median_retention_after_t2={s.get('median')} n={s.get('n')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
