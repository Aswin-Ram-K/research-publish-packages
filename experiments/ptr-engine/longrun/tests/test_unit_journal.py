#!/usr/bin/env python3
"""Kill-test for the append-only unit journal (experiments/ptr-engine/tools/unit_journal.py).

Every case runs in its own temp dir: nothing here touches the real workspace.
Set UNIT_JOURNAL_TOOL to point the suite at an alternate copy of the tool (used to
reproduce the red state by reverting individual guards).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TOOL = os.path.normpath(os.path.join(HERE, "..", "..", "tools", "unit_journal.py"))
TOOL = os.environ.get("UNIT_JOURNAL_TOOL", DEFAULT_TOOL)

ART_A = "docs/A.md"
ART_B = "out/B.json"
ART_MISSING = "docs/NEVER-WRITTEN.md"


def run(root, *args, expect=None):
    """Invoke the tool with --root <tmp> and return CompletedProcess."""
    cmd = [sys.executable, TOOL, "--root", root] + list(args)
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if expect is not None and cp.returncode != expect:
        raise AssertionError("expected exit %s, got %s\ncmd=%s\nout=%s\nerr=%s"
                             % (expect, cp.returncode, " ".join(cmd), cp.stdout, cp.stderr))
    return cp


def jpath(root, unit="U-T"):
    return os.path.join(root, "orchestration", "journals", unit + ".jsonl")


def write(root, rel, data="x"):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(data)


def seed(root, unit="U-T"):
    run(root, "init", "--unit", unit, "--card", "card-1", "--bound", "9",
        "--paths", ART_A, ART_B, expect=0)
    write(root, ART_A, "alpha")
    write(root, ART_B, "{\"b\":1}")
    for p, note in ((ART_A, "A written"), (ART_B, "B written"), (ART_MISSING, "planned, not yet")):
        run(root, "log", "--unit", unit, "--kind", "artifact", "--path", p, "--note", note, expect=0)
    run(root, "log", "--unit", unit, "--kind", "evidence", "--command", "pytest -q",
        "--exit", "0", "--out", "PASS 12/12", expect=0)
    run(root, "log", "--unit", unit, "--kind", "next", "--text", "run corpus audit, then handoff",
        expect=0)


class KillTest(unittest.TestCase):
    def test_a_killed_process_still_reconstructs(self):
        """(a) header+3 artifacts+evidence+next, then SIGKILL before any handoff."""
        with tempfile.TemporaryDirectory() as root:
            journal = jpath(root)
            handoff = os.path.join(root, "orchestration", "handoffs", "U-T.json")
            child = r"""
import os, subprocess, sys, time
TOOL, ROOT = sys.argv[1], sys.argv[2]
def t(*a): subprocess.run([sys.executable, TOOL, "--root", ROOT] + list(a), check=True,
                          capture_output=True)
t("init","--unit","U-T","--card","card-1","--bound","9","--paths","docs/A.md","out/B.json","docs/NEVER-WRITTEN.md")
for p in ("docs/A.md","out/B.json","docs/NEVER-WRITTEN.md"):
    t("log","--unit","U-T","--kind","artifact","--path",p)
t("log","--unit","U-T","--kind","evidence","--command","pytest -q","--exit","0","--out","PASS 12/12")
t("log","--unit","U-T","--kind","next","--text","run corpus audit, then handoff")
# the handoff is the LAST write in the protocol; the kill lands here, before it
time.sleep(120)
"""
            for rel, data in ((ART_A, "alpha"), (ART_B, "{}")):
                write(root, rel, data)
            proc = subprocess.Popen([sys.executable, "-c", child, TOOL, root])
            try:
                deadline = time.time() + 60
                while time.time() < deadline:
                    if os.path.exists(journal) and open(journal, encoding="utf-8").read().count("\n") >= 6:
                        break
                    time.sleep(0.05)
                else:
                    self.fail("child never wrote the six journal records")
                proc.send_signal(signal.SIGKILL)
                proc.wait(timeout=30)
            finally:
                if proc.poll() is None:
                    proc.kill()

            self.assertEqual(proc.returncode, -signal.SIGKILL, "process was actually SIGKILLed")
            self.assertFalse(os.path.exists(handoff), "no handoff was ever written")

            st = run(root, "status", "--unit", "U-T", expect=1)  # one artifact is missing
            out = st.stdout
            self.assertIn("records: 6", out)
            self.assertIn("last_step: 5", out)
            self.assertIn(ART_A, out)
            self.assertIn("%d bytes" % len("alpha"), out)
            self.assertIn("artifacts exist  (2):", out)
            self.assertIn("artifacts MISSING (1):", out)
            self.assertIn(ART_MISSING, out)
            self.assertIn("run corpus audit, then handoff", out)

            rs = run(root, "resume", "--unit", "U-T", expect=0)
            self.assertIn("6 journal records", rs.stdout)
            self.assertIn(ART_A, rs.stdout)
            self.assertIn("5 bytes", rs.stdout)
            self.assertIn(ART_MISSING, rs.stdout)
            self.assertIn("PASS 12/12", rs.stdout)
            self.assertIn("run corpus audit, then handoff", rs.stdout)

    def test_b_torn_last_line_is_not_fatal(self):
        """(b) a half-written final line still yields a usable resume, exit 0."""
        with tempfile.TemporaryDirectory() as root:
            seed(root)
            journal = jpath(root)
            with open(journal, "a", encoding="utf-8") as fh:
                fh.write('{"t":"2026-10-26T15:04:31Z","step":6,"kind":"artifact","pa')
            rs = run(root, "resume", "--unit", "U-T", expect=0)
            self.assertIn(ART_A, rs.stdout)
            self.assertIn("run corpus audit, then handoff", rs.stdout)
            st = run(root, "status", "--unit", "U-T", expect=1)
            self.assertIn("torn_lines: 1", st.stdout)
            self.assertIn("records: 6", st.stdout)
            self.assertIn(ART_MISSING, st.stdout)

    def test_c_status_nonzero_only_for_missing_artifact(self):
        """(c) exit 1 names the missing artifact; all-present exits 0."""
        with tempfile.TemporaryDirectory() as root:
            seed(root)
            st = run(root, "status", "--unit", "U-T", expect=1)
            self.assertIn("MISSING " + ART_MISSING, st.stdout)
            self.assertIn("MISSING-ARTIFACT: " + ART_MISSING, st.stdout)
            write(root, ART_MISSING, "now real")
            st2 = run(root, "status", "--unit", "U-T", expect=0)
            self.assertNotIn("MISSING-ARTIFACT", st2.stdout)
            self.assertIn("artifacts MISSING (0):", st2.stdout)
            self.assertIn("artifacts exist  (3):", st2.stdout)

    def test_d_append_only(self):
        """(d) no rewrite path; a second log leaves earlier bytes identical."""
        with tempfile.TemporaryDirectory() as root:
            seed(root)
            journal = jpath(root)
            before = open(journal, "rb").read()
            run(root, "log", "--unit", "U-T", "--kind", "assumption",
                "--text", "corpus path is stable", expect=0)
            after = open(journal, "rb").read()
            self.assertTrue(after.startswith(before), "earlier bytes were rewritten")
            self.assertGreater(len(after), len(before))

            # init must refuse to rewrite an existing journal
            rc = run(root, "init", "--unit", "U-T", "--card", "card-2")
            self.assertNotEqual(rc.returncode, 0)
            self.assertEqual(open(journal, "rb").read(), after)
            self.assertEqual(after, after, "journal untouched by refused init")

            src = open(TOOL, encoding="utf-8").read()
            for forbidden in ('open(path, "w"', "open(path, 'w'", '"r+")', '"w+")', "os.replace("):
                self.assertNotIn(forbidden, src, "rewrite path present: %s" % forbidden)
            self.assertIn('open(path, "a"', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
