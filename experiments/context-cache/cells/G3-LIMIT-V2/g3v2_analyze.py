#!/usr/bin/env python3
"""G3-LIMIT-V2 analysis: per-arm mean uncached/turn, compaction-vs-baseline
delta with a 95% CI, and the count of compaction events.

Statistics are deliberately simple and stated in the output:
  * per-arm mean uncached tokens per turn, and the steering-free subset
    (turns with ``trigger_reason == "below_budget"``, i.e. not the turn a
    compaction (or a window drop) fired -- those are the boundary break itself);
  * delta = mean(compacting arm) - mean(matched compaction-free baseline at the
    same budget AND the same renderer), bootstrap percentile CI over turns
    (10,000 resamples, seed fixed) because per-turn uncached counts are
    skewed and not independent of the chain length that produced them.
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = HERE / "rows.jsonl"
EVENTS = HERE / "events.jsonl"
OUT = HERE / "analysis.json"
RUN = HERE / "run.json"
BOOT = 10000
SEED = 20251023

BASELINE_OF = {"append_note": "B", "pointer": "B-ptr"}
COMPACTING = ("S", "S-ptr", "F", "F-ptr", "S-k800", "F-k800")


def load_rows(path=ROWS):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_events(path=EVENTS):
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def dedupe(rows):
    seen = {}
    for r in rows:
        seen[(r["arm"], r["budget"], int(r["turn"]))] = r
    return list(seen.values())


def boot_ci(values, n=BOOT, seed=SEED, alpha=0.05):
    rnd = random.Random(seed)
    means = []
    k = len(values)
    for _ in range(n):
        means.append(sum(values[rnd.randrange(k)] for _ in range(k)) / k)
    means.sort()
    return round(means[int(alpha / 2 * n)], 1), round(means[int((1 - alpha / 2) * n)], 1)


def boot_diff_ci(a, b, n=BOOT, seed=SEED, alpha=0.05):
    rnd = random.Random(seed)
    diffs = []
    for _ in range(n):
        ma = sum(a[rnd.randrange(len(a))] for _ in range(len(a))) / len(a)
        mb = sum(b[rnd.randrange(len(b))] for _ in range(len(b))) / len(b)
        diffs.append(ma - mb)
    diffs.sort()
    return round(diffs[int(alpha / 2 * n)], 1), round(diffs[int((1 - alpha / 2) * n)], 1)


def arm_stats(rows):
    unc = [int(r["uncached_tokens"]) for r in rows if r.get("status") == 200]
    below = [
        int(r["uncached_tokens"])
        for r in rows
        if r.get("status") == 200 and r.get("trigger_reason") == "below_budget"
    ]
    hits = [int(r["uncached_tokens"]) for r in rows if r.get("trigger_reason") not in ("below_budget",)]
    lo, hi = boot_ci(unc) if len(unc) > 2 else (None, None)
    return {
        "n": len(rows),
        "n_ok": len(unc),
        "errors": sum(1 for r in rows if r.get("status") != 200),
        "mean_uncached_per_turn": round(statistics.mean(unc), 1) if unc else None,
        "median_uncached_per_turn": round(statistics.median(unc), 1) if unc else None,
        "boot95_ci_mean_uncached": [lo, hi],
        "n_below_budget_turns": len(below),
        "mean_uncached_below_budget": round(statistics.mean(below), 1) if below else None,
        "n_boundary_turns": len(hits),
        "mean_uncached_boundary_turn": round(statistics.mean(hits), 1) if hits else None,
        "compaction_rows": sum(1 for r in rows if r.get("compacted_this_turn")),
        "compactions_total": (max(int(r["compactions_so_far"]) for r in rows) if rows else 0),
        "mean_prompt_tokens": round(statistics.mean(int(r["prompt_tokens"]) for r in rows), 1) if rows else None,
        "mean_est_chain_tokens": round(statistics.mean(int(r["est_chain_tokens"]) for r in rows), 1) if rows else None,
        "mean_nodes": round(statistics.mean(int(r["nodes"]) for r in rows), 2) if rows else None,
        "mean_chars": round(statistics.mean(int(r["chars"]) for r in rows), 1) if rows else None,
        "final_prompt_tokens": int(rows[-1]["prompt_tokens"]) if rows else None,
        "renderer": rows[-1].get("renderer") if rows else None,
        "policy": rows[-1].get("policy") if rows else None,
        "keep_last": rows[-1].get("keep_last") if rows else None,
    }


def main():
    rows = dedupe(load_rows())
    events = [e for e in dedupe_events(load_events())]
    budgets = sorted({r["budget"] for r in rows}, key=lambda b: int(b.rstrip("k")))
    arms = sorted({r["arm"] for r in rows})

    by = {}
    for r in rows:
        by.setdefault((r["budget"], r["arm"]), []).append(r)

    depths = {}
    gate = {}
    for b in budgets:
        arms_out = {}
        for a in arms:
            rs = sorted(by.get((b, a), []), key=lambda r: int(r["turn"]))
            if rs:
                arms_out[a] = arm_stats(rs)
        depths[b] = arms_out
        gate[b] = {a: arms_out.get(a, {}).get("compaction_rows", 0) for a in arms if a in COMPACTING}

    # compaction-vs-baseline deltas, matched on budget AND renderer
    deltas = {}
    for b in budgets:
        for a in COMPACTING:
            if a not in depths[b]:
                continue
            renderer = depths[b][a]["renderer"]
            base = BASELINE_OF[renderer]
            if base not in depths[b]:
                continue
            adv = [int(r["uncached_tokens"]) for r in by[(b, a)] if r.get("status") == 200]
            bl = [int(r["uncached_tokens"]) for r in by[(b, base)] if r.get("status") == 200]
            # same comparison restricted to non-boundary turns
            adv_b = [int(r["uncached_tokens"]) for r in by[(b, a)]
                     if r.get("status") == 200 and r.get("trigger_reason") == "below_budget"]
            bl_b = [int(r["uncached_tokens"]) for r in by[(b, base)]
                    if r.get("status") == 200 and r.get("trigger_reason") == "below_budget"]
            lo, hi = boot_diff_ci(adv, bl)
            lo_b, hi_b = boot_diff_ci(adv_b, bl_b) if len(adv_b) > 2 and len(bl_b) > 2 else (None, None)
            deltas.setdefault(b, {})[a] = {
                "baseline": base,
                "renderer": renderer,
                "mean_uncached_arm": round(statistics.mean(adv), 1),
                "mean_uncached_baseline": round(statistics.mean(bl), 1),
                "delta_tokens_per_turn": round(statistics.mean(adv) - statistics.mean(bl), 1),
                "delta_pct": round(100 * (statistics.mean(adv) / statistics.mean(bl) - 1), 2),
                "boot95_ci_delta": [lo, hi],
                "excludes_zero": bool(lo > 0 or hi < 0),
                "below_budget_only": {
                    "delta_tokens_per_turn": (
                        round(statistics.mean(adv_b) - statistics.mean(bl_b), 1)
                        if adv_b and bl_b else None
                    ),
                    "boot95_ci_delta": [lo_b, hi_b],
                },
                "n_adv": len(adv),
                "n_base": len(bl),
            }

    # renderer effect: within compaction policy, pointer vs append_note
    render_effect = {}
    for b in budgets:
        for a_naive, a_ptr in (("S", "S-ptr"), ("F", "F-ptr"), ("B", "B-ptr")):
            if a_naive in depths[b] and a_ptr in depths[b]:
                v1 = [int(r["uncached_tokens"]) for r in by[(b, a_naive)] if r.get("status") == 200]
                v2 = [int(r["uncached_tokens"]) for r in by[(b, a_ptr)] if r.get("status") == 200]
                lo, hi = boot_diff_ci(v2, v1)
                render_effect.setdefault(b, {})[f"{a_ptr} - {a_naive}"] = {
                    "delta_tokens_per_turn": round(statistics.mean(v2) - statistics.mean(v1), 1),
                    "boot95_ci_delta": [lo, hi],
                    "excludes_zero": bool(lo > 0 or hi < 0),
                }

    # matched-turn contrast: what compaction costs on turns where nothing fired,
    # measured against the matched baseline on the SAME turn, plus the one-turn
    # break the boundary itself causes vs the baseline's own drop turn.
    matched = {}
    for b in budgets:
        bl = {}
        for base in set(BASELINE_OF.values()):
            for r in by.get((b, base), []):
                bl.setdefault(base, {})[int(r["turn"])] = int(r["uncached_tokens"])
        for a in COMPACTING:
            if a not in depths[b]:
                continue
            base = BASELINE_OF[depths[b][a]["renderer"]]
            pairs = [
                (int(r["uncached_tokens"]), bl[base][int(r["turn"])])
                for r in by[(b, a)]
                if r.get("status") == 200
                and r.get("trigger_reason") == "below_budget"
                and int(r["turn"]) in bl.get(base, {})
            ]
            if len(pairs) < 8:
                continue
            d = [x - y for x, y in pairs]
            lo, hi = boot_ci(d)
            matched.setdefault(b, {})[a] = {
                "baseline": base,
                "n_matched_turns": len(pairs),
                "delta_tokens_per_turn": round(statistics.mean(d), 1),
                "delta_pct_of_baseline": round(100 * statistics.mean(d) / statistics.mean(y for _, y in pairs), 2),
                "boot95_ci_delta": [lo, hi],
                "excludes_zero": bool(lo > 0 or hi < 0),
                "boundary_turn_uncached": depths[b][a]["mean_uncached_boundary_turn"],
                "baseline_drop_turn_uncached": depths[b][base]["mean_uncached_boundary_turn"],
                "compaction_turns": [int(r["turn"]) for r in by[(b, a)] if r.get("compacted_this_turn")],
            }
    gate_pass = all(v > 0 for per in gate.values() for v in per.values()) and bool(gate)
    payload = {
        "unit": "G3-LIMIT-V2",
        "rows": len(rows),
        "budgets": budgets,
        "arms": arms,
        "gate": {
            "require": ">=1 compaction per compacting arm at each budget",
            "compaction_rows_per_arm": gate,
            "compaction_events": len(events),
            "pass": gate_pass,
        },
        "matched_turn_contrast": matched,
        "per_arm": depths,
        "deltas": deltas,
        "renderer_effect": render_effect,
        "method": {
            "bootstrap_resamples": BOOT,
            "seed": SEED,
            "delta_definition": "mean uncached tokens/turn (compacting arm) - mean uncached tokens/turn "
                                "(compaction-free baseline, same budget, same renderer)",
            "note": "uncached_tokens = prompt_tokens - cached_tokens from the server's own usage block",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    rows_sha = hashlib.sha256(ROWS.read_bytes()).hexdigest()
    run = {}
    if RUN.exists():
        run = json.loads(RUN.read_text(encoding="utf-8"))
    stamps = sorted(str(r.get("ts_utc") or "") for r in rows if r.get("ts_utc"))
    run.update({
        "unit": "G3-LIMIT-V2",
        "rows": len(rows),
        "rows_sha256": rows_sha,
        "compaction_events": len(events),
        "gate_pass": gate_pass,
        "compaction_rows_per_arm": gate,
        "first_row_ts": stamps[0] if stamps else None,
        "last_row_ts": stamps[-1] if stamps else None,
        "errors": sum(1 for r in rows if r.get("status") != 200),
        "analysis_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    })
    RUN.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")

    print(f"rows={len(rows)} events={len(events)} gate_pass={gate_pass}")
    for b in budgets:
        for a in arms:
            if a in depths[b]:
                s = depths[b][a]
                print(f"{b:>5} {a:<7} n={s['n']:3d} uncached/turn={s['mean_uncached_per_turn']:7.1f} "
                      f"ci={s['boot95_ci_mean_uncached']} below={s['mean_uncached_below_budget']} "
                      f"boundary={s['mean_uncached_boundary_turn']} compactions={s['compactions_total']}")
    for b in budgets:
        for a, d in deltas[b].items():
            print(f"DELTA {b} {a} vs {d['baseline']}: {d['delta_tokens_per_turn']:+.1f} tok/turn "
                  f"({d['delta_pct']:+.2f}%) ci={d['boot95_ci_delta']} excludes_zero={d['excludes_zero']}")
    return 0


def dedupe_events(events):
    seen = {}
    for e in events:
        seen[(e.get("arm"), e.get("budget"), int(e.get("turn", 0)))] = e
    return list(seen.values())


if __name__ == "__main__":
    sys.exit(main())
