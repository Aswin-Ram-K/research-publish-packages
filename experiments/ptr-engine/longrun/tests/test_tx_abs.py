"""Offline absent-fact test for TX-ABS."""
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine"))

import run_longrun as R  # noqa: E402
import check_pointer_fixtures as CPF  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-ABS.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _squash(s):
    return " ".join(str(s or "").split()).lower()


def test_tx_abs_loads_and_checker_passes():
    fx = _load()
    assert fx["task_id"] == "TX-ABS"
    assert len(fx["checkpoints"]) == 48
    # Absent cps cannot satisfy duplicate_expected / gradability / reachability
    # (NONE is repeated and has no source value); those checks are disabled.
    errs = CPF.validate(fx, disabled={"duplicate_expected", "gradability", "reachability"})
    assert errs == [], errs


def test_tx_abs_bucket_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 12, 6: 12, 20: 12, 32: 12}, c


def test_tx_abs_absent_split():
    fx = _load()
    absent = [cp for cp in fx["checkpoints"] if cp["expected"] == "NONE"]
    answerable = [cp for cp in fx["checkpoints"] if cp["expected"] != "NONE"]
    assert len(absent) == 12
    assert len(answerable) == 36
    from collections import Counter
    ac = Counter(cp["distance"] for cp in absent)
    assert dict(ac) == {2: 3, 6: 3, 20: 3, 32: 3}, ac
    # answer_spec kinds
    for cp in absent:
        assert cp["answer_spec"]["kind"] == "NONE"
        assert cp["answer_form"] == "ANSWER: NONE"
    for cp in answerable:
        assert cp["answer_spec"]["kind"] == "NUM"
        assert cp["answer_form"].startswith("ANSWER: NUM ")


def test_tx_abs_48_unique_checkpoint_turns():
    fx = _load()
    turns = [cp["turn"] for cp in fx["checkpoints"]]
    assert len(set(turns)) == 48


def test_tx_abs_distances_match():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_tx_abs_answerable_values_distinct():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"] if cp["expected"] != "NONE"]
    assert len(vals) == 36
    assert len(set(vals)) == 36


def test_tx_abs_mechanical_absence_proof():
    fx = _load()
    turns = fx["turns"]
    items = fx["items"] or []
    system_prompt = fx["system_prompt"] or ""
    # all bodies
    all_bodies = []
    for t in turns:
        for to in (t.get("tool_outputs") or []):
            all_bodies.append(str(to.get("body", "")))
    item_bodies = [str(it.get("body", "")) for it in items if isinstance(it, dict)]

    for cp in fx["checkpoints"]:
        if cp["expected"] == "NONE":
            m = re.search(r"VAL_[A-Z]", cp["question"])
            assert m, cp["id"]
            tok = m.group(0)
            # absent: subject token appears in no body / item / system prompt
            assert tok not in "\n".join(all_bodies), cp["id"]
            assert tok not in "\n".join(item_bodies), cp["id"]
            assert tok not in system_prompt, cp["id"]
            # no candidate numeric value: expected is NONE literal
            assert cp["expected"] == "NONE"
        else:
            val = str(cp["expected"])
            # exactly one body supplies it
            hits = [b for b in all_bodies if _squash(val) in _squash(b)]
            assert len(hits) == 1, (cp["id"], len(hits))
            # not in system prompt / items / other bodies already ensured by checker reachability for answerable
            assert _squash(val) not in _squash(system_prompt), cp["id"]
            for ib in item_bodies:
                assert _squash(val) not in _squash(ib), cp["id"]
            # not in any turn question
            for t in turns:
                assert _squash(val) not in _squash(t.get("question", "")), (cp["id"], t.get("turn"))


def test_tx_abs_checker_fails_duplicate_expected_disabled_toggle():
    fx = _base()
    # removing disabled -> duplicate_expected fires
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs




def test_tx_abs_absent_subjects_distinct_and_shape():
    fx = _load()
    import re
    absent = [cp for cp in fx["checkpoints"] if cp["expected"] == "NONE"]
    answerable = [cp for cp in fx["checkpoints"] if cp["expected"] != "NONE"]
    def subj(cp):
        m = re.search(r"VAL_[A-Z]", cp["question"])
        return m.group(0)
    abs_toks = [subj(cp) for cp in absent]
    ans_toks = [subj(cp) for cp in answerable]
    # distinct
    assert len(set(abs_toks)) == len(abs_toks) == 12, abs_toks
    # shape: same prefix pattern VAL_ and single uppercase letter, length 5
    for t in abs_toks + ans_toks:
        assert re.fullmatch(r"VAL_[A-Z]", t), t
        assert len(t) == 5, t
    # no absent subject appears in any body
    all_bodies = []
    for t in fx["turns"]:
        for to in (t.get("tool_outputs") or []):
            all_bodies.append(str(to.get("body", "")))
    for cp in absent:
        tok = subj(cp)
        for b in all_bodies:
            assert tok not in b, (cp["id"], tok)
    # guard: absent must not share a token prefix that answerable do not.
    # i.e. the set of absent tokens must not be a single repeated token.
    assert len(set(abs_toks)) > 1


def test_tx_abs_absent_token_shape_comparison(capsys):
    fx = _load()
    import re
    from collections import Counter
    absent = [cp for cp in fx["checkpoints"] if cp["expected"] == "NONE"]
    answerable = [cp for cp in fx["checkpoints"] if cp["expected"] != "NONE"]
    def subj(cp):
        return re.search(r"VAL_[A-Z]", cp["question"]).group(0)
    print("ABSENT tokens:", sorted(set(subj(cp) for cp in absent)))
    print("ANSWERABLE tokens:", sorted(set(subj(cp) for cp in answerable)))
    print("absent lens:", dict(Counter(len(subj(cp)) for cp in absent)))
    print("answerable lens:", dict(Counter(len(subj(cp)) for cp in answerable)))
    captured = capsys.readouterr()
    assert "ABSENT tokens" in captured.out


def test_tx_abs_print_rows(capsys):
    fx = _load()
    print("turn | fact_id | distance | kind | expected")
    for cp in sorted(fx["checkpoints"], key=lambda c: c["turn"]):
        kind = "absent" if cp["expected"] == "NONE" else "answerable"
        print(f"{cp['turn']} | {cp['fact_id']} | {cp['distance']} | {kind} | {cp['expected']}")
    captured = capsys.readouterr()
    assert "turn | fact_id | distance" in captured.out
