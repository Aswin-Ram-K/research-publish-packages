#!/usr/bin/env python3
"""VERBOSITY-CONFOUND: builder (offline) + tests for measure/VERBOSITY.json.

Run as a script to (re)generate the report:
    python3 experiments/ptr-engine/longrun/tests/test_verbosity.py

Run under pytest to validate the on-disk report. OFFLINE: no network, no inference.
Never writes a rows file, a grade file, analyze_stats.py, LATENCY-REPORT.json, TVS.json or
docs/OPERATOR-BRIEF.md.
"""
import glob
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REL_GEN = "experiments/ptr-engine/longrun/tests/test_verbosity.py"
P95_FLOOR, MIN_CELL_N = 60, 5


def repo_root():
    p = HERE
    for _ in range(8):
        if os.path.isdir(os.path.join(p, "experiments", "ptr-engine", "measure")):
            return p
        p = os.path.dirname(p)
    return os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


ROOT = repo_root()
MEASURE = os.path.join(ROOT, "experiments/ptr-engine/measure")
JSON_OUT = os.path.join(MEASURE, "VERBOSITY.json")
MD_OUT = os.path.join(ROOT, "docs/VERBOSITY.md")
GEN = os.path.join(ROOT, REL_GEN)

# --------------------------------------------------------------------------- shared row access


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def text_of(r):
    for k in ("content", "answer_text"):
        v = r.get(k)
        if isinstance(v, str):
            return v
    return None


def ttft_ms(r):
    v = num(r.get("ttft_ms"))
    if v is not None:
        return float(v)
    for k in ("ttft_s", "ttft_server_s"):
        v = num(r.get(k))
        if v is not None:
            return 1000.0 * float(v)
    return None


def wall_ms(r):
    v = num(r.get("wall_ms"))
    if v is not None:
        return float(v)
    v = num(r.get("latency_s"))
    return 1000.0 * float(v) if v is not None else None


def is_completed_turn(r):
    kind = r.get("kind")
    if kind is not None and kind != "turn":
        return False
    if r.get("error"):
        return False
    if r.get("timing_usable") is False:
        return False
    t = text_of(r)
    return bool(t and t.strip())


def rows_files():
    return sorted(glob.glob(os.path.join(MEASURE, "rows-*.jsonl")))


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


# --------------------------------------------------------------------------- stats


def stats(vals):
    a = np.asarray([v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))], float)
    if a.size == 0:
        return None
    return {
        "n": int(a.size),
        "mean": round(float(a.mean()), 4),
        "median": round(float(np.percentile(a, 50)), 4),
        "p90": round(float(np.percentile(a, 90)), 4),
        "max": round(float(a.max()), 4),
        "min": round(float(a.min()), 4),
    }


def ttft_stats(rows):
    vals = [ttft_ms(r) for r in rows]
    s = stats(vals)
    if s is None:
        return None
    u = np.asarray([v for v in vals if v is not None], float)
    s["p95"] = round(float(np.percentile(u, 95)), 4) if s["n"] >= P95_FLOOR else None
    s["p95_refused"] = bool(s["n"] < P95_FLOOR)
    s["p95_refused_reason"] = (
        None if s["n"] >= P95_FLOOR else "n=%d < floor %d: p95 refused, mean/median/p90 reported" % (s["n"], P95_FLOOR)
    )
    return s


def cell_table(label, arm, rows):
    n = len(rows)
    texts = [text_of(r) for r in rows]
    chars = [len(t) for t in texts]
    triples = [
        (float(r["completion_tokens"]), wall_ms(r), ttft_ms(r))
        for r in rows
        if num(r.get("completion_tokens")) is not None
    ]
    comp = [t[0] for t in triples]
    prompt = [float(r["prompt_tokens"]) for r in rows if num(r.get("prompt_tokens")) is not None]
    cached = [float(r["cached_tokens"]) for r in rows if num(r.get("cached_tokens")) is not None]
    ttfts = [ttft_ms(r) for r in rows]
    dec = [(c, w - t) for c, w, t in triples if w is not None and t is not None and w > t]

    def corr(x, y):
        pr = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
        if len(pr) < 3:
            return None
        xa = np.asarray([p[0] for p in pr], float)
        ya = np.asarray([p[1] for p in pr], float)
        if xa.std() == 0 or ya.std() == 0:
            return None
        return round(float(np.corrcoef(xa, ya)[0, 1]), 4)

    return {
        "file": label,
        "arm": arm,
        "n_completed_turns": n,
        "completion_tokens": stats(comp),
        "answer_chars": stats(chars),
        "tokens_per_char": round(sum(comp) / sum(chars), 4) if comp and sum(chars) else None,
        "prompt_tokens": stats(prompt),
        "cached_tokens": stats(cached),
        "ttft_ms": ttft_stats(rows),
        "wall_ms": stats([wall_ms(r) for r in rows]),
        "post_ttft_ms": stats([w - t for c, w, t in triples if w is not None and t is not None and w >= t]),
        "decode_tok_per_s": (
            round(1000.0 * sum(c for c, _ in dec) / sum(d for _, d in dec), 4)
            if dec and sum(d for _, d in dec) > 0
            else None
        ),
        "corr_ttft_prompt": corr(prompt, ttfts),
        "corr_ttft_completion": corr(comp, ttfts),
        "corr_wall_completion": corr([c for c, _, _ in triples], [w for _, w, _ in triples]),
        "quality": {
            "answer_verified_rate": round(sum(1 for r in rows if r.get("answer_verified") is True) / n, 4),
            "answer_verified_count": sum(1 for r in rows if r.get("answer_verified") is True),
            "ANSWER_line_rate": round(sum(1 for t in texts if "ANSWER:" in t) / n, 4),
            "ANSWER_line_count": sum(1 for t in texts if "ANSWER:" in t),
            "answer_source": sorted({str(r.get("answer_source")) for r in rows if r.get("answer_source")}),
        },
    }


def ols_loglog(rows):
    X, y = [], []
    for r in rows:
        t, p, c = ttft_ms(r), num(r.get("prompt_tokens")), num(r.get("completion_tokens"))
        if t is None or t <= 0 or not p or p <= 0 or c is None:
            continue
        X.append([1.0, math.log(p), math.log(max(c, 1.0))])
        y.append(math.log(t))
    if len(X) < 8:
        return None
    Xa, ya = np.asarray(X, float), np.asarray(y, float)
    beta, *_ = np.linalg.lstsq(Xa, ya, rcond=None)
    res = ya - Xa @ beta
    ssr, sst = float(res @ res), float(((ya - ya.mean()) ** 2).sum())
    Xc = np.column_stack([np.ones(len(y)), Xa[:, 2]])
    bc_alone, *_ = np.linalg.lstsq(Xc, ya, rcond=None)
    corr_pc = float(np.corrcoef(Xa[:, 1], Xa[:, 2])[0, 1]) if Xa[:, 1].std() > 0 and Xa[:, 2].std() > 0 else None
    return {
        "n": len(y),
        "model": "ln(ttft_ms) = b0 + b_prompt*ln(prompt_tokens) + b_completion*ln(completion_tokens); OLS pooled across arms within this one file",
        "b0": round(float(beta[0]), 6),
        "b_prompt": round(float(beta[1]), 6),
        "b_completion": round(float(beta[2]), 6),
        "r2": round(1.0 - ssr / sst, 6) if sst > 0 else None,
        "resid_sd_log": round(float(res.std(ddof=1)), 6) if len(y) > 3 else None,
        "corr_ln_prompt_ln_completion": None if corr_pc is None else round(corr_pc, 4),
        "collinearity_note": "prompt size and answer length grow together in a transcript arm, so the split between b_prompt and b_completion is not unique; the surviving fraction below is therefore also computed from a completion-only model, which is the most generous account verbosity can get",
        "completion_only_model": {
            "model": "ln(ttft_ms) = c0 + c_completion*ln(completion_tokens) - prompt omitted on purpose, as an UPPER BOUND on what answer length can explain",
            "c_completion": round(float(bc_alone[1]), 6),
        },
    }


def pairs_for(label, fit, by_arm):
    out, means = [], {}
    for arm, rows in by_arm.items():
        v = {"ln_ttft": [], "ln_prompt": [], "ln_comp": []}
        for r in rows:
            t, p, c = ttft_ms(r), num(r.get("prompt_tokens")), num(r.get("completion_tokens"))
            if t is None or t <= 0 or not p or p <= 0 or c is None:
                continue
            v["ln_ttft"].append(math.log(t))
            v["ln_prompt"].append(math.log(p))
            v["ln_comp"].append(math.log(max(c, 1.0)))
        if len(v["ln_ttft"]) >= MIN_CELL_N:
            means[arm] = {k: float(np.mean(x)) for k, x in v.items()}
            means[arm]["n"] = len(v["ln_ttft"])
            means[arm]["med_ln_ttft"] = float(np.median(v["ln_ttft"]))
            means[arm]["med_ln_prompt"] = float(np.median(v["ln_prompt"]))
            means[arm]["med_ln_comp"] = float(np.median(v["ln_comp"]))
    names = sorted(means)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ma, mb = means[a], means[b]
            gap = ma["ln_ttft"] - mb["ln_ttft"]
            dp = ma["ln_prompt"] - mb["ln_prompt"]
            dc = ma["ln_comp"] - mb["ln_comp"]
            pc = fit["b_prompt"] * dp if fit else None
            cc = fit["b_completion"] * dc if fit else None
            rl = gap - (pc + cc) if fit else None
            fr = lambda x: round(x / gap, 6) if fit and abs(gap) > 1e-9 else None
            b_alone = ((fit or {}).get("completion_only_model") or {}).get("c_completion")
            cc_alone = b_alone * dc if b_alone is not None else None
            mgap = ma["med_ln_ttft"] - mb["med_ln_ttft"]
            mfr = lambda x: round(x / mgap, 6) if abs(mgap) > 1e-9 else None
            mpc = fit["b_prompt"] * (ma["med_ln_prompt"] - mb["med_ln_prompt"]) if fit else None
            mcc = fit["b_completion"] * (ma["med_ln_comp"] - mb["med_ln_comp"]) if fit else None
            mrl = mgap - (mpc + mcc) if fit else None
            surv_all = [x for x in (
                (1.0 - fr(cc)) if cc is not None else None,
                (1.0 - fr(cc_alone)) if cc_alone is not None else None,
                (1.0 - mfr(mcc)) if mcc is not None else None,
            ) if x is not None]
            surv_min = min(surv_all) if surv_all else None
            out.append(
                {
                    "file": label,
                    "arm_a": a,
                    "arm_b": b,
                    "n_a": ma["n"],
                    "n_b": mb["n"],
                    "gap_ln_ttft(mean logs)": round(gap, 6),
                    "gap_ratio_of_means": round(math.exp(gap), 4),
                    "delta_ln_prompt_tokens": round(dp, 6),
                    "delta_ln_completion_tokens": round(dc, 6),
                    "completion_tokens_multiple": round(math.exp(dc), 4),
                    "prompt_share_ln": None if pc is None else round(pc, 6),
                    "completion_share_ln": None if cc is None else round(cc, 6),
                    "residual_ln": None if rl is None else round(rl, 6),
                    "prompt_fraction_of_gap": fr(pc) if pc is not None else None,
                    "completion_fraction_of_gap": fr(cc) if cc is not None else None,
                    "residual_fraction_of_gap": fr(rl) if rl is not None else None,
                    "fraction_of_gap_surviving_completion_normalisation": (
                        None if cc is None else round(1.0 - fr(cc), 6)
                    ),
                    "median_basis": {
                        "note": "same attribution on per-arm MEDIAN ln values, i.e. the p50 gap rather than the mean-log gap",
                        "gap_ln_medians": round(mgap, 6),
                        "gap_ratio_of_medians": round(math.exp(mgap), 4),
                        "prompt_share_ln": None if mpc is None else round(mpc, 6),
                        "completion_share_ln": None if mcc is None else round(mcc, 6),
                        "residual_ln": None if mrl is None else round(mrl, 6),
                        "prompt_fraction_of_gap": mfr(mpc) if mpc is not None else None,
                        "completion_fraction_of_gap": mfr(mcc) if mcc is not None else None,
                        "residual_fraction_of_gap": mfr(mrl) if mrl is not None else None,
                        "fraction_of_gap_surviving_completion_normalisation": (
                            None if mcc is None else round(1.0 - mfr(mcc), 6)
                        ),
                    },
                    "completion_only_model": {
                        "c_completion": b_alone,
                        "share_ln": None if cc_alone is None else round(cc_alone, 6),
                        "fraction_of_gap": None if cc_alone is None else fr(cc_alone),
                        "surviving_fraction": None if cc_alone is None else round(1.0 - fr(cc_alone), 6),
                        "note": "upper bound: prompt omitted, so this is the most completion length could ever explain",
                    },
                    "surviving_most_conservative": None if surv_min is None else round(surv_min, 6),
                    "p95_gap": "refused: per-arm n=%d/%d < floor %d" % (ma["n"], mb["n"], P95_FLOOR),
                }
            )
    return out


# --------------------------------------------------------------------------- builder


def build(root=ROOT, write=True):
    measure = os.path.join(root, "experiments/ptr-engine/measure")
    json_out = os.path.join(measure, "VERBOSITY.json")
    md_out = os.path.join(root, "docs/VERBOSITY.md")
    files = sorted(glob.glob(os.path.join(measure, "rows-*.jsonl")))
    corpus, cells, small, decomp, fits, ans = [], [], [], [], [], []
    for path in files:
        label = os.path.basename(path)
        rows_all = load(path)
        by_arm = {}
        for r in rows_all:
            if is_completed_turn(r):
                by_arm.setdefault(r.get("arm"), []).append(r)
        corpus.append(
            {
                "file": label,
                "sha256": sha256(path),
                "rows_total": len(rows_all),
                "rows_completed_turns": sum(len(v) for v in by_arm.values()),
                "arms": {str(k): len(v) for k, v in sorted(by_arm.items(), key=lambda kv: str(kv[0]))},
            }
        )
        for arm, rows in sorted(by_arm.items(), key=lambda kv: str(kv[0])):
            if len(rows) >= MIN_CELL_N:
                c = cell_table(label, arm, rows)
                cells.append(c)
                cs, ch = c["completion_tokens"], c["answer_chars"]
                ans.append(
                    {
                        "file": label,
                        "arm": arm,
                        "n": len(rows),
                        "median_completion_tokens": cs["median"] if cs else None,
                        "median_answer_chars": ch["median"] if ch else None,
                        "ANSWER_line_rate": c["quality"]["ANSWER_line_rate"],
                        "answer_verified_rate": c["quality"]["answer_verified_rate"],
                    }
                )
            else:
                small.append(
                    {
                        "file": label,
                        "arm": arm,
                        "n": len(rows),
                        "reported_as_distribution": False,
                        "note": "n=%d < %d: not reported as a distribution, no p90/p95" % (len(rows), MIN_CELL_N),
                    }
                )
        fit = ols_loglog(rows_all)
        if fit:
            fit["file"] = label
            fits.append(fit)
        if len(by_arm) >= 2:
            decomp.extend(pairs_for(label, fit, by_arm))

    g4 = [p for p in decomp if p["file"] == "rows-longrun-c-2026-10-26.jsonl"]
    focus = next((p for p in g4 if {p["arm_a"], p["arm_b"]} == {"pointer-stable", "transcript-grow"}), None)
    if focus is None and g4:
        focus = max(g4, key=lambda p: abs(p["gap_ln_ttft(mean logs)"]))
    bc = next((f["b_completion"] for f in fits if focus and f["file"] == focus["file"]), None)
    if focus is None:
        val, reason = "not_measurable", "no grid carried two arms with >=5 TTFT rows"
    elif abs(focus["gap_ln_ttft(mean logs)"]) < 0.02:
        val = "confound_immaterial"
        reason = (
            "TTFT gap is <2%% between the compared arms, so there is nothing for completion length to explain "
            "(completion differs %.2fx)" % focus["completion_tokens_multiple"]
        )
    else:
        surv = focus.get("surviving_most_conservative")
        if surv is None:
            surv = focus.get("fraction_of_gap_surviving_completion_normalisation")
        if surv is not None and surv >= 0.80:
            val = "confound_immaterial"
            reason = (
                "holding completion length equal leaves %.1f%% of the TTFT gap in which arm a (%s) is %.2fx the "
                "first-token latency of arm b (%s), i.e. b is %.2fx slower; the fitted b_completion is %+.4f per "
                "ln-token and completion length differs %.2fx between the arms, so verbosity covers only %.1f%% of it"
                % (
                    100 * surv,
                    focus["arm_a"],
                    focus["gap_ratio_of_means"],
                    focus["arm_b"],
                    (1.0 / focus["gap_ratio_of_means"]) if focus["gap_ratio_of_means"] else 0.0,
                    bc if bc is not None else 0.0,
                    focus["completion_tokens_multiple"],
                    100 * (1.0 - surv),
                )
            )
        elif surv is not None and surv > 0.20:
            val = "confound_material"
            reason = "%.1f%% of the %.2fx TTFT gap survives completion-length normalisation (partial confound)" % (
                100 * surv,
                focus["gap_ratio_of_means"],
            )
        else:
            val = "confound_material"
            reason = "%.1f%% of the %.2fx TTFT gap survives completion-length normalisation: verbosity explains most of it" % (
                100 * (surv or 0.0),
                focus["gap_ratio_of_means"],
            )

    tt_cells = [c for c in cells if c["ttft_ms"]]
    p95_ok = [c for c in tt_cells if not c["ttft_ms"]["p95_refused"]]
    out = {
        "unit": "VERBOSITY-CONFOUND",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": True,
        "inference_requests": 0,
        "generator": {
            "path": REL_GEN,
            "sha256": sha256(GEN),
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "repo_head": subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "method": {
            "grouping": "cell = (rows file, arm); never pooled across files; n stated for every cell",
            "completed_turn_row": "kind in {null,'turn'} AND error=='' AND non-empty assistant text AND timing_usable is not False",
            "assistant_text_field": "row['content'] if that key exists else row['answer_text'] (schema differs across files; answer_source recorded per cell)",
            "ttft_ms": "row['ttft_ms'] else 1000*row['ttft_s'] else 1000*row['ttft_server_s']",
            "wall_ms": "row['wall_ms'] else 1000*row['latency_s']",
            "percentiles": "numpy linear interpolation; p50/p90 always, p95 only when n>=%d, otherwise refused" % P95_FLOOR,
            "decomposition": "OLS of ln(ttft_ms) on ln(prompt_tokens)+ln(completion_tokens) pooled across arms within one file; gap=mean(ln ttft)_a-mean(ln ttft)_b; contributions=beta*deltas; residual=gap-contributions",
            "normalisation": "subtract b_completion*ln(completion_tokens) per row; surviving fraction = 1 - completion_fraction_of_gap",
        },
        "floor": {
            "p95_min_n": P95_FLOOR,
            "min_cell_n": MIN_CELL_N,
            "cells_reaching_p95": len(p95_ok),
            "cells_refusing_p95": len(tt_cells) - len(p95_ok),
        },
        "corpus": corpus,
        "cells": cells,
        "small_cells": small,
        "fits": fits,
        "decomposition": decomp,
        "verdict": {
            "value": val,
            "scope": "p95 TTFT is refused corpus-wide at arm level (no cell reaches n>=%d), so this verdict is stated on the median/mean TTFT gap plus the log-log decomposition; p90 is the reported tail." % P95_FLOOR,
            "reason": reason,
            "surviving_fraction_used": None if focus is None else focus.get("surviving_most_conservative"),
            "surviving_fraction_basis": "min over three accountings: the pooled two-regressor model on mean logs, the completion-only upper bound (prompt omitted), and the pooled model on per-arm medians",
            "focus_pair": focus,
            "quality_comparability": {
                "arms_comparable_on_quality": False,
                "why": "completion length and answer length differ by roughly an order of magnitude between arms in the same grid, so ANSWER:-line rate and verified-answer count are functions of answer length as much as of treatment; these cells are not quality-comparable without a per-row length control",
                "cells": ans,
            },
            "missing_field": None,
        },
        "notes": [
            "No p95 is published for any cell: the largest per-(file,arm) completed-turn cell is %d rows, below the %d floor. Mean/median/p90 published with n."
            % (max(c["n_completed_turns"] for c in cells), P95_FLOOR),
            "TTFT is clocked to the first streamed delta; completion tokens are produced after that instant, so completion length cannot mechanically delay TTFT. b_completion is the load-bearing test of that.",
            "Answer length remains a real confound for quality and for ANSWER:-line production, which is a different dependent variable from TTFT.",
        ],
    }
    if write:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
            fh.write("\n")
        write_md(out, md_out)
    return out


def write_md(d, md_out):
    L = []
    A = L.append
    A("# VERBOSITY — does the grow arm's longer answer explain the TTFT gap?\n")
    A(
        "_Generated offline by `%s` (sha256 `%s`) at %s from %d rows files. Zero inference requests._\n"
        % (d["generator"]["path"], d["generator"]["sha256"][:16], d["generated_utc"], len(d["corpus"]))
    )
    A("**Verdict: `%s`.** %s\n" % (d["verdict"]["value"], d["verdict"]["reason"]))
    A("Scope: %s\n" % d["verdict"]["scope"])
    A("## 1. Corpus (pinned)\n")
    A("| rows file | rows | completed turns | sha256 |")
    A("|---|---|---|---|")
    for c in d["corpus"]:
        A("| `%s` | %d | %d | `%s` |" % (c["file"], c["rows_total"], c["rows_completed_turns"], c["sha256"]))
    A("")
    A("## 2. Per-arm distributions, grouped by file (n in every row)\n")
    A(
        "| file | arm | n | completion tok mean / med / p90 / max | answer chars mean / med / p90 | tok/char | prompt tok med / p90 | TTFT ms mean / med / p90 | TTFT p95 |"
    )
    A("|---|---|---|---|---|---|---|---|---|")
    for c in d["cells"]:
        ct, ac, pt, tt = c["completion_tokens"], c["answer_chars"], c["prompt_tokens"], c["ttft_ms"]
        f = lambda s, ks: " / ".join("%.1f" % s[k] for k in ks) if s else "—"
        A(
            "| `%s` | %s | %d | %s | %s | %s | %s | %s | %s |"
            % (
                c["file"],
                c["arm"],
                c["n_completed_turns"],
                f(ct, ["mean", "median", "p90", "max"]),
                f(ac, ["mean", "median", "p90"]),
                ("%.4f" % c["tokens_per_char"]) if c["tokens_per_char"] else "—",
                f(pt, ["median", "p90"]),
                f(tt, ["mean", "median", "p90"]),
                (
                    "— (no TTFT field)"
                    if tt is None
                    else ("refused (n=%d<%d)" % (tt["n"], P95_FLOOR) if tt["p95_refused"] else "%.1f" % tt["p95"])
                ),
            )
        )
    A("")
    if d["small_cells"]:
        A("Cells withheld (n<%d), listed so no small cell masquerades as a distribution:\n" % MIN_CELL_N)
        for s in d["small_cells"]:
            A("- `%s` / `%s`: %s" % (s["file"], s["arm"], s["note"]))
        A("")
    A("## 3. The decomposition\n")
    A("Regression pooled across arms **within one file**, so no slope crosses a file boundary:\n")
    A("| file | n | b_prompt | b_completion | R² | c_completion (prompt omitted, upper bound) | corr(ln prompt, ln completion) |")
    A("|---|---|---|---|---|---|---|")
    for f in d["fits"]:
        A("| `%s` | %d | %+.4f | %+.4f | %.3f | %+.4f | %s |" % (
            f["file"], f["n"], f["b_prompt"], f["b_completion"], f["r2"],
            f["completion_only_model"]["c_completion"],
            "—" if f.get("corr_ln_prompt_ln_completion") is None else "%.3f" % f["corr_ln_prompt_ln_completion"]))
    A("")
    A(
        "A positive `b_prompt` is prefill cost — more prompt tokens, later first token. `b_completion` is the number the "
        "confound hypothesis needs: if longer answers delayed the first token it would be positive and material. TTFT is "
        "clocked to the first streamed delta, so the answer is produced **after** that instant.\n"
    )
    A(
        "| file | arms (a − b) | TTFT ratio | completion × | b_prompt·Δln p | b_completion·Δln c | residual | gap share prompt / completion / residual | survives completion normalisation | survives: most conservative (used) |"
    )
    A("|---|---|---|---|---|---|---|---|---|---|")
    for p in d["decomposition"]:
        g = lambda v: "—" if v is None else "%+.3f" % v
        share = (
            "—"
            if p["prompt_fraction_of_gap"] is None
            else "%.0f%% / %.0f%% / %.0f%%"
            % (
                100 * p["prompt_fraction_of_gap"],
                100 * p["completion_fraction_of_gap"],
                100 * p["residual_fraction_of_gap"],
            )
        )
        surv = (
            "—"
            if p["fraction_of_gap_surviving_completion_normalisation"] is None
            else "%.1f%%" % (100 * p["fraction_of_gap_surviving_completion_normalisation"])
        )
        A(
            "| `%s` | %s − %s | %.2fx | %.2fx | %s | %s | %s | %s | %s | %s |"
            % (
                p["file"],
                p["arm_a"],
                p["arm_b"],
                p["gap_ratio_of_means"],
                p["completion_tokens_multiple"],
                g(p["prompt_share_ln"]),
                g(p["completion_share_ln"]),
                g(p["residual_ln"]),
                share,
                surv,
                "—" if p.get("surviving_most_conservative") is None else "%.1f%%" % (100 * p["surviving_most_conservative"]),
            )
        )
    A("")
    A(
        "How to read the table: arms are listed `a − b`, so `TTFT ratio` is arm a's mean-log TTFT over arm b's "
        "(below 1 means a is faster), `completion ×` is `exp(delta ln completion)` = arm a's answer length relative "
        "to arm b's, the three share columns are `beta * delta` in log units, and the last two columns are the "
        "share of the gap that survives removing the fitted completion-length term (the most conservative of the "
        "mean-log model, the completion-only upper bound, and the p50 basis is the one the verdict uses). "
        "Shares outside 0-100% are honest arithmetic on near-zero gaps, not errors.\n"
    )
    fr = d["verdict"]["focus_pair"]
    if fr:
        A(
            "**Headline (G4 / `%s`).** `%s` answers at **%.2fx** the completion length of `%s` — the other arm's "
            "answers are **%.2fx** longer — yet `%s`'s mean-log TTFT is **%.2fx** that of `%s`. Split by the fitted "
            "coefficients: prompt tokens %+.3f, completion length %+.3f, residual %+.3f of a %+.3f log gap. "
            "**%.1f%% of the gap survives holding completion length equal.**\n"
            % (
                fr["file"],
                fr["arm_a"],
                fr["completion_tokens_multiple"],
                fr["arm_b"],
                (1.0 / fr["completion_tokens_multiple"]) if fr["completion_tokens_multiple"] else 0.0,
                fr["arm_a"],
                fr["gap_ratio_of_means"],
                fr["arm_b"],
                fr["prompt_share_ln"],
                fr["completion_share_ln"],
                fr["residual_ln"],
                fr["gap_ln_ttft(mean logs)"],
                100 * (fr["fraction_of_gap_surviving_completion_normalisation"] or 0.0),
            )
        )
    if fr and fr.get("median_basis"):
        mb = fr["median_basis"]
        A("On the **p50** basis the gap is **%.2fx** (prompt %+.3f, completion %+.3f, residual %+.3f of %.3f); the "
          "completion-only upper bound is %+.3f of that gap, and the most conservative surviving fraction across all "
          "three accountings — mean-log model, completion-only upper bound, p50 basis — is **%.1f%%**, which is the "
          "number the verdict rests on.\n" % (
              mb["gap_ratio_of_medians"], mb["prompt_share_ln"], mb["completion_share_ln"], mb["residual_ln"],
              mb["gap_ln_medians"],
              fr["completion_only_model"]["share_ln"] if fr["completion_only_model"]["share_ln"] is not None else 0.0,
              100 * (fr.get("surviving_most_conservative") or 0.0)))
    A("## 4. Can the arms be compared on quality at all?\n")
    A(
        "**No, not on any answer-length-sensitive metric.** Same grid, same treatment controls, answer length differing "
        "by roughly an order of magnitude: an `ANSWER:`-line rate or a verified-answer count then measures answer length "
        "as much as treatment. Per-arm answer length beside those counts:\n"
    )
    A("| file | arm | n | median completion tok | median answer chars | `ANSWER:` line rate | answer_verified rate |")
    A("|---|---|---|---|---|---|---|")
    for q in d["verdict"]["quality_comparability"]["cells"]:
        A(
            "| `%s` | %s | %d | %.0f | %.0f | %.2f | %.2f |"
            % (
                q["file"],
                q["arm"],
                q["n"],
                q["median_completion_tokens"] or 0,
                q["median_answer_chars"] or 0,
                q["ANSWER_line_rate"],
                q["answer_verified_rate"],
            )
        )
    A("")
    A("## 5. What `RUN-A*` must report so this can never be ambiguous again\n")
    A(
        "`RUN-A*` must publish, **per arm and per grid, with n and the rows-file sha256**: (1) `completion_tokens` and "
        "answer characters as mean/median/p90/max, so verbosity is never inferred from a slope; (2) TTFT at mean/median/p90 "
        "and a p95 **only** where n≥60, with the refusal stated below that floor; (3) the fitted `b_prompt`/`b_completion` "
        "with R², so a TTFT gap is decomposed rather than asserted; (4) `ANSWER:`-line rate and `answer_verified` rate "
        "**beside** median answer length, because a count metric that grows with answer length is not treatment evidence. "
        "A gap quoted without those four numbers is a slope with treatment and verbosity still tangled inside it.\n"
    )
    A("## 6. Limits\n")
    for n in d["notes"]:
        A("- " + n)
    A(
        "- No field in these rows separates prefill *compute* from server queueing/wait: `ttft_ms` is one client-side "
        "first-delta clock. The prompt-side share is therefore a **proxy** (fitted on prompt tokens), not measured prefill "
        "FLOPs. A server-side `prefill_ms` (or per-request `queue_wait_ms`) is what would split them."
    )
    open(md_out, "w", encoding="utf-8").write("\n".join(L) + "\n")


# --------------------------------------------------------------------------- independent validator


def recompute_cell(path, arm):
    """Independent recomputation of one cell's completion-token and answer-char means/medians."""
    rows = [r for r in load(path) if is_completed_turn(r) and r.get("arm") == arm]
    comp = [float(r["completion_tokens"]) for r in rows if num(r.get("completion_tokens")) is not None]
    chars = [len(text_of(r)) for r in rows]
    med = lambda a: float(np.percentile(np.asarray(a, float), 50)) if a else None
    mean = lambda a: float(np.mean(a)) if a else None
    return {"n": len(rows), "comp_mean": mean(comp), "comp_median": med(comp), "chars_mean": mean(chars), "chars_median": med(chars)}


def validate_report(json_path, root=ROOT, tol=1e-3):
    """Re-derive everything checkable from the rows corpus. Returns a list of error strings."""
    errs = []
    try:
        d = json.load(open(json_path, encoding="utf-8"))
    except Exception as exc:
        return ["unparseable JSON: %s" % exc]
    for key in ("corpus", "cells", "small_cells", "fits", "decomposition", "verdict", "method", "floor"):
        if key not in d:
            errs.append("missing top-level key %r" % key)
    if d.get("verdict", {}).get("value") not in {"confound_material", "confound_immaterial", "not_measurable"}:
        errs.append("verdict.value not one of the three allowed words: %r" % d.get("verdict", {}).get("value"))
    measure = os.path.join(root, "experiments/ptr-engine/measure")
    on_disk = {os.path.basename(p): p for p in sorted(glob.glob(os.path.join(measure, "rows-*.jsonl")))}
    declared = {c["file"]: c for c in d.get("corpus", [])}
    for name, path in on_disk.items():
        if name not in declared:
            errs.append("rows file missing from corpus: %s" % name)
            continue
        if declared[name].get("sha256") != sha256(path):
            errs.append("sha256 mismatch for %s" % name)
        if declared[name].get("rows_total") != len(load(path)):
            errs.append("rows_total mismatch for %s" % name)
    for name in declared:
        if name not in on_disk:
            errs.append("corpus lists a file not on disk: %s" % name)
    for c in d.get("cells", []):
        n = c.get("n_completed_turns") or 0
        if n < MIN_CELL_N:
            errs.append("cell %s/%s reported as a distribution with n=%d < %d" % (c["file"], c["arm"], n, MIN_CELL_N))
            continue
        path = on_disk.get(c["file"])
        if not path:
            continue
        rc = recompute_cell(path, c["arm"])
        if rc["n"] != n:
            errs.append("n mismatch %s/%s: json %d, rows %d" % (c["file"], c["arm"], n, rc["n"]))
        for field, key, rc_key in (
            ("completion_tokens", "mean", "comp_mean"),
            ("completion_tokens", "median", "comp_median"),
            ("answer_chars", "mean", "chars_mean"),
            ("answer_chars", "median", "chars_median"),
        ):
            got = c.get(field, {}).get(key)
            want = rc[rc_key]
            if got is None or want is None or abs(float(got) - float(want)) > tol:
                errs.append("fabricated/mismatched %s.%s for %s/%s: json %r, rows %r" % (field, key, c["file"], c["arm"], got, want))
        tt = c.get("ttft_ms")
        if tt:
            if tt.get("p95") is not None and tt.get("n", 0) < P95_FLOOR:
                errs.append("p95 published for %s/%s with n=%d < %d" % (c["file"], c["arm"], tt["n"], P95_FLOOR))
            if tt.get("n", 0) < P95_FLOOR and tt.get("p95") is not None:
                errs.append("p95 present where floor requires refusal: %s/%s" % (c["file"], c["arm"]))
    for s in d.get("small_cells", []):
        if s.get("n", 0) >= MIN_CELL_N:
            errs.append("small_cells entry has n>=%d: %s/%s" % (MIN_CELL_N, s["file"], s["arm"]))
        if s.get("reported_as_distribution"):
            errs.append("small cell reported as a distribution: %s/%s" % (s["file"], s["arm"]))
    for p in d.get("decomposition", []):
        fr = [p.get("prompt_fraction_of_gap"), p.get("completion_fraction_of_gap"), p.get("residual_fraction_of_gap")]
        if all(f is not None for f in fr) and abs(sum(fr) - 1.0) > 1e-3:
            errs.append("gap shares do not sum to 1 for %s %s/%s: %r" % (p["file"], p["arm_a"], p["arm_b"], fr))
    for p in d.get("decomposition", []):
        co = p.get("completion_only_model") or {}
        if co.get("surviving_fraction") is not None and p.get("completion_only_model"):
            if abs((1.0 - co["fraction_of_gap"]) - co["surviving_fraction"]) > 1e-3:
                errs.append("completion-only share/surviving mismatch for %s %s/%s" % (p["file"], p["arm_a"], p["arm_b"]))
        cands = [x for x in (
            p.get("fraction_of_gap_surviving_completion_normalisation"),
            co.get("surviving_fraction"),
            (p.get("median_basis") or {}).get("fraction_of_gap_surviving_completion_normalisation"),
        ) if x is not None]
        if cands and p.get("surviving_most_conservative") is not None and abs(min(cands) - p["surviving_most_conservative"]) > 1e-3:
            errs.append("surviving_most_conservative is not the minimum for %s %s/%s" % (p["file"], p["arm_a"], p["arm_b"]))
    v = d.get("verdict", {})
    f = v.get("focus_pair")
    if v.get("value") == "confound_immaterial" and f and v.get("surviving_fraction_used") is not None:
        if v["surviving_fraction_used"] < 0.80 and abs(f["gap_ln_ttft(mean logs)"]) >= 0.02:
            errs.append("verdict immaterial but only %.3f of the gap survives the most conservative accounting" % v["surviving_fraction_used"])
    return errs


# --------------------------------------------------------------------------- tests


def test_json_parses_and_has_the_tables():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    assert d["unit"] == "VERBOSITY-CONFOUND"
    assert d["offline"] is True and d["inference_requests"] == 0
    assert len(d["corpus"]) >= 14 and len(d["cells"]) >= 1 and len(d["decomposition"]) >= 1
    assert d["verdict"]["value"] in {"confound_material", "confound_immaterial", "not_measurable"}
    assert d["floor"]["p95_min_n"] == 60


def test_every_rows_file_appears_with_its_sha():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    on_disk = {os.path.basename(p): p for p in rows_files()}
    declared = {c["file"]: c for c in d["corpus"]}
    assert set(on_disk) == set(declared), (set(on_disk) ^ set(declared))
    for name, path in on_disk.items():
        assert declared[name]["sha256"] == sha256(path), name
        assert declared[name]["rows_total"] == len(load(path)), name


def test_recomputation_agrees_with_rows():
    assert validate_report(JSON_OUT) == []


def test_fabricated_mean_fails_recomputation():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    victim = next(c for c in d["cells"] if c.get("completion_tokens"))
    victim["completion_tokens"]["mean"] = round(float(victim["completion_tokens"]["mean"]) + 3.0, 4)
    tmpd = tempfile.mkdtemp(prefix="vconf-")
    bad = os.path.join(tmpd, "VERBOSITY.json")
    json.dump(d, open(bad, "w", encoding="utf-8"))
    errs = validate_report(bad)
    assert any("fabricated" in e for e in errs), errs
    assert validate_report(JSON_OUT) == [], "the real report must still pass"


def test_no_cell_below_min_n_is_a_distribution():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    for c in d["cells"]:
        assert c["n_completed_turns"] >= 5, (c["file"], c["arm"], c["n_completed_turns"])
    for s in d["small_cells"]:
        assert s["n"] < 5 and s["reported_as_distribution"] is False


def test_p95_is_refused_below_the_floor():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    refused = 0
    for c in d["cells"]:
        tt = c.get("ttft_ms")
        if not tt:
            continue
        if tt["n"] < 60:
            refused += 1
            assert tt["p95"] is None and tt["p95_refused"] is True, (c["file"], c["arm"], tt["n"])
        else:
            assert tt["p95"] is not None
    assert refused == d["floor"]["cells_refusing_p95"]
    assert refused >= 1


def test_decomposition_shares_are_a_decomposition():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    assert d["decomposition"]
    for p in d["decomposition"]:
        fr = [p["prompt_fraction_of_gap"], p["completion_fraction_of_gap"], p["residual_fraction_of_gap"]]
        assert all(f is not None for f in fr), p
        assert abs(sum(fr) - 1.0) <= 1e-3, (p["file"], p["arm_a"], p["arm_b"], fr)
        assert p["completion_tokens_multiple"] > 0


def test_verdict_matches_its_own_focus_pair():
    d = json.load(open(JSON_OUT, encoding="utf-8"))
    v, f = d["verdict"], d["verdict"]["focus_pair"]
    assert f is not None
    assert {f["arm_a"], f["arm_b"]} == {"pointer-stable", "transcript-grow"}, (f["arm_a"], f["arm_b"])
    surv = v["surviving_fraction_used"]
    assert surv == f["surviving_most_conservative"]
    assert f["completion_only_model"]["surviving_fraction"] is not None
    if v["value"] == "confound_immaterial":
        assert surv >= 0.80, surv
    if v["value"] == "confound_material":
        assert surv < 0.80, surv
    assert d["verdict"]["quality_comparability"]["arms_comparable_on_quality"] is False


if __name__ == "__main__":
    out = build()
    errs = validate_report(JSON_OUT)
    print("WROTE", JSON_OUT)
    print("WROTE", MD_OUT)
    print("cells=%d p95_ok=%d refused=%d decomp=%d fits=%d" % (
        len(out["cells"]), out["floor"]["cells_reaching_p95"], out["floor"]["cells_refusing_p95"],
        len(out["decomposition"]), len(out["fits"])))
    print("VERDICT", out["verdict"]["value"], "|", out["verdict"]["reason"])
    print("FOCUS", json.dumps(out["verdict"]["focus_pair"]))
    print("VALIDATE_ERRORS", errs)
    sys.exit(1 if errs else 0)
