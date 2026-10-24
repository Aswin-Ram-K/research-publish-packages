#!/usr/bin/env python3
"""Offline analysis for WIN-SGL: battery metrics + the recovered cache grid law.

Inputs (all offline, no live calls):

* ``cells/WIN-SGL/rows.jsonl`` — this unit's rows (battery + grid probe), every
  row carrying ``stack``/``config_id``/``config_sha256``/``page_size``/
  ``layer_types``;
* ``cells/G3/rows.jsonl`` — the S0 baseline already on disk (page_size 1,
  888 rows, the *identical* battery);
* ``state/config/<config>-server-info.json`` — that configuration's
  ``/get_server_info`` capture;
* ``cells/WIN-SGL/logs/<config>-config.json`` — launch/restore record.

The grid law is recovered three ways and reported separately, because they
answer different questions:

1. ``gcd_cached`` — the coarsest token block that divides every cached count on
   the configuration (a 64-grid can cache odd multiples of 64; a 128-grid
   cannot);
2. ``fit`` — exact-match counts for ``cached = g*floor((L-1)/g)`` and
   ``cached = g*floor(L/g)`` over steady rows, for g in 32/64/128/256;
3. ``probe`` — four controlled targets, three byte-identical sends each, with
   the 64-grid and the 128-grid prediction printed per row.

Usage::

    python win_sgl_analyze.py            # writes analysis.json + prints a summary
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ROWS_PATH = HERE / "rows.jsonl"
G3_ROWS = REPO / "experiments" / "context-cache" / "cells" / "G3" / "rows.jsonl"
CONFIG_DIR = REPO / "state" / "config"
LOGS = HERE / "logs"
ANALYSIS_PATH = HERE / "analysis.json"

ARMS = ("R", "A", "C", "H")
DEPTHS = ("32k", "64k")
GRID_CANDIDATES = (32, 64, 128, 256)
SERVER_INFO_KEYS = (
    "page_size", "c128_page_size", "mamba_radix_cache_strategy", "mamba_track_interval",
    "max_mamba_cache_size", "mem_fraction_static", "disable_chunked_prefix_cache",
    "max_total_num_tokens", "chunked_prefill_size", "max_running_requests",
)


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def gcd_all(values: Iterable[int]) -> int:
    g = 0
    for v in values:
        g = math.gcd(g, int(v))
        if g == 1:
            return 1
    return g


def law(g: int, L: int, variant: str = "minus1") -> int:
    if L <= 0:
        return 0
    if variant == "minus1":
        return g * ((L - 1) // g)
    return g * (L // g)


def battery_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"depths": {}}
    ok_rows = []
    for depth in DEPTHS:
        arms_out: dict[str, Any] = {}
        for arm in ARMS:
            rs = sorted((r for r in rows if r.get("depth") == depth and r.get("arm") == arm),
                        key=lambda r: r["turn"])
            if not rs:
                arms_out[arm] = {"n": 0, "missing": True}
                continue
            ok = [r for r in rs if r.get("status") == 200 and r.get("prompt_tokens")]
            ok_rows.extend(ok)
            prompt = sum(r["prompt_tokens"] for r in ok)
            cached = sum(r["cached_tokens"] for r in ok)
            uncached = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in ok)
            arms_out[arm] = {
                "n": len(rs),
                "n_ok": len(ok),
                "errors": len(rs) - len(ok),
                "total_prompt_tokens": prompt,
                "total_cached_tokens": cached,
                "total_uncached_tokens": uncached,
                "hit_fraction": round(cached / prompt, 6) if prompt else None,
                "mean_uncached_per_turn": round(uncached / len(ok), 1) if ok else None,
                "final_prompt_tokens": ok[-1]["prompt_tokens"] if ok else None,
                "budget_tokens": rs[-1].get("budget_tokens"),
                "scheduled_compactions": sum(1 for r in rs if r.get("scheduled_compaction")),
            }
        out["depths"][depth] = arms_out
    prompt = sum(r["prompt_tokens"] for r in ok_rows)
    cached = sum(r["cached_tokens"] for r in ok_rows)
    uncached = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in ok_rows)
    out["total"] = {
        "n_rows": len(ok_rows),
        "total_prompt_tokens": prompt,
        "total_cached_tokens": cached,
        "total_uncached_tokens": uncached,
        "hit_fraction": round(cached / prompt, 6) if prompt else None,
        "mean_uncached_per_turn": round(uncached / len(ok_rows), 3) if ok_rows else None,
    }
    # per-arm means pooled over both depths (the R/A/C/H comparison of the S0 table)
    for arm in ARMS:
        vals = [out["depths"][d][arm]["mean_uncached_per_turn"] for d in DEPTHS
                if isinstance((out["depths"].get(d) or {}).get(arm, {}).get("mean_uncached_per_turn"), (int, float))]
        if vals:
            out.setdefault("mean_uncached_per_turn_by_arm", {})[arm] = round(sum(vals) / len(vals), 1)
    for depth in DEPTHS:
        vals = [v["mean_uncached_per_turn"] for v in out["depths"].get(depth, {}).values()
                if isinstance(v.get("mean_uncached_per_turn"), (int, float))]
        out.setdefault("mean_uncached_per_turn_by_depth", {})[depth] = (
            round(sum(vals) / len(vals), 2) if vals else None)
    return out


def grid_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    steady = [r for r in rows if r.get("cached_tokens") and r["cached_tokens"] > 0
              and int(r.get("turn", 0)) > 1 and not r.get("scheduled_compaction")
              and r.get("prompt_tokens")]
    if not steady:
        return {"n_steady": 0}
    cached = [r["cached_tokens"] for r in steady]
    deficits = [r["prompt_tokens"] - r["cached_tokens"] for r in steady]
    fits = {}
    for g in GRID_CANDIDATES:
        fits[str(g)] = {
            "exact_floor_L": sum(1 for r in steady if law(g, r["prompt_tokens"], "floor") == r["cached_tokens"]),
            "exact_floor_Lm1": sum(1 for r in steady if law(g, r["prompt_tokens"], "minus1") == r["cached_tokens"]),
        }
    # Page-size-agnostic granularity: g is consistent with a row when the cached
    # prefix is a multiple of g and the uncached tail is at most one g-block (the
    # tail page that cannot be cached, plus at most a little lag).  The granularity
    # is the LARGEST g that is consistent with every steady row.
    consistent = {
        str(g): sum(1 for r in steady
                    if r["cached_tokens"] % g == 0 and 0 < r["prompt_tokens"] - r["cached_tokens"] <= g)
        for g in GRID_CANDIDATES}
    # Granularity is the gcd of the cached prefixes: every steady row's cached
    # prefix is an exact multiple of it.  (The ``consistent`` counts above are a
    # *lag* statistic, not a granularity one -- the cached prefix typically trails
    # the prompt by ~860 tokens, i.e. the state chunks not yet flushed.)
    best = gcd_all(cached)
    odd64 = [r for r in steady if r["cached_tokens"] % 128 == 64]
    near = sorted((r for r in steady if r["prompt_tokens"] - r["cached_tokens"] <= 128),
                  key=lambda r: r["prompt_tokens"] - r["cached_tokens"])
    return {
        "n_steady": len(steady),
        "gcd_cached": gcd_all(cached),
        "n_cached_multiple_64": sum(1 for c in cached if c % 64 == 0),
        "n_cached_multiple_128": sum(1 for c in cached if c % 128 == 0),
        "n_cached_odd_multiple_64": len(odd64),
        "fraction_cached_multiple_128": round(sum(1 for c in cached if c % 128 == 0) / len(cached), 4),
        "fit": fits,
        "tail_within_one_block_by_g": consistent,
        "best_fit_g": best,
        "deficit": {
            "min": min(deficits),
            "median": statistics.median(deficits),
            "max": max(deficits),
            "n_le_64": sum(1 for d in deficits if d <= 64),
            "n_le_128": sum(1 for d in deficits if d <= 128),
        },
        "near_grid_rows": [
            {"depth": r.get("depth"), "arm": r.get("arm"), "turn": r.get("turn"),
             "L": r["prompt_tokens"], "cached": r["cached_tokens"],
             "deficit": r["prompt_tokens"] - r["cached_tokens"],
             "pred_64": law(64, r["prompt_tokens"], "minus1"),
             "pred_128": law(128, r["prompt_tokens"], "minus1")}
            for r in near[:12]
        ],
    }


def probe_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    probes = [r for r in rows if r.get("phase") == "probe"]
    if not probes:
        return {"n_rows": 0}
    per_target: dict[int, Any] = {}
    for r in probes:
        target = int(r["target"])
        per_target.setdefault(target, {"target": target, "roles": {}})
        if r.get("prompt_tokens"):
            per_target[target]["L"] = r["prompt_tokens"]
            per_target[target]["pred_64"] = law(64, r["prompt_tokens"], "minus1")
            per_target[target]["pred_128"] = law(128, r["prompt_tokens"], "minus1")
            per_target[target]["discriminating"] = per_target[target]["pred_64"] != per_target[target]["pred_128"]
            per_target[target]["pred_64_floor"] = law(64, r["prompt_tokens"], "floor")
            per_target[target]["pred_128_floor"] = law(128, r["prompt_tokens"], "floor")
        per_target[target]["roles"][str(r["role"])] = {
            "cached": r.get("cached_tokens"), "status": r.get("status"), "gap_ms": r.get("gap_ms")}
    rows_out = []
    for target in sorted(per_target):
        entry = per_target[target]
        last = None
        for role in ("cold", "rep1", "rep2"):
            cached = (entry["roles"].get(role) or {}).get("cached")
            if cached:
                last = cached
        entry["settled_cached"] = last
        entry["matches_64"] = None if last is None else last == entry.get("pred_64")
        entry["matches_128"] = None if last is None else last == entry.get("pred_128")
        entry["matches_floor_L_64"] = None if last is None else last == law(64, entry["L"], "floor")
        # page-size-agnostic test: the settled prefix is a multiple of g and the
        # gap to the prompt is at most one g-block (the tail that cannot be cached).
        if last is None:
            entry["consistent_64"] = entry["consistent_128"] = None
        else:
            deficit = entry["L"] - last
            entry["deficit"] = deficit
            entry["consistent_64"] = (last % 64 == 0) and (0 < deficit <= 64)
            entry["consistent_128"] = (last % 128 == 0) and (0 < deficit <= 128)
        rows_out.append(entry)
    discriminators = [e for e in rows_out if e.get("discriminating")]
    return {
        "n_rows": len(probes),
        "targets": rows_out,
        "n_discriminating_targets": len(discriminators),
        "discriminating_matches_64": sum(1 for e in discriminators if e.get("matches_64")),
        "discriminating_matches_128": sum(1 for e in discriminators if e.get("matches_128")),
        "consistent_64": sum(1 for e in rows_out if e.get("consistent_64")),
        "consistent_128": sum(1 for e in rows_out if e.get("consistent_128")),
        "n_targets": len(rows_out),
        "gate": {
            "identical_pair_second_send_cached": rows_out[0]["roles"].get("rep1", {}).get("cached")
            if rows_out else None,
            "identical_third_send_cached": rows_out[0]["roles"].get("rep2", {}).get("cached")
            if rows_out else None,
        },
    }


def server_info(config_id: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{config_id}-server-info.json"
    if not path.exists():
        return {}
    info = json.loads(path.read_text(encoding="utf-8"))
    out = {k: info.get(k) for k in SERVER_INFO_KEYS}
    out["_path"] = str(path.relative_to(REPO))
    out["_sha256"] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    return out


def config_record(config_id: str) -> dict[str, Any]:
    path = LOGS / f"{config_id}-config.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def identity_vs_s0(rows: Sequence[dict[str, Any]], s0_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    bench = {(r.get("depth"), r.get("arm"), int(r.get("turn", 0))): r.get("prompt_tokens") for r in s0_rows}
    matched = mismatch = missing = 0
    examples: list[Any] = []
    for r in rows:
        if r.get("phase") == "probe":
            continue
        key = (r.get("depth"), r.get("arm"), int(r.get("turn", 0)))
        if key not in bench:
            missing += 1
            continue
        if bench[key] == r.get("prompt_tokens"):
            matched += 1
        else:
            mismatch += 1
            if len(examples) < 5:
                examples.append({"key": list(key), "s0": bench[key], "this": r.get("prompt_tokens")})
    return {"matched": matched, "mismatch": mismatch, "missing": missing, "examples": examples}


def cached_vs_s0(rows: Sequence[dict[str, Any]], s0_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Paired (same key => byte-identical prompt) comparison of cached_tokens with S0."""

    bench = {(r.get("depth"), r.get("arm"), int(r.get("turn", 0))): r for r in s0_rows}
    deltas: list[int] = []
    pairs = 0
    for r in rows:
        if r.get("phase") == "probe" or r.get("status") != 200:
            continue
        base = bench.get((r.get("depth"), r.get("arm"), int(r.get("turn", 0))))
        if not base or base.get("cached_tokens") is None or r.get("cached_tokens") is None:
            continue
        pairs += 1
        deltas.append(r["cached_tokens"] - base["cached_tokens"])
    if not pairs:
        return {"n_paired": 0}
    hist: dict[str, int] = {}
    for d in deltas:
        hist[str(d)] = hist.get(str(d), 0) + 1
    top = sorted(hist.items(), key=lambda kv: -kv[1])[:8]
    return {
        "n_paired": pairs,
        "n_identical": sum(1 for d in deltas if d == 0),
        "n_lower": sum(1 for d in deltas if d < 0),
        "n_higher": sum(1 for d in deltas if d > 0),
        "mean_delta_tokens": round(sum(deltas) / len(deltas), 2),
        "total_delta_tokens": sum(deltas),
        "delta_histogram_top": [{"delta": int(k), "n": v} for k, v in top],
    }


def restores() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for config_id in ("S1", "S2", "S3"):
        path = LOGS / f"{config_id}-restore-verify.json"
        if path.exists():
            try:
                out[config_id] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                out[config_id] = {"error": "unparseable"}
    return out


def main() -> int:
    rows = load_rows(ROWS_PATH)
    s0_rows = [r for r in load_rows(G3_ROWS) if r.get("arm")]
    configs: dict[str, Any] = {}

    s0 = {
        "source": "experiments/context-cache/cells/G3/rows.jsonl (S0 baseline, page_size 1)",
        "page_size": 1,
        "battery": battery_metrics(s0_rows),
        "grid": grid_stats(s0_rows),
        "n_rows": len(s0_rows),
        "probe": {"n_rows": 0, "note": "S0 has no grid probe; grid recovered from its 888 battery rows"},
        "server_info": server_info("S0"),
    }
    configs["S0"] = s0

    for config_id in ("S1", "S2", "S3"):
        rs = [r for r in rows if r.get("config_id") == config_id]
        record = config_record(config_id)
        battery_rows = [r for r in rs if r.get("phase") != "probe"]
        configs[config_id] = {
            "page_size": record.get("reported_page_size", record.get("page_size_requested")),
            "launch": record.get("launch"),
            "container": record.get("container"),
            "flag": record.get("flag"),
            "n_rows": len(rs),
            "n_battery_rows": len(battery_rows),
            "requests_live": record.get("cell", {}).get("requests_live", len(rs)),
            "requests_cap": record.get("cell", {}).get("requests_cap"),
            "cell_status": record.get("cell", {}).get("status"),
            "battery": battery_metrics(battery_rows) if battery_rows else {"depths": {}, "total": {"n_rows": 0}},
            "grid": grid_stats(battery_rows) if battery_rows else {"n_steady": 0},
            "probe": probe_stats(rs),
            "identity_vs_s0": identity_vs_s0(battery_rows, s0_rows) if battery_rows else {},
            "cached_vs_s0": cached_vs_s0(battery_rows, s0_rows) if battery_rows else {},
            "server_info": server_info(config_id),
            "restore": record.get("restore"),
            "startup_failure_log": record.get("startup_failure_log"),
        }

    # The load-bearing comparison: is S1's grid different *in granularity* from S0's?
    verdict: dict[str, Any] = {}
    for config_id in ("S1", "S2"):
        g0 = s0["grid"]
        g1 = configs[config_id]["grid"]
        if not g1.get("n_steady"):
            verdict[config_id] = {"measured": False, "reason": "no steady rows"}
            continue
        verdict[config_id] = {
            "measured": True,
            "gcd_s0": g0.get("gcd_cached"),
            "gcd_this": g1.get("gcd_cached"),
            "same_granularity": g0.get("gcd_cached") == g1.get("gcd_cached"),
            "odd_multiple_64_s0": g0.get("n_cached_odd_multiple_64"),
            "odd_multiple_64_this": g1.get("n_cached_odd_multiple_64"),
            "fraction_multiple_128_s0": g0.get("fraction_cached_multiple_128"),
            "fraction_multiple_128_this": g1.get("fraction_cached_multiple_128"),
            "probe_discriminating_targets": configs[config_id]["probe"].get("n_discriminating_targets"),
            "probe_matches_64": configs[config_id]["probe"].get("discriminating_matches_64"),
            "probe_matches_128": configs[config_id]["probe"].get("discriminating_matches_128"),
        }

    requests_total = sum(int(configs[c].get("requests_live") or 0) for c in ("S1", "S2", "S3"))
    payload = {
        "restores": restores(),
        "unit": "WIN-SGL",
        "purpose": "characterise the SGLang pager/flag space: page_size 64, page_size 128, chunked-prefix-cache flag",
        "stack": "sglang",
        "model_layers": {"linear_attention": 30, "full_attention": 10, "n_layers": 40,
                         "full_attention_interval": 4},
        "row_fields": ["stack", "config_id", "config_sha256", "page_size", "layer_types"],
        "requests_total_live": requests_total,
        "requests_bound": 1800,
        "configs": configs,
        "grid_verdict": verdict,
        "fan_out": {"measured": False, "note": "B/A fan-out not measured in this unit (no fan-out arm in the battery)"},
        "assumptions": {
            "s3_requests": "S3 was launched one time only; its request budget was reserved for S1/S2 (total bound 1800)",
            "probe_targets": "four targets spaced 64 tokens apart so quotient parity alternates for any constant template offset",
            "s0_baseline": "S0 rows are the existing G3 cell (page_size 1), not re-measured by this unit",
        },
        "n_rows_total": len(rows),
    }
    ANALYSIS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({"configs": {c: {"page_size": configs[c].get("page_size"),
                                      "n_rows": configs[c].get("n_rows"),
                                      "requests": configs[c].get("requests_live"),
                                      "gcd": configs[c]["grid"].get("gcd_cached"),
                                      "cell_status": configs[c].get("cell_status")}
                                 for c in configs},
                      "requests_total_live": requests_total,
                      "grid_verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
