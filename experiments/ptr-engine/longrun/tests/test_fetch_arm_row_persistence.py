#!/usr/bin/env python3
"""Red->green proof for PAID-ROW-PERSISTENCE on the ``bounded-context-fetch`` arm (U-SPCC-43).

U-SPCC-42 fixed the MAIN turn loop: a mid-turn ``CapRefusal`` used to propagate out of
``fetch_rounds`` before the rows for the follow-ups already bought in that turn were
written, so the exit reconciliation reported a NEGATIVE delta and the ledger understated
the spend.  It recorded two remaining gaps in its own handoff:

1. ``arm_cd.service_fetches`` -- the ``bounded-context-fetch`` arm's INLINE follow-up path
   (``run_cell``'s ``arm == arm_cd.ARM_D`` block) has the same shape: the turn's own paid
   send is only written once the whole fetch block has returned, so anything that unwinds
   out of ``service_fetches`` (a malformed fetch call, a ``make_row`` failure) leaves a
   paid request with no row AND no reconciliation at all.  ``bounded-context-fetch`` is one
   of the three arms in E1, so an E1 run could undercount spend through that path.
2. ``BudgetExhausted`` still exited 4 without reconciling, so a budget-exhausted run
   reported no delta at all.

The programme cap is enforced on ROW COUNTS, so a lost row is invisible spend.

Offline.  ZERO inference requests, no network, no git.  The transport is a fake that
counts sends, can emit a fetch call on a chosen send, and can refuse at a chosen send.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_fetch_arm_row_persistence.py -q
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
ARM = arm_cd.ARM_D
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


class FetchArmRowPersistenceTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, allocation="projection", max_turns=1, projected=None,
                  fetch_on=(), raise_on=None, raise_kind=None, service_raises=False):
        """Run one offline ``bounded-context-fetch`` cell and report its accounting.

        ``fetch_on`` names the 1-based send numbers whose reply carries a fetch call, so
        the turn buys its inline follow-up.  ``raise_on``/``raise_kind`` make that send
        fail instead.  ``service_raises`` replaces ``arm_cd.service_fetches`` with a
        function that raises, which is the malformed-fetch-call path.
        """
        run_dir = tempfile.mkdtemp(prefix="fetcharm-")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        cfg = _Cfg(max_turns=max_turns, manifest_path=manifest_path, manifest_dir=run_dir,
                   budget_glob=os.path.join(run_dir, "rows-*.jsonl"),
                   budget_cap=64, budget_reserve=0, request_allocation=allocation)
        fixture_obj = R.load_fixture(FIXTURE)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            n = calls["n"]
            if raise_on is not None and n == raise_on:
                if raise_kind == "request":
                    raise R.client.RequestFailure(500, "offline transport failure")
                raise R.client.TurnWallCap(999.0, {"turn_wall_cap_s": 1.0})
            text = _fetch_call(n) if n in fetch_on else FINAL_ANSWER
            return _resp(text, n)

        real_send = R.send_chat
        real_service = arm_cd.service_fetches
        real_projected = R.projected_requests
        R.send_chat = fake_chat
        if projected is not None:
            # BUDGET SEAM: ``projected_requests`` is the cell's request budget.  Pinning it
            # to the cell's turn count prices a tools-on cell exactly like a tools-off one
            # (no fetch pool), which is the only way a 1-turn offline cell can reach the
            # request budget at all -- ``fetch_rounds_per_arm`` clamps a non-positive pool
            # back to 48, so the flag cannot express it.
            R.projected_requests = lambda _cfg, _fx, _arm: int(projected)
        if service_raises:
            def _boom(*_a, **_k):
                raise ValueError("fetch request missing tool_call_id")
            arm_cd.service_fetches = _boom
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, ARM, 1, "fetcharm-run-r1", rows_path)
        finally:
            R.send_chat = real_send
            arm_cd.service_fetches = real_service
            R.projected_requests = real_projected
        manifest = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as handle:
                manifest = json.load(handle)
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "manifest": manifest, "stdout": out.getvalue(), "stderr": err.getvalue()}

    def _reconcile(self, res):
        self.assertIsNotNone(res["manifest"],
                             "the run left no manifest, so it never reconciled: "
                             + res["stderr"][-1200:])
        return res["manifest"]["cap_gate"]["reconcile"]

    # -- (1) a refusal after N sends leaves exactly N rows ---------------------
    def test_refused_mid_turn_writes_one_row_per_send(self):
        # allocation 1: the turn's own send is bought, its inline follow-up is refused.
        res = self._scenario(allocation=1, max_turns=1, fetch_on=(1,))
        self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
        self.assertIn("CAP REFUSED", res["stderr"])
        self.assertEqual(res["calls"], 1, "only the turn's own request reached the wire")
        self.assertEqual(len(res["rows"]), res["calls"],
                         f"{res['calls']} paid send(s) must leave {res['calls']} row(s), "
                         f"got {[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        rec = self._reconcile(res)
        self.assertEqual(rec["delta"], 0,
                         f"delta={rec['delta']} (used_in_run={rec['used_in_run']} "
                         f"spent_after={rec['spent_after']} "
                         f"spent_at_start={rec['spent_at_start']})")
        self.assertIn("cap-gate: reconciled", res["stderr"])

    # -- (2) a fetch-heavy refusal preserves every follow-up row ---------------
    def test_fetch_heavy_refusal_preserves_followup_rows(self):
        # Three turns, a fetch call on turns 1 and 2, allocation 3: turn 1 buys its
        # follow-up, turn 2's own send is bought, turn 2's follow-up is refused.  Every
        # follow-up row bought before the refusal must survive.
        res = self._scenario(allocation=3, max_turns=3, fetch_on=(1, 3))
        self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
        self.assertIn("CAP REFUSED", res["stderr"])
        self.assertEqual(res["calls"], 3, "turn 1 + its follow-up + turn 2 reached the wire")
        self.assertEqual(len(res["rows"]), res["calls"],
                         f"every bought request keeps a row: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        followups = [r for r in res["rows"] if r.get("fetch_followup")]
        self.assertEqual(len(followups), 1,
                         "the follow-up bought on turn 1 must keep its row: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        self.assertEqual([r["kind"] for r in res["rows"]],
                         ["turn-initial", "turn", "turn-initial"],
                         "turn 1's own send, turn 1's follow-up (its row IS the turn row), "
                         "turn 2's own send")
        rec = self._reconcile(res)
        self.assertEqual(rec["delta"], 0,
                         f"delta={rec['delta']} (used_in_run={rec['used_in_run']} "
                         f"spent_after={rec['spent_after']})")

    # -- (3) a BudgetExhausted exit reconciles ---------------------------------
    def test_budget_exhausted_exit_reconciles(self):
        # A cell priced at exactly its turn count: the D arm's inline follow-up hits the
        # request budget right after the turn's own send.
        res = self._scenario(allocation="projection", max_turns=1, projected=1,
                             fetch_on=(1,))
        self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
        self.assertIn("BUDGET ABORT", res["stderr"])
        self.assertEqual(res["calls"], 1, "the turn's own request reached the wire")
        self.assertEqual(len(res["rows"]), res["calls"],
                         f"the paid send keeps its row: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        rec = self._reconcile(res)
        self.assertEqual(rec["delta"], 0,
                         f"a budget-exhausted exit must reconcile: delta={rec['delta']} "
                         f"(used_in_run={rec['used_in_run']} "
                         f"spent_after={rec['spent_after']})")
        self.assertIn("cap-gate: reconciled", res["stderr"])

    # -- (4) a completed fetch cell is unchanged -------------------------------
    def test_completed_cell_counts_unchanged(self):
        res = self._scenario(allocation=4, max_turns=1, fetch_on=(1,))
        self.assertEqual(res["rc"], 0, res["stderr"][-1200:])
        self.assertEqual(res["calls"], 2, "the turn plus its inline follow-up")
        self.assertEqual(len(res["rows"]), 2,
                         f"a completed fetch turn keeps one row per send: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        self.assertEqual([r["kind"] for r in res["rows"]], ["turn-initial", "turn"])
        rec = self._reconcile(res)
        self.assertEqual(rec["delta"], 0)
        self.assertEqual(rec["used_in_run"], 2)

    # -- (5) an unwind out of service_fetches keeps the turn's row -------------
    def test_service_failure_persists_the_turn_row(self):
        # A malformed fetch call makes service_fetches raise AFTER the turn's own request
        # was paid for.  That row must be on disk and the run must reconcile.
        res = self._scenario(allocation=4, max_turns=1, fetch_on=(1,), service_raises=True)
        self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
        self.assertEqual(res["calls"], 1, "only the turn's own request reached the wire")
        self.assertEqual(len(res["rows"]), res["calls"],
                         f"the paid send keeps its row: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        rec = self._reconcile(res)
        self.assertEqual(rec["delta"], 0,
                         f"delta={rec['delta']} (used_in_run={rec['used_in_run']} "
                         f"spent_after={rec['spent_after']})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
