#!/usr/bin/env python3
"""test_grade_v6_derive.py - the v6 fixture must be GRADEABLE, item by item.

Unit GRADE-V6-DERIVE. The gate passed LR-01.v6.json (12 decidable checkpoints) but
only 8 of the 12 could be turned into truth: three `NONE` items aborted with
`fixture_truth_mismatch: <id> has no usable answer_spec` and `cp.10.t36`
(`call_at_line`) died with `KeyError: 'function'`. Every assertion below is a guard
on that seam:

(a) COMPLETE     - all 12 checkpoints derive a truth; each grades `pass` on its own
                   expected answer and `fail` on a wrong one.
(b) NONE red     - a forbidden attribute that IS called inside the named function
                   derives `call_present=True` and grades `fail` with a reason that
                   NAMES the attribute (it must not abort).
(c) LINE red     - a `call_at_line` spec whose line holds a different callee is
                   refused with the named SystemExit, never a bare KeyError.
(d) TEXT         - still never passes; an unknown spec kind names id + kind + file;
                   the 8 items that graded before this change derive unchanged.
(e) MIRROR       - score_longrun's acceptance path grades all 12, not just 3.

Run:  python3 -m pytest experiments/ptr-engine/longrun/tests/test_grade_v6_derive.py -q
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
for _p in (LONGRUN, os.path.join(os.path.dirname(LONGRUN), "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v5                                                   # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v6.json")

V6_IDS = ["cp.3.t06", "cp.4.t08", "cp.0.t12", "cp.5.t14", "cp.6.t18", "cp.7.t20",
          "cp.1.t24", "cp.8.t26", "cp.9.t32", "cp.10.t36", "cp.11.t42", "cp.2.t46"]

# The 8 items the pre-change grader could already derive, frozen with their exact
# pre-change `expected` values. A change to any of them is a regression, not a fix.
PRE_CHANGE = {
    "cp.3.t06": {"callee": "ledger.record_resolution",
                 "kwargs": {"block_size": "scope.block()",
                            "bytes_appended": "len(presented.encode('utf-8'))",
                            "entry_text": "entry.text", "scope": "scope.name",
                            "serialized_ref": "presented"},
                 "kwargs_as_written": ["scope", "serialized_ref", "bytes_appended",
                                       "block_size", "entry_text"]},
    "cp.4.t08": {"callee": "scope.block", "kwargs": {}, "kwargs_as_written": []},
    "cp.0.t12": 64,
    "cp.6.t18": 6,
    "cp.1.t24": 31,
    "cp.8.t26": 5,
    "cp.9.t32": 2,
    "cp.2.t46": {"callee": "ledger.record_refusal",
                 "kwargs": {"code": "error.code", "scope": "scope_name",
                            "serialized_ref": "text"},
                 "kwargs_as_written": ["scope", "serialized_ref", "code"]},
}


def load():
    with open(FIXTURE, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def one(fixture, cid):
    """A one-checkpoint fixture carrying the same sources (the unit's own probe)."""
    cps = [c for c in fixture["checkpoints"] if c.get("id") == cid]
    assert cps, cid
    return dict(fixture, checkpoints=cps)


def answer_for(truth):
    """The contract line that asserts the DERIVED truth."""
    if truth["kind"] == "NUM":
        return "ANSWER: NUM %d" % truth["expected"]
    if truth["kind"] == "NONE":
        return "ANSWER: NONE"
    exp = truth["expected"]
    kwargs = ", ".join("%s=%s" % (k, v) for k, v in sorted(exp["kwargs"].items()))
    return "ANSWER: CALL %s(%s)" % (exp["callee"], kwargs)


def wrong_for(truth):
    """A contract line that asserts something the source contradicts."""
    if truth["kind"] == "NUM":
        return "ANSWER: NUM %d" % (int(truth["expected"]) + 1)
    if truth["kind"] == "NONE":
        return "ANSWER: CALL definitely_not_called()"
    return "ANSWER: CALL wrong_callee()"


def grade(truth, text):
    parsed = grade_v5.parse_answer_contract(text)
    assert parsed["answer_parse_error"] is None, (text, parsed["answer_parse_error"])
    return grade_v5.grade_cell(truth, parsed)


# --------------------------------------------------------------------------- (a)
def test_all_12_checkpoints_derive_truth():
    truth = grade_v5.derive_truth(load())
    assert [t["id"] for t in truth] == V6_IDS
    assert len(truth) == 12
    kinds = {t["id"]: t["kind"] for t in truth}
    assert kinds["cp.5.t14"] == kinds["cp.7.t20"] == kinds["cp.11.t42"] == "NONE"
    assert kinds["cp.10.t36"] == "CALL"
    for t in truth:
        assert t["derivation"], t["id"]


def test_all_12_grade_pass_on_own_answer_and_fail_on_wrong():
    truth = grade_v5.derive_truth(load())
    for t in truth:
        ok = grade(t, answer_for(t))
        assert ok["verdict"] == "pass", (t["id"], ok["reason"])
        bad = grade(t, wrong_for(t))
        assert bad["verdict"] == "fail", (t["id"], bad["verdict"], bad["reason"])


def test_none_items_derive_the_boolean_absence():
    truth = {t["id"]: t for t in grade_v5.derive_truth(load())}
    for cid, attr, func in (("cp.5.t14", "record_refusal", "resolve"),
                            ("cp.7.t20", "resolved_count", "_refuse"),
                            ("cp.11.t42", "block", "_refuse")):
        t = truth[cid]
        assert t["expected"] == "NONE"
        assert t["call_present"] is False, cid
        assert t["forbidden_attr"] == attr and t["forbidden_function"] == func
        assert "absent" in t["derivation"]["text"]


def test_call_at_line_derives_callee_at_the_pinned_line():
    t = {x["id"]: x for x in grade_v5.derive_truth(load())}["cp.10.t36"]
    assert t["expected"]["callee"] == "ledger.resolved_count"
    assert t["derivation"]["line"] == 141
    assert t["derivation"]["file"].endswith("resolve.py")


# --------------------------------------------------------------------------- (b)
def test_red_none_item_whose_attribute_is_called_fails_and_names_it():
    """RED half of the NONE branch: `_refuse` DOES call ledger.record_refusal."""
    fixture = one(load(), "cp.5.t14")
    fixture["checkpoints"][0]["answer_spec"]["derive"].update(
        function="_refuse", attr="record_refusal")
    truth = grade_v5.derive_truth(fixture)[0]          # must NOT abort
    assert truth["kind"] == "NONE"
    assert truth["call_present"] is True
    assert truth["derivation"]["call_lines"] == [69]
    cell = grade(truth, "ANSWER: NONE")
    assert cell["verdict"] == "fail", cell
    assert "record_refusal" in cell["reason"], cell["reason"]
    assert "_refuse" in cell["reason"], cell["reason"]


def test_red_none_missing_spec_fields_names_item_kind_and_file():
    fixture = one(load(), "cp.7.t20")
    fixture["checkpoints"][0]["answer_spec"] = {"kind": "NONE", "derive": {"rule":
                                                "no_attr_call_inside_function"}}
    try:
        grade_v5.derive_truth(fixture)
    except SystemExit as exc:
        msg = str(exc.code)
        for needle in ("cp.7.t20", "NONE", "resolve.py", "function"):
            assert needle in msg, msg
    else:                                              # pragma: no cover
        raise AssertionError("a NONE spec without function/attr derived a truth")


# --------------------------------------------------------------------------- (c)
def test_red_call_at_line_with_a_different_callee_is_refused_by_name():
    """RED half of call_at_line: line 69 holds record_refusal, not resolved_count."""
    fixture = one(load(), "cp.10.t36")
    fixture["checkpoints"][0]["answer_spec"]["derive"]["line"] = 69
    try:
        grade_v5.derive_truth(fixture)
    except SystemExit as exc:
        msg = str(exc.code)
        for needle in ("cp.10.t36", "call_at_line", "ledger.resolved_count",
                       "resolve.py:69"):
            assert needle in msg, msg
    except KeyError as exc:                            # pragma: no cover
        raise AssertionError("call_at_line raised a bare KeyError: %r" % (exc,))
    else:                                              # pragma: no cover
        raise AssertionError("a line holding a different callee derived a truth")


def test_call_at_line_accepts_a_declared_callee_override():
    fixture = one(load(), "cp.10.t36")
    fixture["checkpoints"][0]["answer_spec"]["derive"].update(
        line=69, callee="ledger.record_refusal")
    fixture["checkpoints"][0]["expected"] = ("ledger.record_refusal(scope=scope_name, "
                                             "serialized_ref=text, code=error.code)")
    t = grade_v5.derive_truth(fixture)[0]
    assert t["expected"]["callee"] == "ledger.record_refusal"
    assert t["expected"]["kwargs"] == {"scope": "scope_name", "serialized_ref": "text",
                                       "code": "error.code"}


# --------------------------------------------------------------------------- (d)
def test_text_never_passes():
    truth = {t["id"]: t for t in grade_v5.derive_truth(load())}
    for cid in V6_IDS:
        cell = grade(truth[cid], "ANSWER: TEXT 64 because I read it in resolve.py")
        assert cell["verdict"] != "pass", cid
        assert cell["reason"] == "text_not_auto_passed", cell["reason"]


def test_unknown_spec_kind_names_item_kind_and_file():
    fixture = one(load(), "cp.0.t12")
    fixture["checkpoints"][0]["answer_spec"] = {"kind": "PROSE",
                                                "derive": {"rule": "vibes",
                                                           "file": "experiments/ptr-engine/"
                                                                   "ptr_engine/resolve.py"}}
    try:
        grade_v5.derive_truth(fixture)
    except SystemExit as exc:
        msg = str(exc.code)
        for needle in ("cp.0.t12", "PROSE", "resolve.py"):
            assert needle in msg, msg
    else:                                              # pragma: no cover
        raise AssertionError("an unknown answer_spec kind derived a truth")


def test_call_spec_missing_function_is_not_a_keyerror():
    fixture = one(load(), "cp.3.t06")
    fixture["checkpoints"][0]["answer_spec"]["derive"].pop("function")
    try:
        grade_v5.derive_truth(fixture)
    except SystemExit as exc:
        msg = str(exc.code)
        for needle in ("cp.3.t06", "CALL", "function"):
            assert needle in msg, msg
    except KeyError as exc:                            # pragma: no cover
        raise AssertionError("missing 'function' raised a bare KeyError: %r" % (exc,))
    else:                                              # pragma: no cover
        raise AssertionError("a CALL spec without 'function' derived a truth")


def test_the_8_previously_grading_items_are_unchanged():
    truth = {t["id"]: t for t in grade_v5.derive_truth(load())}
    assert set(PRE_CHANGE) <= set(truth)
    for cid, expected in PRE_CHANGE.items():
        assert truth[cid]["expected"] == expected, (cid, truth[cid]["expected"])


# --------------------------------------------------------------------------- (e)
class _Checks(object):
    """The slice of score_longrun.Checks this test needs."""

    def __init__(self):
        self.rows = []

    def add(self, check_id, kind, turn, verdict, detail, required=True):
        self.rows.append({"id": check_id, "kind": kind, "turn": turn,
                          "verdict": verdict, "detail": detail,
                          "required": required})
        return verdict


def _mirror(answers):
    import score_longrun
    fixture = load()
    truth = grade_v5.derive_truth(fixture)
    run = {"turns": {t["turn"]: {"_content": answers.get(t["id"], answer_for(t))}
                     for t in truth}}
    checks = _Checks()
    score_longrun.mirror_answer_contract(fixture, run, checks)
    return checks.rows


def test_mirror_grades_all_12_not_just_three():
    rows = _mirror({})
    assert len(rows) == 12, [r["id"] for r in rows]
    assert {r["verdict"] for r in rows} == {"pass"}
    assert [r["turn"] for r in rows] == [t["turn"] for t in grade_v5.derive_truth(load())]


def test_mirror_red_half_a_wrong_answer_fails():
    rows = {r["id"]: r for r in _mirror({"cp.5.t14": "ANSWER: CALL ledger.record_refusal()",
                                         "cp.10.t36": "ANSWER: NUM 7"})}
    assert rows["acc.derive.cp.5.t14"]["verdict"] == "fail"
    assert rows["acc.derive.cp.10.t36"]["verdict"] == "fail"
    assert rows["acc.derive.cp.0.t12"]["verdict"] == "pass"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([os.path.abspath(__file__), "-q"]))
