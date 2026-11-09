#!/usr/bin/env python3
"""test_grade_v5.py - red->green guard for grade_v5 (ANSWER-CONTRACT v1).

Every model reply here is a FIXTURE STRING and every expected value is derived from
the pinned source tree by AST (`grade_v5.derive_truth`); no request is made and no
row file is written.

GREEN (exit 0): the cells below are decided exactly as the card requires -
  * NUM by integer equality (and a trailing citation is not the value);
  * CALL by exact callee, exact kwarg NAME SET, exact value text;
  * kwargs in the WRONG ORDER pass (order is a formatting rule, not a truth rule);
  * NONE against a checkpoint whose call exists in the source fails;
  * a prose answer is answer_kind=null -> fail/answer_not_contract;
  * TEXT is reported separately and never counted as a pass.

RED (`--red`, exit 1 by construction): the CALL/NONE decisions are stubbed to
"pass" (the pre-change posture: the mention is enough). Every wrong-callee,
wrong-kwarg and NONE case must then FAIL, which proves the green run is not vacuous.

    python3 experiments/ptr-engine/longrun/tests/test_grade_v5.py         # exit 0
    python3 experiments/ptr-engine/longrun/tests/test_grade_v5.py --red   # exit 1
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import grade_v5 as g5

FIXTURE = os.path.join(LONGRUN, "tasks-v5/runtime-v5/LR-01.v5.json")

GOOD_CALL = ("ANSWER: CALL ledger.record_refusal(scope=..., serialized_ref=text, "
             "code=error.code)")


def fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def rows(answers, arm="contract"):
    """answers: {turn: content} -> the rows grade_v5 reads (runner-shaped)."""
    return [{"arm": arm, "task_id": "LR-01", "turn": t, "content": c}
            for t, c in sorted(answers.items())]


def grade(answers, arm="contract"):
    doc = g5.grade_rows(fixture(), rows(answers, arm))
    return {c["turn"]: c for c in doc["cells"]}, doc["arms"][arm]


def full(n12="ANSWER: NUM 64", n24="ANSWER: NUM 31", n46=GOOD_CALL):
    return {12: n12, 24: n24, 46: n46}


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def truth_is_derived_from_source():
    """The expected values are AST facts, each with a file:line derivation."""
    truth = {t["turn"]: t for t in g5.derive_truth(fixture())}
    assert truth[12]["expected"] == 64, truth[12]
    assert truth[24]["expected"] == 31, truth[24]
    assert truth[46]["expected"]["callee"] == "ledger.record_refusal", truth[46]
    assert sorted(truth[46]["expected"]["kwargs"]) == ["code", "scope", "serialized_ref"]
    assert truth[12]["derivation"]["file"].endswith("ptr_engine/resolve.py")
    assert truth[12]["derivation"]["line"] == 39
    assert truth[24]["derivation"]["ast"] == "ast.ClassDef"
    assert truth[46]["derivation"]["ast"].startswith("ast.Call inside _refuse")
    assert truth[46]["derivation"]["line"] > 0


@case
def all_correct_passes():
    cells, arm = grade(full())
    assert [c["verdict"] for c in cells.values()] == ["pass", "pass", "pass"], cells
    assert arm["checkpoint_accuracy"] == "3/3" and arm["verified_success"], arm
    for c in cells.values():
        assert c["asserted"] is not None and c["expected"] is not None and c["derivation"]


@case
def trailing_citation_is_not_the_value():
    cells, _ = grade(full(n12="ANSWER: 64 (resolve.py:39)"))
    assert cells[12]["verdict"] == "pass" and cells[12]["asserted"] == 64, cells[12]
    assert cells[12]["reason"] == "num_equal"


@case
def wrong_numeral_fails():
    cells, _ = grade(full(n12="ANSWER: NUM 63"))
    assert cells[12]["verdict"] == "fail" and cells[12]["reason"] == "num_mismatch", cells[12]


@case
def wrong_callee_fails():
    cells, _ = grade(full(n46="ANSWER: CALL ledger.write_audit(scope=..., "
                              "serialized_ref=text, code=error.code)"))
    assert cells[46]["verdict"] == "fail" and cells[46]["reason"] == "callee_mismatch", cells[46]


@case
def extra_kwarg_fails():
    cells, _ = grade(full(n46="ANSWER: CALL ledger.record_refusal(scope=..., "
                              "serialized_ref=text, code=error.code, grant=scope)"))
    assert cells[46]["reason"] == "kwarg_set_mismatch", cells[46]
    assert cells[46]["extra_kwargs"] == ["grant"], cells[46]


@case
def missing_kwarg_fails():
    cells, _ = grade(full(n46="ANSWER: CALL ledger.record_refusal(scope=..., code=error.code)"))
    assert cells[46]["reason"] == "kwarg_set_mismatch", cells[46]
    assert cells[46]["missing_kwargs"] == ["serialized_ref"], cells[46]


@case
def wrong_kwarg_value_fails():
    cells, _ = grade(full(n46="ANSWER: CALL ledger.record_refusal(scope=..., "
                              "serialized_ref=ref, code=error.code)"))
    assert cells[46]["reason"] == "kwarg_value_mismatch:serialized_ref", cells[46]


@case
def kwargs_in_wrong_order_pass():
    """ORDER IS A FORMATTING RULE, NOT A TRUTH RULE -> pass (decided, and tested)."""
    cells, arm = grade(full(n46="ANSWER: CALL ledger.record_refusal(serialized_ref=text, "
                                 "scope=..., code=error.code)"))
    assert cells[46]["verdict"] == "pass" and cells[46]["reason"] == "call_equal", cells[46]
    assert cells[46]["kwargs_as_written"] == ["serialized_ref", "scope", "code"]
    assert arm["verified_success"]


@case
def none_against_existing_call_fails():
    cells, _ = grade(full(n46="ANSWER: NONE"))
    assert cells[46]["verdict"] == "fail", cells[46]
    assert cells[46]["reason"] == "none_but_call_exists", cells[46]


@case
def none_against_a_number_fails():
    cells, _ = grade(full(n12="ANSWER: NONE"))
    assert cells[12]["reason"] == "none_contradicted_by_source", cells[12]


@case
def prose_answer_is_not_contract():
    cells, arm = grade(full(n46="It calls record_refusal with scope, serialized_ref and code."))
    assert cells[46]["verdict"] == "fail", cells[46]
    assert cells[46]["reason"] == "answer_not_contract", cells[46]
    assert cells[46]["answer_kind"] is None and cells[46]["answer_parse_error"]
    assert not arm["verified_success"]


@case
def text_is_never_a_pass():
    cells, arm = grade(full(n12="ANSWER: TEXT 64 refs per turn"))
    assert cells[12]["verdict"] == "text", cells[12]
    assert cells[12]["reason"] == "text_not_auto_passed", cells[12]
    assert arm["text_reported"] == 1 and not arm["verified_success"], arm
    assert arm["checkpoint_accuracy"] == "2/3", arm


@case
def wrong_kind_fails():
    cells, _ = grade(full(n12="ANSWER: CALL DEFAULT_MAX_REFS()"))
    assert cells[12]["verdict"] == "fail" and cells[12]["reason"].startswith("kind_mismatch"), \
        cells[12]


@case
def runner_parsed_fields_are_used():
    """A runner row that already carries the parse is graded from the row, not re-parsed."""
    r = rows(full())
    r[0].update({"answer_turn": True, "answer_kind": "NUM", "answer_value": 64,
                 "answer_raw": "ANSWER: NUM 64", "answer_parse_error": None,
                 "content": "unparsable prose the runner already rejected"})
    doc = g5.grade_rows(fixture(), r)
    cell = {c["turn"]: c for c in doc["cells"]}[12]
    assert cell["verdict"] == "pass" and cell["answer_parse_detail"]["source"] == "row", cell


@case
def missing_turn_fails():
    doc = g5.grade_rows(fixture(), rows({12: "ANSWER: NUM 64"}))
    cells = {c["turn"]: c for c in doc["cells"]}
    assert cells[24]["reason"] == "turn_missing" and cells[46]["reason"] == "turn_missing", cells


_ORIGINAL_GRADE_CELL = g5.grade_cell


def lenient_grade_cell(truth, parsed):
    """RED mutant: the pre-change posture - a mention is enough, NONE accepted."""
    cell = _ORIGINAL_GRADE_CELL(truth, parsed)
    if parsed.get("answer_kind") in ("CALL", "NONE"):
        cell.update(verdict="pass", reason="ok")
    return cell


def run(mutant=False, verbose=True):
    original = g5.grade_cell
    if mutant:
        g5.grade_cell = lenient_grade_cell
    failures = []
    try:
        for fn in CASES:
            try:
                fn()
                if verbose:
                    print("  GREEN %s" % fn.__name__)
            except AssertionError as exc:
                failures.append(fn.__name__)
                if verbose:
                    print("  RED   %s  <- %s" % (fn.__name__, str(exc)[:200]))
    finally:
        g5.grade_cell = original
    return failures


def main(argv):
    red = "--red" in argv
    print("grader: grade_v5 (fixture %s)" % os.path.relpath(FIXTURE, ROOT))
    failures = run(mutant=red)
    total = len(CASES)
    print("\n%d/%d guard cases %s" % (total - len(failures), total,
                                      "FAILED" if failures else "passed"))
    if red:
        print("RED CONFIRMED: with CALL/NONE stubbed to pass, %d/%d cases fail - the guard is "
              "not vacuous" % (len(failures), total))
        return 1 if failures else 0
    if failures:
        print("GREEN FAILED: %s" % ", ".join(failures))
        return 1
    print("GREEN: value-level grading is red->green (run --red to see it fail)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
