"""TOOL-CHANNEL-WIRE — offline proof that the schema is sent AND the call is consumed.

Both halves are coupled on purpose (docs/TOOL-CHANNEL-ROOT-CAUSE.md §5): a tools-on reply
comes back with ``content_len == 0`` and the call in ``message.tool_calls``, so sending
the schema without consuming the structured call would record nothing at all.

Every test here is offline: the HTTP opener is a fake that records the exact request
bytes, ``run_longrun.send_chat`` is replaced by a scripted responder, and one test asserts
that no socket and no subprocess is ever created during the whole flow.  No fixture is
written; the fixture that is READ is the committed one at
``experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json``.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
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

#: The tools-off request digest measured BEFORE this change (captured by hand from the
#: unmodified client).  It must not move: the tools-off body gained no key.
PRE_FIX_TOOLS_OFF_DIGEST = (
    "f0499dd1335cccb27db359bee8d29c02a0f3015ee8e734404f288fbff0e2f8da")

MESSAGES = [{"role": "system", "content": "sys"}, {"role": "user", "content": "read it"}]
FIXTURE_PATH = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")

#: The exact call the live probe returned (docs/TOOL-CHANNEL-ROOT-CAUSE.md §3, probe A).
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
    """A fake ``urlopen``: records the exact wire body and returns a canned reply."""

    def __init__(self, payload):
        self.payload = payload
        self.requests: list[dict] = []

    def __call__(self, req, timeout):
        self.requests.append({"url": req.full_url, "body": json.loads(req.data)})
        return _FakeHTTP(self.payload)


class _ScriptedSend:
    """Stand-in for ``run_longrun.send_chat``: returns CLIENT-shaped replies, counts sends.

    Each scripted reply is an OpenAI-ish payload folded through the real
    ``client.send_chat`` with a recording opener, so the row sees the same measured
    response dict a live send produces — and still no socket is opened.
    """

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


# ---------------------------------------------------------------- 1. request bodies
def test_tools_off_body_is_byte_identical():
    """The tools-off body is unchanged: no `tools`, no `tool_choice`, same bytes."""
    body = client.request_body(_cfg(tools=""), MESSAGES)
    assert "tools" not in body
    assert "tool_choice" not in body
    # Byte-for-byte against the body builder AS IT WAS before this change (same keys,
    # same order, same values) — not just "no tools key".
    legacy = {
        "model": "occamy-1.0",
        "messages": MESSAGES,
        "temperature": 0,
        "max_tokens": 64,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    assert json.dumps(body) == json.dumps(legacy)
    import hashlib
    assert (client.request_digest(body)
            == hashlib.sha256(json.dumps(legacy).encode("utf-8")).hexdigest())
    # And the HISTORICAL request identity captured before the change, on the exact message
    # set it was captured with, is reproduced bit-for-bit.
    historical = [{"role": "user", "content": "hi"}]
    assert (client.request_digest(client.request_body(_cfg(tools=""), historical))
            == PRE_FIX_TOOLS_OFF_DIGEST)


def test_tools_on_body_carries_the_schema_and_changes_digest():
    body = client.request_body(_cfg(tools="read_file"), MESSAGES)
    assert isinstance(body["tools"], list) and len(body["tools"]) == 1
    schema = body["tools"][0]["function"]
    assert schema["name"] == "read_file"
    assert schema["parameters"]["required"] == ["path", "start_line", "end_line"]
    assert body["tool_choice"] == client.TOOL_CHOICE_AUTO
    digest = client.request_digest(body)
    assert digest != PRE_FIX_TOOLS_OFF_DIGEST
    # the change is additive: every pre-existing key and value is still there
    assert body["temperature"] == 0 and body["max_tokens"] == 64


def test_send_chat_puts_the_schema_on_the_wire_and_surfaces_the_call():
    opener = _RecordingOpener(_payload(tool_calls=[PROBE_CALL],
                                       finish_reason="tool_calls"))
    resp = client.send_chat(_cfg(tools="read_file"), MESSAGES, opener=opener)
    wire = opener.requests[0]["body"]
    assert wire["tools"][0]["function"]["name"] == "read_file"
    assert wire["tool_choice"] == "auto"
    assert resp["tools_schema_sent"] is True
    assert resp["tools_declared"] is True
    assert resp["content"] == ""                       # probe A: content_len 0
    assert resp["tool_calls_present"] is True
    call = resp["tool_calls"][0]
    assert call["name"] == "read_file"
    assert call["arguments_json"] == {"path": "ptr_engine/resolve.py",
                                      "start_line": 66, "end_line": 110}
    assert call["arguments_error"] is None

    # tools off: no schema on the wire, and the row says so
    off = _RecordingOpener(_payload(content="prose"))
    off_resp = client.send_chat(_cfg(tools=""), MESSAGES, opener=off)
    assert "tools" not in off.requests[0]["body"]
    assert off_resp["tools_schema_sent"] is False
    assert off_resp["tool_calls"] == []


# ------------------------------------------------------- 2. the runner consumes it
def test_structured_call_performs_exactly_one_fetch_round(monkeypatch):
    fake = _ScriptedSend([_payload(content="line 66 raises ValueError")])
    monkeypatch.setattr(run_longrun, "send_chat", fake)
    cfg = _cfg(tools="read_file")
    fixture = _fixture()
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(
                                   tool_calls=[PROBE_CALL],
                                   finish_reason="tool_calls")))
    (_m, resp, sent, rounds, calls, followups) = run_longrun.fetch_rounds(
        cfg, fixture, "transcript-grow", 1, "run-offline", 3, "manifest", {},
        MESSAGES, initial, 1, 50, 0, served={}, pinned=[], per_turn_cap=2,
        may_request=lambda: True)
    assert len(fake.messages) == 1, "exactly one follow-up request"
    assert sent == 2
    assert rounds == 1
    assert len(followups) == 1
    row = followups[0]
    assert row["billed_round"] is True
    assert row["kind"] == "tool-followup"
    assert row["send_index"] == 1
    assert row["tools_schema_sent"] is True
    rec = row["tool_calls"][0]
    assert rec["path"] == "ptr_engine/resolve.py"
    assert (rec["start_line"], rec["end_line"]) == (66, 110)
    assert rec["executed"] is True
    assert rec["base"] == "engine"
    assert rec["lines_returned"] == 45
    assert len(calls) == 1 and calls[0]["executed"] is True
    assert resp["content"] == "line 66 raises ValueError"


def test_malformed_arguments_are_refused_and_recorded(monkeypatch):
    fake = _ScriptedSend([])              # any billed round is a failure
    monkeypatch.setattr(run_longrun, "send_chat", fake)
    cfg = _cfg(tools="read_file")
    bad = {"id": "call_bad", "type": "function",
           "function": {"name": "read_file", "arguments": "{not json"}}
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(
                                   tool_calls=[bad], finish_reason="tool_calls")))
    assert initial["tool_calls"][0]["arguments_error"].startswith(
        "malformed_arguments_json:")
    calls, refusals = run_longrun.calls_from_response(initial)
    assert calls == []
    assert refusals[0]["error"] == "malformed_tool_arguments"
    assert refusals[0]["reason"].startswith("malformed_arguments_json:")
    assert refusals[0]["billed"] is False

    (_m, _r, sent, rounds, turn_calls, followups) = run_longrun.fetch_rounds(
        cfg, _fixture(), "transcript-grow", 1, "run-offline", 3, "manifest", {},
        MESSAGES, initial, 1, 50, 0, served={}, pinned=[], per_turn_cap=2,
        may_request=lambda: True)
    assert fake.messages == [], "a malformed call never buys a round"
    assert followups == [] and sent == 1 and rounds == 0
    assert turn_calls[0]["error"] == "malformed_tool_arguments"
    assert turn_calls[0]["executed"] is False


def test_text_tool_call_reply_still_parses(monkeypatch):
    """Backwards compatibility: the old TEXT protocol must keep working unchanged."""
    text = '<tool_call>read_file <tool_call>{"path": "ptr_engine/resolve.py", "start_line": 66, "end_line": 110}'
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(content=text)))
    assert initial["tool_calls"] == []        # no structured call in this reply
    calls, refusals = run_longrun.calls_from_response(initial)
    assert refusals == [] and len(calls) == 1
    assert calls[0]["path"] == "ptr_engine/resolve.py"

    fake = _ScriptedSend([_payload(content="answer")])
    monkeypatch.setattr(run_longrun, "send_chat", fake)
    (_m, _r, _sent, _rounds, turn_calls, followups) = run_longrun.fetch_rounds(
        _cfg(tools="read_file"), _fixture(), "transcript-grow", 1, "run-offline", 3,
        "manifest", {}, MESSAGES, initial, 1, 50, 0, served={}, pinned=[],
        per_turn_cap=2, may_request=lambda: True)
    assert len(fake.messages) == 1 and len(followups) == 1
    assert followups[0]["billed_round"] is True
    assert turn_calls[0]["executed"] is True


def test_empty_reply_with_no_tool_calls_is_recorded_not_empty():
    """content_len=0 and no tool_calls: an explicit stop_reason, on a real row."""
    silent = _payload(content="")
    silent["choices"][0]["finish_reason"] = None       # no finish chunk at all
    resp = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                            opener=_RecordingOpener(silent))
    assert resp["content"] == ""
    assert resp["tool_calls"] == []
    assert resp["stop_reason"] == client.STOP_REASON_EMPTY
    fixture = _fixture()
    row = run_longrun.make_row(_cfg(tools="read_file"), fixture, "transcript-grow", 1,
                               "run-offline", 3, resp, resp["content"], "turn",
                               "manifest", {})
    assert row["stop_reason"] == client.STOP_REASON_EMPTY
    assert row["content_sha256"] == run_longrun.sha256_text("")
    assert row["tools_declared"] is True
    assert row["tools_schema_sent"] is True
    assert run_longrun.calls_from_response(resp) == ([], [])

    # and the SAME shape with a `stop` finish reason is still an explicit, recorded
    # outcome — never a dropped turn
    stopped = client.send_chat(_cfg(tools="read_file"), MESSAGES,
                               opener=_RecordingOpener(_payload(content="")))
    assert stopped["stop_reason"] == client.STOP_REASON_STOP


# ------------------------------------------------------------- 3. the offline guard
def test_flow_touches_no_socket_and_launches_no_subprocess(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("zero network / zero subprocess is a hard requirement")

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    monkeypatch.setattr(run_longrun, "send_chat",
                        _ScriptedSend([_payload(content="ok")]))

    opener = _RecordingOpener(_payload(tool_calls=[PROBE_CALL],
                                       finish_reason="tool_calls"))
    initial = client.send_chat(_cfg(tools="read_file"), MESSAGES, opener=opener)
    (_m, _r, _sent, _rounds, turn_calls, followups) = run_longrun.fetch_rounds(
        _cfg(tools="read_file"), _fixture(), "transcript-grow", 1, "run-offline", 3,
        "manifest", {}, MESSAGES, initial, 1, 50, 0, served={}, pinned=[],
        per_turn_cap=2, may_request=lambda: True)
    assert turn_calls and followups
