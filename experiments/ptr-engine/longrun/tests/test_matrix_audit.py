"""Tests for experiments/ptr-engine/tools/matrix_audit.py (unit MATRIX-HONESTY).

Every test is offline: the only judge is det_verify (AST ground truth) over files
already on disk.  Each of the four contracted checks is red before the audit
distinguishes a missing cell from a failed one and green after:

(a) a green run over the real grid exits 0 without --strict;
(b) a crafted grid with one cell removed reports missing_* with the right reason,
    the per-state counts shift by exactly one, and the accuracy line gains the
    PARTIAL GRID marker;
(c) --strict exits non-zero on the crafted incomplete grid and zero on a
    complete one;
(d) a graded undecidable cell is never counted as pass or as fail.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, TOOLS)

import matrix_audit as M  # noqa: E402

PARTIAL = "\u2013 PARTIAL GRID"
ACC_RE = re.compile(
    r"^(?P<label>.+?) (?P<passed>\d+)/(?P<dec>\d+) "
    r"\(pass (?P<pass>\d+), fail (?P<fail>\d+), missing (?P<missing>\d+), "
    r"undecidable (?P<undec>\d+)\)( – PARTIAL GRID)?$")


class RealGridTest(unittest.TestCase):
    """(a) the real grid, read-only, green."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.result = M.audit()
        cls.rc = M.main(["--out", os.path.join(cls.tmp, "coverage.json")])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_declared_space_is_92_and_explained(self):
        d = self.result["declared_space"]
        self.assertEqual(d["cells"], 92)
        self.assertEqual(d["run_arm_pairs"], 23)
        self.assertEqual(len(d["checkpoints"]), 4)
        self.assertEqual(d["formula"], "23 run/arm pairs x 4 checkpoint ids x 1 rep = 92 cells")
        self.assertEqual(len(self.result["cells"]), 92)

    def test_exit_zero_without_strict(self):
        self.assertEqual(self.rc, 0)

    def test_states_partition_the_grid(self):
        states = self.result["states"]
        self.assertEqual(states["cells"], 92)
        self.assertEqual(sum(states[s] for s in M.STATES), 92)
        self.assertEqual(states["pass"], 5)
        self.assertEqual(states["fail"], 38)
        self.assertEqual(states["undecidable"], 13)
        missing = sum(states[s] for s in M.MISSING_STATES)
        self.assertEqual(missing, 36)
        # the 36 the regrade called "missing" split into two distinct causes
        self.assertEqual(states["missing_turn_absent"] + states["missing_answer_empty"], 36)
        self.assertGreater(states["missing_answer_empty"], 0)
        self.assertGreater(states["missing_turn_absent"], 0)

    def test_every_accuracy_line_obeys_the_denominator_rule(self):
        acc = self.result["accuracy"]
        lines = [acc["overall"]] + list(acc["per_arm"].values()) + \
                list(acc["per_run_arm"].values())
        for line in lines:
            m = ACC_RE.match(line)
            self.assertIsNotNone(m, "malformed accuracy line: %r" % line)
            g = m.groupdict()
            self.assertEqual(int(g["dec"]), int(g["pass"]) + int(g["fail"]))
            self.assertEqual(int(g["passed"]), int(g["pass"]))
            if int(g["missing"]) + int(g["undec"]):
                self.assertTrue(line.endswith(PARTIAL), line)
        self.assertIn("PARTIAL GRID", acc["overall"])

    def test_no_cell_is_unnamed(self):
        for cell in self.result["cells"]:
            self.assertIn(cell["state"], M.STATES)
            self.assertTrue(cell["reason"], cell)


class CraftedGridTest(unittest.TestCase):
    """(b)(c) a crafted grid, complete and with one cell removed."""

    CP_TEXT = {
        12: "ANSWER: 64",
        24: "ANSWER: 31",
        46: ("ANSWER: the code calls ledger.record_refusal with scope, "
             "serialized_ref and code before re-raising"),
    }

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rows = os.path.join(self.tmp, "rows")
        os.makedirs(self.rows)
        with open(M.det_verify.FIXTURE, encoding="utf-8") as fh:
            fixture = json.load(fh)
        fixture.pop("repair", None)  # 3 declared checkpoints, no undecidable slot
        self.fixture = os.path.join(self.tmp, "fixture.json")
        with open(self.fixture, "w", encoding="utf-8") as fh:
            json.dump(fixture, fh)
        self.path = os.path.join(self.rows, "rows-longrun-craft.jsonl")
        self.write_rows([12, 24, 46])
        # The declared arm population comes from a manifest, never from the rows.
        self.mdir = os.path.join(self.tmp, "manifests")
        os.makedirs(self.mdir)
        self.manifests = os.path.join(self.mdir, "*.json")
        self.declare("pointer-stable")

    def declare(self, *arms):
        """Write one run manifest per arm, pairing it with the crafted rows path."""
        for i, arm in enumerate(arms):
            with open(os.path.join(self.mdir, "craft-%d.json" % i), "w",
                      encoding="utf-8") as fh:
                json.dump({"arm": arm, "rows_path": self.path, "dry_run": False,
                           "rep": 1}, fh)

    def audit(self):
        return M.audit(self.rows, self.fixture, manifests=self.manifests)

    def main(self, *extra):
        return M.main(["--rows-dir", self.rows, "--fixture", self.fixture,
                       "--manifests", self.manifests,
                       "--out", os.path.join(self.tmp, "audit.json")] + list(extra))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_rows(self, turns):
        with open(self.path, "w", encoding="utf-8") as fh:
            for turn in turns:
                fh.write(json.dumps({
                    "arm": "pointer-stable", "task_id": "LR-01", "rep": 1,
                    "turn": turn, "kind": "turn", "content": self.CP_TEXT[turn],
                }) + "\n")

    def test_complete_grid_is_complete(self):
        result = self.audit()
        self.assertEqual(result["declared_space"]["cells"], 3)
        self.assertEqual(result["states"]["pass"], 3)
        self.assertEqual(sum(result["states"][s] for s in M.MISSING_STATES), 0)
        line = result["accuracy"]["per_arm"]["pointer-stable"]
        self.assertEqual(line, "pointer-stable 3/3 (pass 3, fail 0, missing 0, undecidable 0)")
        self.assertNotIn("PARTIAL GRID", line)

    def test_removed_cell_is_missing_not_failed(self):
        before = self.audit()
        self.write_rows([24, 46])  # one cell removed
        after = self.audit()

        gone = [c for c in after["cells"] if c["turn"] == 12][0]
        self.assertEqual(gone["state"], "missing_turn_absent")
        self.assertIn("turn 12", gone["reason"])
        self.assertIn("no row", gone["reason"])

        # counts shift by exactly one: pass -> missing_turn_absent
        self.assertEqual(after["states"]["pass"], before["states"]["pass"] - 1)
        self.assertEqual(after["states"]["fail"], before["states"]["fail"])
        self.assertEqual(after["states"]["missing_turn_absent"],
                         before["states"]["missing_turn_absent"] + 1)
        self.assertEqual(after["states"]["missing_answer_empty"],
                         before["states"]["missing_answer_empty"])
        self.assertEqual(sum(after["states"][s] for s in M.STATES), 3)

        line = after["accuracy"]["per_arm"]["pointer-stable"]
        self.assertTrue(line.endswith(PARTIAL), line)
        self.assertIn("2/2 (pass 2, fail 0, missing 1, undecidable 0)", line)

    def test_empty_content_is_answer_empty_not_turn_absent(self):
        self.write_rows_with_empty_24()
        result = self.audit()
        cell = [c for c in result["cells"] if c["turn"] == 24][0]
        self.assertEqual(cell["state"], "missing_answer_empty")
        self.assertIn("empty content", cell["reason"])

    def write_rows_with_empty_24(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            for turn in (12, 46):
                fh.write(json.dumps({"arm": "pointer-stable", "task_id": "LR-01",
                                     "rep": 1, "turn": turn, "kind": "turn",
                                     "content": self.CP_TEXT[turn]}) + "\n")
            fh.write(json.dumps({"arm": "pointer-stable", "task_id": "LR-01", "rep": 1,
                                 "turn": 24, "kind": "turn", "content": "   "}) + "\n")

    def test_strict_exits_nonzero_only_when_incomplete(self):
        self.assertEqual(self.main("--strict"), 0)
        self.write_rows([24, 46])
        self.assertEqual(self.main("--strict"), 1)


class UndecidableTest(unittest.TestCase):
    """(d) a graded undecidable cell is never a pass and never a fail."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.result = M.audit()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_graded_undecidable_is_its_own_state(self):
        answered = [c for c in self.result["cells"]
                    if c["checkpoint"] == "repair.t30" and c.get("answer_chars")]
        self.assertEqual(len(answered), 13)
        for cell in answered:
            self.assertEqual(cell["state"], "undecidable", cell)
            self.assertEqual(cell["reason"], "undecidable")
        self.assertFalse([c for c in self.result["cells"]
                          if c["checkpoint"] == "repair.t30"
                          and c["state"] in ("pass", "fail")])

    def test_denominator_excludes_undecidable(self):
        states = self.result["states"]
        line = self.result["accuracy"]["overall"]
        m = ACC_RE.match(line)
        self.assertEqual(int(m.group("dec")), states["pass"] + states["fail"])
        self.assertEqual(int(m.group("undec")), states["undecidable"])
        self.assertNotIn(states["undecidable"], (states["pass"], states["fail"]))
        self.assertEqual(states["pass"] + states["fail"], 43)


    def test_declared_population_comes_from_outside_the_rows(self):
        d = self.result["declared_space"]["declaration"]
        self.assertGreater(d["arm_registry"]["line"], 0)
        self.assertIn("ARMS", d["arm_registry"]["why_authoritative"])
        self.assertEqual(sorted(d["arm_registry"]["arms"]),
                         ["bounded-context-fetch", "lease-reopen",
                          "masking-no-fetch", "pointer-stable", "spcc",
                          "transcript-compact", "transcript-grow"])
        self.assertEqual(d["declaration_gaps"], [])
        self.assertEqual(d["run_manifests"]["arms_source_by_file"],
                         {k: "manifest" for k in
                          d["run_manifests"]["arms_by_file"]})

    def test_no_cell_on_disk_is_extraneous(self):
        # (e) the corrected figures do not move, and nothing on disk is undeclared
        self.assertEqual(self.result["declared_cells"], 92)
        self.assertEqual(self.result["states"]["cells"], 92)
        self.assertEqual(self.result["states"]["extraneous_cell"], 0)
        self.assertEqual(self.result["extraneous"], [])
        self.assertEqual(len(self.result["declared_space"]["runs"]), 9)
        self.assertEqual(self.result["declared_space"]["run_arm_pairs"], 23)


class DeclaredSpaceTest(unittest.TestCase):
    """(a)-(d) an injected cell is extraneous; a declared-but-unrun cell is not."""

    CP_TEXT = CraftedGridTest.CP_TEXT

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.rows = os.path.join(self.tmp, "rows")
        self.mdir = os.path.join(self.tmp, "manifests")
        os.makedirs(self.rows)
        os.makedirs(self.mdir)
        with open(M.det_verify.FIXTURE, encoding="utf-8") as fh:
            fixture = json.load(fh)
        fixture.pop("repair", None)
        self.fixture = os.path.join(self.tmp, "fixture.json")
        with open(self.fixture, "w", encoding="utf-8") as fh:
            json.dump(fixture, fh)
        self.path = os.path.join(self.rows, "rows-longrun-inject.jsonl")
        self.write(self.rows_for("pointer-stable"))
        self.declare("pointer-stable")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rows_for(self, arm, turns=(12, 24, 46)):
        return [{"arm": arm, "task_id": "LR-01", "rep": 1, "turn": t,
                 "kind": "turn", "content": self.CP_TEXT[t]} for t in turns]

    def write(self, rows):
        with open(self.path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")

    def declare(self, *arms):
        for i, arm in enumerate(arms):
            with open(os.path.join(self.mdir, "craft-%d.json" % i), "w",
                      encoding="utf-8") as fh:
                json.dump({"arm": arm, "rows_path": self.path, "rep": 1,
                           "dry_run": False}, fh)

    def audit(self):
        return M.audit(self.rows, self.fixture, manifests=self.manifests)

    @property
    def manifests(self):
        return os.path.join(self.mdir, "*.json")

    def main(self):
        return M.main(["--rows-dir", self.rows, "--fixture", self.fixture,
                       "--manifests", self.manifests,
                       "--out", os.path.join(self.tmp, "audit.json")])

    def test_a_fabricated_arm_is_extraneous_and_exits_11(self):
        self.write(self.rows_for("pointer-stable-2"))
        result = self.audit()
        # one extraneous cell per undeclared arm, carrying the rows it was seen in
        self.assertEqual(result["states"]["extraneous_cell"], 1)
        self.assertEqual(result["extraneous"][0]["rows"], 3)
        self.assertEqual({c["arm"] for c in result["extraneous"]},
                         {"pointer-stable-2"})
        self.assertEqual({c["kind"] for c in result["extraneous"]}, {"arm"})
        for cell in result["extraneous"]:
            self.assertEqual(cell["state"], "extraneous_cell")
            self.assertFalse(cell["declared"])
            self.assertIn("no declaration admits it", cell["reason"])
        # the declared, unrun arm is missing — never extraneous
        self.assertEqual(result["states"]["missing_turn_absent"], 3)
        self.assertEqual(result["declared_cells"], 3)
        self.assertEqual(self.main(), 11)

    def test_b_undeclared_checkpoint_id_is_extraneous_and_exit_11(self):
        rows = self.rows_for("pointer-stable")
        rows.append({"arm": "pointer-stable", "task_id": "LR-01", "rep": 1,
                     "turn": 99, "kind": "checkpoint", "is_checkpoint": True,
                     "checkpoint": "cp.99.t99", "content": "ANSWER: 7"})
        self.write(rows)
        result = self.audit()
        self.assertEqual(result["states"]["extraneous_cell"], 1)
        extra = result["extraneous"][0]
        self.assertEqual(extra["kind"], "checkpoint")
        self.assertEqual(extra["checkpoint"], "cp.99.t99")
        self.assertIn("cp.99.t99", extra["reason"])
        self.assertIn("cp.99.t99", [c["label"] for c in result["extraneous"]])
        self.assertEqual(result["declared_cells"], 3)
        self.assertEqual(self.main(), 11)

    def test_c_clean_matrix_exits_0(self):
        self.assertEqual(self.audit()["states"]["extraneous_cell"], 0)
        self.assertEqual(self.main(), 0)

    def test_d_declared_but_unrun_arm_is_missing_never_extraneous(self):
        self.declare("pointer-stable", "transcript-grow")
        result = self.audit()
        self.assertEqual(result["declared_cells"], 6)
        self.assertEqual(result["states"]["extraneous_cell"], 0)
        self.assertEqual(result["states"]["missing_turn_absent"], 3)
        gone = [c for c in result["cells"] if c["arm"] == "transcript-grow"]
        for cell in gone:
            self.assertEqual(cell["state"], "missing_turn_absent")
        self.assertEqual(self.main(), 0)


if __name__ == "__main__":
    unittest.main()
