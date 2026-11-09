"""test_contract_presence.py — checkpoint contract line presence (TX-02)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
for _p in (LONGRUN, os.path.join(os.path.dirname(LONGRUN), "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-02.v1.json")


def _load_fixture():
    return R.load_fixture(FIXTURE)


def test_contract_present_exactly_once_on_every_checkpoint_turn():
    fixture = _load_fixture()
    cp_turns = set(R.checkpoint_turns(fixture))
    assert len(cp_turns) == 48
    for arm in ("transcript-grow", "pointer-stable", "lease-reopen"):
        planner = R.Planner(arm, fixture, dry_run=True)
        for t in range(1, int(fixture["N"]) + 1):
            info = planner.build(t)
            if t not in cp_turns:
                continue
            info["prompt"] = R.checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm)
            assert info["prompt"].count("CHECKPOINT TURN.") == 1, (arm, t)
            assert info["prompt"].rstrip().endswith("Anything written after that line is not read."), (arm, t)
            planner.record(t, "<<answer>>")


def test_contract_present_for_cd_arm():
    import arm_cd as A  # noqa: E402
    fixture = _load_fixture()
    cp_turns = set(R.checkpoint_turns(fixture))
    for arm in (A.ARM_C, A.ARM_D):
        planner = R.Planner(arm, fixture, dry_run=True)
        for t in range(1, int(fixture["N"]) + 1):
            info = planner.build(t)
            if t not in cp_turns:
                continue
            info["prompt"] = R.checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm)
            assert info["prompt"].count("CHECKPOINT TURN.") == 1, (arm, t)
            planner.record(t, "<<answer>>")


def test_tool_followup_path_red_when_contract_dropped():
    fixture = _load_fixture()
    cp_turns = sorted(R.checkpoint_turns(fixture))
    t = cp_turns[0]
    planner = R.Planner("pointer-stable", fixture, dry_run=True)
    info = planner.build(t)
    info["prompt"] = R.checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm)
    dropped = info["prompt"].replace(R.CHECKPOINT_CONTRACT_LINE, "")
    assert R.CHECKPOINT_CONTRACT_LINE not in dropped
    followup_green = planner.messages(info["prompt"])
    assert R.CHECKPOINT_CONTRACT_LINE in followup_green[1]["content"]
    followup_red = planner.messages(dropped)
    assert R.CHECKPOINT_CONTRACT_LINE not in followup_red[1]["content"]


def test_idempotent_checkpoint_prompt():
    fixture = _load_fixture()
    t = sorted(R.checkpoint_turns(fixture))[0]
    planner = R.Planner("pointer-stable", fixture, dry_run=True)
    info = planner.build(t)
    once = R.checkpoint_prompt(fixture, t, info["prompt"], arm=planner.arm)
    twice = R.checkpoint_prompt(fixture, t, once, arm=planner.arm)
    assert once == twice
    assert once.count("CHECKPOINT TURN.") == 1