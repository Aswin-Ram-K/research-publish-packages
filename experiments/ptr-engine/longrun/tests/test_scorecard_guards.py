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
        {"prompt_tokens": 120, "cached_tokens": None, "uncached_tokens": 120,
         "billed_tokens": None, "turn": 1},
    ]
    b = sl.billing_block(recs)
    assert b["coverage"] == 0.5
    # cached over the WHOLE prompt total: the row with no cache counter contributed 0.
    assert b["cached_fraction_of_prompt"] == 40/220
    # cached over what the server accounted for (cached + uncached).
    assert b["cached_fraction_of_accounted"] == 40/220
    # both rows are billable: 60, plus the whole 120 prompt when no counter was reported.
    assert b["billed_tokens"] == 180
    assert b["attribution"] == "available"

def test_no_cached_counter_after_turn_one_is_unknown_not_the_whole_prompt():
    # ABSENT is not 0: past the first turn a prior prefix exists, so a missing cache
    # counter leaves the billed quantity unknown -- not the full prompt, not zero.
    recs = [{"prompt_tokens": 10, "cached_tokens": None, "turn": 5}]
    b = sl.billing_block(recs)
    assert b["cached_fraction_of_prompt"] == 0.0
    assert b["billed_tokens"] is None
    assert b["billed_tokens_known"] is None
    assert b["billed_upper_bound_tokens"] == 10
    assert b["billed_unknown_rows"] == 1
    assert b["billed_unknown_turns"] == [5]
    assert b["billed_coverage"] == 0.0
    assert b["attribution"] == "unavailable"
    assert b["coverage"] == 0.0
