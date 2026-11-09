#!/usr/bin/env python3
"""test_gate_messages.py - each gate's `consequence` sentence must agree with its own `ok`.

WHY THIS EXISTS (GATES-MESSAGE-CONSISTENCY): the recorded artefact
`experiments/ptr-engine/measure/cell-pointer-stable-20261026T182535Z-p4-001.gates.json`
has three verdicts with `ok: true`, and two of their `consequence` sentences read as
failures. G1 said "this cell needs 1,154 requests ... but only 4,320 remain: shortfall
-3,166 requests" (1,154 is the CUMULATIVE spend after the cell, 4,320 is the cap, and a
negative shortfall is not a shortfall). G2 said "exceeds the allowed 2880s" on a verdict
that was admitted at the boundary, and called 48 turns "48 request(s)". A reader of the
artefact would conclude both cells were refused while both ran.

What is asserted here is only the SENTENCE and the provenance: the decision, the
threshold, the exit code and the values of computed/limit/ok are not this test's to move.

Every test is OFFLINE: the runner is replaced by the stub in `test_cell_gates`.
"""
import glob
import hashlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PTR_ENGINE = os.path.dirname(LONGRUN)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))
sys.path.insert(0, HERE)

from test_cell_gates import (  # noqa: E402  (the one offline cell harness)
    _env, _fake_ledger, _fake_runner, _live_argv, _run)


def _only_manifest(tmp):
    """The one gate manifest an admitted cell wrote, parsed."""
    paths = sorted(glob.glob(os.path.join(tmp, "out", "*.gates.json")))
    if len(paths) != 1:
        raise AssertionError("expected exactly one gate manifest, got %r" % (paths,))
    with open(paths[0], encoding="utf-8") as fh:
        return json.load(fh)


def _verdict(doc, gate):
    for v in doc.get("verdicts") or []:
        if v.get("gate") == gate:
            return v
    raise AssertionError("no %s verdict in %r" % (gate, doc.get("verdicts")))


def _admitted(tmp, extra):
    """Run one admitted cell: G1 cap 4,320 with 100 spent, H2 at 48 turns."""
    ledger, _rows = _fake_ledger(tmp, cap=4320, spent=100)
    runner, marker = _fake_runner(tmp)
    rc, log = _run(_live_argv(tmp, list(extra)),
                   _env(tmp, ledger, runner, marker))
    return rc, log, marker


class GateMessages(unittest.TestCase):
    def test_a_allowed_g1_prints_no_shortfall_and_its_arithmetic_closes(self):
        """An ADMITTED G1 must not say 'shortfall' and must add up.

        history: the old sentence said "this cell needs <projected> requests but only
        <cap> remain: shortfall -3,166", i.e. it printed a refusal on an admission.
        """
        with tempfile.TemporaryDirectory() as tmp:
            rc, log, marker = _admitted(tmp, ["--hypothesis", "H2", "--max-wall", "2880"])
            assert rc != 4, "G1 refused a cell with headroom (rc=%d)\n%s" % (rc, log)
            assert os.path.exists(marker), "the runner was never invoked\n%s" % log[-3000:]
            g1 = _verdict(_only_manifest(tmp), "G1")
            text = g1["consequence"]
        self.assertNotIn("shortfall", text, "an admission prints a shortfall:\n%s" % text)
        self.assertNotIn("only 4,320 remain", text,
                         "the admission calls the cap what remains:\n%s" % text)
        self.assertIn("admits", text, "no allow family:\n%s" % text)
        self.assertIn("cumulative spend", text,
                      "the admission does not say what `projected` is:\n%s" % text)
        self.assertIn("turn(s)", text, "the admission does not name turns as turns:\n%s"
                      % text)
        # the arithmetic the sentence claims, checked against the gate's own fields
        self.assertEqual(g1["spent"] + g1["would_spend"], g1["projected"],
                         "spent + would_spend must equal projected")
        self.assertLessEqual(g1["projected"], g1["headroom"],
                             "an admitted verdict is within its limit")
        self.assertEqual(g1["headroom"] - g1["projected"], g1["remaining"],
                         "remaining must be limit - projected")

    def test_b_refused_g1_still_names_a_shortfall_and_exits_4(self):
        """The guard: a REFUSED G1 keeps its shortfall sentence and its exit code 4."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger, _rows = _fake_ledger(tmp, cap=120, spent=100)
            runner, marker = _fake_runner(tmp)
            rc, log = _run(_live_argv(tmp, []),
                           _env(tmp, ledger, runner, marker))
            invoked = os.path.exists(marker)
        self.assertEqual(rc, 4, "expected exit 4 (the ledger cap), got %d\n%s"
                         % (rc, log[-3000:]))
        self.assertIn("shortfall", log, "the refusal does not name the shortfall:\n%s"
                      % log[-3000:])
        self.assertIn("G1 ledger-cap REFUSED", log, log[-3000:])
        self.assertNotIn("G1 admits", log, "a refusal printed the allow family:\n%s"
                         % log[-3000:])
        self.assertNotIn("request(s)", log, "a count is labelled with the wrong unit:\n%s"
                         % log[-3000:])
        self.assertFalse(invoked, "the runner was invoked past a G1 refusal")

    def test_c_allowed_g2_at_the_2880_boundary_keeps_its_sentence(self):
        """G2 at projected 2,880 s against --max-wall 2880 must read as an ADMISSION."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, log, marker = _admitted(tmp, ["--hypothesis", "H2",
                                              "--max-wall", "2880"])
            assert rc != 8, "the 2,880 s boundary was refused (exit 8)\n%s" % log[-3000:]
            assert os.path.exists(marker), "the runner was never invoked\n%s" % log[-3000:]
            g2 = _verdict(_only_manifest(tmp), "G2")
        self.assertTrue(g2["ok"], "the boundary verdict is not an admission")
        self.assertEqual(g2["computed"], "2880 s", "computed changed: %r" % g2["computed"])
        self.assertEqual(g2["limit"], "2880 s (--max-wall)",
                         "limit changed: %r" % g2["limit"])
        text = g2["consequence"]
        self.assertNotIn("exceeds", text, "an admission says it exceeds:\n%s" % text)
        self.assertIn("admits", text, "no allow family:\n%s" % text)
        self.assertIn("within", text, "the admission does not say it is inside:\n%s" % text)
        self.assertNotIn("request(s)", text,
                         "the sentence calls the count 'request(s)' "
                         "instead of naming turns and requests:\n%s" % text)
        self.assertIn("turn(s)", text, "the admission does not name turns as turns:\n%s"
                      % text)

    def test_c2_refused_g2_at_2881_keeps_its_sentence_and_exit_8(self):
        """G2 at projected 2,881 s against --max-wall 2880 must read as a REFUSAL, exit 8."""
        with tempfile.TemporaryDirectory() as tmp:
            ledger, _rows = _fake_ledger(tmp, cap=4320, spent=0)
            runner, marker = _fake_runner(tmp)
            # 48 requests x 60.0208333 s per turn rounds to 2,881 s: one second past.
            rc, log = _run(_live_argv(tmp, ["--projected-turn-wall", "60.0208333",
                                            "--max-wall", "2880"]),
                           _env(tmp, ledger, runner, marker))
            invoked = os.path.exists(marker)
        self.assertEqual(rc, 8, "expected exit 8 (projection refusal), got %d\n%s"
                         % (rc, log[-3000:]))
        self.assertIn("G2 projection REFUSED", log, log[-3000:])
        self.assertIn("2881", log, "the refusal does not quote the projected seconds:\n%s"
                      % log[-3000:])
        self.assertIn("exceeds", log, "the refusal does not say it exceeds:\n%s"
                      % log[-3000:])
        self.assertNotIn("G2 admits", log, "a refusal printed the allow family:\n%s"
                         % log[-3000:])
        self.assertNotIn("request(s)", log,
                         "the refusal labels a count with the wrong unit:\n%s" % log[-3000:])
        self.assertFalse(invoked, "the runner was invoked past a G2 refusal")

    def test_d_all_three_verdicts_keep_their_artefact_digest(self):
        """A fixed sentence must not cost the provenance the manifest exists for."""
        with tempfile.TemporaryDirectory() as tmp:
            rc, log, marker = _admitted(tmp, ["--hypothesis", "H2", "--max-wall", "2880"])
            assert os.path.exists(marker), log[-3000:]
            doc = _only_manifest(tmp)
            digests = doc.get("artefact_digests") or {}
            verdicts = doc.get("verdicts") or []
            pairs = []
            for v in verdicts:
                path = v["artefact"]
                if not os.path.isabs(path):
                    path = os.path.join(ROOT, path)
                with open(path, "rb") as fh:
                    actual = hashlib.sha256(fh.read()).hexdigest()
                pairs.append((v["gate"], v["artefact"], v["artefact_sha256"], actual,
                              digests.get(v["artefact"])))
        self.assertEqual(len(verdicts), 3, "the manifest must carry three verdicts")
        for gate, rel, said, actual, published in pairs:
            self.assertRegex(said or "", r"^[0-9a-f]{64}$",
                             "%s carries no artefact_sha256: %r" % (gate, said))
            self.assertEqual(said, actual,
                             "%s digest does not match %s" % (gate, rel))
            self.assertEqual(published, said,
                             "%s digest absent from artefact_digests" % gate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
