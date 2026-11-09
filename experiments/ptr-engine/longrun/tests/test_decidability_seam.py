#!/usr/bin/env python3
"""Regression test for the DECIDABILITY-SEAM defect class.

THE OBSERVED CONTRADICTION (one conductor run, one row file):
  * grade_v5 reported a `decidable` count for the checkpoints;
  * analyze_stats printed `accuracy UNDECIDABLE (n=0 decidable turns)`.

Both were true of DIFFERENT populations: the grader grades checkpoint cells
(`grade_v5.py:_parsed_from_row` parses the answer out of `content` when the row's
`answer_kind` is null), while the analyser counted row-level `answer_kind`
(`analyze_stats.py:row_outcome`), and the v6 row file carries `answer_kind =
null` on every row plus 24 `tool-followup` rows. A record could therefore carry a
headline whose numerator and denominator came from different populations.

THE SECOND COPY (this unit's finding). `analyze_stats.accuracy_from_grade` kept
its OWN copy of the counting rule and that copy had drifted from the grader's:
it dropped `turn_missing` cells out of `failed`, so an arm with unanswered
checkpoints reported a smaller denominator than the grade document for the very
same cells (5/8 vs 5/19 in `measure/MATRIX-*.json`). `grade_v5.
decidable_population` is now the ONLY owner; the analyser calls it.

Red→green contract of this file:
  (a) the pre-fix behaviour is reproducible from the real rows (row-derived
      decidable == 0 while the grader grades cells);
  (b) after the fix the analyser prints `timing_n` and `graded_n` separately and
      takes the numerator/denominator from the shared helper — measured on a
      fixture where pass, fail, undecidable and an ungraded (`pass: null`) cell
      are all present;
  (c) cell.py exits 9 on the contradiction, and 0 with --allow-inconsistent;
  (d) a consistent cell exits 0 and the analysed numbers are the grader's;
  (e) the analyser does not re-derive the rule: it calls grade_v5's owner, and a
      `pass: null` cell is decided by neither side.

The original row file is never edited: it is copied into a temp dir first.
No request is sent: every cell run is `--offline`.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LOGRUN = os.path.dirname(HERE)
PTR = os.path.dirname(LOGRUN)
ROWS = os.path.join(PTR, "measure", "rows-longrun-v6-tools.jsonl")
FIXTURE = os.path.join(LOGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ANALYZE = os.path.join(LOGRUN, "analyze_stats.py")
CELL = os.path.join(LOGRUN, "cell.py")
ARM = "pointer-stable"

if LOGRUN not in sys.path:
    sys.path.insert(0, LOGRUN)
import analyze_stats  # noqa: E402
import grade_v5  # noqa: E402

# A hand-built cell set in which every verdict class is present at least once:
# one pass, one fail, one undecidable (a non-answer), one `turn_missing` fail and
# one cell with NO verdict at all (`pass: null`).  The decidable denominator is
# pass + fail == 3 of 5 cells; `missing` is inside `fail` (never added again) and
# the ungraded cell is undecidable, so an implementation that counts `len(cells)`
# (5) or that treats `pass: null` as a decision cannot pass this file.
MIXED_CELLS = [
    {"arm": ARM, "id": "cp.0.t12", "turn": 12, "verdict": "pass",
     "reason": "num_equal"},
    {"arm": ARM, "id": "cp.1.t24", "turn": 24, "verdict": "fail",
     "reason": "num_mismatch"},
    {"arm": ARM, "id": "cp.2.t46", "turn": 46, "verdict": "undecidable",
     "reason": "prose_only"},
    {"arm": ARM, "id": "cp.3.t58", "turn": 58, "verdict": "fail",
     "reason": "turn_missing"},
    {"arm": ARM, "id": "cp.4.t70", "turn": 70, "pass": None},
]


def _rows(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _grade_doc(path, cells=None):
    """A grade_v5-shaped document over explicit cells (default: MIXED_CELLS)."""
    cells = list(MIXED_CELLS if cells is None else cells)
    pop = grade_v5.decidable_population(cells)
    doc = {"grader": "grade_v5", "arms": {ARM: {
        "decidable": pop["decidable"], "passed": pop["passed"],
        "failed": pop["failed"], "missing": pop["missing"],
        "undecidable": pop["undecidable"], "cells": pop["cells"],
        "checkpoint_accuracy": "%d/%d" % (pop["passed"], pop["decidable"])}},
        "cells": cells}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return doc


def _stub_analyser(path, graded_n):
    """An analyser that writes a doc claiming `graded_n` graded checkpoints."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('''#!/usr/bin/env python3
import argparse, json, sys
GRADED = %d
ap = argparse.ArgumentParser()
ap.add_argument("--rows", nargs="+")
ap.add_argument("--json", default=None)
ap.add_argument("--grade", default=None)
a = ap.parse_args()
doc = {"n_rows": 72, "arms": {"%s": {
    "n_rows": 72,
    "ttft": {"input": 72, "used": 72, "dropped_null": 0, "dropped_unavailable": 0},
    "p50": {"point": 158.19, "lo": 146.19, "hi": 200.61, "n": 72},
    "p95": {"point": 435.27, "lo": 346.51, "hi": 529.89, "n": 72},
    "accuracy": {"source": "grade_v5", "timing_n": 72, "graded_n": GRADED,
                 "passed": 0, "failed": 0, "decidable": 0,
                 "undecidable": 0, "missing": 0}}}, "pairs": []}
if a.json:
    open(a.json, "w").write(json.dumps(doc))
print("stub analyser graded_n=%%d" %% GRADED)
''' % (graded_n, ARM))


class DecidabilitySeamTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="decidability-seam-")
        self.rows = os.path.join(self.tmp, "rows.jsonl")
        shutil.copyfile(ROWS, self.rows)          # the original is never touched
        self.grade_doc = os.path.join(self.tmp, "stub-grade.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------------------------------------------------------------- (a)
    def test_a_pre_fix_population_is_reproducible_from_real_rows(self):
        """The analyser's old population decides NOTHING on the real v6 rows."""
        rows = _rows(self.rows)
        self.assertEqual(len(rows), 72)
        # The row-level fields the analyser keyed on are null on EVERY row ...
        self.assertTrue(all(r.get("answer_kind") is None for r in rows))
        self.assertTrue(all(r.get("answer_value") is None for r in rows))
        outcomes = [analyze_stats.row_outcome(r) for r in rows]
        self.assertEqual(sum(1 for o in outcomes if o is not None), 0)
        # ... and the file is not one row per turn: 24 rows are tool follow-ups,
        # so a row-derived denominator would also have been the wrong SIZE.
        self.assertEqual(sum(1 for r in rows if r.get("kind") == "tool-followup"), 24)
        # Pre-fix headline, without a grade input: still n=0 (the old behaviour).
        proc = self._analyze()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("UNDECIDABLE", proc.stdout)
        self.assertIn("graded_n = 0", proc.stdout)

    # ---------------------------------------------------------------- (b)
    def test_b_analyser_takes_the_shared_decidable_population(self):
        _grade_doc(self.grade_doc)
        out_json = os.path.join(self.tmp, "analysis.json")
        proc = self._analyze("--grade", self.grade_doc, "--json", out_json)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("timing_n = 72", proc.stdout)
        self.assertIn("graded_n = 5", proc.stdout)
        # decidable = pass(1) + fail(2, one of them turn_missing); the prose cell
        # and the `pass: null` cell are undecidable and outside the denominator.
        self.assertIn(
            "accuracy = 1/3 (pass 1, fail 2, undecidable 2, missing 1)", proc.stdout)
        # A bare UNDECIDABLE beside a graded 1/3 is impossible now.
        acc_lines = [l for l in proc.stdout.splitlines() if "accuracy =" in l
                     and "wilson" not in l]
        self.assertEqual(len(acc_lines), 1)
        self.assertNotIn("UNDECIDABLE", acc_lines[0])
        with open(out_json, encoding="utf-8") as fh:
            doc = json.load(fh)
        acc = doc["arms"][ARM]["accuracy"]
        self.assertEqual((acc["source"], acc["graded_n"], acc["timing_n"],
                          acc["passed"], acc["failed"], acc["decidable"],
                          acc["missing"], acc["undecidable"]),
                         ("grade_v5", 5, 72, 1, 2, 3, 1, 2))

    # ---------------------------------------------------------------- (c)
    def test_c_cell_exits_9_on_the_contradiction_and_0_with_override(self):
        grader_n = self._real_decidable()
        self.assertGreater(grader_n, 0)
        stub = os.path.join(self.tmp, "stub_analyse.py")
        _stub_analyser(stub, graded_n=0)
        out_dir = os.path.join(self.tmp, "measure")
        env = dict(os.environ, CELL_ANALYZE_PATH=stub)

        bad = self._cell(out_dir, env)
        self.assertEqual(bad.returncode, 9, bad.stdout + bad.stderr)
        self.assertIn("REFUSED(9)", bad.stdout)
        self.assertIn("grader decidable=%d" % grader_n, bad.stdout)
        self.assertIn("analyser graded_n=0", bad.stdout)
        self.assertIn("grade_v5.py:653", bad.stdout)
        self.assertIn("analyze_stats.py:457", bad.stdout)

        ok = self._cell(out_dir + "-override", env, "--allow-inconsistent")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("6b/7 consistency OVERRIDDEN", ok.stdout)
        records = [n for n in os.listdir(out_dir + "-override")
                   if n.startswith("cell-%s-" % ARM) and n.endswith(".json")
                   and ".analysis." not in n and ".grade-" not in n]
        self.assertEqual(len(records), 1, records)
        with open(os.path.join(out_dir + "-override", records[0]),
                  encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertTrue(rec["consistency"]["override"])
        self.assertTrue(rec["consistency"]["contradictory"])
        self.assertEqual(rec["consistency"]["grader_decidable"], grader_n)
        self.assertEqual(rec["consistency"]["analyser_graded_n"], 0)

    # ---------------------------------------------------------------- (d)
    def test_d_consistent_cell_exits_0(self):
        """The real grader and the real (fixed) analyser agree → exit 0."""
        out_dir = os.path.join(self.tmp, "measure-consistent")
        proc = self._cell(out_dir, dict(os.environ))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        arm = self._real_arms()
        self.assertIn("6b/7 consistency ok", proc.stdout)
        self.assertIn("grader decidable=%d" % arm["decidable"], proc.stdout)
        self.assertIn("analyser graded_n=%d" % arm["cells"], proc.stdout)
        # cell.py gates on the analyser's JSON; the both-ns line lands in the
        # recorded markdown (the analysis is reproduced there verbatim). The
        # analysed numerator/denominator ARE the grader's - one owner, one number.
        md = [n for n in os.listdir(out_dir) if n.endswith(".md")]
        self.assertEqual(len(md), 1, md)
        with open(os.path.join(out_dir, md[0]), encoding="utf-8") as fh:
            recorded = fh.read()
        self.assertIn("timing_n = 72", recorded)
        self.assertIn("graded_n = %d" % arm["cells"], recorded)
        self.assertIn(
            "accuracy = %d/%d (pass %d, fail %d, undecidable %d, missing %d)"
            % (arm["passed"], arm["decidable"], arm["passed"], arm["failed"],
               arm["undecidable"], arm["missing"]), recorded)

    # ---------------------------------------------------------------- (e)
    def test_e_shared_helper_owns_the_number(self):
        """The analyser calls grade_v5's owner instead of recomputing the rule."""
        self.assertIs(analyze_stats.grade_v5, grade_v5)
        self.assertIs(analyze_stats.grade_v5.decidable_population,
                      grade_v5.decidable_population)
        pop = grade_v5.decidable_population(MIXED_CELLS)
        self.assertEqual(pop["cells"], 5)
        self.assertEqual(pop["decidable"], 3)        # pass 1 + fail 2
        self.assertEqual(pop["missing"], 1)          # inside fail, not added again
        self.assertEqual(pop["undecidable"], 2)      # prose cell AND the pass:null
        self.assertNotEqual(pop["decidable"], pop["cells"])   # len(cells) inflates
        acc = analyze_stats.accuracy_from_grade({"cells": MIXED_CELLS,
                                                 "arms": {}}, ARM)
        self.assertEqual(acc["decidable"], pop["decidable"])
        self.assertEqual(acc["decidable_source"], grade_v5.DECIDABLE_SOURCE)
        # An ungraded (`pass: null`) cell decides nothing on either side.
        null_only = [c for c in MIXED_CELLS if "verdict" not in c]
        self.assertEqual(len(null_only), 1)
        self.assertEqual(grade_v5.decidable_population(null_only)["decidable"], 0)
        self.assertEqual(
            analyze_stats.accuracy_from_grade(
                {"cells": null_only, "arms": {}}, ARM)["decidable"], 0)
        # The grader's own arms block is the same owner's output, not a third copy.
        doc = _grade_doc(os.path.join(self.tmp, "mixed.json"))
        self.assertEqual(doc["arms"][ARM]["decidable"], pop["decidable"])

    # ------------------------------------------------------------- helpers
    def _real_arms(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            fixture = json.load(fh)
        return grade_v5.grade_rows(fixture, _rows(self.rows))["arms"][ARM]

    def _real_decidable(self):
        return self._real_arms()["decidable"]

    def _analyze(self, *extra):
        return subprocess.run(
            [sys.executable, ANALYZE, "--rows", self.rows] + list(extra),
            capture_output=True, text=True, timeout=300)

    def _cell(self, out_dir, env, *extra):
        return subprocess.run(
            [sys.executable, CELL, "--arm", ARM, "--fixture", FIXTURE,
             "--offline", self.rows, "--out-dir", out_dir,
             "--no-cell-handoff"] + list(extra),
            capture_output=True, text=True, timeout=600, env=env)


if __name__ == "__main__":
    unittest.main(verbosity=2)
