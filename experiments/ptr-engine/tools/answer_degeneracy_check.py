#!/usr/bin/env python3
"""answer_degeneracy_check.py - acceptance checker for Q0-ANSWER-DEGENERACY.

OFFLINE. Stdlib only. No network, no requests/httpx import, no model call.
Reads the config-C row file (read-only) and re-derives, per arm and per
checkpoint turn, exactly one of four classes for the row that answered that
turn:

    NO_ANSWER_TEXT     no non-empty line at all (content empty/whitespace)
    NO_MARKER          answered (non-empty text) with no ^ANSWER: line anywhere
    MALFORMED_MARKER   a marker-shaped line exists but is not in the concluding
                       position, or the concluding marker carries the refusal
                       sentinel (ANSWER: NOT-AN-ANSWER)
    MARKER_ACCEPTED    the LAST non-empty line is marker-shaped and carries a
                       non-refusal payload

"Accepted" here is position + payload shape only (the ^ANSWER: line rule,
grade_v3.MARKER_RE = ^ANSWER:\\s*\\S.*$).  The separate §4 value test that
grade_v3 applies on top of it is cited from the recorded .grade-v3.json, never
re-scored here.

It prints the table and exits 0 iff the recomputed table equals the table
recorded in orchestration/handoffs/Q0-ANSWER-DEGENERACY.json under
evidence.table[<arm>][<t>], else exits 1 naming the differing cells.

    python3 experiments/ptr-engine/tools/answer_degeneracy_check.py
    python3 experiments/ptr-engine/tools/answer_degeneracy_check.py --table-json   # print only

Idempotent: no writes, no mutation, same output on every run.
"""
import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------- constants
ROWS = "experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl"
HANDOFF = "orchestration/handoffs/Q0-ANSWER-DEGENERACY.json"
ARMS = ["transcript-grow", "transcript-compact", "pointer-stable", "lease-reopen"]
TURNS = [12, 24, 46]                      # config-C checkpoints cp.t12/cp.t24/cp.t46
MARKER_RE = re.compile(r"^ANSWER:\s*\S.*$")     # == grade_v3.MARKER_RE
REFUSAL = "NOT-AN-ANSWER"

NO_ANSWER_TEXT = "NO_ANSWER_TEXT"
NO_MARKER = "NO_MARKER"
MALFORMED_MARKER = "MALFORMED_MARKER"
MARKER_ACCEPTED = "MARKER_ACCEPTED"
CLASSES = (NO_ANSWER_TEXT, NO_MARKER, MALFORMED_MARKER, MARKER_ACCEPTED)


# ---------------------------------------------------------------- classify
def nonempty_lines(text):
    return [l for l in (text or "").splitlines() if l.strip()]


def classify(content):
    """Exactly one of the four classes, per the module docstring."""
    lines = nonempty_lines(content)
    if not lines:
        return NO_ANSWER_TEXT
    last = lines[-1].strip()
    marker_anywhere = any(MARKER_RE.match(l.strip()) for l in lines)
    if not marker_anywhere:
        return NO_MARKER
    if not MARKER_RE.match(last):
        # marker present but not in the concluding position the grader reads
        return MALFORMED_MARKER
    payload = MARKER_RE.match(last).group(0)[len("ANSWER:"):].strip()
    if payload.upper() == REFUSAL:
        return MALFORMED_MARKER       # present, but it declines to answer
    return MARKER_ACCEPTED


# ---------------------------------------------------------------- compute
def load_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if line:
                r = json.loads(line)
                r["_lineno"] = lineno
                rows.append(r)
    return rows


def build_table(rows):
    """table[arm][str(turn)] = class label. Missing row -> TURN_MISSING."""
    table = {a: {} for a in ARMS}
    for turn in TURNS:
        hit = {}
        for r in rows:
            if r.get("turn") == turn and r.get("arm") in table:
                hit[r["arm"]] = r
        for arm in ARMS:
            r = hit.get(arm)
            table[arm][str(turn)] = classify(r.get("content") or "") if r else "TURN_MISSING"
    return table


def value_census(rows):
    """Supplementary (not compared): does the expected value even appear?"""
    out = {}
    for r in rows:
        if r.get("turn") not in TURNS:
            continue
        exp = str(r.get("expected") or "").strip()
        c = r.get("content") or ""
        lead = exp.split()[0] if exp else ""
        out["%s:t%s" % (r["arm"], r["turn"])] = {
            "expected_lead": lead,
            "present_in_answer": bool(lead) and lead.lower() in c.lower(),
            "words": len(c.split()),
            "truncated": bool(r.get("truncated")),
            "lineno": r.get("_lineno"),
        }
    return out


def render(table):
    w = max(len(a) for a in ARMS) + 2
    head = "arm".ljust(w) + "".join(("t%s" % t).ljust(20) for t in TURNS)
    lines = [head, "-" * len(head)]
    for arm in ARMS:
        lines.append(arm.ljust(w) + "".join(table[arm][str(t)].ljust(20) for t in TURNS))
    return "\n".join(lines)


def diff_cells(mine, theirs):
    bad = []
    for arm in ARMS:
        for t in TURNS:
            k = str(t)
            want = (theirs or {}).get(arm, {}).get(k)
            got = mine[arm][k]
            if want != got:
                bad.append((arm, k, want, got))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=ROWS)
    ap.add_argument("--handoff", default=HANDOFF)
    ap.add_argument("--table-json", action="store_true",
                    help="print the table as JSON only (for embedding in the handoff)")
    args = ap.parse_args(argv)

    root = os.getcwd()
    rows_path = args.rows if os.path.isabs(args.rows) else os.path.join(root, args.rows)
    hand_path = args.handoff if os.path.isabs(args.handoff) else os.path.join(root, args.handoff)

    if not os.path.exists(rows_path):
        sys.stderr.write("missing row file: %s\n" % rows_path)
        return 1

    rows = load_rows(rows_path)
    table = build_table(rows)

    if args.table_json:
        print(json.dumps(table, indent=1, sort_keys=True))
        return 0

    print("=== Q0-ANSWER-DEGENERACY: per arm x per checkpoint-turn class ===")
    print("rows: %s (%d rows)" % (args.rows, len(rows)))
    print(render(table))
    print()
    print("class legend:")
    print("  NO_ANSWER_TEXT   no non-empty line")
    print("  NO_MARKER        answered, no ^ANSWER: line anywhere")
    print("  MALFORMED_MARKER marker-shaped line exists but is not concluding, or payload == NOT-AN-ANSWER")
    print("  MARKER_ACCEPTED  last non-empty line is ^ANSWER: <payload>, payload not a refusal")
    print()
    census = value_census(rows)
    print("=== supplementary: does the expected value appear in the answer at all? ===")
    for k in sorted(census):
        v = census[k]
        print("  %-28s line %-4s words=%-4s trunc=%-5s expected_lead=%-12r present=%s"
              % (k, v["lineno"], v["words"], v["truncated"], v["expected_lead"],
                 v["present_in_answer"]))
    print()

    if not os.path.exists(hand_path):
        sys.stderr.write("MISSING HANDOFF %s -- cannot compare\n" % hand_path)
        return 1
    with open(hand_path, "r", encoding="utf-8") as fh:
        hand = json.load(fh)
    recorded = ((hand.get("evidence") or {}).get("table")) or {}
    if not recorded:
        sys.stderr.write("handoff has no evidence.table -- cannot compare\n")
        return 1

    bad = diff_cells(table, recorded)
    if bad:
        print("FAIL: %d cell(s) differ from evidence.table" % len(bad))
        for arm, t, want, got in bad:
            print("  %-18s t%-3s handoff=%-16s recomputed=%-16s" % (arm, t, want, got))
        return 1
    print("PASS: recomputed table equals recorded evidence.table (12/12 cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
