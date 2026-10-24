#!/usr/bin/env python3
"""Recompute every number in ``papers/context-cache/CLAIMS.md`` from the raw rows.

Usage::

    .venv/bin/python papers/context-cache/recompute.py C05

One command per claim id.  Each command reads *only* the row files under
``experiments/context-cache/cells/<UNIT>/`` (plus the two U13/U14 probe JSONs
and the U4 cell source for the static renderer check); it prints the recomputed
value next to the value printed in the paper and exits non-zero on a mismatch.
Nothing is written and no live request is made.

Two claims (C01, C16) are recomputed by the independent verifier's own scripts
``cells/CX-V2/u5_recon.py`` and ``cells/CX-V2/u4_recon.py``; their commands are
named in CLAIMS.md rather than here, because they rebuild the prompts through
the unit's own builder instead of reading a row file.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CELLS = ROOT / "experiments" / "context-cache" / "cells"


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def rows(unit: str, name: str) -> list[dict]:
    path = CELLS / unit / name
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        # Back-compat: cells written before the stack field existed are SGLang.
        if r.get("stack") is None:
            r["stack"] = "sglang"
        out.append(r)
    return out


def load(unit: str, name: str) -> dict:
    return json.loads((CELLS / unit / name).read_text(encoding="utf-8"))


def _require_config(rows_list: list[dict], unit: str, config_id: str) -> list[dict]:
    sub = [r for r in rows_list if r.get("config_id") == config_id]
    if not sub:
        raise ValueError(f"no rows for config_id={config_id!r} in unit {unit!r}")
    return sub


def gcd_all(values) -> int:
    g = 0
    for v in values:
        g = math.gcd(g, int(v))
        if g == 1:
            return 1
    return g


# --------------------------------------------------------------------------- #
# Small exact statistics
# --------------------------------------------------------------------------- #
def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p (binomial, p=1/2), matching scipy's binomtest."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2**n
    return min(1.0, 2.0 * tail)


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact Fisher two-sided p (sum of tables at most as probable as observed)."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    denom = math.comb(n, c1)

    def prob(x: int) -> float:
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / denom

    observed = prob(a)
    total = 0.0
    for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1):
        p = prob(x)
        if p <= observed * (1 + 1e-12):
            total += p
    return total


def ols(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return slope, my - slope * mx


def loglog(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Exponent, and r2 on the log-log fit."""
    lx = [math.log(v) for v in xs]
    ly = [math.log(v) for v in ys]
    n = len(lx)
    mx, my = sum(lx) / n, sum(ly) / n
    b = sum((x - mx) * (y - my) for x, y in zip(lx, ly)) / sum((x - mx) ** 2 for x in lx)
    a = my - b * mx
    pred = [a + b * x for x in lx]
    ssr = sum((y - p) ** 2 for y, p in zip(ly, pred))
    sst = sum((y - my) ** 2 for y in ly)
    return b, 1 - ssr / sst


class Lcg:
    """Same generator as cells/U4/u4_analyze.py, so the permutation p is the unit's."""

    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        self.s = (seed ^ 0x9E3779B97F4A7C15) & ((1 << 64) - 1)

    def below(self, n: int) -> int:
        self.s = (6364136223846793005 * self.s + 1442695040888963407) % (1 << 64)
        return self.s % n


def permutation_median(a: list[float], b: list[float], perms: int = 50_000) -> float:
    observed = statistics.median(a) - statistics.median(b)
    pool = list(a) + list(b)
    rng = Lcg(987654321)
    at_least = 0
    for _ in range(perms):
        idx = list(range(len(pool)))
        for i in range(len(idx) - 1, 0, -1):
            j = rng.below(i + 1)
            idx[i], idx[j] = idx[j], idx[i]
        sample_a = [pool[i] for i in idx[: len(a)]]
        sample_b = [pool[i] for i in idx[len(a):]]
        delta = statistics.median(sample_a) - statistics.median(sample_b)
        if abs(delta) >= abs(observed) - 1e-12:
            at_least += 1
    return (at_least + 1) / (perms + 1)


# --------------------------------------------------------------------------- #
# U5 — rendering identity and compaction loss
# --------------------------------------------------------------------------- #
def u5_arm(condition: str, depth: str = "deep") -> list[dict]:
    return [r for r in rows("U5", "u5_raw.jsonl") if r["depth"] == depth and r["condition"] == condition]


def c02() -> dict:
    data = rows("U5", "u5_raw.jsonl")
    return {
        "rows": len(data),
        "non_200": sum(1 for r in data if r["status"] != 200),
        "with_error": sum(1 for r in data if r["error"]),
        "cases": len({r["case_id"] for r in data}),
        "conditions": len({(r["depth"], r["condition"]) for r in data}),
    }


def c03() -> dict:
    deep = [r for r in rows("U5", "u5_raw.jsonl") if r["depth"] == "deep"]
    equal = 0
    for case_id in {r["case_id"] for r in deep}:
        pair = {r["prompt_sha256"] for r in deep if r["case_id"] == case_id and r["condition"] in ("summarise", "fork")}
        equal += 1 if len(pair) == 1 else 0
    all_rows = rows("U5", "u5_raw.jsonl")
    return {
        "deep_summarise_eq_fork_digest": equal,
        "n_deep_cases": 190,
        "distinct_digests": len({r["prompt_sha256"] for r in all_rows}),
        "n_rows": len(all_rows),
    }


def c07() -> dict:
    out = {}
    for name, cond, depth in (
        ("shallow", "shared", "shallow"),
        ("deep_baseline", "baseline", "deep"),
        ("deep_summarise", "summarise", "deep"),
        ("deep_fork", "fork", "deep"),
    ):
        rs = u5_arm(cond, depth)
        right = sum(1 for r in rs if r["correct"])
        out[f"{name}_correct"] = right
        out[f"{name}_n"] = len(rs)
        out[f"{name}_pct"] = round(100 * right / len(rs), 1)
    return out


def c08() -> dict:
    base = {r["case_id"]: bool(r["correct"]) for r in u5_arm("baseline")}
    out = {}
    for name, cond in (("summarise", "summarise"), ("fork", "fork")):
        other = {r["case_id"]: bool(r["correct"]) for r in u5_arm(cond)}
        ids = sorted(set(base) & set(other))
        b = sum(1 for i in ids if base[i] and not other[i])
        c = sum(1 for i in ids if other[i] and not base[i])
        out[f"{name}_discordant_b"] = b
        out[f"{name}_discordant_c"] = c
        out[f"{name}_mcnemar_p"] = mcnemar_exact(b, c)
    summ = {r["case_id"]: bool(r["correct"]) for r in u5_arm("summarise")}
    fork = {r["case_id"]: bool(r["correct"]) for r in u5_arm("fork")}
    ids = sorted(set(summ) & set(fork))
    b = sum(1 for i in ids if summ[i] and not fork[i])
    c = sum(1 for i in ids if fork[i] and not summ[i])
    out["summarise_vs_fork_discordant_b"] = b
    out["summarise_vs_fork_discordant_c"] = c
    out["summarise_vs_fork_mcnemar_p"] = mcnemar_exact(b, c)
    out["max_delta_pts"] = round(
        100 * max(
            abs(sum(1 for r in u5_arm(k) if r["correct"]) - sum(1 for r in u5_arm("baseline") if r["correct"])) / 190
            for k in ("summarise", "fork")
        ),
        3,
    )
    return out


def c09() -> dict:
    out = {}
    for name, cond in (("baseline", "baseline"), ("summarise", "summarise"), ("fork", "fork")):
        rs = u5_arm(cond)
        for flag in ("gold", "question", "options"):
            out[f"{name}_{flag}"] = sum(1 for r in rs if r["retained"][flag])
        out[f"{name}_n"] = len(rs)
    rs = u5_arm("shared", "shallow")
    out["shallow_gold"] = sum(1 for r in rs if r["retained"]["gold"])
    out["shallow_question"] = sum(1 for r in rs if r["retained"]["question"])
    out["shallow_options"] = sum(1 for r in rs if r["retained"]["options"])
    return out


def _agree(a: dict[str, str], b: dict[str, str]) -> tuple[int, int]:
    ids = sorted(set(a) & set(b))
    return sum(1 for i in ids if a[i] == b[i]), len(ids)


def c10() -> dict:
    base = {r["case_id"]: r["parsed_letter"] for r in u5_arm("baseline")}
    summ = {r["case_id"]: r["parsed_letter"] for r in u5_arm("summarise")}
    fork = {r["case_id"]: r["parsed_letter"] for r in u5_arm("fork")}
    out = {}
    for name, x, y in (("baseline_vs_summarise", base, summ), ("fork_vs_baseline", fork, base), ("summarise_vs_fork", summ, fork)):
        same, n = _agree(x, y)
        out[f"{name}_agreed"] = same
        out[f"{name}_n"] = n
        out[f"{name}_pct"] = round(100 * same / n, 1)
    return out


# --------------------------------------------------------------------------- #
# U4b — fan-out placement
# --------------------------------------------------------------------------- #
def c04() -> dict:
    rs = rows("U4b", "rows.jsonl")
    out = {}
    for arm in "ABC":
        sub = sorted((r for r in rs if r["arm"] == arm), key=lambda r: r["branch"])
        out[f"{arm}_n"] = len(sub)
        out[f"{arm}_prompt"] = sum(r["prompt_tokens"] for r in sub)
        out[f"{arm}_uncached"] = sum(r["uncached_tokens"] for r in sub)
        out[f"{arm}_cached_by_branch"] = [r["cached_tokens"] for r in sub]
        out[f"{arm}_uncached_by_branch"] = [r["uncached_tokens"] for r in sub]
        out[f"{arm}_per_branch_prompt"] = sub[0]["prompt_tokens"]
    return out


def c05() -> dict:
    rs = rows("U4b", "rows.jsonl")
    a = sum(r["uncached_tokens"] for r in rs if r["arm"] == "A")
    b = sum(r["uncached_tokens"] for r in rs if r["arm"] == "B")
    c = sum(r["uncached_tokens"] for r in rs if r["arm"] == "C")
    return {"B_over_A": b / a, "C_over_A": c / a, "requests": len(rs)}


def c06() -> dict:
    rs = sorted((r for r in rows("U4b", "rows.jsonl") if r["arm"] == "A"), key=lambda r: r["branch"])
    warm = rs[1:]  # branches 2..8
    hits = [r for r in warm if r["cached_tokens"] > 0]
    a_total = sum(r["uncached_tokens"] for r in rs)
    b_total = sum(r["uncached_tokens"] for r in rows("U4b", "rows.jsonl") if r["arm"] == "B")
    # race-free counterfactual: branch 2 would cost one delta instead of a full cold prompt
    fixed = a_total - warm[0]["uncached_tokens"] + min(r["uncached_tokens"] for r in warm if r["cached_tokens"] > 0)
    return {
        "warm_branches": len(warm),
        "warm_hits": len(hits),
        "hit_cached_tokens": sorted({r["cached_tokens"] for r in hits}),
        "branch2_cached": warm[0]["cached_tokens"],
        "counterfactual_A_uncached": fixed,
        "counterfactual_B_over_A": b_total / fixed,
    }


# --------------------------------------------------------------------------- #
# U4 — the invalidated comparison
# --------------------------------------------------------------------------- #
def _u4_break_costs() -> list[tuple[str, int, float, float, int, int]]:
    u4 = rows("U4", "u4_rows.jsonl")
    events = rows("U4", "u4_events.jsonl")
    index: dict[str, dict[int, dict]] = defaultdict(dict)
    for r in u4:
        if r["rep"] == 1:
            index[r["cell"]][r["turn"]] = r
    keyed: dict[tuple[str, int], dict[str, tuple]] = defaultdict(dict)
    for e in events:
        r = index[e["cell"]].get(e["turn"])
        if r is None:
            continue
        cost = r["uncached"] - (r["prompt_tokens"] % 64)
        keyed[(e["session"], e["turn"])][e["compaction"]] = (cost, r["prompt_tokens"], r["uncached"], r["cached_tokens"])
    return [(s, t, d["fork"][0], d["summarise_in_place"][0], d["fork"][1], d["summarise_in_place"][1])
            for (s, t), d in sorted(keyed.items()) if "fork" in d and "summarise_in_place" in d]


def c11() -> dict:
    pairs = _u4_break_costs()
    deltas = [f - s for _, _, f, s, _, _ in pairs]
    fork = [f for _, _, f, _, _, _ in pairs]
    summ = [s for _, _, _, s, _, _ in pairs]
    return {
        "n_pairs": len(pairs),
        "n_zero": sum(1 for d in deltas if d == 0),
        "median": statistics.median(deltas),
        "max_abs": max(abs(d) for d in deltas),
        "permutation_p": permutation_median(fork, summ),
    }


def c12() -> dict:
    pairs = _u4_break_costs()
    out = {"nonzero": []}
    for session, turn, f, s, fp, sp in pairs:
        if f != s:
            out["nonzero"].append([session, turn, f - s, fp, sp])
    out["n_nonzero"] = len(out["nonzero"])
    return out


def c13() -> dict:
    src = (CELLS / "U4" / "u4_cell.py").read_text(encoding="utf-8")
    render = None
    for line in src.splitlines():
        if line.startswith("RENDER") and "=" in line:
            raw = line.split("=", 1)[1].split("#", 1)[0].strip()
            render = raw.rsplit(".", 1)[-1].lower()
    return {
        "RENDER": render,
        "POINTER_FORK_in_source": "POINTER_FORK" in src,
        "uses_single_renderer": render is not None,
    }


def c14() -> dict:
    data = rows("U4", "u4_rows.jsonl")
    events = rows("U4", "u4_events.jsonl")
    runlog = load("U4", "u4_runlog.json")
    probe = load("U4", "u4_grid_probe.json")["requests"]
    probe_append = load("U4", "u4_grid_probe_append.json")["requests"]
    return {
        "rows": len(data),
        "events": len(events),
        "events_summarise": sum(1 for e in events if e["compaction"] == "summarise_in_place"),
        "events_fork": sum(1 for e in events if e["compaction"] == "fork"),
        "events_sliding": sum(1 for e in events if e["compaction"] == "sliding_window"),
        "sessions": len({e["session"] for e in events}),
        "batch_requests": runlog.get("requests"),
        "probe_requests": probe + probe_append,
        "logged_requests": runlog.get("requests") + probe + probe_append,
    }


def c15() -> dict:
    d = load("U13", "u13_fork_marker.json")
    naive = d["prompts"]["naive_append"]
    marker, _, summary = d["fork_root_text"].partition("\n\n")
    return {
        "fork_sha8": naive["sha256_fork"][:8],
        "summarise_sha8": naive["sha256_summarise"][:8],
        "legacy_fork_sha8": naive["sha256_legacy_fork"][:8],
        "legacy_fork_equals_summarise": naive["sha256_legacy_fork"] == naive["sha256_summarise"],
        "fork_differs": naive["sha256_fork"] != naive["sha256_summarise"],
        "prompt_chars_fork": naive["prompt_chars_fork"],
        "prompt_chars_summarise": naive["prompt_chars_summarise"],
        "delta_chars": naive["prompt_chars_fork"] - naive["prompt_chars_summarise"],
        "marker_first_line_chars": len(marker),
        "est_tokens": round((naive["prompt_chars_fork"] - naive["prompt_chars_summarise"]) / 4),
        "suffix_is_bare_summary": summary == d["summarise_root_text"],
    }


# --------------------------------------------------------------------------- #
# U15 — the four-arm cell
# --------------------------------------------------------------------------- #
def _arms() -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows("U15", "rows.jsonl"):
        by[r["arm"]].append(r)
    return {a: sorted(rs, key=lambda r: r["turn"]) for a, rs in by.items()}


def _arm_totals(arm: str) -> dict:
    rs = _arms()[arm]
    prompt = sum(r["prompt_tokens"] for r in rs)
    cached = sum(r["cached_tokens"] for r in rs)
    return {
        "prompt": prompt,
        "cached": cached,
        "uncached": prompt - cached,
        "hit_rate": round(cached / prompt, 4),
        "n": len(rs),
    }


def c17() -> dict:
    return {f"R_{k}": v for k, v in _arm_totals("R").items()}


def c18() -> dict:
    return {f"F_{k}": v for k, v in _arm_totals("F").items()}


def c19() -> dict:
    return {f"A_{k}": v for k, v in _arm_totals("A").items()}


def c20() -> dict:
    return {f"C_{k}": v for k, v in _arm_totals("C").items()}


def c21() -> dict:
    t = {a: _arm_totals(a)["uncached"] for a in "RFAC"}
    return {
        "R_over_A": t["R"] / t["A"],
        "R_over_F": t["R"] / t["F"],
        "F_over_A": t["F"] / t["A"],
        "passes_1p5": (t["R"] / t["A"]) >= 1.5,
        "R_F_gap_pct": round(100 * (t["R"] / t["F"] - 1), 2),
    }


def c22() -> dict:
    arms = _arms()
    control = {r["turn"]: r for r in arms["C"]}
    net = 0
    for turn in (18, 35):
        r = next(x for x in arms["R"] if x["turn"] == turn)
        net += r["uncached"] - control[turn]["uncached"]
    gap = _arm_totals("R")["uncached"] - _arm_totals("C")["uncached"]
    return {
        "break_net_total": net,
        "gap": gap,
        "break_share": round(net / gap, 4),
        "steady_state": gap - net,
        "steady_share": round((gap - net) / gap, 4),
    }


def c23() -> dict:
    arms = _arms()
    out = {}
    for a in "RC":
        rs = [r for r in arms[a] if 19 <= r["turn"] <= 34]
        out[f"{a}_mean_uncached"] = statistics.mean(r["uncached"] for r in rs)
        out[f"{a}_mean_prompt"] = statistics.mean(r["prompt_tokens"] for r in rs)
    return out


def c24() -> dict:
    arms = _arms()
    control = _arm_totals("C")["uncached"]
    net = c22()["break_net_total"]
    counterfactual = control + net
    return {
        "counterfactual_R": counterfactual,
        "R_over_counterfactual_A": counterfactual / _arm_totals("A")["uncached"],
    }


def c25() -> dict:
    arms = _arms()
    a = arms["A"]
    return {
        "A_first_prompt": a[0]["prompt_tokens"],
        "A_last_prompt": a[-1]["prompt_tokens"],
        "A_growth": a[-1]["prompt_tokens"] - a[0]["prompt_tokens"],
        "A_growth_factor": round(a[-1]["prompt_tokens"] / a[0]["prompt_tokens"], 4),
        "A_total_prompt": _arm_totals("A")["prompt"],
        "C_total_prompt": _arm_totals("C")["prompt"],
        "A_extra_prompt_vs_C": _arm_totals("A")["prompt"] - _arm_totals("C")["prompt"],
        "R_last_prompt": arms["R"][-1]["prompt_tokens"],
    }


def c26() -> dict:
    arms = _arms()
    out = {}
    for a in "RFAC":
        out[f"{a}_breaks"] = [r["turn"] for i, r in enumerate(arms[a][1:], 1) if r["cached_tokens"] < arms[a][i - 1]["cached_tokens"]]
    return out


# --------------------------------------------------------------------------- #
# U9 — latency
# --------------------------------------------------------------------------- #
U9_LENGTHS = (1024, 2048, 4096, 8192, 16384, 32768)


def _u9_pairs() -> list[tuple[int, int, dict, dict]]:
    trials = rows("U9", "u9_trials.jsonl")

    def last(role: str, length: int, rep: int) -> dict | None:
        sub = [r for r in trials if r["length_target"] == length and r["role"] == role and r["rep"] == rep]
        return sub[-1] if sub else None

    out = []
    for length in U9_LENGTHS:
        reps = sorted({r["rep"] for r in trials if r["length_target"] == length and r["role"] == "miss" and r["rep"] >= 0})
        for rep in reps:
            miss, hit = last("miss", length, rep), last("hit", length, rep)
            if miss and hit:
                out.append((length, rep, miss, hit))
    return out


def _u9_table() -> dict:
    pairs = _u9_pairs()
    out = {}
    for length in U9_LENGTHS:
        sub = [p for p in pairs if p[0] == length]
        miss = statistics.median([p[2]["ttft_ms"] for p in sub])
        hit = statistics.median([p[3]["ttft_ms"] for p in sub])
        out[length] = {
            "reps": len(sub),
            "prompt_tokens": statistics.median([p[2]["prompt_tokens"] for p in sub]),
            "miss_ttft": round(miss, 1),
            "hit_ttft": round(hit, 1),
            "hit_over_miss": round(hit / miss, 4),
            "delta": round(statistics.median([p[2]["ttft_ms"] - p[3]["ttft_ms"] for p in sub]), 1),
        }
    return out


def c27() -> dict:
    t = _u9_table()[1024]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c28() -> dict:
    t = _u9_table()[2048]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c29() -> dict:
    t = _u9_table()[4096]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c30() -> dict:
    t = _u9_table()[8192]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c31() -> dict:
    t = _u9_table()[16384]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c32() -> dict:
    t = _u9_table()[32768]
    return {"miss": t["miss_ttft"], "hit": t["hit_ttft"], "ratio": t["hit_over_miss"], "delta": t["delta"]}


def c33() -> dict:
    table = _u9_table()
    xs = [table[k]["prompt_tokens"] for k in U9_LENGTHS]
    miss = [table[k]["miss_ttft"] for k in U9_LENGTHS]
    hit = [table[k]["hit_ttft"] for k in U9_LENGTHS]
    ratio = [table[k]["hit_over_miss"] for k in U9_LENGTHS]
    bm, rm = loglog(xs, miss)
    bh, rh = loglog(xs, hit)
    br, rr = loglog(xs, ratio)
    return {
        "miss_exponent": round(bm, 4),
        "miss_r2": round(rm, 4),
        "hit_exponent": round(bh, 4),
        "hit_r2": round(rh, 4),
        "ratio_exponent": round(br, 4),
        "ratio_r2": round(rr, 4),
    }


def c34() -> dict:
    table = _u9_table()
    xs = [table[k]["prompt_tokens"] for k in U9_LENGTHS]
    miss_slope, _ = ols(xs, [table[k]["miss_ttft"] for k in U9_LENGTHS])
    hit_slope, _ = ols(xs, [table[k]["hit_ttft"] for k in U9_LENGTHS])
    return {
        "miss_ms_per_token": round(miss_slope, 6),
        "hit_ms_per_token": round(hit_slope, 6),
        "ratio": round(miss_slope / hit_slope, 2),
        "hit_us_per_token": round(hit_slope * 1000, 2),
    }


def c35() -> dict:
    pairs = _u9_pairs()
    deltas = [p[2]["ttft_ms"] - p[3]["ttft_ms"] for p in pairs]
    per_length = len(deltas) // len(U9_LENGTHS)  # 7 reps per length: the test is per length
    return {
        "n_pairs": len(deltas),
        "n_positive": sum(1 for d in deltas if d > 0),
        "reps_per_length": per_length,
        "sign_p_one_sided": 1 / 2 ** per_length,
        "sign_p_two_sided": 2 / 2 ** per_length,
    }


def c36() -> dict:
    trials = rows("U9", "u9_trials.jsonl")
    roles = Counter(r["role"] for r in trials)
    return {
        "rows": len(trials),
        "requests": len(trials),
        "non_200": sum(1 for r in trials if r["status"] != 200),
        "lengths_resolved": len({r["length_target"] for r in trials if r["role"] == "hit"}),
        "calibration": roles["calibration"],
        "prime": roles["prime"],
        "noise_hit": roles["noise_hit"],
        "noise_cold": roles["noise_cold"],
    }


# --------------------------------------------------------------------------- #
# Grid law
# --------------------------------------------------------------------------- #
def c37() -> dict:
    warm = [r for r in rows("U2", "u2_cache_rows.jsonl") if r["arm"] == "warm"]
    cold = [r for r in rows("U2", "u2_cache_rows.jsonl") if r["arm"] == "cold"]
    return {
        "warm": len(warm),
        "cached_eq_law": sum(1 for r in warm if r["cached_tokens"] == 64 * ((r["prompt_tokens"] - 1) // 64)),
        "uncached_residual_zero": sum(1 for r in warm if r["uncached"] == r["prompt_tokens"] % 64),
        "min_len": min(r["prompt_tokens"] for r in warm),
        "max_len": max(r["prompt_tokens"] for r in warm),
        "n_residue_zero": sum(1 for r in warm if r["prompt_tokens"] % 64 == 0),
        "cold_cached_nonzero": sum(1 for r in cold if r["cached_tokens"] != 0),
    }


def c38() -> dict:
    u4 = rows("U4", "u4_rows.jsonl")
    events = {(e["cell"], e["turn"]) for e in rows("U4", "u4_events.jsonl")}
    warm = [r for r in u4 if r["turn"] >= 2 and r["rep"] == 1 and (r["cell"], r["turn"]) not in events]
    residual = [r["uncached"] - (r["prompt_tokens"] % 64) for r in warm]
    return {
        "warm_appends": len(warm),
        "deviating": sum(1 for v in residual if v != 0),
        "min_residual": min(residual),
        "max_residual": max(residual),
        "median_residual": statistics.median(residual),
        "n_buckets": len(set(residual)),
        "min_prompt": min(r["prompt_tokens"] for r in warm),
        "max_prompt": max(r["prompt_tokens"] for r in warm),
    }


def c39() -> dict:
    u2 = rows("U2", "u2_cache_rows.jsonl")
    u4 = rows("U4", "u4_rows.jsonl")
    return {
        "shared_rows": len({(r["case_id"], r["salt"]) for r in u2} & {(r["case_id"], r["salt"]) for r in u4}),
        "u2_min": min(r["prompt_tokens"] for r in u2),
        "u2_max": max(r["prompt_tokens"] for r in u2),
        "u4_min": min(r["prompt_tokens"] for r in u4),
        "u4_max": max(r["prompt_tokens"] for r in u4),
    }


# --------------------------------------------------------------------------- #
# U10 — the 64-boundary first-repeat miss
# --------------------------------------------------------------------------- #
def _u10() -> list[dict]:
    return rows("U10", "u10_rows.jsonl") + rows("U10", "u10_rows_p23.jsonl")


def c40() -> dict:
    data = _u10()
    out = {}
    for length in (1008, 1023, 1024, 1025, 1088):
        rep1 = [r for r in data if r["length_target"] == length and r["role"] == "rep1" and r["phase"] == "p1"]
        out[f"L{length}_n"] = len(rep1)
        out[f"L{length}_misses"] = sum(1 for r in rep1 if r["cached_tokens"] == 0)
        out[f"L{length}_cached"] = sorted({r["cached_tokens"] for r in rep1})
    miss_ttft = [r["ttft_ms"] for r in data
                 if r["length_target"] == 1024 and r["role"] == "rep1" and r["cached_tokens"] == 0]
    out["miss_ttft_ms_1024_median"] = round(statistics.median(miss_ttft), 1)
    rep2 = [r for r in data if r["role"] == "rep2"]
    out["rep2_n"] = len(rep2)
    out["rep2_law_match"] = sum(1 for r in rep2 if r["cached_tokens"] == 64 * ((r["prompt_tokens"] - 1) // 64))
    return out


def c41() -> dict:
    data = _u10()
    p1 = [r for r in data if r["phase"] == "p1" and r["role"] == "rep1"]
    mult = [r for r in p1 if r["length_target"] % 64 == 0]
    non = [r for r in p1 if r["length_target"] % 64 != 0]
    every = [r for r in data if r["role"] == "rep1" and r["length_target"]]
    m2 = [r for r in every if r["length_target"] % 64 == 0]
    n2 = [r for r in every if r["length_target"] % 64 != 0]
    return {
        "p1_multiple_misses": sum(1 for r in mult if r["cached_tokens"] == 0),
        "p1_multiple_n": len(mult),
        "p1_nonmultiple_misses": sum(1 for r in non if r["cached_tokens"] == 0),
        "p1_nonmultiple_n": len(non),
        "fisher_p": fisher_two_sided(len(mult), 0, 0, len(non)),
        "fisher_p_recip_comb": 1 / math.comb(25, 10),
        "pooled_multiple_misses": sum(1 for r in m2 if r["cached_tokens"] == 0),
        "pooled_multiple_n": len(m2),
        "pooled_nonmultiple_misses": sum(1 for r in n2 if r["cached_tokens"] == 0),
        "pooled_nonmultiple_n": len(n2),
        "pooled_fisher_p": fisher_two_sided(len(m2), 0, 0, len(n2)),
    }


def c42() -> dict:
    data = _u10()
    delay = [r for r in data if r["phase"] == "p2" and r["role"] == "rep1"]
    insert = [r for r in data if r["phase"] == "p3" and r["role"] == "rep1"]
    return {
        "delay_n": len(delay),
        "delay_misses": sum(1 for r in delay if r["cached_tokens"] == 0),
        "delay_values": sorted({r["delay_s"] for r in delay}),
        "insert_n": len(insert),
        "insert_misses": sum(1 for r in insert if r["cached_tokens"] == 0),
    }


def c43() -> dict:
    data = _u10()
    cold = [r for r in data if r["role"] == "cold"]
    return {"cold_n": len(cold), "cold_nonzero": sum(1 for r in cold if r["cached_tokens"] != 0)}


def c44() -> dict:
    """G1 decomposition of U15's 1.700x into break cost vs post-compaction window truncation."""
    a = load("G1", "analysis.json")
    rs = rows("G1", "rows.jsonl")
    comp = a["comparison"]
    pb = a["per_break_uncached_cost"]
    rows_path = CELLS / "G1" / "rows.jsonl"
    sha = hashlib.sha256(rows_path.read_bytes()).hexdigest()
    return {
        "n_rows": len(rs),
        "n_rows_E": sum(1 for r in rs if r["arm"] == "E"),
        "n_rows_F": sum(1 for r in rs if r["arm"] == "F"),
        "n_events": pb["n_events"],
        "n_events_within_10pct": pb["n_events_within_10pct"],
        "all_events_within_10pct": pb["all_events_within_10pct"],
        "u15_1_700x_survives_decomposition": a["u15_1_700x_survives_decomposition"],
        "mean_break_cost_gross_E": pb["mean_break_cost_gross_E"],
        "mean_break_cost_gross_F": pb["mean_break_cost_gross_F"],
        "ratio_mean_break_cost_E_over_F": pb["ratio_mean_break_cost_E_over_F"],
        "ratio_total_uncached_E_over_F": comp["ratio_total_uncached_E_over_F"],
        "rows_sha256": sha,
    }


# --------------------------------------------------------------------------- #
# Cross-stack claims (X-SYNTH) — cache-hit granularity across serving stacks
# --------------------------------------------------------------------------- #
def c45() -> dict:
    rs = rows("WIN-SGL", "rows.jsonl")
    _require_config(rs, "WIN-SGL", "S1")
    _require_config(rs, "WIN-SGL", "S2")
    sha = hashlib.sha256((CELLS / "WIN-SGL" / "rows.jsonl").read_bytes()).hexdigest()
    return {
        "rows_total": len(rs),
        "rows_S1": sum(1 for r in rs if r["config_id"] == "S1"),
        "rows_S2": sum(1 for r in rs if r["config_id"] == "S2"),
        "status_200_total": sum(1 for r in rs if r.get("status") == 200),
        "status_200_S1": sum(1 for r in rs if r["config_id"] == "S1" and r.get("status") == 200),
        "status_200_S2": sum(1 for r in rs if r["config_id"] == "S2" and r.get("status") == 200),
        "rows_sha256": sha,
    }


def c46() -> dict:
    ws = rows("WIN-SGL", "rows.jsonl")
    s1 = _require_config(ws, "WIN-SGL", "S1")
    s2 = _require_config(ws, "WIN-SGL", "S2")

    def battery(sub):
        b = [r for r in sub if r.get("phase") == "battery" and r.get("status") == 200 and r.get("prompt_tokens")]
        prompt = sum(r["prompt_tokens"] for r in b)
        cached = sum(r["cached_tokens"] for r in b)
        uncached = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in b)
        per_depth = {}
        for depth in ("32k", "64k"):
            dd = [r for r in b if r.get("depth") == depth]
            u = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in dd)
            per_depth[depth] = round(u / len(dd), 2) if dd else None
        return {
            "n_battery": len(b),
            "hit_fraction": round(cached / prompt, 6),
            "mean_uncached_per_turn": round(uncached / len(b), 1),
            "mean_uncached_32k": per_depth["32k"],
            "mean_uncached_64k": per_depth["64k"],
        }

    def grid(sub):
        steady = [r for r in sub if r.get("phase") == "battery" and r.get("cached_tokens", 0) > 0
                  and r.get("turn", 0) > 1 and not r.get("scheduled_compaction")]
        return {
            "steady_n": len(steady),
            "gcd_cached": gcd_all(r["cached_tokens"] for r in steady),
            "odd64": sum(1 for r in steady if r["cached_tokens"] % 128 == 64),
        }

    m1, m2 = battery(s1), battery(s2)
    g1, g2 = grid(s1), grid(s2)
    return {
        "S1_n_battery": m1["n_battery"],
        "S1_hit_fraction": m1["hit_fraction"],
        "S1_mean_uncached_per_turn": m1["mean_uncached_per_turn"],
        "S1_mean_uncached_32k": m1["mean_uncached_32k"],
        "S1_mean_uncached_64k": m1["mean_uncached_64k"],
        "S1_steady_n": g1["steady_n"],
        "S1_gcd_cached": g1["gcd_cached"],
        "S1_odd64": g1["odd64"],
        "S2_n_battery": m2["n_battery"],
        "S2_hit_fraction": m2["hit_fraction"],
        "S2_mean_uncached_per_turn": m2["mean_uncached_per_turn"],
        "S2_mean_uncached_32k": m2["mean_uncached_32k"],
        "S2_mean_uncached_64k": m2["mean_uncached_64k"],
        "S2_steady_n": g2["steady_n"],
        "S2_gcd_cached": g2["gcd_cached"],
        "S2_odd64": g2["odd64"],
    }


def c47() -> dict:
    rs = rows("G3", "rows.jsonl")
    sub = _require_config(rs, "G3", "S0")
    b = [r for r in sub if r.get("status") == 200 and r.get("prompt_tokens")]
    prompt = sum(r["prompt_tokens"] for r in b)
    cached = sum(r["cached_tokens"] for r in b)
    uncached = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in b)
    per_depth = {}
    for depth in ("32k", "64k"):
        dd = [r for r in b if r.get("depth") == depth]
        u = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in dd)
        per_depth[depth] = round(u / len(dd), 2) if dd else None
    steady = [r for r in sub if r.get("cached_tokens", 0) > 0 and r.get("turn", 0) > 1
              and not r.get("scheduled_compaction")]
    return {
        "rows_total": len(sub),
        "status_200": sum(1 for r in sub if r.get("status") == 200),
        "hit_fraction": round(cached / prompt, 6),
        "mean_uncached_per_turn": round(uncached / len(b), 1),
        "mean_uncached_32k": per_depth["32k"],
        "mean_uncached_64k": per_depth["64k"],
        "steady_n": len(steady),
        "gcd_cached": gcd_all(r["cached_tokens"] for r in steady),
        "odd64": sum(1 for r in steady if r["cached_tokens"] % 128 == 64),
        "rows_sha256": hashlib.sha256((CELLS / "G3" / "rows.jsonl").read_bytes()).hexdigest(),
    }


def c48() -> dict:
    rs = rows("WIN-VLLM", "rows.jsonl")
    for cfg in ("V1", "V2", "V3"):
        _require_config(rs, "WIN-VLLM", cfg)
    sha = hashlib.sha256((CELLS / "WIN-VLLM" / "rows.jsonl").read_bytes()).hexdigest()
    return {
        "rows_total": len(rs),
        "status_200_total": sum(1 for r in rs if r.get("status") == 200),
        "rows_V1": sum(1 for r in rs if r["config_id"] == "V1"),
        "rows_V2": sum(1 for r in rs if r["config_id"] == "V2"),
        "rows_V3": sum(1 for r in rs if r["config_id"] == "V3"),
        "status_200_V1": sum(1 for r in rs if r["config_id"] == "V1" and r.get("status") == 200),
        "status_200_V2": sum(1 for r in rs if r["config_id"] == "V2" and r.get("status") == 200),
        "status_200_V3": sum(1 for r in rs if r["config_id"] == "V3" and r.get("status") == 200),
        "rows_sha256": sha,
    }


def c49() -> dict:
    rs = rows("WIN-VLLM", "rows.jsonl")
    for cfg in ("V1", "V2", "V3"):
        _require_config(rs, "WIN-VLLM", cfg)
    out = {}
    for cfg, g in (("V1", 1088), ("V2", 1056), ("V3", 2096)):
        sub = [r for r in rs if r["config_id"] == cfg and r.get("phase") == "grid"]
        cached = [r["cached_tokens"] for r in sub]
        exact = sum(1 for r in sub if g * ((r["prompt_tokens"] - 1) // g) == r["cached_tokens"])
        out[f"{cfg}_grid_rows"] = len(sub)
        out[f"{cfg}_distinct_L"] = len(set(r["prompt_tokens"] for r in sub))
        out[f"{cfg}_gcd_cached"] = gcd_all(cached)
        out[f"{cfg}_law_exact"] = exact
    return out


def c50() -> dict:
    rs = rows("WIN-VLLM", "rows.jsonl")
    for cfg in ("V1", "V2"):
        _require_config(rs, "WIN-VLLM", cfg)
    out = {}
    for cfg in ("V1", "V2"):
        sub = [r for r in rs if r["config_id"] == cfg and r.get("phase") == "battery"
               and r.get("status") == 200 and r.get("prompt_tokens")]
        prompt = sum(r["prompt_tokens"] for r in sub)
        cached = sum(r["cached_tokens"] for r in sub)
        uncached = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in sub)
        out[f"{cfg}_n_battery"] = len(sub)
        out[f"{cfg}_hit_fraction"] = round(cached / prompt, 6)
        out[f"{cfg}_mean_uncached_per_turn"] = round(uncached / len(sub), 1)
    return out


def c51() -> dict:
    g3 = rows("G3", "rows.jsonl")
    _require_config(g3, "G3", "S0")
    s0_32k = [r for r in g3 if r.get("depth") == "32k" and r.get("status") == 200]
    s0_unc = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in s0_32k) / len(s0_32k)
    s0_prompt = sum(r["prompt_tokens"] for r in g3 if r.get("status") == 200)
    s0_cached = sum(r["cached_tokens"] for r in g3 if r.get("status") == 200)
    wv = rows("WIN-VLLM", "rows.jsonl")
    _require_config(wv, "WIN-VLLM", "V1")
    v1 = [r for r in wv if r["config_id"] == "V1" and r.get("phase") == "battery"
          and r.get("status") == 200 and r.get("prompt_tokens")]
    v1_unc = sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in v1) / len(v1)
    v1_prompt = sum(r["prompt_tokens"] for r in v1)
    v1_cached = sum(r["cached_tokens"] for r in v1)
    return {
        "S0_32k_mean_uncached": round(s0_unc, 2),
        "S0_hit_fraction": round(s0_cached / s0_prompt, 6),
        "V1_mean_uncached_per_turn": round(v1_unc, 1),
        "V1_hit_fraction": round(v1_cached / v1_prompt, 6),
        "ratio_V1_over_S0_32k": round(v1_unc / s0_unc, 3),
    }


def c52() -> dict:
    rs = rows("TUNED", "rows.jsonl")
    _require_config(rs, "TUNED", "TUNED")
    rp = [r for r in rs if r.get("phase") == "R"]
    cached = [r["cached_tokens"] for r in rp]
    exact = sum(1 for r in rp if 64 * ((r["prompt_tokens"] - 1) // 64) == r["cached_tokens"])
    return {
        "rows_total": len(rs),
        "rows_phase_P": sum(1 for r in rs if r.get("phase") == "P"),
        "rows_phase_R": len(rp),
        "status_200_total": sum(1 for r in rs if r.get("status") == 200),
        "grid_gcd_cached": gcd_all(cached),
        "grid_exact_64_minus1": exact,
        "grid_odd64": sum(1 for r in rp if r["cached_tokens"] % 128 == 64),
        "variant": sorted(set(r.get("variant") for r in rs))[0],
        "radix_policy": sorted(set(r.get("radix_eviction_policy") for r in rs))[0],
        "rows_sha256": hashlib.sha256((CELLS / "TUNED" / "rows.jsonl").read_bytes()).hexdigest(),
    }


# --------------------------------------------------------------------------- #
# Cross-stack grid laws, whole-cell form (X-SYNTH, second pass)
#
# Each stack's grid unit is measured over EVERY row of a cell that carries a
# non-zero cached count, not over a phase-filtered steady subset: the unit is
# the gcd of cached_tokens over the hot rows, and the "unit holds" test is
# "every hot row is an exact multiple of that unit".  Both directions are
# checked for vLLM (1056 fails against V1's rows, 1088 against V2's), which is
# what makes the 1088/1056/2096 triple an identification and not a fit.
#
# These functions fail loudly (``main`` exits non-zero): a claim whose
# ``config_id`` has no rows in any cell raises ``KeyError`` instead of
# silently reporting a zero.  A row with no ``stack`` field is SGLang
# (``rows()`` back-fills it), so every cell written before the field existed
# still recomputes.
# --------------------------------------------------------------------------- #
GRID_CELLS = {
    # config_id -> (cell, unit the rows must exhibit, phase filter or None)
    "S0": ("G3", 64, None),
    "S1": ("WIN-SGL", 64, "battery"),
    "S2": ("WIN-SGL", 128, "battery"),
    "V1": ("WIN-VLLM", 1088, "battery"),
    "V2": ("WIN-VLLM", 1056, "battery"),
    "V3": ("WIN-VLLM", 2096, None),
    "TUNED": ("TUNED", 64, None),
}


def _config_rows(cell: str, config_id: str, phase: str | None = None) -> list[dict]:
    """Rows of one config in one cell.  Loud on absence, never a silent empty list."""
    rs = rows(cell, "rows.jsonl")
    sub = [r for r in rs if r.get("config_id") == config_id]
    if not sub:
        present = sorted({r.get("config_id") for r in rs})
        raise KeyError(f"claim cites config_id={config_id!r} but cell {cell!r} has no such rows "
                       f"(config_ids present: {present})")
    if phase is not None:
        sub = [r for r in sub if r.get("phase") == phase]
        if not sub:
            raise KeyError(f"config_id={config_id!r} in cell {cell!r} has no rows in phase {phase!r}")
    return sub


def _ok(sub: list[dict]) -> list[dict]:
    return [r for r in sub if r.get("status") == 200 and r.get("prompt_tokens")]


def _unit_stats(sub: list[dict]) -> dict:
    hot = [r for r in _ok(sub) if int(r.get("cached_tokens") or 0) > 0]
    cached = [int(r["cached_tokens"]) for r in hot]
    unit = gcd_all(cached) if cached else 0
    return {
        "hot": len(hot),
        "gcd_cached": unit,
        "hot_multiple_of_unit": sum(1 for c in cached if unit and c % unit == 0),
        "odd_unit": sum(1 for c in cached if unit and c % (2 * unit) == unit),
    }


def _step_gcd(sub: list[dict]) -> int:
    """gcd of the successive cached deltas of the hot rows (positive or negative)."""
    ok = sorted(_ok(sub), key=lambda r: (r.get("turn") or 0, r.get("arm") or "",
                                         r.get("rep") or 0, r.get("request_index") or 0))
    vals = [int(r["cached_tokens"]) for r in ok if int(r.get("cached_tokens") or 0) > 0]
    steps = [b - a for a, b in zip(vals, vals[1:]) if b != a]
    return gcd_all(abs(s) for s in steps) if steps else 0


def c55() -> dict:
    """The grid unit per stack, and whether that unit holds on every hot row."""
    out = {}
    for cfg, (cell, _unit, _phase) in GRID_CELLS.items():
        s = _unit_stats(_config_rows(cell, cfg))
        out[f"{cfg}_gcd_cached"] = s["gcd_cached"]
        out[f"{cfg}_hot_multiple_of_unit"] = s["hot_multiple_of_unit"]
        out[f"{cfg}_hot_n"] = s["hot"]
    return out


def c56() -> dict:
    """vLLM: the unit is identified, not fitted — 1088 fails on V2, 1056 on V1."""
    def hot(cfg, phase):
        return [int(r["cached_tokens"]) for r in _ok(_config_rows("WIN-VLLM", cfg, phase))
                if int(r.get("cached_tokens") or 0) > 0]
    v1, v2, v3 = hot("V1", "battery"), hot("V2", "battery"), hot("V3", None)
    return {
        "V1_hot_vs_1056": sum(1 for c in v1 if c % 1056 == 0),
        "V1_hot_vs_1088": sum(1 for c in v1 if c % 1088 == 0),
        "V2_hot_vs_1088": sum(1 for c in v2 if c % 1088 == 0),
        "V2_hot_vs_1056": sum(1 for c in v2 if c % 1056 == 0),
        "V3_hot_vs_2096": sum(1 for c in v3 if c % 2096 == 0),
        "V3_hot_vs_1088": sum(1 for c in v3 if c % 1088 == 0),
        "V1_step_gcd": _step_gcd(_config_rows("WIN-VLLM", "V1", "battery")),
        "V2_step_gcd": _step_gcd(_config_rows("WIN-VLLM", "V2", "battery")),
        "V1_hot_min": min(v1),
        "V2_hot_min": min(v2),
    }


def c57() -> dict:
    """SGLang: every hot row is an exact multiple of 64, at any page size."""
    out = {}
    for cfg, cell, phase in (("S0", "G3", None), ("S1", "WIN-SGL", "battery"),
                             ("S2", "WIN-SGL", "battery")):
        s = _unit_stats(_config_rows(cell, cfg, phase))
        out[f"{cfg}_hot_n"] = s["hot"]
        out[f"{cfg}_hot_multiple_of_unit"] = s["hot_multiple_of_unit"]
        out[f"{cfg}_gcd_cached"] = s["gcd_cached"]
        out[f"{cfg}_odd_unit"] = s["odd_unit"]
    s0 = _ok(_config_rows("G3", "S0"))
    s1 = _ok(_config_rows("WIN-SGL", "S1"))
    paired = list(zip(s0, s1))
    out["S1_vs_S0_paired"] = len(paired)
    out["S1_vs_S0_identical"] = sum(1 for a, b in paired if a["cached_tokens"] == b["cached_tokens"])
    return out


def c58() -> dict:
    """The measured condition that moves the grid: --page-size 128, row by row."""
    s1, s2 = _ok(_config_rows("WIN-SGL", "S1")), _ok(_config_rows("WIN-SGL", "S2"))
    paired = list(zip(s1, s2))
    deltas = [int(b["cached_tokens"]) - int(a["cached_tokens"]) for a, b in paired]
    beats = [round(int(b["ttft_ms"]) / int(a["ttft_ms"]), 3) for a, b in paired
             if a.get("ttft_ms") and b.get("ttft_ms")]

    def mean_uncached(sub):
        b = [r for r in sub if r.get("phase") == "battery"]
        return round(sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in b) / len(b), 2)

    return {
        "paired_rows": len(paired),
        "identical": sum(1 for d in deltas if d == 0),
        "S2_lower_by_64": sum(1 for d in deltas if d == -64),
        "S2_higher": sum(1 for d in deltas if d > 0),
        "delta_set": sorted(set(deltas)),
        "mean_uncached_S1": mean_uncached(s1),
        "mean_uncached_S2": mean_uncached(s2),
        "ttft_ratio_median": round(statistics.median(beats), 3) if beats else None,
        "ttft_ratio_min": min(beats) if beats else None,
        "ttft_ratio_max": max(beats) if beats else None,
    }


def c59() -> dict:
    """TUNED: grid 64 under --disable-chunked-prefix-cache true and slru eviction."""
    run = load("TUNED", "run.json")
    sub = _config_rows("TUNED", "TUNED")
    s = _unit_stats(sub)
    rp = [r for r in sub if r.get("phase") == "R" and r.get("status") == 200]
    out = {
        "rows_total": len(sub),
        "hot_n": s["hot"],
        "gcd_cached": s["gcd_cached"],
        "hot_multiple_of_unit": s["hot_multiple_of_unit"],
        "odd_unit": s["odd_unit"],
        "phase_P": sum(1 for r in sub if r.get("phase") == "P"),
        "phase_R": len(rp),
        "disable_chunked_prefix_cache": run["disable_chunked_prefix_cache"],
        "radix_eviction_policy": run["radix_eviction_policy"],
        "max_mamba_cache_size": run["max_mamba_cache_size"],
        "token_capacity": run["token_capacity"],
        "pressure_ratio": round(run["pressure_ratio"], 6),
        "docs_pushed": run["docs_pushed"],
    }
    for band in ("newest", "middle", "oldest"):
        bb = [r for r in rp if r.get("band") == band]
        out[f"band_{band}_hits"] = sum(1 for r in bb if int(r.get("cached_tokens") or 0) > 0)
        out[f"band_{band}_n"] = len(bb)
    return out


def c60() -> dict:
    """Cross-engine: unit 64 on two engines, yet per-turn uncached cost is not shared."""
    def per_turn(sub):
        b = _ok(sub)
        return round(sum(max(0, r["prompt_tokens"] - r["cached_tokens"]) for r in b) / len(b), 2)

    def hit(sub):
        b = _ok(sub)
        return round(sum(r["cached_tokens"] for r in b) / sum(r["prompt_tokens"] for r in b), 6)

    tun, s0 = _config_rows("TUNED", "TUNED"), _config_rows("G3", "S0")
    v1 = _config_rows("WIN-VLLM", "V1", "battery")
    t_mean, s_mean, v_mean = per_turn(tun), per_turn(s0), per_turn(v1)
    return {
        "TUNED_mean_uncached": t_mean,
        "TUNED_hit_fraction": hit(tun),
        "S0_mean_uncached": s_mean,
        "S0_hit_fraction": hit(s0),
        "TUNED_over_S0_per_turn": round(t_mean / s_mean, 4),
        "V1_over_S0_per_turn": round(v_mean / s_mean, 4),
        "V1_over_TUNED_per_turn": round(v_mean / t_mean, 4),
        "grid_units_distinct": len({GRID_CELLS[c][1] for c in GRID_CELLS}),
    }


# Checks printed as claim lines in "recompute.py all" but not value claims.
SPECIAL = {"C61": lambda: grid_guard()}
# Claims whose numbers are grid units: any of them running triggers the guard.
GRID_CLAIMS = {"C55", "C56", "C57", "C58", "C59", "C60", "C61"}


def grid_guard() -> int:
    """Loudly fail if any grid claim cites a config_id with no rows in any cell."""
    bad = 0
    for cfg, (cell, _unit, _phase) in GRID_CELLS.items():
        try:
            n = len(_config_rows(cell, cfg))
        except (KeyError, FileNotFoundError) as exc:
            print(f"GRID GUARD FAIL  {cfg}: {exc}")
            bad += 1
            continue
        print(f"GRID GUARD ok    {cfg}: {n} rows in {cell}")
    print(f"GRID GUARD {'PASS' if not bad else 'FAIL'}  {len(GRID_CELLS) - bad}/{len(GRID_CELLS)} configs")
    return 0 if not bad else 1


def _t_crit_95(df: int) -> float:
    """Student-t two-sided 95 % critical value used by the G5 fan-out CI."""
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
             6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    return table.get(df, 1.96 + 2.0 / max(df, 1))


def c53() -> dict:
    """G5 race-free fan-out: B/A and C/A over per-fan-out uncached totals.

    Reads ``cells/G5/rows.jsonl`` only.  The per-branch histories of layout B
    never share a prefix, so B's cache hit fraction is structurally 0; that is
    what the ratio measures.  Duplicate ``(layout, fanout, branch)`` rows are
    collapsed to the last observation, as the cell's own analyser does.
    """
    rs = rows("G5", "rows.jsonl")
    if not rs:
        raise ValueError("G5 rows are empty: cells/G5/rows.jsonl has no observations")
    latest: dict[tuple[str, int, int], dict] = {}
    for r in rs:
        key = (str(r.get("layout")), int(r.get("fanout_index", 0)), int(r.get("branch_index", 0)))
        latest[key] = r
    rs = list(latest.values())

    per: dict[str, dict[str, int | float]] = {}
    for layout in ("A", "B", "C"):
        sel = [r for r in rs if str(r.get("layout")) == layout]
        if not sel:
            raise ValueError(f"G5 has no rows for layout {layout!r}")
        per[layout] = {
            "prompt": sum(int(r.get("prompt_tokens", 0)) for r in sel),
            "cached": sum(int(r.get("cached_tokens", 0)) for r in sel),
            "uncached": sum(int(r.get("uncached", r.get("uncached_tokens", 0))) for r in sel),
            "n": len(sel),
            "n_hit": sum(1 for r in sel if int(r.get("cached_tokens", 0)) > 0),
            "n_fanouts": len({int(r.get("fanout_index", 0)) for r in sel}),
        }

    def fanout_uncached(layout: str) -> dict[int, int]:
        out: dict[int, int] = {}
        for r in rs:
            if str(r.get("layout")) != layout:
                continue
            fi = int(r.get("fanout_index", 0))
            out[fi] = out.get(fi, 0) + int(r.get("uncached", r.get("uncached_tokens", 0)))
        return out

    a = fanout_uncached("A")
    b = fanout_uncached("B")
    c = fanout_uncached("C")
    common_ab = sorted(set(a) & set(b))
    ratios_ba = [b[i] / a[i] for i in common_ab if a[i] > 0]
    common_ac = sorted(set(a) & set(c))
    ratios_ca = [c[i] / a[i] for i in common_ac if a[i] > 0]
    if len(ratios_ba) < 2 or len(ratios_ca) < 2:
        raise ValueError("G5 lacks paired fan-outs for a B/A or C/A ratio")
    m_ba = statistics.fmean(ratios_ba)
    half = _t_crit_95(len(ratios_ba) - 1) * statistics.stdev(ratios_ba) / math.sqrt(len(ratios_ba))

    missed = [
        r for r in rs
        if str(r.get("layout")) in ("A", "C")
        and int(r.get("branch_index", 0)) >= 2
        and int(r.get("cached_tokens", 0)) == 0
    ]

    return {
        "B_over_A_mean": m_ba,
        "B_over_A_ci95_low": m_ba - half,
        "B_over_A_ci95_high": m_ba + half,
        "C_over_A_mean": statistics.fmean(ratios_ca),
        "A_prompt": per["A"]["prompt"],
        "A_cached": per["A"]["cached"],
        "A_uncached": per["A"]["uncached"],
        "A_hit_fraction": per["A"]["n_hit"] / per["A"]["n"],
        "B_prompt": per["B"]["prompt"],
        "B_cached": per["B"]["cached"],
        "B_uncached": per["B"]["uncached"],
        "B_hit_fraction": per["B"]["n_hit"] / per["B"]["n"],
        "C_prompt": per["C"]["prompt"],
        "C_cached": per["C"]["cached"],
        "C_uncached": per["C"]["uncached"],
        "n_fanouts": per["A"]["n_fanouts"],
        "n_branches": per["A"]["n"],
        "any_missed_after_serialisation": bool(missed),
    }


def c54() -> dict:
    """M4-EVICT resident capacity at 1.5017x pressure, derived from its rows.

    The resident bracket W comes from the boundary-probe rows (phase B) using the
    recency-rank model in ``cells/M4/boundary_probe.py``: a hit gives ``W >= rank``,
    a miss gives ``W < rank``.  The eviction bracket comes from the replay rows
    (phase R): the highest cumulative end among misses and the lowest cumulative
    start among hits.  The state-cache knob is read from the cell's analysis JSON;
    the token-pool comparison is re-derived from the phase-P mean prompt.
    """
    rs = rows("M4", "rows.jsonl")
    p_rows = [r for r in rs if r.get("phase") == "P"]
    r_rows = [r for r in rs if r.get("phase") == "R"]
    b_rows = [r for r in rs if r.get("phase") == "B"]
    if not p_rows or not r_rows or not b_rows:
        raise ValueError("M4-EVICT rows missing a phase (P/R/B); cannot re-derive resident capacity")

    mean_prompt = sum(r["prompt_tokens"] for r in p_rows) / len(p_rows)
    capacity = int(p_rows[0]["token_capacity"])
    n_docs = len(p_rows)

    last_idx: dict[str, list[int]] = {}
    for i, r in enumerate(rs):
        last_idx.setdefault(str(r["doc_id"]), []).append(i)

    def rank_before(i: int) -> int:
        doc = str(rs[i]["doc_id"])
        prevs = [j for j in last_idx[doc] if j < i]
        prev = prevs[-1] if prevs else -1
        seen: dict[str, int] = {}
        for j in range(i - 1, -1, -1):
            seen.setdefault(str(rs[j]["doc_id"]), j)
        return sum(1 for j in seen.values() if j > prev) + 1

    lower, upper = 1, None
    for i, r in enumerate(rs):
        if r.get("phase") != "B":
            continue
        rank = rank_before(i)
        if int(r.get("cached_tokens", 0)) > 0:
            lower = max(lower, rank)
        else:
            upper = rank if upper is None else min(upper, rank)
    w_hi = (upper - 1) if upper is not None else None

    tokens = [round(lower * mean_prompt)]
    ratios = [round(tokens[0] / capacity, 4)]
    if w_hi is not None:
        tokens.append(round(w_hi * mean_prompt))
        ratios.append(round(tokens[1] / capacity, 4))

    cum_end = {r["doc_position"]: r["cum_prompt_tokens"] for r in p_rows}
    onset_doc = lower + 1
    onset_cum = cum_end.get(min(onset_doc, n_docs))
    misses = [r for r in r_rows if int(r.get("cached_tokens", 0)) == 0]
    hits = [r for r in r_rows if int(r.get("cached_tokens", 0)) > 0]
    if not misses or not hits:
        raise ValueError("M4-EVICT replay phase has no hit/miss pair; eviction bracket undefined")

    analysis = load("M4", "analysis.json")
    mamba = analysis.get("run", {}).get("max_mamba_cache_size")
    pool_docs = round(capacity / mean_prompt, 2)
    pool_excluded = bool(w_hi is not None and w_hi < capacity / mean_prompt)

    return {
        "resident_capacity_docs_low": lower,
        "resident_capacity_docs_high": w_hi,
        "resident_capacity_tokens_low": tokens[0],
        "resident_capacity_tokens_high": tokens[1] if len(tokens) > 1 else None,
        "resident_capacity_ratio_low": ratios[0],
        "resident_capacity_ratio_high": ratios[1] if len(ratios) > 1 else None,
        "token_capacity": capacity,
        "total_pressure_tokens": int(p_rows[0]["total_pressure_tokens"]),
        "pressure_ratio": p_rows[0]["pressure_ratio"],
        "docs_pushed": n_docs,
        "evicted_up_to_cum_tokens": max(r["cum_prompt_tokens"] for r in misses),
        "resident_from_cum_tokens": min(r["cum_prompt_tokens_start"] for r in hits),
        "token_pool_lru_docs": pool_docs,
        "token_pool_lru_excluded": pool_excluded,
        "replay_hits": len(hits),
        "replay_misses": len(misses),
        "first_eviction_doc_position": onset_doc,
        "first_eviction_cum_tokens": onset_cum,
        "max_mamba_cache_size": mamba,
        "binding_constraint": "state_cache" if pool_excluded else "unknown",
        "verdict": "consistent_with_lru" if (w_hi is not None and lower <= w_hi) else "refuted",
    }


#: C62's compacting arms and the compaction-free baseline each is matched to.  The pairing
#: is by RENDERER (append-note arms against B, pointer arms against B-ptr), because the 32k
#: B-ptr baseline carries a phase artefact and a renderer-mismatched pairing would confound
#: the two effects the cell was built to separate.
C62_BASELINE = {"S": "B", "F": "B", "S-k800": "B", "F-k800": "B",
                "S-ptr": "B-ptr", "F-ptr": "B-ptr"}
C62_SEED = 20251023
C62_BOOT = 10000


def _c62_boot_ci(a: list[int], b: list[int], seed: int = C62_SEED, n: int = C62_BOOT):
    """Percentile bootstrap of ``mean(a) - mean(b)``, same recipe as the cell's analyser.

    ``random.Random(seed)`` is CPython's own Mersenne Twister and is stable across
    versions, so this re-derives the cell's interval rather than approximating it.
    """
    rnd = random.Random(seed)
    diffs = []
    for _ in range(n):
        ma = sum(a[rnd.randrange(len(a))] for _ in range(len(a))) / len(a)
        mb = sum(b[rnd.randrange(len(b))] for _ in range(len(b))) / len(b)
        diffs.append(ma - mb)
    diffs.sort()
    return round(diffs[int(0.025 * n)], 1), round(diffs[int(0.975 * n)], 1)


def c62() -> dict:
    """G3-LIMIT-V2: what compaction costs on the turns after the boundary fires.

    Reads ``cells/G3-LIMIT-V2/rows.jsonl`` only.  For every compacting arm the turn of its
    first compaction is found from the rows (``compacted_this_turn``); turns after it are
    the *post-boundary* segment and are compared with the matched compaction-free baseline
    on the SAME turn, so the baseline's own phase drift cancels.  Turns before it are the
    control segment: once a compaction is unavoidable, the arms are the same workload, so a
    pre-boundary difference would be a defect, not a result.
    """
    rs = rows("G3-LIMIT-V2", "rows.jsonl")
    if not rs:
        raise ValueError("G3-LIMIT-V2 rows are empty: cells/G3-LIMIT-V2/rows.jsonl")
    if any(r.get("status") != 200 for r in rs):
        raise ValueError("G3-LIMIT-V2 has non-200 rows; the contrast would mix in errors")
    by: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    for r in rs:
        by[(r["budget"], r["arm"])][int(r["turn"])] = r

    out: dict[str, object] = {"rows": len(rs)}
    per_arm: dict[str, dict[str, object]] = {}
    for budget in ("32k", "64k"):
        for arm, base in C62_BASELINE.items():
            a_rows, b_rows = by.get((budget, arm)), by.get((budget, base))
            if not a_rows or not b_rows:
                raise ValueError(f"G3-LIMIT-V2 has no {budget} rows for {arm} or {base}")
            fires = sorted(t for t, r in a_rows.items() if r.get("compacted_this_turn"))
            base_fires = sorted(t for t, r in b_rows.items()
                                if r.get("trigger_reason") == "sliding_window_drop")
            if not fires:
                raise ValueError(f"G3-LIMIT-V2 {budget} {arm} never compacted; C62 has no boundary")
            first = fires[0]
            post = [t for t in sorted(a_rows) if t > first and t in b_rows]
            pre = [t for t in sorted(a_rows) if t < first and t in b_rows]
            adv_post = [int(a_rows[t]["uncached_tokens"]) for t in post]
            bl_post = [int(b_rows[t]["uncached_tokens"]) for t in post]
            # Turns that follow one of the baseline's own window drops are the baseline
            # re-filling its window, not the arm resting -- a weight difference, not noise.
            drops_at = set(base_fires)
            steady = [t for t in post if (t - 1) not in drops_at]
            adv_steady = [int(a_rows[t]["uncached_tokens"]) for t in steady]
            bl_steady = [int(b_rows[t]["uncached_tokens"]) for t in steady]
            adv_pre = [int(a_rows[t]["uncached_tokens"]) for t in pre]
            bl_pre = [int(b_rows[t]["uncached_tokens"]) for t in pre]
            d_post = statistics.fmean(adv_post) - statistics.fmean(bl_post)
            d_pre = statistics.fmean(adv_pre) - statistics.fmean(bl_pre)
            lo, hi = _c62_boot_ci(adv_post, bl_post)
            lo_pre, hi_pre = _c62_boot_ci(adv_pre, bl_pre)
            comp = {t: int(a_rows[t]["uncached_tokens"]) for t in fires}
            drops = {t: int(b_rows[t]["uncached_tokens"]) for t in base_fires}
            per_arm[f"{budget} {arm}"] = {
                "baseline": base,
                "renderer": a_rows[first].get("renderer"),
                "compaction_turns": fires,
                "first_compaction_turn": first,
                "boundary_uncached": comp[first],
                "baseline_drop_uncached": drops.get(first),
                "n_post": len(post),
                "post_arm_mean": round(statistics.fmean(adv_post), 1),
                "post_base_mean": round(statistics.fmean(bl_post), 1),
                "post_delta": round(d_post, 1),
                "post_ci": [lo, hi],
                "post_excludes_zero": bool(lo > 0 or hi < 0),
                "n_pre": len(pre),
                "pre_delta": round(d_pre, 1),
                "pre_ci": [lo_pre, hi_pre],
                "pre_excludes_zero": bool(lo_pre > 0 or hi_pre < 0),
                "baseline_window_drops": base_fires,
                # The band a reader takes away: every matched-turn difference in the
                # post-boundary segment, not the two arm means the interval is built from.
                # ``post_delta`` is a mean over 27-89 turns and averages a large turn with
                # the small ones, so a per-turn range built from arm means understates what
                # the segment costs on a given turn -- and these rows are the only ones in
                # the package that cross a context limit, so no other claim notices it.
                "post_turn_delta_min": round(min(a - b for a, b in zip(adv_post, bl_post)), 1),
                "post_turn_delta_max": round(max(a - b for a, b in zip(adv_post, bl_post)), 1),
                # The segment split by WEIGHT rather than by noise: a turn whose baseline
                # is still re-filling the window it just dropped (the turn after one of the
                # baseline's own ``sliding_window_drop`` turns) is a transition turn, not a
                # resting one, and mixing the two averages a large turn with ninety small
                # ones.  The 32k F-ptr arm went from +134.6 to +112.5 on exactly two such
                # turns, so the split moves an arm's significance and must not be reported
                # without it.
                "post_steady_turns": len(steady),
                "post_steady_delta": round(
                    statistics.fmean(adv_steady) - statistics.fmean(bl_steady), 1)
                if steady else None,
                # Rounded per arm, then the minimum of the ROUNDED pair: the band is
                # quoted to one decimal across arms, so a banker's round at the fourth
                # comparison must not reorder two arms that print the same figure.
                "post_steady_turn_min": min(round(a - b, 1)
                                            for a, b in zip(adv_steady, bl_steady)),
                "post_steady_turn_max": max(round(a - b, 1)
                                            for a, b in zip(adv_steady, bl_steady)),
                "post_transition_turns": [t for t in post if t not in steady],
            }
    out["per_arm"] = per_arm

    post_deltas = [v["post_delta"] for v in per_arm.values()]
    turn_deltas = [d for v in per_arm.values()
                   for d in (v["post_turn_delta_min"], v["post_turn_delta_max"])]
    # Band endpoints taken over EVERY compaction row and EVERY baseline drop row.  The
    # per-arm ``boundary_uncached`` above is the arm's FIRST compaction only, and the 32k
    # arms fire twice, so a band read off ``per_arm`` understates its own upper end
    # (1,826-2,972 instead of 1,826-3,033) -- the published figure was exactly that mistake.
    boundary_all = [int(r["uncached_tokens"]) for r in rs if r.get("compacted_this_turn")]
    drop_all = [int(r["uncached_tokens"]) for r in rs
                if r.get("trigger_reason") == "sliding_window_drop"]
    pre_deltas = [v["pre_delta"] for v in per_arm.values()]
    out.update({
        "arm_kinds": len(per_arm),
        "compacting_arms_at_32k": sum(1 for k in per_arm if k.startswith("32k")),
        "compacting_arms_at_64k": sum(1 for k in per_arm if k.startswith("64k")),
        "compaction_rows": sum(len(v["compaction_turns"]) for v in per_arm.values()),
        "post_delta_min": round(min(post_deltas), 1),
        "post_delta_max": round(max(post_deltas), 1),
        "post_turn_delta_min": round(min(turn_deltas), 1),
        "post_turn_delta_max": round(max(turn_deltas), 1),
        "post_deltas_all_positive": all(d > 0 for d in post_deltas),
        # A segment whose mean is positive need not have every turn positive, and a turn
        # that comes in UNDER the baseline is exactly the reading a "costs nothing before
        # it" summary would hide.
        "post_turns_below_zero": sum(
            1 for v in per_arm.values() if v["post_turn_delta_min"] < 0),
        "post_ci_zero_crossings": sum(1 for v in per_arm.values() if not v["post_excludes_zero"]),
        "pre_delta_min": round(min(pre_deltas), 1),
        "pre_delta_max": round(max(pre_deltas), 1),
        "pre_ci_excludes_zero": sum(1 for v in per_arm.values() if v["pre_excludes_zero"]),
        "baseline_window_drop_rows": sum(len(v["baseline_window_drops"]) for v in per_arm.values()),
        "boundary_turn_uncached_min": min(boundary_all),
        "boundary_turn_uncached_max": max(boundary_all),
        "boundary_turn_rows": len(boundary_all),
        "baseline_drop_uncached_min": min(drop_all),
        "baseline_drop_uncached_max": max(drop_all),
        "baseline_drop_turns": len(drop_all),
        "first_turn_32k": sorted({v["first_compaction_turn"] for k, v in per_arm.items()
                                  if k.startswith("32k")}),
        "first_turn_64k": sorted({v["first_compaction_turn"] for k, v in per_arm.items()
                                  if k.startswith("64k")}),
    })

    # Per budget: the resting-window bracket (last-turn prompt of the baseline vs the arms)
    # and which policy the compaction turn's trigger came from.
    rest: dict[str, object] = {}
    for budget in ("32k", "64k"):
        last = {arm: int(max(by[(budget, arm)].values(), key=lambda r: int(r["turn"]))["prompt_tokens"])
                for (b, arm) in by if b == budget}
        triggers = Counter((r.get("trigger_reason"), bool(r.get("compacted_this_turn")))
                           for (b, _a), t in by.items() if b == budget for r in t.values())
        rest[budget] = {
            "last_prompt_B": last.get("B"),
            "last_prompt_B_ptr": last.get("B-ptr"),
            "last_prompt_arms": {a: v for a, v in sorted(last.items())
                                 if a not in ("B", "B-ptr")},
            "compacted_trigger_reasons": {k[0]: v for k, v in triggers.items() if k[1]},
            "turns_per_arm": {a: len(t) for (b, a), t in sorted(by.items()) if b == budget},
        }
    out["resting_window"] = rest
    return out


# --------------------------------------------------------------------------- #
# C63 — the four-cell model x engine matrix (MATRIX-FOLD)
# --------------------------------------------------------------------------- #
#: (model, engine, cell, config_id), in matrix order.  Two models x two engines, each
#: measured on the SAME 32k schedule (4 arms x 71 turns, battery phase) so the four
#: cells pair row for row on (arm, turn); prompts are byte-identical across the cells
#: (they were rendered by the same driver), and the chat-template artefact moves
#: ``prompt_tokens`` by -4 on 140 of 284 rows in the SGLang cells -- a property of the
#: template, not of the workload, and ``c63`` verifies it rather than ignoring it.
C63_CELLS = (
    ("occamy-1.0", "vllm", "MOE-VLLM", "V3"),
    ("occamy-1.0", "sglang", "G3", "S0"),
    ("qwen3.5-9b", "vllm", "WIN-VLLM", "V1"),
    ("qwen3.5-9b", "sglang", "DENSE-SGL", "P1"),
)
C63_TURNS = 71
C63_ARMS = ("R", "A", "C", "H")
C63_SEED = 20251023
C63_BOOT = 10000


def _c63_boot(v: list[float], seed: int = C63_SEED, n: int = C63_BOOT) -> tuple[float, float]:
    """Percentile bootstrap of a mean over TURNS (the independent unit).

    The four arms are salt-separated replicates: no compaction fires at 32k, so arms
    measure the same schedule under different salts rather than four policies.  Treating
    the 284 (arm, turn) rows as independent would understate the interval by resampling
    replicated arms, so the effects are computed per turn (mean over the four arms) and
    the 71 turns are the resampling units.
    """
    rnd = random.Random(seed)
    means = []
    for _ in range(n):
        means.append(sum(v[rnd.randrange(len(v))] for _ in range(len(v))) / len(v))
    means.sort()
    return round(means[int(0.025 * n)], 1), round(means[int(0.975 * n)], 1)


def _c63_cell_rows(cell: str, cfg: str) -> list[dict]:
    rs = [r for r in rows(cell, "rows.jsonl")
          if r.get("phase") in (None, "battery")
          and r.get("depth") == "32k"
          and r.get("config_id") == cfg
          and r.get("arm") in C63_ARMS
          and 1 <= int(r["turn"]) <= C63_TURNS]
    if not rs:
        raise ValueError(f"C63: cell {cell!r} has no 32k battery rows for config {cfg!r}")
    bad = [r for r in rs if r.get("status") != 200]
    if bad:
        raise ValueError(f"C63: cell {cell!r} has {len(bad)} non-200 row(s); "
                         "the matrix contrast would mix in errors")
    return rs


def _c63_unc(r: dict) -> int:
    """The row's uncached-token count.  The four cells spell the field ``uncached``; the
    fallback keeps the function readable if a cell ever carries the long name."""
    v = r.get("uncached", r.get("uncached_tokens"))
    if v is None:
        raise ValueError("C63 row carries no uncached token count")
    return int(v)


def c63() -> dict:
    """MATRIX-FOLD: separate the engine effect from the model effect on a 2x2 matrix.

    All four model x engine cells measured the same 32k schedule (4 arms x 71 turns,
    prompts byte-identical).  At this band no compaction fires, so the arms are
    replicates and the cell's noise floor is the arm spread.  The claim decomposes the
    four cell means of ``uncached_tokens`` per turn into a 2x2 factorial: the ENGINE
    main effect (vLLM - SGLang, averaged over the two models), the MODEL main effect
    (dense qwen3.5-9b - MoE occamy-1.0, averaged over the two engines), and their
    interaction.  Everything is read from the four cells' rows; nothing is inherited
    from the cells' handoffs.
    """
    cells: dict[tuple[str, str], dict[tuple[str, int], dict]] = {}
    for model, engine, cell, cfg in C63_CELLS:
        rs = _c63_cell_rows(cell, cfg)
        by = {(r["arm"], int(r["turn"])): r for r in rs}
        if len(rs) != len(by):
            raise ValueError(f"C63: cell {cell!r} has duplicate (arm, turn) rows")
        if len(by) != len(C63_ARMS) * C63_TURNS:
            raise ValueError(f"C63: cell {cell!r} has {len(by)} (arm, turn) rows, "
                             f"expected {len(C63_ARMS) * C63_TURNS}")
        cells[(model, engine)] = by
    keys = sorted(next(iter(cells.values())))
    for k, by in cells.items():
        if sorted(by) != keys:
            raise ValueError(f"C63: cell {k} does not cover the same (arm, turn) keys")

    # Prompts must be the same bytes across all six cell pairs; a pairing that is only
    # "similar" would make the paired decomposition a comparison of different workloads.
    pairs = [(a, b) for i, a in enumerate(cells) for b in list(cells)[i + 1:]]
    chars_equal = {p: sum(1 for k in keys if cells[p[0]][k]["chars"] == cells[p[1]][k]["chars"])
                   for p in pairs}
    if any(v != len(keys) for v in chars_equal.values()):
        raise ValueError(f"C63: prompt lengths differ across cells: {chars_equal}")
    # The rows carry the digest the cache keys on, not the rendered text, so equality of
    # prefix_sha256 + chars is the strongest identity the four cells can prove; the claim's
    # prose says exactly that rather than "byte-identical".
    missing_digest = [(cell, k) for cell in cells for k in keys
                      if not cells[cell][k].get("prefix_sha256")]
    if missing_digest:
        raise ValueError("C63: rows without a prompt prefix digest: "
                         f"{missing_digest[:3]} ({len(missing_digest)} rows)")
    digests_equal = {p: sum(1 for k in keys
                            if cells[p[0]][k].get("prefix_sha256")
                            == cells[p[1]][k].get("prefix_sha256"))
                     for p in pairs}
    if any(v != len(keys) for v in digests_equal.values()):
        raise ValueError(f"C63: prompt prefix digests differ across cells: {digests_equal}")
    deltas = Counter(cells[p[0]][k]["prompt_tokens"] - cells[p[1]][k]["prompt_tokens"]
                     for p in pairs for k in keys)

    stats = {}
    for (model, engine), by in cells.items():
        pt = sum(int(by[k]["prompt_tokens"]) for k in keys)
        ca = sum(int(by[k]["cached_tokens"]) for k in keys)
        hot = [int(by[k]["cached_tokens"]) for k in keys if int(by[k]["cached_tokens"]) > 0]
        stats[(model, engine)] = {
            "n": len(by),
            "hit": round(ca / pt, 6),
            "unc": round(statistics.fmean(_c63_unc(by[k]) for k in keys), 4),
            "gcd": gcd_all(hot),
        }

    # Per-turn values (mean over the four replicate arms), then the factorial contrasts.
    def tl(model: str, engine: str) -> dict[int, float]:
        by = cells[(model, engine)]
        return {t: statistics.fmean(_c63_unc(by[(arm, t)]) for arm in C63_ARMS)
                for t in range(1, C63_TURNS + 1)}

    dv, ds = tl("qwen3.5-9b", "vllm"), tl("qwen3.5-9b", "sglang")
    mv, ms = tl("occamy-1.0", "vllm"), tl("occamy-1.0", "sglang")
    turns = range(1, C63_TURNS + 1)
    engine = [((dv[t] - ds[t]) + (mv[t] - ms[t])) / 2 for t in turns]
    model = [((dv[t] - mv[t]) + (ds[t] - ms[t])) / 2 for t in turns]
    interaction = [((dv[t] - ds[t]) - (mv[t] - ms[t])) / 2 for t in turns]
    e_moe = [mv[t] - ms[t] for t in turns]
    e_dense = [dv[t] - ds[t] for t in turns]
    m_vllm = [dv[t] - mv[t] for t in turns]
    m_sgl = [ds[t] - ms[t] for t in turns]

    def effect(v: list[float]) -> dict[str, object]:
        lo, hi = _c63_boot(v)
        return {"mean": round(statistics.fmean(v), 2), "ci": (lo, hi),
                "positive": sum(1 for x in v if x > 0)}

    def ratio(x: dict[int, float], y: dict[int, float]) -> float:
        return round(statistics.fmean(x.values()) / statistics.fmean(y.values()), 4)

    e, m, i = effect(engine), effect(model), effect(interaction)
    e_moe_s, e_dense_s = effect(e_moe), effect(e_dense)
    m_vllm_s, m_sgl_s = effect(m_vllm), effect(m_sgl)

    outcomes = {k: v["unc"] for k, v in stats.items()}
    grand = statistics.fmean(outcomes.values())
    return {
        "rows_total": sum(len(by) for by in cells.values()),
        "rows_per_cell": len(keys),
        "paired_turns": C63_TURNS,
        "chars_equal_pairs": len(pairs),
        "chars_equal_rows": min(chars_equal.values()),
        "prefix_equal_pairs": len(pairs),
        "prefix_equal_rows": min(digests_equal.values()),
        "prompt_token_deltas": tuple(sorted(deltas)),
        "cells": tuple((model, engine, stats[(model, engine)]["n"],
                        stats[(model, engine)]["hit"], stats[(model, engine)]["unc"],
                        stats[(model, engine)]["gcd"])
                       for model, engine, _cell, _cfg in C63_CELLS),
        "cell_mean_grand": round(grand, 4),
        "engine_effect": e["mean"], "engine_ci": e["ci"], "engine_positive_turns": e["positive"],
        "model_effect": m["mean"], "model_ci": m["ci"], "model_positive_turns": m["positive"],
        "interaction": i["mean"], "interaction_ci": i["ci"],
        "interaction_positive_turns": i["positive"],
        "engine_moe": e_moe_s["mean"], "engine_moe_ci": e_moe_s["ci"],
        "engine_moe_positive_turns": e_moe_s["positive"],
        "engine_dense": e_dense_s["mean"], "engine_dense_ci": e_dense_s["ci"],
        "engine_dense_positive_turns": e_dense_s["positive"],
        "model_vllm": m_vllm_s["mean"], "model_vllm_ci": m_vllm_s["ci"],
        "model_vllm_positive_turns": m_vllm_s["positive"],
        "model_sglang": m_sgl_s["mean"], "model_sglang_ci": m_sgl_s["ci"],
        "model_sglang_positive_turns": m_sgl_s["positive"],
        # Ratios are of the cell means (arithmetic), not fitted log slopes: the matrix has
        # two levels per factor, so the arithmetic ratio is the measured figure.
        "engine_ratio_moe": ratio(mv, ms),
        "engine_ratio_dense": ratio(dv, ds),
        "engine_ratio_mean": round((ratio(mv, ms) + ratio(dv, ds)) / 2, 4),
        "model_ratio_vllm": ratio(dv, mv),
        "model_ratio_sglang": ratio(ds, ms),
        "model_ratio_mean": round((ratio(dv, mv) + ratio(ds, ms)) / 2, 4),
        "engine_over_model": round(e["mean"] / m["mean"], 4),
        "engine_share_of_grand": round(e["mean"] / grand, 4),
        "model_share_of_grand": round(m["mean"] / grand, 4),
        # Divided from the UNROUNDED per-turn means, not from the 2-dp figures the prose
        # prints: 548.056338028169 / 3.6056338028169015 = 152.0, whereas the rounded operands
        # give 151.8172.  The claim quotes 4 dp, so the ratio of the raw means is the figure.
        "model_effect_ratio_vllm_over_sglang": round(
            statistics.fmean(m_vllm) / statistics.fmean(m_sgl), 4)
        if statistics.fmean(m_sgl) else None,
        "per_arm_engine": tuple(
            (arm, round(statistics.fmean(
                (_c63_unc(cells[("qwen3.5-9b", "vllm")][(arm, t)])
                 - _c63_unc(cells[("qwen3.5-9b", "sglang")][(arm, t)])
                 + _c63_unc(cells[("occamy-1.0", "vllm")][(arm, t)])
                 - _c63_unc(cells[("occamy-1.0", "sglang")][(arm, t)])) / 2
                for t in turns), 1))
            for arm in C63_ARMS),
        "per_arm_model": tuple(
            (arm, round(statistics.fmean(
                (_c63_unc(cells[("qwen3.5-9b", "vllm")][(arm, t)])
                 - _c63_unc(cells[("occamy-1.0", "vllm")][(arm, t)])
                 + _c63_unc(cells[("qwen3.5-9b", "sglang")][(arm, t)])
                 - _c63_unc(cells[("occamy-1.0", "sglang")][(arm, t)])) / 2
                for t in turns), 1))
            for arm in C63_ARMS),
    }


# --------------------------------------------------------------------------- #
# Expected values — the numbers printed in CLAIMS.md / MANUSCRIPT.md
# --------------------------------------------------------------------------- #
EXPECTED: dict[str, dict[str, object]] = {
    "C02": {"rows": 760, "non_200": 0, "with_error": 0, "cases": 190, "conditions": 4},
    "C03": {"deep_summarise_eq_fork_digest": 190, "n_deep_cases": 190, "distinct_digests": 570, "n_rows": 760},
    "C04": {
        "A_n": 8, "A_prompt": 15400, "A_uncached": 4648, "A_per_branch_prompt": 1925,
        "A_uncached_by_branch": [1925, 1925, 133, 133, 133, 133, 133, 133],
        "B_n": 8, "B_prompt": 15400, "B_uncached": 15400,
        "C_n": 8, "C_prompt": 15400, "C_uncached": 4648,
        "A_cached_by_branch": [0, 0, 1792, 1792, 1792, 1792, 1792, 1792],
        "B_cached_by_branch": [0, 0, 0, 0, 0, 0, 0, 0],
        "C_cached_by_branch": [0, 0, 1792, 1792, 1792, 1792, 1792, 1792],
    },
    "C05": {"B_over_A": 3.3133, "C_over_A": 1.0, "requests": 24},
    "C06": {"warm_branches": 7, "warm_hits": 6, "hit_cached_tokens": [1792], "branch2_cached": 0,
            "counterfactual_A_uncached": 2856, "counterfactual_B_over_A": 5.3922},
    "C07": {"shallow_correct": 126, "shallow_n": 190, "shallow_pct": 66.3,
            "deep_baseline_correct": 137, "deep_baseline_n": 190, "deep_baseline_pct": 72.1,
            "deep_summarise_correct": 134, "deep_summarise_n": 190, "deep_summarise_pct": 70.5,
            "deep_fork_correct": 132, "deep_fork_n": 190, "deep_fork_pct": 69.5},
    "C08": {"summarise_discordant_b": 11, "summarise_discordant_c": 8, "summarise_mcnemar_p": 0.6476,
            "fork_discordant_b": 13, "fork_discordant_c": 8, "fork_mcnemar_p": 0.3833,
            "summarise_vs_fork_discordant_b": 7, "summarise_vs_fork_discordant_c": 5,
            "summarise_vs_fork_mcnemar_p": 0.7744, "max_delta_pts": 2.632},
    "C09": {"baseline_gold": 190, "baseline_question": 190, "baseline_options": 190,
            "summarise_gold": 0, "summarise_question": 190, "summarise_options": 190,
            "fork_gold": 0, "fork_question": 190, "fork_options": 190,
            "shallow_gold": 0, "shallow_question": 190, "shallow_options": 190},
    "C10": {"baseline_vs_summarise_agreed": 167, "baseline_vs_summarise_pct": 87.9,
            "fork_vs_baseline_agreed": 165, "fork_vs_baseline_pct": 86.8,
            "summarise_vs_fork_agreed": 174, "summarise_vs_fork_pct": 91.6},
    "C11": {"n_pairs": 21, "n_zero": 18, "median": 0.0, "max_abs": 64.0, "permutation_p": 1.0},
    "C12": {"n_nonzero": 3,
            "nonzero": [["u4-s1", 17, -64, 6174, 6172],
                        ["u4-s1", 32, 64, 6145, 6143],
                        ["u4-s3", 17, -64, 6224, 6221]]},
    "C13": {"RENDER": "naive_append", "POINTER_FORK_in_source": False, "uses_single_renderer": True},
    "C14": {"rows": 438, "events": 54, "events_summarise": 21, "events_fork": 21, "events_sliding": 12,
            "sessions": 3, "batch_requests": 438, "probe_requests": 13, "logged_requests": 451},
    "C15": {"fork_sha8": "b812c99d", "summarise_sha8": "dc591b7e", "legacy_fork_sha8": "dc591b7e",
            "legacy_fork_equals_summarise": True, "fork_differs": True,
            "prompt_chars_fork": 7966, "prompt_chars_summarise": 7791, "delta_chars": 175,
            "marker_first_line_chars": 171, "est_tokens": 44, "suffix_is_bare_summary": True},
    "C17": {"R_prompt": 194788, "R_cached": 143616, "R_uncached": 51172, "R_hit_rate": 0.7373, "R_n": 40},
    "C18": {"F_prompt": 198376, "F_cached": 151296, "F_uncached": 47080, "F_hit_rate": 0.7627, "F_n": 40},
    "C19": {"A_prompt": 412177, "A_cached": 382080, "A_uncached": 30097, "A_hit_rate": 0.927, "A_n": 40},
    "C20": {"C_prompt": 403259, "C_cached": 372736, "C_uncached": 30523, "C_hit_rate": 0.9243, "C_n": 40},
    "C21": {"R_over_A": 1.7002, "R_over_F": 1.0869, "F_over_A": 1.5643, "passes_1p5": True, "R_F_gap_pct": 8.69},
    "C22": {"break_net_total": 1620, "gap": 20649, "break_share": 0.0785, "steady_state": 19029, "steady_share": 0.9215},
    "C23": {"R_mean_uncached": 1659.9375, "R_mean_prompt": 5811.9375, "C_mean_uncached": 754.9375, "C_mean_prompt": 12838.9375},
    "C24": {"counterfactual_R": 32143, "R_over_counterfactual_A": 1.068},
    "C25": {"A_first_prompt": 1186, "A_last_prompt": 19583, "A_growth": 18397, "A_growth_factor": 16.5118,
            "A_total_prompt": 412177, "C_total_prompt": 403259, "A_extra_prompt_vs_C": 8918, "R_last_prompt": 4134},
    "C26": {"R_breaks": [18, 35], "F_breaks": [18, 35], "A_breaks": [], "C_breaks": []},
    "C27": {"miss": 208.7, "hit": 86.4, "ratio": 0.414, "delta": 122.1},
    "C28": {"miss": 349.2, "hit": 87.2, "ratio": 0.2498, "delta": 259.8},
    "C29": {"miss": 674.6, "hit": 105.2, "ratio": 0.156, "delta": 559.8},
    "C30": {"miss": 1431.6, "hit": 114.3, "ratio": 0.0798, "delta": 1311.7},
    "C31": {"miss": 3039.5, "hit": 139.2, "ratio": 0.0458, "delta": 2892.1},
    "C32": {"miss": 7541.9, "hit": 231.6, "ratio": 0.0307, "delta": 7251.0},
    "C33": {"miss_exponent": 1.052, "miss_r2": 0.9934, "hit_exponent": 0.2683, "hit_r2": 0.8631,
            "ratio_exponent": -0.7837, "ratio_r2": 0.9962},
    "C34": {"miss_ms_per_token": 0.240736, "hit_ms_per_token": 0.004659, "ratio": 51.67, "hit_us_per_token": 4.66},
    "C35": {"n_pairs": 42, "n_positive": 42, "reps_per_length": 7, "sign_p_one_sided": 0.0078, "sign_p_two_sided": 0.0156},
    "C36": {"rows": 139, "requests": 139, "non_200": 0, "lengths_resolved": 6,
            "calibration": 1, "prime": 20, "noise_hit": 20, "noise_cold": 10},
    "C37": {"warm": 44, "cached_eq_law": 44, "uncached_residual_zero": 44, "min_len": 314, "max_len": 1550,
            "n_residue_zero": 0, "cold_cached_nonzero": 0},
    "C38": {"warm_appends": 372, "deviating": 372, "min_residual": 832, "max_residual": 7936,
            "median_residual": 1792, "n_buckets": 15, "min_prompt": 1802, "max_prompt": 12393},
    "C39": {"shared_rows": 0, "u2_min": 314, "u2_max": 1550, "u4_min": 931, "u4_max": 12393},
    "C40": {"L1008_n": 5, "L1008_misses": 0, "L1008_cached": [960],
            "L1023_n": 5, "L1023_misses": 0, "L1023_cached": [960],
            "L1024_n": 5, "L1024_misses": 5, "L1024_cached": [0],
            "L1025_n": 5, "L1025_misses": 0, "L1025_cached": [1024],
            "L1088_n": 5, "L1088_misses": 5, "L1088_cached": [0],
            "miss_ttft_ms_1024_median": 268.4,
            "rep2_n": 10, "rep2_law_match": 10},
    "C41": {"p1_multiple_misses": 10, "p1_multiple_n": 10, "p1_nonmultiple_misses": 0, "p1_nonmultiple_n": 15,
            "fisher_p": 3.06e-07, "pooled_multiple_misses": 35, "pooled_multiple_n": 35,
            "pooled_nonmultiple_misses": 0, "pooled_nonmultiple_n": 15, "pooled_fisher_p": 4.44e-13},
    "C42": {"delay_n": 20, "delay_misses": 20, "insert_n": 5, "insert_misses": 5},
    "C43": {"cold_n": 55, "cold_nonzero": 0},
    "C44": {"n_rows": 264, "n_rows_E": 132, "n_rows_F": 132, "n_events": 6,
            "n_events_within_10pct": 2, "all_events_within_10pct": False,
            "u15_1_700x_survives_decomposition": False,
            "mean_break_cost_gross_E": 1728.0, "mean_break_cost_gross_F": 1664.0,
            "ratio_mean_break_cost_E_over_F": 1.0384615384615385,
            "ratio_total_uncached_E_over_F": 0.9739119834206997,
            "rows_sha256": "9242ad383281b360ec3c4be92bc59e7de7d5cd751eb7e15c0944f2261497ae66"},
    "C45": {"rows_total": 1800, "rows_S1": 900, "rows_S2": 900, "status_200_total": 1800,
            "status_200_S1": 900, "status_200_S2": 900,
            "rows_sha256": "ea5728760540352a752bca501fe77aaae054ec0a88deba4db9bdf8a9f3c5e6c7"},
    "C46": {"S1_n_battery": 888, "S1_hit_fraction": 0.974202, "S1_mean_uncached_per_turn": 740.4,
            "S1_mean_uncached_32k": 729.2, "S1_mean_uncached_64k": 746.01, "S1_steady_n": 880,
            "S1_gcd_cached": 64, "S1_odd64": 351, "S2_n_battery": 888, "S2_hit_fraction": 0.973778,
            "S2_mean_uncached_per_turn": 752.6, "S2_mean_uncached_32k": 745.2, "S2_mean_uncached_64k": 756.28,
            "S2_steady_n": 880, "S2_gcd_cached": 128, "S2_odd64": 0},
    "C47": {"rows_total": 888, "status_200": 888, "hit_fraction": 0.974242,
            "mean_uncached_per_turn": 739.2, "mean_uncached_32k": 725.74, "mean_uncached_64k": 746.01,
            "steady_n": 880, "gcd_cached": 64, "odd64": 351,
            "rows_sha256": "d6313f72c2eca0bc2192922bfcf1bad08c853c9dd11fbd67b0e65f85428759ee"},
    "C48": {"rows_total": 692, "status_200_total": 692, "rows_V1": 358, "rows_V2": 312, "rows_V3": 22,
            "status_200_V1": 358, "status_200_V2": 312, "status_200_V3": 22,
            "rows_sha256": "a606ca06a23145a52d2bb50f82baff1b6e8d0689164c80ce987c441ce83cf1d7"},
    "C49": {"V1_grid_rows": 70, "V1_distinct_L": 19, "V1_gcd_cached": 1088, "V1_law_exact": 10,
            "V2_grid_rows": 26, "V2_distinct_L": 11, "V2_gcd_cached": 1056, "V2_law_exact": 10,
            "V3_grid_rows": 20, "V3_distinct_L": 5, "V3_gcd_cached": 2096, "V3_law_exact": 15},
    "C50": {"V1_n_battery": 284, "V1_hit_fraction": 0.869037, "V1_mean_uncached_per_turn": 2230.8,
            "V2_n_battery": 284, "V2_hit_fraction": 0.868144, "V2_mean_uncached_per_turn": 2246.0},
    "C51": {"S0_32k_mean_uncached": 725.74, "S0_hit_fraction": 0.974242,
            "V1_mean_uncached_per_turn": 2230.8, "V1_hit_fraction": 0.869037,
            "ratio_V1_over_S0_32k": 3.074},
    "C52": {"rows_total": 289, "rows_phase_P": 259, "rows_phase_R": 30, "status_200_total": 289,
            "grid_gcd_cached": 64, "grid_exact_64_minus1": 10, "grid_odd64": 3,
            "variant": "wt-slru", "radix_policy": "slru",
            "rows_sha256": "be59b3bf8d5572cca38a5c74f5b8348152ec6b8a29b4b270fc4374baa62905cc"},
    "C53": {"B_over_A_mean": 6.744331504090632,
            "B_over_A_ci95_low": 4.045426492430726,
            "B_over_A_ci95_high": 9.443236515750538,
            "C_over_A_mean": 1.1051744026291601,
            "A_prompt": 123240, "A_cached": 102912, "A_uncached": 20328,
            "A_hit_fraction": 0.890625,
            "B_prompt": 123256, "B_cached": 0, "B_uncached": 123256,
            "B_hit_fraction": 0.0,
            "C_prompt": 123216, "C_cached": 103424, "C_uncached": 19792,
            "n_fanouts": 8, "n_branches": 64,
            "any_missed_after_serialisation": False},
    "C54": {"resident_capacity_docs_low": 30, "resident_capacity_docs_high": 31,
            "resident_capacity_tokens_low": 258035, "resident_capacity_tokens_high": 266636,
            "resident_capacity_ratio_low": 0.1592, "resident_capacity_ratio_high": 0.1645,
            "token_capacity": 1620892, "total_pressure_tokens": 2434133,
            "pressure_ratio": 1.501724, "docs_pushed": 283,
            "evicted_up_to_cum_tokens": 1255655, "resident_from_cum_tokens": 2348053,
            "token_pool_lru_docs": 188.45, "token_pool_lru_excluded": True,
            "replay_hits": 10, "replay_misses": 20,
            "max_mamba_cache_size": 64, "binding_constraint": "state_cache",
            "verdict": "consistent_with_lru"},
    # X-SYNTH second pass: whole-cell grid laws, the moving condition, cross-engine
    "C55": {"S0_gcd_cached": 64, "S0_hot_multiple_of_unit": 880, "S0_hot_n": 880,
            "S1_gcd_cached": 64, "S1_hot_multiple_of_unit": 888, "S1_hot_n": 888,
            "S2_gcd_cached": 128, "S2_hot_multiple_of_unit": 888, "S2_hot_n": 888,
            "V1_gcd_cached": 1088, "V1_hot_multiple_of_unit": 300, "V1_hot_n": 300,
            "V2_gcd_cached": 1056, "V2_hot_multiple_of_unit": 268, "V2_hot_n": 268,
            "V3_gcd_cached": 2096, "V3_hot_multiple_of_unit": 16, "V3_hot_n": 16,
            "TUNED_gcd_cached": 64, "TUNED_hot_multiple_of_unit": 10, "TUNED_hot_n": 10},
    "C56": {"V1_hot_vs_1056": 0, "V1_hot_vs_1088": 264, "V2_hot_vs_1088": 0, "V2_hot_vs_1056": 264,
            "V3_hot_vs_2096": 16, "V3_hot_vs_1088": 0,
            "V1_step_gcd": 1088, "V2_step_gcd": 1056, "V1_hot_min": 1088, "V2_hot_min": 1056},
    "C57": {"S0_hot_n": 880, "S0_hot_multiple_of_unit": 880, "S0_gcd_cached": 64, "S0_odd_unit": 351,
            "S1_hot_n": 880, "S1_hot_multiple_of_unit": 880, "S1_gcd_cached": 64, "S1_odd_unit": 351,
            "S2_hot_n": 880, "S2_hot_multiple_of_unit": 880, "S2_gcd_cached": 128, "S2_odd_unit": 478,
            "S1_vs_S0_paired": 888, "S1_vs_S0_identical": 887},
    "C58": {"paired_rows": 900, "identical": 534, "S2_lower_by_64": 353, "S2_higher": 13,
            "delta_set": [-64, 0, 832, 896],
            "mean_uncached_S1": 740.4, "mean_uncached_S2": 752.58,
            "ttft_ratio_median": 1.005, "ttft_ratio_min": 0.435, "ttft_ratio_max": 45.798},
    "C59": {"rows_total": 289, "hot_n": 10, "gcd_cached": 64, "hot_multiple_of_unit": 10, "odd_unit": 3,
            "phase_P": 259, "phase_R": 30,
            "disable_chunked_prefix_cache": True, "radix_eviction_policy": "slru",
            "max_mamba_cache_size": 64, "token_capacity": 1480094,
            "pressure_ratio": 1.505083, "docs_pushed": 259,
            "band_newest_hits": 10, "band_newest_n": 10,
            "band_middle_hits": 0, "band_middle_n": 10,
            "band_oldest_hits": 0, "band_oldest_n": 10},
    "C60": {"TUNED_mean_uncached": 8305.0, "TUNED_hit_fraction": 0.034474,
            "S0_mean_uncached": 739.25, "S0_hit_fraction": 0.974242,
            "TUNED_over_S0_per_turn": 11.2344, "V1_over_S0_per_turn": 3.0176,
            "V1_over_TUNED_per_turn": 0.2686, "grid_units_distinct": 5},
    # C62 -- G3-LIMIT-V2, the compaction boundary measured live (MANUSCRIPT SS 6a).  Each
    # per-arm row is (budget, arm, post-boundary delta vs its matched baseline, its bootstrap
    # CI, the pre-boundary delta, the arm's compaction turns, the boundary turn's uncached
    # tokens, the baseline's own window-drop turn's uncached tokens).
    "C62": {"rows": 2780, "arm_kinds": 12, "compaction_rows": 18,
            "compacting_arms_at_32k": 6, "compacting_arms_at_64k": 6,
            # ``post_delta_min``/``max`` are the min and max of twelve 27-89-turn ARM
            # MEANS.  They are kept, but they are NOT the band the prose needs: twelve
            # averages cannot bound a per-turn range, and the smallest arm mean sits 7x
            # above the smallest turn and the largest 3x below the largest.
            "post_delta_min": 134.6, "post_delta_max": 747.2,
            # The per-turn band those means are routinely mistaken for: every matched-turn
            # difference in the twelve post-boundary segments.  Pinned here because
            # ``post_turn_band`` (below) pins it per arm and a rewrite could otherwise keep
            # the tables and move the aggregate the prose quotes.
            "post_turn_delta_min": -927.0, "post_turn_delta_max": 5473.0,
            "post_turns_below_zero": 12,
            "post_deltas_all_positive": True, "post_ci_zero_crossings": 1,
            "pre_delta_min": -11.8, "pre_delta_max": 51.0, "pre_ci_excludes_zero": 0,
            "baseline_window_drop_rows": 18,
            # The two bands the prose quotes around the boundary, derived over ALL rows.
            # Pinned so "1,826-2,972" (first-compaction-only) and "1,236-1,246"
            # (first-drop-only) fail here if anyone hand-copies them back.
            "boundary_turn_uncached_min": 1826, "boundary_turn_uncached_max": 3033,
            "boundary_turn_rows": 18,
            "baseline_drop_uncached_min": 1236, "baseline_drop_uncached_max": 1321,
            "baseline_drop_turns": 6,
            "first_turn_32k": [71], "first_turn_64k": [143],
            "per_arm": (
                ("32k", "S", 390.2, (239.4, 542.1), -10.7, (71, 137), 2846, 1236),
                ("32k", "F", 578.1, (451.4, 709.6), 27.3, (71, 137), 2968, 1236),
                ("32k", "S-k800", 522.0, (410.3, 632.0), -11.7, (71, 140), 1849, 1236),
                ("32k", "F-k800", 526.6, (412.3, 641.0), -11.8, (71, 139), 1972, 1236),
                ("32k", "S-ptr", 278.1, (161.9, 401.7), 51.0, (71, 137), 2842, 1237),
                ("32k", "F-ptr", 134.6, (-12.8, 285.9), 13.0, (71, 137), 2972, 1237),
                ("64k", "S", 700.2, (475.2, 997.7), -5.6, (143,), 2815, 1246),
                ("64k", "F", 747.2, (598.7, 900.2), -11.1, (143,), 2945, 1246),
                ("64k", "S-k800", 697.1, (571.6, 824.7), -4.5, (143,), 1826, 1246),
                ("64k", "F-k800", 653.5, (482.0, 822.0), -11.1, (143,), 1954, 1246),
                ("64k", "S-ptr", 739.6, (595.7, 889.7), 5.6, (143,), 2817, 1244),
                ("64k", "F-ptr", 346.4, (141.2, 559.6), 5.6, (143,), 2948, 1244),
            ),
            # (budget, last-turn prompt of B, then of S, S-ptr, F, F-ptr, S-k800, F-k800)
            "resting_window": (
                ("32k", 9896, 13325, 13321, 13542, 13546, 11009, 11717),
                ("64k", 22063, 23632, 23634, 23762, 23765, 22643, 14197),
            ),
            # THE BAND, per turn.  (budget, arm, smallest matched-turn difference in the
            # arm's post-boundary segment, largest, the same pair with the turns that
            # follow one of the baseline's own window drops removed, and how many turns
            # that leaves).  This is the band every reader-facing sentence has to quote.
            "post_turn_band": (
                ("32k", "S", -54.0, 1919.0, -54.0, 1919.0, 87),
                ("32k", "F", -60.0, 2200.0, -60.0, 2200.0, 87),
                ("32k", "S-k800", -487.0, 1395.0, -487.0, 1395.0, 87),
                ("32k", "F-k800", -35.0, 1335.0, -35.0, 1335.0, 87),
                ("32k", "S-ptr", -59.0, 1914.0, -59.0, 1914.0, 87),
                ("32k", "F-ptr", -57.0, 2203.0, -57.0, 2203.0, 87),
                # 64k S's extremes are its transition turn's neighbours' (144 -> 5,473;
                # 146 -> -927).  The split re-weights the arm MEAN and leaves the band's
                # ends alone, which is why the two pairs agree for all twelve arms.
                ("64k", "S", -927.0, 5473.0, -927.0, 5473.0, 46),
                ("64k", "F", -29.0, 1699.0, -29.0, 1699.0, 46),
                ("64k", "S-k800", -60.0, 964.0, -60.0, 964.0, 46),
                ("64k", "F-k800", -60.0, 964.0, -60.0, 964.0, 26),
                ("64k", "S-ptr", -27.0, 1573.0, -27.0, 1573.0, 46),
                ("64k", "F-ptr", -856.0, 1704.0, -856.0, 1704.0, 46),
            ),
            # (budget, arm, post-boundary delta, the same on resting turns only)
            "post_steady": (
                ("32k", "S", 390.2, 375.1), ("32k", "F", 578.1, 566.4),
                ("32k", "S-k800", 522.0, 515.6), ("32k", "F-k800", 526.6, 524.7),
                ("32k", "S-ptr", 278.1, 260.5), ("32k", "F-ptr", 134.6, 112.5),
                ("64k", "S", 700.2, 681.3), ("64k", "F", 747.2, 726.5),
                ("64k", "S-k800", 697.1, 699.7), ("64k", "F-k800", 653.5, 651.4),
                ("64k", "S-ptr", 739.6, 721.5), ("64k", "F-ptr", 346.4, 316.9),
            ),
            # The same measures with the turn after each baseline window drop removed: for
            # every arm but 64k S the pair is unchanged (their extremes are not transitions),
            # which is the point -- the split does NOT thin the band, it only re-weights the
            # arm means.  Kept as its own row so a future cell cannot quietly redefine it.
            "post_transitions": (
                ("32k", "S", (72, 142)), ("32k", "F", (72, 142)),
                ("32k", "S-k800", (72, 142)), ("32k", "F-k800", (72, 142)),
                ("32k", "S-ptr", (72, 142)), ("32k", "F-ptr", (72, 142)),
                ("64k", "S", (144,)), ("64k", "F", (144,)),
                ("64k", "S-k800", (144,)), ("64k", "F-k800", (144,)),
                ("64k", "S-ptr", (144,)), ("64k", "F-ptr", (144,)),
            )},
    # C63 -- MATRIX-FOLD, the 2x2 model x engine matrix (MANUSCRIPT SS 9b).  Cells are
    # (model, engine, n, hit, uncached/turn, gcd of hot cached_tokens).  The four arms at
    # 32k are replicates (no compaction fires), so the effects resample the 71 TURNS, not
    # the 284 (arm, turn) rows; ``positive`` counts turns, not rows.
    "C63": {
        "rows_total": 1136, "rows_per_cell": 284, "paired_turns": 71,
        "chars_equal_pairs": 6, "chars_equal_rows": 284,
        "prefix_equal_pairs": 6, "prefix_equal_rows": 284,
        "prompt_token_deltas": (-4, 0, 4),
        "cells": (
            ("occamy-1.0", "vllm", 284, 0.901212, 1682.7218, 2096),
            ("occamy-1.0", "sglang", 284, 0.957153, 729.7641, 64),
            ("qwen3.5-9b", "vllm", 284, 0.869037, 2230.7782, 1088),
            ("qwen3.5-9b", "sglang", 284, 0.956941, 733.3697, 64),
        ),
        "cell_mean_grand": 1344.1585,
        "engine_effect": 1225.18, "engine_ci": (1132.2, 1313.3),
        "engine_positive_turns": 70,
        "model_effect": 275.83, "model_ci": (194.3, 357.6),
        "model_positive_turns": 53,
        "interaction": 272.23, "interaction_ci": (190.1, 354.6),
        "interaction_positive_turns": 52,
        # Per-level slices: the engine effect inside each model, the model effect inside
        # each engine.  The second pair is the interaction read as a sentence -- the model
        # effect is 152x larger under vLLM than under SGLang.
        #
        # The ratio below is divided from the per-turn MEANS (m_vllm_s / m_sgl_s), never from
        # the printed cell means: raw 548.056338028169 / 3.6056338028169015 = 152.0, while the
        # ROUNDED operands give 548.06 / 3.61 = 151.8172 (FIX-1518).  The claim quotes it at
        # 4 dp, so 152.0 is the truthful figure; tests/test_c63_ratio_raw_operands.py pins it.
        "engine_moe": 952.96, "engine_moe_ci": (805.7, 1099.8),
        "engine_moe_positive_turns": 67,
        "engine_dense": 1497.41, "engine_dense_ci": (1404.4, 1585.0),
        "engine_dense_positive_turns": 70,
        "model_vllm": 548.06, "model_vllm_ci": (384.7, 711.9),
        "model_vllm_positive_turns": 52,
        "model_sglang": 3.61, "model_sglang_ci": (0.0, 10.8),
        "model_sglang_positive_turns": 1,
        "engine_ratio_moe": 2.3058, "engine_ratio_dense": 3.0418,
        "engine_ratio_mean": 2.6738,
        "model_ratio_vllm": 1.3257, "model_ratio_sglang": 1.0049,
        "model_ratio_mean": 1.1653,
        "engine_over_model": 4.4418,
        "engine_share_of_grand": 0.9115, "model_share_of_grand": 0.2052,
        "model_effect_ratio_vllm_over_sglang": 152.0,
        # Replicate-arm check: the engine effect is flat across the four arms (1216-1230)
        # and the model effect is flat at ~274-281, so neither effect rides on one salt.
        "per_arm_engine": (("R", 1226.1), ("A", 1229.7), ("C", 1216.2), ("H", 1228.8)),
        "per_arm_model": (("R", 281.2), ("A", 274.0), ("C", 274.0), ("H", 274.0)),
    },
}

#: C62's tuple-valued keys are TABLES: each element is one row of printed figures and is
#: compared at the tolerance in ``TUPLE_CLAIMS``.  Pinned as tuples so a rewrite that keeps the
#: range but drops an arm fails in ``check()`` rather than passing on the surviving rows.
TUPLE_CLAIMS = {"C62": 0.05}
C62_REGIONS = ("32k", "64k")
C62_ARMS = ("S", "F", "S-k800", "F-k800", "S-ptr", "F-ptr")


def _ca(got: dict, region: str, arm: str, key: str) -> object:
    return got["per_arm"][f"{region} {arm}"][key]


def _c62_flatten(got: dict) -> dict:
    """Project ``c62()``'s nested dicts onto the pinned tuple rows."""
    flat = {k: v for k, v in got.items() if not isinstance(v, dict)}
    flat["per_arm"] = tuple(
        (region, arm,
         got["per_arm"][f"{region} {arm}"]["post_delta"],
         tuple(got["per_arm"][f"{region} {arm}"]["post_ci"]),
         got["per_arm"][f"{region} {arm}"]["pre_delta"],
         tuple(got["per_arm"][f"{region} {arm}"]["compaction_turns"]),
         got["per_arm"][f"{region} {arm}"]["boundary_uncached"],
         got["per_arm"][f"{region} {arm}"]["baseline_drop_uncached"])
        for region in C62_REGIONS
        for arm in C62_ARMS
    )
    flat["resting_window"] = tuple(
        (region, got["resting_window"][region]["last_prompt_B"],
         *[got["resting_window"][region]["last_prompt_arms"][arm]
           for arm in ("S", "S-ptr", "F", "F-ptr", "S-k800", "F-k800")])
        for region in C62_REGIONS
    )
    # (budget, arm, smallest turn delta, largest turn delta, smallest/largest with the
    # transitions out, resting-turn count).  A band checked only globally would pass on
    # whichever arm happened to carry its ends, so every arm's own pair is pinned.
    flat["post_turn_band"] = tuple(
        (region, arm,
         _ca(got, region, arm, "post_turn_delta_min"),
         _ca(got, region, arm, "post_turn_delta_max"),
         _ca(got, region, arm, "post_steady_turn_min"),
         _ca(got, region, arm, "post_steady_turn_max"),
         _ca(got, region, arm, "post_steady_turns"))
        for region in C62_REGIONS
        for arm in C62_ARMS
    )
    flat["post_transitions"] = tuple(
        (region, arm, tuple(_ca(got, region, arm, "post_transition_turns")))
        for region in C62_REGIONS
        for arm in C62_ARMS
    )
    flat["post_steady"] = tuple(
        (region, arm,
         _ca(got, region, arm, "post_delta"),
         _ca(got, region, arm, "post_steady_delta"))
        for region in C62_REGIONS
        for arm in C62_ARMS
    )
    return flat


#: Projections that turn a function's nested output into the flat dict ``check()`` compares.
FLATTEN = {"C62": _c62_flatten}

TOLERANCE = {
    "C05": 1e-4, "C06": 1e-4, "C08": 1e-4, "C15": 0.5, "C21": 1e-4, "C22": 1e-4,
    "C24": 1e-4, "C25": 1e-4, "C27": 0.05, "C28": 0.05, "C29": 0.05, "C30": 0.05,
    "C31": 0.05, "C32": 0.05, "C33": 1e-3, "C34": 1e-3, "C35": 1e-3,
    "C46": 1e-4, "C47": 1e-4, "C49": 1e-9, "C50": 1e-4, "C51": 1e-4,
    "C53": 1e-9, "C54": 1e-6, "C58": 1e-3, "C60": 1e-4, "C63": 1e-6,
}

FUNCS = {
    "C02": c02, "C03": c03, "C04": c04, "C05": c05, "C06": c06,
    "C07": c07, "C08": c08, "C09": c09, "C10": c10,
    "C11": c11, "C12": c12, "C13": c13, "C14": c14, "C15": c15,
    "C17": c17, "C18": c18, "C19": c19, "C20": c20, "C21": c21, "C22": c22, "C23": c23,
    "C24": c24, "C25": c25, "C26": c26,
    "C27": c27, "C28": c28, "C29": c29, "C30": c30, "C31": c31, "C32": c32, "C33": c33,
    "C34": c34, "C35": c35, "C36": c36,
    "C37": c37, "C38": c38, "C39": c39,
    "C40": c40, "C41": c41, "C42": c42, "C43": c43, "C44": c44,
    "C45": c45, "C46": c46, "C47": c47, "C48": c48, "C49": c49, "C50": c50,
    "C51": c51, "C52": c52, "C53": c53, "C54": c54,
    "C55": c55, "C56": c56, "C57": c57, "C58": c58, "C59": c59, "C60": c60,
    "C62": c62, "C63": c63,
}


def close(got: object, want: object, tol: float) -> bool:
    if isinstance(want, bool) or isinstance(want, str) or isinstance(want, list):
        return got == want
    if isinstance(want, (int, float)):
        return abs(float(got) - float(want)) <= max(tol, abs(float(want)) * tol)
    if isinstance(want, tuple):
        if not isinstance(got, (tuple, list)) or len(got) != len(want):
            return False
        return all(close(g, w, tol) for g, w in zip(got, want))
    return got == want


def check(claim: str) -> int:
    got = FUNCS[claim]()
    got = FLATTEN[claim](got) if claim in FLATTEN else got
    want = EXPECTED[claim]
    tol = TOLERANCE.get(claim, 1e-9)
    failed = 0
    print(f"{claim}  sources: see CLAIMS.md")
    for key, expected in want.items():
        actual = got.get(key)
        ok = close(actual, expected, tol)
        failed += 0 if ok else 1
        mark = "OK  " if ok else "FAIL"
        print(f"  {mark} {key:34s} recomputed={actual!r:26s} paper={expected!r}")
    print(f"  {'PASS' if not failed else 'FAIL'}  {len(want) - failed}/{len(want)} values match")
    return 0 if not failed else 1


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] in ("-h", "--help"):
        print(__doc__)
        print("claims:", " ".join(FUNCS))
        return 0
    claims = argv[1:]
    if claims == ["all"]:
        claims = list(FUNCS)
    if claims and claims[0] == "grid-guard":
        return grid_guard()
    status = 0
    for claim in claims:
        if claim not in FUNCS and claim not in SPECIAL:
            print(f"unknown claim {claim!r}; known: {' '.join(list(FUNCS) + list(SPECIAL))}")
            return 2
        if claim in SPECIAL:
            status |= SPECIAL[claim]()
            continue
        status |= check(claim)
    # A claim whose config_id has no rows in any cell must fail the whole run,
    # not merely argue with its expected value.
    if any(c in GRID_CLAIMS for c in claims):
        status |= grid_guard()
    if len(claims) > 1:
        print(f"\n{len(claims)} claims checked, {'all match' if status == 0 else 'MISMATCH'}")
    # A full run must also account for every claim in the package, not merely
    # the ones it was told to check: a claim in CLAIMS.md with no runner and a
    # runner with no claim row are both silent coverage holes today.
    if claims == list(FUNCS):
        status |= coverage_guard()
    return status


PKG_DIR = Path(__file__).resolve().parent
ROOT_DIR = PKG_DIR.parents[1]
CLAIMS_MD_PATH = PKG_DIR / "CLAIMS.md"


def coverage_ids() -> list[str]:
    """Claim ids as the first cell of a CLAIMS.md table row, in file order."""
    text = CLAIMS_MD_PATH.read_text(encoding="utf-8")
    return re.findall(r"^\|\s*(C\d{2})\s*\|", text, re.MULTILINE)


# A row whose first cell is one of these is not a claim: the title rows of the
# claim tables, their separators, the source-key table, and the numbered
# "Corrections to the source cards" table. Anything else must be a claim row.
NONCLAIM_HEADERS = ("#", "Abbrev")
SOURCE_KEY_SECTION = "Source rows and digests"
NONCLAIM_COUNTER = re.compile(r"\d{1,3}")


def surface_defects() -> list[str]:
    """CLAIMS.md table rows the claim census cannot see.

    Every count here is derived by finding rows whose first cell matches
    ``C\\d{2}``, so a row whose first cell is neither that nor a declared source
    key was invisible: it passed this guard and `verify_package.py` while sitting
    unchecked in the claim ledger. Refusing such a row, rather than skipping it,
    is what makes "every documented claim has a runner" mean every row.
    """
    defects: list[str] = []
    section = ""
    for lineno, line in enumerate(CLAIMS_MD_PATH.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            first = cells[0] if cells else ""
            if re.fullmatch(r"C\d{2}", first):
                continue
            if first in NONCLAIM_HEADERS or set(first) <= set("-: "):
                continue
            if section == SOURCE_KEY_SECTION and len(cells) == 5:
                continue  # a declared source key: abbrev, path, bytes, rows, sha256
            if len(cells) == 4 and NONCLAIM_COUNTER.fullmatch(first):
                continue  # the numbered corrections table
            defects.append(f"CLAIMS.md:{lineno} first cell {first!r}, under {section or 'no section'!r}")
            continue
        if stripped.startswith("**") and stripped.count("**") >= 2:
            # a bold lead-in on its own line opens a section, so the source-key
            # table can be declared by a heading even when it is not an ATX one
            section = stripped.split("**")[1].strip().rstrip(".").strip()
        elif re.match(r"#{1,6}\s", stripped):
            section = re.sub(r"^#{1,6}\s+", "", stripped).strip().rstrip(".").strip()
    return defects


UNRUNNABLE: list[str] = []


def script_backed() -> dict[str, Path]:
    """Claims CLAIMS.md says are recomputed by a checked-in script, and that script.

    The command is read from the claim's own row in CLAIMS.md, so the exemption
    is declared by the document and checked against disk -- never hard-coded here.

    A row with five cells whose command names no ``.py`` is **recorded**, not
    crashed on: this used to be ``re.search(...).group(1)`` and raised
    ``AttributeError: 'NoneType' object has no attribute 'group'`` on the first
    row anyone added with a non-script command -- the shape every new claim is
    written in.  The row was caught (exit 1) but only as a traceback, so the
    guard never said *why*.  ``UNRUNNABLE`` carries it to ``coverage_guard``.
    """
    del UNRUNNABLE[:]
    rows: dict[str, Path] = {}
    for lineno, line in enumerate(CLAIMS_MD_PATH.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 5 or not re.fullmatch(r"C\d{2}", cells[0]):
            continue
        command = re.search(r"(\S+\.py)", cells[4])
        if command is None:
            UNRUNNABLE.append(f"{cells[0]} (CLAIMS.md:{lineno}, command {cells[4][:40]!r})")
            continue
        rel = command.group(1).strip("`")
        path = Path(rel)
        if not path.is_absolute():
            path = (ROOT_DIR / rel).resolve()
        if path == (PKG_DIR / "recompute.py").resolve():
            continue  # an ordinary FUNCS runner, not an external script
        rows[cells[0]] = path
    return rows


def coverage_guard() -> int:
    """Loudly fail if the claim census and the runnable census disagree.

    Derived, never asserted: every id is read from CLAIMS.md, every runner from
    FUNCS / SPECIAL. A prose count in CLAIMS.md or PACKAGE.md is not consulted.
    """
    documented = coverage_ids()
    runners = set(FUNCS) | set(SPECIAL)
    scripts = script_backed()
    bad = 0
    invisible = surface_defects()
    if invisible:
        bad += 1
        print(f"COVERAGE GUARD FAIL  {len(invisible)} CLAIMS.md row(s) invisible to the census, "
              f"so unchecked by this run:")
        for defect in invisible:
            print(f"  - {defect}")
    else:
        print("COVERAGE GUARD ok    every CLAIMS.md table row is a claim row or a declared "
              "source key (nothing invisible to the census)")
    unrun = [c for c in dict.fromkeys(documented) if c not in runners and c not in scripts]
    missing_script = [f"{c} -> {scripts[c]}" for c in sorted(scripts) if not scripts[c].is_file()]
    if unrun:
        bad += 1
        print(f"COVERAGE GUARD FAIL  no runner for {len(unrun)} claim(s): {', '.join(unrun)}")
    else:
        print(f"COVERAGE GUARD ok    every documented claim has a runner: {len(documented)}/{len(documented)}"
              f" ({len(runners)} in recompute.py, {len(scripts)} script-backed)")
    if UNRUNNABLE:
        bad += 1
        print(f"COVERAGE GUARD FAIL  {len(UNRUNNABLE)} claim row(s) whose command names no "
              f".py script (so this run cannot tell whether a runner exists):")
        for row in UNRUNNABLE:
            print(f"  - {row}")
    # Every count above is blind to a row that vanished *above* the maximum id: a
    # lost C40 leaves the census 61 ids that still agree with 61 runners.  The ids
    # are C01..C(n) by construction, so a gap is a defect.
    numbered = [int(c[1:]) for c in dict.fromkeys(documented)]
    gaps = [f"C{n:02d}" for n in range(1, max(numbered) + 1) if n not in numbered] if numbered else []
    if gaps:
        bad += 1
        print(f"COVERAGE GUARD FAIL  claim-id gap(s) below the maximum C{max(numbered):02d}: "
              f"{', '.join(gaps)}")
    else:
        print(f"COVERAGE GUARD ok    claim ids are contiguous C01..C{max(numbered):02d} "
              f"(no row lost above the maximum)")
    if missing_script:
        bad += 1
        print(f"COVERAGE GUARD FAIL  script-backed claim(s) with no script on disk: {'; '.join(missing_script)}")
    orphan = sorted(runners - set(documented))
    if orphan:
        bad += 1
        print(f"COVERAGE GUARD FAIL  runner for undocumented claim(s): {', '.join(orphan)}")
    else:
        print(f"COVERAGE GUARD ok    every runner has a claim row: {len(runners)}/{len(runners)}")
    dupes = sorted({c for c in documented if documented.count(c) > 1})
    if dupes:
        bad += 1
        print(f"COVERAGE GUARD FAIL  duplicate claim row(s) in CLAIMS.md: {', '.join(dupes)}")
    if set(documented) == runners | set(scripts):
        print(f"COVERAGE GUARD ok    census matches runner set: {len(documented)} ids")
    else:
        bad += 1
        print(f"COVERAGE GUARD FAIL  census {len(documented)} ids != runners {len(runners | set(scripts))}")
    if bad:
        print(f"COVERAGE GUARD FAIL  {bad} coverage defect(s)")
        return 1
    print(f"COVERAGE GUARD PASS  {len(documented)} claims documented, "
          f"{len(runners)} runnable here + {len(scripts)} script-backed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
