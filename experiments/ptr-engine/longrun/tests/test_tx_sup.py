"""Offline distance (dose-response) test for TX-SUP (superseded fact)."""
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

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-SUP.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def test_tx_sup_loads_and_checker_passes():
    fx = _load()
    assert fx["task_id"] == "TX-SUP"
    assert len(fx["checkpoints"]) == 48
    assert CPF.validate(fx) == [], CPF.validate(fx)


def test_tx_sup_bucket_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 12, 6: 12, 20: 12, 32: 12}, c


def test_tx_sup_expected_unique():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(set(vals)) == 48


def test_tx_sup_48_unique_checkpoint_turns():
    fx = _load()
    turns = [cp["turn"] for cp in fx["checkpoints"]]
    assert len(set(turns)) == 48


def test_tx_sup_distances_match_measured_gap():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_tx_sup_num_only_answers():
    fx = _load()
    for cp in fx["checkpoints"]:
        assert cp["answer_form"].startswith("ANSWER: NUM "), cp["id"]


def test_tx_sup_stale_differs_from_current():
    fx = _load()
    for cp in fx["checkpoints"]:
        assert str(cp["stale_value"]) != str(cp["expected"]), cp["id"]


def test_tx_sup_stale_present_in_fixture():
    fx = _load()
    blob = json.dumps(fx)
    for cp in fx["checkpoints"]:
        assert str(cp["stale_value"]) in blob, cp["id"]


def test_tx_sup_stale_present_in_initial_revision_not_final_alone():
    fx = _load()
    # each stale value must be recoverable from an initial revision body (rev 1) in a tool output
    stale_to_intro = {}
    for cp in fx["checkpoints"]:
        stale_to_intro.setdefault(cp["stale_value"], cp["fact_introduction_turn"])
    # gather all tool-output bodies keyed by turn
    bodies_by_turn = {}
    for t in fx["turns"]:
        for to in (t.get("tool_outputs") or []):
            bodies_by_turn.setdefault(t["turn"], []).append(str(to.get("body", "")))
    for cp in fx["checkpoints"]:
        stale = str(cp["stale_value"])
        found = False
        for turn, bodies in bodies_by_turn.items():
            if turn == cp["fact_introduction_turn"]:
                continue
            if any(stale in b for b in bodies):
                found = True
                break
        assert found, f"stale value {stale} not found outside final intro turn for {cp['id']}"


def test_tx_sup_checker_fails_duplicate_expected():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs


def test_tx_sup_checker_fails_reachability():
    fx = _base()
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs


def test_tx_sup_checker_fails_distance_mismatch():
    fx = _base()
    fx["checkpoints"][0]["distance"] = 999
    errs = CPF.validate(fx)
    assert any("distance mismatch" in e for e in errs), errs


def test_tx_sup_checker_fails_ungradable():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: MAYBE 42"
    errs = CPF.validate(fx)
    assert any("ungradable" in e for e in errs), errs


def test_tx_sup_red_green_duplicate_check_toggle():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    assert CPF.validate(fx, disabled={"duplicate_expected"}) == []
    assert CPF.validate(fx) != []


def test_tx_sup_print_distance_table(capsys):
    fx = _load()
    print("fact_id | introduction_turn | checkpoint_turn | distance | stale | current")
    for cp in sorted(fx["checkpoints"], key=lambda c: (c["fact_introduction_turn"], c["distance"])):
        print(f"{cp['fact_id']} | {cp['fact_introduction_turn']} | {cp['turn']} | {cp['distance']} | {cp['stale_value']} | {cp['expected']}")
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    print("counts per distance:", dict(sorted(c.items())))
    captured = capsys.readouterr()
    assert "fact_id | introduction_turn" in captured.out


def test_tx_sup_checker_fails_duplicate_checkpoint_turn():
    fx = _base()
    fx["checkpoints"][1]["turn"] = fx["checkpoints"][0]["turn"]
    errs = CPF.validate(fx)
    assert any("duplicate checkpoint turn" in e for e in errs), errs


def test_tx_sup_checker_fails_kind_type_mismatch():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: TEXT 4000"
    errs = CPF.validate(fx)
    assert any("kind/type mismatch" in e for e in errs), errs


def test_tx_sup_checker_fails_injected_question_identity():
    fx = _base()
    fx["checkpoints"][0]["question"] = "not the injected question"
    errs = CPF.validate(fx)
    assert any("injected question" in e or "would inject" in e for e in errs), errs


def test_tx_sup_checkpoint_prompt_identity():
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


def test_tx_sup_no_arithmetic_progression_across_revisions():
    fx = _load()
    import re
    # group values per fact: stale (rev1) then current (rev2)
    facts = sorted({cp["fact_id"] for cp in fx["checkpoints"]})
    assert len(facts) == 12
    for fid in facts:
        # stale values from a rev1 tool output
        stale = None
        cur = None
        for t in fx["turns"]:
            for to in (t.get("tool_outputs") or []):
                if to.get("doc_id") == f"doc-{fid}" and to.get("revision") == 1:
                    stale = [int(x.split("=")[1]) for x in to["body"].splitlines() if "=" in x]
                if to.get("doc_id") == f"doc-{fid}" and to.get("revision") == 2:
                    cur = [int(x.split("=")[1]) for x in to["body"].splitlines() if "=" in x]
        assert stale is not None and cur is not None
        seq = stale + cur
        diffs = [seq[i+1]-seq[i] for i in range(len(seq)-1)]
        assert len(set(diffs)) > 1, (fid, diffs)
        # no constant difference across the whole sequence
        assert not all(d == diffs[0] for d in diffs), fid


def test_tx_sup_stale_differs_current_all_facts():
    fx = _load()
    facts = sorted({cp["fact_id"] for cp in fx["checkpoints"]})
    for fid in facts:
        cps = [cp for cp in fx["checkpoints"] if cp["fact_id"] == fid]
        for cp in cps:
            assert str(cp["stale_value"]) != str(cp["expected"]), (fid, cp["id"])
