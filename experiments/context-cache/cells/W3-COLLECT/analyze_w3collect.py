"""W3-COLLECT analysis -- offline, 0 requests, recomputable from rows.jsonl alone."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = HERE / "rows.jsonl"
OUT = HERE / "analysis.json"


def load():
    return [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line.strip()]


def hit_profile(rows):
    p = sum(r["prompt_tokens"] for r in rows)
    c = sum(r["cached_tokens"] for r in rows)
    return {"rows": len(rows), "prompt_tokens": p, "cached_tokens": c,
            "hit_rate": round(c / p, 6) if p else None,
            "mean_L": round(p / len(rows), 2) if rows else None,
            "uncached_per_turn": round((p - c) / len(rows), 2) if rows else None}


def main() -> int:
    rows = load()
    battery = [r for r in rows if r["phase"] == "battery"]
    grid = [r for r in rows if r["phase"] == "grid"]
    gate = [r for r in rows if r["phase"] == "gate"]
    per_arm = defaultdict(list)
    for r in battery:
        per_arm[r["arm"]].append(r)
    arms = {}
    for arm in "RACH":
        rs = sorted(per_arm[arm], key=lambda r: r["turn"])
        prof = hit_profile(rs)
        warm = [r for r in rs if r["turn"] >= 5]
        prof["uncached_per_turn_warm"] = round(
            sum(r["prompt_tokens"] - r["cached_tokens"] for r in warm) / len(warm), 2)
        prof["turns_with_hit"] = sum(1 for r in rs if r["cached_tokens"] > 0)
        prof["first_turn_cached"] = rs[0]["cached_tokens"]
        prof["max_L"] = max(r["prompt_tokens"] for r in rs)
        arms[arm] = prof
    overall = hit_profile(battery)

    hot = [r["cached_tokens"] for r in battery if r["cached_tokens"] > 0]
    g = 0
    for v in hot:
        g = math.gcd(g, v)
    deltas = [r["prompt_tokens"] - r["cached_tokens"] for r in battery]
    from1 = [r["prompt_tokens"] - r["cached_tokens"] for r in battery if r["turn"] > 1]

    grid_rows = []
    for r in sorted(grid, key=lambda r: (r["target_L"], r["rep"])):
        grid_rows.append({"target_L": r["target_L"], "L": r["prompt_tokens"],
                          "cached": r["cached_tokens"], "rep": r["rep"]})
    grid_hot = [g for g in grid_rows if g["rep"] >= 1]
    probes = [g for g in grid_hot if g["target_L"] in (1100, 1164, 1228, 1292)]

    summary = {
        "unit": "W3-COLLECT",
        "rows_sha256": hashlib.sha256(ROWS.read_bytes()).hexdigest(),
        "cell": {"endpoint": "http://192.168.2.168:8017", "served_model": "qwen3.5-9b",
                 "stack": "sglang", "context_length": 32768, "config_id": "P2"},
        "request_budget": {"rows_total": len(rows), "gate": len(gate), "grid": len(grid),
                           "battery": len(battery), "cap": 400},
        "integrity": {
            "non_200": sum(1 for r in rows if r["status"] != 200),
            "usage_raw_missing": sum(1 for r in rows if r.get("usage_raw") is None),
            "usage_source_counts": dict(Counter(r["usage_source"] for r in rows)),
            "duplicate_arm_turn": sum(1 for v in Counter((r["arm"], r["turn"]) for r in battery).values() if v > 1),
            "context_lengths": sorted({r["context_length"] for r in rows}),
            "prefix_sha256_distinct": len({r["prefix_sha256"] for r in battery}),
        },
        "gate": {
            "tokenize_count": gate[1]["usage_raw"]["prompt_tokens"] - 2 if len(gate) > 1 else None,
            "rep0_usage": gate[0]["usage_raw"] if gate else None,
            "rep1_usage": gate[1]["usage_raw"] if len(gate) > 1 else None,
            "cached_tokens_key_present": bool(
                isinstance(gate[1]["usage_raw"].get("prompt_tokens_details"), dict)
                and "cached_tokens" in gate[1]["usage_raw"]["prompt_tokens_details"]) if len(gate) > 1 else False,
        },
        "battery": {
            "band": "32k", "budget_tokens": 32768, "servable_turns": 71, "arms": list("RACH"),
            "rows": len(battery), "overall": overall, "per_arm": arms,
            "max_depth_reached": max(r["prompt_tokens"] for r in battery),
            "hot_gcd": g, "hot_n": len(hot),
            "hot_odd_multiples_of_64": sum(1 for v in hot if (v // 64) % 2 == 1),
            "hot_pct_multiple_of_128": round(100 * sum(1 for v in hot if v % 128 == 0) / len(hot), 2)
            if hot else None,
            "hot_all_multiples_of_64": sum(1 for v in hot if v % 64) == 0,
            "median_delta_all": statistics.median(deltas),
            "median_delta_turn_ge2": statistics.median(from1),
        },
        "grid": {
            "targets": sorted({r["target_L"] for r in grid}),
            "rows": grid_rows,
            "law_L_minus_L_mod_64_holds": all(
                r["cached"] == r["L"] - (r["L"] % 64) for r in grid_hot),
            "cold_all_zero": all(r["cached"] == 0 for r in grid_rows if r["rep"] == 0),
        },
        "probe": {
            "targets": probes,
            "matches_64_law": sum(1 for p in probes if p["cached"] == p["L"] - (p["L"] % 64)),
            "matches_128_law": sum(1 for p in probes if p["cached"] == p["L"] - (p["L"] % 128)),
            "discriminating": sum(1 for p in probes if p["L"] % 64 != p["L"] % 128),
        },
    }
    OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("integrity", "gate", "probe")}, indent=1))
    print("overall", json.dumps(overall))
    for a in "RACH":
        print(a, json.dumps(arms[a]))
    print("hot gcd", g, "odd64", summary["battery"]["hot_odd_multiples_of_64"], "/", len(hot),
          "pct128", summary["battery"]["hot_pct_multiple_of_128"],
          "median_delta", summary["battery"]["median_delta_all"])
    print("grid law holds:", summary["grid"]["law_L_minus_L_mod_64_holds"],
          "cold zero:", summary["grid"]["cold_all_zero"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
