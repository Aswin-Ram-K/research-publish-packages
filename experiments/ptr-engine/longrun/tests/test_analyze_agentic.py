"""analyze_agentic: attribution classes, accuracy, and the five falsifiers.

Every case is synthetic: the analyser is a pure function over rows, so the tests build
the exact row shapes the contract defines and assert the classification and the verdict
numbers.  No request is sent and no row file outside `tmp_path` is read.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
for _p in (LONGRUN, os.path.join(LONGRUN, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import analyze_agentic as AA  # noqa: E402


def _row(arm, *, task="AG-01", rep=1, step=1, verified=None, present=None,
         fold=False, tools=(), prompt=100, cached=0, dropped=0, pinned=0,
         run_id="run-1", kind="work", value_present=None):
    return {
        "run_id": run_id, "arm": arm, "task_id": task, "rep": rep, "step": step,
        "kind": kind, "prompt_tokens": prompt, "completion_tokens": 0,
        "cached_tokens": cached,
        "tool_calls": [{"name": name, "arguments": {}, "ok": True, "bytes": 0}
                       for name in tools],
        "fold_event": fold, "fold_kind": "fold" if fold else None,
        "dropped_turns": dropped, "pinned_tokens": pinned,
        "answer": None, "expected": None, "verified": verified,
        "expected_present": present, "value_present": value_present,
        "ts": "2026-11-11T00:00:00Z",
    }


def _fired(rows, name):
    return AA.analyse(rows)["verdict"]["falsifiers"][name]["fired"]


# --- attribution -----------------------------------------------------------

def test_attribution_classes_are_separated():
    rows = [
        _row("none", step=1, verified=True, present=None),
        _row("none", step=2, verified=False, present=False),
        _row("none", step=3, verified=False, present=True),
        _row("none", step=4, verified=False, present=None),
    ]
    counts = AA.analyse(rows)["arms"]["none"]["counts"]
    assert counts == {"ok": 1, "lost_then_failed": 1,
                      "present_then_failed": 1, "unclassified": 1,
                      "literal_disagreement": 0}


def test_null_presence_is_never_a_pass():
    rows = [_row("none", verified=False, present=None)]
    arm = AA.analyse(rows)["arms"]["none"]
    assert arm["counts"]["ok"] == 0
    assert arm["counts"]["unclassified"] == 1
    assert arm["accuracy"] == 0.0


def test_ungraded_rows_are_not_counted():
    rows = [_row("none", step=1, verified=None, present=None),
            _row("none", step=2, verified=True, present=True)]
    arm = AA.analyse(rows)["arms"]["none"]
    assert arm["graded"] == 1
    assert arm["verified"] == 1
    assert arm["accuracy"] == 1.0


def test_accuracy_is_verified_over_graded():
    rows = [
        _row("none", step=1, verified=True, present=True),
        _row("none", step=2, verified=True, present=True),
        _row("none", step=3, verified=False, present=True),
        _row("none", step=4, verified=None, present=None),
    ]
    arm = AA.analyse(rows)["arms"]["none"]
    assert arm["graded"] == 3
    assert arm["verified"] == 2
    assert arm["accuracy"] == 2 / 3


# --- refetch ---------------------------------------------------------------

def test_refetch_counts_only_at_or_after_first_fold():
    rows = [
        _row("pinned", step=1, tools=["read_file"]),
        _row("pinned", step=2, fold=True, tools=["read_file"]),
        _row("pinned", step=3, tools=["grep", "read_file"]),
    ]
    assert AA.analyse(rows)["arms"]["pinned"]["refetch_count"] == 3


def test_episode_without_fold_contributes_no_refetch():
    rows = [_row("pinned", step=1, tools=["read_file"]),
            _row("pinned", step=2, tools=["grep"])]
    arm = AA.analyse(rows)["arms"]["pinned"]
    assert arm["refetch_count"] == 0
    assert arm["episodes_without_fold"] == 1


# --- falsifier 1: instrument_failure ---------------------------------------

def test_instrument_failure_fires_without_lost_rows():
    rows = [_row("none", verified=False, present=True)]
    assert _fired(rows, "instrument_failure") is True


def test_instrument_failure_silent_with_a_lost_row():
    rows = [_row("none", verified=False, present=False)]
    assert _fired(rows, "instrument_failure") is False


# --- falsifier 2: null_model_error -----------------------------------------

def test_null_model_error_fires_when_present_dominates_every_arm():
    rows = [_row("none", verified=False, present=True),
            _row("pinned", verified=False, present=True)]
    assert _fired(rows, "null_model_error") is True


def test_null_model_error_silent_when_one_arm_has_lost():
    rows = [_row("none", verified=False, present=True),
            _row("pinned", verified=False, present=False)]
    assert _fired(rows, "null_model_error") is False


# --- falsifier 3: pin_premise_fails ----------------------------------------

def test_pin_premise_fails_when_pinned_not_above_none():
    rows = [_row("none", verified=True, present=True),
            _row("pinned", verified=False, present=True)]
    assert _fired(rows, "pin_premise_fails") is True


def test_pin_premise_silent_when_pinned_above_none():
    rows = [_row("none", verified=False, present=True),
            _row("pinned", verified=True, present=True)]
    assert _fired(rows, "pin_premise_fails") is False


def test_pin_premise_silent_when_both_arms_are_perfect():
    """PIN-PREMISE red->green: two perfect arms are not a failure of pinning.

    Nothing was lost, so there was nothing to recover and the premise is untested.  The
    first version of the falsifier fired here (`not (pin > none)`), which would have
    reported a healthy instrument as broken on the most likely stage-2 outcome.
    """
    rows = [_row("none", verified=True, present=True),
            _row("pinned", verified=True, present=True)]
    assert _fired(rows, "pin_premise_fails") is False


def test_pin_premise_fires_when_both_arms_fail_equally():
    rows = [_row("none", verified=False, present=False),
            _row("pinned", verified=False, present=False)]
    assert _fired(rows, "pin_premise_fails") is True


# --- falsifier 4: recovery_not_paid ----------------------------------------

def _episode(arm, refetch_calls):
    return [_row(arm, step=1, fold=True, tools=()),
            _row(arm, step=2, tools=refetch_calls)]


def test_recovery_not_paid_fires_when_refetch_equal():
    rows = (_episode("bounded-context-fetch", ["read_file"])
            + _episode("masking-no-fetch", ["read_file"]))
    assert _fired(rows, "recovery_not_paid") is True


def test_recovery_not_paid_silent_when_fetch_arm_refetches_more():
    rows = (_episode("bounded-context-fetch", ["read_file", "grep"])
            + _episode("masking-no-fetch", ["read_file"]))
    assert _fired(rows, "recovery_not_paid") is False


# --- falsifier 5: compaction_not_cheaper -----------------------------------

def test_compaction_not_cheaper_fires_when_compact_prompt_not_below_none():
    rows = [_row("none", prompt=100), _row("compact", prompt=100)]
    assert _fired(rows, "compaction_not_cheaper") is True


def test_compaction_not_cheaper_silent_when_compact_is_cheaper():
    rows = [_row("none", prompt=100), _row("compact", prompt=40)]
    assert _fired(rows, "compaction_not_cheaper") is False


# --- CLI -------------------------------------------------------------------

def test_cli_writes_json_and_markdown_and_exits_zero(tmp_path):
    rows = [
        _row("none", step=1, verified=True, present=True),
        _row("none", step=2, verified=False, present=False),
        _row("pinned", step=1, verified=False, present=True),
    ]
    src = tmp_path / "rows-agentic-x.jsonl"
    src.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = tmp_path / "report.json"
    md = tmp_path / "report.md"
    rc = AA.main(["--rows", str(src), "--out", str(out), "--md", str(md)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["row_count"] == 3
    assert report["arms"]["none"]["accuracy"] == 0.5
    assert "| arm |" in md.read_text(encoding="utf-8")


def test_cli_exits_zero_with_no_rows(tmp_path):
    rc = AA.main(["--rows", str(tmp_path / "none-*.jsonl")])
    assert rc == 0


def test_literal_disagreement_counts_the_rows_the_old_rule_misattributed():
    """The literal test and the document anchor disagree on a derived answer.

    A CALL checkpoint's ``expected`` is the derived structure, so ``value_present`` is
    False while the document carrying the fact is in the prompt.  The count is the size
    of the defect the anchor rule repairs, and it must not be folded into the
    attribution classes.
    """
    rows = [
        _row("none", step=1, verified=False, present=True, value_present=False),
        _row("none", step=2, verified=True, present=True, value_present=True),
        _row("none", step=3, verified=False, present=False, value_present=False),
    ]
    arm = AA.analyse(rows)["arms"]["none"]
    assert arm["counts"]["literal_disagreement"] == 1
    assert arm["counts"]["present_then_failed"] == 1
    assert arm["counts"]["lost_then_failed"] == 1
