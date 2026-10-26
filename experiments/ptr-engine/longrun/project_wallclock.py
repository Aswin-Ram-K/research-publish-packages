#!/usr/bin/env python3
"""Project the LONGRUN wall clock from measured per-turn latency rows.

Read-only over `experiments/ptr-engine/measure/`. Sends no requests.

Why this exists: the long-run batch was approved against a request cap, not a
wall clock. Measured latency turns out to be driven by completion length
(reasoning), not by turn depth, so the cost of a grid is roughly
    hours = total_requests x per-turn latency / 3600
with a long right tail from turns that run to `max_tokens`.

Usage
    python3 project_wallclock.py                       # all three row files
    python3 project_wallclock.py --rows FILE [--rows FILE]
    python3 project_wallclock.py --N 48 --reps 1        # projection inputs
    python3 project_wallclock.py --json                 # machine-readable
    python3 project_wallclock.py --grid 500 252 204     # request grids

Contract
* Per (file, max_tokens) group, per arm: n_rows, n_latency_usable,
  mean_latency_s, p50_latency_s, p95_latency_s, max_latency_s,
  mean_completion_tokens, hours_median, hours_p95 for `--N` turns at `--reps`.
* Files with different `max_tokens` are NEVER pooled; each group is printed and
  labelled. A file whose rows all lack `max_tokens` is labelled `max_tokens=None`.
* Refuses (exit 2) if `latency_s` / `latency_ms` is absent from more than 50%
  of a file's rows, or if a file has no latency column at all.
* Prints the projection formula it used.
"""

import argparse
import collections
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
DEFAULT_ROWS = [
    os.path.join(ENGINE, "measure", "rows-longrun-2026-10-26.jsonl"),
    os.path.join(ENGINE, "measure", "rows-longrun-2026-10-26-fix.jsonl"),
    os.path.join(ENGINE, "measure", "rows-longrun-2026-10-26-policy.jsonl"),
]
DEGENERATE_S = 120.0
FORMULA = ("hours_median = n_turns * reps * p50_latency_s / 3600 ; "
           "hours_p95 = n_turns * reps * p95_latency_s / 3600 ; "
           "grid_hours = sum_over_arms(turns_per_arm * arm_p50_or_p95 / 3600)")


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def latency_of(row):
    """Per-turn wall seconds, or None. `latency_s` preferred, `latency_ms` fallback."""
    v = row.get("latency_s")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        return float(v)
    v = row.get("latency_ms")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        return float(v) / 1000.0
    return None


def percentile(xs, p):
    """Linear-interpolated percentile (numpy 'linear'), stdlib only."""
    if not xs:
        return None
    xs = sorted(xs)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p / 100.0
    lo = int(math.floor(k))
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def arm_stats(rows, n_turns, reps):
    lat = [x for x in (latency_of(r) for r in rows) if x is not None]
    comp = [r.get("completion_tokens") for r in rows
            if isinstance(r.get("completion_tokens"), (int, float))]
    turns = n_turns * reps
    return {
        "n_rows": len(rows),
        "n_latency_usable": len(lat),
        "mean_latency_s": round(statistics.mean(lat), 3) if lat else None,
        "p50_latency_s": round(percentile(lat, 50), 3) if lat else None,
        "p95_latency_s": round(percentile(lat, 95), 3) if lat else None,
        "max_latency_s": round(max(lat), 3) if lat else None,
        "mean_completion_tokens": round(statistics.mean(comp), 1) if comp else None,
        "hours_median": round(turns * percentile(lat, 50) / 3600.0, 2) if lat else None,
        "hours_p95": round(turns * percentile(lat, 95) / 3600.0, 2) if lat else None,
    }


def census(rows):
    degen = []
    for r in rows:
        s = latency_of(r)
        if s is not None and s > DEGENERATE_S:
            degen.append({
                "arm": r.get("arm"), "task_id": r.get("task_id"),
                "turn": r.get("turn"), "latency_s": round(s, 1),
                "completion_tokens": r.get("completion_tokens"),
                "finish_reason": r.get("finish_reason"),
                "truncated": r.get("truncated"),
            })
    return {
        "n_rows": len(rows),
        "n_truncated": sum(1 for r in rows if r.get("truncated") is True),
        "n_finish_length": sum(1 for r in rows if r.get("finish_reason") == "length"),
        "n_completion_16384": sum(1 for r in rows if r.get("completion_tokens") == 16384),
        "n_completion_128": sum(1 for r in rows if r.get("completion_tokens") == 128),
        "n_over_120s": len(degen),
        "over_120s": degen,
    }


def depth_check(rows):
    """Is latency a function of turn depth? Pearson r(turn, latency) per arm."""
    out = {}
    by_arm = collections.defaultdict(list)
    for r in rows:
        s = latency_of(r)
        if s is not None and isinstance(r.get("turn"), int):
            by_arm[r.get("arm")].append((r["turn"], s))
    for arm, pairs in sorted(by_arm.items(), key=lambda kv: str(kv[0])):
        if len(pairs) < 6:
            out[str(arm)] = {"n": len(pairs), "r_turn_latency": None}
            continue
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
        third = max(1, len(pairs) // 3)
        out[str(arm)] = {
            "n": len(pairs),
            "r_turn_latency": round(num / den, 3) if den else None,
            "first_third_mean_s": round(statistics.mean(ys[:third]), 2),
            "last_third_mean_s": round(statistics.mean(ys[-third:]), 2),
        }
    return out


def fixtures():
    out = {}
    rdir = os.path.join(HERE, "runtime")
    if not os.path.isdir(rdir):
        return out
    for name in sorted(os.listdir(rdir)):
        if name.startswith("LR-") and name.endswith(".json"):
            try:
                d = json.load(open(os.path.join(rdir, name), encoding="utf-8"))
            except (OSError, ValueError):
                continue
            out[name] = {"N": d.get("N"), "wall_tokens": d.get("wall_tokens")}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Project LONGRUN wall clock from measured rows.")
    ap.add_argument("--rows", action="append", default=None,
                    help="row JSONL path (repeatable); default: the three longrun files")
    ap.add_argument("--N", type=int, default=60,
                    help="turns per task for the projection (frozen prereg N=60; fixtures use N=48)")
    ap.add_argument("--reps", type=int, default=1, help="reps (default 1)")
    ap.add_argument("--grid", type=int, nargs="*", default=None,
                    help="request grids to price, e.g. --grid 500 252 204")
    ap.add_argument("--price-max-tokens", type=int, default=None,
                    help="price the grid from the group with this max_tokens "
                         "(the only legal basis: groups are never merged)")
    ap.add_argument("--turns-per-arm", type=int, default=None,
                    help="override N*reps with the measured total turns per arm "
                         "(e.g. 340 = sum of fixture N over LR-01..06)")
    ap.add_argument("--extra-requests", type=int, default=0,
                    help="requests beyond arms*N*reps (digests, controls, repairs), "
                         "priced at the group's pooled percentile")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    paths = args.rows or DEFAULT_ROWS
    report = {"formula": FORMULA, "N_turns": args.N, "reps": args.reps,
              "degenerate_threshold_s": DEGENERATE_S,
              "fixtures": fixtures(), "files": [], "refusals": []}

    for path in paths:
        if not os.path.exists(path):
            report["refusals"].append({"file": path, "reason": "missing file"})
            continue
        rows = load(path)
        if not rows:
            report["refusals"].append({"file": path, "reason": "empty file"})
            continue
        has_col = any("latency_s" in r or "latency_ms" in r for r in rows)
        usable = sum(1 for r in rows if latency_of(r) is not None)
        if not has_col:
            report["refusals"].append(
                {"file": path, "reason": "no latency_s / latency_ms column",
                 "n_rows": len(rows)})
            continue
        if usable <= 0.5 * len(rows):
            report["refusals"].append(
                {"file": path, "reason": "latency absent from >50% of rows",
                 "n_rows": len(rows), "n_latency_usable": usable})
            continue

        groups = collections.defaultdict(list)
        for r in rows:
            groups[r.get("max_tokens")].append(r)

        entry = {"file": path, "n_rows": len(rows), "n_latency_usable": usable,
                 "groups": [], "census": census(rows), "depth": depth_check(rows)}
        for mt, grs in sorted(groups.items(), key=lambda kv: str(kv[0])):
            by_arm = collections.defaultdict(list)
            for r in grs:
                by_arm[r.get("arm")].append(r)
            arms = {str(a): arm_stats(v, args.N, args.reps) for a, v in sorted(
                by_arm.items(), key=lambda kv: str(kv[0]))}
            entry["groups"].append({
                "max_tokens": mt,
                "n_rows": len(grs),
                "arms": arms,
                "pooled": arm_stats(grs, args.N, args.reps),
                "census": census(grs),
                "depth": depth_check(grs),
            })
        report["files"].append(entry)

    if args.price_max_tokens is not None:
        # Candidates: every group at this max_tokens. Prefer the most arms, then the
        # most rows -- a 3-arm group must not silently price a 4-arm grid.
        candidates = []
        for entry in report["files"]:
            for g in entry["groups"]:
                if g["max_tokens"] == args.price_max_tokens:
                    candidates.append((entry["file"], g))
        # The arm roster is the union over every group in every file.
        roster = []
        for entry in report["files"]:
            for g in entry["groups"]:
                for arm in g["arms"]:
                    if arm not in roster:
                        roster.append(arm)
        if not candidates:
            report["refusals"].append({"file": "grid", "reason":
                "no group with max_tokens=%s; refusing to price a grid from another group"
                % args.price_max_tokens})
        else:
            candidates.sort(key=lambda fg: (len(fg[1]["arms"]), fg[1]["n_rows"]), reverse=True)
            src_file, g = candidates[0]
            pooled = g["pooled"]
            n_arm_turns = args.turns_per_arm or (args.N * args.reps)
            total_req = n_arm_turns * len(roster) + args.extra_requests
            med = p95 = 0.0
            fallback = []
            for arm in roster:
                s = g["arms"].get(arm)
                if s is None or s["p50_latency_s"] is None:
                    fallback.append(arm)
                    s = pooled
                med += n_arm_turns * s["p50_latency_s"] / 3600.0
                p95 += n_arm_turns * s["p95_latency_s"] / 3600.0
            med += args.extra_requests * pooled["p50_latency_s"] / 3600.0
            p95 += args.extra_requests * pooled["p95_latency_s"] / 3600.0
            report["grid"] = {
                "priced_from": src_file,
                "max_tokens": args.price_max_tokens,
                "arms": len(roster),
                "arm_roster": roster,
                "turns_per_arm": n_arm_turns,
                "turns_override": bool(args.turns_per_arm),
                "N": args.N,
                "reps": args.reps,
                "extra_requests": args.extra_requests,
                "total_requests": total_req,
                "hours_median": round(med, 2),
                "hours_p95": round(p95, 2),
                "arms_priced_on_pooled_fallback": fallback,
                "n_rows_in_group": g["n_rows"],
            }

    if args.grid:
        report["grids"] = [{"total_requests": req} for req in args.grid]

    if args.json:
        json.dump(report, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print("FORMULA: " + FORMULA)
        print("N_turns=%d reps=%d  degenerate threshold=%.0fs" % (args.N, args.reps, DEGENERATE_S))
        fx = report["fixtures"]
        if fx:
            print("FIXTURES: " + ", ".join("%s N=%s wall_tokens=%s" % (k, v["N"], v["wall_tokens"])
                                           for k, v in fx.items()))
        for entry in report["files"]:
            print("\n== %s  n_rows=%d  latency_usable=%d" %
                  (entry["file"], entry["n_rows"], entry["n_latency_usable"]))
            print("   EXCLUSION: groups with different max_tokens are reported "
                  "separately and never pooled.")
            for g in entry["groups"]:
                print("   -- max_tokens=%s  n_rows=%d  (EXCLUDED from any other group)" %
                      (g["max_tokens"], g["n_rows"]))
                hdr = ("      %-20s %5s %5s %8s %8s %8s %8s %8s %8s %8s" %
                       ("arm", "n_rows", "n_use", "mean_s", "p50_s", "p95_s", "max_s",
                        "mean_comp", "h_med", "h_p95"))
                print(hdr)
                for arm, s in list(g["arms"].items()) + [("POOLED(group)", g["pooled"])]:
                    print("      %-20s %5d %5d %8.2f %8.2f %8.2f %8.2f %8.1f %8.2f %8.2f" % (
                        arm, s["n_rows"], s["n_latency_usable"],
                        s["mean_latency_s"] or 0, s["p50_latency_s"] or 0,
                        s["p95_latency_s"] or 0, s["max_latency_s"] or 0,
                        s["mean_completion_tokens"] or 0,
                        s["hours_median"] or 0, s["hours_p95"] or 0))
                c = g["census"]
                print("      census: n=%d truncated=%d finish=length=%d completion==16384=%d "
                      "completion==128=%d over_120s=%d" % (
                          c["n_rows"], c["n_truncated"], c["n_finish_length"],
                          c["n_completion_16384"], c["n_completion_128"], c["n_over_120s"]))
                for d in c["over_120s"]:
                    print("        >120s: %s turn=%s %s %.1fs comp=%s finish=%s truncated=%s" % (
                        d["arm"], d["turn"], d["task_id"], d["latency_s"],
                        d["completion_tokens"], d["finish_reason"], d["truncated"]))
                for arm, s in g["depth"].items():
                    if s.get("r_turn_latency") is not None:
                        print("      depth %-20s n=%d r(turn,lat)=%+.3f first_third=%.2fs "
                              "last_third=%.2fs" % (arm, s["n"], s["r_turn_latency"],
                                                    s["first_third_mean_s"], s["last_third_mean_s"]))
        for r in report["refusals"]:
            print("\nREFUSED %s: %s (n_rows=%s usable=%s)" %
                  (r["file"], r["reason"], r.get("n_rows"), r.get("n_latency_usable")))
        g = report.get("grid")
        if g:
            print("\nGRID PRICE: %d requests = %d arms x %d turns%s + %d extra"
                  % (g["total_requests"], g["arms"], g["turns_per_arm"],
                     " (turns-per-arm override)" if g.get("turns_override") else
                     " (N=%d x reps=%d)" % (g.get("N"), g["reps"]),
                     g["extra_requests"]))
            print("   priced from %s (max_tokens=%s, n_rows=%d)" %
                  (os.path.basename(g["priced_from"]), g["max_tokens"], g["n_rows_in_group"]))
            print("   hours_median=%.2f  hours_p95=%.2f" % (g["hours_median"], g["hours_p95"]))
            if g["arms_priced_on_pooled_fallback"]:
                print("   NOTE: arms with no row in this group priced on the group "
                      "pooled latency: %s" % ", ".join(g["arms_priced_on_pooled_fallback"]))
        if report.get("grids"):
            print("\nGRIDS (pass --price-max-tokens to price one): %s" %
                  ", ".join(str(x["total_requests"]) for x in report["grids"]))

    if report["refusals"]:
        print("\nREFUSE: %d file(s) cannot support a projection: %s" % (
            len(report["refusals"]), ", ".join(os.path.basename(r["file"]) for r in report["refusals"])),
            file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
