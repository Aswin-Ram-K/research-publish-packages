"""HARNESS-GUARDS: the run cannot run away. OFFLINE — every stream is faked.

    python3 experiments/ptr-engine/longrun/tests/test_guards.py
    .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_guards.py -q

WHY: the first live cell (`dbed0e9d`, cancelled) produced a turn of 16,384 completion
tokens over 475,873 ms with `thinking` on and nothing in the harness objected — a human
had to stop it. The measurement path was sound; the RUN was unguarded. These tests pin
the four guards and each is RED before the fix:

  (a) every payload carries a finite `max_tokens` (the pre-fix body did not demand it),
  (b) a stream that never ends trips `--turn-wall-cap`; the row records
      error="turn_wall_cap" and truncated=true,
  (c) `--runaway-turns` ends the cell with a non-zero exit after partial rows are written,
  (d) `cell.py` refuses (exit 8) a projection past `--max-wall` BEFORE the runner runs,
  (e) a cell's default thinking policy is OFF and the row records it.

Zero inference requests: the only socket is a fake HTTP server on 127.0.0.1 that emits a
stream of tokens and stops when the client closes; 192.168.2.168 is never contacted.
"""

import json
import os
import shutil
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
CELL = os.path.join(LONG, "cell.py")
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"  # a real arm of run_longrun.py
PY = sys.executable
sys.path.insert(0, LONG)

import client  # noqa: E402


# ------------------------------------------------------------------ (a) payload
def _cfg(**kw):
    base = dict(model="fake-model", stream=True, base_url="http://127.0.0.1:1/v1",
                engine="sglang", timeout=5.0, max_tokens=4096, thinking="off",
                metrics_scrape=False)
    base.update(kw)
    return SimpleNamespace(**base)


class _Resp:
    """A fake HTTP response: iterable SSE lines, records that it was closed."""

    def __init__(self, lines):
        self._lines = lines
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True
        return False

    def __iter__(self):
        return iter(self._lines)

    def read(self):
        return b""


def _sse(text, kind="content", finish=None):
    delta = {kind: text}
    return ("data: " + json.dumps({"choices": [{"delta": delta, "index": 0,
                                                "finish_reason": finish}]}) + "\n").encode()


def _end():
    return b"data: [DONE]\n"


def _payload(cfg, messages=None, **kw):
    """Capture the payload that leaves the client (not the code that builds it)."""
    seen = {}

    def opener(req, timeout):
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp([_sse("ok"), _end()])

    client.send_chat(cfg, messages or [{"role": "user", "content": "hi"}],
                     opener=opener, clock=lambda: 0.0, **kw)
    return seen["body"]


def _require_max_tokens(payload, expected):
    assert "max_tokens" in payload, "payload has no max_tokens: %r" % (payload,)
    assert isinstance(payload["max_tokens"], int) and payload["max_tokens"] > 0, \
        "max_tokens is not a finite positive int: %r" % (payload,)
    assert payload["max_tokens"] == expected, \
        "max_tokens %r != configured %r" % (payload["max_tokens"], expected)


def check_a_payload_carries_max_tokens():
    body = _payload(_cfg(max_tokens=777))
    _require_max_tokens(body, 777)
    # explicit override wins and is what reaches the wire
    _require_max_tokens(_payload(_cfg(max_tokens=777), max_tokens=321), 321)
    # a namespace with no max_tokens attribute still sends the finite default
    naked = SimpleNamespace(model="m", stream=True, base_url="http://127.0.0.1:1/v1",
                            engine="sglang", timeout=5.0, thinking="off",
                            metrics_scrape=False)
    _require_max_tokens(_payload(naked), client.DEFAULT_MAX_TOKENS)
    assert client.DEFAULT_MAX_TOKENS == 4096, client.DEFAULT_MAX_TOKENS
    # a nonsensical cap is refused, never omitted
    for bad in (None, 0, -1, "x"):
        try:
            client.request_body(_cfg(max_tokens=bad), [])
        except ValueError:
            continue
        raise AssertionError("request_body accepted max_tokens=%r" % (bad,))
    # RED: the pre-fix body had no max_tokens and must FAIL this contract.
    legacy = {"model": "fake-model", "messages": [], "temperature": 0, "stream": True}
    try:
        _require_max_tokens(legacy, 4096)
    except AssertionError:
        pass
    else:
        raise AssertionError("RED(a) did not fail: the legacy body passed the contract")


# ------------------------------------------------------------- (b) turn wall cap
class _StepClock:
    """A clock that advances on every read, so a stream that never ends trips the cap."""

    def __init__(self, step=0.9):
        self.t = 0.0
        self.step = step

    def __call__(self):
        now = self.t
        self.t += self.step
        return now


class _Forever:
    def __init__(self, n=40):
        self.n = n

    def __iter__(self):
        for i in range(self.n):
            yield _sse("tok%d " % i, "reasoning_content")


def check_b_cap_aborts_stream():
    resp = _Resp(list(_Forever()))

    def opener(req, timeout):
        return resp

    cfg = _cfg(turn_wall_cap=2.0)
    try:
        client.send_chat(cfg, [{"role": "user", "content": "go"}],
                         opener=opener, clock=_StepClock(0.9))
    except client.TurnWallCap as exc:
        assert exc.error_code == "turn_wall_cap"
        assert exc.wall_s > 2.0, exc.wall_s
        assert exc.fields["completion_tokens"] > 0, exc.fields
        assert exc.fields["first_token_kind"] == "reasoning"
        part = exc.as_response(cfg)
        assert part["truncated"] is True, part
        assert part["max_tokens"] == 4096
    else:
        raise AssertionError("a stream past the wall cap was READ TO THE END")
    assert resp.closed, "the stream was not closed after the cap fired"

    # RED: the same fold WITHOUT the cap reads on to the end and reports no abort.
    folded = client.collect_stream(client.iter_stream_chunks(_Forever(10)), 0.0,
                                   _StepClock(0.9))
    assert folded["content_raw"] == "", folded
    assert "turn_wall_cap" not in json.dumps(folded), folded


# ------------------------------------------------ end-to-end cell through cell.py
class _Fake:
    """A local, fake inference server: SSE tokens forever, plus a /metrics stub."""

    def __init__(self):
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                outer.hits["GET"] = outer.hits.get("GET", 0) + 1
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"")

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                outer.last_body = json.loads(self.rfile.read(n).decode("utf-8"))
                outer.hits["POST"] = outer.hits.get("POST", 0) + 1
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                try:
                    i = 0
                    while True:
                        self.wfile.write(_sse("runaway%d " % i, "reasoning_content"))
                        self.wfile.flush()
                        i += 1
                        time.sleep(0.02)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

        self.hits = {}
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


def _run_runner(tmp, url, turns, runaway, wall_cap, rows_name="rows.jsonl"):
    rows = os.path.join(tmp, rows_name)
    argv = [PY, RUNNER, "--fixture", FIXTURE, "--arms", ARM, "--reps", "1",
            "--max-turns", str(turns), "--turn-wall-cap", str(wall_cap),
            "--runaway-turns", str(runaway), "--rows", rows,
            "--manifest-path", os.path.join(tmp, "manifest-%s.json" % rows_name),
            "--base-url", url, "--no-metrics-scrape", "--max-tokens", "4096",
            "--temperature", "0",
            "--budget-cap", "1000", "--budget-glob", os.path.join(tmp, "*.jsonl")]
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=LONG, timeout=180)
    parsed = []
    if os.path.exists(rows):
        with open(rows, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    parsed.append(json.loads(line))
    return proc, parsed, rows


def check_c_runaway_ends_the_cell(tmp):
    with _Fake() as fake:
        proc, rows, _ = _run_runner(tmp, fake.url, 4, 2, 0.4, "stop.jsonl")
        assert fake.last_body is not None, "no request reached the fake server"
        assert fake.last_body.get("max_tokens") == 4096, fake.last_body
        assert proc.returncode == 6, ("expected exit 6 after --runaway-turns 2, got %d\n%s\n%s"
                                      % (proc.returncode, proc.stdout[-2000:],
                                         proc.stderr[-3000:]))
        assert "RUNAWAY" in proc.stderr, proc.stderr[-2000:]
        assert len(rows) == 2, "partial rows not written before the abort: %d" % len(rows)
        for row in rows:
            assert row["error"] == "turn_wall_cap", row.get("error")
            assert row["truncated"] is True, row.get("truncated")
            assert row["max_tokens"] == 4096, row.get("max_tokens")
            assert row["thinking"] == "off", row.get("thinking")
        # RED: with the runaway guard effectively off the SAME cell runs all 4 turns and
        # exits 0 — so the stop is the guard's doing, not the fixture's.
        proc2, rows2, _ = _run_runner(tmp, fake.url, 4, 99, 0.4, "nored.jsonl")
        assert proc2.returncode == 0, ("without --runaway-turns the run should not abort, "
                                       "got %d" % proc2.returncode)
        assert len(rows2) == 4, "red run wrote %d rows" % len(rows2)


def check_cap_rows_record_error(tmp):
    with _Fake() as fake:
        proc, rows, _ = _run_runner(tmp, fake.url, 1, 2, 0.4, "one.jsonl")
        assert proc.returncode == 0, (proc.returncode, proc.stderr[-2000:])
        assert len(rows) == 1, rows
        row = rows[0]
        assert row["error"] == "turn_wall_cap", row.get("error")
        assert row["truncated"] is True
        assert row["ttft_source"] == "first_delta", row.get("ttft_source")
        assert row["first_token_kind"] == "reasoning", row.get("first_token_kind")
        assert row["ttft_ms"] is not None and row["wall_ms"] is not None
        assert row["ttft_ms"] != row["wall_ms"], "TTFT was substituted by wall clock"
        assert row["completion_tokens"] and row["completion_tokens"] > 0
        # RED: the row is written by the client's cap; a payload without max_tokens was
        # what let the 16,384-token turn exist, and the row must prove the ceiling.
        assert fake.last_body["max_tokens"] == row["max_tokens"] == 4096


# ------------------------------------------------------- (d) projection, exit 8
def _projection_run(tmp):
    out = os.path.join(tmp, "proj")
    os.makedirs(out, exist_ok=True)
    marker = os.path.join(tmp, "live-runner-invoked.marker")
    fake = os.path.join(tmp, "fake_runner.py")
    with open(fake, "w", encoding="utf-8") as fh:
        fh.write("import sys, os\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('  would_send_total=48')\n"
                 "    sys.exit(0)\n"
                 "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
                 "sys.exit(0)\n")
    argv = [PY, CELL, "--arm", ARM, "--fixture", FIXTURE, "--turns", "48", "--reps", "1",
            "--budget", "1000", "--out-dir", out, "--no-cell-handoff",
            # PROJECTION-CALIBRATION: the projection now multiplies by the expected
            # per-turn wall (default 60 s), so this cell is affordable. The guard's own
            # exit-8 contract is pinned here by asking for the old worst case explicitly
            # (--projected-turn-wall 180 == --turn-wall-cap), which must still refuse.
            "--projected-turn-wall", "180",
            # GATE-CHAIN-FIX D2: silence is a refusal now, so every live path must name
            # the claim it would make. This cell (n=48) can honestly declare H2.
            "--hypothesis", "H2"]
    env = dict(os.environ, CELL_RUNNER_PATH=fake, CELL_MARKER=marker)
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=os.path.dirname(LONG),
                          env=env, timeout=180)
    return proc, marker


def check_d_projection(tmp):
    proc, marker = _projection_run(tmp)
    assert proc.returncode == 8, ("expected exit 8, got %d\n%s\n%s"
                                  % (proc.returncode, proc.stdout[-3000:],
                                     proc.stderr[-2000:]))
    assert "projected_wall~=8640s" in proc.stdout, proc.stdout[-2000:]
    assert "--max-wall" in proc.stdout and "3600" in proc.stdout, proc.stdout[-2000:]
    assert "EXIT 8" in proc.stdout, proc.stdout[-1000:]
    assert not os.path.exists(marker), "the runner was invoked past the projection check"
    # RED: a conductor whose projection gate is neutered invokes the runner for the SAME
    # cell (marker). Before GATE-CHAIN-FIX this red passed `--max-wall 0` as a "disabled"
    # switch; a non-positive ceiling is now itself a refusal (exit 8), so the gate has to
    # be neutered in the source to prove it is load-bearing.
    with open(CELL, encoding="utf-8") as fh:
        source = fh.read()
    mutant = source.replace('"ok": (max_wall > 0 and projected <= max_wall),',
                            '"ok": True,  # RED(d) sabotage', 1)
    assert mutant != source, "RED(d): the projection verdict anchor drifted"
    try:
        with open(CELL, "w", encoding="utf-8") as fh:
            fh.write(mutant)
        proc2, marker2 = _projection_run(tmp)
    finally:
        with open(CELL, "w", encoding="utf-8") as fh:
            fh.write(source)
    assert os.path.exists(marker2), ("RED(d) proved nothing: the runner was not invoked "
                                     "with the projection gate neutered")
    assert proc2.returncode != 8, proc2.returncode


# --------------------------------------------------- (e) thinking policy recorded
def check_e_thinking_off_by_default(tmp):
    assert client.DEFAULT_THINKING == "off", client.DEFAULT_THINKING
    body = _payload(_cfg(thinking="off"))
    assert body.get("chat_template_kwargs") == {"enable_thinking": False}, body
    with _Fake() as fake:
        proc, rows, _ = _run_runner(tmp, fake.url, 1, 2, 0.4, "think.jsonl")
        assert proc.returncode == 0, proc.stderr[-1500:]
        assert rows and rows[0]["thinking"] == "off", rows[0].get("thinking")
        # the default reached the wire too
        assert fake.last_body.get("chat_template_kwargs") == {"enable_thinking": False}, \
            fake.last_body
        # RED: 'auto' omits the switch entirely — the pre-fix default was not "off".
        auto = _payload(_cfg(thinking="auto"))
        assert "chat_template_kwargs" not in auto, auto


# ------------------------------------------------------------------------ main
CHECKS = [
    ("a", "payload always carries a finite max_tokens", check_a_payload_carries_max_tokens),
    ("b", "turn wall cap aborts the stream and the row records it", check_b_cap_aborts_stream),
    ("c", "runaway turns stop the cell with exit 6 after partial rows", check_c_runaway_ends_the_cell),
    ("c2", "the cap row records error/truncated and honest TTFT", check_cap_rows_record_error),
    ("d", "projection refuses exit 8 before the runner is invoked", check_d_projection),
    ("e", "default thinking policy is off and recorded", check_e_thinking_off_by_default),
]


def test_guards_all():
    """pytest entry point: every case, with one throwaway tmp tree."""
    tmp = tempfile.mkdtemp(prefix="harness-guards-")
    try:
        for name, _desc, fn in CHECKS:
            fn(tmp) if name not in ("a", "b") else fn()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    tmp = tempfile.mkdtemp(prefix="harness-guards-")
    failed = 0
    try:
        for name, desc, fn in CHECKS:
            try:
                fn(tmp) if name not in ("a", "b") else fn()
            except AssertionError as exc:
                failed += 1
                print("RED %-3s %s\n     %s" % (name, desc, exc))
            else:
                print("GREEN %-3s %s" % (name, desc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d/%d GREEN" % (len(CHECKS) - failed, len(CHECKS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
