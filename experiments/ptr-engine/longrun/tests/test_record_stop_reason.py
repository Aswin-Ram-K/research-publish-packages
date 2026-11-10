"""RECORD-STOP-REASON: a stop is explainable from the row alone.  OFFLINE — hand-built SSE.

    python3 experiments/ptr-engine/longrun/tests/test_record_stop_reason.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_record_stop_reason.py -q

WHY: `STOP-REASON-AUDIT` (10195e9e) classified seven arm-checks as `cap-exhausted` --
content `""`, the empty string's sha, `completion_tokens` 128 on all 99 empty rows, and NO
`finish_reason` / `truncated` / `max_tokens` on the row -- so a cap-exhausted generation and
a silent refusal were indistinguishable without sha-hunting and token arithmetic.  These
tests pin the fix: the closed vocabulary, the ceiling as sent, and the evidence a contentless
stop now carries.  Each is RED before the change (the row has no `stop_reason` at all).

  (a) finish_reason="length"                 -> stop_reason="length",  truncated=True
  (b) finish_reason="stop"                   -> stop_reason="stop",    truncated=False
  (c) a tool-call stream                     -> stop_reason="tool_calls"
  (d) an empty stream with no finish chunk   -> "empty_response", truncated=None,
                                                content_sha256 = sha256("")
  (e) an HTTP 500                            -> stop_reason="http_error", truncated=None
  (f) a turn closed by the wall cap          -> "turn_wall_cap", distinct from "length"
  (g) a FOLLOW-UP row carries the same fields as a turn row

Zero inference requests: no socket is opened.  Every stream is a list of SSE strings.
"""

import hashlib
import json
import os
import sys
import urllib.error
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)                       # experiments/ptr-engine/longrun
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
sys.path.insert(0, LONG)

import client          # noqa: E402
import run_longrun     # noqa: E402

CAP = 128
EMPTY_SHA = hashlib.sha256(b"").hexdigest()
VOCAB = set(client.STOP_REASONS)


# ---------------------------------------------------------------- offline plumbing
def _cfg(**kw):
    base = dict(model="fake-model", stream=True, thinking="off", max_tokens=CAP,
                engine="sglang", metrics_scrape=False, timeout=5.0,
                base_url="http://127.0.0.1:1/v1", turn_wall_cap=None)
    base.update(kw)
    return SimpleNamespace(**base)


class _FakeResponse:
    """The minimum `opener(...)` context manager: iterate for the stream, read for JSON."""

    def __init__(self, lines):
        self.lines = list(lines)

    def __iter__(self):
        return iter(self.lines)

    def read(self):
        return "".join(self.lines).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener(lines):
    def opener(req, timeout):
        opener.last_request = req
        opener.last_body = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(lines)
    opener.last_body = None
    return opener


def _sse(obj):
    return "data: " + json.dumps(obj) + "\n"


_DONE = "data: [DONE]\n"


def _tick(step=0.01, start=0.0):
    """A deterministic clock: every call advances by `step`."""
    state = {"t": start - step}

    def clock():
        state["t"] += step
        return state["t"]
    return clock


def _content_stream(finish_reason, text="the answer", completion=7):
    lines = [
        _sse({"choices": [{"index": 0, "delta": {"role": "assistant", "content": text},
                           "finish_reason": None}]}),
        _sse({"choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}]}),
        _sse({"choices": [],
              "usage": {"prompt_tokens": 11, "completion_tokens": completion,
                        "prompt_tokens_details": {"cached_tokens": 0}}}),
        _DONE,
    ]
    return lines


def _fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        fx = json.load(fh)
    fx["_sha256"] = "0" * 64
    return fx


def _extras(**kw):
    base = dict(is_checkpoint=False, checkpoint=None, answer_turn=False, lease=None,
                evicted=None, prompt_sha256="0" * 64)
    base.update(kw)
    return base


def _row(cfg, resp, content, kind="turn", fixture=None, **extra):
    """The runner's only row writer, called exactly the way the runner calls it."""
    fx = _fixture() if fixture is None else fixture
    return run_longrun.make_row(cfg, fx, "transcript-grow", 1, "run-stop-reason-r1", 1,
                               resp, content, kind, "f" * 64, _extras(**extra))


def _send(lines, cfg=None, opener=None):
    cfg = _cfg() if cfg is None else cfg
    return client.send_chat(cfg, [{"role": "user", "content": "hi"}],
                            opener=opener or _opener(lines), clock=_tick())


# ---------------------------------------------------------------- (a) length
def test_a_length_finish_chunk():
    resp = _send(_content_stream("length", completion=CAP))
    assert resp["stop_reason"] == "length", resp["stop_reason"]
    assert resp["truncated"] is True, resp["truncated"]
    assert resp["max_tokens"] == CAP, resp["max_tokens"]
    assert resp["finish_reasons"] == [{"index": 0, "finish_reason": "length"}], resp["finish_reasons"]
    row = _row(_cfg(), resp, resp["content"])
    assert row["stop_reason"] == "length", row["stop_reason"]
    assert row["truncated"] is True and row["max_tokens"] == CAP, row
    assert row["finish_reasons"] == [{"index": 0, "finish_reason": "length"}]


def test_a2_cap_stop_without_a_finish_chunk_is_length_not_a_refusal():
    """The 128-token case: no finish chunk, completion AT the ceiling -> still `length`."""
    lines = [
        _sse({"choices": [{"index": 0, "delta": {"reasoning_content": "thinking"},
                           "finish_reason": None}]}),
        _sse({"choices": [],
              "usage": {"prompt_tokens": 11, "completion_tokens": CAP}}),
        _DONE,
    ]
    resp = _send(lines)
    assert resp["stop_reason"] == "length", resp["stop_reason"]
    assert resp["truncated"] is True


# ---------------------------------------------------------------- (b) normal stop
def test_b_normal_stop_is_not_truncated():
    resp = _send(_content_stream("stop"))
    assert resp["stop_reason"] == "stop", resp["stop_reason"]
    assert resp["truncated"] is False, resp["truncated"]
    row = _row(_cfg(), resp, resp["content"])
    assert row["stop_reason"] == "stop" and row["truncated"] is False


# ---------------------------------------------------------------- (c) tool calls
def test_c_tool_call_stream():
    lines = [
        _sse({"choices": [{"index": 0,
                           "delta": {"tool_calls": [{"index": 0, "id": "call_1",
                                                     "function": {"name": "read_file",
                                                                  "arguments": "{}"}}]},
                           "finish_reason": None}]}),
        _sse({"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]}),
        _DONE,
    ]
    resp = _send(lines)
    assert resp["stop_reason"] == "tool_calls", resp["stop_reason"]
    assert resp["truncated"] is False
    assert resp["first_token_kind"] == "tool_call", resp["first_token_kind"]


# ---------------------------------------------------------------- (d) empty stream
def test_d_empty_stream_is_empty_response_with_the_empty_sha():
    resp = _send([_sse({"choices": [{"index": 0, "delta": {}, "finish_reason": None}]}), _DONE])
    assert resp["stop_reason"] == "empty_response", resp["stop_reason"]
    assert resp["truncated"] is None, resp["truncated"]
    row = _row(_cfg(), resp, resp["content"])
    assert row["stop_reason"] == "empty_response"
    assert row["truncated"] is None, row["truncated"]
    assert row["content_sha256"] == EMPTY_SHA, row["content_sha256"]
    assert row["stop_evidence"] is True, row["stop_evidence"]


# ---------------------------------------------------------------- (e) HTTP 500
def test_e_http_500_is_http_error():
    def opener(req, timeout):
        raise urllib.error.HTTPError("http://127.0.0.1:1/v1/chat/completions", 500,
                                     "Server Error", {}, None)
    try:
        _send([], opener=opener)
    except client.RequestFailure as exc:
        failure = exc
    else:
        raise AssertionError("an HTTP 500 must raise RequestFailure, never a response")
    assert failure.status == 500, failure.status
    assert failure.stop_reason == "http_error", failure.stop_reason
    row = _row(_cfg(), None, None, http_status=failure.status, error=str(failure))
    assert row["stop_reason"] == "http_error", row["stop_reason"]
    assert row["truncated"] is None, row["truncated"]
    assert row["content_sha256"] == EMPTY_SHA
    assert row["completion_tokens"] == 0 and row["completion_tokens_source"] == "client_observed"
    assert row["finish_reason"] is None and row["finish_reasons"] is None
    assert row["http_status"] == 500


# ---------------------------------------------------------------- (f) wall cap
def test_f_wall_cap_is_turn_wall_cap_not_length():
    cfg = _cfg(turn_wall_cap=0.5, max_tokens=CAP)
    lines = [_sse({"choices": [{"index": 0,
                                "delta": {"reasoning_content": "runaway " + str(i)},
                                "finish_reason": None}]}) for i in range(50)]
    try:
        client.send_chat(cfg, [{"role": "user", "content": "hi"}],
                         opener=_opener(lines), clock=_tick(step=0.1))
    except client.TurnWallCap as exc:
        cap = exc
    else:
        raise AssertionError("a stream past --turn-wall-cap must raise TurnWallCap")
    assert cap.stop_reason == "turn_wall_cap", cap.stop_reason
    part = cap.as_response(cfg)
    assert part["stop_reason"] == "turn_wall_cap", part["stop_reason"]
    assert part["stop_reason"] != "length"
    assert part["max_tokens"] == CAP
    row = _row(cfg, part, part["content"], error="turn_wall_cap",
               turn_wall_cap_s=0.5, http_status=None)
    assert row["stop_reason"] == "turn_wall_cap", row["stop_reason"]
    assert row["truncated"] is True, row["truncated"]
    assert row["error"] == "turn_wall_cap"


# ---------------------------------------------------------------- (g) follow-up rows
def test_g_followup_row_carries_the_same_fields():
    resp = _send(_content_stream("length", completion=CAP))
    turn_row = _row(_cfg(), resp, resp["content"], kind="turn")
    followup_row = _row(_cfg(), resp, resp["content"], kind="tool-followup",
                        fetch_followup=True, tool_calls=[])
    for key in ("stop_reason", "truncated", "max_tokens", "finish_reason",
                "finish_reasons", "stop_evidence"):
        assert key in followup_row, key
        assert followup_row[key] == turn_row[key], (key, followup_row[key], turn_row[key])
    assert followup_row["kind"] == "tool-followup" and followup_row["fetch_followup"] is True
    # a follow-up request closed by the wall cap keeps ITS reason too
    cap_part = client.TurnWallCap(1.0, {"content_raw": "", "reasoning": "",
                                        "completion_tokens": 3, "max_tokens": CAP,
                                        "turn_wall_cap_s": 0.5, "latency_s": 0.5,
                                        "wall_ms": 500.0}).as_response(_cfg())
    capped_followup = _row(_cfg(), cap_part, "", kind="tool-followup",
                           fetch_followup=True, error="turn_wall_cap")
    assert capped_followup["stop_reason"] == "turn_wall_cap"


# ---------------------------------------------------------------- the vocabulary is CLOSED
def test_h_every_row_stop_reason_is_in_the_closed_vocabulary():
    seen = set()
    for lines in (_content_stream("length", completion=CAP), _content_stream("stop"),
                  _content_stream("content_filter"), [_DONE]):
        resp = _send(lines)
        seen.add(resp["stop_reason"])
        seen.add(_row(_cfg(), resp, resp["content"])["stop_reason"])
    seen.add(client.derive_stop_reason("made-up-future-reason", content_present=True))
    assert seen <= VOCAB, sorted(seen - VOCAB)
    assert client.derive_stop_reason("made-up-future-reason",
                                     content_present=True) == "unknown"


CHECKS = [
    ("a", "finish_reason=length -> stop_reason=length, truncated=True",
     test_a_length_finish_chunk),
    ("a2", "a cap stop with no finish chunk is `length`, not a refusal",
     test_a2_cap_stop_without_a_finish_chunk_is_length_not_a_refusal),
    ("b", "finish_reason=stop -> truncated=False", test_b_normal_stop_is_not_truncated),
    ("c", "a tool-call stream -> tool_calls", test_c_tool_call_stream),
    ("d", "an empty stream -> empty_response, truncated=None, sha of the empty string",
     test_d_empty_stream_is_empty_response_with_the_empty_sha),
    ("e", "an HTTP 500 -> http_error", test_e_http_500_is_http_error),
    ("f", "the wall cap -> turn_wall_cap, distinct from length",
     test_f_wall_cap_is_turn_wall_cap_not_length),
    ("g", "a follow-up row carries the same fields", test_g_followup_row_carries_the_same_fields),
    ("h", "the vocabulary is closed", test_h_every_row_stop_reason_is_in_the_closed_vocabulary),
]


if __name__ == "__main__":
    fails = 0
    for label, title, fn in CHECKS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - a test runner prints, then fails
            fails += 1
            print("FAIL (%s) %s: %s: %s" % (label, title, type(exc).__name__, exc))
        else:
            print("ok   (%s) %s" % (label, title))
    print("%d/%d checks passed" % (len(CHECKS) - fails, len(CHECKS)))
    sys.exit(1 if fails else 0)
