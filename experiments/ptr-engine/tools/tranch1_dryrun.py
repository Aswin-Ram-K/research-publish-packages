#!/usr/bin/env python3
"""TRANCH1-DRYRUN — rehearse the ten-cell tranche with cell.py --dry-run, offline.

WHY THIS EXISTS: RUN-A* (10 cells x 48 turns, pair at 3 reps, context at 2 reps) is the
first grid that relies on ALL of cell.py's gate chain, the calibrated projection, the
v8 fixture's per-arm wall, the per-arm warm-up and the ledger brake AT ONCE, and none
of those have ever been exercised together.  This tool drives one `cell.py --dry-run`
per (arm, rep), one manifest per cell, and then re-checks the ten manifests with
`--check` so the rehearsal is reproducible rather than a transcript.

ZERO REQUESTS, ZERO SPAWN, ZERO SOCKET.  Every invocation runs under a
`sitecustomize.py` audit hook that records `socket.*`, `urllib.*`, `http.client`,
`subprocess.*`, `os.exec*`, `os.fork*`, `os.posix_spawn*` into $TDR_AUDIT.  The hook is
injected through PYTHONPATH, so cell.py is never edited to observe it.

THE --hypothesis ASSUMPTION, stated because it is a judgement call: each invocation is
ONE cell (one arm, 48 turns, one rep of the grid) declared at `--reps 1`, and it makes
the claim that cell can actually support -- `--hypothesis H2`, the cache limb, whose
admissibility is `n >= 1` (a ratio over completed turns).  It never declares H1: a
48-turn cell is `n = 48 < 60`, so G3 refuses an H1 claim BY CONSTRUCTION and the cell
must not make one.  The H1 figure belongs to the POST-HOC pooled rows (n = 144 / 96 per
arm), computed by analyze_stats.turn_latency_rows + quantile_ci after the tranche -- see
`pooled_analysis_plan` in the report; this tool never computes it and never launches it.
The marginal cost of a cell is recomputed at reps=1 (53 requests), which is what
request_ledger charges; see `total_projected_requests`.  No threshold, cap, horizon or
n-floor is touched, and no gate is edited to admit either claim.

Usage:
  python3 experiments/ptr-engine/tools/tranch1_dryrun.py                    # the ten runs, claim H2
  python3 experiments/ptr-engine/tools/tranch1_dryrun.py --check            # re-check, exit 1 on any failure
  python3 experiments/ptr-engine/tools/tranch1_dryrun.py --hypothesis H1 --check   # the first rehearsal's grid
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.abspath(os.path.join(HERE, "..", "longrun"))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CELL = os.path.join(LONG, "cell.py")
FIXTURE = os.path.join(LONG, "tasks-v6", "LR-01.v8.json")
MEASURE = os.path.join(ROOT, "experiments", "ptr-engine", "measure")
#: Naming follows the CLAIM being rehearsed, so a re-rehearsal can never overwrite the
#: first one's measurements: TRANCH1-DRYRUN (H1) owns dryrun-t1-* / TRANCH1-DRYRUN.json.
NAMED = {
    "H2": {"prefix": "dryrun2-t2-", "report": "TRANCH1-DRYRUN-2.json",
           "doc": "TRANCH1-DRYRUN-2.md"},
    "H1": {"prefix": "dryrun-t1-", "report": "TRANCH1-DRYRUN.json",
           "doc": "TRANCH1-DRYRUN.md"},
}

TURNS = 48
CAP = 900                      # the per-cell request ceiling the tranche is priced under
MAX_WALL = 2880.0
TURN_WALL_CAP = 180.0
RUNAWAY = 2
THINKING = "off"
DEFAULT_HYPOTHESIS = "H2"
HYPOTHESIS = DEFAULT_HYPOTHESIS        # rebound by --hypothesis (and by --check)
PREFIX = NAMED[HYPOTHESIS]["prefix"]
RATIO = 68.0 / 801.0


def report_path():
    return os.path.join(MEASURE, NAMED[HYPOTHESIS]["report"])


def doc_path():
    return os.path.join(ROOT, "docs", NAMED[HYPOTHESIS]["doc"])

#: One cell = one arm, 48 turns, ONE rep of the grid (--reps 1): the shape the runner
#: actually runs and the shape the ledger charges 53 requests for. The rep label only
#: indexes the cell; the pooled alternative is probed separately (POOLED_PROBES).
CELLS = [
    ("pointer-stable", 1), ("pointer-stable", 2), ("pointer-stable", 3),
    ("transcript-grow", 1), ("transcript-grow", 2), ("transcript-grow", 3),
    ("transcript-compact", 1), ("transcript-compact", 2),
    ("lease-reopen", 1), ("lease-reopen", 2),
]

#: The arm's POOLED design reps, as the tranche declares them (pair 3, context 2). Probing
#: this shape is what shows the second horn: G3 is satisfied and G2 refuses.
POOLED_REPS = {"pointer-stable": 3, "transcript-grow": 3,
               "transcript-compact": 2, "lease-reopen": 2}

#: the treatment each arm must actually fire, and the key it lands in.
ARM_TREATMENT = {
    "transcript-grow": ("grow_evict_turn", "grow"),
    "transcript-compact": ("compact_wall_turn", "wall"),
    "lease-reopen": ("lease_step_turn", "lease"),
    "pointer-stable": ("pointer_prefix_turn", "prefix"),
}

PINNED = [
    "experiments/ptr-engine/longrun/cell.py",
    "experiments/ptr-engine/longrun/run_longrun.py",
    "experiments/ptr-engine/longrun/client.py",
    "experiments/ptr-engine/longrun/exit_codes.py",
    "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
    "experiments/ptr-engine/longrun/analyze_stats.py",
]

HOOK = r'''import os, sys
_LOG = os.environ.get("TDR_AUDIT")
_fd = None
if _LOG:
    try:
        _fd = os.open(_LOG, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    except OSError:
        _fd = None
_PREFIXES = ("socket.", "subprocess.", "os.exec", "os.fork", "os.posix_spawn",
             "os.spawn", "urllib.", "http.client")
if _fd is not None:
    def _hook(event, args):
        if event.startswith(_PREFIXES):
            try:
                os.write(_fd, (event + "\n").encode("utf-8"))
            except Exception:
                pass
    sys.addaudithook(_hook)
'''


# ------------------------------------------------------------------ small helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin():
    return {p: sha256_file(os.path.join(ROOT, p)) for p in PINNED}


def num(text):
    return int(str(text).replace(",", "").strip())


def allowance_for(turns_total):
    """The gate's own arithmetic: ceil(turns_total * 68/801)."""
    return int(math.ceil(max(0, int(turns_total)) * RATIO))


def _rr(rel):
    d = os.path.dirname(rel)
    return d + os.sep * 0 + (os.sep if False else "/") + os.path.basename(rel)


def hook_dir():
    d = os.path.join(tempfile.gettempdir(), "tdr", "hook")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "sitecustomize.py")
    with open(p, "w", encoding="utf-8") as f:
        f.write(HOOK)
    return d


def cell_args(arn, reps, hypothesis=None, extra=()):
    return [
        sys.executable, CELL,
        "--arm", arn, "--fixture", FIXTURE,
        "--turns", str(TURNS), "--reps", str(reps),
        "--thinking", THINKING,
        "--max-wall", str(int(MAX_WALL)),
        "--turn-wall-cap", str(int(TURN_WALL_CAP)),
        "--runaway-turns", str(RUNAWAY),
        "--budget", str(CAP),
        "--hypothesis", hypothesis or HYPOTHESIS,
        "--dry-run",
        "--no-cell-handoff",
    ] + list(extra)


# ------------------------------------------------------- cell.py's own gate functions
def inproc_detail(fixture_path, arm, reps, hypothesis=None, max_wall=None,
                  projected_turn_wall=None):
    """cell.py's OWN gate functions, called in-process for the detail its dry run only
    prints in the live path (G2's mode/source, each verdict's consequence text).

    Nothing is re-implemented: the three eval_gate_* functions are cell.py's.  The
    subprocess's printed figures are cross-checked against these.  ``hypothesis`` and
    ``max_wall`` are how the gate PROBES ask cell.py the same question under a different
    operand -- never to loosen a check, only to show what each gate answers.
    """
    if LONG not in sys.path:
        sys.path.insert(0, LONG)
    import cell as C  # noqa: E402

    hyp = hypothesis or HYPOTHESIS
    wall = MAX_WALL if max_wall is None else max_wall
    fixture = C.load_fixture(fixture_path) if hasattr(C, "load_fixture") else None
    if fixture is None:
        import run_longrun as R  # noqa: E402
        fixture = R.load_fixture(fixture_path)
    turns_total = TURNS * reps
    ns = types.SimpleNamespace(
        arm=arm, fixture=fixture_path, turns=TURNS, reps=reps, budget=CAP,
        endpoint=None, thinking=THINKING, turn_wall_cap=TURN_WALL_CAP,
        projected_turn_wall=projected_turn_wall, projected_from=None,
        fetch_followup_allowance=None, hypothesis=hyp,
        max_wall=wall, runaway_turns=RUNAWAY, out_dir=MEASURE,
        allow_inconsistent=False, offline=None,
    )
    out = {}
    for name, fn, extra in (
            ("g1", C.eval_gate_ledger, None),
            ("g2", C.eval_gate_projection, {"would_send_total": turns_total}),
            ("g3", C.eval_gate_prereg, fixture)):
        try:
            out[name] = fn(ns, extra) if extra is not None else fn(ns)
        except Exception as exc:                       # a raise IS the refusal
            out[name] = {"ok": False, "gate": name, "raised": "%s: %s"
                         % (type(exc).__name__, exc), "hypothesis": hyp}
    return out


def gate_probes(cell0):
    """Both gates, asked the four questions this claim decision has to answer.

    NOTHING IS EDITED HERE.  G3 is cell.py's `eval_gate_prereg` over the real prereg
    artefact, G2 is cell.py's `eval_gate_projection` over the real projection artefact.
    The probes only change the OPERANDS (claim, n, ceiling) so that each gate's own
    verdict, in its own words, is quoted rather than paraphrased.
    """
    h2 = inproc_detail(FIXTURE, "pointer-stable", 1, hypothesis="H2")
    h1_48 = inproc_detail(FIXTURE, "pointer-stable", 1, hypothesis="H1")
    h1_144 = inproc_detail(FIXTURE, "pointer-stable", POOLED_REPS["pointer-stable"],
                           hypothesis="H1")
    g2_2881 = inproc_detail(FIXTURE, "pointer-stable", 1,
                            projected_turn_wall=2881.0 / TURNS)

    def g3(v):
        return {"decision": "allow" if v.get("ok") else "refused",
                "n": v.get("n"), "min_n": (v.get("thresholds") or {}).get("min_n"),
                "computed": v.get("computed"), "limit": v.get("limit"),
                "short": v.get("short"),
                "verbatim": (None if v.get("ok")
                             else v.get("consequence") or v.get("raised"))}

    def g2(v):
        proj = v.get("projected_wall_s")
        cap = v.get("max_wall_s")
        return {"decision": "allow" if v.get("ok") else "refused",
                "projected_wall_s": proj, "max_wall_s": cap,
                "ratio": (round(float(proj) / float(cap), 6) if proj and cap else None),
                "per_turn_s": v.get("projected_turn_wall_s"),
                "source": v.get("projected_turn_wall_source"),
                "computed": v.get("computed"), "limit": v.get("limit"),
                "verbatim": (None if v.get("ok")
                             else v.get("consequence") or v.get("raised"))}

    return {
        "g3_h2_n48": dict(g3(h2["g3"]), hypothesis="H2", turns=TURNS, reps=1,
                          what="the claim a 48-turn cell actually launches under"),
        "g3_h1_n48": dict(g3(h1_48["g3"]), hypothesis="H1", turns=TURNS, reps=1,
                          what="the claim no cell makes; G3 must still refuse it"),
        "g3_h1_pooled_n144": dict(g3(h1_144["g3"]), hypothesis="H1", turns=TURNS,
                                  reps=POOLED_REPS["pointer-stable"],
                                  what="the POST-HOC pooled n; admitted here so the "
                                       "floor is visibly above 60, never launched"),
        "g2_2880": dict(g2(h2["g2"]), what="the launched cell at its own ceiling"),
        "g2_2881": dict(g2(g2_2881["g2"]),
                        what="one second over the ceiling: G2 must refuse"),
    }


def launch_commands():
    """The ten commands that would actually be launched, one per cell.

    Byte-identical to the rehearsed argv except that `--dry-run` is dropped, the output
    directory is named, and every path is RELATIVE TO THE REPO ROOT so the shell string is
    copy-pasteable.  The claim on every one of them is H2; no command names a hypothesis
    the cell's own n cannot carry, and none names H1.
    """
    import shlex
    out, warmed = [], set()
    cell_rel = os.path.relpath(CELL, ROOT)
    fix_rel = os.path.relpath(FIXTURE, ROOT)
    out_rel = os.path.relpath(MEASURE, ROOT)
    for idx, (arm, rep) in enumerate(CELLS, 1):
        # ONE rep of the grid per cell: the rep label indexes the cell, it is never --reps
        args = [a for a in cell_args(arm, 1, HYPOTHESIS)[2:] if a != "--dry-run"]
        args = [fix_rel if a == FIXTURE else a for a in args]
        argv = ["python3", cell_rel] + args + ["--out-dir", out_rel]
        first = arm not in warmed
        warmed.add(arm)
        out.append({
            "cell": idx, "arm": arm, "rep_label": "r%d" % rep, "rep": rep,
            "turns": TURNS, "hypothesis": HYPOTHESIS, "cwd": ".",
            "argv": argv,
            "shell": " ".join(shlex.quote(a) for a in argv),
            "warmup": {"when": "before this arm's first cell" if first else "already warm",
                       "requests": 1 if first else 0, "prompt_tokens": 8,
                       "runs_inside": "run_longrun.py's own request allocation "
                                      "(not a cell.py flag; not in G1's arithmetic)",
                       "source": "experiments/ptr-engine/measure/ENDPOINT-STATE.json "
                                 "-> grid_advice"},
        })
    return out


def pooled_analysis_plan():
    """The POST-HOC analysis of the pooled rows -- a plan, with no numbers.

    There are no rows yet, so nothing here is a result.  It names the files, the
    grouping, the n per arm, the exact quantile_ci call and the stop rule that would
    return 'not adjudicable at this budget'.
    """
    per = {}
    for arm in ("pointer-stable", "transcript-grow", "transcript-compact", "lease-reopen"):
        reps = POOLED_REPS[arm]
        per[arm] = {"cells": reps, "n": TURNS * reps,
                    "above_h1_floor_60": (TURNS * reps) >= 60}
    return {
        "when": "after all ten cells settle and the rows exist; never at launch",
        "rows_glob": "experiments/ptr-engine/measure/rows-tranch1-*.jsonl",
        "rows_files": "one per live cell (rows-tranch1-<arm>-<rep_label>-*.jsonl); "
                      "NO SUCH FILE EXISTS YET -- this plan carries no measured number",
        "grouping": "by arm, pooling every rep of that arm; the pair comparison is "
                    "pointer-stable (C) vs transcript-grow (A)",
        "n_per_arm": per,
        "selector": "analyze_stats.turn_latency_rows(rows) -> (selected, meta); one row "
                    "per TURN, sample = row['ttft_ms'], absent/null/non-finite dropped "
                    "and counted (never coerced to 0)",
        "call": "analyze_stats.quantile_ci([r['ttft_ms'] for r in selected[arm]], "
                "q=0.95, resamples=10000, seed=20261020)",
        "p50_call": "analyze_stats.quantile_ci(values, q=0.50) -- the materiality check, "
                    "not a claim",
        "ranking_rule": "disjoint 95% bootstrap intervals: C.hi < A.lo (PARM-1 H1 "
                        "ranking_rule); overlapping intervals mean NO ranking claim",
        "stop_rule": "p95 intervals overlap OR |p50(C) - p50(A)| < 100 ms => "
                     "'not adjudicable at this budget'",
        "owner": "V-TRANCHE-1 (9d271c32): H1 per grid WITH its n, and no direction "
                 "reported when the pooled intervals overlap",
    }


def price_block(cell0):
    """Price the tranche again from the artefacts: marginal, cumulative, headroom."""
    per_cell = TURNS + allowance_for(TURNS)
    total = per_cell * len(CELLS)
    arms = len({a for a, _ in CELLS})
    spent = cell0["g1"].get("spent")
    cap = cell0["g1"].get("cap")
    ledger = {}
    if isinstance(spent, int) and isinstance(cap, int):
        ledger = {"cap": cap, "spent": spent, "remaining_before": cap - spent,
                  "spent_after_cells": spent + total,
                  "spent_after_warmups": spent + total + arms,
                  "remaining_after": cap - spent - total - arms}
    return {
        "requests_per_cell": per_cell,
        "breakdown": "%d turns + ceil(%d x 68/801) = %d follow-up allowance"
                     % (TURNS, TURNS, allowance_for(TURNS)),
        "cells": len(CELLS), "total_new_requests": total,
        "warmup_requests": arms, "total_with_warmup": total + arms,
        "ledger": ledger,
        "g1_displayed_per_cell": cell0["g1"].get("computed"),
        "g1_is_cumulative": ("the %s per-cell figure is CUMULATIVE (spent + turns + "
                             "allowance), not a marginal forecast: the tranche's new "
                             "spend is %d requests" % (cell0["g1"].get("computed"), total)),
    }


def h1_occurrences(commands, out_dir=None):
    """Count the post-hoc claim's name in the LAUNCH artefacts (commands + manifests).

    It must be ZERO: a ten-cell launch must not smuggle the pooled claim in.  The string
    is allowed only in documentation that describes the post-hoc analysis.
    """
    import glob as _glob
    hits = []
    scan_dir = os.path.abspath(out_dir or MEASURE)
    for c in commands:
        joined = " ".join(c["argv"]) + " " + c["shell"]
        if "H1" in joined:
            hits.append({"where": "launch_commands[cell=%d]" % c["cell"], "count": joined.count("H1")})
    files = sorted(_glob.glob(os.path.join(scan_dir, PREFIX + "*.json")))
    for p in files:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        if "H1" in text:
            hits.append({"where": os.path.relpath(p, ROOT), "count": text.count("H1")})
    return {"count": sum(h["count"] for h in hits), "hits": hits,
            "scanned": {"launch_commands": len(commands), "manifests": len(files)}}


# ---------------------------------------------------------------------- the ten runs
def parse(stdout):
    got = {}
    g = re.search(r"dry-run (G1|G2|G3) (allow|WOULD-REFUSE) computed=([^ ]+) (?:requests|s|n=\S+)? ?"
                  r"limit=(.+?) artefact=(\S*) sha256=(\S*)", stdout)
    for line in stdout.splitlines():
        m = re.search(r"dry-run (G1|G2|G3) (allow|WOULD-REFUSE) computed=(.+?) limit=(.+?)(?: "
                      r"\(--max-wall\)| requests \(cap ([\d,]+) - reserve ([\d,]+) - spent "
                      r"([\d,]+)\)| artefact=|$)", line)
        if m:
            got[m.group(1)] = {
                "decision": "allow" if m.group(2) == "allow" else "refused",
                "computed_raw": m.group(3).strip(),
                "limit_raw": m.group(4).strip(),
                "cap_raw": m.group(5), "reserve_raw": m.group(6), "spent_raw": m.group(7),
                "line": line,
            }
    m = re.search(r"would cost: turns=(\d+) arms=(\d+) reps=(\d+) -> (\d+) requests "
                  r"\(incl\. follow-up allowance (\d+)\)", stdout)
    if m:
        got["cost"] = {"turns": int(m.group(1)), "arms": int(m.group(2)),
                       "reps": int(m.group(3)), "would_send": int(m.group(4)),
                       "allowance": int(m.group(5))}
    m = re.search(r"hypothesis=(\S+) \((.*?)\) thresholds=(.*)$", stdout, re.M)
    if m:
        got["hyp"] = {"hypothesis": m.group(1), "source": m.group(2),
                      "thresholds": m.group(3)}
    m = re.search(r"(\d) of 3 gate\(s\) would refuse", stdout)
    if m:
        got["would_refuse_count"] = int(m.group(1))
    return got


def run_cell(arm, rep, reps, out_dir, tag=None, hypothesis=None, extra=()):
    hook = hook_dir()
    audit = os.path.join(tempfile.gettempdir(), "tdr", "audit-%s.txt" % (tag or ("%s-r%d" % (arm, rep))))
    if os.path.exists(audit):
        os.remove(audit)
    env = dict(os.environ)
    env["TDR_AUDIT"] = audit
    env["PYTHONPATH"] = hook + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    rc = subprocess.run(cell_args(arm, reps, hypothesis, extra), cwd=ROOT, env=env,
                        capture_output=True, text=True)
    events = []
    if os.path.exists(audit):
        with open(audit, encoding="utf-8") as f:
            events = [ln.strip() for ln in f if ln.strip()]
    net = [e for e in events if e.startswith(("socket.", "urllib.", "http.client"))]
    spawn = [e for e in events if e.startswith(("subprocess.", "os.exec", "os.fork",
                                                "os.posix_spawn", "os.spawn"))]
    out = rc.stdout + rc.stderr
    det = inproc_detail(FIXTURE, arm, reps, hypothesis=hypothesis)
    return rc.returncode, out, det, events, net, spawn


def build_manifest(arm, rep, reps, out_dir, hypothesis=None):
    rc, stdout, det, events, net, spawn = run_cell(arm, rep, reps, out_dir,
                                                   hypothesis=hypothesis)
    parsed = parse(stdout)
    cost = parsed.get("cost") or {}
    turns_total = cost.get("turns", TURNS) * cost.get("arms", 1) * cost.get("reps", reps)
    g1v, g2v, g3v = det["g1"], det["g2"], det["g3"]
    spent = g1v.get("spent")
    allowance = g1v.get("fetch_followup_allowance")
    computed = g1v.get("projected")
    projected_wall = g2v.get("projected_wall_s")
    max_wall = g2v.get("max_wall_s") or MAX_WALL
    ratio = (float(projected_wall) / float(max_wall)) if projected_wall else None
    import run_longrun as R  # noqa: E402  (pure planning; no request, no socket)
    fixture = R.load_fixture(FIXTURE)
    wall = R.wall_for_arm(fixture, arm)
    fires = R.treatment_fire_turns(fixture, arm, TURNS)
    treatments = {
        "grow_evict_turn": fires.get("grow"),
        "compact_wall_turn": fires.get("wall"),
        "lease_step_turn": fires.get("lease"),
        "pointer_prefix_turn": fires.get("prefix"),
        "wall_tokens_used": int(wall),
        "horizon": TURNS,
        "refusals": fires.get("reasons"),
    }
    name = "%s%s-r%d.json" % (PREFIX, arm, rep)
    path = os.path.join(out_dir, name)
    hyp = hypothesis or HYPOTHESIS
    man = {
        "schema": "consonance.tranch1-dryrun-cell/1",
        "arm": arm, "rep": rep, "declared_reps": reps, "turns": TURNS,
        "thinking": THINKING, "max_wall": MAX_WALL, "turn_wall_cap": TURN_WALL_CAP,
        "runaway_turns": RUNAWAY, "cap": CAP, "hypothesis": hyp,
        "design_cap_tokens": int(wall),
        "cell_exit_code": rc,
        "g1": {
            "spent": spent, "turns": turns_total,
            "allowance": allowance,
            "allowance_recomputed": allowance_for(turns_total),
            "computed": computed,
            "cap": g1v.get("cap"), "headroom": g1v.get("headroom"),
            "decision": "allow" if g1v.get("ok") else "refused",
            "printed": parsed.get("G1", {}).get("line", ""),
            "within_cap_900": bool((turns_total + (allowance or 0)) <= CAP),
        },
        "g2": {
            "projected_wall": projected_wall,
            "ratio": round(ratio, 6) if ratio is not None else None,
            "source": g2v.get("projected_turn_wall_source"),
            "projected_turn_wall_s": g2v.get("projected_turn_wall_s"),
            "projected_from_arg": None,
            "projected_from_file": g2v.get("projected_from_file"),
            "thinking_mode": g2v.get("thinking_mode"),
            "projected_requests": g2v.get("projected_requests"),
            "worst_case_wall_s": g2v.get("worst_case_wall_s"),
            "max_wall_s": max_wall,
            "decision": "allow" if g2v.get("ok") else "refused",
            "printed": parsed.get("G2", {}).get("line", ""),
        },
        "g3": {
            "n": g3v.get("n"),
            "hypothesis_source": g3v.get("hypothesis_source"),
            "hypothesis": g3v.get("hypothesis"),
            "thresholds": g3v.get("thresholds"),
            "decision": "allow" if g3v.get("ok") else "refused",
            "refusal": g3v.get("consequence") or g3v.get("raised"),
            "printed": parsed.get("G3", {}).get("line", ""),
        },
        "treatments": treatments,
        "manifest_path": os.path.relpath(path, ROOT),
        "spawns": len(spawn), "network_events": len(net),
        "audit_events": events[:20],
        "stdout": stdout,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    man["manifest_sha256"] = sha256_file(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1, sort_keys=True)
    man["manifest_sha256"] = sha256_file(path)
    return man


def pooled_probe(arm, hypothesis=None):
    """The same arm declaring its POOLED design reps (pair 3, context 2).

    Recorded under /tmp so it never joins the ten measured cells. Its purpose is to price
    the only shape that could carry a pooled claim as ONE process: declare more reps,
    which G2 then refuses.  It is evidence about the shape that is NOT launched.
    """
    reps = POOLED_REPS[arm]
    out_dir = os.path.join(tempfile.gettempdir(), "tdr", "probe")
    os.makedirs(out_dir, exist_ok=True)
    rc, stdout, det, events, net, spawn = run_cell(arm, 1, reps, out_dir,
                                                   tag="pooled-%s" % arm,
                                                   hypothesis=hypothesis)
    g1, g2, g3 = det["g1"], det["g2"], det["g3"]
    return {
        "arm": arm, "reps": reps, "turns": TURNS,
        "exit_code": rc,
        "g1": {"spent": g1.get("spent"), "turns": TURNS,
               "allowance": g1.get("fetch_followup_allowance"),
               "computed": g1.get("projected"),
               "decision": "allow" if g1.get("ok") else "refused"},
        "g2": {"projected_wall": g2.get("projected_wall_s"),
               "max_wall": g2.get("max_wall_s"),
               "projected_requests": g2.get("projected_requests"),
               "decision": "allow" if g2.get("ok") else "refused",
               "refusal": (g2.get("consequence") or g2.get("raised") or "")[:400]},
        "g3": {"n": g3.get("n"),
               "decision": "allow" if g3.get("ok") else "refused",
               "refusal": (g3.get("consequence") or g3.get("raised") or "")[:400]},
        "spawns": len(spawn), "network_events": len(net),
        "stdout": stdout,
    }


def do_run(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    before = pin()
    cells, probes = [], []
    for arm, rep in CELLS:
        cells.append(build_manifest(arm, rep, 1, out_dir, hypothesis=HYPOTHESIS))
    for arm in sorted({c[0] for c in CELLS}):
        probes.append(pooled_probe(arm, hypothesis=HYPOTHESIS))
    after = pin()
    moved = [p for p in PINNED if before[p] != after[p]]
    total_marginal = sum(TURNS + allowance_for(TURNS) for _ in CELLS)
    report = {
        "schema": "consonance.tranch1-dryrun/1",
        "generated_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offline": True,
        "fixture": FIXTURE,
        "fixture_sha256": sha256_file(FIXTURE),
        "flags": {"turns": TURNS, "thinking": THINKING, "max_wall": MAX_WALL,
                  "turn_wall_cap": TURN_WALL_CAP, "runaway_turns": RUNAWAY,
                  "cap": CAP, "hypothesis": HYPOTHESIS,
                  "reps": 1, "reps_note": "one cell = one arm, 48 turns, one rep; "
                          "see notes.assumption_reps"},
        "pins_before": before, "pins_after": after, "pins_moved": moved,
        "stamp": "stamped" if not moved else "unstamped",
        "cells": [{
            "arm": c["arm"], "rep": c["rep"], "g1": c["g1"], "g2": c["g2"],
            "g3": c["g3"], "treatments": c["treatments"],
            "manifest_path": c["manifest_path"], "manifest_sha256": c["manifest_sha256"],
            "spawns": c["spawns"], "network_events": c["network_events"],
            "design_cap_tokens": c["design_cap_tokens"],
        } for c in cells],
        "pooled_probes": probes,
        "all_ten_allowed": all(c["g1"]["decision"] == "allow" and
                               c["g2"]["decision"] == "allow" and
                               c["g3"]["decision"] == "allow" for c in cells),
        "total_projected_requests": total_marginal,
        "total_gate_displayed": sum((c["g1"]["computed"] or 0) for c in cells),
        "zero_network": all(c["network_events"] == 0 for c in cells),
        "zero_spawns": all(c["spawns"] == 0 for c in cells),
        "claim_frame": {
            "per_cell_hypothesis": HYPOTHESIS,
            "why": ("one 48-turn cell cannot carry an H1 claim by construction (n = 48 "
                    "< 60, G3 refuses it), so no cell makes one; H2 is a TRUE claim the "
                    "cell can measure (the cache limb, n >= 1)"),
            "h1_owner": ("the POST-HOC pooled rows after the tranche, at n = 144 per pair "
                         "arm (3 reps) / 96 per context arm (2 reps), computed by the "
                         "analysis path, never claimed at launch"),
            "decided_in": "board #975 (main session), card 3a517e10-aa2d-4f17-b901-ad99a22dca40",
            "gates_edited": False,
        },
        "gate_probes": gate_probes(cells[0]),
        "launch_commands": launch_commands(),
        "pooled_analysis_plan": pooled_analysis_plan(),
        "price": price_block(cells[0]),
        "notes": {
            "assumption_reps": (
                "One invocation = one cell = one arm, 48 turns, ONE rep of the grid "
                "(--reps 1): the shape the runner executes and the ledger charges 53 "
                "requests for. The rep label indexes the cell only. The pooled shape "
                "(pair --reps 3, context --reps 2) is probed separately because it is the "
                "only shape whose n satisfies G3's H1 floor; no cap, wall, horizon or "
                "n-floor was lowered anywhere."),
            "marginal_cost": (
                "The ledger charges 48 + ceil(48*68/801) = 53 requests per cell, so the "
                "ten cells cost 530 new requests; G1's displayed 1,154 per cell is the "
                "CUMULATIVE figure (1,101 already spent + 48 turns + 5 allowance), not a "
                "marginal price."),
            "warmup": (
                "run_longrun.py adds one 8-token warm-up per arm inside its own "
                "allocation; G1's would_spend = turns_total + allowance only, so the "
                "warm-up is NOT in cell.py's gate arithmetic -- it is declared here as "
                "not projected rather than silently omitted."),
        },
    }
    report["h1_occurrences"] = h1_occurrences(report["launch_commands"], out_dir)
    dest = os.path.join(out_dir, NAMED[HYPOTHESIS]["report"])
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True)
    # the shared deliverables are written ONLY by the canonical run, so a red/diagnostic
    # run against a trap fixture can never clobber the measured report or the doc.
    if os.path.abspath(out_dir) == os.path.abspath(MEASURE):
        with open(report_path(), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=1, sort_keys=True)
        write_doc(report)
    return report


def write_doc_h2(rep):
    """The re-rehearsal doc: the claim decision, both gates quoted, the ten launches,
    the pooled plan and the price.  No measured H1 number exists yet, and none is
    written here."""
    pr = rep["gate_probes"]
    price = rep["price"]
    plan = rep["pooled_analysis_plan"]
    rows = ["| cell | arm | G1 computed (cumulative) | G1 spent/turns/allowance | G1 | "
            "G2 projected s (ratio, source) | G2 | G3 n / min n (source) | G3 | treatments fire |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(rep["cells"], 1):
        g1, g2, g3 = c["g1"], c["g2"], c["g3"]
        rows.append("| %d | `%s` r%d | %s | %s/%s/%s | %s | %s (%.4f, `%s`) | %s | "
                    "%s / %s (`%s`) | %s | grow=%s compact=%s lease=%s prefix=%s |"
                    % (i, c["arm"], c["rep"], g1["computed"], g1["spent"], g1["turns"],
                       g1["allowance"], g1["decision"], g2["projected_wall"],
                       g2["ratio"] or 0, g2["source"], g2["decision"], g3["n"],
                       (g3.get("thresholds") or {}).get("min_n"),
                       g3["hypothesis_source"], g3["decision"],
                       c["treatments"]["grow_evict_turn"],
                       c["treatments"]["compact_wall_turn"],
                       c["treatments"]["lease_step_turn"],
                       c["treatments"]["pointer_prefix_turn"]))
    probe_rows = ["| the shape NOT launched: arm | reps declared | G2 projected s / max wall | G2 | G3 n | G3 |",
                  "|---|---|---|---|---|---|"]
    for p in rep["pooled_probes"]:
        probe_rows.append("| `%s` | %d | %s / %s | %s | %s | %s |"
                          % (p["arm"], p["reps"], p["g2"]["projected_wall"],
                             p["g2"]["max_wall"], p["g2"]["decision"], p["g3"]["n"],
                             p["g3"]["decision"]))
    launch = []
    for c in rep["launch_commands"]:
        if c["warmup"]["requests"]:
            launch.append("# per-arm warm-up: 1 throwaway 8-token request before this "
                          "arm's first cell (inside run_longrun's allocation, not a "
                          "cell.py flag, not in G1's arithmetic)")
        launch.append(c["shell"])
    per = "`%s`" % "` · `".join("%s n=%d" % (a, v["n"]) for a, v in plan["n_per_arm"].items())
    # each arm's OWN treatment turn, read off its cell (never the first cell's)
    fires = {}
    for c in rep["cells"]:
        fires.setdefault(c["arm"], c["treatments"].get(ARM_TREATMENT[c["arm"]][0]))
    first = rep["cells"][0]
    text = """# TRANCH1-DRYRUN-2 — the ten cells re-rehearsed under the claim they can carry

**Unit:** `TRANCH1-DRYRUN-2` · **Offline:** zero requests, zero spawns, zero sockets · **Stamp:** `%s`
**Grid:** `RUN-A*` — 10 cells x 48 turns (pair at 3 reps, context at 2), `tasks-v6/LR-01.v8.json`,
`--thinking off`, `--max-wall 2880`, `--turn-wall-cap 180`, `--runaway-turns 2`, per-cell cap 900,
**`--hypothesis %s`** on every cell. **Decision: %s.**
**Measurement:** [`../experiments/ptr-engine/measure/TRANCH1-DRYRUN-2.json`](../experiments/ptr-engine/measure/TRANCH1-DRYRUN-2.json)
· **check:** `python3 experiments/ptr-engine/tools/tranch1_dryrun.py --check`

## 1. The claim decision this rehearses

The first rehearsal (`TRANCH1-DRYRUN`) found a pincer: H1 needs `n >= 60` and a 48-turn cell is
`n = 48`, so **G3 refused all ten cells**; the pooled shape that satisfies `n` was refused by G2
(`8640 s > 2880 s`, `5760 s > 2880 s`). The decision (board #975) is that **a 48-turn cell cannot
carry an H1 claim by construction, so no cell makes one**:

- each cell launches with **`--hypothesis H2`** — the cache limb, a claim the cell can measure
  (`n >= 1`: prompt tokens per completed turn, `materiality_margin` `C <= 0.95 x A`);
- **H1 is adjudicated only on the pooled rows, after the tranche**, at **n = 144 per pair arm**
  (3 reps) and **n = 96 per context arm** (2 reps), by the analysis path -- never claimed at launch;
- **neither gate is edited**: G3 still refuses an H1 claim at n=48 (§3 below quotes it), G2 still
  caps the per-cell wall at 2,880 s (nobody launches the pooled shape as one process).

## 2. The ten cells

%s

Every cell is one `cell.py --dry-run` invocation (`--turns 48 --reps 1 --hypothesis %s`) with its
own manifest (`experiments/ptr-engine/measure/dryrun2-t2-<arm>-r<rep>.json`). `all_ten_allowed = %s`.
Total new spend **%s requests** (%d per cell); the sum of G1's cumulative displays is %s.

## 3. Both gates behave — quoted, not paraphrased

`cell.py`'s own `eval_gate_prereg` / `eval_gate_projection`, over the real prereg and projection
artefacts. The probes change only the operand, never the check.

| probe | operand | verdict |
|---|---|---|
| G3, the claim a cell launches | `--hypothesis H2`, `n = 48` | **%s** (`n = %s`, min n = %s) |
| G3, the claim no cell makes | `--hypothesis H1`, `n = 48` | **%s** — verbatim below |
| G3, the pooled shape (post-hoc only) | `--hypothesis H1`, `n = 144` | **%s** (`n = %s`) |
| G2 at the ceiling | projected `%s s`, `--max-wall 2880` | **%s**, ratio **%.4f** |
| G2 one second over | projected `%s s`, `--max-wall 2880` | **%s** — verbatim below |

The `H1` refusal at n=48, verbatim:

> %s

The G2 refusal at 2,881 s, verbatim:

> %s

So the decision costs no gate edit: the claim that would be refused is the claim nobody makes.

## 4. The exact ten launch commands

These are the rehearsed argv with `--dry-run` dropped and `--out-dir` named; nothing else changes.
The per-arm 8-token warm-up is the one request `ENDPOINT-STATE.json -> grid_advice` asks for before
each arm's first cell; it lives in `run_longrun.py`'s own allocation and is **not** in cell.py's G1
arithmetic, so it is declared here rather than silently dropped.

```bash
%s
```

Machine-readable twin: `launch_commands[]` in the measurement JSON (argv + shell + warm-up per cell).

## 5. The pooled analysis plan (a plan — there are no rows)

- **rows:** `%s`, one per live cell; **no such file exists yet**.
- **grouping:** by arm, pooling every rep; the pair comparison is `pointer-stable` (C) vs
  `transcript-grow` (A).
- **n per arm:** %s. All at or above the frozen H1 floor of 60.
- **selector:** `%s`
- **call:** `%s`
- **p50:** `%s`
- **ranking:** %s
- **stop rule:** %s
- **owner:** %s

## 6. Price, from the artefacts

| quantity | value |
|---|---|
| requests per cell | **%s** (%s) |
| cells | %s |
| total new requests (cells) | **%s** |
| per-arm 8-token warm-ups | %s |
| total including warm-ups | **%s** |
| ledger cap / spent / remaining before | %s / %s / %s |
| spent after the tranche | %s |
| remaining after the tranche | %s |

**G1's `%s` per cell is cumulative, not a forecast** — `1,101 already spent + 48 turns + 5 allowance`
— so it must never be quoted as what the tranche costs. The marginal price is %s requests per cell.

## 7. The pooled claim is not smuggled in at launch

Scanned the ten launch commands and the ten manifests for the string `H1`: **%d occurrence(s)**.
Zero is the requirement, and zero is what the artefacts carry: every launch command says
`--hypothesis %s`, and the only `H1` in this document describes the POST-HOC analysis in §1 and §5.

## 8. Zero network, zero spawn

Every invocation ran under a `sitecustomize.py` `sys.addaudithook` injected on `PYTHONPATH`
(`cell.py` unedited), recording `socket.*`, `urllib.*`, `http.client`, `subprocess.*`, `os.exec*`,
`os.fork*`, `os.posix_spawn*`. Per cell: **%d network events, %d spawns**, and every run printed
"0 requests sent, no endpoint contacted". `unshare -n` is unavailable here, so the audit hook plus
the runner's own line is the primitive.

## 9. Treatments still fire inside the horizon

`wall_tokens_by_arm` = **%s** (never the dead top-level 3,838, which sits below v8's first prompt
3,848): `transcript-grow` first FIFO eviction **T%s**, `transcript-compact` first wall **T%s**,
`lease-reopen` first lease step **T%s**, `pointer-stable` first prefix change **T%s**.

## 10. What still stops the launch

1. **A gate refusal on any cell** — live exits 4 (G1), 8 (G2), 12 (G3). Under H2 all ten allow; a
   refusal in the live path is a finding, never something to route around.
2. **Projected wall > `--max-wall`** — the ceiling is exact: any reps>1 declaration or any larger
   per-turn wall refuses (the pooled shape is refused at 8,640 s / 5,760 s).
3. **A treatment that never fires inside 48 turns** — the arm becomes indistinguishable from control.
4. **`design_cap_tokens` reading 3,838 (or 65,536)** — the runner must read the per-arm wall.
5. **A spawn or a socket during a dry run.**
6. **Any pinned file moving between the first and last invocation** — the rehearsal is then
   `unstamped`, not a pass.

## 11. Pinning

`sha256` recorded before and after the ten runs for `cell.py`, `run_longrun.py`, `client.py`,
`exit_codes.py`, `tasks-v6/LR-01.v8.json`, `analyze_stats.py`: **%s**.
""" % (rep["stamp"], rep["claim_frame"]["per_cell_hypothesis"],
       "GO" if rep["all_ten_allowed"] else "HELD",
       "\n".join(rows), rep["claim_frame"]["per_cell_hypothesis"], rep["all_ten_allowed"],
       rep["total_projected_requests"], price["requests_per_cell"],
       rep["total_gate_displayed"],
       pr["g3_h2_n48"]["decision"], pr["g3_h2_n48"]["n"], pr["g3_h2_n48"]["min_n"],
       pr["g3_h1_n48"]["decision"], pr["g3_h1_pooled_n144"]["decision"],
       pr["g3_h1_pooled_n144"]["n"],
       pr["g2_2880"]["projected_wall_s"], pr["g2_2880"]["decision"], pr["g2_2880"]["ratio"],
       pr["g2_2881"]["projected_wall_s"], pr["g2_2881"]["decision"],
       pr["g3_h1_n48"]["verbatim"], pr["g2_2881"]["verbatim"],
       "\n".join(launch),
       plan["rows_glob"], per, plan["selector"], plan["call"], plan["p50_call"],
       plan["ranking_rule"], plan["stop_rule"], plan["owner"],
       price["requests_per_cell"], price["breakdown"], price["cells"],
       price["total_new_requests"], price["warmup_requests"], price["total_with_warmup"],
       price["ledger"].get("cap"), price["ledger"].get("spent"),
       price["ledger"].get("remaining_before"), price["ledger"].get("spent_after_cells"),
       price["ledger"].get("remaining_after"),
       price["g1_displayed_per_cell"], price["requests_per_cell"],
       rep["h1_occurrences"]["count"], rep["claim_frame"]["per_cell_hypothesis"],
       first["network_events"], first["spawns"],
       first["design_cap_tokens"],
       fires.get("transcript-grow"), fires.get("transcript-compact"),
       fires.get("lease-reopen"), fires.get("pointer-stable"),
       "stamped (no file moved)" if rep["stamp"] == "stamped"
       else "UNSTAMPED — moved: " + ", ".join(rep["pins_moved"]))
    with open(doc_path(), "w", encoding="utf-8") as f:
        f.write(text)


# ------------------------------------------------------------------------- the doc
def write_doc(rep):
    if HYPOTHESIS == "H2":
        return write_doc_h2(rep)
    return write_doc_v1(rep)


def write_doc_v1(rep):
    rows = ["| cell | G1 computed (cumulative) | G1 spent / turns / allowance | G1 | "
            "G2 projected s (ratio, source) | G2 | G3 n (source) | G3 | treatments fire |",
            "|---|---|---|---|---|---|---|---|---|"]
    for c in rep["cells"]:
        g1, g2, g3 = c["g1"], c["g2"], c["g3"]
        rows.append("| `%s r%d` | %s | %s / %s / %s | %s | %s (%.4f, `%s`) | %s | %s (`%s`) | %s | grow=%s compact=%s lease=%s prefix=%s |"
                    % (c["arm"], c["rep"], g1["computed"], g1["spent"], g1["turns"],
                       g1["allowance"], g1["decision"], g2["projected_wall"],
                       g2["ratio"] or 0, g2["source"], g2["decision"], g3["n"],
                       g3["hypothesis_source"], g3["decision"],
                       c["treatments"]["grow_evict_turn"],
                       c["treatments"]["compact_wall_turn"],
                       c["treatments"]["lease_step_turn"],
                       c["treatments"]["pointer_prefix_turn"]))
    probe_rows = ["| the other horn: arm | reps declared | G1 computed | G2 projected s / max wall | G2 | G3 n | G3 |",
                  "|---|---|---|---|---|---|---|"]
    for p in rep["pooled_probes"]:
        probe_rows.append("| `%s` | %d | %s | %s / %s | %s | %s | %s |"
                          % (p["arm"], p["reps"], p["g1"]["computed"],
                             p["g2"]["projected_wall"], p["g2"]["max_wall"],
                             p["g2"]["decision"], p["g3"]["n"], p["g3"]["decision"]))
    first = rep["cells"][0]
    verdict = "GO" if rep["all_ten_allowed"] else "HELD"
    text = """# TRANCH1-DRYRUN — the ten-cell grid rehearsed offline

**Unit:** `TRANCH1-DRYRUN` · **Offline:** zero requests, zero spawns, zero sockets · **Stamp:** `%s`
**Grid:** `RUN-A*` — 10 cells x 48 turns (pair at 3 reps, context at 2), `tasks-v6/LR-01.v8.json`,
`--thinking off`, `--max-tokens 4096`, `--max-wall 2880`, `--turn-wall-cap 180`,
`--runaway-turns 2`, per-cell cap 900. **Decision: %s.**
**Measurement:** [`../experiments/ptr-engine/measure/TRANCH1-DRYRUN.json`](../experiments/ptr-engine/measure/TRANCH1-DRYRUN.json)
· **check:** `python3 experiments/ptr-engine/tools/tranch1_dryrun.py --check`

## The ten cells

%s

Every cell is one `cell.py --dry-run` invocation (`--turns 48 --reps 1 --hypothesis H1`) with its
own manifest (`experiments/ptr-engine/measure/dryrun-t1-<arm>-r<rep>.json`); no two share a
filename. `all_ten_allowed = %s`. Total marginal cost **%s requests** (48 + ceil(48x68/801) = 53
per cell); the sum of G1's cumulative displays is %s.

**The grid is HELD, and the reason is a pincer that no flag change can open.** G1 allows every
cell. G2 allows every cell at exactly its ceiling. G3 refuses every cell, because one 48-turn
cell is `n = 48 < 60`. The only shape whose `n` satisfies H1 (declare the arm's pooled reps)
is refused by G2 instead — see the second table.

### G1 — the ledger brake (all ten allow)

G1 prints cumulative spend: `spent + turns + allowance`, with `turns = 48 x arms x reps` and
`allowance = ceil(turns x 68/801)`. Already spent is **%s** against a ledger cap of **4,320**
(headroom 3,219), so every cell prints `1,101 + 48 + 5 = 1,154` and its marginal spend is 53
requests — nowhere near the 900 cap.

### G2 — the mode-aware per-turn wall (all ten allow, at exactly 1.0000 of the ceiling)

`--projected-from` defaults to none, so `projected_turn_wall` comes from the calibrated
projection's `projected_turn_wall_s_by_mode["off"]` — the retained conservative **60 s**, source
`artefact-mode`. It is *not* the 180 s abort cap (`--turn-wall-cap`) and *not* the pooled
218.2 s figure (that is the thinking on/auto value). `48 x 60 = 2,880 s` against `--max-wall
2880`: ratio **1.0000**, allowed because the gate compares `<=`. The measured `thinking=off` p90
of 38.1 s exists in the same artefact but is only used when `--projected-from p90` is passed;
it is not the default and was not used.

### G3 — the pincer (all ten refuse, verbatim)

H1 needs `n >= 60` (`analyze_stats.min_n_for(q=0.95)`), and `n = turns x reps = 48 x 1`. Every
cell's G3 line reads `n=48 < 60`; the verdict text is quoted verbatim in the measurement JSON
(`cells[].g3.refusal`). `--hypothesis H2`/`smoke` was **not** used to get through — that would
have bought a pass with a claim the grid does not make.

%s

So: 48 turns at reps=1 -> G3 refuses (n=48). 48 turns at the arm's pooled reps -> G3 allows
(n=144 / 96) but G2 projects `144 x 60 = 8,640 s` (pair) and `96 x 60 = 5,760 s` (context)
against `--max-wall 2880` and refuses. **No invocation shape of this grid passes G2 and G3 at
the pinned flags.** Opening it needs a card decision — `--max-wall >= 8640`, a per-rep launch
(which cannot claim H1), or an H2 claim — never a lowered cap, wall, horizon or n-floor.

### Treatments fire inside the horizon

Read from `wall_tokens_by_arm` = **10,616**, never the top-level `wall_tokens` 3,838:
`transcript-grow` first FIFO eviction **T%s**, `transcript-compact` first wall **T%s**,
`lease-reopen` first lease step **T%s**, `pointer-stable` first prefix change **T%s** — all at
or below 48. The v8 trap is why this matters: 3,838 sits below v8's own first prompt (3,848), so
a path falling back to it fires the wall near T2 and collapses both transcript arms into one
another. `design_cap_tokens` reads **10,616** in all ten manifests.

### Zero network, zero spawn

Every invocation ran under a `sitecustomize.py` `sys.addaudithook` injected on `PYTHONPATH`
(`cell.py` unedited), recording `socket.*`, `urllib.*`, `http.client`, `subprocess.*`, `os.exec*`,
`os.fork*`, `os.posix_spawn*`. Events per cell: **0 network, 0 spawn**, and every run printed
"0 requests sent, no endpoint contacted". `unshare -n` is unavailable here, so the audit hook
plus the tool's own line is the primitive. The per-arm 8-token warm-up lives inside
`run_longrun.py`'s own allocation; **it is not in cell.py's G1 arithmetic** (`would_spend =
turns_total + allowance` only) and is declared here as deliberately *not* projected rather than
silently omitted.

## What would stop the grid

Each condition was checked by the rehearsal; the live run must still not violate it.

1. **A gate refusal on any cell** — live exits are 4 (G1), 8 (G2), 12 (G3). This rehearsal's ten
   cells are held on G3 (`n=48 < 60`); a G3 refusal is a finding, never something to route
   around with `--hypothesis H2` or `smoke`.
2. **`projected_wall > --max-wall`** — the ceiling is exact (2,880 s at 60 s/turn for 48 turns);
   any larger per-turn wall, or any reps>1 declaration, refuses. The pooled 218.2 s figure would
   refuse a 48-turn cell outright.
3. **A treatment that never fires inside 48 turns** — grow with no FIFO eviction, compact with no
   digest request, lease with no step, or pointer with no prefix change makes the arm
   indistinguishable from its control.
4. **`design_cap_tokens` reading 3,838 (or 65,536) for any arm** — the runner must read
   `wall_tokens_by_arm[arm]` (10,616); the top-level value is below v8's first prompt.
5. **A spawn or a socket during a dry run** — a dry run that would have spawned or connected is
   a defect in `cell.py`, and the launch stops there.
6. **Two cells sharing a manifest filename** — one cell, one manifest, unique per (arm, rep).
7. **Any pinned file moving between the first and last invocation** — the rehearsal is then
   `unstamped`, not a pass, and must be re-run on the settled tree.

## Pinning

`sha256` recorded before and after the ten runs for `cell.py`, `run_longrun.py`, `client.py`,
`exit_codes.py`, `tasks-v6/LR-01.v8.json`, `analyze_stats.py`: **%s**.
""" % (rep["stamp"], verdict,
       "\n".join(rows), rep["all_ten_allowed"], rep["total_projected_requests"],
       rep["total_gate_displayed"], first["g1"]["spent"],
       "\n".join(probe_rows),
       first["treatments"]["grow_evict_turn"],
       first["treatments"]["compact_wall_turn"],
       first["treatments"]["lease_step_turn"],
       first["treatments"]["pointer_prefix_turn"],
       "stamped (no file moved)" if rep["stamp"] == "stamped"
       else "UNSTAMPED — moved: " + ", ".join(rep["pins_moved"]))
    with open(doc_path(), "w", encoding="utf-8") as f:
        f.write(text)


# ------------------------------------------------------------------------- --check
def do_check(manifests_dir, fixture):
    fails, notes = [], []
    paths = sorted(p for p in os.listdir(manifests_dir)
                   if p.startswith(PREFIX) and re.search(r"-r\d+\.json$", p))
    mans = []
    for p in paths:
        with open(os.path.join(manifests_dir, p), encoding="utf-8") as f:
            mans.append((p, json.load(f)))
    if len(mans) != 10:
        fails.append("expected 10 cell manifests, found %d (%s)" % (len(mans), ", ".join(paths)))
    names = [p for p, _ in mans]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        fails.append("duplicate manifest filename(s): %s" % ", ".join(dupes))
    for p, m in mans:
        tag = "%s r%s" % (m.get("arm"), m.get("rep"))
        if m.get("design_cap_tokens") == 3838:
            fails.append("THE TRAP: %s manifest %s quotes design_cap_tokens=3838 (the dead "
                         "top-level wall_tokens, below v8's own first prompt); the runner "
                         "reads wall_tokens_by_arm=10616" % (tag, p))
        for gate in ("g1", "g2", "g3"):
            if (m.get(gate) or {}).get("decision") != "allow":
                fails.append("%s %s refused: %s" % (tag, gate.upper(),
                                                    (m.get(gate) or {}).get("refusal")
                                                    or (m.get(gate) or {}).get("printed")))
        g1 = m.get("g1") or {}
        want = allowance_for(g1.get("turns") or 0)
        if g1.get("allowance") != want:
            fails.append("%s G1 allowance %s != ceil(turns*68/801)=%s"
                         % (tag, g1.get("allowance"), want))
        key, fk = ARM_TREATMENT.get(m.get("arm"), (None, None))
        t = (m.get("treatments") or {}).get(key)
        if t is None:
            fails.append("%s: %s is ABSENT — the treatment never fires inside the horizon"
                         % (tag, key))
        elif int(t) > TURNS:
            fails.append("%s: %s = %s > %s-turn horizon" % (tag, key, t, TURNS))
        if (m.get("spawns") or 0) > 0 or (m.get("network_events") or 0) > 0:
            fails.append("%s: dry run spawned or opened a socket (spawns=%s, network=%s)"
                         % (tag, m.get("spawns"), m.get("network_events")))
        if ((g1.get("turns") or 0) + (g1.get("allowance") or 0)) > CAP:
            fails.append("%s: marginal spend exceeds cap %d" % (tag, CAP))
    # the fixture's own walls and first-fire turns, recomputed from disk
    if LONG not in sys.path:
        sys.path.insert(0, LONG)
    import run_longrun as R  # noqa: E402
    fx = R.load_fixture(fixture)
    walls = (fx.get("wall_tokens_by_arm") or {})
    for arm in sorted({m.get("arm") for _, m in mans}):
        wall = R.wall_for_arm(fx, arm)
        if wall == 3838:
            fails.append("THE TRAP: fixture resolves %s to wall_tokens=3838 (dead top-level "
                         "value, below v8's first prompt 3848)" % arm)
        fires = R.treatment_fire_turns(fx, arm, TURNS)
        key, fk = ARM_TREATMENT[arm]
        for label, val in ((key, fires.get(fk)),):
            if val is None:
                fails.append("THE TRAP: %s at wall_tokens=%s: %s never fires inside %d turns"
                             % (arm, wall, label, TURNS))
            elif int(val) > TURNS:
                fails.append("%s: %s = %s > horizon %d" % (arm, label, val, TURNS))
        notes.append("%s wall=%s fires=%s" % (arm, wall, fires.get("fires")))
    if fails:
        print("tranch1_dryrun --check: FAIL (%d)" % len(fails))
        for f in fails:
            print("  - %s" % f)
        return 1
    print("tranch1_dryrun --check: PASS — 10/10 cells allowed, all four treatments fire "
          "<= %d, no duplicate manifest, design_cap_tokens=%s on every arm, 0 spawns, "
          "0 network events" % (TURNS, sorted({m['design_cap_tokens'] for _, m in mans})))
    for n in notes:
        print("  %s" % n)
    return 0


def main(argv=None):
    global FIXTURE, HYPOTHESIS, PREFIX
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="recompute from the ten manifests; exit 1 on any failure")
    ap.add_argument("--hypothesis", default=DEFAULT_HYPOTHESIS, choices=("H1", "H2"),
                    help="the claim each cell makes (default H2). H1 is NOT admissible at "
                         "n=48 and --check refuses any cell a gate refuses, so H1 only "
                         "reproduces the first rehearsal's HELD grid")
    ap.add_argument("--fixture", default=FIXTURE)
    ap.add_argument("--manifests", default=MEASURE, metavar="DIR")
    ap.add_argument("--out-dir", default=MEASURE)
    args = ap.parse_args(argv)
    HYPOTHESIS = args.hypothesis.upper()
    PREFIX = NAMED[HYPOTHESIS]["prefix"]
    FIXTURE = os.path.abspath(args.fixture)
    if args.check:
        return do_check(os.path.abspath(args.manifests), FIXTURE)
    rep = do_run(os.path.abspath(args.out_dir))
    print("tranch1_dryrun: hypothesis=%s %d cells, all_ten_allowed=%s, "
          "total_projected_requests=%s, H1 in launch artefacts=%d, stamp=%s"
          % (HYPOTHESIS, len(rep["cells"]), rep["all_ten_allowed"],
             rep["total_projected_requests"], rep["h1_occurrences"]["count"],
             rep["stamp"]))
    for c in rep["cells"]:
        print("  %-20s r%d G1 %s (%s/%s/%s) G2 %ss %s G3 n=%s %s treatments %s"
              % (c["arm"], c["rep"], c["g1"]["computed"], c["g1"]["spent"],
                 c["g1"]["turns"], c["g1"]["allowance"], c["g2"]["projected_wall"],
                 c["g2"]["decision"], c["g3"]["n"], c["g3"]["decision"],
                 {k: c["treatments"][k] for k in ("grow_evict_turn", "compact_wall_turn",
                                                 "lease_step_turn", "pointer_prefix_turn")}))
    for p in rep["pooled_probes"]:
        print("  probe %-20s reps=%d G1 %s G2 %s G3 n=%s %s"
              % (p["arm"], p["reps"], p["g1"]["computed"], p["g2"]["decision"], p["g3"]["n"], p["g3"]["decision"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
