"""Guards for experiments/ptr-engine/tools/tranche_canary.py (unit TRANCHE-CANARY).

The canary's job is to keep an offline-passing but live-broken launch shape from spending
480 turns. Its whole value is the VERDICT, so every verdict is pinned here, including the
two ways it must refuse to say "ok": a window that is too short, and an argv it cannot run.

Read-only: the only real file opened is the recorded stopped cell's rows, and only for
reading. No request is made; the live path is never exercised.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TOOL = (Path(__file__).resolve().parents[1]
        / "experiments" / "ptr-engine" / "tools" / "tranche_canary.py")
RECORDED_ROWS = (Path(__file__).resolve().parents[1] / "experiments" / "ptr-engine"
                 / "measure" / "rows-cell-pointer-stable-20261026T182535Z.jsonl")


def _load():
    spec = importlib.util.spec_from_file_location("tranche_canary_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


canary = _load()


def row(turn, **overrides):
    """One turn row, shaped like run_longrun.py's (only the fields the canary reads)."""
    base = {
        "kind": "turn", "arm": "pointer-stable", "rep": 1, "turn": turn,
        "completion_tokens": 40, "max_tokens": 4096, "stop_reason": "stop",
        "truncated": False, "wall_ms": 2000.0,
        "answer_turn": False, "answer_value": None, "answer_raw": None,
        "answer_parse_error": None,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------- shape_ok
def test_ok_with_a_slow_but_untruncated_turn():
    """A turn that takes 2m51s is SLOW, not truncated: it must stay shape_ok.

    wall_ms is a cost, not a verdict. Only the completion ceiling and the two
    cell-ending stop reasons may turn a shape degenerate.
    """
    rows = [
        row(1, completion_tokens=718, wall_ms=20192.1),
        row(2, completion_tokens=342, wall_ms=171_000.0),      # slow, finished cleanly
        row(3, answer_turn=True, answer_value={"callee": "ledger.record_resolution"},
            answer_raw="ANSWER: CALL ledger.record_resolution(block_size=...)"),
        row(4, completion_tokens=256, wall_ms=7283.4),
        row(5, completion_tokens=82, wall_ms=2454.2),
    ]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_ok", verdict
    assert verdict["exit_code"] == 0
    assert verdict["parseable_answers"] == 1
    assert verdict["turns_observed"] == 5
    assert "evidence" not in verdict


# ---------------------------------------------------------------- shape_degenerate
def test_degenerate_on_a_synthetic_cap_length_completion():
    """completion_tokens == max_tokens within N turns is a channel/prompt mismatch."""
    rows = [
        row(1, completion_tokens=718),
        row(2, completion_tokens=4096, max_tokens=4096, stop_reason="length",
            truncated=True, wall_ms=114838.846),
        row(3, completion_tokens=256),
    ]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate", verdict
    assert verdict["exit_code"] == 1
    assert verdict["evidence"]["turn"] == 2
    assert verdict["evidence"]["completion_tokens"] == 4096
    assert verdict["evidence"]["max_tokens"] == 4096
    assert verdict["evidence"]["wall_ms"] == 114838.846
    assert verdict["evidence"]["trigger"] == "completion_ceiling"
    # The signal outranks the short window: 3 rows for a 5-turn window is still evidence.
    assert verdict["turns_observed"] == 3


def test_degenerate_on_a_cell_ending_stop_reason_even_without_the_ceiling():
    rows = [row(1), row(2, completion_tokens=12, stop_reason="turn_wall_cap",
                 wall_ms=180_000.0), row(3), row(4), row(5)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate"
    assert verdict["evidence"]["turn"] == 2
    assert verdict["evidence"]["trigger"] == "degenerate_stop_reason"


# ---------------------------------------------------------------- shape_unknown
def test_unknown_when_fewer_turns_were_recorded_than_asked_for():
    rows = [row(1), row(2)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_unknown"
    assert verdict["exit_code"] == 2
    assert verdict["turns_observed"] == 2
    assert "NOT rounded to ok" in verdict["why"]


def test_unknown_when_no_traffic_at_all():
    verdict = canary.classify([], n=5)
    assert verdict["verdict"] == "shape_unknown"
    assert verdict["exit_code"] == 2
    assert verdict["turns_observed"] == 0


def test_unknown_when_the_answer_contract_produced_no_parseable_answer():
    """A clean window with no parseable answer is NOT ok: the contract is unproven."""
    rows = [row(t) for t in range(1, 6)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_unknown"
    assert verdict["trigger"] == "no_parseable_answer"


# ---------------------------------------------------------------- could not run
def test_cannot_run_on_a_missing_rows_file(tmp_path):
    with pytest.raises(SystemExit) as exc:
        canary.main(["--rows", str(tmp_path / "nope.jsonl")])
    assert exc.value.code == 3


def test_cannot_run_on_a_bad_window_flag(tmp_path):
    rows_file = tmp_path / "rows.jsonl"
    rows_file.write_text(json.dumps(row(1)) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        canary.main(["--rows", str(rows_file), "--turns", "0"])
    assert exc.value.code == 3


def test_cannot_run_when_launch_is_passed_without_live(tmp_path):
    rows_file = tmp_path / "rows.jsonl"
    rows_file.write_text(json.dumps(row(1)) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        canary.main(["--rows", str(rows_file), "--launch", "python3 cell.py"])
    assert exc.value.code == 3


def test_cannot_run_refuses_a_multi_rep_launch():
    """A --reps 3 launch would spend 3x the canary's requests for no extra signal."""
    with pytest.raises(SystemExit) as exc:
        canary.effective_argv("python3 cell.py --arm x --turns 48 --reps 3", 5)
    assert exc.value.code == 3


def test_effective_argv_rewrites_only_the_turn_window():
    argv = canary.effective_argv(
        "python3 cell.py --arm pointer-stable --turns 48 --reps 1 --budget 900", 5)
    assert argv.count("--turns") == 1
    assert argv[argv.index("--turns") + 1] == "5"
    assert argv[argv.index("--reps") + 1] == "1"
    assert argv[argv.index("--budget") + 1] == "900"


# ---------------------------------------------------------------- the recorded cell
@pytest.mark.skipif(not RECORDED_ROWS.is_file(), reason="recorded stopped cell not on disk")
def test_replay_of_the_stopped_cell_is_degenerate_at_five_and_unknown_at_two():
    """The two replay runs the card requires, over the 27 real rows. Zero requests."""
    rows = canary.load_rows(str(RECORDED_ROWS))
    assert len(rows) == 27

    five = canary.classify(rows, n=5)
    assert five["verdict"] == "shape_degenerate"
    assert five["evidence"]["turn"] == 3
    assert five["evidence"]["completion_tokens"] == 4096
    assert five["evidence"]["max_tokens"] == 4096
    assert five["evidence"]["stop_reason"] == "length"

    two = canary.classify(rows, n=2)
    assert two["verdict"] == "shape_unknown"
    assert two["turns_observed"] == 2
    assert "evidence" not in two


# ---------------------------------------------------------------- vocabulary ownership
def test_degenerate_stop_reasons_are_inside_the_closed_vocabulary():
    vocabulary = set(canary.stop_reasons())
    assert canary.DEGENERATE_STOP_REASONS <= vocabulary
    assert {"stop", "length", "runaway_turn", "turn_wall_cap"} <= vocabulary


# ================================================================ CANARY-ERA-B-FIX
# The tools-on (run_longrun) rows carry `finish_reason`, never `stop_reason`, and no
# `answer_turn`. Before this unit the canary resolved stop_reason only, so 3 of 3 tools-on
# files were shape_unknown at every N below 48. Each rule below has its own guard test.
TOOLS_ON_V4 = RECORDED_ROWS.parent / "rows-longrun-v4-tools-2026-10-26.jsonl"
TOOLS_ON_V5 = RECORDED_ROWS.parent / "rows-longrun-v5-tools.jsonl"
TOOLS_ON_V6 = RECORDED_ROWS.parent / "rows-longrun-v6-tools.jsonl"


def era_b(turn, **overrides):
    """One tools-on turn row: the wire fields only, no engine-derived stop_reason."""
    base = {
        "kind": "turn", "arm": "pointer-stable", "rep": 1, "turn": turn,
        "completion_tokens": 40, "max_tokens": 4096, "finish_reason": "stop",
        "truncated": False, "failed_turn": False,
        "answer_verified": None, "is_checkpoint": False, "tool_calls": [],
    }
    base.update(overrides)
    return base


def test_stop_signal_precedence_is_the_documented_order():
    assert canary.STOP_SIGNAL_PRECEDENCE == (
        "stop_reason", "finish_reason", "truncated", "completion_tokens==max_tokens")


def test_stop_reason_outranks_finish_reason():
    """The engine's derivation wins; a wire field never overrides it."""
    reason, source = canary.stop_signal(row(1, stop_reason="stop", finish_reason="length"))
    assert (reason, source) == ("stop", "stop_reason")


def test_era_b_rows_read_finish_reason_and_answer_verified():
    """FINISH_REASON FALLBACK + ANSWER CONTRACT: the shape the canary must bless."""
    rows = [era_b(1), era_b(2), era_b(3, answer_verified=True, is_checkpoint=True),
            era_b(4), era_b(5)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_ok", verdict
    assert verdict["exit_code"] == 0
    assert verdict["shape_era"] == "B"
    assert verdict["answer_contract"] == "answer_verified"
    # Reported separately, and both readable: parseable_answers is structurally 0 here.
    assert verdict["answer_verified"] == 1
    assert verdict["parseable_answers"] == 0
    assert verdict["stop_signal_sources"] == ["finish_reason"]


def test_finish_reason_length_is_a_completion_ceiling():
    """A `length` finish is the ceiling even when the token arithmetic looks short."""
    rows = [era_b(1), era_b(2, finish_reason="length", completion_tokens=900,
                     truncated=True, failed_turn=True), era_b(3)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate", verdict
    assert verdict["trigger"] == "completion_ceiling"
    assert verdict["evidence"]["turn"] == 2
    assert verdict["evidence"]["stop_signal_source"] == "finish_reason"
    assert verdict["evidence"]["stop_reason"] == "length"


def test_truncated_is_the_fallback_when_no_reason_field_is_present():
    rows = [era_b(1, finish_reason=None, truncated=True, completion_tokens=700), era_b(2)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate", verdict
    assert verdict["evidence"]["stop_signal_source"] == "truncated"


def test_completion_tokens_arithmetic_is_the_last_fallback():
    rows = [era_b(1, finish_reason=None, truncated=False,
                  completion_tokens=4096, max_tokens=4096), era_b(2)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate", verdict
    assert verdict["evidence"]["stop_signal_source"] == "completion_tokens==max_tokens"


def test_era_a_is_still_held_to_parseable_answers():
    """The era A gate is NOT loosened: answer_verified alone cannot make era A ok."""
    rows = [row(t, answer_verified=True, answer_turn=False) for t in range(1, 6)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_unknown", verdict
    assert verdict["shape_era"] == "A"
    assert verdict["answer_contract"] == "parseable_answers"
    assert verdict["trigger"] == "no_parseable_answer"


def test_era_b_ok_still_needs_a_verified_answer():
    rows = [era_b(t, answer_verified=(False if t == 3 else None)) for t in range(1, 6)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_unknown", verdict
    assert verdict["trigger"] == "no_verified_answer"
    assert verdict["answer_verified_false"] == 1


def test_tool_call_storm_is_degenerate():
    """130 calls land in ONE turn against a manifest cap of 2: not a measurement."""
    storm = [{"path": "ptr_engine/resolve.py", "error": "fetch_budget_exhausted"}
             for _ in range(130)]
    rows = [era_b(1, answer_verified=True, is_checkpoint=True),
            era_b(2, tool_calls=storm, completion_tokens=1146),
            era_b(3)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate", verdict
    assert verdict["trigger"] == "tool_call_storm"
    assert verdict["evidence"]["turn"] == 2
    assert verdict["evidence"]["tool_calls"] == 130
    assert verdict["storm_min_calls"] == 110


def test_fanout_under_the_measured_threshold_is_not_a_storm():
    """v6 T26 fired 101 calls and stayed contained; 110 is the measured boundary."""
    contained = [{"path": "x", "executed": False, "error": "turn_call_cap"}
                 for _ in range(101)]
    rows = [era_b(1, answer_verified=True, is_checkpoint=True),
            era_b(2, tool_calls=contained, completion_tokens=3283),
            era_b(3), era_b(4), era_b(5)]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_ok", verdict


def test_the_completion_ceiling_is_named_before_a_storm_on_the_same_turn():
    storm = [{"path": "x", "error": "fetch_budget_exhausted"} for _ in range(116)]
    rows = [era_b(1), era_b(2, tool_calls=storm, completion_tokens=4096,
                           max_tokens=4096, finish_reason="length")]
    verdict = canary.classify(rows, n=5)
    assert verdict["verdict"] == "shape_degenerate"
    assert verdict["trigger"] == "completion_ceiling"


@pytest.mark.skipif(not TOOLS_ON_V6.is_file(), reason="tools-on rows not on disk")
def test_tools_on_matrix_v4_v5_v6():
    """The acceptance matrix, replay only: zero requests."""
    v4 = canary.classify(canary.load_rows(str(TOOLS_ON_V4)), n=5)
    assert (v4["verdict"], v4["shape_era"]) == ("shape_unknown", "B")
    v4_48 = canary.classify(canary.load_rows(str(TOOLS_ON_V4)), n=48)
    assert (v4_48["verdict"], v4_48["evidence"]["turn"]) == ("shape_degenerate", 45)
    assert v4_48["evidence"]["stop_signal_source"] == "finish_reason"

    v5_48 = canary.classify(canary.load_rows(str(TOOLS_ON_V5)), n=48)
    assert (v5_48["verdict"], v5_48["evidence"]["turn"]) == ("shape_degenerate", 29)

    v6 = canary.load_rows(str(TOOLS_ON_V6))
    assert canary.classify(v6, n=5)["verdict"] == "shape_unknown"
    assert canary.classify(v6, n=12)["verdict"] == "shape_ok"
    v6_48 = canary.classify(v6, n=48)
    assert v6_48["verdict"] == "shape_ok", v6_48
    assert v6_48["answer_verified"] == 1
