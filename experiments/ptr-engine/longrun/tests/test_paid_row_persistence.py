#!/usr/bin/env python3
"""Red->green proof for PAID-ROW-PERSISTENCE (U-SPCC-42).

The programme cap is enforced on ROW COUNTS: ``tools/request_ledger.py`` sums the rows
across ``measure/rows-*.jsonl`` and the cap gate compares that sum to the cap.  A paid
model call that produces no row is therefore INVISIBLE SPEND.

U-SPCC-40 measured the defect: a fetch-heavy cell stopped by the per-request brake at the
prereg ceiling exited with ``delta=-4`` -- four paid follow-up calls produced no row.  The
mechanism was a mid-turn ``CapRefusal`` propagating out of the round loop before the rows
for the follow-ups already bought in that turn were written.

The invariant this file pins: **every paid model call produces exactly one row, written
before the next send.**  A refusal may stop the run, but it must never discard a row for a
call that was already paid for.

Offline.  ZERO inference requests, no network, no git.  The transport is a fake that
counts sends and returns a fresh tool call on every reply, so a turn buys as many
follow-ups as the allocation allows.

Run:  TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python -m pytest \
        experiments/ptr-engine/longrun/tests/test_paid_row_persistence.py -q
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

FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.json")
FIXTURE_TOOLS = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")


class _Cfg:
    """The runner's cfg surface, minimal and explicit (no argparse, no network)."""

    def __init__(self, **kw):
        self.tools = ""
        self.max_tokens = 256
        self.stream = True
        self.engine = "sglang"
        self.model = "offline-model-was-never-called"
        self.base_url = "http://offline.invalid"
        self.timeout = 5.0
        self.thinking = "auto"
        self.dry_run = False
        self.max_turns = 0
        self.resume = False
        self.manifest_path = None
        self.manifest_dir = tempfile.gettempdir()
        self.turn_wall_cap = 180.0
        self.runaway_turns = 2
        self.budget_cap = None
        self.budget_reserve = 0
        self.budget_glob = None
        self.request_allocation = "projection"
        for key, value in kw.items():
            setattr(self, key, value)


def _resp(text: str) -> dict:
    return {"content": text, "content_raw": text, "reasoning": "", "content_source": "content",
            "finish_reason": "stop", "truncated": False, "max_tokens": 256,
            "prompt_tokens": 10, "raw_cached": None, "token_source": "offline",
            "completion_tokens": 5, "ttft_s": 0.1, "ttft_ms": 100, "latency_s": 0.2,
            "usage_missing": False}


def _write_rows(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(json.dumps(row) + "\n" for row in rows)


def _corpus_row(n: int) -> dict:
    return {"kind": "turn", "arm": "fixture", "task_id": "T-1", "rep": 1, "turn": n,
            "prompt_tokens": 100, "completion_tokens": 10,
            "ts": f"2026-10-26T12:00:{n % 60:02d}.000Z"}


def _read_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _tool_call(n: int) -> str:
    """A DISTINCT read_file range per send, so no round is served from the cache."""
    start = 1 + (n - 1) * 10
    return ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
            '"start_line": %d, "end_line": %d}' % (start, start + 9))


class PaidRowPersistenceTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, corpus=100, cap=500, allocation="projection", max_turns=1,
                  tools="", tool_every_send=False):
        run_dir = tempfile.mkdtemp(prefix="paidrow-")
        corpus_dir = os.path.join(run_dir, "corpus")
        os.makedirs(corpus_dir)
        glob = os.path.join(corpus_dir, "rows-*.jsonl")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        _write_rows(os.path.join(corpus_dir, "rows-fixture.jsonl"),
                    [_corpus_row(n) for n in range(corpus)])
        cfg = _Cfg(tools=tools, max_turns=max_turns, manifest_path=manifest_path,
                   manifest_dir=run_dir, budget_glob=glob, budget_cap=cap,
                   budget_reserve=0, request_allocation=allocation)
        fixture_obj = R.load_fixture(FIXTURE_TOOLS if tools else FIXTURE)
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            n = calls["n"]
            text = _tool_call(n) if (tools and tool_every_send) else "ANSWER: 42"
            resp = _resp(text)
            resp["request_sha256"] = hashlib.sha256(
                ("wire-body-%d" % n).encode()).hexdigest()
            return resp

        real_send = R.send_chat
        R.send_chat = fake_chat
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, "pointer-stable", 1, "paidrow-run-r1",
                                rows_path)
        finally:
            R.send_chat = real_send
        manifest = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as handle:
                manifest = json.load(handle)
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "manifest": manifest, "stdout": out.getvalue(), "stderr": err.getvalue()}

    # -- (1) a refusal after N sends leaves exactly N rows ---------------------
    def test_refused_mid_turn_writes_one_row_per_send(self):
        for allocation in (1, 2, 3):
            with self.subTest(allocation=allocation):
                res = self._scenario(corpus=100, cap=500, allocation=allocation,
                                     max_turns=1, tools="read_file",
                                     tool_every_send=True)
                self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
                self.assertIn("CAP REFUSED", res["stderr"])
                self.assertEqual(
                    len(res["rows"]), res["calls"],
                    f"allocation={allocation}: {res['calls']} paid send(s) must leave "
                    f"{res['calls']} row(s), got {len(res['rows'])}: "
                    f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
                rec = res["manifest"]["cap_gate"]["reconcile"]
                self.assertEqual(rec["delta"], 0,
                                 f"allocation={allocation}: delta={rec['delta']} "
                                 f"(used_in_run={rec['used_in_run']} "
                                 f"spent_after={rec['spent_after']} "
                                 f"spent_at_start={rec['spent_at_start']})")
                self.assertIn("cap-gate: reconciled", res["stderr"])

    # -- (2) a fetch-heavy refusal preserves every follow-up row ---------------
    def test_fetch_heavy_refusal_preserves_followup_rows(self):
        # allocation 3 on a 1-turn cell: the turn's own send + 2 follow-ups are bought,
        # the 3rd follow-up is refused.  Every bought follow-up must have its row.
        res = self._scenario(corpus=100, cap=500, allocation=3, max_turns=1,
                             tools="read_file", tool_every_send=True)
        self.assertEqual(res["rc"], 4, res["stderr"][-1200:])
        self.assertEqual(res["calls"], 3, "the turn plus two follow-ups reached the wire")
        self.assertEqual(len(res["rows"]), 3, res["stderr"][-1200:])
        followups = [r for r in res["rows"] if r.get("fetch_followup")]
        self.assertEqual(len(followups), 2,
                         f"both bought follow-ups must keep a row: "
                         f"{[(r.get('kind'), r.get('send_index')) for r in res['rows']]}")
        self.assertEqual(sorted(int(r["send_index"]) for r in res["rows"]), [0, 1, 2],
                         "each send owns exactly one row")
        self.assertEqual(res["manifest"]["cap_gate"]["reconcile"]["delta"], 0)

    # -- (3) a completed cell is unchanged -------------------------------------
    def test_completed_cell_counts_unchanged(self):
        # No tools: two turns, two sends, two rows, delta 0 -- the pre-fix behaviour.
        plain = self._scenario(corpus=10, cap=4320, allocation=3, max_turns=2)
        self.assertEqual(plain["rc"], 0, plain["stderr"][-1200:])
        self.assertEqual(plain["calls"], 2)
        self.assertEqual(len(plain["rows"]), 2)
        self.assertEqual([r["kind"] for r in plain["rows"]], ["turn", "turn"])
        self.assertEqual(plain["manifest"]["cap_gate"]["reconcile"]["delta"], 0)

        # Tools on, allocation large enough that the turn completes: one row per send.
        with_tools = self._scenario(corpus=10, cap=4320, allocation=4, max_turns=1,
                                    tools="read_file", tool_every_send=True)
        self.assertEqual(with_tools["rc"], 0, with_tools["stderr"][-1200:])
        self.assertEqual(len(with_tools["rows"]), with_tools["calls"],
                         "a completed fetch-heavy turn keeps one row per send")
        self.assertEqual(with_tools["manifest"]["cap_gate"]["reconcile"]["delta"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
