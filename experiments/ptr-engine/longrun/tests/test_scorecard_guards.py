import os, sys, json, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import score_longrun as sl

def _fixture(n=3):
    return {"task_id": "T", "checkpoints": [
        {"id": "cp.%d" % i, "turn": i+1, "expected": str(10+i), "distance": 1}
        for i in range(n)]}

def _row(cid, turn, ak, value, interim=False, arm="a", rep=1, billing=None):
    r = {"kind": "turn", "arm": arm, "rep": rep, "turn": turn,
         "checkpoint": {"id": cid, "turn": turn, "expected": str(10 + int(cid.split('.')[-1])) if False else None},
         "answer_kind": ak, "answer_value": value, "answer_parse_error": None,
         "interim": interim}
    if billing:
        r.update(billing)
    # fix expected
    return r

def make_rows():
    fx = _fixture(3)
    rows = []
    for c in fx["checkpoints"]:
        cid = c["id"]; t = c["turn"]; exp = c["expected"]
        rows.append({"kind": "turn", "arm": "a", "rep": 1, "turn": t,
                     "checkpoint": {"id": cid, "turn": t, "expected": exp, "distance": 1},
                     "answer_kind": "NUM", "answer_value": int(exp),
                     "answer_parse_error": None})
    # fix checkpoint expected in rows
    for r, c in zip(rows, fx["checkpoints"]):
        r["checkpoint"]["expected"] = c["expected"]
    return fx, rows

def test_dup_fail_loudly_names_ids_and_rows():
    fx, rows = make_rows()
    r = dict(rows[0]); r["answer_value"] = 999
    rows2 = rows + [r]
    try:
        sl.score_answer_contract_rows(fx, rows2)
        assert False
    except ValueError as e:
        msg = str(e)
        assert "duplicate non-interim" in msg
        assert rows[0]["checkpoint"]["id"] in msg
        assert "rows" in msg

def test_denominator_mismatch():
    fx, rows = make_rows()
    rows2 = rows[1:]
    out = sl.score_answer_contract_rows(fx, rows2)
    assert out.get("status") == "denominator_mismatch"
    assert out.get("exit_code") != 0

def test_oov_ungradeable_not_abstention():
    fx, rows = make_rows()
    r = dict(rows[0])
    r["answer_kind"] = "OOV"
    r["answer_parse_error"] = "out_of_vocabulary"
    r["answer_value"] = None
    rows2 = list(rows)
    rows2[0] = r
    out = sl.score_answer_contract_rows(fx, rows2)
    a = out["a__rep1"]
    assert a["ungradeable"] >= 1
    assert a["abstained"] == 0

def test_null_cached_coverage():
    # score() path
    import hashlib
    # use synthetic fixture? Just billing_block directly
    recs = [
        {"prompt_tokens": 100, "cached_tokens": 40, "uncached_tokens": 60, "billed_tokens": None},
        {"prompt_tokens": 120, "cached_tokens": None, "uncached_tokens": 120, "billed_tokens": None},
    ]
    b = sl.billing_block(recs)
    assert b["coverage"] == 0.5
    assert b["cached_fraction"] == 40/100
    assert b["attribution"] == "available"

def test_no_cached_unavailable():
    recs = [{"prompt_tokens": 10, "cached_tokens": None}]
    b = sl.billing_block(recs)
    assert b["cached_fraction"] is None
    assert b["attribution"] == "unavailable"
    assert b["coverage"] == 0.0
