#!/usr/bin/env python3
"""test_verdict_semantics.py - the guard that a refusal is never read as a failure.

WHAT IT GUARDS
  1. every code in `exit_codes.EXIT_TABLE` is classified -- and a code added to the
     table without being classified is RED (proved on a /tmp copy with a fake `99`,
     not
     asserted by hand);
  2. `4` (ledger cap) is a refusal and `0` is a pass;
  3. the markdown table in docs/VERDICT-SEMANTICS.md and the code's partition agree, so
     the two cannot drift (the document is parsed, not trusted).

Offline: no request, no network, no git.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)                       # experiments/ptr-engine/longrun
PTR_ENGINE = os.path.dirname(LONGRUN)                 # experiments/ptr-engine
REPO = os.path.dirname(os.path.dirname(PTR_ENGINE))   # repo root
TOOLS = os.path.join(PTR_ENGINE, "tools")
DOC = os.path.join(REPO, "docs", "VERDICT-SEMANTICS.md")

sys.path.insert(0, LONGRUN)
sys.path.insert(0, TOOLS)

import exit_codes          # noqa: E402
import verdict_semantics   # noqa: E402

ROW = re.compile(r"^\|\s*`(\d+)`\s*\|\s*`([^`]+)`\s*\|\s*(measures|refuses)\s*\|\s*`([^`]+)`\s*\|")


def parse_doc_rows(path=DOC):
    """{code: (name, kind, verdict)} from the document's partition table."""
    rows = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = ROW.match(line.strip())
            if match:
                code, name, kind, verdict = match.groups()
                rows[int(code)] = (name, kind, verdict)
    return rows


class TestPartition(unittest.TestCase):
    def test_every_table_code_is_classified(self):
        table = verdict_semantics.table_codes()
        classified = verdict_semantics.classified_codes()
        self.assertEqual(
            sorted(table - classified), [],
            "exit_codes.EXIT_TABLE carries codes the partition never classifies",
        )
        self.assertEqual(
            sorted(classified - table), [],
            "the partition classifies codes exit_codes.EXIT_TABLE does not carry",
        )
        for code in sorted(table):
            self.assertIn(verdict_semantics.classify(code), verdict_semantics.VERDICTS)

    def test_zero_is_a_pass_and_four_is_a_refusal(self):
        self.assertEqual(verdict_semantics.classify(0), verdict_semantics.VERIFIED_PASS)
        self.assertTrue(verdict_semantics.is_refusal(4))
        # CAPGATE-CELL-LABEL's 14 is the cell-level cap-gate reconciliation refusal: the
        # ledger and the rows disagree, so no artefact was measured. Refusal, not failure.
        self.assertTrue(verdict_semantics.is_refusal(exit_codes.EXIT_CAPGATE_UNRECORDED))
        self.assertEqual(verdict_semantics.classify(14),
                         verdict_semantics.UNSTAMPED_REFUSAL)
        self.assertFalse(verdict_semantics.is_refusal(0))
        self.assertFalse(verdict_semantics.is_refusal(11))

    def test_refusals_are_exactly_the_ones_the_doc_names(self):
        codes = {
            code for code in verdict_semantics.classified_codes()
            if verdict_semantics.is_refusal(code)
        }
        self.assertEqual(codes, set(verdict_semantics.REFUSING))
        self.assertTrue({2, 3, 4, 8, 12}.issubset(codes))
        self.assertNotIn(0, codes)

    def test_unknown_code_raises_instead_of_defaulting(self):
        # 99 is in no table: an unknown code must raise, never default to a verdict.
        with self.assertRaises(verdict_semantics.UnclassifiedExitCode):
            verdict_semantics.classify(99)
        with self.assertRaises(verdict_semantics.UnclassifiedExitCode):
            verdict_semantics.is_refusal("not-a-code")

    def test_every_table_code_has_a_name(self):
        for code in sorted(verdict_semantics.table_codes()):
            self.assertTrue(exit_codes.EXIT_TABLE[code]["name"], "code %d has no name" % code)


class TestDocAgreesWithCode(unittest.TestCase):
    def test_doc_parses_and_covers_the_table(self):
        rows = parse_doc_rows()
        self.assertTrue(rows, "docs/VERDICT-SEMANTICS.md has no parseable partition rows")
        self.assertEqual(
            sorted(set(rows)), sorted(verdict_semantics.table_codes()),
            "the doc's codes and exit_codes.EXIT_TABLE's codes differ",
        )

    def test_doc_verdicts_equal_the_code_verdicts(self):
        rows = parse_doc_rows()
        for code, (name, kind, verdict) in sorted(rows.items()):
            self.assertEqual(
                verdict, verdict_semantics.classify(code),
                "doc says code %d is %s; verdict_semantics says %s"
                % (code, verdict, verdict_semantics.classify(code)),
            )
            expected_kind = (
                "refuses" if verdict == verdict_semantics.UNSTAMPED_REFUSAL else "measures"
            )
            self.assertEqual(kind, expected_kind, "code %d: kind disagrees with verdict" % code)
            self.assertEqual(
                name, exit_codes.EXIT_TABLE[code]["name"],
                "code %d: doc name %r != exit_codes name %r"
                % (code, name, exit_codes.EXIT_TABLE[code]["name"]),
            )

    def test_doc_states_the_one_sentence(self):
        with open(DOC, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("*unstamped*, not *failed*", text)
        self.assertIn("the fix is to record a command that measures the card's own artefact", text)


class TestRedOnAnUnclassifiedCode(unittest.TestCase):
    """A code added to the table but not classified must turn this guard RED."""

    def test_fake_ninety_nine_on_a_copy_is_red(self):
        tmpdir = tempfile.mkdtemp(prefix="vrs-red-")
        try:
            table_path = os.path.join(tmpdir, "exit_codes.py")
            shutil.copyfile(os.path.join(LONGRUN, "exit_codes.py"), table_path)
            with open(table_path, "a", encoding="utf-8") as handle:
                handle.write(
                    "\n\n# RED PROOF: a fake code the partition does not classify.\n"
                    "EXIT_TABLE[99] = dict(EXIT_TABLE[EXIT_PREREG], name='fake-99')\n"
                )
            env = dict(os.environ)
            env["VERDICT_SEMANTICS_EXIT_CODES_DIR"] = tmpdir
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            script = (
                "import sys; sys.path.insert(0, %r); import verdict_semantics; "
                "print(verdict_semantics.classify(99))" % TOOLS
            )
            proc = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, env=env, cwd=REPO,
            )
            self.assertNotEqual(
                proc.returncode, 0,
                "a fake 99 in the table was accepted; the guard is blind to new codes",
            )
            self.assertIn("99", proc.stderr + proc.stdout)

            # control: the same script against the real table succeeds
            env.pop("VERDICT_SEMANTICS_EXIT_CODES_DIR")
            ok = subprocess.run(
                [sys.executable, "-c", "import sys; sys.path.insert(0, %r); "
                 "import verdict_semantics; print(len(verdict_semantics.CLASSIFICATION))" % TOOLS],
                capture_output=True, text=True, env=env, cwd=REPO,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
