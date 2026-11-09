#!/usr/bin/env python3
"""test_budget_turn_scope.py - the budget stage and the run stage scope turns ALIKE.

WHY THIS EXISTS (unit BUDGET-STAGE-MAX-TURNS, measured): `LIVE-CANARY-4ARM` was refused
at exit 8 with zero requests. The dry-run preview priced the canary at 12 turns (720 s of
the canary's 900 s wall) and said ALLOW; the live launch refused the same cell at 2880 s.
Two argv builders disagreed about the cell's own shape:

  * `stage_run`   (cell.py:1557-1565 at the time of writing) reads
    ``n_turns = int(args.turns or 0)``, ``truncated = bool(n_turns and fixture_n and
    n_turns != fixture_n)`` and then appends ``--max-turns <n_turns>``;
  * `stage_budget` (cell.py:354-...) built its ``--dry-run`` argv WITHOUT it, so the
    runner priced the fixture's own N (48), and G2's budget-derived request count was 4x
    the cell that would actually run.

Nothing asserted that the two builders agree. This test does, from the OUTSIDE: it reads
the argv each one hands to a stub runner and requires

  * NON-full cell (--turns differs from the fixture's N): BOTH pass --max-turns <n>, and
    the budget stage's priced request count is the CELL's, not the fixture's;
  * FULL cell (--turns == fixture's N): NEITHER passes --max-turns, and the fixture's
    price is unchanged.

The test can FAIL, and does: remove the forward from either builder and the matching case
goes red. It is pointed at a mutated copy with CELL_UNDER_TEST=<path to cell.py>
(see the unit's journal for the red run).

Every case is OFFLINE: the runner is a stub that prints a price and records its argv.
No request is sent, no socket is opened, no --base-url is passed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PTR_ENGINE = os.path.dirname(LONGRUN)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))

# CELL_UNDER_TEST lets a red run point the same assertions at a mutated copy.
CELL = os.environ.get("CELL_UNDER_TEST") or os.path.join(LONGRUN, "cell.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
REAL_PROJECTION = os.path.join(PTR_ENGINE, "measure", "PROJECTION.json")
REAL_PREREG = os.path.join(PTR_ENGINE, "measure", "PREREG-ARM-RUN.json")
ARM = "pointer-stable"
PY = sys.executable
SEP = "\x1f"          # argv field separator in the stub's log


def _stub_runner(tmp):
    """A runner stub: on --dry-run it prices the FIXTURE's N (today's run_dry behaviour)
    and records its argv; on a live call it records its argv and returns."""
    path = os.path.join(tmp, "stub_runner.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "import os, sys\n"
            "argv = sys.argv[1:]\n"
            "log = os.environ['BST_ARGV_LOG']\n"
            "with open(log, 'a', encoding='utf-8') as fh:\n"
            "    fh.write(('dry' if '--dry-run' in argv else 'live') + '\\t'\n"
            "             + '\\x1f'.join(argv) + '\\n')\n"
            "if '--dry-run' in argv:\n"
            "    print('  %s      turn_requests=48 (N=48 x reps=1)  "
            "digest_requests=0  cell_total=48')\n"
            "    print('  would_send_total=48')\n"
            "sys.exit(0)\n" % ARM)
    return path


def _fake_ledger(tmp, cap=4320, spent=0):
    rows = os.path.join(tmp, "rows-scope.jsonl")
    with open(rows, "w", encoding="utf-8") as fh:
        for i in range(spent):
            fh.write(json.dumps({"kind": "turn", "turn": i + 1,
                                 "prompt_tokens": 100}) + "\n")
    doc = {"unit": "REQUEST-LEDGER", "rule": "test fixture", "counting": {},
           "total": {"files": 1, "rows": spent, "requests": spent,
                     "assumed_billed": 0},
           "budget": {"cap": cap, "reserve": 0, "headroom": cap, "spent": spent,
                      "would_spend": 0, "projected": spent, "remaining": cap - spent,
                      "within_budget": True},
           "files": [{"file": rows, "sha256": "0" * 64, "rows": spent,
                      "requests": spent, "assumed_billed": 0, "first_ts": None,
                      "last_ts": None}],
           "suppressed": []}
    path = os.path.join(tmp, "ledger.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    return path


def _invoke(tmp, turns):
    """Run ONE live cell (stub runner) and return its two argvs plus its own log."""
    runner = _stub_runner(tmp)
    ledger = _fake_ledger(tmp)
    log = os.path.join(tmp, "argv.log")
    out = os.path.join(tmp, "out")
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ)
    env.update({"CELL_RUNNER_PATH": runner, "BST_ARGV_LOG": log,
                "CELL_LEDGER_ARTEFACT": ledger,
                "CELL_PROJECTION_ARTEFACT": REAL_PROJECTION,
                "CELL_PREREG_ARTEFACT": REAL_PREREG})
    argv = [PY, CELL, "--arm", ARM, "--fixture", FIXTURE, "--turns", str(turns),
            "--reps", "1", "--budget", "1000", "--max-wall", "3600",
            "--hypothesis", "H2", "--out-dir", out, "--no-cell-handoff"]
    proc = subprocess.run(argv, capture_output=True, text=True, env=env,
                          cwd=ROOT, timeout=300)
    text = proc.stdout + proc.stderr
    dry = live = None
    if os.path.exists(log):
        with open(log, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for line in lines:
            kind, _, rest = line.partition("\t")
            fields = rest.split(SEP) if rest else []
            if kind == "dry":
                dry = fields
            else:
                live = fields
    return {"dry": dry, "live": live, "log": text, "rc": proc.returncode}


def _max_turns(argv):
    """The value of --max-turns in `argv`, or None when the flag is absent."""
    if not argv or "--max-turns" not in argv:
        return None
    i = argv.index("--max-turns")
    assert i + 1 < len(argv), "argv carries --max-turns with no value: %r" % (argv,)
    return argv[i + 1]


def _price(log):
    import re
    m = re.search(r"would_send_total=(\d+)", log)
    return int(m.group(1)) if m else None


class BudgetTurnScope(unittest.TestCase):
    """The two argv builders must agree about turn scoping, in both directions."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="budget-turn-scope-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_partial_cell_both_builders_scope_the_same_turns(self):
        """--turns 12 on an N=48 fixture: BOTH builders say --max-turns 12, and the
        price is the cell's 12, not the fixture's 48."""
        rec = _invoke(self.tmp, turns=12)
        self.assertIsNotNone(rec["dry"],
                             "the budget stage never invoked the runner:\n%s"
                             % rec["log"][-3000:])
        self.assertEqual(_max_turns(rec["dry"]), "12",
                         "stage_budget did not scope the dry run to the cell's 12 "
                         "turns: %r\n%s" % (rec["dry"], rec["log"][-3000:]))
        self.assertIsNotNone(rec["live"],
                             "the run stage never invoked the runner:\n%s"
                             % rec["log"][-3000:])
        self.assertEqual(_max_turns(rec["live"]), "12",
                         "stage_run did not scope the live run to 12 turns: %r"
                         % (rec["live"],))
        self.assertEqual(_price(rec["log"]), 12,
                         "the budget stage priced the fixture, not the cell: %s\n%s"
                         % (_price(rec["log"]), rec["log"][-3000:]))

    def test_full_cell_scopes_nothing(self):
        """--turns 48 == the fixture's N: NEITHER builder passes --max-turns, and the
        fixture's price is untouched."""
        rec = _invoke(self.tmp, turns=48)
        self.assertIsNotNone(rec["dry"], rec["log"][-3000:])
        self.assertIsNone(_max_turns(rec["dry"]),
                          "stage_budget scoped a cell that IS the whole fixture: %r"
                          % (rec["dry"],))
        self.assertIsNotNone(rec["live"], rec["log"][-3000:])
        self.assertIsNone(_max_turns(rec["live"]),
                          "stage_run scoped a cell that IS the whole fixture: %r"
                          % (rec["live"],))
        self.assertEqual(_price(rec["log"]), 48,
                         "the full cell's price moved: %s" % (_price(rec["log"]),))

    def test_the_two_builders_agree_about_turn_scoping(self):
        """The asymmetry itself: for the same cell the two argvs must agree on whether
        the cell is truncated. This is the assertion the unit exists for -- a shape
        disagreement is red even when each builder is internally consistent."""
        for turns in (12, 24, 48):
            with self.subTest(turns=turns):
                sub = os.path.join(self.tmp, "t%d" % turns)
                os.makedirs(sub, exist_ok=True)
                rec = _invoke(sub, turns=turns)
                a, b = _max_turns(rec["dry"]), _max_turns(rec["live"])
                self.assertEqual(a, b,
                                 "the budget stage and the run stage disagree about "
                                 "turn scoping at --turns %d: dry=%r live=%r\n%s"
                                 % (turns, a, b, rec["log"][-3000:]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
