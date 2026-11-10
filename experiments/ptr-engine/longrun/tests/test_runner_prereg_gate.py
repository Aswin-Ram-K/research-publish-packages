#!/usr/bin/env python3
"""Red->green proof for U-SPCC-37: the RUNNER enforces G3 before it spends anything.

``cell.eval_gate_prereg`` was implemented, tested and never called by
``run_longrun.py`` -- the file had zero references to ``eval_gate_prereg``,
``validate_g3`` or ``GATE_PREREG``.  The E1 cell of 2026-11-10 spent 100 requests
against PREREG-SPCC's 200-500 floor and nothing refused it.

Offline.  ZERO inference requests, no network, no git.  ``run_longrun.send_chat`` is
replaced by a fake that COUNTS sends, so "no request was sent" is a measured fact, not
an inference from the absence of an error.

Cases, per the unit contract:
  (a) E1 BELOW THE FLOOR -- TX-03 (N=100, 48 checkpoints) at reps=1 is n=100, outside
      PREREG-SPCC's [200, 500]: exit 12, 0 sends, 0 rows, and the refusal names the
      shortfall (n=100 against 200-500).
  (b) E1 AT THE FLOOR -- the same fixture at reps=2 is n=200: G3 allows it and the fake
      client receives its sends.
  (c) H1 BELOW n=60 -- 10 turns x 1 rep is n=10: refused the same way (exit 12, 0 sends,
      0 rows).
  (d) SMOKE IS NOT REFUSED BY G3 -- a declared smoke cell makes no PARM-1 claim, so no
      n threshold applies; the run proceeds and the fake client receives its sends.
  (e) RED->GREEN -- neuter the call site (the pre-change runner) and the below-floor E1
      cell PROCEEDS and SENDS; restore it and the same cell sends nothing.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_runner_prereg_gate.py -q
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

import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-03.v1.json")


def _resp(text: str) -> dict:
    return {"content": text, "content_raw": text, "reasoning": "",
            "content_source": "content", "finish_reason": "stop", "truncated": False,
            "max_tokens": 256, "prompt_tokens": 10, "raw_cached": None,
            "token_source": "offline", "completion_tokens": 5, "ttft_s": 0.1,
            "ttft_ms": 100, "latency_s": 0.2, "usage_missing": False}


def _read_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class RunnerPreregGateTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)
        self.tmp = tempfile.mkdtemp(prefix="prereggate-")

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _run(self, *, claim_mode, reps=1, max_turns=0, neuter_gate=False):
        """Drive ``main()`` with a fake transport that counts sends."""
        run_dir = tempfile.mkdtemp(prefix="run-", dir=self.tmp)
        corpus_dir = os.path.join(run_dir, "corpus")
        os.makedirs(corpus_dir)
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_dir = os.path.join(run_dir, "manifests")
        os.makedirs(manifest_dir)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            resp = _resp("ANSWER: 42")
            resp["request_sha256"] = hashlib.sha256(
                ("wire-body-%d" % calls["n"]).encode()).hexdigest()
            return resp

        argv = ["--fixture", FIXTURE, "--arms", "spcc", "--reps", str(reps),
                "--temperature", "0", "--seed", "42",
                "--model", "offline-model-was-never-called",
                "--base-url", "http://offline.invalid",
                "--claim-mode", claim_mode,
                "--budget-cap", "100000",
                "--budget-glob", os.path.join(corpus_dir, "rows-*.jsonl"),
                "--rows", rows_path,
                "--manifest-dir", manifest_dir,
                "--run-id", "prereggate-run"]
        if max_turns:
            argv += ["--max-turns", str(max_turns)]

        real_send = R.send_chat
        real_gate = R.enforce_prereg_gate
        R.send_chat = fake_chat
        if neuter_gate:
            # RED: the pre-change runner -- the call site does not exist, so the cell
            # walks straight past G3 and spends.
            R.enforce_prereg_gate = lambda _cfg, _fixture: 0
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.main(argv)
        finally:
            R.send_chat = real_send
            R.enforce_prereg_gate = real_gate
        return {"rc": rc, "calls": calls["n"], "rows": _read_rows(rows_path),
                "stdout": out.getvalue(), "stderr": err.getvalue()}

    # -- (a) E1 below the 200-request floor ------------------------------------
    def test_a_e1_below_floor_is_refused_before_any_send(self):
        res = self._run(claim_mode="E1", reps=1)
        self.assertEqual(res["rc"], 12, res["stderr"][-1200:])
        self.assertEqual(res["calls"], 0, "a G3 refusal must send NO request")
        self.assertEqual(res["rows"], [], "a G3 refusal must write NO row")
        for token in ("G3", "n=100", "200", "500", "PREREG REFUSED (exit 12)"):
            self.assertIn(token, res["stderr"], f"missing refusal token {token!r}")
        self.assertIn("no row was written and no request was sent", res["stderr"])
        print(f"  GREEN(a): exit={res['rc']} sends={res['calls']} rows={len(res['rows'])}")

    # -- (b) E1 at the floor proceeds ------------------------------------------
    def test_b_e1_at_floor_proceeds(self):
        res = self._run(claim_mode="E1", reps=2)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        self.assertGreater(res["calls"], 0, "an admissible cell must reach the wire")
        self.assertEqual(res["calls"], 200, "2 reps x 100 turns = the declared n")
        self.assertNotIn("PREREG REFUSED", res["stderr"])
        print(f"  GREEN(b): exit={res['rc']} sends={res['calls']} rows={len(res['rows'])}")

    # -- (c) H1 below n = 60 ---------------------------------------------------
    def test_c_h1_below_60_is_refused(self):
        res = self._run(claim_mode="H1", reps=1, max_turns=10)
        self.assertEqual(res["rc"], 12, res["stderr"][-1200:])
        self.assertEqual(res["calls"], 0, "a G3 refusal must send NO request")
        self.assertEqual(res["rows"], [], "a G3 refusal must write NO row")
        for token in ("G3", "n=10", "60", "PREREG REFUSED (exit 12)"):
            self.assertIn(token, res["stderr"], f"missing refusal token {token!r}")
        print(f"  GREEN(c): exit={res['rc']} sends={res['calls']} rows={len(res['rows'])}")

    # -- (d) smoke is allowed and non-comparable -------------------------------
    def test_d_smoke_is_not_refused_by_g3(self):
        res = self._run(claim_mode="smoke", reps=1, max_turns=3)
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        self.assertNotIn("PREREG REFUSED", res["stderr"])
        self.assertEqual(res["calls"], 3, "3 turns x 1 rep reached the wire")
        self.assertTrue(res["rows"], "a smoke cell writes its rows")
        for row in res["rows"]:
            self.assertEqual(row.get("claim"), "none")
            self.assertFalse(row.get("comparison_eligible"))
        print(f"  GREEN(d): exit={res['rc']} sends={res['calls']} rows={len(res['rows'])}")

    # -- (e) red->green --------------------------------------------------------
    def test_e_red_green(self):
        red = self._run(claim_mode="E1", reps=1, neuter_gate=True)
        self.assertEqual(red["rc"], 0, "RED: the pre-change runner must NOT refuse")
        self.assertGreater(red["calls"], 0, "RED: the below-floor cell must reach the wire")
        self.assertTrue(red["rows"], "RED: the below-floor cell must write rows")
        self.assertNotIn("PREREG REFUSED", red["stderr"])
        green = self._run(claim_mode="E1", reps=1)
        self.assertEqual(green["rc"], 12)
        self.assertEqual(green["calls"], 0)
        self.assertEqual(green["rows"], [])
        print(f"  RED: exit={red['rc']} sends={red['calls']} rows={len(red['rows'])} | "
              f"GREEN: exit={green['rc']} sends={green['calls']} rows={len(green['rows'])}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
