#!/usr/bin/env python3
"""grade_v3.py - the quality instrument registered in GRADER-V3.md.

Reads row .jsonl files (read-only) and a fixture, emits one JSON verdict file.
No network, no model, no LLM judge. Standard library only.

    python3 grade_v3.py --rows R.jsonl --fixture fixtures/LR-01.json --out O.json
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone

STOPWORDS = set("""
that this than then them they their there these those with from into over
also both each only when where which while would should could must have
has had been being will shall about above across after before below between
more most some such same just like make makes made used using does doing
then once only also very much many what whom whose here were was are and
for the but not you your our its his her all any can may
""".split())

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
MARKER_RE = re.compile(r"^ANSWER:\s*\S.*$")
PREAMBLE_RE = re.compile(
    r"^(let me|let's|i will|i'll|i am going to|i'm going to|i need to|i should|"
    r"first,? i|reading|inspecting|i am reading|i'm reading)\b", re.I)
NUM_ONLY_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*(::[A-Za-z0-9_.]+)?$")

DEFAULT_BUDGETS = {"work": 150, "plant": 150, "repair": 150, "checkpoint": 400, "verify": 400}


# ---------------------------------------------------------------- text helpers
def strip_fences(text):
    """Return text with fenced lines (delimiters included) removed."""
    out, inside = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def tail_lines(text, n=3):
    """Last n non-empty, non-fenced lines."""
    lines = [l for l in strip_fences(text).splitlines() if l.strip()]
    return lines[-n:]


def anchors(s):
    seen, out = set(), []
    for m in TOKEN_RE.finditer(s):
        for part in m.group(0).split("_"):
            p = part.lower()
            if len(p) >= 4 and p not in STOPWORDS and p not in seen:
                seen.add(p)
                out.append(p)
    return out


def has_anchor(text, anchor):
    # "_" is a word char to \b, but §3 splits anchors ON "_", so the boundary
    # must treat "_" as a separator too -- otherwise "record_refusal" never
    # satisfies the anchor "record".
    return re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(anchor), text, re.I) is not None


def number_in(text, value):
    """Standalone-token number match: (?<![\\d.])64(?![\\d.])."""
    pat = r"(?<![\d.])%s(?![\d.])" % re.escape(str(value))
    return re.search(pat, text) is not None


def last_nonempty_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def marker_line(text):
    """The declared-conclusion line, if the answer ends with a marker."""
    lines = [l for l in text.splitlines() if l.strip()]
    if lines and MARKER_RE.match(lines[-1].strip()):
        return lines[-1].strip()
    return None


def excerpt(text, limit=200):
    t = " ".join(str(text).split())
    return t[:limit]


def words(text):
    return len(text.strip().split())


# ---------------------------------------------------------------- checks
def classify_checkpoint(cp):
    """Derive (kind, numeric, expected) when the fixture carries no kind."""
    kind = cp.get("kind")
    expected = cp.get("expected", cp.get("answer"))
    exp = "" if expected is None else str(expected).strip()
    if kind:
        return kind, bool(NUM_ONLY_RE.match(exp)), expected
    if NUM_ONLY_RE.match(exp):
        return "fact", True, expected
    if IDENT_RE.match(exp) and ("::" in exp or re.search(r"\.(py|json|md|yaml)$", exp)
                                or re.match(r"^[A-Z_][A-Z0-9_]*$", exp)):
        return "artifact", False, expected
    return "fact", False, expected


def value_in_prior_context(value, numeric, check_anchors, prior_rows):
    for row in prior_rows:
        c = row.get("content") or ""
        if numeric and number_in(c, value):
            return True
        if not numeric and any(has_anchor(c, a) for a in check_anchors):
            return True
    return False


def judge(kind, numeric, expected, check_anchors, text, marker_required, prior_rows):
    """Return dict(pass, reason, detail, found_excerpt)."""
    res = {"pass": False, "reason": "ok", "detail": "", "found_excerpt": excerpt(text)}
    stripped = strip_fences(text)
    tail = tail_lines(text)
    mline = marker_line(text)
    truncated_note = ""

    knowable = lambda v=None: value_in_prior_context(expected, numeric, check_anchors, prior_rows)
    concl_text = lambda: mline if mline is not None else "\n".join(tail)

    if numeric:
        val = str(expected).strip()
        # (a) a marker-required turn with no marker never concludes
        if marker_required and mline is None:
            res.update(reason="marker_missing", detail="no ^ANSWER: line")
            return res
        # (b) the value quoted only inside a pasted fence is not an answer
        if not number_in(stripped, val) and number_in(text, val):
            res.update(reason="fenced_only",
                       detail="number_only_inside_fence" + ("; marker present" if mline else ""))
            return res
        # (c) the value must sit in the concluding position
        if number_in(concl_text(), val):
            res["pass"] = True
            return res
        # (d) it is absent from the conclusion: name the competing number, if any
        m = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)(?![\d.])", concl_text())
        if m is not None:
            found = m.group(1)
            res.update(reason="number_wrong:%s" % found,
                       detail="expected %s, concluded %s" % (val, found))
            return res
        if mline is not None and knowable():
            res.update(reason="refused_while_knowable",
                       detail="marker %r carries no value; %s was in context"
                       % (mline[:40], val))
            return res
        if mline is not None:
            res.update(reason="marker_without_value",
                       detail="marker carries no %s and it was never in context" % val)
            return res
        if any(PREAMBLE_RE.match(l.strip()) for l in tail):
            res.update(reason="preamble_only",
                       detail="expected %s only above the tail" % val)
            return res
        res.update(reason="value_not_in_concluding_position",
                   detail="expected %s not in last three lines" % val)
        return res

    # ---- non-numeric (prose / artifact)
    missing = [a for a in check_anchors if not has_anchor(stripped, a)]
    if kind == "artifact":
        missing = [a for a in check_anchors if not has_anchor(text, a)]  # fences count
    if marker_required and mline is None:
        res.update(reason="marker_missing", detail="no ^ANSWER: line")
        return res
    if missing:
        res.update(reason="missing_anchor:%s" % missing[0],
                   detail="missing %d/%d anchors: %s" % (len(missing), len(check_anchors),
                                                         ",".join(missing[:6])))
        if mline is not None and knowable():
            res.update(reason="refused_while_knowable",
                       detail="marker dropped anchors; missing " + ",".join(missing[:6]))
        return res
    if kind == "artifact":
        res["pass"] = True
        return res
    if mline is not None or marker_required:
        if any(has_anchor(mline or "", a) for a in check_anchors):
            res["pass"] = True
            return res
        if knowable():
            res.update(reason="refused_while_knowable",
                       detail="anchors present but the marker line does not conclude with them")
            return res
        res.update(reason="value_not_in_concluding_position",
                   detail="anchors above the tail, marker line lacks them")
        return res
    for l in tail:
        if FENCE_RE.match(l) or MARKER_RE.match(l.strip()):
            continue
        if not PREAMBLE_RE.match(l.strip()):
            res["pass"] = True
            return res
    res.update(reason="preamble_only", detail="tail has no concluding sentence")
    return res


def judge_repair(repair, rows_by_turn):
    if not repair:
        return None
    at = repair.get("at_turn")
    literal = repair.get("accept_literal") or repair.get("correct_action") or ""
    wrong = repair.get("wrong_assumption") or ""
    anchors_lit = anchors(literal)
    row = rows_by_turn.get(at)
    text = (row or {}).get("content") or ""
    stripped = strip_fences(text)
    acked = bool(literal and literal.lower() in text.lower()) or (
        anchors_lit and all(has_anchor(stripped, a) for a in anchors_lit))
    marker = None
    for tok in re.findall(r"`([^`]+)`", wrong):
        if len(tok) >= 6:
            marker = tok
            break
    if marker is None:
        for tok in re.findall(r"\b[a-z]+-[a-z]+\b", wrong):
            if len(tok) >= 8:
                marker = tok
                break
    reasserted = False
    reassert_turn = None
    if marker:
        for t, r in sorted(rows_by_turn.items()):
            if t > at and (marker.lower() in (r.get("content") or "").lower()):
                reasserted, reassert_turn = True, t
                break
    ok = bool(acked) and not reasserted
    reason = "ok"
    if not acked:
        reason = "repair_not_acknowledged"
    elif reasserted:
        reason = "superseded_value_reasserted_at_turn_%s" % reassert_turn
    return {"id": "repair.t%s" % at, "kind": "repair", "turn": at, "pass": ok,
            "reason": reason, "found_excerpt": excerpt(text), "required": True,
            "detail": "marker=%r acked=%s" % (marker, acked)}


def judge_constraints(checks, arm_text):
    out = []
    for c in checks:
        if c.get("kind") != "constraint":
            continue
        pat = c.get("pattern")
        if not pat:
            out.append({"id": c.get("id"), "kind": "constraint", "pass": None,
                        "reason": "unverifiable", "required": False,
                        "found_excerpt": "no pattern; rows carry no write evidence"})
            continue
        flags = re.I if c.get("ignore_case") else 0
        hit = re.search(pat, arm_text, flags)
        out.append({"id": c.get("id"), "kind": "constraint", "pass": hit is None,
                    "reason": "ok" if hit is None else "forbidden_pattern_present",
                    "required": True,
                    "found_excerpt": excerpt(hit.group(0)) if hit else ""})
    return out


def judge_artifacts(checks, arm_text):
    out = []
    for c in checks:
        if c.get("kind") != "artifact":
            continue
        expected = str(c.get("expected") or c.get("pattern") or "")
        need = [a for a in anchors(expected)]
        missing = [a for a in need if not has_anchor(arm_text, a)]
        out.append({"id": c.get("id"), "kind": "artifact", "pass": not missing,
                    "required": True,
                    "reason": "ok" if not missing else "missing_anchor:%s" % missing[0],
                    "found_excerpt": excerpt(expected)})
    return out


# ---------------------------------------------------------------- arm grading
def grade_arm(arm, rows, fixture, marker_required, budgets):
    rows = sorted(rows, key=lambda r: r["turn"])
    by_turn = {r["turn"]: r for r in rows}
    arm_text = "\n".join(strip_fences(r.get("content") or "") for r in rows)
    checks, checkpoint_checks = [], []

    for idx, cp in enumerate(fixture.get("checkpoints") or []):
        turn = cp.get("turn")
        expected = cp.get("expected", cp.get("answer"))
        kind, numeric, expected = classify_checkpoint(cp)
        cid = str(cp.get("id") or ("cp.%d.t%s" % (idx, turn)))
        row = by_turn.get(turn)
        if row is None:
            checks.append({"id": cid, "kind": kind, "turn": turn, "pass": False,
                           "reason": "turn_missing", "required": True,
                           "found_excerpt": ""})
            checkpoint_checks.append(checks[-1])
            continue
        text = row.get("content") or ""
        truncated = bool(row.get("truncated")) or row.get("finish_reason") == "length"
        exp = str(expected).strip()
        ch_anchors = anchors(exp)
        prior = [r for r in rows if r["turn"] < turn]
        if truncated:
            present = number_in(strip_fences(text), exp) if numeric else (
                all(has_anchor(strip_fences(text), a) for a in ch_anchors))
            if not present:
                res = {"pass": False, "reason": "truncated_without_value",
                       "detail": "finish_reason=length and value absent before the cut",
                       "found_excerpt": excerpt(text)}
            else:
                res = judge(kind, numeric, expected, ch_anchors, text, marker_required, prior)
        else:
            res = judge(kind, numeric, expected, ch_anchors, text, marker_required, prior)
        chk = {"id": cid, "kind": kind, "turn": turn, "pass": bool(res["pass"]),
               "reason": res["reason"], "detail": res.get("detail", ""),
               "required": True, "found_excerpt": res["found_excerpt"]}
        checks.append(chk)
        checkpoint_checks.append(chk)

    rep = judge_repair(fixture.get("repair"), by_turn)
    if rep:
        checks.append(rep)
    acc = (fixture.get("acceptance") or {}).get("checks") or []
    checks.extend(judge_constraints(acc, arm_text))
    checks.extend(judge_artifacts(acc, arm_text))

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
        budget = budgets.get("checkpoint", 400)
        if words(row.get("content") or "") > budget:
            over += 1

    marker_present = sum(1 for r in rows if marker_line(r.get("content") or ""))
    return {
        "task_id": (rows[0].get("task_id") if rows else None),
        "turns": len(rows),
        "verified_success": verified,
        "checkpoint_accuracy": ("%d/%d" % (cp_pass, cp_total)) if cp_total else "0/0",
        "checkpoint_accuracy_pct": round(100.0 * cp_pass / cp_total, 1) if cp_total else None,
        "tokens_to_verified_success": ttvs,
        "over_budget_pct": round(100.0 * over / cp_turns, 1) if cp_turns else 0.0,
        "failing_reasons": [{"id": c["id"], "reason": c["reason"]} for c in required if not c["pass"]],
        "checks": checks,
        "marker_census": {"turns": len(rows), "marker_lines": marker_present},
    }


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
        import glob, os
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
        marker_required = bool(marker.get("required"))
        budgets = dict(DEFAULT_BUDGETS)
        ab = fx.get("answer_budget")
        if isinstance(ab, dict):
            for k, v in ab.items():
                if isinstance(v, int):
                    budgets[k] = v
        arms[arm] = grade_arm(arm, arows, fx, marker_required, budgets)

    out = {
        "grader": "grade_v3",
        "rule": "experiments/ptr-engine/longrun/GRADER-V3.md",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows_file": args.rows,
        "row_count": len(rows),
        "fixtures": sorted(fixtures),
        "arms": arms,
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for arm, a in arms.items():
        print("%-20s verified=%s acc=%s ttvs=%s over=%s%% reasons=%s" % (
            arm, a["verified_success"], a["checkpoint_accuracy"],
            a["tokens_to_verified_success"], a["over_budget_pct"],
            ",".join(x["reason"] for x in a["failing_reasons"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
