#!/usr/bin/env python3
"""Independent verification dossier for R2-VLLM rows.jsonl (unit R2-VLLM-ANALYSE).

Derives every figure directly from rows.jsonl. Deliberately does NOT read
analysis.json, so a separate verifier can re-run this and re-derive the same
numbers without trusting either the analyser or this unit.

Run from the workspace root:
    .venv/bin/python experiments/context-cache/cells/R2-VLLM/logs/verify-dossier.py
Writes JSON to stdout; redirect to logs/verify-dossier.json.
"""
import json
import hashlib
import collections
import statistics

BASE = "experiments/context-cache/cells/R2-VLLM"
ROWS = BASE + "/rows.jsonl"
LAUNCH = BASE + "/logs/%s-launch.json"
ARMS = ["A", "C", "R", "H"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stats(vals):
    """n / mean / median of a numeric list; None (not 0) when empty."""
    if not vals:
        return {"n": 0, "mean": None, "median": None}
    return {"n": len(vals),
            "mean": round(sum(vals) / len(vals), 3),
            "median": statistics.median(vals)}


def load():
    raw = open(ROWS, "rb").read()
    text = raw.decode("utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return raw, [json.loads(ln) for ln in lines], len(text.splitlines()) - len(lines)


def main():
    raw, rows, n_blank = load()
    out = {}
    out["unit"] = "R2-VLLM-ANALYSE"
    out["rows_file"] = ROWS
    out["rows_sha256"] = sha256_file(ROWS)
    out["n_rows"] = len(rows)
    out["n_blank_lines"] = n_blank

    configs = sorted({r["config_id"] for r in rows})

    # ---------- resolved block size (read from launch record + rows, never assumed) ----------
    out["resolved_block_size"] = {}
    for cfg in configs:
        try:
            d = json.load(open(LAUNCH % cfg))
            logv = d.get("resolved_block_size_from_log")
        except Exception as e:  # unobservable rather than fabricated
            logv = "unobservable: %s" % e
        out["resolved_block_size"][cfg] = {
            "from_launch_log": logv,
            "from_rows": sorted({r["resolved_block_size"] for r in rows
                                 if r["config_id"] == cfg}),
        }

    out["phase_by_config"] = {
        cfg: dict(collections.Counter(r["phase"] for r in rows if r["config_id"] == cfg))
        for cfg in configs}

    # ---------- per (config, arm) ----------
    per = {}
    for cfg in configs:
        for arm in ARMS + [None]:
            sub = [r for r in rows if r["config_id"] == cfg and r["arm"] == arm]
            if not sub:
                continue
            key = "%s|%s" % (cfg, arm if arm is not None else "null")
            unc = [r["prompt_tokens"] - r["cached_tokens"] for r in sub
                   if r["cached_tokens"] is not None]
            excluded = len(sub) - len(unc)
            perpass = collections.Counter((r["turn"], r["rep"]) for r in sub)
            per[key] = {
                "rows": len(sub),
                "distinct_turns": sorted({r["turn"] for r in sub if r["turn"] is not None}),
                "rows_per_turn_rep": {"%s|%s" % (k[0], k[1]): v for k, v in sorted(
                    perpass.items(), key=lambda kv: (str(kv[0][0]), kv[0][1]))},
                "cached_eq_0": sum(1 for r in sub if r["cached_tokens"] == 0),
                "cached_gt_0": sum(1 for r in sub if r["cached_tokens"] is not None
                                   and r["cached_tokens"] > 0),
                "cached_none": sum(1 for r in sub if r["cached_tokens"] is None),
                "total_cached": sum(r["cached_tokens"] for r in sub
                                    if r["cached_tokens"] is not None),
                "uncached_stats": stats(unc),
                "uncached_excluded_n": excluded,
                "uncached_exclusion_reason": ("cached_tokens is None -> uncached undefined"
                                              if excluded else ""),
            }
    out["per_config_arm"] = per

    # ---------- arm identity: distinct prefix_sha256 across the four arms per (config, turn) ----------
    ident = {}
    for cfg in configs:
        per_turn = collections.defaultdict(set)
        for r in rows:
            if r["config_id"] == cfg and r["arm"] is not None:
                per_turn[r["turn"]].add(r["prefix_sha256"])
        counts = {str(t): len(s) for t, s in sorted(per_turn.items())}
        ident[cfg] = {
            "turns": len(counts),
            "distinct_prefix_sha256_per_turn": counts,
            "turns_reaching_4": sum(1 for v in counts.values() if v == 4),
            "all_turns_4_of_4": bool(counts) and all(v == 4 for v in counts.values()),
        }
    out["arm_identity"] = ident

    # ---------- arm_compaction / arm_render / prompt_nodes presence + distribution ----------
    fields = {}
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        e = {"rows": len(sub)}
        for f in ("arm_compaction", "arm_render", "prompt_nodes"):
            present = [r for r in sub if r.get(f) is not None]
            e[f + "_present"] = len(present)
            e[f + "_absent"] = len(sub) - len(present)
            if f == "prompt_nodes":
                dist = collections.Counter(json.dumps(r[f], sort_keys=True) for r in present)
            else:
                dist = collections.Counter(str(r[f]) for r in present)
            e[f + "_dist"] = dict(dist)
            e[f + "_distinct"] = len(dist)
        fields[arm] = e
    out["arm_fields"] = fields

    # ---------- cold-pass integrity: rep=0 rows with cached_tokens > 0 ----------
    cold = {}
    for cfg in configs:
        hits = [{"request_index": r["request_index"], "phase": r["phase"], "arm": r["arm"],
                 "turn": r["turn"], "rep": r["rep"], "prompt_tokens": r["prompt_tokens"],
                 "cached_tokens": r["cached_tokens"],
                 "blocks_available": r["blocks_available"],
                 "prefix_sha256": r["prefix_sha256"][:16]}
                for r in rows if r["config_id"] == cfg and r["rep"] == 0
                and r["cached_tokens"] is not None and r["cached_tokens"] > 0]
        cold[cfg] = {
            "rep0_rows": sum(1 for r in rows if r["config_id"] == cfg and r["rep"] == 0),
            "rep0_rows_with_cached_gt_0": len(hits),
            "list": hits,
        }
    out["cold_pass_contamination"] = cold

    # ---------- repeat pass (rep=1): ratio distribution vs blocks_available ----------
    rep1 = {}
    for cfg in configs:
        sub = [r for r in rows if r["config_id"] == cfg and r["rep"] == 1]
        entry = {"rows": len(sub)}
        for arm in ARMS + [None]:
            a = [r for r in sub if r["arm"] == arm]
            if not a:
                continue
            ratios = [round(r["cached_tokens"] / r["prompt_tokens"], 4)
                      for r in a if r["cached_tokens"] is not None and r["prompt_tokens"]]
            per_row = []
            for r in a:
                if r["cached_tokens"] is None:
                    continue
                ba = r["prompt_tokens"] // r["resolved_block_size"]
                per_row.append({
                    "request_index": r["request_index"], "turn": r["turn"],
                    "prompt_tokens": r["prompt_tokens"],
                    "resolved_block_size": r["resolved_block_size"],
                    "blocks_available_field": r["blocks_available"],
                    "blocks_recomputed": ba,
                    "blocks_field_matches_row": r["blocks_available"] == ba,
                    "cached_tokens": r["cached_tokens"],
                    "cached_eq_one_block": r["cached_tokens"] == r["resolved_block_size"],
                    "ratio": round(r["cached_tokens"] / r["prompt_tokens"], 4),
                    "hit": r["cached_tokens"] > 0,
                })
            entry[arm or "null"] = {
                "n": len(a),
                "ratio_stats": stats(ratios),
                "ratio_distinct": sorted({x["ratio"] for x in per_row}),
                "rows_cached_eq_resolved_block": sum(1 for x in per_row if x["cached_eq_one_block"]),
                "per_row": per_row,
            }
        rep1[cfg] = entry
    out["repeat_pass_rep1"] = rep1

    # ---------- A1 zero pattern ----------
    a1 = [r for r in rows if r["config_id"] == "A1"]

    def cell(r):
        return {"request_index": r["request_index"], "phase": r["phase"], "arm": r["arm"],
                "turn": r["turn"], "rep": r["rep"], "prompt_tokens": r["prompt_tokens"],
                "cached_tokens": r["cached_tokens"],
                "blocks_available": r["blocks_available"],
                "resolved_block_size": r["resolved_block_size"],
                "usage_has_details": r["usage_has_details"]}

    zeros = [r for r in a1 if r["cached_tokens"] == 0]
    out["A1_zeros"] = {
        "rows": len(a1),
        "cached_gt_0": sum(1 for r in a1 if r["cached_tokens"] is not None and r["cached_tokens"] > 0),
        "cached_eq_0": len(zeros),
        "cached_none": sum(1 for r in a1 if r["cached_tokens"] is None),
        "usage_has_details_true": sum(1 for r in a1 if r.get("usage_has_details") is True),
        "hits": [cell(r) for r in a1 if r["cached_tokens"] is not None and r["cached_tokens"] > 0],
        "zero_breakdown": dict(collections.Counter(
            "phase=%s|arm=%s|turn=%s|rep=%s|ba=%s" % (r["phase"], r["arm"], r["turn"],
                                                      r["rep"], r["blocks_available"])
            for r in zeros)),
        "zero_rows_below_one_block": sum(1 for r in zeros
                                         if r["prompt_tokens"] < r["resolved_block_size"]),
        "zero_rows_at_or_above_one_block": sum(1 for r in zeros
                                               if r["prompt_tokens"] >= r["resolved_block_size"]),
        "zero_prompt_tokens_min_max": [min([r["prompt_tokens"] for r in zeros] or [None]),
                                       max([r["prompt_tokens"] for r in zeros] or [None])],
        "all_prompt_tokens_min_max": [min(r["prompt_tokens"] for r in a1),
                                      max(r["prompt_tokens"] for r in a1)],
        "zero_is_observed_miss": len(zeros) > 0 and all(r.get("usage_has_details") is True for r in zeros),
    }

    # ---------- non-200 ----------
    bad = [{"request_index": r["request_index"], "config_id": r["config_id"],
            "status": r["status"], "http_status": r["http_status"],
            "error": r.get("error"), "note": r.get("note")}
           for r in rows if r["status"] != 200 or r["http_status"] != 200]
    out["non_200"] = {"count": len(bad), "rows": bad,
                      "any_error_key_in_rows": any("error" in r for r in rows)}

    # ---------- OH1L leniency (launch-only probe, 0 model requests) ----------
    try:
        d = json.load(open(LAUNCH % "OH1L"))
        spec = d.get("spec") or {}
        cmd = spec.get("cmd") or []
        out["OH1L_leniency"] = {
            "launch_record": LAUNCH % "OH1L",
            "phase": d.get("phase"),
            "config_id": d.get("config_id"),
            "resolved_block_size_from_log": d.get("resolved_block_size_from_log"),
            "spec_pmu": spec.get("pmu"),
            "prefix_match_unit_in_cmd": ("--prefix-match-unit" in cmd),
            "prefix_match_unit_value": (cmd[cmd.index("--prefix-match-unit") + 1]
                                        if "--prefix-match-unit" in cmd else None),
            "health_status": d.get("health_status"),
            "health_wait_s": d.get("health_wait_s"),
            "models_id": (d.get("models") or {}).get("id"),
            "metrics_http_status": (d.get("metrics") or {}).get("http_status"),
            "occamy_status": (d.get("occamy") or {}).get("status"),
            "rows_in_rows_jsonl": sum(1 for r in rows if r["config_id"] == "OH1L"),
        }
    except Exception as e:
        out["OH1L_leniency"] = {"error": "unobservable: %s" % e}

    # ---------- provenance ----------
    out["configs"] = dict(collections.Counter(r["config_id"] for r in rows))
    out["models"] = {c: sorted({r["model"] for r in rows if r["config_id"] == c}) for c in configs}
    out["config_sha256"] = {c: sorted({r["config_sha256"] for r in rows if r["config_id"] == c})
                            for c in configs}
    out["prefix_match_unit_values"] = dict(collections.Counter(
        "%s|%s" % (r["config_id"], r["prefix_match_unit"]) for r in rows))
    out["usage_has_details_true"] = sum(1 for r in rows if r.get("usage_has_details") is True)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
