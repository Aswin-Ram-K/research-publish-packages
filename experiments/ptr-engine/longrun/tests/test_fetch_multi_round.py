#!/usr/bin/env python3
"""Red->green proof for FETCH-MULTI-ROUND on the ``bounded-context-fetch`` arm (U-SPCC-54).

THE DEFECT.  ``run_longrun.run_cell``'s ``arm == arm_cd.ARM_D`` block sent exactly ONE
``_resp2`` follow-up per turn.  ``TOOL_FETCH_ROUNDS_PER_TURN = 3``
(``run_longrun.py:460``) and ``fetch_rounds_cap_per_turn`` was stamped ``3`` on every
row, but ``max(fetch_rounds_this_turn) == 1`` across all 125 fetch rows of
``measure/rows-e1-parserfix-2026-11-10.jsonl``: a second call emitted on the same turn
was never serviced.  ``cp.TX-03.f04.d8`` (turn 32) is the last harness loss it caused --
the fetch succeeded and the follow-up's own tool call was dropped on the floor.

THE FIX.  The per-turn loop services up to ``fetch_rounds_per_turn(cfg)`` rounds.  After
a follow-up response it re-parses that response for declared tool calls and, if the
per-turn cap and the per-arm pool both allow, services them and sends again.  It stops
on: no further calls, the per-turn cap, the per-arm pool, or a non-tool-call finish.
Every follow-up is a PAID request and its row is on disk BEFORE the next send.

UNCHANGED.  The per-turn cap, the per-arm pool, the answer contract and the scoring.
A single response carrying several calls is still serviced in ONE round (that batching
predates this unit and is asserted below so the fix cannot silently change it).

Offline.  ZERO inference requests, no network, no git.  The transport is a fake that
returns the exact dict ``client.send_chat`` returns for a tool-call turn (built with the
client's own ``structured_tool_calls``), so the shape under test is the wire shape.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_fetch_multi_round.py -q
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)

import arm_cd  # noqa: E402
import run_longrun as R  # noqa: E402

# PT-01 carries ``fetch_budget_tokens`` (required by ``arm_cd.resolve_fetch_budget``)
# and declares its checkpoints at turns 12/24/28/32.
FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
ARM = arm_cd.ARM_D
FINAL_ANSWER = "ANSWER: TEXT offline"

#: The three refs PT-01's own tool outputs make resolvable, plus one repeat: a round is
#: billed per REQUEST, so a repeated ref still costs a round (no cross-round cache).
REFS = ("doc-live@r1", "doc-live@r2", "doc-revoked@r1", "doc-live@r1")


class _Cfg:
    """The runner's cfg surface, minimal and explicit (no argparse, no network)."""

    def __init__(self, **kw):
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
        self.manifest_dir = tempfile.gettempdir()
        self.fetch_rounds_per_turn = 3
        self.fetch_rounds_per_arm = 48
        self.turn_wall_cap = 0
        self.runaway_turns = 2
        self.budget_cap = 64
        self.budget_reserve = 0
        self.budget_glob = None
        self.request_allocation = "projection"
        for key, value in kw.items():
            setattr(self, key, value)


def _base_resp(n: int) -> dict:
    return {"content": "", "content_raw": "", "reasoning": "",
            "content_source": "none", "finish_reason": "stop", "truncated": False,
            "max_tokens": 256, "prompt_tokens": 10 + n, "raw_cached": None,
            "token_source": "offline", "completion_tokens": 5, "wall_ms": 40,
            "request_sha256": hashlib.sha256(("wire-body-%d" % n).encode()).hexdigest(),
            "request_identity_complete": True, "ttft_s": 0.04, "ttft_ms": 40,
            "latency_s": 0.08, "usage_missing": False, "tool_calls": None,
            "tool_calls_present": False, "first_token_kind": None}


def _answer_resp(text: str, n: int) -> dict:
    resp = _base_resp(n)
    resp.update({"content": text, "content_raw": text, "content_source": "content",
                 "finish_reason": "stop", "stop_reason": "stop"})
    return resp


def _tool_call_resp(calls, n: int) -> dict:
    """The dict ``client.send_chat`` returns for a streamed tool-call turn.

    ``calls`` is a list of ``(ref, call_id)``.  Built with the client's OWN
    ``structured_tool_calls``, so the record shape under test is the wire shape.
    """
    message = {"tool_calls": [
        {"index": i, "id": call_id, "type": "function",
         "function": {"name": "fetch", "arguments": json.dumps({"ref": ref})}}
        for i, (ref, call_id) in enumerate(calls)]}
    resp = _base_resp(n)
    resp.update({
        "content": "", "content_raw": "", "content_source": "none",
        "finish_reason": "tool_calls", "stop_reason": "tool_calls",
        "completion_tokens": 33, "first_token_kind": "tool_call",
        "tool_calls_present": True,
        "tool_calls": R.client.structured_tool_calls(message),
    })
    return resp


def _read_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class FetchMultiRoundTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, script, max_turns=1, per_turn=3, per_arm=48):
        """Run one offline ``bounded-context-fetch`` cell and return its rows.

        ``script`` is a list indexed by 1-based SEND number: an entry is a list of
        ``(ref, call_id)`` pairs the reply carries as structured tool calls, or ``None``
        for a plain answer.  Sends past the end of the script answer normally.  Nothing
        else is faked: the real ``run_cell``, the real ``arm_cd`` parser and the real row
        writer all run.

        ``rows_at_send[k]`` is the number of rows ON DISK when send ``k`` was issued --
        the observable that proves a paid request's row precedes the next send.
        """
        run_dir = tempfile.mkdtemp(prefix="fetchmulti-")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        cfg = _Cfg(max_turns=max_turns, manifest_path=manifest_path, manifest_dir=run_dir,
                   budget_glob=os.path.join(run_dir, "rows-*.jsonl"),
                   budget_cap=64, budget_reserve=0, request_allocation="projection",
                   fetch_rounds_per_turn=per_turn, fetch_rounds_per_arm=per_arm)
        fixture_obj = R.load_fixture(FIXTURE)
        calls = {"n": 0}
        rows_at_send = {}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            n = calls["n"]
            rows_at_send[n] = len(_read_rows(rows_path))
            spec = script[n - 1] if n - 1 < len(script) else None
            if spec:
                return _tool_call_resp(spec, n)
            return _answer_resp(FINAL_ANSWER, n)

        real_send = R.send_chat
        R.send_chat = fake_chat
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, ARM, 1, "fetchmulti-run-r1", rows_path)
        finally:
            R.send_chat = real_send
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "rows_at_send": rows_at_send,
                "stdout": out.getvalue(), "stderr": err.getvalue()}

    @staticmethod
    def _turn_row(rows, turn=1):
        hits = [r for r in rows if r.get("turn") == turn and r.get("kind") == "turn"]
        assert len(hits) == 1, [(r.get("turn"), r.get("kind")) for r in rows]
        return hits[0]

    @staticmethod
    def _followups(rows):
        """Rows that stand for a follow-up REQUEST (the last one is the turn row)."""
        return [r for r in rows if r.get("fetch_followup") is True]

    # -- (1) two calls on one turn are BOTH serviced, two rounds --------------
    def test_two_calls_on_one_turn_are_both_serviced(self):
        # The turn emits a call on its own reply and ANOTHER on the follow-up's reply.
        # Before U-SPCC-54 the second was dropped: one `_resp2` per turn, full stop.
        res = self._scenario(script=[
            [("doc-live@r1", "call_a1")],
            [("doc-live@r2", "call_a2")],
        ])
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        self.assertEqual(res["calls"], 3,
                         "the turn's own send + one follow-up per serviced call")
        row = self._turn_row(res["rows"])
        self.assertEqual(row.get("fetch_rounds_this_turn"), 2,
                         "two calls on one turn must spend two rounds, not one")
        self.assertEqual(row.get("fetch_rounds_used"), 2)
        self.assertEqual(len(self._followups(res["rows"])), 2,
                         f"two follow-up rows expected: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        self.assertEqual(row.get("tool_call_ids"), ["call_a1", "call_a2"],
                         "both calls' ids must be recorded on the turn row")
        self.assertEqual(row.get("answer_kind"), "TEXT",
                         f"the last follow-up's answer must be graded: {row.get('content')!r}")

    # -- (1b) several calls in ONE response still share ONE round -------------
    def test_calls_in_one_response_share_one_round(self):
        # Unchanged batching: `service_fetches` services a whole response in one round.
        res = self._scenario(script=[
            [("doc-live@r1", "call_b1"), ("doc-live@r2", "call_b2")],
        ])
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        self.assertEqual(res["calls"], 2, "one response, one follow-up")
        row = self._turn_row(res["rows"])
        self.assertEqual(row.get("fetch_rounds_this_turn"), 1)
        self.assertEqual(row.get("tool_call_ids"), ["call_b1", "call_b2"])

    # -- (2) four calls stop at the per-turn cap of three ---------------------
    def test_four_calls_stop_at_the_per_turn_cap(self):
        res = self._scenario(per_turn=3, script=[
            [("doc-live@r1", "call_c1")],
            [("doc-live@r2", "call_c2")],
            [("doc-revoked@r1", "call_c3")],
            [("doc-live@r1", "call_c4")],
        ])
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        self.assertEqual(res["calls"], 4,
                         "the turn's own send + exactly three follow-ups (the cap)")
        row = self._turn_row(res["rows"])
        self.assertEqual(row.get("fetch_rounds_this_turn"), 3,
                         "the per-turn cap is 3, so the fourth call is not serviced")
        self.assertEqual(row.get("fetch_rounds_cap_per_turn"), 3)
        self.assertEqual(len(self._followups(res["rows"])), 3)
        self.assertEqual(row.get("tool_call_ids"), ["call_c1", "call_c2", "call_c3"],
                         "the fourth call must not be serviced")

    # -- (3) the per-arm pool still stops the loop ----------------------------
    def test_per_arm_pool_exhaustion_stops_the_loop(self):
        res = self._scenario(per_turn=3, per_arm=1, script=[
            [("doc-live@r1", "call_d1")],
            [("doc-live@r2", "call_d2")],
            [("doc-revoked@r1", "call_d3")],
        ])
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        self.assertEqual(res["calls"], 2,
                         "a pool of one round buys exactly one follow-up")
        row = self._turn_row(res["rows"])
        self.assertEqual(row.get("fetch_rounds_this_turn"), 1)
        self.assertEqual(row.get("fetch_rounds_used"), 1)
        self.assertEqual(len(self._followups(res["rows"])), 1)

    # -- (4) one row per send, and each row precedes the next send ------------
    def test_one_row_per_send_and_rows_precede_the_next_send(self):
        res = self._scenario(script=[
            [("doc-live@r1", "call_e1")],
            [("doc-live@r2", "call_e2")],
            [("doc-revoked@r1", "call_e3")],
        ])
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        self.assertEqual(len(res["rows"]), res["calls"],
                         f"{res['calls']} paid send(s) must leave {res['calls']} row(s), "
                         f"got {[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        # Wire order: the turn's own send, then each follow-up in order.  Three rounds
        # means four sends, and the LAST follow-up's row is the turn row.
        self.assertEqual([r["kind"] for r in res["rows"]],
                         ["turn-initial", "tool-followup", "tool-followup", "turn"],
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        self.assertEqual([r["send_index"] for r in res["rows"]], [0, 1, 2, 3])
        # Every FOLLOW-UP's row is on disk before the next send.  Follow-up k is send
        # k+1, so its row must be there before send k+2 -- i.e. before send k the file
        # already holds the rows for sends 1..k-1.  (The turn's own row is written with
        # the first follow-up's row: neither is final until that reply is in, and the
        # LAST follow-up's row is the turn row, written after the last send.)
        for k, written in res["rows_at_send"].items():
            if k < 3:
                continue
            self.assertGreaterEqual(
                written, k - 1,
                f"send {k} went out with only {written} row(s) on disk: "
                f"{res['rows_at_send']}")
        # The specific guarantee, stated as counts: follow-up 1's row precedes send 3 and
        # follow-up 2's row precedes send 4.
        self.assertEqual(res["rows_at_send"][3], 2,
                         f"follow-up 1's row must precede send 3: {res['rows_at_send']}")
        self.assertEqual(res["rows_at_send"][4], 3,
                         f"follow-up 2's row must precede send 4: {res['rows_at_send']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
