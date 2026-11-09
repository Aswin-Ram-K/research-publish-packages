#!/usr/bin/env python3
"""test_claim_mode.py - HYPOTHESIS-SMOKE-MODE guards.

Offline. No request, no row file, no fixture, no network. Synthetic rows only.

Green (exit 0):

    python3 experiments/ptr-engine/longrun/tests/test_claim_mode.py
    python3 -m pytest experiments/ptr-engine/longrun/tests/test_claim_mode.py -q

Red (the guards are not vacuous): the suite copies ``claim_mode.py`` into a temp dir,
mutates exactly one line, and must observe the guard FAIL:

  * ``raise ClaimRefusal(flag_value)`` -> ``return ClaimRecord(...smoke...)``:
    silence becomes a permissive smoke default, so "silence is refused" goes red;
  * ``if offenders:`` -> ``if False:``: a smoke cell is silently accepted into a
    comparison instead of refusing it.

Both mutants are loaded by path; nothing under the repo is written.
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import claim_mode as cm  # noqa: E402


SMOKE_ROW = {"cell": "PLUMB-1", "arm": "plumbing", "rep": 1, "turn": 1,
             "claim": "none", "comparison_eligible": False}
H2_ROW = {"cell": "C-H2", "arm": "H2", "rep": 1, "turn": 1,
          "claim": "H2", "comparison_eligible": True}
LEGACY_ROW = {"arm": "old", "rep": 1, "turn": 1}          # no claim fields at all


def _raises(fn):
    try:
        fn()
    except Exception as exc:      # the test wants the exception object, any type
        return exc
    return None


def _silence_is_refused(module):
    return isinstance(_raises(lambda: module.resolve_claim(None)),
                      getattr(module, "ClaimRefusal", ()))


def _smoke_is_refused_by_name(module):
    exc = _raises(lambda: module.assert_comparable([H2_ROW, SMOKE_ROW]))
    return isinstance(exc, getattr(module, "IncomparableClaim", ()))


class TestResolvedShapes(unittest.TestCase):
    def test_smoke_and_plumbing_resolve_to_the_same_declaration(self):
        for spelling in ("smoke", "plumbing", " Smoke ", "PLUMBING"):
            rec = cm.resolve_claim(spelling)
            self.assertEqual(dict(rec),
                             {"mode": "smoke", "claim": "none",
                              "comparison_eligible": False},
                             "spelling %r must resolve to the claim-free shape"
                             % (spelling,))
            self.assertFalse(rec.comparison_eligible)
            self.assertTrue(rec.is_smoke)

    def test_each_hypothesis_resolves_and_is_comparable(self):
        for name in ("H1", "H2", "H3", "h2"):
            rec = cm.resolve_claim(name)
            self.assertEqual(dict(rec),
                             {"mode": "hypothesis", "claim": name.strip().upper(),
                              "comparison_eligible": True})
            self.assertTrue(rec["comparison_eligible"])

    def test_record_is_frozen(self):
        rec = cm.resolve_claim("H2")
        with self.assertRaises(TypeError):
            rec["mode"] = "smoke"                     # no __setitem__
        with self.assertRaises(AttributeError):
            rec.mode = "smoke"                        # __setattr__ refused
        self.assertFalse(hasattr(rec, "update"))
        self.assertEqual(sorted(rec), ["claim", "comparison_eligible", "mode"])


class TestRefusals(unittest.TestCase):
    def test_absent_empty_and_explicit_none_refuse(self):
        for value in (None, "", "   ", "none", "NONE"):
            exc = _raises(lambda v=value: cm.resolve_claim(v))
            self.assertIsInstance(exc, cm.ClaimRefusal,
                                  "%r must refuse, not default" % (value,))
            self.assertEqual(exc.code, 12)
            self.assertEqual(exc.code, cm.EXIT_PREREG)

    def test_unknown_spelling_refuses(self):
        for value in ("H4", "primary", "smoke+", "true", "0"):
            self.assertIsInstance(_raises(lambda v=value: cm.resolve_claim(v)),
                                  cm.ClaimRefusal)

    def test_refusal_names_the_three_forms_and_the_silence_rule(self):
        exc = _raises(lambda: cm.resolve_claim(None))
        text = str(exc)
        self.assertIn("three accepted forms", text)
        for form in ("smoke", "plumbing", "H1", "H2", "H3"):
            self.assertIn(form, text)
        self.assertIn("Silence is not a claim", text)
        self.assertIn("explicit `none`", text)

    def test_refusal_is_the_same_class_and_code_as_g3(self):
        exc = _raises(lambda: cm.resolve_claim(""))
        self.assertIsInstance(exc, cm.ClaimRefusal)
        self.assertEqual(cm.ClaimRefusal.code, 12)
        self.assertEqual(cm.ClaimRefusal.stage, "3c/7 G3 prereg gate")

        class DummyAbort(Exception):
            def __init__(self, code, stage, message, verdict=None):
                super().__init__(message)
                self.code, self.stage, self.verdict = code, stage, verdict

        abort = cm.as_abort(exc, abort_class=DummyAbort)
        self.assertIsInstance(abort, DummyAbort)
        self.assertEqual(abort.code, 12)
        self.assertEqual(abort.stage, "3c/7 G3 prereg gate")
        self.assertTrue(str(abort).startswith("claim REFUSED"))


class TestRowFields(unittest.TestCase):
    def test_smoke_rows_are_not_comparison_eligible(self):
        self.assertEqual(cm.row_fields(cm.resolve_claim("smoke")),
                         {"claim": "none", "comparison_eligible": False})
        self.assertEqual(cm.row_fields(cm.resolve_claim("H3")),
                         {"claim": "H3", "comparison_eligible": True})
        self.assertEqual(cm.ROW_FIELDS, ("claim", "comparison_eligible"))

    def test_row_fields_rejects_a_raw_string(self):
        with self.assertRaises(TypeError):
            cm.row_fields("H2")


class TestAssertComparable(unittest.TestCase):
    def test_hypothesis_cells_pass(self):
        out = cm.assert_comparable([H2_ROW, dict(H2_ROW, arm="H2", rep=2)])
        self.assertTrue(out["comparable"])
        self.assertEqual(out["claims"], {"h2": 2})
        self.assertEqual(out["legacy_rows"], 0)

    def test_one_smoke_cell_among_hypothesis_cells_is_refused_by_name(self):
        rows = [H2_ROW, dict(H2_ROW, rep=2), SMOKE_ROW]
        exc = _raises(lambda: cm.assert_comparable(rows))
        self.assertIsInstance(exc, cm.IncomparableClaim)
        self.assertTrue(str(exc).startswith("incomparable_claim"))
        self.assertIn("cell=PLUMB-1", str(exc))
        self.assertIn("arm=plumbing", str(exc))
        self.assertEqual(len(exc.offenders), 1)
        self.assertEqual(exc.offenders[0]["claim"], "none")
        self.assertEqual(exc.offenders[0]["reason"], "claim_free")

    def test_legacy_rows_are_counted_not_refused(self):
        out = cm.assert_comparable([LEGACY_ROW, H2_ROW])
        self.assertTrue(out["comparable"])
        self.assertEqual(out["legacy_rows"], 1)
        self.assertEqual(out["legacy_arms"], ["old"])

    def test_contradiction_and_unknown_claim_refuse(self):
        contradicted = dict(H2_ROW, comparison_eligible=False)
        self.assertIsInstance(_raises(lambda: cm.assert_comparable([contradicted])),
                              cm.IncomparableClaim)
        unknown = {"arm": "x", "claim": "H4", "comparison_eligible": True}
        exc = _raises(lambda: cm.assert_comparable([unknown]))
        self.assertIsInstance(exc, cm.IncomparableClaim)
        self.assertEqual(exc.offenders[0]["reason"], "unknown_claim")

    def test_half_written_row_refuses(self):
        half = {"arm": "x", "claim": "H2"}            # comparison_eligible missing
        exc = _raises(lambda: cm.assert_comparable([half]))
        self.assertIsInstance(exc, cm.IncomparableClaim)
        self.assertEqual(exc.offenders[0]["reason"], "claim_fields_incomplete")

    def test_helper_does_not_mutate_rows(self):
        rows = [H2_ROW, SMOKE_ROW]
        before = copy.deepcopy(rows)
        _raises(lambda: cm.assert_comparable(rows))
        self.assertEqual(rows, before)


def _mutant(replace_from, replace_to, tag):
    """Copy claim_mode.py to a temp dir with ONE line replaced; load it by path."""
    with open(cm.__file__, "r", encoding="utf-8") as fh:
        source = fh.read()
    if source.count(replace_from) != 1:
        raise AssertionError("mutation anchor must appear exactly once: %r"
                             % (replace_from,))
    source = source.replace(replace_from, replace_to)
    directory = tempfile.mkdtemp(prefix="claim-mode-mutant-")
    path = os.path.join(directory, "claim_mode_mutant_%s.py" % tag)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(source)
    spec = importlib.util.spec_from_file_location("claim_mode_mutant_%s" % tag, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)       # needs exit_codes: LONGRUN is on sys.path
    return module


class TestRedGreen(unittest.TestCase):
    def test_green_silence_is_refused(self):
        self.assertTrue(_silence_is_refused(cm))

    def test_red_permissive_default_for_silence_breaks_the_refusal_test(self):
        mutant = _mutant("    raise ClaimRefusal(flag_value)",
                         "    return ClaimRecord(MODE_SMOKE, CLAIM_NONE, False)",
                         "silence")
        # The mutant resolves silence to a smoke claim; the SAME guard now fails.
        self.assertEqual(dict(mutant.resolve_claim(None)),
                         {"mode": "smoke", "claim": "none",
                          "comparison_eligible": False})
        self.assertFalse(_silence_is_refused(mutant),
                         "a permissive default for silence must make the refusal test "
                         "fail -- it did not, so the test is vacuous")

    def test_green_smoke_in_a_comparison_is_refused(self):
        self.assertTrue(_smoke_is_refused_by_name(cm))

    def test_red_filtering_the_smoke_cell_breaks_the_comparison_test(self):
        mutant = _mutant("    if offenders:",
                         "    if False:", "filter")
        out = mutant.assert_comparable([H2_ROW, SMOKE_ROW])   # silently accepted
        self.assertTrue(out["comparable"])
        self.assertEqual(out["claims"], {"h2": 1, "none": 1})
        self.assertFalse(_smoke_is_refused_by_name(mutant),
                         "filtering the smoke cell must make the by-name refusal test "
                         "fail -- it did not, so the test is vacuous")


class _Args:
    def __init__(self, hypothesis=None):
        self.hypothesis = hypothesis


class Abort(Exception):
    """Stand-in for ``cell.Abort`` -- same 4-arg shape the conductor raises."""

    def __init__(self, code, stage, message, verdict=None):
        super().__init__(message)
        self.code, self.stage, self.verdict = code, stage, verdict


class TestWiringHelpers(unittest.TestCase):
    def test_check_prereg_claim_raises_the_callers_abort(self):
        with self.assertRaises(Abort) as ctx:
            cm.check_prereg_claim(_Args(None), Abort)
        self.assertEqual(ctx.exception.code, 12)
        self.assertEqual(ctx.exception.stage, "3c/7 G3 prereg gate")
        self.assertTrue(cm.check_prereg_claim(_Args("smoke"), Abort).is_smoke)
        self.assertEqual(cm.check_prereg_claim(_Args("H1"), Abort)["claim"], "H1")
        with self.assertRaises(Abort):
            cm.check_prereg_claim(_Args("none"), Abort)

    def test_smoke_prereg_verdict_is_ok_and_non_comparable(self):
        verdict = {"gate": "G3", "what": "prereg", "ok": False,
                   "hypothesis": "SMOKE", "hypothesis_source": "flag:--hypothesis",
                   "n": 4, "thresholds": {}}
        out = cm.smoke_prereg_verdict(verdict, 4)
        self.assertTrue(out["ok"])
        self.assertEqual(out["claim"], "none")
        self.assertFalse(out["comparison_eligible"])
        self.assertIn("smoke", out["short"])
        self.assertFalse(verdict["ok"], "the input verdict must not be mutated")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
