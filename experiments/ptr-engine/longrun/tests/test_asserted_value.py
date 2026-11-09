#!/usr/bin/env python3
"""PROSE-VALUE-METRIC red->green: the widened extractor must read prose, and
must refuse everything that is not an assertion.

The suite is deliberately *not* tolerant: it asserts exact `(value, form, span)`
tuples and exact `None`s. Neuter `asserted_value()` to `return None` and the
three positive cases go red (that is the point of a red->green). Re-widen it
carelessly -- accept `#L39`, a range endpoint, a byte size, a bare tool name --
and the rejection cases go red instead.
"""

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
MEASURE = Path(__file__).resolve().parents[2] / "measure"
sys.path.insert(0, str(TOOLS))

import asserted_value as av  # noqa: E402


# ---------------------------------------------------------------------------
# red -> green: prose that states a value must be read
# ---------------------------------------------------------------------------
def test_prose_is_reads_64():
    """GREEN case 1: an asserted 64 in prose, no `ANSWER:` line at all."""
    text = "The default per-turn resolve budget is **64** refs, set in the module."
    got = av.asserted_value(text)
    assert got is not None, "prose asserting 64 must not be read as no-answer"
    value, form, span = got
    assert value == "64"
    assert form in ("is", "default_of")
    assert text[span[0]:span[1]] == "64"


def test_prose_equals_and_backtick_forms():
    assert av.asserted_value("The budget `64` is the cap.")[0] == "64"
    assert av.asserted_value("max_refs = 64")[0] == "64"
    assert av.asserted_value("It equals 64 here.")[0] == "64"
    assert av.asserted_value("The default of 64 applies.")[0] == "64"


def test_wrong_value_1_is_read_as_1():
    """GREEN case 3: a WRONG value must still be read, so it can be scored wrong."""
    text = ("The default per-turn resolve budget is **1 ref** \u2014 this is derivable "
            "from `refs/experiments/ptr-engine/ptr_engine/resolve.py#L39`,")
    value, form, span = av.asserted_value(text)
    assert value == "1", "a stated wrong value must be gradable, not discarded"
    assert text[span[0]:span[1]] == "1"
    assert av.compare(value, form, "NUM", 64) == "mismatch"


def test_leading_line_and_whole_turn_forms():
    assert av.asserted_value("2000")[0] == "2000"
    assert av.asserted_value("2000")[1] == "leading_bare"
    got = av.asserted_value("7\n\nEvidence: `errors.py` defines eight classes.")
    assert got[0] == "7" and got[1] == "leading_line"


def test_contract_line_forms_are_still_read():
    assert av.asserted_value("ANSWER: NUM 64")[:2] == ("64", "answer_num")
    assert av.asserted_value("some prose\n\nANSWER: 64")[:2] == ("64", "answer_bare")
    v, form, _span = av.asserted_value(
        "ANSWER: CALL ledger.record_refusal(scope=scope_name, serialized_ref=text)")
    assert (v, form) == ("ledger.record_refusal", "answer_call")


def test_prose_call_forms_read_the_callee():
    v, form, _ = av.asserted_value(
        "ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)")
    assert form == "prose_call" and "ledger.record_refusal" in v
    v, form, _ = av.asserted_value("_refuse calls `ledger.record_refusal`. It passes four.")
    assert form == "calls" and v == "ledger.record_refusal"


# ---------------------------------------------------------------------------
# rejection: what must NOT be read as an asserted value
# ---------------------------------------------------------------------------
def test_code_citation_alone_is_none():
    """GREEN case 2: `resolve.py:39` and no value must return None."""
    assert av.asserted_value("See resolve.py:39 for the default; no value is given here.") is None
    assert av.asserted_value("The default lives at `resolve.py#L39`.") is None
    assert av.asserted_value("I need to read resolve.py L66\u2013L71 to see `_refuse`.") is None


def test_range_and_unit_are_not_values():
    assert av.asserted_value("The classes sit within lines 15\u2013142.") is None
    assert av.asserted_value("The excerpt is 1680 B long, ending at line 39.") is None
    assert av.asserted_value("The run was capped at 4096 tokens.") is None


def test_counts_of_other_things_are_not_values():
    assert av.asserted_value("It passes four arguments and nothing more.") is None
    assert av.asserted_value("The evidence lists seven classes in that file.") is None


def test_markup_and_bare_tool_calls_are_not_values():
    assert av.asserted_value("<tool_call>read_file resolve.py 64</tool_call>") is None
    assert av.asserted_value("I will call read_file next.") is None
    assert av.asserted_value("") is None
    assert av.asserted_value(None) is None


def test_tool_spam_turn_terminates():
    """85,100 chars of `<tool_call>open` every ~25 chars: must be O(n), not O(n^2).

    The first implementation rescanned to EOF at every open and did not finish
    in 60 s; this asserts it returns (a wall-clock budget would be flaky, so the
    guard is simply that the call completes).
    """
    text = "<tool_call>open" * 3400
    assert av.asserted_value(text) is None


# ---------------------------------------------------------------------------
# the measure: a SECOND column, never a replacement
# ---------------------------------------------------------------------------
def test_measure_is_a_second_column():
    doc = json.loads((MEASURE / "PROSE-VALUE-METRIC.json").read_text(encoding="utf-8"))
    assert doc["population"]["n_cells"] == 66
    assert doc["population"]["n_documents"] == 8
    assert len(doc["cells"]) == 66
    assert doc["population"]["n_frozen_pass"] + doc["population"]["n_frozen_non_pass"] == 66
    for cell in doc["cells"]:
        assert "frozen_verdict" in cell and "asserted_verdict" in cell
        assert cell["asserted_verdict"] in ("match", "mismatch", "no_value")
        # no cell may carry a rewritten accuracy field
        assert not any("accuracy" in k for k in cell)
        assert cell["source_sha256"] and cell["rows_sha256"]
    assert doc["live_requests"] == 0 and doc["network"] is False


def test_delta_counts_agree_with_cells():
    doc = json.loads((MEASURE / "PROSE-VALUE-METRIC.json").read_text(encoding="utf-8"))
    non = [c for c in doc["cells"] if not c["frozen_pass"]]
    asserting = [c for c in non if c["asserted_verdict"] != "no_value"]
    assert len(non) == doc["population"]["n_frozen_non_pass"]
    assert len(asserting) == doc["delta"]["assert_a_value"]
    assert sum(1 for c in asserting if c["asserted_verdict"] == "mismatch") == doc["delta"]["wrong"]
    assert sum(1 for c in asserting if c["asserted_verdict"] == "match") == doc["delta"]["right"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
