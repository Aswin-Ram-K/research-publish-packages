#!/usr/bin/env python3
"""test_det_verify.py - green/red tests for the deterministic verifier.

    python3 experiments/ptr-engine/tools/tests/test_det_verify.py
        -> exit 0 (the gate FN=0/FP=0 holds on the machine-decidable subset)

RED CASES (both must exit 1; the degradation is applied by env var so the same
assertions that pass in the run above are the ones that fail here):

    DET_VERIFY_DEGRADE=naive  python3 .../test_det_verify.py
        -> the sentence-final punctuation defect is reintroduced: a numeral must be
           followed by whitespace, so "ANSWER: 64." yields no asserted value and the
           correct-intent probe p.cp0.para is rejected (FN > 0).
    DET_VERIFY_DEGRADE=mention python3 .../test_det_verify.py
        -> cp.2 is degraded to a token-mention test (callee named => accepted, no
           negation and no keyword check), which is exactly the old judge's rule; the
           inverted answer p.cp2.negr1gap ("do NOT call ledger.record_refusal ...") is
           then accepted (FP > 0).

The degradation is a test-only monkeypatch of det_verify's module globals; the
shipped checker is not altered on disk.
"""
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import det_verify as dv  # noqa: E402

DEGRADE = os.environ.get("DET_VERIFY_DEGRADE", "").strip().lower()

_ORIG_ASSERTED = dv.asserted_number
_ORIG_NEGATION = dv.negation_in


def _naive_number(segment):
    """The v3 defect: a numeral only counts if it is followed by whitespace/EOL."""
    import re
    m = re.match(r"\s*(\d+)(?=\s|$)", segment)
    if not m:
        return None, {"numeral_found": False, "degraded": "sentence-final punctuation "
                                                   "rejected, as grade_v3 did"}
    return int(m.group(1)), {"numeral_found": True, "degraded": "first numeral only"}


def _mention_only_call(answer, truth_call):
    """The old judge's rule: the callee's name appears somewhere => accepted."""
    import re
    attr = truth_call["callee"].split(".")[-1]
    named = re.search(r"\b%s\b" % re.escape(attr), answer) is not None
    return named, ("mention_present" if named else "call_not_named"), {
        "degraded": "token mention only: negation and keywords not examined"}


_ORIG_CHECK_CALL = dv.check_call


def setUpModule():
    if DEGRADE == "naive":
        dv.asserted_number = _naive_number
    elif DEGRADE == "mention":
        dv.check_call = _mention_only_call
    elif DEGRADE:
        raise RuntimeError("unknown DET_VERIFY_DEGRADE=%r" % DEGRADE)


def tearDownModule():
    dv.asserted_number = _ORIG_ASSERTED
    dv.negation_in = _ORIG_NEGATION
    dv.check_call = _ORIG_CHECK_CALL


def _tmp_out():
    """Red runs must not clobber the shipped matrix; tests write to a temp file."""
    return os.path.join(tempfile.mkdtemp(prefix="det_verify_test_"), "matrix.json")


def probe(pid):
    return next(p for p in dv.load_probes() if p["id"] == pid)


def text(pid):
    return dv.probe_text(probe(pid))


class GroundTruthFromAST(unittest.TestCase):
    """Ground truth is read from the source, not from the fixture's expected string."""

    @classmethod
    def setUpClass(cls):
        cls.truth = dv.Truth()

    def test_constant_value_and_line(self):
        self.assertEqual(self.truth.default_max_refs, 64)
        self.assertEqual(self.truth.default_lineno, 39)
        self.assertTrue(self.truth.digest_matches["resolve.py"],
                        "cited source changed under the verifier")

    def test_class_count_and_names(self):
        self.assertEqual(len(self.truth.ptr_classes), 31)
        names = [n for n, _ in self.truth.ptr_classes]
        self.assertIn("PtrBudgetExceededError", names)
        self.assertTrue(self.truth.digest_matches["errors.py"])

    def test_refuse_call_shape(self):
        call = self.truth.refuse_call
        self.assertEqual(call["callee"], "ledger.record_refusal")
        self.assertEqual(call["keywords"], ["scope", "serialized_ref", "code"])

    def test_answer_segment_is_after_last_marker(self):
        t = "ANSWER: 31 is stale; there are 29 classes."
        self.assertEqual(dv.answer_segment(t).strip(), "31 is stale; there are 29 classes.")


class MeaningOverPunctuation(unittest.TestCase):
    def test_trailing_period_passes(self):
        ok, reason, _ = dv.check_numeric("ANSWER: 64.", 64, "DEFAULT_MAX_REFS")
        self.assertTrue(ok, reason)
        self.assertEqual(reason, "asserted_value_matches")

    def test_bare_and_prose_forms_pass(self):
        for answer in ("ANSWER: 64", "ANSWER: the default is 64 refs.",
                       "ANSWER: 64 refs."):
            ok, reason, _ = dv.check_numeric(answer, 64, "DEFAULT_MAX_REFS")
            self.assertTrue(ok, (answer, reason))

    def test_number_wrong_or_retracted_fails(self):
        for answer in ("ANSWER: 128 refs.",
                       "ANSWER: 64 is wrong; the default is 32 refs.",
                       "ANSWER: 31 is stale; there are 29 Ptr* error classes."):
            truth = 64 if "64" in answer or "128" in answer else 31
            ok, reason, _ = dv.check_numeric(answer, truth, "x")
            self.assertFalse(ok, (answer, reason))

    def test_word_number_is_not_an_assertion(self):
        ok, reason, _ = dv.check_numeric("ANSWER: sixty-four refs.", 64, "x")
        self.assertFalse(ok)
        self.assertEqual(reason, "no_asserted_value")


class StructuralCallCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = dv.Truth()

    def test_correct_call_accepted(self):
        for pid in ("p.cp2.ideal", "p.cp2.para", "p.cp2.para_noraising"):
            ok, reason, detail = dv.verify_probe(probe(pid), text(pid), self.truth)
            self.assertTrue(ok, (pid, reason, detail))

    def test_negated_call_fails(self):
        for pid in ("p.cp2.neg", "p.cp2.negr1gap"):
            ok, reason, detail = dv.verify_probe(probe(pid), text(pid), self.truth)
            self.assertFalse(ok, pid)
            self.assertEqual(reason, "call_negated", (pid, detail))

    def test_wrong_keyword_fails(self):
        answer = ("ANSWER: it calls ledger.record_refusal with scope, grant=text and "
                  "code=error.code, then re-raises.")
        ok, reason, detail = dv.check_call(answer, self.truth.refuse_call)
        self.assertFalse(ok)
        self.assertEqual(reason, "keyword_mismatch")
        self.assertEqual(detail["missing"], ["serialized_ref"])
        self.assertEqual(detail["extra"], ["grant"])

    def test_call_never_named_fails(self):
        ok, reason, _ = dv.check_call("ANSWER: it calls logger.warning and returns.",
                                      self.truth.refuse_call)
        self.assertFalse(ok)
        self.assertEqual(reason, "call_not_named")

    def test_undecidable_is_handed_back(self):
        for pid in ("p.rep.ideal", "p.acc.wrong"):
            ok, reason, detail = dv.verify_probe(probe(pid), text(pid), self.truth)
            self.assertIsNone(ok, pid)
            self.assertEqual(reason, "undecidable")


class Gate(unittest.TestCase):
    """The acceptance gate: FN=0 and FP=0 on the machine-decidable subset.

    The denominator is the IMPLEMENTED probe set, NOT the acceptance checks: 48
    in-scope probes (23 correct-intent, 22 incorrect-intent, 3 omission controls)
    out of 58 in the corpus. The 10 excluded probes belong to the two checkpoints
    no handler decides: repair.t30 x5 and acc.n2b x5.
    """

    @classmethod
    def setUpClass(cls):
        cls.doc = dv.evaluate()

    def test_pooled_gate(self):
        pooled = self.doc["pooled"]
        self.assertEqual(pooled["n_correct"], 23)
        self.assertEqual(pooled["n_incorrect"], 22)
        self.assertEqual(pooled["FN"], 0, [r["probe"] for r in self.doc["rows"]
                                           if r["in_scope"] and r["intent"] == "correct"
                                           and not r["det_verify"]["pass"]])
        self.assertEqual(pooled["FP"], 0, [r["probe"] for r in self.doc["rows"]
                                           if r["in_scope"] and r["intent"] == "incorrect"
                                           and r["det_verify"]["pass"]])
        self.assertTrue(pooled["gate_pass"])

    def test_per_checkpoint_gate(self):
        for cp in dv.DECIDABLE:
            r = self.doc["per_checkpoint"][cp]
            self.assertEqual((r["FN"], r["FP"]), (0, 0), cp)
            self.assertTrue(r["gate_pass"], cp)

    def test_omission_probes_rejected(self):
        p = self.doc["pooled"]
        self.assertEqual(p["omission_rejected"], p["n_omission"])
        self.assertEqual(p["n_omission"], 3)

    def test_every_probe_reaches_the_matrix(self):
        self.assertEqual(len(self.doc["rows"]), len(dv.load_probes()))
        for cp in ("repair.t30", "acc.n2b", "acc.cp1", "acc.4"):
            self.assertIn(cp, {r["checkpoint"] for r in self.doc["rows"]})

    def test_gate_scope_names_denominator_and_exclusions_inline(self):
        doc = dv.build(_tmp_out())
        scope = doc["definition"]["gate_scope"]
        self.assertIn("48 IMPLEMENTED probes", scope)
        self.assertIn("10 excluded", scope)
        self.assertIn("NOT over the acceptance checks as a whole", scope)
        self.assertEqual(sorted(doc["definition"]["excluded_from_gate"]),
                         ["acc.n2b", "repair.t30"])
        self.assertEqual(doc["coverage_summary"], dv.COVERAGE_SUMMARY)


# --------------------------------------------------------------------------- #
# TASK 1: the numeral rule. Red before green: each case below is REJECTED by the
# old last-survivor rule and ACCEPTED by the citation-aware rule.
# --------------------------------------------------------------------------- #
_OLD_INT = re.compile(r"(?<![\w.])\d+(?![\w])")
_OLD_RETRACT = re.compile(
    r"^\s*(?:is|was|are|were)\s+(?:wrong|stale|incorrect|outdated|false|obsolete|"
    r"no\s+longer)\b", re.I)


def old_asserted_number(segment):
    """The rule this fix replaces: take the LAST surviving numeral in the segment."""
    kept = []
    for m in _OLD_INT.finditer(segment):
        if _OLD_RETRACT.match(segment[m.end():m.end() + 48]):
            continue
        kept.append(int(m.group()))
    return kept[-1] if kept else None


NUMERAL_CASES = (
    ("p.num.cite.paren", 64),          # ANSWER: 64 (resolve.py:39)
    ("p.num.cite.ratio", 64),          # ANSWER: 64 refs, 1 of 3 files
    ("p.num.cite.semicolon", 64),      # ANSWER: 64; see ledger.py:12 ...
    ("p.num.cite.wrapped", 64),        # ANSWER:\n\n64 refs per turn (see resolve.py:39)
    ("p.num.cite.line", 64),           # ANSWER: 64 refs (line 39)
    ("p.num.cite.definition", 64),     # ANSWER: DEFAULT_MAX_REFS = 64; at resolve.py:39
    ("p.num.cite.prose_before", 31),   # prose cites errors.py:247; ANSWER: 31, not 30
    ("p.num.cite.range", 31),          # ANSWER: 31 Ptr* classes, lines 15-142
)


class NumeralRule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = dv.Truth()

    def test_each_case_was_red_under_the_old_rule(self):
        for pid, truth_value in NUMERAL_CASES:
            text = dv.probe_text(probe(pid))
            old = old_asserted_number(dv.answer_segment(text))
            self.assertNotEqual(old, truth_value,
                                "old rule should have rejected this case: %s (got %r)"
                                % (pid, old))

    def test_each_case_is_green_under_the_citation_rule(self):
        for pid, truth_value in NUMERAL_CASES:
            ok, reason, detail = dv.verify_probe(probe(pid), dv.probe_text(probe(pid)),
                                                 self.truth)
            self.assertTrue(ok, (pid, reason, detail))
            self.assertEqual(detail["asserted"], truth_value, pid)
            self.assertEqual(reason, "asserted_value_matches", pid)

    def test_citation_forms_are_not_candidates(self):
        for segment, value in (
                ("ANSWER: 64 (resolve.py:39)", 64),
                ("ANSWER: 64 refs, 1 of 3 files", 64),
                ("ANSWER: 64 #L39", 64),
                ("ANSWER: 64 refs (line 39)", 64),
                ("ANSWER: 64; see ledger.py:12", 64),
                ("ANSWER: 31 classes, lines 15-142", 31),
                ("ANSWER: 31 (errors.py:15-142)", 31)):
            got, ev = dv.asserted_number(segment)
            self.assertEqual(got, value, (segment, ev))

    def test_retraction_still_beats_the_first_numeral(self):
        got, ev = dv.asserted_number(" 64 is wrong; the default is 32 refs.")
        self.assertEqual(got, 32, ev)
        ok, reason, _ = dv.check_numeric("ANSWER: 64 is wrong; the default is 32 refs.",
                                         64, "x")
        self.assertFalse(ok)

    def test_spelled_numeral_stays_an_omission(self):
        # Not a regression: the spelling test is the omission control's business
        # (p.cp0.omit expects "sixty-four refs." to be rejected).
        ok, reason, _ = dv.check_numeric("ANSWER: sixty-four refs.", 64, "x")
        self.assertFalse(ok)
        self.assertEqual(reason, "no_asserted_value")


# --------------------------------------------------------------------------- #
# TASK 2: the negation lexicon, including the asymmetry that separates a lexicon
# from a keyword ban.
# --------------------------------------------------------------------------- #
NEGATION_PROBE_IDS = (
    "p.neg.avoid", "p.neg.avoid_call", "p.neg.instead", "p.neg.fails", "p.neg.skips",
    "p.neg.wont", "p.neg.must_not", "p.neg.should_not", "p.neg.without", "p.neg.never",
)

LEXICON_FORMS = (
    ("avoid", "the handler should avoid calling ledger.record_refusal"),
    ("shouldn't", "it shouldn't call the ledger"),
    ("should not", "it should not call the ledger"),
    ("must not", "it must not call the ledger"),
    ("won't", "it won't call the ledger"),
    ("will not", "it will not call the ledger"),
    ("without calling", "the error propagates without calling the ledger"),
    ("instead of calling", "it logs instead of calling the ledger"),
    ("fails to call", "the branch fails to call the ledger"),
    ("failed to call", "the branch failed to call the ledger"),
    ("skips", "it skips the call to the ledger"),
    ("skipped", "it skipped the ledger write"),
    ("doesn't", "it doesn't call the ledger"),
    ("not calling", "not calling the ledger is the bug"),
    ("never", "the ledger call never runs"),
)


class NegationLexicon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truth = dv.Truth()

    def test_every_variant_is_rejected_as_negated(self):
        for pid in NEGATION_PROBE_IDS:
            ok, reason, detail = dv.verify_probe(probe(pid), dv.probe_text(probe(pid)),
                                                 self.truth)
            self.assertFalse(ok, pid)
            self.assertEqual(reason, "call_negated", (pid, detail))

    def test_avoid_outside_the_governing_clause_still_passes(self):
        """The asymmetry test: `avoid` next to a CORRECT call claim is not a denial."""
        for pid in ("p.neg.asym_clause", "p.neg.asym_tail"):
            ok, reason, detail = dv.verify_probe(probe(pid), dv.probe_text(probe(pid)),
                                                 self.truth)
            self.assertTrue(ok, (pid, reason, detail))
            self.assertEqual(reason, "call_shape_matches", pid)

    def test_lexicon_covers_every_required_form(self):
        for name, clause in LEXICON_FORMS:
            self.assertIsNotNone(dv.negation_in(clause), name)

    def test_avoid_with_a_non_call_object_is_not_negation(self):
        self.assertIsNone(dv.negation_in("avoid the retry loop"))


# --------------------------------------------------------------------------- #
# TASK 3: coverage is a code-derived count over the matrix's 13 entries.
# --------------------------------------------------------------------------- #
class CoverageClaim(unittest.TestCase):
    def test_counts_come_from_code_not_prose(self):
        self.assertEqual(len(dv.COVERAGE), 13)
        self.assertEqual(len(dv.CHECK_ORDER), 13)
        self.assertEqual(dv.COVERAGE_SUMMARY["total"], 13)
        self.assertEqual(dv.COVERAGE_SUMMARY["decidable_count"],
                         sum(1 for c in dv.COVERAGE if c["decidable"]))
        self.assertEqual(tuple(dv.COVERAGE_SUMMARY["decidable"]), dv.DECIDABLE)
        self.assertEqual(dv.COVERAGE_SUMMARY["ratio"], "8/13")
        self.assertEqual(dv.COVERAGE_SUMMARY["undecidable"],
                         ["acc.2", "acc.3", "acc.n2b", "acc.n3b..acc.n3e",
                          "repair.t30"])

    def test_every_decidable_entry_has_a_handler_and_a_probe(self):
        truth = dv.Truth()
        probes = dv.load_probes()
        for cp in dv.DECIDABLE:
            self.assertIn(cp, dv.CHECK_HANDLERS, cp)
            cps = [p for p in probes if p["checkpoint"] == cp]
            self.assertTrue(cps, "no probe exercises %s" % cp)
            for p in cps:
                ok, reason, _ = dv.verify_probe(p, dv.probe_text(p), truth)
                self.assertIsNotNone(ok, (cp, p["id"]))
                self.assertNotEqual(reason, "undecidable", (cp, p["id"]))

    def test_every_undecidable_entry_has_no_handler(self):
        for c in dv.COVERAGE:
            if not c["decidable"]:
                self.assertNotIn(c["check"], dv.CHECK_HANDLERS, c["check"])
                self.assertTrue(c["why"], c["check"])

    def test_excluded_probes_are_named(self):
        doc = dv.build(_tmp_out())
        excl = doc["definition"]["excluded_from_gate"]
        self.assertEqual(sorted(excl), ["acc.n2b", "repair.t30"])
        self.assertEqual(sum(len(v) for v in excl.values()), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
