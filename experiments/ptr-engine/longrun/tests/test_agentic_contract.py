"""AGENTIC-CONTRACT: the shared stage-2 contract rejects what it must reject.

The contract is imported by the runner, the task builder and the analyser, so a validator
that accepts a bad task or a bad row is a defect that reaches all three at once.  Each test
below pins one rule the contract states, and the two that matter most are red->green: the
graded value must not appear in the final question (or no fold could ever destroy it), and
`expected_present` must never be defaulted to true (or a lost value would score as a pass).
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import agentic_contract as C  # noqa: E402


def _task(**over):
    task = {
        "task_id": "AG-99",
        "version": "AG-99.v1",
        "root": "experiments/ptr-engine",
        "statement": "work over the tree",
        "steps": [{"prompt": "read a"}, {"prompt": "read b"}, {"prompt": "read c"}],
        "final_question": "using the symbol you identified at step 2, report its override",
        "expected": "4017",
        "answer_form": "NUM",
        "fact": {"value": "4017", "introduced_at_step": 2,
                 "source_path": "ptr_engine/tx05_constants.py"},
        "checkpoints": [{"step": 2, "question": "q", "expected": "4011", "fact_id": "SYM_01"}],
    }
    task.update(over)
    return task


def _row(**over):
    row = {
        "run_id": "r1", "arm": "none", "task_id": "AG-99", "rep": 1, "step": 1,
        "kind": "work", "prompt_tokens": 10, "tool_calls": [], "fold_event": False,
        "fold_kind": None, "answer": None, "expected": None, "verified": None,
        "expected_present": None, "ts": "2026-11-11T00:00:00Z",
    }
    row.update(over)
    return row


def test_a_well_formed_task_validates():
    assert C.validate_task(_task())["task_id"] == "AG-99"


def test_a_task_missing_a_required_key_is_rejected():
    task = _task()
    del task["final_question"]
    with pytest.raises(C.ContractError, match="final_question"):
        C.validate_task(task)


def test_a_final_question_that_restates_the_value_is_rejected():
    """Red->green: the value in the question means no fold could ever destroy it."""
    with pytest.raises(C.ContractError, match="restates the graded value"):
        C.validate_task(_task(final_question="report the override of 4017"))


def test_an_introduced_at_step_outside_the_steps_is_rejected():
    with pytest.raises(C.ContractError, match="introduced_at_step"):
        C.validate_task(_task(fact={"value": "4017", "introduced_at_step": 9,
                                    "source_path": "x.py"}))


def test_an_unknown_answer_form_is_rejected():
    with pytest.raises(C.ContractError, match="answer_form"):
        C.validate_task(_task(answer_form="BOOL"))


def test_a_checkpoint_outside_the_steps_is_rejected():
    with pytest.raises(C.ContractError, match="checkpoint step"):
        C.validate_task(_task(checkpoints=[{"step": 7, "question": "q", "expected": "1"}]))


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


def test_a_row_with_a_non_list_tool_calls_is_rejected():
    with pytest.raises(C.ContractError, match="tool_calls"):
        C.validate_row(_row(tool_calls={"name": "read_file"}))


def test_episode_cost_counts_a_summary_call_per_fold_only_on_summary_arms():
    task = _task()
    assert C.episode_cost(task, "none") == 4
    assert C.episode_cost(task, "compact") == 4
    assert C.episode_cost(task, "compact", folds=3) == 7
    assert C.episode_cost(task, "pinned", folds=3) == 4


def test_load_tasks_validates_every_file(tmp_path):
    good = tmp_path / "AG-99.v1.json"
    good.write_text(json.dumps(_task()), encoding="utf-8")
    assert [t["task_id"] for t in C.load_tasks(str(tmp_path))] == ["AG-99"]
    bad = tmp_path / "AG-98.v1.json"
    bad.write_text(json.dumps(_task(task_id="AG-98", answer_form="BOOL")), encoding="utf-8")
    with pytest.raises(C.ContractError):
        C.load_tasks(str(tmp_path))
