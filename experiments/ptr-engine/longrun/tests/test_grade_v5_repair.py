"""Unit GRADE-V5-REPAIR - red->green tests for the three defects the independent
attack ATTACK-GRADE-V5 (41 probes) measured in grade_v5.py.

    GREEN: python3 -m pytest experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py -q
    RED:   GRADE_V5_MODULE=<pre-repair copy of grade_v5.py> python3 -m pytest <same file> -q

The red run proves each test measures the defect and not the repair: the same file
is executed against a pre-repair copy of the judge.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
TOOLS = os.path.join(os.path.dirname(LONGRUN), "tools")


def _load():
    for p in (LONGRUN, TOOLS):
        if p not in sys.path:
            sys.path.insert(0, p)
    src = os.environ.get("GRADE_V5_MODULE")
    if src:
        spec = importlib.util.spec_from_file_location("grade_v5_under_test", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    import grade_v5 as mod
    return mod


g5 = _load()


def truth(kind="NUM", expected=64, turn=1, cid="t.num"):
    return {"id": cid, "turn": turn, "kind": kind, "expected": expected,
            "derivation": {"text": "hand-built truth (no file I/O)"}}


def verdict(text, t=None):
    return g5.grade_cell(t or truth(), g5.parse_answer_contract(text))


# ---------------------------------------------------------------- (a) TASK 1
class TestTask1NumIsIntegerEquality:
    """NUM used to truncate: 64.99 and NUM 64.999 both graded 64 -> pass."""

    def test_exact_integer_passes(self):
        assert verdict("ANSWER: 64")["verdict"] == "pass"
        assert verdict("ANSWER: NUM 64")["verdict"] == "pass"

    def test_sentence_period_is_not_a_fraction(self):
        assert verdict("ANSWER: 64.")["verdict"] == "pass"
        assert verdict("ANSWER: 64 (resolve.py:39)")["verdict"] == "pass"

    def test_decimal_fraction_fails_and_names_the_value(self):
        cell = verdict("ANSWER: 64.99")
        assert cell["verdict"] == "fail", cell
        assert "64.99" in cell["reason"] and cell["reason"].startswith("num_not_integer")
        cell = verdict("ANSWER: NUM 64.999")
        assert cell["verdict"] == "fail"
        assert "64.999" in cell["reason"]

    def test_integral_decimal_point_fails_and_names_it(self):
        cell = verdict("ANSWER: 64.0")
        assert cell["verdict"] == "fail"
        assert "64.0" in cell["reason"], cell

    def test_other_non_integral_forms_are_rejected(self):
        for text in ("ANSWER: 0x40", "ANSWER: NUM 0x40", "ANSWER: six",
                     "ANSWER: sixty-four", "ANSWER: 640"):
            assert verdict(text)["verdict"] != "pass", text

    def test_rule_is_stated_in_the_module(self):
        assert "integer" in g5.parse_answer_contract("ANSWER: 64")["detail"]["rule"]


# ---------------------------------------------------------------- (b) TASK 2
class TestTask2RowCannotGradeItself:
    """A row whose content is prose but whose fields claim num_equal/64 passed."""

    SPOOF = {"arm": "a", "turn": 1, "content": "ANSWER: TEXT the default is 64",
             "answer_kind": "NUM", "answer_value": 64,
             "answer_raw": "ANSWER: TEXT the default is 64"}

    def test_fields_disagreeing_with_content_is_a_hard_error_naming_both(self):
        try:
            g5._parsed_from_row(dict(self.SPOOF))
        except g5.RowFieldDisagreement as exc:
            msg = str(exc)
            assert "NUM" in msg and "TEXT" in msg, msg
            assert "64" in msg
            assert exc.row_fields["answer_kind"] == "NUM"
            assert exc.content_parse["answer_kind"] == "TEXT"
        else:
            raise AssertionError("a spoofing row was accepted without a hard error")

    def test_spoofing_row_is_non_pass_in_grade_rows(self):
        doc = g5.grade_rows({"task_id": "x"}, [dict(self.SPOOF)],
                            truth=[truth()])
        cell = doc["cells"][0]
        assert cell["verdict"] != "pass", cell
        assert cell["verdict"] == "fail"
        assert cell["reason"] == "row_fields_disagree_with_content"
        assert "NUM" in cell["row_field_conflict"]["error"]
        assert "TEXT" in cell["row_field_conflict"]["error"]
        assert doc["arms"]["a"]["passed"] == 0

    def test_content_alone_decides_when_fields_agree(self):
        row = {"arm": "a", "turn": 1, "content": "ANSWER: 64",
               "answer_kind": "NUM", "answer_value": 64,
               "answer_raw": "ANSWER: 64"}
        doc = g5.grade_rows({"task_id": "x"}, [row], truth=[truth()])
        assert doc["cells"][0]["verdict"] == "pass"
        assert doc["cells"][0]["answer_parse_detail"]["source"] == "content"

    def test_fields_may_not_supply_an_answer_to_prose(self):
        row = {"arm": "a", "turn": 1, "content": "The default is 64 refs.",
               "answer_kind": "NUM", "answer_value": 64,
               "answer_parse_error": None}
        doc = g5.grade_rows({"task_id": "x"}, [row], truth=[truth()])
        assert doc["cells"][0]["verdict"] != "pass"


# ---------------------------------------------------------------- (c) TASK 3
class TestTask3NonAnswersAreUndecidable:
    """Empty/absent answers landed in `fail` and therefore in the denominator."""

    def test_each_non_answer_form_is_undecidable_with_its_reason(self):
        cases = [("", "no_answer_line"),
                 ("The default budget is 64 refs.", "prose_only"),
                 ("ANSWER:", "empty_answer"),
                 ("ANSWER:    \n\n", "empty_answer"),
                 ("ANSWER: six", "out_of_vocabulary")]
        for text, reason in cases:
            cell = verdict(text)
            assert cell["verdict"] == "undecidable", (text, cell)
            assert cell["reason"] == reason, (text, cell)

    def test_no_answer_line_in_content_is_undecidable(self):
        cell = g5.grade_cell(truth(), g5.parse_answer_contract(None))
        assert cell["verdict"] == "undecidable"

    def test_accuracy_denominator_excludes_undecidable(self):
        doc = g5.grade_rows(
            {"task_id": "x"},
            [{"arm": "a", "turn": 1, "content": "ANSWER: 64"},
             {"arm": "a", "turn": 2, "content": "ANSWER:"}],
            truth=[truth(turn=1), truth(expected=3, turn=2, cid="t.count")])
        arm = doc["arms"]["a"]
        assert arm["decidable"] == 1, arm
        assert arm["checkpoint_accuracy"] == "1/1", arm
        assert arm["undecidable"] == 1 and arm["undecidable_reasons"] == ["empty_answer"]
        assert arm["passed"] + arm["failed"] == arm["decidable"]
        assert arm["verified_success"] is False

    def test_missing_turn_stays_a_decidable_fail(self):
        doc = g5.grade_rows({"task_id": "x"},
                            [{"arm": "a", "turn": 1, "content": "ANSWER: 64"}],
                            truth=[truth(turn=1), truth(expected=3, turn=2, cid="c2")])
        arm = doc["arms"]["a"]
        assert arm["decidable"] == 2 and arm["missing"] == 1
        assert doc["cells"][1]["reason"] == "turn_missing"


# ---------------------------------------------------------------- (d) TASK 3
class TestTask4WrongAnswersStillFail:
    """The repair must not launder a wrong-but-well-formed answer into undecidable."""

    def test_wrong_integer_fails(self):
        assert verdict("ANSWER: 65")["verdict"] == "fail"
        assert verdict("ANSWER: NUM 65")["verdict"] == "fail"

    def test_wrong_call_fails(self):
        t = truth(kind="CALL", expected={"callee": "ledger.record_refusal",
                                         "kwargs": {"scope": "s", "code": "c"}})
        cell = verdict("ANSWER: CALL ledger.record_refusal(scope=s, code=WRONG)", t)
        assert cell["verdict"] == "fail"

    def test_text_answer_is_not_a_pass(self):
        assert verdict("ANSWER: TEXT 64")["verdict"] == "text"


# ---------------------------------------------------------------- (e) TASK 4
class TestTask5Derive12Unchanged:
    """GRADE-V6-DERIVE's 12 items must still derive, and correct answers still pass."""

    def _fixture(self):
        path = os.path.join(REPO, "experiments", "ptr-engine", "longrun",
                            "tasks-v5", "runtime-v5", "LR-01.v6.json")
        with open(path, "rb") as fh:
            return json.loads(fh.read().decode("utf-8"))

    @staticmethod
    def answer_for(t):
        if t["kind"] == "NONE":
            return "ANSWER: NONE"
        if t["kind"] == "NUM":
            return "ANSWER: NUM %d" % int(t["expected"])
        exp = t["expected"]
        if isinstance(exp, dict):
            args = ", ".join("%s=%s" % (k, v) for k, v in sorted(exp["kwargs"].items()))
            return "ANSWER: CALL %s(%s)" % (exp["callee"], args)
        return "ANSWER: %s" % exp

    def test_twelve_items_derive_and_all_correct_answers_pass(self):
        fixture = self._fixture()
        truth = g5.derive_truth(fixture)
        assert len(truth) == 12, [t["id"] for t in truth]
        rows = [{"arm": "correct", "turn": t["turn"],
                 "content": self.answer_for(t)} for t in truth]
        doc = g5.grade_rows(fixture, rows, truth=truth)
        bad = [(c["id"], c["verdict"], c["reason"]) for c in doc["cells"]
               if c["verdict"] != "pass"]
        assert not bad, bad
        assert doc["arms"]["correct"]["checkpoint_accuracy"] == "12/12"
