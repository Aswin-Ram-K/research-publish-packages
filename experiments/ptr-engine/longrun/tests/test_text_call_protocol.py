import types
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import arm_cd  # noqa: E402
import run_longrun as R  # noqa: E402
import grade_v5  # noqa: E402


def test_text_form_fetch_executes_and_row_records_variant():
    content = 'ANSWER: CALL(fetch(ref="doc-key-1@1"))'
    resp = {"content": content}
    calls = arm_cd.parse_fetch_calls_from_response(resp)
    assert len(calls) == 1
    assert calls[0]["ref"] == "doc-key-1@r1"
    assert calls[0]["ref_as_emitted"] == "doc-key-1@1"
    assert calls[0]["protocol_variant"] == "text_call"
    assert calls[0]["ref_revision_normalised"] is True
    row = R.make_row.__wrapped__ if hasattr(R.make_row, "__wrapped__") else None
    # make_row stamping
    cfg = types.SimpleNamespace(tools="", max_tokens=256, stream=True, engine="vllm", model="m", base_url="x", claim=None, temperature=0, seed=42, fetch_policy="strict")
    fx = {"task_id": "TX-HOP", "_sha256": "x", "bytes_per_token": 4.0}
    row = R.make_row(cfg, fx, "bounded-context-fetch", 1, "rid-r1", 1, None, content, "turn", "msha", {})
    assert row["protocol_variant"] == "text_call"
    assert row["ref_as_emitted"] == "doc-key-1@1"
    assert row["ref_revision_normalised"] is True


def test_well_formed_answer_call_not_fetch_still_answer():
    parsed = grade_v5.parse_answer_contract('ANSWER: CALL foo(x=1)')
    assert parsed["answer_kind"] == "CALL"
    assert parsed["answer_value"]["callee"] == "foo"


def test_unparseable_text_call_stays_oov():
    parsed = grade_v5.parse_answer_contract('ANSWER: CALL(fetch(ref=))')
    assert parsed["answer_parse_error"] == "out_of_vocabulary"


def test_two_text_calls_execute_only_one():
    content = 'ANSWER: CALL(fetch(ref="a@1")) and ANSWER: CALL(fetch(ref="b@2"))'
    # ensure only first parsed
    calls = arm_cd.parse_text_call(content)
    assert len(calls) == 1
    # parse_fetch_calls_from_response also one
    calls2 = arm_cd.parse_fetch_calls_from_response({"content": content})
    assert len(calls2) == 1


def test_at1_normalises_for_lookup_keeps_emitted():
    norm, changed = arm_cd.normalise_ref_revision("doc-key-1@1")
    assert norm == "doc-key-1@r1"
    assert changed is True
    norm2, changed2 = arm_cd.normalise_ref_revision("doc-key-1@r1")
    assert norm2 == "doc-key-1@r1"
    assert changed2 is False


def test_missing_protocol_variant_on_text_call_row_refused():
    content = 'ANSWER: CALL(fetch(ref="doc-key-1@1"))'
    row = {"content": content}
    try:
        R.require_protocol_variant(row)
        raise AssertionError("expected refusal")
    except ValueError:
        pass
    # present -> ok
    row2 = {"content": content, "protocol_variant": "text_call"}
    assert R.require_protocol_variant(row2) is True
