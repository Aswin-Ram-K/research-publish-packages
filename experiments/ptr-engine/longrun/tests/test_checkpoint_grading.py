import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import score_longrun as sl

def _fixture(n=3):
    return {"task_id": "T", "checkpoints": [
        {"id": "cp.%d" % i, "turn": i+1, "expected": str(10+i), "distance": 1}
        for i in range(n)]}

def _row(cid, turn, ak, value, interim=False, arm="a", rep=1):
    return {"kind": "turn", "arm": arm, "rep": rep, "turn": turn,
            "checkpoint": {"id": cid, "turn": turn, "expected": str(10 + int(cid.split('.')[-1])) if False else None},
            "answer_kind": ak, "answer_value": value, "answer_parse_error": None,
            "interim": interim}

# fix checkpoint expected mapping
def make_rows():
    fx = _fixture(3)
    # map turn->expected
    exp_by_turn = {c["turn"]: c["expected"] for c in fx["checkpoints"]}
    id_by_turn = {c["turn"]: c["id"] for c in fx["checkpoints"]}
    rows = []
    for c in fx["checkpoints"]:
        cid = c["id"]; t = c["turn"]; exp = c["expected"]
        rows.append({"kind": "turn", "arm": "a", "rep": 1, "turn": t,
                     "checkpoint": {"id": cid, "turn": t, "expected": exp, "distance": 1},
                     "answer_kind": "NUM", "answer_value": int(exp),
                     "answer_parse_error": None})
    return fx, rows

def test_clean_run_grades():
    fx, rows = make_rows()
    out = sl.score_answer_contract_rows(fx, rows)
    assert out["a__rep1"]["contract_correct"] == 3
    assert out["a__rep1"]["total"] == 3
    assert out["a__rep1"]["fixture_checkpoints"] == 3

def test_interim_rows_excluded():
    fx, rows = make_rows()
    # add an interim duplicate for first checkpoint
    r = dict(rows[0]); r["interim"] = True; r["answer_value"] = 999
    rows2 = rows + [r]
    out = sl.score_answer_contract_rows(fx, rows2)
    assert out["a__rep1"]["contract_correct"] == 3
    assert out["a__rep1"]["total"] == 3

def test_duplicated_non_interim_fail_loudly():
    fx, rows = make_rows()
    r = dict(rows[0]); r["answer_value"] = 999  # non-interim duplicate
    rows2 = rows + [r]
    try:
        sl.score_answer_contract_rows(fx, rows2)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "duplicate non-interim" in str(e)
        assert rows[0]["checkpoint"]["id"] in str(e)

def test_denominator_mismatch():
    fx, rows = make_rows()
    # remove one checkpoint row -> distinct count 2 != 3
    rows2 = rows[1:]
    out = sl.score_answer_contract_rows(fx, rows2)
    assert out.get("status") == "denominator_mismatch"
