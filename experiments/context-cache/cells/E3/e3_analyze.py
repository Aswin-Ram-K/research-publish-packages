#!/usr/bin/env python3
"""E3 analysis -- decomposition of the warm-append residual, correlations, verdict.

Reads `e3_rows.jsonl` (+ `e3_runlog.json`, `e3_server_state.json`) written by
`e3_probe.py`.  Pure offline: no network.

    python3 e3_analyze.py            # writes e3_report.json next to this file
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
ROWS = HERE / "e3_rows.jsonl"
RUNLOG = HERE / "e3_runlog.json"
STATE = HERE / "e3_server_state.json"
OUT = HERE / "e3_report.json"

GRID = 64


def median(v: Sequence[float]) -> float | None:
    return float(statistics.median(v)) if v else None


def ranks(values: Sequence[float]) -> list[float]:
    """Average ranks (ties share the mean rank)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    n = len(x)
    if n < 3:
        return None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3:
        return None
    return pearson(ranks(x), ranks(y))


def load_rows() -> list[dict[str, Any]]:
    if not ROWS.exists():
        return []
    rows = []
    for line in ROWS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def describe(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": float(min(values)),
        "p25": float(sorted(values)[len(values) // 4]),
        "median": float(statistics.median(values)),
        "mean": round(float(statistics.fmean(values)), 2),
        "p75": float(sorted(values)[(3 * len(values)) // 4]),
        "max": float(max(values)),
    }


def per_chain(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["chain"]].append(r)
    for chain, rs in by.items():
        rs.sort(key=lambda r: r["seq"])
        app = [r for r in rs if r["kind"] == "append"]
        rep = [r for r in rs if r["kind"] == "repeat"]
        out[chain] = {
            "n_rows": len(rs),
            "cold_prompt_tokens": next((r["prompt_tokens"] for r in rs if r["kind"] == "cold"), None),
            "warm_base": next(({"L": r["prompt_tokens"], "cached": r["cached_tokens"],
                                "residual": r["residual"]} for r in rs if r["kind"] == "warm_base"), None),
            "appends": [{"round": r["round"], "L": r["prompt_tokens"],
                         "prev_L": r["prev_prompt_tokens"], "cached": r["cached_tokens"],
                         "residual": r["residual"], "tail_term": r["tail_term"],
                         "deficit": r["deficit"], "ttft_ms": r["ttft_ms"]} for r in app],
            "repeats": [{"round": r["round"], "L": r["prompt_tokens"],
                         "cached": r["cached_tokens"], "residual": r["residual"]} for r in rep],
        }
    return out


def main() -> int:
    rows = load_rows()

    # Previous prompt is the previous request with the SAME salt -- interleaved
    # fresh-salt probes share a chain name but are not part of that chain.
    _prev: dict[str, int] = {}
    mismatch = 0
    for r in sorted(rows, key=lambda r: r["seq"]):
        key = r["salt"]
        pL = _prev.get(key)
        if r["kind"] in ("append", "repeat") and pL is not None:
            expected = GRID * (pL // GRID)
            r["driver_deficit"] = r["deficit"]
            r["prev_prompt_tokens"] = pL
            r["tail_term"] = r["prompt_tokens"] - expected - (r["prompt_tokens"] % GRID)
            r["deficit"] = expected - r["cached_tokens"]
            if r["driver_deficit"] is not None and r["driver_deficit"] != r["deficit"]:
                mismatch += 1
        if r["kind"] != "interleave":
            _prev[key] = r["prompt_tokens"]
    runlog = json.loads(RUNLOG.read_text()) if RUNLOG.exists() else {}
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    app = [r for r in rows if r["kind"] == "append" and r.get("error") == ""]
    rep = [r for r in rows if r["kind"] == "repeat" and r.get("error") == ""]
    warm_base = [r for r in rows if r["kind"] == "warm_base" and r.get("error") == ""]

    res_all = [r["residual"] for r in app if r["residual"] is not None]
    def_all = [r["deficit"] for r in app if r["deficit"] is not None]
    rep_res = [r["residual"] for r in rep if r["residual"] is not None]

    append_zero = sum(1 for d in def_all if d == 0)
    repeat_zero = sum(1 for r in rep_res if r == 0)

    # ---- correlations: deficit vs plausible drivers (append rows only) ----
    drivers: list[dict[str, Any]] = []
    def add_driver(name: str, unit: str, xs: Sequence[float]) -> None:
        ys = [r["deficit"] for r in app if r["deficit"] is not None]
        if len(xs) != len(ys) or len(set(ys)) < 2:
            drivers.append({"metric": name, "unit": unit, "n": len(ys),
                            "spearman_rho": None,
                            "note": "constant/none"})
            return
        drivers.append({"metric": name, "unit": unit, "n": len(ys),
                        "spearman_rho": round(spearman(list(map(float, xs)), ys), 4)
                        if spearman(list(map(float, xs)), ys) is not None else None})

    ordered = sorted(app, key=lambda r: r["seq"])
    add_driver("append_index", "ordinal position of the append in its chain (1..8)",
               [float(i) for i, _ in enumerate(ordered, start=1)])
    add_driver("prev_prompt_tokens", "tokens in the previous full prompt (64-grid anchor)",
               [float(r["prev_prompt_tokens"]) for r in ordered])
    add_driver("current_prompt_tokens", "tokens in this request",
               [float(r["prompt_tokens"]) for r in ordered])
    add_driver("tail_term", "tokens appended since the previous prompt, on the 64 grid",
               [float(r["tail_term"]) for r in ordered])
    add_driver("steps_since_cold", "requests since the cold base of this chain",
               [float(r["steps_since_cold"]) for r in ordered])

    # metrics-derived drivers: same snapshot value across a run is fine, but a
    # driver with no variance cannot be correlated -- those are reported too.
    keys = set()
    for r in ordered:
        keys.update((r.get("metrics_selected") or {}).keys())
    for k in sorted(keys):
        xs = []
        ok = True
        for r in ordered:
            v = (r.get("metrics_selected") or {}).get(k)
            if v is None:
                ok = False
                break
            xs.append(float(v))
        if not ok:
            continue
        unit = k.split("{")[0]
        add_driver(f"metrics:{unit}", "server metric value before the request (its own unit)",
                   xs)

    # ---- perturbation contrast: p60 (after 24 interleaves) vs c60 (same structure) ----
    def deficits(chain: str) -> list[dict]:
        return [{"round": r["round"], "L": r["prompt_tokens"], "prev_L": r["prev_prompt_tokens"],
                 "cached": r["cached_tokens"], "deficit": r["deficit"], "residual": r["residual"]}
                for r in ordered if r["chain"] == chain]

    per = per_chain(rows)
    perturb = {
        "p60": deficits("p60"),
        "c60_control": deficits("c60"),
        "interleaves_between_round1_and_round2": 24,
        "interleaved_tokens_each_est": "~220 (8 sentences); ~4 mamba chunks each",
    }
    p, c = deficits("p60"), deficits("c60")
    if p and c:
        p_by = {d["round"]: d for d in p}
        c_by = {d["round"]: d for d in c}
        perturb["contrast_round2"] = {
            "p60_deficit": p_by.get(2, {}).get("deficit"),
            "c60_deficit": c_by.get(2, {}).get("deficit"),
        }
        perturb["contrast_round3"] = {
            "p60_deficit": p_by.get(3, {}).get("deficit"),
            "c60_deficit": c_by.get(3, {}).get("deficit"),
        }
        perturb["match_collapsed_to_zero_after_pressure"] = [
            d for d in p if d["round"] >= 2 and d["cached"] == 0]

    # ---- verdict (pre-registered rules R1-R4) ----
    n_app, n_rep = len(res_all), len(rep_res)
    rules = {
        "R1_all_append_deficit_zero": bool(n_app and append_zero == n_app),
        "R2_append_deficit_positive_but_repeats_clean": bool(
            n_app and append_zero < n_app and n_rep and repeat_zero == n_rep),
        "R3_repeats_also_deviate": bool(n_rep and repeat_zero < n_rep),
        "counter_observable": bool(state.get("metrics_interesting")),
    }
    if rules["R1_all_append_deficit_zero"] and n_rep and repeat_zero == n_rep:
        verdict = "REFUTED-mamba-eviction"
        statement = (
            "deficit == 0 on every append: the residual equals the appended-tail term on the 64-grid "
            "(L - 64*floor(L_prev/64) - L%64), so the 372/372 deviation is the new tail not being in "
            "the cache yet -- prefix identity -- not checkpointed-state eviction.")
    elif rules["R2_append_deficit_positive_but_repeats_clean"]:
        verdict = "REFUTED-eviction_KEPT-granularity"
        statement = (
            "appends lose tokens beyond the new tail, but a byte-identical repeat of the appended "
            "prompt is exact: the state was retained after completion, the append match simply stops "
            "short of it. Eviction is refuted; checkpoint-boundary granularity survives in weakened form.")
    elif rules["R3_repeats_also_deviate"]:
        verdict = "SURVIVES-or-granularity"
        statement = (
            "repeats of appended prompts also deviate: state for the appended prompt is not fully "
            "reusable. Whether that is eviction or insertion policy is decided by the perturbation.")
    else:
        verdict = "UNTESTABLE"
        statement = "insufficient rows to decide (see blocker)"

    report = {
        "unit": "E3",
        "purpose": "submit G7 (append deviation) to the mamba-checkpoint hypothesis: test or refute",
        "server": {
            "base": state.get("base") or runlog.get("base"),
            "model": state.get("model") or runlog.get("model"),
            "captured_utc": state.get("captured_utc"),
            "metrics_series": state.get("metrics_names"),
            "metrics_interesting": state.get("metrics_interesting"),
            "server_info_sha256": (state.get("/server_info") or {}).get("sha256"),
            "get_model_info_sha256": (state.get("/get_model_info") or {}).get("sha256"),
            "mamba_fields": {
                "uses_mamba_radix_cache": True,
                "max_mamba_cache_size": 64,
                "mamba_radix_cache_strategy": "extra_buffer",
                "mamba_track_interval": 256,
                "linear_replayssm_cache_len": 16,
                "enable_linear_replayssm": False,
                "source": "cells/U2/server_config.json (re-read this unit)",
            },
        },
        "requests": {k: runlog.get(k) for k in
                     ("requests_made", "get_count", "rows", "rows_sha256",
                      "lock_wait_s", "elapsed_s", "status", "blocker")},
        "counts": {"append_rows": n_app, "repeat_rows": n_rep, "warm_base_rows": len(warm_base),
                   "cold_rows": sum(1 for r in rows if r["kind"] == "cold"),
                   "interleave_rows": sum(1 for r in rows if r["kind"] == "interleave"),
                   "errors": sum(1 for r in rows if r.get("error"))},
        "decomposition": {
            "residual_append": describe(res_all),
            "deficit_append": describe(def_all),
            "tail_term_append": describe([r["tail_term"] for r in app if r["tail_term"] is not None]),
            "residual_repeat": describe(rep_res),
            "residual_warm_base": describe([r["residual"] for r in warm_base if r["residual"] is not None]),
            "append_deficit_zero": append_zero,
            "append_deficit_positive": sum(1 for d in def_all if d > 0),
            "append_deficit_negative": sum(1 for d in def_all if d < 0),
            "append_residual_equals_tail_term": sum(
                1 for r in app if r["residual"] is not None and r["residual"] == r["tail_term"]),
            "repeat_residual_zero": repeat_zero,
            "deficit_histogram": dict(Counter(def_all).most_common(20)),
            "residual_append_histogram": dict(Counter(res_all).most_common(20)),
        },
        "drivers": drivers,
        "perturbation": perturb,
        "per_chain": per,
        "recomputed_rows": {"deficit_recomputed_vs_driver_mismatch": mismatch,
                            "note": "driver stored prev_L per chain; repeats after the 24 fresh-salt interleaves were recomputed per salt -- this is the authoritative value"},
        "rules": rules,
        "verdict": {"code": verdict, "statement": statement},
    }
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("counts", "decomposition", "rules", "verdict")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
