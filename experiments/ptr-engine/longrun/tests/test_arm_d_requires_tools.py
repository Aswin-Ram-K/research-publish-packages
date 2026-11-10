#!/usr/bin/env python3
"""Red->green proof for ARM-REQUIRES-TOOLS (U-SPCC-46).

The ``bounded-context-fetch`` arm's treatment IS the fetch channel: its only difference
from ``masking-no-fetch`` is that a masked body can be bought back with a ``fetch`` call.
E1 launched it with ``--tools`` absent (``tools_mode=off``), so the fetch service at the
``arm == arm_cd.ARM_D`` block never ran: 43 of 48 checkpoint turns stranded as interim
``fetch_followup`` rows with ``protocol_violation=answer_wrapped_tool_call`` and
``send_index 0`` on all 100 rows.  The cell exited 0 and reported 0 failed turns, so a
degenerate arm looked like a real result.

The runner now refuses that launch BEFORE the first request: a named refusal, exit 2,
no row written, no socket opened.  ``masking-no-fetch`` (defined by having no tool
channel) and ``spcc`` (never fetches) are unaffected.

Offline.  ZERO inference requests, no network, no git.  ``send_chat`` is a counting fake
and ``socket.socket`` is denied.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_arm_d_requires_tools.py -q
"""

from __future__ import annotations

import io
import json
import os
import socket
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import arm_cd  # noqa: E402
import run_longrun as R  # noqa: E402

# PT-01 carries ``fetch_budget_tokens``, which ``arm_cd.resolve_fetch_budget`` requires
# before the D arm can serve a single fetch.
PT_FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
# LR-01 is the fixture the spcc arm test uses; spcc never fetches.
SPCC_FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
FINAL_ANSWER = "ANSWER: TEXT offline"
# The malformed-launch code the runner already uses for a bad flag value.  Spelled as a
# literal so the RED run fails on BEHAVIOUR (the arm proceeds and sends) rather than on a
# missing attribute; ``test_refusal_code_is_the_launch_code`` pins the constant itself.
REFUSAL_CODE = 2


class _Cfg:
    """The runner's cfg surface, minimal and explicit (no argparse, no network)."""

    def __init__(self, tools="read_file", max_turns=2):
        self.tools = tools
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = max_turns
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = None
        self.fetch_rounds_per_turn = 0
        self.fetch_rounds_per_arm = 48
        self.turn_wall_cap = 0
        self.generation = "gen-7"
        # BUDGET: the cap gate reads a machine-global ledger by default.  This test
        # asserts WIRING, so it declares its own cap and its own row-glob (the scratch
        # dir): a refusal about spend must never decide this test.
        self.budget_cap = 10 ** 9
        self.budget_reserve = 0
        self.request_allocation = "projection"
        self.budget_glob = None


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


def _no_network():
    def _denied(*_a, **_k):
        raise AssertionError("must never open a socket")
    return _denied


def _run_cell(arm, tools, fixture_path, max_turns=2):
    """Run one cell offline; return (rc, sends, rows, stderr_text)."""
    tmp = tempfile.mkdtemp(prefix="armd-tools-")
    rows_path = os.path.join(tmp, "rows.jsonl")
    fixture = R.load_fixture(fixture_path)
    cfg = _Cfg(tools=tools, max_turns=max_turns)
    cfg.manifest_dir = tmp
    cfg.manifest_path = os.path.join(tmp, "manifest.json")
    cfg.budget_glob = os.path.join(tmp, "rows-*.jsonl")
    state = {"n": 0}

    def fake_send(_cfg, _messages):
        state["n"] += 1
        return _resp(FINAL_ANSWER, state["n"])

    run_id = "offline-armd-tools-%s-r1" % arm
    real_send, real_socket = R.send_chat, socket.socket
    R.send_chat = fake_send
    socket.socket = _no_network()
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = R.run_cell(cfg, fixture, arm, 1, run_id, rows_path)
    finally:
        R.send_chat = real_send
        socket.socket = real_socket
    rows = []
    if os.path.exists(rows_path):
        with open(rows_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rc, state["n"], rows, err.getvalue()


class TestFetchArmRequiresTools(unittest.TestCase):
    def test_refusal_code_is_the_launch_code(self):
        self.assertEqual(R.EXIT_ARM_REQUIRES_TOOLS, REFUSAL_CODE)

    def test_d_arm_with_tools_off_is_refused_before_any_send(self):
        rc, sends, rows, err = _run_cell(arm_cd.ARM_D, "", PT_FIXTURE)
        self.assertEqual(sends, 0, "a refused launch must send no request, sent %d" % sends)
        self.assertEqual(rows, [], "a refused launch must write no row, wrote %d" % len(rows))
        self.assertEqual(rc, REFUSAL_CODE,
                         "tools-off fetch arm must refuse, got rc=%r\n%s" % (rc, err))
        self.assertIn("ARM REFUSED", err)
        self.assertIn("--tools", err, "the refusal must name the missing flag")
        self.assertIn(arm_cd.ARM_D, err)

    def test_d_arm_with_tools_on_proceeds(self):
        rc, sends, rows, err = _run_cell(arm_cd.ARM_D, "read_file", PT_FIXTURE)
        self.assertEqual(rc, 0, "tools-on fetch arm must run, got rc=%r\n%s" % (rc, err))
        self.assertGreater(sends, 0, "the arm must actually send")
        self.assertGreater(len(rows), 0, "the arm must write rows")
        self.assertEqual({r["arm"] for r in rows}, {arm_cd.ARM_D})
        self.assertNotIn("ARM REFUSED", err)

    def test_c_arm_with_tools_off_is_unaffected(self):
        rc, sends, rows, err = _run_cell(arm_cd.ARM_C, "", PT_FIXTURE)
        self.assertEqual(rc, 0, "masking-no-fetch must run with tools off, got rc=%r\n%s"
                         % (rc, err))
        self.assertGreater(sends, 0)
        self.assertGreater(len(rows), 0)
        self.assertNotIn("ARM REFUSED", err)

    def test_spcc_arm_with_tools_off_is_unaffected(self):
        rc, sends, rows, err = _run_cell("spcc", "", SPCC_FIXTURE, max_turns=2)
        self.assertEqual(rc, 0, "spcc must run with tools off, got rc=%r\n%s" % (rc, err))
        self.assertGreater(sends, 0)
        self.assertGreater(len(rows), 0)
        self.assertNotIn("ARM REFUSED", err)


class TestMainRefusesBeforeAnyCell(unittest.TestCase):
    def test_main_refuses_tools_off_fetch_arm(self):
        tmp = tempfile.mkdtemp(prefix="armd-main-")
        rows_path = os.path.join(tmp, "rows.jsonl")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            rc = R.main([
                "--temperature", "0",
                "--fixture", PT_FIXTURE,
                "--arms", arm_cd.ARM_D,
                "--rows", rows_path,
                "--claim-mode", "smoke",
                "--budget-cap", "1000000",
                "--budget-glob", os.path.join(tmp, "rows-*.jsonl"),
                "--manifest-dir", tmp,
            ])
        text = err.getvalue()
        self.assertEqual(rc, REFUSAL_CODE, "main must refuse, got rc=%r\n%s"
                         % (rc, text))
        self.assertIn("--tools", text)
        self.assertFalse(os.path.exists(rows_path), "no row file may be created")

    def test_main_refuses_before_an_earlier_arm_spends(self):
        """A multi-arm launch must not spend the first arm then discover the degenerate one."""
        tmp = tempfile.mkdtemp(prefix="armd-main-multi-")
        rows_path = os.path.join(tmp, "rows.jsonl")
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            rc = R.main([
                "--temperature", "0",
                "--fixture", PT_FIXTURE,
                "--arms", "spcc," + arm_cd.ARM_D,
                "--rows", rows_path,
                "--claim-mode", "smoke",
                "--budget-cap", "1000000",
                "--budget-glob", os.path.join(tmp, "rows-*.jsonl"),
                "--manifest-dir", tmp,
            ])
        self.assertEqual(rc, REFUSAL_CODE, err.getvalue())
        self.assertFalse(os.path.exists(rows_path),
                         "the refusal must land before the first cell writes a row")


if __name__ == "__main__":
    unittest.main(verbosity=2)
