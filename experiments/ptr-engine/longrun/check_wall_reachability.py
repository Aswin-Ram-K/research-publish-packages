#!/usr/bin/env python3
"""Deterministic checker: for a fixture, prove turns_to_wall < fixture_turn_count.

Usage:
  python3 check_wall_reachability.py <fixture.json> [<fixture.json> ...]
  python3 check_wall_reachability.py --glob 'tasks-v6/*.v9.json'
"""
import json, sys, glob, os

def turn_count(fx):
    if isinstance(fx.get("N"), int):
        return fx["N"]
    lr = fx.get("long_run") or {}
    if isinstance(lr.get("turns"), int):
        return lr["turns"]
    turns = fx.get("turns")
    if isinstance(turns, list):
        return len(turns)
    raise ValueError("no turn count")

def check(path):
    fx = json.load(open(path))
    n = turn_count(fx)
    basis = fx["wall_tokens_basis"]
    slopes = basis["measured_growth_tok_per_turn_live_base_mean"]
    p1s = basis["prompt_tokens_turn1_live_base"]
    wba = fx["wall_tokens_by_arm"]
    rows = []
    all_ok = True
    for arm in sorted(wba):
        wall = wba[arm]
        slope = slopes[arm]
        p1 = p1s[arm]
        t = 1
        while p1 + slope * (t - 1) <= wall and t < n + 1000:
            t += 1
        turns_to_wall = t
        ok = turns_to_wall < n
        if not ok:
            all_ok = False
        rows.append((arm, wall, slope, p1, turns_to_wall, ok))
    print(f"{os.path.basename(path)}: generation={fx.get('generation')} N={n} wall_reachable_in_horizon={fx.get('wall_reachable_in_horizon')}")
    for arm, wall, slope, p1, ttw, ok in rows:
        print(f"  {arm}: wall={wall} slope={slope} P1={p1} turns_to_wall={ttw} reachable={ok}")
    return all_ok

def main():
    args = sys.argv[1:]
    paths = []
    if not args:
        print("usage: check_wall_reachability.py <file...> | --glob <pattern>", file=sys.stderr)
        sys.exit(2)
    i = 0
    while i < len(args):
        if args[i] == "--glob":
            paths.extend(sorted(glob.glob(args[i+1])))
            i += 2
            continue
        paths.append(args[i])
        i += 1
    # expand dirs/globs
    expanded = []
    for p in paths:
        if "*" in p or "?" in p:
            expanded.extend(sorted(glob.glob(p)))
        else:
            expanded.append(p)
    overall = True
    for p in expanded:
        ok = check(p)
        if not ok:
            overall = False
    print("ALL_REACHABLE=" + str(overall).lower())
    sys.exit(0 if overall else 1)

if __name__ == "__main__":
    main()
