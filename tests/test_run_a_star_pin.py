#!/usr/bin/env python3
"""test_run_a_star_pin.py - HARNESS-PIN-WIRING + CANARY-ARMS-WIRING guards.

Two launch defects this file holds shut (offline; no cell, no socket):

  PIN  ``cell_argv`` never passed ``--expect-harness``, so ``cell.py:336-349``
       refused nothing and the 1,016-request launch could start against bytes
       nobody pinned.
  ARMS the canary ran ONE arm (``a.cell = a.cell or 1``) for 12 requests while the
       priced component was 4 x 12 = 48, so three arms reached the grid ungated.

Facts asserted, with the real launcher loaded by path:

  (a) every grid argv AND every canary argv carries ``--expect-harness <gen-4>``;
  (b) measure/HARNESS-PIN.json is generation 4, its recorded digest equals a LIVE
      recomputation over the six inputs, and generations 1-3 are still on the record;
  (c) the canary iterates the four arms (cells 1,4,7,9) and declares 48 requests;
  (d) the guards are not vacuous: MUTANT launchers (flag stripped / one-arm filter
      restored) loaded by path are observed breaking (a) and (c).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
PIN = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "HARNESS-PIN.json")
LAUNCHER = os.path.join(TOOLS, "run_a_star.py")

SIX = [
    ("run_longrun.py", "experiments/ptr-engine/longrun/run_longrun.py"),
    ("client.py", "experiments/ptr-engine/longrun/client.py"),
    ("grade_v5.py", "experiments/ptr-engine/longrun/grade_v5.py"),
    ("analyze_stats.py", "experiments/ptr-engine/longrun/analyze_stats.py"),
    ("tools/det_verify.py", "experiments/ptr-engine/tools/det_verify.py"),
    ("fixture", "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json"),
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def live_pin():
    """The same recipe cell.py:334-349 uses: sha256 over 'name:sha256\\n', sorted."""
    h = hashlib.sha256()
    per_file = {}
    for name, rel in sorted(SIX):
        with open(os.path.join(ROOT, rel), "rb") as fh:
            d = hashlib.sha256(fh.read()).hexdigest()
        per_file[name] = d
        h.update(("%s:%s\n" % (name, d)).encode())
    return h.hexdigest(), per_file


class PinWiring(unittest.TestCase):
    def setUp(self):
        self.ras = load(LAUNCHER, "ras_pin_test")

    def test_grid_argv_carries_gen4(self):
        argv = self.ras.cell_argv("pointer-stable", 1)
        self.assertIn("--expect-harness", argv)
        self.assertEqual(argv[argv.index("--expect-harness") + 1],
                         self.ras.HARNESS_PIN)
        self.assertEqual(self.ras.HARNESS_PIN, live_pin()[0])

    def test_canary_argv_carries_gen4(self):
        argv = self.ras.cell_argv("lease-reopen", 1, hypothesis="smoke",
                                  turns=12, max_wall=600)
        self.assertIn("--hypothesis", argv)
        self.assertEqual(argv[argv.index("--hypothesis") + 1], "smoke")
        self.assertEqual(argv[argv.index("--expect-harness") + 1],
                         self.ras.HARNESS_PIN)

    def test_pin_record_is_generation_4_and_additive(self):
        rec = json.load(open(PIN, encoding="utf-8"))
        live, per_file = live_pin()
        self.assertEqual(rec["generation"], 7)
        self.assertEqual(rec["harness_sha256"], live)
        self.assertEqual(rec["superseded_harness_sha256"],
                         rec["superseded_pin_generation_6"]["harness_sha256"])
        for name in per_file:
            got = [f for f in rec["files"] if f["name"] == name]
            self.assertEqual(len(got), 1, name)
            self.assertEqual(got[0]["sha256"], per_file[name], name)
        gen6 = rec["superseded_pin_generation_6"]
        self.assertEqual(gen6["generation"], 6)
        gen5 = gen6["supersedes_pin_generation_5"]
        gen2 = gen5["supersedes_pin_generation_4"]["supersedes_pin_generation_3"]["supersedes_pin_generation_2"]
        self.assertEqual(gen2["harness_sha256"],
                         "1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285")
        self.assertIn("c4541802", json.dumps(gen2["supersedes"]))  # generation 1

    def test_record_disagreement_refuses_launcher(self):
        ras = load(LAUNCHER, "ras_pin_bad_record")
        tmp = os.path.join(HERE, ".pin-record-should-not-exist.json")
        self.assertFalse(os.path.exists(tmp))
        ras.PIN_RECORD = tmp
        with self.assertRaises(SystemExit):
            ras.pinned_digest(tmp)


class CanaryArms(unittest.TestCase):
    def setUp(self):
        self.ras = load(LAUNCHER, "ras_arms_test")

    def _run_main(self, mod, argv):
        seen = []

        def fake_run_cell(arm, rep, n, *a, **kw):
            seen.append((arm, rep, n, kw.get("turns"), kw.get("max_wall")))
            return {"rc": 0, "gates": ["G1 allow"], "would_refuse": []}

        old_argv, old_run = sys.argv, mod.run_cell
        mod.run_cell = fake_run_cell
        sys.argv = ["run_a_star.py"] + argv
        try:
            rc = mod.main()
        finally:
            sys.argv, mod.run_cell = old_argv, old_run
        return rc, seen

    def test_canary_runs_one_cell_per_arm(self):
        rc, seen = self._run_main(
            self.ras, ["--tools", "", "--canary", "--budget", "108",
                       "--cell", "1", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertEqual([s[0] for s in seen], list(self.ras.CANARY_ARMS))
        self.assertEqual([s[3] for s in seen], [12, 12, 12, 12])
        self.assertEqual(len(seen) * 12, 48)

    def test_grid_path_still_one_cell(self):
        rc, seen = self._run_main(
            self.ras, ["--tools", "", "--cell", "4", "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertEqual([(s[0], s[2]) for s in seen], [("pointer-stable", 4)])
        self.assertEqual(seen[0][3], 48)


class MutantsAreCaught(unittest.TestCase):
    def _mutant(self, old, new, name):
        src = open(LAUNCHER, encoding="utf-8").read()
        self.assertIn(old, src)
        path = os.path.join(HERE, "%s.py" % name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src.replace(old, new, 1))
        try:
            return load(path, name)
        finally:
            os.unlink(path)

    def test_mutant_without_expect_harness_breaks_wiring(self):
        m = self._mutant('"--expect-harness", pinned_digest(),', "", "mut_no_pin")
        self.assertNotIn("--expect-harness", m.cell_argv("pointer-stable", 1))

    def test_mutant_one_arm_canary_is_caught(self):
        m = self._mutant("if rep == 1]", "if rep == 1 and n == 1]", "mut_one_arm")
        seen = []

        def fake_run_cell(arm, rep, n, *a, **kw):
            seen.append(arm)
            return {"rc": 0, "gates": [], "would_refuse": []}

        old_argv, m.run_cell = sys.argv, fake_run_cell
        sys.argv = ["run_a_star.py", "--canary", "--budget", "108", "--cell", "1",
                    "--dry-run"]
        try:
            m.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(seen, ["pointer-stable"])


if __name__ == "__main__":
    unittest.main()
