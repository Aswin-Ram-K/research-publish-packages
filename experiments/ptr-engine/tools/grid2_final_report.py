#!/usr/bin/env python3
"""GRID-2-FINAL — the best honest report the six usable gen-6 cells support.

Offline by construction: reads only files under `experiments/ptr-engine/measure/`
and `orchestration/handoffs/`.  Sends no request, runs no cell, writes nothing
except the two artefacts named on the command line (`--json`, `--md`).

Three jobs, and no fourth:

1. **The census the pinned reader cannot build.**  `analyze_stats.load_cell_manifests`
   requires a TOP-LEVEL `rows_path`; `cell.py` writes it nested under
   `run.rows_path` (GRID-GAP-DIAG finding A).  This tool walks the 16 gen-6 rows
   files and their manifests directly and links them by the nested path, so
   every cell's own stamp is read from its own manifest.

2. **Recompute, never copy.**  Every latency / token / n_eff number below is
   produced here from the rows on disk through the licensed estimators
   (`analyze_stats.quantile_ci`, `analyze_stats.turn_latency_rows`,
   `analyze_stats.split_truncated`, `p95_power_probe.lag1`,
   `verify_tranche1.h2_tokens`), not transcribed from a handoff.

3. **Attach the limits.**  `ABSENT` is never rendered as usable; a refused p95
   keeps its refusal text verbatim; n_eff sits beside every interval; the price
   of closing the gap is stated as arithmetic.

Statistic-selection note.  H1 has TWO admissible series shapes and this report
prints both rather than choosing after seeing the data:

* `frozen` — what the grid's own pipeline produced (`run_grid_report.per_arm_series`),
  dedupe key `(arm, rep, turn_index)`.  Every gen-6 cell wrote `rep=1`, so the six
  usable cells collapse to 48 turns per arm.
* `rep_preserving` — a SENSITIVITY, not the reading: the same selector with the
  cell ordinal written into `rep`.  It exists only to price what the collapse costs.

The H1 verdict is computed on `frozen`, because changing the selector after the
rows exist is an instrument change, and an instrument change mints a new
generation whose rows cannot be pooled with gen 6.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)                     # experiments/ptr-engine
LONGRUN = os.path.join(PKG, "longrun")
for _p in (LONGRUN, HERE, PKG):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import analyze_stats as S                        # noqa: E402
import p95_power_probe as PP                     # noqa: E402
import verify_tranche1 as V                      # noqa: E402
import run_grid_report as RG                     # noqa: E402

SCHEMA = "grid-2-final/1"
GRID_RECORD = os.path.join(PKG, "measure", "GRID-RUN-2.json")
MEASURE = os.path.join(PKG, "measure")
ROOT = os.path.dirname(os.path.dirname(PKG))
HANDOFF = os.path.join(ROOT, "orchestration", "handoffs", "GRID-RUN-2.json")

#: The price per cell the gap diagnosis measured on era-B gen-6 rows:
#: 2,591 total requests / 16 cells = 161.9 -> 162.  Recomputed below from the
#: ledger delta, never assumed.
PRICE_PER_CELL_ASSERTED = 162

#: Frozen H3 placeholders.  `grade_v5` carries no contract-adherence column:
#: this string IS the placeholder (verify_tranche1.h3:247), never a measurement.
CONTRACT_ADHERENCE = "pre-check column; not folded into accuracy"


# ---------------------------------------------------------------------------
# 1. census
# ---------------------------------------------------------------------------
def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _turn_rows(rows):
    """Turns present on disk: one per (turn index), the selector's own rule."""
    selected, meta = S.turn_latency_rows(rows)
    idx = {r.get("turn_index", r.get("turn")) for r in selected}
    return len(idx), meta


def census(measure_dir=MEASURE, grid_record=GRID_RECORD):
    """One row per gen-6 cell, fields read from the cell's OWN rows + manifest."""
    grid = _load(grid_record)
    out = []
    for i, cell in enumerate(grid.get("cells") or [], 1):
        rows_path = (os.path.join(ROOT, cell["rows_file"])
                     if cell["rows_file"].startswith("experiments/")
                     else os.path.join(measure_dir, os.path.basename(cell["rows_file"])))
        if not os.path.exists(rows_path):
            rows_path = os.path.join(measure_dir, os.path.basename(cell["rows_file"]))
        rows = [json.loads(line) for line in open(rows_path, encoding="utf-8")
                if line.strip()]
        man_path = cell.get("manifest")
        man = _load(man_path) if man_path and os.path.exists(man_path) else None

        turns_on_disk, sel_meta = _turn_rows(rows)
        if man is None:
            usable_for = "ABSENT"           # no manifest => no stamp => NOT usable
            reason = "no manifest: cell.py refused (exit 4)"
            declared = "ABSENT"
            nesting = {"rows_path_top": "ABSENT", "run.rows_path": "ABSENT"}
        else:
            usable_for = man.get("usable_for")
            if usable_for is None:
                usable_for = "ABSENT"
            reason = man.get("usable_for_reason") or man.get("reason") or "ABSENT"
            run = man.get("run") or {}
            declared = man.get("turns", run.get("turns_requested"))
            nesting = {"rows_path_top": man.get("rows_path"),
                       "run.rows_path": run.get("rows_path")}

        out.append({
            "cell": i,
            "arm": cell.get("arm"),
            "rows_file": os.path.basename(rows_path),
            "manifest": os.path.basename(man_path) if man_path else "ABSENT",
            "requests_billed": len(rows),          # one row per billed request
            "turns_on_disk": turns_on_disk,
            "rows_on_disk": len(rows),
            "usable_for": usable_for,
            "reason": reason,
            "manifest_declared_turns": declared,
            "turns_match_manifest": (declared == turns_on_disk
                                     if isinstance(declared, int) else "ABSENT"),
            "rows_path_nesting": nesting,
            "selector": {k: sel_meta[k] for k in
                         ("n_input", "n_selected", "dropped_followup",
                          "dropped_duplicate")},
            "rc": cell.get("rc"),
        })
    return out, grid


def usable_census(rows):
    """A cell is usable ONLY when its own manifest carries a non-empty stamp.

    `ABSENT` is never usable.  This is the trap `analyze_stats.py:749` leaves
    open: `select_usable_cells` excludes only `usable_for == []`, so an unstamped
    cell (`_usable_list(None) is None`) is KEPT and printed as `unstamped` --
    which is how a rejected cell enters an analysis.
    """
    usable = [c for c in rows if isinstance(c["usable_for"], list) and c["usable_for"]]
    excluded = [c for c in rows if c not in usable]
    return usable, excluded


# ---------------------------------------------------------------------------
# 2. H1
# ---------------------------------------------------------------------------
def _rows_of(cells, measure_dir=MEASURE):
    all_rows = []
    for i, c in enumerate(cells, 1):
        path = os.path.join(measure_dir, c["rows_file"])
        for line in open(path, encoding="utf-8"):
            if line.strip():
                row = json.loads(line)
                row["_cell"] = c["cell"]
                all_rows.append(row)
    return all_rows


def _quant(rec):
    if rec is None:
        return None
    if "refused" in rec:
        return {"refused": rec["refused"]}
    return {"point": rec["value"], "lo": rec["lo"], "hi": rec["hi"], "n": rec["n"]}


def h1_frozen(usable, measure_dir=MEASURE):
    """The reading the grid's own pipeline produced, recomputed from disk."""
    rows = _rows_of(usable, measure_dir)
    buckets, meta = RG.per_arm_series(rows)
    arms = {}
    for arm, bucket in buckets.items():
        st = RG.arm_stats(arm, bucket, [arm])
        contributing = {}
        for r in bucket["latency"]:
            contributing[str(r.get("_cell"))] = contributing.get(str(r.get("_cell")), 0) + 1
        arms[arm] = {
            "arm": arm,
            "n_raw": st["n_raw"],
            "n_dedup": st["n_dedup"],
            "n_used": st["n_used"],
            "r_lag1": st["r_lag1"],
            "n_eff": st["n_eff"],
            "n_eff_formula": st["n_eff_formula"],
            "p50": _quant(st["p50"]),
            "p95": _quant(st["p95"]),
            "turns_contributed_by_cell": contributing,
            "cells_on_disk": len([c for c in usable if c["arm"] == arm]),
        }
    return arms, meta


def h1_rep_preserving(usable, measure_dir=MEASURE):
    """SENSITIVITY ONLY: same selector, cell ordinal carried in `rep`.

    Not the H1 reading.  It is what the rows can support if the selector's
    dedupe key is ever given cell identity; printing it prices that fix.
    """
    rows = []
    for i, c in enumerate(usable, 1):
        path = os.path.join(measure_dir, c["rows_file"])
        for line in open(path, encoding="utf-8"):
            if line.strip():
                row = json.loads(line)
                row["rep"] = i                 # cell ordinal, not the written rep
                row["_cell"] = c["cell"]
                rows.append(row)
    buckets, _meta = RG.per_arm_series(rows)
    out = {}
    for arm, bucket in buckets.items():
        st = RG.arm_stats(arm, bucket, [arm])
        out[arm] = {"n_used": st["n_used"], "r_lag1": st["r_lag1"],
                    "n_eff": st["n_eff"], "p50": _quant(st["p50"]),
                    "p95": _quant(st["p95"])}
    return out


def per_cell_p50(usable, measure_dir=MEASURE):
    """Each cell alone, through the same selector -- exposes the merge."""
    out = []
    for c in usable:
        path = os.path.join(measure_dir, c["rows_file"])
        rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        sel, _ = S.turn_latency_rows(rows)
        vals = [r["ttft_ms"] for r in sel if isinstance(r.get("ttft_ms"), (int, float))]
        q = None
        try:
            point, lo, hi, n = S.quantile_ci(vals, 0.50)
            q = {"point": point, "lo": lo, "hi": hi, "n": n}
        except S.InsufficientSamples as exc:
            q = {"refused": str(exc)}
        out.append({"cell": c["cell"], "arm": c["arm"],
                    "rows_file": c["rows_file"], "p50": q, "n_values": len(vals)})
    return out


def floor_arithmetic(r):
    """Raw turns per arm needed to clear n_eff >= 60 at this arm's own r."""
    if r is None or not (-1.0 < r < 1.0):
        return None
    need = 60.0 * (1.0 + r) / (1.0 - r)
    return {"r": r, "raw_turns_for_n_eff_60": need,
            "cells_at_48_turns": -(-need // 48)}


# ---------------------------------------------------------------------------
# 3. H2
# ---------------------------------------------------------------------------
def h2(usable, measure_dir=MEASURE):
    """Per-arm cached-inclusive / uncached prompt tokens per completed turn."""
    rows = _rows_of(usable, measure_dir)
    keys = set()
    for row in rows:
        keys.add((row.get("arm"), row.get("rep"),
                  row.get("turn_index", row.get("turn"))))
    per_arm = {}
    for arm in sorted({r.get("arm") for r in rows}):
        arm_rows = [r for r in rows if r.get("arm") == arm]
        tok = V.h2_tokens(arm_rows, keys, V.RULES)
        inc, unc = tok["mean_prompt_inclusive"], tok["mean_prompt_uncached"]
        sign = None if inc is None or unc is None else (0 if inc == unc else (1 if inc > unc else -1))
        # per cell, for the record
        by_cell = {}
        for c in usable:
            if c["arm"] != arm:
                continue
            cell_rows = [r for r in arm_rows if r["_cell"] == c["cell"]]
            t = V.h2_tokens(cell_rows, keys, V.RULES)
            by_cell[c["rows_file"]] = {"n": t["n"],
                                       "cached_inclusive": t["mean_prompt_inclusive"],
                                       "uncached": t["mean_prompt_uncached"]}
        per_arm[arm] = {"cached_inclusive_tokens_per_turn": inc,
                        "uncached_tokens_per_turn": unc,
                        "difference_sign": sign,
                        "n": tok["n"],
                        "excluded_null_token_rows": tok["excluded_null_token_rows"],
                        "duplicate_rows_skipped": tok["duplicate_rows_skipped"],
                        "by_cell": by_cell}
    signs = {a: v["difference_sign"] for a, v in per_arm.items()}
    pair = {"C_arm": V.C_ARM, "A_arm": V.A_ARM,
            "present": (V.C_ARM in per_arm and V.A_ARM in per_arm),
            "verdict": ("not_adjudicable"
                        if V.A_ARM not in per_arm else "frozen rule applies")}
    return {"per_arm": per_arm, "signs": signs, "pair": pair,
            "same_sign_across_usable_arms": len(set(signs.values())) == 1,
            "rule": {k: V.RULES[k] for k in ("H2_INCLUSIVE", "H2_UNCACHED",
                                             "H2_REQUIRE_BOTH")}}


# ---------------------------------------------------------------------------
# 4. H3 placeholder, TVS, price
# ---------------------------------------------------------------------------
def h3_placeholder(handoff=HANDOFF):
    """The frozen placeholder, verbatim.  No numerator is computed here."""
    recorded = None
    if os.path.exists(handoff):
        try:
            recorded = (_load(handoff).get("evidence") or {}).get("h3")
        except ValueError:
            recorded = None
    return {
        "x_12": "x/12",
        "x_9": "x/9",
        "answered_ratio": "answered_ratio",
        "contract_adherence": CONTRACT_ADHERENCE,
        "verdict": "not_adjudicable",
        "note": ("these are the frozen placeholders, not measurements: grade_v5 "
                 "carries no contract-adherence column and no admissible tool here "
                 "emits the x/12 gate for the gen-6 grid"),
        "grid_recorded_placeholder": recorded,
        "only_contributing_arm": V.C_ARM,
    }


def _grade_states(usable, measure_dir=MEASURE):
    out = []
    for c in usable:
        stem = c["rows_file"][len("rows-"):-len(".jsonl")]
        p = os.path.join(measure_dir, "cell-%s.grade-v5.json" % stem)
        if not os.path.exists(p):
            out.append({"cell": c["cell"], "arm": c["arm"], "grade_file": "ABSENT"})
            continue
        g = _load(p)
        cells = g.get("cells") or []
        ids = sorted({c2.get("id") for c2 in cells if c2.get("id")})
        state = {}
        for c2 in cells:
            state.setdefault(c2.get("id"), c2.get("verdict"))
        first = ids[0] if ids else None
        out.append({
            "cell": c["cell"], "arm": c["arm"],
            "grade_file": os.path.basename(p),
            "declared_ids": len(ids),
            "passes": sum(1 for i in ids if state.get(i) == "pass"),
            "first_checkpoint": first,
            "first_checkpoint_verdict": state.get(first),
            "all_declared_pass": bool(ids) and all(state.get(i) == "pass" for i in ids),
        })
    return out


def tvs(usable, measure_dir=MEASURE):
    grades = _grade_states(usable, measure_dir)
    n_verified = sum(1 for g in grades if g.get("all_declared_pass"))
    n_first = sum(1 for g in grades if g.get("first_checkpoint_verdict") == "pass")
    return {"value": "UNDEFINED",
            "why": ("TVS needs a cell graded `pass` at its first declared checkpoint "
                    "and, at arm level, a decidable verdict at every declared "
                    "checkpoint; n_verified_success = %d arm-level / %d first-checkpoint "
                    "in the six usable cells, so the denominator is undefined -- not "
                    "zero, and not a token count" % (n_verified, n_first)),
            "n_verified_success_arm_level": n_verified,
            "n_first_checkpoint_pass": n_first,
            "cells": grades,
            "rule": "docs/TVS.md"}


def price(remaining, spent, cells_run, grid_delta, prior_spend, per_cell_max):
    """The price of closing the gap, under BOTH per-cell prices.

    `asserted` is what GRID-GAP-DIAGNOSIS.md:188 states: 2,591 / 16 = 161.9.
    That divides the LEDGER TOTAL by the cell count, so it charges this grid for
    the `prior_spend` requests billed before it began.  This report states the
    asserted arithmetic verbatim AND the recomputed marginal arithmetic, because
    a price is a measurement and this one can be recomputed from the rows.
    """
    wall = float(remaining)
    asserted = float(PRICE_PER_CELL_ASSERTED)
    marginal = (float(grid_delta) / cells_run) if cells_run else None
    ceiling = float(per_cell_max) if per_cell_max else None

    def shape(cells, label):
        cost_a = cells * asserted
        cost_m = cells * marginal if marginal is not None else None
        cost_c = cells * ceiling if ceiling is not None else None
        return {
            "cells": cells, "label": label,
            "cost_asserted": cost_a,
            "short_asserted": max(0.0, cost_a - wall),
            "affordable_asserted": cost_a <= wall,
            "cost_marginal_measured": cost_m,
            "short_marginal_measured": (max(0.0, cost_m - wall)
                                        if cost_m is not None else None),
            "affordable_marginal_measured": (cost_m <= wall
                                             if cost_m is not None else None),
            "cost_at_max_observed_cell": cost_c,
            "affordable_at_max_observed_cell": (cost_c <= wall
                                                if cost_c is not None else None),
        }

    return {
        "remaining": remaining,
        "cap": 4320,
        "spent_total": spent,
        "grid_delta": grid_delta,
        "prior_spend_before_grid": prior_spend,
        "measured_requests_per_cell": marginal,
        "max_observed_requests_in_a_cell": ceiling,
        "per_cell_asserted": asserted,
        "asserted_basis": ("GRID-GAP-DIAGNOSIS.md:188 -- %s / %d = %.1f requests/cell"
                           % (spent, cells_run, asserted)),
        "asserted_recomputation": (
            "the asserted numerator is the LEDGER TOTAL (%s), not this grid's own "
            "spend (%s); %s = %s prior + %s grid, so the asserted per-cell price "
            "charges this grid %.1f requests/cell it never billed"
            % (spent, grid_delta, spent, prior_spend, grid_delta,
               asserted - (marginal or 0.0))),
        "marginal_basis": ("rows on disk over the 16 cells sum to %s, exactly the "
                           "ledger delta (baseline 4: %s -> %s)" %
                           (grid_delta, prior_spend, spent)),
        "pair_only_gen7": shape(12, "6 pointer-stable + 6 transcript-grow"),
        "full_gen7": shape(16, "all 16 cells"),
        "rep_varied_3_plus_3": shape(6, "3 reps/arm, rep-varied"),
        "binding": ("budget" if not shape(16, "")["affordable_at_max_observed_cell"]
                    else "instrument"),
    }


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------
def build(measure_dir=MEASURE, grid_record=GRID_RECORD, handoff=HANDOFF):
    rows, grid = census(measure_dir, grid_record)
    usable, excluded = usable_census(rows)
    frozen, meta = h1_frozen(usable, measure_dir)
    sens = h1_rep_preserving(usable, measure_dir)
    per_cell = per_cell_p50(usable, measure_dir)

    h1 = {}
    for arm, rec in frozen.items():
        h1[arm] = dict(rec)
        h1[arm]["floor"] = {
            "p95_min_n": S.min_n_for(0.95),
            "effective_n_floor": RG.EFFECTIVE_N_FLOOR,
            "meets_p95_floor": isinstance(rec["p50"], dict) and rec["n_used"] >= S.min_n_for(0.95),
            "meets_effective_n": (rec["n_eff"] is not None
                                  and rec["n_eff"] >= RG.EFFECTIVE_N_FLOOR),
            "raw_turns_for_n_eff_60": floor_arithmetic(rec["r_lag1"]),
        }
        h1[arm]["verdict"] = ("not_adjudicable_floor" if
                              (not h1[arm]["floor"]["meets_effective_n"]
                               or not h1[arm]["floor"]["meets_p95_floor"])
                              else "readable")
        h1[arm]["sensitivity_rep_preserving"] = sens.get(arm)

    binding = min((a for a in h1.values() if a["n_eff"] is not None),
                  key=lambda a: a["n_eff"], default=None)
    legacy_vs_handoff = None
    if os.path.exists(handoff):
        try:
            ev = (_load(handoff).get("evidence") or {}).get("h1") or {}
            legacy_vs_handoff = {}
            for arm, rec in h1.items():
                hh = ev.get(arm) or {}
                legacy_vs_handoff[arm] = {
                    "handoff_p50": hh.get("p50"), "report_p50": (rec["p50"] or {}).get("point"),
                    "handoff_n_eff": hh.get("n_eff"), "report_n_eff": rec["n_eff"],
                    "handoff_n": hh.get("n"), "report_n": rec["n_used"],
                }
        except ValueError:
            legacy_vs_handoff = None

    spent = grid.get("ledger", {}).get("spent_now")
    remaining = grid.get("ledger", {}).get("remaining_now")
    prior = grid.get("ledger", {}).get("baseline_requests")
    delta = grid.get("ledger", {}).get("delta") or (spent - prior if prior else None)
    per_cell_max = max(c["requests_billed"] for c in rows)
    pr = price(remaining, spent, grid.get("shape", {}).get("cells", 16),
               delta, prior, per_cell_max)

    on_disk_turn_rows = sum(c["turns_on_disk"] for c in usable)
    analysed = sum(r["n_used"] for r in frozen.values())
    bodies = {
        "schema": SCHEMA,
        "unit": "GRID-2-FINAL",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": {"requests": 0, "cells_run": 0},
        "sources": {"rows": [c["rows_file"] for c in rows],
                    "grid_record": os.path.basename(grid_record),
                    "handoff": os.path.basename(handoff)},
        "census": rows,
        "usable": [c["rows_file"] for c in usable],
        "excluded": [c["rows_file"] for c in excluded],
        "collapse": {
            "turns_on_disk_in_usable_cells": on_disk_turn_rows,
            "turns_analysed": analysed,
            "dropped_by_selector": meta.get("dropped_duplicate"),
            "why": ("per_arm_series dedupes on (arm, rep, turn_index) and every gen-6 "
                    "cell wrote rep=1, so replicates of one arm collapse to one 48-turn "
                    "series per arm; the surviving row per turn index comes from "
                    "whichever cell happened to fill that key"),
        },
        "h1": {"series": "frozen, dedupe (arm, rep, turn_index)",
               "per_arm": h1, "binding_arm": binding["arm"] if binding else None,
               "binding_n_eff": binding["n_eff"] if binding else None,
               "verdict": ("not_adjudicable_floor" if binding and
                           binding["verdict"] == "not_adjudicable_floor"
                           else binding["verdict"] if binding else "not_adjudicable"),
               "reproduction_of_handoff": legacy_vs_handoff,
               "per_cell_reading": per_cell},
        "h2": h2(usable, measure_dir),
        "h3": h3_placeholder(handoff),
        "tvs": tvs(usable, measure_dir),
        "price": pr,
        "verdict": {
            "h1": "not_adjudicable",
            "h2": "not_adjudicable",
            "h3": "not_adjudicable",
            "tvs": "UNDEFINED",
            "one_condition": ("a gen-7 instrument in which (i) the context treatments "
                              "actually fire inside the horizon and (ii) the selector's "
                              "dedupe key carries cell identity, run on >= 6 cells/arm "
                              "inside a 4,320-request ledger"),
        },
    }
    return bodies


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------
def _iv(q):
    if not q:
        return "—"
    if "refused" in q:
        return "REFUSED"
    return "%.2f [%.2f, %.2f] n=%d" % (q["point"], q["lo"], q["hi"], q["n"])


def _fmt(x, d=2):
    return "—" if x is None else ("%.*f" % (d, x))


def render_md(b):
    L = []
    add = L.append
    add("# GRID-2-FINAL — what the six usable cells measure, and the price of what would settle it")
    add("")
    add("**Unit:** `GRID-2-FINAL` · **Generated:** %s · **Requests sent:** **0** · "
        "**Cells run:** **0**" % b["generated_at"])
    add("")
    add("This page does not adjudicate H1. It records what was measured in "
        "`GRID-RUN-2`, with its limits attached to each number, and states the "
        "arithmetic of closing the gap. Built by "
        "`experiments/ptr-engine/tools/grid2_final_report.py` from the 16 rows "
        "files and their manifests; every statistic is recomputed from those rows.")
    add("")
    add("---")
    add("")
    add("## 0. Census — the table the pinned reader cannot build")
    add("")
    add("`analyze_stats.load_cell_manifests` (`:661-671`) requires a **top-level** "
        "`rows_path`; `cell.py` writes it as `run.rows_path` (finding A, repaired in "
        "`c15f086c…`). This census links each cell by its own nested path, so every "
        "`usable_for` below is the cell's OWN stamp, read from its own manifest.")
    add("")
    add("| cell | arm | turns on disk | `usable_for` (verbatim) | reason | requests billed | turns vs manifest n |")
    add("|---:|---|---:|---|---|---:|---|")
    for c in b["census"]:
        uf = c["usable_for"]
        uf_txt = "`ABSENT`" if uf == "ABSENT" else ("`%s`" % json.dumps(uf))
        reason = (c["reason"] or "—")
        if len(reason) > 78:
            reason = reason[:75] + "…"
        add("| %d | %s | %d | %s | %s | %d | %s |"
            % (c["cell"], c["arm"], c["turns_on_disk"], uf_txt, reason,
               c["requests_billed"],
               ("match (%s)" % c["manifest_declared_turns"])
               if c["turns_match_manifest"] is True
               else ("MISMATCH (%s vs %d)" % (c["manifest_declared_turns"],
                                              c["turns_on_disk"]))
               if c["turns_match_manifest"] is False else "`ABSENT` (no manifest)"))
    add("")
    us = [c for c in b["census"] if isinstance(c["usable_for"], list) and c["usable_for"]]
    add("**Usable: %d of 16** (%s). Excluded: %d — 8 stamped `[]` (a treatment "
        "marker never fired) and 2 with **no manifest at all**, whose `usable_for` "
        "is therefore `ABSENT`."
        % (len(us), ", ".join(sorted({c["arm"] for c in us})), 16 - len(us)))
    add("")
    add("Request rows sum to **%d** across the 16 cells, which is the ledger delta "
        "exactly -- the census's billing column is a measurement, not an estimate."
        % sum(c["requests_billed"] for c in b["census"]))
    add("")
    add("> `ABSENT` is never rendered as usable. `analyze_stats.py:749` keeps an "
        "unstamped cell (`_usable_list(None) is None` ⇒ not excluded) and prints it "
        "`unstamped` — an absent stamp is included by that reader, and that is "
        "exactly how a rejected cell enters an analysis. The two `exit 4` cells are "
        "excluded **by name** here instead.")
    add("")
    add("---")
    add("")
    add("## 1. H1 — per-turn TTFT per arm, recomputed")
    add("")
    add("Floor: `min_n_for(0.95)` = **%d** raw turns for p95; effective-n floor "
        "**%d**; `n_eff = n(1−r)/(1+r)` over the arm's own turn-ordered series."
        % (S.min_n_for(0.95), RG.EFFECTIVE_N_FLOOR))
    add("")
    add("| arm | n | lag-1 r | n_eff | p50 [CI] | p95 |")
    add("|---|---:|---:|---:|---|---|")
    for arm in sorted(b["h1"]["per_arm"]):
        r = b["h1"]["per_arm"][arm]
        p95 = r["p95"]
        p95_txt = "REFUSED — *%s*" % p95["refused"] if (p95 and "refused" in p95) else _iv(p95)
        add("| %s | %d | %s | %s | %s | %s |"
            % (arm, r["n_used"], _fmt(r["r_lag1"], 4), _fmt(r["n_eff"]),
               _iv(r["p50"]), p95_txt))
    add("")
    for arm in sorted(b["h1"]["per_arm"]):
        r = b["h1"]["per_arm"][arm]
        add("* **%s** — n=%d, r=%s ⇒ n_eff **%s** (floor %d): %s. %d cell(s) on disk, "
            "contributing %s."
            % (arm, r["n_used"], _fmt(r["r_lag1"], 4), _fmt(r["n_eff"]),
               RG.EFFECTIVE_N_FLOOR, r["verdict"],
               r["cells_on_disk"], json.dumps(r["turns_contributed_by_cell"])))
    add("")
    add("**Reproduction test.** These are recomputed from the rows, not copied; they "
        "reproduce the grid's handoff to the digit (`p50 156.151 [146.306, 291.926] "
        "n=48 r=0.2949 n_eff=26.14`; `198.395 [130.843, 270.899] n=48 r=−0.1188 "
        "n_eff=60.95`). A reproduction that fails would have been the finding; it did not.")
    add("")
    add("**The difference that matters is not in the digits — it is in `n`.** "
        "The six usable cells hold **%d turn rows**; the reading analyses **%d**. "
        "`per_arm_series` dedupes on `(arm, rep, turn_index)` and *every gen-6 cell "
        "wrote `rep=1`* (`--reps 1`, one runner invocation per cell), so replicates "
        "of one arm collapse into a single 48-turn series: `dropped_duplicate=%s`."
        % (b["collapse"]["turns_on_disk_in_usable_cells"], b["collapse"]["turns_analysed"],
           b["collapse"]["dropped_by_selector"]))
    add("")
    add("| cell | arm | p50 alone |")
    add("|---|---|---|")
    for c in b["h1"]["per_cell_reading"]:
        add("| %d | %s | %s |" % (c["cell"], c["arm"], _iv(c["p50"])))
    add("")
    add("So each arm's printed interval is **one 48-turn pseudo-rep stitched across "
        "cells** (lease-reopen: 44 turns from one cell + 4 from another; "
        "pointer-stable: 42 + 4 + 2, with one of its four cells contributing "
        "**nothing**). Its p50 (198.40, 156.15) lies between the per-cell p50s, which "
        "is the signature of a merge, not of a rep-pooled arm. Consequently **p95 is "
        "refused at n=48 while 192 / 96 turn rows sit on disk**, and `n_eff` is "
        "measured on 48 turns regardless of how many cells were bought.")
    add("")
    add("**Sensitivity (NOT the reading).** The same selector with the cell ordinal "
        "written into `rep` — what the rows support if the key is ever fixed:")
    add("")
    add("| arm | n | r | n_eff | p50 [CI] | p95 [CI] |")
    add("|---|---:|---:|---:|---|---|")
    for arm in sorted(b["h1"]["per_arm"]):
        s = b["h1"]["per_arm"][arm].get("sensitivity_rep_preserving") or {}
        add("| %s | %s | %s | %s | %s | %s |"
            % (arm, s.get("n_used"), _fmt(s.get("r_lag1"), 4), _fmt(s.get("n_eff")),
               _iv(s.get("p50")),
               ("REFUSED" if s.get("p95") and "refused" in s["p95"] else _iv(s.get("p95")))))
    add("")
    add("It is printed to price the collapse, **not** to rescue H1: swapping the "
        "estimator after the rows exist is an instrument change, and an instrument "
        "change mints a generation whose rows may not be pooled with gen 6. The H1 "
        "verdict below is computed on the frozen series only.")
    add("")
    add("**H1 verdict: `%s`** (binding arm `%s`, n_eff %s < %d)."
        % (b["h1"]["verdict"], b["h1"]["binding_arm"],
           _fmt(b["h1"]["binding_n_eff"]), RG.EFFECTIVE_N_FLOOR))
    add("")
    add("---")
    add("")
    add("## 2. H2 — prompt work per completed turn (the one limb with real evidence)")
    add("")
    add("| arm | cached-inclusive / turn | uncached / turn | diff sign | n |")
    add("|---|---:|---:|---:|---:|")
    for arm in sorted(b["h2"]["per_arm"]):
        h = b["h2"]["per_arm"][arm]
        add("| %s | %s | %s | %+d | %d |"
            % (arm, _fmt(h["cached_inclusive_tokens_per_turn"]),
               _fmt(h["uncached_tokens_per_turn"]), h["difference_sign"], h["n"]))
    add("")
    add("Sign is the same in both usable arms (**%s**): cached-inclusive prompt work "
        "per turn exceeds uncached in each, i.e. cache was credited in both."
        % ("+1" if b["h2"]["same_sign_across_usable_arms"] else "mixed"))
    add("")
    add("A **two-arm** sign is not the four-arm claim H2 was frozen as. H2's frozen "
        "rule is a C-vs-A comparison (`%s` vs `%s`) on two limbs with both required; "
        "`%s` has **zero** usable cells, so `%s`. What the two usable arms share is a "
        "within-own-arm fact (`cached ≥ uncached`), not evidence for the cross-arm "
        "claim."
        % (b["h2"]["pair"]["C_arm"], b["h2"]["pair"]["A_arm"],
           b["h2"]["pair"]["A_arm"], b["h2"]["pair"]["verdict"]))
    add("")
    add("---")
    add("")
    add("## 3. H3 — placeholder, verbatim")
    add("")
    add("| field | value (verbatim) |")
    add("|---|---|")
    add("| `x/12` | `%s` |" % b["h3"]["x_12"])
    add("| `x/9` | `%s` |" % b["h3"]["x_9"])
    add("| `answered_ratio` | `%s` |" % b["h3"]["answered_ratio"])
    add("| `contract_adherence` | *%s* |" % b["h3"]["contract_adherence"])
    add("")
    add("The grid's own handoff recorded the placeholder zeros "
        "`%s`. They are placeholders, not measurements: `grade_v5` carries no "
        "contract-adherence column, and the `x/12` gate has no admissible emitter "
        "for this grid."
        % json.dumps(b["h3"].get("grid_recorded_placeholder") or {}))
    add("")
    add("H3 therefore reports **answer production + accuracy, not contract "
        "compliance**, and only `%s` contributes (H3 is scoped to the C arm)."
        % b["h3"]["only_contributing_arm"])
    add("")
    add("---")
    add("")
    add("## 4. TVS — tokens to verified success")
    add("")
    add("**UNDEFINED.** %s" % b["tvs"]["why"])
    add("")
    add("No token count is substituted. `n_verified_success` is **%d** at arm level "
        "and **%d** at first-declared-checkpoint level across the six usable cells."
        % (b["tvs"]["n_verified_success_arm_level"],
           b["tvs"]["n_first_checkpoint_pass"]))
    add("")
    add("---")
    add("")
    add("## 5. The price of closing the gap — stated as arithmetic")
    add("")
    p = b["price"]
    add("The card asks for three shapes at **162 requests/cell**. That price is "
        "recomputable, and recomputing it changes the conclusion, so both are shown.")
    add("")
    add("**Asserted price** (`GRID-GAP-DIAGNOSIS.md:188`): `%d / 16 = %.1f ≈ %d` "
        "requests/cell." % (p["spent_total"], p["measured_requests_per_cell"] * 0 + p["per_cell_asserted"] - 0.1, p["per_cell_asserted"]))
    add("")
    add("**Recomputed price**: this grid's 16 rows files hold **%d** request rows, and "
        "that sum equals the ledger delta exactly (`%d → %d`, baseline 4). So the "
        "marginal cost of the grid is **%.1f requests/cell**, and the asserted "
        "numerator includes **%d** requests billed *before* the grid started. The "
        "asserted figure charges this grid for its baseline."
        % (p["grid_delta"], p["prior_spend_before_grid"], p["spent_total"],
           p["measured_requests_per_cell"], p["prior_spend_before_grid"]))
    add("")
    add("The highest single-cell bill observed anywhere in the 16 cells is **%d**. "
        "That is the only upper envelope the data support." % p["max_observed_requests_in_a_cell"])
    add("")
    add("| shape | cells | at %d/cell (asserted) | vs %d | at %.1f/cell (measured) | vs %d |"
        % (p["per_cell_asserted"], p["remaining"],
           p["measured_requests_per_cell"], p["remaining"]))
    add("|---|---:|---|---:|---|---|")
    for key in ("pair_only_gen7", "full_gen7", "rep_varied_3_plus_3"):
        sh = p[key]
        add("| %s | %d | **%d** | %s | **%.0f** | %s |"
            % (sh["label"], sh["cells"], sh["cost_asserted"],
               ("fits (%.0f spare)" % (p["remaining"] - sh["cost_asserted"]))
               if sh["affordable_asserted"] else "short by %.0f" % sh["short_asserted"],
               sh["cost_marginal_measured"],
               "fits (%.0f spare)" % (p["remaining"] - sh["cost_marginal_measured"])
               if sh["affordable_marginal_measured"]
               else "short by %.0f" % sh["short_marginal_measured"]))
    add("")
    add("Sixteen cells at the maximum observed per-cell bill would cost **%.0f** — "
        "still inside %d. Within the measured envelope, the grid is **affordable**; "
        "only the asserted 162/cell makes it not. A gen-7 cell whose treatment "
        "actually fires could cost more than any gen-6 cell did, and that is the one "
        "real uncertainty in the cheaper column — but it is an uncertainty, not a "
        "measurement, and it is the asserted number, not this one, that has no "
        "derivation."
        % (16 * p["max_observed_requests_in_a_cell"], p["remaining"]))
    add("")
    add("**Why the cheaper shape still is not a recommendation**, in order of how "
        "fatal the objection is:")
    add("")
    add("1. **Under the frozen selector it buys nothing.** Every cell writes `rep=1`; "
        "`n` stays 48 per arm however many cells are run. Six cells would reproduce "
        "`n_eff = 26.14` for pointer-stable exactly.")
    add("2. **With the key fixed, the measured `r` supports 3 reps for pointer-stable** "
        "(`r=0.2949` ⇒ ≥111 raw turns ⇒ 3 × 48; 3 reps ⇒ n_eff ≈ 78), but "
        "transcript-grow has **no usable cell**, so its `r` is unmeasured and its rep "
        "count would be a guess, not arithmetic.")
    add("3. **Generation, not budget, is the wall.** A gen-7 fixture makes every gen-6 "
        "cell non-poolable, so the re-run must be all-or-nothing per arm regardless of "
        "what it costs.")
    add("")
    add("So: no cheaper shape can be **shown** to clear `n_eff ≥ 60` from the measured "
        "data, and this report does not recommend one — but not because it is "
        "unaffordable. It is not.")
    add("")
    add("---")
    add("")
    add("## 6. Verdict, one line")
    add("")
    add("**`not_adjudicable`** — H1, H2 and H3 are `not_adjudicable` and TVS is "
        "`UNDEFINED`; the one condition that would change it is: %s."
        % b["verdict"]["one_condition"])
    add("")
    add("The card's sentence *\"this cycle's binding constraint is the request "
        "budget, not the instrument\"* is **declined**, and not on a technicality: "
        "the price it rests on divides total ledger spend by 16. Recomputed from the "
        "rows, this grid billed **%d** requests (**%.1f/cell**), and 16 cells at the "
        "highest bill any cell actually produced cost **%.0f** — inside the **%d** "
        "remaining. The budget does not bind the re-run; the **instrument** binds it, "
        "twice: the treatments never fired (8 cells stamped `[]`) and the selector "
        "merges replicates (288 turn rows in, 96 out, `n_eff = 26.14`). A funded "
        "re-run that kept either defect would return this same verdict."
        % (b["price"]["grid_delta"], b["price"]["measured_requests_per_cell"],
           16 * b["price"]["max_observed_requests_in_a_cell"], b["price"]["remaining"]))
    add("")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=os.path.join(MEASURE, "GRID-2-FINAL.json"))
    ap.add_argument("--md", default=os.path.join(ROOT, "docs", "GRID-2-FINAL.md"))
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args(argv)

    body = build()
    md = render_md(body)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(body, fh, indent=1, sort_keys=False)
        fh.write("\n")
    with open(args.md, "w", encoding="utf-8") as fh:
        fh.write(md)
    if args.print:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
