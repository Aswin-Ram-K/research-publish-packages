"""TX-05C chain fixture: the pointer-only reference and its break classifier.

Red->green record (house style).  The leak check was written first and observed
failing: with the carry value interpolated into the use-turn question,
``check_pointer_fixtures.validate`` reported

    chain.pairs[0] carry value '4017' leaked into the use_turn 36 question

and with the pointer text restored it reports nothing.  The classifier test was
written against a synthetic row set in which one arm loses the value (expected_present
False) and one arm still carries it (True); before the two-way attribution existed both
were counted as "the fold broke the chain".
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
for _p in (LONGRUN, os.path.join(LONGRUN, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import analyze_chain as AC  # noqa: E402
import build_chain_fixture as B  # noqa: E402
import check_pointer_fixtures as CPF  # noqa: E402


def test_fixture_lints_clean():
    fx = B.build()
    assert CPF.validate(fx) == []


def test_fold_sits_between_reference_and_carry():
    fx = B.build()
    fold = fx["chain"]["fold_turn"]
    for pair in fx["chain"]["pairs"]:
        assert pair["ref_turn"] < fold < pair["use_turn"]


def test_carry_value_is_not_in_the_question():
    fx = B.build()
    for pair in fx["chain"]["pairs"]:
        q = fx["turns"][pair["use_turn"] - 1]["question"]
        carry = next(c for c in fx["checkpoints"]
                     if c["id"] == pair["carry_checkpoint"])
        assert carry["expected"] not in q
        assert q == pair["pointer_text"]


def test_leak_is_caught():
    """Red->green: interpolating the value must fail the lint."""
    fx = B.build()
    pair = fx["chain"]["pairs"][0]
    ut = pair["use_turn"]
    carry = next(c for c in fx["checkpoints"] if c["id"] == pair["carry_checkpoint"])
    fx["turns"][ut - 1]["question"] = (
        f"Using the symbol you identified at step {pair['ref_turn']} — do not restate "
        f"it — report {carry['expected']}.")
    errs = CPF.validate(fx)
    assert any("leaked into the use_turn" in e for e in errs), errs


def _row(arm, rep, turn, expected, verified, present, compactions=1):
    return {"arm": arm, "rep": rep, "turn": turn, "checkpoint": {"id": f"cp-{turn}"},
            "expected": expected, "answer_value": expected if verified else "0",
            "answer_verified": verified, "expected_present": present,
            "expected_present_source": "prompt-digit-boundary",
            "compactions": compactions}


def test_classifier_separates_fold_from_model_error():
    fx = B.build()
    pair = fx["chain"]["pairs"][0]
    rt, ut = pair["ref_turn"], pair["use_turn"]
    rows = [
        _row("masking-no-fetch", 1, rt, "4011", True, True),
        _row("masking-no-fetch", 1, ut, "4017", False, False),
        {"arm": "masking-no-fetch", "rep": 1, "turn": rt + 1,
         "kind": "tool-followup", "fetch_followup": True},
        _row("pinned", 1, rt, "4011", True, True),
        _row("pinned", 1, ut, "4017", False, True),
    ]
    res = AC.analyse(rows, fx, "<synthetic>", "/tmp")
    assert res["arms"]["masking-no-fetch"]["counts"]["lost_then_failed"] == 1
    assert res["arms"]["pinned"]["counts"]["present_then_failed"] == 1
    assert res["arms"]["masking-no-fetch"]["refetch_count"] == 1
    assert res["arms"]["pinned"]["refetch_count"] == 0


def test_unknown_presence_is_never_counted_as_signal():
    fx = B.build()
    pair = fx["chain"]["pairs"][0]
    rows = [
        _row("spcc", 1, pair["ref_turn"], "4011", True, True),
        _row("spcc", 1, pair["use_turn"], "4017", False, None),
    ]
    res = AC.analyse(rows, fx, "<synthetic>", "/tmp")
    assert res["arms"]["spcc"]["counts"]["unclassified"] == 1
    assert res["arms"]["spcc"]["counts"]["lost_then_failed"] == 0
