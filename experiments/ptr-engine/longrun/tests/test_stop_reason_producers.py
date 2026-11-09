"""STOP-REASON-HOLES: producers for `runaway_turn`, the tool-call hole, row-local `length`.

    python3 experiments/ptr-engine/longrun/tests/test_stop_reason_producers.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_stop_reason_producers.py -q

WHY (three defects `V-INSTRUMENTS` measured in the stop vocabulary against the writer):

  (1) `runaway_turn` had NO producer: `client.send_chat` derived its reason without an
      error code, nothing wrote `error="runaway_turn"`, and `run_longrun` recorded the
      `--runaway-turns` abort as `error=turn_wall_cap` -- so a runaway abort and a single
      slow turn were indistinguishable in the rows.
  (2) a tool-call stream that ended with no finish chunk and no text content was recorded
      as `empty_response`: the row said the model produced nothing when it had produced a
      call.  `derive_stop_reason` never received a tool-call signal.
  (3) `max_tokens` was absent from 99 stage-1 rows, so rule 3 could not be evaluated from
      the row: with the frozen manifest cap 128 they re-derived 99/99 `length`, from the
      row as-is 99/99 `empty_response`.

The fixes are LABELLING ONLY: no guard threshold (180 s turn cap, `--runaway-turns`, the
4,096-token ceiling) is touched, and no historical row, grade or fixture is rewritten.

Zero inference requests: the streams below are hand-built SSE strings, and the only
socket is a fake HTTP server on 127.0.0.1 that emits tokens until the client closes.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)                       # experiments/ptr-engine/longrun
RUNNER = os.path.join(LONG, "run_longrun.py")
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"
PY = sys.executable
CAP = 128
sys.path.insert(0, LONG)

import client          # noqa: E402
import run_longrun     # noqa: E402


# ---------------------------------------------------------------- offline plumbing
def _cfg(**kw):
    base = dict(model="fake-model", stream=True, thinking="off", max_tokens=CAP,
                engine="sglang", metrics_scrape=False, timeout=5.0,
                base_url="http://127.0.0.1:1/v1", turn_wall_cap=None)
    base.update(kw)
    return SimpleNamespace(**base)


class _FakeResponse:
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
        opener.last_body = json.loads(req.data.decode("utf-8"))
        return _FakeResponse(lines)
    opener.last_body = None
    return opener


def _sse(obj):
    return "data: " + json.dumps(obj) + "\n"


_DONE = "data: [DONE]\n"


def _tick(step=0.01, start=0.0):
    state = {"t": start - step}

    def clock():
        state["t"] += step
        return state["t"]
    return clock


def _send(lines, cfg=None):
    cfg = _cfg() if cfg is None else cfg
    return client.send_chat(cfg, [{"role": "user", "content": "hi"}],
                            opener=_opener(lines), clock=_tick())


def _fixture():
    with open(FIXTURE, encoding="utf-8") as fh:
        fx = json.load(fh)
    fx["_sha256"] = "0" * 64
    return fx


def _row(cfg, resp, content, **extra):
    base = dict(is_checkpoint=False, checkpoint=None, answer_turn=False, lease=None,
                evicted=None, prompt_sha256="0" * 64)
    base.update(extra)
    return run_longrun.make_row(cfg, _fixture(), ARM, 1, "run-stop-holes", 1, resp,
                                content, "turn", "f" * 64, base)


def _usage(completion):
    return _sse({"choices": [],
                 "usage": {"prompt_tokens": 11, "completion_tokens": completion}})


# ------------------------------------------------- (2) the tool-call hole
TOOL_DELTA = {"tool_calls": [{"index": 0, "id": "call_1",
                              "function": {"name": "read_file",
                                           "arguments": "{\"path\": \"a.py\""}}]}


def test_tool_call_delta_without_finish_is_tool_calls():
    """A call is a production: no finish chunk and no text must NOT read as empty."""
    lines = [
        _sse({"choices": [{"index": 0, "delta": TOOL_DELTA, "finish_reason": None}]}),
        _usage(7),
        _DONE,
    ]
    resp = _send(lines)
    assert resp["tool_calls_present"] is True, resp
    assert resp["stop_reason"] == "tool_calls", resp["stop_reason"]
    assert resp["truncated"] is False, resp["truncated"]
    row = _row(_cfg(), resp, resp["content"])
    assert row["stop_reason"] == "tool_calls", row["stop_reason"]
    assert row["content"] == "", row["content"]


def test_bare_argument_fragment_alone_is_tool_calls():
    """Even one arguments fragment, with no id or name, is a production signal."""
    lines = [
        _sse({"choices": [{"index": 0,
                           "delta": {"tool_calls": [{"index": 0,
                                                     "function": {"arguments": "{\"p"}}]},
                           "finish_reason": None}]}),
        _usage(3),
        _DONE,
    ]
    assert _send(lines)["stop_reason"] == "tool_calls"


def test_no_tool_call_no_finish_no_content_is_empty_response():
    """The honest empty case must remain reachable: nothing was produced at all."""
    lines = [_usage(7), _DONE]
    resp = _send(lines)
    assert resp["tool_calls_present"] is False, resp
    assert resp["stop_reason"] == "empty_response", resp["stop_reason"]
    assert resp["truncated"] is None, resp["truncated"]


# ------------------------------------------------- (3) length from the row alone
def test_length_recomputable_from_the_row_without_a_manifest():
    lines = [
        _sse({"choices": [{"index": 0, "delta": {"reasoning_content": "thinking"},
                           "finish_reason": None}]}),
        _usage(CAP),
        _DONE,
    ]
    resp = _send(lines)
    assert resp["stop_reason"] == "length"
    row = _row(_cfg(), resp, resp["content"])
    assert row["completion_tokens"] == CAP, row["completion_tokens"]
    assert row["max_tokens"] == CAP, row["max_tokens"]
    # NOTHING but the row: no manifest, no config, no client state.
    rederived = client.derive_stop_reason(
        row.get("finish_reason"),
        content_present=bool((row.get("content") or "").strip()),
        completion_tokens=row["completion_tokens"], max_tokens=row["max_tokens"])
    assert rederived == "length", (rederived, row)


def test_every_turn_row_carries_the_ceiling_even_on_failure():
    cfg = _cfg(max_tokens=321)
    failed = _row(cfg, None, None, error="http_error", http_status=500)
    assert failed["max_tokens"] == 321, failed["max_tokens"]
    ok = _send([_show_stop()], cfg)
    row = _row(cfg, ok, ok["content"])
    assert row["max_tokens"] == 321, row["max_tokens"]


def _show_stop():
    return _sse({"choices": [{"index": 0, "delta": {"content": "ok"},
                              "finish_reason": "stop"}]})


# ------------------------------------------------- closed vocabulary: 10/10
def test_all_ten_members_inducible_and_unmappable_is_unknown():
    calls = {
        "stop": dict(finish_reason="stop", content_present=True),
        "length": dict(finish_reason="length", content_present=True),
        "tool_calls": dict(finish_reason="tool_calls", content_present=False),
        "content_filter": dict(finish_reason="content_filter", content_present=True),
        "turn_wall_cap": dict(finish_reason=None, content_present=False,
                              error_code="turn_wall_cap"),
        "runaway_turn": dict(finish_reason=None, content_present=False,
                             error_code="runaway_turn"),
        "http_error": dict(finish_reason=None, content_present=False,
                           error_code="http_error"),
        "stream_error": dict(finish_reason=None, content_present=False,
                             error_code="stream_error"),
        "empty_response": dict(finish_reason=None, content_present=False),
        "unknown": dict(finish_reason="made-up-future-reason", content_present=True),
    }
    induced = {name: client.derive_stop_reason(**kw) for name, kw in calls.items()}
    assert induced == {name: name for name in calls}, induced
    assert set(induced.values()) == set(client.STOP_REASONS), client.STOP_REASONS
    assert len(client.STOP_REASONS) == 10
    # an unmappable server string still lands on `unknown`, never a neighbour
    assert client.derive_stop_reason("  REFUSED ", content_present=True) == "unknown"


# ------------------------------------------------- (1) the runaway producer
def _sse_delta(text, kind="reasoning_content"):
    return ("data: " + json.dumps({"choices": [{"delta": {kind: text}, "index": 0,
                                                "finish_reason": None}]}) + "\n").encode()


class _Fake:
    """A local fake server: SSE reasoning tokens forever, plus a /metrics stub."""

    def __init__(self):
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                outer.last_body = json.loads(self.rfile.read(n).decode("utf-8"))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                try:
                    i = 0
                    while True:
                        self.wfile.write(_sse_delta("runaway%d " % i))
                        self.wfile.flush()
                        i += 1
                        time.sleep(0.02)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

        self.last_body = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.server.daemon_threads = True
        self.url = "http://127.0.0.1:%d/v1" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()
        return False


def _run_runner(tmp, url, turns, runaway, wall_cap, rows_name):
    rows = os.path.join(tmp, rows_name)
    argv = [PY, RUNNER, "--fixture", FIXTURE, "--arms", ARM, "--reps", "1",
            "--max-turns", str(turns), "--turn-wall-cap", str(wall_cap),
            "--runaway-turns", str(runaway), "--rows", rows,
            "--manifest-path", os.path.join(tmp, "manifest-%s.json" % rows_name),
            "--base-url", url, "--no-metrics-scrape", "--max-tokens", "4096"]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=LONG, timeout=180)
    parsed = []
    if os.path.exists(rows):
        with open(rows, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    parsed.append(json.loads(line))
    return proc, parsed


def test_runaway_abort_records_runaway_turn():
    """The real abort path (--runaway-turns 1): one window, the run ENDS (exit 6)."""
    tmp = tempfile.mkdtemp(prefix="stop-holes-runaway-")
    with _Fake() as fake:
        proc, rows = _run_runner(tmp, fake.url, 1, 1, 0.4, "runaway.jsonl")
    assert fake.last_body is not None, "no request reached the fake server"
    assert proc.returncode == 6, (proc.returncode, proc.stderr[-2000:])
    assert len(rows) == 1, rows
    row = rows[0]
    # The harness EVENT is still the wall cap; the REASON is the runaway abort.
    assert row["error"] == "turn_wall_cap", row.get("error")
    assert row.get("runaway_abort") is True, row
    assert row["stop_reason"] == "runaway_turn", row["stop_reason"]
    assert row["truncated"] is True, row.get("truncated")


def test_single_slow_turn_stays_turn_wall_cap():
    """The same window with --runaway-turns 2: the turn is capped, the run survives."""
    tmp = tempfile.mkdtemp(prefix="stop-holes-slow-")
    with _Fake() as fake:
        proc, rows = _run_runner(tmp, fake.url, 1, 2, 0.4, "slow.jsonl")
    assert proc.returncode == 0, (proc.returncode, proc.stderr[-2000:])
    assert len(rows) == 1, rows
    row = rows[0]
    assert "runaway_abort" not in row, row
    assert row["stop_reason"] == "turn_wall_cap", row["stop_reason"]
    assert row["truncated"] is True, row.get("truncated")


CHECKS = [
    ("tool-hole", "tool-call delta, no finish, no text -> tool_calls",
     test_tool_call_delta_without_finish_is_tool_calls),
    ("tool-fragment", "a bare arguments fragment is still a production",
     test_bare_argument_fragment_alone_is_tool_calls),
    ("honest-empty", "no tool call, no finish, no content -> empty_response",
     test_no_tool_call_no_finish_no_content_is_empty_response),
    ("row-length", "length recomputable from the row alone",
     test_length_recomputable_from_the_row_without_a_manifest),
    ("row-ceiling", "every turn row carries max_tokens",
     test_every_turn_row_carries_the_ceiling_even_on_failure),
    ("vocab", "all ten members inducible, unmappable -> unknown",
     test_all_ten_members_inducible_and_unmappable_is_unknown),
    ("runaway", "runaway abort -> runaway_turn",
     test_runaway_abort_records_runaway_turn),
    ("slow", "a single slow turn -> turn_wall_cap",
     test_single_slow_turn_stays_turn_wall_cap),
]


def main():
    failures = 0
    for name, desc, fn in CHECKS:
        try:
            fn()
            print("PASS %-14s %s" % (name, desc))
        except AssertionError as exc:
            failures += 1
            print("FAIL %-14s %s\n     %s" % (name, desc, exc))
    print("%d/%d checks passed" % (len(CHECKS) - failures, len(CHECKS)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
