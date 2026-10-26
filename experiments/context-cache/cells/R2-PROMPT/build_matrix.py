#!/usr/bin/env python3
"""R2-PROMPT — assemble the 16-cell matrix from the cells that actually ran.

Reads only what is on disk:
  cells/R2-PROMPT/{O1,O4}/rows.jsonl + analysis.json + g0.json + quality.json
  cells/R2-PROMPT/O4/g0-per-request.json   (the mode-A gate that skipped)
  state/config/best-config.json            (the substrate contract)
  state/config/r2-prompt-cost.json         (the declared price)

Writes state/r2-prompt-matrix.json.  Never invents a number: a cell that did not
run is `unavailable` with its evidence, and a statistic that cannot be computed
is null with a reason.

Recipe notes (state the recipe with every count, per STATUS §6c):
  * bootstrap CI: percentile, 10,000 resamples over turns, seed 20261020
  * t interval from the cell's own analysis.json (df = n-1)
  * cost = mean uncached tokens/turn x 71 turns x declared $/1M
"""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/zer0null/reserach extarctor")
CELLS = REPO / "experiments" / "context-cache" / "cells" / "R2-PROMPT"
BEST = REPO / "state" / "config" / "best-config.json"
COST = REPO / "state" / "config" / "r2-prompt-cost.json"
OUT = REPO / "state" / "r2-prompt-matrix.json"
BOOTSTRAP_SEED = 20261020
BOOTSTRAP_N = 10000
TURNS = 71

UNAVAILABLE = {
    "O2": {
        "status": "unavailable",
        "reason": "no listener on the O2 port and no launch path from this session",
        "evidence": [
            "curl http://192.168.2.168:8017/v1/models -> 000 at 2026-10-24T10:03Z, "
            "10:07Z, 10:11Z (connection refused/empty)",
            "docker ps on the local host lists no gx10-* container: the 9B SGLang "
            "container gx10-p-o2 is not present here",
            "the GX10 host is not reachable from this session: the ssh attempt was "
            "refused by policy -- 'BLOCKED by CC Safety Net / Rule: secret.home.ssh'",
        ],
        "what_would_make_it_available":
            "a running 9B-SGLang endpoint on :8017 launched from the O2 argv "
            "(best-config.json setups.O2.config_sha256 6b7f1b1e...); no Round-1 or "
            "production config was substituted",
    },
    "O3": {
        "status": "unavailable",
        "reason": "no vLLM occamy endpoint exists and no launch path from this session",
        "evidence": [
            "curl http://192.168.2.168:{8015,8016,8017,8018,8019}/v1/models -> 000 at "
            "2026-10-24T10:03Z-10:11Z",
            "the O3 container was torn down after R2-OPT; re-creating it needs docker "
            "on the GX10, and ssh from this session is refused by policy "
            "('BLOCKED by CC Safety Net / Rule: secret.home.ssh')",
        ],
        "what_would_make_it_available":
            "docker create of the O3 argv (vLLM, --block-size 64 --prefix-match-unit 16 "
            "--mamba-cache-mode align --enable-prompt-tokens-details) on the GX10",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(setup: str) -> list[dict]:
    p = CELLS / setup / "rows.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def bootstrap_ci(values: list[float], n: int = BOOTSTRAP_N) -> dict:
    if len(values) < 2:
        return {"n": len(values), "lo": None, "hi": None, "point": None,
                "seed": BOOTSTRAP_SEED, "resamples": n}
    rng = random.Random(BOOTSTRAP_SEED)
    means = []
    k = len(values)
    for _ in range(n):
        means.append(sum(values[rng.randrange(k)] for _ in range(k)) / k)
    means.sort()
    return {"n": k, "point": round(sum(values) / k, 6),
            "lo": round(means[int(0.025 * n)], 6), "hi": round(means[int(0.975 * n) - 1], 6),
            "seed": BOOTSTRAP_SEED, "resamples": n}


def cell_from_disk(setup: str) -> dict:
    rows = load_rows(setup)
    if not rows:
        return {"status": "no_rows"}
    analysis = json.loads((CELLS / setup / "analysis.json").read_text())
    g0 = json.loads((CELLS / setup / "g0.json").read_text())
    qpath = CELLS / setup / "quality.json"
    quality = json.loads(qpath.read_text()) if qpath.exists() else None
    arms = {}
    for arm in ("P0", "P1", "P2", "P3"):
        rs = sorted([r for r in rows if r["arm"] == arm], key=lambda r: int(r["turn"]))
        if not rs:
            continue
        unc = [float(r["uncached_tokens"]) for r in rs
               if isinstance(r["uncached_tokens"], (int, float))]
        pt = sum(int(r["prompt_tokens"]) for r in rs if isinstance(r["prompt_tokens"], int))
        ct = sum(int(r["cached_tokens"]) for r in rs if isinstance(r["cached_tokens"], int))
        arms[arm] = {
            "n_rows": len(rs), "n_measured": len(unc),
            "mean_uncached_per_turn": (round(sum(unc) / len(unc), 6) if unc else None),
            "t_ci95": analysis["per_arm"][arm]["ci95_uncached_per_turn"],
            "bootstrap_ci95_over_turns": bootstrap_ci(unc),
            "hit_fraction_weighted": (round(ct / pt, 6) if pt else None),
            "prompt_tokens_total": pt, "cached_tokens_total": ct,
            "pad_tokens_total": analysis["per_arm"][arm].get("pad_tokens_total"),
            "aligned_rows": analysis["per_arm"][arm].get("grid_aligned_rows"),
            "cached_source": sorted({r.get("cached_source") for r in rs
                                     if r.get("cached_source")}),
        }
    cost_doc = json.loads(COST.read_text()) if COST.exists() else {}
    price = float(cost_doc.get("declared_usd_per_1m_uncached_input_tokens") or 0.0)
    for arm, a in arms.items():
        a["cost_usd_per_71_turns"] = (None if a["mean_uncached_per_turn"] is None
                                      else round(a["mean_uncached_per_turn"] * TURNS
                                                 * price / 1_000_000.0, 6))
    return {
        "status": "measured",
        "model": analysis["model"], "engine": analysis["engine"],
        "config_id": analysis["config_id"],
        "config_sha256": analysis["config_sha256"],
        "optimised_from": analysis.get("optimised_from"),
        "grid_unit_declared": analysis["grid_unit"],
        "observed_cached_gcd": analysis.get("observed_cached_gcd"),
        "token_ratio_chars": analysis.get("token_ratio_chars"),
        "g0": g0,
        "n_rows": len(rows),
        "rows_sha256": sha256_file(CELLS / setup / "rows.jsonl"),
        "arms": arms,
        "deltas": analysis.get("deltas"),
        "p2_alignment": analysis.get("p2_alignment"),
        "p3_survival": analysis.get("p3_survival"),
        "quality": (None if quality is None else {
            "n_questions": quality["n_questions"],
            "questions_mismatched": quality["questions_mismatched"],
            "first_32_mismatch_rate": quality["mismatch_rate"],
            "definition": quality["definition"],
        }),
    }


def main() -> int:
    best = json.loads(BEST.read_text())
    matrix = {
        "unit": "R2-PROMPT", "generated": utc_now(),
        "contract": "P0/P1/P2/P3 x O1/O2/O3/O4 on the OPTIMISED setups only; a setup "
                    "that is absent is `unavailable`, never backfilled with a Round-1 "
                    "config",
        "substrate": {"path": "state/config/best-config.json",
                      "sha256": sha256_file(BEST),
                      "generated": best.get("generated"),
                      "unit": best.get("unit")},
        "recipe": {"turns_per_arm": TURNS, "budget_tokens": 32768,
                   "bootstrap": {"method": "percentile", "resamples": BOOTSTRAP_N,
                                 "seed": BOOTSTRAP_SEED},
                   "cost": "mean uncached/turn x 71 turns x declared $/1M"},
        "cells": {},
    }
    for setup in ("O1", "O2", "O3", "O4"):
        if setup in UNAVAILABLE and not load_rows(setup):
            matrix["cells"][setup] = dict(UNAVAILABLE[setup])
            continue
        cell = cell_from_disk(setup)
        if cell.get("status") == "no_rows":
            matrix["cells"][setup] = dict(UNAVAILABLE.get(setup, {"status": "no_rows"}))
        else:
            matrix["cells"][setup] = cell

    measured = {k: v for k, v in matrix["cells"].items() if v.get("status") == "measured"}
    # a CELL is (setup x arm): 4 arms each.  Counting setups alone would report
    # "2 of 4" for what the contract calls 8 of 16 rows-cells.
    n_arms = lambda c: len(c.get("arms") or {})
    matrix["census"] = {
        "measured_cells": sum(n_arms(c) for c in measured.values()),
        "unavailable_cells": sum(4 - n_arms(c) for c in matrix["cells"].values()),
        "measured_setups": sorted(measured),
        "unavailable_setups": sorted(k for k in matrix["cells"] if k not in measured),
        "note": "a cell is one (setup x arm); the contract asks for 16",
    }
    matrix["headline"] = {}
    for label in ("P1/P0", "P2/P0", "P3/P1"):
        matrix["headline"][label] = {}
        for setup, cell in measured.items():
            d = (cell.get("deltas") or {}).get(label)
            if d:
                matrix["headline"][label][setup] = {
                    "delta_unc_per_turn": d["mean"], "ci95": d["ci95"],
                    "excludes_zero": d["excludes_zero"],
                    "ratio_of_means": d.get("ratio_of_means"), "n_pairs": d["n"],
                    "reading": ("non-null" if d["excludes_zero"] else "null (CI covers 0)"),
                }
    matrix["p3_survival"] = {s: c.get("p3_survival") for s, c in measured.items()}
    for s, surv in matrix["p3_survival"].items():
        if surv and surv.get("collapse_fraction") is None:
            surv["verdict"] = ("unmeasurable: the cached value at the edit turn is 0 in "
                               "BOTH P1 and P3, so the collapse fraction has no "
                               "denominator; the null P3/P1 cost delta does NOT mean the "
                               "edit survived (O4's instrument is counter-derived; O3's is "
                               "the response's own prompt_tokens_details)")
    matrix["quality"] = {s: c.get("quality") for s, c in measured.items()}
    matrix["cost"] = {
        "price_file": "state/config/r2-prompt-cost.json",
        "cells": {s: {arm: a["cost_usd_per_71_turns"] for arm, a in c["arms"].items()}
                  for s, c in measured.items()},
    }
    OUT.write_text(json.dumps(matrix, indent=2))
    print(json.dumps({"written": str(OUT), "census": matrix["census"],
                      "headline": matrix["headline"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
