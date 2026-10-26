#!/usr/bin/env python3
"""test_grade_v4.py - red->green guard for R2 (ANCHOR-PREREG.md §1, frozen).

Four GREEN assertions:

  1. R2 win      the real V6 `cp.2.t46` answer (loaded from the row file, never
                 hand-typed) PASSES under grade_v4 while grade_v3 FAILS it.
  2. two-sided   the probe-B wrong call (`record_refusal` -> `write_audit`) and the
                 probe-C wrong kwarg (`scope=` -> `grant=`) both FAIL under
                 grade_v4, each on a missing CODE-SYMBOL anchor.
  3. no relaxation  an answer missing a genuine CODE-SYMBOL anchor (`ledger`)
                 FAILS under grade_v4.
  4. inert C-grid   on the v2/config-C fixture grade_v4 reports `not_applicable`
                 for every arm and its checkpoint accuracy is identical to v3.

RED side (`--stub-code`): with the occurrence-context classifier stubbed to
"always CODE-SYMBOL" (R1 behaviour), assertion 1 must FAIL. That run exits 1 by
construction and prints "RED CONFIRMED"; it is the proof the green run is not
vacuous.

    python3 experiments/ptr-engine/longrun/tests/test_grade_v4.py        # exit 0
    python3 experiments/ptr-engine/longrun/tests/test_grade_v4.py --stub-code  # exit 1

Read-only except for nothing at all: this guard writes no files.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
for p in (LONGRUN, os.path.join(os.path.dirname(LONGRUN), "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import grade_v3 as g3
import grade_v4 as g4

MEASURE = os.path.join(ROOT, "experiments/ptr-engine/measure")
V6_ROWS = os.path.join(MEASURE, "rows-longrun-v6-tools.jsonl")
C_ROWS = os.path.join(MEASURE, "rows-longrun-c-2026-10-26.jsonl")
V4_FIX = os.path.join(LONGRUN, "tasks-v4/runtime-v4/LR-01.v4.tools2.json")
C_FIX = os.path.join(LONGRUN, "fixtures/LR-01.json")

EXPECTED_CP2 = ("ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), "
                "before re-raising")


def load_rows(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def grade(module, rows, fixture_path, arm):
    fx = json.load(open(fixture_path))
    marker = fx.get("answer_marker") or {}
    sub = [r for r in rows if r["arm"] == arm]
    return module.grade_arm(arm, sub, fx, bool(marker.get("required")),
                            module.budgets_for(fx) if module is g4
                            else dict(g3.DEFAULT_BUDGETS))


def check(res, cid):
    for c in res["checks"]:
        if c["id"] == cid and c.get("kind") in (None, "checkpoint", "fact"):
            return c
    raise AssertionError("no check %s" % cid)


def v6_answer():
    rows = load_rows(V6_ROWS)
    hit = [r for r in rows if r.get("turn") == 46 and (r.get("content") or "").strip()]
    assert hit, "no non-empty turn-46 row in %s" % V6_ROWS
    return hit[0]["content"]


def with_t46(rows, text):
    out = []
    for r in rows:
        r = dict(r)
        if r.get("turn") == 46:
            r["content"] = text
        out.append(r)
    return out


# ------------------------------------------------------------------ assertions
def assertion_1():
    """R2 win: real V6 cp.2.t46 passes under v4, failed under v3."""
    good = v6_answer()
    rows = load_rows(V6_ROWS)
    v4 = check(grade(g4, rows, V4_FIX, "pointer-stable"), "cp.2.t46")
    v3 = check(grade(g3, rows, V4_FIX, "pointer-stable"), "cp.2.t46")
    print("  [1] real V6 cp.2.t46 (sha %s)" % __import__("hashlib").sha256(
        good.encode()).hexdigest()[:12])
    print("      v3: pass=%s reason=%s | v4: pass=%s reason=%s"
          % (v3["pass"], v3["reason"], v4["pass"], v4["reason"]))
    assert v3["pass"] is False, "R2 win precondition broken: v3 already passes cp.2.t46"
    assert v4["pass"] is True, "v4 does not pass the real V6 cp.2.t46 answer"
    return True


def assertion_2():
    """Probe B and probe C must both still fail under R2."""
    good = v6_answer()
    rows = load_rows(V6_ROWS)
    b = check(grade(g4, with_t46(rows, good.replace("record_refusal", "write_audit")),
                    V4_FIX, "pointer-stable"), "cp.2.t46")
    c = check(grade(g4, with_t46(rows, good.replace("scope", "grant")),
                    V4_FIX, "pointer-stable"), "cp.2.t46")
    print("  [2] probe B write_audit: pass=%s reason=%s | %s"
          % (b["pass"], b["reason"], b.get("detail", "")))
    print("      probe C grant=     : pass=%s reason=%s | %s"
          % (c["pass"], c["reason"], c.get("detail", "")))
    # R2 keeps grade_v3's taxonomy: a marker that dropped anchors while the value
    # was in context fails as refused_while_knowable; the missing set names the
    # CODE-SYMBOL anchor, which is what makes the rejection the right one.
    blob_b = (b["reason"] + " " + b.get("detail", "")).lower()
    blob_c = (c["reason"] + " " + c.get("detail", "")).lower()
    assert b["pass"] is False, "probe B accepted under R2 - R2 is a blanket pass"
    assert c["pass"] is False, "probe C accepted under R2"
    assert "record" in blob_b or "refusal" in blob_b, \
        "probe B must miss a code anchor (record/refusal), got %r" % blob_b
    assert "scope" in blob_c, "probe C must miss the code anchor scope, got %r" % blob_c
    assert "raising" not in blob_b and "raising" not in blob_c, \
        "probe B/C rejected on the prose connector, not on code"
    return True


def assertion_3():
    """A genuine CODE-SYMBOL anchor is still required."""
    good = v6_answer()
    rows = load_rows(V6_ROWS)
    bad = good.replace("ledger", "store")
    r = check(grade(g4, with_t46(rows, bad), V4_FIX, "pointer-stable"), "cp.2.t46")
    blob = (r["reason"] + " " + r.get("detail", "")).lower()
    print("  [3] answer with `ledger` -> `store`: pass=%s reason=%s | %s"
          % (r["pass"], r["reason"], r.get("detail", "")))
    assert r["pass"] is False, "R2 relaxed a CODE-SYMBOL anchor"
    assert "ledger" in blob, "expected a missing ledger anchor, got %r" % blob
    need = r["required_anchors"]
    assert "raising" not in need and "ledger" in need, "derived set wrong: %r" % (need,)
    return True


def assertion_4():
    """v2/config-C grid: not_applicable and coarse accuracy identical to v3."""
    rows = load_rows(C_ROWS)
    same = []
    for arm in sorted({r["arm"] for r in rows}):
        v4 = grade(g4, rows, C_FIX, arm)
        v3 = grade(g3, rows, C_FIX, arm)
        print("      %-18s v4 r2=%s acc=%s | v3 acc=%s"
              % (arm, v4["r2_status"], v4["checkpoint_accuracy"], v3["checkpoint_accuracy"]))
        assert v4["r2_status"] == "not_applicable", "%s: R2 applied where no marker exists" % arm
        assert v4["checkpoint_accuracy"] == v3["checkpoint_accuracy"], \
            "%s: accuracy moved on the inert grid" % arm
        assert v4["verified_success"] == v3["verified_success"], \
            "%s: verified_success moved on the inert grid" % arm
        for a, b in zip(v4["checks"], v3["checks"]):
            assert (a["id"], a["pass"], a["reason"]) == (b["id"], b["pass"], b["reason"]), \
                "%s: check %s differs from v3" % (arm, a["id"])
        same.append(arm)
    print("  [4] C-grid inert: 4/4 arms not_applicable, %d arms accuracy-identical to v3"
          % len(same))
    return True


def stub_code_symbol():
    """R1 behaviour: every anchor is CODE-SYMBOL, so nothing is optional."""
    g4.is_required = lambda token, source_ref: True


def main(argv):
    red = "--stub-code" in argv
    if red:
        stub_code_symbol()
        print("== RED run: classifier stubbed to always CODE-SYMBOL (R1 behaviour)")
        try:
            assertion_1()
        except AssertionError as e:
            print("   RED CONFIRMED - assertion 1 fails under the R1 stub: %s" % e)
            print("RED exit 1 (expected: the stub removes the R2 win)")
            return 1
        print("   RED NOT CONFIRMED - assertion 1 still passes under the R1 stub!")
        return 0

    print("== GREEN run: grade_v4 (R2) vs grade_v3 (R1)")
    for fn in (assertion_1, assertion_2, assertion_3, assertion_4):
        try:
            fn()
        except AssertionError as e:
            print("FAIL %s: %s" % (fn.__name__, e))
            print("exit 1")
            return 1
    print("GREEN: 4/4 assertions pass; exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
