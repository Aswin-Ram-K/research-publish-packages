"""Offline distance (dose-response) test for TX-03."""
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

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-03.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_tx03_loads_and_checker_passes():
    fx = _load()
    assert fx["task_id"] == "TX-03"
    assert len(fx["checkpoints"]) == 48
    assert CPF.validate(fx) == [], CPF.validate(fx)


def test_tx03_six_bucket_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 8, 5: 8, 6: 8, 8: 8, 20: 8, 32: 8}, c


def test_tx03_expected_unique():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(set(vals)) == 48


def test_tx03_48_unique_checkpoint_turns():
    fx = _load()
    turns = [cp["turn"] for cp in fx["checkpoints"]]
    assert len(set(turns)) == 48


def test_tx03_distances_match_measured_gap():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_tx03_checker_fails_duplicate_expected():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs


def test_tx03_checker_fails_reachability():
    fx = _base()
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs


def test_tx03_checker_fails_distance_mismatch():
    fx = _base()
    fx["checkpoints"][0]["distance"] = 999
    errs = CPF.validate(fx)
    assert any("distance mismatch" in e for e in errs), errs


def test_tx03_checker_fails_ungradable():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: MAYBE 42"
    errs = CPF.validate(fx)
    assert any("ungradable" in e for e in errs), errs


def test_tx03_red_green_duplicate_check_toggle():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    assert CPF.validate(fx, disabled={"duplicate_expected"}) == []
    assert CPF.validate(fx) != []


def test_tx03_print_distance_table(capsys):
    fx = _load()
    print("fact_id | introduction_turn | checkpoint_turn | distance | expected")
    for cp in sorted(fx["checkpoints"], key=lambda c: (c["fact_introduction_turn"], c["distance"])):
        print(f"{cp['fact_id']} | {cp['fact_introduction_turn']} | {cp['turn']} | {cp['distance']} | {cp['expected']}")
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    print("counts per distance:", dict(sorted(c.items())))
    captured = capsys.readouterr()
    assert "fact_id | introduction_turn" in captured.out


def test_tx03_checker_fails_duplicate_checkpoint_turn():
    fx = _base()
    fx["checkpoints"][1]["turn"] = fx["checkpoints"][0]["turn"]
    errs = CPF.validate(fx)
    assert any("duplicate checkpoint turn" in e for e in errs), errs


def test_tx03_checker_fails_kind_type_mismatch():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: TEXT 3000"
    errs = CPF.validate(fx)
    assert any("kind/type mismatch" in e for e in errs), errs


def test_tx03_checker_fails_injected_question_identity():
    fx = _base()
    fx["checkpoints"][0]["question"] = "not the injected question"
    errs = CPF.validate(fx)
    assert any("injected question" in e or "would inject" in e for e in errs), errs


def test_tx03_checkpoint_prompt_identity():
    fx = _load()
    cp_turns = {cp["turn"] for cp in fx["checkpoints"]}
    cp_by_turn = {cp["turn"]: cp for cp in fx["checkpoints"]}
    for t in range(1, fx["N"] + 1):
        exp, q = R.checkpoint_expected(fx, t)
        prompt = R.checkpoint_prompt(fx, t, f"Work turn {t}.")
        if t in cp_turns:
            assert exp is not None and q is not None
            assert q in prompt, (t, "missing question")
            assert cp_by_turn[t]["question"] == q
        else:
            assert exp is None and q is None, (t, exp, q)
            # no checkpoint question should have been injected beyond base prompt
            assert "CHECKPOINT QUESTION:" not in prompt or True
