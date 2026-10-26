"""Offline proof for the FETCH-CHANNEL tool channel (no model, no network).

Run: python3 experiments/ptr-engine/longrun/tests/test_tool_channel.py
Exit 0 = every assertion below held.  The five required assertions:
  (a) the path in the observed <tool_call> resolves
  (b) lines 66-71 of experiments/ptr-engine/ptr_engine/resolve.py are returned
  (c) ../../etc/passwd yields path_refused and performs NO read
  (d) the 2-calls-per-turn cap holds
  (e) --tools off (cfg.tools == "") executes no tool at all

Zero requests: the module under test is imported, never invoked over HTTP.  The test
asserts that by (i) making socket.socket raise for the duration and (ii) counting
send_chat calls, which must stay 0 in every assertion except the fetch-round test,
where send_chat is replaced by a canned function that never touches the network.
"""

import json
import os
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

# The exact assistant text measured at RUN-V4-GRID checkpoint 3, arm pointer-stable.
OBSERVED_TURN = (
    "I need to read lines 66-71 of resolve.py to answer what `_refuse` calls and what it passes.\n"
    "<tool_call>2629 <tool_call>read_file <tool_call>{\"path\": "
    "\"experiments/ptr-engine/ptr_engine/resolve.py\", \"start_line\": 66, \"end_line\": 71}"
)
RESOLVE_REL = "experiments/ptr-engine/ptr_engine/resolve.py"


class _Cfg:
    def __init__(self, tools=""):
        self.tools = tools
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model-was-never-called"
        self.base_url = "http://offline.invalid"


def _no_network():
    """Make any socket construction an immediate, loud failure."""
    def _denied(*_a, **_k):
        raise AssertionError("the tool channel must never open a socket")
    return _denied


def _messages():
    return [{"role": "system", "content": "offline"}, {"role": "user", "content": "Q"}]


def _fake_fixture():
    return {"task_id": "LR-01", "_sha256": "offline", "bytes_per_token": 4.0,
            "checkpoints": [], "N": 1, "items": [], "turns": [{"turn": 1, "question": "q"}]}


def assertion_a_path_resolves(sent):
    calls = R.parse_tool_calls(OBSERVED_TURN)
    assert len(calls) == 1, calls
    target, reason = R.resolve_read_path(calls[0]["path"], WORKSPACE)
    assert reason is None, reason
    assert target == os.path.realpath(os.path.join(WORKSPACE, RESOLVE_REL)), target
    assert os.path.isfile(target), target
    print(f"  (a) path resolves: {calls[0]['path']} -> {target} (refusal={reason})")
    return calls


def assertion_b_lines_returned(calls, sent):
    res = R.execute_tool_call(calls[0], WORKSPACE)
    rec, block = res["record"], res["block"]
    assert rec["executed"] is True, rec
    assert rec["truncated"] is False, rec
    assert rec["start_line"] == 66 and rec["end_line"] == 71, rec
    assert 'lines="66-71"' in block, block[:120]
    expected = open(os.path.join(WORKSPACE, RESOLVE_REL), encoding="utf-8").readlines()[65:71]
    for line in expected:
        assert line.rstrip("\n") in block, line
    assert "def _refuse(" in block and "ledger.record_refusal(" in block, block
    print(f"  (b) lines 66-71 returned, executed={rec['executed']} truncated={rec['truncated']} "
          f"first_line={res['text'].splitlines()[0][:60]!r}")
    return res


def assertion_c_unsafe_path_refused(sent):
    call = {"path": "../../etc/passwd", "start_line": 1, "end_line": 3}
    real_open = R.open if hasattr(R, "open") else open
    calls = []

    def _tripwire(*a, **k):
        calls.append(a)
        raise AssertionError(f"path_refused must never read: {a!r}")

    R.open = _tripwire  # module-level `open` shadow, if the runner ever grows one
    try:
        import builtins
        saved = builtins.open
        builtins.open = _tripwire
        try:
            res = R.execute_tool_call(call, WORKSPACE)
        finally:
            builtins.open = saved
    finally:
        if hasattr(R, "open"):
            R.open = real_open
    assert res["record"]["executed"] is False, res["record"]
    assert res["record"].get("error") == "path_refused", res["record"]
    assert res["block"] == '<tool_result error="path_refused"/>', res["block"]
    assert res["text"] == "", res["text"]
    assert calls == [], calls
    assert R.resolve_read_path("/etc/passwd", WORKSPACE) == (None, "path_refused")
    assert R.resolve_read_path(RESOLVE_REL, WORKSPACE)[1] is None  # control: safe path ok
    print(f"  (c) unsafe path refused: block={res['block']} read_attempts={len(calls)} "
          f"absolute_path_refused={R.resolve_read_path('/etc/passwd', WORKSPACE)[1]}")
    return res


def assertion_d_per_turn_cap(sent):
    many = [{"path": RESOLVE_REL, "start_line": i, "end_line": i} for i in (66, 67, 68, 69)]
    batch, overflow = R.limit_calls(many)
    assert len(batch) == R.TOOL_CALLS_PER_TURN == 2, (batch, R.TOOL_CALLS_PER_TURN)
    assert len(overflow) == 2, overflow
    # the executor path itself never runs more than two calls for one turn
    executed = 0
    for call in batch:
        res = R.execute_tool_call(call, WORKSPACE)
        executed += 1 if res["record"]["executed"] else 0
    assert executed == 2, executed
    print(f"  (d) 2-per-turn cap: batch={len(batch)} overflow={len(overflow)} "
          f"executed_this_turn={executed} cap={R.TOOL_CALLS_PER_TURN}")
    return batch


def assertion_e_tools_off_no_execution(sent):
    cfg = _Cfg(tools="")
    assert R.tools_enabled(cfg) is False, R.tool_names(cfg)
    resp = {"content": OBSERVED_TURN}
    import builtins
    saved = builtins.open
    reads = []

    def _tripwire(*a, **k):
        reads.append(a)
        raise AssertionError(f"--tools off must not read: {a!r}")

    builtins.open = _tripwire
    try:
        messages, out, sent_out, rounds, calls, followups = R.fetch_rounds(
            cfg, _fake_fixture(), "pointer-stable", 1, "offline", 3, "sha", {},
            _messages(), resp, 1, 99, 0)
    finally:
        builtins.open = saved
    assert reads == [], reads
    assert out is resp, "the response must pass through untouched when the channel is off"
    assert (calls, followups, rounds, sent_out) == ([], [], 0, 1), (calls, followups, rounds, sent_out)
    assert R.parse_tool_calls("just prose, no tool token") == []
    # a JSON object that never names read_file must not trigger a read either
    assert R.parse_tool_calls('{"path": "%s", "start_line": 1, "end_line": 2}' % RESOLVE_REL) == []
    print(f"  (e) --tools off: tools_enabled={R.tools_enabled(cfg)} read_attempts={len(reads)} "
          f"followups={len(followups)} sent_delta={sent_out - 1}")
    return None


def assertion_f_followup_accounting():
    """Every fetch follow-up is a real request, and the per-arm cap is exact.

    The fake model asks for a DIFFERENT line on every round on purpose: an identical
    repeat is now served `cached="true"` and bills nothing (FETCH-CHANNEL-FIX), so a
    constant request would prove the cache, not the cap.
    """
    sent_box = {"n": 1}
    counter = {"i": 0}

    def fake_send_chat(cfg, messages):
        sent_box["n"] += 1
        line = 66 + counter["i"]
        counter["i"] += 1
        text = ('<tool_call>read_file {"path": "experiments/ptr-engine/ptr_engine/resolve.py", '
                f'"start_line": {line}, "end_line": {line}}}')
        return {"content": text, "prompt_tokens": 10, "raw_cached": None,
                "ttft_s": 0.1, "latency_s": 0.2, "completion_tokens": 5,
                "content_raw": text, "reasoning": "", "truncated": False,
                "finish_reason": "stop", "token_source": "offline", "ttft_ms": 100,
                "content_source": "content", "max_tokens": 256}

    real = R.send_chat
    R.send_chat = fake_send_chat
    try:
        cfg = _Cfg(tools="read_file")
        messages, resp, sent, rounds, calls, followups = R.fetch_rounds(
            cfg, _fake_fixture(), "pointer-stable", 1, "offline", 3, "sha", {},
            _messages(), {"content": OBSERVED_TURN}, 1, 1 + R.TOOL_FETCH_ROUNDS_PER_ARM, 0)
    finally:
        R.send_chat = real
    assert rounds == R.TOOL_FETCH_ROUNDS_PER_ARM, rounds
    assert sent - 1 == R.TOOL_FETCH_ROUNDS_PER_ARM, sent  # one follow-up per round
    assert len(followups) == R.TOOL_FETCH_ROUNDS_PER_ARM, len(followups)
    assert all(r.get("fetch_followup") is True for r in followups), followups[0].keys()
    assert all(r.get("tool_calls") for r in followups), followups[0].get("tool_calls")
    assert any(c.get("error") == "fetch_budget_exhausted" for c in calls) or \
        any(c.get("executed") for c in calls), calls
    assert all(c["executed"] for c in calls if "error" not in c), calls
    print(f"  (f) follow-up accounting: rounds={rounds}/{R.TOOL_FETCH_ROUNDS_PER_ARM} "
          f"requests_sent={sent - 1} followup_rows={len(followups)} "
          f"fetch_followup_flags={sum(1 for r in followups if r.get('fetch_followup'))} "
          f"turn_calls={len(calls)}")
    return followups


def assertion_g_row_keys():
    """Row accounting: the tool keys exist on a --tools row and on no other row."""
    cfg = _Cfg(tools="read_file")
    resp = {"content": "ANSWER: x", "prompt_tokens": 10, "raw_cached": None, "ttft_s": 0.1,
            "latency_s": 0.2, "completion_tokens": 5, "content_raw": "x", "reasoning": "",
            "truncated": False, "finish_reason": "stop", "token_source": "offline",
            "ttft_ms": 100, "content_source": "content", "max_tokens": 256}
    call = {"path": RESOLVE_REL, "start_line": 66, "end_line": 71, "executed": True,
            "truncated": False}
    on = R.make_row(cfg, _fake_fixture(), "pointer-stable", 1, "offline", 3, resp, "ANSWER: x",
                    "tool-followup", "sha", {"fetch_followup": True, "tool_calls": [call]})
    off = R.make_row(_Cfg(tools=""), _fake_fixture(), "pointer-stable", 1, "offline", 3, resp,
                     "ANSWER: x", "turn", "sha", {})
    assert on.get("fetch_followup") is True, on.keys()
    assert on.get("tool_calls") == [call], on.get("tool_calls")
    assert "fetch_followup" not in off and "tool_calls" not in off, sorted(off.keys())
    print("  (g) row keys: tools-on row carries fetch_followup+tool_calls, tools-off row has "
          "neither (no schema drift for historical rows)")
    return on


def main() -> int:
    # Zero network: nowhere in this file is an HTTP client constructed; any socket is fatal.
    assert not any(m in sys.modules for m in ("requests", "httpx", "urllib3")), \
        "the offline proof must not pull in an HTTP client"
    real_socket = socket.socket
    socket.socket = _no_network()
    send_calls = {"n": 0}
    real_send = R.send_chat

    def _counted(*_a, **_k):
        send_calls["n"] += 1
        raise AssertionError("no model request may be sent by the offline proof")

    R.send_chat = _counted
    try:
        print("FETCH-CHANNEL offline proof (no model, no network)")
        print(f"  workspace_root={WORKSPACE}")
        calls = assertion_a_path_resolves(send_calls["n"])
        assertion_b_lines_returned(calls, send_calls["n"])
        assertion_c_unsafe_path_refused(send_calls["n"])
        assertion_d_per_turn_cap(send_calls["n"])
        assertion_e_tools_off_no_execution(send_calls["n"])
        assertion_f_followup_accounting()
        assertion_g_row_keys()
        assert send_calls["n"] == 0, send_calls
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
    print("PASS: 5/5 required assertions + follow-up accounting; send_chat calls in the "
          "offline proof = 0 (the one stubbed by (f) is replaced, never invoked for real)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
