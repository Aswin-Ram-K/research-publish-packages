#!/usr/bin/env python3
"""Red->green proof for FETCH-ROUNDS-ACCOUNTING (U-SPCC-50).

Two defects, both offline-provable with a fake client and zero requests:

  1. ``fetch_rounds_used`` was initialised at ``run_longrun.py:3359`` and never
     incremented on the ``bounded-context-fetch`` path, which is the arm that actually
     fetches.  The E1 cell therefore stamped ``0`` on 52 rows and ``null`` on 66 while
     spending 18 of its 48-round pool, and ``manifest['tools']['fetch_rounds_used']``
     stayed ``0``.
  2. The manifest's ``tools`` block was frozen at launch and never updated at
     finalisation, so a finished cell reported launch POLICY, not what happened.

The three assertions below are the acceptance contract:

  (1) a tools-on run stamps a monotonically non-decreasing ``fetch_rounds_used`` that
      ends equal to the number of rounds actually spent;
  (2) a tools-off run stamps ``null``, not ``0``;
  (3) the finalised manifest's ``tools`` block reports the OBSERVED total, not the
      launch default.

Run from the workspace root:
  python3 experiments/ptr-engine/longrun/tests/test_fetch_rounds_accounting.py
Exit 0 = every assertion held.  No socket is opened: ``send_chat`` is a canned function
and ``arm_cd.service_fetches`` reads the fixture's own documents.
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

# PT-01 carries ``fetch_budget_tokens``, which ``arm_cd.resolve_fetch_budget`` requires
# before the D arm can serve a single fetch.
FIXTURE = os.path.join(LONGRUN, "tasks-v6", "PT-01.v9.json")
ARM_FETCH = arm_cd.ARM_D
ARM_PLAIN = "pointer-stable"
FINAL_ANSWER = "ANSWER: TEXT offline"


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


def _resp(text: str, n: int) -> dict:
    return {"content": text, "content_raw": text, "reasoning": "",
            "content_source": "content", "finish_reason": "stop", "truncated": False,
            "max_tokens": 256, "prompt_tokens": 10 + n, "raw_cached": None,
            "token_source": "offline", "completion_tokens": 5, "wall_ms": 40,
            "request_sha256": hashlib.sha256(("wire-body-%d" % n).encode()).hexdigest(),
            "request_identity_complete": True, "ttft_s": 0.04, "ttft_ms": 40,
            "latency_s": 0.08, "usage_missing": False, "tool_calls": None}


def _fetch_call(n: int) -> str:
    """A DISTINCT fetch ref per send, so no round is served from the cache."""
    return '<tool_call>fetch {"ref": "turn-%d@r1"}' % n


def _read_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class FetchRoundsAccountingTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, arm, tools, max_turns, fetch_on=()):
        """Run one offline cell and return its rows, manifest and launch manifest."""
        run_dir = tempfile.mkdtemp(prefix="fetchrounds-")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        cfg = _Cfg(tools=tools, max_turns=max_turns, manifest_path=manifest_path,
                   manifest_dir=run_dir, budget_glob=os.path.join(run_dir, "rows-*.jsonl"),
                   budget_cap=64, budget_reserve=0, request_allocation="projection")
        fixture_obj = R.load_fixture(FIXTURE)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            n = calls["n"]
            text = _fetch_call(n) if n in fetch_on else FINAL_ANSWER
            return _resp(text, n)

        real_send = R.send_chat
        R.send_chat = fake_chat
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, arm, 1, "fetchrounds-run-r1", rows_path)
        finally:
            R.send_chat = real_send
        launch = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as handle:
                launch = json.load(handle)
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "manifest": launch, "stdout": out.getvalue(), "stderr": err.getvalue()}

    # -- (1) tools-on: monotonic, ends at the rounds actually spent ------------
    def test_tools_on_counter_is_monotonic_and_final(self):
        # `fetch_on` names SEND numbers, not turns: send 1 is T1's own request, send 2 is
        # T1's follow-up, send 3 is T2's own request.  So turns 1 and 2 each buy a round.
        res = self._scenario(arm=ARM_FETCH, tools="read_file", max_turns=3,
                             fetch_on=(1, 3))
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        rows = res["rows"]
        self.assertTrue(rows, "the cell wrote no rows")

        stamped = [r.get("fetch_rounds_used") for r in rows]
        self.assertNotIn(None, stamped,
                         "every row of a tools-on run must carry the counter: "
                         f"{[(r.get('kind'), r.get('turn'), r.get('fetch_rounds_used')) for r in rows]}")
        self.assertEqual(stamped, sorted(stamped),
                         f"fetch_rounds_used must be non-decreasing in row order: {stamped}")

        spent = sum(1 for r in rows if r.get("fetch_followup") is True)
        self.assertEqual(spent, 2, f"the cell bought 2 fetch rounds, rows say {spent}")
        self.assertEqual(stamped[-1], spent,
                         f"the counter must END at the rounds actually spent: "
                         f"final={stamped[-1]} spent={spent}")

        # the launch default is 0; the finalised block must report the observed total
        tools = res["manifest"]["tools"]
        self.assertEqual(tools["fetch_rounds_used"], spent,
                         f"manifest tools.fetch_rounds_used={tools['fetch_rounds_used']} "
                         f"but the cell spent {spent}")
        self.assertEqual(tools["fetch_rounds_available"], R.TOOL_FETCH_ROUNDS_PER_ARM,
                         tools["fetch_rounds_available"])
        self.assertIsInstance(tools["tools_schema_sent"], bool, tools["tools_schema_sent"])
        print(f"  (1) tools-on: rows={len(rows)} stamped={stamped} spent={spent} "
              f"manifest_used={tools['fetch_rounds_used']} "
              f"available={tools['fetch_rounds_available']} "
              f"schema_sent={tools['tools_schema_sent']}")

    # -- (2) tools-off: null, never 0 -----------------------------------------
    def test_tools_off_counter_is_null_not_zero(self):
        res = self._scenario(arm=ARM_PLAIN, tools="", max_turns=2)
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        rows = res["rows"]
        self.assertTrue(rows, "the cell wrote no rows")
        values = [r.get("fetch_rounds_used") for r in rows]
        self.assertTrue(all(v is None for v in values),
                        f"a tools-off run must stamp null, not 0: {values}")
        self.assertNotIn(0, values, f"0 is a lie on a tools-off run: {values}")
        self.assertNotIn("tools", res["manifest"],
                         "a tools-off manifest must keep the bytes it had before --tools")
        print(f"  (2) tools-off: rows={len(rows)} values={values} "
              f"manifest_has_tools={'tools' in res['manifest']}")

    # -- (3) the manifest reports the observed total, not the launch default ---
    def test_manifest_tools_block_is_finalised(self):
        res = self._scenario(arm=ARM_FETCH, tools="read_file", max_turns=2,
                             fetch_on=(1,))
        self.assertEqual(res["rc"], 0, res["stderr"][-1500:])
        tools = res["manifest"]["tools"]
        spent = sum(1 for r in res["rows"] if r.get("fetch_followup") is True)
        self.assertEqual(spent, 1, f"one fetch round was bought, rows say {spent}")
        self.assertEqual(tools["fetch_rounds_used"], 1,
                         f"the finalised block must report the observed total, not the "
                         f"launch default 0: {tools['fetch_rounds_used']}")
        # the launch policy fields survive the update untouched
        self.assertEqual(tools["max_fetch_rounds_per_arm"], R.TOOL_FETCH_ROUNDS_PER_ARM)
        self.assertIn("max_fetch_rounds_per_turn", tools,
                      "the launch policy fields must survive the finalisation update")
        print(f"  (3) finalised manifest: fetch_rounds_used={tools['fetch_rounds_used']} "
              f"(launch default was 0) available={tools['fetch_rounds_available']} "
              f"schema_sent={tools['tools_schema_sent']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
