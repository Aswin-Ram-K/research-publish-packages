#!/usr/bin/env python3
"""test_refusal_fix2.py - three classes, never merged.

NONE -> refusal; TEXT -> prose; out-of-vocabulary (incl. NOT-AN-ANSWER) -> OOV
ungradeable, never a refusal, never abstained_correctly.
"""
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); LONGRUN=os.path.dirname(HERE)
sys.path.insert(0,LONGRUN)
import grade_v5 as g5
sys.path.insert(0, os.path.join(os.path.dirname(LONGRUN),'tools'))
try:
    import score_longrun as sl
except Exception:
    sl=None

def _truth(expected=64):
    return {"checkpoint_id":"t.n","turn":1,"kind":"NUM","expected":expected,
            "derivation":{"kind":"constant_value"},"source":"src"} 

def test_none_is_refusal_and_counted():
    p=g5.parse_answer_contract("ANSWER: NONE")
    assert p["answer_kind"]=="NONE"
    assert g5.is_abstention(p) is True
    assert p["answer_parse_error"] is None

def test_not_an_answer_is_oov_not_refusal():
    p=g5.parse_answer_contract("ANSWER: NOT-AN-ANSWER")
    assert p["answer_kind"]=="OOV"
    assert p["answer_parse_error"]=="out_of_vocabulary"
    assert p["detail"]["offending_token"]=="NOT-AN-ANSWER"
    assert p["answer_raw"]=="ANSWER: NOT-AN-ANSWER"
    assert g5.is_abstention(p) is False
    cell=g5.grade_cell(_truth(),p)
    assert cell["verdict"]=="undecidable" and cell.get("ungradeable") is True
    assert cell["offending_token"]=="NOT-AN-ANSWER"

def test_prose_text():
    p=g5.parse_answer_contract("ANSWER: TEXT hello world")
    assert p["answer_kind"]=="TEXT" and p["answer_value"]=="hello world"
    assert g5.is_abstention(p) is False

def test_num_correct_and_wrong_value():
    good=g5.parse_answer_contract("ANSWER: NUM 64")
    bad=g5.parse_answer_contract("ANSWER: NUM 65")
    gc=g5.grade_cell(_truth(),good); bc=g5.grade_cell(_truth(),bad)
    assert gc["verdict"]=="pass"
    assert bc["verdict"]=="fail" and bc["reason"]=="num_mismatch"
