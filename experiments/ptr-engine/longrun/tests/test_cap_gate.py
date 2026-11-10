#!/usr/bin/env python3
"""Red->green proof for WIRE-CAP-GATE: the budget cap stops a request BEFORE it is sent.

Offline. ZERO inference requests, no network, no git.  Every transport is a fake; the
real HTTP path is never reached because the gate refuses first (or the fake is installed).

Cases, per the unit contract:
  (a) ZERO ROWS ON REFUSAL -- ledger headroom smaller than the run's allocation: the run
      refuses at T1, exits 4, writes 0 rows, and the fake transport was NEVER called.
  (b) MID-RUN REFUSAL -- allocation 2 on a 3-turn cell: stops at the request that would
      exceed (T3), exits 4, and rows written == exactly the 2 legitimate requests.
  (c) FOLLOW-UP REQUESTS ARE COUNTED -- a turn that triggers a fetch follow-up consumes
      TWO units; allocation 1 refuses the follow-up (transport called once), allocation 2
      allows both.
  (d) ALLOWS -- a run under both limits exits 0, and the manifest records used_in_run ==
      the actual request count, with a reconciling delta of 0.
  (e) RED->GREEN -- neuter the pre-send call: the zero-rows scenario then WRITES rows
      (named); restore it and the same scenario writes none.
  (f) RECONCILE DIVERGENCE -- a writer that records a row no request bought makes the run
      fail loudly (exit 9, delta printed), never silently.
  (g) EXIT CODES reach the process exit status unmodified: 4 (refusal), 3 (usage),
      5 (unreadable rows) through main() -> sys.exit.

Run:  python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cap_gate.py' -v
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

RUNNER = os.path.join(LONGRUN, "run_longrun.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.json")
FIXTURE_TOOLS = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
TOOL_CALL_TURN = ('<tool_call>read_file {"path": "ptr_engine/resolve.py", '
                  '"start_line": 1, "end_line": 30}')


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


class CapGateTest(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(REPO)
        self.tmp = tempfile.mkdtemp(prefix="capgate-")
        self.corpus_dir = os.path.join(self.tmp, "corpus")
        os.makedirs(self.corpus_dir)
        self.glob = os.path.join(self.corpus_dir, "rows-*.jsonl")
        self.rows_path = os.path.join(self.tmp, "rows-cell.jsonl")
        self.manifest_path = os.path.join(self.tmp, "manifest.json")

    def tearDown(self):
        os.chdir(self._cwd)

    # -- harness ---------------------------------------------------------------
    def _scenario(self, *, corpus=100, cap=None, reserve=0, allocation="projection",
                  max_turns=2, tools="", neuter_brake=False, extra_row_writer=False,
                  drop_rows=False, fixture=None):
        run_dir = tempfile.mkdtemp(prefix="run-", dir=self.tmp)
        corpus_dir = os.path.join(run_dir, "corpus")
        os.makedirs(corpus_dir)
        glob = os.path.join(corpus_dir, "rows-*.jsonl")
        rows_path = os.path.join(run_dir, "rows-cell.jsonl")
        manifest_path = os.path.join(run_dir, "manifest.json")
        _write_rows(os.path.join(corpus_dir, "rows-fixture.jsonl"),
                    [_corpus_row(n) for n in range(corpus)])
        cfg = _Cfg(tools=tools, max_turns=max_turns, manifest_path=manifest_path,
                   manifest_dir=run_dir, budget_glob=glob, budget_cap=cap,
                   budget_reserve=reserve, request_allocation=allocation)
        fixture_obj = R.load_fixture(fixture or (FIXTURE_TOOLS if tools else FIXTURE))
        calls = {"n": 0}

        def fake_chat(_cfg, _messages):
            calls["n"] += 1
            if extra_row_writer:
                # A writer that records a row no request bought: the divergence the
                # reconciliation must catch instead of rounding away.
                with open(rows_path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(_corpus_row(99)) + "\n")
            resp = _resp(TOOL_CALL_TURN if (tools and calls["n"] == 1) else "ANSWER: 42")
            # REQUEST-IDENTITY: the real transport hashes the exact wire body, one
            # distinct value per SEND (test_row_attribution.py:94-95).  Without it every
            # row would carry REQUEST_SHA_UNKNOWN and the per-send invariant could not
            # be asserted at all.
            resp["request_sha256"] = hashlib.sha256(
                ("wire-body-%d" % calls["n"]).encode()).hexdigest()
            return resp

        real_send, real_acquire = R.send_chat, R.RequestCapGate.acquire
        real_append = R.append_row
        R.send_chat = fake_chat
        if drop_rows:
            # A request reaches the wire but its row never lands: the ledger then
            # under-states what was billed, which is the delta<0 direction.
            R.append_row = lambda path, row: None
        if neuter_brake:
            # RED: the pre-send call is neutered -- the slot is never reserved and never
            # refused, so the run walks straight through the cap and writes rows.
            R.RequestCapGate.acquire = lambda self, turn, kind="turn": self.used_in_run + 1
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                rc = R.run_cell(cfg, fixture_obj, "pointer-stable", 1, "capgate-run-r1",
                                rows_path)
        finally:
            R.send_chat, R.RequestCapGate.acquire = real_send, real_acquire
            R.append_row = real_append
        manifest = None
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as handle:
                manifest = json.load(handle)
        return {"rc": rc, "rows": _read_rows(rows_path), "calls": calls["n"],
                "manifest": manifest, "stdout": out.getvalue(), "stderr": err.getvalue()}

    # -- (a) the test the ledger's own hint asked for --------------------------
    def test_a_zero_rows_on_refusal(self):
        # spent=100 rows on disk, headroom=100: the very first request projects 101.
        res = self._scenario(corpus=100, cap=100, allocation=3, max_turns=3)
        self.assertEqual(res["rc"], 4, res["stderr"][-800:])
        self.assertEqual(len(res["rows"]), 0, "a refusal must write NO row")
        self.assertEqual(res["calls"], 0, "the transport must never be called")
        for token in ("spent=100", "would_spend=1", "cap=100", "reserve=0", "headroom=100",
                      "allocation=3", "used_in_run=0", "turn=1", "CAP REFUSED"):
            self.assertIn(token, res["stderr"], f"missing arithmetic token {token!r}")
        self.assertIn("cap-gate: reconciled", res["stderr"])
        self.assertEqual(res["manifest"]["cap_gate"]["final_used_in_run"], 0)

    # -- (b) mid-run refusal ---------------------------------------------------
    def test_b_midrun_stops_at_the_right_turn(self):
        res = self._scenario(corpus=100, cap=500, allocation=2, max_turns=3)
        self.assertEqual(res["rc"], 4, res["stderr"][-800:])
        self.assertEqual(res["calls"], 2, "exactly the legitimate requests reached the wire")
        self.assertEqual([(r["turn"], r["kind"]) for r in res["rows"]],
                         [(1, "turn"), (2, "turn")], "rows == the legitimate requests")
        self.assertIn("CAP REFUSED at T3", res["stderr"])
        self.assertIn("used_in_run=2", res["stderr"])
        self.assertEqual(res["manifest"]["cap_gate"]["final_used_in_run"], 2)

    # -- (c) follow-ups are requests too ---------------------------------------
    def test_c_followup_counts_as_a_second_unit(self):
        refused = self._scenario(corpus=100, cap=500, allocation=1, max_turns=1,
                                 tools="read_file")
        self.assertEqual(refused["rc"], 4, refused["stderr"][-800:])
        self.assertEqual(refused["calls"], 1, "the turn was sent; the follow-up was not")
        self.assertIn("(tool-followup)", refused["stderr"])
        self.assertIn("used_in_run=1", refused["stderr"])
        self.assertEqual([r["kind"] for r in refused["rows"]], ["turn"])

        allowed = self._scenario(corpus=100, cap=500, allocation=2, max_turns=1,
                                 tools="read_file")
        self.assertEqual(allowed["rc"], 0, allowed["stderr"][-800:])
        self.assertEqual(allowed["calls"], 2, "turn + follow-up = two billed requests")
        self.assertEqual(len(allowed["rows"]), 2)
        # ROW-ATTRIBUTION is the contract now (test_row_attribution.py:222-231): ONE ROW
        # PER SEND.  For k=1 follow-up the turn writes the turn's own request as
        # kind="turn-initial" (send_index 0) and the FOLLOW-UP's request as kind="turn"
        # (send_index 1, row_measurement_source="tool-followup").  The old literal list
        # ["turn-initial", "tool-followup", "turn"] is the PRE-fix row model: it expected
        # the follow-up to be written twice, once as its own row and once mirrored by the
        # turn row.  A follow-up is still a second billed unit; that intent is now
        # expressed as an invariant stronger than any literal kind list -- each send owns
        # exactly one row, and each row carries that send's own request identity.
        by_send = sorted(allowed["rows"], key=lambda r: int(r["send_index"]))
        self.assertEqual([int(r["send_index"]) for r in by_send], [0, 1],
                         "each send owns exactly one row")
        self.assertEqual([r["row_measurement_source"] for r in by_send],
                         ["turn-initial", "tool-followup"],
                         "row 0 measures the turn's own send, row 1 the follow-up's")
        self.assertIs(by_send[1]["fetch_followup"], True,
                      "the follow-up's row is marked as the follow-up it measures")
        shas = [r["request_sha256"] for r in by_send]
        self.assertEqual(len(set(shas)), 2, f"each send has its OWN request_sha256: {shas}")
        self.assertTrue(all(s and s != R.client.REQUEST_SHA_UNKNOWN for s in shas), shas)
        self.assertEqual(allowed["manifest"]["cap_gate"]["final_used_in_run"], 2)

    # -- (d) allows ------------------------------------------------------------
    def test_d_allows_and_records_the_count(self):
        res = self._scenario(corpus=10, cap=4320, reserve=100, allocation=3, max_turns=2)
        self.assertEqual(res["rc"], 0, res["stderr"][-800:])
        self.assertEqual(res["calls"], 2)
        self.assertEqual(len(res["rows"]), 2)
        block = res["manifest"]["cap_gate"]
        self.assertEqual(block["final_used_in_run"], 2)
        self.assertEqual(block["used_in_run"], 2)
        self.assertEqual(block["reconcile"]["delta"], 0)
        self.assertEqual(block["spent_at_start"], 10)
        self.assertEqual(block["reconcile"]["spent_after"], 12)
        self.assertEqual(block["allocation"], 3)
        self.assertEqual(block["ordering"].split(":")[0], "record->gate->send")
        self.assertIn("cap-gate: reconciled", res["stderr"])

    # -- (e) red -> green ------------------------------------------------------
    def test_e_red_green_neutered_brake_writes_rows(self):
        red = self._scenario(corpus=100, cap=100, allocation=3, max_turns=3,
                            neuter_brake=True)
        self.assertGreater(len(red["rows"]), 0, "the neutered brake must visibly write rows")
        first = red["rows"][0]
        self.assertEqual((first["turn"], first["kind"]), (1, "turn"),
                         "the row a post-send/absent gate lets through is T1/turn")
        self.assertTrue(all("CAP REFUSED" not in red["stderr"] for _ in [0]),
                        "a neutered brake cannot refuse")
        print(f"  RED: neutered pre-send call -> rc={red['rc']} rows={len(red['rows'])} "
              f"first_row=T{first['turn']}/{first['kind']} requests={red['calls']}")

        green = self._scenario(corpus=100, cap=100, allocation=3, max_turns=3)
        self.assertEqual(green["rc"], 4)
        self.assertEqual(len(green["rows"]), 0)
        self.assertEqual(green["calls"], 0)
        print(f"  GREEN: brake restored -> rc={green['rc']} rows={len(green['rows'])} "
              f"requests={green['calls']}")

    # -- (f) reconcile divergence ---------------------------------------------
    def test_f_divergence_fails_loudly(self):
        res = self._scenario(corpus=10, cap=4320, allocation=3, max_turns=1,
                             extra_row_writer=True)
        self.assertEqual(res["rc"], R.EXIT_CAP_DIVERGENCE, res["stderr"][-800:])
        self.assertIn("RECONCILE DIVERGENCE", res["stderr"])
        self.assertIn("delta=1", res["stderr"])
        self.assertEqual(res["manifest"]["cap_gate"]["reconcile"]["delta"], 1)

    # -- (g) exit codes reach the process exit status --------------------------
    def _subprocess(self, extra, corpus_rows=None):
        corpus = os.path.join(self.corpus_dir, "rows-fixture.jsonl")
        if corpus_rows is not None:
            _write_rows(corpus, corpus_rows)
        argv = [sys.executable, RUNNER, "--fixture", FIXTURE, "--arms", "pointer-stable",
                "--max-turns", "1", "--rows", self.rows_path,
                "--manifest-path", self.manifest_path, "--budget-glob", self.glob,
                "--temperature", "0"] + extra
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=120)
        return proc

    def test_g1_exit4_reaches_the_process(self):
        proc = self._subprocess(["--budget-cap", "1", "--request-allocation", "3"],
                                corpus_rows=[_corpus_row(1)])
        self.assertEqual(proc.returncode, 4, proc.stderr[-800:])
        self.assertIn("CAP REFUSED at T1", proc.stderr)
        self.assertEqual(_read_rows(self.rows_path), [])

    def test_g2_exit3_usage(self):
        proc = self._subprocess(["--request-allocation", "not-a-number"],
                                corpus_rows=[_corpus_row(1)])
        self.assertEqual(proc.returncode, 3, proc.stderr[-800:])
        self.assertIn("CAP GATE USAGE", proc.stderr)

    def test_g3_exit5_unreadable_rows(self):
        corpus = os.path.join(self.corpus_dir, "rows-fixture.jsonl")
        with open(corpus, "w", encoding="utf-8") as handle:
            handle.write('{"kind": "turn"\n')  # unparseable
        proc = self._subprocess([])
        self.assertEqual(proc.returncode, 5, proc.stderr[-800:])
        self.assertIn("CAP GATE ROWS", proc.stderr)
        self.assertEqual(_read_rows(self.rows_path), [])


    # -- UNRECORDED-REFUSE: a short ledger must REFUSE, not report ------------
    def test_unrecorded_spend_refuses(self):
        # One request reached the wire, its row was dropped: delta = -1.
        res = self._scenario(corpus=10, cap=4320, allocation=3, max_turns=1,
                             drop_rows=True)
        self.assertEqual(res["calls"], 1, "exactly one request reached the wire")
        self.assertEqual(res["rows"], [], "the dropped row must not appear")
        self.assertEqual(res["rc"], R.EXIT_CAP_DIVERGENCE,
                         "unrecorded spend must refuse with the divergence code: "
                         + res["stderr"][-800:])
        self.assertIn("CAP GATE UNRECORDED", res["stderr"])
        self.assertIn("delta=-1", res["stderr"])
        self.assertIn("ledger cannot be trusted", res["stderr"])
        self.assertIn("headroom_before=", res["stderr"])
        self.assertNotIn("RECONCILE DIVERGENCE", res["stderr"],
                         "unrecorded must be distinguishable from divergence")
        self.assertEqual(res["manifest"]["cap_gate"]["reconcile"]["delta"], -1)
        line = [ln for ln in res["stderr"].splitlines() if "CAP GATE UNRECORDED" in ln]
        self.assertTrue(line, "the refusal line must be printed")
        print(f"  GREEN: exit={res['rc']} | {line[0]}")

    def test_reconciled_run_still_succeeds(self):
        res = self._scenario(corpus=10, cap=4320, reserve=100, allocation=3,
                             max_turns=2)
        self.assertEqual(res["rc"], 0, res["stderr"][-800:])
        self.assertEqual(res["manifest"]["cap_gate"]["reconcile"]["delta"], 0)
        self.assertIn("cap-gate: reconciled", res["stderr"])
        self.assertNotIn("CAP GATE UNRECORDED", res["stderr"])

    def test_positive_delta_still_diverges(self):
        res = self._scenario(corpus=10, cap=4320, allocation=3, max_turns=1,
                             extra_row_writer=True)
        self.assertEqual(res["rc"], R.EXIT_CAP_DIVERGENCE, res["stderr"][-800:])
        self.assertIn("RECONCILE DIVERGENCE", res["stderr"])
        self.assertIn("delta=+1", res["stderr"])
        self.assertNotIn("CAP GATE UNRECORDED", res["stderr"])

    def test_presend_refusal_unchanged(self):
        res = self._scenario(corpus=100, cap=100, allocation=3, max_turns=3)
        self.assertEqual(res["rc"], 4, res["stderr"][-800:])
        self.assertEqual(res["rows"], [], "a refusal must write NO row")
        self.assertEqual(res["calls"], 0, "the transport must never be called")
        self.assertIn("CAP REFUSED", res["stderr"])
        self.assertIn("projected=101", res["stderr"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
