"""LEDGER-KIND-RULE -- the recount and the attribution derive `spent` from ONE function.

The bug this guards: `request_ledger.classify()` counted an unrecognised kind (1, flagged
assumed_billed) while `run_a_star._row_counts()` returned False for every kind outside
{turn, tool-followup}. Both read the same rows files, so 30 `turn-initial` rows were inside
the ledger's total and outside the attribution's delta. RUN-A-STAR-2 was refused at gate 2
with zero requests sent (1176 + 115 == 1291 vs live 1321).

What is asserted here, all on real files or /tmp copies (never a mutation of the corpus):

  (a) for EVERY measure/rows-*.jsonl, the ledger recount == the attribution count, per file
      and in total -- the two numbers the grid compares;
  (b) one added `turn-initial` row moves BOTH numbers by exactly 1 (a one-sided move fails);
  (c) a `turn-initial` row renamed to an unknown kind REFUSES on both sides -- no silent
      unbill;
  (d) `tool_calls` is a row FIELD, not a kind: it adds no request to a row that already bills.

RED-GREEN: revert `run_a_star._row_counts` to `return True if kind is None else str(kind) in
("turn", "tool-followup")` and case (a) fails on the four files carrying `turn-initial`
(rows-cell-pointer-stable-20261027T004027Z, rows-cell-lease-reopen-20261027T004219Z,
...T024223Z, ...T084049Z, rows-cell-transcript-compact-20261027T004155Z,
rows-cell-transcript-grow-20261027T004129Z); revert `request_ledger.row_bills` to count
unknown kinds and case (c) fails on both sides.
"""

import glob
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ENG, "tools"))

import request_ledger as ledger          # noqa: E402
import run_a_star as launcher            # noqa: E402

MEAS = os.path.join(ENG, "measure")
ROWS = sorted(glob.glob(os.path.join(MEAS, "rows-*.jsonl")), key=os.path.basename)


def _rows_of(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _attribution(path):
    """run_a_star's side: the count it would contribute to attributed_delta."""
    return sum(1 for row in _rows_of(path) if launcher._row_counts(row))


def _recount(path):
    """request_ledger's side: the count it would contribute to `requests`."""
    entry = ledger.scan_file(path)
    return entry["requests"]


def _turn_initial_row():
    return {
        "ts": "2026-10-27T21:00:00.000Z",
        "kind": "turn-initial",
        "turn": 1,
        "content_sha256": "0" * 64,
        "prompt_tokens": 1,
        "completion_tokens": 1,
        "send_index": 0,
        "initial_send": True,
    }


def _fixture_with_extra_turn_initial(tmpdir):
    """A /tmp copy of one real file plus ONE synthetic turn-initial row."""
    src = os.path.join(MEAS, "rows-cell-lease-reopen-20261027T004219Z.jsonl")
    dst = os.path.join(tmpdir, os.path.basename(src))
    shutil.copyfile(src, dst)
    with open(dst, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(_turn_initial_row(), sort_keys=True) + "\n")
    return src, dst


class TestOneRulePerFile(unittest.TestCase):
    def test_every_rows_file_agrees(self):
        """(a) recount == attribution for every rows file, and in total."""
        if not ROWS:
            self.skipTest("no measure/rows-*.jsonl on disk")
        table, bad = [], []
        for path in ROWS:
            rec, att = _recount(path), _attribution(path)
            table.append((os.path.basename(path), rec, att))
            if rec != att:
                bad.append((os.path.basename(path), rec, att))
        total_rec = sum(t[1] for t in table)
        total_att = sum(t[2] for t in table)
        print("\n  per-file recount == attribution")
        for name, rec, att in table:
            print("    %-58s %4d %4d %s" % (name, rec, att, "OK" if rec == att else "DIFF"))
        print("    %-58s %4d %4d %s" % ("TOTAL", total_rec, total_att,
                                        "OK" if total_rec == total_att else "DIFF"))
        self.assertEqual(bad, [], "files where recount != attribution: %r" % (bad,))
        self.assertEqual(total_rec, total_att)

    def test_turn_initial_is_billed_by_both(self):
        """turn-initial is one wire request (run_longrun.py:2726-2729) on both sides."""
        row = _turn_initial_row()
        self.assertTrue(ledger.row_bills(row))
        self.assertTrue(launcher._row_counts(row))
        self.assertEqual(ledger.classify(row), (1, 0))

    def test_no_kind_is_counted_and_flagged(self):
        self.assertEqual(ledger.classify({}), (1, 1))
        self.assertTrue(launcher._row_counts({}))

    def test_suppression_markers_do_not_bill(self):
        for row in ({"billed": False}, {"billed": "false"},
                    {"followup_suppressed": True}, {"served_from": "prompt"}):
            row = dict(row, kind="turn")
            self.assertFalse(ledger.row_bills(row), row)
            self.assertFalse(launcher._row_counts(row), row)

    def test_tool_calls_field_adds_no_request(self):
        """(d) `tool_calls` is a row FIELD, not a kind: the turn row bills once."""
        row = dict(_turn_initial_row(), kind="turn",
                   tool_calls=[{"name": "fetch"}, {"name": "fetch"}])
        self.assertEqual(ledger.classify(row), (1, 0))
        self.assertTrue(launcher._row_counts(row))


class TestFixturesMoveBothNumbers(unittest.TestCase):
    def test_one_added_turn_initial_moves_both_by_one(self):
        """(b) a one-sided change is the STOP condition; both must move by exactly 1."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = _fixture_with_extra_turn_initial(tmp)
            self.assertEqual(_recount(dst) - _recount(src), 1,
                             "ledger recount did not move by 1")
            self.assertEqual(_attribution(dst) - _attribution(src), 1,
                             "attribution did not move by 1 (silent unbill)")
            # and the ledger's own totals agree too
            base = ledger.build_report([src], 4320, 0, 0)
            fix = ledger.build_report([dst], 4320, 0, 0)
            self.assertEqual(fix["requests"] - base["requests"], 1)
            self.assertEqual(fix["remaining"] - base["remaining"], -1)

    def test_unknown_kind_refuses_on_both_sides(self):
        """(c) renaming turn-initial -> unknown must REFUSE, never silently unbill."""
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = _fixture_with_extra_turn_initial(tmp)
            rows = _rows_of(dst)
            rows[-1]["kind"] = "turn-initial-typo"
            with open(dst, "w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
            with self.assertRaises(ledger.RowsUnreadable):
                ledger.scan_file(dst)
            self.assertNotEqual(ledger.main(["--glob", dst, "--cap", "4320",
                                             "--reserve", "0", "--would-spend", "0",
                                             "--quiet"]), 0)
            with self.assertRaises(SystemExit):
                launcher._row_counts({"kind": "turn-initial-typo"})
            with self.assertRaises(SystemExit):
                launcher.attributed_delta(0.0, rows_glob=dst)


if __name__ == "__main__":
    unittest.main(verbosity=2)
