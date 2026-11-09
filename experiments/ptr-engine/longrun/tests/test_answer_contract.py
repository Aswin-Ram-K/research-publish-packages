#!/usr/bin/env python3
"""test_answer_contract.py - red->green guard for the v5 answer parser.

The parser is `grade_v5.parse_answer_contract` (the runner imports the same
function; there is no second implementation). Every reply below is a FIXTURE
STRING: this guard spends zero requests.

GREEN (this run, exit 0): every accept case parses to the contracted kind/value
and every reject case ends with answer_kind=None plus a parse error.

RED (`--red`, exit 1 by construction): the parser is replaced by the PRE-CHANGE
behaviour - "the text after ANSWER: is the answer" - which cannot tell a kind, a
numeral inside a citation, or a malformed line from a valid one. The same cases
must then FAIL; that failure is the proof the green run is not vacuous.

    python3 experiments/ptr-engine/longrun/tests/test_answer_contract.py         # exit 0
    python3 experiments/ptr-engine/longrun/tests/test_answer_contract.py --red  # exit 1
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import grade_v5 as g5

# (reply, kind, value-test) - value-test is a callable on answer_value
ACCEPT = [
    ("ANSWER: NUM 64", "NUM", lambda v: v == 64),
    # the card's own case: the citation numeral 39 must never win
    ("ANSWER: 64 (resolve.py:39)", "NUM", lambda v: v == 64),
    ("ANSWER: NUM 64 (resolve.py:39)", "NUM", lambda v: v == 64),
    ("ANSWER: NUM 31", "NUM", lambda v: v == 31),
    ("ANSWER: 64 refs per turn (line 39).", "NUM", lambda v: v == 64),
    ("I read #L39 first.\nANSWER: NUM 64", "NUM", lambda v: v == 64),
    ("ANSWER: NONE", "NONE", lambda v: v is None),
    ("ANSWER: TEXT the guard sits inside the recorded block", "TEXT",
     lambda v: v == "the guard sits inside the recorded block"),
    ("ANSWER: CALL ledger.record_refusal(scope=..., serialized_ref=text, code=error.code)",
     "CALL", lambda v: v["callee"] == "ledger.record_refusal"
     and v["kwargs"] == {"code": "error.code", "scope": "...", "serialized_ref": "text"}),
    ("ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
     "CALL", lambda v: v["kwargs_as_written"] == ["code", "scope", "serialized_ref"]),
    ("ANSWER: CALL resolve(ref=Reference(kind='x'), scope=Scope(name='s'))", "CALL",
     lambda v: v["callee"] == "resolve" and len(v["kwargs"]) == 2),
]

REJECT = [
    ("The default per-turn resolve budget is 64 refs.", "no_answer_line"),
    ("", "no_answer_line"),
    ("Traceback (most recent call last):\n  KeyError: 'system_prompt'", "no_answer_line"),
    ("ANSWER:", "empty_answer"),
    ("ANSWER: NUM", "empty_num"),
    ("ANSWER: MAYBE 64", "out_of_vocabulary"),
    ("ANSWER: the budget is 64", "out_of_vocabulary"),
    ("ANSWER: NONE 64", "trailing_after_none"),
    ("ANSWER: TEXT", "empty_text"),
    ("ANSWER: 64 (resolve.py:39)\nANSWER: 31", "multiple_answer_lines"),
    ("ANSWER: CALL record_refusal(1, 2)", "call_arg_not_kwarg:1"),
    ("ANSWER: CALL f(a=1, a=2)", "call_duplicate_kwarg:a"),
    ("ANSWER: CALL not a call", "call_not_parsable"),
]


def naive_pre_change(text):
    """The behaviour BEFORE this card: no kind, no citation rule, no validation."""
    out = {"answer_kind": None, "answer_value": None, "answer_raw": None,
           "answer_parse_error": None, "answer_turn": False, "detail": {}}
    if "ANSWER:" in text:
        out["answer_value"] = text.split("ANSWER:")[-1].strip()
        out["answer_kind"] = "TEXT"
    return out


def run(parse, verbose=True):
    failures = []

    def check(name, ok, detail=""):
        if verbose:
            print(("  GREEN %s" if ok else "  RED   %s") % name + ("" if ok else "  <- " + detail))
        if not ok:
            failures.append(name)

    for i, (text, kind, value_ok) in enumerate(ACCEPT):
        got = parse(text)
        ok = (got["answer_kind"] == kind and got["answer_parse_error"] is None
              and value_ok(got["answer_value"]))
        check("accept[%d] %r -> %s" % (i, text[:44], kind), ok,
              "kind=%r value=%r err=%r" % (got["answer_kind"], got["answer_value"],
                                           got["answer_parse_error"]))
    for i, (text, err) in enumerate(REJECT):
        got = parse(text)
        ok = got["answer_kind"] is None and got["answer_parse_error"] == err
        check("reject[%d] %r -> %s" % (i, text[:44], err), ok,
              "kind=%r err=%r" % (got["answer_kind"], got["answer_parse_error"]))
    # the citation rule is det_verify's, not a weaker copy: 39 is never the value
    got = parse("ANSWER: 64 (resolve.py:39)")
    check("citation numeral is not the value",
          isinstance(got["answer_value"], int) and got["answer_value"] == 64,
          "value=%r" % (got["answer_value"],))
    check("citation span is reported by det_verify",
          bool(got["detail"].get("citation_spans")), "no citation_spans in detail")
    return failures


def main(argv):
    red = "--red" in argv
    parse = naive_pre_change if red else g5.parse_answer_contract
    label = "PRE-CHANGE parser (red mode)" if red else "grade_v5.parse_answer_contract"
    print("parser: %s" % label)
    failures = run(parse)
    total = len(ACCEPT) + len(REJECT) + 2
    # LABEL FIX (WIRE-CLIENT): this line used to print the COMPLEMENT of the failure count
    # while reading "FAILED", so `--red` printed "0/26 assertions FAILED" beside a header
    # saying 26/26 fail.  A reader could mistake that for a vacuous guard.  Count the
    # failures, and label the pass case as a pass.
    if failures:
        print("\n%d/%d assertions FAILED" % (len(failures), total))
    else:
        print("\n%d/%d assertions passed" % (total, total))
    if red:
        print("RED CONFIRMED: the pre-change parser fails %d/%d assertions - the guard is "
              "not vacuous" % (len(failures), total))
        return 1 if failures else 0
    if failures:
        print("GREEN FAILED: %s" % ", ".join(failures))
        return 1
    print("GREEN: contract parse accept/reject is red->green (run --red to see it fail)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
