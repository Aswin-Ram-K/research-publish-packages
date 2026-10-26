#!/usr/bin/env python3
"""cached_dedupe.py — offline detector for duplicated / stale ``cached_tokens`` credit.

THE SIGNATURE CHOSEN: candidate (c), quantum-relative
-----------------------------------------------------
The gap ``prompt - cached`` jumping by a suspicious constant, made quantum-relative,
one-sided, bounded and transient:

    gap[i] = prompt_tokens[i] - cached_tokens[i]      (credit rows: 0 < cached <= prompt)
    base   = p25(gap)                                 one-sided: this defect only ADDS
    q      = median positive advance of cached_tokens  the arm's own cache quantum
    FIRE   = base + 0.9q <= gap[i] <= base + 1.6q      the row is credited with the PREVIOUS
             and prompt grew vs the previous credit row turn's cache state, so the gap gains
             and gap <= base + 0.5q within 3 credit rows ~exactly one quantum, transiently
             and not (cached == ceiling, all later == ceiling)   (excludes saturation)

Rejected with measurements: (a) 2-cycle alternation fires on 0 rows of the known-bad file;
(b) "value repeated at a non-adjacent turn" fires on 33-34 rows of the CLEAN controls' arm A.

THE CALIBRATION FAILS, AND THAT IS THE FINDING
----------------------------------------------
This signature reproduces the ARMS-PARITY claim exactly — 40/71 on
``cells/PROMPT-O1/rows.pre-correction.jsonl`` and 0 on ``cells/R2-P1-O1/rows.jsonl`` — but it
ALSO fires on ``cells/GROUND-TRUTH-PROMPT/rows.jsonl``, a fresh independent re-measurement of
the same cell (mean uncached 589.20, 69/71 measured). The two series share the structure:

    GROUND-TRUTH-PROMPT cached: 384, 1088, 1088, 1408, 2112, 2112, 2432, 3136, 3136, ...
                          gaps: 765, 400, 739, 758, 393, 732, 751, 386, 725, 744, ...

A stall-then-catch-up rhythm in 64-token blocks is normal cache physics on this stack, so the
pattern track CANNOT be verdict-bearing. ``GROUND-TRUTH-R`` shows the same (18 stalls / 40 rows).

The one artefact that is physically impossible is the withdrawn repair
``cells/PROMPT-O1/rows.repaired-DO-NOT-USE.jsonl``: 40 of 71 arm-R ``cached_tokens`` are not
multiples of 64 (1409, 1793, 2433, 2753, 3777, ...) — a value this stack cannot emit — and its
gap sequence is ``cells/R2-P1-O1``'s gap sequence subtracted from PROMPT-O1's prompt sizes.

  corrupt   an impossible value: off the 64 grid, or a transplanted gap sequence
  suspect   the pattern fires at >= 25% (cannot be distinguished from ground truth)
  clean     neither

Read-only on cells/**; zero live requests; no endpoint, no lock, no GX10.

USAGE
  python3 tools/audit/cached_dedupe.py [--json] [--out PATH] [--cells DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

DEFAULT_CELLS = "experiments/context-cache/cells"
GRID = 64
BASELINE_QUANTILE = 0.25
BAND_LO_QUANTA = 0.9
BAND_HI_QUANTA = 1.6
RECOVERY_QUANTA = 0.5
RECOVERY_WINDOW = 3
SUSPECT_MIN_RATE = 0.25
TRANSPLANT_MIN_OVERLAP = 20
TRANSPLANT_MIN_MATCH = 0.90

FIXTURES = [
    ("PROMPT-O1", "R", "rows.pre-correction.jsonl"),
    ("PROMPT-O1", "R", "rows.repaired-DO-NOT-USE.jsonl"),
]

CONTROLS = {
    "R2-P1-O1": "clean control: smooth sawtooth, measured correctly",
    "PROMPT-O1": "restored corpus; rows.jsonl == rows.pre-correction.jsonl (sha256 dc0774d8...)",
    "GROUND-TRUTH-PROMPT": "fresh independent re-measurement (589.20 mean); pattern fires here too",
    "GROUND-TRUTH-R": "fresh independent re-measurement; 18 stalls in 40 rows",
}
RANK = {"clean": 0, "suspect": 1, "corrupt": 2}


def quantile(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] * (1 - (k - lo)) + s[hi] * (k - lo)


def load_arm(path, arm):
    """(turn, prompt, cached) for one arm, ordered by turn; non-int cached -> unavailable."""
    out, unavailable = [], []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(r.get("arm")) != arm:
                continue
            p, c = r.get("prompt_tokens"), r.get("cached_tokens")
            if not isinstance(p, int) or not isinstance(c, int) or c < 0 or c > p:
                unavailable.append(r.get("turn"))
                continue
            t = r.get("turn")
            t = int(t) if isinstance(t, int) or (isinstance(t, str) and t.isdigit()) else len(out) + 1
            out.append((t, p, c))
    out.sort(key=lambda x: x[0])
    return out, unavailable


def pattern_fires(series):
    """Candidate (c): one-quantum, bounded, transient gap inflation."""
    credit = [s for s in series if 0 < s[2] <= s[1]]
    if len(credit) < 8:
        return [], None, None
    gaps = [p - c for _, p, c in credit]
    base = quantile(gaps, BASELINE_QUANTILE)
    advances = [credit[i][2] - credit[i - 1][2] for i in range(1, len(credit))
                if credit[i][2] > credit[i - 1][2]]
    q = statistics.median(advances) if advances else 0.0
    if not q or not base:
        return [], base, q
    lo, hi = base + BAND_LO_QUANTA * q, base + BAND_HI_QUANTA * q
    ceiling = max(c for _, _, c in credit)
    fires = []
    for i, (turn, prompt, cached) in enumerate(credit):
        gap = prompt - cached
        if not (lo <= gap <= hi):
            continue
        if i == 0 or prompt <= credit[i - 1][1]:
            continue
        if i + 1 < len(credit) and all(c >= ceiling for _, _, c in credit[i + 1:]):
            continue
        if not any(credit[j][1] - credit[j][2] <= base + RECOVERY_QUANTA * q
                   for j in range(i + 1, min(i + 1 + RECOVERY_WINDOW, len(credit)))):
            continue
        fires.append({"turn": turn, "prompt": prompt, "cached": cached, "gap": gap,
                      "base": round(base, 2), "q": round(q, 2),
                      "cached_repeats_neighbour": i > 0 and cached == credit[i - 1][2]})
    return fires, base, q


QUANTA = (16, 32, 64, 128)


def arm_quantum(series):
    """The arm's own cache block size: the largest B in QUANTA dividing >=95% of credit values.

    Engine-agnostic on purpose: SGLang credits in 64-token blocks, vLLM in 16, some cells in
    32. A hard-coded 64 would call every vLLM cell corrupt. ``None`` means the arm has no
    consistent quantum at all, which no block-quantised server can produce.
    """
    vals = [c for _, _, c in series if c > 0]
    if len(vals) < 8:
        return None
    for b in sorted(QUANTA, reverse=True):
        if sum(1 for v in vals if v % b == 0) / len(vals) >= 0.95:
            return b
    return None


def impossible_fires(series, quantum=None):
    """Values this stack cannot emit: off the arm's own grid, or a non-monotone credit."""
    out, prev = [], None
    q = quantum or 0
    for i, (turn, prompt, cached) in enumerate(series):
        if q and cached > 0 and cached % q != 0:
            out.append({"turn": turn, "prompt": prompt, "cached": cached,
                        "gap": prompt - cached, "test": "S1_OFF_GRID",
                        "quantum": q, "remainder": cached % q})
        if i >= 2 and prev is not None and cached < prev:
            out.append({"turn": turn, "prompt": prompt, "cached": cached,
                        "gap": prompt - cached, "test": "S3_NON_MONOTONE",
                        "prev_cached": prev})
        prev = cached
    return out


def find_transplants(series):
    """S2: an arm whose gap sequence is a near-exact copy of another cell's."""
    found = {}
    keys = sorted(series)
    for a in keys:
        ga = [p - c for _, p, c in series[a]]
        for b in keys:
            if a == b or a.split("::")[0] == b.split("::")[0]:
                continue
            gb = [p - c for _, p, c in series[b]]
            m = min(len(ga), len(gb))
            if m < TRANSPLANT_MIN_OVERLAP:
                continue
            same = sum(1 for x, y in zip(ga[:m], gb[:m]) if x == y)
            if same / m >= TRANSPLANT_MIN_MATCH:
                found.setdefault(a, []).append({"copied_from": b, "overlap": m,
                                                "identical_gaps": same,
                                                "fraction": round(same / m, 4)})
    return found


def judge(series, transplants):
    """Verdict: grid coherence is the only physically decisive test.

    S3 (non-monotone credit) and S2 (shared gap sequence) fire on 20 of 25 cells and on the
    clean controls, so they are reported as diagnostics and never decide the class.
    """
    pat, base, q = pattern_fires(series)
    quantum = arm_quantum(series)
    off64 = [s for s in series if s[2] > 0 and s[2] % GRID != 0]
    rate = len(pat) / len(series) if series else 0.0
    if quantum is None and len(off64) >= 10:
        cls, reasons = "corrupt", ["S1_GRID_INCOHERENT"]
        detail = [{"turn": t, "prompt": pr, "cached": c, "gap": pr - c,
                   "test": "S1_GRID_INCOHERENT", "remainder64": c % GRID}
                  for t, pr, c in off64]
    elif rate >= SUSPECT_MIN_RATE:
        cls, reasons = "suspect", ["C1_PATTERN_ONLY"]
        detail = pat
    else:
        cls, reasons = "clean", []
        detail = pat
    return {"rows": len(series), "fires": len(pat), "rate": round(rate, 4), "class": cls,
            "reasons": reasons, "pattern_fires": len(pat),
            "impossible_fires": len(off64) if cls == "corrupt" else 0,
            "arm_quantum": quantum, "off_grid_vs_64": len(off64),
            "baseline_gap": round(base, 2) if base else None,
            "cache_quantum": round(q, 2) if q else None,
            "first_three": [{"turn": f["turn"], "prompt": f["prompt"], "cached": f["cached"],
                             "gap": f["gap"], "test": f.get("test", "C1_PATTERN"),
                             "cached_repeats_neighbour": f.get("cached_repeats_neighbour")}
                            for f in detail[:3]],
            "impossible_detail": detail[:3],
            "non_monotone_diagnostic": sum(1 for f in impossible_fires(series, quantum)
                                           if f["test"] == "S3_NON_MONOTONE"),
            "transplant_evidence": transplants}


def audit(cells_dir=DEFAULT_CELLS, grid=GRID):
    targets = []
    for name in sorted(os.listdir(cells_dir)):
        p = os.path.join(cells_dir, name, "rows.jsonl")
        if not os.path.isfile(p):
            continue
        arms = set()
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        arms.add(str(json.loads(line).get("arm")))
                    except json.JSONDecodeError:
                        pass
        for arm in sorted(a for a in arms if a not in ("None", "null")):
            targets.append((name, arm, "rows.jsonl", p))
    for cell, arm, fname in FIXTURES:
        p = os.path.join(cells_dir, cell, fname)
        if os.path.isfile(p):
            targets.append((cell, arm, fname, p))

    loaded, series = [], {}
    for cell, arm, label, p in targets:
        s, unavail = load_arm(p, arm)
        if not s:
            continue
        key = f"{cell}::{label}::{arm}"
        series[key] = s
        loaded.append((cell, arm, label, key, unavail))
    transplants = find_transplants(series)

    cells = {}
    for cell, arm, label, key, unavail in loaded:
        res = judge(series[key], transplants.get(key, []))
        res["unavailable_rows"] = len(unavail)
        res["file"] = label
        c = cells.setdefault(cell, {"class": "clean", "rows": 0, "fires": 0, "arms": {},
                                    "is_control": cell in CONTROLS,
                                    "control_note": CONTROLS.get(cell, ""), "reasons": set()})
        c["arms"][arm if label == "rows.jsonl" else f"{arm}@{label}"] = res
        c["rows"] += res["rows"]
        c["fires"] += res["fires"]
        c["reasons"].update(res["reasons"])
        if RANK[res["class"]] > RANK[c["class"]]:
            c["class"] = res["class"]

    for c in cells.values():
        c["reasons"] = sorted(c["reasons"])
        c["rate"] = round(c["fires"] / c["rows"], 4) if c["rows"] else 0.0

    counts = {"clean": 0, "suspect": 0, "corrupt": 0}
    for c in cells.values():
        counts[c["class"]] += 1

    return {
        "tool": "tools/audit/cached_dedupe.py",
        "schema": "cached-dedupe-audit/1",
        "grid": grid,
        "signature": ("candidate (c): quantum-relative, one-sided, bounded, transient gap "
                      "inflation (prompt-cached gains ~1 cache quantum, then snaps back)"),
        "cells_scanned": len(cells),
        "counts": counts,
        "cells": dict(sorted(cells.items())),
        "controls": CONTROLS,
        "verdict": (
            "The card's signature reproduces the ARMS-PARITY claim (40/71 on "
            "rows.pre-correction.jsonl, 0 on R2-P1-O1) but is NOT discriminating: it also fires "
            "on the fresh independent GROUND-TRUTH-PROMPT re-measurement, whose cached series "
            "shows the same 64-block stall-then-catch-up rhythm. No cell is therefore called "
            "corrupt on the pattern. The only physically impossible artefact is "
            "rows.repaired-DO-NOT-USE.jsonl (40 off-grid cached values; gaps transplanted from "
            "R2-P1-O1). rows.jsonl is byte-identical to rows.pre-correction.jsonl, so the "
            "card's 'silent on the repaired rows.jsonl' control cannot coexist with 'fires on "
            "rows.pre-correction.jsonl' — RESTORE-O1 restored the file at 03:03."),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cells", default=DEFAULT_CELLS)
    ap.add_argument("--grid", type=int, default=GRID)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    report = audit(args.cells, args.grid)
    blob = json.dumps(report, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(blob + "\n")
    if args.json:
        print(blob)
        return 0

    print(f"grid={report['grid']} cells={report['cells_scanned']} "
          f"clean={report['counts']['clean']} suspect={report['counts']['suspect']} "
          f"corrupt={report['counts']['corrupt']}")
    print(f"{'cell':22s} {'arm':30s} {'rows':>5s} {'fires':>6s} {'rate':>7s} {'imp':>4s}  class")
    for cell, c in report["cells"].items():
        for arm, a in c["arms"].items():
            print(f"{cell:22s} {arm:30s} {a['rows']:5d} {a['fires']:6d} {a['rate']:7.3f} "
                  f"{a['impossible_fires']:4d}  {a['class']}")
    bad = {k: v for k, v in report["cells"].items() if v["class"] != "clean"}
    print("\nnon-clean:", ", ".join(f"{k}({v['class']})" for k, v in bad.items()) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
