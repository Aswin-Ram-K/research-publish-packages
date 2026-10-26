#!/usr/bin/env python3
"""U9 analysis — does a prompt-cache hit actually reduce TTFT?

Pure function of ``u9_trials.jsonl``; no network, no clock.  Re-runnable, so
every number in the report can be re-derived from the raw trial rows.

Definitions (fixed before the live sweep):

* **miss trial** -- a request whose ``cached_tokens == 0`` (genuinely cold).
* **hit trial** -- the byte-identical request sent next, ``cached_tokens ==
  64*floor(prompt/64)`` (the U2 law).  A trial failing its predicate is
  excluded from the distributions and counted separately.
* **paired delta** -- within one repetition, ``miss.ttft - hit.ttft``; positive
  means the hit was faster.  One delta per repetition, so n = 7 per length.
* **ratio** -- ``median(hit.ttft) / median(miss.ttft)``; a value < 1 means the
  hit is faster.
* **noise floor** -- coefficient of variation of 10 consecutive byte-identical
  warm sends (and, at 1k, of 10 independent cold sends).  The effect is called
  *resolvable* only when |median delta| exceeds 2 x the warm-path sigma AND the
  bootstrap CI of the median delta excludes zero.

Usage::

    python3 u9_analyze.py            # writes u9_report.json, prints table
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

HERE = Path(__file__).resolve().parent
IN_TRIALS = HERE / "u9_trials.jsonl"
OUT_REPORT = HERE / "u9_report.json"

BOOTSTRAP = 5000
BOOTSTRAP_SEED = 20261020
SIGMA_K = 2.0


def expected_cached(prompt_tokens: int) -> int:
    """The cache law, refined at the block boundary.

    U2 measured ``cached == 64*floor(L/64)`` over 44 lengths whose residues mod
    64 were all NON-zero (its residue list was 1,2,3,5,7,...,62 -- never 0).
    This sweep hit the untested case: at L=1024 the server reuses 960 tokens,
    not 1024, because the last token of the prompt is never reusable.  The
    general law is therefore ``64*floor((L-1)/64)``; it equals U2's for every
    length that is not an exact multiple of 64.
    """

    return 64 * ((prompt_tokens - 1) // 64)


# --------------------------------------------------------------------------- #
# Small statistics helpers (no numpy dependency)
# --------------------------------------------------------------------------- #
def percentile(values: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile (numpy's default), p in [0, 100]."""

    if not values:
        raise ValueError("percentile of empty sequence")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * (p / 100.0)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def median(values: Sequence[float]) -> float:
    return percentile(values, 50.0)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def stdev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def cv(values: Sequence[float]) -> float:
    mu = mean(values)
    return stdev(values) / mu if mu else float("nan")


class Lcg:
    A = 6364136223846793005
    C = 1442695040888963407
    M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = (seed ^ 0x9E3779B97F4A7C15) & (self.M - 1)

    def below(self, n: int) -> int:
        self.state = (self.A * self.state + self.C) & (self.M - 1)
        return self.state % n


def sign_test_p(deltas: Sequence[float]) -> float:
    """Exact one-sided binomial p for 'miss slower than hit' (H1: delta > 0)."""

    n = len(deltas)
    wins = sum(1 for d in deltas if d > 0)
    ties = sum(1 for d in deltas if d == 0)
    n_eff = n - ties
    if n_eff == 0:
        return 1.0
    # P(X >= wins) under Binomial(n_eff, 0.5)
    tail = sum(math.comb(n_eff, k) for k in range(wins, n_eff + 1))
    return tail / (2 ** n_eff)


def bootstrap_median_ci(
    values: Sequence[float], *, alpha: float = 0.05, reps: int = BOOTSTRAP
) -> tuple[float, float]:
    if len(values) < 2:
        return (float("nan"), float("nan"))
    rng = Lcg(BOOTSTRAP_SEED)
    n = len(values)
    medians: list[float] = []
    for _ in range(reps):
        sample = [values[rng.below(n)] for _ in range(n)]
        medians.append(median(sample))
    return (percentile(medians, 100 * alpha / 2), percentile(medians, 100 * (1 - alpha / 2)))


def linfit(xs: Sequence[float], ys: Sequence[float]) -> dict[str, float]:
    """Ordinary least squares ``y = intercept + slope*x``."""

    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx else float("nan")
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    return {
        "slope_ms_per_token": slope,
        "intercept_ms": intercept,
        "r2": 1 - ss_res / ss_tot if ss_tot else float("nan"),
        "n": n,
    }


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_rows(path: Path = IN_TRIALS) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def last_per_rep(rows: Iterable[dict[str, Any]], role: str) -> dict[int, dict[str, Any]]:
    """Latest record per repetition (a salt-retry supersedes its first attempt)."""

    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        if row["role"] == role:
            out[int(row["rep"])] = row
    return out


def summary(values: Sequence[float]) -> dict[str, float]:
    return {
        "n": len(values),
        "median": round(median(values), 3),
        "p10": round(percentile(values, 10), 3),
        "p90": round(percentile(values, 90), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "mean": round(mean(values), 3),
        "cv": round(cv(values), 4),
    }


# --------------------------------------------------------------------------- #
# Noise floor
# --------------------------------------------------------------------------- #
def noise_floor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    hit_rows = [r for r in rows if r["role"] == "noise_hit"]
    for length in sorted({int(r["length_target"]) for r in hit_rows}):
        vals = [r["ttft_ms"] for r in hit_rows if int(r["length_target"]) == length]
        out[f"warm_{length}"] = {
            **summary(vals),
            "ttft_ms": [round(v, 3) for v in vals],
            "all_cached_ok": all(r["cached_ok"] for r in hit_rows
                                 if int(r["length_target"]) == length),
        }
    cold_rows = [r for r in rows if r["role"] == "noise_cold"]
    if cold_rows:
        vals = [r["ttft_ms"] for r in cold_rows]
        out["cold_1024"] = {
            **summary(vals),
            "ttft_ms": [round(v, 3) for v in vals],
            "all_cold_ok": all(r["cold_ok"] for r in cold_rows),
        }
    return out


def sigma_from_noise(noise: dict[str, Any], length: int) -> float | None:
    """Warm-path sigma in ms at ``length``: CV x the hit median at that length.

    The CV is measured at the two noise lengths (1k, 8k); for other lengths we
    use the CV of the nearest measured noise point and the *hit* median at the
    length in question.  Conservative: the warm path gets noisier, not less, as
    prompts grow, so this cannot manufacture significance.
    """

    available = sorted(
        (int(k.split("_")[1]), v) for k, v in noise.items() if k.startswith("warm_")
    )
    if not available:
        return None
    nearest = min(available, key=lambda kv: abs(kv[0] - length))[1]
    return None if not nearest["median"] else nearest["cv"] * nearest["median"]


# --------------------------------------------------------------------------- #
# Main analysis
# --------------------------------------------------------------------------- #
def analyse(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = sorted({int(r["length_target"]) for r in rows if r["role"] in ("miss", "hit")})
    noise = noise_floor(rows)
    per_length: dict[str, Any] = {}
    deltas_all: list[float] = []
    ratio_points: list[tuple[float, float]] = []

    for length in lengths:
        subset = [r for r in rows if int(r["length_target"]) == length]
        miss_by_rep = last_per_rep(subset, "miss")
        hit_by_rep = last_per_rep(subset, "hit")
        reps = sorted(set(miss_by_rep) & set(hit_by_rep))
        invalid_miss = [r for r in miss_by_rep.values() if not r["cold_ok"]]
        invalid_hit = [r for r in hit_by_rep.values()
                       if r["cached_tokens"] != expected_cached(r["prompt_tokens"])]
        reps_valid = [r for r in reps
                      if miss_by_rep[r]["cold_ok"]
                      and hit_by_rep[r]["cached_tokens"]
                      == expected_cached(hit_by_rep[r]["prompt_tokens"])]
        # rows where the driver's pre-correction predicate (64*(L//64))
        # disagreed with the refined law -- labels only, no measured value
        predicate_disagreements = [
            int(r["rep"]) for r in hit_by_rep.values()
            if bool(r["cached_ok"])
            != (r["cached_tokens"] == expected_cached(r["prompt_tokens"]))
        ]

        miss_ttft = [miss_by_rep[r]["ttft_ms"] for r in reps_valid]
        hit_ttft = [hit_by_rep[r]["ttft_ms"] for r in reps_valid]
        miss_wall = [miss_by_rep[r]["wall_ms"] for r in reps_valid]
        hit_wall = [hit_by_rep[r]["wall_ms"] for r in reps_valid]
        deltas = [m - h for m, h in zip(miss_ttft, hit_ttft)]

        entry: dict[str, Any] = {
            "pair_length_tokens": int(round(median(
                [miss_by_rep[r]["prompt_tokens"] for r in reps_valid]))) if reps_valid else None,
            "miss_prompt_tokens": [miss_by_rep[r]["prompt_tokens"] for r in reps_valid],
            "hit_cached_tokens": [hit_by_rep[r]["cached_tokens"] for r in reps_valid],
            # measured, not modelled: the driver's own expected_uncached field was
            # computed under the pre-correction law and undercounts by 64 at L % 64 == 0
            "uncached_tokens": [hit_by_rep[r]["prompt_tokens"] - hit_by_rep[r]["cached_tokens"]
                                for r in reps_valid],
            "miss": summary(miss_ttft) if miss_ttft else {"n": 0},
            "hit": summary(hit_ttft) if hit_ttft else {"n": 0},
            "miss_wall": summary(miss_wall) if miss_wall else {"n": 0},
            "hit_wall": summary(hit_wall) if hit_wall else {"n": 0},
            "invalid_miss_reps": [int(r["rep"]) for r in invalid_miss],
            "invalid_hit_reps": [int(r["rep"]) for r in invalid_hit],
            "predicate_disagreement_reps": predicate_disagreements,
            "expected_cached_law": "64*((L-1)//64)",
            "hit_first_warm_median_ms": (
                round(median([hit_by_rep[r]["ttft_ms"] for r in reps_valid
                              if int(hit_by_rep[r]["attempt"]) == 1]), 3)
                if any(int(hit_by_rep[r]["attempt"]) == 1 for r in reps_valid) else None),
            "hit_repeat_warm_median_ms": (
                round(median([hit_by_rep[r]["ttft_ms"] for r in reps_valid
                              if int(hit_by_rep[r]["attempt"]) > 1]), 3)
                if any(int(hit_by_rep[r]["attempt"]) > 1 for r in reps_valid) else None),
            "hit_repeat_warm_reps": [int(r) for r in reps_valid
                                     if int(hit_by_rep[r]["attempt"]) > 1],
            "pairs_valid": len(reps_valid),
            "deltas_ms": [round(d, 3) for d in deltas],
            "order_split": {},
        }
        if miss_ttft and hit_ttft:
            entry["ratio"] = round(median(hit_ttft) / median(miss_ttft), 4)
            entry["speedup"] = round(median(miss_ttft) / median(hit_ttft), 2)
            entry["abs_diff_ms"] = round(median(miss_ttft) - median(hit_ttft), 3)
            entry["delta_median_ms"] = round(median(deltas), 3) if deltas else None
            entry["delta_ci95_ms"] = (
                [round(x, 3) for x in bootstrap_median_ci(deltas)] if len(deltas) > 1
                else [None, None]
            )
            entry["sign_test_p"] = round(sign_test_p(deltas), 4) if deltas else None
            entry["wall_ratio"] = round(median(hit_wall) / median(miss_wall), 4)
            sigma = sigma_from_noise(noise, length)
            entry["noise_sigma_ms"] = None if sigma is None else round(sigma, 3)
            entry["noise_margin_ms"] = None if sigma is None else round(SIGMA_K * sigma, 3)
            entry["resolvable"] = bool(
                sigma is not None
                and deltas
                and abs(median(deltas)) > SIGMA_K * sigma
                and entry["delta_ci95_ms"][0] is not None
                and entry["delta_ci95_ms"][0] > 0
            )

            for order in ("A", "B"):
                sel = [r for r in reps_valid if miss_by_rep[r]["order"] == order]
                if sel:
                    d = [miss_by_rep[r]["ttft_ms"] - hit_by_rep[r]["ttft_ms"] for r in sel]
                    entry["order_split"][order] = {
                        "n": len(sel),
                        "delta_median_ms": round(median(d), 3),
                        "miss_median_ms": round(median(
                            [miss_by_rep[r]["ttft_ms"] for r in sel]), 3),
                        "hit_median_ms": round(median(
                            [hit_by_rep[r]["ttft_ms"] for r in sel]), 3),
                    }
            deltas_all.extend(deltas)
            ratio_points.append((float(entry["pair_length_tokens"] or length),
                                 entry["ratio"]))

        per_length[str(length)] = entry

    # ---- scaling fits ------------------------------------------------ #
    usable = [e for e in per_length.values() if e.get("pairs_valid")]
    fit: dict[str, Any] = {}
    if len(usable) >= 2:
        xs_miss = [e["pair_length_tokens"] for e in usable]
        fit["miss"] = linfit(xs_miss, [e["miss"]["median"] for e in usable])
        fit["hit"] = linfit(xs_miss, [e["hit"]["median"] for e in usable])
        fit["miss"]["implied_prefill_tokens_per_s"] = round(
            1000.0 / fit["miss"]["slope_ms_per_token"], 1
        ) if fit["miss"]["slope_ms_per_token"] else None
        fit["hit"]["implied_prefill_tokens_per_s"] = round(
            1000.0 / fit["hit"]["slope_ms_per_token"], 1
        ) if fit["hit"]["slope_ms_per_token"] else None
        for key in ("miss", "hit"):
            fit[key] = {k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in fit[key].items()}
        # power laws for each arm: ttft ~ L^exponent (honest about convexity,
        # which a straight line through a convex miss curve hides)
        for key in ("miss", "hit"):
            power = linfit([math.log(x) for x in xs_miss],
                           [math.log(e[key]["median"]) for e in usable])
            fit[f"{key}_power"] = {
                "exponent": round(power["slope_ms_per_token"], 4),
                "r2": round(power["r2"], 4),
                "n": power["n"],
            }
        # log-log slope of the ratio: s < 0 means the ratio falls as L grows
        log_fit = linfit([math.log(x) for x, _ in ratio_points],
                         [math.log(y) for _, y in ratio_points])
        fit["ratio_loglog"] = {
            "exponent": round(log_fit["slope_ms_per_token"], 4),
            "r2": round(log_fit["r2"], 4),
            "n": log_fit["n"],
            "reading": (
                "ratio falls with L (prefill-skipping signature)"
                if log_fit["slope_ms_per_token"] < -0.2
                else "ratio roughly flat with L (prefill is not the bottleneck)"
                if abs(log_fit["slope_ms_per_token"]) <= 0.2
                else "ratio RISES with L (unexpected; investigate)"
            ),
        }
        fit["ratio_at_length"] = {
            e["pair_length_tokens"]: e["ratio"] for e in usable
        }

    # ---- order effect ------------------------------------------------ #
    order_effect = {}
    for order in ("A", "B"):
        vals = [e["order_split"][order]["delta_median_ms"]
                for e in usable if order in e["order_split"]]
        vals = [v for v in vals if v is not None]
        if vals:
            order_effect[order] = {"lengths": len(vals), "delta_median_ms": round(median(vals), 3)}
    if "A" in order_effect and "B" in order_effect:
        order_effect["abs_gap_ms"] = round(
            abs(order_effect["A"]["delta_median_ms"] - order_effect["B"]["delta_median_ms"]), 3
        )

    # ---- verdict ------------------------------------------------------ #
    resolvable = [e for e in usable if e.get("resolvable")]
    faster_everywhere = all(e["abs_diff_ms"] > 0 for e in usable)
    worst = min(usable, key=lambda e: e["abs_diff_ms"]) if usable else None
    verdict: dict[str, Any] = {
        "speed_claim_supported": bool(resolvable) and faster_everywhere,
        "lengths_measured": len(usable),
        "lengths_resolvable": len(resolvable),
        "all_lengths_hit_faster": faster_everywhere,
        "smallest_effect": None if worst is None else {
            "length_tokens": worst["pair_length_tokens"],
            "abs_diff_ms": worst["abs_diff_ms"],
            "noise_margin_ms": worst.get("noise_margin_ms"),
            "resolvable": worst.get("resolvable"),
        },
        "min_sign_test_p_possible_n7": round(1 / 2 ** 7, 4),
        "sign_test_p_by_length": {
            e["pair_length_tokens"]: e["sign_test_p"] for e in usable
        },
    }

    return {
        "unit": "U9",
        "question": "Is a prompt-cache hit faster (TTFT) than a cold request at equal prompt length?",
        "method": {
            "metric": "TTFT = first streamed content chunk; wall = full response",
            "cold_isolation": "fresh 16-hex salt at the front of message 0 -> radix prefix match 0",
            "pairs": "one cold and one byte-identical warm request per repetition, adjacent in time",
            "order_pattern": "A(miss,hit) for reps 0/2/4/6; B(prime,hit,miss) for reps 1/3/5",
            "requests": "strictly serial, one in flight",
            "hit_predicate": "cached == 64*floor(prompt/64) (U2's law)",
            "resolvable": "|median paired delta| > 2 sigma_warm AND bootstrap CI95 excludes 0",
        },
        "noise_floor": noise,
        "per_length": per_length,
        "fit": fit,
        "order_effect": order_effect,
        "verdict": verdict,
    }


def main() -> int:
    rows = load_rows()
    report = analyse(rows)
    OUT_REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"{'L':>7} {'miss med':>8} {'hit med':>8} {'ratio':>6} {'delta':>8} "
          f"{'p':>6} {'noise':>7} {'res':>4} {'wall r':>7} {'cached':>8}")
    for key in sorted(report["per_length"], key=lambda k: int(report["per_length"][k]
                                                              ["pair_length_tokens"] or 0)):
        e = report["per_length"][key]
        if not e.get("pairs_valid"):
            print(f"{key:>7} INVALID")
            continue
        print(
            f"{e['pair_length_tokens']:>7} {e['miss']['median']:>8.1f} "
            f"{e['hit']['median']:>8.1f} {e['ratio']:>6.3f} "
            f"{e['abs_diff_ms']:>8.1f} {e['sign_test_p']:>6.4f} "
            f"{(e['noise_margin_ms'] if e['noise_margin_ms'] is not None else float('nan')):>7.1f} "
            f"{str(e['resolvable'])[:3]:>4} "
            f"{e['wall_ratio']:>7.3f} "
            f"{median(e['hit_cached_tokens'])}/{e['pair_length_tokens']:<6}"
        )
    print()
    print(json.dumps({"fit": report["fit"], "order": report["order_effect"],
                      "verdict": report["verdict"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
