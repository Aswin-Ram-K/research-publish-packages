"""Offline distance (dose-response) test for TX-02."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine"))

import run_longrun as R  # noqa: E402
import check_pointer_fixtures as CPF  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-02.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_tx02_loads_and_checker_passes():
    fx = _load()
    assert fx["task_id"] == "TX-02"
    assert len(fx["checkpoints"]) == 48
    assert CPF.validate(fx) == [], CPF.validate(fx)


def test_tx02_distance_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 12, 8: 12, 20: 12, 32: 12}, c


def test_tx02_expected_unique():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(set(vals)) == 48


def test_tx02_distances_match_measured_gap():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp["fact_introduction_turn"]
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_tx02_checker_fails_duplicate_expected():
    fx = _base()
    # duplicate an expected value
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs


def test_tx02_checker_fails_reachability():
    fx = _base()
    # leak a fact value into another turn's question
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs


def test_tx02_checker_fails_distance_mismatch():
    fx = _base()
    fx["checkpoints"][0]["distance"] = 999
    errs = CPF.validate(fx)
    assert any("distance mismatch" in e for e in errs), errs


def test_tx02_checker_fails_ungradable():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: MAYBE 42"
    errs = CPF.validate(fx)
    assert any("ungradable" in e for e in errs), errs


def test_tx02_red_green_duplicate_check_toggle():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    # with check disabled -> accepted
    assert CPF.validate(fx, disabled={"duplicate_expected"}) == []
    # restored -> rejected
    assert CPF.validate(fx) != []


def test_tx02_print_distance_table(capsys):
    fx = _load()
    print("fact_id | introduction_turn | checkpoint_turn | distance | expected")
    for cp in sorted(fx["checkpoints"], key=lambda c: (c["fact_introduction_turn"], c["distance"])):
        print(f"{cp['fact_id']} | {cp['fact_introduction_turn']} | {cp['turn']} | {cp['distance']} | {cp['expected']}")
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    print("counts per distance:", dict(sorted(c.items())))
    captured = capsys.readouterr()
    assert "fact_id | introduction_turn" in captured.out


def test_tx02_checker_fails_duplicate_checkpoint_turn():
    fx = _base()
    fx["checkpoints"][1]["turn"] = fx["checkpoints"][0]["turn"]
    errs = CPF.validate(fx)
    assert any("duplicate checkpoint turn" in e for e in errs), errs


def test_tx02_checker_fails_kind_type_mismatch():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: TEXT 2000"
    errs = CPF.validate(fx)
    assert any("kind/type mismatch" in e for e in errs), errs


def test_tx02_checker_fails_injected_question_identity():
    fx = _base()
    fx["checkpoints"][0]["question"] = "not the injected question"
    errs = CPF.validate(fx)
    assert any("injected question" in e or "would inject" in e for e in errs), errs
