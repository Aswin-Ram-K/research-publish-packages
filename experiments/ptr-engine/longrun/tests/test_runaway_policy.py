"""RUNAWAY-POLICY: `--runaway-turns` counts WALL-TIME runaways, not cap-length truncations.

    python3 experiments/ptr-engine/longrun/tests/test_runaway_policy.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_runaway_policy.py -q

WHY (measured, cell 1 of RUN-A*): `--runaway-turns 2` aborted a 48-turn cell at T27 while
`turns_over_180s` was 0. The two turns that tripped it were 4,096-token `length`
truncations (T3, T27) that finished in seconds — a data property of the answer, not the
wall-time hazard the guard was built for (the historical 16,384-token / 475,873 ms turn).
The three tests below pin the policy in docs/RUNAWAY-POLICY.md (option B):

  (1) ONE cap-length truncation is data: the cell CONTINUES to all its turns, rc 0.
  (2) the abort condition (two WALL-TIME runaways) stops the cell and NAMES the turns.
  (3) the historical hazard is STILL caught: a turn that would run for hundreds of seconds
      is closed by --turn-wall-cap, counted, and ends the cell with exit 6.

Zero inference requests: every socket is a fake HTTP server on 127.0.0.1.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
RUNNER = os.environ.get("RUNAWAY_RUNNER") or os.path.join(LONG, "run_longrun.py")
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"
PY = sys.executable
CAP = 4096


def _sse(obj):
    return ("data: " + json.dumps(obj) + "\n").encode()


def _delta(text):
    return _sse({"choices": [{"index": 0, "delta": {"content": text},
                              "finish_reason": None}]})


def _finish(reason):
    return _sse({"choices": [{"index": 0, "delta": {}, "finish_reason": reason}]})


def _usage(n):
    return _sse({"choices": [], "usage": {"prompt_tokens": 11, "completion_tokens": n}})


_DONE = b"data: [DONE]\n"


class _Fake:
    """mode='length_once': request 1 truncates at the ceiling, the rest stop normally.
    mode='slow': every stream runs forever (only --turn-wall-cap can close it)."""

    def __init__(self, mode):
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.end_headers()

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(n)
                outer.requests += 1
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                try:
                    if mode == "slow":
                        i = 0
                        while True:
                            self.wfile.write(_delta("runaway%d " % i))
                            self.wfile.flush()
                            i += 1
                            time.sleep(0.02)
                    if mode == "length_once" and outer.requests == 1:
                        # THE MEASURED EVENT: finish_reason=length, completion == ceiling.
                        self.wfile.write(_delta("truncated answer "))
                        self.wfile.write(_finish("length"))
                        self.wfile.write(_usage(CAP))
                    else:
                        self.wfile.write(_delta("ok "))
                        self.wfile.write(_finish("stop"))
                        self.wfile.write(_usage(3))
                    self.wfile.write(_DONE)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

        self.requests = 0
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


def _run(tmp, url, turns, runaway, wall_cap, max_tokens, name):
    rows = os.path.join(tmp, name)
    argv = [PY, RUNNER, "--fixture", FIXTURE, "--arms", ARM, "--reps", "1",
            "--max-turns", str(turns), "--turn-wall-cap", str(wall_cap),
            "--runaway-turns", str(runaway), "--rows", rows,
            "--manifest-path", os.path.join(tmp, "manifest-%s.json" % name),
            "--base-url", url, "--no-metrics-scrape", "--max-tokens", str(max_tokens),
            "--temperature", "0",
            # own cap over own rows: the corpus ledger's 7869 > 4320 refusal is about
            # spend, not about the runaway contract this test pins.
            "--budget-cap", "1000", "--budget-glob", os.path.join(tmp, "*.jsonl")]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=LONG, timeout=180)
    parsed = []
    if os.path.exists(rows):
        with open(rows, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    parsed.append(json.loads(line))
    return proc, parsed


# ---------------------------------------------------------------- (1) data, not abort
def test_one_cap_length_turn_does_not_abort_the_cell():
    """A `length` truncation at --max-tokens costs one answer, not the other 47 turns."""
    tmp = tempfile.mkdtemp(prefix="runaway-policy-length-")
    with _Fake("length_once") as fake:
        # --runaway-turns 1: the red case. The old predicate fired on ONE such turn.
        proc, rows = _run(tmp, fake.url, 4, 1, 180, CAP, "length.jsonl")
    assert proc.returncode == 0, (proc.returncode, proc.stderr[-2000:])
    assert "RUNAWAY ABORT" not in proc.stderr, proc.stderr[-2000:]
    assert len(rows) == 4, "the cell must reach every turn: %r" % [r.get("turn") for r in rows]
    first = rows[0]
    assert first["stop_reason"] == "length", first["stop_reason"]
    assert first["truncated"] is True, first.get("truncated")
    assert first["completion_tokens"] == CAP, first["completion_tokens"]
    assert first.get("runaway_abort") is None, first
    assert all(r.get("runaway_abort") is None for r in rows), "no turn may be a runaway here"


# ------------------------------------------------- (2) the abort, naming its turns
def test_two_wall_time_runaways_abort_and_name_the_turns():
    """Two turns whose streams --turn-wall-cap closed end the cell, by index and reason."""
    tmp = tempfile.mkdtemp(prefix="runaway-policy-wall-")
    with _Fake("slow") as fake:
        proc, rows = _run(tmp, fake.url, 4, 2, 0.4, CAP, "wall.jsonl")
    assert proc.returncode == 6, (proc.returncode, proc.stderr[-2000:])
    err = proc.stderr
    assert "wall-time runaways 2/2" in err, err[-2000:]
    assert "T1 (wall " in err, "the message must name the turn by index: %r" % err[-2000:]
    assert "T2 (wall " in err, "the message must name the turn by index: %r" % err[-2000:]
    assert "partial" in err and "turns reached" in err, err[-2000:]
    assert len(rows) == 2, [r.get("turn") for r in rows]
    # the first runaway is recorded but does NOT end the run; the second one does.
    assert rows[0].get("runaway_abort") is None, rows[0]
    assert rows[0]["error"] == "turn_wall_cap", rows[0]["error"]
    assert rows[1].get("runaway_abort") is True, rows[1]
    assert rows[1]["stop_reason"] == "runaway_turn", rows[1]["stop_reason"]


# --------------------------------------- (3) THE LOAD-BEARING ONE: the historical hazard
def test_historical_16384_token_475s_turn_is_still_caught():
    """The LIVE-SMOKE-CELL shape (16,384 tokens, 475,873 ms) must still be caught.

    It is caught by the bound that replaces the cap-hit counter: the per-turn
    --turn-wall-cap closes the stream at the cap (client.py:530 raises TurnWallCap), the
    turn is recorded as truncated, and --runaway-turns 1 ends the cell with exit 6. The
    row's own wall proves the 475 s turn never ran to completion.
    """
    tmp = tempfile.mkdtemp(prefix="runaway-policy-hazard-")
    with _Fake("slow") as fake:
        proc, rows = _run(tmp, fake.url, 4, 1, 0.4, 16384, "hazard.jsonl")
    assert proc.returncode == 6, (proc.returncode, proc.stderr[-2000:])
    assert len(rows) == 1, [r.get("turn") for r in rows]
    row = rows[0]
    assert row["error"] == "turn_wall_cap", row.get("error")
    assert row["stop_reason"] == "runaway_turn", row["stop_reason"]
    assert row.get("runaway_abort") is True, row
    assert row["truncated"] is True, row.get("truncated")
    # bounded AT the cap, not left to run: the turn is closed at ~0.4 s, not 475 s.
    assert 0 < row["wall_ms"] < 5000, row["wall_ms"]
    assert row["max_tokens"] == 16384, row["max_tokens"]
    assert "wall-time runaways 1/1" in proc.stderr, proc.stderr[-2000:]


CHECKS = [
    ("length-is-data", "one cap-length turn continues the cell", test_one_cap_length_turn_does_not_abort_the_cell),
    ("wall-abort", "two wall-time runaways abort, naming turns", test_two_wall_time_runaways_abort_and_name_the_turns),
    ("hazard", "the 16,384-token / 475 s shape is still caught", test_historical_16384_token_475s_turn_is_still_caught),
]

if __name__ == "__main__":
    failed = 0
    for name, why, fn in CHECKS:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print("FAIL %-14s %s\n  %s" % (name, why, exc))
        else:
            print("ok   %-14s %s" % (name, why))
    sys.exit(1 if failed else 0)
