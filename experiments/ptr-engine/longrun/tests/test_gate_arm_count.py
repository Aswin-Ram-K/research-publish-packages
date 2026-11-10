#!/usr/bin/env python3
"""Red->green proof for U-SPCC-40: G3's ``n`` carries the arm term.

THE DEFECT.  ``cell.validate_g3`` computed ``n = turns x reps`` with NO arm term
(``cell.py:1259``) and compared it to PREREG-SPCC's ``request_ceiling`` of 200-500,
which is denominated in REQUESTS.  G1 already did it correctly
(``cell.py:1130``: ``turns_total = turns x arms x reps``) and the runner prices per arm
(``run_longrun.py:3105``) and sums into ``would_send_total`` (``:3113``).  Measured
consequence: a three-arm, two-rep, 100-turn cell was ADMITTED at ``n = 200`` while
sending 600 -- 100 above the preregistration's own ceiling -- and the only three-arm
shape that fits the ceiling (one rep, 300 requests) was REFUSED for being under the
floor at ``n = 100``.  E1 as preregistered was unsatisfiable.

THE FIX, in two parts, because the baseline is not the send count:

  (1) ``n = turns x arms x reps`` is the BASELINE.  It is a floor test and a first
      ceiling test: a baseline below 200 cannot support the claim whatever it fetches,
      and a baseline above 500 is already over before a single follow-up.
  (2) The ceiling itself is enforced on ACTUAL sends by the runner's per-request brake
      (``RequestCapGate.acquire``), because fetch follow-ups are real requests the
      baseline cannot see (``run_longrun.py:500-501``).  A fetch-heavy cell admitted at
      a baseline of 300 is stopped at 500 real requests, not admitted on a prediction.

Offline.  ZERO inference requests, no network, no git.  ``run_longrun.send_chat`` is a
fake that COUNTS sends, so "the brake stopped it" is a measured fact.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_gate_arm_count.py -q
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
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)

import cell          # noqa: E402
import run_longrun as R  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-03.v1.json")
TOOL_CALL_TURN = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                  '"start_line": 1, "end_line": 30}</tool_call>'
                  '<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                  '"start_line": 31, "end_line": 60}</tool_call>')


def _args(**kw):
    """G3's operand surface.  ``arms`` is absent unless a case supplies it, so the
    pre-existing single-arm callers are exercised exactly as they were."""
    base = dict(hypothesis="E1", turns=100, reps=1)
    base.update(kw)
    return SimpleNamespace(**base)


def _gate(**kw):
    cell._CLAIM_CACHE.clear()
    return cell.eval_gate_prereg(_args(**kw), R.load_fixture(FIXTURE))


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


class GateArmCountTest(unittest.TestCase):
    """The four shapes, the H1 path, the adapter, and the brake."""

    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)
        self.tmp = tempfile.mkdtemp(prefix="armcount-")

    def tearDown(self):
        os.chdir(self._cwd)

    # -- (1) three arms x one rep x 100 turns -> n = 300, ADMITTED ---------------
    def test_three_arms_one_rep_is_admitted_at_300(self):
        verdict = _gate(hypothesis="E1", turns=100, reps=1, arms=3)
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual(verdict["n"], 300, verdict)
        self.assertEqual(verdict["arms"], 3, verdict)
        self.assertEqual(verdict["thresholds"]["request_ceiling"], [200, 500], verdict)
        # ... and the runner would send exactly that many: 3 arms x 100 turns.
        cfg = R.build_parser().parse_args(
            ["--fixture", FIXTURE, "--arms", "spcc,pointer-stable,transcript-grow",
             "--reps", "1", "--temperature", "0", "--claim-mode", "E1"])
        fixture = R.load_fixture(FIXTURE)
        gate_args = R.prereg_gate_args(cfg, fixture)
        self.assertEqual(gate_args.arms, 3, "the adapter must supply the real arm count")
        self.assertEqual(gate_args.turns, 100)
        would_send = sum(R.projected_requests(cfg, fixture, arm)
                         for arm in ("spcc", "pointer-stable", "transcript-grow"))
        self.assertEqual(would_send, 300, "3 arms x 100 turns = the admitted baseline")
        print(f"  GREEN(1): n={verdict['n']} admitted, runner would send {would_send}")

    # -- (2) three arms x two reps x 100 turns -> n = 600, REFUSED --------------
    def test_three_arms_two_reps_is_refused_at_600(self):
        """THE CASE THAT WAS WRONGLY ADMITTED: 600 requests against a 500 ceiling."""
        verdict = _gate(hypothesis="E1", turns=100, reps=2, arms=3)
        self.assertFalse(verdict["ok"], verdict)
        self.assertEqual(verdict["n"], 600, verdict)
        self.assertEqual(verdict.get("exit", 12), 12, verdict)
        self.assertIn("baseline n=600", verdict["computed"], verdict["computed"])
        self.assertIn("200-500", verdict["consequence"], verdict["consequence"])
        self.assertIn("500 actual sends", verdict["consequence"], verdict["consequence"])
        try:
            cell._enforce(verdict, "3c/7 G3 prereg gate", 12)
        except cell.Abort as exc:
            self.assertEqual(exc.code, 12, exc.code)
        else:
            raise AssertionError("a three-arm two-rep cell over the ceiling was allowed")
        print(f"  GREEN(2): n={verdict['n']} refused (ceiling 500)")

    # -- (3) one arm x two reps x 100 turns -> n = 200, ADMITTED ----------------
    def test_one_arm_two_reps_is_admitted_at_200(self):
        verdict = _gate(hypothesis="E1", turns=100, reps=2, arms=1)
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual(verdict["n"], 200, verdict)
        print(f"  GREEN(3): n={verdict['n']} admitted (floor 200)")

    # -- (4) one arm x one rep x 100 turns -> n = 100, REFUSED ------------------
    def test_one_arm_one_rep_is_refused_at_100(self):
        verdict = _gate(hypothesis="E1", turns=100, reps=1, arms=1)
        self.assertFalse(verdict["ok"], verdict)
        self.assertEqual(verdict["n"], 100, verdict)
        self.assertIn("baseline n=100", verdict["computed"], verdict["computed"])
        print(f"  GREEN(4): n={verdict['n']} refused (floor 200)")

    # -- (5) the H1 path is UNCHANGED ------------------------------------------
    def test_h1_path_is_unchanged(self):
        """With no arm count supplied, n is turns x reps exactly as before, and the
        threshold is still PARM-1's 60."""
        at_59 = _gate(hypothesis="H1", turns=59, reps=1)
        self.assertEqual(at_59["n"], 59, at_59)
        self.assertEqual(at_59["thresholds"]["min_n"], 60, at_59["thresholds"])
        self.assertFalse(at_59["ok"], at_59)
        at_60 = _gate(hypothesis="H1", turns=60, reps=1)
        self.assertEqual(at_60["n"], 60, at_60)
        self.assertTrue(at_60["ok"], at_60)
        # the pre-existing shape: turns x reps, no arm term when none is declared
        two_reps = _gate(hypothesis="H1", turns=30, reps=2)
        self.assertEqual(two_reps["n"], 60, two_reps)
        self.assertTrue(two_reps["ok"], two_reps)
        # and the arm term is the SAME rule for H1 -- the threshold is what is unchanged
        three_arms = _gate(hypothesis="H1", turns=20, reps=1, arms=3)
        self.assertEqual(three_arms["n"], 60, three_arms)
        self.assertTrue(three_arms["ok"], three_arms)
        print(f"  GREEN(5): H1 n=59 refused, n=60 admitted, threshold 60 unchanged")

    # -- (6) the adapter never defaults the arm count to 1 ---------------------
    def test_adapter_supplies_the_real_arm_count(self):
        fixture = R.load_fixture(FIXTURE)
        for spec, want in (("spcc", 1), ("spcc,pointer-stable", 2),
                           ("spcc,pointer-stable,transcript-grow", 3)):
            cfg = R.build_parser().parse_args(
                ["--fixture", FIXTURE, "--arms", spec, "--reps", "1",
                 "--temperature", "0", "--claim-mode", "E1"])
            self.assertEqual(R.prereg_gate_args(cfg, fixture).arms, want, spec)
        print("  GREEN(6): adapter arm counts 1/2/3 from --arms")

    # -- (7) the CEILING is enforced on ACTUAL sends by the brake --------------
    def test_fetch_heavy_three_arm_cell_is_stopped_at_the_ceiling(self):
        """Three arms, one rep, 100 turns, fetch rounds per turn > 0.

        The baseline is 300 -- ADMITTED by G3 -- but every turn buys a fetch follow-up,
        so the run would send 600.  The brake must stop it at 500 ACTUAL requests.
        """
        run_dir = tempfile.mkdtemp(prefix="run-", dir=self.tmp)
        corpus_dir = os.path.join(run_dir, "corpus")
        os.makedirs(corpus_dir)
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_dir = os.path.join(run_dir, "manifests")
        os.makedirs(manifest_dir)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            # A DISTINCT range every send, so no call is ever served from the
            # conversation cache: every fetch turn really buys its follow-ups.
            start = 1 + (calls["n"] % 4000)
            resp = _resp('<tool_call>read_file {"path": '
                         '"experiments/ptr-engine/longrun/run_longrun.py", '
                         '"start_line": %d, "end_line": %d}</tool_call>'
                         % (start, start + 4))
            resp["request_sha256"] = hashlib.sha256(
                ("wire-body-%d" % calls["n"]).encode()).hexdigest()
            return resp

        cfg = R.build_parser().parse_args(
            ["--fixture", FIXTURE, "--arms", "transcript-grow", "--reps", "1",
             "--temperature", "0", "--seed", "42",
             "--model", "offline-model-was-never-called",
             "--base-url", "http://offline.invalid",
             "--claim-mode", "E1",
             "--tools", "read_file",
             "--fetch-rounds-per-turn", "10",
             "--fetch-rounds-per-arm", "200",
             "--budget-cap", "100000",
             "--budget-glob", os.path.join(corpus_dir, "rows-*.jsonl"),
             "--rows", rows_path,
             "--manifest-dir", manifest_dir,
             "--run-id", "armcount-run"])
        fixture = R.load_fixture(FIXTURE)
        # what enforce_prereg_gate + main arm before the first cell
        cfg.prereg_request_ceiling = 500
        cfg.prereg_sends = {"n": 0}

        real_send = R.send_chat
        R.send_chat = fake_chat
        rcs = []
        err = io.StringIO()
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                for arm in ("transcript-grow", "pointer-stable", "lease-reopen"):
                    rcs.append(R.run_cell(cfg, fixture, arm, 1,
                                          "armcount-run-%s-r1" % arm, rows_path))
        finally:
            R.send_chat = real_send

        stderr = err.getvalue()
        # The first two cells run to completion; the third is STOPPED.  A refusal that
        # lands mid-turn leaves the follow-up rows already bought in that turn unwritten,
        # so the exit reconciliation reports the gap and refuses with 9 instead of 4 --
        # the pre-existing mid-turn accounting path, unchanged here.  Either way the run
        # does not continue past the ceiling.
        self.assertEqual(rcs[0], 0, stderr[-1500:])
        self.assertIn(rcs[1], (4, 9), stderr[-1500:])
        self.assertEqual(calls["n"], 500, "the brake must stop at the ceiling, not past it")
        self.assertEqual(cfg.prereg_sends["n"], 500, "the run-scoped tally is the ceiling")
        self.assertIn("prereg request ceiling", stderr, stderr[-1500:])
        self.assertIn("prereg_ceiling=500", stderr, stderr[-1500:])
        self.assertIn("CAP REFUSED", stderr, stderr[-1500:])
        # the baseline was 300 and G3 admitted it: the brake, not the gate, is what
        # stopped this run -- and it stopped it at the ceiling, not at the prediction.
        self.assertLess(300, calls["n"], "the true send count exceeded the baseline")
        print(f"  GREEN(7): baseline=300 admitted, brake stopped at {calls['n']} actual sends")


if __name__ == "__main__":
    unittest.main(verbosity=2)
