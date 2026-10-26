"""Offline tests for VLLM-CELL. No network: the POST is monkeypatched."""

import importlib.util
import os
import sys

import pytest

CELL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vllm_cell.py")
spec = importlib.util.spec_from_file_location("vllm_cell", CELL)
cell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cell)


class FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


# 1. details absent -> None + "unavailable", NOT 0
def test_details_absent_is_null_not_zero():
    row = cell.parse_row({"usage": {"prompt_tokens": 1000}}, "R", 1, "abc", False)
    assert row["cached_tokens"] is None
    assert row["cache_report"] == "unavailable"
    assert row["uncached_tokens"] is None  # not 1000-0


# 2. cached_tokens: 128 -> 128
def test_cached_tokens_reported():
    payload = {"usage": {"prompt_tokens": 1000,
                         "prompt_tokens_details": {"cached_tokens": 128}}}
    row = cell.parse_row(payload, "R", 1, "abc", False)
    assert row["cached_tokens"] == 128
    assert row["cache_report"] == "reported"
    assert row["uncached_tokens"] == 872


# 2b. details present but the cached key itself absent -> still null
def test_details_present_key_absent_is_null():
    payload = {"usage": {"prompt_tokens": 1000, "prompt_tokens_details": {}}}
    row = cell.parse_row(payload, "R", 1, "abc", False)
    assert row["cached_tokens"] is None
    assert row["cache_report"] == "unavailable"


# 3. status 500 -> raises
def test_http_500_raises(monkeypatch):
    monkeypatch.setattr(cell.requests, "post", lambda *a, **k: FakeResp(500, {}))
    with pytest.raises(RuntimeError):
        cell.post_chat("http://x", "m", [{"role": "user", "content": "hi"}])


# 3b. a 500 aborts the run without writing a row
def test_http_500_writes_no_row(monkeypatch, tmp_path):
    monkeypatch.setattr(cell.requests, "post", lambda *a, **k: FakeResp(500, {}))
    with pytest.raises(RuntimeError):
        cell.run("http://x", "m", ("R",), 3, 32768, str(tmp_path), False)
    rows = tmp_path / "rows.jsonl"
    assert not rows.exists() or rows.read_text() == ""


# 4. two arms rendering identical bytes -> ARMS_IDENTICAL
def test_arms_identical_raises(monkeypatch):
    original = cell.render
    monkeypatch.setattr(cell, "render",
                        lambda arm, turn: original("R", turn))
    with pytest.raises(RuntimeError, match="ARMS_IDENTICAL"):
        cell.assert_arms_distinct()


# 5. R and A at the same turn differ in bytes
def test_R_and_A_differ():
    assert cell.render("R", 7)[0]["content"] != cell.render("A", 7)[0]["content"]


# extra: the real four arms are pairwise distinct at the contracted probe turns
def test_four_arms_pairwise_distinct():
    cell.assert_arms_distinct()


# extra: pairwise distinct across the WHOLE battery, not just turn 1/20.
# This catches an arm that renders another arm's bytes at ANY turn in the run,
# which the two-turn probe would miss.
def test_four_arms_pairwise_distinct_every_turn():
    for turn in range(1, cell.DEFAULT_TURNS + 1):
        texts = {arm: cell.render(arm, turn)[0]["content"] for arm in cell.ARMS}
        assert len(set(texts.values())) == len(cell.ARMS), \
            "arms collided at turn %d" % turn


# extra: H's compaction actually bites once a summary boundary is in the index
def test_hybrid_compacts_at_summary_boundary():
    # The index at turn t holds deltas 1..t-1, so the first fold lands at turn
    # SUMMARY_EVERY+1 (the first summary-multiple delta is t=8).
    boundary = cell.SUMMARY_EVERY + 1
    at_fold = cell.render("H", boundary)[0]["content"]
    before = cell.render("H", boundary - 1)[0]["content"]
    assert "SUMMARY[" in at_fold, "no compaction event at the first summary boundary"
    assert "SUMMARY[" not in before, "compaction fired before the first boundary"
    assert at_fold != cell.render("A", boundary)[0]["content"], "H did not compress"
    # the folded delta keeps its FINAL line, so a fold that only relabels the first
    # 90 clipped chars is byte-identical to a plain summary and must not pass
    folded = [l for l in at_fold.splitlines() if "SUMMARY[" in l][0]
    assert cell.delta_block(cell.SUMMARY_EVERY).splitlines()[-1] in folded, \
        "fold dropped the delta's final line -- it is a relabel, not a compression"


# extra: rendering is deterministic (no clock, no randomness)
def test_render_is_deterministic():
    for arm in cell.ARMS:
        assert cell.render(arm, 20) == cell.render(arm, 20)


# extra: budget truncation sets the flag and is recorded
def test_budget_truncation_flag():
    messages, truncated = cell.fit_budget(cell.render("R", 40), 10)
    assert truncated is True
    assert len(messages[0]["content"]) <= 40


def test_no_truncation_when_under_budget():
    messages, truncated = cell.fit_budget(cell.render("A", 3), 32768)
    assert truncated is False
    assert messages == cell.render("A", 3)


# extra: a full stubbed run writes the contracted row keys
def test_stubbed_run_writes_contracted_keys(monkeypatch, tmp_path):
    payload = {"usage": {"prompt_tokens": 900,
                         "prompt_tokens_details": {"cached_tokens": 64}}}
    monkeypatch.setattr(cell.requests, "post", lambda *a, **k: FakeResp(200, payload))
    written, path = cell.run("http://x", "m", ("R", "A"), 2, 32768, str(tmp_path), False)
    assert written == 4
    lines = [json.loads(l) for l in open(path)]
    assert set(lines[0]) == set(cell.parse_row({}, "R", 1, "", False))
    assert all(r["cached_tokens"] == 64 for r in lines)


import json  # noqa: E402  (used by the stubbed-run test above)
