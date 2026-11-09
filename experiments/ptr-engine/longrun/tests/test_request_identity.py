"""REQUEST-IDENTITY: does the new row field tell a duplicate from a re-send?

Run from the workspace root:

    python3 experiments/ptr-engine/longrun/tests/test_request_identity.py

Exit 0 = every GREEN assertion held AND the two RED assertions failed for the intended
reason.  The file is also pytest-collectable (every ``test_*`` function is a case).

WHY THIS TEST EXISTS
====================
`V-DUPLICATE-RULE` failed the ledger's duplicate rule on one decisive point: the rule's
``content_sha256`` is ``sha256(assistant content)`` — the RESPONSE
(`experiments/ptr-engine/longrun/run_longrun.py:1555`, confirmed 869/869 rows), so the
tuple ``(ts, content_sha256, prompt_tokens, completion_tokens)`` merges two rows that
share a RESPONSE, not a REQUEST.  It cannot distinguish

    (i)  one request whose row was written twice, from
    (ii) two different requests that happened to return byte-identical text.

Cases (a)-(c) below are the three questions the ledger rule has to answer, asked of
``client.request_digest`` / ``send_chat``'s ``request_sha256`` / ``append_row``'s
``row_seq``:

  (a) two DIFFERENT requests with byte-identical response text -> different
      ``request_sha256`` (the old tuple says "duplicate": RED);
  (b) the SAME request re-sent -> same ``request_sha256`` AND a new ``row_seq``
      (one send, two sends: same hash, two positions);
  (c) ONE request whose row is written twice -> same ``request_sha256`` AND the same
      ``row_seq``.

The historical double append is reproduced at the end with the real writer functions:
the mechanism (`run_longrun.py:2072-2076`, turn row built from the response
`fetch_rounds` returned) makes a ``kind="tool-followup"`` row and a ``kind="turn"`` row
share one response object.  Under the new identity they must share ``request_sha256``,
which is exactly what the ledger rule must read.

Zero requests: every stream is a fake, the clock is a fake, and ``_no_socket`` makes a
real socket impossible for the whole run.
"""

import json
import os
import socket
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE.rsplit(os.sep, 1)[0])

import client  # noqa: E402  (module under test)
import run_longrun as rl  # noqa: E402  (the writer under test)


FAILURES: list[str] = []
CHECKS = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if cond:
        print("  GREEN %s" % name)
    else:
        print("  RED   %s  %s" % (name, detail))
        FAILURES.append(name)


def check_red(name: str, cond: bool, detail: str = "") -> None:
    """A RED assertion passes when the OLD rule's behaviour is reproduced."""
    global CHECKS
    CHECKS += 1
    if cond:
        print("  RED-as-designed %s" % name)
    else:
        print("  NOT-RED %s  %s" % (name, detail))
        FAILURES.append(name)


def _no_socket(*_a, **_k):
    raise AssertionError("network is forbidden in this test")


# The guard is installed only for the duration of the run (module-level patching would
# leak into every later test in a shared pytest session).
_REAL_SOCKET = socket.socket


# ----------------------------------------------------------------------- fakes
class FakeCfg:
    model = "fake-model"
    base_url = "http://127.0.0.1:9/v1"
    stream = False            # non-streamed: one JSON body, no SSE folding needed
    max_tokens = 64
    engine = "sglang"
    timeout = 5.0
    metrics_timeout = 1.0
    metrics_scrape = False
    turn_wall_cap = None


class _Resp:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self) -> bytes:
        return self._payload

    def __iter__(self):
        return iter(())


def opener_for(response_text: str):
    """An opener that always answers with the SAME assistant text."""
    payload = json.dumps({
        "choices": [{"index": 0, "message": {"content": response_text},
                     "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 3},
    }).encode("utf-8")

    def opener(_req, _timeout):
        return _Resp(payload)

    return opener


_FIXTURE = {
    "task_id": "request-identity",
    "_sha256": "0" * 64,
    "bytes_per_token": 4.0,
    "N": 4,
    "checkpoints": [],
    "system_prompt": "s",
    "turns": [],
}
_EXTRAS = {"prompt_sha256": "a" * 64, "lease": 1, "evicted": 0}


def _messages(text: str) -> list[dict]:
    return [{"role": "system", "content": "sys"}, {"role": "user", "content": text}]


def _send(text: str, response_text: str = "identical answer") -> dict:
    return client.send_chat(FakeCfg(), _messages(text), opener=opener_for(response_text),
                            clock=_FakeClock())


class _FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self) -> float:
        self.t += 0.001
        return self.t


def _write_rows(rows: list[dict]) -> tuple[str, list[dict]]:
    d = tempfile.mkdtemp(prefix="reqid-")
    path = os.path.join(d, "rows-request-identity.jsonl")
    for row in rows:
        rl.append_row(path, row)
    with open(path, encoding="utf-8") as fh:
        return path, [json.loads(line) for line in fh if line.strip()]


# --------------------------------------------------------- (a) different requests
def case_a():
    print("\n(a) two DIFFERENT requests, byte-identical response text")
    r1 = _send("question one")
    r2 = _send("question two")
    text = "identical answer"
    check("response content is byte-identical",
          r1["content"] == r2["content"] == text)
    check("LEGACY content_sha256 collides (why the old rule merges)",
          rl.sha256_text(r1["content"]) == rl.sha256_text(r2["content"]))
    check("request_sha256 DIFFERS for two different requests",
          r1["request_sha256"] != r2["request_sha256"],
          "%s vs %s" % (r1["request_sha256"], r2["request_sha256"]))
    check("both identities are complete",
          r1["request_identity_complete"] and r2["request_identity_complete"])

    # RED: the ledger's tuple would call this pair a duplicate although it is two sends.
    row1 = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r1, r1["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    row2 = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 2, r2, r2["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    old_tuple = lambda r: (r["content_sha256"], r["prompt_tokens"], r["completion_tokens"])  # noqa: E731
    check_red("legacy tuple (without ts) equates the two sends", old_tuple(row1) == old_tuple(row2))
    check("new identity keeps them apart on the row itself",
          row1["request_sha256"] != row2["request_sha256"])


# ------------------------------------------------------------- (b) same request
def case_b():
    print("\n(b) the SAME request re-sent")
    r1 = _send("re-send me")
    r2 = _send("re-send me")
    check("re-send gets the SAME request_sha256",
          r1["request_sha256"] == r2["request_sha256"],
          "%s vs %s" % (r1["request_sha256"], r2["request_sha256"]))
    row1 = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r1, r1["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    row2 = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r2, r2["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    _path, rows = _write_rows([row1, row2])
    check("row_seq is 1 then 2 (a re-send is a new write position)",
          [r["row_seq"] for r in rows] == [1, 2],
          repr([r.get("row_seq") for r in rows]))
    check("same request_sha256, different row_seq -> NOT a duplicate",
          rows[0]["request_sha256"] == rows[1]["request_sha256"]
          and rows[0]["row_seq"] != rows[1]["row_seq"])


# ----------------------------------------------------------- (c) one send, two rows
def case_c():
    print("\n(c) ONE request whose row is written twice")
    r = _send("the turn that gets written twice")
    follow = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r, r["content"],
                         "tool-followup", "m" * 64,
                         dict(_EXTRAS, fetch_followup=True,
                              prompt_sha256=rl.sha256_text("follow-up user message")))
    turn = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r, r["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    check("the two rows measure one response",
          follow["content_sha256"] == turn["content_sha256"]
          and follow["ttft_s"] == turn["ttft_s"]
          and follow["latency_s"] == turn["latency_s"])
    check("the two rows share ONE request_sha256",
          follow["request_sha256"] == turn["request_sha256"])
    check("their prompt_sha256 differ (the writer's own contradiction)",
          follow["prompt_sha256"] != turn["prompt_sha256"])

    # The same row object appended twice keeps its seq: the double-append signature.
    _path, rows = _write_rows([follow, follow])
    check("same object written twice -> same row_seq",
          rows[0]["row_seq"] == rows[1]["row_seq"],
          repr([r.get("row_seq") for r in rows]))
    check("duplicate = same request_sha256 AND same row_seq",
          rows[0]["request_sha256"] == rows[1]["request_sha256"]
          and rows[0]["row_seq"] == rows[1]["row_seq"])


# ------------------------------------------------ (d) the historical mechanism, live
def case_d():
    print("\n(d) reproduce the 30 historical pairs with the real writer functions")
    r = _send("turn one's last follow-up")
    follow = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r, r["content"],
                         "tool-followup", "m" * 64,
                         dict(_EXTRAS, fetch_followup=True,
                              prompt_sha256=rl.sha256_text("follow-up user message")))
    turn = rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, r, r["content"],
                       "turn", "m" * 64, dict(_EXTRAS))
    check("turn-row content_sha256 == follow-up-row content_sha256 (rows 1..30)",
          follow["content_sha256"] == turn["content_sha256"])
    check("and both name ONE send by request_sha256 (the detector fires)",
          follow["request_sha256"] == turn["request_sha256"])
    check("the failed row keeps request_sha256='unknown' and complete=false",
          rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, None, None,
                      "turn", "m" * 64, dict(_EXTRAS))["request_sha256"]
          == client.REQUEST_SHA_UNKNOWN
          and rl.make_row(FakeCfg(), _FIXTURE, "arm", 1, "run", 1, None, None,
                          "turn", "m" * 64, dict(_EXTRAS))["request_identity_complete"]
          is False)


def test_request_identity() -> int:
    print("REQUEST-IDENTITY — the three-way discriminator")
    socket.socket = _no_socket  # type: ignore[assignment]
    try:
        case_a()
        case_b()
        case_c()
        case_d()
    finally:
        socket.socket = _REAL_SOCKET  # type: ignore[assignment]
    print("\n%d checks, %d failed" % (CHECKS, len(FAILURES)))
    if FAILURES:
        print("FAILED: %s" % ", ".join(FAILURES))
        return 1
    print("ALL GREEN (and both RED assertions failed as designed)")
    return 0


# ------------------------------------------------------- red -> green (the guards)
def red_green() -> int:
    """Revert the two guards IN MEMORY and require the suite to go RED for that reason.

    Guard 1 — ``make_row`` writes a REQUEST identity.  Neutered, the row falls back to the
    old rule's value (a hash of the RESPONSE), which is exactly the defect.
    Guard 2 — ``append_row`` assigns ``row_seq`` once per row OBJECT.  Neutered, every
    write takes a fresh integer, so a double append stops being visible.

    Nothing on disk is touched: both are module attributes patched for the duration.
    """
    global CHECKS
    print("RED->GREEN — reverter run")
    real_make, real_append = rl.make_row, rl.append_row

    def old_make_row(*a, **k):
        row = real_make(*a, **k)
        row["request_sha256"] = row.get("content_sha256") or client.REQUEST_SHA_UNKNOWN
        return row

    def old_append_row(path, row):
        row.pop("row_seq", None)          # every write is a brand new position
        return real_append(path, row)

    rl.make_row, rl.append_row = old_make_row, old_append_row
    saved, saved_checks = list(FAILURES), CHECKS
    FAILURES.clear()
    try:
        socket.socket = _no_socket  # type: ignore[assignment]
        case_a()
        case_c()
    finally:
        socket.socket = _REAL_SOCKET  # type: ignore[assignment]
        rl.make_row, rl.append_row = real_make, real_append
    red = list(FAILURES)
    FAILURES.clear()
    FAILURES.extend(saved)
    CHECKS = saved_checks
    print("\nRED with the guards reverted: %s" % (", ".join(red) or "NOTHING (test cannot fail)"))
    if not red:
        print("RED->GREEN FAILED: the suite passes with the identity reverted")
        return 1
    if test_request_identity() != 0:
        return 1
    print("RED->GREEN: %d check(s) red with the identity reverted, all green restored" % len(red))
    return 0


if __name__ == "__main__":
    if "--red-green" in sys.argv[1:]:
        raise SystemExit(red_green())
    raise SystemExit(test_request_identity())
