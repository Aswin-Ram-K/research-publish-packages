"""RED->GREEN for the two row fields that lied about the masking arm.

`evicted` was initialised to 0 and assigned only by `transcript-grow`, so the masking
arm reported "nothing evicted" on the very turn its only fact was masked away.
`expected_present` was computed from the RESPONSE's reasoning channel, which is empty
whenever thinking is off, so it read False on every checkpoint -- including the eight
that answered correctly -- and could support no claim about absence.

Zero network: `Planner.build` renders prompts locally and `make_row` is pure.
"""
import json
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
MEASURE = os.path.join(os.path.dirname(LONG), "measure")
sys.path.insert(0, LONG)

import run_longrun as R  # noqa: E402
import score_longrun as S  # noqa: E402

FIXTURE = os.path.join(LONG, "tasks-v7", "TX-03.v1.json")
ROWS = os.path.join(MEASURE, "rows-tx03-masking-r1.jsonl")


def _fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        fixture = json.load(fh)
    # the row literal stamps the fixture digest; the file on disk may omit it
    fixture.setdefault("_sha256", "0" * 64)
    return fixture


def _cfg():
    return SimpleNamespace(
        model="fake-model", stream=True, thinking="off", max_tokens=64,
        engine="sglang", metrics_scrape=False, timeout=5.0,
        base_url="http://127.0.0.1:1/v1", turn_wall_cap=None,
        temperature=0.0, seed=42, dry_run=True, fetch_policy="strict",
        generation="test")


def _resp(text, prompt_tokens=11):
    return {
        "content": text, "content_raw": text, "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 64, "prompt_tokens": prompt_tokens, "raw_cached": None,
        "completion_tokens": 3, "wall_ms": 5.0, "latency_s": 0.005, "ttft_s": 0.001,
        "request_sha256": "a" * 64, "request_identity_complete": True,
    }


def _row(fixture, turn, prompt_text, answer="ANSWER: NONE", **extra):
    extras = {"is_checkpoint": True, "answer_turn": True, "prompt_text": prompt_text}
    extras.update(extra)
    resp = _resp(answer)
    return R.make_row(_cfg(), fixture, "masking-no-fetch", 1, "rid-degeneracy-r1",
                      turn, resp, resp["content"], "turn", "0" * 64, extras)


def _checkpoint(fixture, distance=None):
    for cp in fixture.get("checkpoints") or []:
        if distance is None or int(cp.get("distance", -1)) == int(distance):
            return cp
    raise AssertionError("no checkpoint with distance %r" % (distance,))


# ------------------------------------------------------------------ evicted
def test_masking_turn_with_one_masked_row_stamps_evicted_one():
    """RED today: `masked_rows == 1` and `evicted == 0` on the same turn."""
    fixture = _fixture()
    info = R.Planner("masking-no-fetch", fixture, dry_run=True).build(5)
    assert info["masked_rows"] == 1, info["masked_rows"]
    assert info["evicted"] == 1, (
        "turn 5 masked 1 tool-output entry but evicted=%r" % (info["evicted"],))


def test_masking_turn_with_nothing_masked_stamps_zero():
    fixture = _fixture()
    info = R.Planner("masking-no-fetch", fixture, dry_run=True).build(4)
    assert info["masked_rows"] == 0 and info["evicted"] == 0, info


def test_arm_without_an_eviction_concept_stamps_null_not_zero():
    fixture = _fixture()
    info = R.Planner("pointer-stable", fixture, dry_run=True).build(3)
    assert info["evicted"] is None, info["evicted"]


# ---------------------------------------------------------- expected_present
def test_no_checkpoint_stamps_null():
    fixture = _fixture()
    row = _row(fixture, 2, "QUESTION (T1): Work turn 1.")
    assert row["expected"] is None, row["expected"]
    assert row["expected_present"] is None, row["expected_present"]
    assert row["expected_present_source"] == "no-checkpoint"
    assert row["expected_present"] is not False, "ABSENT is not False"


def test_d2_probe_with_the_value_in_the_prompt_stamps_true():
    """RED today: the value IS in the prompt and the row said False."""
    fixture = _fixture()
    cp = _checkpoint(fixture, distance=2)
    prompt = ("QUESTION (T1): Work turn 1.\nTOOL OUTPUTS:\n"
              "TOOL_OUTPUT (%s@%s): # %s\nVAL_A = %s\nVAL_B = 1"
              % ("doc-01", 1, "doc-01", cp["expected"]))
    row = _row(fixture, int(cp["turn"]), prompt)
    assert row["expected"] == str(cp["expected"]), row["expected"]
    assert row["expected_present"] is True, (
        "prompt carries %r but expected_present=%r" % (cp["expected"],
                                                       row["expected_present"]))
    assert row["expected_present_source"] in ("prompt-digit-boundary",
                                              "prompt-val-anchor")


def test_masked_prompt_without_the_value_stamps_false():
    fixture = _fixture()
    cp = _checkpoint(fixture, distance=6)
    prompt = ("QUESTION (T5): Work turn 5.\nTOOL OUTPUTS:\n[MASKED doc-fact-01@r1]")
    row = _row(fixture, int(cp["turn"]), prompt)
    assert row["expected_present"] is False, row["expected_present"]
    assert row["expected_present_source"] == "prompt-absent"


def test_value_inside_a_longer_number_does_not_count():
    """The digit-boundary guard: 3001 must not match inside 13001."""
    fixture = _fixture()
    cp = _checkpoint(fixture, distance=2)
    value = str(cp["expected"])
    prompt = "VAL_A = 1%s" % value
    row = _row(fixture, int(cp["turn"]), prompt)
    assert row["expected_present"] is False, row["expected_present"]


def test_no_retained_prompt_stamps_null_and_says_why():
    fixture = _fixture()
    cp = _checkpoint(fixture, distance=2)
    row = _row(fixture, int(cp["turn"]), None)
    assert row["expected_present"] is None, row["expected_present"]
    assert row["expected_present_source"] == "no-prompt-retained"


def test_every_rendered_prompt_of_the_fixture_splits_eight_true_forty_false():
    """The writer's own output, on the real fixture: 8 d2 probes carry the value, the
    40 post-mask probes do not, and the 8 mask turns stamp `evicted == masked_rows`."""
    fixture = _fixture()
    planner = R.Planner("masking-no-fetch", fixture, dry_run=True)
    by_turn = {int(cp["turn"]): cp for cp in fixture.get("checkpoints") or []}
    seen = {True: 0, False: 0}
    mask_turns = []
    for t in range(1, len(fixture["turns"]) + 1):
        info = planner.build(t)
        if info["masked_rows"]:
            mask_turns.append(t)
            assert info["evicted"] == info["masked_rows"] == 1, (t, info)
        cp = by_turn.get(t)
        if cp is not None:
            present, _src = R.expected_value_in_prompt(info["prompt"], str(cp["expected"]))
            assert present is (int(cp["distance"]) == 2), (
                "turn %d (%s, d=%s) stamped %r" % (t, cp["id"], cp["distance"], present))
            seen[present] += 1
        planner.record(t, "ANSWER: NONE")
    assert seen == {True: 8, False: 40}, seen
    assert mask_turns == [5, 12, 21, 28, 49, 56, 65, 72], mask_turns


# ------------------------------------------------------------ the real corpus
def test_real_rows_file_outcome_split_is_eight_forty_zero_zero():
    with open(ROWS, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    out = S.score_answer_contract_rows(_fixture(), rows)
    arm = out["masking-no-fetch__rep1"]
    assert arm["answered_correctly"] == 8, arm["answered_correctly"]
    assert arm["abstained_after_mask"] == 40, arm["abstained_after_mask"]
    assert arm["answered_wrong"] == 0, arm["answered_wrong"]
    assert arm["unparsed"] == 0, arm["unparsed"]
    assert arm["checkpoint_accuracy"] == "8/48", arm["checkpoint_accuracy"]
    assert arm["mask_turn_by_doc"] == {
        "doc-fact-01": 5, "doc-fact-02": 12, "doc-fact-03": 21, "doc-fact-04": 28,
        "doc-fact-05": 49, "doc-fact-06": 56, "doc-fact-07": 65, "doc-fact-08": 72}
