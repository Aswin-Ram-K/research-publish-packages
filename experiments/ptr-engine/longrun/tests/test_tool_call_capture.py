#!/usr/bin/env python3
"""Red->green proof for TOOL-CALL-CAPTURE on the ``bounded-context-fetch`` arm (U-SPCC-49).

THE DEFECT.  In the corrected E1 cell (``08a7908``, 318 requests, delta 0) ten of the
fetch arm's 48 checkpoints ended on ``finish_reason=tool_calls`` with ``content ''``,
``tool_calls []``, ``tool_call_ids null`` and NO follow-up request.  The server signalled
a tool call; the harness captured none, so the checkpoint scored ``unparsed``.  That is
the arm's largest single loss -- ten checkpoints, more than its four wrong answers.

THE CAUSE.  ``run_cell``'s ``arm == arm_cd.ARM_D`` block reads the reply through
``arm_cd.parse_fetch_calls_from_response``, which delegates to
``ptr_engine.fetch_tool.parse_fetch_calls``.  That parser keeps ONLY calls whose
``function.name`` is ``"fetch"`` (``fetch_tool.py:96-99``: ``if name != "fetch": ...
continue``).  The schema actually on the wire is ``read_file`` (``TOOL_NAMES``,
``tools_mode="on:read_file"``), so a ``read_file`` call is filtered out, ``_calls`` is
empty, no follow-up is bought, and the empty content is parsed as ``no_answer_line``.
The call is dropped SILENTLY: nothing on the row says a call was ever signalled.

THE FIX (``run_longrun.py`` only -- ``arm_cd.py`` is out of scope).  Every structured
call the fetch parser did not consume is preserved on the row and labelled
``protocol_violation="tool_call_unserviced"``.  The answer contract, the scoring and the
fetch budget are untouched: the call is RECORDED, not serviced, so no request is bought
and no round is spent.

SUPERSEDED IN PART BY U-SPCC-52.  ``read_file`` is now a DECLARED name the parser
services (``tests/test_fetch_call_names.py``), so the two capture tests below exercise
the guarantee with an UNDECLARED name (``write_file``).  The guarantee itself -- nothing
the server signalled is dropped silently -- is unchanged.

Offline.  ZERO inference requests, no network, no git.  The transport is a fake that
returns the exact dict ``client.send_chat`` returns for a tool-call turn (built with the
client's own ``structured_tool_calls``), so the shape under test is the wire shape.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_tool_call_capture.py -q
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
CP_TURN = 12
FINAL_ANSWER = "ANSWER: TEXT offline"

#: The exact argument string a ``read_file`` call carries on the wire.
READ_FILE_ARGS = '{"path": "doc-live", "start_line": 1, "end_line": 1}'
READ_FILE_ID = "call_c1985245fd5c457d83111c74"
FETCH_ARGS = '{"ref": "doc-live@r1"}'
FETCH_ID = "call_8c0b282c75e64c6f9bc4c12e"
#: A name the run never declared.  U-SPCC-52 made the DECLARED names (`read_file`,
#: `fetch`) serviced, so the capture guarantee is exercised with this one.
UNDECLARED_NAME = "write_file"


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
        self.fetch_rounds_per_turn = 0
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


def _tool_call_resp(name: str, arguments: str, call_id: str, n: int) -> dict:
    """The dict ``client.send_chat`` returns for a streamed tool-call turn.

    Built with the client's OWN ``structured_tool_calls``, so the record shape under test
    is the shape the real client produces from ``delta.tool_calls`` fragments -- not a
    hand-written approximation of it.
    """
    message = {"tool_calls": [{"index": 0, "id": call_id, "type": "function",
                               "function": {"name": name, "arguments": arguments}}]}
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


class ToolCallCaptureTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, max_turns=CP_TURN, tool_call_on=None, name="read_file",
                  arguments=READ_FILE_ARGS, call_id=READ_FILE_ID):
        """Run one offline ``bounded-context-fetch`` cell and return its rows.

        ``tool_call_on`` names the 1-based send whose reply carries a structured tool
        call; every other send answers normally.  Nothing else is faked: the real
        ``run_cell``, the real ``arm_cd`` parser and the real row writer all run.
        """
        run_dir = tempfile.mkdtemp(prefix="toolcall-")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        cfg = _Cfg(max_turns=max_turns, manifest_path=manifest_path, manifest_dir=run_dir,
                   budget_glob=os.path.join(run_dir, "rows-*.jsonl"),
                   budget_cap=64, budget_reserve=0, request_allocation="projection")
        fixture_obj = R.load_fixture(FIXTURE)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            n = calls["n"]
            if tool_call_on is not None and n == tool_call_on:
                return _tool_call_resp(name, arguments, call_id, n)
            return _answer_resp(FINAL_ANSWER, n)

        real_send = R.send_chat
        R.send_chat = fake_chat
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, ARM, 1, "toolcall-run-r1", rows_path)
        finally:
            R.send_chat = real_send
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "stdout": out.getvalue(), "stderr": err.getvalue()}

    @staticmethod
    def _turn_row(rows, turn):
        hits = [r for r in rows if r.get("turn") == turn and r.get("kind") == "turn"]
        assert len(hits) == 1, [(r.get("turn"), r.get("kind")) for r in rows]
        return hits[0]

    # -- (1) an UNDECLARED call on a checkpoint turn is RECORDED, not dropped --
    # FETCH-NAME-DRIFT (U-SPCC-52) superseded the original subject of this test: a
    # `read_file` call is now SERVICED (see tests/test_fetch_call_names.py), so the
    # capture guarantee is exercised with a name the run never declared.  The guarantee
    # itself is unchanged: nothing the server signalled is dropped silently.
    def test_undeclared_call_on_checkpoint_turn_is_recorded_not_dropped(self):
        res = self._scenario(tool_call_on=CP_TURN, name=UNDECLARED_NAME,
                             arguments=READ_FILE_ARGS, call_id=READ_FILE_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], CP_TURN)

        # The server signalled a call; the row must say so.
        self.assertEqual(row.get("protocol_violation"), "tool_call_unserviced",
                         "a tool call the server signalled was dropped silently: "
                         f"protocol_violation={row.get('protocol_violation')!r} "
                         f"tool_calls={row.get('tool_calls')!r} "
                         f"answer_parse_error={row.get('answer_parse_error')!r}")
        # ... and the call itself must survive on the row, verbatim.
        preserved = row.get("tool_calls") or []
        self.assertEqual(len(preserved), 1, f"the call was not preserved: {preserved!r}")
        self.assertEqual(preserved[0].get("name"), UNDECLARED_NAME)
        self.assertEqual(preserved[0].get("id"), READ_FILE_ID)
        self.assertEqual(preserved[0].get("arguments"), READ_FILE_ARGS)
        self.assertEqual(row.get("unserviced_tool_call_ids"), [READ_FILE_ID])

        # The ANSWER CONTRACT is unchanged: no answer line was emitted, so the row is
        # still an unparsed answer -- it is just no longer SILENTLY unparsed.
        self.assertIsNone(row.get("answer_kind"))
        self.assertEqual(row.get("answer_parse_error"), "no_answer_line")

        # The FETCH BUDGET is unchanged: recording a call buys no request.
        self.assertEqual(res["calls"], CP_TURN,
                         "recording an unserviced call must not buy a follow-up request")
        self.assertFalse([r for r in res["rows"] if r.get("fetch_followup")],
                         "no follow-up row may exist for a recorded-only call")

    # -- (2) an undeclared call on a WORK turn is recorded the same way --------
    def test_undeclared_call_on_work_turn_is_recorded(self):
        res = self._scenario(max_turns=2, tool_call_on=1, name=UNDECLARED_NAME,
                             arguments=READ_FILE_ARGS, call_id=READ_FILE_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], 1)
        self.assertEqual(row.get("protocol_violation"), "tool_call_unserviced",
                         f"work-turn drop: tool_calls={row.get('tool_calls')!r}")
        self.assertEqual((row.get("tool_calls") or [{}])[0].get("name"), UNDECLARED_NAME)
        self.assertEqual(res["calls"], 2, "no follow-up may be bought for a recorded call")

    # -- (3) the working path is untouched: a fetch call is still SERVICED -----
    def test_fetch_call_on_checkpoint_turn_is_still_serviced(self):
        res = self._scenario(tool_call_on=CP_TURN, name="fetch",
                             arguments=FETCH_ARGS, call_id=FETCH_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], CP_TURN)
        self.assertIsNone(row.get("protocol_violation"),
                          "a serviced fetch call is not a protocol violation")
        self.assertEqual(row.get("answer_kind"), "TEXT",
                         f"the follow-up's answer must be graded: {row.get('content')!r}")
        self.assertEqual(res["calls"], CP_TURN + 1,
                         "a fetch call still buys exactly one follow-up request")
        self.assertEqual(row.get("tool_call_ids"), [FETCH_ID])

    # -- (4) the helper: only calls the parser did NOT consume are reported ----
    def test_unserviced_structured_calls_helper(self):
        raw = R.client.structured_tool_calls({"tool_calls": [
            {"index": 0, "id": "a", "type": "function",
             "function": {"name": "fetch", "arguments": FETCH_ARGS}},
            {"index": 1, "id": "b", "type": "function",
             "function": {"name": "read_file", "arguments": READ_FILE_ARGS}},
        ]})
        resp = {"tool_calls": raw}
        # Nothing consumed -> every call is unserviced.
        self.assertEqual([c["id"] for c in R.unserviced_structured_calls(resp, [])],
                         ["a", "b"])
        # The fetch call consumed -> only the read_file call is unserviced.
        served = [{"ref": "doc-live@r1", "tool_call_id": "a"}]
        self.assertEqual([c["id"] for c in R.unserviced_structured_calls(resp, served)],
                         ["b"])
        # Everything consumed -> nothing reported.
        served = [{"ref": "doc-live@r1", "tool_call_id": "a"},
                  {"path": "doc-live", "tool_call_id": "b"}]
        self.assertEqual(R.unserviced_structured_calls(resp, served), [])
        # No structured call at all -> nothing reported (text calls are not this path).
        self.assertEqual(R.unserviced_structured_calls({"tool_calls": []}, []), [])
        self.assertEqual(R.unserviced_structured_calls({}, []), [])


if __name__ == "__main__":
    unittest.main()
