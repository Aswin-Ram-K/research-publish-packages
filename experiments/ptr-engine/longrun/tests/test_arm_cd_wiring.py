"""Offline wiring test for arms C (masking-no-fetch) and D (bounded-context-fetch).

Zero network: socket is denied and send_chat is a counting fake.
"""
import io
import json
import os
import socket
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
PT_FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
FINAL_ANSWER = "ANSWER: TEXT offline"

def _no_network():
    def _denied(*_a, **_k):
        raise AssertionError("must never open a socket")
    return _denied


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


def _resp(text, send_id):
    return {
        "content": text, "content_raw": text, "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 256, "prompt_tokens": 10 + send_id, "raw_cached": None,
        "token_source": "offline", "completion_tokens": 5, "wall_ms": 40,
        "request_sha256": "sha%d" % send_id,
        "request_identity_complete": True,
        "ttft_s": 0.04, "ttft_ms": 40,
        "latency_s": 0.08, "usage_missing": False,
        "tool_calls": None,
    }


def _run(arm, fake_send, max_turns=8, fixture_path=None):
    tmp = tempfile.mkdtemp(prefix="armcd-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(fixture_path or FIXTURE)
    cfg = _Cfg()
    cfg.max_turns = max_turns
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    run_id = "offline-armcd-%s-r1" % arm
    real_send, real_socket = R.send_chat, socket.socket
    R.send_chat = fake_send
    socket.socket = _no_network()
    buf, old_stdout = io.StringIO(), sys.stdout
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, arm, 1, run_id, rows_path)
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
        sys.stdout = old_stdout
    assert rc == 0, "run_cell exit %d\n%s" % (rc, buf.getvalue()[-2000:])
    rows = []
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_c_masked_rows_after_window():
    import json, arm_cd
    fx = json.load(open(PT_FIXTURE))
    st = arm_cd.ArmCDState(fixture=fx)
    masked_rows, masked_entry = st.mask_old_turns(5)
    assert masked_rows == 2, "expected 2 masked rows at turn 5, got %d" % masked_rows
    # negative: turn 7 (cutoff 3) has no tool_outputs on turn 3
    st2 = arm_cd.ArmCDState(fixture=fx)
    st2.mask_old_turns(6)  # masks turn2 (1 output)
    mr, _ = st2.mask_old_turns(7)
    assert mr == 0, "turn 3 has no tool_outputs, expected 0, got %d" % mr

def test_d_fetch_rows_and_outcomes():
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        # first send of the (single) turn emits a fetch call
        if state["n"] == 1:
            return _resp('<tool_call>fetch {"ref": "turn-1@r1"}', state["n"])
        return _resp(FINAL_ANSWER, state["n"])

    # single turn enough for fetch test
    cfg_override = None
    rows = _run("bounded-context-fetch", fake_send, max_turns=1, fixture_path=PT_FIXTURE)
    assert any((r.get("fetch_rows") or 0) > 0 for r in rows), "no fetch row"
    outs = [o for r in rows for o in (r.get("retrieval_outcomes") or [])]
    assert len(outs) > 0, "no retrieval outcomes"


def test_d_two_fetches_two_model_calls():
    # Re-run with a counter to assert exactly 2 sends for a turn with 2 fetches
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        if state["n"] == 1:
            return _resp('<tool_call>fetch {"ref": "turn-1@r1"} <tool_call>fetch {"ref": "turn-2@r1"}', state["n"])
        return _resp(FINAL_ANSWER, state["n"])

    rows = _run("bounded-context-fetch", fake_send, max_turns=1, fixture_path=PT_FIXTURE)
    assert state["n"] == 2, "expected exactly 2 model calls, got %d" % state["n"]


def test_d_never_fetches_predicate_fails():
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        return _resp(FINAL_ANSWER, state["n"])

    rows = _run("bounded-context-fetch", fake_send, fixture_path=PT_FIXTURE)
    assert all((r.get("fetch_rows") or 0) == 0 for r in rows)
    assert not R.activation_predicate("bounded-context-fetch", rows)


if __name__ == "__main__":
    test_c_masked_rows_after_window()
    test_d_fetch_rows_and_outcomes()
    test_d_two_fetches_two_model_calls()
    test_d_never_fetches_predicate_fails()
    print("ALL OK")


def test_arm_cd_raises_on_unimportable_ptr_engine():
    import shutil, subprocess
    scratch = tempfile.mkdtemp(prefix="armcd-scratch-")
    shutil.copy(os.path.join(LONGRUN, "arm_cd.py"), os.path.join(scratch, "arm_cd.py"))
    env = dict(os.environ)
    env["PYTHONPATH"] = scratch
    # ensure repo paths not leaked
    for k in ("PYTHONSTARTUP",):
        env.pop(k, None)
    proc = subprocess.run(
        [sys.executable, "-c", "import arm_cd"],
        cwd=scratch, env=env, capture_output=True, text=True,
    )
    print("STDOUT:\n" + proc.stdout)
    print("STDERR:\n" + proc.stderr)
    assert proc.returncode != 0, "import unexpectedly succeeded"
    combined = proc.stdout + proc.stderr
    assert "ModuleNotFoundError" in combined or "ImportError" in combined


def test_arm_cd_no_fallback_pattern():
    src = open(os.path.join(LONGRUN, "arm_cd.py"), encoding="utf-8").read()
    assert "except Exception" not in src
    for name in ("mask_output", "batched_fetch", "PointerEntry", "FetchResult"):
        # no local definitions of these names
        assert ("def " + name) not in src
        assert ("class " + name) not in src
