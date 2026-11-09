#!/usr/bin/env python3
"""Tests for tools/gate_ledger.py -- the gate ledger must be countable, not asserted.

Red->green here is structural: every red case mutates a copy of the SHIPPED artefact in a
temp dir and asserts the check fails for the RIGHT reason; the green case runs the shipped
artefact unchanged. The tool is exercised as a subprocess so its exit code is the thing
under test, not a Python return value.

Offline: 0 requests, 0 sockets, temp-dir writes only.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
TOOL = os.path.join(REPO_ROOT, "experiments", "ptr-engine", "tools", "gate_ledger.py")
ARTEFACT = os.path.join(REPO_ROOT, "experiments", "ptr-engine", "measure",
                        "GATE-LEDGER.json")


def run(tool, artefact):
    return subprocess.run([sys.executable, tool, "--check", "--artefact", artefact],
                          cwd=REPO_ROOT, capture_output=True, text=True)


class GateLedgerCheck(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gate-ledger-")
        with open(ARTEFACT, "r", encoding="utf-8") as fh:
            self.doc = json.load(fh)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _mutant(self, mutate):
        doc = json.loads(json.dumps(self.doc))
        mutate(doc)
        path = os.path.join(self.dir, "GATE-LEDGER.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
        return run(TOOL, path)

    # ---- GREEN: the shipped record is counted --------------------------------
    def test_green_shipped_artefact_passes(self):
        res = run(TOOL, ARTEFACT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("GATE-LEDGER CHECK OK", res.stdout)
        self.assertIn("21 cards", res.stdout)

    # ---- RED 1: an uncounted card -------------------------------------------
    def test_red_uncounted_card(self):
        def mutate(doc):
            doc["cards"] = [c for c in doc["cards"] if c["card"] != "WIRE-CAP-GATE"]
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("WIRE-CAP-GATE: uncounted card", res.stdout)

    # ---- RED 2: a gate with no stated benefit -------------------------------
    def test_red_gate_without_prevents(self):
        def mutate(doc):
            doc["gates"][1]["prevents"] = ""
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("prevents is empty", res.stdout)

    def test_red_gate_without_the_prevents_key(self):
        def mutate(doc):
            del doc["gates"][0]["prevents"]
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("missing required field 'prevents'", res.stdout)

    # ---- RED 3: a recommendation with no compliance sentence ---------------
    def test_red_recommendation_without_compliance_sentence(self):
        def mutate(doc):
            del doc["gates"][2]["compliance_statement"]
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("NO compliance sentence", res.stdout)

    def test_red_compliance_sentence_not_a_licensed_form(self):
        def mutate(doc):
            doc["gates"][0]["compliance_statement"] = "the guard is inconvenient"
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("not one of the two licensed forms", res.stdout)

    # ---- RED 4: retiring a guard dressed up as "no weakening" --------------
    def test_red_retire_cannot_claim_no_weakening(self):
        def mutate(doc):
            doc["gates"][1]["recommendation"] = "retire"
            doc["gates"][1]["compliance_statement"] = (
                "this does not weaken a guard: the refusal is unchanged and the removed"
                " element is the projection")
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("exactly a relaxation", res.stdout)

    # ---- RED 5: totals that are a claim, not a recomputation ---------------
    def test_red_totals_must_be_recomputed(self):
        def mutate(doc):
            doc["totals"]["defects"] = 3
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("totals.defects: stored 3, recomputed 15", res.stdout)

    def test_red_defect_count_must_match_its_list(self):
        def mutate(doc):
            doc["gates"][0]["defects_found"] = 5
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("defects_found=5", res.stdout)

    # ---- RED 6: silence about a missing corpus ----------------------------
    def test_red_absent_handoff_needs_a_reason(self):
        def mutate(doc):
            card = [c for c in doc["cards"] if c["card"] == "SPAWN-RECORD-BIND"][0]
            card.pop("unreconstructible", None)
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("an absent corpus is a finding", res.stdout)

    # ---- RED 7: a bypass answer must cover both thinking modes ------------
    def test_red_bypass_answer_must_cover_both_modes(self):
        def mutate(doc):
            doc["gates"][2]["live_path_bypass_possible"].pop("thinking_on_auto", None)
        res = self._mutant(mutate)
        self.assertEqual(res.returncode, 1, res.stdout)
        self.assertIn("thinking_on_auto", res.stdout)

    def test_unreadable_artefact_is_exit_2(self):
        res = run(TOOL, os.path.join(self.dir, "does-not-exist.json"))
        self.assertEqual(res.returncode, 2, res.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
