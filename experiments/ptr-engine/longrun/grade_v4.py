#!/usr/bin/env python3
"""grade_v4.py - R2 anchor rule (ANCHOR-PREREG.md §1, frozen 2026-10-26T13:29:21Z).

Identical to grade_v3.py in EVERY respect except one: the set of anchors a
non-numeric checkpoint requires is DERIVED from an occurrence-context
classification of the cited source file instead of being "every token
`anchors()` emits":

    CODE-SYMBOL      the token occurs in the cited file outside a string literal
                     or comment -> REQUIRED
    NUMBER           the expected value is a numeric literal -> unchanged path
                     (`number_in`); required_anchors = []
    PROSE-CONNECTOR  every occurrence lies inside a string/comment, or the token
                     is absent from the file -> informational, NOT required

The classification is NOT re-implemented here: it is imported from
`experiments/ptr-engine/tools/anchor_prereg_check.py` (`classify`, `prose_lines`,
`occurrences`), which is the canonical implementation the prereg's own acceptance
checker runs. grade_v4.py therefore depends on that file.

The rest of the grader (marker requirement, `missing_anchor` reason strings,
`refused_while_knowable` taxonomy, `repair.*`, `acc.*`, budgets, accuracy) is
grade_v3.py's own code, imported and called - not copied - so it cannot drift.
When no token is classified PROSE-CONNECTOR the required set equals R1's and
`grade_v4.judge_anchored` delegates to `grade_v3.judge` verbatim, so such a grid
is graded by the identical code path.

If the fixture declares no required `answer_marker`, R2 is not applicable: the
arm is graded exactly as grade_v3 does and reports `r2_status: not_applicable`.

    python3 experiments/ptr-engine/longrun/grade_v4.py \
        --rows R.jsonl --fixture F.json --out O.grade-v4.json

Offline. Stdlib only. Writes only the --out file.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), "tools")
for _p in (HERE, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v3 as g3                      # read-only reuse of the R1 instrument
import anchor_prereg_check as apc          # canonical R2 classifier

RULE = "experiments/ptr-engine/longrun/ANCHOR-PREREG.md §1 (R2, frozen 2026-10-26T13:29:21Z)"


# ------------------------------------------------------------------ R2 rule
def classify_anchor(token, source_ref):
    """(class, evidence) for one anchor token against the cited file.

    Conservative on a malformed/missing citation: an anchor we cannot classify
    stays required (R1 behaviour), never silently relaxed.
    """
    path, _, _lineref = (source_ref or "").partition("#")
    if not path or not os.path.exists(os.path.join(apc.ROOT, path)):
        return "CODE-SYMBOL", "unclassifiable citation (%r); kept required" % (source_ref,)
    return apc.classify(source_ref, token)


def is_required(token, source_ref):
    """R2: required iff CODE-SYMBOL or NUMBER. Numbers are graded separately."""
    return classify_anchor(token, source_ref)[0] != "PROSE-CONNECTOR"


def required_anchors(expected, source_ref):
    """R2's derived required set. NUMBER expected -> [] (number_in grades it)."""
    if g3.NUM_ONLY_RE.match(str(expected).strip()):
        return []
    return [a for a in g3.anchors(str(expected).strip()) if is_required(a, source_ref)]


# ------------------------------------------------------------------ judging
def judge_anchored(kind, numeric, expected, all_anchors, need, text,
                   marker_required, prior_rows):
    """grade_v3.judge with `need` as the required set.

    `all_anchors` (R1's full derived list) is still what the knowability probe
    consults, so the refused_while_knowable / missing_anchor taxonomy of every
    check whose required set did not shrink is byte-identical to v3.
    """
    if numeric:
        # numbers are graded by number_in(); the anchor set is irrelevant here
        return g3.judge(kind, numeric, expected, all_anchors, text, marker_required, prior_rows)
    if list(need) == list(all_anchors):
        # nothing was reclassified: run R1's exact code path, not a copy of it
        return g3.judge(kind, numeric, expected, all_anchors, text, marker_required, prior_rows)

    res = {"pass": False, "reason": "ok", "detail": "", "found_excerpt": g3.excerpt(text)}
    stripped = g3.strip_fences(text)
    mline = g3.marker_line(text)

    def knowable():
        return g3.value_in_prior_context(expected, False, all_anchors, prior_rows)

    hay = text if kind == "artifact" else stripped
    missing = [a for a in need if not g3.has_anchor(hay, a)]
    if marker_required and mline is None:
        res.update(reason="marker_missing", detail="no ^ANSWER: line")
        return res
    if missing:
        res.update(reason="missing_anchor:%s" % missing[0],
                   detail="missing %d/%d anchors: %s" % (len(missing), len(need),
                                                         ",".join(missing[:6])))
        if mline is not None and knowable():
            res.update(reason="refused_while_knowable",
                       detail="marker dropped anchors; missing " + ",".join(missing[:6]))
        return res
    if kind == "artifact":
        res["pass"] = True
        return res
    if mline is not None or marker_required:
        if any(g3.has_anchor(mline or "", a) for a in need):
            res["pass"] = True
            return res
        if knowable():
            res.update(reason="refused_while_knowable",
                       detail="anchors present but the marker line does not conclude with them")
            return res
        res.update(reason="value_not_in_concluding_position",
                   detail="anchors above the tail, marker line lacks them")
        return res
    for line in g3.tail_lines(text):
        if g3.FENCE_RE.match(line) or g3.MARKER_RE.match(line.strip()):
            continue
        if not g3.PREAMBLE_RE.match(line.strip()):
            res["pass"] = True
            return res
    res.update(reason="preamble_only", detail="tail has no concluding sentence")
    return res


# ------------------------------------------------------------------ arm grading
def grade_arm(arm, rows, fixture, marker_required, budgets):
    rows = sorted(rows, key=lambda r: r["turn"])
    by_turn = {r["turn"]: r for r in rows}
    arm_text = "\n".join(g3.strip_fences(r.get("content") or "") for r in rows)
    checks, checkpoint_checks = [], []
    census, required_map = [], {}
    # R2 is applicable only where the fixture demands an ^ANSWER: marker.
    applicable = bool(marker_required)

    for idx, cp in enumerate(fixture.get("checkpoints") or []):
        turn = cp.get("turn")
        expected = cp.get("expected", cp.get("answer"))
        kind, numeric, expected = g3.classify_checkpoint(cp)
        cid = str(cp.get("id") or ("cp.%d.t%s" % (idx, turn)))
        src = cp.get("source", "")
        exp = "" if expected is None else str(expected).strip()
        all_anchors = g3.anchors(exp)
        if applicable:
            need = required_anchors(exp, src)
            for t in all_anchors:
                cls, ev = classify_anchor(t, src)
                census.append({"checkpoint": cid, "token": t, "class": cls, "evidence": ev})
            if numeric:
                census.append({"checkpoint": cid, "token": exp, "class": "NUMBER",
                               "evidence": "graded by number_in(); required_anchors=[]"})
        else:
            need = list(all_anchors)         # R2 not applicable: R1's set, R1's path
        required_map[cid] = need

        row = by_turn.get(turn)
        if row is None:
            checks.append({"id": cid, "kind": kind, "turn": turn, "pass": False,
                           "reason": "turn_missing", "required": True,
                           "found_excerpt": ""})
            checkpoint_checks.append(checks[-1])
            continue
        text = row.get("content") or ""
        truncated = bool(row.get("truncated")) or row.get("finish_reason") == "length"
        prior = [r for r in rows if r["turn"] < turn]
        if truncated:
            # "is the value present before the cut" stays R1's test (full anchor
            # list): truncation is a separate failure, R2 only trims requiredness.
            present = g3.number_in(g3.strip_fences(text), exp) if numeric else (
                all(g3.has_anchor(g3.strip_fences(text), a) for a in all_anchors))
            if not present:
                res = {"pass": False, "reason": "truncated_without_value",
                       "detail": "finish_reason=length and value absent before the cut",
                       "found_excerpt": g3.excerpt(text)}
            else:
                res = judge_anchored(kind, numeric, expected, all_anchors, need, text,
                                     marker_required, prior)
        else:
            res = judge_anchored(kind, numeric, expected, all_anchors, need, text,
                                 marker_required, prior)
        chk = {"id": cid, "kind": kind, "turn": turn, "pass": bool(res["pass"]),
               "reason": res["reason"], "detail": res.get("detail", ""),
               "required": True, "found_excerpt": res["found_excerpt"],
               "required_anchors": need}
        checks.append(chk)
        checkpoint_checks.append(chk)

    rep = g3.judge_repair(fixture.get("repair"), by_turn)
    if rep:
        checks.append(rep)
    acc = (fixture.get("acceptance") or {}).get("checks") or []
    checks.extend(g3.judge_constraints(acc, arm_text))
    checks.extend(g3.judge_artifacts(acc, arm_text))

    required = [c for c in checks if c.get("required") and c.get("pass") is not None]
    verified = bool(required) and all(c["pass"] for c in required)

    ttvs = None
    if verified:
        turns_hit = [c["turn"] for c in required if c.get("turn") is not None]
        if turns_hit:
            cut = max(turns_hit)
            ttvs = sum(r.get("uncached_tokens") or 0 for r in rows if r["turn"] <= cut)

    cp_total = len(checkpoint_checks)
    cp_pass = sum(1 for c in checkpoint_checks if c["pass"])
    over, cp_turns = 0, 0
    for c in checkpoint_checks:
        row = by_turn.get(c.get("turn"))
        if not row:
            continue
        cp_turns += 1
        if g3.words(row.get("content") or "") > budgets.get("checkpoint", 400):
            over += 1

    marker_present = sum(1 for r in rows if g3.marker_line(r.get("content") or ""))
    return {
        "task_id": (rows[0].get("task_id") if rows else None),
        "turns": len(rows),
        "anchor_rule": "R2",
        "r2_status": "applied" if applicable else "not_applicable",
        "r2_note": ("" if applicable else
                    "fixture declares no required answer_marker; R2 not applicable, "
                    "graded by grade_v3's path (not a pass)"),
        "required_anchors": required_map,
        "anchor_census": census,
        "verified_success": verified,
        "checkpoint_accuracy": ("%d/%d" % (cp_pass, cp_total)) if cp_total else "0/0",
        "checkpoint_accuracy_pct": round(100.0 * cp_pass / cp_total, 1) if cp_total else None,
        "tokens_to_verified_success": ttvs,
        "over_budget_pct": round(100.0 * over / cp_turns, 1) if cp_turns else 0.0,
        "failing_reasons": [{"id": c["id"], "reason": c["reason"]}
                            for c in required if not c["pass"]],
        "checks": checks,
        "marker_census": {"turns": len(rows), "marker_lines": marker_present},
    }


def budgets_for(fixture):
    budgets = dict(g3.DEFAULT_BUDGETS)
    ab = fixture.get("answer_budget")
    if isinstance(ab, dict):
        for k, v in ab.items():
            if isinstance(v, int):
                budgets[k] = v
    return budgets


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--fixture")
    ap.add_argument("--fixtures")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    rows = [json.loads(l) for l in open(args.rows) if l.strip()]
    fixtures = {}
    if args.fixture:
        f = json.load(open(args.fixture))
        fixtures[f["task_id"]] = f
    elif args.fixtures:
        import glob
        for p in sorted(glob.glob(os.path.join(args.fixtures, "*.json"))):
            f = json.load(open(p))
            if "task_id" in f and "checkpoints" in f:
                fixtures[f["task_id"]] = f
    else:
        sys.exit("need --fixture or --fixtures")

    by_arm = {}
    for r in rows:
        by_arm.setdefault(r["arm"], []).append(r)

    arms = {}
    for arm, arows in sorted(by_arm.items()):
        fx = fixtures.get(arows[0].get("task_id"))
        if fx is None:
            sys.exit("no fixture for task_id %r" % arows[0].get("task_id"))
        marker = fx.get("answer_marker") or {}
        arms[arm] = grade_arm(arm, arows, fx, bool(marker.get("required")),
                              budgets_for(fx))

    out = {
        "grader": "grade_v4",
        "rule": RULE,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows_file": args.rows,
        "row_count": len(rows),
        "fixtures": sorted(fixtures),
        "arms": arms,
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for arm, a in arms.items():
        print("%-20s r2=%s verified=%s acc=%s ttvs=%s over=%s%% reasons=%s" % (
            arm, a["r2_status"], a["verified_success"], a["checkpoint_accuracy"],
            a["tokens_to_verified_success"], a["over_budget_pct"],
            ",".join(x["reason"] for x in a["failing_reasons"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
