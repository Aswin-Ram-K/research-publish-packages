#!/usr/bin/env python3
"""test_row_attribution.py - a turn's OWN send must have its own measurement.

Run from the workspace root:

    python3 experiments/ptr-engine/longrun/tests/test_row_attribution.py
    python3 experiments/ptr-engine/longrun/tests/test_row_attribution.py --red-green

Exit 0 = every GREEN assertion held AND every RED assertion reproduced the pre-fix
defect.  Pytest-collectable: every ``test_*`` function is one case.

WHY THIS TEST EXISTS
====================
`orchestration/handoffs/DEDUPE-ROOT-CAUSE.json` (`evidence.double_append`) proved that
the writer built the ``kind="tool-followup"`` row from the LAST follow-up response and
then handed that SAME object back to the caller, which rebuilt the ``kind="turn"`` row
from it.  Per turn with k >= 1 follow-ups that gave k+1 sends, k+1 rows and only k
distinct measurements: the turn's INITIAL send left no measurement of its own, and the
turn row carried the last follow-up's latency.

THE CONTRACT THIS FILE CHECKS (docs/ROW-MODEL.md)
=================================================
For every turn, with k follow-ups:

  * the number of rows for the turn equals the number of HTTP requests it made (k+1);
  * the number of DISTINCT ``request_sha256`` values equals the number of sends;
  * every send's ``ttft_ms`` appears exactly once -- no row mirrors another row's
    measurement;
  * the initial send is its own row (``kind="turn-initial"``, ``send_index=0``);
  * the turn row's ``prompt_sha256`` is the hash of the prompt the TURN sent, i.e. the
    user message of send 0, not the follow-up prompt.

k = 0, 1, 2 and 3 are each driven end-to-end through the real ``run_longrun.run_cell``
with a fixture and a canned ``send_chat``.  Zero requests: ``socket.socket`` raises for
the whole run and ``send_chat`` is a counted fake that never touches the network.  No
row file, grade file or report is read or modified -- every cell writes into its own
temporary directory.
"""

from __future__ import annotations

import hashlib
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
ARM = "pointer-stable"
# L1-30 of resolve.py lies OUTSIDE the pointer arm's pinned body (L36-110), so a call
# for it is executed rather than served from the prompt and buys a real follow-up.
UNPINNED = [(1, 30), (1, 31), (1, 32), (1, 33)]
FINAL_ANSWER = "ANSWER: TEXT offline"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Cfg:
    def __init__(self):
        self.tools = "read_file"
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model-was-never-called"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = 1
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = None
        self.fetch_rounds_per_turn = 0          # 0 = unbounded per turn (the run's cap)
        self.turn_wall_cap = 0


def _resp(text, send_id, ttft_ms):
    """One canned response object shaped like ``client.send_chat``'s return."""
    return {
        "content": text, "content_raw": text, "reasoning": "",
        "content_source": "content", "finish_reason": "stop", "truncated": False,
        "max_tokens": 256, "prompt_tokens": 10 + send_id, "raw_cached": None,
        "token_source": "offline", "completion_tokens": 5, "wall_ms": ttft_ms + 40,
        # REQUEST-IDENTITY: a real wire body would hash here; one distinct value per SEND.
        "request_sha256": _sha("wire-body-%d" % send_id),
        "request_identity_complete": True,
        "ttft_s": round(ttft_ms / 1000.0, 6), "ttft_ms": ttft_ms,
        "latency_s": round((ttft_ms + 40) / 1000.0, 6),
        "usage_missing": False,
    }


def _drive(k: int):
    """Run one offline cell whose turn 1 grants exactly ``k`` tool follow-ups.

    Returns (rows, sends, first_user_prompt) where ``sends`` is the number of requests
    that actually reached ``send_chat`` for turn 1 and ``first_user_prompt`` is the user
    message of send 0 (the turn's own prompt).
    """
    tmp = tempfile.mkdtemp(prefix="rowattr-k%d-" % k)
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(FIXTURE)
    cfg = _Cfg()
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    run_id = "offline-row-attr-k%d-r1" % k

    state = {"sends": 0, "turn1": 0, "first_user": None}

    def fake_send_chat(_cfg, messages):
        idx = state["sends"]
        state["sends"] = idx + 1
        if state["turn1"] == 0:
            state["first_user"] = messages[1]["content"]
        within_turn = state["turn1"]
        state["turn1"] += 1
        if within_turn < k:
            start, end = UNPINNED[within_turn % len(UNPINNED)]
            text = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                    '"start_line": %d, "end_line": %d}' % (start, end))
        else:
            text = FINAL_ANSWER
        return _resp(text, idx, ttft_ms=100 + 25 * idx)

    buf, old_stdout = io.StringIO(), sys.stdout
    real_send, real_socket = R.send_chat, socket.socket
    R.send_chat = fake_send_chat
    socket.socket = _no_network()
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, ARM, 1, run_id, rows_path)
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
        sys.stdout = old_stdout
    assert rc == 0, "run_cell exit %d (expected 0)\n%s" % (rc, buf.getvalue()[-3000:])

    rows = []
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                row = json.loads(line)
                if int(row.get("turn") or 0) == 1:
                    rows.append(row)
    return rows, k + 1, state["first_user"], state["sends"]


def _no_network():
    def _denied(*_a, **_k):
        raise AssertionError("the row-attribution test must never open a socket")
    return _denied


def _measure_rows(rows):
    """The rows that carry a measurement of ONE send (excludes no-measurement rows)."""
    return [r for r in rows if r.get("kind") in ("turn", "turn-initial", "tool-followup")]


# ------------------------------------------------------------------- GREEN cases
def test_k0_no_followup():
    rows, sends, prompt, seen = _drive(0)
    measured = _measure_rows(rows)
    assert seen == sends == 1, (seen, sends)
    assert len(measured) == sends, [r.get("kind") for r in measured]
    assert measured[0]["kind"] == "turn"
    assert measured[0]["send_index"] == 0
    assert measured[0]["row_measurement_source"] == "turn-initial"
    assert measured[0]["prompt_sha256"] == _sha(prompt), "turn prompt hash is not the sent prompt"
    assert not any(r.get("kind") == "turn-initial" for r in rows), "k=0 invents an initial row"


def test_k1_initial_send_has_its_own_row():
    rows, sends, prompt, seen = _drive(1)
    measured = _measure_rows(rows)
    assert seen == sends == 2, (seen, sends)
    assert len(measured) == sends, [r.get("kind") for r in measured]
    initial = [r for r in measured if r.get("kind") == "turn-initial"]
    assert len(initial) == 1, [r.get("kind") for r in measured]
    assert initial[0]["send_index"] == 0
    assert initial[0]["prompt_sha256"] == _sha(prompt)
    turn = [r for r in measured if r.get("kind") == "turn"][0]
    assert turn["send_index"] == 1
    assert turn["content"] == FINAL_ANSWER, turn["content"]
    assert turn["prompt_sha256"] == _sha(prompt), "the turn row's prompt hash is the TURN's prompt"
    _assert_one_measurement_per_send(measured, sends)


def test_k2_consecutive_followups():
    rows, sends, prompt, seen = _drive(2)
    measured = _measure_rows(rows)
    assert seen == sends == 3, (seen, sends)
    assert len(measured) == sends, [r.get("kind") for r in measured]
    assert sorted(int(r["send_index"]) for r in measured) == list(range(sends))
    turn = [r for r in measured if r.get("kind") == "turn"][0]
    assert turn["prompt_sha256"] == _sha(prompt)
    assert turn["fetch_followup"] is True and turn.get("fetch_round_final") is True
    _assert_one_measurement_per_send(measured, sends)


def test_k3_three_followups():
    rows, sends, prompt, seen = _drive(3)
    measured = _measure_rows(rows)
    assert seen == sends == 4, (seen, sends)
    assert len(measured) == sends, [r.get("kind") for r in measured]
    assert sorted(int(r["send_index"]) for r in measured) == list(range(sends))
    assert [r["kind"] for r in measured] == ["turn-initial"] + ["tool-followup"] * 2 + ["turn"]
    _assert_one_measurement_per_send(measured, sends)


def _assert_one_measurement_per_send(measured, sends):
    """THE INVARIANT: distinct request_sha256 per turn == sends; ttft appears once."""
    shas = [r["request_sha256"] for r in measured]
    assert len(set(shas)) == sends, (len(set(shas)), sends, shas)
    assert all(s and s != R.client.REQUEST_SHA_UNKNOWN for s in shas), shas
    ttfts = [r["ttft_ms"] for r in measured]
    assert len(set(ttfts)) == sends, ("two rows share one measurement", ttfts)
    # no two rows may carry the same request identity -> no mirror row exists
    assert len(set(shas)) == len(shas), ("a request is recorded twice", shas)


# ------------------------------------------------------------- RED (pre-fix) case
def test_red_without_attribution_reproduces_the_defect():
    """Revert the fix IN MEMORY (the old ``resp`` rebinding) and the invariant breaks.

    The pre-fix writer wrote every follow-up row AND a turn row built from the last
    follow-up's response: k+1 rows, k distinct measurements, no initial row.
    """
    k = 2
    tmp = tempfile.mkdtemp(prefix="rowattr-red-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(FIXTURE)
    cfg = _Cfg()
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    state = {"sends": 0, "turn1": 0}

    def fake_send_chat(_cfg, messages):
        idx = state["sends"]
        state["sends"] = idx + 1
        within = state["turn1"]
        state["turn1"] += 1
        if within < k:
            start, end = UNPINNED[within % len(UNPINNED)]
            text = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                    '"start_line": %d, "end_line": %d}' % (start, end))
        else:
            text = FINAL_ANSWER
        return _resp(text, idx, ttft_ms=100 + 25 * idx)

    buf, old_stdout = io.StringIO(), sys.stdout
    real_send, real_socket, real_guard = R.send_chat, socket.socket, R.attribute_initial_send
    R.send_chat = fake_send_chat
    R.attribute_initial_send = lambda: False        # IN MEMORY: the pre-fix writer
    socket.socket = _no_network()
    sys.stdout = buf
    try:
        rc = R.run_cell(cfg, fixture, ARM, 1, "offline-row-attr-red-r1", rows_path)
    finally:
        R.send_chat = real_send
        R.attribute_initial_send = real_guard
        socket.socket = real_socket
        sys.stdout = old_stdout
    assert rc == 0, "red run exit %d\n%s" % (rc, buf.getvalue()[-3000:])

    rows = []
    with open(rows_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                row = json.loads(line)
                if int(row.get("turn") or 0) == 1:
                    rows.append(row)
    measured = _measure_rows(rows)
    sends = k + 1
    # THE DEFECT, asserted positively: no initial row, and one measurement short.
    assert not any(r.get("kind") == "turn-initial" for r in rows), \
        "the reverted writer still wrote an initial row - the red proof is not red"
    assert len(set(r["request_sha256"] for r in measured)) == sends - 1, \
        "reverted writer must leave the initial send unmeasured"
    assert len(measured) == sends, "the old writer still wrote k+1 rows (one of them a mirror)"
    assert len(set(r["ttft_ms"] for r in measured)) == sends - 1, \
        "the old writer's turn row must mirror the last follow-up's ttft"
    print("RED (attribution reverted in memory): %d rows / %d sends / %d distinct "
          "measurements - the initial send has no row" %
          (len(measured), sends, len(set(r["ttft_ms"] for r in measured))))


def main() -> int:
    cases = [
        ("k=0", test_k0_no_followup),
        ("k=1", test_k1_initial_send_has_its_own_row),
        ("k=2", test_k2_consecutive_followups),
        ("k=3", test_k3_three_followups),
    ]
    fails = 0
    for name, fn in cases:
        try:
            fn()
        except AssertionError as exc:
            fails += 1
            print("FAIL %-4s %s" % (name, str(exc)[:600]))
        else:
            print("ok   %-4s one row per send, distinct ttft, turn prompt hash" % name)
    if "--red-green" in sys.argv[1:]:
        try:
            test_red_without_attribution_reproduces_the_defect()
        except AssertionError as exc:
            fails += 1
            print("FAIL red  %s" % str(exc)[:600])
    print("\n%d green case(s), %d failure(s); RED->GREEN: the same assertions fail with "
          "attribute_initial_send() reverted in memory" % (len(cases), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
