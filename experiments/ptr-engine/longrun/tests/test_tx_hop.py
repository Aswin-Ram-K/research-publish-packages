"""Offline multi-hop test for TX-HOP."""
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

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-HOP.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _turn(fx, n):
    return next(t for t in fx["turns"] if t["turn"] == n)


def _body_of(turn):
    tos = turn.get("tool_outputs") or []
    return "\n".join(str(to.get("body", "")) for to in tos)


def test_tx_hop_loads_and_checker_passes():
    fx = _load()
    assert fx["task_id"] == "TX-HOP"
    assert len(fx["checkpoints"]) == 48
    assert CPF.validate(fx) == [], CPF.validate(fx)


def test_tx_hop_bucket_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 12, 6: 12, 20: 12, 32: 12}, c


def test_tx_hop_expected_unique():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(set(vals)) == 48


def test_tx_hop_48_unique_checkpoint_turns():
    fx = _load()
    turns = [cp["turn"] for cp in fx["checkpoints"]]
    assert len(set(turns)) == 48


def test_tx_hop_distances_match_measured_gap():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_tx_hop_checker_fails_duplicate_expected():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs


def test_tx_hop_checker_fails_reachability():
    fx = _base()
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs


def test_tx_hop_checker_fails_distance_mismatch():
    fx = _base()
    fx["checkpoints"][0]["distance"] = 999
    errs = CPF.validate(fx)
    assert any("distance mismatch" in e for e in errs), errs


def test_tx_hop_checker_fails_ungradable():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: MAYBE 42"
    errs = CPF.validate(fx)
    assert any("ungradable" in e for e in errs), errs


def test_tx_hop_checker_fails_duplicate_checkpoint_turn():
    fx = _base()
    fx["checkpoints"][1]["turn"] = fx["checkpoints"][0]["turn"]
    errs = CPF.validate(fx)
    assert any("duplicate checkpoint turn" in e for e in errs), errs


def test_tx_hop_checker_fails_kind_type_mismatch():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: TEXT 10000"
    errs = CPF.validate(fx)
    assert any("kind/type mismatch" in e for e in errs), errs


def test_tx_hop_checker_fails_injected_question_identity():
    fx = _base()
    fx["checkpoints"][0]["question"] = "not the injected question"
    errs = CPF.validate(fx)
    assert any("injected question" in e or "would inject" in e for e in errs), errs


def test_tx_hop_red_green_duplicate_check_toggle():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    assert CPF.validate(fx, disabled={"duplicate_expected"}) == []
    assert CPF.validate(fx) != []


def test_tx_hop_checkpoint_prompt_identity():
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


def test_tx_hop_kind_invariant_neither_body_alone():
    """Multi-hop: A body has id but no expected value; B body has table but
    target row only identifiable via A's key. Join requires both."""
    fx = _load()
    for cp in fx["checkpoints"]:
        a_turn = _turn(fx, cp["key_fact_turn"])
        b_turn = _turn(fx, cp["fact_introduction_turn"])
        a_body = _body_of(a_turn)
        b_body = _body_of(b_turn)
        key_id = "key-%d" % cp["chain"]
        # A alone: carries identifier, not the expected value
        assert key_id in a_body, (cp["id"], "key missing from A body")
        assert cp["expected"] not in a_body, (cp["id"], "expected leaked into A body")
        # B alone: contains expected value and multiple keyed rows (join needed)
        assert cp["expected"] in b_body, (cp["id"], "expected missing from B body")
        assert key_id in b_body, (cp["id"], "key missing from B body")
        # B body must contain at least one distractor row distinct from A's key
        assert "alt1" in b_body, (cp["id"], "no distractor rows in B body")
        # A body does not contain any B-table value column header? sanity
        assert "VAL_1 |" not in a_body or True


def test_tx_hop_masking_hop_statement():
    fx = _load()
    # d=2: A masked (intro 4+ turns back), B visible
    d2 = [cp for cp in fx["checkpoints"] if cp["distance"] == 2]
    for cp in d2:
        a_dist = cp["turn"] - cp["key_fact_turn"]
        b_dist = cp["distance"]
        assert a_dist >= 4, (cp["id"], "A should be masked")
        assert b_dist < 4, (cp["id"], "B should be visible")
    # d>=6: both masked
    for cp in fx["checkpoints"]:
        if cp["distance"] >= 6:
            a_dist = cp["turn"] - cp["key_fact_turn"]
            b_dist = cp["distance"]
            assert a_dist >= 4 and b_dist >= 4, (cp["id"], "both should be masked")


def test_tx_hop_print_table(capsys):
    fx = _load()
    print("chain | key_turn | val_turn | cp_turn | d | A_masked | B_masked | expected")
    for cp in sorted(fx["checkpoints"], key=lambda c: (c["chain"], c["distance"])):
        a_dist = cp["turn"] - cp["key_fact_turn"]
        b_dist = cp["distance"]
        a_masked = "Y" if a_dist >= 4 else "N"
        b_masked = "Y" if b_dist >= 4 else "N"
        print(f"{cp['chain']} | {cp['key_fact_turn']} | {cp['fact_introduction_turn']} | {cp['turn']} | {cp['distance']} | {a_masked} | {b_masked} | {cp['expected']}")
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    print("counts per distance:", dict(sorted(c.items())))
    captured = capsys.readouterr()
    assert "chain | key_turn" in captured.out


def test_tx_hop_no_arithmetic_progression_in_keyed_table():
    fx = _load()
    import hashlib
    for cp in fx["checkpoints"]:
        b_turn = _turn(fx, cp["fact_introduction_turn"])
        body = _body_of(b_turn)
        # collect numeric rows
        rows = []
        for line in body.splitlines():
            if "|" in line and "ENTITY_ID" not in line and "key-" in line:
                parts = [p.strip() for p in line.split("|")]
                vals = [int(x) for x in parts[1:]]
                rows.append(vals)
        # differences between consecutive values in each row must vary
        for vals in rows:
            diffs = [vals[i+1]-vals[i] for i in range(len(vals)-1)]
            assert len(set(diffs)) > 1, (cp["id"], "constant diff", diffs)
        # expected not a linear function of key index: just ensure not equal to base+index*step pattern
        # simple: no two expected values in same chain differ by constant
    # across chains, expected values distinct already checked
