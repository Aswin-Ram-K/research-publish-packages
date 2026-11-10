#!/usr/bin/env python3
"""Recompute campaign arm metrics and selection from raw rows.

Trusts no prior summary. Reads rows from the path given in the envelope
(or --rows override). Prints a full per-arm table and applies the selection
rule.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CAMPAIGN_ROOT = Path(__file__).resolve().parents[1]


def _load_envelope(path):
    return json.loads(Path(path).read_text())


def _resolve_path(env, candidates, base_dirs):
    for k in candidates:
        v = env.get(k)
        if v:
            p = Path(v)
            if not p.is_absolute():
                for bd in base_dirs:
                    cand = Path(bd) / p
                    if cand.exists():
                        p = cand
                        break
            return p
    return None


def _base_dirs(env_path):
    ep = Path(env_path).resolve().parent
    return [Path.cwd(), ep, ep.parent, ep.parent.parent]


def _load_rows(env, env_path, rows_override, phase):
    if rows_override:
        p = Path(rows_override)
    else:
        envd = _load_envelope(env_path) if env_path else {}
        base = _base_dirs(env_path) if env_path else [Path.cwd()]
        p = _resolve_path(envd, ("rows_path", "rows", "row_path", "rows_file", "rows_jsonl", "row_file", "output_rows"), base)
    if p is None:
        # default
        p = Path("rows.jsonl")
    rows = []
    if not p.exists():
        return rows, p
    for line in p.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    if phase:
        filtered = [r for r in rows if (r.get("phase") is None or r.get("phase") == phase)]
        if filtered:
            rows = filtered
    return rows, p


def _task_id(r):
    return r.get("task_id") or r.get("task") or r.get("taskid")


def _arm(r):
    return r.get("arm") or r.get("arm_id")


def _turn(r):
    return r.get("turn")


def _grade(r):
    g = r.get("grade")
    if isinstance(g, dict):
        return g
    return {}


def _output(r):
    if "output" in r:
        return r.get("output")
    return r.get("text")


def _finish(r):
    return r.get("finish_reason")


def _prompt(r):
    v = r.get("prompt_tokens")
    if v is None and isinstance(r.get("raw_usage"), dict):
        v = r.get("raw_usage", {}).get("prompt_tokens")
    return v


def _cached(r):
    v = r.get("cached_tokens")
    if v is None and isinstance(r.get("raw_usage"), dict):
        v = r.get("raw_usage", {}).get("cached_tokens")
    return v


def _completion(r):
    v = r.get("completion_tokens")
    if v is None and isinstance(r.get("raw_usage"), dict):
        v = r.get("raw_usage", {}).get("completion_tokens")
    if v is None:
        v = r.get("output_tokens")
    return v


def _reasoning(r):
    v = r.get("reasoning_tokens")
    if v is None and isinstance(r.get("raw_usage"), dict):
        v = r.get("raw_usage", {}).get("reasoning_tokens")
    return v


def _ttft(r):
    return r.get("ttft_ms")


def _wall(r):
    v = r.get("wall_ms")
    if v is None:
        v = r.get("total_ms")
    return v


def _silent(r):
    g = _grade(r)
    if "silent" in g:
        return bool(g.get("silent"))
    out = _output(r)
    return str(out).strip() == "" if out is not None else True


def _is_length(r):
    fr = str(_finish(r) or "").lower()
    return fr in ("length", "max_tokens", "max_output_tokens")


def _grade_ok(r):
    g = _grade(r)
    if "ok" in g:
        return g.get("ok")
    if "verified_success" in r:
        return bool(r.get("verified_success"))
    return None


def _uncached_row(r):
    cached = _cached(r)
    prompt = _prompt(r)
    if prompt is None:
        return None
    if cached is None:
        return None  # unknown -> range handled separately
    try:
        return max(0, int(prompt) - int(cached))
    except Exception:
        return None


def _median(xs):
    if not xs:
        return None
    try:
        return statistics.median(xs)
    except Exception:
        return None


def _sum_or_none(xs):
    if any(x is None for x in xs):
        return None
    return sum(xs)


def _range_for_arm(rows):
    """Return dict with point or range for cached/uncached/work."""
    prompts = [_prompt(r) for r in rows]
    completions = [_completion(r) for r in rows]
    cacheds = [_cached(r) for r in rows]
    # output tokens
    outputs = [int(x) if x is not None else 0 for x in completions]
    total_output = sum(outputs)
    total_prompt = sum(int(x) if x is not None else 0 for x in prompts)
    any_null_cache = any(_cached(r) is None for r in rows)
    # uncached per row where known
    uncached_known = []
    for r in rows:
        u = _uncached_row(r)
        if u is not None:
            uncached_known.append(u)
    if any_null_cache:
        # low: treat null cached as full hit (cached=prompt) -> uncached 0 for those
        low_uncached = 0
        for r in rows:
            cached = _cached(r)
            prompt = _prompt(r)
            p = int(prompt) if prompt is not None else 0
            if cached is None:
                low_uncached += 0
            else:
                low_uncached += max(0, p - int(cached))
        # high: treat null as miss (cached=0) -> uncached prompt
        high_uncached = 0
        for r in rows:
            cached = _cached(r)
            prompt = _prompt(r)
            p = int(prompt) if prompt is not None else 0
            if cached is None:
                high_uncached += p
            else:
                high_uncached += max(0, p - int(cached))
        low_proxy = low_uncached + total_output
        high_proxy = high_uncached + total_output
        cached_low = total_prompt - high_uncached  # if miss for null, cached lower
        cached_high = total_prompt - low_uncached
        return {
            "input_tokens": total_prompt,
            "cached_tokens": (cached_low, cached_high),
            "uncached_tokens": (low_uncached, high_uncached),
            "output_tokens": total_output,
            "work_proxy": (low_proxy, high_proxy),
            "work_proxy_point": None,
            "any_null_cache": True,
        }
    # no nulls
    total_cached = sum(int(_cached(r)) for r in rows)
    total_uncached = sum(int(_uncached_row(r)) for r in rows)
    proxy = total_uncached + total_output
    return {
        "input_tokens": total_prompt,
        "cached_tokens": total_cached,
        "uncached_tokens": total_uncached,
        "output_tokens": total_output,
        "work_proxy": proxy,
        "work_proxy_point": proxy,
        "any_null_cache": False,
    }


def _task_success(rows_by_task_arm):
    # rows_by_task_arm: dict task -> list rows for an arm
    out = {}
    for task, rs in rows_by_task_arm.items():
        oks = [_grade_ok(r) for r in rs]
        # successful if all turns grade True and none None
        success = (len(rs) > 0 and all(ok is True for ok in oks))
        out[task] = success
    return out


def analyse(rows, phase, paired_by):
    arms = sorted(set(_arm(r) for r in rows if _arm(r) is not None))
    # group
    by_arm: Dict[str, List[Any]] = {a: [] for a in arms}
    for r in rows:
        a = _arm(r)
        if a in by_arm:
            by_arm[a].append(r)

    # discovery task detection
    def is_discovery(tid):
        if tid is None:
            return False
        s = str(tid).lower()
        return s.startswith("d") or "discovery" in s

    # per arm metrics
    arm_metrics = {}
    for arm in arms:
        rs = by_arm[arm]
        # task grouping
        by_task = {}
        for r in rs:
            by_task.setdefault(_task_id(r), []).append(r)
        task_success = _task_success(by_task)
        successful_tasks = sum(1 for v in task_success.values() if v)
        discovery_tasks = {t: v for t, v in task_success.items() if is_discovery(t)}
        successful_discovery = sum(1 for v in discovery_tasks.values() if v)
        undefined_recovery = any(_grade_ok(r) is None for r in rs)
        silent_turns = sum(1 for r in rs if _silent(r))
        failed_turns = sum(1 for r in rs if _grade_ok(r) is False)
        length_turns = sum(1 for r in rs if _is_length(r))
        ttfts = [x for x in (_ttft(r) for r in rs) if x is not None]
        walls = [x for x in (_wall(r) for r in rs) if x is not None]
        rng = _range_for_arm(rs)
        arm_metrics[arm] = {
            "calls": len(rs),
            "task_pass_count": sum(1 for v in task_success.values() if v),
            "task_total": len(task_success),
            "successful_discovery_tasks": successful_discovery,
            "discovery_task_total": len(discovery_tasks),
            "undefined_recovery": undefined_recovery,
            "silent_turns": silent_turns,
            "failed_turns": failed_turns,
            "length_exhausted_turns": length_turns,
            "range": rng,
            "ttft_median": _median(ttfts),
            "ttft_min": (min(ttfts) if ttfts else None),
            "ttft_max": (max(ttfts) if ttfts else None),
            "wall_median": _median(walls),
            "wall_min": (min(walls) if walls else None),
            "wall_max": (max(walls) if walls else None),
            "task_success": task_success,
        }

    # per-task paired differences vs A
    # work proxy per task per arm (sum)
    task_arm_proxy = {}
    for arm in arms:
        for r in by_arm[arm]:
            tid = _task_id(r)
            cached = _cached(r)
            prompt = _prompt(r)
            comp = _completion(r)
            # for paired diff use point if possible else treat null as 0 uncached? Use range midpoint? Use miss for null.
            if prompt is None:
                u = 0
            elif cached is None:
                u = int(prompt)
            else:
                u = max(0, int(prompt) - int(cached))
            c = int(comp) if comp is not None else 0
            task_arm_proxy.setdefault(tid, {}).setdefault(arm, 0)
            task_arm_proxy[tid][arm] += u + c

    paired_diffs = {}
    if "A" in arms:
        for tid in sorted(task_arm_proxy):
            diffs = {}
            base = task_arm_proxy[tid].get("A")
            for arm in arms:
                if arm == "A":
                    continue
                val = task_arm_proxy[tid].get(arm)
                if base is not None and val is not None:
                    diffs[arm] = val - base
            paired_diffs[tid] = diffs

    # selection rule (discovery)
    base_arm = "A"
    base_metrics = arm_metrics.get(base_arm, {})
    base_discovery_success = base_metrics.get("successful_discovery_tasks", 0)
    base_ttft_median = base_metrics.get("ttft_median")
    base_proxy = None
    if isinstance(base_metrics.get("range", {}).get("work_proxy"), tuple):
        base_proxy = base_metrics["range"]["work_proxy"][1]  # conservative? use high
    else:
        base_proxy = base_metrics.get("range", {}).get("work_proxy")

    eligible = []
    excluded = {}
    if base_metrics.get("undefined_recovery"):
        # quality not defined for A
        pass
    for arm in arms:
        if arm == base_arm:
            continue
        m = arm_metrics[arm]
        reasons = []
        if m["successful_discovery_tasks"] < base_discovery_success:
            reasons.append(f"fewer successful discovery tasks ({m['successful_discovery_tasks']} < {base_discovery_success})")
        if m["undefined_recovery"]:
            reasons.append("undefined recovery checks")
        if base_metrics.get("undefined_recovery"):
            reasons.append("baseline A has undefined recovery checks")
        if reasons:
            excluded[arm] = "; ".join(reasons)
            continue
        # ttft condition checked at selection: no median ttft increase
        eligible.append(arm)

    # Among eligible, pick greatest work-proxy reduction subject to no observed median TTFT increase.
    # Compute reduction using work proxy (point or high bound). Use total work proxy per arm.
    def arm_proxy_total(arm):
        r = arm_metrics[arm]["range"].get("work_proxy")
        if isinstance(r, tuple):
            return r[1]  # conservative upper
        return r

    base_total = arm_proxy_total(base_arm) if base_arm in arm_metrics else None
    candidates = []
    for arm in eligible:
        m = arm_metrics[arm]
        # no observed median TTFT increase
        arm_ttft = m["ttft_median"]
        if base_ttft_median is not None and arm_ttft is not None and arm_ttft > base_ttft_median:
            excluded[arm] = excluded.get(arm, "") 
            if "median TTFT increase" not in excluded[arm]:
                excluded[arm] = (excluded[arm] + "; " if excluded[arm] else "") + f"median TTFT increase ({arm_ttft} > {base_ttft_median})"
            continue
        if base_total and base_total > 0:
            reduction = (base_total - arm_proxy_total(arm)) / base_total
        else:
            reduction = 0.0
        candidates.append((arm, reduction, arm_ttft if arm_ttft is not None else float("inf")))

    winner = base_arm
    if candidates:
        # greatest reduction; tie -> lower median TTFT; then lexicographic arm ID
        # sort: reduction desc, ttft asc, arm asc
        candidates_sorted = sorted(candidates, key=lambda x: (-x[1], x[2], x[0]))
        winner = candidates_sorted[0][0]
        # but if no reduction? rule says if none qualifies select A; "qualifies" maybe reduction>0? 
        # The spec: eligible arms have no fewer tasks; among eligible pick greatest reduction subject to no TTFT increase.
        # If reduction <=0, still could select? Adoption gate later. For discovery selection, choose best even if no reduction? 
        # We'll select winner only if reduction > 0? The plan: "If none qualifies, select A." Qualifies includes eligible + no TTFT increase. 
        # We already filtered. But if reduction <= 0, arguably not a candidate. However spec doesn't require reduction>0 for selection.
        # Keep winner as best eligible.
    # Quality defined check
    quality_defined = not base_metrics.get("undefined_recovery") and base_discovery_success >= 0
    # if baseline has null grades, quality not defined -> no winner
    if base_metrics.get("undefined_recovery"):
        winner = base_arm
        quality_defined = False

    # If no eligible candidates, winner A
    if not candidates:
        winner = base_arm

    return arm_metrics, paired_diffs, eligible, excluded, candidates, winner, quality_defined, base_discovery_success


def _fmt_range(v):
    if isinstance(v, tuple):
        return f"[{v[0]}..{v[1]}]"
    return v


def print_report(arm_metrics, paired_diffs, eligible, excluded, candidates, winner, quality_defined, base_discovery_success, phase, paired_by):
    print(f"PHASE: {phase}")
    if paired_by:
        print(f"PAIRED-BY: {paired_by} (independent unit = task/trajectory; turn-level rows not pooled)")
    print("")
    # table header
    print(f"{'arm':4} {'calls':>6} {'tasks_pass':>10} {'disc_ok':>8} {'silent':>7} {'failed':>7} {'length':>7} {'input':>9} {'cached':>12} {'uncached':>12} {'output':>9} {'work_proxy':>14} {'ttft_med':>10} {'ttft_min':>10} {'ttft_max':>10}")
    for arm in sorted(arm_metrics):
        m = arm_metrics[arm]
        r = m["range"]
        print(f"{arm:4} {m['calls']:6} {m['task_pass_count']:10} {m['successful_discovery_tasks']:8} {m['silent_turns']:7} {m['failed_turns']:7} {m['length_exhausted_turns']:7} {r['input_tokens']:9} {_fmt_range(r['cached_tokens']):>12} {_fmt_range(r['uncached_tokens']):>12} {r['output_tokens']:9} {_fmt_range(r['work_proxy']):>14} {str(m['ttft_median']):>10} {str(m['ttft_min']):>10} {str(m['ttft_max']):>10}")
    print("")
    print("ELIGIBLE:", eligible if eligible else "[]")
    print("EXCLUDED:")
    if excluded:
        for arm, reason in excluded.items():
            print(f"  {arm}: {reason}")
    else:
        print("  (none)")
    print("")
    if not quality_defined:
        print("WINNER: none (quality not defined)")
    else:
        print(f"WINNER: {winner}")
    print("")
    print("PAIRED DIFFS vs A (work proxy per task):")
    for tid in sorted(paired_diffs):
        print(f"  {tid}: {paired_diffs[tid]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelope", required=True)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--phase-instances", dest="phase_instances", default=None)
    ap.add_argument("--paired-by", dest="paired_by", default=None)
    ap.add_argument("--rows", default=None)
    args = ap.parse_args()

    env_path = args.envelope
    env = _load_envelope(env_path)
    base_dirs = _base_dirs(env_path)
    rows, rows_path = _load_rows(env, env_path, args.rows, args.phase)

    synth_rows = [r for r in rows if r.get("synthetic") is True]
    if synth_rows:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print("WARNING: SYNTHETIC ROWS DETECTED (%d of %d) - EXCLUDED FROM MEASUREMENT" % (len(synth_rows), len(rows)), file=sys.stderr)
        print("A phase containing synthetic rows cannot contribute to work proxy, cache ratio, or winner selection." % (), file=sys.stderr)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        rows = [r for r in rows if r.get("synthetic") is not True]

    if not rows:
        print("no non-synthetic rows to analyse", file=sys.stderr)
        sys.exit(1)

    arm_metrics, paired_diffs, eligible, excluded, candidates, winner, quality_defined, base_disc = analyse(
        rows, args.phase, args.paired_by
    )

    print_report(arm_metrics, paired_diffs, eligible, excluded, candidates, winner, quality_defined, base_disc, args.phase, args.paired_by)
    # exit 0 normally
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
