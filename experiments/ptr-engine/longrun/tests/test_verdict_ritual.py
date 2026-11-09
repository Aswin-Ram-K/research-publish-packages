#!/usr/bin/env python3
"""test_verdict_ritual.py — make a finished-but-unverdicted unit red in the suite, offline.

Why this exists: `orchestration/VERDICT-RITUAL.md`. The page described a ritual, every card's tag demanded
it, and **0 of 7** closures after it landed carried a verdict row — all seven were classified *never
attempted*, and 0 of the 7 cards even carried the tag. Prose did not survive contact with the handoff step.

This test is the lever that does: it reads the LOCAL orchestration ledgers
(`~/.dsh/storages/orchestration/{closure,verdict}.jsonl`, plain JSONL — no network, no inference, nothing
written) and fails when a done/verdict-shaped handoff has a closed execution with no verdict row, for every
closure settled after the recorded baseline. Historical gaps stay recorded in
`experiments/ptr-engine/measure/VERDICT-ADOPTION.json` as a dated baseline rather than failing forever.

It also asserts the ORDER the fix installed — verdict row BEFORE the handoff write — in both the ritual page
and the unit template, so the order cannot be quietly reversed while the gate stays green.

Honesty rules: this module never writes a ledger, never invents a row, and treats a repaired gap (a row that
appeared after the closure) as repaired. Run directly (`python3 .../test_verdict_ritual.py`) or under pytest.
"""

import glob
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
HANDOFF_DIR = os.path.join(ROOT, "orchestration", "handoffs")
RITUAL_DOC = os.path.join(ROOT, "orchestration", "VERDICT-RITUAL.md")
TEMPLATE = os.path.join(ROOT, "orchestration", "units", "TEMPLATE.md")
BASELINE = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "VERDICT-ADOPTION.json")
STORE = os.path.expanduser(os.path.join("~", ".dsh", "storages", "orchestration"))
CLOSURES = os.path.join(STORE, "closure.jsonl")
VERDICTS = os.path.join(STORE, "verdict.jsonl")

ORDER_MARKER = "ORDER: verdict-row-before-handoff"


def _puts(path):
    """Every `put` record in a plugin JSONL ledger; a missing file is an empty ledger."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("op") == "put" and "key" in rec:
                out.append(rec)
    return out


def read_ledger(closures_path=CLOSURES, verdicts_path=VERDICTS):
    """(closures by `taskId:executionId`, set of keys that have a verdict row)."""
    closures = {}
    for rec in _puts(closures_path):
        closures[rec["key"]] = rec.get("value") or {}
    return closures, {rec["key"] for rec in _puts(verdicts_path)}


def unit_of(title):
    """A closure title is `<UNIT> — <purpose>`; the unit name is its prefix."""
    return (title or "").split(" — ")[0].strip()


def handoff_units(handoff_dir=HANDOFF_DIR):
    """Units whose handoff declares completion — `status: done`, or the verifier's `overall` shape."""
    seen = set()
    for path in glob.glob(os.path.join(handoff_dir, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                h = json.load(fh)
        except (ValueError, OSError):
            continue
        declared = h.get("status") == "done" or h.get("overall") in ("pass", "fail", "partial")
        if not declared:
            continue
        if h.get("unit"):
            seen.add(str(h["unit"]))
        seen.add(os.path.splitext(os.path.basename(path))[0])
    return seen


def unverdicted(handoffs, closures, verdict_keys):
    """{unit: [closure keys]} for a done handoff whose closed execution has no verdict row."""
    missing = {}
    for key, value in closures.items():
        unit = unit_of(value.get("title"))
        if unit not in handoffs:
            continue
        if key in verdict_keys:
            continue
        missing.setdefault(unit, []).append(key)
    return missing


def new_since(missing, closures, as_of_ms):
    """Only the gaps settled after the baseline: the past is recorded, not re-litigated."""
    out = {}
    for unit, keys in missing.items():
        fresh = [k for k in keys if (closures[k].get("createdAt") or 0) > as_of_ms]
        if fresh:
            out[unit] = fresh
    return out


class GateTest(unittest.TestCase):
    """The gate's own logic, proved with synthetic ledgers — a real red case and its green."""

    def test_red_a_done_handoff_with_no_row_is_reported(self):
        closures = {"t:e": {"title": "SYNTH-UNIT — did work", "verdict": "failed",
                            "reason": "no-verdict", "createdAt": 2000}}
        self.assertEqual(unverdicted({"SYNTH-UNIT"}, closures, set()), {"SYNTH-UNIT": ["t:e"]})

    def test_green_the_same_closure_with_a_row_is_clean(self):
        closures = {"t:e": {"title": "SYNTH-UNIT — did work", "verdict": "verified", "createdAt": 2000}}
        self.assertEqual(unverdicted({"SYNTH-UNIT"}, closures, {"t:e"}), {})

    def test_red_to_green_is_one_row_apart(self):
        closures = {"t:e": {"title": "SYNTH-UNIT — did work", "verdict": "failed", "createdAt": 2000}}
        red = unverdicted({"SYNTH-UNIT"}, closures, set())
        green = unverdicted({"SYNTH-UNIT"}, closures, {"t:e"})
        self.assertTrue(red and not green, "adding the row must be the only difference")

    def test_a_handoff_that_did_not_declare_done_is_out_of_scope(self):
        closures = {"t:e": {"title": "SYNTH-UNIT — did work", "createdAt": 2000}}
        self.assertEqual(unverdicted(set(), closures, set()), {})

    def test_baseline_suppresses_history_and_reports_only_new(self):
        closures = {"a:1": {"title": "OLD — x", "createdAt": 1000},
                    "a:2": {"title": "NEW — y", "createdAt": 3000}}
        missing = unverdicted({"OLD", "NEW"}, closures, set())
        fresh = new_since(missing, closures, 2000)
        self.assertEqual(fresh, {"NEW": ["a:2"]})


class OrderTest(unittest.TestCase):
    """The fix is ordering; a page that reverses it must fail here."""

    def test_ritual_declares_the_order_marker(self):
        with open(RITUAL_DOC, encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn(ORDER_MARKER, doc)
        self.assertLess(doc.index("Record the verdict row"),
                        doc.index("Write the handoff"),
                        "the ritual must put the verdict before the handoff")

    def test_template_closing_puts_the_verdict_first(self):
        with open(TEMPLATE, encoding="utf-8") as fh:
            closing = fh.read().split("## CLOSING", 1)[1].split("## verify", 1)[0].lower()
        self.assertLess(closing.index("record the verdict"),
                        closing.index("write the handoff"),
                        "TEMPLATE.md must say verdict -> handoff, not handoff -> verdict")


@unittest.skipUnless(os.path.exists(CLOSURES), "no local orchestration closure ledger")
class LiveLedgerTest(unittest.TestCase):
    """The measurement: no NEW finished-but-unverdicted closure since the recorded baseline."""

    @classmethod
    def setUpClass(cls):
        with open(BASELINE, encoding="utf-8") as fh:
            cls.doc = json.load(fh)
        cls.base = cls.doc["baseline"]
        cls.closures, cls.verdict_keys = read_ledger()
        cls.units = handoff_units()
        cls.missing = unverdicted(cls.units, cls.closures, cls.verdict_keys)

    def test_no_new_unverdicted_closure_since_the_baseline(self):
        fresh = new_since(self.missing, self.closures, self.base["as_of_ms"])
        self.assertEqual(fresh, {}, "a done handoff settled with no verdict row: %r" % (fresh,))

    def test_every_baseline_gap_is_either_still_missing_or_repaired(self):
        still = {k for keys in self.missing.values() for k in keys}
        for key in self.base["known_unverdicted_keys"]:
            self.assertTrue(key in still or key in self.verdict_keys,
                            "baseline key %s neither missing nor repaired — the baseline drifted" % key)

    def test_baseline_matches_the_measured_justification(self):
        counts = self.doc["diagnosis"]["counts"]
        self.assertEqual(counts["never_attempted"], 7)
        self.assertEqual(counts["attempted_and_refused"], 0)
        exclusive = ("never_attempted", "attempted_and_refused", "attempted_too_late", "other")
        self.assertEqual(sum(counts[k] for k in exclusive), 7,
                         "the four exclusive classes must partition the seven closures")
        self.assertEqual(counts["no_acceptance_command_existed"], 2,
                         "an overlapping class: 2 of the 7 named no runnable acceptance command")
        self.assertEqual(self.doc["diagnosis"]["post_ritual_closures"], 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
