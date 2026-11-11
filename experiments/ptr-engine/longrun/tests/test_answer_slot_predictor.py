#!/usr/bin/env python3
"""test_answer_slot_predictor.py - U-SPCC-67's binding diagnosis, as an offline test.

THE RULE UNDER TEST (named, because a test that only asserts "it passes" proves nothing):

    BOUND  = the arm's prompt replays `ANSWER (T<n>):` lines, AND the block immediately
             above the current answer slot (after the host's `CHECKPOINT TURN.` contract
             and any `CHECKPOINT QUESTION: ` suffix is stripped) is a `TOOL_OUTPUT
             (doc@rev): body` delivery of a document OTHER than the asked one, AND that
             body carries `<asked symbol> = <int>`.
    FREE   = everything else, with the reason: `no_answer_replay` (spcc's layered
             compiler has no positional slot to bind to), `no_delivery_above`,
             `same_document`, or `symbol_not_in_delivery`.

  The prediction is about the SHAPE of the prompt and the checkpoint's own metadata.
  It never reads a row's answer, a distance, or an expected value, so the two tests
  below that join answers are measurements, not derivations.

RED -> GREEN (this file's own record; each failure text is copied from a run against a
deliberately broken variant, and the broken variant was reverted before the next run):

  1. `same_document` guard removed from `predict_answer_slot.classify` (the rule then
     fires on ANY delivery above the slot).  Recorded red:
       test_same_document_delivery_above_is_free
       AssertionError: assert 'BOUND' == 'FREE'
  2. the no-network gate removed from `predict_answer_slot.main` (the `if NET_ATTEMPTS:
     return 9` block deleted).  Recorded red:
       test_no_network_guard_trips_and_the_tool_refuses_to_report
       assert 0 == 9
     where 0 is what main() returns once it is allowed to proceed on a violated premise.
  3. the decoy's delivery deleted from turn 13 of TX-04S (13 mismatch turns instead of
     14; the declared count then disagrees with the turns).  Recorded red:
       test_mismatch_fixture_declares_at_least_twelve_binding_turns
       AssertionError: assert [3, 4, 5, 6, 7, 9, 10, 17, 24, 29, 36, 41, 73] ==
                        [3, 4, 5, 6, 7, 9, 10, 13, 17, 24, 29, 36, 41, 73]
     (pytest renders it as the list diff `- 13`; the fixture was regenerated with
     `build_mismatch_fixture.py`, whose bytes are a function of its constants, and the
     emitted sha256 returned to 7f41f9b31df2d6be...)

Offline: the predictor arms its own trip-wires in `main`, and the test that trips one
restores the five primitives afterwards, so importing this module patches nothing for the
rest of the suite.
"""
import os
import sys
import urllib.request

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
TOOLS = os.path.join(ENGINE, "tools")
for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_pointer_fixtures as CPF  # noqa: E402
import predict_answer_slot as PAS  # noqa: E402
import run_longrun as R  # noqa: E402

TX04 = os.path.join(LONGRUN, "tasks-v7", "TX-04.v1.json")
TX04S = os.path.join(LONGRUN, "tasks-v7", "TX-04S.v1.json")
ROWS = os.path.join(ENGINE, "measure", "rows-e3-retain-2026-11-10.jsonl")

D06 = "# doc-fact-06\nVAL_A = 4061\nVAL_B = 4062\nVAL_C = 4063\nVAL_D = 4064\n"
D02 = "# doc-fact-02\nVAL_A = 4021\nVAL_B = 4022\nVAL_C = 4023\nVAL_D = 4024\n"


# --------------------------------------------------------------- prompt shapes
def _delivery(doc: str, body: str) -> dict:
    return {"doc_id": doc, "revision": 1, "body": body}


def _current(t: int, turn: dict) -> str:
    """The current turn exactly as the masking arm renders it (body sits above the slot)."""
    text = R.turn_user(t, turn)
    tos = R._turn_tool_outputs(turn)
    if tos:
        text += "\nTOOL OUTPUTS:\n" + "\n".join(
            "TOOL_OUTPUT (%s@%s): %s" % (to["doc_id"], to["revision"], to["body"])
            for to in tos)
    return text


def _flat_prompt(current_turn: int, current: dict, prior_turns: int = 9,
                 contract: bool = True) -> str:
    """A flat transcript: `prior_turns` worked turns, then the checkpoint's own block."""
    parts = ["WORKING SET\nINDEX\n"]
    for t in range(1, prior_turns + 1):
        parts.append(R.turn_block(t, {"turn": t, "question": "Work turn %d." % t},
                                 "ANSWER: TEXT ok"))
    parts.append(_current(current_turn, current))
    prompt = "\n\n".join(parts)
    if contract:
        prompt = R.checkpoint_prompt({"checkpoints": []}, current_turn, prompt,
                                     "masking-no-fetch")
    return prompt


def _checkpoint(doc: str, symbol: str, body: str) -> dict:
    return {
        "turn": 10,
        "question": "What is %s of %s?" % (symbol, doc),
        "ground_truth": {"doc": doc, "revision": 1, "value": body},
        "expected": "0",
    }


# ------------------------------------------------------------------ (a) the rule
def test_mismatched_delivery_above_binds_the_answer_slot():
    """A different document's body sits above the slot -> BOUND, with that body's value."""
    turn = {"turn": 10, "question": "What is VAL_A of doc-fact-02?",
            "tool_outputs": [_delivery("doc-fact-06", D06)]}
    cp = _checkpoint("doc-fact-02", "VAL_A", D02)
    prompt = _flat_prompt(10, turn)

    shape = PAS.answer_slot_shape(prompt, 10)
    assert shape["grammar"] == PAS.GRAMMAR_FLAT
    assert shape["replays_answers"] is True
    assert shape["contract_present"] is True
    assert shape["block_above"]["doc_id"] == "doc-fact-06"

    pred = PAS.classify(shape, cp)
    assert pred["prediction"] == "BOUND"
    assert pred["reason"] == "mismatched_delivery_above"
    assert pred["predicted_value"] == 4061        # doc-fact-06's VAL_A, not 4021
    assert pred["asked_doc"] == "doc-fact-02"
    assert pred["asked_symbol"] == "VAL_A"


def test_same_document_delivery_above_is_free():
    """The asked document's own body above the slot is a retrieval aid, not a binding."""
    turn = {"turn": 10, "question": "What is VAL_A of doc-fact-06?",
            "tool_outputs": [_delivery("doc-fact-06", D06)]}
    cp = _checkpoint("doc-fact-06", "VAL_A", D06)
    shape = PAS.answer_slot_shape(_flat_prompt(10, turn), 10)
    pred = PAS.classify(shape, cp)
    assert pred["prediction"] == "FREE"
    assert pred["reason"] == "same_document"
    assert pred["predicted_value"] is None
    assert pred["delivered_doc"] == "doc-fact-06"


def test_no_delivery_above_is_free():
    """Nothing delivered above the slot -> FREE (the common checkpoint shape)."""
    turn = {"turn": 10, "question": "What is VAL_A of doc-fact-06?"}
    cp = _checkpoint("doc-fact-06", "VAL_A", D06)
    shape = PAS.answer_slot_shape(_flat_prompt(10, turn), 10)
    assert shape["block_above"] is None
    pred = PAS.classify(shape, cp)
    assert pred["prediction"] == "FREE"
    assert pred["reason"] == "no_delivery_above"


def test_spcc_layered_shape_is_free():
    """No `ANSWER (Tn):` replay means no positional rule exists -> FREE, never BOUND."""
    layered = ("WORKING SET\nINDEX\n\nBODY item-1 (33 B)\nitem body\n\n"
               "QUESTION (T10): What is VAL_A of doc-fact-02?\n"
               "TOOL_OUTPUT (doc-fact-06@r1): " + D06)
    cp = _checkpoint("doc-fact-02", "VAL_A", D02)
    shape = PAS.answer_slot_shape(layered, 10)
    assert shape["grammar"] == PAS.GRAMMAR_LAYERED
    assert shape["replays_answers"] is False
    pred = PAS.classify(shape, cp)
    assert pred["prediction"] == "FREE"
    assert pred["reason"] == "no_answer_replay"


# ------------------------------------------------------- (b) the no-network guard
def test_no_network_guard_trips_and_the_tool_refuses_to_report(tmp_path):
    """The guard is structural, and a violated premise produces NO report."""
    report = tmp_path / "report.json"
    PAS.install_tripwires()
    try:
        with pytest.raises(AssertionError, match="NETWORK REFUSED"):
            urllib.request.urlopen("http://192.168.2.168:8000/v1/models", timeout=1)
        assert PAS.NET_ATTEMPTS == ["urllib.request.urlopen"]

        rc = PAS.main(["--fixture", TX04, "--rows", ROWS,
                       "--arms", "masking-no-fetch",
                       "--workdir", str(tmp_path / "work"),
                       "--json", str(report)])
        assert rc == 9, "a recorded network attempt must refuse the report (exit 9)"
        assert not report.exists(), "the tool wrote a report on a violated no-network premise"
    finally:
        PAS.restore_tripwires()

    assert PAS.NET_ATTEMPTS == []
    assert PAS.PROBE_REFUSALS == []
    assert PAS.PT.NET_ATTEMPTS == []


def test_import_arms_nothing_of_mine_and_leaves_the_repos_guard_up():
    """`prompt_at_turn` arms the same five primitives at ITS import (its own card).

    So the process-wide guard is already up before this module is used, and what this
    module must guarantee is narrower: importing it records nothing, and after a test
    restores its own wires the inherited guard is the one still standing (a test must not
    leave the suite weakly guarded).
    """
    assert PAS.NET_ATTEMPTS == []
    assert PAS.PT.NET_ATTEMPTS == []
    with pytest.raises(AssertionError, match="NETWORK REFUSED"):
        urllib.request.urlopen("http://127.0.0.1:9/nothing", timeout=0.2)
    # the refusal came from the inherited guard, not from a wire of mine
    assert PAS.NET_ATTEMPTS == []
    assert PAS.PT.NET_ATTEMPTS == ["urllib.request.urlopen"]
    PAS.PT.NET_ATTEMPTS.clear()


# ---------------------------------------------------- (c) the mismatch fixture
def test_mismatch_fixture_declares_at_least_twelve_binding_turns():
    """TX-04S loads through load_fixture and recomputes to >= 12 mismatch turns."""
    fx = R.load_fixture(TX04S)
    assert CPF.validate(fx) == []

    delivered = {int(t["turn"]): [to["doc_id"] for to in (t.get("tool_outputs") or [])]
                 for t in fx["turns"] if t.get("tool_outputs")}
    # the schedule is one delivery per turn: two bodies would make "the block above"
    # ambiguous and the predictor's rule would be measuring the fixture's order
    assert all(len(docs) == 1 for docs in delivered.values())

    cps = {int(c["turn"]): c for c in fx["checkpoints"]}
    mismatched = [t for t in sorted(cps)
                  if t in delivered and delivered[t][0] != cps[t]["ground_truth"]["doc"]]
    design = fx["answer_slot_design"]
    assert len(mismatched) >= 12, "the fixture must carry >= 12 binding turns"
    assert sorted(mismatched) == design["mismatch_turns"]
    assert design["mismatch_count"] == len(mismatched)
    # the decoy is never checkpointed, so re-delivering it cannot leak a truth
    assert design["decoy_mismatch_turns"], "no decoy turns declared"
    assert all(cps[t]["ground_truth"]["doc"] != "doc-fact-12" for t in cps)

    # the expected answers stay derivable from the answer_spec, not from prose
    expected = [str(c["expected"]) for c in fx["checkpoints"]]
    assert len(set(expected)) == len(expected), "duplicate expected values"
    assert all(c["answer_spec"]["derive"]["rule"] == "constant_value"
               for c in fx["checkpoints"])
