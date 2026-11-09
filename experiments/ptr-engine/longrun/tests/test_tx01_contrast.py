"""Offline contrast test for TX-01: facts live only in transient tool output."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine"))

import run_longrun as R  # noqa: E402
import arm_cd  # noqa: E402
from ptr_engine.pointer_table import reset_bodies, build_table, fetch, PointerEntry  # noqa: E402
from ptr_engine.errors import PtrStoreMissError  # noqa: E402
from ptr_engine.quantise import StubTokenizer  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-01.v1.json")

FACT_STRINGS = {
    20: "RETRY_LIMIT = 3",
    22: "TIMEOUT_SECONDS = 30",
    24: "MAX_BATCH_SIZE = 64",
    26: "MAX_RETRIES = 5",
    28: "class PtrMissingRefError",
    30: 'code = "E001"',
    32: 'code = "E002"',
    34: 'code = "E003"',
    36: "DEFAULT_PAGE_SIZE = 128",
    38: "MAX_REFS = 64",
    40: 'HASH_PREFIX = "sha256"',
    42: "RETENTION_DAYS = 7",
}


def _load():
    return R.load_fixture(FIXTURE)


def _delivery_turn(fx, doc_id, revision):
    for turn in fx["turns"]:
        for to in (turn.get("tool_outputs") or []):
            if to.get("doc_id") == doc_id and int(to.get("revision")) == int(revision):
                return int(turn["turn"])
    raise AssertionError(f"no delivery turn for {doc_id}@{revision}")


def test_tx01_fact_present_in_tool_output():
    fx = _load()
    for cp in fx["checkpoints"]:
        t = cp["turn"]
        doc = cp["ground_truth"]["doc"]
        rev = cp["ground_truth"]["revision"]
        dt = _delivery_turn(fx, doc, rev)
        turn = fx["turns"][dt - 1]
        bodies = [to.get("body", "") for to in turn.get("tool_outputs", [])
                  if to.get("doc_id") == doc and int(to.get("revision")) == int(rev)]
        assert bodies, f"cp turn {t}: no tool output"
        assert FACT_STRINGS[t] in bodies[0], f"cp turn {t}: fact not in tool output"


def test_tx01_fact_absent_from_masked_prompt():
    fx = _load()
    for arm in ("masking-no-fetch", "bounded-context-fetch"):
        planner = R.Planner(arm, fx, True)
        # Realistic answer history: replay the model's actual contracted answers,
        # not a blanket ANSWER: NONE substitution.
        for i in range(1, fx["N"]):
            ans = "ANSWER: NONE"
            for cp in fx["checkpoints"]:
                if int(cp["turn"]) == i:
                    ans = cp.get("answer_form", ans)
            planner.record(i, ans)
        for cp in fx["checkpoints"]:
            t = cp["turn"]
            info = planner.build(t)
            sent = planner.messages(info["prompt"])
            prompt = "\n".join(m.get("content", "") for m in sent)
            fs = FACT_STRINGS[t]
            assert fs not in prompt, f"arm {arm} cp turn {t}: fact leaked into masked prompt"


def test_tx01_fact_recoverable_by_fetch():
    fx = _load()
    task_id = fx["task_id"]
    reset_bodies(task_id)
    tok = StubTokenizer()
    for cp in fx["checkpoints"]:
        t = cp["turn"]
        doc = cp["ground_truth"]["doc"]
        rev = cp["ground_truth"]["revision"]
        ref = f"{doc}@r{rev}"
        st = arm_cd.ArmCDState(fixture=fx, tokenizer=tok)
        st.mask_old_turns(t)
        ents = st.all_entries(t)
        seen = set()
        uniq = []
        for e in ents:
            if e.ref in seen:
                continue
            seen.add(e.ref)
            uniq.append(e)
        table = build_table(uniq, task_id=task_id)
        fr = fetch(table, ref, budget_tokens=fx["fetch_budget_tokens"],
                  tokenizer=tok, task_id=task_id)
        assert fr.outcome == "OK", f"cp turn {t}: fetch outcome {fr.outcome}"
        assert fr.text is not None and FACT_STRINGS[t] in fr.text, \
            f"cp turn {t}: fetched body missing fact"


def test_tx01_masked_turn_has_marker():
    fx = _load()
    planner = R.Planner("masking-no-fetch", fx, True)
    for i in range(1, fx["N"]):
        planner.record(i, "ANSWER: NONE")
    for cp in fx["checkpoints"]:
        t = cp["turn"]
        doc = cp["ground_truth"]["doc"]
        rev = cp["ground_truth"]["revision"]
        ref = f"{doc}@r{rev}"
        info = planner.build(t)
        assert f"[MASKED {ref}]" in info["prompt"], f"cp turn {t}: marker missing"


def test_tx01_fetch_stored_body_lookup_and_miss():
    fx = _load()
    task_id = fx["task_id"]
    reset_bodies(task_id)
    tok = StubTokenizer()
    cp = fx["checkpoints"][0]
    t = cp["turn"]
    doc = cp["ground_truth"]["doc"]
    rev = cp["ground_truth"]["revision"]
    ref = f"{doc}@r{rev}"
    st = arm_cd.ArmCDState(fixture=fx, tokenizer=tok)
    st.mask_old_turns(t)
    ents = st.all_entries(t)
    seen = set()
    uniq = []
    for e in ents:
        if e.ref in seen:
            continue
        seen.add(e.ref)
        uniq.append(e)
    table = build_table(uniq, task_id=task_id)
    # stored-body lookup: an entry with no body resolves from _BODIES
    from dataclasses import replace as _rep
    nobody = [_rep(e, body=None) for e in uniq if e.ref == ref][0]
    table2 = build_table([nobody] + [e for e in uniq if e.ref != ref], task_id=task_id)
    fr = fetch(table2, ref, budget_tokens=fx["fetch_budget_tokens"],
              tokenizer=tok, task_id=task_id)
    assert fr.outcome == "OK"
    assert fr.text is not None and FACT_STRINGS[t] in fr.text
    # missing-body failure
    reset_bodies()
    try:
        fetch(table2, ref, budget_tokens=fx["fetch_budget_tokens"],
              tokenizer=tok, task_id=task_id)
    except PtrStoreMissError:
        pass
    else:
        raise AssertionError("expected PtrStoreMissError on missing body")


def test_tx01_all_expected_distinct():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(vals) == 12
    assert len(set(vals)) == 12, f"duplicate expected values: {vals}"
    assert len(fx["checkpoints"]) == 12


def test_tx01_expected_absent_from_replayed_history():
    fx = _load()
    for arm in ("masking-no-fetch", "bounded-context-fetch"):
        planner = R.Planner(arm, fx, True)
        for i in range(1, fx["N"]):
            ans = "ANSWER: NONE"
            for cp in fx["checkpoints"]:
                if int(cp["turn"]) == i:
                    ans = cp.get("answer_form", ans)
            planner.record(i, ans)
        for cp in fx["checkpoints"]:
            t = cp["turn"]
            info = planner.build(t)
            sent = planner.messages(info["prompt"])
            prompt = "\n".join(m.get("content", "") for m in sent)
            af = cp.get("answer_form")
            assert af not in prompt, f"arm {arm} cp turn {t}: answer_form leaked"
