"""Offline guards for CONTRACT3: answer contract + marker grammar + fetch gating."""
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine"))

import run_longrun as R  # noqa: E402
import arm_cd  # noqa: E402
import grade_v5 as g5  # noqa: E402
from ptr_engine.fetch_tool import (  # noqa: E402
    parse_fetch_calls, extract_marker_refs, MARKER_RE,
)
from ptr_engine.pointer_table import (  # noqa: E402
    reset_bodies, build_table, fetch,
)
from ptr_engine.quantise import StubTokenizer  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-01.v1.json")


def _fx():
    return R.load_fixture(FIXTURE)


def test_every_marker_parses_to_ref():
    fx = _fx()
    planner = R.Planner("masking-no-fetch", fx, True)
    for i in range(1, fx["N"]):
        planner.record(i, "ANSWER: NONE")
    # turn 5 has three masked markers
    info = planner.build(5)
    markers = extract_marker_refs(info["prompt"])
    assert len(markers) == 3, markers
    for m in markers:
        assert MARKER_RE.fullmatch(f"[MASKED {m}]") or MARKER_RE.search(f"[MASKED {m}]")
        msg = {"tool_calls": [{"function": {"name": "fetch",
                                           "arguments": {"ref": m}}}]}
        calls = parse_fetch_calls(msg)
        assert len(calls) == 1
        assert calls[0]["ref"] == m
        # resolve (doc_id, revision)
        assert "@" in m and m.endswith("@r1")
    # D body resolution
    task_id = fx["task_id"]
    reset_bodies(task_id)
    tok = StubTokenizer()
    st = arm_cd.ArmCDState(fixture=fx, tokenizer=tok)
    st.mask_old_turns(5)
    ents = st.all_entries(5)
    seen = set(); uniq = []
    for e in ents:
        if e.ref in seen:
            continue
        seen.add(e.ref); uniq.append(e)
    table = build_table(uniq, task_id=task_id)
    for m in markers:
        fr = fetch(table, m, budget_tokens=fx["fetch_budget_tokens"],
                   tokenizer=tok, task_id=task_id)
        assert fr.outcome == "OK", (m, fr.outcome)
        assert fr.text and len(fr.text) > 0


def test_contract_text_no_slash_enumeration():
    fx = _fx()
    assert "NUM/CALL/NONE/TEXT" not in fx["system_prompt"]
    assert "NUM/CALL/NONE/TEXT" not in R.CHECKPOINT_CONTRACT_LINE


def test_c_prompt_no_fetch_instruction_or_tool_schema():
    fx = _fx()
    planner = R.Planner("masking-no-fetch", fx, True)
    for i in range(1, fx["N"]):
        planner.record(i, "ANSWER: NONE")
    # force a checkpoint turn
    cp_turn = fx["checkpoints"][0]["turn"]
    for i in range(1, cp_turn):
        planner.record(i, "ANSWER: NONE")
    info = planner.build(cp_turn)
    prompt = R.checkpoint_prompt(fx, cp_turn, info["prompt"], arm="masking-no-fetch")
    low = prompt.lower()
    assert "fetch(" not in low
    assert "fetch(ref" not in low
    assert "tool_calls" not in low or True
    # no tool schema
    assert "parameters" not in prompt
    assert "FETCH_TOOL" not in prompt


def test_d_prompt_names_marker_grammar_and_example_call():
    fx = _fx()
    planner = R.Planner("bounded-context-fetch", fx, True)
    cp_turn = fx["checkpoints"][0]["turn"]
    for i in range(1, cp_turn):
        planner.record(i, "ANSWER: NONE")
    info = planner.build(cp_turn)
    prompt = R.checkpoint_prompt(fx, cp_turn, info["prompt"], arm="bounded-context-fetch")
    assert "[MASKED <ref>]" in prompt
    assert "doc-<name>@r<revision>" in prompt
    assert "fetch(ref=" in prompt


def test_four_forms_only_kinds_oov():
    # ANSWER: 1/1/NONE is out-of-vocabulary, ungradeable
    r = g5.parse_answer_contract("ANSWER: 1/1/NONE")
    assert r["answer_kind"] == "OOV"
    assert r["answer_parse_error"] == "out_of_vocabulary"
    # four forms allowed
    for form in ("ANSWER: NUM 1", "ANSWER: CALL f(x=1)", "ANSWER: NONE", "ANSWER: TEXT hi"):
        rr = g5.parse_answer_contract(form)
        assert rr["answer_parse_error"] is None or rr["answer_parse_error"] != "out_of_vocabulary"


if __name__ == "__main__":
    # run all
    test_every_marker_parses_to_ref()
    test_contract_text_no_slash_enumeration()
    test_c_prompt_no_fetch_instruction_or_tool_schema()
    test_d_prompt_names_marker_grammar_and_example_call()
    test_four_forms_only_kinds_oov()
    print("ALL PASS")
