"""Offline fetched-turn assertions (W1-FETCHROW)."""

import io
import json
import os
import socket
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LONGRUN = os.path.join(ROOT, "longrun")
sys.path.insert(0, LONGRUN)
sys.path.insert(0, ROOT)

import run_longrun as R  # noqa: E402
import arm_cd  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
FINAL_ANSWER = "ANSWER: TEXT offline"


class _Cfg:
    def __init__(self):
        self.tools = "read_file"
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = 8
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = None
        self.fetch_rounds_per_turn = 0
        self.turn_wall_cap = 0


def _resp(text, send_id, tool_calls=None):
    return {
        "content": text, "content_raw": text, "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 256, "prompt_tokens": 10 + send_id, "raw_cached": None,
        "token_source": "offline", "completion_tokens": 5, "wall_ms": 40,
        "request_sha256": "sha%d" % send_id,
        "request_identity_complete": True,
        "ttft_s": 0.04, "ttft_ms": 40,
        "latency_s": 0.08, "usage_missing": False,
        "tool_calls": tool_calls,
    }


def _run():
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        if state["n"] == 1:
            return _resp('<tool_call>fetch {"ref": "doc-live@r1"}', state["n"])
        return _resp(FINAL_ANSWER, state["n"])

    tmp = tempfile.mkdtemp(prefix="fetchrow-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(FIXTURE)
    cfg = _Cfg()
    cfg.max_turns = 1
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    run_id = "offline-fetchrow-r1"
    real_send, real_socket = R.send_chat, socket.socket
    R.send_chat = fake_send
    socket.socket = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no socket"))
    buf, old_stdout = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, "bounded-context-fetch", 1, run_id, rows_path)
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
        sys.stdout = old_stdout
    assert rc == 0, buf.getvalue()[-2000:]
    rows = [json.loads(l) for l in open(rows_path) if l.strip()]
    return rows, state


def test_fetched_turn_row():
    rows, _ = _run()
    fetched = [r for r in rows if (r.get("fetch_rows") or 0) > 0]
    assert len(fetched) == 1, "expected one fetched turn"
    row = fetched[0]
    # parsed call id from the model response path
    parsed = arm_cd.parse_fetch_calls_from_response({"content": '<tool_call>fetch {"ref": "doc-live@r1"}'})
    assert len(parsed) == 1
    parsed_id = parsed[0].get("tool_call_id", parsed[0].get("id"))
    assert row["tool_call_id"] == parsed_id
    assert row["fetch_rows"] == 1
    assert (row.get("tokenizer_calls") or 0) >= 1 or row.get("tokenizer_reused") or row.get("reused")
    # masked_rows consistent with marker count for this single turn
    assert row.get("masked_rows") in (0, None)

