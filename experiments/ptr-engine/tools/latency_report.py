#!/usr/bin/env python3
"""latency_report.py - re-derive LATENCY-REPORT.json from rows, on de-duplicated rows.

Why this exists
---------------
`measure/LATENCY-REPORT.json` was assembled from raw row counts. `TVS-REGRADE`
then measured **30 defensible duplicate rows** across the 14 rows files (rule R:
identical `(ts, content_sha256, prompt_tokens, completion_tokens)` within one
file, first occurrence kept) and showed that one published p95 - G7
`pointer-stable` V4-TOOLS at n=68 - reaches the analyser's n>=60 floor *only*
by counting duplicates. This script re-runs the same analysis on de-duplicated
rows, per grid, and keeps the floor exactly where it was.

The floor policy (LATENCY-UNDER-DISPUTE)
---------------------------------------
Rule R's stated basis then FAILED verification: `V-DUPLICATE-RULE` proved
`content_sha256` is `sha256(assistant content)` - a *response* hash, 869/869 rows
at `run_longrun.py:1493` - so an identical tuple is not proof of one request.
A de-duplication whose justification is disputed must not be able to *raise* the
evidence to publication, and must not be able to *lower* it either. So a cell's
p95 is produced **only if both counts clear the analyser's floor**:

    publish p95  <=>  n_raw >= 60  AND  n_dedup >= 60

Otherwise the cell is refused BY NAME with both counts quoted. This is strictly
stronger than `n_dedup >= 60` and it is the only shape that survives either
reading of the dispute (n=51 if the duplicate rows are double-writes, n=68 if
they are genuine requests). The env switch `LATENCY_FLOOR_POLICY=off` reverts the
gate to "either count clears the floor" - the union rule that lets one reading of
a disputed de-duplication decide publication - and exists only so the red->green
run of `longrun/tests/test_latency_floor_policy.py` is non-vacuous.

What it does NOT do
-------------------
* It does not edit any rows file, grade file, `TVS.json`, `REQUEST-LEDGER.json`
  or `docs/TVS.md`. De-duplicated rows are written to a TEMPORARY directory
  outside the repo and thrown away; nothing in the measurement corpus moves.
* It does not compute quantiles itself. `analyze_stats.py` is invoked **once per
  grid** (one `--rows` call, one grid's rows file) so its internal group-by-arm
  can only group inside one grid. Every p50/p95, interval and refusal string in
  the output is the analyser's own.
* It does not lower the p95 floor. `analyze_stats.min_n_for(0.95)` is 60 and is
  read from the module, not restated here.
* It does not re-derive tvs, quality or the ledger. The per-cell `quality` block
  and the `comparisons` block are carried over from the report being replaced,
  because they have other owners (`TVS.json`, `PARM-1-ERRATA`,
  `REQUEST-LEDGER-2`).

Rule status per file
--------------------
Rule R is applied only to files that can decide it: every row carries a
non-empty `content_sha256` and a millisecond `ts`. The legacy-schema files have
no `content_sha256` and a one-second `ts_utc`; applying R there collapses rows
that are demonstrably different requests, so they are `not_applicable` and are
NOT de-duplicated (excess = 0, defensible duplicate count = 0).

Usage
-----
    python3 experiments/ptr-engine/tools/latency_report.py \
        --report experiments/ptr-engine/measure/LATENCY-REPORT.json \
        --out    experiments/ptr-engine/measure/LATENCY-REPORT.json \
        --json-summary /tmp/latency-summary.json

Offline: reads rows, calls the local analyser. No network, no request.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(HERE)                      # experiments/ptr-engine
REPO = os.path.dirname(os.path.dirname(PTR))     # repo root
MEASURE = os.path.join(PTR, "measure")
ANALYZER = os.path.join(PTR, "longrun", "analyze_stats.py")

# --- grid inventory (fixture sha, tools on/off, harness era, arm) ------------
# Identity fields come from the report being replaced; n_raw / n_turn /
# n_followup / ts bounds are recomputed from the rows on every run.
GRIDS = [
    {"grid_id": "G1", "label": "stage1",
     "rows_file": "rows-longrun-2026-10-26.jsonl"},
    {"grid_id": "G2", "label": "smoke-rp",
     "rows_file": "rows-longrun-2026-10-26-policy.jsonl"},
    {"grid_id": "G3", "label": "fix-smoke",
     "rows_file": "rows-longrun-2026-10-26-fix.jsonl"},
    {"grid_id": "G4", "label": "RUN-C-V2",
     "rows_file": "rows-longrun-c-2026-10-26.jsonl"},
    {"grid_id": "G5", "label": "V3",
     "rows_file": "rows-longrun-v3-2026-10-26.jsonl"},
    {"grid_id": "G6", "label": "V4",
     "rows_file": "rows-longrun-v4-2026-10-26.jsonl"},
    {"grid_id": "G7", "label": "V4-TOOLS",
     "rows_file": "rows-longrun-v4-tools-2026-10-26.jsonl"},
    {"grid_id": "G8", "label": "V5-TOOLS",
     "rows_file": "rows-longrun-v5-tools.jsonl"},
    {"grid_id": "G9", "label": "V6-TOOLS",
     "rows_file": "rows-longrun-v6-tools.jsonl"},
    {"grid_id": "G10", "label": "CELL-145758Z",
     "rows_file": "rows-cell-pointer-stable-20261026T145758Z.jsonl"},
]

MS_TS = re.compile(r"T\d{2}:\d{2}:\d{2}\.\d+Z$")

# --- the disputed rule, labelled wherever a p95 depends on it ----------------
DEDUP_RULE_STATUS = ("disputed (V-DUPLICATE-RULE fail: response hash, "
                     "not request identity)")
POLICY_ENV = "LATENCY_FLOOR_POLICY"
FLOOR_POLICY_RULE = ("a cell's p95 is produced only if n_raw >= 60 AND "
                     "n_dedup >= 60; otherwise it is refused by name with both "
                     "counts quoted")
FLOOR_POLICY_REASON = ("rule R's justification failed verification "
                       "(content_sha256 is sha256(assistant content), a response "
                       "hash: V-DUPLICATE-RULE), so a disputed de-duplication "
                       "must not be able to raise the evidence to publication")


def policy_enabled():
    """True unless the red->green switch turns the both-count gate off."""
    return os.environ.get(POLICY_ENV, "on") != "off"


def publication_gate(n_raw, n_dedup, floor95):
    """The floor policy, in one function, over BOTH counts.

    `publish` is True only when the raw sample AND the de-duplicated sample each
    reach the floor. When the policy switch is off the gate falls back to
    "either count clears the floor", which is the pre-policy union rule; that
    fallback is what the red->green test exercises, never a published report.
    """
    raw_ok = isinstance(n_raw, int) and n_raw >= floor95
    ded_ok = isinstance(n_dedup, int) and n_dedup >= floor95
    if not policy_enabled():
        ok = raw_ok or ded_ok
        basis = ("policy disabled (%s=off): published on whichever count clears "
                 "the floor - n_raw=%s, n_dedup=%s, floor=%d"
                 % (POLICY_ENV, n_raw, n_dedup, floor95))
    else:
        ok = raw_ok and ded_ok
        if ok:
            basis = ("both counts clear the floor: n_raw=%s, n_dedup=%s (floor %d)"
                     % (n_raw, n_dedup, floor95))
        else:
            short = []
            if not raw_ok:
                short.append("n_raw=%s" % (n_raw,))
            if not ded_ok:
                short.append("n_dedup=%s" % (n_dedup,))
            basis = ("withheld by the both-count floor policy: %s below %d "
                     "(n_raw=%s, n_dedup=%s)"
                     % (" and ".join(short), floor95, n_raw, n_dedup))
    return {"publish": ok, "policy_enabled": policy_enabled(),
            "floor": floor95, "n_raw": n_raw, "n_dedup": n_dedup,
            "basis": basis}


def load_analyzer():
    spec = importlib.util.spec_from_file_location("analyze_stats", ANALYZER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_stats"] = mod
    spec.loader.exec_module(mod)
    return mod


def read_rows(path):
    rows = []
    with open(path, "rb") as fh:
        for line in fh.read().decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # half-written tail: never fatal
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def rule_status(rows):
    """`decided` iff every row carries content_sha256 and a millisecond ts."""
    if not rows:
        return "not_applicable"
    for r in rows:
        if not r.get("content_sha256"):
            return "not_applicable"
        ts = r.get("ts")
        if not isinstance(ts, str) or not MS_TS.search(ts):
            return "not_applicable"
    return "decided"


_TURN_KINDS = None


def turn_row_kinds():
    """The turn-kind set, owned by the frozen analyser (`TURN_ROW_KINDS`).

    Read from `analyze_stats`, never restated here: a turn row is a *turn
    identity* row (`turn-initial` or legacy `turn`), and the ledger's own
    definition of it has one owner.
    """
    global _TURN_KINDS
    if _TURN_KINDS is None:
        _TURN_KINDS = tuple(getattr(load_analyzer(), "TURN_ROW_KINDS",
                                    ("turn-initial", "turn")))
    return _TURN_KINDS


def _row_seq(r, ordinal):
    """Wire order of one row: explicit `row_seq`, else `send_index`, else file ordinal."""
    for field in ("row_seq", "send_index"):
        v = r.get(field)
        if isinstance(v, int):
            return v
    return ordinal


def dedupe(rows):
    """Rule R. Returns (kept_rows, groups, excess).

    Collision precedence, and only this precedence, decides the survivor:

    1. **A turn-kind row beats a non-turn row.** On the legacy tools files the
       first-written copy of the last send is a `tool-followup` row and the
       mirrored copy is the `kind='turn'` row the frozen per-turn definition
       selects (`analyze_stats.turn_latency_rows`). The two rows carry the same
       measurement (`ts`, `ttft_ms`, `latency_s`, token counts); only `kind` and
       `prompt_sha256` differ. Keeping the tool-followup copy therefore removes
       no measurement but deletes a *turn* from the turn-level sample -- 48
       turns become 46 (G8) / 37 (G9). A turn is identified by its request, so
       rule R must never drop a turn-kind row while a non-turn duplicate exists.
    2. **Between two turn-kind rows the later write survives** -- later
       `row_seq`, else later `send_index`, else later position in the file
       (`_row_seq`). `run_longrun.py` writes one row per send and the attributed
       turn row is the LAST send of the turn (`send_index=len(followup_rows)`),
       so the last copy is the attributed measurement of that request.
    3. **Otherwise the first occurrence is kept** (the pre-existing rule,
       unchanged for every non-turn collision).

    The survivor stays in its original wire position and the kept-row count is
    unchanged: a collision group still contributes exactly one row.
    """
    seen, kept, where, groups = set(), [], {}, {}
    ords = []
    tk = turn_row_kinds()
    for ordinal, r in enumerate(rows):
        key = (r.get("ts"), r.get("content_sha256"),
               r.get("prompt_tokens"), r.get("completion_tokens"))
        if key in seen:
            groups[key] = groups.get(key, 1) + 1
            pos = where[key]
            prev = kept[pos]
            new_turn = r.get("kind") in tk
            prev_turn = prev.get("kind") in tk
            if new_turn and not prev_turn:
                kept[pos], ords[pos] = r, ordinal      # 1: turn-kind wins
            elif new_turn and prev_turn and \
                    _row_seq(r, ordinal) > _row_seq(prev, ords[pos]):
                kept[pos], ords[pos] = r, ordinal      # 2: later turn-kind wins
            continue                                   # 3: else first kept
        seen.add(key)
        where[key] = len(kept)
        kept.append(r)
        ords.append(ordinal)
    excess = len(rows) - len(kept)
    return kept, len(groups), excess


def _mean_ttft(rows, arm):
    """AD HOC mean TTFT of the kept rows (no interval; the analyser owns intervals).

    Replaced, not carried over: a duplicate row is a second copy of one
    measurement, so de-duplication moves a mean and the old value is stale.
    """
    vals = [float(r["ttft_ms"]) for r in rows
            if (r.get("arm") or "default") == arm
            and isinstance(r.get("ttft_ms"), (int, float))
            and r.get("ttft_source") != "unavailable"]
    return round(sum(vals) / len(vals), 2) if vals else None


def dedupe_rows(rows, enabled=True):
    """Apply rule R only where it is decidable.

    Returns (kept, groups, excess, status). `status` is `decided` only for a
    file where every row carries a content_sha256 and a millisecond ts; a
    legacy-schema file is `not_applicable` and every row is kept, because R
    there collapses rows that are demonstrably different requests.
    `enabled=False` is the red->green switch: it skips R while leaving the
    p95 floor exactly where it is, which is how the refusal test is proved
    non-vacuous.
    """
    status = rule_status(rows)
    if not enabled or status != "decided":
        return rows, 0, 0, status
    kept, groups, excess = dedupe(rows)
    return kept, groups, excess, status


def run_analyzer(path, tmpdir, tag):
    out = os.path.join(tmpdir, "%s.json" % tag)
    proc = subprocess.run(
        [sys.executable, ANALYZER, "--rows", path, "--json", out],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit("analyze_stats failed on %s: %s" % (tag, proc.stderr[-2000:]))
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", default=os.path.join(MEASURE, "LATENCY-REPORT.json"),
                    help="the report being re-issued (source of quality/comparisons)")
    ap.add_argument("--out", default=os.path.join(MEASURE, "LATENCY-REPORT.json"))
    ap.add_argument("--summary", default=None,
                    help="optional JSON summary of the numbers that moved")
    ap.add_argument("--no-dedup", action="store_true",
                    help="RED-TO-GREEN switch: disable de-duplication (the p95 "
                         "refusal must disappear when this is set)")
    args = ap.parse_args(argv)

    stats = load_analyzer()
    floor95 = stats.min_n_for(0.95)
    floor50 = stats.min_n_for(0.50)

    with open(args.report, encoding="utf-8") as fh:
        prior = json.load(fh)
    prior_cells = {(c["grid_id"], c["arm"]): c for c in prior["cells"]}
    prior_grids = {g["grid_id"]: g for g in prior["grids"]}

    tmpdir = tempfile.mkdtemp(prefix="latency-dedup-")
    file_report, cells, grids, moved = {}, [], [], []

    # Every rows file in measure/ gets a rule status, including the ones that
    # feed no grid (the non-longrun corpus): the report has to say per FILE
    # whether R was applied, not only per grid.
    for path in sorted(glob.glob(os.path.join(MEASURE, "rows-*.jsonl"))):
        name = os.path.basename(path)
        rows = read_rows(path)
        kept, groups, excess, status = dedupe_rows(rows)
        file_report[name] = {
            "rows": len(rows), "dedup_rows": len(kept),
            "groups": groups, "excess": excess,
            "rule_status": status, "sha256": sha256(path),
            "feeds_grid": any(g["rows_file"] == name for g in GRIDS),
        }
    all_cell_summary = []

    for g in GRIDS:
        gid, label = g["grid_id"], g["label"]
        path = os.path.join(MEASURE, g["rows_file"])
        rows = read_rows(path)
        kept, groups, excess, status = dedupe_rows(
            rows, enabled=not args.no_dedup)
        used_status = status if not args.no_dedup else "not_deduped"
        file_report[g["rows_file"]] = {
            "rows": len(rows), "dedup_rows": len(kept),
            "groups": groups, "excess": excess,
            "rule_status": used_status,
            "sha256": sha256(path),
            "feeds_grid": True,
        }
        dedup_path = os.path.join(tmpdir, "%s.jsonl" % gid)
        with open(dedup_path, "w", encoding="utf-8") as fh:
            for r in kept:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        arm_stats = run_analyzer(dedup_path, tmpdir, gid)

        gmeta = {k: v for k, v in prior_grids[gid].items() if k != "arm_cells"}
        gmeta.update({
            "n_rows": len(rows),
            "n_rows_dedup": len(kept),
            "dedup_excess": excess,
            "rule_status": used_status,
            "ts_min": min((r.get("ts") or "") for r in rows) or None,
            "ts_max": max((r.get("ts") or "") for r in rows) or None,
        })
        gmeta["n_turn"] = sum(1 for r in rows if r.get("kind") == "turn")
        gmeta["n_tool_followup"] = sum(
            1 for r in rows if r.get("kind") == "tool-followup")
        gmeta_kept = [r for r in kept]
        gmeta["n_turn_dedup"] = sum(1 for r in gmeta_kept if r.get("kind") == "turn")
        gmeta["n_tool_followup_dedup"] = sum(
            1 for r in gmeta_kept if r.get("kind") == "tool-followup")
        gmeta["arm_cells"] = []

        for arm in gmeta.get("arms", sorted(arm_stats["arms"])):
            if arm not in arm_stats["arms"]:
                continue
            a = arm_stats["arms"][arm]
            old = prior_cells.get((gid, arm), {})
            # Values this re-issue replaces. Inherited on a re-run so a second
            # pass cannot quietly forget what was withdrawn.
            sup = old.get("supersedes") or {
                "n_raw": old.get("n_rows"),
                "p50": (old.get("p50") or {}).get("point"),
                "p95": (old.get("p95") or {}).get("point"),
            }
            p50, p95 = a["p50"], a["p95"]
            ttft = a["ttft"]
            # --- the both-count floor policy, applied to EVERY cell ----------
            gate = publication_gate(sup.get("n_raw"), a["n_rows"], floor95)
            rule_touched = (used_status == "decided" and excess > 0)
            if p95.get("point") is not None and not gate["publish"]:
                # a p95 the analyser would print but the floor policy refuses:
                # never published, never replaced by a hand-computed quantile.
                p95 = {"refused": gate["basis"], "n": p95.get("n"),
                       "n_raw": sup.get("n_raw"), "n_dedup": a["n_rows"]}
            cell = {
                "grid_id": gid, "label": label, "arm": arm,
                "n_raw": sup.get("n_raw"),
                "n_dedup": a["n_rows"],
                "n_turn": old.get("n_turn"),
                "n_turn_dedup": sum(
                    1 for r in kept
                    if (r.get("arm") or "default") == arm
                    and r.get("kind") == "turn"),
                "n_followup": old.get("n_followup"),
                "n_followup_dedup": sum(
                    1 for r in kept
                    if (r.get("arm") or "default") == arm
                    and r.get("kind") == "tool-followup"),
                "requests": old.get("requests"),
                "requests_dedup": a["n_rows"],
                "ttft_used": ttft["used"],
                "ttft_dropped_null": ttft["dropped_null"],
                "ttft_dropped_unavailable": ttft["dropped_unavailable"],
                "prompt_tokens": sum(int(r.get("prompt_tokens") or 0) for r in kept
                                     if (r.get("arm") or "default") == arm),
                "completion_tokens": sum(
                    int(r.get("completion_tokens") or 0) for r in kept
                    if (r.get("arm") or "default") == arm),
                "mean_ttft_ms_ADHOC": _mean_ttft(kept, arm),
                "supersedes": sup,
                "p50": p50, "p95": p95,
                "publication": gate,
                "quality": old.get("quality"),
                "dedup": {
                    "n_raw": sup.get("n_raw"), "n_dedup": a["n_rows"],
                    "excess": (sup.get("n_raw") or 0) - a["n_rows"],
                    "rule_status": used_status,
                },
            }
            if (rule_touched or p95.get("point") is not None
                    or (old.get("p95") or {}).get("point") is not None):
                # Every withheld or surviving p95 in a rule-R-touched tool grid
                # carries the dispute label beside BOTH counts: a reader can see
                # the number is conditional without opening the card.
                cell["dedup_rule_status"] = DEDUP_RULE_STATUS
                cell["withdrawal_basis"] = (
                    p95.get("refused") and gate["basis"]
                    or ("not withdrawn - both counts clear the floor (n_raw=%s, "
                        "n_dedup=%s); the figure is conditional on rule R, not "
                        "withdrawn by arithmetic"
                        % (sup.get("n_raw"), a["n_rows"])))
            if p95.get("point") is not None and p95.get("n", 0) < floor95:
                raise SystemExit("floor violated: %s/%s p95 at n=%s < %s"
                                 % (gid, arm, p95.get("n"), floor95))
            if p95.get("point") is not None and policy_enabled() and not gate["publish"]:
                raise SystemExit("both-count floor violated: %s/%s p95 published "
                                 "at n_raw=%s n_dedup=%s"
                                 % (gid, arm, sup.get("n_raw"), a["n_rows"]))
            if p95.get("point") is not None and (
                    sup.get("n_raw") is None or a["n_rows"] is None):
                raise SystemExit("bare p95 without both counts at %s/%s"
                                 % (gid, arm))
            if "refused" in p95 and "point" in p95:
                raise SystemExit("bare/duplicated p95 representation at %s/%s" % (gid, arm))
            if p95.get("point") is not None and (p95.get("lo") is None or p95.get("hi") is None):
                raise SystemExit("p95 without interval at %s/%s" % (gid, arm))
            # what moved
            op50, op95 = sup.get("p50"), sup.get("p95")
            rec = {"grid_id": gid, "arm": arm,
                   "n_raw": sup.get("n_raw"), "n_dedup": a["n_rows"],
                   "p50_before": op50, "p50_after": p50.get("point"),
                   "p95_before": op95, "p95_after": p95.get("point"),
                   "p95_refusal_after": p95.get("refused"),
                   "publication": gate}
            if op95 is not None and p95.get("point") is None:
                rec["withdrawn"] = True
            cells.append(cell)
            gmeta["arm_cells"].append(cell)
            all_cell_summary.append(rec)
        grids.append(gmeta)

    # A withdrawal is a permanent record: carry every earlier one forward and
    # add only the ones this pass newly discovers.
    withdrawn = [dict(w) for w in prior.get("withdrawn", [])]
    by_key = {(w.get("grid_id"), w.get("arm")): i for i, w in enumerate(withdrawn)}
    for rec in all_cell_summary:
        if not rec.get("withdrawn"):
            continue
        prior_p95 = prior_cells[(rec["grid_id"], rec["arm"])].get("p95") or {}
        old = {"point": rec["p95_before"], "lo": prior_p95.get("lo"),
               "hi": prior_p95.get("hi"), "n": prior_p95.get("n")}
        key = (rec["grid_id"], rec["arm"])
        if key in by_key:
            # A refreshed entry keeps the ORIGINAL published figure: the
            # withdrawn number is history, not something this pass re-derives.
            prev_old = withdrawn[by_key[key]].get("old") or {}
            for k in ("point", "lo", "hi", "n"):
                if prev_old.get(k) is not None:
                    old[k] = prev_old[k]
        entry = {
            "grid_id": rec["grid_id"], "arm": rec["arm"], "metric": "p95",
            "old": {"point": old.get("point"),
                    "lo": old.get("lo"), "hi": old.get("hi"),
                    "n": old.get("n")},
            "n_raw": rec["n_raw"], "n_dedup": rec["n_dedup"],
            "dedup_rule_status": DEDUP_RULE_STATUS,
            "withdrawal_basis": (
                "two independent grounds, either sufficient: (1) the both-count "
                "floor policy - n_raw=%s, n_dedup=%s, floor=%s; (2) rule R's "
                "justification failed V-DUPLICATE-RULE, so the de-duplicated n "
                "is itself disputed and must not re-publish or re-withdraw the "
                "figure. Withheld pending a request_sha256 or a writer-level "
                "double-append proof (owned by DEDUPE-ROOT-CAUSE)."
                % (rec["n_raw"], rec["n_dedup"], floor95)),
            "reason": ("duplicate-inflated raw n: the published n=%s counted %d "
                       "duplicate row(s); on de-duplicated rows n=%s < %s, so "
                       "analyze_stats.py refuses p95 by name and this value is "
                       "WITHDRAWN, not replaced"
                       % (old.get("n"),
                          (rec["n_raw"] or 0) - (rec["n_dedup"] or 0),
                          rec["n_dedup"], floor95)),
            "refusal": rec["p95_refusal_after"],
        }
        if key in by_key:
            withdrawn[by_key[key]] = entry      # refreshed, never duplicated
        else:
            by_key[key] = len(withdrawn)
            withdrawn.append(entry)

    p95_cells = [c for c in cells if c["p95"].get("point") is not None]
    p50_cells = [c for c in cells if c["p50"].get("point") is not None]
    comparisons = prior.get("comparisons", [])
    pairs_with_p95 = sum(1 for c in comparisons
                         if c.get("p95_available_both") and c.get("p95_a") is not None)
    p50_moved = [c for c in p50_cells if c["n_raw"] != c["n_dedup"]]
    g4 = [c for c in cells if c["grid_id"] == "G4"]

    report = {
        "unit": "LATENCY-UNDER-DISPUTE",
        "supersedes_unit": "LATENCY-REPORT-2",
        "generated": prior.get("generated"),
        "reissued": "2026-10-26",
        "live_requests": 0,
        "network": False,
        "analyser": prior.get("analyser"),
        "grid_rule": prior.get("grid_rule"),
        "floor_policy": {
            "rule": FLOOR_POLICY_RULE,
            "reason": FLOOR_POLICY_REASON,
            "floor": floor95,
            "applied_to": "every cell, both p50 and p95 columns; p95 only",
            "env_switch": "%s=off reverts the gate to 'either count clears the "
                          "floor' for the red->green test only" % POLICY_ENV,
            "cells": len(cells),
            "cells_with_p50": len(p50_cells),
            "cells_with_p95_published": len(p95_cells),
            "cells_with_p95_withheld": sum(
                1 for c in cells
                if (c["p95"].get("point") is None
                    and (c["supersedes"] or {}).get("p95") is not None)),
            "cells_withheld_by_this_policy_alone": sum(
                1 for c in cells
                if c["p95"].get("refused") and c["publication"]["publish"]),
        },
        "disputed_rule": {
            "rule": "identical (ts, content_sha256, prompt_tokens, "
                    "completion_tokens) within one file; first occurrence kept "
                    "(TVS-REGRADE duplicate_rows.rule)",
            "status": DEDUP_RULE_STATUS,
            "verdict": "orchestration/handoffs/V-DUPLICATE-RULE.json overall=fail",
            "why_it_fails": "content_sha256 is sha256(assistant content), a "
                            "RESPONSE hash - 869/869 rows at run_longrun.py:1493 "
                            "- so an identical tuple is not proof of one request. "
                            "The 41 groups / 54 excess / 30 decided pairs and the "
                            "0-of-30 second-attempt finding reproduce; the identity "
                            "claim does not.",
            "readings": {
                "if_the_30_are_double_writes":
                    "G7 V4-TOOLS pointer-stable true n = 51 and its p95 is "
                    "unmeasurable at the current corpus (51 < 60).",
                "if_the_30_are_genuine_requests":
                    "G7 true n = 68 and the published p95 318.14 [235.00, 526.41] "
                    "n=68 stands.",
            },
            "deciding_measurement": "a request_sha256 recorded on future rows, or "
                                    "a writer-level double-append proof",
            "owner": "DEDUPE-ROOT-CAUSE",
            "until_then": "the WITHDRAWN reading is the one to quote; the "
                          "both-count floor policy withholds G7 under either reading",
        },
        "estimability_floor": {
            "p50_min_n": floor50, "p95_min_n": floor95,
            "source": "analyze_stats.min_n_for(q) — read from the module, never restated",
            "enforced": "a p95 is published only when BOTH n_raw and n_dedup reach "
                        "%d AND the analyser produced a point with an interval; "
                        "otherwise the cell is refused by name with both counts "
                        "quoted" % floor95,
        },
        "dedup_rule": {
            "rule": "identical (ts, content_sha256, prompt_tokens, "
                    "completion_tokens) within one file; first occurrence kept, "
                    "the rest are excess (TVS-REGRADE duplicate_rows.rule)",
            "source": "orchestration/handoffs/TVS-REGRADE.json; measure/DUPLICATE-ROWS.md §1 Rule R (no disagreement)",
            "applicability": "decided only on files whose every row carries a "
                             "content_sha256 and a millisecond ts; the legacy "
                             "schema (no content_sha256, one-second ts_utc) is "
                             "not_applicable and is NOT de-duplicated",
            "files_decided": sorted(k for k, v in file_report.items()
                                    if v["rule_status"] == "decided"),
            "files_not_applicable": sorted(k for k, v in file_report.items()
                                           if v["rule_status"] != "decided"),
            "defensible_excess": sum(v["excess"] for v in file_report.values()
                                     if v["rule_status"] == "decided"),
            "rows_raw": sum(v["rows"] for v in file_report.values()),
            "rows_dedup": sum(v["dedup_rows"] for v in file_report.values()),
        },
        "files_not_applicable": sorted(k for k, v in file_report.items()
                                       if v["rule_status"] != "decided"),
        "row_files": {
            "count": len(file_report),
            "files": file_report,
            "sha256": {k: v["sha256"] for k, v in sorted(file_report.items())},
        },
        "withdrawn": withdrawn,
        "cells": cells,
        "grids": grids,
        "comparisons": comparisons,
        "quality_totals": prior.get("quality_totals"),
        "tokens_to_verified_success": prior.get("tokens_to_verified_success"),
        "p95_inventory": {
            "cells_with_p50": len(p50_cells),
            "cells_with_p95": len(p95_cells),
            "cells": [{"grid_id": c["grid_id"], "arm": c["arm"],
                       "n": c["n_dedup"], "n_raw": c["n_raw"],
                       "n_dedup": c["n_dedup"],
                       "dedup_rule_status": c.get("dedup_rule_status"),
                       "p95": c["p95"].get("point"),
                       "lo": c["p95"].get("lo"), "hi": c["p95"].get("hi")}
                      for c in p95_cells],
            "grids_with_a_p95": sorted({c["grid_id"] for c in p95_cells}),
            "arms_with_a_p95": sorted({c["arm"] for c in p95_cells}),
            "arms_with_a_p95_count": len({c["arm"] for c in p95_cells}),
            "pairs_with_p95": pairs_with_p95,
            "any_inter_arm_comparison": False,
            "inter_arm_basis": "every p95-bearing cell is a single-arm tool grid "
                               "(pointer-stable, tools ON); the 8 comparison rows "
                               "are G4/G5/G6 p50-only and carry p95_available_both "
                               "= false",
            # Label note (not a number): this counts cells of the PRIOR artefact
            # that carry a p95 point -- the "before" for cells_with_p95 above,
            # NOT a refusal count. Documented on docs/LATENCY-REPORT.md.
            "cells_with_p95_raw": sum(
                1 for c in prior["cells"]
                if (c.get("p95") or {}).get("point") is not None),
        },
        "unaffected_by_rule_r": {
            "p50_cells_total": len(p50_cells),
            "p50_cells_bitexact": len(p50_cells) - len(p50_moved),
            "p50_cells_moved": [
                {"grid_id": c["grid_id"], "arm": c["arm"],
                 "n_raw": c["n_raw"], "n_dedup": c["n_dedup"],
                 "p50": c["p50"].get("point")} for c in p50_moved],
            "g4_run_c_v2": {
                "grid_id": "G4",
                "arms": sorted(c["arm"] for c in g4),
                "arms_count": len(g4),
                "n_raw_per_arm": sorted({c["n_raw"] for c in g4}),
                "n_dedup_per_arm": sorted({c["n_dedup"] for c in g4}),
                "excess": sorted({(c["dedup"] or {}).get("excess") for c in g4}),
                "p50_moved": any(c["n_raw"] != c["n_dedup"] for c in g4),
            },
            "note": "rule R is a no-op on any file with zero excess: the G4 four-arm "
                    "RUN-C-V2 table (48 raw = 48 de-duplicated per arm, 0 removed) "
                    "and 9 of the 12 p50 cells are bit-identical to LATENCY-REPORT. "
                    "The 3 p50 values that moved sit on the only three files rule R "
                    "touched, and all three keep a p50 above the n>=20 floor under "
                    "BOTH counts (smallest: G7 n_raw 68, n_dedup 51).",
        },
        "cells_moved": [r for r in all_cell_summary
                        if r["n_raw"] != r["n_dedup"]
                        or r["p50_before"] != r["p50_after"]
                        or (r["p95_before"] is not None
                            and r["p95_after"] is None)],
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
        fh.write("\n")

    summary = {
        "p95_before": report["p95_inventory"]["cells_with_p95_raw"],
        "p95_after": len(p95_cells),
        "p95_cells": report["p95_inventory"]["cells"],
        "withdrawn": withdrawn,
        "moved": all_cell_summary,
        "files_not_applicable": report["files_not_applicable"],
    }
    if args.summary:
        with open(args.summary, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=1)
    print(json.dumps({k: summary[k] for k in ("p95_before", "p95_after",
                                              "p95_cells", "withdrawn")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
