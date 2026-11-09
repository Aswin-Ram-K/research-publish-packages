#!/usr/bin/env python3
"""GATE-OPERAND-VALIDATION — the assertions, derived from the requirement.

Run from the REPO ROOT or from this directory; every path resolves from ``__file__``:

    python3 experiments/ptr-engine/longrun/tests/test_gate_operand_validation.py

What this pins (and why it is not a re-test of the code's own output):

* every hostile numeric value (``0``, ``-1``, ``-48``, ``1e-9``, ``1e308``, ``inf``,
  ``nan``, ``"abc"``, ``""``, ``None``) of every operand of every gate is REFUSED with
  the exit code the requirement names, and the refusal spawns no runner;
* the only rows that may assert exit 0 are the values the requirement calls legal
  (plus the documented ``None`` default sentinels);
* the six bypasses named in ``orchestration/handoffs/VERDICT-DISPUTE.json`` — F1
  ``--max-wall 1e308``, F2 a 1e-9 override, F3 an artefact zero, F4 ``--turns 0`` under
  H3, F5 a negative turn count, F8 ``--turn-wall-cap 0`` — now refuse (8, 8, 8, 4, 4, 8)
  with zero live spawns, end-to-end through ``cell.main()``;
* ``EXIT_TABLE``, ``docs/GATE-CHAIN.md`` and the gates agree on every gate-chain code
  (2, 3, 4, 8, 12). Nothing was renumbered.

The gate chain is repaired, never relaxed: if a future edit admits one hostile value,
one of these assertions fails. No test here asserts "allows" for a hostile value.
"""

import json
import os
import sys
import tempfile
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(TESTS)
ENGINE = os.path.dirname(LONG)
REPO = os.path.dirname(os.path.dirname(ENGINE))
TOOLS = os.path.join(ENGINE, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
if LONG not in sys.path:
    sys.path.insert(0, LONG)

import gate_attack as A            # noqa: E402  (the attack IS the table)
import cell                        # noqa: E402  (the module under attack)

# The values the requirement calls LEGAL for the operand they are applied to. Anything
# else that expects exit 0 would be a relaxed assertion, so it is not allowed here.
LEGAL = {
    ("G1", "turns", "48"), ("G1", "cap", "4320"), ("G1", "allowance", "96"),
    ("G1", "reserve", "0"), ("G1", "allowance", "None"),
    ("G2", "max_wall", "3600.0"), ("G2", "max_wall", "2880.0"),
    ("G2", "turn_wall_cap", "180.0"), ("G2", "projected_turn_wall", "60.0"),
    ("G2", "projected_turn_wall", "None"),
    ("G3", "hypothesis", "'H1'@60"), ("G3", "hypothesis", "'H2'"),
    ("G3", "hypothesis", "'H3'"), ("G3", "checkpoints", "None"),
}
# H3 needs 8 of 12: a legal checkpoint count is 8 or more.
LEGAL_CHECKPOINTS = 8


class OperandMatrix(unittest.TestCase):
    """One assertion per row of the requirement-derived table."""

    @classmethod
    def tearDownClass(cls):
        cell._run = cls.orig_run

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="gate-operands-")
        if not hasattr(cell, "Abort"):        # be explicit if the module is not ours
            raise unittest.SkipTest("cell.py is not importable")
        cls.spawn = {"n": 0}
        cls.orig_run = cell._run

        def counted(*a, **k):                 # the only process primitive, counted
            cls.spawn["n"] += 1
            return 0, "", ""

        cell._run = counted
        cls.rows = A.run_rows(cell, A.build_rows(cell, cls.tmp), cls.tmp, cls.spawn)
        cls.f_cases = A.run_chain_cases(cell, cls.tmp)

    def test_every_hostile_row_is_refused_with_its_required_exit_code(self):
        bad = [r for r in self.rows if r["expected"] != 0 and r["actual"] == 0]
        self.assertEqual([], bad, "hostile operands ADMITTED: %s"
                         % [(r["gate"], r["operand"], r["label"]) for r in bad])

    def test_every_row_matches_its_requirement_derived_expectation(self):
        bad = [(r["gate"], r["operand"], r["label"], r["expected"], r["actual"],
                r["detail"][:120]) for r in self.rows if not r["ok"]]
        self.assertEqual([], bad)

    def test_no_refusal_spawns_a_runner(self):
        spawned = [(r["gate"], r["operand"], r["label"]) for r in self.rows
                   if r["spawned"]]
        self.assertEqual([], spawned, "a refusing evaluator spawned: %s" % spawned)

    def test_an_allow_row_is_only_a_value_the_requirement_calls_legal(self):
        for row in self.rows:
            if row["expected"] == 0 and row["gate"] in ("G1", "G2", "G3"):
                key = (row["gate"], row["operand"], row["label"])
                if row["gate"] == "G3" and row["operand"] == "checkpoints":
                    self.assertTrue(row["value"] is None
                                    or (isinstance(row["value"], int)
                                        and row["value"] >= LEGAL_CHECKPOINTS),
                                    "checkpoint allow-row below the H3 floor: %r"
                                    % (row["value"],))
                    continue
                if row["gate"] == "G3" and row["operand"] == "hypothesis" \
                        and row["kwargs"].get("turns") == 60:
                    self.assertEqual("'H1'", row["label"])
                    continue
                self.assertIn(key, LEGAL, "row asserts exit 0 for a hostile value: %r"
                              % (key,))

    def test_claim_counts(self):
        self.assertGreaterEqual(len(self.rows), 150)
        for gate in ("G1", "G2", "G3"):
            sub = [r for r in self.rows if r["gate"] == gate]
            self.assertTrue(sub, gate)
        hostile = [r for r in self.rows if r["expected"] != 0]
        self.assertEqual([], [r for r in hostile if r["actual"] == 0])

    def test_the_six_named_bypasses_now_refuse_with_zero_live_spawns(self):
        want = {"F1": 8, "F2": 8, "F3": 8, "F4": 4, "F5": 4, "F8": 8}
        got = {c["case"]: c for c in self.f_cases}
        self.assertEqual(sorted(want), sorted(got))
        for case, code in want.items():
            self.assertEqual(code, got[case]["actual"],
                             "%s: expected exit %s, got %s (%s)"
                             % (case, code, got[case]["actual"],
                                got[case]["refusal"][:200]))
            self.assertEqual(0, got[case]["live_spawns"],
                             "%s spawned a runner while refusing" % case)
            self.assertTrue(got[case]["refusal"],
                            "%s refused without naming the refusal" % case)

    def test_exit_table_and_the_gate_doc_agree_on_every_gate_code(self):
        table = A.exit_table_check()
        self.assertEqual([2, 3, 4, 8, 12], table["gate_codes"])
        self.assertTrue(table["gate_codes_agree"], json.dumps(table))
        self.assertEqual([], table["documented_not_declared"])


class DocumentedGates(unittest.TestCase):
    """The three gates exist, keep their codes, and their refusals are actionable."""

    def test_gate_ids_and_codes_are_unchanged(self):
        self.assertEqual(cell.GATE_LEDGER, "G1")
        self.assertEqual(cell.GATE_PROJECTION, "G2")
        self.assertEqual(cell.GATE_PREREG, "G3")
        sys.path.insert(0, LONG)
        try:
            import exit_codes
        finally:
            sys.path.pop(0)
        self.assertEqual(4, exit_codes.EXIT_TABLE[4]["name"].count("ledger-cap")
                         and 4)
        self.assertEqual(8, exit_codes.EXIT_TABLE[8]["name"].count("projection") and 8)
        self.assertEqual(12, exit_codes.EXIT_TABLE[12]["name"].count("prereg") and 12)

    def test_refusal_names_computed_limit_artefact_and_flag(self):
        tmp = tempfile.mkdtemp(prefix="gate-msg-")
        ledger, _ = A.fake_ledger(tmp, cap=0, spent=0, name="ledger-msg.json")
        cell.LEDGER_ARTEFACT = ledger
        args = A.ns(cell)
        verdict = cell.eval_gate_ledger(args)
        self.assertFalse(verdict["ok"])
        message = cell._gate_message(verdict)
        for part in ("G1 ledger-cap REFUSED", "computed", "limit", "artefact",
                     "sha256", "to change this decision pass",
                     "a larger cap in the ledger"):
            self.assertIn(part, message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
