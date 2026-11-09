"""V-TOOL-CHANNEL — adversarial tests for the TOOL-CHANNEL-WIRE claim.

This file is a VERIFIER's file, not the author's.  It re-derives each claim from the
code and tries to break it; where the code disagrees with the hand-off, the test pins
the OBSERVED behaviour and says so in the name/docstring (and one expectation the
hand-off implies is marked ``xfail(strict=True)`` so the disagreement is visible
instead of silently passing).

Offline: every HTTP reply is a fake folded through the real ``client.send_chat`` with a
recording opener, and ``run_longrun.send_chat`` is replaced by a scripted sender.  No
socket, no subprocess, no fixture write.
"""
from __future__ import annotations

import json
import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.abspath(os.path.join(HERE, "..", "longrun"))
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import claim_mode  # noqa: E402
import client  # noqa: E402
import run_longrun  # noqa: E402

#: The tools-off request identity measured BEFORE the change (hand-off evidence).
PRE_FIX_TOOLS_OFF_DIGEST = (
    "f0499dd1335cccb27db359bee8d29c02a0f3015ee8e734404f288fbff0e2f8da")
#: The tools-on identity the hand-off reports for the same message set.
TOOLS_ON_DIGEST = (
    "3c0ff847d9689168b17ab8c50dbd754d7f67cc3f590f7b387ac74a32f2ee6561")

MESSAGES = [{"role": "system", "content": "sys"}, {"role": "user", "content": "read it"}]
HISTORICAL = [{"role": "user", "content": "hi"}]
FIXTURE_PATH = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")

PROBE_CALL = {
    "id": "call_0ffd2bc459de42e790223702",
    "type": "function",
    "function": {
        "name": "read_file",
        "arguments": ('{"path": "ptr_engine/resolve.py", "start_line": 66,'
                      ' "end_line": 110}'),
    },
}


def _cfg(**over):
    base = dict(model="occamy-1.0", base_url="http://fake.invalid/v1", engine="sglang",
                stream=False, max_tokens=64, thinking="off", tools="", tools_choice=None,
                metrics_scrape=False, timeout=5.0, turn_wall_cap=None,
                claim=claim_mode.resolve_claim("smoke"))
    base.update(over)
    return types.SimpleNamespace(**base)


def _payload(content="", tool_calls=None, finish_reason="stop"):
    message = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {"choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14}}


class _FakeHTTP:
    def __init__(self, payload):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _RecordingOpener:
    def __init__(self, payload):
        self.payload = payload
        self.requests: list[dict] = []

    def __call__(self, req, timeout):
        self.requests.append({"url": req.full_url, "body": json.loads(req.data)})
        return _FakeHTTP(self.payload)


class _ScriptedSend:
    """Stand-in for run_longrun.send_chat: real client fold, counted sends."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.messages: list[list] = []

    def __call__(self, cfg, messages):
        self.messages.append(messages)
        if not self.replies:
            raise AssertionError("a fetch round was billed more times than scripted")
        return client.send_chat(cfg, messages,
                                opener=_RecordingOpener(self.replies.pop(0)))


def _fixture():
    return run_longrun.load_fixture(FIXTURE_PATH)


def _fetch(cfg, initial, monkeypatch, scripted):
    fake = _ScriptedSend(scripted)
    monkeypatch.setattr(run_longrun, "send_chat", fake)
    out = run_longrun.fetch_rounds(
        cfg, _fixture(), "transcript-grow", 1, "run-attack", 3, "manifest", {},
        MESSAGES, initial, 1, 50, 0, served={}, pinned=[], per_turn_cap=2,
        may_request=lambda: True)
    return fake, out


# ============================================================ 1. byte neutrality
def test_attack1_tools_off_body_never_gains_tools_in_any_off_shape():
    """Every tools-off declaration must serialise the exact legacy body + digest."""
    shapes = [
        ("absent", None),
        ("empty", {"tools": ""}),
        ("none-word", {"tools": "none"}),
        ("None", {"tools": None}),
        ("False", {"tools": False}),
        ("0", {"tools": 0}),
        ("wrong-list", {"tools": ["read_file"]}),   # a list is NOT the string flag
        ("other-tool", {"tools": "write_file"}),
    ]
    for label, over in shapes:
        cfg = _cfg(**(over or {}))
        if over is None:
            delattr(cfg, "tools")
        body = client.request_body(cfg, HISTORICAL)
        assert "tools" not in body, (label, list(body))
        assert "tool_choice" not in body, (label, list(body))
        assert client.tools_body_members(cfg) == {}, label
        assert client.request_digest(body) == PRE_FIX_TOOLS_OFF_DIGEST, label
        assert list(body) == ["model", "messages", "temperature", "max_tokens", "stream",
                              "chat_template_kwargs"], label


def test_attack1_mutate_after_build_cannot_retrofit_tools_onto_the_body():
    """Aliasing/mutate-after-build: flipping cfg.tools later must not touch the body."""
    cfg = _cfg(tools="")
    body = client.request_body(cfg, HISTORICAL)
    sent = json.dumps(body)                    # the bytes as send_chat would build them
    cfg.tools = "read_file"                    # mutate AFTER the body exists
    assert "tools" not in body
    assert json.dumps(body) == sent
    assert client.request_digest(body) == PRE_FIX_TOOLS_OFF_DIGEST


def test_attack1_tools_off_wire_body_carries_no_tools_member():
    """The REAL send path (not just request_body): a tools-off request has no schema."""
    opener = _RecordingOpener(_payload(content="ok"))
    client.send_chat(_cfg(tools=""), MESSAGES, opener=opener)
    wire = opener.requests[0]["body"]
    assert "tools" not in wire and "tool_choice" not in wire
    assert list(wire) == ["model", "messages", "temperature", "max_tokens", "stream",
                          "chat_template_kwargs"]


def test_attack1_tools_on_body_shape_and_digest():
    body = client.request_body(_cfg(tools="read_file"), HISTORICAL)
    assert list(body)[-2:] == ["tools", "tool_choice"]
    assert len(body["tools"]) == 1
    fn = body["tools"][0]["function"]
    assert fn["name"] == "read_file"
    params = fn["parameters"]
    assert params["required"] == ["path", "start_line", "end_line"]
    assert set(params["properties"]) == {"path", "start_line", "end_line"}
    assert body["tool_choice"] == "auto"
    assert client.request_digest(body) == TOOLS_ON_DIGEST


def test_attack1_tool_choice_follows_the_mode():
    """``tool_choice`` appears only on a tools-on body, and reflects cfg.tool_choice."""
    assert "tool_choice" not in client.request_body(_cfg(tools=""), HISTORICAL)
    assert client.request_body(_cfg(tools="read_file"),
                               HISTORICAL)["tool_choice"] == "auto"
    # NOTE: the cfg attribute is `tool_choice` (NOT `tools_choice`), and no CLI flag
    # sets it — the mode can only be "required" when a caller injects cfg.tool_choice.
    assert client.request_body(_cfg(tools="read_file", tool_choice="required"),
                               HISTORICAL)["tool_choice"] == "required"
    # an invalid choice falls back to auto rather than putting junk on the wire
    assert client.request_body(_cfg(tools="read_file", tool_choice="bogus"),
                               HISTORICAL)["tool_choice"] == "auto"
    # the wire flag the runner actually exposes is --tools only
    assert client.tools_choice(_cfg(tools="read_file", tools_choice="required")) == "auto"


# ======================================================== 2. double consumption
def test_attack2_structured_and_text_in_one_reply_bills_exactly_one_round(monkeypatch):
    """One reply carrying BOTH shapes: structured wins, nothing is billed twice."""
    text = ('<tool_call>read_file <tool_call>{"path": "ptr_engine/resolve.py",'
            ' "start_line": 66, "end_line": 110}')
    initial = client.send_chat(
        _cfg(tools="read_file"), MESSAGES,
        opener=_RecordingOpener(_payload(content=text, tool_calls=[PROBE_CALL],
                                         finish_reason="tool_calls")))
    assert initial["tool_calls"] and initial["content"] == text
    fake, (_m, _r, sent, rounds, turn_calls, followups) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [_payload(content="answer")])
    assert len(fake.messages) == 1, "one follow-up send, not two"
    assert (sent, rounds) == (2, 1)
    assert len(followups) == 1 and followups[0]["billed_round"] is True
    assert len(turn_calls) == 1, "one call record for one request, not two"
    assert turn_calls[0]["executed"] is True
    # OBSERVED: execute_tool_call rebuilds the record and DROPS `source`/`call_id`, so
    # the row cannot say the call came from the structured channel (see report).
    assert "source" not in turn_calls[0] and "call_id" not in turn_calls[0]


# ========================================================= 3. malformed arguments
def _roundtrip(bad_call, monkeypatch):
    initial = client.send_chat(
        _cfg(tools="read_file"), MESSAGES,
        opener=_RecordingOpener(_payload(tool_calls=[bad_call],
                                         finish_reason="tool_calls")))
    return initial, _fetch(_cfg(tools="read_file"), initial, monkeypatch, [])


def test_attack3_invalid_json_is_a_recorded_refusal_not_a_crash(monkeypatch):
    bad = {"id": "call_bad", "type": "function",
           "function": {"name": "read_file", "arguments": "{not json"}}
    initial, (fake, (_m, _r, sent, rounds, turn_calls, followups)) = _roundtrip(
        bad, monkeypatch)
    assert initial["tool_calls"][0]["arguments_error"].startswith(
        "malformed_arguments_json:")
    assert fake.messages == [] and followups == []
    assert (sent, rounds) == (1, 0)
    assert turn_calls[0]["error"] == "malformed_tool_arguments"
    assert turn_calls[0]["reason"].startswith("malformed_arguments_json:")
    assert turn_calls[0]["executed"] is False and turn_calls[0]["billed"] is False


def test_attack3_missing_path_is_a_recorded_refusal(monkeypatch):
    bad = {"id": "call_nopath", "type": "function",
           "function": {"name": "read_file", "arguments": '{"start_line": 1, "end_line": 2}'}}
    _initial, (fake, (_m, _r, sent, rounds, turn_calls, _f)) = _roundtrip(bad, monkeypatch)
    assert fake.messages == [] and (sent, rounds) == (1, 0)
    assert turn_calls[0]["error"] == "malformed_tool_arguments"
    assert turn_calls[0]["reason"] == "missing_path"


def test_attack3_unknown_tool_is_a_recorded_refusal(monkeypatch):
    bad = {"id": "call_x", "type": "function",
           "function": {"name": "shell", "arguments": '{"cmd": "rm -rf /"}'}}
    _initial, (fake, (_m, _r, sent, rounds, turn_calls, _f)) = _roundtrip(bad, monkeypatch)
    assert fake.messages == [] and (sent, rounds) == (1, 0)
    assert turn_calls[0]["reason"] == "unknown_tool"


@pytest.mark.parametrize("path", ["../../etc/passwd", "/etc/passwd",
                                  "~/.ssh/id_rsa", "creds.env"])
def test_attack3_path_outside_the_allowed_root_never_reads(path, monkeypatch):
    call = {"id": "call_out", "type": "function",
            "function": {"name": "read_file",
                         "arguments": json.dumps({"path": path, "start_line": 1,
                                                  "end_line": 2})}}
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(
                                   tool_calls=[call], finish_reason="tool_calls")))
    fake, (_m, _r, _sent, _rounds, turn_calls, followups) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [_payload(content="answer")])
    rec = turn_calls[0]
    assert rec["executed"] is False
    assert rec["error"] in ("path_refused", "path_not_found")
    # the block that reaches the next prompt is an ERROR block, never file content
    blocks = fake.messages[0][-1]["content"]
    assert blocks.startswith('<tool_result error="')
    assert "</tool_result>" not in blocks
    assert "root:" not in blocks
    # billing observation: a refused-but-well-formed call still buys ONE round
    assert followups[0]["billed_round"] is True


def test_attack3_reversed_range_is_silently_normalised_not_refused(monkeypatch):
    """OBSERVED, contradicts the card's 'must be a recorded refusal': 110>66 is swapped."""
    call = {"id": "call_rev", "type": "function",
            "function": {"name": "read_file",
                         "arguments": '{"path": "ptr_engine/resolve.py",'
                                      ' "start_line": 110, "end_line": 66}'}}
    calls, refusals = run_longrun.calls_from_response({
        "tool_calls": [{"name": "read_file", "id": "call_rev",
                        "arguments_json": {"path": "ptr_engine/resolve.py",
                                           "start_line": 110, "end_line": 66},
                        "arguments_error": None}]})
    assert refusals == []
    assert (calls[0]["start_line"], calls[0]["end_line"]) == (66, 110)
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(
                                   tool_calls=[call], finish_reason="tool_calls")))
    fake, (_m, _r, _sent, _rounds, turn_calls, _f) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [_payload(content="answer")])
    assert fake.messages, "a reversed range EXECUTES a fetch (swapped), it is not refused"
    assert turn_calls[0]["executed"] is True
    assert (turn_calls[0]["start_line"], turn_calls[0]["end_line"]) == (66, 110)


@pytest.mark.xfail(strict=True, reason="card requires a refusal for start>end; "
                                       "the wire silently swaps the range instead")
def test_attack3_reversed_range_should_be_a_recorded_refusal():
    _calls, refusals = run_longrun.calls_from_response({
        "tool_calls": [{"name": "read_file", "id": "call_rev",
                        "arguments_json": {"path": "ptr_engine/resolve.py",
                                           "start_line": 110, "end_line": 66},
                        "arguments_error": None}]})
    assert refusals and refusals[0]["error"] == "malformed_tool_arguments"


# ======================================================= 4. empty-content turn
def test_attack4_empty_content_no_tool_calls_is_recorded_not_vanished():
    silent = _payload(content="")
    silent["choices"][0]["finish_reason"] = None
    resp = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                            opener=_RecordingOpener(silent))
    assert resp["content"] == "" and resp["tool_calls"] == []
    assert resp["stop_reason"] == client.STOP_REASON_EMPTY
    assert run_longrun.calls_from_response(resp) == ([], [])
    row = run_longrun.make_row(_cfg(tools="read_file"), _fixture(), "transcript-grow", 1,
                               "run-attack", 3, resp, resp["content"], "turn",
                               "manifest", {})
    assert row["stop_reason"] == client.STOP_REASON_EMPTY
    assert row["content_sha256"] == run_longrun.sha256_text("")
    assert row["content"] == "" and row["content_tokens"] == 0
    assert row["tools_schema_sent"] is True


# ==================================================== 5. text fallback preserved
def test_attack5_text_only_reply_still_parses_and_bills_one_round(monkeypatch):
    text = ('<tool_call>read_file <tool_call>{"path": "ptr_engine/resolve.py",'
            ' "start_line": 66, "end_line": 110}')
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(content=text)))
    assert initial["tool_calls"] == []
    calls, refusals = run_longrun.calls_from_response(initial)
    assert refusals == [] and len(calls) == 1
    fake, (_m, _r, sent, rounds, turn_calls, followups) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [_payload(content="answer")])
    assert len(fake.messages) == 1 and (sent, rounds) == (2, 1)
    assert followups[0]["billed_round"] is True
    assert turn_calls[0]["executed"] is True


def test_attack5_mixed_invalid_structured_plus_valid_text_fetches_nothing(monkeypatch):
    """OBSERVATION: any structured entry suppresses the text fallback, even a refused one."""
    text = ('<tool_call>read_file <tool_call>{"path": "ptr_engine/resolve.py",'
            ' "start_line": 66, "end_line": 110}')
    initial = client.send_chat(
        _cfg(tools="read_file"), MESSAGES,
        opener=_RecordingOpener(_payload(
            content=text,
            tool_calls=[{"id": "bad", "type": "function",
                         "function": {"name": "read_file", "arguments": "{not json"}}],
            finish_reason="tool_calls")))
    calls, refusals = run_longrun.calls_from_response(initial)
    assert calls == [], "the valid text call is NOT recovered"
    assert refusals and refusals[0]["error"] == "malformed_tool_arguments"
    fake, (_m, _r, sent, rounds, _tc, _f) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [])
    assert fake.messages == [] and (sent, rounds) == (1, 0)


# ========================================================== 6. label honesty
def test_attack6_failure_row_claims_schema_sent_with_no_request(monkeypatch):
    """OBSERVED DEFECT: a failure row (resp=None) claims tools_schema_sent=True.

    Nothing was serialised and nothing was sent, so the wire fact 'a schema was on the
    wire' is false; the field falls back to the DECLARED flag.
    """
    row = run_longrun.make_row(_cfg(tools="read_file"), _fixture(), "transcript-grow", 1,
                               "run-attack", 3, None, None, "turn", "manifest", {})
    assert row["tools_declared"] is True
    assert row["tools_schema_sent"] is True          # <-- the defect
    assert row.get("failed_turn") is True


def test_attack6_wallcap_label_follows_cfg_not_the_body():
    """OBSERVED DEFECT: mutate cfg.tools after the tools-off body exists -> cap row says sent."""
    cfg = _cfg(tools="")
    body = client.request_body(cfg, HISTORICAL)
    assert "tools" not in body
    cfg.tools = "read_file"
    exc = client.TurnWallCap(1.0, {"content_raw": "partial", "request_sha256": "x",
                                   "max_tokens": 64, "completion_tokens": 1})
    resp = exc.as_response(cfg)
    assert resp["tools_schema_sent"] is True          # <-- no tools on that wire
    assert "tools" not in body


def test_attack6_manifest_provenance_claims_sent_on_a_dry_run():
    """OBSERVED DEFECT: the manifest block is derived from the FLAG, not any wire."""
    prov = run_longrun.provenance_for(_cfg(tools="read_file"), _fixture())
    assert prov["tools_mode"] == "on:read_file"
    assert prov["tools_schema_sent"] is True    # no request was ever made here


def test_attack6_response_stamp_is_the_wire_fact_not_the_flag():
    """On a real client reply the stamp follows the BODY: off->False, on->True."""
    off = client.send_chat(_cfg(tools=""), MESSAGES,
                           opener=_RecordingOpener(_payload(content="x")))
    on = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                          opener=_RecordingOpener(_payload(content="x")))
    assert off["tools_schema_sent"] is False and off["tools_declared"] is False
    assert on["tools_schema_sent"] is True and on["tools_declared"] is True
    row_off = run_longrun.make_row(_cfg(tools=""), _fixture(), "transcript-grow", 1,
                                   "run-attack", 3, off, off["content"], "turn",
                                   "manifest", {})
    row_on = run_longrun.make_row(_cfg(tools="read_file"), _fixture(), "transcript-grow",
                                  1, "run-attack", 3, on, on["content"], "turn",
                                  "manifest", {})
    assert row_off["tools_schema_sent"] is False
    assert row_on["tools_schema_sent"] is True


# ============================================== 7. end-to-end fetch (the untested claim)
def test_attack7_structured_call_reaches_the_next_prompt_as_a_tool_result(monkeypatch):
    initial = client.send_chat(
        _cfg(tools="read_file"), MESSAGES,
        opener=_RecordingOpener(_payload(tool_calls=[PROBE_CALL],
                                         finish_reason="tool_calls")))
    fake, (_m, _r, sent, rounds, turn_calls, followups) = _fetch(
        _cfg(tools="read_file"), initial, monkeypatch, [_payload(content="answer")])
    assert (sent, rounds) == (2, 1) and len(fake.messages) == 1
    prompt = fake.messages[0]
    assistant, user = prompt[-2], prompt[-1]
    assert assistant == {"role": "assistant", "content": ""}
    assert user["role"] == "user"
    block = user["content"]
    assert block.startswith('<tool_result for="read_file"')
    assert 'base="engine"' in block.split("\n", 1)[0]
    assert "</tool_result>" in block
    # the real file content, not a fabricated body: line 66 is in the block
    target = os.path.join(LONGRUN, "..", "ptr_engine", "resolve.py")
    line66 = open(os.path.normpath(target), encoding="utf-8").read().splitlines()[65]
    assert line66 in block
    assert 'Use the tool result above' in block
    rec = turn_calls[0]
    assert rec["executed"] is True and rec["base"] == "engine"
    assert rec["lines_returned"] == 45
    assert followups[0]["prompt_sha256"] == run_longrun.sha256_text(block)
    print("FOLLOW-UP PROMPT[-1][:200]:", repr(block[:200]))
