#!/usr/bin/env python3
"""test_run_a_star_claim.py - CANARY-ARGV-WIRING guards (offline, no request).

The launcher used to hard-code ``--hypothesis H2`` at
``experiments/ptr-engine/tools/run_a_star.py:182``, so NOTHING could ask for a
claim-free run: RUN-A-STAR-2's 12-turn canary would have been stamped ``claim: H2``
and the analyser would have pooled it into the arm it exists to compare.

These tests hold the wiring to four facts, with the real assembler:

  (a) a grid cell's argv is BYTE-IDENTICAL to the frozen shape (``--hypothesis H2``);
  (b) ``cell_argv(..., hypothesis="smoke")`` carries the smoke declaration, and every
      row it stamps reads ``claim: "none"`` / ``comparison_eligible: false``;
  (c) the analyser refuses those canary rows BY NAME (``incomparable_claim``) while it
      accepts the grid cells' rows;
  (d) the guard is not vacuous: a MUTANT launcher with the literal restored is loaded
      by path and the canary is observed being ACCEPTED as an H2 cell.

Offline: no cell is launched, no socket is opened, no row file outside tmp is written.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENG = os.path.join(ROOT, "experiments", "ptr-engine")
TOOLS = os.path.join(ENG, "tools")
LONGRUN = os.path.join(ENG, "longrun")
for p in (LONGRUN, TOOLS):
    if p not in sys.path:
        sys.path.insert(0, p)

import claim_mode as cm  # noqa: E402

# PIN-DERIVED (TEST-GRID-ARGV-PIN): the gen-4 digest is READ from the frozen
# record, never typed into this file, so the expectation tracks the record that
# cell.py itself enforces instead of a copy that drifts from it.
PIN_RECORD = os.path.join(ENG, "measure", "HARNESS-PIN.json")
with open(PIN_RECORD, encoding="utf-8") as _fh:
    PIN_REC = json.load(_fh)
PIN_GEN = PIN_REC["generation"]
PIN = PIN_REC["harness_sha256"]

# RUN-A-STAR-PATH lets a MUTANT launcher be loaded without touching the tree
# (TestGuardBites' /tmp copies use the same idea). Unset -> the real launcher.
LAUNCHER = os.environ.get("RUN_A_STAR_PATH") or os.path.join(TOOLS, "run_a_star.py")

GRID_ARGV = [
    sys.executable, "experiments/ptr-engine/longrun/cell.py",
    "--arm", "pointer-stable",
    "--fixture", "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
    "--turns", "48", "--reps", "1", "--thinking", "off", "--max-wall", "2880",
    "--turn-wall-cap", "180", "--runaway-turns", "2", "--budget", "108",
    "--hypothesis", "H2",
    "--expect-harness", PIN,
    "--no-cell-handoff",
    "--out-dir", "experiments/ptr-engine/measure",
    "--endpoint", "http://192.168.2.168:8012/v1",
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def analyser():
    return load(os.path.join(LONGRUN, "analyze_stats.py"), "analyze_stats_canary")


def rows_for(argv, n=12, arm="pointer-stable"):
    """The row-stamp path, driven by the argv's OWN claim value (not a constant)."""
    hyp = argv[argv.index("--hypothesis") + 1]
    rec = cm.resolve_claim(hyp)
    return [{"arm": arm, **cm.row_fields(rec), "rep": 1, "turn": t}
            for t in range(1, n + 1)]


class TestAssembler(unittest.TestCase):
    def setUp(self):
        self.ra = load(LAUNCHER, "run_a_star_canary")

    def test_grid_argv_is_byte_identical_to_the_frozen_shape(self):
        self.assertEqual(self.ra.cell_argv("pointer-stable", 1), GRID_ARGV)

    def test_default_is_h2(self):
        self.assertIn("--hypothesis", GRID_ARGV)
        self.assertEqual(self.ra.cell_argv("pointer-stable", 1)[
            GRID_ARGV.index("--hypothesis") + 1], "H2")

    # HARNESS-PIN-WIRING: the launcher's claim test must carry the pin it now
    # always passes, on BOTH paths, with the value the frozen record holds.
    def test_expect_harness_present_and_pinned_in_both_paths(self):
        self.assertEqual(PIN_GEN, 7, "HARNESS-PIN generation moved: %r" % (PIN_GEN,))
        self.assertEqual(self.ra.HARNESS_PIN, PIN,
                         "launcher HARNESS_PIN is not the record's digest")
        self.assertEqual(self.ra.pinned_digest(), PIN)
        grid = self.ra.cell_argv("pointer-stable", 1)
        canary = self.ra.cell_argv("pointer-stable", 1, "smoke", 12, 600)
        for path, argv in (("grid", grid), ("canary", canary)):
            with self.subTest(path=path):
                self.assertIn("--expect-harness", argv,
                              "%s argv is missing --expect-harness: %r"
                              % (path, argv))
                self.assertEqual(argv[argv.index("--expect-harness") + 1], PIN,
                                 "%s argv carries the wrong --expect-harness" % path)
                # the pin sits before --no-cell-handoff on both paths
                self.assertLess(argv.index("--expect-harness"),
                                argv.index("--no-cell-handoff"))

    # CANARY-ARMS-WIRING: four arms x twelve turns = 48 requests, not one arm.
    # The plan is built inline in main(), so the ASSERTION reads it there: the
    # selection must be one cell per arm (``if rep == 1``) and nothing narrower.
    def test_canary_covers_four_arms_and_48_requests(self):
        import ast
        self.assertEqual(len(self.ra.CANARY_ARMS), 4,
                         "CANARY_ARMS must name four arms, got %r"
                         % (self.ra.CANARY_ARMS,))
        arms = [arm for (arm, rep) in self.ra.CELLS if rep == 1]
        self.assertEqual(len(arms), 4,
                         "canary must cover four arms, got %r" % (arms,))
        self.assertEqual(sorted(set(arms)), sorted(self.ra.CANARY_ARMS))
        tree = ast.parse(open(LAUNCHER, encoding="utf-8").read())
        # main() holds TWO cell comprehensions (canary and grid); the canary's is
        # the one whose condition does not mention ``a.cell``.
        cands = [n for fn in tree.body
                 if isinstance(fn, ast.FunctionDef) and fn.name == "main"
                 for n in ast.walk(fn)
                 if isinstance(n, ast.ListComp)
                 and "CELLS" in ast.dump(n.generators[0].iter)]
        sel = [n for n in cands
               if len(n.generators[0].ifs) == 1
               and "'a'" not in ast.dump(n.generators[0].ifs[0])]
        self.assertEqual(len(sel), 1,
                         "canary cell selection not found in main() (candidates=%d)"
                         % len(cands))
        self.assertNotIn("'arm'", ast.dump(sel[0].generators[0].ifs[0]),
                         "canary plan narrows by arm: arm count would be 1, "
                         "not four arms / 48 requests")
        turns = int(self.ra.cell_argv(arms[0], 1, "smoke", 12, 600)[
            self.ra.cell_argv(arms[0], 1, "smoke", 12, 600).index("--turns") + 1])
        self.assertEqual(turns, 12, "canary turn count is not 12")
        self.assertEqual(len(arms) * turns, 48,
                         "canary must price 48 requests, got %d"
                         % (len(arms) * turns))

    def test_canary_argv_carries_the_smoke_declaration(self):
        cy = self.ra.cell_argv("pointer-stable", 1, "smoke", 12, 600)
        self.assertEqual(cy[cy.index("--hypothesis") + 1], "smoke")
        self.assertNotIn("H2", cy)
        self.assertEqual(cy[cy.index("--turns") + 1], "12")
        self.assertEqual(cy[cy.index("--max-wall") + 1], "600")
        # every OTHER element is untouched, in order
        rest_grid = [x for i, x in enumerate(GRID_ARGV)
                     if x != "H2" and x != "48" and x != "2880"]
        rest_cy = [x for i, x in enumerate(cy)
                   if x != "smoke" and x != "12" and x != "600"]
        self.assertEqual(rest_cy, rest_grid)

    def test_launcher_resolves_the_canary_claim_once(self):
        self.assertEqual(self.ra.claim_mode_of("H2"),
                         {"mode": "hypothesis", "claim": "H2",
                          "comparison_eligible": True})
        self.assertEqual(self.ra.claim_mode_of("smoke"),
                         {"mode": "smoke", "claim": "none",
                          "comparison_eligible": False})


class TestRowStamp(unittest.TestCase):
    def setUp(self):
        self.ra = load(LAUNCHER, "run_a_star_canary")

    def test_grid_rows_are_h2_and_eligible(self):
        rows = rows_for(self.ra.cell_argv("pointer-stable", 1, "H2", 48, 2880), n=12)
        self.assertEqual({(r["claim"], r["comparison_eligible"]) for r in rows},
                         {("H2", True)})

    def test_canary_rows_make_no_claim(self):
        rows = rows_for(self.ra.cell_argv("pointer-stable", 1, "smoke", 12, 600))
        self.assertEqual(len(rows), 12)
        self.assertEqual({(r["claim"], r["comparison_eligible"]) for r in rows},
                         {("none", False)})

    def test_analyser_refuses_canary_rows_by_name_and_accepts_cells(self):
        a = analyser()
        canary = rows_for(self.ra.cell_argv("pointer-stable", 1, "smoke", 12, 600))
        cells = rows_for(self.ra.cell_argv("pointer-stable", 1, "H2", 48, 2880))
        with self.assertRaises(a.IncomparableClaim) as ctx:
            a.require_comparable_claim(canary, "canary")
        self.assertTrue(str(ctx.exception).startswith("incomparable_claim"),
                        str(ctx.exception))
        self.assertIn("make no claim", str(ctx.exception))
        accepted = a.require_comparable_claim(cells, "cells")
        self.assertTrue(accepted["comparable"])
        self.assertEqual(accepted["claims"], {"h2": 12})


class TestGuardBites(unittest.TestCase):
    """A mutant launcher with the H2 literal restored must let the canary be pooled."""

    def test_hardcoded_h2_mutant_would_pool_the_canary(self):
        d = tempfile.mkdtemp(prefix="canary-argv-mutant-")
        try:
            src = os.path.join(TOOLS, "run_a_star.py")
            dst = os.path.join(d, "run_a_star.py")
            shutil.copyfile(src, dst)
            body = open(dst, encoding="utf-8").read()
            old = '"--hypothesis", hypothesis,'
            assert body.count(old) == 1
            open(dst, "w", encoding="utf-8").write(
                body.replace(old, '"--hypothesis", "H2",'))
            mutant = load(dst, "run_a_star_mutant")
            cy = mutant.cell_argv("pointer-stable", 1, "smoke", 12, 600)
            self.assertNotIn("smoke", cy)                 # the canary was ignored
            rows = rows_for(cy)                            # -> stamped from argv = H2
            self.assertEqual({(r["claim"], r["comparison_eligible"]) for r in rows},
                             {("H2", True)})
            a = analyser()
            accepted = a.require_comparable_claim(rows, "mutant")
            self.assertTrue(accepted["comparable"], accepted)
            self.assertEqual(accepted["claims"], {"h2": 12})
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
