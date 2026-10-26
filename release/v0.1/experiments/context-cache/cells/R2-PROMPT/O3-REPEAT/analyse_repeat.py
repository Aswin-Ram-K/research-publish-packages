#!/usr/bin/env python3
"""O3-P2-REPEAT — re-derive the repeat's statistics from its own rows.

Reads   experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/rows.jsonl
Writes  experiments/context-cache/cells/R2-PROMPT/O3-REPEAT/replication.json

Bootstrap recipe is the matrix's own: percentile, 10000 resamples, seed 20261020.
The t-interval comes from the frozen harness's own `mean_ci`, so the repeat is
compared to R2-PROMPT on one estimator, not two.
"""
import importlib.util
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
FROZEN = HERE.parent / "prompt_r2prompt_cell.py"
MATRIX = REPO / "state" / "r2-prompt-matrix.json"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(FROZEN, "r2prompt_frozen")
SALT = "o3-repeat-20261024T11:05Z-a1"
BOOT = {"method": "percentile", "resamples": 10000, "seed": 20261020}


def boot_ci(values, seed, resamples=10000):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(resamples):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return {"n": n, "point": round(sum(values) / n, 6),
            "lo": round(means[int(0.025 * resamples)], 6),
            "hi": round(means[int(0.975 * resamples) - 1], 6),
            "seed": seed, "resamples": resamples}


def main():
    rows = [json.loads(l) for l in (HERE / "rows.jsonl").read_text().splitlines() if l.strip()]
    arms = sorted({r["arm"] for r in rows})
    per, unc, cached = {}, {}, {}
    for a in arms:
        rs = sorted([r for r in rows if r["arm"] == a], key=lambda r: int(r["turn"]))
        u = [float(r["uncached_tokens"]) for r in rs if isinstance(r["uncached_tokens"], (int, float))]
        unc[a] = {int(r["turn"]): float(r["uncached_tokens"]) for r in rs
                  if isinstance(r["uncached_tokens"], (int, float))}
        cached[a] = {int(r["turn"]): int(r["cached_tokens"]) for r in rs
                     if isinstance(r["cached_tokens"], int)}
        ci = H.mean_ci(u)
        pt = sum(int(r["prompt_tokens"]) for r in rs if isinstance(r["prompt_tokens"], int))
        ct = sum(int(r["cached_tokens"]) for r in rs if isinstance(r["cached_tokens"], int))
        per[a] = {
            "n_rows": len(rs),
            "mean_uncached_per_turn": ci["mean"],
            "t_ci95": ci["ci95"],
            "bootstrap_ci95_over_turns": boot_ci(u, BOOT["seed"]),
            "hit_fraction_weighted": round(ct / pt, 6) if pt else None,
            "prompt_tokens_total": pt,
            "cached_tokens_total": ct,
            "n_cached_gt_0": sum(1 for r in rs if isinstance(r["cached_tokens"], int)
                                 and r["cached_tokens"] > 0),
            "n_zero_cached": sum(1 for r in rs if r["cached_tokens"] == 0),
            "pad_tokens_total": sum(int(r.get("pad_tokens") or 0) for r in rs),
            "n_pad_aligned_mod16": sum(1 for r in rs if isinstance(r["prompt_tokens"], int)
                                       and r["prompt_tokens"] % 16 == 0),
            "n_pad_aligned_mod48": sum(1 for r in rs if isinstance(r["prompt_tokens"], int)
                                       and r["prompt_tokens"] % 48 == 0),
            "n_pad_aligned_mod2112": sum(1 for r in rs if isinstance(r["prompt_tokens"], int)
                                         and r["prompt_tokens"] % 2112 == 0),
            "pad_corrections_total": sum(int(r.get("pad_corrections") or 0) for r in rs),
            "distinct_prefix_sha256": len({r["prefix_sha256"] for r in rs}),
            "null_cached_rows": sum(1 for r in rs if not isinstance(r["cached_tokens"], int)),
            "non_200_rows": sum(1 for r in rs if r.get("http_status") != 200),
        }

    deltas = {}
    for a, b in (("P1", "P0"), ("P2", "P0"), ("P2", "P1")):
        if a in unc and b in unc:
            d = H.paired_delta(unc[a], unc[b])
            turns = sorted(set(unc[a]) & set(unc[b]))
            diffs = [unc[a][t] - unc[b][t] for t in turns]
            d["bootstrap_ci95_over_turns"] = boot_ci(diffs, BOOT["seed"])
            d["ratio_of_means"] = (round(per[a]["mean_uncached_per_turn"]
                                         / per[b]["mean_uncached_per_turn"], 6)
                                   if per[b]["mean_uncached_per_turn"] else None)
            d["pct_vs_baseline"] = (round(100.0 * (per[a]["mean_uncached_per_turn"]
                                                   - per[b]["mean_uncached_per_turn"])
                                          / per[b]["mean_uncached_per_turn"], 2)
                                    if per[b]["mean_uncached_per_turn"] else None)
            deltas["%s/%s" % (a, b)] = d

    # ---- the alignment-law probe ------------------------------------------ #
    # Every P2 prompt is a multiple of 16 by construction.  Split those rows by
    # whether they are ALSO multiples of 48 / 2112 and compare their cache
    # behaviour: if the win is a coarse-page law, only the 48-multiples should
    # carry it.
    p2 = [r for r in rows if r["arm"] == "P2" and isinstance(r["prompt_tokens"], int)
          and isinstance(r["cached_tokens"], int)]
    def bucket(pred):
        sel = [r for r in p2 if pred(r)]
        if not sel:
            return {"n": 0}
        return {"n": len(sel),
                "mean_cached": round(sum(r["cached_tokens"] for r in sel) / len(sel), 3),
                "n_cached_gt_0": sum(1 for r in sel if r["cached_tokens"] > 0),
                "mean_uncached": round(sum(r["uncached_tokens"] for r in sel) / len(sel), 3)}
    law = {
        "P2_rows_mod48_eq0": bucket(lambda r: r["prompt_tokens"] % 48 == 0),
        "P2_rows_mod48_ne0": bucket(lambda r: r["prompt_tokens"] % 48 != 0),
        "P2_rows_mod2112_eq0": bucket(lambda r: r["prompt_tokens"] % 2112 == 0),
        "P1_rows_mod48_eq0": None,
        "note": "P1 rows are unaligned by construction; the P2 split is the discriminating test",
    }
    p1 = [r for r in rows if r["arm"] == "P1" and isinstance(r["prompt_tokens"], int)
          and isinstance(r["cached_tokens"], int)]
    sel = [r for r in p1 if r["prompt_tokens"] % 48 == 0]
    law["P1_rows_mod48_eq0"] = ({"n": len(sel),
                                 "mean_cached": round(sum(r["cached_tokens"] for r in sel) / len(sel), 3)
                                 if sel else None,
                                 "n_cached_gt_0": sum(1 for r in sel if r["cached_tokens"] > 0)}
                                if sel else {"n": 0})

    # ---- side-by-side with the run being replicated ----------------------- #
    m = json.loads(MATRIX.read_text())["cells"]["O3"]
    orig = {a: {"mean_uncached_per_turn": v["mean_uncached_per_turn"],
                "t_ci95": v["t_ci95"],
                "hit_fraction_weighted": v["hit_fraction_weighted"],
                "pad_tokens_total": v["pad_tokens_total"],
                "n_rows": v["n_rows"]}
            for a, v in m["arms"].items()}
    side = {"original_cell": "experiments/context-cache/cells/R2-PROMPT/O3",
            "original_arms": orig,
            "original_deltas": {k: {kk: v[kk] for kk in ("mean", "ci95", "excludes_zero",
                                                         "ratio_of_means")}
                                for k, v in m["deltas"].items()},
            "repeat_arms": per,
            "repeat_deltas": deltas}

    out = {"unit": "O3-P2-REPEAT", "salt": SALT,
           "grid_used": 16, "grid_declared_in_best_config": m["grid_unit_declared"],
           "bootstrap": BOOT, "n_rows": len(rows), "arms": arms,
           "side_by_side": side, "alignment_law_probe": law}
    (HERE / "replication.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"arms": {a: {"unc": per[a]["mean_uncached_per_turn"],
                                   "t_ci": per[a]["t_ci95"],
                                   "boot_ci": [per[a]["bootstrap_ci95_over_turns"]["lo"],
                                               per[a]["bootstrap_ci95_over_turns"]["hi"]],
                                   "hit": per[a]["hit_fraction_weighted"],
                                   "zero_cached": per[a]["n_zero_cached"],
                                   "pad": per[a]["pad_tokens_total"]}
                              for a in arms},
                      "deltas": {k: {"mean": v["mean"], "t_ci": v["ci95"],
                                     "boot_ci": [v["bootstrap_ci95_over_turns"]["lo"],
                                                 v["bootstrap_ci95_over_turns"]["hi"]],
                                     "pct": v["pct_vs_baseline"],
                                     "ratio": v["ratio_of_means"],
                                     "excludes_zero": v["excludes_zero"]}
                                 for k, v in deltas.items()},
                      "law": law}, indent=1))


if __name__ == "__main__":
    main()
