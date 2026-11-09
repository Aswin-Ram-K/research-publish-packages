"""Tests for experiments/ptr-engine/tools/parm1_errata_check.py (PARM-1-ERRATA).

One green case and five red cases. The red cases are the point: each mutates a single
claim in a *temporary copy* of the errata (or, for the threshold test, a temporary copy of
the frozen rule) and asserts that the check exits non-zero naming that claim. Nothing here
edits docs/PREREG-ARM-RUN.md, the fixture, any grade file or any rows file.

    python3 -m pytest experiments/ptr-engine/longrun/tests/test_parm1_errata.py -q
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOL = os.path.join(ROOT, "experiments", "ptr-engine", "tools", "parm1_errata_check.py")
ERRATA = os.path.join(ROOT, "docs", "PARM-1-ERRATA.md")
PREREG = os.path.join(ROOT, "docs", "PREREG-ARM-RUN.md")
TVS = os.path.join(ROOT, "docs", "TVS.md")
FIXTURE = os.path.join(ROOT, "experiments", "ptr-engine", "longrun", "tasks-v6", "LR-01.v7.json")

sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine", "tools"))

import parm1_errata_check as pec  # noqa: E402


def run(*args):
    proc = subprocess.run([sys.executable, TOOL] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def mutated_errata(old, new, name="PARM-1-ERRATA.mutated.md"):
    """Copy the errata with one claim string rewritten; returns the copy's path."""
    with open(ERRATA, encoding="utf-8") as fh:
        text = fh.read()
    assert text.count(old) == 1, "mutation anchor must occur exactly once: %r" % (old,)
    path = os.path.join(tempfile.mkdtemp(prefix="parm1-errata-"), name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new))
    return path


class GreenCase(unittest.TestCase):
    def test_check_passes_on_the_real_errata(self):
        rc, out = run()
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS parm1 errata check", out)
        self.assertIn("frozen bytes intact", out)
        # the three things the end report has to name
        self.assertIn("9 substantive", out)
        self.assertIn("3 NONE", out)
        self.assertIn("repair.t30 excluded", out)

    def test_census_recomputes_to_12_9_3(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            c = pec.census(json.load(fh))
        self.assertEqual(c["ids_total"], 12)
        self.assertEqual(c["ids_substantive"], 9)
        self.assertEqual(c["ids_none"], 3)
        self.assertEqual(c["ids_by_kind"], {"NUM": 5, "CALL": 4, "NONE": 3})
        self.assertEqual(c["none_ids"], ["cp.10.t42", "cp.3.t14", "cp.5.t20"])
        self.assertEqual(c["decidable_fixture"], 12)


class RedCases(unittest.TestCase):
    def test_red_errata_claiming_12_of_12_substantive_fails(self):
        """The contracted red case: '12/12 substantive' must not pass."""
        rc, out = run("--errata", mutated_errata('"ids_substantive": 9',
                                                 '"ids_substantive": 12'))
        self.assertEqual(rc, 1, out)
        self.assertIn("CLAIM ids_substantive = 12", out)
        self.assertIn("FAIL", out)

    def test_red_tvs_denominator_written_as_12_fails(self):
        rc, out = run("--errata", mutated_errata('"tvs_denominator": 3',
                                                 '"tvs_denominator": 12'))
        self.assertEqual(rc, 1, out)
        self.assertIn("CLAIM tvs_denominator = 12", out)
        self.assertIn("different claim", out)

    def test_red_relabelled_none_ids_fail(self):
        rc, out = run("--errata", mutated_errata('"cp.10.t42"]', '"cp.11.t46"]'))
        self.assertEqual(rc, 1, out)
        self.assertIn("CLAIM none_ids", out)

    def test_red_repair_t30_claimed_scored_fails(self):
        rc, out = run("--errata", mutated_errata('"rep_t30_scored": false',
                                                 '"rep_t30_scored": true'))
        self.assertEqual(rc, 1, out)
        self.assertIn("CLAIM rep_t30_scored", out)

    def test_red_invented_denominator_key_fails(self):
        rc, out = run("--errata", mutated_errata('"h3_denominator": 12,',
                                                 '"h3_denominator": 12, "ids_semantic_v2": 11,'))
        self.assertEqual(rc, 1, out)
        self.assertIn("cannot recompute", out)
        self.assertIn("ids_semantic_v2", out)

    def test_red_threshold_change_in_a_frozen_copy_fails(self):
        """A moved threshold fails even though the errata itself is untouched."""
        with open(PREREG, encoding="utf-8") as fh:
            text = fh.read()
        old = "= 16.7 percentage points"
        self.assertEqual(text.count(old), 1)
        path = os.path.join(tempfile.mkdtemp(prefix="parm1-prereg-"), "PARM-1-rule.mutated.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(old, "= 20.0 percentage points"))
        rc, out = run("--prereg", path)
        self.assertEqual(rc, 1, out)
        self.assertIn("frozen body moved", out)
        self.assertIn("threshold phrases missing", out)


if __name__ == "__main__":
    unittest.main()
