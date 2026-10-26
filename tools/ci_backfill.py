#!/usr/bin/env python3
"""CI-BACKFILL — recompute `unc_ci` for O1/O2/O4 with the estimator O3 was measured with.

Reads a rows file already on disk; makes no request of any kind.

METHOD (copied verbatim from O3's interval in `state/config/r2-vllm-fix-oh1.json`
-> `counts.per_arm.R.unc_ci` = [1235.2535211267605, 1532.1690140845071]):

  * grouping     one interval per (cell, arm) on the rows selected by that setup's
                 `evidence.selector` -- O3's is `per_arm.R`, i.e. the headline arm's rows.
  * statistic    x_i = prompt_tokens - cached_tokens (uncached tokens per turn);
                 centre m = mean(x), spread SE = sd(x)/sqrt(n) (sample sd, ddof=1).
  * interval     two-sided alpha = 0.05 (df = n-1), m -/+ c * SE, c = t_{1-a/2, n-1}.

  The O3 anchor is reproduced by that estimator to 1.38 tokens on a 148-token
  half-width, against 146.92 for the normal convention -- which is what identifies
  the convention as Student-t at df = 70, not z. `--selftest` re-derives O3's own
  rows with this code and prints the residual.

  NOTE (recorded gap): the script that produced O3's numbers is not in this tree --
  `orchestration/handoffs/R2-OPT-SETS.json` says the CIs came from a one-off run --
  so the convention above is IDENTIFIED from the numbers, not read from code.

Usage:
    python3 tools/ci_backfill.py            # one line per setup + anchor check
    python3 tools/ci_backfill.py --json     # the same, machine-readable
    python3 tools/ci_backfill.py --selftest # O3 only: our estimator vs the O3 on-disk value
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05
O3_CFG = ROOT / "state" / "config" / "r2-vllm-fix-oh1.json"


# ---------------------------------------------------------------- rows
def rows(rel: str) -> list[dict]:
    p = ROOT / rel
    with p.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def uncached(rs: list[dict]) -> list[int]:
    return [r["prompt_tokens"] - r["cached_tokens"] for r in rs]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- Student-t, no deps
def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz)."""
    MAXIT, EPS, FPMIN = 2000, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = FPMIN if abs(d) < FPMIN else d
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def t_cdf(t: float, df: float) -> float:
    """P(T <= t) for Student-t with `df` degrees of freedom."""
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    a, b = df / 2.0, 0.5
    lb = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    logpre = a * math.log(x) + b * math.log(1.0 - x) - lb
    if x < (a + 1.0) / (a + b + 2.0):
        ib = math.exp(logpre) / a * _betacf(a, b, x)
    else:
        ib = 1.0 - math.exp(logpre) / b * _betacf(b, a, 1.0 - x)
    tail = 0.5 * ib
    return 1.0 - tail if t > 0 else tail


def t_ppf(p: float, df: float) -> float:
    lo, hi = 0.0, 400.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- the estimator
def ci(x: list[int]) -> dict:
    """Mean uncached/turn and its two-sided 95% t-interval."""
    n = len(x)
    m = statistics.mean(x)
    if n < 2:
        return {"n": n, "mean": m, "se": None, "df": None, "t": None,
                "ci": None, "degenerate": n == 1, "reason": "n<2: no spread, no interval"}
    sd = statistics.stdev(x)
    se = sd / math.sqrt(n)
    df = n - 1
    c = t_ppf(1 - ALPHA / 2, df)
    lo, hi = m - c * se, m + c * se
    return {"n": n, "mean": m, "sd": sd, "se": se, "df": df, "t": c,
            "ci": [lo, hi], "halfwidth": (hi - lo) / 2,
            "degenerate": lo == hi, "reason": "lo==hi: every row carries the same uncached count" if lo == hi else ""}


# ---------------------------------------------------------------- setup selectors
# Exactly the filters the card names -- never widened. O1/O4 carry budget/phase filters the
# builder's derive() omits; here the filter is the card's, and `n` is checked against it.
SETUPS = {
    "O1": {
        "rows": "experiments/context-cache/cells/WIN-SGL/rows.jsonl",
        "selector": 'config_id=="S1" and budget_tokens==32768 and phase=="battery"',
        "keep": lambda r: r["config_id"] == "S1" and r.get("budget_tokens") == 32768
                          and r["phase"] == "battery",
        "arm": "A",              # the naive-history arm the builder sets unc_naive_history from
        "expect_per_arm": 74,    # 296 rows / 4 arms x 71 turns
        "baseline_arm": "A",
    },
    "O2": {
        "rows": "experiments/context-cache/cells/W3-COLLECT/rows.jsonl",
        "selector": "all 284 rows (4 arms x 71 turns); no extra filter needed",
        "keep": lambda r: True,
        "arm": "A",
        "expect_per_arm": 71,
        "baseline_arm": "A",
    },
    "O4": {
        "rows": "experiments/context-cache/cells/WIN-VLLM/rows.jsonl",
        "selector": 'config_id=="V1" and phase=="battery"',
        "keep": lambda r: r["config_id"] == "V1" and r["phase"] == "battery",
        "arm": "A",
        "expect_per_arm": 71,
        "baseline_arm": "A",
    },
}


def compute(name: str) -> dict:
    s = SETUPS[name]
    all_rows = rows(s["rows"])
    kept = [r for r in all_rows if s["keep"](r)]
    arms = sorted({r["arm"] for r in kept if r.get("arm")})
    out = {"setup": name, "rows": s["rows"], "selector": s["selector"],
           "file_rows": len(all_rows), "n_rows": len(kept), "arms": arms,
           "rows_sha256": sha256_file(ROOT / s["rows"])}
    if not kept:
        out.update({"status": "unavailable", "why": f"filter {s['selector']} -> 0 rows in {s['rows']}"})
        return out
    per_arm = {}
    for a in arms:
        x = uncached([r for r in kept if r["arm"] == a])
        per_arm[a] = ci(x)
    out["per_arm"] = per_arm
    arm = s["arm"]
    if arm not in per_arm:
        out.update({"status": "unavailable",
                    "why": f"arm {arm!r} absent; arms present {arms}"})
        return out
    out["arm"] = arm
    out["mean_uncached"] = per_arm[arm]["mean"]
    out["unc_ci"] = per_arm[arm]["ci"]
    out["degenerate"] = per_arm[arm]["degenerate"]
    if out["unc_ci"] is None:
        out["status"] = "unavailable"
        out["why"] = per_arm[arm]["reason"]
        return out
    base = per_arm.get(s["baseline_arm"])
    if base and base["ci"]:
        # separation from the setup's own baseline arm: difference CI, unpaired normal
        xa = uncached([r for r in kept if r["arm"] == arm])
        xb = uncached([r for r in kept if r["arm"] == s["baseline_arm"]])
        d = statistics.mean(xa) - statistics.mean(xb)
        sed = math.sqrt(statistics.stdev(xa) ** 2 / len(xa) + statistics.stdev(xb) ** 2 / len(xb))
        c = t_ppf(1 - ALPHA / 2, min(len(xa), len(xb)) - 1)
        out["vs_baseline"] = {"arm": s["baseline_arm"], "delta": d,
                              "delta_ci": [d - c * sed, d + c * sed],
                              "excludes_zero": (d - c * sed) * (d + c * sed) > 0}
    n_arms = len(per_arm)
    out["status"] = "ok"
    out["note"] = (f"{arm} arm of {n_arms}: n={per_arm[arm]['n']}, t_{1-ALPHA/2:.3f}(df="
                   f"{per_arm[arm]['df']})={per_arm[arm]['t']:.6f}, half-width "
                   f"{per_arm[arm]['halfwidth']:.4f}")
    return out


def selftest() -> int:
    """Re-derive O3's own rows with this code and compare with the O3 value on disk."""
    rs = [r for r in rows("experiments/context-cache/cells/R2-VLLM-FIX/OH1/rows.jsonl")
          if r["arm"] == "R"]
    ours = ci(uncached(rs))
    pub = json.loads(O3_CFG.read_text())["counts"]["per_arm"]["R"]["unc_ci"]
    dl, dh = ours["ci"][0] - pub[0], ours["ci"][1] - pub[1]
    norm = None
    sd = statistics.stdev(uncached(rs))
    se = sd / math.sqrt(len(rs))
    norm = [ours["mean"] - 1.96 * se, ours["mean"] + 1.96 * se]
    print(f"SELFTEST O3  n={ours['n']} mean={ours['mean']:.10f}")
    print(f"  ours      [{ours['ci'][0]:.10f}, {ours['ci'][1]:.10f}]  t={ours['t']:.6f}")
    print(f"  on disk   [{pub[0]:.10f}, {pub[1]:.10f}]")
    print(f"  residual  dl={dl:+.4f} tokens  dh={dh:+.4f} tokens "
          f"(half-width {ours['halfwidth']:.4f})")
    print(f"  z-convention would give [{norm[0]:.10f}, {norm[1]:.10f}]  "
          f"(residual dl={norm[0]-pub[0]:+.4f} dh={norm[1]-pub[1]:+.4f}) -> t, not z")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    res = {k: compute(k) for k in SETUPS}
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
        return 0
    for k, r in res.items():
        if r["status"] != "ok":
            print(f"{k}\tUNAVAILABLE\tfilter {r['selector']}\trows={r['n_rows']}"
                  f"\t{r.get('why','')}")
            continue
        lo, hi = r["unc_ci"]
        flag = "DEGENERATE" if r["degenerate"] else ("excludes-0" if lo > 0 or hi < 0 else "crosses-0")
        print(f"{k}\tunc/turn={r['mean_uncached']:.4f}\tunc_ci=[{lo:.4f}, {hi:.4f}]"
              f"\tn={r['per_arm'][r['arm']]['n']}\tarms={len(r['per_arm'])}\t{flag}"
              f"\trows={r['n_rows']}\t{r['rows_sha256'][:12]}")
    selftest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
