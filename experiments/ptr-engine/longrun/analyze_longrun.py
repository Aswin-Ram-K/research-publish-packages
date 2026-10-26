#!/usr/bin/env python3
"""analyze_longrun.py — METRICS-V2: five dashboard metrics over long-run rows.

Read-only. Computes, per row file and per arm, from rows already paid for:
  TTFT p50/p95/p99/max, cached_share per turn + early/middle/late trend,
  tokens_to_verified_success, time_to_verified_success_s, failure-charged
  aggregation, per-depth checkpoint accuracy, false-claim rate, and a
  VALIDITY verdict per file.

It never edits a row file, never runs a request, and never pools across
different `max_tokens` values (a group is split and flagged instead).

Usage:
  .venv/bin/python analyze_longrun.py ROWFILE [ROWFILE ...] [--json OUT]
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(HERE, "runtime", "LR-01.json")

FAILED_TURN_RULE = (
    "A turn is a FAILED TURN when (answer_source == 'none' OR truncated == true) "
    "and no expected value is present for that turn. A run that never verifies a "
    "checkpoint is charged at WORST CASE: observed per-turn cost plus, for every "
    "turn not observed up to N, the largest per-turn (uncached+completion, and "
    "latency) seen in that run. A failed run is never dropped."
)
FROZEN_RULE = (
    "pointer-stable wins only on p95 TTFT >= 2x better than transcript-grow at the "
    "final turn, tokens-to-verified-success no worse, checkpoint accuracy no worse."
)
CLAIM_RE = re.compile(
    r"(?i)\b(i (?:have )?(?:completed|finished)|all tests (?:pass|passed)|"
    r"tests (?:pass|passed)|verified successfully|task (?:is )?complete|"
    r"acceptance (?:checks? )?pass(?:ed)?|exit code 0|fix (?:is )?verified|"
    r"successfully (?:fixed|verified)|everything (?:works|passed))\b"
)


def load_rows(path):
    """Tolerant reader: a growing/partial file yields the whole rows it has."""
    with open(path, "rb") as fh:
        blob = fh.read()
    rows, malformed = [], 0
    for line in blob.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1  # typically a half-written last line; never fatal
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows, {"bytes": len(blob), "malformed_rows_skipped": malformed}


def pct(values, p):
    """Linear-interpolated percentile. n=0 -> None. Estimates, not exact order stats."""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p
    lo, hi = int(rank), min(int(rank) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo)


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def ttft_ms(r):
    """TTFT in ms: prefer ttft_ms, fall back to ttft_s; None if neither exists."""
    v = num(r.get("ttft_ms"))
    if v is not None:
        return v
    s = num(r.get("ttft_s"))
    return s * 1000.0 if s is not None else None


def prompt_cost(r):
    u = num(r.get("uncached_tokens"))
    if u is None:
        pt, ct = num(r.get("prompt_tokens")), num(r.get("cached_tokens"))
        u = (pt - ct) if (pt is not None and ct is not None) else None
    c = num(r.get("completion_tokens")) or 0
    return None if u is None else u + c


def answer_text(r):
    txt = r.get("content") or ""
    if not txt.strip() and r.get("reasoning"):
        txt = r.get("reasoning") or ""
    return txt


def exact_match(text, expected):
    return bool(expected) and text.strip() == str(expected).strip()


def contains_match(text, expected):
    return bool(expected) and str(expected).strip() in text


def validity(rows, meta, cps, N):
    n = len(rows)
    trunc = sum(1 for r in rows if r.get("truncated") is True)
    trunc_missing = sum(1 for r in rows if "truncated" not in r)
    as_none = sum(1 for r in rows if r.get("answer_source") == "none")
    as_missing = sum(1 for r in rows if "answer_source" not in r or r.get("answer_source") is None)
    ttft_missing = sum(1 for r in rows if ttft_ms(r) is None)
    mt = sorted({r.get("max_tokens") for r in rows if num(r.get("max_tokens")) is not None})
    ctoks = [num(r.get("completion_tokens")) for r in rows if num(r.get("completion_tokens")) is not None]
    empty = sum(1 for r in rows if not answer_text(r).strip())
    turns = sorted({r.get("turn") for r in rows if isinstance(r.get("turn"), int)})
    reasons = []
    if not rows:
        reasons.append("no parseable rows")
    if as_missing == n or (as_none + as_missing) == n:
        reasons.append("answer_source absent or 'none' on every row (content-only parser)")
    if not mt and ctoks and max(ctoks) <= 256:
        reasons.append("max_tokens absent from every row; completion_tokens capped at %d" % max(ctoks))
    if empty == n:
        reasons.append("every row has empty content")
    verdict = "INVALID-INSTRUMENT" if reasons else "VALID"
    completeness = "COMPLETE" if (turns and max(turns) >= N) else "PARTIAL"
    return {
        "verdict": verdict,
        "reason": "; ".join(reasons) if reasons else "fields required by the five metrics are present",
        "completeness": completeness,
        "rows": n,
        "turns_seen": len(turns),
        "max_turn_seen": max(turns) if turns else None,
        "N": N,
        "truncated_rows": trunc,
        "truncated_field_missing_rows": trunc_missing,
        "answer_source_none_rows": as_none,
        "answer_source_absent_rows": as_missing,
        "ttft_missing_rows": ttft_missing,
        "max_tokens_seen": mt,
        "completion_tokens_max": max(ctoks) if ctoks else None,
        "empty_content_rows": empty,
        "bytes": meta.get("bytes"),
        "malformed_rows_skipped": meta.get("malformed_rows_skipped"),
    }


def thirds(rows):
    turns = sorted({r.get("turn") for r in rows if isinstance(r.get("turn"), int)})
    if not turns:
        return {}
    out = {}
    for label, lo in (("early", 0), ("middle", 1), ("late", 2)):
        a = (lo * len(turns)) // 3
        b = ((lo + 1) * len(turns)) // 3 if lo < 2 else len(turns)
        band = turns[a:b]
        vals = [num(r.get("cached_tokens")) / num(r.get("prompt_tokens"))
                for r in rows
                if r.get("turn") in band and num(r.get("prompt_tokens")) and num(r.get("cached_tokens")) is not None]
        out[label] = {
            "turns": [band[0], band[-1]] if band else None,
            "n": len(vals),
            "mean_cached_share": round(sum(vals) / len(vals), 4) if vals else None,
        }
    return out


def by_run(rows):
    groups = {}
    for r in rows:
        groups.setdefault(r.get("run_id") or "run:%s:%s" % (r.get("arm"), r.get("rep")), []).append(r)
    return groups


def run_costs(run_rows, cps, N):
    """Verified-success cost if it verifies; else observed + worst-case fill."""
    ordered = sorted(run_rows, key=lambda r: r.get("turn") or 0)
    verify_turn, verified = None, False
    for r in ordered:
        exp = r.get("expected")
        if exp is None and r.get("turn") in cps:
            exp = cps[r.get("turn")]["expected"]
        if (r.get("is_checkpoint") or r.get("turn") in cps) and exp is not None:
            text = answer_text(r)
            ok = r.get("answer_verified") is True or exact_match(text, exp)
            if ok:
                verify_turn, verified = r.get("turn"), True
                break
    tokens = secs = 0.0
    tok_n = lat_n = 0
    max_tok = max_lat = 0.0
    for r in ordered:
        if verify_turn is not None and (r.get("turn") or 0) > verify_turn:
            break
        tc, lat = prompt_cost(r), num(r.get("latency_s"))
        if tc is not None:
            tokens += tc; tok_n += 1; max_tok = max(max_tok, tc)
        if lat is not None:
            secs += lat; lat_n += 1; max_lat = max(max_lat, lat)
    out = {
        "verified": verified,
        "verified_at_turn": verify_turn,
        "tokens_to_verified_success": tokens if verified else None,
        "time_to_verified_success_s": round(secs, 3) if verified else None,
        "observed_tokens": tokens,
        "observed_latency_s": round(secs, 3),
        "tokens_n": tok_n,
        "latency_n": lat_n,
    }
    if not verified:
        last = max((r.get("turn") or 0) for r in ordered)
        missing = max(0, N - last)
        out["worst_case_charge"] = {
            "missing_turns_filled": missing,
            "charged_tokens": round(tokens + missing * max_tok, 1),
            "charged_latency_s": round(secs + missing * max_lat, 3),
            "rule": "unobserved turns up to N charged at this run's largest per-turn cost",
        }
    return out


def false_claims(rows, cps):
    hits = []
    for r in rows:
        turn = r.get("turn")
        is_cp = r.get("is_checkpoint") is True or turn in cps or r.get("kind") == "verify"
        if not is_cp:
            continue
        exp = r.get("expected")
        if exp is None and turn in cps:
            exp = cps[turn]["expected"]
        if exp is not None:
            continue  # expected present: an assertion is checkable, not a false claim
        text = answer_text(r)
        m = CLAIM_RE.search(text)
        if m:
            hits.append({
                "arm": r.get("arm"), "rep": r.get("rep"), "turn": turn,
                "run_id": r.get("run_id"),
                "claim": m.group(0),
                "expected_absent": True,
                "answer_source": r.get("answer_source"),
                "quote": text.strip()[:200],
            })
    return hits


def depth_accuracy(rows, cps):
    out = {}
    for idx, turn in enumerate(sorted(cps)):
        label = {0: "quarter", 1: "half", 2: "end"}.get(idx, "cp%d" % turn)
        cp = cps[turn]
        at = [r for r in rows if r.get("turn") == turn]
        passed = 0
        observed = []
        for r in at:
            text = answer_text(r)
            exp = cp["expected"]
            ok = exact_match(text, exp)
            passed += 1 if ok else 0
            observed.append({
                "run_id": r.get("run_id"), "rep": r.get("rep"),
                "answer_source": r.get("answer_source"),
                "exact_match": ok,
                "contains_expected": contains_match(text, exp),
                "quote": text.strip()[:200],
            })
        out[label] = {
            "turn": turn,
            "expected": cp["expected"],
            "n_observed": len(at),
            "n_exact": passed,
            "accuracy": round(passed / len(at), 4) if at else None,
            "status": "observed" if at else "NOT_OBSERVED",
            "answers": observed,
        }
    return out


def arm_block(rows, cps, N):
    ttft = [v for v in (ttft_ms(r) for r in rows) if v is not None]
    cache = {}
    for r in rows:
        pt, ct = num(r.get("prompt_tokens")), num(r.get("cached_tokens"))
        if pt and ct is not None:
            cache.setdefault(r.get("turn"), []).append(ct / pt)
    groups = by_run(rows)
    runs = {rid: run_costs(rr, cps, N) for rid, rr in groups.items()}
    fc = false_claims(rows, cps)
    return {
        "arm": rows[0].get("arm"),
        "n_rows": len(rows),
        "n_runs": len(groups),
        "turns_seen": sorted({r.get("turn") for r in rows if isinstance(r.get("turn"), int)}),
        "ttft_ms": {
            "n": len(ttft),
            "p50": round(pct(ttft, 0.50), 2) if ttft else None,
            "p95": round(pct(ttft, 0.95), 2) if ttft else None,
            "p99": round(pct(ttft, 0.99), 2) if ttft else None,
            "max": round(max(ttft), 2) if ttft else None,
            "note": "p95/p99 estimated from %d samples (interpolated)" % len(ttft) if ttft else "no usable TTFT rows",
        },
        "cached_share_per_turn": {str(k): round(sum(v) / len(v), 4) for k, v in sorted(cache.items(), key=lambda kv: kv[0] or 0)},
        "cached_share_by_third": thirds(rows),
        "runs": runs,
        "per_depth_checkpoint_accuracy": depth_accuracy(rows, cps),
        "false_claims": {"count": len(fc), "hits": fc},
    }


def analyse_file(path, cps, N):
    rows, meta = load_rows(path)
    val = validity(rows, meta, cps, N)
    if val["verdict"] == "INVALID-INSTRUMENT":
        # An invalid instrument is reported, never averaged into a metric.
        return {"path": path, "validity": val, "arms": {},
                "arms_withheld": "INVALID-INSTRUMENT: per-arm metrics are not a data point and are withheld (%s)" % val["reason"]}
    # never pool across differing max_tokens values
    buckets = {}
    for r in rows:
        buckets.setdefault((r.get("arm"), r.get("max_tokens")), []).append(r)
    by_arm = {}
    for (arm, mt), rs in buckets.items():
        block = arm_block(rs, cps, N)
        block["max_tokens"] = mt
        values = sorted({x for (a, x) in buckets if a == arm and x is not None})
        block["pooling_refused_across_max_tokens"] = len(values) > 1
        by_arm.setdefault(arm or "<none>", []).append(block)
    return {"path": path, "validity": val, "arms": by_arm}


def fmt(v, nd=2):
    if v is None:
        return "-"
    if isinstance(v, float):
        return ("%%.%df" % nd) % v
    return str(v)


def print_file(res):
    v = res["validity"]
    print("\n== %s" % res["path"])
    print("VALIDITY  %s  [%s]  rows=%d turns=%s/%d  %s"
          % (v["verdict"], v["completeness"], v["rows"], v["max_turn_seen"], v["N"], v["reason"]))
    print("  truncated_rows=%d  answer_source_none_rows=%d  answer_source_absent_rows=%d  "
          "ttft_missing_rows=%d  max_tokens_seen=%s  completion_tokens_max=%s"
          % (v["truncated_rows"], v["answer_source_none_rows"], v["answer_source_absent_rows"],
             v["ttft_missing_rows"], v["max_tokens_seen"], v["completion_tokens_max"]))
    if res.get("arms_withheld"):
        print("  METRICS WITHHELD — %s" % res["arms_withheld"])
        return
    for arm, blocks in res["arms"].items():
        for b in blocks:
            t = b["ttft_ms"]
            runs = b["runs"]
            print("\n  %s  (max_tokens=%s, n_rows=%d, n_runs=%d%s)"
                  % (arm, b["max_tokens"], b["n_rows"], b["n_runs"],
                     ", POOLING REFUSED across max_tokens" if b["pooling_refused_across_max_tokens"] else ""))
            print("    TTFT(ms)  n=%d  p50=%s  p95=%s  p99=%s  max=%s"
                  % (t["n"], fmt(t["p50"]), fmt(t["p95"]), fmt(t["p99"]), fmt(t["max"])))
            cth = b["cached_share_by_third"]
            print("    cached_share  early=%s (n=%s)  middle=%s (n=%s)  late=%s (n=%s)"
                  % (fmt(cth.get("early", {}).get("mean_cached_share"), 3), cth.get("early", {}).get("n"),
                     fmt(cth.get("middle", {}).get("mean_cached_share"), 3), cth.get("middle", {}).get("n"),
                     fmt(cth.get("late", {}).get("mean_cached_share"), 3), cth.get("late", {}).get("n")))
            for rid, r in runs.items():
                if r["verified"]:
                    print("    TTVS  run=%s  verified@t%s  tokens=%s  time=%ss"
                          % (rid, r["verified_at_turn"], fmt(r["tokens_to_verified_success"], 0),
                             fmt(r["time_to_verified_success_s"], 2)))
                else:
                    w = r["worst_case_charge"]
                    print("    TTVS  run=%s  NOT VERIFIED  observed_tokens=%s  observed_latency=%ss  "
                          "worst_case_fill=%d turns -> tokens=%s time=%ss"
                          % (rid, fmt(r["observed_tokens"], 0), fmt(r["observed_latency_s"], 2),
                             w["missing_turns_filled"], fmt(w["charged_tokens"], 0), fmt(w["charged_latency_s"], 2)))
            for label, d in b["per_depth_checkpoint_accuracy"].items():
                print("    depth %-7s turn=%s expected=%r accuracy=%s (n=%d) status=%s"
                      % (label, d["turn"], d["expected"], fmt(d["accuracy"], 3), d["n_observed"], d["status"]))
            print("    false_claims=%d" % b["false_claims"]["count"])
            for h in b["false_claims"]["hits"]:
                print("      -> %s t%s source=%s quote=%r" % (h["arm"], h["turn"], h["answer_source"], h["quote"][:120]))


def main(argv):
    files = [a for a in argv if not a.startswith("--")]
    out_json = None
    if "--json" in argv:
        out_json = argv[argv.index("--json") + 1]
        files = [a for a in files if a != out_json]
    if not files:
        print(__doc__)
        return 2
    with open(RUNTIME, "r", encoding="utf-8") as fh:
        fixture = json.load(fh)
    N = int(fixture.get("N") or 48)
    cps = {int(c["turn"]): c for c in (fixture.get("checkpoints") or [])}
    results = [analyse_file(p, cps, N) for p in files]
    payload = {
        "schema": "metrics-v2/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frozen_decision_rule": FROZEN_RULE,
        "frozen_rule_untouched": True,
        "failed_turn_rule": FAILED_TURN_RULE,
        "files": results,
    }
    for res in results:
        print_file(res)
    if out_json:
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print("\nJSON written: %s" % out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
