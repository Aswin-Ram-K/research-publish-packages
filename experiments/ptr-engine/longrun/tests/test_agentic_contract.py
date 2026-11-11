"""AGENTIC-CONTRACT: the shared row contract rejects what it must reject.

The contract is imported by the cell (which writes every row) and by the analyser (which
reads them), so a validator that accepts a bad row is a defect that reaches both at once.
Each test below pins one rule the contract states.

The TASK half of this module is gone: ``consonance.longrun-fixture/2`` won the schema
ruling (2026-11-11) and ``run_longrun.load_fixture`` validates it, so a second task
validator here would be a second convention for the same measurement.  The task tests
that used to live in this file were deleted with ``validate_task``/``load_tasks``/
``episode_cost``.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import agentic_contract as C  # noqa: E402


def _row(**over):
    row = {
        "run_id": "r1", "harness_sha256": "0" * 64, "arm": "none", "task_id": "AG-99",
        "rep": 1, "step": 1,
        "kind": "work", "prompt_tokens": 10, "tool_calls": [], "fetch_rounds": 0,
        "fold_event": False, "fold_kind": None, "compactions": 0, "evicted": 0,
        "prompt_tokens_max": 10, "tools_schema_sent": True, "answer": None,
        "expected": None, "verified": None, "expected_present": None,
        "ts": "2026-11-11T00:00:00Z",
    }
    row.update(over)
    return row


def test_the_arm_set_is_the_five_the_design_names():
    assert C.ARMS == ("none", "masking-no-fetch", "pinned", "bounded-context-fetch",
                      "compact")


def test_the_tool_surface_is_read_file_and_grep():
    assert C.TOOL_NAMES == ("read_file", "grep")


def test_a_well_formed_row_validates():
    assert C.validate_row(_row())["arm"] == "none"


def test_a_row_with_an_unknown_arm_is_rejected():
    with pytest.raises(C.ContractError, match="arm"):
        C.validate_row(_row(arm="spcc"))


def test_a_row_missing_expected_present_is_rejected():
    """Red->green: the field must be present, so a runner cannot silently omit it."""
    row = _row()
    del row["expected_present"]
    with pytest.raises(C.ContractError, match="expected_present"):
        C.validate_row(row)


def test_a_row_missing_a_stage_two_field_is_rejected():
    """Red->green: the m00447 fields are required, not optional extras."""
    for key in ("fetch_rounds", "compactions", "evicted", "prompt_tokens_max",
                "tools_schema_sent"):
        row = _row()
        del row[key]
        with pytest.raises(C.ContractError, match=key):
            C.validate_row(row)


def test_a_row_with_a_non_list_tool_calls_is_rejected():
    with pytest.raises(C.ContractError, match="tool_calls"):
        C.validate_row(_row(tool_calls={"name": "read_file"}))


def test_a_row_with_an_unknown_kind_is_rejected():
    with pytest.raises(C.ContractError, match="kind"):
        C.validate_row(_row(kind="probe"))


def test_a_non_object_row_is_rejected():
    with pytest.raises(C.ContractError, match="not an object"):
        C.validate_row(["not", "a", "row"])


def test_the_removed_task_api_is_gone():
    """The cutover is the point: a resurrected task validator would be a second schema."""
    for name in ("validate_task", "load_task", "load_tasks", "episode_cost",
                 "REQUIRED_TASK_KEYS", "ANSWER_FORMS", "SUMMARY_ARMS"):
        assert not hasattr(C, name), name
