#!/usr/bin/env python3
"""Red->green proof for FETCH-NAME-DRIFT on the ``bounded-context-fetch`` arm (U-SPCC-52).

THE DEFECT.  ``run_longrun.run_cell`` reads the fetch arm's reply through
``arm_cd.parse_fetch_calls_from_response``, which delegates to
``ptr_engine.fetch_tool.parse_fetch_calls``.  That parser kept ONLY calls whose
``function.name`` was ``"fetch"`` (``fetch_tool.py:96-99``: ``if name != "fetch": ...
continue``).  The schema actually on the wire is ``read_file`` (``TOOL_NAMES``,
``tools_mode="on:read_file"``), so a ``read_file`` call was filtered out, ``_calls`` came
back empty, no follow-up was bought, the empty content parsed as ``no_answer_line``, and
the checkpoint scored ``unparsed``.  Measured on ``measure/rows-e1-tools-2026-11-10.jsonl``:
ten checkpoints stranded at turns 9, 13, 25, 51, 56, 58, 60, 67, 74, 76 -- every one of
them with ``first_token_kind=tool_call``, i.e. the server HAD signalled the call and the
client HAD assembled it.  The loss was downstream of the client.

``U-SPCC-49`` (``4c6c8a0``) preserved the dropped call on the row and labelled it
``protocol_violation="tool_call_unserviced"``.  That is a diagnostic, not a fix: the ten
still scored ``unparsed``.

THE FIX.  ``parse_fetch_calls`` takes the tool names the run DECLARED and services any
call whose name is in that set; ``run_longrun.fetch_call_tool_names`` supplies the set
(``--tools`` plus ``fetch``, which the ARM_D prompt still teaches).  A ``read_file`` call
is serviced exactly as a ``fetch`` call is: same ``ref``/``range`` extraction, same
``tool_call_id`` requirement, same budget accounting.  An UNDECLARED name is still
rejected -- and stays visible on the row through ``unserviced_structured_calls``.

Offline.  ZERO inference requests, no network, no git.  The transport is a fake that
returns the exact dict ``client.send_chat`` returns for a tool-call turn (built with the
client's own ``structured_tool_calls``), so the shape under test is the wire shape.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_fetch_call_names.py -q
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
from ptr_engine.fetch_tool import parse_fetch_calls  # noqa: E402

# PT-01 carries ``fetch_budget_tokens`` (required by ``arm_cd.resolve_fetch_budget``)
# and declares its checkpoints at turns 12/24/28/32.
FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
ARM = arm_cd.ARM_D
CP_TURN = 12
FINAL_ANSWER = "ANSWER: TEXT offline"

#: A ``read_file`` call as the wire schema shapes it: ``path``/``start_line``/``end_line``.
#: ``path`` carries the ref the ARM_D prompt taught (``doc-<name>@r<rev>``), which is the
#: only ref-bearing field the schema gives the model.
READ_FILE_ARGS = '{"path": "doc-live@r1", "start_line": 1, "end_line": 1}'
READ_FILE_ID = "call_c1985245fd5c457d83111c74"
FETCH_ARGS = '{"ref": "doc-live@r1"}'
FETCH_ID = "call_8c0b282c75e64c6f9bc4c12e"
UNDECLARED_ARGS = '{"path": "doc-live@r1", "start_line": 1, "end_line": 1}'
UNDECLARED_ID = "call_5f1d0a7b93e24c8a9d3e6b21"


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
    is the shape the real client produces from ``delta.tool_calls`` fragments.
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


class FetchCallNamesTest(unittest.TestCase):
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
        run_dir = tempfile.mkdtemp(prefix="fetchname-")
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
                rc = R.run_cell(cfg, fixture_obj, ARM, 1, "fetchname-run-r1", rows_path)
        finally:
            R.send_chat = real_send
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "stdout": out.getvalue(), "stderr": err.getvalue()}

    @staticmethod
    def _turn_row(rows, turn):
        hits = [r for r in rows if r.get("turn") == turn and r.get("kind") == "turn"]
        assert len(hits) == 1, [(r.get("turn"), r.get("kind")) for r in rows]
        return hits[0]

    @staticmethod
    def _followups(rows):
        return [r for r in rows
                if r.get("kind") == "tool-followup" or r.get("fetch_followup") is True]

    # -- (0) the parser itself: the declared set decides what is accepted ------
    def test_parser_accepts_the_declared_set(self):
        resp = {"tool_calls": R.client.structured_tool_calls({"tool_calls": [
            {"index": 0, "id": READ_FILE_ID, "type": "function",
             "function": {"name": "read_file", "arguments": READ_FILE_ARGS}},
            {"index": 1, "id": FETCH_ID, "type": "function",
             "function": {"name": "fetch", "arguments": FETCH_ARGS}},
        ]})}

        # No set supplied -> the default set services BOTH names.
        both = parse_fetch_calls(resp)
        self.assertEqual([c["tool_call_id"] for c in both], [READ_FILE_ID, FETCH_ID])
        self.assertEqual([c["ref"] for c in both], ["doc-live@r1", "doc-live@r1"])

        # A run that declared only `read_file` still services `fetch` (the prompt
        # teaches it) but rejects anything outside the set.
        declared = R.fetch_call_tool_names(_Cfg(tools="read_file"))
        self.assertEqual(declared, ("read_file", "fetch"))
        self.assertEqual([c["tool_call_id"] for c in parse_fetch_calls(resp, declared)],
                         [READ_FILE_ID, FETCH_ID])

        # A set that excludes `read_file` rejects it -- visibly, by returning nothing.
        self.assertEqual(parse_fetch_calls(resp, tool_names=("fetch",)),
                         [{"ref": "doc-live@r1", "range": None,
                           "tool_call_id": FETCH_ID, "id": FETCH_ID}])

    # -- (1) a read_file call is SERVICED: follow-up bought, round spent -------
    def test_read_file_call_is_serviced(self):
        res = self._scenario(tool_call_on=CP_TURN, name="read_file",
                             arguments=READ_FILE_ARGS, call_id=READ_FILE_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], CP_TURN)

        # The call was consumed, so it is NOT a protocol violation any more.
        self.assertIsNone(row.get("protocol_violation"),
                          "a declared tool name must not be labelled unserviced: "
                          f"protocol_violation={row.get('protocol_violation')!r} "
                          f"tool_calls={row.get('tool_calls')!r}")
        self.assertIsNone(row.get("unserviced_tool_call_ids"))

        # A follow-up WAS bought.
        self.assertEqual(res["calls"], CP_TURN + 1,
                         "a read_file call must buy exactly one follow-up request")
        followups = self._followups(res["rows"])
        self.assertEqual(len(followups), 1, f"no follow-up row: {res['rows']!r}")

        # The tool result reached the model and the answer was graded.
        self.assertEqual(row.get("tool_call_ids"), [READ_FILE_ID])
        self.assertEqual(row.get("answer_kind"), "TEXT",
                         f"the follow-up's answer must be graded: {row.get('content')!r}")

    # -- (1b) servicing a read_file call SPENDS a round ------------------------
    def test_read_file_call_spends_a_round(self):
        # A WORK turn, not a checkpoint turn: the cumulative round counter is stamped on
        # the turn row only for a non-answer turn (``run_longrun.py:4000``), so this is
        # the row that can prove the round was billed.
        res = self._scenario(max_turns=2, tool_call_on=1, name="read_file",
                             arguments=READ_FILE_ARGS, call_id=READ_FILE_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], 1)
        self.assertIsNone(row.get("protocol_violation"))
        self.assertEqual(res["calls"], 3, "one follow-up request for the read_file call")
        self.assertEqual(row.get("fetch_rounds_used"), 1,
                         "servicing a read_file call must spend one fetch round")
        self.assertEqual(row.get("retrieval_outcomes"), ["OK"],
                         "the read_file call's ref must resolve in the pointer table")

    # -- (2) a fetch call is STILL serviced, unchanged -------------------------
    def test_fetch_call_is_still_serviced(self):
        res = self._scenario(tool_call_on=CP_TURN, name="fetch",
                             arguments=FETCH_ARGS, call_id=FETCH_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], CP_TURN)
        self.assertIsNone(row.get("protocol_violation"))
        self.assertEqual(res["calls"], CP_TURN + 1,
                         "a fetch call still buys exactly one follow-up request")
        self.assertEqual(len(self._followups(res["rows"])), 1)
        self.assertEqual(row.get("tool_call_ids"), [FETCH_ID])
        self.assertEqual(row.get("answer_kind"), "TEXT")

    # -- (3) an UNDECLARED name is rejected, and the rejection is VISIBLE ------
    def test_undeclared_name_is_rejected_and_visible(self):
        res = self._scenario(tool_call_on=CP_TURN, name="write_file",
                             arguments=UNDECLARED_ARGS, call_id=UNDECLARED_ID)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        row = self._turn_row(res["rows"], CP_TURN)

        # Rejected: no follow-up, no round.
        self.assertEqual(res["calls"], CP_TURN,
                         "an undeclared tool name must not buy a follow-up request")
        self.assertEqual(self._followups(res["rows"]), [])

        # ... but not silent: the call survives on the row, labelled.
        self.assertEqual(row.get("protocol_violation"), "tool_call_unserviced",
                         f"an undeclared call was dropped silently: {row!r}")
        preserved = row.get("tool_calls") or []
        self.assertEqual(len(preserved), 1, f"the call was not preserved: {preserved!r}")
        self.assertEqual(preserved[0].get("name"), "write_file")
        self.assertEqual(preserved[0].get("id"), UNDECLARED_ID)
        self.assertEqual(row.get("unserviced_tool_call_ids"), [UNDECLARED_ID])

    # -- (4) the label from 4c6c8a0 no longer fires for a DECLARED name --------
    def test_declared_name_does_not_raise_unserviced_label(self):
        for name, arguments, call_id in (("read_file", READ_FILE_ARGS, READ_FILE_ID),
                                         ("fetch", FETCH_ARGS, FETCH_ID)):
            with self.subTest(name=name):
                res = self._scenario(max_turns=2, tool_call_on=1, name=name,
                                     arguments=arguments, call_id=call_id)
                self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
                row = self._turn_row(res["rows"], 1)
                self.assertIsNone(row.get("protocol_violation"),
                                  f"{name} is declared, so it must be serviced, not "
                                  f"labelled: {row.get('protocol_violation')!r}")
                self.assertEqual(res["calls"], 3,
                                 f"{name} on a work turn must buy one follow-up")


if __name__ == "__main__":
    unittest.main()
