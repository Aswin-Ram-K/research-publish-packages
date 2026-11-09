#!/usr/bin/env python3
"""test_gate01_control.py - gate 0.1 positive control on the v4 fixture.

Scorer unit tests on synthetic input: these construct run logs in memory and
score them with score_longrun.py. They spend zero model requests and are NOT
measured evidence of any arm.

Cases:
  1. a correct synthetic transcript scores verified_success=True with zero failed
     required checks.
  2. ANSWER: NUM 65 fails cp1 (cp.t12) and ANSWER: NUM 64 passes it; the
     comparison is exact string equality on the parsed value ("65" != "64").
  3. a cp3 answer missing one of the three facts fails.
  4. truncated working set -> verified_success=False, failed_required ==
     [acc.2, acc.3, acc.4].
  5. verify turn omitting "exit 0" -> verified_success=False, failed_required ==
     [acc.2].
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)

import score_longrun as sl

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "LR-01.v4.json")


def sha_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_fixture():
    raw = open(FIXTURE, "rb").read()
    fx = json.loads(raw.decode("utf-8"))
    return sl.normalise_fixture(fx, hashlib.sha256(raw).hexdigest())


def make_log(contents):
    fixture_sha = sha_file(FIXTURE)
    rows = [{"fixture_sha256": fixture_sha, "task_id": "LR-01", "arm": "B", "rep": 1}]
    for turn in range(1, 49):
        txt = contents.get(turn, "work turn %d" % turn)
        if turn == 30:
            txt = contents.get(30, "restore the typed guard deleted at turn 8")
        rows.append({"turn": turn, "arm": "B", "rep": 1, "content": txt,
                     "tokens": 10})
    return rows, fixture_sha


def score_contents(contents):
    rows, fixture_sha = make_log(contents)
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    fx = load_fixture()
    run = sl.load_run(path)
    card = sl.score(fx, run, sha_file(FIXTURE))
    os.remove(path)
    return card


GOOD_CONTENT = (
    "pytest tests/test_scope.py and tests/test_negative_controls.py exit 0\n"
    "PtrNotAReferenceError PTR_NOT_A_REFERENCE ledger\n"
    "def test_ tests/test_scope.py 9"
)


def test_correct_transcript_grades_true():
    contents = {
        12: "ANSWER: NUM 64",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: GOOD_CONTENT,
    }
    card = score_contents(contents)
    assert card["verified_success"] is True, card.get("failed_required")
    assert card["failed_required"] == [], card.get("failed_required")
    assert card["checkpoint_accuracy"] == "3/3", card.get("checkpoint_accuracy")
    # scorer unit test on synthetic input, not measured evidence


def test_num_65_fails_cp1_num_64_passes():
    # 65 fails
    contents = {
        12: "ANSWER: NUM 65",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: GOOD_CONTENT,
    }
    card = score_contents(contents)
    # exact comparison: parsed value "65" != expected "64"
    assert "cp.t12" in card["failed_required"], card["failed_required"]
    # 64 passes
    contents[12] = "ANSWER: NUM 64"
    card2 = score_contents(contents)
    assert "cp.t12" not in card2["failed_required"], card2["failed_required"]
    assert card2["verified_success"] is True


def test_cp3_missing_fact_fails():
    contents = {
        12: "ANSWER: NUM 64",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=...)",
        48: GOOD_CONTENT,
    }
    card = score_contents(contents)
    assert "cp.t46" in card["failed_required"], card["failed_required"]


def test_truncated_working_set_negative():
    contents = {
        12: "ANSWER: NUM 64",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: "truncated working set: only three Ptr error classes visible",
    }
    card = score_contents(contents)
    assert card["verified_success"] is False
    assert card["failed_required"] == ["acc.2", "acc.3", "acc.4"], card["failed_required"]


def test_verify_turn_missing_exit_0_negative():
    contents = {
        12: "ANSWER: NUM 64",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: ("pytest tests/test_scope.py and tests/test_negative_controls.py\n"
             "PtrNotAReferenceError PTR_NOT_A_REFERENCE ledger\n"
             "def test_ tests/test_scope.py 9"),
    }
    card = score_contents(contents)
    assert card["verified_success"] is False
    assert card["failed_required"] == ["acc.2"], card["failed_required"]


def test_same_log_scores_identically_twice():
    """Determinism: full structured scorecard is byte-identical across two runs."""
    contents = {
        12: "ANSWER: NUM 64",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: GOOD_CONTENT,
    }
    card1 = score_contents(contents)
    card2 = score_contents(contents)
    assert card1 == card2, (card1, card2)
    assert card1["exit_code"] == card2["exit_code"]
    import json as _json
    assert _json.dumps(card1, sort_keys=True) == _json.dumps(card2, sort_keys=True)


def test_tampered_fixture_exits_2_and_differs_from_wrong_value():
    import hashlib
    import json
    import os
    import shutil
    import tempfile

    # wrong-value scenario (exit 1, not tampered) for discrimination
    contents = {
        12: "ANSWER: NUM 65",
        24: "ANSWER: NUM 31",
        30: "restore the typed guard deleted at turn 8",
        46: "ANSWER: CALL ledger.record_refusal(code=error.code, scope=..., serialized_ref=text)",
        48: GOOD_CONTENT,
    }
    card_wrong = score_contents(contents)
    assert card_wrong["tampered"] is False
    assert card_wrong["exit_code"] == 1
    assert "cp.t12" in card_wrong["failed_required"]

    # tamper: mutate a copy of the fixture under the scratch area
    scratch_dir = os.path.join(ROOT, "experiments", "ptr-engine", "state", "scratch", "gate01-tamper")
    os.makedirs(scratch_dir, exist_ok=True)
    copy_path = os.path.join(scratch_dir, "LR-01.v4.tampered.json")
    try:
        shutil.copyfile(FIXTURE, copy_path)
        raw = open(copy_path, "rb").read()
        mutated = raw.replace(b"64", b"65", 1)
        assert mutated != raw
        open(copy_path, "wb").write(mutated)

        # run log recorded against the ORIGINAL fixture digest
        rows, _ = make_log(contents)
        fd, run_path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")

        fx_raw = open(copy_path, "rb").read()
        fx = sl.normalise_fixture(json.loads(fx_raw.decode("utf-8")),
                                 hashlib.sha256(fx_raw).hexdigest())
        run = sl.load_run(run_path)
        card_tampered = sl.score(fx, run, hashlib.sha256(fx_raw).hexdigest())
        assert card_tampered["tampered"] is True, card_tampered
        assert card_tampered["exit_code"] == 2, card_tampered.get("exit_code")
        os.remove(run_path)
    finally:
        if os.path.exists(copy_path):
            os.remove(copy_path)
        if os.path.exists(scratch_dir):
            try:
                os.rmdir(scratch_dir)
            except OSError:
                pass

    assert not os.path.exists(copy_path)
    assert not os.path.exists(scratch_dir)
