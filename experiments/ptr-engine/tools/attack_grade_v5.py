#!/usr/bin/env python3
"""attack_grade_v5.py - an independent adversarial probe set for grade_v5.py.

WHAT THIS IS. `grade_v5.py` claims: a checkpoint answer is a typed value, parsing is
mechanical, truth is AST-derived, and TEXT never passes. This script does not take
that claim on trust. It builds its OWN temp fixture - a small resolve.py/errors.py
pair written into a temp dir, whose AST truth it controls - wires it into
`grade_v5.derive_truth` through absolute `sources` paths (grade_v5 joins a path
containing a separator onto ROOT, and an absolute second argument wins, so the
fixture's truth really does come from the temp tree, not the repo), and then grades
hand-written probe answers against it.

Zero inference. Every probe is a literal string. Nothing in the repo is edited: the
judge, its tests and the fixtures are imported/read only.

    python3 experiments/ptr-engine/tools/attack_grade_v5.py            # table + json
    python3 experiments/ptr-engine/tools/attack_grade_v5.py --keep-temp
    python3 experiments/ptr-engine/tools/attack_grade_v5.py --json /tmp/x.json

Exit status: 0 when every mandatory attack behaves acceptably, 1 when at least one
does not (the unsatisfied attack ids are printed). Probe `expect` values are
"pass" (a correct answer; must pass), "fail" (a wrong or absent answer; must not
pass), or "observe" (no binary expectation: the card asks what happens).

Offline, stdlib only, deterministic.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.join(os.path.dirname(HERE), "longrun")
for _p in (LONGRUN, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import det_verify as dv          # noqa: E402  (canonical citation/AST helpers)
import grade_v5 as g5            # noqa: E402  (the judge under attack)


# --------------------------------------------------------------------------- #
# 1. the temp fixture: AST truth we control
# --------------------------------------------------------------------------- #
RESOLVE_SRC = '''"""Probe module for attack_grade_v5 (temp tree, not repo source).

Docstring occurrences on purpose: `ledger.record_refusal(...)` and
`ledger.write_audit(...)` are NAMED here in prose only. An AST-derived judge must
never read a string or a docstring as evidence of a call.
"""
DEFAULT_MAX_REFS = 64


def _refuse(ledger=None, scope_name=None, text=None, error=None):
    """Record the refusal before re-raising.

    Text written before re-raising:
        ledger.record_refusal(scope=..., serialized_ref=..., code=...)
    """
    if ledger is not None:
        ledger.record_refusal(
            scope=scope_name, serialized_ref=text, code=error.code
        )
    return None
'''

# only a STRING mentions the call; the function body contains none.
STRING_ONLY_SRC = '''"""_refuse does not call ledger.record_refusal(scope=..., serialized_ref=..., code=...)."""


def _refuse(ledger=None):
    """It never calls ledger.record_refusal(scope=x, serialized_ref=y, code=z)."""
    return None
'''

ERRORS_SRC = '''"""Probe error taxonomy (temp tree)."""


class PtrError(Exception):
    pass


class PtrScopeError(PtrError):
    pass


class PtrRefError(PtrError):
    pass


class Helper(object):
    pass
'''

CALL_EXPECTED = "ledger.record_refusal(scope=..., serialized_ref=text, code=error.code)"
CALL_TEXT = "ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)"
# The contract form is `ANSWER: CALL <callee>(...)` (v5 fixture system_prompt, normative).
CALL_ANSWER = "ANSWER: CALL " + CALL_TEXT


def build_temp_fixture():
    tmp = tempfile.mkdtemp(prefix="attack-grade-v5-")
    root = os.path.join(tmp, "fixture")
    os.makedirs(root)
    resolve_path = os.path.join(root, "resolve.py")
    string_path = os.path.join(root, "resolve_stringonly.py")
    errors_path = os.path.join(root, "errors.py")
    for path, src in ((resolve_path, RESOLVE_SRC), (string_path, STRING_ONLY_SRC),
                      (errors_path, ERRORS_SRC)):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
    fixture = {
        "task_id": "ATTACK-GRADE-V5.probe",
        "fixture_version": "attack-probe",
        "sources": [
            {"id": "resolve.py", "path": resolve_path},
            {"id": "errors.py", "path": errors_path},
        ],
        "checkpoints": [
            {"id": "atk.num", "turn": 12, "expected": "64",
             "question": "value of DEFAULT_MAX_REFS",
             "answer_spec": {"kind": "NUM",
                             "derive": {"rule": "constant_value",
                                        "symbol": "DEFAULT_MAX_REFS"}}},
            {"id": "atk.count", "turn": 24, "expected": "3",
             "question": "count of class Ptr* in errors.py",
             "answer_spec": {"kind": "NUM",
                             "derive": {"rule": "count_classes",
                                        "pattern": r"^Ptr\w*$"}}},
            {"id": "atk.call", "turn": 46, "expected": CALL_EXPECTED,
             "question": "what does _refuse call, and what does it pass?",
             "answer_spec": {"kind": "CALL",
                             "derive": {"rule": "call_inside_function",
                                        "function": "_refuse",
                                        "attr": "record_refusal"}}},
        ],
    }
    fixture_path = os.path.join(root, "PROBE-LR-01.v5.json")
    with open(fixture_path, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, indent=1)
    return tmp, fixture_path, fixture, {"resolve": resolve_path,
                                        "string_only": string_path,
                                        "errors": errors_path}


# --------------------------------------------------------------------------- #
# 2. the probe set (hand-written answers, one per row)
# --------------------------------------------------------------------------- #
# expect: "pass" = a correct answer; "fail" = wrong/absent; "observe" = report only.
PROBES = [
    # ---- attack 1: citation-numeral trap (NUM truth 64) ---------------------
    dict(id="P01", attack=1, truth="NUM", text="ANSWER: 64 (resolve.py:39)",
         expect="pass", note="citation must not override the asserted value"),
    dict(id="P02", attack=1, truth="NUM", text="ANSWER: 39",
         expect="fail", note="the citation numeral is not the answer"),
    dict(id="P03", attack=1, truth="NUM", text="ANSWER: NUM 64 (resolve.py:39)",
         expect="pass", note="explicit NUM form with a trailing citation"),
    dict(id="P04", attack=1, truth="NUM", text="ANSWER: 39 (resolve.py:64)",
         expect="fail", note="wrong value whose citation is the right value"),
    # ---- attack 2: negation inversion (CALL truth) -------------------------
    dict(id="P05", attack=2, truth="CALL",
         text="ANSWER: do NOT call ledger.record_refusal(scope, serialized_ref, code)",
         expect="fail", note="the card's literal probe: a denial in prose"),
    dict(id="P06", attack=2, truth="CALL",
         text="ANSWER: CALL do NOT call ledger.record_refusal(scope, serialized_ref, code)",
         expect="fail", note="the same denial forced into the CALL form"),
    dict(id="P07", attack=2, truth="CALL",
         text="never call the retry loop twice.\n" + CALL_ANSWER,
         expect="pass",
         note="asymmetry control: unrelated `never` in a preamble line"),
    dict(id="P08", attack=2, truth="CALL",
         text=CALL_ANSWER + " - avoid the retry loop.",
         expect="observe",
         note="asymmetry control on the SAME line (contract: exactly one line, "
              "nothing else)"),
    # ---- attack 3: wrong value, right shape -------------------------------
    dict(id="P09", attack=3, truth="CALL",
         text="ANSWER: ledger.record_refusal(scope=wrong, serialized_ref, code)",
         expect="fail",
         note="the card's literal probe: rejected on VALUE or on SHAPE?"),
    dict(id="P10", attack=3, truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=wrong, serialized_ref=text, "
              "code=error.code)",
         expect="fail", reason_prefix="kwarg_value_mismatch", note="value test, scope"),
    dict(id="P11", attack=3, truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=scope_name, "
              "serialized_ref=wrong, code=error.code)",
         expect="fail", reason_prefix="kwarg_value_mismatch", note="value test, ref"),
    dict(id="P12", attack=3, truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=..., serialized_ref=text, "
              "code=error.code)",
         expect="fail",
         note="OWN: the fixture elides scope; the answer may write a literal '...'"),
    # ---- attack 4: right tokens, wrong callee -----------------------------
    dict(id="P13", attack=4, truth="CALL",
         text="ANSWER: CALL ledger.write_audit(scope=scope_name, serialized_ref=text, "
              "code=error.code)",
         expect="fail", reason_prefix="callee_mismatch",
         note="a callee that occurs in a docstring only"),
    dict(id="P14", attack=4, truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text)",
         expect="fail", reason_prefix="kwarg_set_mismatch",
         note="right callee, one kwarg dropped"),
    dict(id="P15", attack=4, truth="CALL",
         text="ANSWER: CALL self.record_refusal(scope=scope_name, serialized_ref=text, "
              "code=error.code)",
         expect="fail", reason_prefix="callee_mismatch",
         note="wrong receiver, right method name"),
    # ---- baseline: the contract's own CALL form --------------------------
    dict(id="P16", attack=0, truth="CALL", text=CALL_ANSWER, expect="pass",
         note="baseline: a correct answer in the contract form"),
    # ---- attack 6: format tolerance, both ways ----------------------------
    dict(id="P17", attack=6, truth="NUM", text="ANSWER:64", expect="pass",
         note="no space after the colon"),
    dict(id="P18", attack=6, truth="NUM", text="ANSWER: 64.", expect="pass",
         note="trailing sentence period"),
    dict(id="P19", attack=6, truth="NUM", text="answer: 64", expect="observe",
         note="lowercase marker"),
    dict(id="P20", attack=6, truth="NUM",
         text="ANSWER: 64. The default is defined in resolve.py; see line 39.",
         expect="pass", note="correct answer + trailing sentence"),
    dict(id="P21", attack=6, truth="NUM", text="ANSWER: The default is 64.",
         expect="observe", note="numeric value wrapped in prose"),
    dict(id="P22", attack=6, truth="NUM", text="  ANSWER: 64", expect="observe",
         note="indented marker line"),
    dict(id="P23", attack=6, truth="NUM", text="**ANSWER: 64**", expect="observe",
         note="markdown-emphasised marker"),
    dict(id="P24", attack=6, truth="CALL", text="ANSWER: " + CALL_TEXT,
         expect="observe", note="correct call, `CALL` keyword omitted"),
    dict(id="P25", attack=6, truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=scope_name, "
              "serialized_ref='text', code=error.code)",
         expect="observe", note="same value, quoted as a string literal"),
    # ---- attack 7: the empty / absent answer -----------------------------
    dict(id="P26", attack=7, truth="NUM", text="The default budget is 64 refs.",
         expect="fail", note="prose only, no marker"),
    dict(id="P27", attack=7, truth="NUM", text="ANSWER:", expect="fail",
         note="marker with nothing after it"),
    dict(id="P28", attack=7, truth="NUM", text="ANSWER:    \n\n",
         expect="fail", note="marker with whitespace only"),
    # ---- attack 8: TEXT immunity -----------------------------------------
    dict(id="P29", attack=8, truth="NUM", text="ANSWER: TEXT the default is 64",
         expect="fail", note="TEXT must never pass, whatever its content"),
    dict(id="P30", attack=8, truth="CALL", text="ANSWER: TEXT 64", expect="fail",
         note="TEXT on a CALL checkpoint"),
    dict(id="P31", attack=8, truth="NUM", text="ANSWER: TEXT", expect="fail",
         note="empty TEXT body"),
    # ---- attack 9: numeric equivalence -----------------------------------
    dict(id="P32", attack=9, truth="NUM", text="ANSWER: 0x40", expect="observe",
         note="hex, bare"),
    dict(id="P33", attack=9, truth="NUM", text="ANSWER: NUM 0x40", expect="observe",
         note="hex, explicit NUM"),
    dict(id="P34", attack=9, truth="NUM", text="ANSWER: 64.0", expect="observe",
         note="decimal point, equal value"),
    dict(id="P35", attack=9, truth="NUM", text="ANSWER: sixty-four", expect="observe",
         note="number word"),
    dict(id="P36", attack=9, truth="NUM", text="ANSWER: 640", expect="fail",
         note="digit-prefix trap: 640 must not be read as 64"),
    # ---- attack 10: our own ----------------------------------------------
    dict(id="P37", attack=10, truth="NUM", text="ANSWER: 64.99", expect="fail",
         note="OWN: a decimal fraction of a value that is not 64"),
    dict(id="P38", attack=10, truth="NUM", text="ANSWER: NUM 64.999", expect="fail",
         note="OWN: same, explicit NUM head"),
    dict(id="P39", attack=10, truth="NUM", text="ANSWER: 64%; the previous value was 31",
         expect="pass", note="OWN: trailing prose with a stale numeral"),
    dict(id="P40", attack=10, truth="NUM", text="ANSWER: 39\nANSWER: 64",
         expect="fail", note="OWN: two ANSWER lines: a corrected answer"),
    dict(id="P41", attack=10, truth="NUM", text="ANSWER: 64\nANSWER: 64",
         expect="fail", note="OWN: a correct answer repeated is rejected"),
]


# --------------------------------------------------------------------------- #
# 3. run
# --------------------------------------------------------------------------- #
def grade_probe(probe, truth_by_kind):
    truth = truth_by_kind[probe["truth"]]
    parsed = g5.parse_answer_contract(probe["text"])
    return g5.grade_cell(truth, parsed)


def run_integration(fixture, truth):
    """Arm-level behaviour: denominators, TEXT, missing turns, row trust."""
    out = {}

    def row(turn, content, **kw):
        r = {"arm": kw.pop("arm"), "turn": turn, "content": content}
        r.update(kw)
        return r

    arms_rows = [
        row(12, "ANSWER: 64", arm="clean"),
        row(24, "ANSWER: 3", arm="clean"),
        row(46, CALL_ANSWER, arm="clean"),
        row(12, "ANSWER: 64", arm="missing_turn"),
        row(24, "ANSWER: 3", arm="missing_turn"),
        row(12, "The default budget is 64 refs.", arm="prose_only"),
        row(24, "ANSWER: 3", arm="prose_only"),
        row(46, CALL_ANSWER, arm="prose_only"),
        row(12, "ANSWER:", arm="empty_answer"),
        row(24, "ANSWER:", arm="empty_answer"),
        row(46, "ANSWER:", arm="empty_answer"),
        row(12, "ANSWER: TEXT the default is 64", arm="text_only"),
        row(24, "ANSWER: 3", arm="text_only"),
        row(46, CALL_ANSWER, arm="text_only"),
        # a row whose parsed fields disagree with its own content
        row(12, "ANSWER: TEXT the default is 64", arm="row_says_num",
            answer_kind="NUM", answer_value=64,
            answer_raw="ANSWER: TEXT the default is 64"),
        row(24, "ANSWER: 3", arm="row_says_num"),
        row(46, "ANSWER: " + CALL_TEXT, arm="row_says_num"),
    ]
    doc = g5.grade_rows(fixture, arms_rows, truth=truth)
    for arm, a in doc["arms"].items():
        out[arm] = {
            "decidable": a["decidable"],
            "passed": a["passed"],
            "checkpoint_accuracy": a["checkpoint_accuracy"],
            "text_reported": a["text_reported"],
            "verified_success": a["verified_success"],
            "failing_reasons": a["failing_reasons"],
            "verdicts": [c["verdict"] for c in doc["cells"] if c["arm"] == arm],
        }
    out["spoof_cell"] = [c for c in doc["cells"]
                         if c["arm"] == "row_says_num" and c["turn"] == 12][0]
    return out


def run_none_truth(fixture, paths):
    """Can ANY fixture declare a NONE checkpoint? (attack 5's premise)"""
    fx = json.loads(json.dumps(fixture))
    fx["checkpoints"].append({
        "id": "atk.none", "turn": 48, "expected": "NONE",
        "question": "does _refuse call ledger.write_audit?",
        "answer_spec": {"kind": "NONE", "derive": {"rule": "call_absent",
                                                   "function": "_refuse",
                                                   "attr": "write_audit"}},
    })
    try:
        g5.derive_truth(fx)
        return {"declarable": True, "error": None}
    except SystemExit as exc:
        return {"declarable": False, "error": str(exc)}
    except Exception as exc:                       # pragma: no cover
        return {"declarable": False, "error": "%s: %s" % (type(exc).__name__, exc)}


def run_docstring_check(paths):
    """Does a docstring/string occurrence ever become evidence? (attack 5)"""
    tree, sha = dv.parse_module(paths["string_only"])
    try:
        found = dv.call_inside_function(tree, "_refuse", "record_refusal")
        return {"treated_as_evidence": True, "found": found, "sha": sha}
    except SystemExit as exc:
        return {"treated_as_evidence": False, "error": str(exc), "sha": sha}


def run_none_grade_cell(truth_call):
    """Reachability of the `ANSWER: NONE` pass branch with a hand-built truth."""
    hand = {"id": "hand.none", "turn": 48, "kind": "NONE", "expected": None,
            "call_present": False, "elided_kwargs": [],
            "derivation": {"text": "hand-built truth (unreachable via derive_truth)"},
            "documented_expected": "NONE"}
    parsed = g5.parse_answer_contract("ANSWER: NONE")
    return g5.grade_cell(hand, parsed)


# --------------------------------------------------------------------------- #
# 4. table + verdict
# --------------------------------------------------------------------------- #
# Mandatory attacks: what must hold. `checks` are (probe_id, predicate-name).
# `class` is the JUDGEMENT the card asks for, not a measurement:
#   correct    - the judge does the right thing on every probe of this attack
#   limitation - defensible, but only if written down where a reader finds it
#   defect     - a wrong answer can pass, or a right answer is rejected for a reason
#                a reasonable grader would not use
MANDATORY = {
    1: {"name": "citation-numeral trap", "class": "correct",
        "must": [("P01", "pass"), ("P02", "fail")]},
    2: {"name": "negation inversion", "class": "correct",
        "must": [("P05", "fail"), ("P06", "fail"), ("P07", "pass")]},
    3: {"name": "wrong value, right shape", "class": "correct",
        "must": [("P09", "fail"), ("P10", "fail_value"), ("P11", "fail_value")]},
    4: {"name": "right tokens, wrong callee", "class": "correct",
        "must": [("P13", "fail_callee"), ("P14", "fail_kwargset"),
                 ("P15", "fail_callee")]},
    5: {"name": "docstring occurrence / NONE truth", "class": "limitation",
        "must": []},
    6: {"name": "format tolerance", "class": "correct",
        "must": [("P17", "pass"), ("P18", "pass"), ("P20", "pass")]},
    7: {"name": "empty / absent answer", "class": "limitation",
        "must": [("P26", "not_pass"), ("P27", "not_pass"), ("P28", "not_pass"),
                 ("T7", "state")]},
    8: {"name": "TEXT immunity", "class": "limitation",
        "must": [("P29", "not_pass"), ("P30", "not_pass"), ("P31", "not_pass"),
                 ("T8", "row_text_not_pass")]},
    9: {"name": "numeric equivalence", "class": "correct", "must": [("P36", "fail")]},
    10: {"name": "our own", "class": "defect",
         "must": [("P37", "fail"), ("P38", "fail")]},
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="adversarial probes for grade_v5.py")
    ap.add_argument("--json", default=os.path.join(dv.ROOT, "experiments",
                                                   "ptr-engine", "measure",
                                                   "attack-grade-v5.json"))
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args(argv)

    tmp, fixture_path, fixture, paths = build_temp_fixture()
    fixture = g5.load_fixture(fixture_path)
    truth = g5.derive_truth(fixture)
    truth_by_kind = {}
    for t in truth:
        truth_by_kind.setdefault(t["kind"], t)
    print("TEMP FIXTURE: %s" % tmp)
    for t in truth:
        print("TRUTH %-9s expected=%r" % (t["id"], t["expected"]))
    print("")

    rows, fn, fp, npass, nfail = [], 0, 0, 0, 0
    for p in PROBES:
        cell = grade_probe(p, truth_by_kind)
        verdict = cell["verdict"]
        observed = "%s/%s" % (verdict, cell["reason"])
        rows.append({
            "id": p["id"], "attack": p["attack"], "truth_kind": p["truth"],
            "answer": p["text"], "expected": p["expect"],
            "observed_verdict": verdict, "observed_reason": cell["reason"],
            "observed_parse_error": cell["answer_parse_error"],
            "observed": observed, "asserted": cell["asserted"],
            "note": p["note"],
        })
        if p["expect"] == "pass":
            npass += 1
            if verdict != "pass":
                fn += 1
                rows[-1]["counted_as"] = "FN"
        elif p["expect"] == "fail":
            nfail += 1
            if verdict == "pass":
                fp += 1
                rows[-1]["counted_as"] = "FP"
    width = max(len(p["text"].replace("\n", "\\n")) for p in PROBES)
    width = min(max(width, 20), 62)
    print("%-4s %-6s %-4s %-*s %-6s %s" % ("ID", "TRUTH", "EXP", width, "ANSWER",
                                           "OBS", "NOTE"))
    for r in rows:
        ans = r["answer"].replace("\n", "\\n")
        if len(ans) > width:
            ans = ans[:width - 1] + "~"
        print("%-4s %-6s %-4s %-*s %-6s %s" % (
            r["id"], r["truth_kind"], r["expected"], width, ans,
            r["observed_verdict"], r["note"]))
    print("")

    integration = run_integration(fixture, truth)
    none_truth = run_none_truth(fixture, paths)
    docstring = run_docstring_check(paths)
    none_cell = run_none_grade_cell(truth_by_kind["CALL"])

    # ---- mandatory-attack evaluation -----------------------------------
    by_id = {r["id"]: r for r in rows}
    results = {}

    def check(pid, pred):
        r = by_id[pid]
        if pred == "pass":
            return r["observed_verdict"] == "pass"
        if pred == "fail":
            return r["observed_verdict"] != "pass"
        if pred == "fail_value":
            return (r["observed_verdict"] == "fail"
                    and r["observed_reason"].startswith("kwarg_value_mismatch"))
        if pred == "fail_callee":
            return (r["observed_verdict"] == "fail"
                    and r["observed_reason"] == "callee_mismatch")
        if pred == "fail_kwargset":
            return (r["observed_verdict"] == "fail"
                    and r["observed_reason"] == "kwarg_set_mismatch")
        if pred == "not_pass":
            return r["observed_verdict"] != "pass"
        raise AssertionError(pred)

    for aid, spec in MANDATORY.items():
        checks = []
        for pid, pred in spec["must"]:
            if pid == "T7":
                # every non-answer 1) does not pass and 2) is not counted as fail
                # inside a *decidable* denominator.
                a = integration["missing_turn"]
                b = integration["prose_only"]
                c = integration["empty_answer"]
                ok = all(x["passed"] == 0 for x in (a, b, c))
                undecided = (a["decidable"] != a["decidable"]
                             or a["decidable"] == len(a["verdicts"]))
                checks.append({"probe": "T7", "predicate": "state",
                               "ok": bool(ok and not undecided),
                               "observed": {
                                    "missing_turn": {k: a[k] for k in
                                                     ("decidable", "passed",
                                                      "checkpoint_accuracy",
                                                      "verified_success",
                                                      "failing_reasons")},
                                    "prose_only": {k: b[k] for k in
                                                   ("decidable", "passed",
                                                    "checkpoint_accuracy",
                                                    "verified_success",
                                                    "failing_reasons")},
                                    "empty_answer": {k: c[k] for k in
                                                     ("decidable", "passed",
                                                      "checkpoint_accuracy",
                                                      "verified_success",
                                                      "failing_reasons")},
                                    "decidable_equals_all_checkpoints":
                                        a["decidable"] == len(a["verdicts"])}})
                continue
            if pid == "T8":
                sc = integration["spoof_cell"]
                ok = sc["verdict"] != "pass"
                checks.append({"probe": "T8", "predicate": "row_text_not_pass",
                               "ok": bool(ok),
                               "observed": {"verdict": sc["verdict"],
                                            "reason": sc["reason"],
                                            "answer_raw": sc["answer_raw"]}})
                continue
            ok = check(pid, pred)
            checks.append({"probe": pid, "predicate": pred, "ok": bool(ok),
                           "observed": by_id[pid]["observed"]})
        results[aid] = {"name": spec["name"], "class": spec["class"],
                        "satisfied": all(x["ok"] for x in checks),
                        "checks": checks}

    # ---- report --------------------------------------------------------
    print("FN %d / %d should-pass probes | FP %d / %d should-fail probes"
          % (fn, npass, fp, nfail))
    print("should-pass probes: %s" % ", ".join(
        r["id"] for r in rows if r["expected"] == "pass"))
    print("should-fail probes: %s" % ", ".join(
        r["id"] for r in rows if r["expected"] == "fail"))
    print("")
    print("INTEGRATION")
    for arm in ("clean", "missing_turn", "prose_only", "empty_answer", "text_only",
                "row_says_num"):
        a = integration[arm]
        print("  %-13s acc=%-4s decidable=%d text=%d verified=%s verdicts=%s reasons=%s"
              % (arm, a["checkpoint_accuracy"], a["decidable"],
                 a["text_reported"], a["verified_success"], a["verdicts"],
                 ",".join("%s:%s" % (x["id"], x["reason"])
                          for x in a["failing_reasons"]) or "-"))
    print("  spoof cell: verdict=%s reason=%s answer_raw=%r"
          % (integration["spoof_cell"]["verdict"],
             integration["spoof_cell"]["reason"],
             integration["spoof_cell"]["answer_raw"]))
    print("")
    print("NONE AS A DECLARABLE TRUTH: declarable=%s error=%r"
          % (none_truth["declarable"], none_truth["error"]))
    print("NONE PASS BRANCH (hand-built truth): verdict=%s reason=%s"
          % (none_cell["verdict"], none_cell["reason"]))
    print("DOCSTRING AS EVIDENCE: treated_as_evidence=%s (%s)"
          % (docstring["treated_as_evidence"],
             docstring.get("error") or docstring.get("found")))
    print("")
    print("MANDATORY ATTACKS")
    for aid in sorted(results):
        r = results[aid]
        bad = [c for c in r["checks"] if not c["ok"]]
        print("  %2d %-32s %-10s %s%s" % (
            aid, r["name"], r["class"].upper(),
            "SATISFIED" if r["satisfied"] else "UNSATISFIED",
            "" if r["satisfied"] else "  <- " + "; ".join(
                "%s/%s=%s" % (c["probe"], c["predicate"],
                              c["observed"] if isinstance(c["observed"], str)
                              else json.dumps(c["observed"])[:160])
                for c in bad)))
    unsatisfied = [aid for aid in sorted(results)
                   if not results[aid]["satisfied"]
                   and results[aid]["class"] != "limitation"]
    print("")
    print("UNSATISFIED (defect-class): %s" % (unsatisfied or "none"))

    doc = {
        "unit": "ATTACK-GRADE-V5",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "judge": "experiments/ptr-engine/longrun/grade_v5.py",
        "judge_sha256": dv.sha256_file(os.path.join(LONGRUN, "grade_v5.py")),
        "det_verify_sha256": dv.sha256_file(os.path.join(HERE, "det_verify.py")),
        "method": "hand-written answers graded against a temp fixture whose AST "
                  "truth is controlled by this script (absolute sources paths)",
        "inference_requests": 0,
        "truth": [{k: v for k, v in t.items() if k != "class_names"} for t in truth],
        "fn": fn, "fn_denominator": npass,
        "fp": fp, "fp_denominator": nfail,
        "probe_count": len(rows),
        "probes": rows,
        "integration": integration,
        "none_truth_declarable": none_truth,
        "none_pass_branch_hand_built": {"verdict": none_cell["verdict"],
                                        "reason": none_cell["reason"]},
        "docstring_check": docstring,
        "mandatory_attacks": {str(k): v for k, v in results.items()},
        "unsatisfied_defect_class": unsatisfied,
        "limitation_class": [aid for aid in sorted(results)
                             if results[aid]["class"] == "limitation"],
        "defect_class": [aid for aid in sorted(results)
                         if results[aid]["class"] == "defect"],
    }
    if args.json:
        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
        print("wrote %s" % args.json)
    if not args.keep_temp:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if unsatisfied else 0


if __name__ == "__main__":
    sys.exit(main())
